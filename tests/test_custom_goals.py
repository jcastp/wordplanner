"""Tests for custom day goals in the UI (issues-program.org P17).

- 0 is accepted ("make it a rest day"); goals are whole numbers up to MAX_DAILY_WORDS.
- Dates outside the plan, spare days and weekend rest days are refused
  (their goal would be ignored), as are past days (decision 2).
- Setting, removing or clearing goals asks the shared adjustment question
  (move the end date / keep the end date / change the total), with previews.
"""

import contextlib
import io
import pytest
from datetime import datetime, timedelta
from freezegun import freeze_time
import plan
import planea


MON = datetime(2026, 11, 2)
MOVE_END, KEEP_END, CHANGE_TOTAL = "1", "2", "3"


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


def edit_goals(p, answers, scripted_input):
    scripted_input(answers + ["0"])  # ... then "Done"
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        planea.edit_individual_day_goal(p)
    return out.getvalue()


@freeze_time("2026-10-01")
class TestSetGoal:

    def test_zero_makes_a_rest_day(self, ten_day_plan, scripted_input):
        # Used to be rejected by get_positive_number
        edit_goals(ten_day_plan, ["1", key(day(4)), "0", KEEP_END], scripted_input)

        assert ten_day_plan.get_daily_goal(date=day(4)) == 0
        assert ten_day_plan.end_date == day(10)
        assert ten_day_plan.daily == pytest.approx(10000 / 9)
        assert schedule_sum(ten_day_plan) == pytest.approx(10000)

    def test_move_end_date(self, ten_day_plan, scripted_input):
        edit_goals(ten_day_plan, ["1", key(day(4)), "3000", MOVE_END], scripted_input)

        # Days 1-3 + 3,000 + days 5-8 = 10,000: two days fewer
        assert ten_day_plan.end_date == day(8)
        assert ten_day_plan.daily == pytest.approx(1000)
        assert schedule_sum(ten_day_plan) == pytest.approx(10000)

    def test_change_total(self, ten_day_plan, scripted_input):
        edit_goals(ten_day_plan, ["1", key(day(4)), "3000", CHANGE_TOTAL], scripted_input)

        assert ten_day_plan.total == pytest.approx(12000)
        assert ten_day_plan.daily == pytest.approx(1000)

    def test_question_shows_previews(self, ten_day_plan, scripted_input):
        output = edit_goals(ten_day_plan, ["1", key(day(4)), "3000", KEEP_END], scripted_input)

        assert "This changes the day's goal. How should the rest of the plan adjust?" in output
        assert "-> ends 2026-11-09, 1,000 words/day, total 10,000 words" in output
        assert "-> ends 2026-11-11, 778 words/day, total 10,000 words" in output

    def test_above_maximum_refused(self, ten_day_plan, scripted_input):
        edit_goals(ten_day_plan, ["1", key(day(4)), "100001", "5000", KEEP_END], scripted_input)

        assert ten_day_plan.custom_daily_goals == {key(day(4)): 5000}

    def test_same_goal_asks_nothing(self, ten_day_plan, scripted_input):
        edit_goals(ten_day_plan, ["1", key(day(4)), "1000"], scripted_input)

        assert ten_day_plan.custom_daily_goals == {key(day(4)): 1000}


@freeze_time("2026-10-01")
class TestRefusedDates:

    @pytest.mark.parametrize("date, message", [
        (day(11), "is outside the plan (2026-11-02 to 2026-11-11)"),
        (MON - timedelta(days=1), "is outside the plan"),
    ])
    def test_outside_the_plan(self, ten_day_plan, scripted_input, date, message):
        output = edit_goals(ten_day_plan, ["1", key(date)], scripted_input)

        assert message in output
        assert ten_day_plan.custom_daily_goals == {}

    def test_spare_day(self, ten_day_plan, scripted_input):
        ten_day_plan.spare_days_dates.append(day(4))

        output = edit_goals(ten_day_plan, ["1", key(day(4))], scripted_input)

        assert "is a spare day" in output
        assert ten_day_plan.custom_daily_goals == {}

    def test_weekend_rest_day(self, ten_day_plan, scripted_input):
        ten_day_plan.weekend_mode = "spare"

        output = edit_goals(ten_day_plan, ["1", key(day(6))], scripted_input)

        assert "Saturdays are rest days in this plan" in output
        assert ten_day_plan.custom_daily_goals == {}

    def test_weekend_in_different_mode_allowed(self, ten_day_plan, scripted_input):
        ten_day_plan.weekend_mode = "different"
        ten_day_plan.weekend_daily = 500

        edit_goals(ten_day_plan, ["1", key(day(6)), "2000", KEEP_END], scripted_input)

        assert ten_day_plan.get_daily_goal(date=day(6)) == 2000


class TestRemoveAndClear:

    @freeze_time("2026-10-01")
    def test_remove_asks(self, ten_day_plan, scripted_input):
        ten_day_plan.set_custom_daily_goal(day(4), 3000)
        ten_day_plan.sync_daily()  # as the plan menu does: 7,000 over 9 days

        edit_goals(ten_day_plan, ["2", key(day(4)), CHANGE_TOTAL], scripted_input)

        # Day 4 is ordinary again at the same daily goal: 10 x 777.78,
        # rounded to whole words (P21)
        assert ten_day_plan.custom_daily_goals == {}
        assert ten_day_plan.total == 7778
        assert ten_day_plan.daily == pytest.approx(777.8)
        assert schedule_sum(ten_day_plan) == pytest.approx(7778)

    @freeze_time(day(6) + timedelta(hours=10))
    def test_clear_keeps_past_goals(self, ten_day_plan, scripted_input):
        ten_day_plan.custom_daily_goals[key(day(2))] = 1500
        ten_day_plan.set_custom_daily_goal(day(8), 3000)
        ten_day_plan.lock_past_goals()

        edit_goals(ten_day_plan, ["3", "y", KEEP_END], scripted_input)

        assert ten_day_plan.custom_daily_goals == {key(day(2)): 1500}
        assert schedule_sum(ten_day_plan) == pytest.approx(10000)
