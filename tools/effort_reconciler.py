#!/usr/bin/env python3
"""effort_reconciler -- person-months commitment reconciler across projects (advisory).

Motivation: 2 CFR 200.430 (Compensation - personal services) requires that
compensation charged to federal awards reflects work actually performed, so
institutions track committed effort against what is available. That regulation
is named here as motivation only; nothing in this tool is legal advice, and
this tool is not an effort certification.

Conversion used and documented here:
  - 1 academic month counts as 1 month of a 9-month academic-year appointment.
  - A full year decomposes as 12 calendar months = 9 academic months
    + 3 summer months.
  - Calendar-month equivalent of a project entry = cal_months + acad_months
    + sum_months.
Confirm your institution's own conversion policy before relying on this.

Input (--commitments YAML):
  people:
    - name: Dr. Ada Example
      appointment: academic9+summer   # calendar | academic9 | academic9+summer
      projects:
        - {name: PROJ-1, acad_months: 2, period: Y1}
        - {name: PROJ-1 summer, sum_months: 1, period: Y1}
        - {name: PROJ-2, cal_months: 3, period: Y2}

Per person and period the tool totals calendar-month equivalents and reports:
  - OVER (flag): total > 12 calendar months in a period (over 100 percent).
  - NEAR CAP (warning): total >= --warn-at (default 11.4, i.e. 95 percent of 12).
  - Appointment mismatch flags: academic or summer months on a calendar
    appointment; summer months on a plain academic9 appointment; academic
    months over 9; summer months over 3.
  - Negative months values (flag).

Exit codes:
  0 -- reconciliation complete (flags and warnings are reported in the body)
  1 -- invalid input (missing, unreadable, or malformed YAML; non-numeric
       months; unknown appointment), or any FLAG when --strict is given
       (warnings alone do not trip --strict)

Usage:
  python3 tools/effort_reconciler.py --commitments commitments.yml
  python3 tools/effort_reconciler.py --commitments commitments.yml --warn-at 11.0
  python3 tools/effort_reconciler.py --commitments commitments.yml --strict --out effort.md

Limits (honest):
  - Totals come only from the input file. The tool knows nothing about actual
    appointments, payroll records, or sponsor-specific effort rules.
  - Periods are free-text labels from your file (e.g. Y1, 2026-2027); the tool
    groups by exact label and sorts labels lexically.
"""
from __future__ import annotations
import argparse
import os
import sys

import yaml

# UTF-8 stdout guard
import cambium_io  # noqa: F401

APPOINTMENTS = ("calendar", "academic9", "academic9+summer")
CAP = 12.0
ACAD_MAX = 9.0
SUMMER_MAX = 3.0
EPS = 1e-9


# ---------------------------------------------------------------------------
# Loader and validation
# ---------------------------------------------------------------------------

