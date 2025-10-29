"""Integration tests for plan storage (save/load functionality)."""

import pytest
from datetime import datetime, timedelta
from pathlib import Path
import json
import plan
import plan_storage


class TestPlanSerialization:
    """Test plan serialization to/from dictionary."""

    def test_plan_to_dict(self, complete_plan):
        """Test converting plan to dictionary."""
        plan_dict = plan_storage.plan_to_dict(complete_plan)

        assert plan_dict['total'] == complete_plan.total
        assert plan_dict['daily'] == complete_plan.daily
        assert plan_dict['time'] == complete_plan.time
        assert plan_dict['name'] == complete_plan.name
        assert plan_dict['pattern'] == complete_plan.pattern
        assert plan_dict['weekend_mode'] == complete_plan.weekend_mode

    def test_dict_to_plan(self, sample_plan_dict):
        """Test converting dictionary to plan."""
        p = plan_storage.dict_to_plan(sample_plan_dict)

        assert p.total == sample_plan_dict['total']
        assert p.daily == sample_plan_dict['daily']
        assert p.time == sample_plan_dict['time']
        assert p.name == sample_plan_dict['name']

    def test_round_trip_serialization(self, complete_plan):
        """Test plan survives round-trip to dict and back."""
        plan_dict = plan_storage.plan_to_dict(complete_plan)
        restored_plan = plan_storage.dict_to_plan(plan_dict)

        assert restored_plan.total == complete_plan.total
        assert restored_plan.daily == complete_plan.daily
        assert restored_plan.time == complete_plan.time
        assert restored_plan.name == complete_plan.name
        assert restored_plan.pattern == complete_plan.pattern
        assert restored_plan.weekend_mode == complete_plan.weekend_mode


class TestPlanSaveLoad:
    """Test saving and loading plans to/from files."""

    def test_save_plan(self, basic_plan, temp_plan_directory):
        """Test saving a plan to file."""
        basic_plan.name = "Test Plan"

        # Temporarily override the save directory
        original_dir = plan_storage.get_plans_directory()
        plan_storage.config.SAVE_DIRECTORY = str(temp_plan_directory.parent)

        try:
            filepath = plan_storage.save_plan(basic_plan)
            assert filepath.exists()
            assert "Test_Plan" in filepath.name
        finally:
            plan_storage.config.SAVE_DIRECTORY = original_dir

    def test_load_plan(self, basic_plan, temp_plan_directory):
        """Test loading a plan from file."""
        basic_plan.name = "Test Plan"

        # Temporarily override the save directory
        original_dir = plan_storage.get_plans_directory()
        plan_storage.config.SAVE_DIRECTORY = str(temp_plan_directory.parent)

        try:
            # Save the plan
            filepath = plan_storage.save_plan(basic_plan)

            # Load it back
            loaded_plan = plan_storage.load_plan(filepath)

            assert loaded_plan.name == basic_plan.name
            assert loaded_plan.total == basic_plan.total
            assert loaded_plan.daily == basic_plan.daily
            assert loaded_plan.time == basic_plan.time
        finally:
            plan_storage.config.SAVE_DIRECTORY = original_dir

    def test_save_plan_with_progress(self, plan_with_progress, temp_plan_directory):
        """Test saving and loading a plan with progress."""
        plan_with_progress.name = "Progress Plan"

        original_dir = plan_storage.get_plans_directory()
        plan_storage.config.SAVE_DIRECTORY = str(temp_plan_directory.parent)

        try:
            filepath = plan_storage.save_plan(plan_with_progress)
            loaded_plan = plan_storage.load_plan(filepath)

            assert loaded_plan.progress == plan_with_progress.progress
            assert len(loaded_plan.progress) > 0
        finally:
            plan_storage.config.SAVE_DIRECTORY = original_dir

    def test_save_plan_with_custom_goals(self, plan_with_custom_goals, temp_plan_directory):
        """Test saving and loading a plan with custom daily goals."""
        plan_with_custom_goals.name = "Custom Goals Plan"

        original_dir = plan_storage.get_plans_directory()
        plan_storage.config.SAVE_DIRECTORY = str(temp_plan_directory.parent)

        try:
            filepath = plan_storage.save_plan(plan_with_custom_goals)
            loaded_plan = plan_storage.load_plan(filepath)

            assert loaded_plan.custom_daily_goals == plan_with_custom_goals.custom_daily_goals
            assert len(loaded_plan.custom_daily_goals) == 3
        finally:
            plan_storage.config.SAVE_DIRECTORY = original_dir

    def test_list_saved_plans(self, temp_plan_directory):
        """Test listing saved plans."""
        # Create test plan files
        plan1 = plan.Plan(name="Plan 1", total=10000, daily=1000, time=10)
        plan2 = plan.Plan(name="Plan 2", total=20000, daily=2000, time=10)

        original_dir = plan_storage.get_plans_directory()
        plan_storage.config.SAVE_DIRECTORY = str(temp_plan_directory.parent)

        try:
            plan_storage.save_plan(plan1)
            plan_storage.save_plan(plan2)

            plans = plan_storage.list_saved_plans()
            assert len(plans) == 2
            assert any(p['name'] == 'Plan 1' for p in plans)
            assert any(p['name'] == 'Plan 2' for p in plans)
        finally:
            plan_storage.config.SAVE_DIRECTORY = original_dir


