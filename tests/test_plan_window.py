"""Tests for the plan window: Plan.time, end_date, total_calendar_days, plan_days().

These replace ~21 copies of `int(plan.time) + plan.spare_days` (issues-program.org RC3)
and fix P5 (quick actions adding a year of spare days), P6 (spare days outside
the plan lengthening it) and P11 (fractional days losing words).
"""

import contextlib
import csv
import io
import pytest
from datetime import datetime, timedelta
from freezegun import freeze_time
import plan
import planea
import plan_export
import plan_manager
import calendar_view


MON = datetime(2026, 11, 2)


def day(n):
    """Date of calendar day n of a plan starting MON (1-based)."""
    return MON + timedelta(days=n - 1)


def schedule_sum(p):
    """What the calendar, exports and analytics show: sum of goals over the plan."""
    return sum(p.get_daily_goal(date=d) for d in p.plan_days())


@pytest.fixture
def ten_day_plan():
    """10,000 words / 10 writing days starting Monday 2026-11-02."""
    return plan.Plan(total=10000, daily=1000, time=10, start_date=MON)


class TestWholeDays:
    """Plan.time is always a whole number of days (P11)."""

    def test_time_rounds_up(self):
        p = plan.Plan(total=10000, daily=1000, time=10.5)

        assert p.time == 11

    def test_float_noise_does_not_add_a_day(self):
        p = plan.Plan(total=10000, daily=1000, time=48.0000000001)

        assert p.time == 48

    def test_calculate_time_spreads_total_over_whole_days(self):
        p = plan.Plan(total=50000, daily=1667, start_date=MON)

        p.calculate_time()

        assert p.time == 30
        assert p.daily == pytest.approx(50000 / 30)
        assert schedule_sum(p) == pytest.approx(50000)

    def test_exact_division_keeps_daily(self):
        p = plan.Plan(total=48000, daily=1000)

        p.calculate_time()

        assert p.time == 48
        assert p.daily == 1000

    def test_zero_total_gives_zero_days(self):
        p = plan.Plan(total=0, daily=1000)

        p.calculate_time()

        assert p.time == 0
        assert p.daily == 1000


class TestEndDate:
    """Plan.end_date and friends."""

    def test_no_spare_days(self, ten_day_plan):
        assert ten_day_plan.end_date == day(10)
        assert ten_day_plan.total_calendar_days == 10
        assert list(ten_day_plan.plan_days()) == [day(n) for n in range(1, 11)]

    def test_spare_day_inside_extends_plan(self, ten_day_plan):
        ten_day_plan.spare_days_dates.append(day(4))

        assert ten_day_plan.end_date == day(11)
        assert ten_day_plan.spare_days == 1
        assert ten_day_plan.total_calendar_days == 11

    def test_spare_day_on_would_be_last_day_extends_plan(self, ten_day_plan):
        ten_day_plan.spare_days_dates.append(day(10))

        assert ten_day_plan.end_date == day(11)

    def test_end_date_is_always_a_writing_day(self, ten_day_plan):
        ten_day_plan.spare_days_dates.extend([day(10), day(11), day(12)])

        assert ten_day_plan.end_date == day(13)
        assert not ten_day_plan.is_spare_day(ten_day_plan.end_date)

    def test_without_start_date(self):
        p = plan.Plan(total=10000, daily=1000, time=10, spare_days_dates=[day(4)])

        assert p.end_date is None
        assert p.total_calendar_days == 0
        assert list(p.plan_days()) == []
        assert p.spare_days == 1

    def test_without_writing_days(self):
        p = plan.Plan(total=0, daily=1000, time=0, start_date=MON)

        assert p.end_date is None
        assert p.total_calendar_days == 0


class TestSpareDaysOutsideThePlan:
    """P6: spare days outside the window don't lengthen the plan."""

    def test_spare_day_after_end_ignored(self, ten_day_plan):
        ten_day_plan.spare_days_dates.append(day(15))

        assert ten_day_plan.end_date == day(10)
        assert ten_day_plan.spare_days == 0
        assert schedule_sum(ten_day_plan) == pytest.approx(10000)

    def test_spare_day_before_start_ignored(self, ten_day_plan):
        ten_day_plan.spare_days_dates.append(MON - timedelta(days=3))

        assert ten_day_plan.end_date == day(10)
        assert ten_day_plan.spare_days == 0

    def test_moving_start_date_leaves_spare_day_behind(self, ten_day_plan):
        # Repro from issues-program.org: used to give an 11-day plan and 11,000 words
        ten_day_plan.spare_days_dates.append(day(3))

        ten_day_plan.start_date = MON - timedelta(days=13)

        assert ten_day_plan.total_calendar_days == 10
        assert schedule_sum(ten_day_plan) == pytest.approx(10000)

    def test_recalculate_total_ignores_spare_day_outside(self, ten_day_plan):
        ten_day_plan.spare_days_dates.append(day(20))

        assert ten_day_plan.recalculate_total_from_daily_goals() == pytest.approx(10000)


