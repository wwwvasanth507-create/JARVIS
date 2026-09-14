"""
Service Layer for MyLLM API Server.

Coordinates shared model lifecycle, session registry operations, synchronous
chat generation, Server-Sent Events (SSE) streaming, and JSON persistence.
"""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
import json
import logging
from pathlib import Path
from typing import Any, AsyncIterator, Dict, List, Optional, Union
import torch

from myllm.api.errors import ContextOverflowAPIError, InvalidRequestError
from myllm.api.models import (
    ChatResponseModel,
    DeleteSessionResponse,
    GenerationConfigOverride,
    MessageModel,
    ModelInfoResponse,
    SaveSessionResponse,
    SessionDetailResponse,
    SessionResponse,
    StreamTokenEvent,
    TelemetryModel,
)
from myllm.api.sessions import SessionHandle, SessionRegistry
from myllm.chat.session import ChatSession
from myllm.config import ServerConfig
from myllm.data.tokenizer_pipeline import compute_tokenizer_fingerprint
from myllm.inference.loader import load_inference_system
from myllm.inference.types import GenerationConfig
from myllm.model.gpt import GPTModel
from myllm.tokenizer import Tokenizer
from myllm.utils.device import resolve_device

logger = logging.getLogger(__name__)


def build_generation_config(
    base_config: GenerationConfig,
    override: Optional[GenerationConfigOverride] = None,
) -> GenerationConfig:
    """Apply request-specific overrides to a base GenerationConfig."""
    if override is None:
        return base_config

    return GenerationConfig(
        max_new_tokens=override.max_new_tokens if override.max_new_tokens is not None else base_config.max_new_tokens,
        temperature=override.temperature if override.temperature is not None else base_config.temperature,
        top_k=override.top_k if override.top_k is not None else base_config.top_k,
        top_p=override.top_p if override.top_p is not None else base_config.top_p,
        repetition_penalty=override.repetition_penalty if override.repetition_penalty is not None else base_config.repetition_penalty,
        do_sample=override.do_sample if override.do_sample is not None else base_config.do_sample,
        seed=override.seed if override.seed is not None else base_config.seed,
        use_cache=base_config.use_cache,
        stop_on_eos=base_config.stop_on_eos,
        eos_token_id=base_config.eos_token_id,
        pad_token_id=base_config.pad_token_id,
    )


