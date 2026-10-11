"""Tests for creating plans from templates (issues-program.org P16).

- Customising a template never changes the shared TEMPLATES.
- The pattern intensity chosen in the template flow is applied (it used to be
  stored as {'intensity': ...}, which the pattern code ignores).
"""

import contextlib
import io
import pytest
from datetime import datetime
from freezegun import freeze_time
import plan_templates
import planea


def template_number(key):
    """Menu number of a template in create_plan_from_template()."""
    keys = [k for ks in plan_templates.list_templates_by_category().values() for k in ks]
    return str(keys.index(key) + 1)


@pytest.fixture
def run_template_flow(monkeypatch, scripted_input):
    """Run the template flow with answers and return the plan it creates."""
    def _run(answers):
        created = []
        monkeypatch.setattr(planea, 'handle_plan_actions', created.append)
        scripted_input(answers)
        with contextlib.redirect_stdout(io.StringIO()):
            planea.create_plan_from_template()
        return created[0]
    return _run


class TestTemplatesAreNotShared:

    def test_get_all_templates_returns_copies(self):
        plan_templates.get_all_templates()['nanowrimo'].total = 1

        assert plan_templates.get_template('nanowrimo').total == 50000
        assert plan_templates.TEMPLATES['nanowrimo'].total == 50000

    def test_get_template_returns_a_copy(self):
        plan_templates.get_template('nanowrimo').time = 3

        assert plan_templates.TEMPLATES['nanowrimo'].time == 30

    @freeze_time("2026-10-01")
    def test_customised_flow_leaves_template_alone(self, run_template_flow):
        answers = [
            template_number('nanowrimo'),
            "n",            # not as-is
            "y", "40000",   # change total
            "y", "20",      # change duration
            "y", "5000", "y",  # pre-existing words, confirmed
            "2026-11-02",   # start date
            "y",            # suggested flat pattern
            "n",            # suggested weekend settings
        ]

        first = run_template_flow(answers)
        second = run_template_flow([template_number('nanowrimo'), "y", "n", "2026-11-02", "y", "n"])

        assert (first.total, first.time, first.preexisting_words) == (40000, 20, 5000)
        assert first.daily == pytest.approx(35000 / 20)
        assert (second.total, second.time, second.preexisting_words) == (50000, 30, 0)
        assert plan_templates.TEMPLATES['nanowrimo'].total == 50000


@freeze_time("2026-10-01")
class TestTemplatePatternIntensity:
    """Short Story suggests a rising pattern."""

    def flow(self, intensity):
        return [
            template_number('short_story'),
            "y",              # as-is
            "n",              # no pre-existing words
            "2026-11-02",     # start date
            "y", intensity,   # suggested rising pattern, intensity
            "n",              # suggested weekend settings
        ]

    @pytest.mark.parametrize("intensity, config", [
        ("1", {'start_multiplier': 0.8, 'end_multiplier': 1.2}),
        ("2", {'start_multiplier': 0.5, 'end_multiplier': 1.5}),
        ("3", {'start_multiplier': 0.3, 'end_multiplier': 2.0}),
    ])
    def test_intensity_is_stored_as_multipliers(self, run_template_flow, intensity, config):
        p = run_template_flow(self.flow(intensity))

        assert p.pattern == 'rising'
        assert p.pattern_config == config

    def test_intensity_changes_the_goals(self, run_template_flow):
        mild = run_template_flow(self.flow("1"))
        extreme = run_template_flow(self.flow("3"))

        def spread(p):
            goals = [p.get_daily_goal(date=d) for d in p.plan_days()]
            return max(goals) / min(goals)

        assert spread(mild) == pytest.approx(1.5)
        assert spread(extreme) > 6
        assert sum(mild.get_daily_goal(date=d) for d in mild.plan_days()) == pytest.approx(5000)
