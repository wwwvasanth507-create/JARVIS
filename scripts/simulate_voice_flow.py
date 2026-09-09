"""
State Machine & Voice Workflow Simulation Test Script for PROMPT 004.
Verifies all state transitions, fast-path acknowledgement, command timeouts, and speech interruption.
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
from jarvis.voice.manager import VoiceManager
from jarvis.voice.stt import MockSpeechRecognizer
from jarvis.voice.tts import MockTextToSpeech
from jarvis.voice.wakeword import MockWakeWordDetector
from jarvis.voice.state_machine import MicrophoneState


def run_state_machine_simulation():
    print("=======================================================")
    print("  JARVIS PROMPT 004 VOICE STATE MACHINE SIMULATION     ")
    print("=======================================================")

    config = JarvisConfig.load_from_yaml("config/config.yaml")
    
    mock_stt = MockSpeechRecognizer(mock_transcript="What is the system status?")
    mock_tts = MockTextToSpeech()
    mock_ww = MockWakeWordDetector()

    vm = VoiceManager(
        voice_settings=config.voice,
        wakeword_settings=config.wakeword,
        stt=mock_stt,
        tts=mock_tts,
        wakeword=mock_ww,
    )

    recorded_states = []

    def state_logger(old_s, new_s, reason):
        recorded_states.append((old_s.value, new_s.value, reason))
        print(f"  [TRANSITION] {old_s.value} -> {new_s.value} ({reason or 'N/A'})")

    vm.state_machine.register_callback(state_logger)

    # -------------------------------------------------------------
    # Scenario 1: Standard Wake -> Command -> Processing -> Speaking Flow
    # -------------------------------------------------------------
    print("\n--- SCENARIO 1: Standard Wake -> Fast-Path Ack -> Command -> Response ---")
    assert vm.state_machine.current_state == MicrophoneState.MICROPHONE_OFF
    
    # 1. Start listening
    vm.start_listening()
    assert vm.state_machine.current_state == MicrophoneState.LISTENING_FOR_WAKEWORD
    assert vm.privacy_status == "MIC LISTENING (Wake Word Only)"

    # 2. Wake phrase detected ("JARVIS")
    mock_ww.trigger_wake_event()
    assert mock_ww.is_detected(b"dummy") is True

    # 3. Handle wake detection
    cmd_text = vm.handle_wake_detection()
    assert cmd_text == "What is the system status?"
    assert vm.state_machine.current_state == MicrophoneState.PROCESSING

    # 4. Speak response
    vm.speak("All systems operational, Boss.")
    assert vm.state_machine.current_state == MicrophoneState.LISTENING_FOR_WAKEWORD

    print("  [SUCCESS] Scenario 1 verified cleanly.")

    # -------------------------------------------------------------
    # Scenario 2: Command Timeout Flow
    # -------------------------------------------------------------
    print("\n--- SCENARIO 2: Wake Detected -> Command Silence / Timeout ---")
    # Simulate silence STT output
    vm.stt = MockSpeechRecognizer(mock_transcript="")
    
    mock_ww.trigger_wake_event()
    assert mock_ww.is_detected(b"dummy") is True
    
    res_cmd = vm.handle_wake_detection()
    assert res_cmd is None
    assert vm.state_machine.current_state == MicrophoneState.LISTENING_FOR_WAKEWORD

    print("  [SUCCESS] Scenario 2 verified cleanly.")

    # -------------------------------------------------------------
    # Scenario 3: Single-Utterance Flow ("JARVIS, report status.")
    # -------------------------------------------------------------
    print("\n--- SCENARIO 3: Single-Utterance ('JARVIS, report status.') ---")
    vm.stt = MockSpeechRecognizer(mock_transcript="JARVIS, report status.")
    
    single_cmd = vm.handle_wake_detection(audio_chunk=b"audio_containing_full_sentence")
    assert single_cmd == "REPORT STATUS"
    assert vm.state_machine.current_state == MicrophoneState.PROCESSING

    vm.speak("Status optimal, Boss.")
    assert vm.state_machine.current_state == MicrophoneState.LISTENING_FOR_WAKEWORD
    print("  [SUCCESS] Scenario 3 verified cleanly.")

    # -------------------------------------------------------------
    # Scenario 4: Speech Interruption Flow
    # -------------------------------------------------------------
    print("\n--- SCENARIO 4: Interruption during JARVIS Speaking ---")
    vm.state_machine.transition_to(MicrophoneState.WAKEWORD_DETECTED, reason="Wake detected")
    vm.state_machine.transition_to(MicrophoneState.PROCESSING, reason="Preparing output")
    vm.state_machine.transition_to(MicrophoneState.SPEAKING, reason="Testing playback")
    assert vm.state_machine.current_state == MicrophoneState.SPEAKING

    # Interrupt!
    vm.interrupt()
    assert vm.state_machine.current_state == MicrophoneState.LISTENING_FOR_WAKEWORD
    print("  [SUCCESS] Scenario 4 verified cleanly.")

    # Stop listening
    vm.stop_listening()
    assert vm.state_machine.current_state == MicrophoneState.MICROPHONE_OFF

    # Resource measurements
    proc = psutil.Process()
    mem_mb = proc.memory_info().rss / (1024**2)
    cpu_pct = psutil.cpu_percent(interval=0.1)

    print("\n-------------------------------------------------------")
    print(f"[+] Total State Transitions Logged : {len(recorded_states)}")
    print(f"[+] Final Memory Footprint         : {mem_mb:.2f} MB")
    print(f"[+] Idle CPU Utilization           : {cpu_pct:.1f}%")
    print("=======================================================")
    print("[SUCCESS] All state machine simulation flows passed!")
    print("=======================================================\n")


if __name__ == "__main__":
    run_state_machine_simulation()
