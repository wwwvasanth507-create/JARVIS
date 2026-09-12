"""
Notification Delivery Manager for JARVIS Scheduler.
Supports Text, Desktop, and Voice notification channels with fallback handling.
"""

import logging
from typing import Optional, Dict, Any

logger = logging.getLogger("jarvis.scheduler.notifications")


class NotificationManager:
    """Manages reminder and alert delivery across available output channels."""

    def __init__(self, voice_manager: Optional[Any] = None):
        self.voice_manager = voice_manager

    def notify_text(self, message: str, title: str = "JARVIS Reminder") -> bool:
        """Prints text notification to standard output / UI stream."""
        logger.info(f"[{title}] {message}")
        print(f"\n[JARVIS REMINDER] {title}: {message}\n")
        return True

    def notify_desktop(self, message: str, title: str = "JARVIS Reminder") -> bool:
        """Sends desktop notification if available, with text fallback."""
        try:
            # Attempt win10toast or plyer if installed
            import win10toast  # type: ignore
            toaster = win10toast.ToastNotifier()
            toaster.show_toast(title, message, duration=5, threaded=True)
            return True
        except Exception:
            # Fallback to text
            return self.notify_text(message, title=title)

    def notify_voice(self, message: str) -> bool:
        """Synthesizes voice speech notification if voice manager available, fallback to text."""
        if self.voice_manager and hasattr(self.voice_manager, "speak"):
            try:
                self.voice_manager.speak(message)
                return True
            except Exception as e:
                logger.warning(f"Voice notification failed: {e}, falling back to text")

        return self.notify_text(message, title="JARVIS Voice Reminder")

    def notify(self, message: str, notification_type: str = "TEXT", title: str = "JARVIS Reminder") -> bool:
        """Dispatches notification using requested delivery channel with fallback."""
        ntype = notification_type.upper()
        if ntype == "VOICE":
            return self.notify_voice(message)
        elif ntype == "DESKTOP":
            return self.notify_desktop(message, title=title)
        else:
            return self.notify_text(message, title=title)

    def deliver(self, notification_type: str, message: str, title: str = "JARVIS Reminder") -> bool:
        """Alias method for dispatching notifications."""
        return self.notify(message=message, notification_type=notification_type, title=title)
