"""Tests for the menu clean-up (issues-program.org Q1).

Menus read their choice with ui_utils.get_menu_choice, which re-asks on
empty, non-numeric or out-of-range answers; spare-day dates are parsed by
one shared planea.parse_date_list().
"""

import contextlib
import io
import pytest
from datetime import datetime, timedelta
from freezegun import freeze_time
import plan
import planea


MON = datetime(2026, 11, 2)


def make_plan(**kwargs):
    values = dict(name="Novel", total=10000, daily=1000, time=10, start_date=MON)
    values.update(kwargs)
    return plan.Plan(**values)


def run(func, *args):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        result = func(*args)
    return result, out.getvalue()


class TestParseDateList:

    def test_single_and_comma_separated(self):
        assert planea.parse_date_list("2026-11-03") == [datetime(2026, 11, 3)]
        assert planea.parse_date_list("2026-11-03, 2026-11-05,") == [
            datetime(2026, 11, 3), datetime(2026, 11, 5)]

    def test_range_in_either_order(self):
        expected = [datetime(2026, 11, d) for d in (3, 4, 5)]

        assert planea.parse_date_list("2026-11-03 to 2026-11-05") == expected
        assert planea.parse_date_list("2026-11-05 TO 2026-11-03") == expected

    @pytest.mark.parametrize("text", ["2026-13-01", "tomorrow", "2026-11-01 to 2026-11-02 to 2026-11-03"])
    def test_malformed(self, text):
        with pytest.raises(ValueError):
            planea.parse_date_list(text)

    @freeze_time("2026-10-01")
    def test_malformed_range_on_remove_is_reported(self, scripted_input):
        # Removing used to ignore a malformed range silently
        p = make_plan(spare_days_dates=[MON + timedelta(days=3)])
        scripted_input(["2", "2026-11-05 to 2026-11-06 to 2026-11-07", "0"])

        _, output = run(planea.manage_spare_days, p)

        assert "Invalid date format" in output
        assert p.spare_days_dates == [MON + timedelta(days=3)]


@freeze_time("2026-10-01")
class TestMenusReask:

    def test_out_of_range_and_text_are_asked_again(self, scripted_input):
        p = make_plan()
        scripted_input(["11", "abc", "", "0"])   # modify menu: three bad answers, then Cancel

        result, output = run(planea.modify_plan, p)

        assert result is False
        assert "between 0 and 10" in output
        assert "Invalid input 'abc'" in output

    def test_sub_menu_choice(self, scripted_input):
        # Modify -> Total words -> 30,000 -> "3" (out of range) -> "2" keep days
        p = make_plan()
        scripted_input(["1", "30000", "3", "2"])

        result, _ = run(planea.modify_plan, p)

        assert result is True
        assert p.total == 30000 and p.time == 10

    def test_model_error_is_reported_not_mislabelled(self, scripted_input, monkeypatch):
        p = make_plan()

        def broken():
            raise ValueError("time must be greater than 0")
        monkeypatch.setattr(p, 'calculate_daily', broken)
        scripted_input(["1", "30000", "2", "0"])   # keep days -> error; then Cancel

        _, output = run(planea.modify_plan, p)

        assert "Invalid input: time must be greater than 0" in output
        assert "Please enter a number" not in output

    def test_calendar_menu(self, scripted_input):
        scripted_input(["5", "2"])   # out of range, then weekly summary

        _, output = run(planea.show_calendar_options, make_plan())

        assert "between 0 and 3" in output
        assert "Week" in output

    def test_export_menu(self, scripted_input):
        scripted_input(["3", ""])   # Markdown, then "Press Enter"

        _, output = run(planea.export_plan_menu, make_plan())

        assert "Markdown exported" in output

    def test_weekend_menu_skip(self, scripted_input):
        p = make_plan()
        scripted_input(["9", "0"])

        _, output = run(planea.configure_weekend_settings, p)

        assert "between 0 and 3" in output
        assert p.weekend_mode == "same"
