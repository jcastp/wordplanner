"""Tests for the plan manager screens (issues-program.org T4).

Each test drives a screen of plan_manager_ui with scripted answers and checks
what it shows and what it saved. Plans are listed in file name order, which
for these fixtures is the order of their names.
"""

import contextlib
import io
import pytest
from datetime import datetime, timedelta
from freezegun import freeze_time
import plan
import plan_manager
import plan_manager_ui
import plan_storage


MON = datetime(2026, 11, 2)


@pytest.fixture
def plans():
    """Alpha (current, novel, with progress), Beta (tagged), Gamma (archived)."""
    alpha = plan.Plan(name="Alpha", total=10000, daily=1000, time=10, start_date=MON,
                      category="novel", tags=["draft"], is_active=True)
    alpha.record_progress(MON, 1500)
    alpha.record_progress(MON + timedelta(days=1), 1500)
    beta = plan.Plan(name="Beta", total=20000, daily=1000, time=20, start_date=MON,
                     tags=["draft", "sci-fi"])
    gamma = plan.Plan(name="Gamma", total=5000, daily=500, time=10, status="archived")
    for p in (alpha, beta, gamma):
        plan_storage.save_plan(p)
    return alpha, beta, gamma


def saved(name):
    """The plan called name, as it is on disk now."""
    return next(p for p in plan_manager.get_all_plans() if p.name == name)


def run(func, *args):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        result = func(*args)
    return result, out.getvalue()


@freeze_time("2026-11-04")
class TestOverviewAndStatistics:

    def test_overview_groups_plans_by_status(self, plans, scripted_input):
        scripted_input(["1", "", "0"])   # overview, Enter, back

        _, output = run(plan_manager_ui.manage_plans_menu)

        assert "Total Plans: 3" in output
        assert "Active: 2 | Archived: 1 | Completed: 0" in output
        assert "★ Current plan: Alpha" in output
        assert "Active Plans (2)" in output and "Archived Plans (1)" in output
        assert "[novel]" in output and "Tags: draft, sci-fi" in output
        # Alpha wrote 3,000 by the 2nd day; 2,000 were due by yesterday
        assert "Progress: 30% complete, ✓ ahead" in output
        assert "Not started yet (starts 2026-11-02)" in output

    def test_statistics(self, plans, scripted_input):
        scripted_input(["8", "", "0"])

        _, output = run(plan_manager_ui.manage_plans_menu)

        assert "Total word goal: 35,000 words" in output
        assert "Total words written: 3,000 words" in output
        assert "Plans with progress: 1" in output
        assert "novel: 1 plans" in output
        assert "draft, sci-fi" in output
        assert "★ Alpha" in output

    def test_statistics_without_plans(self, scripted_input):
        scripted_input([""])

        _, output = run(plan_manager_ui.display_plan_statistics)

        assert "Total Plans: 0" in output
        assert "Current plan:" not in output


class TestFilterAndSort:

    @pytest.mark.parametrize("status, shown, hidden", [
        ("1", ["Alpha", "Beta"], ["Gamma"]),
        ("2", ["Gamma"], ["Alpha", "Beta"]),
    ])
    def test_filter_by_status(self, plans, scripted_input, status, shown, hidden):
        scripted_input(["2", "1", status, "", "0"])

        _, output = run(plan_manager_ui.manage_plans_menu)

        for name in shown:
            assert f". {name}" in output
        for name in hidden:
            assert f". {name}" not in output

    def test_filter_by_status_none_found(self, plans, scripted_input):
        scripted_input(["3", ""])   # completed

        _, output = run(plan_manager_ui.filter_by_status_ui)

        assert "No completed plans found." in output

    def test_filter_by_category(self, plans, scripted_input):
        scripted_input(["2", "1", ""])   # filter by category, "novel"

        _, output = run(plan_manager_ui.filter_and_sort_menu)

        assert "1. novel (1 plans)" in output
        assert "Plans in category 'novel' (1)" in output
        assert "1. Alpha" in output and "Beta" not in output

    def test_filter_by_tag(self, plans, scripted_input):
        scripted_input(["3", "2", ""])   # filter by tag, "sci-fi"

        _, output = run(plan_manager_ui.filter_and_sort_menu)

        assert "Plans with tag 'sci-fi' (1)" in output
        assert "1. Beta" in output and "Tags: draft, sci-fi" in output

    @pytest.mark.parametrize("screen, message", [
        (plan_manager_ui.filter_by_category_ui, "No categories found"),
        (plan_manager_ui.filter_by_tag_ui, "No tags found"),
    ])
    def test_filters_without_plans(self, scripted_input, screen, message):
        scripted_input([""])

        _, output = run(screen)

        assert message in output

    @pytest.mark.parametrize("sort_choice, expected", [
        ("1", "Status: active"),          # name
        ("2", "Created: "),               # created
        ("3", "Last modified: "),         # modified
        ("4", "30% complete | 3,000 / 10,000 words"),
        ("5", "Deadline: 2026-11-11"),    # Alpha: 10 days from Nov 2
    ])
    def test_sort_shows_the_sort_key(self, plans, scripted_input, sort_choice, expected):
        scripted_input([sort_choice, ""])

        _, output = run(plan_manager_ui.sort_plans_ui)

        assert expected in output
        assert output.count(". Alpha") == 1

    def test_sort_by_deadline_puts_undated_plans_last(self, plans, scripted_input):
        scripted_input(["5", ""])

        _, output = run(plan_manager_ui.sort_plans_ui)

        assert "No deadline set | 5,000 words" in output


