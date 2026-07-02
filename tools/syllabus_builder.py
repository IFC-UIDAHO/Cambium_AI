#!/usr/bin/env python3
"""syllabus_builder -- compose Cambium Academy modules into a dated syllabus.

Reads academy/courses.json (the same file academy/index.html is generated
from), and lays selected modules onto a weekly calendar starting at a given
date. Emits a Markdown syllabus (week number, session dates, module title,
one-line objectives pulled from the module's "summary" field) and an
optional .ics calendar with one VEVENT per session.

Module discovery: modules are read in the order they appear in
academy/courses.json ("academy order"). --modules accepts a comma-separated
list of module ids in the order you want them taught (not necessarily
academy order), or the literal string "all" for every module in academy
order.

Session dating: session 1 starts on --start. With --per-week 1 (default),
session N lands 7*(N-1) days after --start. With --per-week 2, sessions
alternate weeks in pairs: session 1 and 2 both fall in week 1 (session 2 is
3 days after session 1, session 3 starts week 2, etc.) -- in general,
session index i (0-based) is in week (i // per_week), and its date is
--start + 7*(i // per_week) + round(3.5 * (i % per_week)) days, so multiple
sessions in the same week are spread across it rather than stacked same-day.

Usage:
  python3 tools/syllabus_builder.py --modules way,evidence,gates --start 2026-09-01
  python3 tools/syllabus_builder.py --modules all --start 2026-09-01 --per-week 2 --out syllabus.md --ics syllabus.ics

Exit codes:
  0 -- syllabus built
  1 -- an unknown module id was requested (message lists valid ids)
  2 -- academy/courses.json missing or unreadable
"""
from __future__ import annotations
import argparse
import json
import os
import sys
from datetime import datetime, timedelta

import cambium_io  # noqa: F401  (UTF-8 stdout guard)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATE_FMT = "%Y-%m-%d"


def _load_courses(courses_path: str) -> dict:
    if not os.path.exists(courses_path):
        print(f"[syllabus_builder] ERROR: academy file not found: {courses_path}", file=sys.stderr)
        sys.exit(2)
    try:
        with open(courses_path, encoding="utf-8") as fh:
            return json.load(fh)
    except json.JSONDecodeError as exc:
        print(f"[syllabus_builder] ERROR: academy file is not valid JSON: {courses_path}\n  {exc}", file=sys.stderr)
        sys.exit(2)
    except OSError as exc:
        print(f"[syllabus_builder] ERROR: cannot read academy file: {courses_path}\n  {exc}", file=sys.stderr)
        sys.exit(2)


def discover_modules(courses: dict) -> list[dict]:
    """Modules in academy order, as they appear in courses.json."""
    return list(courses.get("modules", []))


def select_modules(courses: dict, spec: str) -> list[dict]:
    """Resolve --modules spec ('all' or a comma-list of ids) against discovered modules.

    Exits 1 (listing valid ids) if any requested id is unknown.
    """
    catalog = discover_modules(courses)
    by_id = {m.get("id"): m for m in catalog}

    if spec.strip().lower() == "all":
        return catalog

    requested = [s.strip() for s in spec.split(",") if s.strip()]
    unknown = [r for r in requested if r not in by_id]
    if unknown:
        valid = ", ".join(sorted(by_id.keys()))
        print(
            f"[syllabus_builder] ERROR: unknown module id(s): {', '.join(unknown)}\n"
            f"  valid module ids: {valid}",
            file=sys.stderr,
        )
        sys.exit(1)
    return [by_id[r] for r in requested]


def module_objective(mod: dict) -> str:
    """One-line objectives pulled from the module's summary, else its first lesson title."""
    summary = mod.get("summary")
    if summary:
        return summary
    lessons = mod.get("lessons") or []
    if lessons and lessons[0].get("title"):
        return lessons[0]["title"]
    return "(no objective text found in module)"


# ---------------------------------------------------------------------------
# Session scheduling
# ---------------------------------------------------------------------------

def schedule_sessions(modules: list[dict], start: datetime, per_week: int) -> list[dict]:
    """Return one session dict per module, dated per the per-week rule in the module docstring."""
    per_week = max(1, per_week)
    sessions = []
    for i, mod in enumerate(modules):
        week = i // per_week
        slot_in_week = i % per_week
        offset_days = 7 * week + round(3.5 * slot_in_week)
        date = start + timedelta(days=offset_days)
        sessions.append({
            "week": week + 1,
            "date": date,
            "module_id": mod.get("id", f"module{i}"),
            "title": mod.get("title", mod.get("id", f"module{i}")),
            "objective": module_objective(mod),
        })
    return sessions


