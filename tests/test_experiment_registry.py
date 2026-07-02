"""Tests for tools/experiment_registry.py.

Stdlib + tmp_path only. A hypothesis or analysis plan registered before it runs
must be provably unchanged later: register writes a sha256 row, verify checks
the current content against it.
"""
import os
import sys

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_REPO, "tools"))

import experiment_registry as R


def _ledger(tmp_path):
    return str(tmp_path / "ledger.csv")


def test_register_then_verify_ok(tmp_path):
    plan = tmp_path / "plan.md"
    plan.write_text("H1: treatment increases yield over control.", encoding="utf-8")
    ledger = _ledger(tmp_path)

    rc = R.main(["--ledger", ledger, "register", "--file", str(plan), "--title", "H1 plan"])
    assert rc == 0
    assert os.path.exists(ledger)

    rc = R.main(["--ledger", ledger, "verify", "--title", "H1 plan", "--file", str(plan)])
    assert rc == 0


def test_modified_content_fails_verify(tmp_path, capsys):
    plan = tmp_path / "plan.md"
    plan.write_text("H1: treatment increases yield over control.", encoding="utf-8")
    ledger = _ledger(tmp_path)

    rc = R.main(["--ledger", ledger, "register", "--file", str(plan), "--title", "H1 plan"])
    assert rc == 0

    # Tamper with the plan after registration.
    plan.write_text("H1: treatment DECREASES yield vs control (changed after registering).", encoding="utf-8")

    rc = R.main(["--ledger", ledger, "verify", "--title", "H1 plan", "--file", str(plan)])
    assert rc == 1
    captured = capsys.readouterr()
    assert "TAMPERED" in captured.err


def test_list_shows_registered_rows(tmp_path, capsys):
    ledger = _ledger(tmp_path)
    rc = R.main(["--ledger", ledger, "register", "--text", "inline hypothesis text", "--title", "Inline plan"])
    assert rc == 0

    rc = R.main(["--ledger", ledger, "list"])
    assert rc == 0
    captured = capsys.readouterr()
    assert "Inline plan" in captured.out
    assert "EXP0001" in captured.out


def test_missing_ledger_handled_by_list_and_verify(tmp_path, capsys):
    ledger = str(tmp_path / "does_not_exist.csv")

    rc = R.main(["--ledger", ledger, "list"])
    assert rc == 0
    captured = capsys.readouterr()
    assert "not found" in captured.out

    rc = R.main(["--ledger", ledger, "verify", "--title", "nope", "--text", "x"])
    assert rc == 1


def test_duplicate_title_warns_but_still_registers(tmp_path, capsys):
    ledger = _ledger(tmp_path)
    rc = R.main(["--ledger", ledger, "register", "--text", "first version", "--title", "Same title"])
    assert rc == 0
    rc = R.main(["--ledger", ledger, "register", "--text", "second version", "--title", "Same title"])
    assert rc == 0
    captured = capsys.readouterr()
    assert "already exists" in captured.err

    rows = R._read_ledger(ledger)
    assert len(rows) == 2
    assert rows[0]["id"] == "EXP0001"
    assert rows[1]["id"] == "EXP0002"


def test_register_requires_title(tmp_path, capsys):
    ledger = _ledger(tmp_path)
    rc = R.main(["--ledger", ledger, "register", "--text", "no title given"])
    assert rc == 2
    captured = capsys.readouterr()
    assert "title" in captured.err.lower()


def test_verify_missing_file_exits_2(tmp_path):
    ledger = _ledger(tmp_path)
    rc = R.main(["--ledger", ledger, "register", "--text", "x", "--title", "T"])
    assert rc == 0
    rc = R.main(["--ledger", ledger, "verify", "--title", "T", "--file", str(tmp_path / "nope.md")])
    assert rc == 2


def test_sha256_is_deterministic():
    a = R._sha256("same content")
    b = R._sha256("same content")
    assert a == b
    assert a != R._sha256("different content")


def test_no_em_dash_in_source():
    with open(os.path.join(_REPO, "tools", "experiment_registry.py"), encoding="utf-8") as fh:
        source = fh.read()
    assert chr(0x2014) not in source
