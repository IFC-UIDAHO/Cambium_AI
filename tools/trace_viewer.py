#!/usr/bin/env python3
"""trace_viewer -- render a Cambium run trace to a self-contained HTML timeline.

Reads the actual on-disk trace format written by tools/audit_log.py: a JSON-lines file at
governance/audit_trail.jsonl, one event per line, in the shape append() writes:

  {"ts": "2026-07-01T12:00:00", "gate": "G2", "agent": "scout-landscape",
   "model": "claude-sonnet-4-6", "query_sha": "...", "response_sha": "...",
   "human_action": "APPROVE", "note": "...", "prev": "...", "chain": "..."}

This is the only sequential, timestamped, per-event log Cambium writes on disk (task_router /
run_trace produce a single-snapshot run_state.json, not a trace of discrete events), so it is
the trace this tool renders.

Rendering:
  - one swimlane per "gate" value (events with no gate group under a "-" lane; gate values act
    as the closest thing to a phase grouping in this log)
  - event blocks appear in file order (oldest first) within each lane
  - each block shows agent, model, human_action, and the ts; consecutive events in the SAME
    lane show the elapsed duration between them (seconds), when both timestamps parse
  - events carrying a human_action are visually highlighted as gate events
  - ALL text fields go through html.escape plus '=' -> &#61; encoding -- a trace containing <script> or onerror= payloads renders inert
  - inline CSS only, no CDN, no external fonts, self-contained single HTML file

Usage:
  python3 tools/trace_viewer.py                          # reads governance/audit_trail.jsonl
  python3 tools/trace_viewer.py --trace path/to/trail.jsonl
  python3 tools/trace_viewer.py --out agent_outputs/trace_view.html

Missing or empty trace file: writes a friendly "no events yet" page and exits 0 (not an error --
a fresh repo legitimately has no audit trail yet).

Exit codes:
  0  always (rendering a friendly empty page is success, not failure)
"""
from __future__ import annotations
import argparse
import html
import json
import os
import sys
from datetime import datetime

import cambium_io  # noqa: F401 -- UTF-8 stdout/stderr guard on Windows

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_TRACE = os.path.join(ROOT, "governance", "audit_trail.jsonl")
DEFAULT_OUT = os.path.join("agent_outputs", "trace_view.html")

_STYLE = """
<style>
 body{margin:0;background:#07231A;color:#F4F7F2;font:14px/1.5 Inter,system-ui,Segoe UI,sans-serif}
 .wrap{max-width:900px;margin:0 auto;padding:24px}
 h1{font-size:19px;margin:0 0 4px}
 .sub{color:#8AA197;font-size:12.5px;margin-bottom:20px}
 .lane{border:1px solid #1F4D3B;border-radius:12px;padding:14px 16px;margin-bottom:14px;background:#0E3326}
 .lane h2{margin:0 0 10px;font-size:13px;color:#B7F36A;text-transform:uppercase;letter-spacing:.05em}
 .ev{border:1px solid #1F4D3B;border-radius:9px;padding:9px 11px;margin-bottom:8px;background:#0A271D}
 .ev.gate{border-color:#B7F36A}
 .ev:last-child{margin-bottom:0}
 .ev-top{display:flex;gap:10px;align-items:baseline;flex-wrap:wrap}
 .ev-agent{font-weight:700}
 .ev-model{color:#8AA197;font-size:11.5px}
 .ev-ts{margin-left:auto;color:#5E7468;font-size:11px;font-family:ui-monospace,monospace}
 .ev-action{display:inline-block;margin-top:5px;font-size:11px;font-weight:800;
   border:1px solid #B7F36A;color:#B7F36A;border-radius:6px;padding:1px 7px}
 .ev-note{margin-top:5px;color:#C7D6CE;font-size:12.5px}
 .ev-dur{margin-top:4px;color:#5E7468;font-size:11px}
 .empty{color:#8AA197;padding:30px;text-align:center;border:1px dashed #1F4D3B;border-radius:12px}
</style>
""".strip()


