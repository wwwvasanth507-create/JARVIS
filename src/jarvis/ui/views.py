"""
JARVIS Desktop UI Component Views.

Modular UI views: HeaderView, ConversationView, InputView, StatusView,
SchedulerView, and CapabilitiesView.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
from typing import Callable, Optional, List, Dict, Any
from datetime import datetime

from jarvis.ui.theme import (
    BG_DARK, BG_SURFACE, BG_INPUT, BORDER_COLOR, TEXT_PRIMARY, TEXT_MUTED, TEXT_BRIGHT,
    CYAN_ACCENT, GREEN_SUCCESS, YELLOW_WARN, RED_ERROR, PURPLE_VOICE,
    FONT_TITLE, FONT_SUBTITLE, FONT_BODY, FONT_MUTED, FONT_MONO, PAD_S, PAD_M, PAD_L
)


class HeaderView(tk.Frame):
    """Header bar displaying title, status, performance profile, and subsystem indicators."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=BG_SURFACE, highlightbackground=BORDER_COLOR, highlightthickness=1, **kwargs)
        self.pack(fill=tk.X, padx=PAD_M, pady=(PAD_M, PAD_S))
        self._build_ui()

    def _build_ui(self):
        # Left: Branding
        left_frame = tk.Frame(self, bg=BG_SURFACE)
        left_frame.pack(side=tk.LEFT, padx=PAD_M, pady=PAD_M)

        lbl_logo = tk.Label(left_frame, text="🤖 JARVIS", bg=BG_SURFACE, fg=CYAN_ACCENT, font=FONT_TITLE)
        lbl_logo.pack(side=tk.LEFT)

        lbl_sub = tk.Label(left_frame, text=" | Desktop Assistant", bg=BG_SURFACE, fg=TEXT_MUTED, font=FONT_BODY)
        lbl_sub.pack(side=tk.LEFT)

        # Right: Status Badges
        right_frame = tk.Frame(self, bg=BG_SURFACE)
        right_frame.pack(side=tk.RIGHT, padx=PAD_M, pady=PAD_M)

        self.lbl_status = tk.Label(right_frame, text="● READY", bg=BG_SURFACE, fg=GREEN_SUCCESS, font=FONT_SUBTITLE)
        self.lbl_status.pack(side=tk.RIGHT, padx=(PAD_M, 0))

        self.lbl_profile = tk.Label(right_frame, text="MODE: LOW", bg=BG_INPUT, fg=TEXT_PRIMARY, font=FONT_MUTED, padx=6, pady=2)
        self.lbl_profile.pack(side=tk.RIGHT, padx=PAD_S)

        self.lbl_mic = tk.Label(right_frame, text="MIC: READY", bg=BG_SURFACE, fg=TEXT_MUTED, font=FONT_MUTED)
        self.lbl_mic.pack(side=tk.RIGHT, padx=PAD_S)

    def update_status(self, state_name: str, profile_name: str = "MEDIUM"):
        if state_name in ("READY", "RUNNING"):
            self.lbl_status.configure(text=f"● {state_name}", fg=GREEN_SUCCESS)
        elif state_name in ("INITIALIZING", "VALIDATING", "PAUSING"):
            self.lbl_status.configure(text=f"● {state_name}", fg=YELLOW_WARN)
        else:
            self.lbl_status.configure(text=f"● {state_name}", fg=RED_ERROR)
        self.lbl_profile.configure(text=f"MODE: {profile_name}")

    def update_mic_state(self, mic_state_text: str, is_active: bool = False):
        color = PURPLE_VOICE if is_active else TEXT_MUTED
        self.lbl_mic.configure(text=f"MIC: {mic_state_text}", fg=color)


