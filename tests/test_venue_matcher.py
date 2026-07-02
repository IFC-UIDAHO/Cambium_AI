#!/usr/bin/env python3
"""Tests for tools/venue_matcher.py.

Offline pytest checks: runs the CLI as a subprocess against tmp_path
abstracts and inspects the ranked Markdown report.
"""
from __future__ import annotations
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = os.path.join(ROOT, "tools", "venue_matcher.py")

ML_ABSTRACT = (
    "We study reinforcement learning with deep neural network function "
    "approximation. Our machine learning benchmark evaluates optimization "
    "and training of deep learning agents."
)

FOREST_ABSTRACT = (
    "Thinning treatments in mixed conifer forest plots: a silviculture "
    "field experiment measuring timber growth and wildfire risk."
)


def run_tool(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, TOOL, *args], capture_output=True, text=True, cwd=ROOT
    )


def write_abstract(tmp_path, text):
    path = tmp_path / "abstract.txt"
    path.write_text(text, encoding="utf-8")
    return str(path)


def test_ml_abstract_ranks_neurips_first(tmp_path):
    result = run_tool("--abstract", write_abstract(tmp_path, ML_ABSTRACT))
    assert result.returncode == 0, result.stderr
    assert "### 1. NeurIPS" in result.stdout
    assert "machine learning" in result.stdout  # matched term is reported


def test_forest_abstract_matches_forest_journal(tmp_path):
    result = run_tool("--abstract", write_abstract(tmp_path, FOREST_ABSTRACT))
    assert result.returncode == 0, result.stderr
    assert "### 1. Forest Ecology and Management" in result.stdout
    assert "silviculture" in result.stdout


def test_custom_profiles_replace_builtins(tmp_path):
    profiles = tmp_path / "profiles.yml"
    profiles.write_text(
        "- name: Journal of Zebrafish Research\n"
        "  scope: [zebrafish, \"larval development\"]\n"
        "  methods: [imaging]\n"
        "  notes: Example custom venue profile.\n",
        encoding="utf-8",
    )
    abstract = write_abstract(tmp_path, "We observe larval development in zebrafish.")
    result = run_tool("--abstract", abstract, "--profiles", str(profiles))
    assert result.returncode == 0, result.stderr
    assert "Journal of Zebrafish Research" in result.stdout
    assert "NeurIPS" not in result.stdout  # built-ins fully replaced
    assert "user profiles from" in result.stdout


def test_k_limits_number_of_entries(tmp_path):
    result = run_tool("--abstract", write_abstract(tmp_path, ML_ABSTRACT), "--k", "2")
    assert result.returncode == 0, result.stderr
    assert result.stdout.count("### ") == 2


def test_zero_overlap_reported_honestly(tmp_path):
    result = run_tool("--abstract", write_abstract(tmp_path, "qqqq zzzz xyzzy plugh"))
    assert result.returncode == 0, result.stderr
    assert "No venue had any keyword overlap" in result.stdout


def test_caveat_present(tmp_path):
    result = run_tool("--abstract", write_abstract(tmp_path, ML_ABSTRACT))
    assert "coarse lexical heuristic" in result.stdout
    assert "not editorial advice" in result.stdout


def test_missing_abstract_exits_1(tmp_path):
    result = run_tool("--abstract", str(tmp_path / "absent.txt"))
    assert result.returncode == 1
    assert "not found" in result.stderr


def test_no_em_dash_in_source():
    with open(TOOL, encoding="utf-8") as fh:
        assert "\u2014" not in fh.read()
