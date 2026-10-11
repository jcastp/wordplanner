"""Tests for the weekly summary (calendar view).

Weeks are 7-day blocks from the start date. Fixed: weekend rest days counted
as writing days, the daily goal hid weekend and custom goals, the cumulative
total left out pre-existing words, and truncating each week made it drift.
Added: words written per week, days written, actual vs planned total and
ahead/behind.
"""

import contextlib
import io
from datetime import datetime, timedelta
from freezegun import freeze_time
import pytest
import calendar_view
import plan


WED = datetime(2026, 11, 4)


def day(n):
    return WED + timedelta(days=n)


def make_plan(**kwargs):
    values = dict(name="Novel", total=10000, daily=1000, time=10, start_date=WED)
    values.update(kwargs)
    p = plan.Plan(**values)
    p.sync_daily()
    return p


def weeks(p):
    return calendar_view.weekly_summary(p)


@freeze_time("2026-10-01")   # before the plan
class TestPlannedWeeks:

    def test_weekend_rest_days_are_rest_days(self):
        first, second = weeks(make_plan(weekend_mode="spare"))

        assert (first['writing_days'], first['rest_days']) == (5, 2)
        assert calendar_view.format_week_goal(first) == "1,250"
        assert first['goal'] == pytest.approx(6250)
        assert (second['writing_days'], second['rest_days']) == (3, 0)

    def test_spare_dates_are_rest_days(self):
        first, _ = weeks(make_plan(spare_days_dates=[day(1)]))

        assert (first['writing_days'], first['rest_days']) == (6, 1)

    def test_daily_goal_shows_weekend_and_custom_goals(self):
        p = make_plan(weekend_mode="different", weekend_daily=300)
        assert calendar_view.format_week_goal(weeks(p)[0]) == "300-1,175"

        p = make_plan(custom_daily_goals={day(8).strftime('%Y-%m-%d'): 2000})
        assert calendar_view.format_week_goal(weeks(p)[1]) == "889-2,000"

    def test_totals_include_preexisting_words(self):
        first, second = weeks(make_plan(preexisting_words=4000))

        assert first['planned_total'] == pytest.approx(4000 + 7 * 600)
        assert second['planned_total'] == pytest.approx(10000)

    def test_totals_do_not_drift(self):
        # 666.67 a day: truncating each week used to end at 9,998
        p = make_plan(time=15)

        assert weeks(p)[-1]['planned_total'] == pytest.approx(10000)

    def test_last_total_is_the_goal_after_a_recalculation(self):
        p = make_plan()
        for n in range(3):
            p.record_progress(day(n), 500)
        with freeze_time(day(3)):
            p.recalculate_from_progress()
            assert weeks(p)[-1]['planned_total'] == pytest.approx(10000)

    def test_future_weeks_have_no_progress(self):
        first = weeks(make_plan())[0]

        assert not first['started']
        assert first['written'] is None and first['difference'] is None
        assert calendar_view.format_week_written(first) == ""


@freeze_time(day(9))   # Friday of week 2
class TestProgress:

    @pytest.fixture
    def p(self):
        p = make_plan(total=20000, time=20, preexisting_words=1000)   # 950 a day
        for n in range(7):
            if n != 3:
                p.record_progress(day(n), 1200)
        p.record_progress(day(7), 500)
        return p

    def test_ended_week(self, p):
        first = weeks(p)[0]

        assert first['ended']
        assert first['written'] == 6 * 1200
        assert (first['days_written'], first['writing_days']) == (6, 7)
        assert first['written_total'] == 1000 + 7200
        assert first['difference'] == pytest.approx(7200 - 7 * 950)
        assert calendar_view.format_week_written(first) == "7,200 [green]✓[/green] 108%"

    def test_current_week_is_expected_up_to_yesterday(self, p):
        second = weeks(p)[1]

        assert second['started'] and not second['ended']
        assert second['written'] == 500
        assert second['days_written'] == 1
        # Expected: 9 days (through yesterday) at 950
        assert second['difference'] == pytest.approx(7700 - 9 * 950)
        assert second['difference'] == pytest.approx(p.is_on_track()[1]['difference'])
        assert calendar_view.format_week_written(second) == "500 8%"

    def test_writing_today_counts(self, p):
        p.record_progress(day(9), 3000)

        assert weeks(p)[1]['difference'] == pytest.approx(10700 - 9 * 950)

    @pytest.mark.parametrize("words, expected", [
        (3000, "3,000 [yellow]~[/yellow] 43%"),   # of 7,000
        (0, "0 [red]✗[/red] 0%"),
    ])
    def test_short_weeks(self, words, expected):
        p = make_plan(total=20000, time=20)
        if words:
            p.record_progress(day(0), words)

        assert calendar_view.format_week_written(weeks(p)[0]) == expected

    @pytest.mark.parametrize("difference, expected", [
        (564.4, "[green]+564[/green]"),
        (-691, "[red]-691[/red]"),
        (0.2, "0"),
        (None, ""),
    ])
    def test_format_difference(self, difference, expected):
        assert calendar_view.format_difference(difference) == expected

    def test_display(self, p, monkeypatch):
        monkeypatch.setenv("COLUMNS", "130")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            calendar_view.display_weekly_summary(p, p.start_date)
        text = out.getvalue()

        assert "Weekly Summary (Nov 04, 2026 - Nov 23, 2026)" in text
        assert "Nov 04 - Nov 10" in text
        assert "6/7" in text and "-/6" in text
        assert "7,200 ✓ 108%" in text
        assert "+550" in text   # 8,200 written by the end of week 1, 7,650 planned
        assert "20,000" in text
