"""Tests for config.py being used, not decorative (issues-program.org Q2)."""

import contextlib
import io
import re
from datetime import datetime
from pathlib import Path
from freezegun import freeze_time
import config
import plan
import plan_manager_ui
import ui_create
import ui_modify
import ui_plan_actions


ROOT = Path(__file__).parent.parent


def run(func, *args):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        result = func(*args)
    return result, out.getvalue()


def test_every_constant_is_used():
    """A constant nobody reads is misleading: it looks like a setting but changes nothing."""
    source = "\n".join(path.read_text() for path in ROOT.glob("*.py") if path.name != "config.py")
    constants = [name for name in vars(config) if name.isupper()]

    unused = [name for name in constants if not re.search(rf"\bconfig\.{name}\b", source)]

    assert constants and unused == []


@freeze_time("2026-10-01")
class TestInputLimits:

    def test_total_above_max_words_is_refused(self, scripted_input, monkeypatch):
        opened = []
        monkeypatch.setattr(ui_plan_actions, 'handle_plan_actions', opened.append)
        # Calculate days: total (too big, then ok), no pre-existing, daily (too big, then ok),
        # no pattern, start date, no weekend settings
        scripted_input(["1", str(config.MAX_WORDS + 1), "50000", "n",
                        str(config.MAX_DAILY_WORDS + 1), "2000", "n", "2026-11-02", "n"])

        _, output = run(ui_create.create_new_plan)

        assert output.count("Value cannot exceed") == 2
        assert (opened[0].total, opened[0].time) == (50000, 25)

    def test_days_above_max_days_are_refused(self, scripted_input):
        p = plan.Plan(total=10000, daily=1000, time=10, start_date=datetime(2026, 11, 2))
        # Modify -> writing days -> too many, then 20 -> keep total (recalculate daily)
        scripted_input(["3", str(config.MAX_DAYS + 1), "20", "1"])

        _, output = run(ui_modify.modify_plan, p)

        assert "Value cannot exceed 36,500" in output
        assert p.time == 20


def test_sort_menu_comes_from_config(scripted_input, monkeypatch):
    monkeypatch.setattr(plan_manager_ui.plan_manager, 'get_all_plans', lambda: [])
    scripted_input(["0"])

    _, output = run(plan_manager_ui.sort_plans_ui)

    for number, description in enumerate(config.PLAN_SORT_OPTIONS.values(), 1):
        assert f"{number}. {description}" in output
