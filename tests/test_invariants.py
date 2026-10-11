"""Property-style invariant tests over random modification sequences (issues-program.org T3).

Each seed builds a random plan and lives through a few weeks: every simulated
day it may log words, locks past days (as the plan menu does) and applies a
random modification through the same code the menus use. After every step:

- past (locked) goals never change and stay inside the plan (decision 2);
- the schedule adds up to the words it has to cover; right after a
  recalculation, the open days add up to the words actually left;
- the plan has exactly `time` writing days, ends on a writing day and never
  drops locked days;
- no goal is negative;
- saving and loading keeps every goal;
- each adjustment option keeps what it promises (decision 1).

The seed is in the test id, so a failure can be replayed.
"""

import random
import pytest
from datetime import datetime, timedelta
from freezegun import freeze_time
import plan
import copy
import ui_modify


START = datetime(2026, 11, 2)
PATTERNS = {
    "flat": {},
    "rising": {'start_multiplier': 0.5, 'end_multiplier': 1.5},
    "declining": {'start_multiplier': 1.5, 'end_multiplier': 0.5},
    "valley": {'peak_multiplier': 1.5, 'valley_multiplier': 0.7},
    "mountain": {'peak_multiplier': 1.5, 'valley_multiplier': 0.7},
    "random": {'min_multiplier': 0.5, 'max_multiplier': 1.5, 'seed': 7},
}
SEEDS = range(60)
DAYS = 25


def key(d):
    return d.strftime('%Y-%m-%d')


def schedule_goals(p):
    return p.build_schedule()['goals']


