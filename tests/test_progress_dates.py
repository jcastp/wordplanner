"""Tests for which dates progress can be logged for (issues-program.org P20).

Future dates are refused. Dates outside the plan (before the start, after the
end) are logged after a warning and a confirmation: the words count toward
the total wherever they're logged.
"""

import contextlib
import io
import pytest
from datetime import datetime, timedelta
from freezegun import freeze_time
import plan
import planea


MON = datetime(2026, 11, 2)


def day(n):
    """Date of calendar day n of a plan starting MON (1-based)."""
    return MON + timedelta(days=n - 1)


def key(d):
    return d.strftime('%Y-%m-%d')


@pytest.fixture
def ten_day_plan():
    """10,000 words / 10 writing days, Mon 2026-11-02 to Wed 2026-11-11."""
    return plan.Plan(total=10000, daily=1000, time=10, start_date=MON)


@pytest.fixture
def log_progress(monkeypatch, scripted_input):
    """Run the progress screen with answers (the ahead/behind offer is tested elsewhere)."""
    monkeypatch.setattr(planea, 'check_and_offer_recalculation', lambda p: True)

    def _run(p, answers):
        scripted_input(answers)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            planea.update_progress(p)
        return out.getvalue()
    return _run


@freeze_time(day(5) + timedelta(hours=10))
class TestSpecificDate:

    def test_future_date_refused(self, ten_day_plan, log_progress):
        output = log_progress(ten_day_plan, ["2", key(day(6)), "0"])

        assert "You can't log progress for a future date." in output
        assert ten_day_plan.progress == {}

    def test_past_date_inside_the_plan(self, ten_day_plan, log_progress):
        # date, words, done, don't save
        log_progress(ten_day_plan, ["2", key(day(3)), "800", "0", "n"])

        assert ten_day_plan.progress == {key(day(3)): 800}

    def test_before_start_confirmed(self, ten_day_plan, log_progress):
        # Used to be refused outright
        output = log_progress(ten_day_plan, ["2", key(day(-1)), "y", "500", "0", "n"])

        assert "is before the plan starts (2026-11-02)" in output
        assert ten_day_plan.progress == {key(day(-1)): 500}
        assert ten_day_plan.get_total_written() == 500

    def test_before_start_declined(self, ten_day_plan, log_progress):
        log_progress(ten_day_plan, ["2", key(day(-1)), "n", "0"])

        assert ten_day_plan.progress == {}


@freeze_time(day(15) + timedelta(hours=10))
class TestAfterTheEnd:

    def test_quick_entry_warns(self, ten_day_plan, log_progress):
        output = log_progress(ten_day_plan, ["1", "y", "700", "0", "n"])

        assert "is after the plan ends (2026-11-11)" in output
        assert ten_day_plan.progress == {key(day(15)): 700}

    def test_quick_entry_declined(self, ten_day_plan, log_progress):
        log_progress(ten_day_plan, ["1", "n", "0"])

        assert ten_day_plan.progress == {}


@freeze_time(day(3) + timedelta(hours=10))
def test_quick_entry_inside_the_plan_asks_nothing(ten_day_plan, log_progress):
    log_progress(ten_day_plan, ["1", "1200", "0", "n"])

    assert ten_day_plan.progress == {key(day(3)): 1200}
