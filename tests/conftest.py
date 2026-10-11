"""Shared pytest fixtures for planeapalabras tests."""

import pytest
import datetime
from pathlib import Path
import sys

# Add parent directory to path so we can import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

import plan
import config


@pytest.fixture(autouse=True)
def isolated_storage(tmp_path_factory, monkeypatch):
    """
    Keep every test away from the real ~/.wordplanner.

    Plans, exports and preferences all live under config.SAVE_DIRECTORY;
    an absolute path is used as is. Tests that set it themselves still can.
    """
    monkeypatch.setattr(config, 'SAVE_DIRECTORY', str(tmp_path_factory.mktemp('wordplanner')))


@pytest.fixture
def basic_plan():
    """
    Basic plan with minimal configuration.

    Returns:
        Plan: A simple plan with total=10000, daily=1000, time=10
    """
    return plan.Plan(total=10000, daily=1000, time=10)


@pytest.fixture
def complete_plan():
    """
    Fully configured plan with all features.

    Returns:
        Plan: A plan with patterns, progress, weekends, custom goals, etc.
    """
    start_date = datetime.datetime(2025, 11, 1)
    p = plan.Plan(
        total=50000,
        daily=1000,
        time=50,
        name="Complete Test Plan",
        start_date=start_date,
        pattern="valley",
        pattern_config={"intensity": "moderate"},
        weekend_mode="different",
        weekend_daily=1500,
        weekend_days=[5, 6]
    )

    # Add some progress
    p.record_progress(start_date, 1200)
    p.record_progress(start_date + datetime.timedelta(days=1), 950)
    p.record_progress(start_date + datetime.timedelta(days=2), 1100)

    # Add a custom daily goal
    p.set_custom_daily_goal(start_date + datetime.timedelta(days=10), 2000)

    # Add spare days
    p.spare_days_dates.append(start_date + datetime.timedelta(days=15))
    p.spare_days_dates.append(start_date + datetime.timedelta(days=16))

    return p


@pytest.fixture
def plan_with_progress():
    """
    Plan with recorded progress data.

    Returns:
        Plan: A plan with 7 days of progress recorded
    """
    start_date = datetime.datetime(2025, 11, 1)
    p = plan.Plan(
        total=10000,
        daily=1000,
        time=10,
        start_date=start_date
    )

    # Add progress for a week
    progress_data = [1200, 950, 1100, 800, 1300, 900, 1000]
    for i, words in enumerate(progress_data):
        p.record_progress(start_date + datetime.timedelta(days=i), words)

    return p


@pytest.fixture
def plan_with_weekends():
    """
    Plan with weekend configuration.

    Returns:
        Plan: A plan with weekend mode set to 'different'
    """
    return plan.Plan(
        total=10000,
        daily=1000,
        time=10,
        start_date=datetime.datetime(2025, 11, 1),
        weekend_mode="different",
        weekend_daily=1500,
        weekend_days=[5, 6]
    )


@pytest.fixture
def plan_with_pattern():
    """
    Plan with writing pattern.

    Returns:
        Plan: A plan with valley pattern
    """
    return plan.Plan(
        total=10000,
        daily=1000,
        time=10,
        start_date=datetime.datetime(2025, 11, 1),
        pattern="valley",
        pattern_config={"intensity": "moderate"}
    )


@pytest.fixture
def plan_with_custom_goals():
    """
    Plan with custom daily goals set.

    Returns:
        Plan: A plan with several custom daily goals
    """
    start_date = datetime.datetime(2025, 11, 1)
    p = plan.Plan(
        total=10000,
        daily=1000,
        time=10,
        start_date=start_date
    )

    # Set custom goals for specific dates
    p.set_custom_daily_goal(start_date + datetime.timedelta(days=5), 2000)
    p.set_custom_daily_goal(start_date + datetime.timedelta(days=6), 500)
    p.set_custom_daily_goal(start_date + datetime.timedelta(days=7), 1500)

    return p


@pytest.fixture
def sample_dates():
    """
    Collection of test dates.

    Returns:
        dict: Dictionary of named dates for testing
    """
    base_date = datetime.datetime(2025, 11, 1)
    return {
        'monday': base_date,  # 2025-11-01 is a Saturday, adjust as needed
        'tuesday': base_date + datetime.timedelta(days=1),
        'wednesday': base_date + datetime.timedelta(days=2),
        'thursday': base_date + datetime.timedelta(days=3),
        'friday': base_date + datetime.timedelta(days=4),
        'saturday': base_date + datetime.timedelta(days=5),
        'sunday': base_date + datetime.timedelta(days=6),
        'next_week': base_date + datetime.timedelta(days=7),
        'next_month': base_date + datetime.timedelta(days=30),
    }


@pytest.fixture
def temp_plan_directory(tmp_path):
    """
    Temporary directory for file operations.

    Args:
        tmp_path: pytest's built-in tmp_path fixture

    Returns:
        Path: Path to temporary directory for testing file operations
    """
    plans_dir = tmp_path / "plans"
    plans_dir.mkdir()
    return plans_dir


@pytest.fixture
def temp_export_directory(tmp_path):
    """
    Temporary directory for export operations.

    Args:
        tmp_path: pytest's built-in tmp_path fixture

    Returns:
        Path: Path to temporary directory for testing exports
    """
    exports_dir = tmp_path / "exports"
    exports_dir.mkdir()
    return exports_dir


@pytest.fixture
def sample_plan_dict():
    """
    Sample plan data as dictionary (for testing serialization).

    Returns:
        dict: Plan data in dictionary format
    """
    return {
        'name': 'Test Plan',
        'total': 10000,
        'daily': 1000,
        'time': 10,
        'words': 10000,
        'spare_days_dates': ['2025-11-15', '2025-11-16'],
        'start_date': '2025-11-01T00:00:00',
        'created_date': '2025-10-28T12:00:00',
        'pattern': 'flat',
        'pattern_config': {},
        'progress': {
            '2025-11-01': 1200,
            '2025-11-02': 950,
        },
        'weekend_mode': 'same',
        'weekend_daily': 0,
        'weekend_days': [5, 6],
        'custom_daily_goals': {},
    }


@pytest.fixture
def nanowrimo_plan():
    """
    NaNoWriMo-style plan (50,000 words in 30 days).

    Returns:
        Plan: A plan matching NaNoWriMo requirements
    """
    return plan.Plan(
        total=50000,
        time=30,
        name="NaNoWriMo 2025",
        start_date=datetime.datetime(2025, 11, 1)
    )


class InputExhausted(BaseException):
    """
    Raised when a test's scripted answers run out.

    Derives from BaseException so the `except Exception` retry loops in
    ui_utils cannot swallow it and spin forever.
    """


@pytest.fixture
def scripted_input(monkeypatch):
    """
    Replace input() with a fixed list of answers.

    Usage:
        scripted_input(["1", "80000", "y"])

    Raises InputExhausted if the code asks for more answers than provided.
    """
    def _script(answers):
        remaining = iter(answers)

        def fake_input(prompt=""):
            try:
                return next(remaining)
            except StopIteration:
                raise InputExhausted(f"No scripted answer left for prompt: {prompt!r}")

        monkeypatch.setattr('builtins.input', fake_input)

    return _script
