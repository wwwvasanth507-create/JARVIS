"""
Unified GoalManager Facade for JARVIS Goal Subsystem.
Orchestrates goal lifecycle, proposals, priority scheduling, arbitration, checkpoints, drift detection, and postmortems.
"""

import time
import logging
from typing import List, Optional, Dict, Any, Tuple
from jarvis.core.goals.models import (
    Goal,
    GoalStatus,
    GoalPriority,
    AutonomyLevel,
    DeadlineType,
    GoalOwner,
    ProgressConfidence,
    DeadlineRisk,
    Objective,
    ObjectiveStatus,
    GoalCheckpoint,
    GoalProgress,
)
from jarvis.core.goals.repository import GoalRepository
from jarvis.core.goals.queue import BoundedGoalPriorityQueue
from jarvis.core.goals.arbitrator import GoalArbitrator
from jarvis.core.goals.policy import GoalPolicy, GoalPolicyError
from jarvis.core.goals.templates import GoalTemplateRegistry
from jarvis.system.event_bus import JarvisEventBus, SystemEventType
from jarvis.security.permissions import PermissionEvaluator, RiskLevel

logger = logging.getLogger("jarvis.core.goals.manager")


class GoalManager:
    """Unified entry point for managing JARVIS goal operations."""

    def __init__(
        self,
        repository: Optional[GoalRepository] = None,
        policy: Optional[GoalPolicy] = None,
        queue: Optional[BoundedGoalPriorityQueue] = None,
        arbitrator: Optional[GoalArbitrator] = None,
        templates: Optional[GoalTemplateRegistry] = None,
    ):
        self.repo = repository or GoalRepository()
        self.policy = policy or GoalPolicy()
        self.queue = queue or BoundedGoalPriorityQueue()
        self.arbitrator = arbitrator or GoalArbitrator(queue=self.queue)
        self.templates = templates or GoalTemplateRegistry()
        self.event_bus = JarvisEventBus.get_instance()

        # Load active goals into priority queue
        self._sync_queue()

    def _sync_queue(self) -> None:
        self.queue.clear()
        active = self.repo.list_goals(status=GoalStatus.ACTIVE)
        for g in active:
            self.queue.enqueue(g)

    def create_goal(
        self,
        title: str,
        description: str = "",
        owner: GoalOwner = GoalOwner.USER,
        priority: GoalPriority = GoalPriority.NORMAL,
        deadline: Optional[float] = None,
        deadline_type: DeadlineType = DeadlineType.SOFT,
        autonomy_level: AutonomyLevel = AutonomyLevel.LEVEL_1_ASSISTED,
        risk_level: RiskLevel = RiskLevel.LOW,
        objectives: Optional[List[Dict[str, Any]]] = None,
        associated_project: Optional[str] = None,
        template_id: Optional[str] = None,
    ) -> Goal:
        """Creates a new structured goal."""
        active_count = len(self.repo.list_goals(status=GoalStatus.ACTIVE))
        
        goal_obj = Goal(
            title=title,
            description=description,
            owner=owner,
            priority=priority,
            deadline=deadline,
            deadline_type=deadline_type,
            autonomy_level=autonomy_level,
            risk_level=risk_level,
            associated_project=associated_project,
            status=GoalStatus.DRAFT,
        )

        # Build objectives from template or provided dictionary
        if template_id:
            tmpl = self.templates.get_template(template_id)
            if tmpl:
                goal_obj.title = goal_obj.title or tmpl.name
                goal_obj.description = goal_obj.description or tmpl.description
                goal_obj.risk_level = tmpl.risk_level
                goal_obj.autonomy_level = tmpl.default_autonomy_level
                for o_idx, o_tmpl in enumerate(tmpl.objective_templates):
                    obj = Objective(
                        goal_id=goal_obj.goal_id,
                        title=o_tmpl["title"],
                        description=o_tmpl.get("description", ""),
                    )
                    if o_idx > 0 and goal_obj.objectives:
                        obj.dependencies.append(goal_obj.objectives[-1].objective_id)
                    goal_obj.objectives.append(obj)

        if objectives:
            prev_id = None
            for o_data in objectives:
                obj = Objective(
                    goal_id=goal_obj.goal_id,
                    title=o_data.get("title", "Objective"),
                    description=o_data.get("description", ""),
                    dependencies=o_data.get("dependencies", [prev_id] if prev_id else []),
                )
                goal_obj.objectives.append(obj)
                prev_id = obj.objective_id

        self.policy.validate_goal_creation(goal_obj, current_active_count=active_count)
        saved_goal = self.repo.create_goal(goal_obj)
        self.event_bus.publish(SystemEventType.GOAL_CREATED, "GoalManager", {"goal_id": saved_goal.goal_id, "title": saved_goal.title})
        return saved_goal

    def propose_goal_from_intent(self, user_request: str) -> Dict[str, Any]:
        """Generates a structured goal proposal for user confirmation."""
        req_lower = user_request.lower()
        matched_tmpl = None
        if "test" in req_lower or "health" in req_lower:
            matched_tmpl = self.templates.get_template("project_health")
        elif "document" in req_lower or "summarize" in req_lower:
            matched_tmpl = self.templates.get_template("document_processing")
        elif "report" in req_lower:
            matched_tmpl = self.templates.get_template("weekly_report")
        elif "download" in req_lower or "organize" in req_lower:
            matched_tmpl = self.templates.get_template("download_organization")
        elif "monitor" in req_lower:
            matched_tmpl = self.templates.get_template("scheduled_monitoring")
        elif "research" in req_lower or "search" in req_lower:
            matched_tmpl = self.templates.get_template("research_and_summary")

        if matched_tmpl:
            proposal_title = matched_tmpl.name
            proposal_desc = matched_tmpl.description
            objs = [o["title"] for o in matched_tmpl.objective_templates]
            autonomy = matched_tmpl.default_autonomy_level.value
            risk = matched_tmpl.risk_level.value
            template_id = matched_tmpl.template_id
        else:
            proposal_title = f"Goal: {user_request.capitalize()}"
            proposal_desc = user_request
            objs = [f"Execute task: {user_request}", "Verify task outcome"]
            autonomy = AutonomyLevel.LEVEL_1_ASSISTED.value
            risk = RiskLevel.LOW.value
            template_id = None

        return {
            "proposed_title": proposal_title,
            "proposed_description": proposal_desc,
            "objectives": objs,
            "autonomy_level": autonomy,
            "risk_level": risk,
            "template_id": template_id,
            "requires_confirmation": risk in ("HIGH", "CRITICAL") or autonomy >= 2,
        }

    def activate_goal(self, goal_id: str) -> Goal:
        goal = self.repo.get_goal(goal_id)
        if not goal:
            raise ValueError(f"Goal '{goal_id}' not found.")

        goal.status = GoalStatus.ACTIVE
        self.repo.update_goal(goal)
        self.queue.enqueue(goal)
        self.event_bus.publish(SystemEventType.GOAL_ACTIVATED, "GoalManager", {"goal_id": goal.goal_id})
        return goal

    def pause_goal(self, goal_id: str) -> Goal:
        goal = self.repo.get_goal(goal_id)
        if not goal:
            raise ValueError(f"Goal '{goal_id}' not found.")

        goal.status = GoalStatus.PAUSED
        self.repo.update_goal(goal)
        self.queue.remove(goal_id)
        self.event_bus.publish(SystemEventType.GOAL_PAUSED, "GoalManager", {"goal_id": goal.goal_id})
        return goal

    def resume_goal(self, goal_id: str) -> Goal:
        goal = self.repo.get_goal(goal_id)
        if not goal:
            raise ValueError(f"Goal '{goal_id}' not found.")

        goal.status = GoalStatus.ACTIVE
        self.repo.update_goal(goal)
        self.queue.enqueue(goal)
        self.event_bus.publish(SystemEventType.GOAL_RESUMED, "GoalManager", {"goal_id": goal.goal_id})
        return goal

    def cancel_goal(self, goal_id: str) -> Goal:
        goal = self.repo.get_goal(goal_id)
        if not goal:
            raise ValueError(f"Goal '{goal_id}' not found.")

        goal.status = GoalStatus.CANCELLED
        self.repo.update_goal(goal)
        self.queue.remove(goal_id)
        self.event_bus.publish(SystemEventType.GOAL_FAILED, "GoalManager", {"goal_id": goal.goal_id, "reason": "Cancelled by user"})
        return goal

    def list_goals(
        self,
        status: Optional[GoalStatus] = None,
        owner: Optional[GoalOwner] = None,
        priority: Optional[GoalPriority] = None,
        project: Optional[str] = None,
        limit: int = 100,
    ) -> List[Goal]:
        return self.repo.list_goals(status=status, owner=owner, priority=priority, project=project, limit=limit)

    def get_goal_progress(self, goal_id: str) -> GoalProgress:
        goal = self.repo.get_goal(goal_id)
        if not goal:
            raise ValueError(f"Goal '{goal_id}' not found.")

        total_objs = len(goal.objectives)
        completed_objs = sum(1 for o in goal.objectives if o.status == ObjectiveStatus.COMPLETED)
        blocked_objs = sum(1 for o in goal.objectives if o.status == ObjectiveStatus.BLOCKED)

        pct = (completed_objs / total_objs * 100.0) if total_objs > 0 else (100.0 if goal.status == GoalStatus.COMPLETED else 0.0)
        goal.progress = round(pct, 1)
        self.repo.update_goal(goal)

        now = time.time()
        deadline_risk = DeadlineRisk.ON_TRACK
        if goal.deadline is not None:
            if now > goal.deadline and goal.status not in (GoalStatus.COMPLETED, GoalStatus.CANCELLED):
                deadline_risk = DeadlineRisk.OVERDUE
            elif (goal.deadline - now) < 3600 and pct < 80.0:
                deadline_risk = DeadlineRisk.AT_RISK

        # Explainable health score computation
        health = 1.0
        if blocked_objs > 0:
            health -= 0.3
        if deadline_risk == DeadlineRisk.OVERDUE:
            health -= 0.5
        elif deadline_risk == DeadlineRisk.AT_RISK:
            health -= 0.2
        if goal.status == GoalStatus.AT_RISK:
            health -= 0.3

        health_score = max(0.0, min(1.0, round(health, 2)))

        curr_act = "Idle"
        in_prog = [o for o in goal.objectives if o.status == ObjectiveStatus.IN_PROGRESS]
        if in_prog:
            curr_act = f"Executing: {in_prog[0].title}"
        elif goal.status == GoalStatus.COMPLETED:
            curr_act = "Completed"

        return GoalProgress(
            goal_id=goal.goal_id,
            progress_percent=goal.progress,
            confidence=goal.progress_confidence,
            total_objectives=total_objs,
            completed_objectives=completed_objs,
            blocked_objectives=blocked_objs,
            current_activity=curr_act,
            deadline_risk=deadline_risk,
            health_score=health_score,
        )

    def reconcile_goals_on_startup(self) -> List[Goal]:
        """Post-restart goal reconciliation: checks active goals and restores queue safely."""
        logger.info("Reconciling active goals on startup...")
        active_goals = self.repo.list_goals(status=GoalStatus.ACTIVE)
        reconciled = []
        for goal in active_goals:
            # Save checkpoint on startup reconciliation
            chk = GoalCheckpoint(
                goal_id=goal.goal_id,
                state={"reconciled_at": time.time(), "status": goal.status.value},
            )
            self.repo.save_checkpoint(chk)
            self.queue.enqueue(goal)
            reconciled.append(goal)
        return reconciled

    def explain_goal(self, goal_id: str) -> Dict[str, Any]:
        goal = self.repo.get_goal(goal_id)
        if not goal:
            raise ValueError(f"Goal '{goal_id}' not found.")

        prog = self.get_goal_progress(goal_id)
        return {
            "goal_id": goal.goal_id,
            "title": goal.title,
            "status": goal.status.value,
            "priority": goal.priority.value,
            "autonomy_level": goal.autonomy_level.name,
            "progress_percent": prog.progress_percent,
            "health_score": prog.health_score,
            "deadline_risk": prog.deadline_risk.value,
            "explanation": f"Goal '{goal.title}' is currently {goal.status.value} with priority {goal.priority.value}. Progress is {prog.progress_percent}% ({prog.completed_objectives}/{prog.total_objectives} objectives completed).",
            "blockers": goal.blockers,
        }

    def postmortem(self, goal_id: str) -> Dict[str, Any]:
        """Generates structured postmortem summary after goal completion or failure."""
        goal = self.repo.get_goal(goal_id)
        if not goal:
            raise ValueError(f"Goal '{goal_id}' not found.")

        duration = goal.updated_at - goal.created_at
        prog = self.get_goal_progress(goal_id)

        postmortem_data = {
            "goal_id": goal.goal_id,
            "title": goal.title,
            "final_status": goal.status.value,
            "duration_sec": round(duration, 2),
            "completed_objectives": prog.completed_objectives,
            "total_objectives": prog.total_objectives,
            "blockers_encountered": goal.blockers,
            "lessons_learned": f"Goal '{goal.title}' reached final status {goal.status.value} in {round(duration, 1)} seconds.",
        }

        self.repo.log_event(goal.goal_id, "GOAL_POSTMORTEM", "Goal postmortem generated.", postmortem_data)
        return postmortem_data
