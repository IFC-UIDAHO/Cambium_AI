"""Tests for tools/policy_diff.py.

Offline, deterministic, tmp_path only. Plain asserts.
"""
import os
import subprocess
import sys

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_REPO, "tools"))

import policy_diff as P

_TOOL = os.path.join(_REPO, "tools", "policy_diff.py")

OLD = """Introduction. We appreciate your interest in this program.

Proposals must be submitted within 30 days of the posting date.
Applicants shall include a budget justification.
The page limit is 15 pages.
"""

NEW = """Introduction. We appreciate your interest in this program very much.

Proposals must be submitted within 45 days of the posting date.
Applicants shall include a budget justification.
A data management plan is required for all proposals.
"""


def _diff(old_text=OLD, new_text=NEW):
    return P.diff_requirements(P.split_units(old_text), P.split_units(new_text))


def test_added_requirement_detected():
    added, _, _ = _diff()
    assert any("data management plan" in a.lower() for a in added)


def test_removed_requirement_detected():
    _, removed, _ = _diff()
    assert any("page limit" in r.lower() for r in removed)


def test_changed_sentence_paired_with_both_versions():
    _, _, changed = _diff()
    pairs = [c for c in changed if "30 days" in c["old"] and "45 days" in c["new"]]
    assert len(pairs) == 1
    assert pairs[0]["overlap"] >= P.PAIR_THRESHOLD


def test_unchanged_and_non_requirement_sentences_not_reported():
    added, removed, changed = _diff()
    all_text = " ".join(added + removed
                        + [c["old"] for c in changed] + [c["new"] for c in changed])
    assert "budget justification" not in all_text   # identical in both versions
    assert "appreciate" not in all_text             # changed, but not requirement-bearing


def test_identical_files_report_no_changes():
    added, removed, changed = _diff(OLD, OLD)
    assert added == [] and removed == [] and changed == []


def test_report_has_diff_appendix_and_honest_note(tmp_path):
    old_path = tmp_path / "v1.txt"
    new_path = tmp_path / "v2.txt"
    old_path.write_text(OLD, encoding="utf-8")
    new_path.write_text(NEW, encoding="utf-8")
    out = tmp_path / "diff.md"
    assert P.main(["--old", str(old_path), "--new", str(new_path),
                   "--out", str(out)]) == 0
    text = out.read_text(encoding="utf-8")
    assert "```diff" in text
    assert "@@" in text                      # unified diff hunks present
    assert "not legal interpretation" in text.lower()
    assert "advisory" in text.lower()
    assert "—" not in text


def test_help_exits_zero():
    proc = subprocess.run([sys.executable, _TOOL, "--help"],
                          capture_output=True, text=True)
    assert proc.returncode == 0
    assert "--old" in proc.stdout
