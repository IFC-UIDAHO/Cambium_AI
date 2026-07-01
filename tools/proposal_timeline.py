#!/usr/bin/env python3
"""proposal_timeline -- backwards-planned deadline and task tracker for a proposal.

Given a submission deadline, computes an internal due date for each proposal task
by counting calendar days backwards from the deadline (stdlib datetime only).
Prints a Markdown timeline table sorted earliest-first, plus an open-items list.
Optionally writes a hand-built .ics calendar file (stdlib only, no external library).

This is an internal planning aid. It is not the sponsor's official deadline record.
Always confirm every date against the actual solicitation or NOFO and the sponsor's
submission portal before treating any date here as authoritative.

Inputs:
  --deadline YYYY-MM-DD   the submission deadline (required)
  --tasks tasks.json      optional list of {task, owner, lead_days} objects.
                          If omitted, a built-in default task set is used.

Default task set (typical lead times in calendar days before the deadline):
  final PI review                 1 day
  budget finalized                3 days
  subaward documents               7 days
  biosketches and current-and-pending  10 days
  draft to sponsored programs      5 days
  letters of support               14 days
  intent to submit                 21 days

Exit codes:
  0  -- timeline built and printed (or written)
  2  -- input file missing, unreadable, or deadline is not a valid date

Usage:
  python3 tools/proposal_timeline.py --deadline 2026-09-01
  python3 tools/proposal_timeline.py --deadline 2026-09-01 --tasks tasks.json
  python3 tools/proposal_timeline.py --deadline 2026-09-01 --out timeline.md --ics out.ics
"""
from __future__ import annotations
import argparse
import json
import os
import sys
from datetime import datetime, timedelta

# UTF-8 stdout guard
import cambium_io  # noqa: F401

DATE_FMT = "%Y-%m-%d"

DEFAULT_TASKS = [
    {"task": "Intent to submit", "owner": "PI", "lead_days": 21},
    {"task": "Letters of support", "owner": "PI", "lead_days": 14},
    {"task": "Biosketches and current-and-pending", "owner": "PI / research team", "lead_days": 10},
    {"task": "Subaward documents", "owner": "PI / partner institutions", "lead_days": 7},
    {"task": "Draft to sponsored programs", "owner": "PI", "lead_days": 5},
    {"task": "Budget finalized", "owner": "sponsored programs", "lead_days": 3},
    {"task": "Final PI review", "owner": "PI", "lead_days": 1},
]


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------

def _parse_deadline(raw: str) -> datetime:
    try:
        return datetime.strptime(raw, DATE_FMT)
    except ValueError:
        print(f"[proposal_timeline] ERROR: --deadline must be YYYY-MM-DD, got: {raw}", file=sys.stderr)
        sys.exit(2)


def _load_tasks(path: str | None) -> list[dict]:
    """Load tasks from JSON, or return the default set if no path is given."""
    if path is None:
        return [dict(t) for t in DEFAULT_TASKS]
    if not os.path.exists(path):
        print(f"[proposal_timeline] ERROR: tasks file not found: {path}", file=sys.stderr)
        sys.exit(2)
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except json.JSONDecodeError as exc:
        print(f"[proposal_timeline] ERROR: tasks file is not valid JSON: {path}\n  {exc}", file=sys.stderr)
        sys.exit(2)
    except OSError as exc:
        print(f"[proposal_timeline] ERROR: cannot read tasks file: {path}\n  {exc}", file=sys.stderr)
        sys.exit(2)
    if not isinstance(data, list):
        print(f"[proposal_timeline] ERROR: tasks file must contain a JSON list: {path}", file=sys.stderr)
        sys.exit(2)
    tasks = []
    for i, item in enumerate(data):
        if not isinstance(item, dict) or "task" not in item or "lead_days" not in item:
            print(
                f"[proposal_timeline] ERROR: tasks[{i}] must be an object with at least "
                "'task' and 'lead_days'",
                file=sys.stderr,
            )
            sys.exit(2)
        tasks.append({
            "task": item["task"],
            "owner": item.get("owner", "unassigned"),
            "lead_days": int(item["lead_days"]),
        })
    return tasks


# ---------------------------------------------------------------------------
# Timeline computation
# ---------------------------------------------------------------------------

def compute_timeline(deadline: datetime, tasks: list[dict]) -> list[dict]:
    """Compute internal due date for each task, sorted earliest first."""
    rows = []
    for t in tasks:
        due = deadline - timedelta(days=int(t["lead_days"]))
        rows.append({
            "task": t["task"],
            "owner": t.get("owner", "unassigned"),
            "lead_days": int(t["lead_days"]),
            "due_date": due,
        })
    rows.sort(key=lambda r: r["due_date"])
    return rows


