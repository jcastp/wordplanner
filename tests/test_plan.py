"""Unit tests for Plan class calculations and methods."""

import pytest
from datetime import datetime, timedelta
import plan


class TestPlanCalculations:
    """Test basic plan calculations."""

    def test_calculate_daily(self):
        """Test calculating daily words from total and time."""
        p = plan.Plan(total=10000, time=10)
        p.calculate_daily()
        assert p.daily == 1000

    def test_calculate_time(self):
        """Test calculating time from total and daily."""
        p = plan.Plan(total=10000, daily=1000)
        p.calculate_time()
        assert p.time == 10

    def test_calculate_words(self):
        """Test calculating total words from daily and time."""
        p = plan.Plan(daily=1000, time=10)
        p.calculate_words()
        assert p.total == 10000

    def test_calculate_daily_fractional(self):
        """Test calculating daily with fractional result."""
        p = plan.Plan(total=10000, time=7)
        p.calculate_daily()
        assert abs(p.daily - 1428.57) < 0.01

    def test_calculate_time_fractional(self):
        """Test calculating time with fractional result."""
        p = plan.Plan(total=10000, daily=1500)
        p.calculate_time()
        assert abs(p.time - 6.67) < 0.01


class TestPlanSpareDays:
    """Test spare days functionality."""

    def test_spare_days_count(self, basic_plan):
        """Test spare_days property returns correct count."""
        basic_plan.spare_days_dates = [
            datetime(2025, 11, 1),
            datetime(2025, 11, 2),
            datetime(2025, 11, 3)
        ]
        assert basic_plan.spare_days == 3

    def test_is_spare_day(self, basic_plan):
        """Test is_spare_day identifies spare days correctly."""
        spare_date = datetime(2025, 11, 5)
        basic_plan.spare_days_dates = [spare_date]

        assert basic_plan.is_spare_day(spare_date) is True
        assert basic_plan.is_spare_day(datetime(2025, 11, 6)) is False

    def test_is_spare_day_date_only(self, basic_plan):
        """Test is_spare_day works with date-only comparison."""
        spare_date = datetime(2025, 11, 5, 14, 30)  # With time
        check_date = datetime(2025, 11, 5, 0, 0)  # Different time
        basic_plan.spare_days_dates = [spare_date]

        assert basic_plan.is_spare_day(check_date) is True


class TestPlanWeekends:
    """Test weekend functionality."""

    def test_is_weekend_saturday(self):
        """Test Saturday is identified as weekend."""
        p = plan.Plan()
        p.weekend_days = [5, 6]  # Sat, Sun
        saturday = datetime(2025, 11, 1)  # This is a Saturday
        assert p.is_weekend(saturday) is True

    def test_is_weekend_custom_days(self):
        """Test custom weekend days work correctly."""
        p = plan.Plan()
        p.weekend_days = [4, 5]  # Fri, Sat
        friday = datetime(2025, 10, 31)  # Friday
        sunday = datetime(2025, 11, 2)  # Sunday
        assert p.is_weekend(friday) is True
        assert p.is_weekend(sunday) is False

    def test_weekend_mode_different(self, plan_with_weekends):
        """Test weekend mode with different daily goal."""
        assert plan_with_weekends.weekend_mode == "different"
        assert plan_with_weekends.weekend_daily == 1500

    def test_weekend_mode_spare(self):
        """Test weekend mode as spare days."""
        p = plan.Plan(weekend_mode="spare")
        assert p.weekend_mode == "spare"


