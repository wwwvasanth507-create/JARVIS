"""
Structured Selector Engine and Element Resolution Module for JARVIS.
Resolves accessibility roles, labels, text, CSS, XPath, and handles ambiguous element targets.
"""

from typing import Any, Dict, Optional, Tuple
import logging
from playwright.sync_api import Page, Locator

from jarvis.browser.errors import TargetNotFoundError, AmbiguousTargetError

logger = logging.getLogger("jarvis.browser.selectors")


class SelectorEngine:
    """Resolves structured target specifications to Playwright Locators with ambiguity detection."""

    @staticmethod
    def resolve_locator(page: Page, target: Dict[str, Any] | str) -> Tuple[Locator, str]:
        """
        Resolves target specification into Playwright Locator and description string.
        Target Priority: role/name -> label -> text -> css -> xpath
        """
        if isinstance(target, str):
            # Treat simple string as CSS selector or text lookup
            if target.startswith((".", "#", "[", "input", "button", "a", "form")):
                loc = page.locator(target)
                desc = f"CSS selector '{target}'"
            else:
                loc = page.get_by_text(target)
                desc = f"text '{target}'"
        elif isinstance(target, dict):
            role = target.get("role")
            name = target.get("name")
            label = target.get("label")
            text = target.get("text")
            css = target.get("css")
            xpath = target.get("xpath")

            if role:
                kwargs = {}
                if name:
                    kwargs["name"] = name
                loc = page.get_by_role(role, **kwargs)
                desc = f"role '{role}' (name: '{name}')"
            elif label:
                loc = page.get_by_label(label)
                desc = f"label '{label}'"
            elif text:
                loc = page.get_by_text(text)
                desc = f"text '{text}'"
            elif css:
                loc = page.locator(css)
                desc = f"CSS '{css}'"
            elif xpath:
                loc = page.locator(xpath)
                desc = f"XPath '{xpath}'"
            else:
                raise TargetNotFoundError(f"Invalid target specification dict: {target}")
        else:
            raise TargetNotFoundError(f"Unsupported target format: {target}")

        count = loc.count()
        if count == 0:
            raise TargetNotFoundError(f"Target matching {desc} was not found on the page.")
        elif count > 1:
            logger.warning(f"Ambiguous target detected: {count} elements match {desc}")
            # Filter to visible element if possible
            visible_loc = loc.filter(has_text=text) if text else loc.first
            if loc.count() > 1 and not target.get("allow_multiple", False):
                # Return first visible element or raise ambiguous signal
                pass

        return loc.first, desc
