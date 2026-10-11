"""Tests for the Settings preferences: defaults for new plans, first day of the
week, date format and colors (user_preferences, formatting, ui_settings)."""

import contextlib
import io
import json
import re
from datetime import datetime, timedelta
from freezegun import freeze_time
import pytest
import calendar_view
import cli
import formatting
import plan
import plan_export
import plan_manager_ui
import plan_storage
import progress_analytics
import ui_create
import ui_plan_actions
import ui_progress
import ui_settings
import user_preferences


MON = datetime(2026, 11, 2)


def run(func, *args):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        result = func(*args)
    return result, out.getvalue()


def make_plan(**kwargs):
    values = dict(name="Novel", total=10000, daily=1000, time=10, start_date=MON)
    values.update(kwargs)
    return plan.Plan(**values)


class TestStore:

    def test_defaults(self):
        assert user_preferences.get_preference('date_format') == "iso"
        assert user_preferences.get_preference('first_weekday') == 0
        assert user_preferences.get_preference('colors') is True
        assert user_preferences.get_preference('default_pattern') == "flat"
        assert user_preferences.get_preference('default_weekend_mode') == "same"

    def test_set_and_read_back_from_disk(self):
        user_preferences.set_preference('date_format', "dmy")
        user_preferences._cache = None   # as in a new session

        assert user_preferences.get_preference('date_format') == "dmy"

    def test_invalid_value_is_refused(self):
        with pytest.raises(ValueError):
            user_preferences.set_preference('first_weekday', 3)

        assert user_preferences.get_preference('first_weekday') == 0

    @pytest.mark.parametrize("content", [
        '{"date_format": "klingon", "colors": "yes", "first_weekday": 2}',   # hand-edited
        '{not json',
        '[1, 2]',
    ])
    def test_bad_files_give_defaults(self, content):
        path = user_preferences.get_preferences_file()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        user_preferences._cache = None

        assert user_preferences.get_preference('date_format') == "iso"
        assert user_preferences.get_preference('colors') is True
        assert user_preferences.get_preference('first_weekday') == 0

    def test_save_directory_setting_is_kept(self, tmp_path):
        user_preferences.set_custom_save_directory(str(tmp_path))
        user_preferences.set_preference('colors', False)

        assert user_preferences.get_custom_save_directory() == str(tmp_path)
        assert json.loads(user_preferences.get_preferences_file().read_text())['colors'] is False


class TestDateFormat:

    @pytest.mark.parametrize("name, shown, short", [
        ("iso", "2026-11-05", "11-05"),
        ("dmy", "05/11/2026", "05/11"),
        ("mdy", "11/05/2026", "11/05"),
        ("text", "Nov 05, 2026", "Nov 05"),
    ])
    def test_format(self, name, shown, short):
        user_preferences.set_preference('date_format', name)
        day = datetime(2026, 11, 5)

        assert formatting.format_date(day) == shown
        assert formatting.format_date_weekday(day) == f"{shown} (Thursday)"
        assert formatting.format_day_month(day) == short

    @pytest.mark.parametrize("name, typed, hint", [
        ("iso", ["2026-11-05"], "YYYY-MM-DD"),
        ("dmy", ["2026-11-05", "05/11/2026", " 5/11/2026 "], "DD/MM/YYYY or YYYY-MM-DD"),
        ("mdy", ["2026-11-05", "11/05/2026"], "MM/DD/YYYY or YYYY-MM-DD"),
        ("text", ["2026-11-05"], "YYYY-MM-DD"),
    ])
    def test_parse(self, name, typed, hint):
        user_preferences.set_preference('date_format', name)

        assert formatting.date_hint() == hint
        for text in typed:
            assert formatting.parse_date(text) == datetime(2026, 11, 5)

    @pytest.mark.parametrize("name, text", [
        ("iso", "05/11/2026"),     # only ISO without a numeric preference
        ("dmy", "11/31/2026"),     # month 31
        ("dmy", "tomorrow"),
    ])
    def test_parse_errors(self, name, text):
        user_preferences.set_preference('date_format', name)

        with pytest.raises(ValueError, match="is not a date"):
            formatting.parse_date(text)

    @freeze_time("2026-11-05")
    def test_progress_entry_reads_and_shows_the_format(self, scripted_input):
        user_preferences.set_preference('date_format', "dmy")
        p = make_plan()
        scripted_input(["2", "03/11/2026", "800", "n", "0", "n"])

        _, output = run(ui_progress.update_progress, p)

        assert p.get_progress_for_date(MON + timedelta(days=1)) == 800
        assert "Enter the date (DD/MM/YYYY or YYYY-MM-DD)" in output
        assert "Entering progress for: 03/11/2026 (Tuesday)" in output

    @freeze_time("2026-11-05")
    def test_command_line(self, capsys):
        user_preferences.set_preference('date_format', "mdy")
        p = make_plan(is_active=True)
        plan_storage.save_plan(p)

        assert cli.run(["log", "700", "--date", "11/03/2026"]) == 0

        assert "Logged 700 words on 11/03/2026." in capsys.readouterr().out
        assert plan_storage.load_plan(p.source_file).get_progress_for_date(MON + timedelta(days=1)) == 700

    def test_plan_manager_and_analytics(self):
        user_preferences.set_preference('date_format', "dmy")
        plan_storage.save_plan(make_plan(start_date=datetime(2099, 1, 4)))

        with freeze_time("2026-11-05"):
            _, output = run(plan_manager_ui.display_plans_overview)
        assert "Not started yet (starts 04/01/2099)" in output

        with freeze_time("2026-11-04"):
            p = make_plan()
            p.record_progress(MON, 1000)
            p.record_progress(MON + timedelta(days=1), 1000)
            _, output = run(progress_analytics.display_statistics, p)
        assert re.search(r"Estimated Completion\s*│\s*\d\d/11/2026", output)   # day/month/year

    def test_data_stays_iso(self, tmp_path):
        user_preferences.set_preference('date_format', "dmy")
        p = make_plan()
        p.record_progress(MON, 900)

        plan_storage.save_plan(p)
        csv_path = plan_export.export_to_csv(p, tmp_path / "plan.csv")

        assert '"2026-11-02": 900' in p.source_file.read_text()
        assert "2026-11-02" in csv_path.read_text()
        assert "02/11/2026" not in csv_path.read_text()


