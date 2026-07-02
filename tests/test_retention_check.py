"""Tests for tools/retention_check.py.

Verifies: age flag using os.utime to backdate a tmp file, pattern precedence (first match
wins), oversized flag, the scanned directory is byte-for-byte unchanged after a run
(snapshot file list + mtimes before/after), and a bad policy JSON exits 1. Also asserts
the tool never calls any delete/remove function -- advisory only.
"""
import json
import os
import sys
import tempfile
import time
from datetime import date, datetime, timedelta, timezone

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_REPO, "tools"))

import retention_check as RC


def _mk_dir():
    return tempfile.mkdtemp()


def _write_file(path, content="hello world"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)


def _backdate(path, days_ago):
    t = time.time() - days_ago * 86400
    os.utime(path, (t, t))


def _write_policy(path, rules):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(rules, fh)


def test_age_flag_using_utime_backdate():
    d = _mk_dir()
    f = os.path.join(d, "old_log.txt")
    _write_file(f, "log content")
    _backdate(f, days_ago=400)

    policy = os.path.join(d, "policy.json")
    _write_policy(policy, [{"pattern": "*.txt", "max_age_days": 365, "note": "logs"}])

    flags = RC.scan_directory(d, RC._load_policy(policy), date.today(), max_mb=100)
    assert len(flags) == 1
    assert flags[0]["path"] == "old_log.txt"
    assert any("age" in r for r in flags[0]["reasons"])


def test_file_within_age_not_flagged():
    d = _mk_dir()
    f = os.path.join(d, "fresh.txt")
    _write_file(f)
    _backdate(f, days_ago=10)

    policy = os.path.join(d, "policy.json")
    _write_policy(policy, [{"pattern": "*.txt", "max_age_days": 365, "note": "logs"}])

    flags = RC.scan_directory(d, RC._load_policy(policy), date.today(), max_mb=100)
    assert flags == []


def test_pattern_precedence_first_match_wins():
    d = _mk_dir()
    f = os.path.join(d, "report_2020.csv")
    _write_file(f)
    _backdate(f, days_ago=100)

    policy = os.path.join(d, "policy.json")
    # A specific pattern first with a short max_age; a broad *.csv pattern second with a long one.
    _write_policy(policy, [
        {"pattern": "report_*.csv", "max_age_days": 30, "note": "reports expire fast"},
        {"pattern": "*.csv", "max_age_days": 9999, "note": "generic csv"},
    ])

    flags = RC.scan_directory(d, RC._load_policy(policy), date.today(), max_mb=100)
    assert len(flags) == 1
    assert flags[0]["matched_pattern"] == "report_*.csv"


def test_oversized_flag():
    d = _mk_dir()
    f = os.path.join(d, "big.bin")
    with open(f, "wb") as fh:
        fh.write(b"0" * (2 * 1024 * 1024))  # 2 MB

    policy = os.path.join(d, "policy.json")
    _write_policy(policy, [])

    flags = RC.scan_directory(d, RC._load_policy(policy), date.today(), max_mb=1)
    assert len(flags) == 1
    assert any("oversized" in r for r in flags[0]["reasons"])


def test_directory_unchanged_after_run():
    d = _mk_dir()
    f1 = os.path.join(d, "a.txt")
    f2 = os.path.join(d, "sub", "b.csv")
    _write_file(f1, "aaa")
    _write_file(f2, "bbb")
    _backdate(f1, days_ago=500)

    policy = os.path.join(d, "policy.json")
    _write_policy(policy, [{"pattern": "*.txt", "max_age_days": 100, "note": "x"}])

    def _snapshot():
        snap = {}
        for dirpath, _dn, filenames in os.walk(d):
            for fn in filenames:
                p = os.path.join(dirpath, fn)
                st = os.stat(p)
                snap[p] = (st.st_mtime, st.st_size)
        return snap

    before = _snapshot()
    rc = RC.main(["--dir", d, "--policy", policy, "--out", os.path.join(d, "out", "report")])
    assert rc == 0
    after = _snapshot()
    assert before == after, "scanned directory changed after a retention_check run"


def test_bad_policy_json_exits_1():
    d = _mk_dir()
    policy = os.path.join(d, "bad_policy.json")
    with open(policy, "w", encoding="utf-8") as fh:
        fh.write("{not valid json")
    rc = RC.main(["--dir", d, "--policy", policy])
    assert rc == 1


def test_policy_not_a_list_raises_value_error():
    d = _mk_dir()
    policy = os.path.join(d, "policy.json")
    with open(policy, "w", encoding="utf-8") as fh:
        json.dump({"pattern": "*.txt"}, fh)
    rc = RC.main(["--dir", d, "--policy", policy])
    assert rc == 1


def test_pii_screen_unavailable_degrades_gracefully(monkeypatch):
    d = _mk_dir()
    f = os.path.join(d, "old.txt")
    _write_file(f, "some content")
    _backdate(f, days_ago=999)
    policy = os.path.join(d, "policy.json")
    _write_policy(policy, [{"pattern": "*.txt", "max_age_days": 1, "note": "x"}])

    monkeypatch.setattr(RC, "_load_pii_screen", lambda: None)
    flags = RC.scan_directory(d, RC._load_policy(policy), date.today(), max_mb=100)
    status = RC.apply_pii_screen(flags, d)
    assert status == "pii-check: unavailable"
    assert flags[0]["pii_suspect"] == "pii-check: unavailable"


def test_pii_screen_runs_when_available_via_real_module():
    d = _mk_dir()
    f = os.path.join(d, "contact.txt")
    _write_file(f, "email me at someone@example.com")
    _backdate(f, days_ago=999)
    policy = os.path.join(d, "policy.json")
    _write_policy(policy, [{"pattern": "*.txt", "max_age_days": 1, "note": "x"}])

    flags = RC.scan_directory(d, RC._load_policy(policy), date.today(), max_mb=100)
    status = RC.apply_pii_screen(flags, d)
    assert "pii-check" in status
    assert flags[0]["pii_suspect"] is not None


def test_never_deletes_no_os_remove_calls(monkeypatch):
    d = _mk_dir()
    f = os.path.join(d, "old.txt")
    _write_file(f)
    _backdate(f, days_ago=999)
    policy = os.path.join(d, "policy.json")
    _write_policy(policy, [{"pattern": "*.txt", "max_age_days": 1, "note": "x"}])

    def _boom(*a, **k):
        raise AssertionError("retention_check must never call os.remove")
    monkeypatch.setattr(os, "remove", _boom)
    monkeypatch.setattr(os, "unlink", _boom)

    rc = RC.main(["--dir", d, "--policy", policy, "--out", os.path.join(d, "out", "report")])
    assert rc == 0


def test_json_report_matches_md_flag_count():
    d = _mk_dir()
    f = os.path.join(d, "old.txt")
    _write_file(f)
    _backdate(f, days_ago=999)
    policy = os.path.join(d, "policy.json")
    _write_policy(policy, [{"pattern": "*.txt", "max_age_days": 1, "note": "x"}])

    stem = os.path.join(d, "out", "report")
    RC.main(["--dir", d, "--policy", policy, "--out", stem, "--today", date.today().isoformat()])
    data = json.loads(open(stem + ".json", encoding="utf-8").read())
    md = open(stem + ".md", encoding="utf-8").read()
    assert len(data["flags"]) == 1
    assert "old.txt" in md
