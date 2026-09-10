"""
Screen capture provider with privacy integration and mode selection.
"""

import time
import logging
from typing import Optional, Tuple, Dict, Any
from PIL import Image, ImageGrab
from jarvis.computer.vision.models import CaptureMode
from jarvis.computer.vision.privacy import ScreenPrivacyPolicy
from jarvis.computer.windows.screen import WindowsScreen
from jarvis.computer.windows.window import WindowsWindowManager

logger = logging.getLogger("jarvis.computer.vision.capture")


class ScreenCapture:
    """
    Captures full screen, active window, or bounded regions with privacy validation.
    """

    def __init__(self, privacy_policy: Optional[ScreenPrivacyPolicy] = None):
        self.privacy_policy = privacy_policy or ScreenPrivacyPolicy()

    def capture(
        self,
        mode: CaptureMode = CaptureMode.FULL_SCREEN,
        region: Optional[Tuple[int, int, int, int]] = None
    ) -> Dict[str, Any]:
        """
        Captures screenshot according to requested mode.
        Returns dict containing PIL Image and metadata.
        """
        active_window_title = "Desktop"
        try:
            active_info = WindowsWindowManager.get_active_window()
            if active_info:
                active_window_title = active_info.title
        except Exception:
            pass

        # Privacy validation
        self.privacy_policy.validate_screen_capture_allowed(active_window_title)

        start = time.perf_counter()
        img: Image.Image
        source_str = "full_screen"

        def _safe_grab_full() -> Image.Image:
            try:
                return ImageGrab.grab()
            except Exception:
                sz = WindowsScreen.get_screen_size()
                return Image.new("RGB", (sz.width, sz.height), (24, 24, 32))

        def _safe_grab_region(reg: Tuple[int, int, int, int]) -> Image.Image:
            try:
                x, y, w, h = reg
                return ImageGrab.grab(bbox=(x, y, x + w, y + h))
            except Exception:
                return Image.new("RGB", (reg[2], reg[3]), (24, 24, 32))

        if mode == CaptureMode.ACTIVE_WINDOW:
            res = WindowsScreen.screenshot(active_window_only=True)
            source_str = f"active_window ({active_window_title})"
            if res.success and res.data.get("saved_path"):
                img = Image.open(res.data["saved_path"])
            else:
                img = _safe_grab_full()

        elif mode == CaptureMode.REGION and region:
            source_str = f"region {region}"
            res = WindowsScreen.screenshot(region=region)
            if res.success and res.data.get("saved_path"):
                img = Image.open(res.data["saved_path"])
            else:
                img = _safe_grab_region(region)

        else: # FULL_SCREEN
            source_str = "full_screen"
            res = WindowsScreen.screenshot()
            if res.success and res.data.get("saved_path"):
                img = Image.open(res.data["saved_path"])
            else:
                img = _safe_grab_full()

        dur = time.perf_counter() - start

        return {
            "image": img,
            "width": img.width,
            "height": img.height,
            "active_window": active_window_title,
            "mode": mode.value,
            "source": source_str,
            "timestamp": time.time(),
            "duration_seconds": round(dur, 4)
        }

    def capture_full_screen(self) -> Dict[str, Any]:

        return self.capture(CaptureMode.FULL_SCREEN)

    def capture_window(self) -> Dict[str, Any]:
        return self.capture(CaptureMode.ACTIVE_WINDOW)

    def capture_region(self, region: Tuple[int, int, int, int]) -> Dict[str, Any]:
        return self.capture(CaptureMode.REGION, region=region)
