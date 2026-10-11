"""Tests for the plan management gaps (issues-program.org S4).

- Plans can be opened and deleted from the plan manager.
- The current plan (★, Plan.is_active) can be continued from the main menu.
- Changing the save directory offers to move existing plans.
"""

import contextlib
import io
import pytest
from datetime import datetime
from pathlib import Path
import plan
import plan_manager
import plan_manager_ui
import plan_storage
import planea
import user_preferences
import config
import ui_plan_actions
import ui_settings


OPEN, DELETE = "9", "10"


def make_plan(name):
    return plan.Plan(name=name, total=10000, daily=1000, time=10, start_date=datetime(2026, 11, 2))


@pytest.fixture
def two_plans():
    plans = [make_plan("Alpha"), make_plan("Beta")]
    for p in plans:
        plan_storage.save_plan(p)
    return plans


def names():
    return sorted(p.name for p in plan_manager.get_all_plans())


def menu_number(name):
    return str([p.name for p in plan_manager.get_all_plans()].index(name) + 1)


def quiet(func, *args):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        func(*args)
    return out.getvalue()


class TestDelete:

    def test_delete_with_confirmation(self, two_plans, scripted_input):
        scripted_input([DELETE, menu_number("Alpha"), "y", "", "0"])

        quiet(plan_manager_ui.manage_plans_menu)

        assert names() == ["Beta"]
        assert not two_plans[0].source_file.exists()

    def test_declined(self, two_plans, scripted_input):
        scripted_input([DELETE, menu_number("Alpha"), "n", "", "0"])

        quiet(plan_manager_ui.manage_plans_menu)

        assert names() == ["Alpha", "Beta"]

    def test_backup_deleted_too(self, two_plans, scripted_input):
        plan_storage.save_plan(two_plans[0])  # creates the .bak
        backup = Path(str(two_plans[0].source_file) + ".bak")
        assert backup.exists()
        scripted_input([DELETE, menu_number("Alpha"), "y", "", "0"])

        quiet(plan_manager_ui.manage_plans_menu)

        assert not backup.exists()


class TestOpen:

    def test_opens_the_plan_actions(self, two_plans, scripted_input, monkeypatch):
        opened = []
        monkeypatch.setattr(ui_plan_actions, 'handle_plan_actions', opened.append)
        scripted_input([OPEN, menu_number("Beta"), "0"])

        quiet(plan_manager_ui.manage_plans_menu)

        assert [p.name for p in opened] == ["Beta"]
        assert opened[0].source_file == two_plans[1].source_file

    def test_go_back(self, two_plans, scripted_input, monkeypatch):
        opened = []
        monkeypatch.setattr(ui_plan_actions, 'handle_plan_actions', opened.append)
        scripted_input([OPEN, "0", "0"])

        quiet(plan_manager_ui.manage_plans_menu)

        assert opened == []


class TestContinueCurrentPlan:

    def test_main_menu_offers_it(self, two_plans, scripted_input, monkeypatch):
        plan_manager.set_active_plan(two_plans[1].source_file)
        opened = []
        monkeypatch.setattr(ui_plan_actions, 'handle_plan_actions', opened.append)
        scripted_input(["6", "0"])

        output = quiet(planea.main_menu_loop)

        assert "6. Continue the current plan: ★ Beta" in output
        assert [p.name for p in opened] == ["Beta"]

    def test_no_current_plan_no_option(self, two_plans, scripted_input):
        scripted_input(["6", "0"])  # 6 is out of range, so it's asked again

        output = quiet(planea.main_menu_loop)

        assert "Continue the current plan" not in output
        assert "between 0 and 5" in output

    def test_manager_calls_it_the_current_plan(self, two_plans):
        plan_manager.set_active_plan(two_plans[0].source_file)

        output = quiet(plan_manager_ui.display_plans_overview)

        assert "★ Current plan: Alpha" in output
        assert "Currently Active" not in output


class TestMovePlans:

    def test_move_plans_and_backups(self, tmp_path):
        old, new = tmp_path / "old", tmp_path / "new"
        old.mkdir()
        (old / "a.json").write_text("{}")
        (old / "a.json.bak").write_text("{}")
        (old / "b.json").write_text("{}")
        new.mkdir()
        (new / "b.json").write_text('{"keep": 1}')

        moved, skipped = plan_storage.move_plans(old, new)

        assert moved == 1 and skipped == ["b.json"]
        assert sorted(f.name for f in new.iterdir()) == ["a.json", "a.json.bak", "b.json"]
        assert (new / "b.json").read_text() == '{"keep": 1}'
        assert (old / "b.json").exists()

    @pytest.fixture
    def custom_prefs(self, tmp_path, monkeypatch):
        """Preferences in a temp file, so a custom directory can be set."""
        prefs = tmp_path / "preferences.json"
        monkeypatch.setattr(user_preferences, 'get_preferences_file', lambda: prefs)

    def test_changing_directory_moves_plans(self, two_plans, custom_prefs, tmp_path, scripted_input):
        target = tmp_path / "Writing"
        scripted_input(["1", str(target), "y", "y"])  # set, create it, move plans

        quiet(ui_settings.configure_save_directory)

        assert plan_storage.get_plans_directory() == target / config.PLANS_SUBDIRECTORY
        assert names() == ["Alpha", "Beta"]

    def test_declining_leaves_them(self, two_plans, custom_prefs, tmp_path, scripted_input):
        target = tmp_path / "Writing"
        scripted_input(["1", str(target), "y", "n"])

        output = quiet(ui_settings.configure_save_directory)

        assert names() == []
        assert "They stay in" in output
        assert two_plans[0].source_file.exists()
