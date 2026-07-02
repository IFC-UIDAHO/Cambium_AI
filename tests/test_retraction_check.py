#!/usr/bin/env python3
"""Tests for tools/retraction_check.py.

Fully offline pytest checks: every run uses --input-json fixtures so the
network is never touched. Runs the CLI as a subprocess against tmp_path
files and inspects the Markdown report.
"""
from __future__ import annotations
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = os.path.join(ROOT, "tools", "retraction_check.py")

FIXTURE = {
    "10.5555/retracted.1": {
        "message": {
            "updated-by": [
                {"DOI": "10.5555/notice.1", "type": "retraction", "label": "Retraction"}
            ]
        }
    },
    "10.5555/corrected.1": {
        "message": {"updated-by": [{"DOI": "10.5555/err.1", "type": "correction"}]}
    },
    "10.5555/concern.1": {
        "message": {"updated-by": [{"DOI": "10.5555/eoc.1", "type": "expression_of_concern"}]}
    },
    "10.5555/clean.1": {"message": {"title": ["A fine paper"]}},
}


def run_tool(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, TOOL, *args], capture_output=True, text=True, cwd=ROOT
    )


def write_fixture(tmp_path, data=None) -> str:
    path = tmp_path / "fixture.json"
    path.write_text(json.dumps(data if data is not None else FIXTURE), encoding="utf-8")
    return str(path)


def row_for(stdout: str, doi: str) -> str:
    rows = [line for line in stdout.splitlines() if line.startswith(f"| {doi} ")]
    assert rows, f"no table row for {doi} in output:\n{stdout}"
    return rows[0]


def test_statuses_classified_from_fixture(tmp_path):
    fixture = write_fixture(tmp_path)
    result = run_tool(
        "--dois", "10.5555/clean.1", "10.5555/retracted.1",
        "10.5555/corrected.1", "10.5555/concern.1",
        "--input-json", fixture,
    )
    assert result.returncode == 0, result.stderr
    assert "| OK |" in row_for(result.stdout, "10.5555/clean.1")
    assert "| RETRACTED |" in row_for(result.stdout, "10.5555/retracted.1")
    assert "| CORRECTED |" in row_for(result.stdout, "10.5555/corrected.1")
    assert "| CONCERN |" in row_for(result.stdout, "10.5555/concern.1")
    assert "- DOIs checked: 4" in result.stdout


def test_strict_exits_1_only_on_retracted(tmp_path):
    fixture = write_fixture(tmp_path)
    with_retracted = run_tool(
        "--dois", "10.5555/retracted.1", "--input-json", fixture, "--strict"
    )
    assert with_retracted.returncode == 1
    assert "STRICT" in with_retracted.stderr
    without_retracted = run_tool(
        "--dois", "10.5555/corrected.1", "10.5555/concern.1",
        "--input-json", fixture, "--strict",
    )
    assert without_retracted.returncode == 0, without_retracted.stderr


def test_missing_fixture_entry_is_unchecked_and_exit_0(tmp_path):
    fixture = write_fixture(tmp_path)
    result = run_tool("--dois", "10.5555/unknown.1", "--input-json", fixture, "--strict")
    assert result.returncode == 0, result.stderr
    assert "| UNCHECKED |" in row_for(result.stdout, "10.5555/unknown.1")


def test_bib_extraction_finds_field_and_url_dois(tmp_path):
    bib = tmp_path / "refs.bib"
    bib.write_text(
        "@article{clean2020,\n"
        "  title = {A fine paper},\n"
        "  doi = {10.5555/clean.1},\n"
        "}\n"
        "@misc{retr2019,\n"
        "  url = {https://doi.org/10.5555/retracted.1},\n"
        "}\n",
        encoding="utf-8",
    )
    result = run_tool("--bib", str(bib), "--input-json", write_fixture(tmp_path))
    assert result.returncode == 0, result.stderr
    assert "- DOIs checked: 2" in result.stdout
    assert "| OK |" in row_for(result.stdout, "10.5555/clean.1")
    assert "| RETRACTED |" in row_for(result.stdout, "10.5555/retracted.1")


def test_update_to_fragment_and_mixed_case_type(tmp_path):
    data = {
        "10.5555/upd.1": {"update-to": [{"DOI": "10.5555/x.1", "type": "Retraction"}]}
    }
    result = run_tool("--dois", "10.5555/upd.1", "--input-json", write_fixture(tmp_path, data))
    assert result.returncode == 0, result.stderr
    assert "| RETRACTED |" in row_for(result.stdout, "10.5555/upd.1")


def test_invalid_inputs_exit_1(tmp_path):
    no_doi_bib = tmp_path / "empty.bib"
    no_doi_bib.write_text("@article{x, title = {No identifiers here}}\n", encoding="utf-8")
    assert run_tool("--bib", str(no_doi_bib)).returncode == 1
    assert run_tool("--bib", str(tmp_path / "absent.bib")).returncode == 1


def test_honest_wording_and_no_em_dash(tmp_path):
    fixture = write_fixture(tmp_path)
    result = run_tool("--dois", "10.5555/clean.1", "--input-json", fixture)
    assert "advisory, not a certification" in result.stdout
    assert "not proof of integrity" in result.stdout
    assert "\u2014" not in result.stdout
    with open(TOOL, encoding="utf-8") as fh:
        assert "\u2014" not in fh.read()
