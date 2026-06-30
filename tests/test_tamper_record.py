"""Tests for tools/tamper_record.py.

Stdlib + tmp dirs only. Never touches live repo data. The record is honest:
it reports only what the run recorded and marks the rest 'not recorded'.
"""
import os
import sys
import json
import tempfile

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_REPO, "tools"))

import tamper_record as T


def _seed_run(root, with_gates=True, with_state=True, model=None):
    os.makedirs(os.path.join(root, "agent_outputs"), exist_ok=True)
    os.makedirs(os.path.join(root, "governance"), exist_ok=True)
    if with_state:
        with open(os.path.join(root, "agent_outputs", "run_state.json"), "w", encoding="utf-8") as fh:
            json.dump({"phase": "Verify", "note": "add math + stats skills"}, fh)
    if with_gates:
        with open(os.path.join(root, "governance", "GATES.md"), "w", encoding="utf-8") as fh:
            fh.write(
                "| Gate | Decision | Approver role | Approved by | Date |\n"
                "|---|---|---|---|---|\n"
                "| G4 | accept results | Director | Jaslam | 2026-06-30 |\n"
            )
    if model:
        with open(os.path.join(root, "config.yml"), "w", encoding="utf-8") as fh:
            fh.write(f'model: "{model}"\n')


def test_record_has_all_tamper_steps():
    with tempfile.TemporaryDirectory() as root:
        _seed_run(root)
        rec = T.build_record(root, "Test deliverable")
        for step in ("task", "model", "prompt", "evaluation", "reporting"):
            assert step in rec["tamper"], f"missing TaMPER step: {step}"


def test_four_pillars_present():
    with tempfile.TemporaryDirectory() as root:
        _seed_run(root)
        rec = T.build_record(root, "Test")
        for pillar in ("security", "accuracy", "reproducibility", "flexibility"):
            assert pillar in rec["four_pillars"]
            assert rec["four_pillars"][pillar]["mechanism"]


def test_task_uses_run_state_note():
    with tempfile.TemporaryDirectory() as root:
        _seed_run(root)
        rec = T.build_record(root, "Test")
        assert "math" in rec["tamper"]["task"]["description"]
        assert rec["tamper"]["task"]["current_phase"] == "Verify"


def test_model_marked_not_recorded_when_absent():
    with tempfile.TemporaryDirectory() as root:
        _seed_run(root, model=None)
        rec = T.build_record(root, "Test")
        assert rec["tamper"]["model"]["engine"] == T.NOT_RECORDED


def test_model_override_is_used():
    with tempfile.TemporaryDirectory() as root:
        _seed_run(root)
        rec = T.build_record(root, "Test", model_override="claude-opus-4-8")
        assert rec["tamper"]["model"]["engine"] == "claude-opus-4-8"


def test_model_read_from_config():
    with tempfile.TemporaryDirectory() as root:
        _seed_run(root, model="claude-sonnet-4-6")
        rec = T.build_record(root, "Test")
        assert rec["tamper"]["model"]["engine"] == "claude-sonnet-4-6"


def test_evaluation_counts_decided_gates():
    with tempfile.TemporaryDirectory() as root:
        _seed_run(root, with_gates=True)
        rec = T.build_record(root, "Test")
        assert rec["tamper"]["evaluation"]["human_gates_with_decisions"] == 1
        assert "Jaslam" in rec["tamper"]["evaluation"]["approvers"]


def test_graceful_with_empty_root():
    with tempfile.TemporaryDirectory() as root:
        rec = T.build_record(root, "Empty")
        assert rec["tamper"]["model"]["engine"] == T.NOT_RECORDED
        # still produces a full structure
        assert rec["four_pillars"]["security"]["status"]


def test_markdown_render_contains_pillars_and_tamper():
    with tempfile.TemporaryDirectory() as root:
        _seed_run(root)
        md = T.render_markdown(T.build_record(root, "Test"))
        assert "## TaMPER" in md
        assert "Four Pillars" in md
        assert "T -- Task" in md


def test_json_render_roundtrips():
    with tempfile.TemporaryDirectory() as root:
        _seed_run(root)
        rec = T.build_record(root, "Test")
        parsed = json.loads(T.render_json(rec))
        assert parsed["tamper"]["task"]["current_phase"] == "Verify"


def test_no_em_dash_in_output():
    with tempfile.TemporaryDirectory() as root:
        _seed_run(root)
        rec = T.build_record(root, "Test")
        blob = T.render_markdown(rec) + T.render_json(rec)
        assert chr(0x2014) not in blob


def test_honest_notes_disclaim_extraction_and_compliance():
    with tempfile.TemporaryDirectory() as root:
        _seed_run(root)
        rec = T.build_record(root, "Test")
        joined = " ".join(rec["honest_notes"]).lower()
        assert "does not extract" in joined
        assert "compliance determination" in joined


def test_cli_writes_json(tmp_path):
    root = str(tmp_path)
    _seed_run(root)
    out = os.path.join(root, "rec.json")
    rc = T.main(["--root", root, "--title", "CLI", "--format", "json", "--out", out])
    assert rc == 0
    assert os.path.exists(out)
    parsed = json.loads(open(out, encoding="utf-8").read())
    assert parsed["framework"].startswith("TaMPER")