class ConversationView(tk.Frame):
    """Scrollable chat timeline rendering Boss and JARVIS messages, steps, and errors."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=BG_DARK, **kwargs)
        self.pack(fill=tk.BOTH, expand=True, padx=PAD_M, pady=PAD_S)
        self._build_ui()

    def _build_ui(self):
        self.txt_history = scrolledtext.ScrolledText(
            self,
            bg=BG_DARK,
            fg=TEXT_PRIMARY,
            insertbackground=TEXT_PRIMARY,
            font=FONT_BODY,
            wrap=tk.WORD,
            border=0,
            highlightthickness=0,
            padx=PAD_M,
            pady=PAD_M
        )
        self.txt_history.pack(fill=tk.BOTH, expand=True)

        # Configure tags
        self.txt_history.tag_configure("boss_header", foreground=CYAN_ACCENT, font=FONT_SUBTITLE, spacing1=10)
        self.txt_history.tag_configure("boss_msg", foreground=TEXT_BRIGHT, font=FONT_BODY, lmargin1=15, lmargin2=15)
        self.txt_history.tag_configure("jarvis_header", foreground=GREEN_SUCCESS, font=FONT_SUBTITLE, spacing1=10)
        self.txt_history.tag_configure("jarvis_msg", foreground=TEXT_PRIMARY, font=FONT_BODY, lmargin1=15, lmargin2=15)
        self.txt_history.tag_configure("progress_msg", foreground=YELLOW_WARN, font=FONT_MUTED, lmargin1=15, lmargin2=15)
        self.txt_history.tag_configure("error_msg", foreground=RED_ERROR, font=FONT_BODY, lmargin1=15, lmargin2=15)
        self.txt_history.tag_configure("system_msg", foreground=TEXT_MUTED, font=FONT_MUTED, spacing1=5)

    def add_boss_message(self, text: str):
        now_str = datetime.now().strftime("%H:%M:%S")
        self.txt_history.insert(tk.END, f"\nBoss ({now_str}):\n", "boss_header")
        self.txt_history.insert(tk.END, f"{text}\n", "boss_msg")
        self.txt_history.see(tk.END)

    def add_jarvis_message(self, text: str, verified: bool = True):
        now_str = datetime.now().strftime("%H:%M:%S")
        tag = "jarvis_header" if verified else "error_msg"
        prefix = "JARVIS" if verified else "JARVIS (Unverified)"
        self.txt_history.insert(tk.END, f"\n{prefix} ({now_str}):\n", tag)
        self.txt_history.insert(tk.END, f"{text}\n", "jarvis_msg")
        self.txt_history.see(tk.END)

    def add_progress(self, stage: str):
        self.txt_history.insert(tk.END, f"  ⚡ {stage}...\n", "progress_msg")
        self.txt_history.see(tk.END)

    def add_error(self, error_text: str):
        self.txt_history.insert(tk.END, f"\n❌ Error:\n{error_text}\n", "error_msg")
        self.txt_history.see(tk.END)

    def add_system_notice(self, notice_text: str):
        self.txt_history.insert(tk.END, f"📌 [System] {notice_text}\n", "system_msg")
        self.txt_history.see(tk.END)

    def clear(self):
        self.txt_history.delete("1.0", tk.END)


class InputView(tk.Frame):
    """Text entry area with Send, Universal Stop, Voice button, and Wake-Word toggle."""

    def __init__(
        self,
        parent,
        on_send: Callable[[str], None],
        on_cancel: Callable[[], None],
        on_voice_toggle: Callable[[], None],
        on_wakeword_toggle: Callable[[], None],
        on_clear: Callable[[], None],
        **kwargs
    ):
        super().__init__(parent, bg=BG_SURFACE, highlightbackground=BORDER_COLOR, highlightthickness=1, **kwargs)
        self.on_send = on_send
        self.on_cancel = on_cancel
        self.on_voice_toggle = on_voice_toggle
        self.on_wakeword_toggle = on_wakeword_toggle
        self.on_clear = on_clear

        self.pack(fill=tk.X, padx=PAD_M, pady=(PAD_S, PAD_M))
        self._build_ui()

    def _build_ui(self):
        top_frame = tk.Frame(self, bg=BG_SURFACE)
        top_frame.pack(fill=tk.X, padx=PAD_M, pady=(PAD_M, PAD_S))

        # Text Input
        self.entry_cmd = tk.Entry(
            top_frame,
            bg=BG_INPUT,
            fg=TEXT_PRIMARY,
            insertbackground=TEXT_PRIMARY,
            font=FONT_BODY,
            border=0,
            highlightbackground=BORDER_COLOR,
            highlightthickness=1
        )
        self.entry_cmd.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, PAD_S), ipady=6)
        self.entry_cmd.bind("<Return>", self._handle_enter)
        self.entry_cmd.bind("<Escape>", lambda e: self.on_cancel())

        # Send Button
        btn_send = tk.Button(top_frame, text="Send", bg=CYAN_ACCENT, fg="#000000", font=FONT_SUBTITLE, command=self._submit, relief="flat", padx=14)
        btn_send.pack(side=tk.LEFT, padx=PAD_S)

        # Stop Button
        btn_stop = tk.Button(top_frame, text="Stop", bg=RED_ERROR, fg="#ffffff", font=FONT_SUBTITLE, command=self.on_cancel, relief="flat", padx=12)
        btn_stop.pack(side=tk.LEFT, padx=PAD_S)

        # Controls Row
        ctrl_frame = tk.Frame(self, bg=BG_SURFACE)
        ctrl_frame.pack(fill=tk.X, padx=PAD_M, pady=(0, PAD_M))

        self.btn_mic = tk.Button(ctrl_frame, text="🎤 Voice: OFF", bg=BG_INPUT, fg=TEXT_MUTED, font=FONT_MUTED, command=self.on_voice_toggle, relief="flat", padx=10)
        self.btn_mic.pack(side=tk.LEFT, padx=(0, PAD_S))

        self.btn_wake = tk.Button(ctrl_frame, text="🔔 Wake Word: ON", bg=BG_INPUT, fg=GREEN_SUCCESS, font=FONT_MUTED, command=self.on_wakeword_toggle, relief="flat", padx=10)
        self.btn_wake.pack(side=tk.LEFT, padx=PAD_S)

        btn_clear = tk.Button(ctrl_frame, text="Clear Chat", bg=BG_INPUT, fg=TEXT_MUTED, font=FONT_MUTED, command=self.on_clear, relief="flat", padx=10)
        btn_clear.pack(side=tk.RIGHT)

    def _handle_enter(self, event):
        self._submit()

    def _submit(self):
        text = self.entry_cmd.get().strip()
        if text:
            self.entry_cmd.delete(0, tk.END)
            self.on_send(text)

    def update_voice_button(self, is_listening: bool):
        if is_listening:
            self.btn_mic.configure(text="🎙 Listening...", bg=PURPLE_VOICE, fg="#ffffff")
        else:
            self.btn_mic.configure(text="🎤 Voice: OFF", bg=BG_INPUT, fg=TEXT_MUTED)

    def update_wakeword_button(self, is_enabled: bool):
        if is_enabled:
            self.btn_wake.configure(text="🔔 Wake Word: ON", fg=GREEN_SUCCESS)
        else:
            self.btn_wake.configure(text="🔕 Wake Word: OFF", fg=TEXT_MUTED)


class StatusView(tk.Frame):
    """Footer status bar showing RAM/CPU footprint, current task, and scheduler status."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=BG_SURFACE, **kwargs)
        self.pack(fill=tk.X, side=tk.BOTTOM)
        self._build_ui()

    def _build_ui(self):
        self.lbl_info = tk.Label(self, text="JARVIS v0.1.0 | Idle | Memory: -- MB | Scheduler: Active", bg=BG_SURFACE, fg=TEXT_MUTED, font=FONT_MUTED, padx=PAD_M, pady=PAD_S)
        self.lbl_info.pack(side=tk.LEFT)

    def update_metrics(self, active_task: str = "Idle", ram_mb: float = 0.0, scheduler_status: str = "Active"):
        ram_str = f"{ram_mb:.1f} MB" if ram_mb > 0 else "--"
        self.lbl_info.configure(text=f"JARVIS v0.1.0 | {active_task} | RAM: {ram_str} | Scheduler: {scheduler_status}")