class Simulation:
    """One random plan living through DAYS simulated days."""

    def __init__(self, seed, clock):
        self.rng = random.Random(seed)
        self.clock = clock
        self.today = START - timedelta(days=self.rng.randint(0, 3))
        self.locked_snapshot = {}
        self.plan = self.random_plan()

    # -- setup -----------------------------------------------------------

    def random_plan(self):
        rng = self.rng
        pattern = rng.choice(list(PATTERNS))
        p = plan.Plan(
            name="Sim", total=rng.choice([5000, 12000, 30000]), time=rng.randint(8, 30),
            start_date=START, pattern=pattern, pattern_config=dict(PATTERNS[pattern]),
            weekend_mode=rng.choice(["same", "different", "spare"]),
            weekend_daily=rng.choice([0, 300, 1500]),
            preexisting_words=rng.choice([0, 0, 1000]))
        p.calculate_daily()
        for _ in range(rng.randint(0, 2)):
            p.spare_days_dates.append(START + timedelta(days=rng.randint(0, 20)))
        for _ in range(rng.randint(0, 2)):
            p.set_custom_daily_goal(START + timedelta(days=rng.randint(0, 20)), rng.choice([0, 400, 2500]))
        p.sync_daily()
        return p

    # -- helpers -----------------------------------------------------------

    def future_plan_day(self):
        """A plan day from today on, or None."""
        days = [d for d in self.plan.plan_days() if d >= self.today]
        return self.rng.choice(days) if days else None

    def adjust(self, before):
        """Pick one of the decision 1 options and check its promise."""
        p = self.plan
        adjustment = self.rng.choice(plan.Plan.ADJUSTMENTS)
        if adjustment == 'move_end' and before.daily <= 0:
            adjustment = 'keep_end'
        old_end = before.end_date
        p.apply_adjustment(before, adjustment)

        if p.build_schedule()['adjustable_weight'] == 0:
            return  # the total was refitted to the fixed days
        if adjustment in ('move_end', 'keep_end'):
            assert p.total == before.total, adjustment
        if adjustment == 'move_end':
            # Rounding the days up can lower the daily goal a little, never raise it
            assert p.daily <= before.daily + 1e-6
        else:
            assert p.end_date <= old_end, adjustment
        if adjustment == 'change_total':
            assert p.daily == pytest.approx(before.daily, rel=1e-3, abs=1)

    # -- modifications -----------------------------------------------------

    def modify(self):
        p = self.plan
        rng = self.rng
        before = copy.deepcopy(p)
        action = rng.choice([
            'spare_add', 'spare_remove', 'custom_set', 'custom_remove', 'weekend',
            'pattern', 'total', 'daily', 'time', 'recalculate', 'adjust_time',
            'move_start', 'nothing',
        ])

        if action == 'spare_add':
            d = self.future_plan_day()
            if d and not p.is_spare_day(d):
                p.spare_days_dates.append(d)
                self.adjust(before)
        elif action == 'spare_remove':
            future = [d for d in p.spare_days_dates if d >= self.today]
            if future:
                p.spare_days_dates.remove(rng.choice(future))
                self.adjust(before)
        elif action == 'custom_set':
            d = self.future_plan_day()
            if d and ui_modify.custom_goal_date_problem(p, d) is None:
                p.set_custom_daily_goal(d, rng.choice([0, 250, 1200, 4000]))
                self.adjust(before)
        elif action == 'custom_remove':
            future = [k for k in p.custom_daily_goals if k >= key(self.today)]
            if future:
                del p.custom_daily_goals[rng.choice(future)]
                self.adjust(before)
        elif action == 'weekend':
            p.weekend_mode = rng.choice(["same", "different", "spare"])
            p.weekend_daily = rng.choice([0, 500, 2000])
            self.adjust(before)
        elif action == 'pattern':
            p.pattern = rng.choice(list(PATTERNS))
            p.pattern_config = dict(PATTERNS[p.pattern])
        elif action == 'total':
            # Modify menu: new total, keep the days (recalculate daily)
            p.total = rng.choice([4000, 15000, 40000])
            if p.time > 0:
                p.calculate_daily()
        elif action == 'daily':
            # Modify menu: new daily, keep the total (recalculate days)
            p.daily = rng.choice([300, 800, 2000])
            p.calculate_time()
        elif action == 'time':
            p.time = max(p.min_writing_days() + 1, rng.randint(5, 40))
            p.calculate_daily()
        elif action == 'recalculate':
            result = p.recalculate_from_progress()
            if result.get('success'):
                self.check_open_days_cover_words_left(result['as_of_date'])
        elif action == 'adjust_time':
            p.adjust_time_from_progress()
        elif action == 'move_start' and not p.locked_goals and self.today < p.start_date:
            p.move_start_date(self.today + timedelta(days=rng.randint(0, 5)),
                              shift_dated_days=rng.random() < 0.5)
        return action

    # -- invariants ----------------------------------------------------------

    def check_open_days_cover_words_left(self, as_of_date):
        p = self.plan
        goals = schedule_goals(p)
        if p.build_schedule()['level'] <= 0:
            return
        future = sum(g for k, g in goals.items() if k >= key(as_of_date))
        # A locked today is credited with at least its goal (decision 9)
        today_key = key(self.today)
        extra_today = 0
        if as_of_date > self.today and today_key in p.locked_goals:
            extra_today = max(0, p.locked_goals[today_key] - p.progress.get(today_key, 0))
        left = p.total - p.get_total_written() - extra_today
        assert future == pytest.approx(max(0, left), abs=0.5)

    def check(self, step):
        p = self.plan
        goals = schedule_goals(p)

        # Past goals never change, and past days with a goal never leave the plan.
        # (A past rest day with goal 0 may fall outside a plan that its earlier
        # days already cover: no expected words change.)
        for date_key, goal in self.locked_snapshot.items():
            if date_key in goals:
                assert goals[date_key] == pytest.approx(goal), f"{step}: past goal of {date_key} changed"
            else:
                assert goal == 0, f"{step}: locked day {date_key} left the plan"

        # Plan length: exactly `time` writing days, ending on a writing day
        if p.time > 0:
            writing = [d for d in p.plan_days() if not p.is_spare_day(d)]
            assert len(writing) == p.time, step
            assert not p.is_spare_day(p.end_date), step
            assert p.time >= p.min_writing_days(), step

        # No negative goals
        assert all(g >= 0 for g in goals.values()), step

        # The schedule covers the words it has to (unless fixed days exceed them)
        schedule = p.build_schedule()
        if schedule['level'] > 0:
            assert sum(goals.values()) == pytest.approx(
                p.words_to_schedule + p.schedule_adjustment, abs=0.5), step

        # Saving and loading keeps every goal
        loaded = plan.Plan.from_json(p.to_json())
        assert schedule_goals(loaded) == pytest.approx(goals), step

    # -- the run -----------------------------------------------------------

    def run(self):
        for step in range(DAYS):
            self.clock.move_to(self.today + timedelta(hours=10))
            p = self.plan

            # The plan menu locks past days on every visit
            p.lock_past_goals()
            for date_key in p.locked_goals:
                self.locked_snapshot.setdefault(date_key, schedule_goals(p)[date_key]
                                                if date_key in schedule_goals(p) else None)
            self.locked_snapshot = {k: v for k, v in self.locked_snapshot.items() if v is not None}
            p.sync_daily()
            self.check(f"day {step} after locking")

            if self.rng.random() < 0.7:
                p.record_progress(self.today, self.rng.choice([0, 300, 900, 1500, 2500]))

            for _ in range(self.rng.randint(0, 2)):
                action = self.modify()
                self.check(f"day {step} after {action}")

            self.today += timedelta(days=1)


@pytest.mark.parametrize("seed", SEEDS)
def test_random_modification_sequences(seed):
    with freeze_time(START) as clock:
        Simulation(seed, clock).run()
