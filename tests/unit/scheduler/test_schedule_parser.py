"""
Unit tests for ScheduleParser.
"""

from jarvis.scheduler.parser import ScheduleParser


def test_parse_relative_minutes():
    parser = ScheduleParser()
    base_ts = 1700000000.0
    next_ts, is_rec, norm = parser.parse_expression("in 30 minutes", base_timestamp=base_ts)
    assert next_ts == base_ts + 1800.0
    assert is_rec is False


def test_parse_relative_hours():
    parser = ScheduleParser()
    base_ts = 1700000000.0
    next_ts, is_rec, norm = parser.parse_expression("in 2 hours", base_timestamp=base_ts)
    assert next_ts == base_ts + 7200.0
    assert is_rec is False


def test_parse_recurring_every_day():
    parser = ScheduleParser()
    base_ts = 1700000000.0
    next_ts, is_rec, norm = parser.parse_expression("every day at 8 AM", base_timestamp=base_ts)
    assert is_rec is True
    assert next_ts > base_ts
