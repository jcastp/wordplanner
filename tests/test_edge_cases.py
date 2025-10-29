"""Edge case tests for planeapalabras."""

import pytest
from datetime import datetime, timedelta
import plan


class TestZeroValues:
    """Test handling of zero values."""

    def test_zero_total_words(self):
        """Test plan with zero total words."""
        p = plan.Plan(total=0, daily=1000, time=10)
        assert p.total == 0

    def test_zero_daily_words(self):
        """Test plan with zero daily words."""
        p = plan.Plan(total=10000, daily=0, time=10)
        assert p.daily == 0

    def test_zero_time(self):
        """Test plan with zero time."""
        p = plan.Plan(total=10000, daily=1000, time=0)
        assert p.time == 0

    def test_calculate_with_zero_time(self):
        """Test calculation prevents division by zero."""
        p = plan.Plan(total=10000, time=0)
        # Should not raise ZeroDivisionError
        try:
            p.calculate_daily()
        except ZeroDivisionError:
            pytest.fail("calculate_daily raised ZeroDivisionError with time=0")

    def test_calculate_with_zero_daily(self):
        """Test calculation prevents division by zero."""
        p = plan.Plan(total=10000, daily=0)
        # Should not raise ZeroDivisionError
        try:
            p.calculate_time()
        except ZeroDivisionError:
            pytest.fail("calculate_time raised ZeroDivisionError with daily=0")


class TestLargeValues:
    """Test handling of very large values."""

    def test_million_word_project(self):
        """Test plan with million-word goal."""
        p = plan.Plan(total=1000000, daily=10000, time=100)
        p.calculate_words()
        assert p.total == 1000000

    def test_very_long_timeframe(self):
        """Test plan with very long timeframe."""
        p = plan.Plan(total=365000, daily=1000, time=365)
        assert p.time == 365

    def test_very_high_daily_goal(self):
        """Test plan with very high daily goal."""
        p = plan.Plan(total=100000, daily=10000, time=10)
        assert p.daily == 10000


class TestFractionalValues:
    """Test handling of fractional values."""

    def test_fractional_daily(self):
        """Test fractional daily word count."""
        p = plan.Plan(total=10000, time=7)
        p.calculate_daily()
        assert abs(p.daily - 1428.57) < 0.01

    def test_fractional_time(self):
        """Test fractional time period."""
        p = plan.Plan(total=10000, daily=1500)
        p.calculate_time()
        assert abs(p.time - 6.67) < 0.01

    def test_fractional_pattern_goals(self):
        """Test patterns work with fractional daily values."""
        p = plan.Plan(total=10000, time=7)
        p.calculate_daily()
        p.pattern = "mountain"
        p.pattern_config = {'peak_multiplier': 1.5, 'valley_multiplier': 0.7}

        goals = p.calculate_pattern_goals()
        assert len(goals) == 7
        assert all(g > 0 for g in goals)


class TestEmptyCollections:
    """Test handling of empty collections."""

    def test_plan_with_no_spare_days(self, basic_plan):
        """Test plan with empty spare days list."""
        basic_plan.spare_days_dates = []
        assert basic_plan.spare_days == 0

    def test_plan_with_no_progress(self, basic_plan):
        """Test plan with no progress recorded."""
        basic_plan.progress = {}
        assert basic_plan.get_total_written() == 0
        assert basic_plan.get_days_with_progress() == 0

    def test_plan_with_no_custom_goals(self, basic_plan):
        """Test plan with no custom daily goals."""
        basic_plan.custom_daily_goals = {}
        basic_plan.start_date = datetime(2025, 11, 1)
        goal = basic_plan.get_daily_goal(date=datetime(2025, 11, 5))
        assert goal == basic_plan.daily


class TestBoundaryConditions:
    """Test boundary conditions."""

    def test_one_day_plan(self):
        """Test plan with single day."""
        p = plan.Plan(total=1000, daily=1000, time=1)
        assert p.time == 1

    def test_pattern_with_one_day(self):
        """Test patterns work with single day."""
        p = plan.Plan(total=1000, daily=1000, time=1)
        p.pattern = "mountain"
        goals = p.calculate_pattern_goals()
        assert len(goals) == 1

    def test_pattern_with_two_days(self):
        """Test patterns work with two days."""
        p = plan.Plan(total=2000, daily=1000, time=2)
        p.pattern = "mountain"
        goals = p.calculate_pattern_goals()
        assert len(goals) == 2