class TestSearchAndCompare:

    def test_search(self, plans, scripted_input):
        scripted_input(["3", "sci", "", "0"])

        _, output = run(plan_manager_ui.manage_plans_menu)

        assert "Search results for 'sci' (1 found)" in output
        assert "1. Beta" in output

    def test_search_without_match_or_query(self, plans, scripted_input):
        scripted_input(["nothing-like-this", ""])
        _, output = run(plan_manager_ui.search_plans_ui)
        assert "No matching plans found." in output

        scripted_input([""])
        _, output = run(plan_manager_ui.search_plans_ui)
        assert "Search results" not in output

    def test_compare_two_plans(self, plans, scripted_input):
        scripted_input(["4", "1, 2", "", "0"])

        _, output = run(plan_manager_ui.manage_plans_menu)

        assert "PLAN COMPARISON" in output
        assert "★ Alpha" in output and "Beta" in output
        assert "Combined word goal: 30,000 words" in output
        assert "Combined days: 30 days" in output

    @pytest.mark.parametrize("selection, message", [
        ("1", "Please select at least 2 plans."),
        ("1, 9", "Please select at least 2 plans."),   # out of range is dropped
        ("one, two", "Invalid selection."),
    ])
    def test_compare_bad_selection(self, plans, scripted_input, selection, message):
        scripted_input([selection, ""])

        _, output = run(plan_manager_ui.compare_plans_ui)

        assert message in output
        assert "PLAN COMPARISON" not in output

    def test_compare_needs_two_plans(self, scripted_input):
        plan_storage.save_plan(plan.Plan(name="Only", total=1000, daily=100, time=10))
        scripted_input([""])

        _, output = run(plan_manager_ui.compare_plans_ui)

        assert "at least 2 plans" in output


class TestCurrentPlan:

    def test_set_current_plan(self, plans, scripted_input):
        scripted_input(["5", "2", "", "0"])

        _, output = run(plan_manager_ui.manage_plans_menu)

        assert "'Beta' is now the current plan." in output
        assert saved("Beta").is_active and not saved("Alpha").is_active

    def test_clear_current_plan(self, plans, scripted_input):
        scripted_input(["0", "y", ""])

        _, output = run(plan_manager_ui.set_active_plan_ui)

        assert "No plan is the current plan now." in output
        assert plan_manager.get_active_plan() is None

    def test_no_plans(self, scripted_input):
        scripted_input([""])

        _, output = run(plan_manager_ui.set_active_plan_ui)

        assert "No plans available." in output


