#!/usr/bin/env python3
"""Tests for tools/cost_share_ledger.py.

Stdlib only. Uses tmp_path for the commitments and contributions CSVs; never
touches the live repo data. Covers totals/shortfall math, empty-doc flag,
in-kind third-party flag, multi-award separation, and a report containing a
flags section.
"""
from __future__ import annotations
import os
import sys

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_REPO, "tools"))

import pytest
import cost_share_ledger as L


# ---------------------------------------------------------------------------
# Totals and shortfall math
# ---------------------------------------------------------------------------

def test_totals_and_shortfall_math():
    commitments = [{"award": "A1", "source": "State U", "type": "cash", "committed": 50000}]
    contributions = [
        {"award": "A1", "date": "2026-01-01", "source": "State U", "amount": 20000, "doc": "d1.pdf"},
        {"award": "A1", "date": "2026-02-01", "source": "State U", "amount": 10000, "doc": "d2.pdf"},
    ]
    status = L.compute_status("A1", commitments, contributions, institution="State U")
    assert status["committed"] == pytest.approx(50000)
    assert status["documented"] == pytest.approx(30000)
    assert status["shortfall"] == pytest.approx(20000)
    assert "SHORTFALL" in status["flags"]


def test_no_shortfall_when_fully_documented():
    commitments = [{"award": "A2", "source": "State U", "type": "cash", "committed": 10000}]
    contributions = [{"award": "A2", "date": "2026-01-01", "source": "State U", "amount": 10000, "doc": "d1.pdf"}]
    status = L.compute_status("A2", commitments, contributions, institution="State U")
    assert status["shortfall"] == pytest.approx(0)
    assert "SHORTFALL" not in status["flags"]


def test_overdocumented_has_no_shortfall_flag():
    commitments = [{"award": "A3", "source": "State U", "type": "cash", "committed": 10000}]
    contributions = [{"award": "A3", "date": "2026-01-01", "source": "State U", "amount": 15000, "doc": "d1.pdf"}]
    status = L.compute_status("A3", commitments, contributions, institution="State U")
    assert "SHORTFALL" not in status["flags"]
    assert status["shortfall"] < 0


# ---------------------------------------------------------------------------
# Empty-doc flag
# ---------------------------------------------------------------------------

def test_empty_doc_flag():
    commitments = [{"award": "A4", "source": "State U", "type": "cash", "committed": 10000}]
    contributions = [
        {"award": "A4", "date": "2026-01-01", "source": "State U", "amount": 5000, "doc": ""},
        {"award": "A4", "date": "2026-02-01", "source": "State U", "amount": 3000, "doc": "receipt.pdf"},
    ]
    status = L.compute_status("A4", commitments, contributions, institution="State U")
    assert "UNDOCUMENTED_MATCH" in status["flags"]
    assert status["undocumented_count"] == 1


def test_no_empty_doc_flag_when_all_documented():
    commitments = [{"award": "A5", "source": "State U", "type": "cash", "committed": 10000}]
    contributions = [{"award": "A5", "date": "2026-01-01", "source": "State U", "amount": 5000, "doc": "receipt.pdf"}]
    status = L.compute_status("A5", commitments, contributions, institution="State U")
    assert "UNDOCUMENTED_MATCH" not in status["flags"]


def test_whitespace_only_doc_counts_as_empty():
    commitments = [{"award": "A6", "source": "State U", "type": "cash", "committed": 10000}]
    contributions = [{"award": "A6", "date": "2026-01-01", "source": "State U", "amount": 5000, "doc": "   "}]
    status = L.compute_status("A6", commitments, contributions, institution="State U")
    assert "UNDOCUMENTED_MATCH" in status["flags"]


# ---------------------------------------------------------------------------
# In-kind third-party flag
# ---------------------------------------------------------------------------

def test_in_kind_third_party_flag():
    commitments = [{"award": "A7", "source": "Partner Org", "type": "in-kind", "committed": 20000}]
    contributions = [{"award": "A7", "date": "2026-01-01", "source": "Partner Org", "amount": 20000, "doc": "letter.pdf"}]
    status = L.compute_status("A7", commitments, contributions, institution="State U")
    assert "IN_KIND_NEEDS_LETTER" in status["flags"]
    assert status["needs_letter_count"] == 1


def test_in_kind_from_institution_itself_not_flagged():
    commitments = [{"award": "A8", "source": "State U", "type": "in-kind", "committed": 20000}]
    contributions = [{"award": "A8", "date": "2026-01-01", "source": "State U", "amount": 20000, "doc": "internal.pdf"}]
    status = L.compute_status("A8", commitments, contributions, institution="State U")
    assert "IN_KIND_NEEDS_LETTER" not in status["flags"]


