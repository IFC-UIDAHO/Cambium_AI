#!/usr/bin/env python3
"""Tests for tools/rebuttal_matrix.py.

Offline pytest checks: runs the CLI as a subprocess against tmp_path
fixtures and inspects the Markdown matrix it produces.
"""
from __future__ import annotations
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = os.path.join(ROOT, "tools", "rebuttal_matrix.py")


def run_tool(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, TOOL, *args], capture_output=True, text=True, cwd=ROOT
    )


def test_blank_line_split_joins_continuations(tmp_path):
    reviews = tmp_path / "reviews.txt"
    reviews.write_text(
        "The sample size seems small\nand underjustified.\n\n"
        "Figure 2 is unreadable at print size.\n\n"
        "Please release the analysis code.\n",
        encoding="utf-8",
    )
    result = run_tool("--reviews", str(reviews))
    assert result.returncode == 0, result.stderr
    assert "- Points parsed: 3" in result.stdout
    assert "small and underjustified" in result.stdout


def test_bullet_and_number_markers_split(tmp_path):
    reviews = tmp_path / "reviews.txt"
    reviews.write_text(
        "- Missing baseline comparison\n"
        "* Conclusions overclaim the evidence\n"
        "1. Typo in the abstract\n"
        "2) Wrong units in Table 1\n",
        encoding="utf-8",
    )
    result = run_tool("--reviews", str(reviews))
    assert result.returncode == 0, result.stderr
    assert "- Points parsed: 4" in result.stdout


def test_responses_fill_matrix_and_strict_passes(tmp_path):
    reviews = tmp_path / "reviews.txt"
    reviews.write_text("Justify the sample size.\n\nFigure 2 is unreadable.\n", encoding="utf-8")
    responses = tmp_path / "responses.yml"
    responses.write_text(
        "P1:\n"
        "  response: We added a power analysis in Section 2.3.\n"
        "  change_made: New Section 2.3.\n"
        "  evidence: Table 4.\n"
        "2: We redrew Figure 2 at 600 dpi.\n",
        encoding="utf-8",
    )
    result = run_tool("--reviews", str(reviews), "--responses", str(responses), "--strict")
    assert result.returncode == 0, result.stderr
    assert "We added a power analysis" in result.stdout
    assert "We redrew Figure 2" in result.stdout
    assert result.stdout.count("| filled |") == 2
    assert "- UNADDRESSED: 0" in result.stdout


def test_unaddressed_is_advisory_without_strict(tmp_path):
    reviews = tmp_path / "reviews.txt"
    reviews.write_text("Point one.\n\nPoint two.\n", encoding="utf-8")
    responses = tmp_path / "responses.yml"
    responses.write_text("P1:\n  response: Done.\n", encoding="utf-8")
    result = run_tool("--reviews", str(reviews), "--responses", str(responses))
    assert result.returncode == 0, result.stderr
    assert "UNADDRESSED: 1 (P2)" in result.stdout


def test_strict_exits_1_when_unaddressed(tmp_path):
    reviews = tmp_path / "reviews.txt"
    reviews.write_text("Point one.\n\nPoint two.\n", encoding="utf-8")
    result = run_tool("--reviews", str(reviews), "--strict")
    assert result.returncode == 1
    assert "STRICT" in result.stderr


def test_unknown_response_id_is_noted(tmp_path):
    reviews = tmp_path / "reviews.txt"
    reviews.write_text("Only one point here.\n", encoding="utf-8")
    responses = tmp_path / "responses.yml"
    responses.write_text("P9:\n  response: Response to a point that does not exist.\n", encoding="utf-8")
    result = run_tool("--reviews", str(reviews), "--responses", str(responses))
    assert result.returncode == 0, result.stderr
    assert "no matching point" in result.stdout
    assert "P9" in result.stdout


def test_missing_reviews_file_exits_1(tmp_path):
    result = run_tool("--reviews", str(tmp_path / "absent.txt"))
    assert result.returncode == 1
    assert "not found" in result.stderr


def test_no_em_dash_in_source():
    with open(TOOL, encoding="utf-8") as fh:
        assert "\u2014" not in fh.read()
