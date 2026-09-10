"""
Model Health Check Subsystem for JARVIS.
"""

from typing import Optional
from pydantic import BaseModel, Field
from jarvis.brain.provider import ModelProvider, GenerationRequest


class ModelHealthCheckResult(BaseModel):
    model_exists: bool
    can_load: bool
    can_generate: bool
    can_unload: bool
    latency_ms: float = 0.0
    error: Optional[str] = None


class ModelHealthCheck:
    """Runs a non-destructive health check on a ModelProvider instance."""

    @staticmethod
    def run_check(provider: ModelProvider) -> ModelHealthCheckResult:
        import time

        model_exists = provider.is_available()
        if not model_exists:
            return ModelHealthCheckResult(
                model_exists=False,
                can_load=False,
                can_generate=False,
                can_unload=False,
                error="Model binary missing or unavailable.",
            )

        start = time.perf_counter()
        can_load = False
        can_generate = False
        can_unload = False
        err_msg = None

        try:
            # Check 1: Load
            can_load = provider.initialize()

            # Check 2: Generate
            req = GenerationRequest(prompt="Hello", max_tokens=10)
            resp = provider.generate(req)
            can_generate = bool(resp and resp.text)

            # Check 3: Unload
            can_unload = provider.unload()
        except Exception as e:
            err_msg = str(e)

        elapsed_ms = (time.perf_counter() - start) * 1000.0

        return ModelHealthCheckResult(
            model_exists=model_exists,
            can_load=can_load,
            can_generate=can_generate,
            can_unload=can_unload,
            latency_ms=round(elapsed_ms, 2),
            error=err_msg,
        )


ModelHealthChecker = ModelHealthCheck

