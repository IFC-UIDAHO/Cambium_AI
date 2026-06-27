"""Pause/resume handoff round-trip: state survives a simulated context wipe (ADR-023)."""
import subprocess, sys, json, pathlib

TOOLS = pathlib.Path(__file__).resolve().parents[1] / "tools"


def _run(cwd, script, *args):
    return subprocess.run([sys.executable, str(TOOLS / script), *args],
                          cwd=str(cwd), capture_output=True, text=True)


def test_pause_resume_roundtrip(tmp_path):
    (tmp_path / "agent_outputs").mkdir()
    _run(tmp_path, "run_state.py", "phase", "3", "--note", "Labs building")
    _run(tmp_path, "run_state.py", "loop", "iter 2/5")
    _run(tmp_path, "run_state.py", "finding", "lab-theory", "contribution sharpened")
    _run(tmp_path, "run_state.py", "gate", "G4", "accept results?", "--rec", "accept")

    p = _run(tmp_path, "handoff.py", "pause", "--reason", "test", "--context", "86")
    assert p.returncode == 0
    assert (tmp_path / "agent_outputs" / "HANDOFF.md").exists()

    # simulate losing the context: wipe state, then resume must restore it
    _run(tmp_path, "run_state.py", "reset")
    r = _run(tmp_path, "handoff.py", "resume")
    assert r.returncode == 0
    st = json.loads((tmp_path / "agent_outputs" / "run_state.json").read_text(encoding="utf-8"))
    assert st["phase"] == 3
    assert st["loop_position"] == "iter 2/5"
    assert st["gate"]["id"] == "G4"
    assert st["findings"]["lab-theory"] == "contribution sharpened"

    # consumed handoff is archived; live handoff is gone
    assert (tmp_path / "archive" / "handoffs").exists()
    assert list((tmp_path / "archive" / "handoffs").glob("HANDOFF_*.md"))
    assert not (tmp_path / "agent_outputs" / "HANDOFF.md").exists()


def test_autoloop_guardrails_present():
    import yaml
    cfg = yaml.safe_load(open(pathlib.Path(TOOLS).parent / "phases.yml", encoding="utf-8"))
    al = cfg["autoloop"]
    assert al["never_auto_clear_gates"] is True
    assert al["max_iterations"] >= 1 and al["budget_usd"] >= 1
    assert al["integrity_each_iteration"] is True
