"""
Top-Level Production Desktop Application Controller for JARVIS.

Integrates:
- Tkinter GUI main window
- Single authoritative JARVISApp runtime controller
- Thread-safe background execution queue (queue.Queue / root.after)
- Universal command cancellation (Stop button)
- High-risk operation GUI confirmation modals
- System tray & notification area integration
- Single-instance lock protection
- Graceful shutdown
"""

import sys
import queue
import threading
import time
import logging
import psutil
import tkinter as tk
from tkinter import messagebox
from typing import Optional, Dict, Any

from jarvis.app import JARVISApp
from jarvis.core.lifecycle import ApplicationState
from jarvis.system.single_instance import SingleInstanceLock
from jarvis.ui.theme import apply_ttk_theme, BG_DARK, CYAN_ACCENT, TEXT_BRIGHT
from jarvis.ui.system_tray import SystemTrayManager
from jarvis.ui.dialogs import ConfirmationDialog, HumanInterventionDialog, SettingsWindow
from jarvis.ui.views import (
    HeaderView, ConversationView, InputView, StatusView,
    SchedulerView, CapabilitiesView
)

logger = logging.getLogger(__name__)


class JarvisDesktopApp:
    """
    Main Desktop GUI Controller for JARVIS.
    Wraps single authoritative JARVISApp runtime into a responsive desktop shell.
    """

    def __init__(self, jarvis_app: Optional[JARVISApp] = None, safe_mode: bool = False):
        self.safe_mode = safe_mode
        self.single_instance_lock = SingleInstanceLock()
        
        # Runtime instance (single authoritative instance)
        self.jarvis_app = jarvis_app or JARVISApp(safe_mode=safe_mode)

        # Threading Queue
        self.ui_queue = queue.Queue()
        
        # State variables
        self.is_voice_active = False
        self.is_wakeword_active = True
        self.current_worker_thread: Optional[threading.Thread] = None

        # Tkinter Root
        self.root = tk.Tk()
        self.root.title("JARVIS Personal AI Assistant")
        self.root.geometry("820x640")
        self.root.minsize(700, 500)
        self.root.configure(bg=BG_DARK)

        # System Tray
        self.tray_manager = SystemTrayManager(
            on_open=self.restore_from_tray,
            on_doctor=self.open_doctor,
            on_status=self.open_capabilities,
            on_toggle_wakeword=self.toggle_wakeword,
            on_exit=self.quit_app
        )

        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close_window)

    def _build_ui(self):
        apply_ttk_theme(self.root)

        # 1. Header View
        self.header = HeaderView(self.root)

        # 2. Conversation View
        self.conversation = ConversationView(self.root)

        # 3. Input View
        self.input_view = InputView(
            self.root,
            on_send=self.handle_user_submit,
            on_cancel=self.handle_cancel,
            on_voice_toggle=self.toggle_voice,
            on_wakeword_toggle=self.toggle_wakeword,
            on_clear=self.clear_conversation
        )

        # 4. Status View (Footer)
        self.status_view = StatusView(self.root)

    def run(self) -> int:
        """
        Starts the desktop application.
        Acquires single-instance lock and initializes runtime.
        """
        if not self.single_instance_lock.acquire():
            messagebox.showwarning("JARVIS Active", "Another instance of JARVIS is already running.")
            return 1

        # Initialize JARVIS Runtime
        self.conversation.add_system_notice("Initializing JARVIS desktop runtime...")
        init_ok = self.jarvis_app.initialize()
        
        if not init_ok:
            self.conversation.add_error("Failed to initialize JARVIS runtime. Check logs.")
            self.header.update_status("FAILED")
        else:
            self.header.update_status("READY", self.jarvis_app.hardware_specs.performance_profile.value if self.jarvis_app.hardware_specs else "MEDIUM")
            self.conversation.add_jarvis_message("At your service, Boss. How can I assist you today?")

        # Initialize System Tray
        self.tray_manager.initialize()

        # Start periodic UI Queue and Status updater
        self.root.after(50, self._process_ui_queue)
        self.root.after(2000, self._update_periodic_status)

        try:
            self.root.mainloop()
            return 0
        finally:
            self.single_instance_lock.release()

    def handle_user_submit(self, text: str):
        """Handle command submission from GUI input field."""
        self.conversation.add_boss_message(text)
        self.header.update_status("RUNNING")

        # Execute in background thread to keep UI thread responsive
        worker = threading.Thread(target=self._worker_execute_command, args=(text,), daemon=True)
        self.current_worker_thread = worker
        worker.start()

    def _worker_execute_command(self, text: str):
        """Worker thread executing command through JARVISApp runtime."""
        try:
            self.ui_queue.put(("progress", "Understanding intent"))
            time.sleep(0.05)
            
            res = self.jarvis_app.execute_command(text)
            self.ui_queue.put(("command_result", res))
        except Exception as e:
            logger.error(f"Worker command error: {e}", exc_info=True)
            self.ui_queue.put(("error", str(e)))

    def _process_ui_queue(self):
        """Main UI thread message pump processing background queue updates."""
        try:
            while not self.ui_queue.empty():
                msg_type, payload = self.ui_queue.get_nowait()

                if msg_type == "progress":
                    self.conversation.add_progress(payload)
                elif msg_type == "command_result":
                    self.header.update_status("READY")
                    success = payload.get("success", False)
                    resp_text = payload.get("response", "No response.")
                    verified = payload.get("verified", True)
                    self.conversation.add_jarvis_message(resp_text, verified=verified and success)
                elif msg_type == "error":
                    self.header.update_status("READY")
                    self.conversation.add_error(payload)

        except Exception as e:
            logger.error(f"Error processing UI queue: {e}")
        finally:
            self.root.after(50, self._process_ui_queue)

    def _update_periodic_status(self):
        """Periodically update footer RAM footprint and status."""
        try:
            mem = psutil.Process().memory_info()
            ram_mb = round(mem.rss / (1024 * 1024), 1)
            sched_status = "Active" if (self.jarvis_app.scheduler and not self.safe_mode) else "Safe Mode"
            active_task = "Busy" if self.jarvis_app.lifecycle.state == ApplicationState.RUNNING else "Idle"
            self.status_view.update_metrics(active_task=active_task, ram_mb=ram_mb, scheduler_status=sched_status)
        except Exception:
            pass
        finally:
            self.root.after(3000, self._update_periodic_status)

    def handle_cancel(self):
        """Universal Stop/Cancel button callback."""
        self.conversation.add_system_notice("Cancellation requested by Boss.")
        if self.jarvis_app.orchestrator and self.jarvis_app.orchestrator.cancellation_mgr:
            self.jarvis_app.orchestrator.cancellation_mgr.request_cancellation("User clicked Stop button")
        self.header.update_status("READY")

    def toggle_voice(self):
        self.is_voice_active = not self.is_voice_active
        self.input_view.update_voice_button(self.is_voice_active)
        self.header.update_mic_state("LISTENING" if self.is_voice_active else "READY", is_active=self.is_voice_active)
        state_str = "started" if self.is_voice_active else "stopped"
        self.conversation.add_system_notice(f"Voice microphone listening {state_str}.")

    def toggle_wakeword(self):
        self.is_wakeword_active = not self.is_wakeword_active
        self.input_view.update_wakeword_button(self.is_wakeword_active)
        state_str = "enabled" if self.is_wakeword_active else "disabled"
        self.conversation.add_system_notice(f"Wake word detection ('JARVIS') {state_str}.")

    def clear_conversation(self):
        self.conversation.clear()
        self.conversation.add_jarvis_message("Conversation cleared. Ready for your next command, Boss.")

    def open_doctor(self):
        from jarvis.core.diagnostics import JarvisDoctor, DiagnosticStatus
        results = JarvisDoctor.run_diagnostics()
        diag_lines = [f"[{res.status.value}] {res.component}: {res.message}" for res in results]
        messagebox.showinfo("JARVIS Doctor Diagnostics", "\n".join(diag_lines))

    def open_capabilities(self):
        CapabilitiesView(self.root, self.jarvis_app.capabilities)

    def open_scheduler(self):
        SchedulerView(self.root, self.jarvis_app.scheduler)

    def restore_from_tray(self):
        self.tray_manager.restore_window(self.root)

    def on_close_window(self):
        """Handle window close event (minimize to tray or quit)."""
        self.tray_manager.on_window_minimize(self.root)

    def quit_app(self):
        """Gracefully shut down desktop UI and underlying JARVISApp runtime."""
        self.conversation.add_system_notice("Shutting down JARVIS...")
        try:
            self.jarvis_app.shutdown()
            self.tray_manager.shutdown()
            self.single_instance_lock.release()
            self.root.destroy()
        except Exception as e:
            logger.error(f"Error during desktop app quit: {e}")
            sys.exit(0)
