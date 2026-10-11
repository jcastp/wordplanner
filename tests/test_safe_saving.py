"""Tests for not losing work (issues-program.org S1, S2, S6).

S1: unsaved changes are noticed when leaving a plan and on Ctrl+C / Ctrl+D.
S2: saves are atomic and keep the previous version as <file>.bak.
S6: saving after progress asks once.
"""

import contextlib
import io
import json
import os
import pytest
from datetime import datetime
from freezegun import freeze_time
import plan
import plan_storage
import planea
import ui_utils
import user_preferences
import file_utils


@pytest.fixture
def plans_dir(tmp_path, monkeypatch):
    """Send plan storage to a temporary directory, whatever the user's preferences say."""
    monkeypatch.setattr(plan_storage.config, 'SAVE_DIRECTORY', str(tmp_path))
    monkeypatch.setattr(user_preferences, 'get_custom_save_directory', lambda: None)
    monkeypatch.setattr(plan_storage.user_preferences, 'get_custom_save_directory', lambda: None)
    return plan_storage.get_plans_directory()


@pytest.fixture
def saved_plan(plans_dir):
    p = plan.Plan(name="Novel", total=10000, daily=1000, time=10, start_date=datetime(2026, 11, 2))
    plan_storage.save_plan(p)
    return p


def quiet(func, *args, **kwargs):
    with contextlib.redirect_stdout(io.StringIO()):
        return func(*args, **kwargs)


def saved_files(plans_dir):
    return sorted(f.name for f in plans_dir.iterdir())


class TestWriteAtomically:

    def test_writes_and_replaces(self, tmp_path):
        target = tmp_path / "plan.json"

        file_utils.write_atomically(target, '{"a": 1}')
        file_utils.write_atomically(target, '{"a": 2}')

        assert json.loads(target.read_text()) == {"a": 2}
        assert [f.name for f in tmp_path.iterdir()] == ["plan.json"]

    def test_failed_write_leaves_old_file(self, tmp_path, monkeypatch):
        target = tmp_path / "plan.json"
        target.write_text('{"a": 1}')

        def broken_replace(src, dst):
            raise OSError("disk full")
        monkeypatch.setattr(file_utils.os, 'replace', broken_replace)

        with pytest.raises(OSError):
            file_utils.write_atomically(target, '{"a": 2}')

        assert json.loads(target.read_text()) == {"a": 1}
        assert [f.name for f in tmp_path.iterdir()] == ["plan.json"]

    def test_backup_keeps_previous_version(self, tmp_path):
        target = tmp_path / "plan.json"
        target.write_text('{"a": 1}')

        file_utils.write_atomically(target, '{"a": 2}', backup=True)

        assert json.loads(file_utils.backup_path(target).read_text()) == {"a": 1}

    def test_corrupt_file_does_not_replace_good_backup(self, tmp_path):
        target = tmp_path / "plan.json"
        file_utils.backup_path(target).write_text('{"a": 1}')
        target.write_text('{"a": ')  # half-written

        file_utils.write_atomically(target, '{"a": 3}', backup=True)

        assert json.loads(file_utils.backup_path(target).read_text()) == {"a": 1}

    def test_keeps_file_permissions(self, tmp_path):
        target = tmp_path / "plan.json"
        target.write_text('{}')
        os.chmod(target, 0o640)

        file_utils.write_atomically(target, '{"a": 1}')

        assert target.stat().st_mode & 0o777 == 0o640


class TestPlanStorage:

    def test_save_keeps_backup_and_listing_ignores_it(self, saved_plan, plans_dir):
        saved_plan.total = 20000
        plan_storage.save_plan(saved_plan)

        name = saved_plan.source_file.name
        assert saved_files(plans_dir) == [name, name + ".bak"]
        assert len(plan_storage.list_saved_plans()) == 1
        assert json.loads((plans_dir / (name + ".bak")).read_text())['total'] == 10000

    def test_load_error_mentions_backup(self, saved_plan):
        plan_storage.save_plan(saved_plan)
        saved_plan.source_file.write_text('{"name": ')

        with pytest.raises(ValueError, match=r"previous version is in .*\.json\.bak"):
            plan_storage.load_plan(saved_plan.source_file)

    def test_delete_removes_backup(self, saved_plan, plans_dir):
        plan_storage.save_plan(saved_plan)

        plan_storage.delete_plan(saved_plan.source_file)

        assert saved_files(plans_dir) == []

    def test_preferences_saved_atomically(self, tmp_path, monkeypatch):
        prefs = tmp_path / "preferences.json"
        monkeypatch.setattr(user_preferences, 'get_preferences_file', lambda: prefs)
        monkeypatch.setattr(user_preferences, 'ensure_preferences_directory', lambda: None)
        calls = []
        real = file_utils.write_atomically
        monkeypatch.setattr(user_preferences, 'write_atomically',
                            lambda *a, **k: calls.append(a) or real(*a, **k))

        user_preferences.save_preferences({'x': 1})

        assert calls and json.loads(prefs.read_text()) == {'x': 1}


