"""Tests for Plan.milestones() and where it's shown (issues-program.org P18).

Milestones used to be linear (start + int(time x p) - 1), so spare days,
weekends and patterns gave wrong dates, and a 1-day plan put 25% on the day
before the start. They now follow the schedule.
"""

import contextlib
import io
from datetime import datetime, timedelta
from freezegun import freeze_time
import plan
import plan_export
import calendar_view


MON = datetime(2026, 11, 2)


def day(n):
    """Date of calendar day n of a plan starting MON (1-based)."""
    return MON + timedelta(days=n - 1)


def make_plan(**kwargs):
    values = dict(total=10000, daily=1000, time=10, start_date=MON)
    values.update(kwargs)
    return plan.Plan(**values)


def dates(p):
    return [m['date'] for m in p.milestones()]


class TestMilestoneDates:

    def test_flat_plan(self):
        p = make_plan()

        # 2,500 needs 3 days; the old formula said day 2 (2,000 words)
        assert dates(p) == [day(3), day(5), day(8), day(10)]
        assert [m['day'] for m in p.milestones()] == [3, 5, 8, 10]
        assert [m['words'] for m in p.milestones()] == [2500, 5000, 7500, 10000]

    def test_one_day_plan(self):
        # Used to put 25% on the day before the start
        p = make_plan(total=1000, time=1)

        assert dates(p) == [MON] * 4

    def test_spare_day(self):
        p = make_plan(spare_days_dates=[day(4)])

        assert dates(p) == [day(3), day(6), day(9), day(11)]

    def test_weekends_as_rest_days(self):
        # 1,250 on weekdays, 0 on Sat 11-07 and Sun 11-08: 5,000 on Thu 11-05,
        # 7,500 on Mon 11-09
        p = make_plan(weekend_mode="spare")
        p.sync_daily()

        assert dates(p) == [day(2), day(4), day(8), day(10)]

    def test_rising_pattern_reaches_half_later(self):
        p = make_plan(pattern="rising", pattern_config={'start_multiplier': 0.5, 'end_multiplier': 1.5})

        assert dates(p)[1] > day(5)
        assert dates(p)[3] == day(10)

    def test_pre_existing_words_count_from_the_start(self):
        # 50,000 goal, 20,000 already written, 30,000 over 30 days
        p = make_plan(total=50000, time=30, preexisting_words=20000)
        p.calculate_daily()

        first, second = p.milestones()[:2]
        assert first['date'] is None and first['day'] == 0 and first['reached']
        # 25,000 = 20,000 + 5 days
        assert second['date'] == day(5) and not second['reached']
        assert p.milestones()[3]['date'] == day(30)

    @freeze_time(day(6) + timedelta(hours=10))
    def test_after_recalculation_100_percent_is_the_end_date(self):
        p = make_plan()
        for n in range(1, 6):
            p.record_progress(day(n), 500)
        p.recalculate_from_progress()

        assert p.schedule_adjustment != 0
        assert dates(p)[3] == p.end_date

    def test_reached(self):
        p = make_plan()
        p.record_progress(day(1), 5000)

        assert [m['reached'] for m in p.milestones()] == [True, True, False, False]


class TestShownMilestones:

    def test_calendar(self):
        p = make_plan(spare_days_dates=[day(4)])
        out = io.StringIO()

        with contextlib.redirect_stdout(out):
            calendar_view.display_calendar_view(p, p.start_date)

        text = out.getvalue()
        assert "Plan Day" in text
        assert "Nov 07, 2026" in text  # 50%: day 6
        assert "Nov 12, 2026" in text  # 100%: day 11

    def test_markdown_export(self, tmp_path):
        p = make_plan(total=50000, time=30, preexisting_words=20000)
        p.calculate_daily()
        path = tmp_path / "plan.md"

        plan_export.export_to_markdown(p, path)

        text = path.read_text()
        assert "| 25% | before the start | 12,500 | - | ✅ reached |" in text
        assert "| 50% | Nov 06, 2026 | 25,000 | 5 |  |" in text
