"""Tests for Plan.build_schedule() and the schedule-aware calculator.

issues-program.org RC1 (one schedule, one invariant) and P10 (the 3-variable
calculator on a started plan), plus the bugs they fix: P1, P2, P3, P12 (items
2 and 3), P15 and the formula in P13 item 3.
"""

import contextlib
import io
import itertools
import json
import pytest
from datetime import datetime, timedelta
from freezegun import freeze_time
import plan
import planea


MON = datetime(2026, 11, 2)
PATTERNS = {
    "flat": {},
    "valley": {'peak_multiplier': 1.5, 'valley_multiplier': 0.7},
    "mountain": {'peak_multiplier': 1.5, 'valley_multiplier': 0.7},
    "rising": {'start_multiplier': 0.5, 'end_multiplier': 1.5},
    "declining": {'start_multiplier': 1.5, 'end_multiplier': 0.5},
    "random": {'min_multiplier': 0.5, 'max_multiplier': 1.5, 'seed': 42},
}


def day(n):
    """Date of calendar day n of a plan starting MON (1-based)."""
    return MON + timedelta(days=n - 1)


def schedule_sum(p):
    return sum(p.build_schedule()['goals'].values())


def goals(p, days):
    return [p.get_daily_goal(date=day(n)) for n in days]


def quiet(func, *args, **kwargs):
    with contextlib.redirect_stdout(io.StringIO()):
        return func(*args, **kwargs)


def make_plan(**kwargs):
    values = dict(total=10000, daily=1000, time=10, start_date=MON)
    values.update(kwargs)
    return plan.Plan(**values)


class TestScheduleInvariant:
    """The schedule always adds up to the words the plan has to cover."""

    @pytest.mark.parametrize("pattern, weekend_mode, spare, custom, preexisting", itertools.product(
        PATTERNS, ["same", "different", "spare"], [False, True], [False, True], [0, 3000]))
    def test_sum_equals_words_to_schedule(self, pattern, weekend_mode, spare, custom, preexisting):
        p = make_plan(total=20000, time=14, pattern=pattern, pattern_config=dict(PATTERNS[pattern]),
                      weekend_mode=weekend_mode, weekend_daily=800, preexisting_words=preexisting)
        if spare:
            p.spare_days_dates.extend([day(3), day(9)])
        if custom:
            p.set_custom_daily_goal(day(4), 2500)
            p.set_custom_daily_goal(day(11), 0)

        assert schedule_sum(p) == pytest.approx(20000 - preexisting)
        assert all(g >= 0 for g in p.build_schedule()['goals'].values())

    def test_fixed_days_keep_their_goals(self):
        p = make_plan(weekend_mode="different", weekend_daily=300)
        p.set_custom_daily_goal(day(2), 2000)

        assert p.get_daily_goal(date=day(2)) == 2000
        assert p.get_daily_goal(date=day(6)) == 300   # Saturday
        assert p.get_daily_goal(date=day(7)) == 300   # Sunday

    def test_fixed_days_larger_than_total_leave_open_days_at_zero(self):
        p = make_plan(total=1000)
        p.set_custom_daily_goal(day(1), 5000)

        assert goals(p, range(2, 11)) == [0] * 9
        assert p.build_schedule()['level'] == 0

    def test_days_outside_the_plan_have_no_goal(self):
        p = make_plan()

        assert p.get_daily_goal(date=day(11)) == 0
        assert p.get_daily_goal(date=MON - timedelta(days=1)) == 0


