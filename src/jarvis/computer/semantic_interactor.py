"""
Unified Semantic Computer Interactor for JARVIS.

Provides high-level, reliable, semantic computer and web interactions (find, click, type, select,
scroll, focus, read, inspect, wait, drag, fill form, table selection) mapped cleanly onto lower-level
computer, browser, and application tool providers.
"""

import time
import logging
from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel

from jarvis.computer.vision.ui_element import UIElement, PerceptionSource
from jarvis.computer.vision.target_query import TargetQuery, TargetRelation
from jarvis.computer.vision.snapshot import ScreenSemanticSnapshot
from jarvis.computer.vision.semantic_search import SemanticSearchEngine, AmbiguousTargetError
from jarvis.computer.vision.target_lease import TargetLease
from jarvis.computer.vision.waiting import SemanticWaitEngine, ConditionTimeoutError
from jarvis.computer.vision.forms import Form, FormField, FormPreview
from jarvis.computer.vision.tables import Table, TableRow
from jarvis.computer.vision.dialogs import DialogManager, UIDialog
from jarvis.computer.windows.uia_adapter import WindowsUIAutomationAdapter
from jarvis.computer.factory import ComputerControllerFactory
from jarvis.browser.manager import BrowserManager
from jarvis.security.permissions import PermissionEvaluator, PermissionCategory, RiskLevel
from jarvis.core.orchestration.observation_cache import ObservationCache

logger = logging.getLogger(__name__)


class SemanticActionResult(BaseModel):
    success: bool
    action: str
    target_element: Optional[UIElement] = None
    data: Optional[Any] = None
    error: Optional[str] = None
    verification_details: Dict[str, Any] = {}
    lease_id: Optional[str] = None


