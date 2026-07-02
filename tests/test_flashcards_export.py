"""Tests for tools/flashcards_export.py.

Small synthetic fixtures in tmp_path; offline; fast. The lab-spec fixture
mirrors the real gen_learning_lab.py / academy/courses.json shape.
"""
import csv
import io
import json
import os
import subprocess
import sys

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_REPO, "tools"))
import flashcards_export as FE

SCRIPT = os.path.join(_REPO, "tools", "flashcards_export.py")

PACKET_MD = """# Learning Packet: Demo

## Glossary

| Term | Plain meaning |
|------|---------------|
| Gate | A checkpoint where the run pauses for a decision |
| Agent | A named specialist with one job |

## Flashcards

- Q: What is a council?
  A: A team of related agents.

- Q: What is __FILL__?
  A: __FILL__

## Quick quiz

1. Who approves gate G3?

<details>
<summary>Answer</summary>

The Director plus a second human.

</details>
"""

GENERIC_MD = """# Notes

## Evidence tiers

Evidence tiers grade how well a claim is supported before release happens.

A **gate** is a checkpoint where the run stops and waits for a decision.
"""

LAB_SPEC = {
    "id": "demo", "title": "Demo Lab",
    "modules": [{
        "id": "m1", "title": "Module one",
        "lessons": [{
            "id": "l1", "title": "Lesson",
            "blocks": [
                {"type": "concept", "title": "skip me", "html": "<p>x</p>"},
                {"type": "flashcards", "cards": [
                    {"front": "What is an agent?", "back": "A named specialist."}]},
                {"type": "predict", "q": "What happens first?",
                 "choices": ["Everything runs", "The orchestrator plans"],
                 "answer": 1, "explain": "It plans."},
            ],
        }],
        "quiz": [{"q": "Which tier means a script ran?",
                  "choices": ["Asserted", "Code-verified"], "answer": 1,
                  "explain": "Reproduced by a run."}],
    }],
}


def _run(args):
    r = subprocess.run([sys.executable, SCRIPT] + args, capture_output=True, text=True)
    return r.returncode, r.stdout, r.stderr


def test_help_exits_zero():
    rc, out, _ = _run(["--help"])
    assert rc == 0
    assert "--source" in out


def test_packet_md_tsv(tmp_path):
    src = tmp_path / "packet.md"
    src.write_text(PACKET_MD, encoding="utf-8")
    rc, out, err = _run(["--source", str(src)])
    assert rc == 0
    rows = [line.split("\t") for line in out.strip().splitlines()]
    assert all(len(r) == 3 for r in rows)
    fronts = [r[0] for r in rows]
    assert "What is a council?" in fronts          # explicit Q/A
    assert "Gate" in fronts                        # glossary table
    assert "Who approves gate G3?" in fronts       # quiz + details answer
    assert not any("__FILL__" in r[0] or "__FILL__" in r[1] for r in rows)


def test_generic_md_bold_and_heading(tmp_path):
    src = tmp_path / "notes.md"
    src.write_text(GENERIC_MD, encoding="utf-8")
    rc, out, _ = _run(["--source", str(src), "--format", "json"])
    assert rc == 0
    cards = json.loads(out)["cards"]
    fronts = {c["front"] for c in cards}
    assert "gate" in fronts             # bold-term + "is"
    assert "Evidence tiers" in fronts   # heading + paragraph
    auto = [c for c in cards if "auto-extracted" in c["tags"]]
    assert auto, "heuristic cards must carry the auto-extracted tag"


def test_lab_spec_json(tmp_path):
    src = tmp_path / "lab.json"
    src.write_text(json.dumps(LAB_SPEC), encoding="utf-8")
    rc, out, _ = _run(["--source", str(src), "--format", "json"])
    assert rc == 0
    payload = json.loads(out)
    kinds = {c["kind"] for c in payload["cards"]}
    assert kinds == {"lab-flashcard", "lab-predict", "lab-quiz"}
    predict = [c for c in payload["cards"] if c["kind"] == "lab-predict"][0]
    assert predict["back"].startswith("The orchestrator plans")
    assert any("m1" in c["tags"] for c in payload["cards"])


def test_csv_format(tmp_path):
    src = tmp_path / "packet.md"
    src.write_text(PACKET_MD, encoding="utf-8")
    rc, out, _ = _run(["--source", str(src), "--format", "csv"])
    assert rc == 0
    rows = list(csv.reader(io.StringIO(out)))
    assert rows[0] == ["front", "back", "tags"]
    assert len(rows) > 1


def test_schedule(tmp_path):
    src = tmp_path / "packet.md"
    src.write_text(PACKET_MD, encoding="utf-8")
    plan = tmp_path / "plan.md"
    rc, _, _ = _run(["--source", str(src), "--out", str(tmp_path / "d.tsv"),
                     "--schedule", str(plan), "--start", "2026-01-01"])
    assert rc == 0
    text = plan.read_text(encoding="utf-8")
    for date in ("2026-01-01", "2026-01-02", "2026-01-04", "2026-01-08",
                 "2026-01-15", "2026-01-31"):
        assert date in text
    assert "not an adaptive scheduler" in text


def test_invalid_inputs(tmp_path):
    rc, _, err = _run(["--source", str(tmp_path / "missing.md")])
    assert rc == 1
    empty = tmp_path / "empty.md"
    empty.write_text("just one plain line, no patterns\n", encoding="utf-8")
    rc, _, err = _run(["--source", str(empty)])
    assert rc == 1
    assert "no flashcard patterns" in err
    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    rc, _, _ = _run(["--source", str(bad)])
    assert rc == 1
