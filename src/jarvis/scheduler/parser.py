"""
Schedule Expression Parser for JARVIS Scheduler.
Converts natural language expressions to structured schedule definitions.
"""

import re
import time
from datetime import datetime, timedelta, timezone
from typing import Tuple, Optional, Dict, Any
from jarvis.scheduler.errors import ScheduleParseError
from jarvis.scheduler.recurrence import RecurrencePattern


class ScheduleParser:
    """Parses relative, exact, and recurring schedule expressions into timestamps."""

    def parse_expression(
        self,
        expression: str,
        base_timestamp: Optional[float] = None
    ) -> Tuple[float, bool, str]:
        """
        Parses schedule string into (next_run_at, is_recurring, normalized_expr).
        """
        now_ts = base_timestamp or time.time()
        expr = expression.lower().strip()

        # 1. Relative time offset (e.g., "in 30 minutes", "in 2 hours", "in 1 day")
        rel_match = re.search(r"in\s+(\d+)\s+(minute|min|hour|hr|day|sec|second)s?", expr)
        if rel_match:
            amount = int(rel_match.group(1))
            unit = rel_match.group(2)
            if "sec" in unit:
                target_ts = now_ts + amount
            elif "min" in unit:
                target_ts = now_ts + (amount * 60)
            elif "hour" in unit or "hr" in unit:
                target_ts = now_ts + (amount * 3600)
            elif "day" in unit:
                target_ts = now_ts + (amount * 86400)
            else:
                target_ts = now_ts + (amount * 60)
            return target_ts, False, f"in {amount} {unit}s"

        # 2. Tomorrow expression (e.g., "tomorrow at 9 am")
        if "tomorrow" in expr:
            now_dt = datetime.fromtimestamp(now_ts, tz=timezone.utc)
            tomorrow_dt = now_dt + timedelta(days=1)
            hour = 9
            if "9" in expr:
                hour = 9
            elif "8" in expr:
                hour = 8
            elif "10" in expr:
                hour = 10
            target_dt = tomorrow_dt.replace(hour=hour, minute=0, second=0, microsecond=0)
            return target_dt.timestamp(), False, f"tomorrow at {hour}:00"

        # 3. Recurring expressions (e.g., "every morning at 8 am", "every monday at 9 am", "every 2 hours")
        if "every" in expr:
            next_ts = RecurrencePattern.calculate_next_run(expr, from_timestamp=now_ts)
            return next_ts or (now_ts + 3600), True, expr

        # Fallback default: 30 minutes from now
        return now_ts + 1800, False, expression
