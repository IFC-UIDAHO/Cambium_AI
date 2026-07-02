#!/usr/bin/env python3
"""Tests for tools/effort_cert.py.

Stdlib only. Uses tmp_path for the ledger; never touches the live repo data.
Covers golden conversions for all three appointment types, cap proration,
no-cap passthrough, certify appends a parseable row, and invalid percent
exits 1.
"""
from __future__ import annotations
import csv
import os
import sys

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_REPO, "tools"))

import pytest
import effort_cert as E


# ---------------------------------------------------------------------------
# Golden conversions -- percent <-> person-months, all three appointment types
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "appt,percent,expected_pm",
    [
        ("calendar", 25, 3.0),
        ("calendar", 100, 12.0),
        ("academic", 25, 2.25),
        ("academic", 100, 9.0),
        ("summer", 100, 3.0),
        ("summer", 50, 1.5),
    ],
)
def test_percent_to_pm_golden(appt, percent, expected_pm):
    assert E.percent_to_pm(percent, appt) == pytest.approx(expected_pm)


@pytest.mark.parametrize(
    "appt,pm,expected_percent",
    [
        ("calendar", 3.0, 25.0),
        ("calendar", 12.0, 100.0),
        ("academic", 2.25, 25.0),
        ("academic", 9.0, 100.0),
        ("summer", 3.0, 100.0),
        ("summer", 1.5, 50.0),
    ],
)
def test_pm_to_percent_golden(appt, pm, expected_percent):
    assert E.pm_to_percent(pm, appt) == pytest.approx(expected_percent)


def test_roundtrip_all_appointment_types():
    """percent -> pm -> percent must roundtrip for every appointment type."""
    for appt in ("calendar", "academic", "summer"):
        for percent in (0, 10, 33.33, 50, 100):
            pm = E.percent_to_pm(percent, appt)
            back = E.pm_to_percent(pm, appt)
            assert back == pytest.approx(percent, abs=1e-9)


# ---------------------------------------------------------------------------
# Salary proration
# ---------------------------------------------------------------------------

def test_cap_proration_math():
    """salary above cap: chargeable uses the cap rate, not the actual salary."""
    # academic appt, 1 pm out of 9 = 1/9 fraction
    result = E.prorate_salary(salary=120000, pm=1.0, appt="academic", cap=90000)
    fraction = 1.0 / 9.0
    assert result["requested"] == pytest.approx(120000 * fraction)
    assert result["chargeable"] == pytest.approx(90000 * fraction)
    assert result["chargeable"] < result["requested"]


def test_no_cap_passthrough():
    """no cap given: chargeable equals requested exactly."""
    result = E.prorate_salary(salary=100000, pm=6.0, appt="calendar", cap=None)
    assert result["chargeable"] == pytest.approx(result["requested"])
    assert result["chargeable"] == pytest.approx(50000.0)


def test_salary_under_cap_no_proration():
    """salary at or under cap: chargeable equals requested even though cap is set."""
    result = E.prorate_salary(salary=80000, pm=3.0, appt="calendar", cap=90000)
    assert result["chargeable"] == pytest.approx(result["requested"])


# ---------------------------------------------------------------------------
# certify subcommand -- ledger row appended and parseable
# ---------------------------------------------------------------------------

def test_certify_row_appended_and_parseable(tmp_path):
    ledger = tmp_path / "EFFORT_LEDGER.csv"
    rc = E.main([
        "certify", "--appt", "academic", "--percent", "25",
        "--salary", "90000", "--cap", "80000",
        "--person", "J. Doe", "--award", "NSF-1234567",
        "--ledger", str(ledger),
    ])
    assert rc == 0
    assert ledger.exists()

    with open(ledger, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) == 1
    row = rows[0]
    assert row["person"] == "J. Doe"
    assert row["award"] == "NSF-1234567"
    assert row["appt"] == "academic"
    assert float(row["percent"]) == pytest.approx(25.0)
    assert float(row["pm"]) == pytest.approx(2.25)
    assert float(row["salary"]) == pytest.approx(90000.0)
    assert float(row["cap"]) == pytest.approx(80000.0)
    # chargeable should reflect the cap, not the raw salary
    fraction = 2.25 / 9.0
    assert float(row["chargeable"]) == pytest.approx(80000 * fraction)


def test_certify_appends_second_row_without_duplicating_header(tmp_path):
    ledger = tmp_path / "EFFORT_LEDGER.csv"
    for _ in range(2):
        rc = E.main([
            "certify", "--appt", "calendar", "--percent", "10",
            "--person", "A", "--award", "AWD-1",
            "--ledger", str(ledger),
        ])
        assert rc == 0
    with open(ledger, newline="", encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    # 1 header + 2 data rows
    assert len(lines) == 3
    assert lines[0].startswith("date,person,award")


# ---------------------------------------------------------------------------
# Invalid input -- exits 1
# ---------------------------------------------------------------------------

def test_percent_over_100_exits_1():
    with pytest.raises(SystemExit) as exc:
        E.main(["convert", "--appt", "calendar", "--percent", "150"])
    assert exc.value.code == 1


def test_percent_negative_exits_1():
    with pytest.raises(SystemExit) as exc:
        E.main(["convert", "--appt", "calendar", "--percent", "-5"])
    assert exc.value.code == 1


def test_bad_appointment_type_exits_1():
    with pytest.raises(SystemExit):
        E.main(["convert", "--appt", "quarterly", "--percent", "10"])


def test_missing_percent_and_pm_exits_1():
    with pytest.raises(SystemExit) as exc:
        E.main(["convert", "--appt", "calendar"])
    assert exc.value.code == 1


def test_both_percent_and_pm_exits_1():
    with pytest.raises(SystemExit) as exc:
        E.main(["convert", "--appt", "calendar", "--percent", "10", "--pm", "1"])
    assert exc.value.code == 1


# ---------------------------------------------------------------------------
# convert subcommand -- stdout formatting sanity
# ---------------------------------------------------------------------------

def test_convert_stdout_contains_advisory_note(capsys):
    rc = E.main(["convert", "--appt", "summer", "--percent", "100"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "ADVISORY" in out
    assert "3.0000" in out  # person-months for 100% summer
    assert "—" not in out  # no em dashes (Cambium house rule)