def _fail(msg: str) -> None:
    print(f"[effort_reconciler] ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def _load_yaml(path: str) -> dict:
    if not os.path.exists(path):
        _fail(f"commitments file not found: {path}")
    try:
        with open(path, encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
    except yaml.YAMLError as exc:
        _fail(f"commitments file is not valid YAML: {path}\n  {exc}")
    except OSError as exc:
        _fail(f"cannot read commitments file: {path}\n  {exc}")
    if not isinstance(data, dict) or not isinstance(data.get("people"), list):
        _fail(f"commitments file must be a YAML mapping with a 'people' list: {path}")
    return data


def _num(value, ctx: str) -> float:
    if isinstance(value, bool) or value is None:
        _fail(f"months value is not numeric for {ctx}: {value!r}")
    try:
        return float(value)
    except (TypeError, ValueError):
        _fail(f"months value is not numeric for {ctx}: {value!r}")
    return 0.0  # unreachable; keeps type checkers calm


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------

def analyze(data: dict, warn_at: float) -> dict:
    """Reconcile commitments. Returns {people: [...], flags: [...], warnings: [...]}."""
    flags: list[str] = []
    warnings: list[str] = []
    people_out: list[dict] = []

    for pi, person in enumerate(data.get("people") or [], start=1):
        if not isinstance(person, dict):
            _fail(f"people[{pi}] is not a mapping")
        name = str(person.get("name") or f"person {pi}")
        appointment = person.get("appointment")
        if appointment not in APPOINTMENTS:
            _fail(f"{name}: unknown appointment {appointment!r} "
                  f"(expected one of: {', '.join(APPOINTMENTS)})")

        periods: dict[str, dict] = {}
        for entry in person.get("projects") or []:
            if not isinstance(entry, dict):
                _fail(f"{name}: project entry is not a mapping: {entry!r}")
            project = str(entry.get("name") or "unnamed project")
            period = str(entry.get("period") or "unspecified")
            cal = _num(entry.get("cal_months", 0), f"{name} / {project} cal_months")
            acad = _num(entry.get("acad_months", 0), f"{name} / {project} acad_months")
            summer = _num(entry.get("sum_months", 0), f"{name} / {project} sum_months")
            for label, v in (("cal_months", cal), ("acad_months", acad), ("sum_months", summer)):
                if v < 0:
                    flags.append(f"{name} / {period} / {project}: negative {label} value {v:g}.")
            agg = periods.setdefault(period, {"cal": 0.0, "acad": 0.0, "summer": 0.0,
                                              "total": 0.0, "rows": [], "status": "OK"})
            equiv = cal + acad + summer
            agg["cal"] += cal
            agg["acad"] += acad
            agg["summer"] += summer
            agg["total"] += equiv
            agg["rows"].append({"project": project, "cal": cal, "acad": acad,
                                "summer": summer, "equiv": equiv})

        for period in sorted(periods):
            agg = periods[period]
            total = agg["total"]
            if total > CAP + EPS:
                agg["status"] = "OVER"
                flags.append(f"{name} / {period}: total {total:.2f} calendar-month equivalents "
                             f"exceeds the {CAP:.2f} cap (over 100 percent effort).")
            elif total >= warn_at - EPS:
                agg["status"] = "NEAR CAP"
                warnings.append(f"{name} / {period}: total {total:.2f} calendar-month equivalents "
                                f"is at or above the near-cap threshold {warn_at:.2f}.")
            if appointment == "calendar" and (agg["acad"] > EPS or agg["summer"] > EPS):
                flags.append(f"{name} / {period}: academic or summer months listed on a "
                             f"calendar appointment; entry types do not match the appointment.")
            if appointment == "academic9" and agg["summer"] > EPS:
                flags.append(f"{name} / {period}: summer months listed but the appointment is "
                             f"academic9 with no summer term stated.")
            if appointment in ("academic9", "academic9+summer") and agg["acad"] > ACAD_MAX + EPS:
                flags.append(f"{name} / {period}: academic months total {agg['acad']:.2f} exceeds "
                             f"the {ACAD_MAX:.2f} available on a 9-month appointment.")
            if appointment == "academic9+summer" and agg["summer"] > SUMMER_MAX + EPS:
                flags.append(f"{name} / {period}: summer months total {agg['summer']:.2f} exceeds "
                             f"the {SUMMER_MAX:.2f} available summer months.")

        people_out.append({"name": name, "appointment": appointment, "periods": periods})

    return {"people": people_out, "flags": flags, "warnings": warnings}


# ---------------------------------------------------------------------------
# Report builder
# ---------------------------------------------------------------------------

def _cell(text) -> str:
    return str(text).replace("|", "\\|")


def build_report(analysis: dict, warn_at: float, src_path: str) -> str:
    lines: list[str] = []
    lines.append("# Effort reconciliation (advisory, not an effort certification)")
    lines.append("")
    lines.append(
        "> Bookkeeping aid motivated by 2 CFR 200.430 (compensation and effort principles). "
        "Conversion documented in the tool: 1 academic month = 1 month of a 9-month "
        "appointment; 12 calendar months = 9 academic + 3 summer. This is not legal advice "
        "and not a certification of effort."
    )
    lines.append("")
    lines.append(f"**Commitments file:** {os.path.basename(src_path)}")
    lines.append(f"**Cap:** {CAP:.2f} calendar-month equivalents per period | "
                 f"**Near-cap warning at:** {warn_at:.2f}")
    lines.append(f"**People:** {len(analysis['people'])} | **Flags:** {len(analysis['flags'])} | "
                 f"**Warnings:** {len(analysis['warnings'])}")
    lines.append("")

    for person in analysis["people"]:
        lines.append("---")
        lines.append("")
        lines.append(f"## {person['name']} (appointment: {person['appointment']})")
        lines.append("")
        if not person["periods"]:
            lines.append("No project entries listed.")
            lines.append("")
            continue
        lines.append("| Period | Project | Cal | Acad | Summer | Cal-equivalent |")
        lines.append("|---|---|---|---|---|---|")
        for period in sorted(person["periods"]):
            agg = person["periods"][period]
            for row in agg["rows"]:
                lines.append(f"| {_cell(period)} | {_cell(row['project'])} | {row['cal']:.2f} | "
                             f"{row['acad']:.2f} | {row['summer']:.2f} | {row['equiv']:.2f} |")
            lines.append(f"| {_cell(period)} | (period total) | {agg['cal']:.2f} | "
                         f"{agg['acad']:.2f} | {agg['summer']:.2f} | "
                         f"{agg['total']:.2f} ({agg['status']}) |")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## Flags")
    lines.append("")
    if analysis["flags"]:
        lines.extend(f"- {f}" for f in analysis["flags"])
    else:
        lines.append("- No flags.")
    lines.append("")
    lines.append("## Warnings")
    lines.append("")
    if analysis["warnings"]:
        lines.extend(f"- {w}" for w in analysis["warnings"])
    else:
        lines.append("- No warnings.")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Closing statement")
    lines.append("")
    lines.append(
        "**This reconciliation is advisory: review, not validation. Totals derive only from "
        "the commitments file supplied, using the conversion documented above. It is not an "
        "effort certification and not legal advice. A human in sponsored programs must verify "
        "commitments against appointments and institutional policy and make the final "
        "determination.**"
    )
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description=(
            "Advisory person-months reconciler across projects. Converts commitments to "
            "calendar-month equivalents, totals per person and period, and flags "
            "over-commitment. Not an effort certification."
        )
    )
    ap.add_argument("--commitments", required=True, help="Path to commitments YAML file.")
    ap.add_argument("--warn-at", type=float, default=11.4,
                    help="Near-cap warning threshold in calendar months (default: 11.4, "
                         "i.e. 95 percent of 12).")
    ap.add_argument("--strict", action="store_true",
                    help="Exit 1 if any FLAG is raised (warnings do not count).")
    ap.add_argument("--out", default=None,
                    help="Output path for the Markdown report (default: print to stdout).")
    args = ap.parse_args(argv)

    data = _load_yaml(args.commitments)
    analysis = analyze(data, args.warn_at)
    report = build_report(analysis, args.warn_at, args.commitments)

    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(report)
        print(f"[effort_reconciler] wrote {args.out}")
    else:
        sys.stdout.write(report)

    if args.strict and analysis["flags"]:
        print(f"[effort_reconciler] --strict: {len(analysis['flags'])} flag(s) raised.",
              file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
