"""Tests for the smaller model issues (issues-program.org P21)."""

import contextlib
import io
import json
from datetime import datetime, timedelta
from freezegun import freeze_time
import plan
import planea


MON = datetime(2026, 11, 2)


def make_plan(**kwargs):
    values = dict(total=10000, daily=1000, time=10, start_date=MON)
    values.update(kwargs)
    return plan.Plan(**values)


class TestWeekendDays:

    def test_default_is_saturday_and_sunday(self):
        assert make_plan().weekend_days == [5, 6]

    def test_no_weekend_days_survives_a_save(self):
        # Used to come back as [5, 6]: `weekend_days or [5, 6]`
        p = make_plan(weekend_days=[])

        loaded = plan.Plan.from_json(p.to_json())

        assert loaded.weekend_days == []
        assert not loaded.is_weekend(MON + timedelta(days=5))

    def test_old_file_without_weekend_days(self, sample_plan_dict):
        sample_plan_dict.pop('weekend_days', None)

        assert plan.Plan.from_dict(sample_plan_dict).weekend_days == [5, 6]


class TestUnusedWordsField:

    def test_not_saved(self):
        assert 'words' not in make_plan().to_dict()

    def test_old_files_with_it_still_load(self, sample_plan_dict):
        sample_plan_dict['words'] = 12345

        assert plan.Plan.from_dict(sample_plan_dict).total == sample_plan_dict['total']


class TestWholeNumbers:

    def test_whole_numbers_load_as_ints(self):
        data = json.loads(make_plan().to_json())
        data['total'] = 50000.0
        data['weekend_daily'] = 1500.0

        p = plan.Plan.from_dict(data)

        assert type(p.total) is int and type(p.weekend_daily) is int
        assert f"{p.total:,}" == "50,000"

    def test_fractional_numbers_stay(self):
        data = json.loads(make_plan().to_json())
        data['daily'] = 1666.67

        assert plan.Plan.from_dict(data).daily == 1666.67

    def test_calculated_totals_are_whole_words(self):
        p = make_plan(pattern="rising", pattern_config={'start_multiplier': 0.5, 'end_multiplier': 1.5})
        p.set_custom_daily_goal(MON + timedelta(days=3), 1234.5)
        p.daily = 777.7

        p.calculate_words()

        assert type(p.total) is int
        assert p.recalculate_total_from_daily_goals() == p.total


@freeze_time("2026-10-01")
class TestModifiedMessage:
    """"Plan modified successfully!" only when something changed."""

    def run_actions(self, p, answers, scripted_input):
        scripted_input(answers)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            planea.handle_plan_actions(p)
        return out.getvalue()

    def test_cancel_says_nothing(self, scripted_input):
        # modify, cancel; back to main menu, without saving
        output = self.run_actions(make_plan(), ["4", "0", "0", "2"], scripted_input)

        assert "Plan modified successfully" not in output

    def test_spare_days_viewed_but_unchanged(self, scripted_input):
        # Used to say "modified" whenever the plan had any spare day
        p = make_plan(spare_days_dates=[MON + timedelta(days=3)])

        output = self.run_actions(p, ["4", "4", "0", "0", "2"], scripted_input)

        assert "Plan modified successfully" not in output

    def test_real_change_says_so(self, scripted_input):
        # modify -> spare days -> add 2026-11-04, move the end date, done
        output = self.run_actions(
            make_plan(), ["4", "4", "1", "2026-11-04", "1", "0", "0", "2"], scripted_input)

        assert "Plan modified successfully" in output

    def test_spare_day_screen_reports_change(self, scripted_input):
        p = make_plan(spare_days_dates=[MON + timedelta(days=3)])
        scripted_input(["0"])

        with contextlib.redirect_stdout(io.StringIO()):
            assert planea.manage_spare_days(p) is False
