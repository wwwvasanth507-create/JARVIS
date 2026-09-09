"""
Terminal Chat & Human-to-JARVIS Interactive Interface.
Supports progressive token streaming, command filtering, voice integration, and graceful error handling.
"""

from typing import Any, Dict, Optional
import os
import sys
import time
import logging

from jarvis.core.config import JarvisConfig
from jarvis.brain.provider import ModelProvider, MockModelProvider, LlamaCppModelProvider
from jarvis.brain.context import ContextManager
from jarvis.brain.conversation import ConversationManager, UserMessage, AssistantMessage
from jarvis.voice.manager import VoiceManager
from jarvis.system.hardware import HardwareDetector

logger = logging.getLogger("jarvis.ui.chat")


class JarvisTerminalInterface:
    """
    Main Terminal Interface connecting the Boss to local JARVIS Brain & Voice subsystem.
    """

    def __init__(
        self,
        config: Optional[JarvisConfig] = None,
        model_provider: Optional[ModelProvider] = None,
        voice_manager: Optional[VoiceManager] = None,
    ):
        self.config = config or JarvisConfig.load_from_yaml("config/config.yaml")
        
        # Brain setup
        if model_provider:
            self.provider = model_provider
        else:
            # Try loading LlamaCpp if file exists, otherwise Mock
            path = self.config.model_provider.model_path
            llama_provider = LlamaCppModelProvider(path, self.config.model_provider.model_dump())
            if llama_provider.is_available():
                self.provider = llama_provider
            else:
                self.provider = MockModelProvider()

        # Context & Conversation Managers
        self.context_mgr = ContextManager(max_context_tokens=self.config.model_provider.context_size)
        self.conversation_mgr = ConversationManager(max_tokens=self.config.model_provider.context_size)

        # Voice Subsystem
        if voice_manager:
            self.voice_mgr = voice_manager
        else:
            self.voice_mgr = VoiceManager(voice_settings=self.config.voice)

        self.mode = self.config.voice.mode  # "chat", "voice", "hybrid"
        self.running = False

    def display_banner(self) -> None:
        """Prints startup banner and status summary."""
        hw = HardwareDetector.detect()
        print("\n=======================================================")
        print("                JARVIS AI ASSISTANT")
        print("          Local-First CPU Personal AI Interface")
        print("=======================================================")
        print(f"  User       : {self.config.system.user_alias}")
        print(f"  Hardware   : {hw.cpu_name} ({hw.physical_cores} Cores, {hw.ram_gb:.1f} GB RAM)")
        print(f"  Brain      : {self.provider.model_info()['name']} ({'Ready' if self.provider.is_ready() else 'Loaded on demand'})")
        v_status = self.voice_mgr.get_status()
        print(f"  Voice STT  : {v_status['stt_engine']} ({'Active' if v_status['stt_available'] else 'Degraded'})")
        print(f"  Voice TTS  : {v_status['tts_engine']} ({'Active' if v_status['tts_available'] else 'Degraded'})")
        print(f"  Wake Word  : {v_status['wakeword_phrase']} ({'Enabled' if v_status['wakeword_enabled'] else 'Disabled'})")
        print(f"  Privacy    : {v_status['privacy_status']}")
        print(f"  Mode       : {self.mode.upper()}")
        print("-------------------------------------------------------")
        print(" Type '/help' for command list. Type 'exit' to quit.")
        print("=======================================================\n")

    def handle_command(self, user_input: str) -> bool:
        """
        Intercepts local commands.
        Returns True if a command was executed (meaning do NOT send to LLM).
        Returns False if standard message to pass to LLM.
        """
        cmd = user_input.strip().lower()

        if cmd in ["exit", "quit", "/exit", "/quit"]:
            print("\nJARVIS: Goodbye, Boss. Standing by.\n")
            self.running = False
            return True

        if cmd in ["clear", "/clear"]:
            os.system("cls" if os.name == "nt" else "clear")
            self.conversation_mgr.clear()
            self.display_banner()
            print("JARVIS: Conversation history and screen cleared, Boss.\n")
            return True

        if cmd in ["help", "/help"]:
            print("\nAvailable Commands:")
            print("  exit, quit, /quit  : Exit JARVIS interface")
            print("  clear, /clear      : Clear screen & session conversation history")
            print("  status, /status    : Display system hardware, brain, and voice status")
            print("  /chat              : Switch to Text Chat mode (keyboard only)")
            print("  /voice             : Switch to Voice mode (speech input/output)")
            print("  /hybrid            : Switch to Hybrid mode (text/voice input & voice output)")
            print("  /listen            : Trigger voice input capture via microphone\n")
            return True

        if cmd in ["status", "/status"]:
            hw = HardwareDetector.detect()
            v_status = self.voice_mgr.get_status()
            print("\n--- JARVIS STATUS ---")
            print(f"  System         : JARVIS v{self.config.system.version}")
            print(f"  User           : {self.config.system.user_alias}")
            print(f"  Hardware       : CPU-Only ({hw.physical_cores} Physical Cores, {hw.ram_gb:.1f} GB RAM)")
            print(f"  Model Provider : {type(self.provider).__name__} ({self.provider.model_info()['name']})")
            print(f"  Active Mode    : {self.mode.upper()}")
            print(f"  Wake Word      : {v_status['wakeword_phrase']} (Engine: {v_status['wakeword_engine']})")
            print(f"  Privacy Status : {v_status['privacy_status']}")
            print(f"  Mic State      : {v_status['microphone_state']}")
            print(f"  Audio Owner    : {v_status['audio_owner']}")
            print(f"  STT Engine     : {v_status['stt_engine']} (Available: {v_status['stt_available']})")
            print(f"  TTS Engine     : {v_status['tts_engine']} (Available: {v_status['tts_available']})")
            print(f"  Microphone     : {v_status['microphone']}")
            print(f"  Speaker        : {v_status['speaker']}")
            print(f"  History Count  : {self.conversation_mgr.message_count} messages\n")
            return True

        if cmd == "/chat":
            self.mode = "chat"
            print("JARVIS: Switched to Chat mode, Boss.\n")
            return True

        if cmd == "/voice":
            self.mode = "voice"
            print("JARVIS: Switched to Voice mode, Boss.\n")
            return True

        if cmd == "/hybrid":
            self.mode = "hybrid"
            print("JARVIS: Switched to Hybrid mode, Boss.\n")
            return True

        if cmd == "/listen":
            self.process_voice_input()
            return True

        return False

    def process_voice_input(self) -> None:
        """Captures voice input from microphone and passes transcription to processing pipeline."""
        print("\n[JARVIS Listening... Speak now]")
        transcript = self.voice_mgr.listen_and_transcribe(duration_seconds=3.0)
        
        if not transcript:
            print("JARVIS: I couldn't hear or transcribe any speech. Please try again, Boss.\n")
            return

        print(f"\nBoss (Voice): {transcript}")
        self.process_user_message(transcript, source="voice")

    def process_user_message(self, text: str, source: str = "chat") -> None:
        """
        Main processing pipeline:
        1. Add UserMessage to ConversationManager
        2. Assemble prompt using ContextManager
        3. Stream response tokens from LLM
        4. Play TTS stream if mode is 'voice' or 'hybrid'
        5. Record AssistantMessage
        """
        if not text.strip():
            return

        # 1. Add UserMessage
        user_msg = self.conversation_mgr.add_user_message(text=text, source=source)

        # 2. Assemble context & request
        history = self.conversation_mgr.get_chat_history()[:-1]  # Exclude current prompt already passed
        gen_request = self.context_mgr.build_generation_request(
            user_prompt=text,
            history=history,
            temperature=self.config.model_provider.temperature,
        )

        print("JARVIS: ", end="", flush=True)
        start_time = time.perf_counter()

        # 3. Stream from Brain & TTS
        def token_stream_generator():
            for chunk in self.provider.stream(gen_request):
                sys.stdout.write(chunk)
                sys.stdout.flush()
                yield chunk

        if self.mode in ["voice", "hybrid"] and self.config.voice.text_to_speech.enabled:
            response_text = self.voice_mgr.speak_stream(token_stream_generator())
        else:
            collected = []
            for chunk in token_stream_generator():
                collected.append(chunk)
            response_text = "".join(collected)

        print("\n")
        duration = time.perf_counter() - start_time
        tokens = len(response_text.split())

        # 4. Record AssistantMessage
        self.conversation_mgr.add_assistant_message(
            text=response_text, duration_seconds=duration, tokens_generated=tokens
        )

    def start_loop(self) -> None:
        """Starts the interactive CLI loop."""
        self.running = True
        self.display_banner()

        while self.running:
            try:
                if self.mode == "voice":
                    prompt = input(f"Boss [{self.mode}] (Press Enter to Speak, or type command): ")
                    if not prompt.strip():
                        self.process_voice_input()
                        continue
                else:
                    prompt = input(f"Boss [{self.mode}] > ")

                if not prompt.strip():
                    continue

                # Handle local commands
                is_command = self.handle_command(prompt)
                if is_command:
                    continue

                # Process natural user query
                self.process_user_message(prompt, source="chat")

            except (KeyboardInterrupt, EOFError):
                print("\nJARVIS: Session interrupted. Goodbye, Boss.")
                self.running = False
                break
