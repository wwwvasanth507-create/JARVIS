"""
Unit tests for JarvisTerminalInterface command interception, mode switching, and response flow.
"""

import pytest
from jarvis.ui.chat import JarvisTerminalInterface
from jarvis.brain.provider import MockModelProvider
from jarvis.voice.manager import VoiceManager
from jarvis.voice.stt import MockSpeechRecognizer
from jarvis.voice.tts import MockTextToSpeech


def test_command_interception():
    ui = JarvisTerminalInterface(
        model_provider=MockModelProvider(),
        voice_manager=VoiceManager(stt=MockSpeechRecognizer(), tts=MockTextToSpeech()),
    )

    # Test /help command
    assert ui.handle_command("/help") is True
    assert ui.handle_command("help") is True

    # Test /status command
    assert ui.handle_command("/status") is True
    assert ui.handle_command("status") is True

    # Test mode switching commands
    assert ui.handle_command("/voice") is True
    assert ui.mode == "voice"

    assert ui.handle_command("/chat") is True
    assert ui.mode == "chat"

    assert ui.handle_command("/hybrid") is True
    assert ui.mode == "hybrid"

    # Test regular user query is NOT intercepted as command
    assert ui.handle_command("What is the capital of France?") is False


def test_user_message_processing(capsys):
    ui = JarvisTerminalInterface(
        model_provider=MockModelProvider(),
        voice_manager=VoiceManager(stt=MockSpeechRecognizer(), tts=MockTextToSpeech()),
    )

    ui.process_user_message("Hello JARVIS")
    
    assert ui.conversation_mgr.message_count == 2
    user_msg = ui.conversation_mgr.get_last_user_message()
    ast_msg = ui.conversation_mgr.get_last_assistant_message()

    assert user_msg.text == "Hello JARVIS"
    assert "Boss" in ast_msg.text or "At your service" in ast_msg.text