def load_events(trace_path: str) -> list:
    """Parse JSON-lines trace events. Blank lines and lines that fail to parse as JSON are
    skipped (never raises -- a malformed trace renders what it can, not a crash)."""
    if not os.path.exists(trace_path):
        return []
    events = []
    with open(trace_path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return events


def _parse_ts(ts: str):
    try:
        return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S")
    except (ValueError, TypeError):
        return None


def group_by_lane(events: list) -> dict:
    """Group events by their 'gate' field (file order preserved within each lane); events
    with no gate (or an empty one) go in the '-' lane."""
    lanes: dict = {}
    for ev in events:
        lane = str(ev.get("gate") or "-")
        lanes.setdefault(lane, []).append(ev)
    return lanes


def _duration_line(prev_ev, ev) -> str:
    if prev_ev is None:
        return ""
    t0, t1 = _parse_ts(prev_ev.get("ts", "")), _parse_ts(ev.get("ts", ""))
    if t0 is None or t1 is None:
        return ""
    secs = (t1 - t0).total_seconds()
    if secs < 0:
        return ""
    return f'<div class="ev-dur">+{secs:.0f}s since previous event in this lane</div>'


def _esc(value) -> str:
    """Escape a user-supplied trace field for safe HTML embedding. On top of
    html.escape(quote=True), '=' becomes '&#61;' so attribute-style payloads
    (e.g. onerror=alert(...)) cannot appear verbatim anywhere in the document.
    Browsers render &#61; identically to '='."""
    return html.escape(str(value), quote=True).replace("=", "&#61;")


def _render_event(ev: dict, prev_ev) -> str:
    agent = _esc(ev.get("agent", ""))
    model = _esc(ev.get("model", ""))
    ts = _esc(ev.get("ts", ""))
    action = str(ev.get("human_action", "") or "")
    note = str(ev.get("note", "") or "")
    is_gate = bool(action.strip())
    cls = "ev gate" if is_gate else "ev"
    parts = [f'<div class="{cls}">',
             f'<div class="ev-top"><span class="ev-agent">{agent}</span>'
             f'<span class="ev-model">{model}</span><span class="ev-ts">{ts}</span></div>']
    if action.strip():
        parts.append(f'<span class="ev-action">{_esc(action)}</span>')
    if note.strip():
        parts.append(f'<div class="ev-note">{_esc(note)}</div>')
    parts.append(_duration_line(prev_ev, ev))
    parts.append('</div>')
    return "".join(parts)


def render_html(events: list) -> str:
    if not events:
        body = '<div class="empty">No trace events found. Nothing has been logged to '\
               'governance/audit_trail.jsonl yet (or --trace pointed at an empty/missing file).</div>'
        n_lanes = 0
    else:
        lanes = group_by_lane(events)
        lane_html = []
        for lane_name in lanes:
            lane_events = lanes[lane_name]
            blocks = []
            prev = None
            for ev in lane_events:
                blocks.append(_render_event(ev, prev))
                prev = ev
            lane_html.append(
                f'<div class="lane"><h2>Gate {_esc(lane_name)}</h2>{"".join(blocks)}</div>'
            )
        body = "".join(lane_html)
        n_lanes = len(lanes)

    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Cambium -- trace viewer</title>
{_STYLE}</head>
<body><div class="wrap">
<h1>Cambium run trace</h1>
<div class="sub">{len(events)} event(s) across {n_lanes} lane(s) -- source: governance/audit_trail.jsonl</div>
{body}
</div></body></html>"""


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Render a Cambium audit trail to a self-contained HTML timeline.")
    ap.add_argument("--trace", default=DEFAULT_TRACE, help="Path to the JSON-lines trace file.")
    ap.add_argument("--out", default=DEFAULT_OUT, help="Output HTML path (default: agent_outputs/trace_view.html).")
    args = ap.parse_args(argv)

    events = load_events(args.trace)
    doc = render_html(events)

    out_dir = os.path.dirname(os.path.abspath(args.out)) or "."
    os.makedirs(out_dir, exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(doc)

    print(f"[trace_viewer] {len(events)} event(s) from {args.trace} -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
