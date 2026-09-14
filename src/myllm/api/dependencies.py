"""
FastAPI Dependency Injection for MyLLM Server.

Allows endpoints to inject the initialized APIService instance.
"""

from __future__ import annotations

from typing import Optional
from fastapi import Depends, Request
from myllm.api.service import APIService


def get_api_service(request: Request) -> APIService:
    """Dependency provider extracting APIService from app state."""
    service: Optional[APIService] = getattr(request.app.state, "api_service", None)
    if service is None:
        raise RuntimeError("APIService has not been initialized in application state.")
    return service
