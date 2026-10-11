"""Tests for locking past goals (issues-program.org RC5/P9, decision 2).

Once a day is in the past its goal is frozen in Plan.locked_goals; no later
change may alter it. Today is not locked (decision 4: it isn't over yet).
"""

import contextlib
import io
import pytest
from datetime import datetime, timedelta
from freezegun import freeze_time
import plan
import planea


MON = datetime(2026, 11, 2)
TODAY = MON + timedelta(days=5)   # Saturday, day 6 of the plan


def day(n):
    """Date of plan day n (1-based)."""
    return MON + timedelta(days=n - 1)


def key(d):
    return d.strftime('%Y-%m-%d')


def goals(p, days):
    return [p.get_daily_goal(date=day(n)) for n in days]


def quiet(func, *args):
    with contextlib.redirect_stdout(io.StringIO()):
        return func(*args)


@pytest.fixture
def ten_day_plan():
    """10,000 words / 10 days starting Monday 2026-11-02."""
    return plan.Plan(total=10000, daily=1000, time=10, start_date=MON)


@pytest.fixture
def locked_plan(ten_day_plan):
    """The ten-day plan with days 1-5 locked (today is day 6)."""
    ten_day_plan.lock_past_goals(TODAY)
    return ten_day_plan


class TestLockPastGoals:
    """Plan.lock_past_goals()"""

    def test_locks_days_before_as_of_date(self, ten_day_plan):
        locked = ten_day_plan.lock_past_goals(TODAY)

        assert locked == 5
        assert ten_day_plan.locked_goals == {key(day(n)): 1000 for n in range(1, 6)}

    def test_today_is_not_locked(self, locked_plan):
        assert not locked_plan.is_locked(TODAY)
        assert locked_plan.is_locked(TODAY - timedelta(days=1))

    def test_time_of_day_is_ignored(self, ten_day_plan):
        assert ten_day_plan.lock_past_goals(TODAY + timedelta(hours=15)) == 5

    def test_idempotent_and_keeps_existing_locks(self, locked_plan):
        locked_plan.daily = 2000

        assert locked_plan.lock_past_goals(TODAY) == 0
        assert goals(locked_plan, range(1, 6)) == [1000] * 5

    def test_locks_current_goal_including_overrides(self, ten_day_plan):
        ten_day_plan.spare_days_dates.append(day(2))
        ten_day_plan.set_custom_daily_goal(day(3), 1800)

        ten_day_plan.lock_past_goals(TODAY)

        assert ten_day_plan.locked_goals[key(day(2))] == 0
        assert ten_day_plan.locked_goals[key(day(3))] == 1800

    def test_only_plan_days_are_locked(self, ten_day_plan):
        ten_day_plan.lock_past_goals(day(30))

        assert len(ten_day_plan.locked_goals) == 10
        assert key(MON - timedelta(days=1)) not in ten_day_plan.locked_goals

    def test_defaults_to_today(self, ten_day_plan):
        with freeze_time(TODAY + timedelta(hours=10)):
            assert ten_day_plan.lock_past_goals() == 5

    def test_nothing_to_lock_without_start_date(self):
        p = plan.Plan(total=10000, daily=1000, time=10)

        assert p.lock_past_goals(TODAY) == 0


class TestModificationsDoNotRewriteHistory:
    """Every kind of change leaves locked days alone."""

    def test_change_daily(self, locked_plan):
        locked_plan.total = 20000
        locked_plan.calculate_daily()

        # The 5 open days cover what the locked days don't: 15,000
        assert goals(locked_plan, range(1, 6)) == [1000] * 5
        assert goals(locked_plan, range(6, 11)) == [pytest.approx(3000)] * 5

    def test_change_pattern(self, locked_plan):
        locked_plan.pattern = "rising"
        locked_plan.pattern_config = {'start_multiplier': 0.5, 'end_multiplier': 1.5}
        locked_plan.invalidate_daily_goals_cache()

        assert goals(locked_plan, range(1, 6)) == [1000] * 5

    def test_change_weekends(self, ten_day_plan):
        # Sat 11-07 and Sun 11-08 are days 6 and 7; lock through Sunday
        ten_day_plan.lock_past_goals(day(8))

        ten_day_plan.weekend_mode = "spare"

        assert goals(ten_day_plan, [6, 7]) == [1000, 1000]

    def test_custom_goal_and_spare_day_on_past_date(self, locked_plan):
        locked_plan.set_custom_daily_goal(day(2), 5000)
        locked_plan.spare_days_dates.append(day(3))

        assert goals(locked_plan, [2, 3]) == [1000, 1000]

    def test_on_track_status_is_stable(self, locked_plan):
        for n in range(1, 6):
            locked_plan.record_progress(day(n), 1000)
        _, before = locked_plan.is_on_track(as_of_date=day(5))

        locked_plan.daily = 3000
        _, after = locked_plan.is_on_track(as_of_date=day(5))

        assert after['expected_words'] == before['expected_words'] == 5000
        assert after['status'] == 'on_track'


