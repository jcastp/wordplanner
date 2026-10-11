"""Tests for moving a plan's start date (issues-program.org P8, decisions 7 and 10).

Plan.move_start_date() keeps spare days and custom goals on their dates unless
asked to shift them, never moves progress, keeps locked goals on their dates,
and rebases a started plan so its open days cover the words actually left.
ui_modify.change_start_date() previews both options and asks before applying.
"""

import contextlib
import io
import pytest
from datetime import datetime, timedelta
from freezegun import freeze_time
import plan
import ui_modify


MON = datetime(2026, 11, 2)
BEFORE_PLAN = "2026-10-01 10:00"


def day(n):
    """Date of calendar day n of a plan starting MON (1-based)."""
    return MON + timedelta(days=n - 1)


def key(d):
    return d.strftime('%Y-%m-%d')


def schedule_sum(p):
    return sum(p.get_daily_goal(date=d) for d in p.plan_days())


@pytest.fixture
def ten_day_plan():
    """10,000 words / 10 writing days, Mon 2026-11-02 to Wed 2026-11-11."""
    return plan.Plan(total=10000, daily=1000, time=10, start_date=MON)


@freeze_time(BEFORE_PLAN)
class TestMoveNotStartedPlan:

    def test_window_moves_and_keeps_writing_days(self, ten_day_plan):
        result = ten_day_plan.move_start_date(day(8))

        assert result['offset'] == 7
        assert ten_day_plan.start_date == day(8)
        assert ten_day_plan.end_date == day(17)
        assert result['rebased'] is False
        assert ten_day_plan.schedule_adjustment == 0
        assert schedule_sum(ten_day_plan) == pytest.approx(10000)

    def test_keep_leaves_spare_days_and_goals_on_their_dates(self, ten_day_plan):
        ten_day_plan.spare_days_dates.append(day(3))
        ten_day_plan.set_custom_daily_goal(day(5), 2000)

        ten_day_plan.move_start_date(day(8))

        assert ten_day_plan.spare_days_dates == [day(3)]
        assert ten_day_plan.custom_daily_goals == {key(day(5)): 2000}
        # Both are now before the plan: ignored
        assert ten_day_plan.spare_days == 0
        assert ten_day_plan.end_date == day(17)
        assert schedule_sum(ten_day_plan) == pytest.approx(10000)

    def test_shift_moves_them_with_the_plan(self, ten_day_plan):
        ten_day_plan.spare_days_dates.append(day(3))
        ten_day_plan.set_custom_daily_goal(day(5), 2000)

        ten_day_plan.move_start_date(day(8), shift_dated_days=True)

        assert ten_day_plan.spare_days_dates == [day(10)]
        assert ten_day_plan.custom_daily_goals == {key(day(12)): 2000}
        # A week later: same weekdays
        assert day(10).weekday() == day(3).weekday()
        assert ten_day_plan.end_date == day(18)
        assert schedule_sum(ten_day_plan) == pytest.approx(10000)

    def test_shift_earlier(self, ten_day_plan):
        ten_day_plan.spare_days_dates.append(day(10))

        ten_day_plan.move_start_date(day(-2), shift_dated_days=True)

        assert ten_day_plan.spare_days_dates == [day(7)]

    def test_preexisting_words_follow_the_plan(self, ten_day_plan):
        ten_day_plan.total = 12000
        ten_day_plan.preexisting_words = 2000

        ten_day_plan.move_start_date(day(8))

        assert schedule_sum(ten_day_plan) == pytest.approx(10000)
        assert ten_day_plan.get_total_written() == 2000

    def test_progress_never_moves(self, ten_day_plan):
        ten_day_plan.record_progress(day(1), 500)

        ten_day_plan.move_start_date(day(8), shift_dated_days=True)

        assert ten_day_plan.progress == {key(day(1)): 500}


@freeze_time(day(6) + timedelta(hours=10))
class TestMoveStartedPlan:
    """Today is day 6; days 1-5 are locked with 800 written on each."""

    @pytest.fixture
    def started_plan(self, ten_day_plan):
        for n in range(1, 6):
            ten_day_plan.record_progress(day(n), 800)
        ten_day_plan.lock_past_goals()
        return ten_day_plan

    def test_restart_later_covers_words_left(self, started_plan):
        result = started_plan.move_start_date(day(8))

        assert result['rebased'] is True
        assert started_plan.end_date == day(17)
        # Locked days are outside the window now; the new days cover what's left
        assert schedule_sum(started_plan) == pytest.approx(10000 - 4000)
        assert started_plan.daily == pytest.approx(600)

    def test_locked_days_kept_on_their_dates(self, started_plan):
        locked = dict(started_plan.locked_goals)

        started_plan.move_start_date(day(8))

        assert started_plan.locked_goals == locked

    def test_locked_days_inside_keep_their_goals(self, started_plan):
        # Start one day earlier: days 1-5 stay inside with their goals
        started_plan.move_start_date(day(0))

        assert [started_plan.get_daily_goal(date=day(n)) for n in range(1, 6)] == [1000] * 5
        # The day that joined is past, so it's locked too
        assert started_plan.is_locked(day(0))
        # Open days cover the words left
        open_days = [d for d in started_plan.plan_days() if d >= day(6)]
        assert sum(started_plan.get_daily_goal(date=d) for d in open_days) == pytest.approx(6000)

    def test_shift_leaves_past_items_alone(self, started_plan):
        started_plan.spare_days_dates.extend([day(2), day(8)])
        started_plan.custom_daily_goals[key(day(3))] = 1000
        started_plan.set_custom_daily_goal(day(9), 1500)

        started_plan.move_start_date(day(8), shift_dated_days=True)

        assert sorted(started_plan.spare_days_dates) == [day(2), day(15)]
        assert started_plan.custom_daily_goals == {key(day(3)): 1000, key(day(16)): 1500}

    def test_shifted_goal_never_replaces_a_past_one(self, started_plan):
        started_plan.custom_daily_goals[key(day(3))] = 1000
        started_plan.set_custom_daily_goal(day(7), 2500)

        started_plan.move_start_date(day(-3), shift_dated_days=True)

        assert started_plan.custom_daily_goals == {key(day(3)): 1000}


