"""Tests for the progress screens and the analytics menu (issues-program.org T4).

The plan runs Mon 2 Nov - Wed 11 Nov 2026 at 1,000 words a day; the clock is
pinned inside it. Each test drives a screen with scripted answers and checks
the plan afterwards, not only what was printed.
"""

import contextlib
import io
import pytest
from datetime import datetime, timedelta
from freezegun import freeze_time
import plan
import plan_storage
import progress_analytics
import ui_files
import ui_plan_actions
import ui_progress


MON = datetime(2026, 11, 2)
TODAY = MON + timedelta(days=3)   # Thursday, 4th day of the plan


def make_plan(**kwargs):
    values = dict(name="Novel", total=10000, daily=1000, time=10, start_date=MON)
    values.update(kwargs)
    return plan.Plan(**values)


def with_progress(*words, **kwargs):
    """A plan with words logged on its first days."""
    p = make_plan(**kwargs)
    for i, count in enumerate(words):
        p.record_progress(MON + timedelta(days=i), count)
    return p


def run(func, *args):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        result = func(*args)
    return result, out.getvalue()


@freeze_time(TODAY)
class TestUpdateProgress:

    def test_quick_entry_logs_today(self, scripted_input):
        p = with_progress(1000, 1000, 1000)
        scripted_input(["1", "1200", "n", "0", "n"])   # today, 1,200 words; ahead: no; done; don't save

        _, output = run(ui_progress.update_progress, p)

        assert p.get_progress_for_date(TODAY) == 1200
        assert "Goal for today: 1,000 words" in output
        assert "You met your daily goal!" in output

    def test_quick_entry_short_of_goal(self, scripted_input):
        p = with_progress(1000, 1000, 1000)
        scripted_input(["1", "400", "n", "0", "n"])

        _, output = run(ui_progress.update_progress, p)

        assert "(600 words short of goal)" in output

    @pytest.mark.parametrize("answer, message", [
        ("-5", "Word count cannot be negative"),
        ("lots", "Invalid input. Please enter a number."),
        ("", None),   # Enter cancels
    ])
    def test_quick_entry_bad_answers_log_nothing(self, scripted_input, answer, message):
        p = with_progress(1000, 1000, 1000)
        scripted_input(["1", answer, "0"])

        _, output = run(ui_progress.update_progress, p)

        assert p.get_progress_for_date(TODAY) is None
        if message:
            assert message in output

    def test_entry_for_a_past_date_shows_existing_words(self, scripted_input):
        p = with_progress(1000, 300)
        scripted_input(["2", "2026-11-03", "800", "n", "0", "n"])   # behind: no

        _, output = run(ui_progress.update_progress, p)

        assert "Current progress: 300 words" in output
        assert p.get_progress_for_date(MON + timedelta(days=1)) == 800

    @pytest.mark.parametrize("answers, message", [
        (["2026-11-03", "-1"], "Word count cannot be negative"),
        (["03/11/2026"], "Invalid input"),
        (["2026-11-20"], "You can't log progress for a future date."),
        (["2026-11-03", ""], None),   # Enter cancels
        ([""], None),
    ])
    def test_date_entry_bad_answers_log_nothing(self, scripted_input, answers, message):
        p = make_plan()
        scripted_input(["2", *answers, "0"])

        _, output = run(ui_progress.update_progress, p)

        assert p.progress == {}
        if message:
            assert message in output

    def test_view_entries(self, scripted_input):
        p = with_progress(1200, 500)
        scripted_input(["3", "", "0"])

        _, output = run(ui_progress.update_progress, p)

        assert "✓ 2026-11-02 (Monday): 1,200 words (goal: 1,000)" in output
        assert "○ 2026-11-03 (Tuesday): 500 words (goal: 1,000)" in output

    def test_view_entries_when_there_are_none(self, scripted_input):
        scripted_input(["3", "", "0"])

        _, output = run(ui_progress.update_progress, make_plan())

        assert "No progress entries recorded yet" in output

    def test_offers_to_save_after_logging(self, scripted_input):
        p = with_progress(1000, 1000, 1000)
        scripted_input(["1", "0", "0", "y", "y"])   # log 0 (on track), done, save, keep name

        run(ui_progress.update_progress, p)

        assert p.source_file is not None and p.source_file.exists()
        assert plan_storage.load_plan(p.source_file).get_progress_for_date(TODAY) == 0

    def test_needs_a_start_date(self, scripted_input):
        scripted_input([""])

        _, output = run(ui_progress.update_progress, make_plan(start_date=None))

        assert "You must set a start date" in output


