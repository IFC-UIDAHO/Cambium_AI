#!/usr/bin/env python3
"""Tests for tools/power_calc.py.

Offline pytest checks: runs the CLI as a subprocess and validates results
against known reference values (normal-approximation formulas from Fleiss
1981 and Cohen 1988), using sane ranges rather than brittle exact matches.
"""
from __future__ import annotations
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = os.path.join(ROOT, "tools", "power_calc.py")


def run_tool(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, TOOL, *args], capture_output=True, text=True, cwd=ROOT
    )


def get_required_n(stdout: str) -> int:
    match = re.search(r"Required n = (\d+)", stdout)
    assert match, f"no 'Required n' line in output:\n{stdout}"
    return int(match.group(1))


def get_power(stdout: str) -> float:
    match = re.search(r"Achieved power = ([0-9.]+)", stdout)
    assert match, f"no 'Achieved power' line in output:\n{stdout}"
    return float(match.group(1))


def test_two_prop_matches_known_example():
    # Reference: p1=0.30, p2=0.15, alpha=0.05 one-sided, power=0.80 gives
    # approximately 95 per arm with the pooled normal approximation.
    result = run_tool("two-prop", "--p1", "0.30", "--p2", "0.15",
                      "--alpha", "0.05", "--tail", "one", "--power", "0.80")
    assert result.returncode == 0, result.stderr
    assert 90 <= get_required_n(result.stdout) <= 100


def test_two_mean_d_half_two_sided():
    # Reference: d=0.5, alpha=0.05 two-sided, power=0.80 gives about 63 per
    # group (normal approximation; t-based methods give about 64).
    result = run_tool("two-mean", "--d", "0.5")
    assert result.returncode == 0, result.stderr
    assert 60 <= get_required_n(result.stdout) <= 67


def test_corr_r_03_two_sided():
    # Reference: r=0.3, alpha=0.05 two-sided, power=0.80 gives about 84-85.
    result = run_tool("corr", "--r", "0.3")
    assert result.returncode == 0, result.stderr
    assert 82 <= get_required_n(result.stdout) <= 88


def test_achieved_power_mode_is_sane_and_monotone():
    r95 = run_tool("two-prop", "--p1", "0.30", "--p2", "0.15", "--tail", "one", "--n", "95")
    r200 = run_tool("two-prop", "--p1", "0.30", "--p2", "0.15", "--tail", "one", "--n", "200")
    assert r95.returncode == 0 and r200.returncode == 0
    p95 = get_power(r95.stdout)
    p200 = get_power(r200.stdout)
    assert 0.75 <= p95 <= 0.85
    assert p200 > p95


def test_invalid_inputs_exit_1():
    assert run_tool("two-prop", "--p1", "0.3", "--p2", "0.3").returncode == 1
    assert run_tool("two-mean", "--d", "0.5", "--alpha", "1.5").returncode == 1
    assert run_tool("corr", "--r", "0").returncode == 1


def test_honest_note_and_formula_present():
    result = run_tool("two-mean", "--d", "0.5")
    assert "statistician" in result.stdout
    assert "advisory" in result.stdout.lower()
    assert "n per group = 2 * ((z_a + z_b) / d)^2" in result.stdout
    assert "\u2014" not in result.stdout  # no em dashes


def test_out_flag_writes_file(tmp_path):
    out_path = tmp_path / "power.md"
    result = run_tool("corr", "--r", "0.3", "--out", str(out_path))
    assert result.returncode == 0
    assert "Required n" in out_path.read_text(encoding="utf-8")
