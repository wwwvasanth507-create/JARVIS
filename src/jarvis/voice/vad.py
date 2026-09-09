"""
Voice Activity Detection (VAD) Subsystem for JARVIS.
CPU-friendly energy thresholding and lightweight speech frame detection.
"""

from typing import List, Optional
import math
import struct
import logging

logger = logging.getLogger("jarvis.voice.vad")


class VoiceActivityDetector:
    """
    Lightweight Voice Activity Detector for CPU-only systems.
    Computes RMS audio energy level to avoid running heavy STT models continuously when idle.
    """

    def __init__(self, energy_threshold: int = 300, silence_duration_seconds: float = 1.5):
        self.energy_threshold = energy_threshold
        self.silence_duration_seconds = silence_duration_seconds

    @staticmethod
    def calculate_rms(pcm_data: bytes) -> float:
        """Calculates Root Mean Square (RMS) energy level of 16-bit PCM audio samples."""
        if not pcm_data:
            return 0.0
        count = len(pcm_data) // 2
        if count == 0:
            return 0.0
        
        format_str = f"<{count}h"
        try:
            samples = struct.unpack(format_str, pcm_data[: count * 2])
            sum_squares = sum(s * s for s in samples)
            rms = math.sqrt(sum_squares / count)
            return rms
        except Exception:
            return 0.0

    def is_speech(self, pcm_data: bytes) -> bool:
        """Determines if the given audio chunk contains speech based on energy threshold."""
        rms = self.calculate_rms(pcm_data)
        return rms >= self.energy_threshold

    def filter_silence(self, chunks: List[bytes]) -> List[bytes]:
        """Returns non-silent audio chunks from a sequence of recorded chunks."""
        return [chunk for chunk in chunks if self.is_speech(chunk)]