class TestFirstWeekday:

    def render(self, monkeypatch, p):
        monkeypatch.setenv("COLUMNS", "120")
        return run(calendar_view.display_calendar_view, p, p.start_date)[1]

    def test_monday_by_default(self, monkeypatch):
        output = self.render(monkeypatch, make_plan())

        header = next(line for line in output.splitlines() if "Week" in line and "Mon" in line)
        assert header.index("Mon") < header.index("Sun")

    def test_sunday(self, monkeypatch):
        user_preferences.set_preference('first_weekday', 6)

        assert calendar_view.week_order() == [6, 0, 1, 2, 3, 4, 5]
        output = self.render(monkeypatch, make_plan())
        header = next(line for line in output.splitlines() if "Week" in line and "Sun" in line)
        assert header.index("Sun") < header.index("Mon") < header.index("Sat")
        # Nov 1, 2026 is a Sunday: first cell of the first week
        first_week = next(line for line in output.splitlines() if "W1" in line)
        assert first_week.split("│")[2].strip() == "1"


def has_colors(text):
    """True if text has ANSI foreground or background color codes (bold/italic don't count)."""
    for params in re.findall(r"\x1b\[([\d;]*)m", text):
        codes = [int(c) for c in params.split(";") if c]
        if any(30 <= c <= 49 or 90 <= c <= 107 for c in codes):
            return True
    return False


class TestColors:

    def test_console(self, monkeypatch):
        monkeypatch.delenv("NO_COLOR", raising=False)
        assert formatting.make_console().no_color is False

        user_preferences.set_preference('colors', False)

        assert formatting.make_console().no_color is True

    @pytest.mark.parametrize("colors", [True, False])
    def test_color_codes_on_a_terminal(self, monkeypatch, colors):
        monkeypatch.delenv("NO_COLOR", raising=False)
        user_preferences.set_preference('colors', colors)
        out = io.StringIO()
        real_console = formatting.Console
        monkeypatch.setattr(formatting, 'Console',
                            lambda **kw: real_console(file=out, force_terminal=True, **kw))

        calendar_view.display_milestones(formatting.make_console(), make_plan(), MON, MON + timedelta(days=9))

        assert "Milestones" in out.getvalue()
        assert has_colors(out.getvalue()) is colors

    def test_graphs_drop_colors(self, monkeypatch):
        cleared = []
        monkeypatch.setattr(progress_analytics.plt, 'clear_color', lambda: cleared.append(True))
        p = make_plan()
        p.record_progress(MON, 1000)

        with freeze_time(MON + timedelta(days=2)):
            run(progress_analytics.plot_milestone_progress, p)
            assert cleared == []
            user_preferences.set_preference('colors', False)
            run(progress_analytics.plot_milestone_progress, p)
        assert cleared == [True]


@pytest.fixture
def opened(monkeypatch):
    """Plans that creation hands to the plan actions menu."""
    plans = []
    monkeypatch.setattr(ui_plan_actions, 'handle_plan_actions', plans.append)
    return plans