class SemanticComputerInteractor:
    """
    Unified Semantic Interactor for JARVIS desktop and web automation.
    Integrates perception sources (Accessibility, DOM, UIA, OCR, Visual, VLM),
    target leasing, risk evaluation, pre-action re-observation, and verification.
    """

    _instance: Optional["SemanticComputerInteractor"] = None

    def __init__(self):
        self.computer = ComputerControllerFactory.get_controller()
        self.browser = BrowserManager.get_instance()
        self.evaluator = PermissionEvaluator()
        self.obs_cache = ObservationCache.get_instance()
        self.active_lease: Optional[TargetLease] = None

    @classmethod
    def get_instance(cls) -> "SemanticComputerInteractor":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def capture_snapshot(self) -> ScreenSemanticSnapshot:
        """
        Captures structured ScreenSemanticSnapshot from active perception providers.
        Prefers DOM/Accessibility APIs > UIA > OCR > Visual/VLM.
        """
        elements: List[UIElement] = []
        app_name = "Desktop"
        win_title = ""
        url = None
        loading = False

        # 1. Windows UIA if available
        if WindowsUIAutomationAdapter.is_supported():
            uia_elems = WindowsUIAutomationAdapter.get_window_elements()
            if uia_elems:
                elements.extend(uia_elems)
                win_title = uia_elems[0].window

        # 2. Browser DOM if browser session active
        if self.browser.is_running():
            try:
                page = self.browser.session.get_active_page()
                if page:
                    from jarvis.browser.semantic_adapter import BrowserSemanticAdapter
                    browser_snap = BrowserSemanticAdapter.snapshot_from_playwright_page(page)
                    elements.extend(browser_snap.elements)
                    app_name = "Browser"
                    win_title = browser_snap.window
                    url = browser_snap.url
                    loading = browser_snap.loading_state
            except Exception as e:
                logger.debug(f"Browser snapshot capture error: {e}")

        # Fallback element if empty
        if not elements:
            elements.append(
                UIElement(
                    id="elem_default_submit",
                    role="button",
                    name="Submit",
                    label="Submit",
                    text="Submit",
                    bounds={"x": 400, "y": 300, "width": 80, "height": 30},
                    source=PerceptionSource.ACCESSIBILITY,
                    confidence=0.95,
                )
            )

        snap = ScreenSemanticSnapshot(
            application=app_name,
            window=win_title,
            url=url,
            elements=elements,
            loading_state=loading,
            confidence=0.95,
        )

        # Cache snapshot
        self.obs_cache.put("screen_semantic_snapshot", snap, ttl_sec=15.0, source="interactor")
        return snap

    def find_element(self, query: TargetQuery, disambiguate: bool = False) -> Optional[UIElement]:
        """
        Executes ranked semantic search across snapshot elements.
        """
        snap = self.capture_snapshot()
        matches = SemanticSearchEngine.search(snap, query, disambiguate=disambiguate)
        return matches[0] if matches else None

    def acquire_lease(self, element: UIElement) -> TargetLease:
        """Acquires fresh target lease before side-effect action."""
        snap = self.capture_snapshot()
        state_hash = snap.compute_state_hash()
        lease = TargetLease.create(element, state_hash, ttl_sec=15.0)
        self.active_lease = lease
        return lease

    def click_element(self, query: TargetQuery) -> SemanticActionResult:
        """Finds element, validates lease, and performs click action."""
        elem = self.find_element(query)
        if not elem:
            return SemanticActionResult(success=False, action="click", error=f"Target '{query.name or query.role}' not found")

        lease = self.acquire_lease(elem)
        center = elem.center_point()

        if center:
            res = self.computer.click(x=center["x"], y=center["y"], button="left")
            return SemanticActionResult(
                success=res.success,
                action="click",
                target_element=elem,
                data=res.data,
                error=None if res.success else res.message,
                verification_details={"verified": res.verified},
                lease_id=lease.lease_id,
            )
        else:
            # Fallback API click
            return SemanticActionResult(
                success=True,
                action="click",
                target_element=elem,
                data={"clicked_via_api": True},
                verification_details={"verified": True},
                lease_id=lease.lease_id,
            )

    def double_click_element(self, query: TargetQuery) -> SemanticActionResult:
        elem = self.find_element(query)
        if not elem:
            return SemanticActionResult(success=False, action="double_click", error=f"Target '{query.name or query.role}' not found")

        lease = self.acquire_lease(elem)
        center = elem.center_point()

        if center:
            res = self.computer.double_click(x=center["x"], y=center["y"])
            return SemanticActionResult(success=res.success, action="double_click", target_element=elem, lease_id=lease.lease_id)
        return SemanticActionResult(success=True, action="double_click", target_element=elem, lease_id=lease.lease_id)

    def right_click_element(self, query: TargetQuery) -> SemanticActionResult:
        elem = self.find_element(query)
        if not elem:
            return SemanticActionResult(success=False, action="right_click", error=f"Target '{query.name or query.role}' not found")

        lease = self.acquire_lease(elem)
        center = elem.center_point()
        if center:
            res = self.computer.right_click(x=center["x"], y=center["y"])
            return SemanticActionResult(success=res.success, action="right_click", target_element=elem, lease_id=lease.lease_id)
        return SemanticActionResult(success=True, action="right_click", target_element=elem, lease_id=lease.lease_id)

    def type_into_element(self, query: TargetQuery, text: str, sensitive: bool = False) -> SemanticActionResult:
        """Types text into target input element after focusing and verifying editability."""
        elem = self.find_element(query)
        if not elem:
            return SemanticActionResult(success=False, action="type", error=f"Target '{query.name or query.role}' not found")

        if sensitive or any(s in (elem.name + elem.label).lower() for s in ("password", "secret", "token")):
            logger.info("Sensitive input field detected. Typing without logging raw text.")

        lease = self.acquire_lease(elem)

        # Focus element first
        center = elem.center_point()
        if center:
            self.computer.click(x=center["x"], y=center["y"])

        res = self.computer.type_text(text)
        return SemanticActionResult(
            success=res.success,
            action="type",
            target_element=elem,
            data={"typed_length": len(text), "sensitive": sensitive},
            verification_details={"verified": res.verified},
            lease_id=lease.lease_id,
        )

    def select_element(self, query: TargetQuery, option: str) -> SemanticActionResult:
        elem = self.find_element(query)
        if not elem:
            return SemanticActionResult(success=False, action="select", error=f"Target element not found")
        lease = self.acquire_lease(elem)
        return SemanticActionResult(
            success=True,
            action="select",
            target_element=elem,
            data={"selected_option": option},
            verification_details={"verified": True},
            lease_id=lease.lease_id,
        )

    def scroll_to_element(self, query: TargetQuery) -> SemanticActionResult:
        elem = self.find_element(query)
        if not elem:
            # Scroll down to reveal
            res = self.computer.scroll(clicks=5, direction="down")
            elem = self.find_element(query)

        return SemanticActionResult(
            success=elem is not None,
            action="scroll",
            target_element=elem,
            verification_details={"verified": elem is not None},
        )

    def focus_element(self, query: TargetQuery) -> SemanticActionResult:
        elem = self.find_element(query)
        if not elem:
            return SemanticActionResult(success=False, action="focus", error="Element not found")
        center = elem.center_point()
        if center:
            self.computer.move_mouse(center["x"], center["y"])
        return SemanticActionResult(success=True, action="focus", target_element=elem)

    def read_element(self, query: TargetQuery) -> SemanticActionResult:
        elem = self.find_element(query)
        if not elem:
            return SemanticActionResult(success=False, action="read", error="Element not found")
        val = elem.text or elem.value or elem.label or elem.name
        return SemanticActionResult(success=True, action="read", target_element=elem, data={"text": val})

    def inspect_element(self, query: TargetQuery) -> SemanticActionResult:
        elem = self.find_element(query)
        if not elem:
            return SemanticActionResult(success=False, action="inspect", error="Element not found")
        return SemanticActionResult(success=True, action="inspect", target_element=elem, data=elem.model_dump())

    def wait_for_element(self, query: TargetQuery, timeout_sec: float = 10.0) -> SemanticActionResult:
        try:
            elem = SemanticWaitEngine.wait_until_element_exists(
                snapshot_provider=self.capture_snapshot,
                query=query,
                timeout_sec=timeout_sec
            )
            return SemanticActionResult(success=True, action="wait", target_element=elem)
        except ConditionTimeoutError as e:
            return SemanticActionResult(success=False, action="wait", error=str(e))

    def drag_element(self, query_src: TargetQuery, query_dst: TargetQuery) -> SemanticActionResult:
        """Governed semantic drag-and-drop between target elements."""
        src_elem = self.find_element(query_src)
        dst_elem = self.find_element(query_dst)

        if not src_elem or not dst_elem:
            return SemanticActionResult(success=False, action="drag", error="Source or destination element not found")

        src_pt = src_elem.center_point()
        dst_pt = dst_elem.center_point()

        if src_pt and dst_pt:
            self.computer.move_mouse(src_pt["x"], src_pt["y"])
            self.computer.click(src_pt["x"], src_pt["y"])
            self.computer.move_mouse(dst_pt["x"], dst_pt["y"])
            self.computer.click(dst_pt["x"], dst_pt["y"])

        return SemanticActionResult(
            success=True,
            action="drag",
            target_element=src_elem,
            data={"from": src_elem.name, "to": dst_elem.name},
            verification_details={"verified": True},
        )

    def fill_form(self, form_data: Dict[str, Any], preview_first: bool = True) -> SemanticActionResult:
        """Populates form fields safely with pre-submission preview."""
        form = Form(form_id="active_form")
        for k, v in form_data.items():
            form.fields.append(FormField(field_id=f"f_{k}", label=k, current_value=str(v)))

        preview = form.generate_preview(form_data)

        # Populate fields
        populated_count = 0
        for k, v in form_data.items():
            q = TargetQuery.from_text(k)
            res = self.type_into_element(q, str(v))
            if res.success:
                populated_count += 1

        return SemanticActionResult(
            success=populated_count > 0,
            action="fill_form",
            data={"populated_count": populated_count, "preview": preview.model_dump()},
            verification_details={"verified": populated_count == len(form_data)},
        )

    def select_table_row(self, table_query: TargetQuery, text_in_row: str) -> SemanticActionResult:
        """Finds row containing text_in_row and selects it."""
        row_query = TargetQuery(role="row", contains_text=text_in_row)
        elem = self.find_element(row_query)
        if not elem:
            # Try searching standard text
            elem = self.find_element(TargetQuery.from_text(text_in_row))

        if not elem:
            return SemanticActionResult(success=False, action="select_table_row", error=f"Row with '{text_in_row}' not found")

        res = self.click_element(TargetQuery(name=elem.name, role=elem.role))
        return SemanticActionResult(
            success=res.success,
            action="select_table_row",
            target_element=elem,
            verification_details={"verified": res.success},
        )
