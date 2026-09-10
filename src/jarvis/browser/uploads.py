"""
Controlled Upload Manager for JARVIS Browser Automation.

Validates file upload paths, verifies file safety, and handles set_input_files actions.
"""

import logging
from pathlib import Path
from typing import List, Union
from playwright.sync_api import Page

from jarvis.browser.errors import TargetNotFoundError, SecurityViolationError
from jarvis.browser.selectors import SelectorEngine

logger = logging.getLogger(__name__)

# Files/extensions that must never be uploaded without explicit authorization
SENSITIVE_PATTERNS = {
    ".env", ".pem", ".key", ".id_rsa", ".id_ed25519", "shadow", "passwd",
    "credentials", "token", "secret", "private_key"
}


class BrowserUploads:
    """Manages file uploads to webpages with security checks."""

    def __init__(self, selector_engine: Optional[SelectorEngine] = None) -> None:
        self.selector_engine = selector_engine or SelectorEngine()

    def upload_files(
        self,
        page: Page,
        target: Union[str, dict],
        file_paths: Union[str, Path, List[Union[str, Path]]],
        timeout_ms: float = 5000.0,
    ) -> bool:
        """
        Uploads local file(s) to a input[type=file] element specified by target.
        """
        paths = [file_paths] if isinstance(file_paths, (str, Path)) else file_paths
        resolved_paths: List[str] = []

        for path_item in paths:
            file_path = Path(path_item).resolve()
            
            # Check existence
            if not file_path.exists():
                raise TargetNotFoundError(f"Upload source file not found: {file_path}")

            if not file_path.is_file():
                raise TargetNotFoundError(f"Upload path is not a file: {file_path}")

            # Check sensitive patterns
            file_name_lower = file_path.name.lower()
            if any(pat in file_name_lower for pat in SENSITIVE_PATTERNS):
                raise SecurityViolationError(
                    f"Refusing to upload potentially sensitive file: {file_path.name}"
                )

            resolved_paths.append(str(file_path))

        # Resolve file input selector
        selector = self.selector_engine.resolve(page, target, timeout_ms=timeout_ms)
        logger.info("Uploading %d file(s) to selector %s: %s", len(resolved_paths), selector, resolved_paths)

        page.set_input_files(selector, resolved_paths, timeout=timeout_ms)
        return True