class TestPlanPatterns:
    """Test writing pattern functionality."""

    def test_flat_pattern(self, basic_plan):
        """Test flat pattern returns consistent goals."""
        basic_plan.pattern = "flat"
        basic_plan.time = 10
        goals = basic_plan.calculate_pattern_goals()

        assert len(goals) == 10
        assert all(abs(g - basic_plan.daily) < 0.01 for g in goals)

    def test_pattern_preserves_total(self, plan_with_pattern):
        """Test all patterns preserve total word count."""
        patterns = ["valley", "mountain", "rising", "declining", "random"]

        for pattern_name in patterns:
            plan_with_pattern.pattern = pattern_name
            goals = plan_with_pattern.calculate_pattern_goals()
            total_from_goals = sum(goals)

            assert abs(total_from_goals - plan_with_pattern.total) < 1, \
                f"Pattern {pattern_name} doesn't preserve total"

    def test_valley_pattern_shape(self):
        """Test valley pattern has correct shape."""
        p = plan.Plan(total=10000, daily=1000, time=10)
        p.pattern = "valley"
        p.pattern_config = {'peak_multiplier': 1.5, 'valley_multiplier': 0.7}
        goals = p.calculate_pattern_goals()

        # First goal should be higher
        # Middle goal should be lower
        # Last goal should be higher
        assert goals[0] > goals[4]
        assert goals[-1] > goals[4]

    def test_mountain_pattern_shape(self):
        """Test mountain pattern has correct shape."""
        p = plan.Plan(total=10000, daily=1000, time=10)
        p.pattern = "mountain"
        p.pattern_config = {'peak_multiplier': 1.5, 'valley_multiplier': 0.7}
        goals = p.calculate_pattern_goals()

        # First goal should be lower
        # Middle goal should be higher
        # Last goal should be lower
        assert goals[0] < goals[4]
        assert goals[-1] < goals[4]

    def test_rising_pattern_increases(self):
        """Test rising pattern increases over time."""
        p = plan.Plan(total=10000, daily=1000, time=10)
        p.pattern = "rising"
        p.pattern_config = {'start_multiplier': 0.5, 'end_multiplier': 1.5}
        goals = p.calculate_pattern_goals()

        # Goals should generally increase
        assert goals[0] < goals[-1]
        assert goals[2] < goals[7]

    def test_declining_pattern_decreases(self):
        """Test declining pattern decreases over time."""
        p = plan.Plan(total=10000, daily=1000, time=10)
        p.pattern = "declining"
        p.pattern_config = {'start_multiplier': 1.5, 'end_multiplier': 0.5}
        goals = p.calculate_pattern_goals()

        # Goals should generally decrease
        assert goals[0] > goals[-1]
        assert goals[2] > goals[7]


class TestCustomDailyGoals:
    """Test custom daily goals functionality."""

    def test_set_custom_daily_goal(self, basic_plan):
        """Test setting a custom daily goal."""
        basic_plan.start_date = datetime(2025, 11, 1)
        target_date = datetime(2025, 11, 5)

        basic_plan.set_custom_daily_goal(target_date, 2000)
        assert '2025-11-05' in basic_plan.custom_daily_goals
        assert basic_plan.custom_daily_goals['2025-11-05'] == 2000

    def test_remove_custom_daily_goal(self, plan_with_custom_goals):
        """Test removing a custom daily goal."""
        target_date = datetime(2025, 11, 6)  # Has custom goal of 500
        assert '2025-11-06' in plan_with_custom_goals.custom_daily_goals

        plan_with_custom_goals.remove_custom_daily_goal(target_date)
        assert '2025-11-06' not in plan_with_custom_goals.custom_daily_goals

    def test_get_daily_goal_custom_overrides(self, plan_with_custom_goals):
        """Test custom goal overrides pattern-based goal."""
        target_date = datetime(2025, 11, 7)  # Custom goal of 500 (start_date + 6 days)
        goal = plan_with_custom_goals.get_daily_goal(date=target_date)

        assert goal == 500

    def test_get_daily_goal_default(self, basic_plan):
        """Test get_daily_goal returns default when no custom goal."""
        basic_plan.start_date = datetime(2025, 11, 1)
        target_date = datetime(2025, 11, 5)
        goal = basic_plan.get_daily_goal(date=target_date)

        assert goal == basic_plan.daily


