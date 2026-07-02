"""Tests for tools/transcript.py. Records live in tmp_path; offline."""
import hashlib
import json
import os
import subprocess
import sys
import datetime

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_REPO, "tools"))
import transcript as TR

SCRIPT = os.path.join(_REPO, "tools", "transcript.py")


def _run(args):
    r = subprocess.run([sys.executable, SCRIPT] + args, capture_output=True, text=True)
    return r.returncode, r.stdout, r.stderr


def _add(rec, learner, item, kind, extra=None):
    return _run(["add", "--record", rec, "--learner", learner,
                 "--item", item, "--kind", kind] + (extra or []))


def test_help_exits_zero():
    rc, out, _ = _run(["--help"])
    assert rc == 0
    assert "verify" in out


def test_add_creates_record_defaults_today(tmp_path):
    rec = str(tmp_path / "t.json")
    rc, out, _ = _add(rec, "Alice", "way-module", "module", ["--score", "92"])
    assert rc == 0
    data = json.loads(open(rec, encoding="utf-8").read())
    assert data["format"] == "cambium-transcript-v1"
    entry = data["entries"][0]["data"]
    assert entry == {"learner": "Alice", "item": "way-module", "kind": "module",
                     "score": 92.0, "date": datetime.date.today().isoformat()}


def test_chain_hash_matches_spec(tmp_path):
    rec = str(tmp_path / "t.json")
    _add(rec, "Alice", "m1", "module", ["--date", "2026-01-01"])
    _add(rec, "Alice", "lab1", "lab", ["--date", "2026-01-02", "--score", "80"])
    data = json.loads(open(rec, encoding="utf-8").read())
    prev = ""
    for e in data["entries"]:
        canonical = json.dumps(e["data"], sort_keys=True, separators=(",", ":"))
        expected = hashlib.sha256((prev + canonical).encode("utf-8")).hexdigest()
        assert e["hash"] == expected
        prev = e["hash"]


def test_show_table_and_totals(tmp_path):
    rec = str(tmp_path / "t.json")
    _add(rec, "Alice", "m1", "module", ["--score", "90", "--date", "2026-01-01"])
    _add(rec, "Alice", "lab1", "lab", ["--date", "2026-01-02"])
    _add(rec, "Bob", "m1", "module", ["--date", "2026-01-03"])
    rc, out, _ = _run(["show", "--record", rec, "--learner", "Alice"])
    assert rc == 0
    assert "# Transcript: Alice" in out
    assert "| 2026-01-01 | m1 | module | 90 |" in out
    assert "2 entries (modules: 1, labs: 1, quizzes: 0)" in out
    assert "Average score: 90.0 over 1 scored entries" in out
    assert "not an accredited credential" in out
    assert "Bob" not in out


def test_verify_intact(tmp_path):
    rec = str(tmp_path / "t.json")
    _add(rec, "Alice", "m1", "module", ["--date", "2026-01-01"])
    _add(rec, "Alice", "m2", "module", ["--date", "2026-01-02"])
    rc, out, _ = _run(["verify", "--record", rec, "--learner", "Alice"])
    assert rc == 0
    assert "chain intact: 2 entries verified" in out
    assert "entries for Alice: 2" in out


def test_verify_detects_tampering(tmp_path):
    rec = str(tmp_path / "t.json")
    _add(rec, "Alice", "m1", "module", ["--score", "50", "--date", "2026-01-01"])
    _add(rec, "Alice", "m2", "module", ["--date", "2026-01-02"])
    data = json.loads(open(rec, encoding="utf-8").read())
    data["entries"][0]["data"]["score"] = 100.0  # grade inflation attempt
    open(rec, "w", encoding="utf-8").write(json.dumps(data))
    rc, out, _ = _run(["verify", "--record", rec])
    assert rc == 1
    assert "BROKEN chain at entry 1 of 2" in out
    assert "item: m1" in out


def test_invalid_inputs(tmp_path):
    rec = str(tmp_path / "t.json")
    rc, _, err = _add(rec, "Alice", "m1", "module", ["--date", "01/02/2026"])
    assert rc == 1
    assert "invalid --date" in err
    rc, _, _ = _add(rec, "Alice", "m1", "seminar")  # bad kind -> argparse error
    assert rc != 0
    rc, _, err = _run(["show", "--record", str(tmp_path / "none.json"),
                       "--learner", "Alice"])
    assert rc == 1
    _add(rec, "Alice", "m1", "module")
    rc, _, err = _run(["show", "--record", rec, "--learner", "Nobody"])
    assert rc == 1
    assert "no entries" in err
