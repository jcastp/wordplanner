"""Tests that plan dates never carry a time of day (issues-program.org RC4/P7).

"Press Enter for today" used to store datetime.now(), e.g. 2026-10-05 14:30.
Calendar days are compared at midnight, so the start day itself fell outside
the plan: not drawn in the calendar, status 'no_goal', not expected, no streak.
"""

import pytest
from datetime import date, datetime, timedelta
from freezegun import freeze_time
import plan
import plan_templates
import ui_utils


START_WITH_TIME = datetime(2026, 10, 5, 14, 30, 12, 345)
START = datetime(2026, 10, 5)


class TestStartDateNormalization:
    """Plan.start_date is always stored at midnight."""

    def test_constructor_drops_time(self):
        p = plan.Plan(total=3000, daily=1000, time=3, start_date=START_WITH_TIME)

        assert p.start_date == START

    def test_assignment_drops_time(self):
        p = plan.Plan(total=3000, daily=1000, time=3)

        p.start_date = START_WITH_TIME

        assert p.start_date == START

    def test_date_object_becomes_midnight_datetime(self):
        p = plan.Plan(total=3000, daily=1000, time=3, start_date=date(2026, 10, 5))

        assert p.start_date == START
        assert isinstance(p.start_date, datetime)

    def test_none_stays_none(self):
        p = plan.Plan(total=3000, daily=1000, time=3)

        assert p.start_date is None

    def test_spare_days_drop_time(self):
        p = plan.Plan(total=3000, daily=1000, time=3, start_date=START,
                      spare_days_dates=[datetime(2026, 10, 6, 9, 15)])

        assert p.spare_days_dates == [datetime(2026, 10, 6)]


class TestOldFilesAreMigrated:
    """Plans saved with a time of day are fixed when loaded."""

    def test_from_dict_drops_time(self, sample_plan_dict):
        sample_plan_dict['start_date'] = '2025-11-01T14:30:12.000345'
        sample_plan_dict['spare_days_dates'] = ['2025-11-15T14:30:12']

        p = plan.Plan.from_dict(sample_plan_dict)

        assert p.start_date == datetime(2025, 11, 1)
        assert p.spare_days_dates == [datetime(2025, 11, 15)]

    def test_saved_again_without_time(self, sample_plan_dict):
        sample_plan_dict['start_date'] = '2025-11-01T14:30:12'

        data = plan.Plan.from_dict(sample_plan_dict).to_dict()

        assert data['start_date'] == '2025-11-01T00:00:00'

    def test_legacy_integer_spare_days_land_at_midnight(self, sample_plan_dict):
        sample_plan_dict['start_date'] = '2025-11-01T14:30:12'
        sample_plan_dict['spare_days_dates'] = [3]

        p = plan.Plan.from_dict(sample_plan_dict)

        assert p.spare_days_dates == [datetime(2025, 11, 3)]


class TestStartDayIsPartOfThePlan:
    """The P7 scenario: start date entered with a time of day."""

    @pytest.fixture
    def started_plan(self):
        p = plan.Plan(total=3000, daily=1000, time=3, start_date=START_WITH_TIME)
        p.record_progress(START, 1000)
        return p

    @freeze_time("2026-10-07")
    def test_start_day_status(self, started_plan):
        assert started_plan.get_progress_status_for_date(START) == 'met'

    def test_start_day_is_expected(self, started_plan):
        on_track, info = started_plan.is_on_track(as_of_date=START)

        assert info['expected_words'] == 1000
        assert info['days_elapsed'] == 1
        assert on_track is True

    @freeze_time("2026-10-06 20:00")
    def test_start_day_counts_in_streak(self, started_plan):
        started_plan.record_progress(START + timedelta(days=1), 1000)

        assert started_plan.get_current_streak() == 2

    def test_start_day_inside_calendar_range(self, started_plan):
        # calendar_view draws a day when start_date <= day <= end_date
        assert started_plan.start_date <= START


class TestTodayInputsAreMidnight:
    """Places that use "today" as a default produce midnight dates."""

    @freeze_time("2026-10-05 14:30:12")
    def test_get_date_input_enter_means_today_at_midnight(self, scripted_input):
        scripted_input([""])

        assert ui_utils.get_date_input("Start date: ") == START

    @freeze_time("2026-10-05 14:30:12")
    def test_template_default_start_date(self):
        template = plan_templates.create_custom_template("Test", "Test template", 3000, time=3)

        p = template.create_plan()

        assert p.start_date == START
