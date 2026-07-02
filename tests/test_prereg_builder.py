#!/usr/bin/env python3
"""Tests for tools/prereg_builder.py.

Offline pytest checks: runs the CLI as a subprocess (matching real usage)
against tmp_path fixtures and inspects the rendered Markdown.
"""
from __future__ import annotations
import json
import os
import subprocess
import sys

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = os.path.join(ROOT, "tools", "prereg_builder.py")

COMPLETE_SPEC = {
    "title": "Effect of cover crops on spring soil nitrate",
    "hypotheses": ["H1: cover-cropped plots show lower spring nitrate than fallow plots"],
    "design": "Randomized complete block design, 4 blocks, 2 treatments.",
    "sample_plan": "24 plots; size fixed by available field area.",
    "outcomes": ["Spring soil nitrate (mg/kg) at 0-30 cm depth"],
    "analysis_plan": "Linear mixed model with block as a random intercept.",
}


def run_tool(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, TOOL, *args], capture_output=True, text=True, cwd=ROOT
    )


def write_spec(path, data) -> None:
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def test_template_prints_starter_spec():
    result = run_tool("--template")
    assert result.returncode == 0
    for key in ("title:", "hypotheses:", "design:", "sample_plan:", "outcomes:", "analysis_plan:"):
        assert key in result.stdout
    assert "TODO" in result.stdout


def test_complete_spec_renders_numbered_sections(tmp_path):
    spec_path = tmp_path / "study.yml"
    write_spec(spec_path, COMPLETE_SPEC)
    result = run_tool("--spec", str(spec_path))
    assert result.returncode == 0
    assert "## 1. Title" in result.stdout
    assert "## 2. Hypotheses" in result.stdout
    assert "## 6. Analysis plan" in result.stdout
    assert "cover-cropped plots" in result.stdout
    assert "Missing or empty: none" in result.stdout


def test_missing_sections_listed_but_exit_0(tmp_path):
    spec = dict(COMPLETE_SPEC)
    del spec["outcomes"]
    spec["design"] = ""
    spec_path = tmp_path / "study.yml"
    write_spec(spec_path, spec)
    result = run_tool("--spec", str(spec_path))
    assert result.returncode == 0
    missing_lines = [line for line in result.stdout.splitlines() if "Missing or empty" in line]
    assert missing_lines
    assert "design" in missing_lines[0]
    assert "outcomes" in missing_lines[0]


def test_strict_incomplete_exits_1(tmp_path):
    spec = dict(COMPLETE_SPEC)
    del spec["analysis_plan"]
    spec_path = tmp_path / "study.yml"
    write_spec(spec_path, spec)
    result = run_tool("--spec", str(spec_path), "--strict")
    assert result.returncode == 1
    assert "STRICT" in result.stderr


def test_json_spec_accepted(tmp_path):
    spec_path = tmp_path / "study.json"
    spec_path.write_text(json.dumps(COMPLETE_SPEC), encoding="utf-8")
    result = run_tool("--spec", str(spec_path))
    assert result.returncode == 0
    assert "Missing or empty: none" in result.stdout


def test_out_flag_writes_file(tmp_path):
    spec_path = tmp_path / "study.yml"
    write_spec(spec_path, COMPLETE_SPEC)
    out_path = tmp_path / "prereg.md"
    result = run_tool("--spec", str(spec_path), "--out", str(out_path))
    assert result.returncode == 0
    text = out_path.read_text(encoding="utf-8")
    assert "Preregistration draft" in text


def test_invalid_spec_exits_1(tmp_path):
    missing = run_tool("--spec", str(tmp_path / "nope.yml"))
    assert missing.returncode == 1
    bad_path = tmp_path / "bad.json"
    bad_path.write_text("{not json", encoding="utf-8")
    bad = run_tool("--spec", str(bad_path))
    assert bad.returncode == 1


def test_no_em_dash_in_source_or_output(tmp_path):
    with open(TOOL, encoding="utf-8") as fh:
        assert "\u2014" not in fh.read()
    spec_path = tmp_path / "study.yml"
    write_spec(spec_path, COMPLETE_SPEC)
    result = run_tool("--spec", str(spec_path))
    assert "\u2014" not in result.stdout
