"""Tests for tools/portfolio_report.py.

Verifies: fixture tree rollup is correct, missing files are tolerated (cell "-"), open-P0
counting matches the fixture, both json + md are written, and an empty root exits 0 with
a note. Also runs one integration test against the real repo's examples/ directory (a
mixed bag of demo projects, some with GATES.md, some without -- must not crash).
"""
import csv
import json
import os
import sys
import tempfile
import textwrap

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_REPO, "tools"))

import portfolio_report as PR


def _mk_root():
    return tempfile.mkdtemp()


def _write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)


def _write_ledger(path, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["id", "issue", "agents", "severity", "claim_tier", "evidence", "status", "action"])
        for row in rows:
            w.writerow(row)


def _mk_fixture_tree():
    """Build a two-project fixture: proj-a (fully populated), proj-b (mostly missing files)."""
    root = _mk_root()

    proj_a = os.path.join(root, "proj-a")
    _write(os.path.join(proj_a, "governance", "GATES.md"), textwrap.dedent("""\
        # Gates
        ## Approvals log
        | Gate | Date | Approver | Decision | Notes |
        |---|---|---|---|---|
        | G1 | 2026-01-01 | Director | APPROVE | pursue |
        | G4 | 2026-02-15 | Director | APPROVE | ship fixes |
    """))
    _write(os.path.join(proj_a, "run_state.json"), json.dumps({"phase": "development"}))
    _write_ledger(os.path.join(proj_a, "agent_outputs", "findings_ledger.csv"), [
        ["F1", "leak", "verify-evidence", "P0", "Code-verified", "e", "open", "fix"],
        ["F2", "no baseline", "verify-evidence", "P1", "Asserted", "e", "open", "fix"],
        ["F3", "typo", "verify-evidence", "P2", "Asserted", "e", "open", "fix"],
        ["F4", "resolved leak", "verify-evidence", "P0", "Code-verified", "e", "accepted", "fixed"],
    ])
    _write(os.path.join(proj_a, "agent_outputs", "ai_disclosure.md"), "# AI Use Disclosure\n")

    proj_b = os.path.join(root, "proj-b")
    os.makedirs(proj_b, exist_ok=True)  # a project dir with nothing else inside it

    return root


def test_fixture_tree_rollup_correct():
    root = _mk_fixture_tree()
    rows = PR.build_rollup(root)
    by_name = {r["project"]: r for r in rows}

    a = by_name["proj-a"]
    assert a["latest_gate"].startswith("G4")
    assert a["phase"] == "development"
    assert a["open_p0"] == 1
    assert a["open_p1"] == 1
    assert a["disclosure"] == "yes"


def test_missing_files_tolerated_with_dash():
    root = _mk_fixture_tree()
    rows = PR.build_rollup(root)
    by_name = {r["project"]: r for r in rows}

    b = by_name["proj-b"]
    assert b["latest_gate"] == "-"
    assert b["phase"] == "-"
    assert b["open_p0"] == 0
    assert b["open_p1"] == 0
    assert b["disclosure"] == "no"


def test_open_p0_counting_excludes_accepted_and_p2():
    root = _mk_fixture_tree()
    p0, p1 = PR.open_p0_p1_counts(os.path.join(root, "proj-a"))
    assert p0 == 1  # F4 is P0 but accepted, so it must not count
    assert p1 == 1


def test_json_and_md_both_written():
    root = _mk_fixture_tree()
    stem = os.path.join(root, "out", "portfolio")
    rc = PR.main(["--root", root, "--out", stem])
    assert rc == 0
    assert os.path.isfile(stem + ".md")
    assert os.path.isfile(stem + ".json")
    data = json.loads(open(stem + ".json", encoding="utf-8").read())
    assert len(data["projects"]) == 2


def test_empty_root_exits_0_with_note(capsys):
    root = _mk_root()  # no subdirectories at all
    stem = os.path.join(root, "out", "portfolio")
    rc = PR.main(["--root", os.path.join(root, "nonexistent"), "--out", stem])
    assert rc == 0
    captured = capsys.readouterr()
    assert "note" in captured.out.lower()


def test_empty_root_writes_no_projects_row():
    root = _mk_root()
    rows = PR.build_rollup(os.path.join(root, "does_not_exist"))
    assert rows == []
    report = PR.render_markdown(rows, root)
    assert "No project" in report


def test_markdown_report_lists_project_row():
    root = _mk_fixture_tree()
    rows = PR.build_rollup(root)
    report = PR.render_markdown(rows, root)
    assert "proj-a" in report
    assert "proj-b" in report


def test_disclosure_glob_matches_prefixed_filenames():
    root = _mk_root()
    proj = os.path.join(root, "p1")
    _write(os.path.join(proj, "agent_outputs", "ai_disclosure_20260701.md"), "x")
    assert PR.disclosure_present(proj) is True


def test_integration_against_real_examples_dir_does_not_crash():
    """examples/ is a mixed bag of real demo projects: some have GATES.md, some do not,
    some have findings_ledger.csv at project root instead of under agent_outputs/. Must
    not crash and must produce one row per subdirectory."""
    examples_root = os.path.join(_REPO, "examples")
    rows = PR.build_rollup(examples_root)
    assert len(rows) == len(PR.list_projects(examples_root))
    for r in rows:
        assert r["disclosure"] in ("yes", "no")
        assert isinstance(r["open_p0"], int)
        assert isinstance(r["open_p1"], int)

    # full-lifecycle ships a real governance/GATES.md; must resolve to something other than "-"
    by_name = {r["project"]: r for r in rows}
    assert by_name["full-lifecycle"]["latest_gate"] != "-"


def test_findings_ledger_found_at_any_depth():
    """e2e-worked-example keeps findings_ledger.csv at the project root, not under
    agent_outputs/ -- the glob('**') scan must still find it."""
    root = _mk_root()
    proj = os.path.join(root, "flat-ledger-proj")
    _write_ledger(os.path.join(proj, "findings_ledger.csv"), [
        ["F1", "issue", "agent", "P0", "Asserted", "e", "open", "fix"],
    ])
    p0, p1 = PR.open_p0_p1_counts(proj)
    assert p0 == 1
