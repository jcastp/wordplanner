"""Tests for Plan.preexisting_words (issues-program.org P14, decision 3).

`total` is the full project goal. Words written before the plan are stored in
`preexisting_words`; the schedule only covers `total - preexisting_words`.
"""

import contextlib
import io
import pytest
from datetime import datetime, timedelta
import plan
import planea
import progress_analytics


START = datetime(2025, 11, 20)
PRE_START_KEY = (START - timedelta(days=1)).strftime('%Y-%m-%d')


def schedule_sum(p):
    return sum(p.get_daily_goal(date=d) for d in p.plan_days())


@pytest.fixture
def novel_plan():
    """Goal 50,000 with 10,000 already written, 30 days -> 1,333.33/day."""
    p = plan.Plan(total=50000, time=30, start_date=START, preexisting_words=10000)
    p.calculate_daily()
    return p


def quiet(func, *args):
    with contextlib.redirect_stdout(io.StringIO()):
        return func(*args)


class TestPreExistingField:
    """The field and the word counts derived from it."""

    def test_default_is_zero(self):
        p = plan.Plan(total=10000, daily=1000, time=10)

        assert p.preexisting_words == 0
        assert p.words_to_schedule == 10000

    def test_negative_rejected(self):
        with pytest.raises(ValueError, match="Pre-existing word count cannot be negative"):
            plan.Plan(total=10000, preexisting_words=-1)

    def test_words_to_schedule(self, novel_plan):
        assert novel_plan.words_to_schedule == 40000

    def test_words_to_schedule_never_negative(self):
        p = plan.Plan(total=1000, preexisting_words=5000)

        assert p.words_to_schedule == 0

    def test_counts_toward_completion(self, novel_plan):
        novel_plan.record_progress(START, 2000)

        assert novel_plan.get_total_written() == 12000
        assert novel_plan.get_plan_written() == 2000
        assert novel_plan.get_remaining_words() == 38000
        assert novel_plan.get_completion_percentage() == pytest.approx(24.0)

    def test_not_stored_as_progress(self, novel_plan):
        assert novel_plan.progress == {}
        assert novel_plan.get_days_with_progress() == 0


class TestCalculatorUsesWordsToWrite:
    """calculate_time/daily/words schedule only the words still to write."""

    def test_calculate_time(self):
        p = plan.Plan(total=80000, daily=1000, preexisting_words=32000)

        p.calculate_time()

        assert p.time == 48
        assert p.total == 80000

    def test_calculate_daily(self):
        p = plan.Plan(total=50000, time=40, preexisting_words=10000)

        p.calculate_daily()

        assert p.daily == pytest.approx(1000)

    def test_calculate_words_adds_pre_existing(self):
        p = plan.Plan(daily=500, time=60, preexisting_words=5000)

        p.calculate_words()

        assert p.total == 35000


class TestScheduleCoversOnlyWordsToWrite:
    """The P14 symptoms from issues-program.org, with their old wrong values."""

    def test_flat_schedule(self, novel_plan):
        assert schedule_sum(novel_plan) == pytest.approx(40000)

    def test_pattern_schedule(self, novel_plan):
        # Was 50,000: patterns scaled to the full goal
        novel_plan.pattern = "rising"
        novel_plan.pattern_config = {'start_multiplier': 0.5, 'end_multiplier': 1.5}
        novel_plan.invalidate_daily_goals_cache()

        assert schedule_sum(novel_plan) == pytest.approx(40000)

    def test_keep_total_does_not_add_pre_existing_to_daily_work(self, novel_plan):
        # Was: daily 1,333 -> 1,788 after configuring weekends during creation
        novel_plan.weekend_mode = "different"
        novel_plan.weekend_daily = novel_plan.daily

        quiet(planea.recalculate_plan_with_choice, novel_plan, novel_plan.total, 'total')

        assert novel_plan.daily == pytest.approx(40000 / 30)
        assert novel_plan.total == 50000
        assert schedule_sum(novel_plan) == pytest.approx(40000)

    def test_keep_days_keeps_pre_existing_in_total(self, novel_plan):
        # Was: total dropped to 40,000 and completion showed 25% instead of 20%
        quiet(planea.recalculate_plan_with_choice, novel_plan, novel_plan.total, 'days')

        assert novel_plan.total == pytest.approx(50000)
        assert novel_plan.get_completion_percentage() == pytest.approx(20.0)

    def test_on_track_ignores_pre_existing(self):
        # Was: AHEAD by 10,000 as soon as the plan started
        p = plan.Plan(total=40000, time=30, start_date=START, preexisting_words=10000)
        p.calculate_daily()
        p.record_progress(START, 1000)

        on_track, info = p.is_on_track(as_of_date=START)

        assert info['status'] == 'on_track'
        assert info['expected_words'] == pytest.approx(1000)
        assert info['actual_words'] == 1000

    def test_moving_start_date_keeps_pre_existing(self, novel_plan):
        novel_plan.start_date = START + timedelta(days=14)

        assert novel_plan.get_total_written() == 10000
        assert novel_plan.progress == {}


