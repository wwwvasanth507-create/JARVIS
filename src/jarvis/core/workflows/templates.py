"""
Declarative Workflow Templates for Common Daily Tasks in JARVIS.
"""

from typing import Dict, Any, List, Optional
from jarvis.core.workflows.engine import Workflow, WorkflowStep, WorkflowState


class WorkflowTemplateRegistry:
    """Provides declarative, parameterized, permission-aware workflow templates."""

    @staticmethod
    def get_template(template_name: str, params: Optional[Dict[str, Any]] = None) -> Workflow:
        params = params or {}

        if template_name == "research_and_save":
            query = params.get("query", "JARVIS research")
            out_file = params.get("out_file", "C:\\temp\\research_summary.md")
            steps = [
                WorkflowStep(name="Web Search", tool_name="browser.search", arguments={"query": query}),
                WorkflowStep(name="Summarize Results", tool_name="doc.summarize", arguments={"text": f"Results for {query}"}),
                WorkflowStep(name="Save File", tool_name="filesystem.write_file", arguments={"path": out_file, "content": "Summary"}),
            ]
            return Workflow(name="Research & Save", goal=f"Research '{query}' and save to {out_file}", steps=steps, state=WorkflowState.READY)

        elif template_name == "find_and_summarize_file":
            pattern = params.get("pattern", "*.pdf")
            steps = [
                WorkflowStep(name="Find File", tool_name="filesystem.search", arguments={"query": pattern}),
                WorkflowStep(name="Inspect Document", tool_name="doc.inspect", arguments={"path": "candidate.pdf"}),
                WorkflowStep(name="Summarize Document", tool_name="doc.summarize", arguments={"path": "candidate.pdf"}),
            ]
            return Workflow(name="Find & Summarize File", goal=f"Find matching '{pattern}' and summarize", steps=steps, state=WorkflowState.READY)

        elif template_name == "organize_downloads":
            target_dir = params.get("target_dir", "Downloads")
            steps = [
                WorkflowStep(name="Scan Directory", tool_name="filesystem.list_directory", arguments={"path": target_dir}),
                WorkflowStep(name="Propose Organization", tool_name="filesystem.organize", arguments={"path": target_dir, "dry_run": True}),
            ]
            return Workflow(name="Organize Downloads", goal=f"Scan and organize '{target_dir}' directory", steps=steps, state=WorkflowState.READY)

        elif template_name == "browser_research":
            topic = params.get("topic", "AI progress")
            steps = [
                WorkflowStep(name="Open Browser", tool_name="browser.open", arguments={"url": f"https://google.com/search?q={topic}"}),
                WorkflowStep(name="Read Content", tool_name="browser.get_text", arguments={}),
            ]
            return Workflow(name="Browser Research", goal=f"Conduct web research on '{topic}'", steps=steps, state=WorkflowState.READY)

        elif template_name == "scheduled_report":
            cron = params.get("cron", "0 9 * * 1")
            steps = [
                WorkflowStep(name="Schedule Recurring Task", tool_name="scheduler.create", arguments={"command": "Check Weekly Report", "cron": cron}),
            ]
            return Workflow(name="Scheduled Report", goal=f"Schedule recurring report with cron '{cron}'", steps=steps, state=WorkflowState.READY)

        else:
            raise ValueError(f"Unknown workflow template: '{template_name}'")
