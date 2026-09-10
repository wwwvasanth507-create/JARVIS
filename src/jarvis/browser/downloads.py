"""
Controlled Download Manager for JARVIS Browser Automation.

Handles file downloads, enforces download location boundaries, prevents automatic
execution of downloaded files, and logs download metadata.
"""

from dataclasses import dataclass
from datetime import datetime
import logging
from pathlib import Path
from typing import Optional, Set
from playwright.sync_api import Page, Download

from jarvis.browser.errors import DownloadError, SecurityViolationError

logger = logging.getLogger(__name__)

# Dangerous file extensions requiring untrusted classification & execution prevention
UNTRUSTED_EXTENSIONS: Set[str] = {
    ".exe", ".msi", ".bat", ".cmd", ".ps1", ".vbs", ".sh", ".bash",
    ".scr", ".pif", ".application", ".gadget", ".com", ".cpl", ".hta",
    ".jar", ".wsf", ".wsh", ".reg"
}


@dataclass
class DownloadRecord:
    url: str
    filename: str
    save_path: str
    size_bytes: int
    timestamp: str
    is_executable: bool


class BrowserDownloads:
    """Manages secure file downloads within Playwright sessions."""

    def __init__(self, download_dir: str = "data/downloads") -> None:
        self.download_dir = Path(download_dir).resolve()
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.history: list[DownloadRecord] = []

    def download_file(
        self,
        page: Page,
        trigger_action: callable,
        timeout_ms: float = 30000.0,
    ) -> DownloadRecord:
        """
        Executes a trigger action (e.g. clicking a download button) while listening for Playwright download.
        """
        try:
            with page.expect_download(timeout=timeout_ms) as download_info:
                trigger_action()
            
            download: Download = download_info.value
            return self._process_download(download)
        except Exception as e:
            logger.error("Download failed or timed out: %s", e)
            raise DownloadError(f"Download failed or timed out: {e}") from e

    def save_download(self, download: Download) -> DownloadRecord:
        """Processes an already intercepted Playwright Download object."""
        return self._process_download(download)

    def _process_download(self, download: Download) -> DownloadRecord:
        suggested_name = download.suggested_filename
        target_path = (self.download_dir / suggested_name).resolve()

        # Prevent path traversal attacks
        if not str(target_path).startswith(str(self.download_dir)):
            raise SecurityViolationError(
                f"Path traversal detected in download filename: {suggested_name}"
            )

        # Save to local path
        download.save_as(str(target_path))

        file_size = target_path.stat().st_size if target_path.exists() else 0
        ext = target_path.suffix.lower()
        is_exec = ext in UNTRUSTED_EXTENSIONS

        record = DownloadRecord(
            url=download.url,
            filename=suggested_name,
            save_path=str(target_path),
            size_bytes=file_size,
            timestamp=datetime.now().isoformat(),
            is_executable=is_exec,
        )

        self.history.append(record)
        logger.info(
            "Download completed: %s (size=%d, exec=%s) -> %s",
            suggested_name,
            file_size,
            is_exec,
            target_path,
        )

        if is_exec:
            logger.warning(
                "Downloaded file %s is marked as untrusted/executable. Automatic execution is FORBIDDEN.",
                suggested_name,
            )

        return record

    def list_downloads(self) -> list[DownloadRecord]:
        return list(self.history)
