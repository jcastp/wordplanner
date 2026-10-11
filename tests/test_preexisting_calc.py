"""Tests for pre-existing words in the plan creation flows.

These drive the real interactive functions in planea.py with scripted answers,
and capture the plan that would be handed to the plan actions menu.
"""

import copy
import pytest
from datetime import datetime
import ui_plan_actions
import plan_templates
import ui_create


# Far-future date so get_date_input() never asks about past dates
START_STR = "2099-01-05"
START = datetime(2099, 1, 5)


@pytest.fixture
def created_plans(monkeypatch):
    """Capture plans passed to handle_plan_actions instead of opening the menu."""
    plans = []
    monkeypatch.setattr(ui_plan_actions, "handle_plan_actions", plans.append)
    return plans


@pytest.fixture
def isolated_templates(monkeypatch):
    """The template flow mutates template objects; give each test its own copies."""
    monkeypatch.setattr(plan_templates, "TEMPLATES", copy.deepcopy(plan_templates.TEMPLATES))


class TestCreateNewPlanWithPreExistingWords:
    """ui_create.create_new_plan() for each calculation method."""

    def test_calculate_time(self, scripted_input, created_plans):
        # Goal 80,000, 32,000 already written, 1,000/day -> 48 days
        scripted_input([
            "1",          # calculate days needed
            "80000",      # total goal
            "y",          # already written some words?
            "32000",      # how many
            "y",          # confirm
            "1000",       # daily capacity
            "n",          # variable pattern?
            START_STR,    # start date
            "n",          # weekend settings?
        ])

        ui_create.create_new_plan()

        [p] = created_plans
        assert p.time == pytest.approx(48)
        assert p.daily == 1000
        assert p.total == 80000
        assert p.preexisting_words == 32000
        assert p.progress == {}
        assert p.get_remaining_words() == 48000
        assert p.get_completion_percentage() == pytest.approx(40.0)

    def test_calculate_total_words(self, scripted_input, created_plans):
        # 500/day for 60 days plus 5,000 already written -> goal 35,000
        scripted_input([
            "2",          # calculate total words
            "500",        # daily capacity
            "60",         # days available
            "y",          # already written some words?
            "5000",       # how many
            "y",          # confirm
            "n",          # variable pattern?
            START_STR,
            "n",          # weekend settings?
        ])

        ui_create.create_new_plan()

        [p] = created_plans
        assert p.total == 35000
        assert p.daily == 500
        assert p.time == 60
        assert p.preexisting_words == 5000
        assert p.progress == {}
        assert p.get_remaining_words() == 30000

    def test_calculate_daily_words(self, scripted_input, created_plans):
        # Goal 50,000, 10,000 already written, 40 days -> 1,000/day
        scripted_input([
            "3",          # calculate daily words
            "50000",      # total goal
            "y",          # already written some words?
            "10000",      # how many
            "y",          # confirm
            "40",         # days available
            "n",          # variable pattern?
            START_STR,
            "n",          # weekend settings?
        ])

        ui_create.create_new_plan()

        [p] = created_plans
        assert p.daily == pytest.approx(1000)
        assert p.total == 50000
        assert p.time == 40
        assert p.preexisting_words == 10000
        assert p.progress == {}

    def test_no_pre_existing_words(self, scripted_input, created_plans):
        scripted_input([
            "3",
            "50000",
            "n",          # already written some words?
            "40",
            "n",
            START_STR,
            "n",
        ])

        ui_create.create_new_plan()

        [p] = created_plans
        assert p.daily == pytest.approx(1250)
        assert p.progress == {}

    def test_pre_existing_equal_to_goal_creates_no_plan(self, scripted_input, created_plans):
        scripted_input([
            "1",
            "10000",      # total goal
            "y",          # already written some words?
            "10000",      # how many (equals goal)
            "y",          # continue anyway?
            "1000",       # daily capacity
            "",           # "Press Enter to continue"
        ])

        ui_create.create_new_plan()

        assert created_plans == []


class TestCreateFromTemplateWithPreExistingWords:
    """ui_create.create_plan_from_template() with pre-existing words."""

    def test_nanowrimo_with_pre_existing(self, scripted_input, created_plans, isolated_templates):
        # NaNoWriMo: 50,000 words / 30 days, 10,000 already written
        scripted_input([
            "1",          # NaNoWriMo (first template listed)
            "y",          # use as-is
            "y",          # already written some words?
            "10000",      # how many
            "y",          # confirm
            START_STR,
            "y",          # apply suggested 'flat' pattern
            "n",          # configure suggested weekend settings
        ])

        ui_create.create_plan_from_template()

        [p] = created_plans
        assert p.name == "NaNoWriMo"
        assert p.total == 50000
        assert p.time == 30
        assert p.daily == pytest.approx(40000 / 30)
        assert p.preexisting_words == 10000
        assert p.progress == {}
        assert p.get_remaining_words() == 40000