def run_change(p, new_start, answers, scripted_input):
    scripted_input(answers)
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        changed = ui_modify.change_start_date(p, new_start)
    return changed, out.getvalue()


@freeze_time(BEFORE_PLAN)
class TestChangeStartDateUI:

    def test_no_dated_days_just_confirms(self, ten_day_plan, scripted_input):
        changed, output = run_change(ten_day_plan, day(8), ["y"], scripted_input)

        assert changed
        assert ten_day_plan.start_date == day(8)
        assert "New: 2026-11-09 to 2026-11-18" in output

    def test_declined(self, ten_day_plan, scripted_input):
        changed, _ = run_change(ten_day_plan, day(8), ["n"], scripted_input)

        assert not changed
        assert ten_day_plan.start_date == MON

    def test_same_date(self, ten_day_plan, scripted_input):
        changed, _ = run_change(ten_day_plan, MON, [], scripted_input)

        assert not changed

    def test_lists_days_outside_and_keeps_them(self, ten_day_plan, scripted_input):
        ten_day_plan.spare_days_dates.append(day(3))
        ten_day_plan.set_custom_daily_goal(day(9), 2000)

        changed, output = run_change(ten_day_plan, day(8), ["1", "y"], scripted_input)

        assert changed
        assert "2026-11-04 (Wednesday): spare day" in output
        assert "2026-11-10 (Tuesday): custom goal" not in output.split("would fall outside")[1].split("1.")[0]
        assert ten_day_plan.spare_days_dates == [day(3)]

    def test_shift(self, ten_day_plan, scripted_input):
        ten_day_plan.spare_days_dates.append(day(3))

        changed, output = run_change(ten_day_plan, day(8), ["2", "y"], scripted_input)

        assert changed
        assert "2. Shift all of them 7 day(s) later\n" in output
        assert ten_day_plan.spare_days_dates == [day(10)]

    def test_shift_mentions_weekday_change(self, ten_day_plan, scripted_input):
        ten_day_plan.spare_days_dates.append(day(3))

        _, output = run_change(ten_day_plan, day(4), ["0"], scripted_input)

        assert "Shift all of them 3 day(s) later (they land on other weekdays)" in output

    def test_cancel(self, ten_day_plan, scripted_input):
        ten_day_plan.spare_days_dates.append(day(3))

        changed, _ = run_change(ten_day_plan, day(8), ["0"], scripted_input)

        assert not changed
        assert ten_day_plan.start_date == MON

    def test_warns_about_progress_outside(self, ten_day_plan, scripted_input):
        ten_day_plan.record_progress(day(1), 500)

        _, output = run_change(ten_day_plan, day(8), ["y"], scripted_input)

        assert "1 day(s) with progress (500 words) are outside the new plan" in output

    def test_modify_menu_uses_it(self, ten_day_plan, scripted_input):
        scripted_input(["6", key(day(8)), "y"])

        with contextlib.redirect_stdout(io.StringIO()):
            assert ui_modify.modify_plan(ten_day_plan)

        assert ten_day_plan.start_date == day(8)


@freeze_time(day(6) + timedelta(hours=10))
class TestChangeStartDateWarnings:

    def test_past_days_joining(self, ten_day_plan, scripted_input):
        # Backdating a plan that hasn't been opened since day 1
        _, output = run_change(ten_day_plan, day(-1), ["y", "y"], scripted_input)

        assert "2 day(s) before today join the plan" in output

    def test_started_plan_says_it_recalculates(self, ten_day_plan, scripted_input):
        for n in range(1, 6):
            ten_day_plan.record_progress(day(n), 800)
        ten_day_plan.lock_past_goals()

        _, output = run_change(ten_day_plan, day(8), ["y"], scripted_input)

        assert "cover the 6,000 words left" in output
        assert "outside the plan; their goals no longer count" in output
