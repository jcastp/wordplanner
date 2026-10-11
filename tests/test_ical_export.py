"""Tests for the iCal export (issues-program.org X1, RFC 5545)."""

import re
import warnings
from datetime import datetime, timedelta
import plan
import plan_export
import plan_storage


MON = datetime(2026, 11, 2)


def make_plan(**kwargs):
    values = dict(name="Novel", total=10000, daily=1000, time=10, start_date=MON)
    values.update(kwargs)
    return plan.Plan(**values)


def export(p, tmp_path):
    path = tmp_path / "plan.ics"
    plan_export.export_to_ical(p, path)
    return path.read_bytes().decode('utf-8')


def unfold(text):
    """Undo RFC 5545 line folding and split into content lines."""
    return text.replace("\r\n ", "").split("\r\n")[:-1]


def events(text):
    """Each VEVENT as a dict of property name (without parameters) -> value."""
    result, current = [], None
    for line in unfold(text):
        if line == "BEGIN:VEVENT":
            current = {}
        elif line == "END:VEVENT":
            result.append(current)
            current = None
        elif current is not None:
            name, value = line.split(":", 1)
            current[name.split(";")[0]] = value
    return result


class TestFormat:

    def test_every_line_ends_with_crlf(self, tmp_path):
        text = export(make_plan(), tmp_path)

        assert text.endswith("END:VCALENDAR\r\n")
        assert "\n" not in text.replace("\r\n", "")

    def test_lines_are_folded_at_75_octets(self, tmp_path):
        p = make_plan(name="Ünïcödé 🖋 " * 12)  # long, with multi-byte characters

        text = export(p, tmp_path)

        for line in text.split("\r\n"):
            assert len(line.encode('utf-8')) <= 75
        # Folding never breaks a character and unfolds to the original
        assert f"X-WR-CALNAME:{p.name}" in unfold(text)

    def test_all_day_events_end_the_next_day(self, tmp_path):
        for event in events(export(make_plan(), tmp_path)):
            start = datetime.strptime(event['DTSTART'], '%Y%m%d')
            end = datetime.strptime(event['DTEND'], '%Y%m%d')
            assert end - start == timedelta(days=1)

    def test_text_is_escaped(self, tmp_path):
        p = make_plan(name="Draft, part 1; notes\\old")

        lines = unfold(export(p, tmp_path))

        assert "X-WR-CALNAME:Draft\\, part 1\\; notes\\\\old" in lines
        summary = next(line for line in lines if line.startswith("SUMMARY:Write"))
        assert summary == "SUMMARY:Write 1\\,000 words - Draft\\, part 1\\; notes\\\\old"

    def test_description_newlines_are_escaped(self, tmp_path):
        event = events(export(make_plan(), tmp_path))[0]

        assert event['DESCRIPTION'] == (
            "Writing goal: 1\\,000 words\\nDay 1 of the plan\\nTotal goal: 10\\,000 words")

    def test_no_deprecated_utcnow(self, tmp_path):
        with warnings.catch_warnings():
            warnings.simplefilter("error", DeprecationWarning)
            export(make_plan(), tmp_path)

    def test_escape_and_fold_helpers(self):
        assert plan_export.ical_escape("a,b;c\\d\ne") == "a\\,b\\;c\\\\d\\ne"
        assert plan_export.ical_fold("x" * 75) == "x" * 75
        assert plan_export.ical_fold("x" * 76) == "x" * 75 + "\r\n x"


class TestEvents:

    def test_one_event_per_plan_day(self, tmp_path):
        # P5 used to export a 62-day plan here
        p = make_plan(spare_days_dates=[MON + timedelta(days=3), MON + timedelta(days=40)])

        found = events(export(p, tmp_path))

        assert len(found) == p.total_calendar_days == 11
        assert sum(1 for e in found if e['SUMMARY'].startswith("Spare day")) == 1

    def test_weekend_rest_days_are_rest_events(self, tmp_path):
        p = make_plan(weekend_mode="spare")
        p.sync_daily()

        found = events(export(p, tmp_path))

        rest = [e for e in found if e['SUMMARY'].startswith("Rest day")]
        assert [e['DTSTART'] for e in rest] == ["20261107", "20261108"]
        assert all(e['TRANSP'] == "TRANSPARENT" for e in rest)
        assert not any("Write 0 words" in e['SUMMARY'] for e in found)


class TestStableUids:

    def uids(self, p, tmp_path):
        return [e['UID'] for e in events(export(p, tmp_path))]

    def test_renaming_keeps_uids(self, tmp_path):
        # Used to contain the name: a rename duplicated every event on re-import
        p = make_plan()
        before = self.uids(p, tmp_path)

        p.name = "Novel (second draft)"

        assert self.uids(p, tmp_path) == before
        assert len(set(before)) == len(before)

    def test_plan_id_survives_save_and_load(self):
        p = make_plan()
        plan_storage.save_plan(p)

        assert plan_storage.load_plan(p.source_file).plan_id == p.plan_id

    def test_old_files_get_a_stable_id(self, sample_plan_dict):
        sample_plan_dict.pop('plan_id', None)

        first = plan.Plan.from_dict(dict(sample_plan_dict)).plan_id
        second = plan.Plan.from_dict(dict(sample_plan_dict)).plan_id

        assert first == second

    def test_save_as_new_copy_gets_its_own_id(self, tmp_path):
        p = make_plan()
        plan_storage.save_plan(p)
        original_id = p.plan_id

        plan_storage.save_plan(p, overwrite_source=False)

        assert p.plan_id != original_id

    def test_uid_format(self, tmp_path):
        p = make_plan()

        assert all(re.fullmatch(rf"(writing|spare|rest)-\d{{8}}-{p.plan_id}@wordplanner", uid)
                   for uid in self.uids(p, tmp_path))
