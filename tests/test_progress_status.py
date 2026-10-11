"""Tests for day status and the writing streak (issues-program.org P19).

Rest days (goal 0: spare days, weekend rest days, custom 0) used to show as
missed and break the streak, and the streak was 0 all day until today's words
were logged.
"""

import contextlib
import io
from datetime import datetime, timedelta
from freezegun import freeze_time
import plan
import calendar_view


MON = datetime(2026, 11, 2)
TODAY = MON + timedelta(days=9)   # Wednesday, day 10 of a 14-day plan


def day(n):
    """Date of calendar day n of a plan starting MON (1-based)."""
    return MON + timedelta(days=n - 1)


def make_plan(**kwargs):
    values = dict(total=14000, daily=1000, time=14, start_date=MON)
    values.update(kwargs)
    return plan.Plan(**values)


def write(p, days, words=1000):
    for n in days:
        p.record_progress(day(n), words)


@freeze_time(TODAY + timedelta(hours=10))
class TestStatus:

    def test_weekend_rest_day_is_not_missed(self):
        p = make_plan(weekend_mode="spare")

        # Sat 11-07 and Sun 11-08
        assert p.get_progress_status_for_date(day(6)) == 'spare'
        assert p.get_progress_status_for_date(day(7)) == 'spare'

    def test_custom_zero_and_spare_day(self):
        p = make_plan(spare_days_dates=[day(3)])
        p.set_custom_daily_goal(day(4), 0)

        assert p.get_progress_status_for_date(day(3)) == 'spare'
        assert p.get_progress_status_for_date(day(4)) == 'spare'

    def test_writing_on_a_rest_day_counts(self):
        p = make_plan(weekend_mode="spare")
        p.record_progress(day(6), 300)

        assert p.get_progress_status_for_date(day(6)) == 'exceeded'

    def test_past_day_with_goal_and_no_words_is_missed(self):
        assert make_plan().get_progress_status_for_date(day(2)) == 'missed'

    def test_today_without_words_is_pending(self):
        p = make_plan()

        assert p.get_progress_status_for_date(TODAY) == 'future'

    def test_today_with_some_words_is_partial(self):
        p = make_plan()
        p.record_progress(TODAY, 400)

        assert p.get_progress_status_for_date(TODAY) == 'partial'

    def test_outside_the_plan(self):
        p = make_plan()

        assert p.get_progress_status_for_date(MON - timedelta(days=1)) == 'no_goal'
        assert p.get_progress_status_for_date(day(15)) == 'no_goal'

    def test_future_rest_day(self):
        p = make_plan(weekend_mode="spare")

        assert p.get_progress_status_for_date(day(13)) == 'spare'
        assert p.get_progress_status_for_date(day(12)) == 'future'


@freeze_time(TODAY + timedelta(hours=10))
class TestStreak:

    def test_counts_from_yesterday_until_today_is_logged(self):
        p = make_plan()
        write(p, range(5, 10))

        assert p.get_current_streak() == 5

        p.record_progress(TODAY, 200)
        assert p.get_current_streak() == 6

    def test_weekend_rest_days_do_not_break_it(self):
        # Wrote Thu-Fri (days 4-5), rested Sat-Sun, wrote Mon-Tue (days 8-9)
        p = make_plan(weekend_mode="spare")
        write(p, [4, 5, 8, 9])

        assert p.get_current_streak() == 4

    def test_writing_on_a_rest_day_adds_to_it(self):
        p = make_plan(weekend_mode="spare")
        write(p, [5, 6, 8, 9])

        assert p.get_current_streak() == 4

    def test_custom_zero_day_does_not_break_it(self):
        p = make_plan()
        p.set_custom_daily_goal(day(8), 0)
        write(p, [6, 7, 9])

        assert p.get_current_streak() == 3

    def test_missed_day_breaks_it(self):
        p = make_plan()
        write(p, [5, 6, 8, 9])

        assert p.get_current_streak() == 2

    def test_no_progress(self):
        assert make_plan().get_current_streak() == 0

    def test_after_the_end_a_day_without_words_breaks_it(self):
        p = make_plan(time=5)   # ends Fri 11-06
        write(p, range(1, 6))

        assert p.get_current_streak() == 0


@freeze_time(TODAY + timedelta(hours=10))
class TestCalendar:

    def test_rest_days_shown_as_rest_not_missed(self):
        p = make_plan(weekend_mode="spare")
        p.sync_daily()
        write(p, range(1, 6), 1400)
        write(p, [8, 9], 1400)
        out = io.StringIO()

        with contextlib.redirect_stdout(out):
            calendar_view.display_calendar_view(p, p.start_date)

        text = out.getvalue()
        # Two weekends in the plan: 11-07/08 and 11-14/15
        assert text.count("REST") == 4
        assert "✗" not in text