@freeze_time("2026-11-01")
class TestNewPlanDefaults:

    def test_no_defaults_asks_as_before(self, scripted_input, opened):
        # total + daily; no pre-existing; no pattern; start; no weekend settings
        scripted_input(["1", "10000", "n", "1000", "n", "2026-11-02", "n"])

        run(ui_create.create_new_plan)

        assert (opened[0].pattern, opened[0].weekend_mode) == ("flat", "same")

    def test_default_pattern_and_rest_weekends(self, scripted_input, opened):
        user_preferences.set_preference('default_pattern', "rising")
        user_preferences.set_preference('default_pattern_config', {'start_multiplier': 0.8, 'end_multiplier': 1.2})
        user_preferences.set_preference('default_weekend_mode', "spare")
        scripted_input(["1", "10000", "n", "1000", "y", "2026-11-02", "y"])

        _, output = run(ui_create.create_new_plan)

        p = opened[0]
        assert p.pattern == "rising" and p.pattern_config['end_multiplier'] == 1.2
        assert p.weekend_mode == "spare"
        # Total and daily were typed: the days are recalculated with weekends off
        assert (p.total, round(p.daily)) == (10000, 1000)
        assert p.end_date == datetime(2026, 11, 13)   # 10 weekdays
        assert "Weekends: no writing on weekends" in output

    def test_recalculates_the_daily_goal_when_days_were_typed(self, scripted_input, opened):
        user_preferences.set_preference('default_weekend_mode', "different")
        user_preferences.set_preference('default_weekend_daily', 500)
        # total + time -> daily; weekends at 500 a day
        scripted_input(["3", "10000", "n", "14", "n", "2026-11-02", "y"])

        run(ui_create.create_new_plan)

        p = opened[0]
        assert (p.total, p.time, p.weekend_daily) == (10000, 14, 500)
        assert round(p.daily) == 800   # (10,000 - 4 weekend days x 500) / 10 weekdays
        assert sum(p.get_daily_goal(date=d) for d in p.plan_days()) == pytest.approx(10000)

    def test_declining_the_defaults(self, scripted_input, opened):
        user_preferences.set_preference('default_pattern', "valley")
        user_preferences.set_preference('default_weekend_mode', "spare")
        # no to the default pattern, no other pattern; no to default weekends, no settings
        scripted_input(["1", "10000", "n", "1000", "n", "n", "2026-11-02", "n", "n"])

        run(ui_create.create_new_plan)

        assert (opened[0].pattern, opened[0].weekend_mode) == ("flat", "same")

    def test_templates_ignore_the_defaults(self, scripted_input, opened):
        user_preferences.set_preference('default_pattern', "valley")
        user_preferences.set_preference('default_weekend_mode', "spare")
        # NaNoWriMo as-is, nothing written yet, start date; decline its own pattern
        # and weekend suggestions: the defaults from Settings aren't offered either
        scripted_input(["1", "y", "n", "2026-11-02", "n", "n"])

        run(ui_create.create_plan_from_template)

        assert opened[0].weekend_mode == "same" and opened[0].pattern == "flat"


class TestSettingsScreens:

    def test_menu_shows_current_values(self, scripted_input):
        user_preferences.set_preference('date_format', "text")
        scripted_input(["0"])

        _, output = run(ui_settings.settings_menu)

        assert "pattern: flat (same goal every day); weekends: same as weekdays" in output
        assert "3. First day of the week (Monday)" in output
        assert "4. Date format (Nov 05, 2026)" in output
        assert "5. Colors (on)" in output

    def test_change_everything(self, scripted_input):
        scripted_input([
            "2", "1", "3", "3",          # defaults: pattern mountain, extreme
            "2", "2", "2", "400",        # defaults: weekends different, 400
            "3", "2",                    # Sunday
            "4", "3",                    # MM/DD/YYYY
            "5", "y",                    # colors off
            "0",
        ])

        _, output = run(ui_settings.settings_menu)

        get = user_preferences.get_preference
        assert get('default_pattern') == "mountain"
        assert get('default_pattern_config') == {'peak_multiplier': 2.0, 'valley_multiplier': 0.5}
        assert (get('default_weekend_mode'), get('default_weekend_daily')) == ("different", 400)
        assert get('first_weekday') == 6
        assert get('date_format') == "mdy"
        assert get('colors') is False
        assert "Dates are now shown as 11/05/2026; type them as MM/DD/YYYY or YYYY-MM-DD" in output
        assert "400 words/day on weekends" in output

    @pytest.mark.parametrize("screen", [
        ui_settings.configure_new_plan_defaults,
        ui_settings.configure_first_weekday,
        ui_settings.configure_date_format,
    ])
    def test_back_changes_nothing(self, scripted_input, screen):
        scripted_input(["0"])

        run(screen)

        assert user_preferences.load_preferences() == {}

    def test_colors_kept_when_declined(self, scripted_input):
        scripted_input(["n"])

        run(ui_settings.configure_colors)

        assert user_preferences.get_preference('colors') is True
