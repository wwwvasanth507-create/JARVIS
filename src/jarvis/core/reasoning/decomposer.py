"""
Hierarchical Task Decomposer for JARVIS General Reasoning.
Decomposes structured user intent into a multi-level execution tree:
TASK -> SUBTASK -> STEP -> ACTION -> CHECK.
"""

import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from jarvis.core.reasoning.interpreter import StructuredIntent

logger = logging.getLogger("jarvis.core.reasoning.decomposer")


class TaskNode(BaseModel):
    """Represents a single step or action in the hierarchical task plan."""
    step_id: int
    name: str
    action_type: str  # 'DISCOVER', 'LAUNCH_APP', 'READ_DATA', 'COMPOSE', 'PREVIEW', 'CONFIRM', 'EXECUTE_TOOL', 'VERIFY'
    tool_name: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    preconditions: List[str] = Field(default_factory=list)
    verification_check: str = "DEFAULT"
    risk_level: str = "LOW"
    status: str = "PENDING"  # PENDING, RUNNING, COMPLETED, FAILED, CANCELLED


class TaskHierarchy(BaseModel):
    """Hierarchical plan containing ordered execution steps and verification strategy."""
    goal_title: str
    objective: str
    primary_domain: str
    steps: List[TaskNode] = Field(default_factory=list)
    requires_boss_approval: bool = False
    estimated_total_steps: int = 0


