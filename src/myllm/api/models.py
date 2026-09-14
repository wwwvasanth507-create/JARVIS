"""
Pydantic Request and Response Models for MyLLM API Server.

Defines validated schemas for health, model introspection, sessions, messages,
streaming events, and structured error payloads.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class HealthResponse(BaseModel):
    """Health check status response."""
    status: str = "ok"
    service: str = "MyLLM"
    device: str = "cpu"


class ReadyResponse(BaseModel):
    """Readiness check status response verifying model availability."""
    status: str = "ready"
    ready: bool = True
    model_loaded: bool = True
    parameter_count: int
    context_length: int
    device: str = "cpu"



class ModelInfoResponse(BaseModel):
    """Model architecture and checkpoint metadata response."""
    model_name: str
    checkpoint: str
    parameter_count: int
    context_length: int
    vocab_size: int
    tokenizer_fingerprint: str
    device: str = "cpu"
    kv_cache_supported: bool = True


class GenerationConfigOverride(BaseModel):
    """Optional per-request generation parameters."""
    max_new_tokens: Optional[int] = Field(default=None, ge=1, le=512)
    temperature: Optional[float] = Field(default=None, gt=0.0, le=5.0)
    top_k: Optional[int] = Field(default=None, ge=0)
    top_p: Optional[float] = Field(default=None, gt=0.0, le=1.0)
    repetition_penalty: Optional[float] = Field(default=None, gt=0.0, le=5.0)
    do_sample: Optional[bool] = None
    seed: Optional[int] = None


class CreateSessionRequest(BaseModel):
    """Request payload for session creation."""
    system_prompt: Optional[str] = None
    generation_config: Optional[GenerationConfigOverride] = None


class SessionResponse(BaseModel):
    """Response payload upon session creation."""
    session_id: str
    created_at: str
    model: str
    context_length: int
    system_prompt: Optional[str] = None


class MessageModel(BaseModel):
    """Message item schema."""
    role: str
    content: str

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        norm = v.strip().lower()
        if norm not in {"system", "user", "assistant"}:
            raise ValueError(f"Invalid role '{v}'. Supported roles: 'system', 'user', 'assistant'.")
        return norm


class SessionDetailResponse(BaseModel):
    """Detailed session inspection response."""
    session_id: str
    system_prompt: Optional[str] = None
    messages: List[MessageModel] = []
    generation_config: Dict[str, Any] = {}
    created_at: str
    updated_at: str
    model_checkpoint: Optional[str] = None


class DeleteSessionResponse(BaseModel):
    """Response payload for session deletion."""
    status: str = "deleted"
    session_id: str


class SendMessageRequest(BaseModel):
    """Request payload to post a user message."""
    content: str = Field(..., min_length=1, max_length=16384)
    generation_config: Optional[GenerationConfigOverride] = None

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Message content cannot be empty or whitespace only.")
        return stripped


class TelemetryModel(BaseModel):
    """Runtime performance metrics for generation."""
    prompt_tokens: int
    generated_tokens: int
    total_tokens: int
    tokens_per_second: float
    generation_latency: float
    stop_reason: str
    context_truncated: bool
    removed_messages: int


class ChatResponseModel(BaseModel):
    """Synchronous chat response container."""
    message: MessageModel
    telemetry: TelemetryModel


class StreamTokenEvent(BaseModel):
    """Payload emitted during Server-Sent Event (SSE) streaming."""
    token: str
    finished: bool
    stop_reason: Optional[str] = None


class SaveSessionRequest(BaseModel):
    """Request payload to explicitly persist session state."""
    path: str = Field(..., min_length=1)


class SaveSessionResponse(BaseModel):
    """Response payload upon successful session persistence."""
    status: str = "saved"
    session_id: str
    path: str


class ErrorDetail(BaseModel):
    """Structured error descriptor."""
    code: str
    message: str


class ErrorResponse(BaseModel):
    """Standardized API error response body."""
    error: ErrorDetail
