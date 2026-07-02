"""Tests for tools/award_calendar.py.

Offline, deterministic (fixed --today), tmp_path only. Plain asserts.
"""
import datetime
import os
import subprocess
import sys

import pytest
import yaml

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_REPO, "tools"))

import award_calendar as A

_TOOL = os.path.join(_REPO, "tools", "award_calendar.py")


def _award(**overrides):
    award = {
        "start": "2026-01-01",
        "end": "2026-12-31",
        "reports": [
            {"type": "Financial report", "frequency": "quarterly",
             "due_days_after_period_end": 30},
        ],
    }
    award.update(overrides)
    return award


def _write(tmp_path, award):
    p = tmp_path / "award.yml"
    p.write_text(yaml.safe_dump(award), encoding="utf-8")
    return str(p)


def test_quarterly_periods_and_due_dates():
    rows = A.build_schedule(_award())
    assert len(rows) == 4
    assert rows[0]["period_end"] == datetime.date(2026, 3, 31)
    assert rows[0]["due"] == datetime.date(2026, 4, 30)
    assert rows[-1]["period_end"] == datetime.date(2026, 12, 31)
    assert rows[-1]["due"] == datetime.date(2027, 1, 30)


def test_final_report_due_after_award_end():
    award = _award(reports=[{"type": "Final RPPR", "frequency": "final",
                             "due_days_after_period_end": 120}])
    rows = A.build_schedule(award)
    assert len(rows) == 1
    assert rows[0]["due"] == datetime.date(2027, 4, 30)


def test_add_months_clamps_day_of_month():
    assert A.add_months(datetime.date(2026, 1, 31), 1) == datetime.date(2026, 2, 28)
    assert A.add_months(datetime.date(2024, 1, 31), 1) == datetime.date(2024, 2, 29)
    assert A.add_months(datetime.date(2026, 11, 30), 3) == datetime.date(2027, 2, 28)


def test_other_deadlines_appear_in_schedule():
    award = _award(other_deadlines=[{"item": "IRB renewal", "date": "2026-05-05"}])
    rows = A.build_schedule(award)
    hits = [r for r in rows if r["item"] == "IRB renewal"]
    assert len(hits) == 1
    assert hits[0]["due"] == datetime.date(2026, 5, 5)
    assert hits[0]["period"] == "one-time"


def test_overdue_status_against_fixed_today(tmp_path):
    path = _write(tmp_path, _award())
    out = tmp_path / "schedule.md"
    assert A.main(["--award", path, "--today", "2026-06-01",
                   "--out", str(out)]) == 0
    text = out.read_text(encoding="utf-8")
    assert "OVERDUE" in text          # P1 due 2026-04-30 is past
    assert "scheduled" in text        # P4 due 2027-01-30 is far out
    assert "advisory" in text.lower()
    assert "—" not in text


def test_ics_structure_and_escaping(tmp_path):
    award = _award(reports=[{"type": "Financial, quarterly", "frequency": "annual",
                             "due_days_after_period_end": 60}])
    path = _write(tmp_path, award)
    ics_path = tmp_path / "award.ics"
    out = tmp_path / "schedule.md"
    assert A.main(["--award", path, "--today", "2026-01-01",
                   "--ics", str(ics_path), "--out", str(out)]) == 0
    ics = ics_path.read_text(encoding="utf-8")
    assert ics.startswith("BEGIN:VCALENDAR")
    assert ics.count("BEGIN:VEVENT") == 1
    assert "Financial\\, quarterly" in ics   # comma escaped per RFC 5545
    assert "DTSTART;VALUE=DATE:20270301" in ics  # 2026-12-31 + 60 days


def test_end_before_start_is_invalid_input(tmp_path):
    path = _write(tmp_path, _award(start="2027-01-01", end="2026-01-01"))
    with pytest.raises(SystemExit) as exc:
        A.main(["--award", path, "--today", "2026-01-01"])
    assert exc.value.code == 1


def test_help_exits_zero():
    proc = subprocess.run([sys.executable, _TOOL, "--help"],
                          capture_output=True, text=True)
    assert proc.returncode == 0
    assert "--ics" in proc.stdout