class TestBackwardCompatibility:
    """Test backward compatibility with old plan formats."""

    def test_load_plan_without_weekends(self, temp_plan_directory):
        """Test loading a plan saved without weekend fields."""
        # Create an old-format plan dictionary
        old_format_dict = {
            'name': 'Old Plan',
            'total': 10000,
            'daily': 1000,
            'time': 10,
            'words': 10000,
            'spare_days_dates': [],
            'start_date': '2025-11-01T00:00:00',
            'created_date': '2025-10-28T12:00:00',
            'pattern': 'flat',
            'pattern_config': {},
            'progress': {},
            # Note: Missing weekend_mode, weekend_daily, weekend_days, custom_daily_goals
        }

        # Save it manually
        filepath = temp_plan_directory / "old_plan.json"
        with open(filepath, 'w') as f:
            json.dump(old_format_dict, f)

        # Load it
        loaded_plan = plan_storage.load_plan(filepath)

        # Should load with defaults
        assert loaded_plan.name == 'Old Plan'
        assert loaded_plan.weekend_mode == 'same'  # Default
        assert loaded_plan.weekend_days == [5, 6]  # Default
        assert loaded_plan.custom_daily_goals == {}  # Default

    def test_load_plan_with_old_spare_days_format(self, temp_plan_directory):
        """Test loading a plan with old spare days format (integers)."""
        old_format_dict = {
            'name': 'Old Spare Days',
            'total': 10000,
            'daily': 1000,
            'time': 10,
            'words': 10000,
            'spare_days_dates': [3, 5, 7],  # Old format: day numbers
            'start_date': '2025-11-01T00:00:00',
            'created_date': '2025-10-28T12:00:00',
            'pattern': 'flat',
            'pattern_config': {},
            'progress': {},
        }

        filepath = temp_plan_directory / "old_spare_days.json"
        with open(filepath, 'w') as f:
            json.dump(old_format_dict, f)

        # Load it (should handle gracefully)
        loaded_plan = plan_storage.load_plan(filepath)
        assert loaded_plan.name == 'Old Spare Days'


class TestFileOperations:
    """Test file system operations."""

    def test_get_plans_directory_creates_if_not_exists(self, temp_plan_directory):
        """Test ensure_plans_directory creates directory if it doesn't exist."""
        original_dir = plan_storage.get_plans_directory()
        test_dir = temp_plan_directory / "new_plans_dir"

        plan_storage.config.SAVE_DIRECTORY = str(test_dir.parent)

        try:
            plan_storage.ensure_plans_directory()
            plans_dir = plan_storage.get_plans_directory()
            assert Path(plans_dir).exists()
        finally:
            plan_storage.config.SAVE_DIRECTORY = original_dir

    def test_save_plan_creates_unique_filenames(self, basic_plan, temp_plan_directory):
        """Test that saving plans creates unique filenames."""
        basic_plan.name = "Same Name"

        original_dir = plan_storage.get_plans_directory()
        plan_storage.config.SAVE_DIRECTORY = str(temp_plan_directory.parent)

        try:
            filepath1 = plan_storage.save_plan(basic_plan, overwrite_source=False)

            # Small delay to ensure different timestamp
            import time
            time.sleep(0.01)

            filepath2 = plan_storage.save_plan(basic_plan, overwrite_source=False)

            assert filepath1 != filepath2
            assert filepath1.exists()
            assert filepath2.exists()
        finally:
            plan_storage.config.SAVE_DIRECTORY = original_dir
