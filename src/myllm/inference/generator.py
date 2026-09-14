"""
Autoregressive Text Generator for MyLLM.

Supports both KV-cached generation and naive generation on CPU, with
sampling controls, deterministic seeding, EOS stopping, and context validation.
"""

from __future__ import annotations

import logging
import time
from typing import List, Optional, Union
import torch
import torch.nn as nn
from myllm.inference.cache import KVCache
from myllm.inference.sampling import sample_next_token
from myllm.inference.stopping import check_eos, validate_and_truncate_context
from myllm.inference.types import GenerationConfig, GenerationResult
from myllm.model.gpt import GPTModel
from myllm.tokenizer import Tokenizer

logger = logging.getLogger(__name__)


class Generator:
    """
    Autoregressive inference engine for GPT models.
    """

    def __init__(
        self,
        model: GPTModel,
        tokenizer: Optional[Tokenizer] = None,
        device: Union[str, torch.device] = "cpu",
    ) -> None:
        """
        Initialize the generator.

        Args:
            model: Trained GPTModel instance.
            tokenizer: Optional Tokenizer for string encoding/decoding.
            device: Execution device (must be 'cpu').
        """
        self.device = torch.device(device)
        if self.device.type != "cpu":
            raise ValueError(f"Generator strictly requires CPU device, got '{self.device.type}'")

        self.model = model.to(self.device)
        self.model.eval()
        self.tokenizer = tokenizer

    @torch.no_grad()
    def generate(
        self,
        prompt: Union[str, List[int]],
        config: Optional[GenerationConfig] = None,
    ) -> GenerationResult:
        """
        Generate tokens autoregressively from a prompt.

        Args:
            prompt: Text prompt string or list of integer token IDs.
            config: GenerationConfig options (uses default if None).

        Returns:
            GenerationResult containing generated tokens, text, timings, and metadata.
        """
        if config is None:
            config = GenerationConfig()

        # 1. Resolve prompt token IDs
        if isinstance(prompt, str):
            if self.tokenizer is None:
                raise ValueError("Tokenizer must be supplied to Generator to encode string prompt.")
            prompt_str = prompt
            raw_prompt_ids = self.tokenizer.encode(prompt_str)
        elif isinstance(prompt, list):
            raw_prompt_ids = list(prompt)
            if self.tokenizer is not None:
                prompt_str = self.tokenizer.decode(raw_prompt_ids)
            else:
                prompt_str = ""
        else:
            raise TypeError(f"Prompt must be str or list of ints, got {type(prompt)}")

        # 2. Resolve EOS token ID
        eos_id = config.eos_token_id
        if eos_id is None and self.tokenizer is not None:
            if hasattr(self.tokenizer, "eos_token_id") and self.tokenizer.eos_token_id is not None:
                eos_id = self.tokenizer.eos_token_id
            elif "<|endoftext|>" in self.tokenizer.vocab.special_tokens:
                eos_id = self.tokenizer.vocab.special_tokens["<|endoftext|>"]

        # 3. Validate and enforce context limit
        prompt_ids, effective_max_new = validate_and_truncate_context(
            prompt_ids=raw_prompt_ids,
            max_new_tokens=config.max_new_tokens,
            context_length=self.model.config.context_length,
            strategy=config.context_overflow_strategy,
        )

        # 4. Prepare deterministic CPU generator if seed is set
        rng_generator: Optional[torch.Generator] = None
        if config.seed is not None:
            rng_generator = torch.Generator(device="cpu")
            rng_generator.manual_seed(config.seed)

        start_time = time.perf_counter()
        generated_token_ids: List[int] = []
        seen_tokens = list(prompt_ids)
        stopped_on_eos = False
        stopped_reason = "max_tokens"

        if effective_max_new == 0:
            stopped_reason = "context_limit"
        elif config.use_cache:
            # === Generation with KV Cache ===
            kv_cache = KVCache(context_length=self.model.config.context_length)

            # Prefill phase: full prompt forward
            input_tensor = torch.tensor([prompt_ids], dtype=torch.long, device=self.device)
            model_out = self.model(input_tensor, past_key_values=None, use_cache=True)
            logits, present_kvs = (model_out[0], model_out[2]) if len(model_out) == 3 else model_out
            kv_cache.update(present_kvs)

            next_token_logits = logits[0, -1, :]
            next_token = sample_next_token(
                logits=next_token_logits,
                seen_tokens=seen_tokens,
                config=config,
                generator=rng_generator,
            )
            generated_token_ids.append(next_token)
            seen_tokens.append(next_token)

            if check_eos(next_token, eos_id, config.stop_on_eos):
                stopped_on_eos = True
                stopped_reason = "eos"
            else:
                # Incremental decoding phase
                for _ in range(1, effective_max_new):
                    curr_input = torch.tensor([[next_token]], dtype=torch.long, device=self.device)
                    model_out = self.model(
                        curr_input,
                        past_key_values=kv_cache.past_key_values,
                        use_cache=True,
                    )
                    logits, present_kvs = (model_out[0], model_out[2]) if len(model_out) == 3 else model_out
                    kv_cache.update(present_kvs)

                    next_token_logits = logits[0, -1, :]
                    next_token = sample_next_token(
                        logits=next_token_logits,
                        seen_tokens=seen_tokens,
                        config=config,
                        generator=rng_generator,
                    )
                    generated_token_ids.append(next_token)
                    seen_tokens.append(next_token)

                    if check_eos(next_token, eos_id, config.stop_on_eos):
                        stopped_on_eos = True
                        stopped_reason = "eos"
                        break

        else:
            # === Naive Generation without KV Cache ===
            curr_sequence = list(prompt_ids)
            for _ in range(effective_max_new):
                input_tensor = torch.tensor([curr_sequence], dtype=torch.long, device=self.device)
                model_output = self.model(input_tensor, use_cache=False)
                logits = model_output[0] if isinstance(model_output, tuple) else model_output

                next_token_logits = logits[0, -1, :]
                next_token = sample_next_token(
                    logits=next_token_logits,
                    seen_tokens=seen_tokens,
                    config=config,
                    generator=rng_generator,
                )
                generated_token_ids.append(next_token)
                curr_sequence.append(next_token)
                seen_tokens.append(next_token)

                if check_eos(next_token, eos_id, config.stop_on_eos):
                    stopped_on_eos = True
                    stopped_reason = "eos"
                    break

        elapsed = time.perf_counter() - start_time
        num_generated = len(generated_token_ids)
        tps = num_generated / elapsed if elapsed > 0 else 0.0

        # Decode generated text
        if self.tokenizer is not None:
            generated_text = self.tokenizer.decode(generated_token_ids)
        else:
            generated_text = ""

        return GenerationResult(
            prompt=prompt_str,
            prompt_token_ids=prompt_ids,
            generated_token_ids=generated_token_ids,
            text=generated_text,
            prompt_tokens=len(prompt_ids),
            generated_tokens=num_generated,
            total_tokens=len(prompt_ids) + num_generated,
            generation_time=elapsed,
            tokens_per_second=tps,
            stopped_on_eos=stopped_on_eos,
            stopped_reason=stopped_reason,
        )
