"""Tests for tools/audit_bundle.py: auditor evidence pack (synthetic tmp fixtures)."""
import hashlib, json, os, re, subprocess, sys, zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import audit_log  # the real module whose verify() audit_bundle calls


def run(*args):
    return subprocess.run([sys.executable, os.path.join(ROOT, "tools", "audit_bundle.py"), *args],
                          capture_output=True, text=True)


def make_root(tmp_path, with_trail=True):
    root = tmp_path / "repo"
    (root / "governance").mkdir(parents=True)
    (root / "governance" / "GATES.md").write_text(
        "# Ledger\n\n## Approvals log\n| Gate | Date | Approver | Decision | Notes |\n"
        "|---|---|---|---|---|\n| G1 | 2026-01-01 | Director (T) | APPROVE | ok |\n",
        encoding="utf-8")
    (root / ".claude-plugin").mkdir()
    (root / ".claude-plugin" / "plugin.json").write_text(json.dumps({"version": "9.9.9"}), encoding="utf-8")
    (root / "examples" / "projA").mkdir(parents=True)
    (root / "examples" / "projA" / "provenance_manifest.json").write_text('{"schema": "x"}', encoding="utf-8")
    (root / "examples" / "projB").mkdir(parents=True)
    (root / "examples" / "projB" / "provenance_manifest.json").write_text('{"schema": "y"}', encoding="utf-8")
    if with_trail:
        old = audit_log.TRAIL
        audit_log.TRAIL = str(root / "governance" / "audit_trail.jsonl")
        try:
            audit_log.append("G1", "tester", "model-x", "q1", "r1", "APPROVE", "")
            audit_log.append("G2", "tester", "model-x", "q2", "r2", "APPROVE", "")
        finally:
            audit_log.TRAIL = old
    return root


def test_help_exits_0():
    r = run("--help")
    assert r.returncode == 0 and "evidence" in (r.stdout + r.stderr).lower()


def test_bundle_builds_and_verdict_passes(tmp_path):
    root = make_root(tmp_path)
    out = tmp_path / "bundle.zip"
    r = run("--root", str(root), "--out", str(out))
    assert r.returncode == 0, r.stdout + r.stderr
    assert out.exists()
    with zipfile.ZipFile(out) as zf:
        names = zf.namelist()
        assert "INDEX.md" in names
        assert "governance/GATES.md" in names
        assert "governance/audit_trail.jsonl" in names
        assert ".claude-plugin/plugin.json" in names
        index = zf.read("INDEX.md").decode("utf-8")
    assert "PASSED" in index and "not a certification" in index.lower()
    assert "9.9.9" in index  # version surfaced
    # SHA-256 in the index matches an independent hash of the source file
    gates_sha = hashlib.sha256((root / "governance" / "GATES.md").read_bytes()).hexdigest()
    assert gates_sha in index
    assert re.search(r"BUNDLE_SHA256 [0-9a-f]{64}", r.stdout)


def test_tampered_chain_marks_failed_and_exits_1(tmp_path):
    root = make_root(tmp_path)
    trail = root / "governance" / "audit_trail.jsonl"
    lines = trail.read_text(encoding="utf-8").splitlines()
    row = json.loads(lines[0]); row["agent"] = "evil"
    lines[0] = json.dumps(row)
    trail.write_text("\n".join(lines) + "\n", encoding="utf-8")
    out = tmp_path / "bundle.zip"
    r = run("--root", str(root), "--out", str(out))
    assert r.returncode == 1
    assert out.exists()  # bundle still written
    with zipfile.ZipFile(out) as zf:
        index = zf.read("INDEX.md").decode("utf-8")
    assert "FAILED" in index


def test_no_trail_is_ok(tmp_path):
    root = make_root(tmp_path, with_trail=False)
    out = tmp_path / "bundle.zip"
    r = run("--root", str(root), "--out", str(out))
    assert r.returncode == 0, r.stdout + r.stderr
    assert "NO TRAIL" in r.stdout
    with zipfile.ZipFile(out) as zf:
        assert "governance/audit_trail.jsonl" not in zf.namelist()


def test_project_filter_limits_manifests(tmp_path):
    root = make_root(tmp_path)
    out = tmp_path / "bundle.zip"
    r = run("--root", str(root), "--out", str(out), "--project", "projA")
    assert r.returncode == 0
    with zipfile.ZipFile(out) as zf:
        names = zf.namelist()
    assert any("projA" in n for n in names)
    assert not any("projB" in n for n in names)


def test_missing_root_exits_1(tmp_path):
    r = run("--root", str(tmp_path / "nope"), "--out", str(tmp_path / "b.zip"))
    assert r.returncode == 1 and "ERROR" in r.stdout
