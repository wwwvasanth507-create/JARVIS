"""
MyLLM Local API Package (Phase 9).

Exports application factory, service layer, session registry, and schemas.
"""

from myllm.api.app import create_app
from myllm.api.errors import (
    APIError,
    ContextOverflowAPIError,
    InvalidRequestError,
    MaxSessionsExceededError,
    SessionNotFoundError,
)
from myllm.api.models import (
    ChatResponseModel,
    CreateSessionRequest,
    DeleteSessionResponse,
    ErrorDetail,
    ErrorResponse,
    GenerationConfigOverride,
    HealthResponse,
    ReadyResponse,
    MessageModel,
    ModelInfoResponse,
    SaveSessionRequest,
    SaveSessionResponse,
    SendMessageRequest,
    SessionDetailResponse,
    SessionResponse,
    StreamTokenEvent,
    TelemetryModel,
)
from myllm.api.service import APIService
from myllm.api.sessions import SessionHandle, SessionRegistry

__all__ = [
    "create_app",
    "APIService",
    "SessionRegistry",
    "SessionHandle",
    "APIError",
    "SessionNotFoundError",
    "MaxSessionsExceededError",
    "InvalidRequestError",
    "ContextOverflowAPIError",
    "HealthResponse",
    "ReadyResponse",
    "ModelInfoResponse",
    "CreateSessionRequest",
    "SessionResponse",
    "MessageModel",
    "SessionDetailResponse",
    "DeleteSessionResponse",
    "SendMessageRequest",
    "TelemetryModel",
    "ChatResponseModel",
    "StreamTokenEvent",
    "SaveSessionRequest",
    "SaveSessionResponse",
    "ErrorDetail",
    "ErrorResponse",
    "GenerationConfigOverride",
]
