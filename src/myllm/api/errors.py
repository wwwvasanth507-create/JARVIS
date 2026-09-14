"""
API Error Handling and Structured Exception Handlers for MyLLM Server.

Defines domain-specific API exceptions and registers FastAPI exception handlers
to return standardized JSON error bodies without leaking tracebacks.
"""

from __future__ import annotations

import logging
from typing import Any
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


class APIError(Exception):
    """Base class for all application API errors."""
    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


class SessionNotFoundError(APIError):
    """Raised when a requested session ID does not exist."""
    def __init__(self, session_id: str) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code="SESSION_NOT_FOUND",
            message=f"Session '{session_id}' not found.",
        )


class MaxSessionsExceededError(APIError):
    """Raised when active session registry exceeds capacity."""
    def __init__(self, max_sessions: int) -> None:
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            code="MAX_SESSIONS_EXCEEDED",
            message=f"Maximum active sessions ({max_sessions}) exceeded. Please delete unused sessions.",
        )


class InvalidRequestError(APIError):
    """Raised on bad request parameters."""
    def __init__(self, message: str) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="INVALID_REQUEST",
            message=message,
        )


class ContextOverflowAPIError(APIError):
    """Raised when a prompt exceeds model context length without room for generation."""
    def __init__(self, message: str) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="CONTEXT_OVERFLOW",
            message=message,
        )


def register_error_handlers(app: FastAPI) -> None:
    """Register custom exception handlers on the FastAPI application."""

    @app.exception_handler(APIError)
    async def handle_api_error(request: Request, exc: APIError) -> JSONResponse:
        logger.warning(f"API Error [{exc.code}]: {exc.message} on {request.url.path}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                }
            },
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        error_msgs = []
        for err in exc.errors():
            loc = ".".join(str(item) for item in err.get("loc", []))
            msg = err.get("msg", "Invalid value")
            error_msgs.append(f"{loc}: {msg}" if loc else msg)
        combined = "; ".join(error_msgs)
        logger.warning(f"Validation Error on {request.url.path}: {combined}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": f"Invalid request body: {combined}",
                }
            },
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        code_map = {
            404: "NOT_FOUND",
            405: "METHOD_NOT_ALLOWED",
            413: "REQUEST_ENTITY_TOO_LARGE",
        }
        code = code_map.get(exc.status_code, "HTTP_ERROR")
        logger.warning(f"HTTP {exc.status_code} [{code}] on {request.url.path}: {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": code,
                    "message": str(exc.detail),
                }
            },
        )

    @app.exception_handler(Exception)
    async def handle_generic_exception(request: Request, exc: Exception) -> JSONResponse:
        logger.exception(f"Unhandled server error on {request.url.path}: {exc}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected server error occurred. Please consult server logs.",
                }
            },
        )