class APIService:
    """
    Central API business logic coordinating model execution and session state.
    """

    def __init__(
        self,
        model: GPTModel,
        tokenizer: Tokenizer,
        config: ServerConfig,
        checkpoint_path: Optional[str] = None,
    ) -> None:
        self.device = resolve_device(config.device, strict_cpu=True)
        self.model = model.to(self.device)
        self.model.eval()
        self.tokenizer = tokenizer
        self.config = config
        self.checkpoint_path = checkpoint_path or config.checkpoint

        self.tokenizer_fingerprint = compute_tokenizer_fingerprint(self.tokenizer)
        self.parameter_count = sum(p.numel() for p in self.model.parameters())
        self.context_length = self.model.config.context_length
        self.vocab_size = self.model.config.vocab_size

        default_gen_cfg = GenerationConfig(
            max_new_tokens=min(config.max_new_tokens, 24),
            temperature=config.default_temperature,
            top_p=config.default_top_p,
            repetition_penalty=1.1,
            do_sample=True,  # Conversational sampling by default
            use_cache=True,
            stop_on_eos=True,
        )

        self.registry = SessionRegistry(
            model=self.model,
            tokenizer=self.tokenizer,
            max_sessions=config.max_sessions,
            checkpoint_path=self.checkpoint_path,
            default_config=default_gen_cfg,
        )

        # Concurrency control: thread pool and global inference lock for CPU execution
        self._inference_lock = asyncio.Lock()
        self._executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="myllm-api")

    @classmethod
    def create_from_config(cls, config: ServerConfig) -> APIService:
        """Factory initializing model, tokenizer, and service from ServerConfig."""
        logger.info(
            f"Loading checkpoint '{config.checkpoint}' and tokenizer '{config.tokenizer}' on CPU..."
        )
        model, tokenizer, payload = load_inference_system(
            checkpoint_path=config.checkpoint,
            tokenizer_path=config.tokenizer,
        )
        if tokenizer is None:
            raise ValueError(f"Failed to load tokenizer from {config.tokenizer}")

        return cls(
            model=model,
            tokenizer=tokenizer,
            config=config,
            checkpoint_path=config.checkpoint,
        )

    def get_model_info(self) -> ModelInfoResponse:
        """Return introspection metadata regarding the served model."""
        return ModelInfoResponse(
            model_name="MyLLM-GPT",
            checkpoint=str(self.checkpoint_path),
            parameter_count=self.parameter_count,
            context_length=self.context_length,
            vocab_size=self.vocab_size,
            tokenizer_fingerprint=self.tokenizer_fingerprint,
            device="cpu",
            kv_cache_supported=True,
        )

    async def create_session(
        self,
        system_prompt: Optional[str] = None,
        generation_config_override: Optional[GenerationConfigOverride] = None,
    ) -> SessionResponse:
        """Create a new conversational session."""
        base_cfg = self.registry.default_config
        cfg = build_generation_config(base_cfg, generation_config_override)

        handle = await self.registry.create_session(
            system_prompt=system_prompt,
            generation_config=cfg,
        )
        return SessionResponse(
            session_id=handle.session_id,
            created_at=handle.created_at,
            model="MyLLM-GPT",
            context_length=self.context_length,
            system_prompt=handle.system_prompt,
        )

    async def get_session(self, session_id: str) -> SessionDetailResponse:
        """Retrieve message history and metadata for a session."""
        handle = await self.registry.get_session(session_id)
        async with handle.lock:
            history_msgs = [
                MessageModel(role=m.role, content=m.content)
                for m in handle.engine.get_history()
            ]
            cfg_dict = {
                "max_new_tokens": handle.config.max_new_tokens,
                "temperature": handle.config.temperature,
                "top_k": handle.config.top_k,
                "top_p": handle.config.top_p,
                "repetition_penalty": handle.config.repetition_penalty,
                "do_sample": handle.config.do_sample,
                "seed": handle.config.seed,
                "use_cache": handle.config.use_cache,
            }
            return SessionDetailResponse(
                session_id=handle.session_id,
                system_prompt=handle.system_prompt,
                messages=history_msgs,
                generation_config=cfg_dict,
                created_at=handle.created_at,
                updated_at=handle.updated_at,
                model_checkpoint=self.checkpoint_path,
            )

    async def delete_session(self, session_id: str) -> DeleteSessionResponse:
        """Delete an active session and clear its KV cache."""
        await self.registry.delete_session(session_id)
        return DeleteSessionResponse(status="deleted", session_id=session_id)

    async def send_message(
        self,
        session_id: str,
        content: str,
        generation_config_override: Optional[GenerationConfigOverride] = None,
    ) -> ChatResponseModel:
        """Post a user message and generate assistant response synchronously."""
        handle = await self.registry.get_session(session_id)

        # Enforce maximum message length
        if len(content) > self.config.max_message_length:
            raise InvalidRequestError(
                f"Message length ({len(content)}) exceeds maximum allowed ({self.config.max_message_length})."
            )

        gen_cfg = build_generation_config(handle.config, generation_config_override)

        # Protect session state and CPU inference execution
        async with handle.lock:
            handle.engine.send_user_message(content)
            handle.touch()

            loop = asyncio.get_running_loop()
            async with self._inference_lock:
                try:
                    response = await loop.run_in_executor(
                        self._executor,
                        handle.engine.generate_response,
                        gen_cfg,
                    )
                except Exception as e:
                    logger.error(f"Inference execution failed: {e}")
                    raise InvalidRequestError(f"Generation failed: {str(e)}") from e

            handle.touch()
            return ChatResponseModel(
                message=MessageModel(role=response.message.role, content=response.message.content),
                telemetry=TelemetryModel(
                    prompt_tokens=response.telemetry.prompt_tokens,
                    generated_tokens=response.telemetry.generated_tokens,
                    total_tokens=response.telemetry.total_tokens,
                    tokens_per_second=response.telemetry.tokens_per_second,
                    generation_latency=response.telemetry.generation_latency,
                    stop_reason=response.telemetry.stop_reason,
                    context_truncated=response.telemetry.context_truncated,
                    removed_messages=response.telemetry.removed_messages,
                ),
            )

    async def stream_message(
        self,
        session_id: str,
        content: str,
        generation_config_override: Optional[GenerationConfigOverride] = None,
    ) -> AsyncIterator[str]:
        """Post a user message and stream assistant response via Server-Sent Events (SSE)."""
        handle = await self.registry.get_session(session_id)

        if len(content) > self.config.max_message_length:
            raise InvalidRequestError(
                f"Message length ({len(content)}) exceeds maximum allowed ({self.config.max_message_length})."
            )

        gen_cfg = build_generation_config(handle.config, generation_config_override)

        async with handle.lock:
            handle.engine.send_user_message(content)
            handle.touch()

            # Execute generator in worker thread and feed queue for async consumption
            queue: asyncio.Queue[Optional[StreamTokenEvent]] = asyncio.Queue()
            loop = asyncio.get_running_loop()

            def run_sync_stream():
                try:
                    for tok in handle.engine.stream_response(config=gen_cfg):
                        event = StreamTokenEvent(
                            token=tok.text,
                            finished=tok.finished,
                            stop_reason=tok.stop_reason,
                        )
                        loop.call_soon_threadsafe(queue.put_nowait, event)
                except Exception as exc:
                    logger.error(f"Streaming error: {exc}")
                    err_event = StreamTokenEvent(token="", finished=True, stop_reason="error")
                    loop.call_soon_threadsafe(queue.put_nowait, err_event)
                finally:
                    loop.call_soon_threadsafe(queue.put_nowait, None)

            async with self._inference_lock:
                stream_task = asyncio.create_task(asyncio.to_thread(run_sync_stream))

                while True:
                    event = await queue.get()
                    if event is None:
                        break
                    # Format as SSE event: data: {json}\n\n
                    data_str = json.dumps(event.model_dump(), ensure_ascii=False)
                    yield f"data: {data_str}\n\n"

                await stream_task

            handle.touch()

    async def save_session(self, session_id: str, target_path: str) -> SaveSessionResponse:
        """Explicitly persist a session state to a JSON file."""
        handle = await self.registry.get_session(session_id)
        async with handle.lock:
            session_obj = handle.engine.create_session()
            saved_path = session_obj.save_json(target_path)
            logger.info(f"Saved session '{session_id}' to '{saved_path}'")
            return SaveSessionResponse(
                status="saved",
                session_id=session_id,
                path=str(saved_path),
            )
