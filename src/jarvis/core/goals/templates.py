"""
Declarative Goal Templates Registry for JARVIS.
"""

import logging
from typing import Dict, List, Optional
from jarvis.core.goals.models import GoalTemplate, AutonomyLevel
from jarvis.security.permissions import RiskLevel

logger = logging.getLogger("jarvis.core.goals.templates")


class GoalTemplateRegistry:
    """Registry for built-in declarative goal templates."""

    def __init__(self):
        self._templates: Dict[str, GoalTemplate] = {}
        self._load_builtin_templates()

    def register(self, template: GoalTemplate) -> None:
        self._templates[template.template_id] = template

    def get_template(self, template_id: str) -> Optional[GoalTemplate]:
        return self._templates.get(template_id)

    def list_templates(self) -> List[GoalTemplate]:
        return list(self._templates.values())

    def _load_builtin_templates(self) -> None:
        templates = [
            GoalTemplate(
                template_id="project_health",
                name="Project Health & Test Suite Monitor",
                description="Continuously monitor project workspace, execute unit tests, and report failures.",
                required_capabilities=["shell", "filesystem", "notification"],
                risk_level=RiskLevel.MEDIUM,
                default_autonomy_level=AutonomyLevel.LEVEL_2_SUPERVISED,
                objective_templates=[
                    {"title": "Inspect project workspace", "description": "Verify source files and test suite structure."},
                    {"title": "Run test suite", "description": "Execute pytest and record test pass/fail results."},
                    {"title": "Generate health summary", "description": "Summarize test outcomes and alert Boss on failures."},
                ],
            ),
            GoalTemplate(
                template_id="document_processing",
                name="Multi-Document Intelligence & Processing",
                description="Batch process, extract tables, chunk, and summarize a set of target documents.",
                required_capabilities=["document", "filesystem"],
                risk_level=RiskLevel.LOW,
                default_autonomy_level=AutonomyLevel.LEVEL_1_ASSISTED,
                objective_templates=[
                    {"title": "Discover target documents", "description": "Scan folder for un-processed documents."},
                    {"title": "Extract and chunk text", "description": "Normalize text and extract key tables."},
                    {"title": "Summarize findings", "description": "Create unified summary document with grounded citations."},
                ],
            ),
            GoalTemplate(
                template_id="weekly_report",
                name="Weekly Status & Activity Report",
                description="Gather weekly project activity, task history, and format status report.",
                required_capabilities=["memory", "filesystem", "notification"],
                risk_level=RiskLevel.LOW,
                default_autonomy_level=AutonomyLevel.LEVEL_3_SCHEDULED,
                objective_templates=[
                    {"title": "Query activity history", "description": "Fetch completed tasks and key memory events."},
                    {"title": "Compile status report", "description": "Write Markdown report into documents folder."},
                    {"title": "Notify Boss", "description": "Send notification with report summary."},
                ],
            ),
            GoalTemplate(
                template_id="download_organization",
                name="Download Directory Cleanup & Organization",
                description="Scan and organize downloaded files into categorized subfolders by extension.",
                required_capabilities=["filesystem"],
                risk_level=RiskLevel.MEDIUM,
                default_autonomy_level=AutonomyLevel.LEVEL_1_ASSISTED,
                objective_templates=[
                    {"title": "Scan Downloads folder", "description": "List files and compute categories."},
                    {"title": "Stage duplicate detection", "description": "Identify potential duplicate files."},
                    {"title": "Move files safely", "description": "Move files to appropriate subfolders with backup."},
                ],
            ),
            GoalTemplate(
                template_id="scheduled_monitoring",
                name="System & Process Health Monitoring",
                description="Periodic monitoring of system resources, desktop apps, and long-running tasks.",
                required_capabilities=["system", "notification"],
                risk_level=RiskLevel.LOW,
                default_autonomy_level=AutonomyLevel.LEVEL_3_SCHEDULED,
                objective_templates=[
                    {"title": "Inspect system metrics", "description": "Measure CPU, RAM, and disk utilization."},
                    {"title": "Check active applications", "description": "Verify running state of key applications."},
                    {"title": "Alert on resource pressure", "description": "Notify Boss if thresholds are exceeded."},
                ],
            ),
            GoalTemplate(
                template_id="research_and_summary",
                name="Topic Research & Structured Summary",
                description="Perform web search, extract web content, and compile a structured research report.",
                required_capabilities=["browser", "filesystem"],
                risk_level=RiskLevel.MEDIUM,
                default_autonomy_level=AutonomyLevel.LEVEL_1_ASSISTED,
                objective_templates=[
                    {"title": "Perform topic search", "description": "Query browser/search tools for target topic."},
                    {"title": "Extract page contents", "description": "Parse key web page text and citations."},
                    {"title": "Write research report", "description": "Synthesize findings into formatted Markdown file."},
                ],
            ),
        ]

        for t in templates:
            self.register(t)
