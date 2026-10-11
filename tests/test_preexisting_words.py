"""Tests for recording pre-existing words and how they count as progress."""

import pytest
from datetime import datetime, timedelta
import plan
import planea


START = datetime(2025, 11, 20)
PRE_START_KEY = (START - timedelta(days=1)).strftime('%Y-%m-%d')


@pytest.fixture
def ten_k_plan():
    """10,000 words / 10 days starting 2025-11-20."""
    return plan.Plan(name="Test Pre-existing Words", total=10000, daily=1000, time=10, start_date=START)


class TestRecordPreExistingWords:
    """planea.record_pre_existing_words()"""

    def test_recorded_on_day_before_start(self, ten_k_plan):
        assert planea.record_pre_existing_words(ten_k_plan, 3000) is True

        assert ten_k_plan.progress == {PRE_START_KEY: 3000}

    def test_counts_toward_completion(self, ten_k_plan):
        planea.record_pre_existing_words(ten_k_plan, 3000)

        assert ten_k_plan.get_total_written() == 3000
        assert ten_k_plan.get_remaining_words() == 7000
        assert ten_k_plan.get_completion_percentage() == pytest.approx(30.0)

    def test_does_not_create_a_goal_or_touch_plan_days(self, ten_k_plan):
        planea.record_pre_existing_words(ten_k_plan, 3000)

        assert ten_k_plan.get_progress_for_date(START) is None
        assert ten_k_plan.total == 10000

    def test_zero_words_not_recorded(self, ten_k_plan):
        assert planea.record_pre_existing_words(ten_k_plan, 0) is False
        assert ten_k_plan.progress == {}

    def test_requires_start_date(self):
        p = plan.Plan(total=10000, daily=1000, time=10)

        assert planea.record_pre_existing_words(p, 3000) is False
        assert p.progress == {}


class TestPreExistingWordsWithRecalculation:
    """recalculate_from_progress() counts pre-existing words as completed."""

    def test_recalculation_includes_pre_existing(self, ten_k_plan):
        planea.record_pre_existing_words(ten_k_plan, 3000)
        ten_k_plan.record_progress(START, 1000)
        ten_k_plan.record_progress(START + timedelta(days=1), 900)

        result = ten_k_plan.recalculate_from_progress(as_of_date=START + timedelta(days=2))

        assert result['success'] is True
        assert result['words_completed'] == 4900
        assert result['words_remaining'] == 5100
        assert result['remaining_writing_days'] == 8
        assert result['new_daily'] == pytest.approx(5100 / 8)

    def test_recalculation_with_pre_existing_and_partial_progress(self):
        p = plan.Plan(total=20000, daily=1000, time=15, start_date=START)
        planea.record_pre_existing_words(p, 5000)
        for offset, words in enumerate([700, 600, 700]):
            p.record_progress(START + timedelta(days=offset), words)

        result = p.recalculate_from_progress(as_of_date=START + timedelta(days=3))

        assert result['words_completed'] == 7000
        assert result['words_remaining'] == 13000
        assert result['remaining_writing_days'] == 12
        assert result['new_daily'] == pytest.approx(13000 / 12)
