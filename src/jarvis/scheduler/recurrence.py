"""
Recurrence Pattern Evaluator for JARVIS Scheduler.
Calculates next_run_at timestamps for recurring tasks.
"""

import time
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Optional


class RecurrenceType(str, Enum):
    ONCE = "ONCE"
    HOURLY = "HOURLY"
    DAILY = "DAILY"
    WEEKDAYS = "WEEKDAYS"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"


class RecurrencePattern:
    """Calculates next execution time based on recurrence rules."""

    @staticmethod
    def calculate_next_run(
        schedule_expr: str,
        from_timestamp: Optional[float] = None,
        tz_offset_hours: float = 0.0
    ) -> Optional[float]:
        """
        Calculates next_run_at epoch timestamp.
        """
        now_ts = from_timestamp or time.time()
        now_dt = datetime.fromtimestamp(now_ts, tz=timezone.utc)
        expr = schedule_expr.lower().strip()

        if expr.startswith("every ") or "every" in expr:
            if "hour" in expr:
                # Every N hours
                parts = expr.split()
                hours = 1
                for p in parts:
                    if p.isdigit():
                        hours = int(p)
                        break
                next_dt = now_dt + timedelta(hours=hours)
                return next_dt.timestamp()

            if "day" in expr and "weekday" not in expr:
                # Every day
                next_dt = now_dt + timedelta(days=1)
                return next_dt.timestamp()

            if "weekday" in expr:
                # Every weekday (Mon-Fri)
                next_dt = now_dt + timedelta(days=1)
                while next_dt.weekday() >= 5:
                    next_dt += timedelta(days=1)
                return next_dt.timestamp()

            if "monday" in expr:
                days_ahead = (0 - now_dt.weekday()) % 7
                if days_ahead == 0:
                    days_ahead = 7
                next_dt = now_dt + timedelta(days=days_ahead)
                return next_dt.timestamp()

        # One-time default fallback (e.g. + 1 hour)
        return (now_dt + timedelta(hours=1)).timestamp()