class TestPlanProgress:
    """Test progress tracking functionality."""

    def test_record_progress(self, basic_plan):
        """Test recording progress for a date."""
        basic_plan.start_date = datetime(2025, 11, 1)
        date = datetime(2025, 11, 1)

        basic_plan.record_progress(date, 1200)
        assert basic_plan.get_progress_for_date(date) == 1200

    def test_get_total_written(self, plan_with_progress):
        """Test calculating total words written."""
        total = plan_with_progress.get_total_written()
        assert total == 1200 + 950 + 1100 + 800 + 1300 + 900 + 1000

    def test_get_remaining_words(self, plan_with_progress):
        """Test calculating remaining words."""
        remaining = plan_with_progress.get_remaining_words()
        total_written = plan_with_progress.get_total_written()
        expected = plan_with_progress.total - total_written
        assert remaining == expected

    def test_get_completion_percentage(self, plan_with_progress):
        """Test calculating completion percentage."""
        percentage = plan_with_progress.get_completion_percentage()
        total_written = plan_with_progress.get_total_written()
        expected = (total_written / plan_with_progress.total) * 100
        assert abs(percentage - expected) < 0.01

    def test_get_days_with_progress(self, plan_with_progress):
        """Test counting days with progress."""
        days = plan_with_progress.get_days_with_progress()
        assert days == 7


class TestPlanRecalculation:
    """Test plan recalculation functionality."""

    def test_recalculate_total_from_daily_goals_flat(self):
        """Test recalculation with flat pattern."""
        p = plan.Plan(daily=1000, total=10000, time=10)
        p.start_date = datetime(2025, 11, 1)
        p.pattern = "flat"

        new_total = p.recalculate_total_from_daily_goals()
        assert abs(new_total - 10000) < 0.01

    def test_recalculate_with_custom_goal(self):
        """Test recalculation after setting custom goal."""
        p = plan.Plan(daily=1000, total=10000, time=10)
        p.start_date = datetime(2025, 11, 1)
        p.pattern = "flat"

        # Set custom goal for one day
        p.set_custom_daily_goal(datetime(2025, 11, 5), 2000)

        new_total = p.recalculate_total_from_daily_goals()
        # 9 days * 1000 + 1 day * 2000 = 11000
        assert abs(new_total - 11000) < 0.01

    def test_recalculate_with_weekend_different(self):
        """Test recalculation with different weekend goal."""
        p = plan.Plan(daily=1000, total=14000, time=14)
        p.start_date = datetime(2025, 11, 3)  # Monday
        p.pattern = "flat"
        p.weekend_mode = "different"
        p.weekend_daily = 500
        p.weekend_days = [5, 6]

        new_total = p.recalculate_total_from_daily_goals()
        # 10 weekdays * 1000 + 4 weekends * 500 = 12000
        assert abs(new_total - 12000) < 0.01

    def test_recalculate_with_spare_days(self):
        """Test recalculation respects spare days."""
        p = plan.Plan(daily=1000, total=10000, time=10)
        p.start_date = datetime(2025, 11, 1)
        p.pattern = "flat"
        p.spare_days_dates = [
            datetime(2025, 11, 5),
            datetime(2025, 11, 6)
        ]

        new_total = p.recalculate_total_from_daily_goals()
        # 10 days * 1000, spare days are 0 in the iteration
        assert abs(new_total - 10000) < 0.01


class TestPlanValidation:
    """Test plan validation and constraints."""

    def test_plan_with_zero_values(self):
        """Test plan handles zero values."""
        p = plan.Plan(daily=0, total=0, time=0)
        assert p.daily == 0
        assert p.total == 0
        assert p.time == 0

    def test_plan_with_large_values(self):
        """Test plan handles large values."""
        p = plan.Plan(total=1000000, daily=10000, time=100)
        assert p.total == 1000000
        assert p.daily == 10000
        assert p.time == 100


class TestPlanInitialization:
    """Test Plan class initialization."""

    def test_basic_initialization(self):
        """Test basic plan initialization."""
        p = plan.Plan()
        assert p.daily == 0
        assert p.total == 0
        assert p.time == 0

    def test_initialization_with_values(self):
        """Test plan initialization with values."""
        p = plan.Plan(daily=1000, total=10000, time=10, name="Test Plan")
        assert p.daily == 1000
        assert p.total == 10000
        assert p.time == 10
        assert p.name == "Test Plan"

    def test_initialization_defaults(self):
        """Test plan initialization sets correct defaults."""
        p = plan.Plan()
        assert p.pattern == "flat"
        assert p.pattern_config == {}
        assert p.progress == {}
        assert p.weekend_mode == "same"
        assert p.weekend_days == [5, 6]
        assert p.custom_daily_goals == {}
        assert p.spare_days_dates == []
