#!/usr/bin/env python3
"""Tests for tools/subaward_register.py.

Stdlib only. Uses tmp_path for the register and invoice CSVs; never touches
the live repo data. Covers burn math, over-invoice flag, out-of-period flag,
low-burn-near-end flag, report contains all subawards, and unknown id exit 1.
"""
from __future__ import annotations
import os
import sys
from datetime import datetime

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_REPO, "tools"))

import pytest
import subaward_register as S


# ---------------------------------------------------------------------------
# Burn math
# ---------------------------------------------------------------------------

def test_burn_math_basic():
    subaward = {"org": "State U", "pi": "A. Smith", "total": 100000, "start": "2026-01-01", "end": "2026-12-31"}
    invoices = [
        {"id": "SA-1", "amount": 25000, "date": "2026-03-01"},
        {"id": "SA-1", "amount": 15000, "date": "2026-06-01"},
    ]
    today = datetime(2026, 7, 1)
    status = S.compute_status("SA-1", subaward, invoices, today)
    assert status["invoiced"] == pytest.approx(40000)
    assert status["burn"] == pytest.approx(0.40)
    assert status["remaining"] == pytest.approx(60000)
    assert status["flags"] == []


def test_zero_invoices_zero_burn():
    subaward = {"org": "X", "pi": "Y", "total": 50000, "start": "2026-01-01", "end": "2026-12-31"}
    status = S.compute_status("SA-2", subaward, [], datetime(2026, 3, 1))
    assert status["invoiced"] == 0
    assert status["burn"] == 0
    assert status["remaining"] == pytest.approx(50000)


# ---------------------------------------------------------------------------
# Over-invoice flag
# ---------------------------------------------------------------------------

def test_over_invoiced_flag():
    subaward = {"org": "X", "pi": "Y", "total": 10000, "start": "2026-01-01", "end": "2026-12-31"}
    invoices = [{"id": "SA-3", "amount": 12000, "date": "2026-02-01"}]
    status = S.compute_status("SA-3", subaward, invoices, datetime(2026, 3, 1))
    assert "OVER_INVOICED" in status["flags"]


def test_not_over_invoiced_when_exactly_total():
    subaward = {"org": "X", "pi": "Y", "total": 10000, "start": "2026-01-01", "end": "2026-12-31"}
    invoices = [{"id": "SA-4", "amount": 10000, "date": "2026-02-01"}]
    status = S.compute_status("SA-4", subaward, invoices, datetime(2026, 3, 1))
    assert "OVER_INVOICED" not in status["flags"]


# ---------------------------------------------------------------------------
# Out-of-period flag
# ---------------------------------------------------------------------------

def test_out_of_period_flag_before_start():
    subaward = {"org": "X", "pi": "Y", "total": 10000, "start": "2026-03-01", "end": "2026-12-31"}
    invoices = [{"id": "SA-5", "amount": 1000, "date": "2026-01-01"}]
    status = S.compute_status("SA-5", subaward, invoices, datetime(2026, 4, 1))
    assert "OUT_OF_PERIOD" in status["flags"]


def test_out_of_period_flag_after_end():
    subaward = {"org": "X", "pi": "Y", "total": 10000, "start": "2026-01-01", "end": "2026-06-30"}
    invoices = [{"id": "SA-6", "amount": 1000, "date": "2026-08-01"}]
    status = S.compute_status("SA-6", subaward, invoices, datetime(2026, 8, 15))
    assert "OUT_OF_PERIOD" in status["flags"]


def test_in_period_no_flag():
    subaward = {"org": "X", "pi": "Y", "total": 10000, "start": "2026-01-01", "end": "2026-12-31"}
    invoices = [{"id": "SA-7", "amount": 1000, "date": "2026-06-15"}]
    status = S.compute_status("SA-7", subaward, invoices, datetime(2026, 7, 1))
    assert "OUT_OF_PERIOD" not in status["flags"]


# ---------------------------------------------------------------------------
# Low-burn-near-end flag
# ---------------------------------------------------------------------------

def test_low_burn_near_end_flag():
    subaward = {"org": "X", "pi": "Y", "total": 100000, "start": "2026-01-01", "end": "2026-12-31"}
    invoices = [{"id": "SA-8", "amount": 20000, "date": "2026-06-01"}]  # 20% burn
    # today = Nov 15, end = Dec 31 -> 46 days left, within 60-day window
    today = datetime(2026, 11, 15)
    status = S.compute_status("SA-8", subaward, invoices, today)
    assert "LOW_BURN_NEAR_END" in status["flags"]


