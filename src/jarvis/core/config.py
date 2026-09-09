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


class SpeechToTextSettings(BaseModel):
    enabled: bool = True
    engine: str = "whisper"
    model: str = "tiny"
    language: str = "auto"
    device: str = "cpu"
    compute_type: str = "int8"


class TextToSpeechSettings(BaseModel):
    enabled: bool = True
    engine: str = "pyttsx3"
    voice: str = "auto"
    speed: float = 1.0
    volume: float = 1.0
    streaming: bool = True


class AudioSettings(BaseModel):
    input_device: str = "default"
    output_device: str = "default"
    sample_rate: int = 16000
    channels: int = 1
    chunk_size: int = 1024
    vad_energy_threshold: int = 300
    vad_silence_duration: float = 1.5


class VoiceSettings(BaseModel):
    mode: str = "hybrid"
    push_to_talk: bool = True
    push_to_talk_key: str = "space"
    speech_to_text: SpeechToTextSettings = Field(default_factory=SpeechToTextSettings)
    text_to_speech: TextToSpeechSettings = Field(default_factory=TextToSpeechSettings)
    audio: AudioSettings = Field(default_factory=AudioSettings)


class JarvisConfig(BaseModel):
    system: SystemSettings = Field(default_factory=SystemSettings)
    model_provider: ModelProviderSettings = Field(default_factory=ModelProviderSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    voice: VoiceSettings = Field(default_factory=VoiceSettings)
    raw_config: Dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def load_from_yaml(cls, config_path: str | Path) -> "JarvisConfig":
        path = Path(config_path)
        if not path.is_absolute():
            path = path.resolve()
        
        if not path.exists():
            return cls()

        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        system_data = data.get("system", {})
        model_data = data.get("model_provider", {})
        security_data = data.get("security", {})

        # Load voice config if config/voice.yaml exists alongside
        voice_path = path.parent / "voice.yaml"
        voice_data = {}
        if voice_path.exists():
            with open(voice_path, "r", encoding="utf-8") as vf:
                voice_data = yaml.safe_load(vf) or {}

        return cls(
            system=SystemSettings(**system_data),
            model_provider=ModelProviderSettings(**model_data),
            security=SecuritySettings(**security_data),
            voice=VoiceSettings(
                mode=voice_data.get("mode", "hybrid"),
                push_to_talk=voice_data.get("push_to_talk", True),
                push_to_talk_key=voice_data.get("push_to_talk_key", "space"),
                speech_to_text=SpeechToTextSettings(**voice_data.get("speech_to_text", {})),
                text_to_speech=TextToSpeechSettings(**voice_data.get("text_to_speech", {})),
                audio=AudioSettings(**voice_data.get("audio", {})),
            ),
            raw_config=data,
        )

