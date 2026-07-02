"""tests/test_trace_viewer.py -- tests for tools/trace_viewer.py"""
import importlib.util
import json
import os
import sys
import tempfile

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL_PATH = os.path.join(REPO_ROOT, "tools", "trace_viewer.py")

sys.path.insert(0, os.path.join(REPO_ROOT, "tools"))


def _load():
    spec = importlib.util.spec_from_file_location("trace_viewer", TOOL_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


trace_viewer = _load()


def _write_jsonl(path, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row) + "\n")


def test_events_appear_in_output():
    with tempfile.TemporaryDirectory() as tmp:
        trace = os.path.join(tmp, "trail.jsonl")
        _write_jsonl(trace, [
            {"ts": "2026-07-01T12:00:00", "gate": "G2", "agent": "scout-landscape",
             "model": "claude-sonnet-4-6", "human_action": "APPROVE", "note": "first pass"},
        ])
        out = os.path.join(tmp, "out.html")
        rc = trace_viewer.main(["--trace", trace, "--out", out])
        assert rc == 0
        with open(out, encoding="utf-8") as fh:
            doc = fh.read()
        assert "scout-landscape" in doc
        assert "claude-sonnet-4-6" in doc
        assert "APPROVE" in doc
        assert "first pass" in doc


def test_script_injection_escaped():
    with tempfile.TemporaryDirectory() as tmp:
        trace = os.path.join(tmp, "trail.jsonl")
        _write_jsonl(trace, [
            {"ts": "2026-07-01T12:00:00", "gate": "G1",
             "agent": "<script>alert(1)</script>", "model": "m",
             "human_action": "", "note": "<img src=x onerror=alert(2)>"},
        ])
        out = os.path.join(tmp, "out.html")
        trace_viewer.main(["--trace", trace, "--out", out])
        with open(out, encoding="utf-8") as fh:
            doc = fh.read()
        assert "<script>alert(1)</script>" not in doc
        assert "&lt;script&gt;" in doc
        assert "onerror=alert(2)" not in doc
        assert "&lt;img" in doc


def test_empty_trace_handled_friendly_exit_0():
    with tempfile.TemporaryDirectory() as tmp:
        trace = os.path.join(tmp, "does-not-exist.jsonl")
        out = os.path.join(tmp, "out.html")
        rc = trace_viewer.main(["--trace", trace, "--out", out])
        assert rc == 0
        with open(out, encoding="utf-8") as fh:
            doc = fh.read()
        assert "No trace events found" in doc
        assert doc.rstrip().endswith("</html>")


def test_file_written_where_asked():
    with tempfile.TemporaryDirectory() as tmp:
        trace = os.path.join(tmp, "trail.jsonl")
        _write_jsonl(trace, [{"ts": "2026-07-01T12:00:00", "gate": "-", "agent": "a", "model": "m"}])
        out = os.path.join(tmp, "nested", "custom.html")
        rc = trace_viewer.main(["--trace", trace, "--out", out])
        assert rc == 0
        assert os.path.exists(out)


def test_phases_grouped_by_gate_lane():
    with tempfile.TemporaryDirectory() as tmp:
        trace = os.path.join(tmp, "trail.jsonl")
        _write_jsonl(trace, [
            {"ts": "2026-07-01T12:00:00", "gate": "G1", "agent": "a1", "model": "m"},
            {"ts": "2026-07-01T12:00:05", "gate": "G1", "agent": "a2", "model": "m"},
            {"ts": "2026-07-01T12:00:10", "gate": "G2", "agent": "a3", "model": "m"},
        ])
        events = trace_viewer.load_events(trace)
        lanes = trace_viewer.group_by_lane(events)
        assert set(lanes.keys()) == {"G1", "G2"}
        assert len(lanes["G1"]) == 2
        assert len(lanes["G2"]) == 1
        doc = trace_viewer.render_html(events)
        assert "Gate G1" in doc and "Gate G2" in doc
        assert "+5s since previous event in this lane" in doc
