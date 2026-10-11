"""Tests for the analytics pace figures (issues-program.org A1).

- The average is per elapsed writing day: missed days count, rest days don't.
- The ETA spends that average on writing days only, skipping rest days.
- Velocity is a moving average over elapsed writing days, so gaps show.
- "Days ahead/behind" is measured along the schedule, not divided by the
  current daily goal.
"""

import pytest
from datetime import datetime, timedelta
from freezegun import freeze_time
import plan
import progress_analytics as pa


MON = datetime(2026, 11, 2)


def day(n):
    """Date of calendar day n of a plan starting MON (1-based)."""
    return MON + timedelta(days=n - 1)


def at(n, hour=10):
    """freeze_time target: day n at 10:00."""
    return day(n) + timedelta(hours=hour)


def make_plan(**kwargs):
    values = dict(total=10000, daily=1000, time=10, start_date=MON)
    values.update(kwargs)
    p = plan.Plan(**values)
    p.sync_daily()
    return p


def write(p, days, words):
    for n in days:
        p.record_progress(day(n), words)


class TestAverage:

    @freeze_time(at(6))
    def test_missed_days_count(self):
        p = make_plan()
        write(p, [1, 2, 3], 1000)   # days 4 and 5 missed

        # Used to be 1,000: only days with entries counted
        assert pa.average_words_per_writing_day(p) == pytest.approx(600)
        assert pa.calculate_statistics(p)['average_per_day'] == pytest.approx(600)

    @freeze_time(at(9))
    def test_rest_days_do_not_count(self):
        p = make_plan(weekend_mode="spare")
        write(p, [1, 2, 3, 4, 5, 8], 1250)

        # Days 1-5 and 8; the weekend (6, 7) is rest
        assert pa.average_words_per_writing_day(p) == pytest.approx(1250)

    @freeze_time(at(9))
    def test_writing_on_a_rest_day_counts_as_a_day(self):
        p = make_plan(weekend_mode="spare")
        write(p, [1, 2, 3, 4, 5, 6, 8], 1000)

        assert len(pa.elapsed_writing_days(p)) == 7

    @freeze_time(at(3))
    def test_today_counts_once_logged(self):
        p = make_plan()
        write(p, [1, 2], 1000)
        assert len(pa.elapsed_writing_days(p)) == 2

        p.record_progress(day(3), 500)

        assert len(pa.elapsed_writing_days(p)) == 3
        assert pa.average_words_per_writing_day(p) == pytest.approx(2500 / 3)


class TestEta:

    @freeze_time(at(4))
    def test_on_pace_finishes_on_the_end_date(self):
        # 1,250 per weekday; Thu + Fri, weekend off, Mon-Wed = 5 writing days
        p = make_plan(weekend_mode="spare")
        write(p, [1, 2, 3], 1250)

        assert pa.calculate_completion_eta(p) == day(10)

    @freeze_time(at(4))
    def test_slower_pace_keeps_skipping_weekends_after_the_end(self):
        # 625 per weekday: 8,125 left = 13 writing days from Thu 11-05:
        # Thu, Fri (2), Mon 9 - Fri 13 (7), Mon 16 - Fri 20 (12), Mon 23 (13)
        p = make_plan(weekend_mode="spare")
        write(p, [1, 2, 3], 625)

        assert pa.calculate_completion_eta(p) == datetime(2026, 11, 23)

    @freeze_time(at(4))
    def test_starts_tomorrow_once_today_is_logged(self):
        p = make_plan()
        write(p, [1, 2, 3, 4], 1000)

        # 6,000 left at 1,000/day: days 5-10
        assert pa.calculate_completion_eta(p) == day(10)

    @freeze_time(at(4))
    def test_missed_days_make_it_later(self):
        p = make_plan()
        write(p, [1], 1500)   # days 2 and 3 missed: 500 per writing day

        # 8,500 left at 500/day = 17 days from day 4
        assert pa.calculate_completion_eta(p) == day(20)

    @freeze_time(at(4))
    def test_completed(self):
        p = make_plan()
        write(p, [1], 10000)

        assert pa.calculate_completion_eta(p) == day(4)


class TestDaysAheadBehind:

    @freeze_time(at(6))
    def test_flat_plan(self):
        p = make_plan()
        write(p, [1, 2, 3], 1000)

        # 3,000 written = 3 days of goals; 5 days expected
        assert pa.calculate_days_ahead_behind(p) == pytest.approx(-2)

    @freeze_time(at(6))
    def test_follows_the_pattern_not_the_daily_goal(self):
        p = make_plan(pattern="rising", pattern_config={'start_multiplier': 0.5, 'end_multiplier': 1.5})
        goals = [p.get_daily_goal(date=day(n)) for n in range(1, 4)]
        p.record_progress(day(1), sum(goals))   # days 1-3 of goals (stored as whole words)

        assert pa.calculate_days_ahead_behind(p) == pytest.approx(-2, abs=0.01)

    @freeze_time(at(6))
    def test_ahead(self):
        p = make_plan()
        write(p, [1, 2, 3, 4, 5], 1500)   # 7,500 = 7.5 days of goals

        assert pa.calculate_days_ahead_behind(p) == pytest.approx(2.5)

    @freeze_time(at(6))
    def test_after_recalculation_on_track_is_zero(self):
        # Dividing by the new daily goal used to change the answer
        p = make_plan()
        write(p, [1, 2, 3, 4, 5], 600)
        p.recalculate_from_progress()

        assert pa.calculate_days_ahead_behind(p) == pytest.approx(0)

    @freeze_time(at(9))
    def test_weekend_rest_days_are_not_counted(self):
        p = make_plan(weekend_mode="spare")
        write(p, [1, 2, 3, 4, 5], 1250)   # all weekdays so far done; Mon (8) missed

        assert pa.calculate_days_ahead_behind(p) == pytest.approx(-1)


class TestGraphs:

    @pytest.fixture
    def plotted(self, monkeypatch):
        calls = []
        monkeypatch.setattr(pa.plt, 'plot', lambda x, y, **kw: calls.append((kw.get('label'), list(y))))
        monkeypatch.setattr(pa.plt, 'bar', lambda *a, **kw: None)
        monkeypatch.setattr(pa.plt, 'show', lambda: None)
        return calls

    @freeze_time(at(6))
    def test_velocity_shows_gaps(self, plotted, capsys):
        p = make_plan()
        write(p, [1, 2, 5], 900)   # days 3 and 4 missed

        pa.plot_velocity(p)

        velocity = dict(plotted)["Velocity (3-day avg)"]
        target = dict(plotted)["Target"]
        # Windows: 1-3, 2-4, 3-5 (used to skip the missed days entirely)
        assert velocity == pytest.approx([600, 300, 300])
        assert target == pytest.approx([1000, 1000, 1000])

    @freeze_time(at(6))
    def test_daily_graph_shows_missed_days(self, monkeypatch, capsys):
        p = make_plan()
        write(p, [1, 5], 900)
        shown = []
        monkeypatch.setattr(pa.plt, 'multiple_bar', lambda x, ys, **kw: shown.append(ys))
        monkeypatch.setattr(pa.plt, 'show', lambda: None)

        pa.plot_daily_progress(p)

        assert shown and shown[0][1] == [900, 0, 0, 0, 900]


class TestLongestStreak:

    @freeze_time(at(10))
    def test_weekend_rest_days_do_not_break_it(self):
        p = make_plan(weekend_mode="spare")
        write(p, [3, 4, 5, 8, 9], 1250)

        assert pa.calculate_longest_streak(p) == 5
