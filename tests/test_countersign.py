"""Tests for tools/countersign.py.

Verifies: record appends, check passes with a distinct name, a same-person countersign
is rejected, a missing countersign is flagged and --strict exits 1, a malformed GATES
row is skipped with a warning (not a crash).
"""
import csv
import os
import sys
import tempfile
import textwrap

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_REPO, "tools"))

import countersign as CS


def _mk_dir():
    return tempfile.mkdtemp()


def _write_gates(path, body):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(body)


def test_record_appends_row():
    d = _mk_dir()
    ledger = os.path.join(d, "governance", "COUNTERSIGNS.csv")
    CS.record(ledger, "G3", "run-1", "A. Reyes", "Co-PI")
    CS.record(ledger, "G6", "run-1", "B. Chen", "Dean")
    rows = CS.load_countersigns(ledger)
    assert len(rows) == 2
    assert rows[0]["gate"] == "G3"
    assert rows[1]["name"] == "B. Chen"


def test_check_passes_with_distinct_name():
    d = _mk_dir()
    ledger = os.path.join(d, "governance", "COUNTERSIGNS.csv")
    gates_md = os.path.join(d, "governance", "GATES.md")
    _write_gates(gates_md, textwrap.dedent("""\
        # Gates
        ## Approvals log
        | Gate | Date | Approver | Decision | Notes |
        |---|---|---|---|---|
        | G3 | 2026-07-01 | Director (Jaslam) | APPROVE | final submit |
    """))
    CS.record(ledger, "G3", "run-1", "A. Reyes", "Co-PI")
    result = CS.check(ledger, gates_md)
    assert result["ok"] is True
    assert result["rows"][0]["valid"] is True


def test_same_person_countersign_rejected():
    d = _mk_dir()
    ledger = os.path.join(d, "governance", "COUNTERSIGNS.csv")
    gates_md = os.path.join(d, "governance", "GATES.md")
    _write_gates(gates_md, textwrap.dedent("""\
        # Gates
        ## Approvals log
        | Gate | Date | Approver | Decision | Notes |
        |---|---|---|---|---|
        | G3 | 2026-07-01 | Director (Jaslam) | APPROVE | final submit |
    """))
    CS.record(ledger, "G3", "run-1", "Jaslam", "Director")  # same person, different string
    result = CS.check(ledger, gates_md)
    assert result["ok"] is False
    assert result["rows"][0]["valid"] is False


def test_missing_countersign_flagged_and_strict_exit_1():
    d = _mk_dir()
    ledger = os.path.join(d, "governance", "COUNTERSIGNS.csv")
    gates_md = os.path.join(d, "governance", "GATES.md")
    _write_gates(gates_md, textwrap.dedent("""\
        # Gates
        ## Approvals log
        | Gate | Date | Approver | Decision | Notes |
        |---|---|---|---|---|
        | G6 | 2026-07-01 | Director (Jaslam) | APPROVE | publish |
    """))
    result = CS.check(ledger, gates_md)
    assert result["ok"] is False
    rc = CS.main(["check", "--ledger", ledger, "--gates-md", gates_md, "--strict"])
    assert rc == 1


def test_check_non_strict_exits_0_even_when_invalid():
    d = _mk_dir()
    ledger = os.path.join(d, "governance", "COUNTERSIGNS.csv")
    gates_md = os.path.join(d, "governance", "GATES.md")
    _write_gates(gates_md, textwrap.dedent("""\
        # Gates
        ## Approvals log
        | Gate | Date | Approver | Decision | Notes |
        |---|---|---|---|---|
        | G3 | 2026-07-01 | Director (Jaslam) | APPROVE | final submit |
    """))
    rc = CS.main(["check", "--ledger", ledger, "--gates-md", gates_md])
    assert rc == 0


def test_malformed_gates_row_skipped_with_warning_not_crash():
    d = _mk_dir()
    ledger = os.path.join(d, "governance", "COUNTERSIGNS.csv")
    gates_md = os.path.join(d, "governance", "GATES.md")
    _write_gates(gates_md, textwrap.dedent("""\
        # Gates
        ## Approvals log
        | Gate | Date | Approver | Decision | Notes |
        |---|---|---|---|---|
        | G3 | 2026-07-01 | Director (Jaslam) | APPROVE (fused row missing cells
        | G6 | 2026-07-01 | Director (Jaslam) | APPROVE | publish |
    """))
    CS.record(ledger, "G6", "run-1", "A. Reyes", "Co-PI")
    result = CS.check(ledger, gates_md)  # must not raise
    assert any("fused or truncated" in w for w in result["warnings"])
    gate_ids = [r["gate"] for r in result["rows"]]
    assert "G6" in gate_ids


def test_gates_md_missing_reports_warning_not_crash():
    d = _mk_dir()
    ledger = os.path.join(d, "governance", "COUNTERSIGNS.csv")
    gates_md = os.path.join(d, "governance", "GATES.md")  # never written
    result = CS.check(ledger, gates_md)
    assert result["rows"] == []
    assert any("not found" in w for w in result["warnings"])


def test_non_g3_g6_gates_not_required_to_countersign():
    d = _mk_dir()
    ledger = os.path.join(d, "governance", "COUNTERSIGNS.csv")
    gates_md = os.path.join(d, "governance", "GATES.md")
    _write_gates(gates_md, textwrap.dedent("""\
        # Gates
        ## Approvals log
        | Gate | Date | Approver | Decision | Notes |
        |---|---|---|---|---|
        | G1 | 2026-07-01 | Director (Jaslam) | APPROVE | pursue |
    """))
    result = CS.check(ledger, gates_md)
    assert result["ok"] is True
    assert result["rows"] == []


def test_same_person_helper_substring_match():
    assert CS._same_person("Director (Jaslam)", "Jaslam") is True
    assert CS._same_person("Jaslam", "Director (Jaslam)") is True
    assert CS._same_person("A. Reyes", "B. Chen") is False
    assert CS._same_person("", "Jaslam") is False


def test_record_creates_ledger_with_header():
    d = _mk_dir()
    ledger = os.path.join(d, "governance", "COUNTERSIGNS.csv")
    CS.record(ledger, "G3", "run-1", "A. Reyes", "Co-PI")
    with open(ledger, newline="", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        header = next(reader)
    assert header == CS.FIELDS
