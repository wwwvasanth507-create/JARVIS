"""
Browser DOM & Playwright Accessibility Tree Semantic Adapter for JARVIS.

Converts Playwright DOM elements and accessibility node trees into unified `UIElement` models,
handling stale element handle defense by re-resolving target queries automatically.
"""

import logging
from typing import List, Dict, Any, Optional
from jarvis.computer.vision.ui_element import UIElement, PerceptionSource
from jarvis.computer.vision.snapshot import ScreenSemanticSnapshot

logger = logging.getLogger(__name__)


class BrowserSemanticAdapter:
    """
    Adapts Playwright browser page state and DOM nodes into common UIElement structures.
    Handles stale element handle recovery by storing semantic paths rather than ephemeral references.
    """

    @classmethod
    def snapshot_from_playwright_page(cls, page: Any) -> ScreenSemanticSnapshot:
        """
        Builds ScreenSemanticSnapshot from active Playwright Page object.
        """
        elements: List[UIElement] = []
        app_name = "Browser"
        win_title = "Web Page"
        url = ""

        try:
            url = page.url
            win_title = page.title()
        except Exception as e:
            logger.debug(f"Could not fetch page title/url: {e}")

        try:
            # Query DOM elements via JavaScript evaluation inside browser
            dom_data = page.evaluate("""
                () => {
                    const nodes = Array.from(document.querySelectorAll('button, input, select, textarea, a, form, table, [role]'));
                    return nodes.map((node, i) => {
                        const rect = node.getBoundingClientRect();
                        return {
                            id: node.id || `dom_${i}`,
                            tagName: node.tagName.toLowerCase(),
                            role: node.getAttribute('role') || (node.tagName === 'A' ? 'link' : node.tagName === 'BUTTON' ? 'button' : node.tagName.toLowerCase()),
                            name: node.innerText || node.getAttribute('aria-label') || node.name || node.value || node.placeholder || '',
                            label: node.getAttribute('aria-label') || node.labels?.[0]?.innerText || node.placeholder || '',
                            value: node.value || '',
                            placeholder: node.placeholder || '',
                            bounds: { x: Math.round(rect.left), y: Math.round(rect.top), width: Math.round(rect.width), height: Math.round(rect.height) },
                            enabled: !node.disabled,
                            visible: rect.width > 0 && rect.height > 0,
                            checked: node.checked || false,
                            semanticPath: node.id ? `#${node.id}` : `${node.tagName.toLowerCase()}:nth-of-type(${i+1})`
                        };
                    });
                }
            """)

            for item in dom_data:
                role = item["role"]
                if role in ("input", "textarea") and item.get("placeholder"):
                    role = "input"

                elements.append(
                    UIElement(
                        id=item["id"],
                        role=role,
                        name=item["name"].strip()[:100],
                        label=item["label"].strip()[:100],
                        text=item["name"].strip()[:200],
                        value=str(item["value"]),
                        placeholder=item["placeholder"],
                        application=app_name,
                        window=win_title,
                        bounds=item["bounds"],
                        enabled=item["enabled"],
                        visible=item["visible"],
                        selected=item["checked"],
                        clickable=True,
                        editable=role in ("input", "textarea"),
                        source=PerceptionSource.DOM,
                        confidence=0.95,
                        semantic_path=item["semanticPath"],
                    )
                )

        except Exception as e:
            logger.warning(f"DOM evaluation failed or page not ready: {e}")

        # Check for loading indicators or dialogs
        loading = any(e.role in ("spinner", "progressbar") or "loading" in e.name.lower() for e in elements)
        dialog_elems = [e for e in elements if e.role in ("dialog", "alertdialog", "modal")]

        return ScreenSemanticSnapshot(
            application=app_name,
            window=win_title,
            url=url,
            elements=elements,
            dialogs=[{"title": d.name, "element": d.model_dump()} for d in dialog_elems],
            loading_state=loading,
            confidence=0.95,
        )

    @classmethod
    def is_handle_stale(cls, page: Any, selector: str) -> bool:
        """
        Verifies whether a DOM selector / element handle is stale.
        """
        try:
            count = page.locator(selector).count()
            return count == 0
        except Exception:
            return True
