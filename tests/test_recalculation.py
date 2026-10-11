"""Tests for Plan.recalculate_from_progress(): ahead, behind, spare days and failure cases."""

import pytest
from datetime import datetime, timedelta
import plan


START = datetime(2025, 11, 1)


def make_plan(**kwargs):
    """10,000 words over 10 writing days starting 2025-11-01, unless overridden."""
    values = dict(name="Test Recalculation", total=10000, daily=1000, time=10, start_date=START)
    values.update(kwargs)
    return plan.Plan(**values)


def record(p, words_per_day):
    """Record consecutive progress entries starting on the plan's start date."""
    for offset, words in enumerate(words_per_day):
        p.record_progress(p.start_date + timedelta(days=offset), words)


class TestRecalculateAheadBehind:
    """Redistributing remaining words over the remaining days, end date fixed."""

    def test_ahead_of_schedule_lowers_daily(self):
        p = make_plan()
        record(p, [1200, 1100, 1300])

        result = p.recalculate_from_progress(as_of_date=datetime(2025, 11, 4))

        assert result['success'] is True
        assert result['words_completed'] == 3600
        assert result['words_remaining'] == 6400
        assert result['remaining_writing_days'] == 7
        assert result['old_daily'] == 1000
        assert result['new_daily'] == pytest.approx(6400 / 7)
        assert p.daily == pytest.approx(6400 / 7)

    def test_behind_schedule_raises_daily(self):
        p = make_plan()
        record(p, [800, 900, 700])

        result = p.recalculate_from_progress(as_of_date=datetime(2025, 11, 4))

        assert result['success'] is True
        assert result['words_remaining'] == 7600
        assert result['remaining_writing_days'] == 7
        assert result['new_daily'] == pytest.approx(7600 / 7)
        assert result['new_daily'] > result['old_daily']

    def test_end_date_is_unchanged(self):
        p = make_plan()
        record(p, [500, 500, 500])

        result = p.recalculate_from_progress(as_of_date=datetime(2025, 11, 4))

        assert result['end_date'] == datetime(2025, 11, 10)
        assert p.time == 10

    def test_spare_days_are_not_remaining_writing_days(self):
        p = make_plan(spare_days_dates=[datetime(2025, 11, 6)])
        record(p, [1000, 1000])

        result = p.recalculate_from_progress(as_of_date=datetime(2025, 11, 3))

        # Plan spans 11 calendar days (10 writing + 1 spare): 11-01 .. 11-11.
        # From 11-03 that leaves 9 calendar days, one of them spare.
        assert result['success'] is True
        assert result['end_date'] == datetime(2025, 11, 11)
        assert result['words_remaining'] == 8000
        assert result['remaining_writing_days'] == 8
        assert result['new_daily'] == pytest.approx(1000)
        assert p.get_daily_goal(date=datetime(2025, 11, 6)) == 0


class TestRecalculateFailures:
    """Cases where recalculation is refused."""

    def test_no_start_date_returns_none(self):
        p = plan.Plan(total=10000, daily=1000, time=10)
        p.record_progress(START, 1000)

        assert p.recalculate_from_progress(as_of_date=START) is None

    def test_goal_already_met(self):
        p = make_plan()
        record(p, [5000, 5000])

        result = p.recalculate_from_progress(as_of_date=datetime(2025, 11, 3))

        assert result['success'] is False
        assert result['reason'] == 'goal_already_met'
        assert result['words_remaining'] == 0

    def test_past_end_date(self):
        p = make_plan()
        record(p, [1000])

        result = p.recalculate_from_progress(as_of_date=datetime(2025, 11, 11))

        assert result['success'] is False
        assert result['reason'] == 'past_end_date'
        assert result['words_remaining'] == 9000
        assert result['end_date'] == datetime(2025, 11, 10)

    def test_no_remaining_writing_days(self):
        # 2 writing days + 1 spare = 11-01 .. 11-03; recalculating on the spare
        # last day leaves no writing days.
        p = make_plan(total=2000, time=2, spare_days_dates=[datetime(2025, 11, 3)])
        record(p, [500])

        result = p.recalculate_from_progress(as_of_date=datetime(2025, 11, 3))

        assert result['success'] is False
        assert result['reason'] == 'no_remaining_days'
        assert result['words_remaining'] == 1500

    def test_failed_recalculation_leaves_plan_untouched(self):
        p = make_plan()
        record(p, [5000, 5000])

        p.recalculate_from_progress(as_of_date=datetime(2025, 11, 3))

        assert p.daily == 1000
        assert p.custom_daily_goals == {}