class TestSerialization:
    """Saving, loading, and migrating old files."""

    def test_round_trip(self, novel_plan):
        loaded = plan.Plan.from_json(novel_plan.to_json())

        assert loaded.preexisting_words == 10000
        assert loaded.progress == {}

    def test_old_file_entry_moved_into_field(self, sample_plan_dict):
        sample_plan_dict['start_date'] = '2025-11-20T00:00:00'
        sample_plan_dict['progress'] = {PRE_START_KEY: 3000, '2025-11-20': 900}

        p = plan.Plan.from_dict(sample_plan_dict)

        assert p.preexisting_words == 3000
        assert p.progress == {'2025-11-20': 900}
        assert p.get_total_written() == 3900

    def test_old_file_with_time_of_day_start(self, sample_plan_dict):
        sample_plan_dict['start_date'] = '2025-11-20T14:30:00'
        sample_plan_dict['progress'] = {PRE_START_KEY: 3000}

        p = plan.Plan.from_dict(sample_plan_dict)

        assert p.preexisting_words == 3000
        assert p.progress == {}

    def test_old_file_without_entry(self, sample_plan_dict):
        p = plan.Plan.from_dict(sample_plan_dict)

        assert p.preexisting_words == 0
        assert p.progress == sample_plan_dict['progress']

    def test_new_file_is_not_migrated_again(self, sample_plan_dict):
        # Once the field exists, an entry on the day before the start is real progress
        sample_plan_dict['start_date'] = '2025-11-20T00:00:00'
        sample_plan_dict['progress'] = {PRE_START_KEY: 500}
        sample_plan_dict['preexisting_words'] = 3000

        p = plan.Plan.from_dict(sample_plan_dict)

        assert p.preexisting_words == 3000
        assert p.progress == {PRE_START_KEY: 500}


class TestRecalculationWithPreExistingWords:
    """recalculate_from_progress() counts pre-existing words as completed."""

    def test_recalculation_includes_pre_existing(self):
        p = plan.Plan(total=10000, daily=1000, time=10, start_date=START, preexisting_words=3000)
        p.record_progress(START, 1000)
        p.record_progress(START + timedelta(days=1), 900)

        result = p.recalculate_from_progress(as_of_date=START + timedelta(days=2))

        assert result['success'] is True
        assert result['words_completed'] == 4900
        assert result['words_remaining'] == 5100
        assert result['remaining_writing_days'] == 8
        assert result['new_daily'] == pytest.approx(5100 / 8)

    def test_recalculation_with_partial_progress(self):
        p = plan.Plan(total=20000, daily=1000, time=15, start_date=START, preexisting_words=5000)
        for offset, words in enumerate([700, 600, 700]):
            p.record_progress(START + timedelta(days=offset), words)

        result = p.recalculate_from_progress(as_of_date=START + timedelta(days=3))

        assert result['words_completed'] == 7000
        assert result['words_remaining'] == 13000
        assert result['remaining_writing_days'] == 12
        assert result['new_daily'] == pytest.approx(13000 / 12)


class TestAnalyticsIgnorePreExistingWords:
    """Pre-existing words are not a writing day (issues-program.org A1)."""

    def test_average_and_best_day(self, novel_plan):
        novel_plan.record_progress(START, 1000)
        novel_plan.record_progress(START + timedelta(days=1), 1500)

        stats = progress_analytics.calculate_statistics(novel_plan)

        assert stats['total_written'] == 12500
        assert stats['days_recorded'] == 2
        assert stats['average_per_day'] == pytest.approx(1250)
        assert stats['best_day'] == ('2025-11-21', 1500)

    def test_completion_eta_uses_logged_velocity(self, novel_plan):
        novel_plan.record_progress(START, 1000)

        eta = progress_analytics.calculate_completion_eta(novel_plan)

        # 39,000 remaining at 1,000/day
        assert (eta - datetime.now()).days in (38, 39)