@freeze_time(TODAY)
class TestAheadBehindOffers:
    """Logging today's words compares the plan with what's due by yesterday."""

    def test_behind_increase_daily_goals(self, scripted_input):
        p = with_progress(500, 500, 500)
        # log 0 today -> behind; adjust; 1 = increase daily goals; apply; done
        scripted_input(["1", "0", "y", "1", "y", "0", "n"])

        _, output = run(ui_progress.update_progress, p)

        assert "You're BEHIND schedule" in output
        assert "Behind by: 1,500 words" in output
        # Today is locked (words logged) and credited with its goal (decision 9):
        # 10,000 - 1,500 written - 1,000 = 7,500 over the 6 days from tomorrow
        assert p.get_daily_goal(date=TODAY + timedelta(days=1)) == pytest.approx(1250)
        assert p.end_date == MON + timedelta(days=9)

    def test_behind_extend_deadline(self, scripted_input):
        p = with_progress(500, 500, 500)
        scripted_input(["1", "0", "y", "2", "y", "0", "n"])

        _, output = run(ui_progress.update_progress, p)

        # 7,500 left at 1,000 a day: days are whole (decision 8), so 8 days at 937.5
        assert "Writing days: 10 -> 12" in output
        assert "Extension: 2 days" in output
        assert p.end_date == MON + timedelta(days=11)
        assert p.get_daily_goal(date=TODAY + timedelta(days=1)) == pytest.approx(937.5)

    def test_ahead_finish_early(self, scripted_input):
        p = with_progress(2000, 2000, 2000)
        scripted_input(["1", "1000", "y", "2", "y", "0", "n"])

        _, output = run(ui_progress.update_progress, p)

        assert "You're AHEAD of schedule!" in output
        assert "Finishing early by:" in output
        assert p.end_date < MON + timedelta(days=9)

    def test_ahead_reduce_daily_goals(self, scripted_input):
        p = with_progress(2000, 2000, 2000)
        scripted_input(["1", "1000", "y", "1", "y", "0", "n"])

        run(ui_progress.update_progress, p)

        assert p.get_daily_goal(date=TODAY + timedelta(days=1)) < 1000
        assert p.end_date == MON + timedelta(days=9)

    @pytest.mark.parametrize("adjust, choice", [("n", None), ("y", "0")])
    def test_declining_keeps_the_plan(self, scripted_input, adjust, choice):
        p = with_progress(2000, 2000, 2000)
        answers = ["1", "1000", adjust] + ([choice] if choice else []) + ["0", "n"]
        scripted_input(answers)

        run(ui_progress.update_progress, p)

        assert p.schedule_adjustment == 0
        assert p.end_date == MON + timedelta(days=9)

    def test_offered_once_per_visit(self, scripted_input):
        p = with_progress(500, 500, 500)
        scripted_input(["1", "0", "n", "2", "2026-11-02", "400", "0", "n"])

        _, output = run(ui_progress.update_progress, p)

        assert output.count("PROGRESS STATUS") == 1

    def test_declined_preview_leaves_plan_unchanged(self, scripted_input):
        p = with_progress(500, 500, 500)
        before = p.fingerprint()
        scripted_input(["n"])

        applied, output = run(ui_progress.offer_daily_recalculation, p)

        assert applied is False
        assert "Plan left unchanged." in output
        assert p.fingerprint() == before


