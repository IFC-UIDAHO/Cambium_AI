"""gen_board_pro: the premium run board renders from real run state, all placeholders filled."""
import json, os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import gen_board_pro as B

STATE = {"phase": 2, "note": "verification underway",
 "plan": {"type": "cambium", "request": "Test request",
  "phases": [
   {"council": "Execution", "label": "Build it", "agents": [["Execution","Research Engineer","research-engineer","did the thing"]]},
   {"council": "Verification", "label": "Check it", "agents": [["Verification","Evidence","verify-evidence"]],
    "gate": {"id": "G-test", "decision": "Ship it?"}},
   {"council": "Support", "label": "Close out", "agents": [["Support","Record Keeper","record-keeper"]]}]}}

def _render():
    f = tempfile.mktemp(suffix=".json"); json.dump(STATE, open(f, "w"))
    return B.render(f, "Test request")

def test_renders_full_html_no_placeholders():
    h = _render()
    assert h.startswith("<!doctype html") and "CAMBIUM INSTITUTE" in h
    assert "{req}" not in h and "{pct}" not in h and "{cards}" not in h

def test_status_done_now_waiting():
    # phase index 0 done (cur=2>1), index 1 now (cur==2), index 2 waiting
    assert B.status_of(0, 2) == "done" and B.status_of(1, 2) == "now" and B.status_of(2, 2) == "waiting"

def test_active_gate_card_shown_when_pending():
    h = _render()
    assert "GATE G-test — your decision" in h and "Ship it?" in h
    assert "APPROVE" in h and "REVISE" in h and "REJECT" in h

def test_agent_finding_rendered():
    assert "did the thing" in _render()

def test_progress_reflects_done_phases():
    # 1 of 3 done -> 33%
    h = _render(); assert "33%" in h

def test_cli_writes_file():
    f = tempfile.mktemp(suffix=".json"); json.dump(STATE, open(f, "w"))
    out = tempfile.mktemp(suffix=".html")
    r = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "gen_board_pro.py"),
                        "--state", f, "--out", out], capture_output=True, text=True)
    assert r.returncode == 0 and os.path.exists(out) and "CAMBIUM" in open(out).read()