# ---------------------------------------------------------------------------
# Markdown report
# ---------------------------------------------------------------------------

def build_report(deadline: datetime, rows: list[dict]) -> str:
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    lines: list[str] = []

    lines.append("# Proposal timeline (internal planning aid)")
    lines.append("")
    lines.append(
        "> This is an internal, backwards-planned schedule generated from lead times. "
        "It is not the sponsor's official deadline record. Confirm every date against "
        "the actual solicitation or NOFO and your sponsored programs office."
    )
    lines.append("")
    lines.append(f"**Generated:** {now}")
    lines.append(f"**Submission deadline:** {deadline.strftime(DATE_FMT)}")
    lines.append(f"**Tasks:** {len(rows)}")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Timeline")
    lines.append("")
    lines.append("| Internal due date | Task | Owner | Days before deadline |")
    lines.append("|---|---|---|---|")
    for r in rows:
        lines.append(
            f"| {r['due_date'].strftime(DATE_FMT)} | {r['task']} | {r['owner']} | {r['lead_days']} |"
        )
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Open items")
    lines.append("")
    for r in rows:
        lines.append(f"- [ ] {r['due_date'].strftime(DATE_FMT)}: {r['task']} ({r['owner']})")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(
        "**This timeline is a planning aid only. It does not replace reading the "
        "sponsor's solicitation or a human decision by the principal investigator "
        "and sponsored programs office about actual due dates.**"
    )
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# .ics calendar (hand-written, stdlib only)
# ---------------------------------------------------------------------------

def _ics_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace(",", "\\,").replace(";", "\\;")


def build_ics(deadline: datetime, rows: list[dict]) -> str:
    """Hand-write a minimal valid .ics with one all-day VEVENT per task plus the deadline."""
    now_stamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    lines: list[str] = []
    lines.append("BEGIN:VCALENDAR")
    lines.append("VERSION:2.0")
    lines.append("PRODID:-//Cambium//proposal_timeline//EN")
    lines.append("CALSCALE:GREGORIAN")

    events = list(rows) + [{
        "task": "Submission deadline",
        "owner": "sponsor",
        "lead_days": 0,
        "due_date": deadline,
    }]

    for i, r in enumerate(events):
        d = r["due_date"]
        dtstart = d.strftime("%Y%m%d")
        dtend = (d + timedelta(days=1)).strftime("%Y%m%d")
        uid = f"proposal-timeline-{i}-{dtstart}@cambium"
        summary = _ics_escape(f"{r['task']} ({r['owner']})")
        lines.append("BEGIN:VEVENT")
        lines.append(f"UID:{uid}")
        lines.append(f"DTSTAMP:{now_stamp}")
        lines.append(f"DTSTART;VALUE=DATE:{dtstart}")
        lines.append(f"DTEND;VALUE=DATE:{dtend}")
        lines.append(f"SUMMARY:{summary}")
        lines.append("END:VEVENT")

    lines.append("END:VCALENDAR")
    # RFC 5545 requires CRLF line endings
    return "\r\n".join(lines) + "\r\n"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(
        description=(
            "Backwards-planned deadline and task tracker for a proposal. "
            "Internal planning aid; confirm dates against the sponsor's official deadline."
        )
    )
    ap.add_argument("--deadline", required=True, help="Submission deadline, YYYY-MM-DD.")
    ap.add_argument("--tasks", default=None, help="Path to a tasks JSON file (optional).")
    ap.add_argument("--out", default=None, help="Output path for the Markdown timeline (default: stdout).")
    ap.add_argument("--ics", default=None, help="Output path for a .ics calendar file (optional).")
    args = ap.parse_args(argv)

    deadline = _parse_deadline(args.deadline)
    tasks = _load_tasks(args.tasks)
    rows = compute_timeline(deadline, tasks)

    report = build_report(deadline, rows)

    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(report)
        print(f"[proposal_timeline] wrote {args.out}")
    else:
        sys.stdout.write(report)

    if args.ics:
        ics_text = build_ics(deadline, rows)
        os.makedirs(os.path.dirname(os.path.abspath(args.ics)), exist_ok=True)
        with open(args.ics, "w", encoding="utf-8", newline="") as fh:
            fh.write(ics_text)
        print(f"[proposal_timeline] wrote {args.ics}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