def test_no_low_burn_flag_when_far_from_end():
    subaward = {"org": "X", "pi": "Y", "total": 100000, "start": "2026-01-01", "end": "2026-12-31"}
    invoices = [{"id": "SA-9", "amount": 5000, "date": "2026-02-01"}]  # 5% burn
    today = datetime(2026, 3, 1)  # far from Dec 31
    status = S.compute_status("SA-9", subaward, invoices, today)
    assert "LOW_BURN_NEAR_END" not in status["flags"]


def test_no_low_burn_flag_when_burn_high_near_end():
    subaward = {"org": "X", "pi": "Y", "total": 100000, "start": "2026-01-01", "end": "2026-12-31"}
    invoices = [{"id": "SA-10", "amount": 60000, "date": "2026-06-01"}]  # 60% burn
    today = datetime(2026, 11, 15)  # near end but burn is high
    status = S.compute_status("SA-10", subaward, invoices, today)
    assert "LOW_BURN_NEAR_END" not in status["flags"]


# ---------------------------------------------------------------------------
# CLI integration -- add, invoice, status, report
# ---------------------------------------------------------------------------

def _register_path(tmp_path):
    return str(tmp_path / "SUBAWARDS.csv")


def _invoices_path(tmp_path):
    return str(tmp_path / "SUBAWARD_INVOICES.csv")


def test_cli_add_then_status(tmp_path, capsys):
    reg = _register_path(tmp_path)
    inv = _invoices_path(tmp_path)
    rc = S.main([
        "add", "--id", "SA-100", "--org", "State U", "--pi", "A. Smith",
        "--total", "50000", "--start", "2026-01-01", "--end", "2026-12-31",
        "--register", reg,
    ])
    assert rc == 0
    assert os.path.exists(reg)

    rc = S.main([
        "invoice", "--id", "SA-100", "--amount", "10000", "--date", "2026-03-01",
        "--register", reg, "--invoices", inv,
    ])
    assert rc == 0
    assert os.path.exists(inv)

    capsys.readouterr()
    rc = S.main(["status", "--id", "SA-100", "--register", reg, "--invoices", inv, "--today", "2026-04-01"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "SA-100" in out
    assert "burn=20.0%" in out


def test_report_contains_all_subawards(tmp_path):
    reg = _register_path(tmp_path)
    inv = _invoices_path(tmp_path)
    S.main(["add", "--id", "SA-A", "--org", "Org A", "--pi", "PI A", "--total", "10000",
            "--start", "2026-01-01", "--end", "2026-12-31", "--register", reg])
    S.main(["add", "--id", "SA-B", "--org", "Org B", "--pi", "PI B", "--total", "20000",
            "--start", "2026-01-01", "--end", "2026-12-31", "--register", reg])
    out_path = str(tmp_path / "report.md")
    rc = S.main(["report", "--register", reg, "--invoices", inv, "--today", "2026-06-01", "--out", out_path])
    assert rc == 0
    with open(out_path, encoding="utf-8") as fh:
        content = fh.read()
    assert "SA-A" in content
    assert "SA-B" in content
    assert "Org A" in content
    assert "Org B" in content
    assert "—" not in content  # no em dashes


def test_unknown_id_invoice_exits_1(tmp_path):
    reg = _register_path(tmp_path)
    S.main(["add", "--id", "SA-KNOWN", "--org", "X", "--pi", "Y", "--total", "1000",
            "--start", "2026-01-01", "--end", "2026-12-31", "--register", reg])
    with pytest.raises(SystemExit) as exc:
        S.main(["invoice", "--id", "SA-NOPE", "--amount", "100", "--date", "2026-02-01",
                "--register", reg, "--invoices", str(reg) + ".inv.csv"])
    assert exc.value.code == 1


def test_unknown_id_status_exits_1(tmp_path):
    reg = _register_path(tmp_path)
    S.main(["add", "--id", "SA-KNOWN2", "--org", "X", "--pi", "Y", "--total", "1000",
            "--start", "2026-01-01", "--end", "2026-12-31", "--register", reg])
    with pytest.raises(SystemExit) as exc:
        S.main(["status", "--id", "SA-NOPE2", "--register", reg, "--today", "2026-02-01"])
    assert exc.value.code == 1


def test_bad_date_on_add_exits_2(tmp_path):
    reg = _register_path(tmp_path)
    with pytest.raises(SystemExit) as exc:
        S.main(["add", "--id", "SA-BAD", "--org", "X", "--pi", "Y", "--total", "1000",
                "--start", "not-a-date", "--end", "2026-12-31", "--register", reg])
    assert exc.value.code == 2
