"""Tests for what recalculate_from_progress() does to past and future days.

Mirrors the "adjust plan" flow in planea.py, which recalculates from tomorrow
so that past days (including today) keep their goals.
"""

import pytest
from datetime import datetime, timedelta
import plan


START = datetime(2025, 11, 1)
TODAY = START + timedelta(days=5)        # day 6 of the plan
TOMORROW = TODAY + timedelta(days=1)


def day(n):
    """Date of plan day n (1-based)."""
    return START + timedelta(days=n - 1)


@pytest.fixture
def behind_plan():
    """10,000 words / 10 days, 800 words written on each of days 1-5."""
    p = plan.Plan(name="Test Progress Recalc", total=10000, daily=1000, time=10, start_date=START)
    for n in range(1, 6):
        p.record_progress(day(n), 800)
    return p


class TestRecalculateFromTomorrow:
    """Recalculating as the progress flow does: from tomorrow onwards."""

    def test_result_values(self, behind_plan):
        result = behind_plan.recalculate_from_progress(as_of_date=TOMORROW)

        assert result['success'] is True
        assert result['words_completed'] == 4000
        assert result['words_remaining'] == 6000
        # Days 7-10 remain
        assert result['remaining_writing_days'] == 4
        assert result['new_daily'] == pytest.approx(1500)
        assert result['new_daily'] == pytest.approx(
            result['words_remaining'] / result['remaining_writing_days'])

    def test_past_days_keep_their_goals(self, behind_plan):
        behind_plan.recalculate_from_progress(as_of_date=TOMORROW)

        # Days 1-6 (today included) are before as_of_date
        for n in range(1, 7):
            assert behind_plan.get_daily_goal(date=day(n)) == pytest.approx(1000)

    def test_future_days_use_new_daily(self, behind_plan):
        behind_plan.recalculate_from_progress(as_of_date=TOMORROW)

        for n in range(7, 11):
            assert behind_plan.get_daily_goal(date=day(n)) == pytest.approx(1500)

    def test_future_goals_cover_remaining_words(self, behind_plan):
        result = behind_plan.recalculate_from_progress(as_of_date=TOMORROW)

        future = sum(behind_plan.get_daily_goal(date=day(n)) for n in range(7, 11))
        assert future == pytest.approx(result['words_remaining'])

    def test_past_goals_preserved_count(self, behind_plan):
        result = behind_plan.recalculate_from_progress(as_of_date=TOMORROW)

        assert result['past_goals_preserved'] == 6

    def test_last_modified_updated(self, behind_plan):
        before = behind_plan.last_modified

        behind_plan.recalculate_from_progress(as_of_date=TOMORROW)

        assert behind_plan.last_modified >= before


class TestRecalculatePatternsAndCustomGoals:
    """Patterns and custom goals are handled as the confirmation screen describes."""

    def test_pattern_past_goals_kept_and_future_flattened(self):
        p = plan.Plan(total=10000, daily=1000, time=10, start_date=START, pattern="rising",
                      pattern_config={'start_multiplier': 0.5, 'end_multiplier': 1.5})
        past_goals = [p.get_daily_goal(date=day(n)) for n in range(1, 4)]
        for n in range(1, 4):
            p.record_progress(day(n), 700)

        result = p.recalculate_from_progress(as_of_date=day(4))

        assert result['old_pattern'] == 'rising'
        assert p.pattern == 'flat'
        assert [p.get_daily_goal(date=day(n)) for n in range(1, 4)] == pytest.approx(past_goals)
        for n in range(4, 11):
            assert p.get_daily_goal(date=day(n)) == pytest.approx(result['new_daily'])

    def test_future_custom_goals_cleared_past_kept(self):
        p = plan.Plan(total=10000, daily=1000, time=10, start_date=START)
        p.set_custom_daily_goal(day(2), 1500)
        p.set_custom_daily_goal(day(8), 3000)
        p.record_progress(day(1), 1000)
        p.record_progress(day(2), 1500)

        result = p.recalculate_from_progress(as_of_date=day(3))

        assert result['cleared_custom_goals'] == 1
        assert p.custom_daily_goals[day(2).strftime('%Y-%m-%d')] == 1500
        assert day(8).strftime('%Y-%m-%d') not in p.custom_daily_goals
        assert p.get_daily_goal(date=day(8)) == pytest.approx(result['new_daily'])
