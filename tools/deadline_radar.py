#!/usr/bin/env python3
"""deadline_radar -- multi-solicitation deadline calendar.

Merges deadlines from one or more rules JSON files (accepting either the
budget_review/checklist_builder solicitation-rules shape, which carries a
top-level "deadline" plus optional "name"/"funder" fields, or a simple list
of {"name","funder","deadline"} objects) and/or repeated --add flags, then
prints a table sorted by days-left with bucket labels. Can also export a
pure-text .ics calendar (no external library).

ADVISORY: dates come from files or flags a human supplies. This tool does
not fetch, verify, or reconcile deadlines against a sponsor's portal. Always
confirm the actual deadline against the solicitation or NOFO before treating
anything here as authoritative.

Input sources (any mix; merged and de-duplicated by identical name+deadline):
  --rules rules1.json [rules2.json ...]
      Each file is either:
        (a) an object with a "deadline" key (the budget_review rules shape),
            optionally carrying "name" and "funder"; or
        (b) a JSON list of {"name","funder","deadline"} objects.
  --add "name=...,funder=...,deadline=YYYY-MM-DD"
      Repeatable. Comma-separated key=value pairs.

Buckets (computed from --today, or the current UTC date if omitted):
  OVERDUE   -- days_left < 0
  <14d      -- 0 <= days_left < 14
  <30d      -- 14 <= days_left < 30
  <90d      -- 30 <= days_left < 90
  later     -- days_left >= 90

Exit codes:
  0  -- radar built and printed (or written)
  2  -- input file missing/unreadable, --add malformed, or a deadline is not
        a valid YYYY-MM-DD date

Usage:
  python3 tools/deadline_radar.py --rules rules1.json rules2.json
  python3 tools/deadline_radar.py --add "name=NSF CAREER,funder=NSF,deadline=2026-07-20"
  python3 tools/deadline_radar.py --rules rules.json --today 2026-07-01 --out radar.md --ics radar.ics
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

BUCKET_ORDER = ["OVERDUE", "<14d", "<30d", "<90d", "later"]


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------

def _load_json(path: str) -> object:
    if not os.path.exists(path):
        print(f"[deadline_radar] ERROR: rules file not found: {path}", file=sys.stderr)
        sys.exit(2)
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except json.JSONDecodeError as exc:
        print(f"[deadline_radar] ERROR: rules file is not valid JSON: {path}\n  {exc}", file=sys.stderr)
        sys.exit(2)
    except OSError as exc:
        print(f"[deadline_radar] ERROR: cannot read rules file: {path}\n  {exc}", file=sys.stderr)
        sys.exit(2)


def _validate_date(raw: str, context: str) -> str:
    try:
        datetime.strptime(raw, DATE_FMT)
    except (ValueError, TypeError):
        print(f"[deadline_radar] ERROR: bad date for {context}: {raw!r} (expected YYYY-MM-DD)", file=sys.stderr)
        sys.exit(2)
    return raw


def items_from_rules_file(path: str) -> list[dict]:
    """Parse one rules file, accepting either the budget_review rules object
    shape (single deadline) or a simple list-of-objects shape (many deadlines)."""
    data = _load_json(path)
    items: list[dict] = []

    if isinstance(data, dict):
        deadline = data.get("deadline")
        if deadline is None:
            return []
        items.append({
            "name": data.get("name", os.path.basename(path)),
            "funder": data.get("funder", "unspecified"),
            "deadline": _validate_date(deadline, f"{path} (deadline)"),
        })
    elif isinstance(data, list):
        for i, entry in enumerate(data):
            if not isinstance(entry, dict) or "deadline" not in entry:
                print(
                    f"[deadline_radar] ERROR: {path}[{i}] must be an object with a 'deadline' key",
                    file=sys.stderr,
                )
                sys.exit(2)
            items.append({
                "name": entry.get("name", f"{os.path.basename(path)}[{i}]"),
                "funder": entry.get("funder", "unspecified"),
                "deadline": _validate_date(entry["deadline"], f"{path}[{i}] (deadline)"),
            })
    else:
        print(f"[deadline_radar] ERROR: {path} must be a JSON object or list", file=sys.stderr)
        sys.exit(2)

    return items


def item_from_add_string(raw: str) -> dict:
    """Parse a repeatable --add "name=...,funder=...,deadline=YYYY-MM-DD" string."""
    fields = {}
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        if "=" not in part:
            print(f"[deadline_radar] ERROR: --add entry malformed (expected key=value): {part!r}", file=sys.stderr)
            sys.exit(2)
        key, _, value = part.partition("=")
        fields[key.strip()] = value.strip()
    if "deadline" not in fields:
        print(f"[deadline_radar] ERROR: --add entry missing 'deadline': {raw!r}", file=sys.stderr)
        sys.exit(2)
    return {
        "name": fields.get("name", "unnamed"),
        "funder": fields.get("funder", "unspecified"),
        "deadline": _validate_date(fields["deadline"], f"--add {raw!r}"),
    }


def merge_and_dedupe(items: list[dict]) -> list[dict]:
    """De-duplicate items with identical (name, deadline), keeping first occurrence."""
    seen = set()
    out = []
    for item in items:
        key = (item["name"], item["deadline"])
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


# ---------------------------------------------------------------------------
# Bucketing and sorting
# ---------------------------------------------------------------------------

def bucket_for(days_left: int) -> str:
    if days_left < 0:
        return "OVERDUE"
    if days_left < 14:
        return "<14d"
    if days_left < 30:
        return "<30d"
    if days_left < 90:
        return "<90d"
    return "later"


def compute_rows(items: list[dict], today: datetime) -> list[dict]:
    rows = []
    for item in items:
        dl_dt = datetime.strptime(item["deadline"], DATE_FMT)
        days_left = (dl_dt - today).days
        rows.append({
            "name": item["name"],
            "funder": item["funder"],
            "deadline": item["deadline"],
            "days_left": days_left,
            "bucket": bucket_for(days_left),
        })
    rows.sort(key=lambda r: r["days_left"])
    return rows


# ---------------------------------------------------------------------------
# Markdown report
# ---------------------------------------------------------------------------

def build_report(rows: list[dict], today: datetime) -> str:
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    lines: list[str] = []
    lines.append("# Deadline radar (advisory, confirm against the solicitation)")
    lines.append("")
    lines.append(
        "> Dates come from files or flags supplied by a human. This is not a live feed "
        "from any sponsor's portal. Confirm every date against the actual solicitation."
    )
    lines.append("")
    lines.append(f"**Generated:** {now}")
    lines.append(f"**As of:** {today.strftime(DATE_FMT)}")
    lines.append(f"**Deadlines tracked:** {len(rows)}")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Calendar")
    lines.append("")
    lines.append("| Days left | Bucket | Deadline | Name | Funder |")
    lines.append("|---|---|---|---|---|")
    for r in rows:
        lines.append(f"| {r['days_left']} | {r['bucket']} | {r['deadline']} | {r['name']} | {r['funder']} |")
    lines.append("")
    lines.append("---")
    lines.append("")
    for bucket in BUCKET_ORDER:
        in_bucket = [r for r in rows if r["bucket"] == bucket]
        if in_bucket:
            names = "; ".join(f"{r['name']} ({r['deadline']})" for r in in_bucket)
            lines.append(f"**{bucket}:** {names}")
    lines.append("")
    lines.append(
        "**This calendar is a planning aid. Confirm every deadline against the sponsor's "
        "solicitation before acting on it.**"
    )
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# .ics export (hand-written, stdlib only)
# ---------------------------------------------------------------------------

def _ics_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace(",", "\\,").replace(";", "\\;")


def build_ics(rows: list[dict], alarm_days_before: int = 14) -> str:
    """Hand-write a minimal valid .ics with one all-day VEVENT per deadline.

    UID is deterministic from name+date so re-exporting the same items
    produces the same UIDs (stable across runs).
    """
    now_stamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    lines: list[str] = []
    lines.append("BEGIN:VCALENDAR")
    lines.append("VERSION:2.0")
    lines.append("PRODID:-//Cambium//deadline_radar//EN")
    lines.append("CALSCALE:GREGORIAN")

    for r in rows:
        dtstart = r["deadline"].replace("-", "")
        d = datetime.strptime(r["deadline"], DATE_FMT)
        dtend = (d + timedelta(days=1)).strftime("%Y%m%d")
        safe_name = "".join(c if c.isalnum() else "-" for c in r["name"]).strip("-").lower() or "deadline"
        uid = f"{safe_name}-{dtstart}@cambium"
        summary = _ics_escape(f"{r['name']} deadline ({r['funder']})")
        lines.append("BEGIN:VEVENT")
        lines.append(f"UID:{uid}")
        lines.append(f"DTSTAMP:{now_stamp}")
        lines.append(f"DTSTART;VALUE=DATE:{dtstart}")
        lines.append(f"DTEND;VALUE=DATE:{dtend}")
        lines.append(f"SUMMARY:{summary}")
        lines.append("BEGIN:VALARM")
        lines.append("ACTION:DISPLAY")
        lines.append(f"DESCRIPTION:{summary}")
        lines.append(f"TRIGGER:-P{alarm_days_before}D")
        lines.append("END:VALARM")
        lines.append("END:VEVENT")

    lines.append("END:VCALENDAR")
    # RFC 5545 requires CRLF line endings
    return "\r\n".join(lines) + "\r\n"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Multi-solicitation deadline calendar. Advisory only; confirm dates against the solicitation."
    )
    ap.add_argument("--rules", nargs="*", default=[], help="One or more rules JSON files.")
    ap.add_argument("--add", action="append", default=[], help='Repeatable: "name=...,funder=...,deadline=YYYY-MM-DD"')
    ap.add_argument("--today", default=None, help="YYYY-MM-DD; default: current UTC date.")
    ap.add_argument("--out", default=None, help="Output path for the Markdown report (default: stdout).")
    ap.add_argument("--ics", default=None, help="Output path for a .ics calendar file (optional).")
    args = ap.parse_args(argv)

    items: list[dict] = []
    for path in args.rules:
        items.extend(items_from_rules_file(path))
    for raw in args.add:
        items.append(item_from_add_string(raw))

    items = merge_and_dedupe(items)

    if not items:
        print("[deadline_radar] no deadlines given (use --rules and/or --add)", file=sys.stderr)

    if args.today:
        _validate_date(args.today, "--today")
        today = datetime.strptime(args.today, DATE_FMT)
    else:
        today = datetime.utcnow()

    rows = compute_rows(items, today)
    report = build_report(rows, today)

    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(report)
        print(f"[deadline_radar] wrote {args.out}")
    else:
        sys.stdout.write(report)

    if args.ics:
        ics_text = build_ics(rows)
        os.makedirs(os.path.dirname(os.path.abspath(args.ics)) or ".", exist_ok=True)
        with open(args.ics, "w", encoding="utf-8", newline="") as fh:
            fh.write(ics_text)
        print(f"[deadline_radar] wrote {args.ics}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