@freeze_time(TODAY)
class TestRecalculateScreen:

    def test_recalculate_from_progress(self, scripted_input):
        p = with_progress(500, 500, 500, pattern="rising")
        scripted_input(["y", ""])

        applied, output = run(ui_progress.recalculate_plan_from_progress, p)

        assert applied is True
        assert "Pattern kept: rising" in output
        assert "Past daily goals locked: 3" in output
        total_open = sum(p.get_daily_goal(date=TODAY + timedelta(days=i)) for i in range(7))
        assert total_open == pytest.approx(8500)

    @pytest.mark.parametrize("p, message", [
        (make_plan(start_date=None), "doesn't have a start date"),
        (make_plan(), "No progress has been recorded yet."),
    ])
    def test_refused(self, scripted_input, p, message):
        scripted_input([""])

        applied, output = run(ui_progress.recalculate_plan_from_progress, p)

        assert applied is False
        assert message in output

    def test_goal_already_met(self, scripted_input):
        p = with_progress(5000, 5000)
        scripted_input([""])

        applied, output = run(ui_progress.recalculate_plan_from_progress, p)

        assert applied is False
        assert "already met your goal" in output

    @pytest.mark.parametrize("result, message", [
        (None, "Plan has no start date"),
        ({'reason': 'past_end_date', 'end_date': MON, 'words_remaining': 10},
         "Plan end date has already passed"),
        ({'reason': 'no_remaining_days', 'words_remaining': 10}, "No remaining writing days"),
        ({'reason': 'something else'}, "Recalculation failed: something else"),
    ])
    def test_failure_messages(self, result, message):
        _, output = run(ui_progress.print_recalculation_failure, result)

        assert message in output


@freeze_time(TODAY)
class TestProgressSummary:

    def test_summary_behind(self, scripted_input):
        p = with_progress(0, 1000, 1400)   # the streak counts days with any words
        scripted_input([""])

        _, output = run(ui_progress.view_progress_summary, p)

        assert "Written: 2,400 words (24.0%)" in output
        assert "Days recorded: 3" in output
        assert "Current streak: 2 days" in output
        assert "BEHIND by 600 words" in output
        assert "Days elapsed: 3" in output

    def test_summary_ahead(self, scripted_input):
        scripted_input([""])

        _, output = run(ui_progress.view_progress_summary, with_progress(2000, 2000, 2000))

        assert "AHEAD by 3,000 words" in output

    def test_needs_a_start_date(self, scripted_input):
        scripted_input([""])

        _, output = run(ui_progress.view_progress_summary, make_plan(start_date=None))

        assert "No start date set" in output

    def test_plan_results_show_progress_and_settings(self):
        p = with_progress(1000, 1000, 400, preexisting_words=500, weekend_mode="different",
                          weekend_daily=500, spare_days_dates=[MON + timedelta(days=4)],
                          custom_daily_goals={"2026-11-10": 2000})

        _, output = run(ui_plan_actions.display_results, p)

        assert "Already written before the plan: 500 words" in output
        assert "Weekend goal: 500 words/day (Sat, Sun)" in output
        assert "Custom day goals: 1 day(s) customized" in output
        assert "Spare days: 1 days (0 words)" in output
        assert "Status: ⚠ BEHIND" in output


@freeze_time(TODAY)
class TestAnalyticsMenu:
    """Graphs catch their own errors, so each test checks none was printed."""

    @pytest.mark.parametrize("choice, expected", [
        ("1", "Writing Analytics"),
        ("2", "Cumulative Word Count"),
        ("3", "Daily"),
        ("4", "Velocity"),
        ("5", "Milestone Progress (Current: 24.0%)"),
    ])
    def test_each_view(self, scripted_input, choice, expected):
        p = with_progress(1000, 1000, 400)
        scripted_input([choice, "", "0"])

        _, output = run(progress_analytics.show_analytics_menu, p)

        assert expected.lower() in output.lower()
        assert "Error generating graph" not in output

    def test_all_graphs(self, scripted_input):
        p = with_progress(1500, 0, 1200, pattern="mountain", spare_days_dates=[MON + timedelta(days=1)])
        scripted_input(["6", "", "", "0"])

        _, output = run(progress_analytics.show_analytics_menu, p)

        assert "Best Day" in output and "Worst Day" in output
        assert "Milestone Progress" in output
        assert "Error" not in output

    @pytest.mark.parametrize("answer, message", [
        ("", "Input cannot be empty"),
        ("x", "Invalid input 'x'"),
        ("9", "between 0 and 6"),
    ])
    def test_bad_choices_are_asked_again(self, scripted_input, answer, message):
        scripted_input([answer, "0"])

        _, output = run(progress_analytics.show_analytics_menu, with_progress(1000))

        assert message in output

    def test_ctrl_c_is_not_swallowed(self, monkeypatch):
        # main() catches it to offer saving the open plan (save_after_interrupt)
        def interrupt(prompt=""):
            raise KeyboardInterrupt
        monkeypatch.setattr('builtins.input', interrupt)

        with pytest.raises(KeyboardInterrupt):
            run(progress_analytics.show_analytics_menu, with_progress(1000))

    def test_without_progress(self, scripted_input):
        scripted_input([""])

        _, output = run(progress_analytics.show_analytics_menu, make_plan())

        assert "No progress data available yet." in output

    @pytest.mark.parametrize("graph", [
        progress_analytics.plot_cumulative_progress,
        progress_analytics.plot_daily_progress,
        progress_analytics.plot_velocity,
        progress_analytics.plot_milestone_progress,
    ])
    def test_graphs_need_a_start_date(self, graph):
        _, output = run(graph, make_plan(start_date=None))

        assert "No start date set" in output or "Cannot generate" in output

    def test_ahead_status_in_statistics(self):
        _, output = run(progress_analytics.display_statistics, with_progress(2000, 2000, 2000))

        assert "AHEAD by 3.0 writing days" in output
        assert "Estimated Completion" in output