# ---------------------------------------------------------------------------
# Markdown output
# ---------------------------------------------------------------------------

def build_markdown(sessions: list[dict], start: datetime, per_week: int) -> str:
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    lines: list[str] = []
    lines.append("# Cambium Academy syllabus")
    lines.append("")
    lines.append(f"**Generated:** {now}")
    lines.append(f"**Start date:** {start.strftime(DATE_FMT)}")
    lines.append(f"**Sessions per week:** {per_week}")
    lines.append(f"**Sessions:** {len(sessions)}")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Weekly schedule")
    lines.append("")
    lines.append("| Week | Date | Module | Objectives |")
    lines.append("|---|---|---|---|")
    for s in sessions:
        lines.append(
            f"| {s['week']} | {s['date'].strftime(DATE_FMT)} | {s['title']} | {s['objective']} |"
        )
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(
        "*Objectives are pulled from each module's summary field in academy/courses.json. "
        "This syllabus is a scheduling aid; an instructor should review pacing before publishing it.*"
    )
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ICS output (deterministic UIDs from module id + date)
# ---------------------------------------------------------------------------

def _ics_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace(",", "\\,").replace(";", "\\;")


def build_ics(sessions: list[dict]) -> str:
    now_stamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    lines: list[str] = []
    lines.append("BEGIN:VCALENDAR")
    lines.append("VERSION:2.0")
    lines.append("PRODID:-//Cambium//syllabus_builder//EN")
    lines.append("CALSCALE:GREGORIAN")

    for s in sessions:
        dtstart = s["date"].strftime("%Y%m%d")
        dtend = (s["date"] + timedelta(days=1)).strftime("%Y%m%d")
        uid = f"syllabus-{s['module_id']}-{dtstart}@cambium"
        summary = _ics_escape(f"Academy: {s['title']}")
        lines.append("BEGIN:VEVENT")
        lines.append(f"UID:{uid}")
        lines.append(f"DTSTAMP:{now_stamp}")
        lines.append(f"DTSTART;VALUE=DATE:{dtstart}")
        lines.append(f"DTEND;VALUE=DATE:{dtend}")
        lines.append(f"SUMMARY:{summary}")
        lines.append(f"DESCRIPTION:{_ics_escape(s['objective'])}")
        lines.append("END:VEVENT")

    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse_date(raw: str) -> datetime:
    try:
        return datetime.strptime(raw, DATE_FMT)
    except ValueError:
        print(f"[syllabus_builder] ERROR: --start must be YYYY-MM-DD, got: {raw}", file=sys.stderr)
        sys.exit(2)


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Compose Cambium Academy modules into a dated syllabus (Markdown + optional .ics)."
    )
    ap.add_argument("--modules", required=True, help="Comma-separated module ids, or 'all' for academy order.")
    ap.add_argument("--start", required=True, help="First session date, YYYY-MM-DD.")
    ap.add_argument("--per-week", type=int, default=1, help="Sessions per week (default: 1).")
    ap.add_argument("--courses", default=os.path.join(ROOT, "academy", "courses.json"),
                     help="Path to academy/courses.json (default: repo's academy/courses.json).")
    ap.add_argument("--out", default=os.path.join("agent_outputs", "syllabus.md"),
                     help="Output Markdown path (default: agent_outputs/syllabus.md).")
    ap.add_argument("--ics", default=None, help="Optional output path for a .ics calendar file.")
    args = ap.parse_args(argv)

    courses = _load_courses(args.courses)
    modules = select_modules(courses, args.modules)
    start = _parse_date(args.start)
    sessions = schedule_sessions(modules, start, args.per_week)

    md = build_markdown(sessions, start, args.per_week)
    out_dir = os.path.dirname(os.path.abspath(args.out)) or "."
    os.makedirs(out_dir, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(md)
    print(f"[syllabus_builder] wrote {args.out} ({len(sessions)} sessions)")

    if args.ics:
        ics_text = build_ics(sessions)
        ics_dir = os.path.dirname(os.path.abspath(args.ics)) or "."
        os.makedirs(ics_dir, exist_ok=True)
        with open(args.ics, "w", encoding="utf-8", newline="") as fh:
            fh.write(ics_text)
        print(f"[syllabus_builder] wrote {args.ics}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
