"""Tests for decision 1: adding or removing writing days asks how the plan adjusts.

Spare days (added, removed, cleared, quick actions) and weekend settings
(menu and template flow) all go through ui_modify.offer_plan_adjustment(),
which offers: move the end date (keep daily), keep the end date (change daily),
or keep the end date and daily (change the total). Issues-program.org P4 and P5.
"""

import contextlib
import copy
import io
import pytest
from datetime import datetime, timedelta
from freezegun import freeze_time
import plan
import ui_modify


MON = datetime(2026, 11, 2)

MOVE_END, KEEP_END, CHANGE_TOTAL = "1", "2", "3"


def day(n):
    """Date of calendar day n of a plan starting MON (1-based)."""
    return MON + timedelta(days=n - 1)


def key(d):
    return d.strftime('%Y-%m-%d')


def schedule_sum(p):
    return sum(p.get_daily_goal(date=d) for d in p.plan_days())


def quiet(func, *args, **kwargs):
    with contextlib.redirect_stdout(io.StringIO()):
        return func(*args, **kwargs)


@pytest.fixture
def ten_day_plan():
    """10,000 words / 10 writing days, Mon 2026-11-02 to Wed 2026-11-11."""
    return plan.Plan(total=10000, daily=1000, time=10, start_date=MON)


class TestKeepEndDate:
    """Plan.writing_days_until() and Plan.keep_end_date()"""

    def test_writing_days_until_skips_spare_days(self, ten_day_plan):
        ten_day_plan.spare_days_dates.append(day(4))

        assert ten_day_plan.writing_days_until(day(10)) == 9
        assert ten_day_plan.writing_days_until(day(10) + timedelta(hours=9)) == 9
        assert ten_day_plan.writing_days_until(MON - timedelta(days=1)) == 0

    def test_spare_day_redistributes(self, ten_day_plan):
        ten_day_plan.spare_days_dates.append(day(4))

        ten_day_plan.keep_end_date(day(10))

        assert ten_day_plan.end_date == day(10)
        assert ten_day_plan.time == 9
        assert ten_day_plan.daily == pytest.approx(10000 / 9)
        assert schedule_sum(ten_day_plan) == pytest.approx(10000)

    def test_spare_last_day_ends_on_previous_writing_day(self, ten_day_plan):
        ten_day_plan.spare_days_dates.append(day(10))

        ten_day_plan.keep_end_date(day(10))

        assert ten_day_plan.end_date == day(9)
        assert schedule_sum(ten_day_plan) == pytest.approx(10000)

    def test_never_drops_locked_days(self, ten_day_plan):
        ten_day_plan.lock_past_goals(day(6))

        ten_day_plan.keep_end_date(day(2))

        assert ten_day_plan.time == 5


@freeze_time("2026-10-01")  # before the plan: nothing is locked
class TestSpareDays:
    """Adding, removing and clearing spare days in manage_spare_days()."""

    def test_add_move_end(self, ten_day_plan, scripted_input):
        scripted_input(["1", key(day(4)), MOVE_END, "0"])

        quiet(ui_modify.manage_spare_days, ten_day_plan)

        assert ten_day_plan.end_date == day(11)
        assert ten_day_plan.daily == pytest.approx(1000)
        assert schedule_sum(ten_day_plan) == pytest.approx(10000)

    def test_add_keep_end(self, ten_day_plan, scripted_input):
        scripted_input(["1", key(day(4)), KEEP_END, "0"])

        quiet(ui_modify.manage_spare_days, ten_day_plan)

        assert ten_day_plan.end_date == day(10)
        assert ten_day_plan.daily == pytest.approx(10000 / 9)
        assert schedule_sum(ten_day_plan) == pytest.approx(10000)

    def test_add_change_total(self, ten_day_plan, scripted_input):
        scripted_input(["1", key(day(4)), CHANGE_TOTAL, "0"])

        quiet(ui_modify.manage_spare_days, ten_day_plan)

        assert ten_day_plan.end_date == day(10)
        assert ten_day_plan.daily == pytest.approx(1000)
        assert ten_day_plan.total == pytest.approx(9000)
        assert schedule_sum(ten_day_plan) == pytest.approx(9000)

    def test_remove_move_end_shortens_plan(self, ten_day_plan, scripted_input):
        ten_day_plan.spare_days_dates.append(day(4))
        scripted_input(["2", key(day(4)), MOVE_END, "0"])

        quiet(ui_modify.manage_spare_days, ten_day_plan)

        assert ten_day_plan.end_date == day(10)
        assert ten_day_plan.daily == pytest.approx(1000)

    def test_remove_keep_end_lowers_daily(self, ten_day_plan, scripted_input):
        ten_day_plan.spare_days_dates.append(day(4))
        scripted_input(["2", key(day(4)), KEEP_END, "0"])

        quiet(ui_modify.manage_spare_days, ten_day_plan)

        assert ten_day_plan.end_date == day(11)
        assert ten_day_plan.daily == pytest.approx(10000 / 11)
        assert schedule_sum(ten_day_plan) == pytest.approx(10000)

    def test_no_question_when_the_plan_is_unaffected(self, ten_day_plan, scripted_input):
        # Day 20 is after the end: ignored, nothing to adjust
        scripted_input(["1", key(day(20)), "0"])

        quiet(ui_modify.manage_spare_days, ten_day_plan)

        assert ten_day_plan.end_date == day(10)

    def test_preview_shows_every_option(self, ten_day_plan, scripted_input):
        scripted_input(["1", key(day(4)), KEEP_END, "0"])
        out = io.StringIO()

        with contextlib.redirect_stdout(out):
            ui_modify.manage_spare_days(ten_day_plan)

        text = out.getvalue()
        assert "Before: ends 2026-11-11, 1,000 words/day, total 10,000 words" in text
        assert "-> ends 2026-11-12, 1,000 words/day, total 10,000 words" in text
        assert "-> ends 2026-11-11, 1,111 words/day, total 10,000 words" in text
        assert "-> ends 2026-11-11, 1,000 words/day, total 9,000 words" in text