class TestWordsForRunningTotal:

    def test_counts_preexisting_words_and_earlier_entries_only(self):
        p = with_progress(1000, 1000, 1000, total=15000, preexisting_words=5000)   # 1,000 a day

        assert p.words_for_running_total(9200, MON + timedelta(days=3)) == 1200
        # A past day: later entries don't count
        assert p.words_for_running_total(7500, MON + timedelta(days=1)) == 1500
        assert p.words_for_running_total(7900, MON + timedelta(days=3)) == -100


@freeze_time(TODAY)
class TestRunningTotalEntry:
    """Option 4: the day's words come from the manuscript's total."""

    @pytest.fixture
    def p(self):
        return with_progress(1000, 1000, 1000, total=15000, preexisting_words=5000)   # 1,000 a day

    @pytest.mark.parametrize("answer", ["9200", "9,200", " 9,200 "])
    def test_today(self, p, scripted_input, answer):
        scripted_input(["", answer])

        logged, output = run(ui_progress.log_running_total, p)

        assert logged is True
        assert p.get_progress_for_date(TODAY) == 1200
        assert "Logged before this day: 8,000 words" in output
        assert "Progress recorded: 1,200 words on 2026-11-05 (running total 9,200)" in output
        assert "You met your daily goal!" in output
        assert p.get_total_written() == 9200

    def test_replaces_the_days_entry(self, p, scripted_input):
        p.record_progress(TODAY, 300)
        scripted_input(["", "8500"])

        _, output = run(ui_progress.log_running_total, p)

        assert "already has 300 words logged; they will be replaced" in output
        assert p.get_progress_for_date(TODAY) == 500
        assert "(500 words short of goal)" in output

    def test_past_day(self, p, scripted_input):
        scripted_input(["2026-11-03", "7500"])

        run(ui_progress.log_running_total, p)

        assert p.get_progress_for_date(MON + timedelta(days=1)) == 1500
        assert p.get_progress_for_date(MON + timedelta(days=2)) == 1000

    def test_lower_total_is_refused(self, p, scripted_input):
        scripted_input(["", "7,500"])

        logged, output = run(ui_progress.log_running_total, p)

        assert logged is False
        assert "That's 500 below the 8,000 already logged" in output
        assert "Enter for a specific date" in output
        assert p.get_progress_for_date(TODAY) is None

    def test_same_total_logs_zero(self, p, scripted_input):
        scripted_input(["", "8000"])

        run(ui_progress.log_running_total, p)

        assert p.get_progress_for_date(TODAY) == 0

    @pytest.mark.parametrize("answers, message", [
        (["tomorrow"], "Invalid date 'tomorrow'"),
        (["2026-11-20"], "You can't log progress for a future date."),
        (["", "lots"], "Invalid number 'lots'"),
        (["", ""], None),   # Enter cancels
    ])
    def test_nothing_logged(self, p, scripted_input, answers, message):
        before = dict(p.progress)
        scripted_input(answers)

        logged, output = run(ui_progress.log_running_total, p)

        assert logged is False
        assert p.progress == before
        if message:
            assert message in output

    def test_from_the_progress_menu(self, p, scripted_input):
        # Option 4, today, 9,200 -> ahead (4,200 logged vs 3,000 due): no; done; save: no
        scripted_input(["4", "", "9200", "n", "0", "n"])

        _, output = run(ui_progress.update_progress, p)

        assert "4. Enter your running total" in output
        assert "You're AHEAD of schedule!" in output
        assert p.get_progress_for_date(TODAY) == 1200
        assert p.source_file is None   # declined the save offer
