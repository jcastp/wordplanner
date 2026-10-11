"""Tests for the command-line commands (cli.py): log and status on the current plan."""

from datetime import datetime, timedelta
from freezegun import freeze_time
import pytest
import cli
import plan
import plan_manager
import plan_storage
import planea


MON = datetime(2026, 11, 2)
TODAY = MON + timedelta(days=3)   # Thursday


def day(n):
    return MON + timedelta(days=n)


def save_current(**kwargs):
    """Save a current (★) plan: 15,000 words, 5,000 pre-existing, 1,000 a day for 10 days."""
    values = dict(name="Novel", total=15000, daily=1000, time=10, start_date=MON,
                  preexisting_words=5000, is_active=True)
    values.update(kwargs)
    p = plan.Plan(**values)
    p.sync_daily()
    for n in range(3):
        p.record_progress(day(n), 1000)
    plan_storage.save_plan(p)
    return p


def reloaded(p):
    return plan_storage.load_plan(p.source_file)


@freeze_time(TODAY)
class TestLog:

    def test_words_for_today(self, capsys):
        p = save_current()

        code = planea.main(["log", "1,200"])

        out = capsys.readouterr().out
        assert code == 0
        assert reloaded(p).get_progress_for_date(TODAY) == 1200
        assert "Logged 1,200 words on 2026-11-05." in out
        assert "Today (Thu Nov 05): 1,200 / 1,000 words ✓" in out
        assert "Written: 9,200 / 15,000 words (61.3%), 5,800 to go" in out

    def test_replaces_the_days_entry(self, capsys):
        p = save_current()
        cli.run(["log", "300"])

        cli.run(["log", "800"])

        assert "Logged 800 words on 2026-11-05 (replaces 300)." in capsys.readouterr().out
        assert reloaded(p).get_progress_for_date(TODAY) == 800

    def test_running_total(self, capsys):
        p = save_current()

        code = cli.run(["log", "--total", "9200"])

        assert code == 0
        assert reloaded(p).get_progress_for_date(TODAY) == 1200

    def test_lower_running_total_is_refused(self, capsys):
        p = save_current()

        code = cli.run(["log", "--total", "7,500"])

        err = capsys.readouterr().err
        assert code == 1
        assert "7,500 is 500 below the 8,000 already logged before 2026-11-05" in err
        assert reloaded(p).get_progress_for_date(TODAY) is None

    def test_earlier_day(self):
        p = save_current()

        cli.run(["log", "1500", "--date", "2026-11-03"])

        saved = reloaded(p)
        assert saved.get_progress_for_date(day(1)) == 1500
        assert saved.get_total_written() == 8500

    def test_future_day_is_refused(self, capsys):
        p = save_current()

        assert cli.run(["log", "100", "--date", "2026-11-06"]) == 1
        assert "2026-11-06 is in the future." in capsys.readouterr().err
        assert reloaded(p).get_progress_for_date(day(4)) is None

    def test_day_outside_the_plan_is_logged_with_a_note(self, capsys):
        p = save_current()

        assert cli.run(["log", "400", "--date", "2026-10-30"]) == 0
        assert "outside the plan" in capsys.readouterr().out
        assert reloaded(p).get_total_written() == 8400

    def test_past_days_are_locked_first(self):
        # Like the plan menu: logging must not change the goals of past days
        p = save_current()

        cli.run(["log", "5000"])

        saved = reloaded(p)
        assert all(saved.locked_goals[day(n).strftime('%Y-%m-%d')] == pytest.approx(1000)
                   for n in range(3))

    def test_only_the_current_plan_changes(self):
        other = plan.Plan(name="Other", total=1000, daily=100, time=10, start_date=MON)
        plan_storage.save_plan(other)
        save_current()

        cli.run(["log", "700"])

        assert reloaded(other).progress == {}

    @pytest.mark.parametrize("args", [
        ["log"],
        ["log", "5", "--total", "3"],
        ["log", "abc"],
        ["log", "-5"],
        ["log", "5", "--date", "05/11/2026"],
        ["dance"],
    ])
    def test_bad_usage(self, args):
        save_current()

        with pytest.raises(SystemExit) as exit_info:
            cli.run(args)

        assert exit_info.value.code == 2


class TestStatus:

    @freeze_time(TODAY)
    def test_on_track(self, capsys):
        save_current()

        assert planea.main(["status"]) == 0

        out = capsys.readouterr().out
        assert "★ Novel (Nov 02, 2026 - Nov 11, 2026)" in out
        assert "Today (Thu Nov 05): 0 / 1,000 words, 1,000 to go" in out
        assert "Status: ✓ on track" in out

    @freeze_time(TODAY + timedelta(days=1))
    def test_behind_after_a_missed_day(self, capsys):
        save_current()

        cli.run(["status"])

        assert "Status: ⚠ behind by 1,000 words" in capsys.readouterr().out

    @freeze_time(TODAY)
    def test_ahead(self, capsys):
        save_current()
        cli.run(["log", "1500"])

        # Today's words count; its goal is expected only once the day is over
        assert "Status: ✓ ahead by 1,500 words" in capsys.readouterr().out

    @freeze_time(day(5))   # Saturday
    def test_rest_day(self, capsys):
        save_current(weekend_mode="spare")

        cli.run(["status"])

        assert "Today (Sat Nov 07): rest day" in capsys.readouterr().out

    @freeze_time(MON - timedelta(days=2))
    def test_before_the_start(self, capsys):
        p = plan.Plan(name="Later", total=1000, daily=100, time=10, start_date=MON, is_active=True)
        plan_storage.save_plan(p)

        cli.run(["status"])

        out = capsys.readouterr().out
        assert "Starts on Monday, Nov 02." in out
        assert "Status" not in out

    @freeze_time(MON + timedelta(days=30))
    def test_after_the_end(self, capsys):
        save_current()

        cli.run(["status"])

        assert "The plan's last day has passed." in capsys.readouterr().out

    def test_no_current_plan(self, capsys):
        plan_storage.save_plan(plan.Plan(name="Not current", total=1000, daily=100, time=10,
                                         start_date=MON))

        assert cli.run(["status"]) == 1
        assert "there is no current plan" in capsys.readouterr().err

    def test_no_start_date(self, capsys):
        p = plan.Plan(name="Undated", total=1000, daily=100, time=10, is_active=True)
        plan_storage.save_plan(p)

        assert cli.run(["status"]) == 0
        assert "no start date set" in capsys.readouterr().out
        assert cli.run(["log", "100"]) == 1
        assert "no start date" in capsys.readouterr().err


def test_no_arguments_open_the_menus(monkeypatch):
    opened = []
    monkeypatch.setattr(planea, 'main_menu_loop', lambda: opened.append(True))

    assert planea.main([]) == 0
    assert opened == [True]
    assert plan_manager.get_active_plan() is None