class TestPatterns:
    """P1, P2, P15: patterns follow writing days and cover the words exactly."""

    def test_spare_day_does_not_shift_the_pattern(self):
        # P1: valley + one spare day used to sum to 10,294 with a flat last day
        plain = make_plan(pattern="valley", pattern_config=dict(PATTERNS["valley"]))
        with_spare = make_plan(pattern="valley", pattern_config=dict(PATTERNS["valley"]),
                               spare_days_dates=[day(5)])

        writing_days = [d for d in with_spare.plan_days() if not with_spare.is_spare_day(d)]
        assert [with_spare.get_daily_goal(date=d) for d in writing_days] == \
            pytest.approx(goals(plain, range(1, 11)))
        assert schedule_sum(with_spare) == pytest.approx(10000)

    def test_weekend_different_with_pattern(self):
        # P2: rising + weekend-different used to sum to 10,778
        p = make_plan(pattern="rising", pattern_config=dict(PATTERNS["rising"]),
                      weekend_mode="different", weekend_daily=1500)

        assert schedule_sum(p) == pytest.approx(10000)
        weekdays = [p.get_daily_goal(date=d) for d in p.plan_days() if not p.is_weekend(d)]
        assert weekdays == sorted(weekdays)

    def test_pattern_shape_kept_around_custom_goal(self):
        p = make_plan(pattern="rising", pattern_config=dict(PATTERNS["rising"]))
        p.set_custom_daily_goal(day(5), 1000)

        open_goals = goals(p, [1, 2, 3, 4, 6, 7, 8, 9, 10])
        assert open_goals == sorted(open_goals)
        assert schedule_sum(p) == pytest.approx(10000)

    def test_random_pattern_is_stable(self):
        # P15: used to re-roll on every cache reset and reload
        p = make_plan(pattern="random", pattern_config={'min_multiplier': 0.5, 'max_multiplier': 1.5})
        first = goals(p, range(1, 11))

        p.invalidate_daily_goals_cache()
        reloaded = plan.Plan.from_json(p.to_json())

        assert 'seed' in p.pattern_config
        assert goals(p, range(1, 11)) == first
        assert goals(reloaded, range(1, 11)) == pytest.approx(first)


@freeze_time("2026-11-07 10:00")  # day 6: the recalculation day is today
class TestCalculatorOnAStartedPlan:
    """P10: calculate_daily/time/words account for locked, fixed and pre-existing words."""

    @pytest.fixture
    def recalculated_plan(self):
        # 10,000 / 10 days; 1,500 written on each of days 1-5; recalculated on day 6
        p = make_plan()
        for n in range(1, 6):
            p.record_progress(day(n), 1500)
        p.recalculate_from_progress(as_of_date=day(6))
        return p

    def test_recalculated_plan_state(self, recalculated_plan):
        assert recalculated_plan.daily == pytest.approx(500)
        assert goals(recalculated_plan, range(6, 11)) == [pytest.approx(500)] * 5

    def test_more_days_keep_daily(self, recalculated_plan):
        # Repro from issues-program.org: used to give total 6,000 with 7,500 written
        recalculated_plan.time = 12
        recalculated_plan.calculate_words()

        assert recalculated_plan.total == pytest.approx(11000)
        assert goals(recalculated_plan, range(6, 13)) == [pytest.approx(500)] * 7

    def test_new_total_keep_time(self, recalculated_plan):
        recalculated_plan.total = 12500
        recalculated_plan.calculate_daily()

        # 12,500 - 7,500 written = 5,000 over 5 open days
        assert recalculated_plan.daily == pytest.approx(1000)
        assert goals(recalculated_plan, range(1, 6)) == [1000] * 5

    def test_new_total_keep_daily(self, recalculated_plan):
        recalculated_plan.total = 12500
        recalculated_plan.calculate_time()

        # 5,000 left at 500/day -> 10 open days after the 5 locked ones
        assert recalculated_plan.time == 15
        assert recalculated_plan.daily == pytest.approx(500)

    def test_calculate_time_counts_fixed_days(self):
        p = make_plan(total=10000, daily=1000, weekend_mode="spare")
        p.calculate_time()

        # Weekends are rest days inside the window: 10 working days need 14 calendar days,
        # i.e. time 14 (time counts every non-spare-date day, weekend-spare included)
        assert schedule_sum(p) == pytest.approx(10000)
        assert p.daily == pytest.approx(1000)
        assert p.end_date == day(12)

    def test_calculate_time_never_drops_locked_days(self):
        p = make_plan()
        p.lock_past_goals(day(6))
        p.total = 5000
        p.calculate_time()

        assert p.time >= 5
        assert goals(p, range(1, 6)) == [1000] * 5

    def test_calculate_words_with_custom_goal(self):
        p = make_plan()
        p.set_custom_daily_goal(day(3), 3000)

        p.calculate_words()

        assert p.total == pytest.approx(12000)
        assert p.get_daily_goal(date=day(4)) == pytest.approx(1000)

    def test_without_start_date(self):
        p = plan.Plan(total=10000, time=8)
        p.calculate_daily()
        assert p.daily == pytest.approx(1250)

        p.daily = 2000
        p.calculate_time()
        assert p.time == 5