class TestTagsAndCategories:

    def test_set_category(self, plans, scripted_input):
        scripted_input(["6", "1", "2", "2", "", "0"])   # Beta -> short-story

        _, output = run(plan_manager_ui.manage_plans_menu)

        assert "Category set to 'short-story'." in output
        assert saved("Beta").category == "short-story"

    def test_remove_category(self, plans, scripted_input):
        scripted_input(["1", "0", ""])   # Alpha -> remove category

        _, output = run(plan_manager_ui.set_plan_category_ui)

        assert "Category removed." in output
        assert saved("Alpha").category is None

    def test_add_tags(self, plans, scripted_input):
        scripted_input(["2", "3", " revision, ,  summer ", ""])   # Gamma

        _, output = run(plan_manager_ui.manage_tags_categories_menu)

        assert "Added 2 tag(s)." in output
        assert saved("Gamma").tags == ["revision", "summer"]

    def test_tags_are_lowercased_and_not_duplicated(self, plans, scripted_input):
        scripted_input(["1", "DRAFT, Rewrite, rewrite", ""])

        _, output = run(plan_manager_ui.add_tags_ui)

        assert saved("Alpha").tags == ["draft", "rewrite"]
        assert "Added 1 tag(s)." in output
        assert "Already tagged: draft" in output

    def test_adding_only_existing_tags_adds_nothing(self, plans, scripted_input):
        # Used to say "Added 1 tag(s)."
        scripted_input(["1", "draft", ""])

        _, output = run(plan_manager_ui.add_tags_ui)

        assert "Added" not in output and "Failed" not in output
        assert "Already tagged: draft" in output
        assert saved("Alpha").tags == ["draft"]

    def test_add_tag_reports_whether_it_added(self):
        p = plan.Plan(name="Tags", total=1000, daily=100, time=10, tags=["old"])
        plan_storage.save_plan(p)

        assert plan_manager.add_tag_to_plan(p, " New ") is True
        assert plan_manager.add_tag_to_plan(p, "new") is False
        assert plan_manager.add_tag_to_plan(p, "  ") is False
        assert p.tags == ["old", "new"]

    def test_failed_save_is_reported(self, plans, scripted_input, monkeypatch):
        def broken(*args, **kwargs):
            raise OSError("disk full")
        monkeypatch.setattr(plan_storage, 'save_plan', broken)
        scripted_input(["3", "fresh", ""])   # Gamma

        _, output = run(plan_manager_ui.add_tags_ui)

        assert "Error adding tag: disk full" in output
        assert "Failed to add tags." in output

    def test_remove_tag(self, plans, scripted_input):
        scripted_input(["3", "2", "1", ""])   # Beta, remove "draft"

        _, output = run(plan_manager_ui.manage_tags_categories_menu)

        assert "Tag 'draft' removed." in output
        assert saved("Beta").tags == ["sci-fi"]

    def test_remove_tag_from_untagged_plan(self, plans, scripted_input):
        scripted_input(["3", ""])   # Gamma has no tags

        _, output = run(plan_manager_ui.remove_tags_ui)

        assert "This plan has no tags." in output

    def test_view_tags_and_categories(self, plans, scripted_input):
        scripted_input(["4", ""])
        _, output = run(plan_manager_ui.manage_tags_categories_menu)
        assert "Total unique tags: 2" in output
        assert "1. draft (2 plans)" in output

        scripted_input(["5", ""])
        _, output = run(plan_manager_ui.manage_tags_categories_menu)
        assert "• novel: 1 plans" in output
        assert "Full-length novel" in output

    @pytest.mark.parametrize("screen", [
        plan_manager_ui.set_plan_category_ui,
        plan_manager_ui.add_tags_ui,
        plan_manager_ui.remove_tags_ui,
    ])
    def test_screens_without_plans(self, scripted_input, screen):
        scripted_input([""])

        _, output = run(screen)

        assert "No plans available." in output


class TestArchiveAndComplete:

    def test_archive(self, plans, scripted_input):
        scripted_input(["7", "1", "1", "y", "", "0"])   # archive Alpha

        _, output = run(plan_manager_ui.manage_plans_menu)

        assert "'Alpha' archived." in output
        archived = saved("Alpha")
        assert archived.status == "archived" and not archived.is_active

    def test_archive_needs_confirmation(self, plans, scripted_input):
        scripted_input(["2", "n", ""])

        run(plan_manager_ui.archive_plan_ui)

        assert saved("Beta").status == "active"

    def test_unarchive(self, plans, scripted_input):
        scripted_input(["2", "1", "y", ""])   # unarchive Gamma

        _, output = run(plan_manager_ui.archive_unarchive_menu)

        assert "'Gamma' unarchived." in output
        assert saved("Gamma").status == "active"

    def test_mark_completed(self, plans, scripted_input):
        scripted_input(["3", "1", "y", ""])   # Alpha

        _, output = run(plan_manager_ui.archive_unarchive_menu)

        assert "Alpha (30% complete)" in output
        assert "'Alpha' marked as completed!" in output
        assert saved("Alpha").status == "completed"

    def test_nothing_to_archive_unarchive_or_complete(self, scripted_input):
        done = plan.Plan(name="Done", total=1000, daily=100, time=10, status="completed")
        plan_storage.save_plan(done)

        for screen, message in [
            (plan_manager_ui.archive_plan_ui, "No active plans to archive."),
            (plan_manager_ui.unarchive_plan_ui, "No archived plans to unarchive."),
            (plan_manager_ui.mark_completed_ui, "All plans are already completed."),
        ]:
            scripted_input([""])
            _, output = run(screen)
            assert message in output


class TestGoBack:

    @pytest.mark.parametrize("screen", [
        plan_manager_ui.filter_and_sort_menu,
        plan_manager_ui.filter_by_status_ui,
        plan_manager_ui.filter_by_category_ui,
        plan_manager_ui.filter_by_tag_ui,
        plan_manager_ui.sort_plans_ui,
        plan_manager_ui.manage_tags_categories_menu,
        plan_manager_ui.set_plan_category_ui,
        plan_manager_ui.add_tags_ui,
        plan_manager_ui.remove_tags_ui,
        plan_manager_ui.archive_unarchive_menu,
        plan_manager_ui.archive_plan_ui,
        plan_manager_ui.unarchive_plan_ui,
        plan_manager_ui.mark_completed_ui,
        plan_manager_ui.open_plan_ui,
    ])
    def test_go_back_changes_nothing(self, plans, scripted_input, screen):
        before = {p.name: p.fingerprint() for p in plan_manager.get_all_plans()}
        scripted_input(["0"])

        run(screen)

        assert {p.name: p.fingerprint() for p in plan_manager.get_all_plans()} == before