def test_cash_third_party_not_flagged_as_in_kind():
    commitments = [{"award": "A9", "source": "Partner Org", "type": "cash", "committed": 20000}]
    contributions = [{"award": "A9", "date": "2026-01-01", "source": "Partner Org", "amount": 20000, "doc": "check.pdf"}]
    status = L.compute_status("A9", commitments, contributions, institution="State U")
    assert "IN_KIND_NEEDS_LETTER" not in status["flags"]


# ---------------------------------------------------------------------------
# Multi-award separation
# ---------------------------------------------------------------------------

def test_multi_award_separation():
    commitments = [
        {"award": "AW1", "source": "State U", "type": "cash", "committed": 10000},
        {"award": "AW2", "source": "State U", "type": "cash", "committed": 50000},
    ]
    contributions = [
        {"award": "AW1", "date": "2026-01-01", "source": "State U", "amount": 10000, "doc": "d1.pdf"},
        {"award": "AW2", "date": "2026-01-01", "source": "State U", "amount": 5000, "doc": "d2.pdf"},
    ]
    statuses = L.compute_all_statuses(commitments, contributions, institution="State U")
    by_award = {s["award"]: s for s in statuses}
    assert len(statuses) == 2
    assert "SHORTFALL" not in by_award["AW1"]["flags"]
    assert "SHORTFALL" in by_award["AW2"]["flags"]
    assert by_award["AW1"]["documented"] == pytest.approx(10000)
    assert by_award["AW2"]["documented"] == pytest.approx(5000)


# ---------------------------------------------------------------------------
# CLI integration and report
# ---------------------------------------------------------------------------

def test_cli_commit_then_contribute_then_status(tmp_path, capsys):
    commitments_path = str(tmp_path / "COMMITMENTS.csv")
    contributions_path = str(tmp_path / "CONTRIBUTIONS.csv")

    rc = L.main([
        "commit", "--award", "AW-100", "--source", "State U", "--type", "cash",
        "--committed", "30000", "--commitments", commitments_path,
    ])
    assert rc == 0
    assert os.path.exists(commitments_path)

    rc = L.main([
        "contribute", "--award", "AW-100", "--date", "2026-01-01", "--source", "State U",
        "--amount", "10000", "--doc", "receipt.pdf", "--contributions", contributions_path,
    ])
    assert rc == 0
    assert os.path.exists(contributions_path)

    capsys.readouterr()
    rc = L.main([
        "status", "--award", "AW-100", "--commitments", commitments_path,
        "--contributions", contributions_path, "--institution", "State U",
    ])
    assert rc == 0
    out = capsys.readouterr().out
    assert "AW-100" in out
    assert "SHORTFALL" in out


def test_report_contains_flags_section(tmp_path):
    commitments_path = str(tmp_path / "COMMITMENTS.csv")
    contributions_path = str(tmp_path / "CONTRIBUTIONS.csv")
    L.main(["commit", "--award", "AW-200", "--source", "Partner Org", "--type", "in-kind",
            "--committed", "15000", "--commitments", commitments_path])
    L.main(["contribute", "--award", "AW-200", "--date", "2026-01-01", "--source", "Partner Org",
            "--amount", "5000", "--doc", "", "--contributions", contributions_path])

    out_path = str(tmp_path / "report.md")
    rc = L.main([
        "report", "--commitments", commitments_path, "--contributions", contributions_path,
        "--institution", "State U", "--out", out_path,
    ])
    assert rc == 0
    with open(out_path, encoding="utf-8") as fh:
        content = fh.read()
    assert "## Flags detail" in content
    assert "AW-200" in content
    assert "shortfall" in content.lower()
    assert "no doc reference" in content
    assert "may need a letter" in content
    assert "—" not in content  # no em dashes


def test_unknown_award_status_exits_1(tmp_path):
    commitments_path = str(tmp_path / "COMMITMENTS.csv")
    L.main(["commit", "--award", "KNOWN", "--source", "X", "--type", "cash",
            "--committed", "1000", "--commitments", commitments_path])
    with pytest.raises(SystemExit) as exc:
        L.main(["status", "--award", "UNKNOWN", "--commitments", commitments_path,
                "--contributions", str(tmp_path / "empty_contrib.csv"), "--institution", "X"])
    assert exc.value.code == 1