@freeze_time("2026-11-07 10:00")  # day 6: the recalculation day is today
class TestRecalculateFromProgressBaseline:
    """After a recalculation, the plan follows the new baseline."""

    def test_on_track_right_after_recalculation(self):
        p = make_plan()
        for n in range(1, 6):
            p.record_progress(day(n), 1500)

        p.recalculate_from_progress(as_of_date=day(6))
        p.record_progress(day(6), 500)
        _, info = p.is_on_track(as_of_date=day(6))

        assert info['status'] == 'on_track'
        assert info['expected_words'] == pytest.approx(8000)

    def test_weekend_spare_days_not_counted_as_remaining(self):
        # P12 item 2: used to count 13 days and schedule only 6,231 of 9,000
        p = make_plan(time=14, weekend_mode="spare")
        p.record_progress(day(1), 1000)

        result = p.recalculate_from_progress(as_of_date=day(2))

        future = sum(p.get_daily_goal(date=d) for d in p.plan_days() if d >= day(2))
        assert future == pytest.approx(9000)
        assert result['remaining_writing_days'] == 9
        assert result['new_daily'] == pytest.approx(1000)

    def test_weekend_different_gets_weekday_goal(self):
        p = make_plan(time=14, weekend_mode="different", weekend_daily=2000)
        p.record_progress(day(1), 1000)

        result = p.recalculate_from_progress(as_of_date=day(2))

        assert p.weekend_daily == pytest.approx(result['new_daily'])
        assert sum(p.get_daily_goal(date=d) for d in p.plan_days() if d >= day(2)) == pytest.approx(9000)

    def test_later_changes_keep_the_baseline(self):
        p = make_plan()
        for n in range(1, 6):
            p.record_progress(day(n), 1500)
        p.recalculate_from_progress(as_of_date=day(6))

        p.set_custom_daily_goal(day(8), 1000)
        quiet(planea.recalculate_plan_with_choice, p, p.total, 'total')

        # Still covers exactly the 2,500 words left
        future = sum(goals(p, range(6, 11)))
        assert future == pytest.approx(2500)


@freeze_time("2026-11-07 10:00")  # day 6: the recalculation day is today
class TestAdjustTimeFromProgress:
    """'Finish early' / 'extend deadline': keep daily, move the end date (P13 item 3)."""

    def test_ahead_finishes_early(self):
        p = make_plan()
        for n in range(1, 6):
            p.record_progress(day(n), 1500)

        result = p.adjust_time_from_progress(as_of_date=day(6))

        # 2,500 left at 1,000/day -> 3 days after the 5 locked ones
        assert result['new_time'] == 8
        assert result['new_end_date'] == day(8)
        assert sum(goals(p, range(6, 9))) == pytest.approx(2500)

    def test_behind_extends_deadline(self):
        p = make_plan(pattern="rising", pattern_config=dict(PATTERNS["rising"]))
        for n in range(1, 6):
            p.record_progress(day(n), 300)

        result = p.adjust_time_from_progress(as_of_date=day(6))

        assert result['new_end_date'] > result['old_end_date']
        assert sum(goals(p, range(6, result['new_time'] + 1))) == pytest.approx(10000 - 1500)

    @freeze_time("2026-11-06 10:00")  # Friday, day 5
    def test_preview_not_applied_when_declined(self, scripted_input):
        p = make_plan()
        for n in range(1, 5):
            p.record_progress(day(n), 1500)
        before = p.to_dict()
        scripted_input(["n"])

        quiet(planea.offer_deadline_adjustment, p)

        assert p.to_dict() == before

    @freeze_time("2026-11-06 10:00")
    def test_applied_when_accepted(self, scripted_input):
        p = make_plan()
        for n in range(1, 5):
            p.record_progress(day(n), 1500)
        scripted_input(["y"])

        quiet(planea.offer_deadline_adjustment, p)

        # Today (day 5) keeps 1,000; 3,000 left after it at 1,000/day -> ends day 8
        assert p.end_date == day(8)


