"""Tests for the running total in the monthly calendar.

Each day up to today shows the words written by the end of that day against
the total, and the completion percentage: 1,000 on day 1 and 1,100 on day 2
of an 80,000-word plan show 1,000/80,000 1.25% and 2,100/80,000 2.62%.
"""

import contextlib
import io
from datetime import datetime, timedelta
from freezegun import freeze_time
import pytest
import calendar_view
import plan


MON = datetime(2026, 11, 2)
TODAY = MON + timedelta(days=5)   # Saturday


def day(n):
    return MON + timedelta(days=n)


def make_plan(**kwargs):
    values = dict(name="Novel", total=80000, daily=1000, time=80, start_date=MON)
    values.update(kwargs)
    p = plan.Plan(**values)
    p.record_progress(day(0), 1000)
    p.record_progress(day(1), 1100)
    p.record_progress(day(4), 1250)
    return p


class TestWrittenThrough:

    def test_counts_entries_up_to_the_day(self):
        p = make_plan()

        assert p.get_plan_written(through=day(0)) == 1000
        assert p.get_plan_written(through=day(3)) == 2100
        assert p.get_plan_written(through=day(9)) == p.get_plan_written() == 3350

    def test_includes_preexisting_words_and_entries_before_the_plan(self):
        p = make_plan(preexisting_words=5000)
        p.record_progress(MON - timedelta(days=2), 400)

        assert p.get_total_written(through=MON - timedelta(days=1)) == 5400
        assert p.get_total_written(through=day(1)) == 7500

    def test_completion_percentage(self):
        p = make_plan()

        assert p.get_completion_percentage(through=day(1)) == pytest.approx(2.625)
        assert p.get_completion_percentage() == pytest.approx(3350 / 800)


@freeze_time(TODAY)
class TestRunningTotal:

    def test_the_example(self):
        p = make_plan()

        assert calendar_view.running_total(p, day(0)) == ("1,000/80,000", "1.25%")
        assert calendar_view.running_total(p, day(1)) == ("2,100/80,000", "2.62%")

    def test_days_without_words_carry_the_total(self):
        p = make_plan(spare_days_dates=[day(3)])

        assert calendar_view.running_total(p, day(2))[0] == "2,100/80,000"   # missed
        assert calendar_view.running_total(p, day(3))[0] == "2,100/80,000"   # spare

    def test_today_only_once_logged(self):
        p = make_plan()
        assert calendar_view.running_total(p, TODAY) is None

        p.record_progress(TODAY, 300)
        assert calendar_view.running_total(p, TODAY) == ("3,650/80,000", "4.56%")

    def test_none_for_future_days_or_without_progress(self):
        assert calendar_view.running_total(make_plan(), TODAY + timedelta(days=1)) is None
        empty = plan.Plan(total=80000, daily=1000, time=80, start_date=MON)
        assert calendar_view.running_total(empty, day(0)) is None

    def test_wide_totals_are_shortened(self):
        p = make_plan(total=150000, time=150, preexisting_words=101000)

        assert calendar_view.running_total(p, day(0)) == ("102.0k/150k", "68.00%")
        assert all(len(part) <= calendar_view.DAY_CELL_WIDTH
                   for part in calendar_view.running_total(p, day(4)))

    def test_shown_in_the_calendar(self, monkeypatch):
        # The month table is ~115 columns wide; narrower terminals wrap every cell
        monkeypatch.setenv("COLUMNS", "120")
        p = make_plan(spare_days_dates=[day(3)])
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            calendar_view.display_calendar_view(p, p.start_date)
        output = out.getvalue()

        assert "1,000/80,000" in output and "1.25%" in output
        # Mon-Fri, then nothing for today (not logged) or later days
        assert output.count("/80,000") == 5
        assert "3,350/80,000" in output and "4.19%" in output