@freeze_time("2026-10-01")  # before the plan: quick actions skip past days
class TestMarkWeekdaysAsSpare:
    """P5: quick actions only mark days inside the (growing) plan window."""

    def test_saturdays_on_ten_day_plan(self, ten_day_plan):
        # Used to add 52 Saturdays: 62-day plan, 53,000 words.
        # Mon 11-02 .. Fri 11-06 (5), Sat 11-07 spare, Sun 11-08 .. Thu 11-12 (5)
        added = planea.mark_weekdays_as_spare(ten_day_plan, [5])

        assert added == 1
        assert ten_day_plan.spare_days_dates == [datetime(2026, 11, 7)]
        assert ten_day_plan.end_date == datetime(2026, 11, 12)
        assert schedule_sum(ten_day_plan) == pytest.approx(10000)

    def test_weekends_follow_growing_window(self, ten_day_plan):
        # 10 weekdays from Mon 11-02 end on Fri 11-13; only Sat 11-07 and
        # Sun 11-08 fall inside, the next weekend is after the end
        added = planea.mark_weekdays_as_spare(ten_day_plan, [5, 6])

        assert added == 2
        assert ten_day_plan.spare_days_dates == [datetime(2026, 11, 7), datetime(2026, 11, 8)]
        assert ten_day_plan.end_date == datetime(2026, 11, 13)
        assert ten_day_plan.total_calendar_days == 12

    def test_custom_weekend_days(self, ten_day_plan):
        ten_day_plan.weekend_days = [4, 5]  # Friday and Saturday

        planea.mark_weekdays_as_spare(ten_day_plan, ten_day_plan.weekend_days)

        # Mon-Thu (4), Fri 6 + Sat 7 spare, Sun-Thu (9), Fri 13 + Sat 14 spare, Sun 15 (10)
        assert ten_day_plan.spare_days_dates == [
            datetime(2026, 11, 6), datetime(2026, 11, 7),
            datetime(2026, 11, 13), datetime(2026, 11, 14),
        ]
        assert ten_day_plan.end_date == datetime(2026, 11, 15)

    def test_existing_spare_day_not_duplicated(self, ten_day_plan):
        ten_day_plan.spare_days_dates.append(datetime(2026, 11, 7))

        added = planea.mark_weekdays_as_spare(ten_day_plan, [5])

        assert added == 0
        assert len(ten_day_plan.spare_days_dates) == 1


class TestConsumersUseThePlanWindow:
    """Exports, calendar and plan manager read the same window."""

    def test_csv_has_one_row_per_plan_day(self, ten_day_plan, tmp_path):
        ten_day_plan.spare_days_dates.extend([day(4), day(30)])
        path = tmp_path / "plan.csv"

        plan_export.export_to_csv(ten_day_plan, path)

        with open(path, newline='') as f:
            rows = list(csv.DictReader(f))
        assert len(rows) == 11
        assert rows[-1]['Date'] == '2026-11-12'
        assert rows[-1]['Cumulative_Goal'] == '10000'

    def test_calendar_draws_every_plan_day(self, ten_day_plan):
        ten_day_plan.spare_days_dates.extend([day(4), day(30)])
        out = io.StringIO()

        with contextlib.redirect_stdout(out):
            calendar_view.display_calendar_view(ten_day_plan, ten_day_plan.start_date)

        assert out.getvalue().count("1,000w") == 10
        assert out.getvalue().count("SPARE") == 1

    def test_deadline_sort_uses_end_date(self):
        early = plan.Plan(name="early", total=1000, daily=100, time=10, start_date=MON)
        late = plan.Plan(name="late", total=1000, daily=100, time=10, start_date=MON,
                         spare_days_dates=[day(3)])

        ordered = plan_manager.sort_plans([late, early], sort_by="deadline", reverse=False)

        assert [p.name for p in ordered] == ["early", "late"]
