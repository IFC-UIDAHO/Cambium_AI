#!/usr/bin/env python3
"""award_calendar -- post-award compliance calendar from stated award terms (advisory).

Builds a deterministic schedule of reporting periods and due dates from the
award start/end and the reporting requirements you state. No deadline rules
are invented: every period and due date derives arithmetically from the input
file. Advisory only: verify every date against the award terms and sponsor
system of record before relying on it.

Input (--award YAML):
  start: 2026-09-01
  end: 2029-08-31
  reports:
    - {type: RPPR, frequency: annual, due_days_after_period_end: 60}
    - {type: Financial report, frequency: quarterly, due_days_after_period_end: 30}
    - {type: Final RPPR, frequency: final, due_days_after_period_end: 120}
  other_deadlines:                    # optional one-time items
    - {item: IRB renewal, date: 2027-03-15}

Schedule computation (stdlib datetime only):
  - frequency months: monthly=1, quarterly=3, semiannual=6, annual=12;
    final = a single period covering the whole award.
  - Period i runs from add_months(start, (i-1) x m) to
    add_months(start, i x m) - 1 day, truncated at the award end.
  - add_months clamps the day of month (e.g. Jan 31 + 1 month = Feb 28/29),
    so start days of 29-31 produce clamped boundaries; the table shows them.
  - due date = period end + due_days_after_period_end days.

Lead-time display:
  - Status vs --today (default: system date; pass an ISO date for
    deterministic output): OVERDUE if due before today, otherwise
    "due within N days" when due within --lead-days (default 30, a display
    threshold of this tool, not a sponsor rule), otherwise "scheduled".

Optional --ics FILE writes a minimal VCALENDAR with one all-day VEVENT per
due date (text escaped per RFC 5545; DTSTAMP is derived from --today so the
file is deterministic for a fixed --today).

Exit codes:
  0 -- schedule built
  1 -- invalid input (missing, unreadable, or malformed YAML; unparseable
       dates; end before start; unknown frequency; missing or non-integer
       due_days_after_period_end; malformed other_deadlines)

Usage:
  python3 tools/award_calendar.py --award award.yml
  python3 tools/award_calendar.py --award award.yml --today 2026-10-01 --lead-days 45
  python3 tools/award_calendar.py --award award.yml --ics award.ics --out schedule.md

Limits (honest):
  - The tool schedules only what you state. It does not know sponsor policy,
    grace periods, business-day rules, or time zones; all dates are plain
    calendar dates.
"""
from __future__ import annotations
import argparse
import calendar as _calendar
import datetime
import os
import sys

import yaml

# UTF-8 stdout guard
import cambium_io  # noqa: F401

FREQ_MONTHS = {"monthly": 1, "quarterly": 3, "semiannual": 6, "annual": 12}


# ---------------------------------------------------------------------------
# Loader and date helpers
# ---------------------------------------------------------------------------

