"""
Conversational Chat Engine for MyLLM.

Coordinates multi-turn dialogue, context window management, KV cache reuse and
invalidation, deterministic streaming and batch generation, and session persistence.
"""

from __future__ import annotations

import logging
from pathlib import Path
import time
from typing import Any, Dict, Iterator, List, Optional, Tuple, Union
import torch

from myllm.chat.context import ContextInfo, ContextManager
from myllm.chat.message import ChatHistory, ChatMessage
from myllm.chat.session import ChatSession
from myllm.chat.telemetry import ChatResponse, ChatTelemetry, ChatToken
from myllm.chat.template import ChatTemplate
from myllm.inference.cache import KVCache
from myllm.inference.loader import load_inference_system
from myllm.inference.sampling import sample_next_token
from myllm.inference.stopping import check_eos
from myllm.inference.types import GenerationConfig
from myllm.model.gpt import GPTModel
from myllm.tokenizer import Tokenizer
from myllm.tokenizer.vocabulary import EOS_ID

logger = logging.getLogger(__name__)


class ChatEngine:
    """
    Stateful multi-turn conversational chat engine.
    """

    def __init__(
        self,
        model: GPTModel,
        tokenizer: Tokenizer,
        system_prompt: Optional[str] = None,
        default_config: Optional[GenerationConfig] = None,
        checkpoint_path: Optional[str] = None,
        device: Union[str, torch.device] = "cpu",
    ) -> None:
        self.device = torch.device(device)
        if self.device.type != "cpu":
            raise ValueError(f"ChatEngine strictly requires CPU execution, got '{self.device.type}'")

        self.model = model.to(self.device)
        self.model.eval()
        self.tokenizer = tokenizer
        self.system_prompt = system_prompt.strip() if system_prompt else None
        self.checkpoint_path = str(checkpoint_path) if checkpoint_path else None

        # Verify tokenizer fingerprint
        from myllm.data.tokenizer_pipeline import compute_tokenizer_fingerprint
        self.tokenizer_fingerprint = compute_tokenizer_fingerprint(self.tokenizer)

        # Context manager
        self.context_length = self.model.config.context_length
        self.context_manager = ContextManager(
            tokenizer=self.tokenizer,
            context_length=self.context_length,
            min_response_budget=1,
        )

        # Default generation configuration
        if default_config is not None:
            self.default_config = default_config
        else:
            self.default_config = GenerationConfig(
                max_new_tokens=32,
                do_sample=False,  # Greedy by default for determinism
                use_cache=True,
                stop_on_eos=True,
            )

        # Chat state
        self.history = ChatHistory()
        self.session_id: Optional[str] = None
        self.kv_cache = KVCache(context_length=self.context_length)
        self.cache_dirty = True

    @classmethod
    def from_checkpoint(
        cls,
        checkpoint_path: Union[str, Path],
        tokenizer_path: Optional[Union[str, Path]] = None,
        system_prompt: Optional[str] = None,
        default_config: Optional[GenerationConfig] = None,
        device: str = "cpu",
    ) -> ChatEngine:
        """
        Factory method to initialize ChatEngine from checkpoint and tokenizer files.
        """
        model, tokenizer, payload = load_inference_system(
            checkpoint_path=checkpoint_path,
            tokenizer_path=tokenizer_path,
        )
        if tokenizer is None:
            raise ValueError("A valid tokenizer path must be provided to initialize ChatEngine.")

        return cls(
            model=model,
            tokenizer=tokenizer,
            system_prompt=system_prompt,
            default_config=default_config,
            checkpoint_path=str(checkpoint_path),
            device=device,
        )

    def start_chat(self, system_prompt: Optional[str] = None) -> None:
        """Reset conversation and optionally update the system prompt."""
        self.reset()
        if system_prompt is not None:
            self.system_prompt = system_prompt.strip() if system_prompt else None

    def reset(self) -> None:
        """Clear conversation history, invalidate KV cache, and reset session."""
        self.history.clear()
        self.kv_cache.reset()
        self.cache_dirty = True
        self.session_id = None

    def add_message(self, role: str, content: str) -> ChatMessage:
        """Add a message to the history and mark KV cache dirty."""
        msg = self.history.add_message(role=role, content=content)
        self.cache_dirty = True
        return msg

    def send_user_message(self, content: str) -> ChatMessage:
        """Convenience method to append a user message."""
        return self.add_message(role="user", content=content)

    def get_history(self) -> List[ChatMessage]:
        """Get the current conversation history."""
        return self.history.messages

    def create_session(self) -> ChatSession:
        """Export current conversational state into a ChatSession object."""
        gen_cfg_dict = {
            "max_new_tokens": self.default_config.max_new_tokens,
            "temperature": self.default_config.temperature,
            "top_k": self.default_config.top_k,
            "top_p": self.default_config.top_p,
            "repetition_penalty": self.default_config.repetition_penalty,
            "do_sample": self.default_config.do_sample,
            "seed": self.default_config.seed,
            "use_cache": self.default_config.use_cache,
        }
        return ChatSession(
            session_id=self.session_id,
            system_prompt=self.system_prompt,
            history=self.history.clone(),
            generation_config=gen_cfg_dict,
            model_checkpoint=self.checkpoint_path,
            tokenizer_fingerprint=self.tokenizer_fingerprint,
        )

    def load_session(self, session: ChatSession) -> None:
        """Load conversation history and configuration from a ChatSession."""
        self.reset()
        self.session_id = session.session_id
        self.system_prompt = session.system_prompt
        self.history = session.history.clone()
        self.cache_dirty = True

    @torch.no_grad()
    def stream_response(
        self,
        config: Optional[GenerationConfig] = None,
    ) -> Iterator[ChatToken]:
        """
        Generate assistant response in a token-by-token streaming manner.

        Yields:
            ChatToken for each generated token, with the final item marked finished=True.
        """
        if len(self.history) == 0 or self.history.last_message.role != "user":
            raise RuntimeError("Cannot generate response: last message in history must be from 'user'.")

        cfg = config or self.default_config

        # 1. Resolve EOS ID
        eos_id = cfg.eos_token_id
        if eos_id is None and hasattr(self.tokenizer, "eos_token_id") and self.tokenizer.eos_token_id is not None:
            eos_id = self.tokenizer.eos_token_id
        elif eos_id is None:
            eos_id = EOS_ID

        # 2. Context Window Truncation
        truncated_history, context_info, prompt_text = self.context_manager.fit_context(
            history=self.history.messages,
            system_prompt=self.system_prompt,
            max_new_tokens=cfg.max_new_tokens,
        )

        prompt_ids = self.tokenizer.encode(prompt_text, add_bos=False, add_eos=False)
        prompt_len = len(prompt_ids)

        # If context was truncated, KV cache cannot be reused from previous turn
        if context_info.truncated or self.cache_dirty:
            self.kv_cache.reset()
            self.cache_dirty = False

        # Calculate effective generation budget
        available_budget = self.context_length - prompt_len
        if available_budget <= 0:
            yield ChatToken(token_id=eos_id, text="", finished=True, stop_reason="context_limit")
            return

        effective_max_new = min(cfg.max_new_tokens, available_budget)

        # Setup deterministic RNG if seed provided
        rng_generator: Optional[torch.Generator] = None
        if cfg.seed is not None:
            rng_generator = torch.Generator(device="cpu")
            rng_generator.manual_seed(cfg.seed)

        generated_token_ids: List[int] = []
        seen_tokens = list(prompt_ids)
        stopped_reason = "max_new_tokens"

        if cfg.use_cache:
            # === Generation with KV Cache ===
            self.kv_cache.reset()  # Prefill current turn prompt
            input_tensor = torch.tensor([prompt_ids], dtype=torch.long, device=self.device)
            model_out = self.model(input_tensor, past_key_values=None, use_cache=True)
            logits, present_kvs = (model_out[0], model_out[2]) if len(model_out) == 3 else model_out
            self.kv_cache.update(present_kvs)

            next_logits = logits[0, -1, :]
            next_token = sample_next_token(
                logits=next_logits,
                seen_tokens=seen_tokens,
                config=cfg,
                generator=rng_generator,
            )
            generated_token_ids.append(next_token)
            seen_tokens.append(next_token)

            token_str = self.tokenizer.decode([next_token])
            if check_eos(next_token, eos_id, cfg.stop_on_eos):
                stopped_reason = "eos"
                yield ChatToken(token_id=next_token, text=token_str, finished=False)
                yield ChatToken(token_id=next_token, text="", finished=True, stop_reason=stopped_reason)
            else:
                yield ChatToken(token_id=next_token, text=token_str, finished=False)

                for step_idx in range(1, effective_max_new):
                    # Check context ceiling
                    if prompt_len + len(generated_token_ids) >= self.context_length:
                        stopped_reason = "context_limit"
                        break

                    curr_input = torch.tensor([[next_token]], dtype=torch.long, device=self.device)
                    model_out = self.model(
                        curr_input,
                        past_key_values=self.kv_cache.past_key_values,
                        use_cache=True,
                    )
                    logits, present_kvs = (model_out[0], model_out[2]) if len(model_out) == 3 else model_out
                    self.kv_cache.update(present_kvs)

                    next_logits = logits[0, -1, :]
                    next_token = sample_next_token(
                        logits=next_logits,
                        seen_tokens=seen_tokens,
                        config=cfg,
                        generator=rng_generator,
                    )
                    generated_token_ids.append(next_token)
                    seen_tokens.append(next_token)

                    token_str = self.tokenizer.decode([next_token])
                    if check_eos(next_token, eos_id, cfg.stop_on_eos):
                        stopped_reason = "eos"
                        yield ChatToken(token_id=next_token, text=token_str, finished=False)
                        break

                    yield ChatToken(token_id=next_token, text=token_str, finished=False)

                yield ChatToken(token_id=next_token, text="", finished=True, stop_reason=stopped_reason)

        else:
            # === Generation without KV Cache ===
            curr_sequence = list(prompt_ids)
            for step_idx in range(effective_max_new):
                if len(curr_sequence) >= self.context_length:
                    stopped_reason = "context_limit"
                    break

                input_tensor = torch.tensor([curr_sequence], dtype=torch.long, device=self.device)
                model_output = self.model(input_tensor, use_cache=False)
                logits = model_output[0] if isinstance(model_output, tuple) else model_output

                next_logits = logits[0, -1, :]
                next_token = sample_next_token(
                    logits=next_logits,
                    seen_tokens=seen_tokens,
                    config=cfg,
                    generator=rng_generator,
                )
                generated_token_ids.append(next_token)
                curr_sequence.append(next_token)
                seen_tokens.append(next_token)

                token_str = self.tokenizer.decode([next_token])
                if check_eos(next_token, eos_id, cfg.stop_on_eos):
                    stopped_reason = "eos"
                    yield ChatToken(token_id=next_token, text=token_str, finished=False)
                    break

                yield ChatToken(token_id=next_token, text=token_str, finished=False)

            yield ChatToken(token_id=generated_token_ids[-1] if generated_token_ids else eos_id, text="", finished=True, stop_reason=stopped_reason)

        # Filter out EOS if present from assistant message text
        final_token_ids = [t for t in generated_token_ids if t != eos_id]
        full_assistant_text = self.tokenizer.decode(final_token_ids).strip()
        if not full_assistant_text:
            full_assistant_text = "..."  # Fallback to satisfy non-empty assistant content policy

        # Add assistant response to history
        self.history.add_message(role="assistant", content=full_assistant_text)
        self.cache_dirty = True

    def generate_response(
        self,
        config: Optional[GenerationConfig] = None,
    ) -> ChatResponse:
        """
        Generate assistant response and return complete structured ChatResponse.
        """
        cfg = config or self.default_config
        start_time = time.perf_counter()

        tokens: List[ChatToken] = []
        final_stop_reason = "max_new_tokens"

        for tok in self.stream_response(config=cfg):
            if tok.finished:
                final_stop_reason = tok.stop_reason or "max_new_tokens"
            else:
                tokens.append(tok)

        elapsed = time.perf_counter() - start_time
        num_generated = len(tokens)
        tps = num_generated / elapsed if elapsed > 0 else 0.0

        # Most recent message is the assistant message added by stream_response
        assistant_msg = self.history.last_message
        assert assistant_msg is not None and assistant_msg.role == "assistant"

        # Obtain context info
        _, context_info, _ = self.context_manager.fit_context(
            history=self.history.messages[:-1],  # prompt without the newly added response
            system_prompt=self.system_prompt,
            max_new_tokens=cfg.max_new_tokens,
        )

        telemetry = ChatTelemetry(
            prompt_tokens=context_info.used_tokens,
            generated_tokens=num_generated,
            total_tokens=context_info.used_tokens + num_generated,
            generation_latency=elapsed,
            tokens_per_second=tps,
            stop_reason=final_stop_reason,
            context_truncated=context_info.truncated,
            removed_messages=context_info.removed_messages,
            cache_used=cfg.use_cache,
        )

        return ChatResponse(
            message=assistant_msg,
            telemetry=telemetry,
            context_info=context_info,
        )
