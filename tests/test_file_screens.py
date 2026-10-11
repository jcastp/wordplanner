"""Tests for the save/load screens and the pattern menu (issues-program.org T4)."""

import contextlib
import io
import pytest
from datetime import datetime, time
import plan
import plan_storage
import ui_files
from pattern_utils import choose_writing_pattern, get_pattern_description


MON = datetime(2026, 11, 2)


def make_plan(**kwargs):
    values = dict(name="Novel", total=10000, daily=1000, time=10, start_date=MON)
    values.update(kwargs)
    return plan.Plan(**values)


def run(func, *args, **kwargs):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        result = func(*args, **kwargs)
    return result, out.getvalue()


class TestSavePrompt:

    def test_new_plan_asks_for_a_name(self, scripted_input):
        p = make_plan(name=None)
        scripted_input(["y", "My Novel"])

        saved, _ = run(ui_files.save_plan_prompt, p)

        assert saved is True
        assert plan_storage.load_plan(p.source_file).name == "My Novel"

    def test_new_plan_without_a_name_is_not_saved(self, scripted_input):
        p = make_plan(name=None)
        scripted_input(["y", "  "])

        saved, output = run(ui_files.save_plan_prompt, p)

        assert saved is False
        assert "No name provided" in output
        assert plan_storage.list_saved_plans() == []

    def test_new_plan_can_be_renamed_on_save(self, scripted_input):
        p = make_plan()
        scripted_input(["n", "Second Novel"])   # ask=False: straight to the name

        run(ui_files.save_plan_prompt, p, ask=False)

        assert p.name == "Second Novel"
        assert p.source_file.name.startswith("Second_Novel_")

    def test_overwrite_the_original(self, scripted_input):
        p = make_plan()
        plan_storage.save_plan(p)
        original = p.source_file
        p.total = 12000
        scripted_input(["1"])

        saved, output = run(ui_files.save_plan_prompt, p, ask=False)

        assert saved is True
        assert "Plan updated successfully" in output
        assert plan_storage.load_plan(original).total == 12000
        assert len(plan_storage.list_saved_plans()) == 1

    def test_save_as_new_file_with_a_new_name(self, scripted_input):
        p = make_plan(is_active=True)
        plan_storage.save_plan(p)
        original = p.source_file
        scripted_input(["2", "n", "Copy"])

        _, output = run(ui_files.save_plan_prompt, p, ask=False)

        assert p.source_file != original and p.name == "Copy"
        assert "The original stays your current plan" in output
        assert sorted(info['name'] for info in plan_storage.list_saved_plans()) == ["Copy", "Novel"]

    def test_cancel_and_decline(self, scripted_input):
        p = make_plan()
        plan_storage.save_plan(p)
        p.total = 12000

        scripted_input(["0"])
        assert run(ui_files.save_plan_prompt, p, ask=False)[0] is False
        scripted_input(["n"])
        assert run(ui_files.save_plan_prompt, p)[0] is False

        assert plan_storage.load_plan(p.source_file).total == 10000

    def test_save_error_is_reported(self, scripted_input, monkeypatch):
        def broken(*args, **kwargs):
            raise OSError("disk full")
        monkeypatch.setattr(plan_storage, 'save_plan', broken)
        scripted_input(["y", "y"])

        saved, output = run(ui_files.save_plan_prompt, make_plan())

        assert saved is False
        assert "Error saving plan: disk full" in output


class TestLoadScreen:

    def test_load(self, scripted_input):
        plan_storage.save_plan(make_plan(name="Alpha"))
        plan_storage.save_plan(make_plan(name="Beta", total=20000, time=20))
        names = [info['name'] for info in plan_storage.list_saved_plans()]
        scripted_input([str(names.index("Beta") + 1)])

        loaded, output = run(ui_files.load_saved_plan)

        assert "Found 2 saved plan(s)" in output
        assert "20,000 words | 1,000/day | 20 days" in output
        assert loaded.name == "Beta" and not loaded.has_unsaved_changes()

    def test_cancel(self, scripted_input):
        plan_storage.save_plan(make_plan())
        scripted_input(["0"])

        assert run(ui_files.load_saved_plan)[0] is None

    def test_no_plans(self, scripted_input):
        scripted_input([""])

        loaded, output = run(ui_files.load_saved_plan)

        assert loaded is None
        assert "No saved plans found." in output

    def test_load_error_is_reported(self, scripted_input, monkeypatch):
        plan_storage.save_plan(make_plan())
        listed = plan_storage.list_saved_plans()
        # The file goes bad between listing and loading
        monkeypatch.setattr(plan_storage, 'list_saved_plans', lambda: listed)

        def broken(filepath):
            raise ValueError("bad file")
        monkeypatch.setattr(plan_storage, 'load_plan', broken)
        scripted_input(["1", ""])

        loaded, output = run(ui_files.load_saved_plan)

        assert loaded is None
        assert "Error loading plan: bad file" in output