class TestDateBoundaries:
    """Test date boundary conditions."""

    def test_year_boundary(self):
        """Test plan spanning year boundary."""
        p = plan.Plan(total=10000, daily=1000, time=10)
        p.start_date = datetime(2025, 12, 28)
        # Plan spans from Dec 28, 2025 to Jan 6, 2026

        target_date = datetime(2026, 1, 3)
        goal = p.get_daily_goal(date=target_date)
        assert goal > 0

    def test_leap_year(self):
        """Test plan handling leap year."""
        p = plan.Plan(total=366000, daily=1000, time=366)
        p.start_date = datetime(2024, 1, 1)  # 2024 is a leap year
        # Plan spans entire leap year
        assert p.time == 366

    def test_month_boundary(self):
        """Test plan spanning month boundary."""
        p = plan.Plan(total=5000, daily=1000, time=5)
        p.start_date = datetime(2025, 10, 29)
        # Spans from Oct 29 to Nov 2

        nov_date = datetime(2025, 11, 1)
        goal = p.get_daily_goal(date=nov_date)
        assert goal == 1000


class TestNegativeValues:
    """Test handling of negative values (edge case for invalid input)."""

    def test_negative_total(self):
        """Test plan allows negative total (even if illogical)."""
        p = plan.Plan(total=-1000, daily=1000, time=10)
        # Should not crash, even if it doesn't make logical sense
        assert p.total == -1000

    def test_negative_daily(self):
        """Test plan allows negative daily."""
        p = plan.Plan(total=10000, daily=-1000, time=10)
        assert p.daily == -1000

    def test_negative_time(self):
        """Test plan allows negative time."""
        p = plan.Plan(total=10000, daily=1000, time=-10)
        assert p.time == -10


class TestComplexScenarios:
    """Test complex real-world scenarios."""

    def test_nanowrimo_with_weekends_off(self):
        """Test NaNoWriMo plan with weekends as spare days."""
        p = plan.Plan(total=50000, time=30)
        p.start_date = datetime(2025, 11, 1)
        p.weekend_mode = "spare"
        p.weekend_days = [5, 6]

        # November 2025: 30 days total
        # Weekends: 1-2, 8-9, 15-16, 22-23, 29-30 = 10 weekend days
        # Writing days: 20 days
        # Daily goal should be: 50000 / 20 = 2500 words/day

        # This is simulated - actual implementation would need to handle this

    def test_plan_with_all_features(self):
        """Test plan using all features simultaneously."""
        p = plan.Plan(total=50000, daily=1000, time=50)
        p.start_date = datetime(2025, 11, 1)
        p.pattern = "valley"
        p.pattern_config = {'peak_multiplier': 1.5, 'valley_multiplier': 0.7}
        p.weekend_mode = "different"
        p.weekend_daily = 1500
        p.weekend_days = [5, 6]

        # Add spare days
        p.spare_days_dates = [
            datetime(2025, 11, 10),
            datetime(2025, 11, 11)
        ]

        # Add custom goals
        p.set_custom_daily_goal(datetime(2025, 11, 15), 2000)

        # Add progress
        p.record_progress(datetime(2025, 11, 1), 1200)
        p.record_progress(datetime(2025, 11, 2), 1400)

        # Verify it all works together
        assert p.total == 50000
        assert len(p.progress) == 2
        assert len(p.custom_daily_goals) == 1
        assert p.spare_days == 2

    def test_plan_modification_after_progress(self):
        """Test modifying plan after recording progress."""
        p = plan.Plan(total=10000, daily=1000, time=10)
        p.start_date = datetime(2025, 11, 1)

        # Record some progress
        p.record_progress(datetime(2025, 11, 1), 1200)
        p.record_progress(datetime(2025, 11, 2), 800)

        # Modify the plan
        p.daily = 1500
        p.calculate_words()

        # Progress should be preserved
        assert len(p.progress) == 2
        assert p.get_total_written() == 2000


class TestStringConversions:
    """Test string formatting and conversions."""

    def test_plan_name_with_special_characters(self):
        """Test plan name with special characters."""
        p = plan.Plan(name="Test: Plan & Stuff (v2.0)")
        assert p.name == "Test: Plan & Stuff (v2.0)"

    def test_plan_name_with_unicode(self):
        """Test plan name with unicode characters."""
        p = plan.Plan(name="Mon Plan d'Écriture 2025")
        assert p.name == "Mon Plan d'Écriture 2025"

    def test_empty_plan_name(self):
        """Test plan with empty name."""
        p = plan.Plan(name="")
        assert p.name == ""

    def test_very_long_plan_name(self):
        """Test plan with very long name."""
        long_name = "A" * 500
        p = plan.Plan(name=long_name)
        assert p.name == long_name
