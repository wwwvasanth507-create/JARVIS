"""
Goal Management Dashboard View for JARVIS UI Subsystem.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, List, Dict, Any
from jarvis.core.goals.manager import GoalManager
from jarvis.core.goals.models import GoalStatus, GoalPriority, AutonomyLevel
from jarvis.ui.theme import BG_DARK, BG_PANEL, BG_HEADER, CYAN_ACCENT, TEXT_BRIGHT, TEXT_MUTED


class GoalDashboardView:
    """Tkinter / TTK UI Dashboard for managing and monitoring JARVIS Goals."""

    def __init__(self, parent: tk.Widget, manager: Optional[GoalManager] = None):
        self.parent = parent
        self.mgr = manager or GoalManager()

        self.frame = ttk.Frame(parent, padding=10)
        self._build_ui()
        self.refresh_goals()

    def _build_ui(self):
        # Header controls
        hdr_frame = ttk.Frame(self.frame)
        hdr_frame.pack(fill="x", pady=(0, 10))

        lbl = ttk.Label(hdr_frame, text="Governed Agent Operations & Goals", font=("Segoe UI", 12, "bold"))
        lbl.pack(side="left")

        btn_refresh = ttk.Button(hdr_frame, text="Refresh", command=self.refresh_goals)
        btn_refresh.pack(side="right", padx=5)

        # Main Split Layout
        split_frame = ttk.Frame(self.frame)
        split_frame.pack(fill="both", expand=True)

        # Left Column: Goals Treeview
        left_frame = ttk.LabelFrame(split_frame, text="Active Goals", padding=5)
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))

        cols = ("ID", "Title", "Status", "Priority", "Progress", "Autonomy", "Health")
        self.tree = ttk.Treeview(left_frame, columns=cols, show="headings", height=15)
        self.tree.heading("ID", text="ID")
        self.tree.heading("Title", text="Title")
        self.tree.heading("Status", text="Status")
        self.tree.heading("Priority", text="Priority")
        self.tree.heading("Progress", text="Progress")
        self.tree.heading("Autonomy", text="Autonomy")
        self.tree.heading("Health", text="Health")

        self.tree.column("ID", width=70)
        self.tree.column("Title", width=180)
        self.tree.column("Status", width=90)
        self.tree.column("Priority", width=70)
        self.tree.column("Progress", width=70)
        self.tree.column("Autonomy", width=80)
        self.tree.column("Health", width=60)

        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self._on_select_goal)

        # Action Buttons below Treeview
        act_frame = ttk.Frame(left_frame)
        act_frame.pack(fill="x", pady=5)

        btn_pause = ttk.Button(act_frame, text="Pause Goal", command=self._pause_selected)
        btn_pause.pack(side="left", padx=2)

        btn_resume = ttk.Button(act_frame, text="Resume Goal", command=self._resume_selected)
        btn_resume.pack(side="left", padx=2)

        btn_cancel = ttk.Button(act_frame, text="Cancel Goal", command=self._cancel_selected)
        btn_cancel.pack(side="left", padx=2)

        # Right Column: Goal Detail Panel
        right_frame = ttk.LabelFrame(split_frame, text="Goal Details & Objectives", padding=10)
        right_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))

        self.txt_detail = tk.Text(right_frame, wrap="word", bg=BG_PANEL, fg=TEXT_BRIGHT, relief="flat", font=("Consolas", 10))
        self.txt_detail.pack(fill="both", expand=True)

    def refresh_goals(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        goals = self.mgr.list_goals(limit=100)
        for g in goals:
            prog = self.mgr.get_goal_progress(g.goal_id)
            self.tree.insert(
                "",
                "end",
                iid=g.goal_id,
                values=(
                    g.goal_id[:8],
                    g.title,
                    g.status.value,
                    g.priority.value,
                    f"{prog.progress_percent}%",
                    g.autonomy_level.name.replace("LEVEL_", "L"),
                    f"{int(prog.health_score * 100)}%",
                ),
            )

    def _on_select_goal(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        goal_id = sel[0]
        try:
            exp = self.mgr.explain_goal(goal_id)
            goal = self.mgr.repo.get_goal(goal_id)
            self.txt_detail.delete("1.0", "end")
            if goal:
                lines = [
                    f"ID: {goal.goal_id}",
                    f"Title: {goal.title}",
                    f"Description: {goal.description}",
                    f"Status: {goal.status.value} | Priority: {goal.priority.value} | Risk: {goal.risk_level.value}",
                    f"Autonomy Level: {goal.autonomy_level.name}",
                    f"Owner: {goal.owner.value} | Project: {goal.associated_project or 'None'}",
                    f"Progress: {exp['progress_percent']}% | Health Score: {exp['health_score'] * 100}%",
                    f"Deadline Risk: {exp['deadline_risk']}",
                    "\n--- OBJECTIVES ---",
                ]
                for o_idx, o in enumerate(goal.objectives, 1):
                    lines.append(f"{o_idx}. [{o.status.value}] {o.title}: {o.description}")

                if goal.blockers:
                    lines.append("\n--- BLOCKERS ---")
                    for b in goal.blockers:
                        lines.append(f"- {b}")

                self.txt_detail.insert("1.0", "\n".join(lines))
        except Exception as e:
            self.txt_detail.delete("1.0", "end")
            self.txt_detail.insert("1.0", f"Error loading goal details: {e}")

    def _pause_selected(self):
        sel = self.tree.selection()
        if sel:
            self.mgr.pause_goal(sel[0])
            self.refresh_goals()

    def _resume_selected(self):
        sel = self.tree.selection()
        if sel:
            self.mgr.resume_goal(sel[0])
            self.refresh_goals()

    def _cancel_selected(self):
        sel = self.tree.selection()
        if sel:
            self.mgr.cancel_goal(sel[0])
            self.refresh_goals()
