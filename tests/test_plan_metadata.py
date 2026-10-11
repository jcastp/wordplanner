"""Tests for last_modified and is_active staying right (issues-program.org S3).

- Saving updates last_modified when the plan changed (or a new file is
  created); saving an unchanged plan leaves it alone.
- "Save as a new file" never gives two active plans.
"""

import contextlib
import io
import pytest
from datetime import datetime
from freezegun import freeze_time
import plan
import plan_manager
import plan_storage
import planea


CREATED = datetime(2026, 10, 1, 9, 0)
LATER = datetime(2026, 10, 5, 18, 30)


def make_plan(name="Novel"):
    return plan.Plan(name=name, total=10000, daily=1000, time=10, start_date=datetime(2026, 11, 2))


@pytest.fixture
def saved_plan():
    with freeze_time(CREATED):
        p = make_plan()
        plan_storage.save_plan(p)
    return p


def stored(p):
    return plan_storage.load_plan(p.source_file)


class TestLastModified:

    def test_first_save_sets_it(self, saved_plan):
        assert stored(saved_plan).last_modified == CREATED

    @freeze_time(LATER)
    def test_changed_plan_updates_it(self, saved_plan):
        # Used to keep CREATED: only plan-manager actions updated it
        saved_plan.record_progress(datetime(2026, 11, 2), 900)

        plan_storage.save_plan(saved_plan)

        assert stored(saved_plan).last_modified == LATER

    @freeze_time(LATER)
    def test_unchanged_plan_keeps_it(self, saved_plan):
        loaded = stored(saved_plan)

        plan_storage.save_plan(loaded)

        assert stored(saved_plan).last_modified == CREATED

    @freeze_time(LATER)
    def test_sort_by_modified_follows_edits(self, saved_plan):
        with freeze_time(CREATED.replace(day=3)):
            other = make_plan("Other")
            plan_storage.save_plan(other)
        saved_plan.total = 12000
        plan_storage.save_plan(saved_plan)

        newest_first = plan_manager.sort_plans(plan_manager.get_all_plans(), "modified")

        assert [p.name for p in newest_first] == ["Novel", "Other"]

    @freeze_time(LATER)
    def test_failed_save_restores_it(self, saved_plan, monkeypatch):
        def broken(*args, **kwargs):
            raise OSError("disk full")
        monkeypatch.setattr(plan_storage, 'write_atomically', broken)
        saved_plan.total = 12000

        with pytest.raises(OSError):
            plan_storage.save_plan(saved_plan)

        assert saved_plan.last_modified == CREATED


class TestSaveAsNewCopy:

    @pytest.fixture
    def active_plan(self, saved_plan):
        plan_manager.set_active_plan(saved_plan.source_file)
        return stored(saved_plan)

    def test_copy_is_not_active(self, active_plan):
        original_path = active_plan.source_file

        plan_storage.save_plan(active_plan, overwrite_source=False)

        assert active_plan.source_file != original_path
        assert not active_plan.is_active
        assert plan_storage.load_plan(original_path).is_active
        actives = [p for p in plan_manager.get_all_plans() if p.is_active]
        assert len(actives) == 1

    def test_copy_keeps_status_and_tags(self, active_plan):
        active_plan.tags = ["draft"]

        plan_storage.save_plan(active_plan, overwrite_source=False)

        assert stored(active_plan).tags == ["draft"]

    def test_first_save_of_an_active_plan_keeps_it(self):
        p = make_plan()
        p.is_active = True

        plan_storage.save_plan(p)

        assert stored(p).is_active

    def test_failed_copy_restores_the_plan(self, active_plan, monkeypatch):
        original_path = active_plan.source_file
        monkeypatch.setattr(plan_storage, 'write_atomically',
                            lambda *a, **k: (_ for _ in ()).throw(OSError("disk full")))

        with pytest.raises(OSError):
            plan_storage.save_plan(active_plan, overwrite_source=False)

        assert active_plan.source_file == original_path
        assert active_plan.is_active

    def test_save_prompt_says_the_original_stays_active(self, active_plan, scripted_input):
        scripted_input(["2", "y"])  # save as new file, keep the name
        out = io.StringIO()

        with contextlib.redirect_stdout(out):
            assert planea.save_plan_prompt(active_plan, ask=False)

        assert "The original stays your active plan" in out.getvalue()
