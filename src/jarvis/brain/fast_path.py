"""
Fast Intent Router for bypassing LLM reasoning on simple deterministic commands.
"""

import re
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class FastIntentMatch(BaseModel):
    matched: bool = False
    intent_category: Optional[str] = None
    action_name: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    target_tool: Optional[str] = None
    fast_response: Optional[str] = None


class FastIntentRouter:
    """
    Evaluates user prompts against lightweight regex/keyword rules.
    If a known deterministic command is matched, it bypasses LLM planning.
    """

    PATTERNS = [
        # Conversational greetings & status
        (r"^(?:hi|hello|hai|hey|greetings)(?:\s+jarvis|\s+boss)?$", "conversation.greeting", None, {}, "Hello Boss! How can I assist you today?"),
        (r"^(?:how\s+are\s+you|how\s+are\s+you\s+doing)", "conversation.status", None, {}, "All systems operational and ready for your command, Boss."),
        (r"^(?:who\s+are\s+you|what\s+are\s+you)", "conversation.identity", None, {}, "I am JARVIS, your local personal AI computer assistant, Boss."),
        (r"^(?:help|what\s+can\s+you\s+do)", "conversation.help", None, {}, "I can control applications, manage files, search the web, execute shell commands, automate screen actions, and schedule background tasks, Boss."),

        # Application opening
        (r"^(?:open|launch|start)\s+(chrome|browser)", "app.open", "application.open", {"name": "chrome", "app": "chrome"}, "Opening Chrome, Boss."),
        (r"^(?:open|launch|start)\s+(notepad|editor)", "app.open", "application.open", {"name": "notepad", "app": "notepad"}, "Opening Notepad, Boss."),
        (r"^(?:open|launch|start)\s+(calculator|calc)", "app.open", "application.open", {"name": "calculator", "app": "calculator"}, "Opening Calculator, Boss."),
        (r"^(?:open|launch|start)\s+(terminal|cmd|powershell)", "app.open", "application.open", {"name": "terminal", "app": "terminal"}, "Opening Terminal, Boss."),
        
        # Application closing
        (r"^(?:close|quit|exit)\s+(chrome|browser)", "app.close", "application.close", {"name": "chrome", "app": "chrome"}, "Closing Chrome, Boss."),
        (r"^(?:close|quit|exit)\s+(notepad|editor)", "app.close", "application.close", {"name": "notepad", "app": "notepad"}, "Closing Notepad, Boss."),
        (r"^(?:close|quit|exit)\s+(calculator|calc)", "app.close", "application.close", {"name": "calculator", "app": "calculator"}, "Closing Calculator, Boss."),
        
        # Media / System Control
        (r"^(?:pause|stop)\s+(?:music|playback|audio)", "media.pause", "computer.key_press", {"key": "playpause"}, "Pausing playback, Boss."),
        (r"^(?:play|resume)\s+(?:music|playback|audio)", "media.play", "computer.key_press", {"key": "playpause"}, "Resuming playback, Boss."),
        (r"^(?:turn|set)?\s*volume\s+(?:down|lower)", "system.volume_down", "computer.key_press", {"key": "volumedown"}, "Lowering volume, Boss."),
        (r"^(?:turn|set)?\s*volume\s+(?:up|higher)", "system.volume_up", "computer.key_press", {"key": "volumeup"}, "Raising volume, Boss."),
        (r"^(?:mute|silence)\s+(?:volume|audio|sound)", "system.mute", "computer.key_press", {"key": "volumemute"}, "Muting audio, Boss."),
        
        # Screenshot
        (r"^(?:take|capture)\s+(?:a\s+)?screenshot", "system.screenshot", "computer.screenshot", {}, "Taking screenshot, Boss."),
    ]

    @classmethod
    def match(cls, user_prompt: str) -> FastIntentMatch:
        prompt_clean = user_prompt.strip().lower()

        for pattern, cat, tool, default_params, response in cls.PATTERNS:
            m = re.match(pattern, prompt_clean, re.IGNORECASE)
            if m:
                params = dict(default_params)
                return FastIntentMatch(
                    matched=True,
                    intent_category=cat,
                    action_name=cat,
                    parameters=params,
                    target_tool=tool,
                    fast_response=response,
                )

        return FastIntentMatch(matched=False)
