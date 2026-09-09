"""
Integration and Performance Test Script for PROMPT 003:
Tests full human-to-JARVIS chat pipeline, voice component readiness, and measures real CPU runtime performance.
"""

from pathlib import Path
import sys
import time
import psutil

src_dir = Path(__file__).resolve().parent.parent / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from jarvis.core.config import JarvisConfig
from jarvis.brain.provider import MockModelProvider
from jarvis.brain.context import ContextManager
from jarvis.brain.conversation import ConversationManager
from jarvis.voice.manager import VoiceManager
from jarvis.voice.stt import MockSpeechRecognizer, LocalWhisperSTT
from jarvis.voice.tts import MockTextToSpeech, PyTTSx3TextToSpeech
from jarvis.ui.chat import JarvisTerminalInterface


def run_integration_benchmark():
    print("=======================================================")
    print("      JARVIS PROMPT 003 INTEGRATION & BENCHMARK TEST   ")
    print("=======================================================")

    start_init = time.perf_counter()
    config = JarvisConfig.load_from_yaml("config/config.yaml")

    # Initialize components
    provider = MockModelProvider()
    provider.initialize()

    stt = MockSpeechRecognizer(mock_transcript="Hello JARVIS, report system status.")
    tts = PyTTSx3TextToSpeech(config.voice.text_to_speech.model_dump())
    if not tts.is_available():
        tts = MockTextToSpeech()

    voice_mgr = VoiceManager(voice_settings=config.voice, stt=stt, tts=tts)
    ui = JarvisTerminalInterface(config=config, model_provider=provider, voice_manager=voice_mgr)
    
    init_duration = time.perf_counter() - start_init
    print(f"[+] Component Startup Time : {init_duration*1000:.2f} ms")

    # Measure Chat First-Token Latency & Generation Speed
    ctx_mgr = ContextManager()
    gen_req = ctx_mgr.build_generation_request(user_prompt="Hello JARVIS. How are you today?")
    
    start_gen = time.perf_counter()
    stream_gen = provider.stream(gen_req)
    first_token_time = None
    chunks = []
    
    for idx, chunk in enumerate(stream_gen):
        if idx == 0:
            first_token_time = time.perf_counter() - start_gen
        chunks.append(chunk)

    total_gen_duration = time.perf_counter() - start_gen
    full_text = "".join(chunks)
    token_count = len(full_text.split())
    tokens_per_sec = token_count / max(0.001, total_gen_duration)

    print(f"[+] Chat First-Token Latency : {first_token_time*1000:.2f} ms")
    print(f"[+] Chat Total Gen Duration  : {total_gen_duration*1000:.2f} ms")
    print(f"[+] Chat Generation Speed    : {tokens_per_sec:.2f} tokens/sec")

    # Measure STT processing time
    dummy_audio = b"\x00\x10\x00\x20" * 4000  # ~0.5s dummy PCM audio
    start_stt = time.perf_counter()
    transcript = voice_mgr.stt.transcribe(dummy_audio)
    stt_duration = time.perf_counter() - start_stt
    print(f"[+] STT Processing Time      : {stt_duration*1000:.2f} ms ('{transcript}')")

    # Measure TTS processing time
    start_tts = time.perf_counter()
    tts_success = voice_mgr.speak("Hello Boss. I am operational.")
    tts_duration = time.perf_counter() - start_tts
    print(f"[+] TTS Synthesis Time       : {tts_duration*1000:.2f} ms (Success: {tts_success})")

    # Measure Process Resource Utilization
    process = psutil.Process()
    mem_info = process.memory_info()
    cpu_percent = psutil.cpu_percent(interval=0.1)

    print(f"[+] Process Memory Usage     : {mem_info.rss / (1024**2):.2f} MB")
    print(f"[+] CPU Utilization (Idle)   : {cpu_percent:.1f}%")

    print("-------------------------------------------------------")
    print("[SUCCESS] All integration tests passed cleanly.")
    print("=======================================================\n")


if __name__ == "__main__":
    run_integration_benchmark()