class TestKeepTotalOrDays:
    """recalculate_plan_with_choice() on top of the schedule (P3)."""

    def test_weekend_spare_keep_total(self):
        # P3: used to give daily 1,200 and a 9,600 schedule
        p = make_plan(weekend_mode="spare")

        quiet(planea.recalculate_plan_with_choice, p, 10000, 'total', 1000)

        assert p.daily == pytest.approx(1250)
        assert schedule_sum(p) == pytest.approx(10000)

    def test_weekend_spare_keep_days(self):
        p = make_plan(weekend_mode="spare")

        quiet(planea.recalculate_plan_with_choice, p, 10000, 'days', 1000)

        assert p.total == pytest.approx(8000)
        assert p.daily == pytest.approx(1000)

    def test_pattern_keep_total_with_custom_goal(self):
        # P3: daily changes used to have no effect on non-flat patterns
        p = make_plan(pattern="rising", pattern_config=dict(PATTERNS["rising"]))
        p.set_custom_daily_goal(day(5), 4000)

        quiet(planea.recalculate_plan_with_choice, p, 10000, 'total')

        assert schedule_sum(p) == pytest.approx(10000)

    def test_no_open_days_sets_total_to_fixed_words(self):
        p = make_plan(time=2)
        p.set_custom_daily_goal(day(1), 700)
        p.set_custom_daily_goal(day(2), 800)

        quiet(planea.recalculate_plan_with_choice, p, 10000, 'total')

        assert p.total == pytest.approx(1500)


class TestLegacyFiles:
    """Plans saved before the schedule rewrite keep what they showed."""

    def test_old_recalculated_plan_keeps_its_daily(self, sample_plan_dict):
        # Old recalculation: daily 500 from day 6, past days frozen as custom goals,
        # pattern flat with pattern_config null, total left at 10,000
        sample_plan_dict.update({
            'total': 10000, 'daily': 500, 'time': 10, 'start_date': '2025-11-01T00:00:00',
            'spare_days_dates': [], 'pattern': 'flat', 'pattern_config': None,
            'progress': {f'2025-11-0{n}': 1500 for n in range(1, 6)},
            'custom_daily_goals': {f'2025-11-0{n}': 1000 for n in range(1, 6)},
        })

        p = plan.Plan.from_dict(sample_plan_dict)

        assert p.schedule_adjustment == pytest.approx(-2500)
        assert p.get_daily_goal(date=datetime(2025, 11, 8)) == pytest.approx(500)
        assert p.daily == 500

    def test_ordinary_old_plan_not_adjusted(self, sample_plan_dict):
        p = plan.Plan.from_dict(sample_plan_dict)

        assert p.schedule_adjustment == 0

    def test_saved_adjustment_round_trips(self):
        p = make_plan(schedule_adjustment=-1234.5)

        assert json.loads(p.to_json())['schedule_adjustment'] == -1234.5
        assert plan.Plan.from_json(p.to_json()).schedule_adjustment == -1234.5


@freeze_time("2026-11-07 10:00")  # day 6
class TestWritingDaysGuard:

    def test_cannot_shrink_below_locked_days(self, scripted_input):
        p = make_plan()
        p.lock_past_goals()
        scripted_input(["3", "6"])  # too few, then valid

        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            days = planea.get_writing_days("Days: ", p)

        assert days == 6
        assert "at least 5" in output.getvalue()
