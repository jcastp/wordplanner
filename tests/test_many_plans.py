"""Tests for loading many plans (issues-program.org S5).

Every plan-manager operation reads each plan file once, and an unreadable
file is reported once per session instead of on every listing.
"""

import contextlib
import io
import os
import pytest
from datetime import datetime
import plan
import plan_manager
import plan_manager_ui
import plan_storage


N = 5


@pytest.fixture
def plans():
    saved = []
    for n in range(N):
        p = plan.Plan(name=f"Plan {n}", total=10000, daily=1000, time=10,
                      start_date=datetime(2026, 11, 2), tags=[f"tag{n % 2}"])
        plan_storage.save_plan(p)
        saved.append(p)
    return saved


@pytest.fixture
def count_loads(monkeypatch):
    """Count plan_storage.load_plan() calls."""
    calls = []
    real = plan_storage.load_plan

    def counting(filepath):
        calls.append(filepath)
        return real(filepath)
    monkeypatch.setattr(plan_storage, 'load_plan', counting)
    return calls


@pytest.fixture(autouse=True)
def fresh_error_reports(monkeypatch):
    monkeypatch.setattr(plan_storage, '_reported_load_errors', set())


def quiet(func, *args):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        result = func(*args)
    return result, out.getvalue()


class TestEachFileReadOnce:

    @pytest.mark.parametrize("operation", [
        plan_manager.get_all_plans,
        plan_manager.get_plans_by_status,
        plan_manager.get_active_plan,
        plan_manager.get_all_tags,
        plan_manager.get_all_categories,
        plan_manager.get_plan_statistics,
        plan_storage.list_saved_plans,
        plan_manager.clear_active_plan,
    ])
    def test_operation(self, plans, count_loads, operation):
        # Statistics used to read every file about 12 times
        operation()

        assert len(count_loads) == N

    def test_set_active_plan(self, plans, count_loads):
        plan_manager.set_active_plan(plans[2].source_file)

        assert len(count_loads) == N
        assert [p.name for p in plan_manager.get_all_plans() if p.is_active] == ["Plan 2"]

    def test_switching_saves_only_the_two_changed_plans(self, plans, monkeypatch):
        plan_manager.set_active_plan(plans[0].source_file)
        saved = []
        real_save = plan_storage.save_plan
        monkeypatch.setattr(plan_storage, 'save_plan',
                            lambda p, **kw: saved.append(p.name) or real_save(p, **kw))

        plan_manager.set_active_plan(plans[3].source_file)

        assert sorted(saved) == ["Plan 0", "Plan 3"]

    def test_overview_screen(self, plans, count_loads):
        quiet(plan_manager_ui.display_plans_overview)

        assert len(count_loads) == N

    def test_tags_screen(self, plans, count_loads, monkeypatch):
        monkeypatch.setattr('builtins.input', lambda prompt="": "")

        _, output = quiet(plan_manager_ui.view_all_tags_ui)

        # Used to reload every plan once per tag
        assert len(count_loads) == N
        assert "tag0 (3 plans)" in output


class TestBrokenFiles:

    @pytest.fixture
    def broken(self, plans):
        path = plan_storage.get_plans_directory() / "broken.json"
        path.write_text('{"name": ')
        return path

    def test_reported_once(self, broken):
        _, first = quiet(plan_manager.get_plan_statistics)
        _, second = quiet(plan_manager.get_all_plans)

        assert first.count("Could not load broken.json") == 1
        assert "broken.json" not in second

    def test_reported_again_when_the_file_changes(self, broken):
        quiet(plan_manager.get_all_plans)
        broken.write_text('{"name": "still broken"')
        os.utime(broken, ns=(1, 1))

        _, output = quiet(plan_manager.get_all_plans)

        assert "Could not load broken.json" in output

    def test_other_plans_still_listed(self, broken):
        loaded, _ = quiet(plan_manager.get_all_plans)

        assert len(loaded) == N
