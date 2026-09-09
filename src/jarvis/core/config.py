"""
Core bootstrap and configuration module for JARVIS.
"""

from pathlib import Path
from typing import Any, Dict, Optional
import yaml
from pydantic import BaseModel, Field


class SystemSettings(BaseModel):
    name: str = "JARVIS"
    version: str = "0.1.0"
    environment: str = "development"
    user_alias: str = "Boss"
    local_first: bool = True
    allow_external_apis: bool = False


class ModelProviderSettings(BaseModel):
    type: str = "llama_cpp"
    model_path: str = "models/gguf/model-Q4_K_M.gguf"
    context_size: int = 2048
    temperature: float = 0.2
    n_threads: int = 4
    n_gpu_layers: int = 0


class SecuritySettings(BaseModel):
    permissions_file: str = "config/permissions.yaml"
    require_confirmation_above_risk: str = "MEDIUM"
    audit_logging: bool = True


class JarvisConfig(BaseModel):
    system: SystemSettings = Field(default_factory=SystemSettings)
    model_provider: ModelProviderSettings = Field(default_factory=ModelProviderSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    raw_config: Dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def load_from_yaml(cls, config_path: str | Path) -> "JarvisConfig":
        path = Path(config_path)
        if not path.is_absolute():
            # Resolve relative to project root (assuming standard execution)
            path = path.resolve()
        
        if not path.exists():
            return cls()

        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        system_data = data.get("system", {})
        model_data = data.get("model_provider", {})
        security_data = data.get("security", {})

        return cls(
            system=SystemSettings(**system_data),
            model_provider=ModelProviderSettings(**model_data),
            security=SecuritySettings(**security_data),
            raw_config=data,
        )