class TestUnsavedChanges:
    """Plan.has_unsaved_changes()"""

    def test_new_plan_is_unsaved(self):
        assert plan.Plan(total=1000, daily=100, time=10).has_unsaved_changes()

    def test_saved_and_loaded_plans_are_clean(self, saved_plan):
        assert not saved_plan.has_unsaved_changes()
        assert not plan_storage.load_plan(saved_plan.source_file).has_unsaved_changes()

    def test_change_is_noticed(self, saved_plan):
        saved_plan.record_progress(datetime(2026, 11, 2), 500)

        assert saved_plan.has_unsaved_changes()

    def test_undoing_a_change_is_clean(self, saved_plan):
        saved_plan.total = 20000
        saved_plan.total = 10000

        assert not saved_plan.has_unsaved_changes()

    def test_automatic_locking_and_sync_are_not_changes(self, saved_plan):
        saved_plan.lock_past_goals(datetime(2026, 11, 6))
        saved_plan.daily = 999.9999
        saved_plan.sync_daily()

        assert not saved_plan.has_unsaved_changes()


class TestLeavingAPlan:
    """S1: "Go back to main menu" asks when there are unsaved changes."""

    def test_clean_plan_leaves_without_asking(self, saved_plan, scripted_input):
        scripted_input(["0"])

        quiet(planea.handle_plan_actions, saved_plan)

    def test_go_back_without_saving(self, saved_plan, scripted_input):
        saved_plan.total = 20000
        scripted_input(["0", "2"])

        quiet(planea.handle_plan_actions, saved_plan)

        assert plan_storage.load_plan(saved_plan.source_file).total == 10000

    def test_save_and_go_back(self, saved_plan, scripted_input):
        saved_plan.total = 20000
        scripted_input(["0", "1", "1"])  # back, save, overwrite the original

        quiet(planea.handle_plan_actions, saved_plan)

        assert plan_storage.load_plan(saved_plan.source_file).total == 20000

    def test_stay(self, saved_plan, scripted_input):
        saved_plan.total = 20000
        scripted_input(["0", "0", "0", "2"])  # back, stay; back, discard

        quiet(planea.handle_plan_actions, saved_plan)

    def test_cancelled_save_stays(self, saved_plan, scripted_input):
        saved_plan.total = 20000
        scripted_input(["0", "1", "0", "0", "2"])  # back, save, cancel; back, discard

        quiet(planea.handle_plan_actions, saved_plan)


class TestInterrupts:
    """S1: Ctrl+C and Ctrl+D end the program without losing work."""

    @pytest.fixture
    def run_main(self, monkeypatch):
        """Run planea.main() with answers; an exception instance is raised instead of answered."""
        def _run(answers):
            remaining = iter(answers)

            def fake_input(prompt=""):
                answer = next(remaining, EOFError())
                if isinstance(answer, BaseException):
                    raise answer
                return answer
            monkeypatch.setattr('builtins.input', fake_input)
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                planea.main()
            return out.getvalue()
        return _run

    @pytest.fixture
    def open_plan(self, saved_plan, monkeypatch):
        """Main menu option 3 opens saved_plan."""
        monkeypatch.setattr(planea, 'load_saved_plan', lambda: saved_plan)
        return saved_plan

    def test_ctrl_c_in_main_menu_exits_cleanly(self, plans_dir, run_main):
        output = run_main([KeyboardInterrupt()])

        assert "Happy writing" in output

    def test_ctrl_c_offers_to_save(self, open_plan, run_main):
        # Open the plan, modify it (menu 4 -> 1 change total), then Ctrl+C
        open_plan.total = 20000
        run_main(["3", KeyboardInterrupt(), "y", "1"])  # save, overwrite

        assert plan_storage.load_plan(open_plan.source_file).total == 20000

    def test_ctrl_c_and_decline(self, open_plan, plans_dir, run_main):
        open_plan.total = 20000
        run_main(["3", KeyboardInterrupt(), "n"])

        assert plan_storage.load_plan(open_plan.source_file).total == 10000
        assert len(plan_storage.list_saved_plans()) == 1

    def test_end_of_input_saves_recovery_copy(self, open_plan, plans_dir, run_main):
        open_plan.total = 20000

        output = run_main(["3"])  # then input ends

        assert plan_storage.load_plan(open_plan.source_file).total == 10000
        plans = {p['name']: p for p in plan_storage.list_saved_plans()}
        assert set(plans) == {"Novel", "Novel (recovered)"}
        assert plan_storage.load_plan(plans["Novel (recovered)"]['path']).total == 20000
        assert "Unsaved changes kept" in output

    def test_no_changes_nothing_asked(self, open_plan, plans_dir, run_main):
        run_main(["3"])

        assert len(plan_storage.list_saved_plans()) == 1

    def test_input_helpers_do_not_loop_on_end_of_input(self, monkeypatch):
        # They used to catch EOFError as "Unexpected error" and ask again forever
        def no_input(prompt=""):
            raise EOFError
        monkeypatch.setattr('builtins.input', no_input)

        for helper, args in [(ui_utils.get_positive_number, ("n: ",)),
                             (ui_utils.get_menu_choice, ("c: ", 0, 3))]:
            with pytest.raises(EOFError):
                quiet(helper, *args)


class TestSaveAfterProgress:
    """S6: one question, not two."""

    @freeze_time("2026-11-04 10:00")
    def test_progress_save_asks_once(self, saved_plan, scripted_input):
        # quick entry 500, decline the "behind" offer, done, save, overwrite
        scripted_input(["1", "500", "n", "0", "y", "1"])

        quiet(planea.update_progress, saved_plan)

        assert plan_storage.load_plan(saved_plan.source_file).progress == {'2026-11-04': 500}
        assert not saved_plan.has_unsaved_changes()
