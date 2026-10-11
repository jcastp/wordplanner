"""Tests for export file names (X2) and whole-number word counts (X3)."""

import contextlib
import io
import re
import pytest
from datetime import datetime
import plan
import plan_export
import plan_storage
import plan_manager_ui
import calendar_view


MON = datetime(2026, 11, 2)
EXPORTERS = [
    (plan_export.export_to_csv, "csv"),
    (plan_export.export_to_ical, "ics"),
    (plan_export.export_to_markdown, "md"),
]


def make_plan(**kwargs):
    values = dict(name="Novel", total=10000, daily=1000, time=10, start_date=MON)
    values.update(kwargs)
    return plan.Plan(**values)


class TestSafeFilenameStem:

    @pytest.mark.parametrize("name, stem", [
        ("My Novel", "My_Novel"),
        ("Draft 1/2: notes*?", "Draft_12_notes"),
        ("Café  — été", "Café_été"),
        ("///", "plan"),
        ("", "plan"),
        (None, "plan"),
        ("../../etc/passwd", "etcpasswd"),
    ])
    def test_stems(self, name, stem):
        assert plan_storage.safe_filename_stem(name) == stem

    def test_plan_files_use_it(self):
        assert plan_storage.get_plan_filename("a/b c").startswith("ab_c_")


class TestExportFilenames:

    @pytest.mark.parametrize("exporter, extension", EXPORTERS)
    def test_slash_in_name_exports_into_the_exports_folder(self, exporter, extension):
        # A '/' used to make the path point at a missing subfolder: the export failed
        p = make_plan(name="Draft 1/2: notes")

        path = exporter(p)

        assert path.exists()
        assert path.parent == plan_export.get_exports_directory()
        assert re.fullmatch(rf"Draft_12_notes_\d{{8}}_\d{{6}}\.{extension}", path.name)

    @pytest.mark.parametrize("exporter, extension", EXPORTERS)
    def test_unnamed_plan(self, exporter, extension):
        path = exporter(make_plan(name=None))

        assert path.name.startswith("plan_") and path.name.endswith(f".{extension}")


class TestWholeNumbers:
    """Totals can be floats in memory (e.g. a customised template total)."""

    @pytest.fixture
    def float_plan(self):
        p = make_plan(total=50000.0, preexisting_words=10000, time=40)
        p.calculate_daily()
        p.record_progress(MON, 1000)
        return p

    def test_markdown(self, float_plan, tmp_path):
        path = tmp_path / "plan.md"

        plan_export.export_to_markdown(float_plan, path)

        text = path.read_text()
        assert "**Total Word Goal**: 50,000 words" in text
        assert "**Written Before the Plan**: 10,000 words" in text
        assert "**Remaining**: 39,000 words" in text
        assert "**Mon, November 02, 2026**: 1,000 words → 1,000 written" in text
        assert not re.search(r"\d\.0 words", text)

    def test_calendar_summary(self, float_plan):
        out = io.StringIO()

        with contextlib.redirect_stdout(out):
            calendar_view.display_calendar_view(float_plan, float_plan.start_date)

        assert "Remaining: 39,000 words" in out.getvalue()
        assert ".0 words" not in out.getvalue()

    def test_plan_manager_overview(self, float_plan):
        plan_storage.save_plan(float_plan)
        out = io.StringIO()

        with contextlib.redirect_stdout(out):
            plan_manager_ui.display_plans_overview()

        assert "Total Word Goal: 50,000 words" in out.getvalue()