class SchedulerView(tk.Toplevel):
    """Upcoming and recurring scheduled tasks management panel."""

    def __init__(self, parent, scheduler_manager, on_refresh: Optional[Callable[[], None]] = None):
        super().__init__(parent)
        self.scheduler_manager = scheduler_manager
        self.on_refresh = on_refresh

        self.title("JARVIS Task Scheduler")
        self.geometry("600x380")
        self.configure(bg=BG_DARK)
        self.transient(parent)

        self._build_ui()
        self.refresh_tasks()

    def _build_ui(self):
        container = tk.Frame(self, bg=BG_SURFACE, padx=PAD_M, pady=PAD_M)
        container.pack(fill=tk.BOTH, expand=True, padx=PAD_M, pady=PAD_M)

        lbl_title = tk.Label(container, text="📅 Scheduled Background Automation Tasks", bg=BG_SURFACE, fg=TEXT_BRIGHT, font=FONT_TITLE)
        lbl_title.pack(anchor="w", pady=(0, PAD_M))

        # Task Listbox / Treeview
        columns = ("id", "name", "next_run", "status")
        self.tree = ttk.Treeview(container, columns=columns, show="headings", height=8)
        self.tree.heading("id", text="Task ID")
        self.tree.heading("name", text="Task Name")
        self.tree.heading("next_run", text="Next Run")
        self.tree.heading("status", text="State")

        self.tree.column("id", width=110)
        self.tree.column("name", width=220)
        self.tree.column("next_run", width=150)
        self.tree.column("status", width=80)
        self.tree.pack(fill=tk.BOTH, expand=True, pady=(0, PAD_M))

        btn_frame = tk.Frame(container, bg=BG_SURFACE)
        btn_frame.pack(fill=tk.X)

        btn_ref = tk.Button(btn_frame, text="Refresh", bg=BG_INPUT, fg=TEXT_PRIMARY, font=FONT_BODY, command=self.refresh_tasks, relief="flat", padx=12)
        btn_ref.pack(side=tk.LEFT)

        btn_cancel = tk.Button(btn_frame, text="Cancel Selected", bg=RED_ERROR, fg="#ffffff", font=FONT_BODY, command=self._cancel_selected, relief="flat", padx=12)
        btn_cancel.pack(side=tk.RIGHT)

    def refresh_tasks(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        if not self.scheduler_manager:
            return

        tasks = self.scheduler_manager.list_tasks()
        for t in tasks:
            next_str = datetime.fromtimestamp(t.next_run_at).strftime("%m-%d %H:%M:%S") if t.next_run_at else "None"
            self.tree.insert("", tk.END, values=(t.task_id, t.name, next_str, t.state.value if hasattr(t.state, 'value') else str(t.state)))

    def _cancel_selected(self):
        selected = self.tree.selection()
        if selected and self.scheduler_manager:
            item = self.tree.item(selected[0])
            task_id = item["values"][0]
            self.scheduler_manager.cancel_task(task_id)
            self.refresh_tasks()


class CapabilitiesView(tk.Toplevel):
    """Subsystem Capabilities Diagnostic Matrix."""

    def __init__(self, parent, capabilities_registry):
        super().__init__(parent)
        self.capabilities_registry = capabilities_registry

        self.title("JARVIS Subsystem Capabilities Matrix")
        self.geometry("540x420")
        self.configure(bg=BG_DARK)
        self.transient(parent)

        self._build_ui()

    def _build_ui(self):
        container = tk.Frame(self, bg=BG_SURFACE, padx=PAD_M, pady=PAD_M)
        container.pack(fill=tk.BOTH, expand=True, padx=PAD_M, pady=PAD_M)

        lbl_title = tk.Label(container, text="🛡️ System Capability Health", bg=BG_SURFACE, fg=TEXT_BRIGHT, font=FONT_TITLE)
        lbl_title.pack(anchor="w", pady=(0, PAD_M))

        txt_matrix = scrolledtext.ScrolledText(container, bg=BG_INPUT, fg=TEXT_PRIMARY, font=FONT_MONO, border=0, padx=10, pady=10)
        txt_matrix.pack(fill=tk.BOTH, expand=True)

        report = self.capabilities_registry.get_status_report()
        txt_matrix.insert(tk.END, f"Total Capabilities: {report['total_capabilities']}\n")
        txt_matrix.insert(tk.END, f"AVAILABLE: {report['available_count']} | DEGRADED: {report['degraded_count']} | UNAVAILABLE: {report['unavailable_count']}\n")
        txt_matrix.insert(tk.END, "=" * 55 + "\n\n")

        for name, cap in report["capabilities"].items():
            st = cap["status"]
            symbol = "✓" if st == "AVAILABLE" else ("!" if st == "DEGRADED" else "✗")
            txt_matrix.insert(tk.END, f"[{st:<11}] {symbol} {name:<22} : {cap['reason']}\n")