class TaskDecomposer:
    """
    Decomposes natural language task intent into a structured, executable hierarchical plan.
    """

    @classmethod
    def decompose(cls, intent: StructuredIntent) -> TaskHierarchy:
        logger.info(f"Decomposing task intent: {intent.objective} ({intent.primary_domain})")
        hierarchy = TaskHierarchy(
            goal_title=intent.raw_query,
            objective=intent.objective,
            primary_domain=intent.primary_domain,
            requires_boss_approval=intent.requires_boss_approval
        )

        steps: List[TaskNode] = []
        step_counter = 1

        # 1. SEND_EMAIL Workflow Decomposition
        if intent.objective == "SEND_EMAIL":
            # Step 1: Discover / Resolve Contact
            steps.append(TaskNode(
                step_id=step_counter,
                name="Resolve Recipient Contact",
                action_type="DISCOVER",
                tool_name="communication.find_contact",
                parameters={"query": intent.recipient or "Boss"},
                verification_check="CONTACT_RESOLVED",
                risk_level="LOW"
            ))
            step_counter += 1

            # Step 2: Compose Email Draft
            steps.append(TaskNode(
                step_id=step_counter,
                name="Compose Email Message",
                action_type="COMPOSE",
                tool_name="communication.compose_email",
                parameters={
                    "recipient": intent.recipient or "Vasanth",
                    "subject": intent.subject or "Message from Boss",
                    "content": intent.content or intent.raw_query
                },
                verification_check="DRAFT_CREATED",
                risk_level="LOW"
            ))
            step_counter += 1

            # Step 3: Render Message Preview for Boss Inspection
            steps.append(TaskNode(
                step_id=step_counter,
                name="Preview Exact Outgoing Message Payload",
                action_type="PREVIEW",
                tool_name="communication.preview_email",
                parameters={"draft_id": "latest"},
                verification_check="PREVIEW_RENDERED",
                risk_level="LOW"
            ))
            step_counter += 1

            # Step 4: Dispatch Email (Requires Boss Approval if policy demands)
            steps.append(TaskNode(
                step_id=step_counter,
                name="Send Email Message",
                action_type="EXECUTE_TOOL",
                tool_name="communication.send_email",
                parameters={"draft_id": "latest"},
                verification_check="DISPATCHED",
                risk_level="HIGH" if intent.requires_boss_approval else "LOW"
            ))
            step_counter += 1

            # Step 5: Verify Sent State
            steps.append(TaskNode(
                step_id=step_counter,
                name="Verify Message Sent State",
                action_type="VERIFY",
                tool_name="communication.verify_sent",
                parameters={"recipient": intent.recipient or "Vasanth"},
                verification_check="SENT_CONFIRMED",
                risk_level="LOW"
            ))

        # 2. CROSS_APP_WORKFLOW Decomposition
        elif intent.objective == "CROSS_APP_WORKFLOW":
            doc_path = intent.target_path
            if not doc_path:
                import re
                m = re.search(r"([A-Za-z0-9_\-/\\]+\.[a-zA-Z0-9]+)", intent.raw_query)
                if m:
                    doc_path = m.group(1)

            steps.append(TaskNode(
                step_id=1,
                name="Locate and Read Input Document",
                action_type="READ_DATA",
                tool_name="document.extract_text",
                parameters={"path": doc_path or "monthly_report.txt"},
                verification_check="DOCUMENT_EXTRACTED",
                risk_level="LOW"
            ))
            if intent.recipient:
                steps.append(TaskNode(
                    step_id=2,
                    name="Resolve Target Recipient & Channel",
                    action_type="DISCOVER",
                    tool_name="communication.find_contact",
                    parameters={"query": intent.recipient},
                    verification_check="TARGET_FOUND",
                    risk_level="LOW"
                ))
            else:
                steps.append(TaskNode(
                    step_id=2,
                    name="Discover Target Application & Form",
                    action_type="DISCOVER",
                    tool_name="filesystem.list_directory",
                    parameters={"path": "."},
                    verification_check="TARGET_FOUND",
                    risk_level="LOW"
                ))
            steps.append(TaskNode(
                step_id=3,
                name="Transfer Extracted Data to Target",
                action_type="EXECUTE_TOOL",
                tool_name="communication.compose_email" if intent.recipient else "computer.fill_form",
                parameters={"content": intent.raw_query, "recipient": intent.recipient or "Vasanth", "subject": intent.subject or "Report Summary"},
                verification_check="DATA_TRANSFERRED",
                risk_level="LOW"
            ))

        # 3. FILESYSTEM_OPERATION Decomposition
        elif intent.objective == "FILESYSTEM_OPERATION":
            if "read" in intent.raw_query.lower() or "find" in intent.raw_query.lower():
                steps.append(TaskNode(
                    step_id=1,
                    name="Search / Read Filesystem Location",
                    action_type="EXECUTE_TOOL",
                    tool_name="filesystem.search" if "find" in intent.raw_query.lower() else "filesystem.read_file",
                    parameters={"root_path": intent.target_path or "data/test_workspace"} if "find" in intent.raw_query.lower() else {"path": intent.target_path or "data/test_workspace"},
                    verification_check="FILESYSTEM_READ",
                    risk_level="LOW"
                ))
            else:
                steps.append(TaskNode(
                    step_id=1,
                    name="Execute Filesystem Write Operation",
                    action_type="EXECUTE_TOOL",
                    tool_name="filesystem.create_file",
                    parameters={"path": intent.target_path or "data/test_workspace/output.txt", "content": intent.content or "JARVIS Output", "overwrite": True},
                    verification_check="FILE_WRITTEN",
                    risk_level="LOW"
                ))

        # 4. BROWSER_NAVIGATION Decomposition
        elif intent.objective == "BROWSER_NAVIGATION":
            steps.append(TaskNode(
                step_id=1,
                name="Navigate Browser to Target URL",
                action_type="EXECUTE_TOOL",
                tool_name="browser.open",
                parameters={"url": intent.target_url or "https://example.com", "headless": True},
                verification_check="BROWSER_OPENED",
                risk_level="LOW"
            ))
            steps.append(TaskNode(
                step_id=2,
                name="Read Page Content and Structure",
                action_type="VERIFY",
                tool_name="browser.read_page",
                parameters={},
                verification_check="PAGE_READ",
                risk_level="LOW"
            ))

        # 5. APPLICATION_CONTROL Decomposition
        elif intent.objective == "APPLICATION_CONTROL":
            steps.append(TaskNode(
                step_id=1,
                name="Launch or Focus Application",
                action_type="LAUNCH_APP",
                tool_name="application.open",
                parameters={"app_name": intent.target_app or "notepad.exe"},
                verification_check="APP_RUNNING",
                risk_level="LOW"
            ))

        # 6. Fallback General Task Node
        else:
            steps.append(TaskNode(
                step_id=1,
                name="Execute General System Command",
                action_type="EXECUTE_TOOL",
                tool_name="system.get_info",
                parameters={},
                verification_check="STATUS_OK",
                risk_level="LOW"
            ))

        hierarchy.steps = steps
        hierarchy.estimated_total_steps = len(steps)
        return hierarchy