@freeze_time(TODAY + timedelta(hours=10))
class TestRecalculateFromProgressUsesLocks:
    """recalculate_from_progress() locks history instead of writing custom goals (P12 item 3)."""

    def test_custom_goals_not_polluted(self, ten_day_plan):
        for n in range(1, 4):
            ten_day_plan.record_progress(day(n), 800)

        result = ten_day_plan.recalculate_from_progress(as_of_date=day(4))

        assert result['past_goals_preserved'] == 3
        assert ten_day_plan.custom_daily_goals == {}
        assert ten_day_plan.locked_goals == {key(day(n)): 1000 for n in range(1, 4)}

    def test_respects_earlier_locks(self, locked_plan):
        for n in range(1, 6):
            locked_plan.record_progress(day(n), 500)

        result = locked_plan.recalculate_from_progress(as_of_date=TODAY)

        assert result['past_goals_preserved'] == 0
        assert goals(locked_plan, range(1, 6)) == [1000] * 5
        assert goals(locked_plan, range(6, 11)) == [pytest.approx(1500)] * 5


class TestKeepTotalSkipsLockedDays:
    """recalculate_plan_with_choice('total') only adjusts open days."""

    def test_custom_goal_redistributed_over_future_only(self, locked_plan):
        # Day 8 gets 2,000 (+1,000). Days 6, 7, 9, 10 must absorb -1,000:
        # 750 each. Past days used to be counted as adjustable too.
        old_total = locked_plan.total
        locked_plan.set_custom_daily_goal(day(8), 2000)

        quiet(planea.recalculate_plan_with_choice, locked_plan, old_total, 'total')

        assert goals(locked_plan, range(1, 6)) == [1000] * 5
        assert goals(locked_plan, [6, 7, 9, 10]) == [pytest.approx(750)] * 4
        assert sum(goals(locked_plan, range(1, 11))) == pytest.approx(10000)


class TestSerialization:

    def test_round_trip(self, locked_plan):
        loaded = plan.Plan.from_json(locked_plan.to_json())

        assert loaded.locked_goals == locked_plan.locked_goals

    def test_old_file_has_no_locks(self, sample_plan_dict):
        assert plan.Plan.from_dict(sample_plan_dict).locked_goals == {}


@freeze_time(TODAY + timedelta(hours=10))
class TestUserInterface:
    """planea.py refuses changes to past days and locks on entry."""

    def test_plan_actions_menu_locks_past_days(self, ten_day_plan, scripted_input):
        scripted_input(["0"])  # go straight back to the main menu

        quiet(planea.handle_plan_actions, ten_day_plan)

        assert sorted(ten_day_plan.locked_goals) == [key(day(n)) for n in range(1, 6)]

    def test_quick_action_skips_past_days(self, ten_day_plan):
        # Sat 11-07 is today; no Saturday before today gets marked
        added = planea.mark_weekdays_as_spare(ten_day_plan, [5, 6])

        assert all(d >= TODAY for d in ten_day_plan.spare_days_dates)
        assert added == len(ten_day_plan.spare_days_dates) > 0

    def test_add_past_spare_day_refused(self, ten_day_plan, scripted_input):
        scripted_input(["1", key(day(2)), "0"])

        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            planea.manage_spare_days(ten_day_plan)

        assert ten_day_plan.spare_days_dates == []
        assert "locked" in output.getvalue()

    def test_remove_past_spare_day_refused(self, ten_day_plan, scripted_input):
        ten_day_plan.spare_days_dates.append(day(2))
        scripted_input(["2", key(day(2)), "0"])

        quiet(planea.manage_spare_days, ten_day_plan)

        assert ten_day_plan.spare_days_dates == [day(2)]

    def test_clear_all_keeps_past_spare_days(self, ten_day_plan, scripted_input):
        ten_day_plan.spare_days_dates.extend([day(2), day(8)])
        scripted_input(["3", "y", "1", "0"])  # clear, then "move the end date"

        quiet(planea.manage_spare_days, ten_day_plan)

        assert ten_day_plan.spare_days_dates == [day(2)]

    def test_custom_goal_on_past_date_refused(self, ten_day_plan, scripted_input):
        scripted_input(["1", key(day(2)), "0"])

        quiet(planea.edit_individual_day_goal, ten_day_plan)

        assert ten_day_plan.custom_daily_goals == {}

    def test_custom_goal_today_allowed(self, ten_day_plan, scripted_input):
        scripted_input(["1", key(TODAY), "1500", "2", "0"])  # set, then "keep days"

        quiet(planea.edit_individual_day_goal, ten_day_plan)

        assert ten_day_plan.custom_daily_goals == {key(TODAY): 1500}
