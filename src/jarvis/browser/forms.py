"""
Form Automation & Interaction Module for JARVIS Browser Automation.

Supports filling input fields, selecting dropdown options, toggling checkboxes/radio buttons,
and submitting forms with sensitive action risk classification.
"""

from dataclasses import dataclass
import logging
from typing import Any, Dict, List, Optional, Union
from playwright.sync_api import Page

from jarvis.browser.errors import TargetNotFoundError, SecurityViolationError
from jarvis.browser.selectors import SelectorEngine

logger = logging.getLogger(__name__)

# Keywords indicating potentially sensitive form actions
SENSITIVE_FORM_KEYWORDS = {
    "password", "passcode", "credit_card", "card_number", "cvv", "ssn",
    "delete_account", "transfer", "pay", "checkout", "purchase", "billing"
}


@dataclass
class FormField:
    name: str
    type: str
    value: str
    label: str


class BrowserForms:
    """Manages web form interactions with input field validation and risk identification."""

    def __init__(self, selector_engine: Optional[SelectorEngine] = None) -> None:
        self.selector_engine = selector_engine or SelectorEngine()

    def select_option(
        self,
        page: Page,
        target: Union[str, dict],
        value: Optional[str] = None,
        label: Optional[str] = None,
        index: Optional[int] = None,
        timeout_ms: float = 5000.0,
    ) -> List[str]:
        """Selects option(s) in a select dropdown."""
        selector = self.selector_engine.resolve(page, target, timeout_ms=timeout_ms)
        kw: Dict[str, Any] = {}
        if value is not None:
            kw["value"] = value
        elif label is not None:
            kw["label"] = label
        elif index is not None:
            kw["index"] = index
        else:
            raise ValueError("Must specify value, label, or index for select_option")

        selected = page.select_option(selector, **kw, timeout=timeout_ms)
        logger.info("Selected option %s in dropdown %s", selected, selector)
        return selected

    def set_checkbox(
        self,
        page: Page,
        target: Union[str, dict],
        checked: bool = True,
        timeout_ms: float = 5000.0,
    ) -> bool:
        """Checks or unchecks a checkbox or radio button."""
        selector = self.selector_engine.resolve(page, target, timeout_ms=timeout_ms)
        if checked:
            page.check(selector, timeout=timeout_ms)
        else:
            page.uncheck(selector, timeout=timeout_ms)
        logger.info("Set checkbox %s checked state to %s", selector, checked)
        return True

    def fill_form(
        self,
        page: Page,
        fields: Dict[Union[str, dict], str],
        timeout_ms: float = 5000.0,
    ) -> bool:
        """
        Fills multiple form fields specified by target -> text mapping.
        """
        for target, text_val in fields.items():
            self._check_field_sensitivity(target, text_val)
            selector = self.selector_engine.resolve(page, target, timeout_ms=timeout_ms)
            page.fill(selector, str(text_val), timeout=timeout_ms)
            logger.info("Filled form field %s with value", selector)
        return True

    def submit_form(
        self,
        page: Page,
        target: Optional[Union[str, dict]] = None,
        timeout_ms: float = 5000.0,
    ) -> bool:
        """Submits a form by clicking its submit button or pressing Enter."""
        if target:
            selector = self.selector_engine.resolve(page, target, timeout_ms=timeout_ms)
            page.click(selector, timeout=timeout_ms)
        else:
            # Fall back to pressing Enter on active element or first submit button
            submit_btn = page.query_selector("button[type='submit'], input[type='submit']")
            if submit_btn:
                submit_btn.click(timeout=timeout_ms)
            else:
                page.keyboard.press("Enter")
        logger.info("Submitted form on page %s", page.url)
        return True

    def _check_field_sensitivity(self, target: Union[str, dict], val: str) -> None:
        target_str = str(target).lower()
        if any(kw in target_str for kw in SENSITIVE_FORM_KEYWORDS):
            logger.warning("Interacting with potentially sensitive form field: %s", target_str)
