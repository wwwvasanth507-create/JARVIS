"""
Audio Input and Output Device Discovery and Hardware Abstraction for JARVIS.
Handles microphone and speaker enumeration, recording, playback, and resource release.
"""

from typing import List, Optional
from pydantic import BaseModel
import logging
import time

logger = logging.getLogger("jarvis.voice.audio_device")


class AudioDeviceInfo(BaseModel):
    id: int
    name: str
    max_input_channels: int = 0
    max_output_channels: int = 0
    default_sample_rate: int = 16000
    is_default: bool = False


class AudioDeviceDiscovery:
    """Discovers available audio input (microphones) and output (speakers) hardware devices."""

    @staticmethod
    def list_microphones() -> List[AudioDeviceInfo]:
        devices: List[AudioDeviceInfo] = []
        try:
            import sounddevice as sd
            dev_list = sd.query_devices()
            default_input = sd.default.device[0] if sd.default.device else -1
            for idx, dev in enumerate(dev_list):
                if dev.get("max_input_channels", 0) > 0:
                    devices.append(
                        AudioDeviceInfo(
                            id=idx,
                            name=dev.get("name", f"Microphone {idx}"),
                            max_input_channels=dev.get("max_input_channels", 0),
                            max_output_channels=dev.get("max_output_channels", 0),
                            default_sample_rate=int(dev.get("default_samplerate", 16000)),
                            is_default=(idx == default_input),
                        )
                    )
        except Exception as e:
            logger.warning(f"Audio input discovery degraded: {e}")
            # Fallback mock default device
            devices.append(
                AudioDeviceInfo(
                    id=0,
                    name="Default System Microphone",
                    max_input_channels=1,
                    max_output_channels=0,
                    default_sample_rate=16000,
                    is_default=True,
                )
            )
        return devices

    @staticmethod
    def list_speakers() -> List[AudioDeviceInfo]:
        devices: List[AudioDeviceInfo] = []
        try:
            import sounddevice as sd
            dev_list = sd.query_devices()
            default_output = sd.default.device[1] if sd.default.device else -1
            for idx, dev in enumerate(dev_list):
                if dev.get("max_output_channels", 0) > 0:
                    devices.append(
                        AudioDeviceInfo(
                            id=idx,
                            name=dev.get("name", f"Speaker {idx}"),
                            max_input_channels=dev.get("max_input_channels", 0),
                            max_output_channels=dev.get("max_output_channels", 0),
                            default_sample_rate=int(dev.get("default_samplerate", 44100)),
                            is_default=(idx == default_output),
                        )
                    )
        except Exception as e:
            logger.warning(f"Audio output discovery degraded: {e}")
            devices.append(
                AudioDeviceInfo(
                    id=0,
                    name="Default System Speaker",
                    max_input_channels=0,
                    max_output_channels=2,
                    default_sample_rate=44100,
                    is_default=True,
                )
            )
        return devices

    @classmethod
    def get_default_microphone(cls) -> Optional[AudioDeviceInfo]:
        mics = cls.list_microphones()
        for m in mics:
            if m.is_default:
                return m
        return mics[0] if mics else None

    @classmethod
    def get_default_speaker(cls) -> Optional[AudioDeviceInfo]:
        speakers = cls.list_speakers()
        for s in speakers:
            if s.is_default:
                return s
        return speakers[0] if speakers else None


class AudioInputManager:
    """Manages audio recording from microphone and prompt resource cleanup."""

    def __init__(self, sample_rate: int = 16000, channels: int = 1, device_id: Optional[int] = None):
        self.sample_rate = sample_rate
        self.channels = channels
        self.device_id = device_id
        self._is_recording = False

    def record_seconds(self, duration_seconds: float = 3.0) -> bytes:
        """Records raw PCM audio data for a given duration."""
        logger.info(f"VOICE_INPUT_STARTED: Recording for {duration_seconds} seconds")
        self._is_recording = True
        try:
            import sounddevice as sd
            import numpy as np

            recording = sd.rec(
                int(duration_seconds * self.sample_rate),
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype="int16",
                device=self.device_id,
            )
            sd.wait()
            self._is_recording = False
            logger.info("VOICE_INPUT_COMPLETED")
            return recording.tobytes()
        except Exception as e:
            self._is_recording = False
            logger.error(f"VOICE_ERROR: Audio recording failed ({e})")
            return b""

    def release(self) -> None:
        """Releases audio hardware resources."""
        self._is_recording = False


class AudioOutputManager:
    """Manages audio playback to speakers with cancellation/stop support."""

    def __init__(self, device_id: Optional[int] = None):
        self.device_id = device_id
        self._is_playing = False

    def play_pcm(self, pcm_bytes: bytes, sample_rate: int = 16000) -> bool:
        """Plays raw PCM audio data."""
        if not pcm_bytes:
            return False
        self._is_playing = True
        try:
            import sounddevice as sd
            import numpy as np

            audio_array = np.frombuffer(pcm_bytes, dtype=np.int16)
            sd.play(audio_array, samplerate=sample_rate, device=self.device_id)
            sd.wait()
            self._is_playing = False
            return True
        except Exception as e:
            self._is_playing = False
            logger.error(f"VOICE_ERROR: Audio playback failed ({e})")
            return False

    def stop(self) -> None:
        """Stops ongoing playback immediately."""
        try:
            import sounddevice as sd
            sd.stop()
        except Exception:
            pass
        self._is_playing = False
