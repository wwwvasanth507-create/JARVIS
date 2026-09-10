"""
Confirmation, Human Intervention, and Settings Dialogs for JARVIS Desktop UI.

Implements high-risk action confirmation GUI modals, human intervention prompts,
and user settings panel.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any, Optional, Callable
import logging

from jarvis.ui.theme import (
    BG_DARK, BG_SURFACE, BG_INPUT, BORDER_COLOR, TEXT_PRIMARY, TEXT_MUTED, TEXT_BRIGHT,
    RED_ERROR, YELLOW_WARN, CYAN_ACCENT, FONT_TITLE, FONT_SUBTITLE, FONT_BODY, PAD_M, PAD_S, PAD_L
)

logger = logging.getLogger(__name__)


class ConfirmationDialog(tk.Toplevel):
    """GUI Confirmation dialog for high-risk and critical operations."""

    def __init__(
        self,
        parent,
        action_name: str,
        risk_level: str,
        description: str,
        on_decision: Callable[[bool], None]
    ):
        super().__init__(parent)
        self.action_name = action_name
        self.risk_level = risk_level
        self.description = description
        self.on_decision = on_decision
        self.result = False

        self.title("JARVIS Confirmation Required")
        self.geometry("480x260")
        self.configure(bg=BG_DARK)
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self._build_ui()
        self.center_window(parent)

    def center_window(self, parent):
        self.update_idletasks()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        px = parent.winfo_x()
        py = parent.winfo_y()
        w = self.winfo_width()
        h = self.winfo_height()
        self.geometry(f"{w}x{h}+{px + (pw - w) // 2}+{py + (ph - h) // 2}")

    def _build_ui(self):
        container = tk.Frame(self, bg=BG_SURFACE, padx=PAD_L, pady=PAD_L, highlightbackground=BORDER_COLOR, highlightthickness=1)
        container.pack(fill=tk.BOTH, expand=True, padx=PAD_M, pady=PAD_M)

        # Header
        lbl_title = tk.Label(container, text="⚠️ Confirmation Required", bg=BG_SURFACE, fg=YELLOW_WARN, font=FONT_TITLE)
        lbl_title.pack(anchor="w", pady=(0, PAD_S))

        # Risk Banner
        risk_color = RED_ERROR if self.risk_level in ("HIGH", "CRITICAL") else YELLOW_WARN
        lbl_risk = tk.Label(container, text=f"RISK TIER: {self.risk_level}", bg=BG_SURFACE, fg=risk_color, font=FONT_SUBTITLE)
        lbl_risk.pack(anchor="w", pady=(0, PAD_M))

        # Action & Details
        lbl_action = tk.Label(container, text=f"Action: {self.action_name}", bg=BG_SURFACE, fg=TEXT_BRIGHT, font=FONT_BODY, justify="left")
        lbl_action.pack(anchor="w")

        lbl_desc = tk.Label(container, text=self.description, bg=BG_SURFACE, fg=TEXT_PRIMARY, font=FONT_BODY, wraplength=420, justify="left")
        lbl_desc.pack(anchor="w", pady=PAD_S)

        # Buttons
        btn_frame = tk.Frame(container, bg=BG_SURFACE)
        btn_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(PAD_M, 0))

        btn_cancel = tk.Button(btn_frame, text="Cancel", bg=BG_INPUT, fg=TEXT_PRIMARY, font=FONT_BODY, command=self._on_cancel, relief="flat", padx=16, pady=4)
        btn_cancel.pack(side=tk.RIGHT, padx=(PAD_S, 0))

        btn_confirm = tk.Button(btn_frame, text="Confirm Execution", bg=RED_ERROR if self.risk_level in ("HIGH", "CRITICAL") else CYAN_ACCENT, fg="#ffffff" if self.risk_level in ("HIGH", "CRITICAL") else "#000000", font=FONT_SUBTITLE, command=self._on_confirm, relief="flat", padx=16, pady=4)
        btn_confirm.pack(side=tk.RIGHT)

    def _on_confirm(self):
        self.result = True
        self.on_decision(True)
        self.destroy()

    def _on_cancel(self):
        self.result = False
        self.on_decision(False)
        self.destroy()


class HumanInterventionDialog(tk.Toplevel):
    """GUI Modal surfacing HumanInterventionRequiredError (CAPTCHA, user choices, manual input)."""

    def __init__(self, parent, prompt_message: str, on_response: Callable[[str], None]):
        super().__init__(parent)
        self.prompt_message = prompt_message
        self.on_response = on_response

        self.title("JARVIS Attention Required")
        self.geometry("450x220")
        self.configure(bg=BG_DARK)
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self._build_ui()

    def _build_ui(self):
        container = tk.Frame(self, bg=BG_SURFACE, padx=PAD_L, pady=PAD_L)
        container.pack(fill=tk.BOTH, expand=True, padx=PAD_M, pady=PAD_M)

        lbl_title = tk.Label(container, text="👤 Action Required from Boss", bg=BG_SURFACE, fg=CYAN_ACCENT, font=FONT_TITLE)
        lbl_title.pack(anchor="w", pady=(0, PAD_S))

        lbl_msg = tk.Label(container, text=self.prompt_message, bg=BG_SURFACE, fg=TEXT_PRIMARY, font=FONT_BODY, wraplength=400, justify="left")
        lbl_msg.pack(anchor="w", pady=(0, PAD_M))

        self.entry_input = tk.Entry(container, bg=BG_INPUT, fg=TEXT_PRIMARY, font=FONT_BODY, insertbackground=TEXT_PRIMARY)
        self.entry_input.pack(fill=tk.X, pady=(0, PAD_M))
        self.entry_input.focus_set()

        btn_frame = tk.Frame(container, bg=BG_SURFACE)
        btn_frame.pack(fill=tk.X, side=tk.BOTTOM)

        btn_submit = tk.Button(btn_frame, text="Submit", bg=CYAN_ACCENT, fg="#000000", font=FONT_SUBTITLE, command=self._on_submit, relief="flat", padx=16)
        btn_submit.pack(side=tk.RIGHT)

    def _on_submit(self):
        val = self.entry_input.get().strip()
        self.on_response(val)
        self.destroy()


class SettingsWindow(tk.Toplevel):
    """User Settings GUI backed by YAML configuration."""

    def __init__(self, parent, config, on_save: Callable[[Dict[str, Any]], None]):
        super().__init__(parent)
        self.config = config
        self.on_save = on_save

        self.title("JARVIS Settings")
        self.geometry("460x380")
        self.configure(bg=BG_DARK)
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self._build_ui()

    def _build_ui(self):
        container = tk.Frame(self, bg=BG_SURFACE, padx=PAD_L, pady=PAD_L)
        container.pack(fill=tk.BOTH, expand=True, padx=PAD_M, pady=PAD_M)

        lbl_title = tk.Label(container, text="⚙️ Preferences & Configuration", bg=BG_SURFACE, fg=TEXT_BRIGHT, font=FONT_TITLE)
        lbl_title.pack(anchor="w", pady=(0, PAD_M))

        # Checkboxes
        self.var_voice = tk.BooleanVar(value=self.config.voice.push_to_talk)
        chk_voice = tk.Checkbutton(container, text="Enable Voice Subsystem", variable=self.var_voice, bg=BG_SURFACE, fg=TEXT_PRIMARY, selectcolor=BG_INPUT, activebackground=BG_SURFACE, font=FONT_BODY)
        chk_voice.pack(anchor="w", pady=PAD_S)

        self.var_wakeword = tk.BooleanVar(value=self.config.wakeword.enabled)
        chk_wake = tk.Checkbutton(container, text="Enable Background Wake Word ('JARVIS')", variable=self.var_wakeword, bg=BG_SURFACE, fg=TEXT_PRIMARY, selectcolor=BG_INPUT, activebackground=BG_SURFACE, font=FONT_BODY)
        chk_wake.pack(anchor="w", pady=PAD_S)

        self.var_tts = tk.BooleanVar(value=self.config.voice.text_to_speech.enabled)
        chk_tts = tk.Checkbutton(container, text="Enable Text-To-Speech Output", variable=self.var_tts, bg=BG_SURFACE, fg=TEXT_PRIMARY, selectcolor=BG_INPUT, activebackground=BG_SURFACE, font=FONT_BODY)
        chk_tts.pack(anchor="w", pady=PAD_S)

        # Buttons
        btn_frame = tk.Frame(container, bg=BG_SURFACE)
        btn_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(PAD_M, 0))

        btn_save = tk.Button(btn_frame, text="Save Settings", bg=CYAN_ACCENT, fg="#000000", font=FONT_SUBTITLE, command=self._on_save, relief="flat", padx=16)
        btn_save.pack(side=tk.RIGHT)

    def _on_save(self):
        updated = {
            "voice_enabled": self.var_voice.get(),
            "wakeword_enabled": self.var_wakeword.get(),
            "tts_enabled": self.var_tts.get(),
        }
        self.on_save(updated)
        self.destroy()
