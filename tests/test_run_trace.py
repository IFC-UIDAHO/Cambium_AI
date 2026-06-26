import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import run_trace

def test_mermaid_has_flow_gate_and_orchestrator():
    m = run_trace.mermaid("summarize this grant call and tell me whether to apply")
    assert "flowchart TD" in m and "🚦" in m and "Orchestration" in m

def test_text_plan_lists_gate():
    t = run_trace.text("draft proposal")
    assert "Cambium plan" in t and "GATE" in t

def test_svg_renders_with_gate():
    s = run_trace.svg("summarize this grant call and tell me whether to apply")
    assert s.startswith("<svg") and s.rstrip().endswith("</svg>") and "GATE" in s

def test_status_board_marks_now_done_waiting():
    s = run_trace.status("draft the grant proposal", 4)
    assert s.startswith("<svg") and "NOW" in s and "✓" in s and "▶" in s and "○" in s
    t = run_trace.text("draft the grant proposal", 4)
    assert "✓" in t and "▶" in t and "○" in t