def _fail(msg: str) -> None:
    print(f"[award_calendar] ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def _load_yaml(path: str) -> dict:
    if not os.path.exists(path):
        _fail(f"award file not found: {path}")
    try:
        with open(path, encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
    except yaml.YAMLError as exc:
        _fail(f"award file is not valid YAML: {path}\n  {exc}")
    except OSError as exc:
        _fail(f"cannot read award file: {path}\n  {exc}")
    if not isinstance(data, dict):
        _fail(f"award file must be a YAML mapping: {path}")
    return data


def _to_date(value, ctx: str) -> datetime.date:
    if isinstance(value, datetime.datetime):
        return value.date()
    if isinstance(value, datetime.date):
        return value
    try:
        return datetime.date.fromisoformat(str(value).strip())
    except (TypeError, ValueError):
        _fail(f"{ctx} is not a parseable date (expected YYYY-MM-DD): {value!r}")
    return datetime.date.min  # unreachable


def add_months(d: datetime.date, n: int) -> datetime.date:
    """Add n months to d, clamping the day to the target month's length."""
    y = d.year + (d.month - 1 + n) // 12
    m = (d.month - 1 + n) % 12 + 1
    last = _calendar.monthrange(y, m)[1]
    return datetime.date(y, m, min(d.day, last))


# ---------------------------------------------------------------------------
# Schedule builder
# ---------------------------------------------------------------------------

def build_schedule(award: dict) -> list[dict]:
    """Return schedule rows: {item, period, period_end, due}, sorted by due date."""
    start = _to_date(award.get("start"), "start")
    end = _to_date(award.get("end"), "end")
    if end < start:
        _fail(f"end {end} is before start {start}")

    rows: list[dict] = []

    for ri, rep in enumerate(award.get("reports") or [], start=1):
        if not isinstance(rep, dict):
            _fail(f"reports[{ri}] is not a mapping")
        rtype = rep.get("type")
        if not rtype:
            _fail(f"reports[{ri}] is missing 'type'")
        rtype = str(rtype)
        freq = rep.get("frequency")
        if freq != "final" and freq not in FREQ_MONTHS:
            _fail(f"{rtype}: unknown frequency {freq!r} (expected monthly, quarterly, "
                  f"semiannual, annual, or final)")
        due_days = rep.get("due_days_after_period_end")
        if isinstance(due_days, bool) or not isinstance(due_days, int):
            _fail(f"{rtype}: due_days_after_period_end must be an integer, got {due_days!r}")

        if freq == "final":
            due = end + datetime.timedelta(days=due_days)
            rows.append({"item": rtype, "period": f"final ({start} to {end})",
                         "period_end": end, "due": due})
            continue

        months = FREQ_MONTHS[freq]
        i = 1
        while True:
            p_start = add_months(start, (i - 1) * months)
            if p_start > end:
                break
            p_end = min(add_months(start, i * months) - datetime.timedelta(days=1), end)
            due = p_end + datetime.timedelta(days=due_days)
            rows.append({"item": rtype, "period": f"P{i} ({p_start} to {p_end})",
                         "period_end": p_end, "due": due})
            i += 1

    for di, od in enumerate(award.get("other_deadlines") or [], start=1):
        if not isinstance(od, dict) or not od.get("item"):
            _fail(f"other_deadlines[{di}] must be a mapping with 'item' and 'date'")
        due = _to_date(od.get("date"), f"other_deadlines[{di}].date")
        rows.append({"item": str(od["item"]), "period": "one-time",
                     "period_end": due, "due": due})

    rows.sort(key=lambda r: (r["due"].isoformat(), r["item"], r["period"]))
    return rows


def _status(due: datetime.date, today: datetime.date, lead_days: int) -> str:
    if due < today:
        return "OVERDUE"
    if (due - today).days <= lead_days:
        return f"due within {lead_days} days"
    return "scheduled"


# ---------------------------------------------------------------------------
# Report and ICS builders
# ---------------------------------------------------------------------------

def _cell(text) -> str:
    return str(text).replace("|", "\\|")


def build_report(rows: list[dict], award: dict, src_path: str,
                 today: datetime.date, lead_days: int) -> str:
    lines: list[str] = []
    lines.append("# Award compliance calendar (advisory, derived from your input only)")
    lines.append("")
    lines.append(
        "> Every period and due date below is computed arithmetically from the award file "
        "you supplied. No sponsor rules are encoded or assumed. Verify each date against "
        "the award terms and the sponsor's system of record."
    )
    lines.append("")
    lines.append(f"**Award file:** {os.path.basename(src_path)}")
    lines.append(f"**Award period:** {_to_date(award.get('start'), 'start')} to "
                 f"{_to_date(award.get('end'), 'end')}")
    lines.append(f"**Today (for status):** {today} | **Lead-time threshold:** {lead_days} days")
    lines.append(f"**Scheduled items:** {len(rows)}")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Schedule")
    lines.append("")
    if not rows:
        lines.append("No reports or other deadlines were stated in the award file.")
    else:
        lines.append("| Item | Period | Period end | Due date | Days from today | Status |")
        lines.append("|---|---|---|---|---|---|")
        for r in rows:
            days = (r["due"] - today).days
            lines.append(f"| {_cell(r['item'])} | {_cell(r['period'])} | {r['period_end']} | "
                         f"{r['due']} | {days} | {_status(r['due'], today, lead_days)} |")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Closing statement")
    lines.append("")
    lines.append(
        "**This calendar is advisory: review, not validation. It derives every date from "
        "the stated award terms with plain calendar arithmetic and encodes no sponsor "
        "policy. A human in sponsored programs must confirm each due date against the "
        "notice of award and the sponsor's system before relying on it.**"
    )
    lines.append("")
    return "\n".join(lines)


def ics_escape(text: str) -> str:
    """Escape TEXT property values per RFC 5545 section 3.3.11."""
    return (str(text).replace("\\", "\\\\").replace(";", "\\;")
            .replace(",", "\\,").replace("\r\n", "\n").replace("\n", "\\n"))


def build_ics(rows: list[dict], today: datetime.date) -> str:
    """Minimal deterministic VCALENDAR: one all-day VEVENT per due date."""
    stamp = today.strftime("%Y%m%dT000000Z")
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0",
             "PRODID:-//cambium//award_calendar//EN"]
    for i, r in enumerate(rows, start=1):
        lines.extend([
            "BEGIN:VEVENT",
            f"UID:cambium-award-calendar-{i:04d}@local",
            f"DTSTAMP:{stamp}",
            f"DTSTART;VALUE=DATE:{r['due'].strftime('%Y%m%d')}",
            "SUMMARY:" + ics_escape("{0} due ({1})".format(r["item"], r["period"])),
            "END:VEVENT",
        ])
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description=(
            "Advisory post-award compliance calendar. Derives reporting periods and due "
            "dates from the stated award terms only; encodes no sponsor rules."
        )
    )
    ap.add_argument("--award", required=True, help="Path to award YAML file.")
    ap.add_argument("--today", default=None,
                    help="ISO date used for status and lead-time display "
                         "(default: system date; pass a date for deterministic output).")
    ap.add_argument("--lead-days", type=int, default=30,
                    help="Display threshold in days for the 'due within N days' status "
                         "(default: 30; a display setting of this tool, not a sponsor rule).")
    ap.add_argument("--ics", default=None,
                    help="Optional path to write a minimal iCalendar (.ics) file.")
    ap.add_argument("--out", default=None,
                    help="Output path for the Markdown schedule (default: print to stdout).")
    args = ap.parse_args(argv)

    award = _load_yaml(args.award)
    today = _to_date(args.today, "--today") if args.today else datetime.date.today()
    if args.lead_days < 0:
        _fail(f"--lead-days must be >= 0, got {args.lead_days}")

    rows = build_schedule(award)
    report = build_report(rows, award, args.award, today, args.lead_days)

    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(report)
        print(f"[award_calendar] wrote {args.out}")
    else:
        sys.stdout.write(report)

    if args.ics:
        os.makedirs(os.path.dirname(os.path.abspath(args.ics)), exist_ok=True)
        with open(args.ics, "w", encoding="utf-8", newline="") as fh:
            fh.write(build_ics(rows, today))
        print(f"[award_calendar] wrote {args.ics}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