class TestExportMenu:

    def test_all_formats(self, scripted_input):
        scripted_input(["4", "n", ""])

        _, output = run(ui_files.export_plan_menu, make_plan())

        assert "Exported 3 file(s)" in output

    def test_ical_asks_for_a_reminder_time(self, scripted_input, monkeypatch):
        used = []
        monkeypatch.setattr(ui_files.plan_export, 'export_to_ical',
                            lambda p, reminder=None: used.append(reminder) or "plan.ics")
        scripted_input(["2", "y", "25:00", "19:30", ""])   # an invalid time is asked again

        _, output = run(ui_files.export_plan_menu, make_plan())

        assert used == [time(19, 30)]
        assert "Invalid time '25:00'" in output

    @pytest.mark.parametrize("answers, reminder", [
        (["y", ""], time(9, 0)),    # Enter: the default time
        (["n"], None),
    ])
    def test_reminder_answers(self, scripted_input, answers, reminder):
        scripted_input(answers)

        result, _ = run(ui_files.ask_reminder_time)

        assert result == reminder

    def test_other_formats_ask_nothing(self, scripted_input):
        scripted_input(["1", ""])   # CSV, then "Press Enter": no reminder question

        _, output = run(ui_files.export_plan_menu, make_plan())

        assert "CSV exported" in output
        assert "Add a reminder" not in output

    def test_needs_a_start_date(self, scripted_input):
        scripted_input([""])

        _, output = run(ui_files.export_plan_menu, make_plan(start_date=None))

        assert "must have a start date" in output


class TestPatternMenu:

    @pytest.mark.parametrize("answers, pattern, config", [
        (["0"], "flat", {}),
        (["1"], "flat", {}),
        (["2", ""], "valley", {'peak_multiplier': 1.5, 'valley_multiplier': 0.7}),
        (["3", "1"], "mountain", {'peak_multiplier': 1.2, 'valley_multiplier': 0.8}),
        (["3", "3"], "mountain", {'peak_multiplier': 2.0, 'valley_multiplier': 0.5}),
        (["4", "1"], "rising", {'start_multiplier': 0.8, 'end_multiplier': 1.2}),
        (["4", "3"], "rising", {'start_multiplier': 0.3, 'end_multiplier': 2.0}),
        (["4", ""], "rising", {'start_multiplier': 0.5, 'end_multiplier': 1.5}),
        (["5", "1"], "declining", {'start_multiplier': 1.2, 'end_multiplier': 0.8}),
        (["5", "3"], "declining", {'start_multiplier': 2.0, 'end_multiplier': 0.3}),
        (["5", ""], "declining", {'start_multiplier': 1.5, 'end_multiplier': 0.5}),
        (["6", "1", "n"], "random", {'min_multiplier': 0.8, 'max_multiplier': 1.2}),
        (["6", "", "n"], "random", {'min_multiplier': 0.5, 'max_multiplier': 1.5}),
    ])
    def test_choices(self, scripted_input, answers, pattern, config):
        scripted_input(answers)

        assert run(choose_writing_pattern)[0] == (pattern, config)

    def test_random_with_a_seed(self, scripted_input):
        scripted_input(["6", "3", "y"])

        (pattern, config), _ = run(choose_writing_pattern)

        assert (config['min_multiplier'], config['max_multiplier']) == (0.3, 2.0)
        assert isinstance(config['seed'], int)

    def test_descriptions(self):
        assert get_pattern_description('valley').startswith("Valley")
        assert get_pattern_description('custom') == "Custom"
