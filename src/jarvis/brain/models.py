"""
Data models for JARVIS local model runtime.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class PerformanceMode(str, Enum):
    AUTO = "AUTO"
    BATTERY_SAVER = "BATTERY_SAVER"
    BALANCED = "BALANCED"
    PERFORMANCE = "PERFORMANCE"


class HardwareProfile(str, Enum):
    ULTRA_LOW = "ULTRA_LOW"         # < 8GB RAM, 2-4 cores
    LOW = "LOW"                     # 8GB RAM, 4 cores
    MEDIUM = "MEDIUM"               # 16GB RAM, 6-8 cores
    HIGH = "HIGH"                   # 32GB+ RAM, 8+ cores
    GPU_ACCELERATED = "GPU_ACCELERATED"


class ChatMessage(BaseModel):
    role: str = Field(..., description="Role: system, user, assistant, tool")
    content: str = Field(..., description="Text content")
    name: Optional[str] = None


class GenerationRequest(BaseModel):
    messages: List[ChatMessage] = Field(default_factory=list)
    prompt: Optional[str] = None
    system_prompt: Optional[str] = None
    temperature: float = 0.2
    top_p: float = 0.9
    top_k: int = 40
    repeat_penalty: float = 1.1
    max_tokens: int = 512
    stop_sequences: List[str] = Field(default_factory=list)
    stream: bool = False
    seed: Optional[int] = None


class GenerationResponse(BaseModel):
    text: str
    finish_reason: str = "stop"
    tokens_generated: int = 0
    duration_seconds: float = 0.0
    tokens_per_second: float = 0.0
    model_name: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None


class ModelInfo(BaseModel):
    name: str
    path: str
    format: str = "GGUF"
    size_bytes: int = 0
    size_mb: float = 0.0
    context_size: int = 2048
    quantization: str = "Unknown"
    backend: str = "llama_cpp"
    available: bool = True
    loaded: bool = False

    def __getitem__(self, item: str) -> Any:
        return getattr(self, item)



class ModelHealth(BaseModel):
    available: bool
    loaded: bool
    backend: str
    model: str
    context_size: int
    threads: int
    gpu_layers: int
    memory_estimate_mb: float
    last_error: Optional[str] = None
