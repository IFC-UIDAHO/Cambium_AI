"""Tests for tools/gate_simulator.py. Non-interactive modes only; offline."""
import os
import subprocess
import sys

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_REPO, "tools"))
import gate_simulator as GS

SCRIPT = os.path.join(_REPO, "tools", "gate_simulator.py")


def _run(args):
    r = subprocess.run([sys.executable, SCRIPT] + args, capture_output=True, text=True)
    return r.returncode, r.stdout, r.stderr


def test_help_exits_zero():
    rc, out, _ = _run(["--help"])
    assert rc == 0
    assert "--play" in out and "--quiz" in out


def test_scenario_data_integrity():
    gates = [s["gate"] for s in GS.SCENARIOS]
    assert 6 <= len(GS.SCENARIOS) <= 8
    assert set(gates) == {"G0", "G1", "G2", "G3a", "G3", "G4", "G5", "G6"}
    for s in GS.SCENARIOS:
        assert set(s["options"]) == {"approve", "revise", "reject"}
        assert s["correct"] in GS.CHOICES
        assert len(s["situation"]) > 40 and len(s["why"]) > 40
        assert s["rules"], "every scenario must cite its grounding rules"
        assert all(len(s["options"][c]) > 20 for c in GS.CHOICES)


def test_list_mode():
    rc, out, _ = _run(["--list"])
    assert rc == 0
    for s in GS.SCENARIOS:
        assert "[%s]" % s["gate"] in out


def test_play_wrong_choice_explains():
    # scenario 6 (G4 unverified headline): approve is wrong, revise is right
    rc, out, _ = _run(["--play", "6", "--choose", "approve"])
    assert rc == 0  # a wrong answer is a lesson, not invalid input
    assert "not the rubric answer" in out
    assert "REVISE" in out
    assert "Asserted" in out and "Code-verified" in out
    assert "VERIFICATION_PROTOCOL" in out


def test_play_correct_choice():
    rc, out, _ = _run(["--play", "8", "--choose", "revise"])
    assert rc == 0
    assert "correct, this matches the rubric" in out
    assert "second" in out.lower()  # missing second approver grounding
    assert "human action" in out


def test_quiz_hides_answers_key_reveals():
    rc, quiz, _ = _run(["--quiz"])
    assert rc == 0
    assert "Rubric-correct" not in quiz and "Answer key" not in quiz
    for s in GS.SCENARIOS:
        assert s["title"] in quiz
    rc, key, _ = _run(["--key"])
    assert rc == 0
    for s in GS.SCENARIOS:
        assert s["correct"].upper() in key
    assert "Answer key" in key


def test_invalid_inputs():
    rc, _, err = _run(["--play", "99", "--choose", "approve"])
    assert rc == 1
    assert "no scenario" in err
    rc, _, err = _run(["--choose", "approve"])
    assert rc == 1
    rc, _, _ = _run([])  # no mode
    assert rc == 1


def test_no_em_dashes_or_real_names():
    text = open(SCRIPT, encoding="utf-8").read()
    assert "\u2014" not in text, "em dashes are banned in Cambium output"
    # scenarios must stay generic: no named people from the real ledger
    assert "Jaslam" not in text