@freeze_time("2026-10-01")
class TestQuickActions:
    """P5: "Mark all ..." follows decision 1 too."""

    @pytest.fixture
    def twelve_day_plan(self):
        """12,000 words / 12 days, Mon 2026-11-02 to Fri 2026-11-13."""
        return plan.Plan(total=12000, daily=1000, time=12, start_date=MON)

    def test_weekends_move_end(self, twelve_day_plan, scripted_input):
        # The growing window reaches the second weekend (11-14, 11-15)
        scripted_input(["6", MOVE_END, "0"])

        quiet(ui_modify.manage_spare_days, twelve_day_plan)

        assert sorted(twelve_day_plan.spare_days_dates) == [day(6), day(7), day(13), day(14)]
        assert twelve_day_plan.end_date == day(16)
        assert twelve_day_plan.daily == pytest.approx(1000)
        assert schedule_sum(twelve_day_plan) == pytest.approx(12000)

    def test_weekends_keep_end_marks_only_days_inside(self, twelve_day_plan, scripted_input):
        scripted_input(["6", KEEP_END, "0"])
        out = io.StringIO()

        with contextlib.redirect_stdout(out):
            ui_modify.manage_spare_days(twelve_day_plan)

        assert sorted(twelve_day_plan.spare_days_dates) == [day(6), day(7)]
        assert twelve_day_plan.end_date == day(12)
        assert twelve_day_plan.daily == pytest.approx(1200)
        assert schedule_sum(twelve_day_plan) == pytest.approx(12000)
        assert "Marked 2 weekend days as spare days" in out.getvalue()


@freeze_time("2026-10-01")
class TestWeekendSettings:
    """P4: switching weekend mode asks instead of dropping words."""

    def test_spare_move_end(self, ten_day_plan, scripted_input):
        scripted_input(["3", "n", MOVE_END])

        quiet(ui_modify.configure_weekend_settings, ten_day_plan)

        # 10 weekdays from Mon 11-02 end on Fri 11-13
        assert ten_day_plan.end_date == datetime(2026, 11, 13)
        assert ten_day_plan.daily == pytest.approx(1000)
        assert schedule_sum(ten_day_plan) == pytest.approx(10000)

    def test_spare_keep_end(self, ten_day_plan, scripted_input):
        scripted_input(["3", "n", KEEP_END])

        quiet(ui_modify.configure_weekend_settings, ten_day_plan)

        assert ten_day_plan.end_date == day(10)
        assert ten_day_plan.daily == pytest.approx(1250)
        assert schedule_sum(ten_day_plan) == pytest.approx(10000)

    def test_spare_change_total(self, ten_day_plan, scripted_input):
        # The old silent behaviour, now an explicit choice
        scripted_input(["3", "n", CHANGE_TOTAL])

        quiet(ui_modify.configure_weekend_settings, ten_day_plan)

        assert ten_day_plan.total == pytest.approx(8000)
        assert schedule_sum(ten_day_plan) == pytest.approx(8000)

    def test_bigger_weekend_goal_can_finish_early(self, ten_day_plan, scripted_input):
        scripted_input(["2", "2000", "n", MOVE_END])

        quiet(ui_modify.configure_weekend_settings, ten_day_plan)

        # Mon-Fri 5,000 + Sat-Sun 4,000 = 9,000 by Sun 11-08; one more day
        assert ten_day_plan.end_date == day(8)
        assert ten_day_plan.daily == pytest.approx(1000)
        assert schedule_sum(ten_day_plan) == pytest.approx(10000)

    def test_same_mode_unchanged_asks_nothing(self, ten_day_plan, scripted_input):
        scripted_input(["1"])

        quiet(ui_modify.configure_weekend_settings, ten_day_plan)

        assert ten_day_plan.end_date == day(10)


@freeze_time(day(6) + timedelta(hours=10))
class TestLockedDays:

    def test_options_never_touch_past_days(self, ten_day_plan, scripted_input):
        ten_day_plan.lock_past_goals()
        scripted_input(["3", "n", KEEP_END])

        quiet(ui_modify.configure_weekend_settings, ten_day_plan)

        # Sat 11-07 (today) and Sun 11-08 rest; days 8-10 absorb their words
        assert [ten_day_plan.get_daily_goal(date=day(n)) for n in range(1, 6)] == [1000] * 5
        assert ten_day_plan.end_date == day(10)
        assert ten_day_plan.daily == pytest.approx(5000 / 3)
        assert schedule_sum(ten_day_plan) == pytest.approx(10000)


class TestRebalanceHelper:

    def test_template_flow_style_call(self, ten_day_plan, scripted_input):
        before = copy.deepcopy(ten_day_plan)
        ten_day_plan.weekend_mode = 'spare'
        scripted_input([KEEP_END])

        choice = quiet(ui_modify.offer_plan_adjustment, ten_day_plan, before)

        assert choice == 'keep_end'
        assert schedule_sum(ten_day_plan) == pytest.approx(10000)

    def test_without_start_date_does_nothing(self):
        p = plan.Plan(total=10000, daily=1000, time=10)
        before = copy.deepcopy(p)
        p.weekend_mode = 'spare'

        assert ui_modify.offer_plan_adjustment(p, before) is None
