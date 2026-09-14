"""
FastAPI Application and Route Handlers for MyLLM Server (Phase 9).

Provides REST and Server-Sent Events (SSE) streaming endpoints for model introspection,
session lifecycle, multi-turn chat generation, and explicit session persistence.
"""

from __future__ import annotations

import logging
from typing import Optional
from fastapi import Depends, FastAPI, status
from fastapi.responses import StreamingResponse

from myllm.api.dependencies import get_api_service
from myllm.api.errors import register_error_handlers
from myllm.api.models import (
    ChatResponseModel,
    CreateSessionRequest,
    DeleteSessionResponse,
    HealthResponse,
    ModelInfoResponse,
    SaveSessionRequest,
    SaveSessionResponse,
    SendMessageRequest,
    SessionDetailResponse,
    SessionResponse,
)
from myllm.api.service import APIService
from myllm.config import ServerConfig

logger = logging.getLogger(__name__)


def create_app(
    service: Optional[APIService] = None,
    config: Optional[ServerConfig] = None,
) -> FastAPI:
    """
    Application factory constructing the FastAPI instance.

    Args:
        service: Optional pre-configured APIService instance.
        config: Optional ServerConfig (used if service is omitted).

    Returns:
        Configured FastAPI application with registered routes and error handlers.
    """
    app = FastAPI(
        title="MyLLM Local API",
        version="1.0.0",
        description=(
            "Local CPU-only API server for MyLLM GPT language model. "
            "Provides endpoints for model metadata, stateful multi-turn chat sessions, "
            "synchronous response generation, real-time Server-Sent Events (SSE) streaming, "
            "and explicit JSON session persistence."
        ),
        docs_url="/docs",
        redoc_url=None,
        openapi_url="/openapi.json",
    )

    # Register error handlers
    register_error_handlers(app)

    # Initialize or assign service
    if service is not None:
        app.state.api_service = service
    elif config is not None:
        app.state.api_service = APIService.create_from_config(config)
    else:
        cfg = ServerConfig()
        app.state.api_service = APIService.create_from_config(cfg)

    # ================= Routes =================

    @app.get(
        "/health",
        response_model=HealthResponse,
        tags=["System"],
        summary="Service Health Check",
        description="Returns service availability and execution device without running model inference.",
    )
    async def health() -> HealthResponse:
        return HealthResponse(status="ok", service="MyLLM", device="cpu")

    @app.get(
        "/v1/model",
        response_model=ModelInfoResponse,
        tags=["Model"],
        summary="Model Information",
        description="Returns architecture dimensions, parameter count, context length, and tokenizer fingerprint.",
    )
    async def get_model_info(
        service: APIService = Depends(get_api_service),
    ) -> ModelInfoResponse:
        return service.get_model_info()

    @app.post(
        "/v1/sessions",
        response_model=SessionResponse,
        status_code=status.HTTP_201_CREATED,
        tags=["Sessions"],
        summary="Create Chat Session",
        description="Initializes a new stateful conversational session with an isolated KV cache.",
    )
    async def create_session(
        request: CreateSessionRequest,
        service: APIService = Depends(get_api_service),
    ) -> SessionResponse:
        return await service.create_session(
            system_prompt=request.system_prompt,
            generation_config_override=request.generation_config,
        )

    @app.get(
        "/v1/sessions/{session_id}",
        response_model=SessionDetailResponse,
        tags=["Sessions"],
        summary="Get Session Details",
        description="Retrieves message history, system prompt, and configuration for an active session.",
    )
    async def get_session(
        session_id: str,
        service: APIService = Depends(get_api_service),
    ) -> SessionDetailResponse:
        return await service.get_session(session_id)

    @app.delete(
        "/v1/sessions/{session_id}",
        response_model=DeleteSessionResponse,
        tags=["Sessions"],
        summary="Delete Chat Session",
        description="Deletes an active session and clears its associated conversational history and KV cache.",
    )
    async def delete_session(
        session_id: str,
        service: APIService = Depends(get_api_service),
    ) -> DeleteSessionResponse:
        return await service.delete_session(session_id)

    @app.post(
        "/v1/sessions/{session_id}/messages",
        response_model=ChatResponseModel,
        tags=["Chat"],
        summary="Send Chat Message (Synchronous)",
        description="Appends a user message and generates the complete assistant response synchronously.",
    )
    async def send_message(
        session_id: str,
        request: SendMessageRequest,
        service: APIService = Depends(get_api_service),
    ) -> ChatResponseModel:
        return await service.send_message(
            session_id=session_id,
            content=request.content,
            generation_config_override=request.generation_config,
        )

    @app.post(
        "/v1/sessions/{session_id}/messages/stream",
        tags=["Chat"],
        summary="Send Chat Message (Streaming SSE)",
        description="Appends a user message and streams assistant tokens in real time via Server-Sent Events (SSE).",
        response_class=StreamingResponse,
    )
    async def stream_message(
        session_id: str,
        request: SendMessageRequest,
        service: APIService = Depends(get_api_service),
    ) -> StreamingResponse:
        generator = service.stream_message(
            session_id=session_id,
            content=request.content,
            generation_config_override=request.generation_config,
        )
        return StreamingResponse(
            generator,
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    @app.post(
        "/v1/sessions/{session_id}/save",
        response_model=SaveSessionResponse,
        tags=["Sessions"],
        summary="Explicitly Persist Session",
        description="Saves current session state and conversational history to a target JSON file on disk.",
    )
    async def save_session(
        session_id: str,
        request: SaveSessionRequest,
        service: APIService = Depends(get_api_service),
    ) -> SaveSessionResponse:
        return await service.save_session(
            session_id=session_id,
            target_path=request.path,
        )

    return app
