"""Tests for tools/proposal_timeline.py.

Uses only stdlib and tmp dirs. Never touches the live repo data.
All computations are deterministic: same inputs produce same outputs.
"""
import os
import sys
import json
import tempfile
from datetime import datetime

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_REPO, "tools"))

import proposal_timeline as PT


DEADLINE = PT._parse_deadline("2026-09-01")


# ---------------------------------------------------------------------------
# Deadline parsing
# ---------------------------------------------------------------------------

def test_parse_deadline_valid():
    d = PT._parse_deadline("2026-09-01")
    assert d.year == 2026 and d.month == 9 and d.day == 1


def test_parse_deadline_invalid_exits_2():
    try:
        PT._parse_deadline("not-a-date")
        assert False, "Expected SystemExit(2)"
    except SystemExit as exc:
        assert exc.code == 2


# ---------------------------------------------------------------------------
# Default task set
# ---------------------------------------------------------------------------

def test_default_tasks_loaded_without_path():
    tasks = PT._load_tasks(None)
    assert len(tasks) == len(PT.DEFAULT_TASKS)
    names = [t["task"] for t in tasks]
    assert "Intent to submit" in names
    assert "Final PI review" in names


def test_default_timeline_sorted_and_before_deadline():
    tasks = PT._load_tasks(None)
    rows = PT.compute_timeline(DEADLINE, tasks)
    # sorted earliest first
    due_dates = [r["due_date"] for r in rows]
    assert due_dates == sorted(due_dates)
    # every internal due date must be on or before the deadline
    for r in rows:
        assert r["due_date"] <= DEADLINE
    # earliest task should be the one with the largest lead_days (intent to submit)
    assert rows[0]["task"] == "Intent to submit"
    # latest task should be the one with the smallest lead_days (final PI review)
    assert rows[-1]["task"] == "Final PI review"


def test_lead_days_produce_correct_offset():
    tasks = [{"task": "x", "owner": "PI", "lead_days": 10}]
    rows = PT.compute_timeline(DEADLINE, tasks)
    assert (DEADLINE - rows[0]["due_date"]).days == 10


# ---------------------------------------------------------------------------
# Custom tasks file
# ---------------------------------------------------------------------------

def test_load_tasks_from_file():
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "tasks.json")
        custom = [
            {"task": "Custom task A", "owner": "PI", "lead_days": 5},
            {"task": "Custom task B", "owner": "sponsored programs", "lead_days": 2},
        ]
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(custom, fh)
        tasks = PT._load_tasks(path)
        assert len(tasks) == 2
        assert tasks[0]["task"] == "Custom task A"


def test_load_tasks_missing_file_exits_2():
    with tempfile.TemporaryDirectory() as tmp:
        try:
            PT._load_tasks(os.path.join(tmp, "nonexistent.json"))
            assert False, "Expected SystemExit(2)"
        except SystemExit as exc:
            assert exc.code == 2


def test_load_tasks_missing_required_key_exits_2():
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "tasks.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump([{"task": "no lead days"}], fh)
        try:
            PT._load_tasks(path)
            assert False, "Expected SystemExit(2)"
        except SystemExit as exc:
            assert exc.code == 2


# ---------------------------------------------------------------------------
# Report content
# ---------------------------------------------------------------------------

def test_build_report_contains_planning_aid_header():
    tasks = PT._load_tasks(None)
    rows = PT.compute_timeline(DEADLINE, tasks)
    report = PT.build_report(DEADLINE, rows)
    assert "internal planning aid" in report.lower()
    assert "2026-09-01" in report


def test_build_report_no_em_dashes():
    tasks = PT._load_tasks(None)
    rows = PT.compute_timeline(DEADLINE, tasks)
    report = PT.build_report(DEADLINE, rows)
    assert "—" not in report


def test_build_report_contains_open_items():
    tasks = PT._load_tasks(None)
    rows = PT.compute_timeline(DEADLINE, tasks)
    report = PT.build_report(DEADLINE, rows)
    assert "## Open items" in report
    assert "- [ ]" in report


# ---------------------------------------------------------------------------
# .ics output
# ---------------------------------------------------------------------------

def test_build_ics_contains_valid_vevents():
    tasks = PT._load_tasks(None)
    rows = PT.compute_timeline(DEADLINE, tasks)
    ics = PT.build_ics(DEADLINE, rows)
    assert ics.startswith("BEGIN:VCALENDAR")
    assert ics.rstrip("\r\n").endswith("END:VCALENDAR")
    assert ics.count("BEGIN:VEVENT") == len(rows) + 1  # + deadline event
    assert ics.count("END:VEVENT") == len(rows) + 1
    assert "SUMMARY:Submission deadline" in ics


# ---------------------------------------------------------------------------
# CLI end-to-end
# ---------------------------------------------------------------------------

def test_cli_writes_markdown_and_ics():
    with tempfile.TemporaryDirectory() as tmp:
        out_path = os.path.join(tmp, "timeline.md")
        ics_path = os.path.join(tmp, "out.ics")
        rc = PT.main(["--deadline", "2026-09-01", "--out", out_path, "--ics", ics_path])
        assert rc == 0
        assert os.path.exists(out_path)
        assert os.path.exists(ics_path)
        md = open(out_path, encoding="utf-8").read()
        assert "Proposal timeline" in md
        ics = open(ics_path, encoding="utf-8").read()
        assert "BEGIN:VCALENDAR" in ics


def test_cli_with_custom_tasks_file():
    with tempfile.TemporaryDirectory() as tmp:
        tasks_path = os.path.join(tmp, "tasks.json")
        with open(tasks_path, "w", encoding="utf-8") as fh:
            json.dump([{"task": "Only task", "owner": "PI", "lead_days": 4}], fh)
        out_path = os.path.join(tmp, "timeline.md")
        rc = PT.main(["--deadline", "2026-09-01", "--tasks", tasks_path, "--out", out_path])
        assert rc == 0
        md = open(out_path, encoding="utf-8").read()
        assert "Only task" in md


def test_cli_exits_2_on_bad_deadline():
    with tempfile.TemporaryDirectory() as tmp:
        out_path = os.path.join(tmp, "timeline.md")
        try:
            PT.main(["--deadline", "09/01/2026", "--out", out_path])
            assert False, "Expected SystemExit(2)"
        except SystemExit as exc:
            assert exc.code == 2
