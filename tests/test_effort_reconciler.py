"""Tests for tools/effort_reconciler.py.

Offline, deterministic, tmp_path only. Plain asserts.
"""
import os
import subprocess
import sys

import pytest
import yaml

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_REPO, "tools"))

import effort_reconciler as E

_TOOL = os.path.join(_REPO, "tools", "effort_reconciler.py")


def _data(appointment="calendar", projects=None):
    return {"people": [{"name": "Dr. A", "appointment": appointment,
                        "projects": projects or []}]}


def _write(tmp_path, data):
    p = tmp_path / "commitments.yml"
    p.write_text(yaml.safe_dump(data), encoding="utf-8")
    return str(p)


def test_full_year_converts_to_twelve_and_is_near_cap():
    data = _data(appointment="academic9+summer", projects=[
        {"name": "P1", "acad_months": 9, "period": "Y1"},
        {"name": "P1 summer", "sum_months": 3, "period": "Y1"},
    ])
    a = E.analyze(data, warn_at=11.4)
    agg = a["people"][0]["periods"]["Y1"]
    assert abs(agg["total"] - 12.0) < 1e-9  # 12 cal = 9 acad + 3 summer
    assert agg["status"] == "NEAR CAP"  # 12.0 is at cap, not over it
    assert a["flags"] == []


def test_over_commitment_flags_and_strict_exits_one(tmp_path):
    data = _data(projects=[
        {"name": "P1", "cal_months": 8, "period": "Y1"},
        {"name": "P2", "cal_months": 5, "period": "Y1"},
    ])
    a = E.analyze(data, warn_at=11.4)
    assert a["people"][0]["periods"]["Y1"]["status"] == "OVER"
    assert any("100 percent" in f for f in a["flags"])
    path = _write(tmp_path, data)
    out = str(tmp_path / "r.md")
    assert E.main(["--commitments", path, "--out", out]) == 0
    assert E.main(["--commitments", path, "--out", out, "--strict"]) == 1


def test_near_cap_warns_but_does_not_trip_strict(tmp_path):
    data = _data(projects=[{"name": "P1", "cal_months": 11.5, "period": "Y1"}])
    a = E.analyze(data, warn_at=11.4)
    assert a["people"][0]["periods"]["Y1"]["status"] == "NEAR CAP"
    assert a["warnings"] and not a["flags"]
    path = _write(tmp_path, data)
    out = str(tmp_path / "r.md")
    assert E.main(["--commitments", path, "--out", out, "--strict"]) == 0


def test_academic9_with_summer_months_flags():
    data = _data(appointment="academic9", projects=[
        {"name": "P1", "sum_months": 1, "period": "Y1"},
    ])
    a = E.analyze(data, warn_at=11.4)
    assert any("summer" in f.lower() for f in a["flags"])


def test_periods_are_totaled_separately():
    data = _data(projects=[
        {"name": "P1", "cal_months": 6, "period": "Y1"},
        {"name": "P2", "cal_months": 7, "period": "Y2"},
    ])
    a = E.analyze(data, warn_at=11.4)
    periods = a["people"][0]["periods"]
    assert abs(periods["Y1"]["total"] - 6.0) < 1e-9
    assert abs(periods["Y2"]["total"] - 7.0) < 1e-9
    assert a["flags"] == []  # 13 total across two periods is fine


def test_nonnumeric_months_is_invalid_input():
    data = _data(projects=[{"name": "P1", "cal_months": "two", "period": "Y1"}])
    with pytest.raises(SystemExit) as exc:
        E.analyze(data, warn_at=11.4)
    assert exc.value.code == 1


def test_report_is_advisory_and_names_source(tmp_path):
    data = _data(projects=[{"name": "P1", "cal_months": 2, "period": "Y1"}])
    path = _write(tmp_path, data)
    out = tmp_path / "r.md"
    assert E.main(["--commitments", path, "--out", str(out)]) == 0
    text = out.read_text(encoding="utf-8")
    assert "advisory" in text.lower()
    assert "2 CFR 200.430" in text
    assert "not an effort certification" in text.lower()
    assert "—" not in text


def test_help_exits_zero():
    proc = subprocess.run([sys.executable, _TOOL, "--help"],
                          capture_output=True, text=True)
    assert proc.returncode == 0
    assert "--warn-at" in proc.stdout
