#!/usr/bin/env python3
"""portfolio_report -- institutional rollup across projects.

Walks --root and treats each immediate subdirectory as a project. For each project,
reads (when present, tolerating absence silently -- cell shows "-"):
  governance/GATES.md or GATES.md  -- last row of the '## Approvals log' table = latest gate
  run_state.json                   -- "phase" field
  findings_ledger.csv (any depth)  -- counts OPEN rows with severity P0 / P1
  agent_outputs/ai_disclosure*      -- disclosure present (yes/no)

ADVISORY: a rollup of what is on disk. It does not verify a gate was actually approved
correctly, that a phase is accurate, or that a findings ledger is complete -- it reads
what exists and reports it.

Usage:
  python3 tools/portfolio_report.py [--root projects] [--out agent_outputs/portfolio_report]

Exit: 0 always (an empty or missing root is reported, not fatal).
"""
from __future__ import annotations
import argparse
import csv
import glob
import json
import os
import re
import sys

import cambium_io  # noqa: F401 -- reconfigures stdout/stderr to UTF-8 on Windows

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_ROOT = os.path.join(ROOT, "projects")
OPEN_STATUSES = {"open"}
TRACKED_SEVERITIES = {"P0", "P1"}


def _find_gates_md(proj_dir: str) -> str:
    for candidate in ("governance/GATES.md", "GATES.md"):
        p = os.path.join(proj_dir, candidate)
        if os.path.exists(p):
            return p
    return ""


def latest_gate(proj_dir: str) -> str:
    """Return 'id (date) decision' for the last approvals-table row, or '-'.

    Handles both real-world shapes of GATES.md:
      - the canonical root-repo format: an '## Approvals log' section whose table is
        | Gate | Date | Approver | Decision | Notes |
      - demo/example files whose approvals table sits at the top of the file with no
        section heading and a different column order, e.g.
        | Gate | Decision | Approver role | Approved by (name) | Date | Notes |
    Column meaning is read from the table's own header row (first cell 'Gate'), so
    either order works. When no '## Approvals log' heading exists, the whole file is
    scanned for gate tables instead of giving up.
    """
    path = _find_gates_md(proj_dir)
    if not path:
        return "-"
    text = open(path, encoding="utf-8", errors="replace").read()
    lines = text.splitlines()
    start = 0
    for i, line in enumerate(lines):
        if line.strip().lower().startswith("## approvals log"):
            start = i + 1
            break

    header: list = []
    last_row = None
    last_header: list = []
    for line in lines[start:]:
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if all(re.match(r"^[-:]+$", c) for c in cells if c):
            continue  # separator row
        if cells and cells[0].lower() == "gate":
            header = [c.lower() for c in cells]  # header row defines column meaning
            continue
        if cells and cells[0]:
            last_row = cells
            last_header = header
    if not last_row:
        return "-"
    gate_id = last_row[0]

    def _col(name: str) -> str:
        for idx, h in enumerate(last_header):
            if name in h and idx < len(last_row):
                return last_row[idx].strip()
        return ""

    if last_header:
        date_col = _col("date")
        decision_col = _col("decision")
    else:
        # No header row seen: assume the canonical Gate|Date|Approver|Decision|Notes order.
        date_col = last_row[1].strip() if len(last_row) > 1 else ""
        decision_col = last_row[3].strip() if len(last_row) > 3 else ""

    if len(decision_col) > 60:
        decision_col = decision_col[:57].rstrip() + "..."

    out = gate_id
    if date_col:
        out += " (%s)" % date_col
    if decision_col:
        out += " %s" % decision_col
    return out


def project_phase(proj_dir: str) -> str:
    path = os.path.join(proj_dir, "run_state.json")
    if not os.path.exists(path):
        return "-"
    try:
        data = json.load(open(path, encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return "-"
    phase = data.get("phase")
    return str(phase) if phase not in (None, "") else "-"


def _find_findings_ledgers(proj_dir: str) -> list:
    return sorted(glob.glob(os.path.join(proj_dir, "**", "findings_ledger.csv"), recursive=True))


def open_p0_p1_counts(proj_dir: str) -> tuple:
    """Return (open_p0, open_p1) counts across every findings_ledger.csv found under proj_dir.
    A row counts as open if its status column (case-insensitive) is 'open'."""
    p0 = p1 = 0
    for ledger_path in _find_findings_ledgers(proj_dir):
        try:
            with open(ledger_path, newline="", encoding="utf-8") as fh:
                for row in csv.DictReader(fh):
                    status = (row.get("status") or "").strip().lower()
                    severity = (row.get("severity") or "").strip().upper()
                    if status in OPEN_STATUSES and severity in TRACKED_SEVERITIES:
                        if severity == "P0":
                            p0 += 1
                        elif severity == "P1":
                            p1 += 1
        except (OSError, csv.Error):
            continue
    return p0, p1


def disclosure_present(proj_dir: str) -> bool:
    pattern = os.path.join(proj_dir, "agent_outputs", "ai_disclosure*")
    return bool(glob.glob(pattern))


def list_projects(root: str) -> list:
    if not os.path.isdir(root):
        return []
    return sorted(d for d in os.listdir(root) if os.path.isdir(os.path.join(root, d)))


def build_rollup(root: str) -> list:
    rows = []
    for name in list_projects(root):
        proj_dir = os.path.join(root, name)
        p0, p1 = open_p0_p1_counts(proj_dir)
        rows.append({
            "project": name,
            "latest_gate": latest_gate(proj_dir),
            "phase": project_phase(proj_dir),
            "open_p0": p0,
            "open_p1": p1,
            "disclosure": "yes" if disclosure_present(proj_dir) else "no",
        })
    return rows


def render_markdown(rows: list, root: str) -> str:
    lines = ["# Institutional portfolio rollup", ""]
    lines.append("> ADVISORY: reports what is on disk under each project directory. Does not "
                  "verify gate correctness or ledger completeness.")
    lines.append("")
    lines.append("**Root:** `%s` &nbsp; **Projects:** %d" % (root, len(rows)))
    lines.append("")
    if not rows:
        lines.append("No project subdirectories found under this root.")
        return "\n".join(lines)
    lines.append("| Project | Latest gate | Phase | Open P0 | Open P1 | Disclosure |")
    lines.append("|---|---|---|---|---|---|")
    for r in rows:
        lines.append("| %s | %s | %s | %d | %d | %s |" % (
            r["project"], r["latest_gate"], r["phase"], r["open_p0"], r["open_p1"], r["disclosure"]))
    return "\n".join(lines)


def _write(path: str, content: str) -> None:
    d = os.path.dirname(os.path.abspath(path))
    if d:
        os.makedirs(d, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--root", default=DEFAULT_ROOT, help="Root directory whose subdirectories are projects (default: projects/).")
    ap.add_argument("--out", default=None, help="Output path stem (writes .md and .json; default agent_outputs/portfolio_report).")
    args = ap.parse_args(argv)

    rows = build_rollup(args.root)
    report = render_markdown(rows, args.root)

    stem = args.out or os.path.join(ROOT, "agent_outputs", "portfolio_report")
    md_path, json_path = stem + ".md", stem + ".json"
    _write(md_path, report)
    _write(json_path, json.dumps({"root": args.root, "projects": rows}, indent=2))

    print(report)
    if not rows:
        print("\n[portfolio_report] note: no projects found under %s (root missing or empty)." % args.root)
    print("\n[portfolio_report] wrote %s and %s" % (md_path, json_path))
    return 0


if __name__ == "__main__":
    sys.exit(main())
