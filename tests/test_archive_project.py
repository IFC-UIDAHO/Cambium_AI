"""Tests for tools/archive_project.py: retention/archival copies with hash manifest."""
import json, os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run(*args):
    return subprocess.run([sys.executable, os.path.join(ROOT, "tools", "archive_project.py"), *args],
                          capture_output=True, text=True)


def make_root(tmp_path):
    root = tmp_path / "repo"
    (root / "agent_outputs").mkdir(parents=True)
    (root / "agent_outputs" / "findings.md").write_text("finding one\n", encoding="utf-8")
    (root / "projects" / "alpha").mkdir(parents=True)
    (root / "projects" / "alpha" / "data.txt").write_text("alpha data\n", encoding="utf-8")
    (root / "governance").mkdir()
    (root / "governance" / "GATES.md").write_text(
        "## Approvals log\n| Gate | Date | Approver | Decision | Notes |\n|---|---|---|---|---|\n"
        "| G1 | 2026-01-01 | Alice | APPROVE | run: alpha kickoff |\n"
        "| G2 | 2026-01-02 | Bob | APPROVE | unrelated beta work |\n", encoding="utf-8")
    return root


def test_help_exits_0():
    assert run("--help").returncode == 0


def test_archive_project_copies_and_manifest(tmp_path):
    root = make_root(tmp_path)
    out = tmp_path / "arch"
    r = run("--root", str(root), "--project", "alpha", "--out", str(out),
            "--retention-note", "keep 7 years")
    assert r.returncode == 0, r.stdout + r.stderr
    m = json.loads((out / "MANIFEST.json").read_text(encoding="utf-8"))
    paths = [e["path"] for e in m["files"]]
    assert "agent_outputs/findings.md" in paths
    assert "projects/alpha/data.txt" in paths
    assert "GOVERNANCE_SUMMARY.md" in paths
    assert m["retention_note"] == "keep 7 years"
    assert "sha256" in m["files"][0] and len(m["files"][0]["sha256"]) == 64
    # governance summary filtered to rows mentioning the project
    summary = (out / "GOVERNANCE_SUMMARY.md").read_text(encoding="utf-8")
    assert "alpha kickoff" in summary and "beta work" not in summary


def test_sources_never_moved(tmp_path):
    root = make_root(tmp_path)
    out = tmp_path / "arch"
    assert run("--root", str(root), "--project", "alpha", "--out", str(out)).returncode == 0
    assert (root / "agent_outputs" / "findings.md").read_text(encoding="utf-8") == "finding one\n"
    assert (root / "projects" / "alpha" / "data.txt").exists()


def test_verify_ok_then_fails_after_tamper(tmp_path):
    root = make_root(tmp_path)
    out = tmp_path / "arch"
    assert run("--root", str(root), "--project", "alpha", "--out", str(out)).returncode == 0
    assert run("--verify", str(out)).returncode == 0
    (out / "agent_outputs" / "findings.md").write_text("altered\n", encoding="utf-8")
    r = run("--verify", str(out))
    assert r.returncode == 1 and "ALTERED" in r.stdout


def test_verify_flags_missing_file(tmp_path):
    root = make_root(tmp_path)
    out = tmp_path / "arch"
    assert run("--root", str(root), "--project", "alpha", "--out", str(out)).returncode == 0
    os.remove(out / "projects" / "alpha" / "data.txt")
    r = run("--verify", str(out))
    assert r.returncode == 1 and "MISSING" in r.stdout


def test_paths_mode(tmp_path):
    root = make_root(tmp_path)
    out = tmp_path / "arch2"
    r = run("--root", str(root), "--paths", "projects/alpha", "--out", str(out))
    assert r.returncode == 0, r.stdout
    assert (out / "projects" / "alpha" / "data.txt").exists()


def test_no_selection_exits_1(tmp_path):
    root = make_root(tmp_path)
    r = run("--root", str(root))
    assert r.returncode == 1 and "ERROR" in r.stdout


def test_bad_paths_exit_1(tmp_path):
    root = make_root(tmp_path)
    r = run("--root", str(root), "--paths", "does/not/exist", "--out", str(tmp_path / "a3"))
    assert r.returncode == 1
