#!/usr/bin/env python3
"""effort_cert -- person-month / percent-effort arithmetic with an audit line.

Converts between percent effort and person-months for the three common
appointment lengths (calendar 12 months, academic 9 months, summer 3 months),
and prorates chargeable salary against an optional sponsor salary cap.

ADVISORY: this tool does the arithmetic and appends a contemporaneous ledger
row. It is not effort certification in the federal compliance sense, not a
system of record for institutional payroll, and not a substitute for the
effort reporting process required by the institution's policy and 2 CFR 200.
A human (the PI or department administrator) must review and certify effort;
this tool only helps them do the math consistently and leaves a paper trail.
Salary and cap values are INPUTS supplied by the caller; this tool never
invents or looks up a rate.

Conversions:
  percent effort -> person-months = percent/100 * appointment_months
  person-months -> percent effort = pm / appointment_months * 100
  appointment_months: calendar=12, academic=9, summer=3

Salary proration:
  requested = salary * (pm / appointment_months)
  if --cap is given and salary > cap:
      chargeable = cap * (pm / appointment_months)   (capped)
  else:
      chargeable = requested                          (no cap, or salary <= cap)
  The cap is an INPUT the caller supplies (e.g. an agency salary cap such as
  NIH's); this tool never looks one up or assumes one.

Subcommands:
  convert   -- print the conversion (and proration, if --salary given)
  certify   -- run the same computation and append one contemporaneous CSV
               row to a ledger: [date-iso, person, award, appt, percent, pm,
               salary, cap, chargeable]

Exit codes:
  0  -- computed / certified
  1  -- invalid input (percent out of [0, 100], negative pm/salary, bad appt)
  2  -- ledger path not writable

Usage:
  python3 tools/effort_cert.py convert --appt academic --percent 25
  python3 tools/effort_cert.py convert --appt calendar --pm 3 --salary 120000 --cap 100000
  python3 tools/effort_cert.py certify --appt summer --percent 100 --salary 12000 \
      --person "J. Doe" --award "NSF-1234567"
  python3 tools/effort_cert.py certify --appt academic --pm 1 --salary 90000 --cap 80000 \
      --person "J. Doe" --award "NSF-1234567" --ledger governance/EFFORT_LEDGER.csv
"""
from __future__ import annotations
import argparse
import csv
import os
import sys
from datetime import datetime, timezone

# UTF-8 stdout guard
import cambium_io  # noqa: F401

APPT_MONTHS = {"calendar": 12, "academic": 9, "summer": 3}
LEDGER_DEFAULT = os.path.join("governance", "EFFORT_LEDGER.csv")
LEDGER_HEADER = ["date", "person", "award", "appt", "percent", "pm", "salary", "cap", "chargeable"]


# ---------------------------------------------------------------------------
# Core arithmetic
# ---------------------------------------------------------------------------

def percent_to_pm(percent: float, appt: str) -> float:
    """Convert percent effort to person-months for the given appointment type."""
    months = APPT_MONTHS[appt]
    return percent / 100.0 * months


def pm_to_percent(pm: float, appt: str) -> float:
    """Convert person-months to percent effort for the given appointment type."""
    months = APPT_MONTHS[appt]
    return pm / months * 100.0


def prorate_salary(salary: float, pm: float, appt: str, cap: float | None) -> dict:
    """Compute requested and (possibly capped) chargeable salary for pm months of effort.

    requested = salary * (pm / appointment_months)
    chargeable = min(requested-at-cap-rate, requested) when cap is given and
    salary exceeds it; otherwise chargeable == requested (no-cap passthrough).
    """
    months = APPT_MONTHS[appt]
    fraction = pm / months
    requested = salary * fraction
    if cap is not None and salary > cap:
        chargeable = cap * fraction
    else:
        chargeable = requested
    return {"requested": requested, "chargeable": chargeable, "fraction": fraction}


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def _fail(msg: str) -> None:
    print(f"[effort_cert] ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def _validate_appt(appt: str) -> None:
    if appt not in APPT_MONTHS:
        _fail(f"--appt must be one of {sorted(APPT_MONTHS)}, got: {appt}")


def _validate_percent(percent: float) -> None:
    if percent < 0 or percent > 100:
        _fail(f"--percent must be between 0 and 100, got: {percent}")


def _validate_pm(pm: float, appt: str) -> None:
    months = APPT_MONTHS[appt]
    if pm < 0 or pm > months:
        _fail(f"--pm must be between 0 and {months} for appt={appt}, got: {pm}")


def _validate_salary(salary: float | None) -> None:
    if salary is not None and salary < 0:
        _fail(f"--salary must be >= 0, got: {salary}")


def _validate_cap(cap: float | None) -> None:
    if cap is not None and cap < 0:
        _fail(f"--cap must be >= 0, got: {cap}")


def resolve_inputs(args) -> dict:
    """Validate args and resolve to a single canonical (appt, percent, pm) triple."""
    _validate_appt(args.appt)
    if args.percent is None and args.pm is None:
        _fail("one of --percent or --pm is required")
    if args.percent is not None and args.pm is not None:
        _fail("give only one of --percent or --pm, not both")
    _validate_salary(args.salary)
    _validate_cap(args.cap)

    if args.percent is not None:
        _validate_percent(args.percent)
        pm = percent_to_pm(args.percent, args.appt)
        percent = args.percent
    else:
        _validate_pm(args.pm, args.appt)
        pm = args.pm
        percent = pm_to_percent(args.pm, args.appt)

    result = {"appt": args.appt, "percent": percent, "pm": pm}
    if args.salary is not None:
        result.update(prorate_salary(args.salary, pm, args.appt, args.cap))
        result["salary"] = args.salary
        result["cap"] = args.cap
    return result


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def format_result(result: dict) -> str:
    lines = []
    lines.append(f"Appointment: {result['appt']} ({APPT_MONTHS[result['appt']]} months)")
    lines.append(f"Percent effort: {result['percent']:.4f}%")
    lines.append(f"Person-months: {result['pm']:.4f}")
    if "requested" in result:
        lines.append(f"Salary (annual, input): {result['salary']:.2f}")
        lines.append(f"Requested chargeable (uncapped): {result['requested']:.2f}")
        if result.get("cap") is not None:
            lines.append(f"Cap (input): {result['cap']:.2f}")
            if result["salary"] > result["cap"]:
                lines.append(f"Chargeable (capped): {result['chargeable']:.2f}")
            else:
                lines.append(f"Chargeable (salary at/under cap, no proration): {result['chargeable']:.2f}")
        else:
            lines.append(f"Chargeable (no cap given): {result['chargeable']:.2f}")
    lines.append("")
    lines.append(
        "ADVISORY: this is arithmetic support, not effort certification. "
        "A human must certify actual effort per institutional policy."
    )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Ledger
# ---------------------------------------------------------------------------

def append_ledger(ledger_path: str, person: str, award: str, result: dict) -> None:
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    row = [
        now_iso,
        person,
        award,
        result["appt"],
        f"{result['percent']:.4f}",
        f"{result['pm']:.4f}",
        f"{result.get('salary', '')}" if result.get("salary") is not None else "",
        f"{result.get('cap', '')}" if result.get("cap") is not None else "",
        f"{result.get('chargeable', '')}" if "chargeable" in result else "",
    ]
    try:
        os.makedirs(os.path.dirname(os.path.abspath(ledger_path)) or ".", exist_ok=True)
        is_new = not os.path.exists(ledger_path)
        with open(ledger_path, "a", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            if is_new:
                w.writerow(LEDGER_HEADER)
            w.writerow(row)
    except OSError as exc:
        print(f"[effort_cert] ERROR: cannot write ledger {ledger_path}\n  {exc}", file=sys.stderr)
        sys.exit(2)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _add_common_args(sp) -> None:
    sp.add_argument("--appt", required=True, choices=sorted(APPT_MONTHS), help="Appointment type.")
    sp.add_argument("--percent", type=float, default=None, help="Percent effort (0-100). Mutually exclusive with --pm.")
    sp.add_argument("--pm", type=float, default=None, help="Person-months. Mutually exclusive with --percent.")
    sp.add_argument("--salary", type=float, default=None, help="Annual salary (input; not looked up).")
    sp.add_argument("--cap", type=float, default=None, help="Sponsor salary cap, annual (input; not looked up).")


def main(argv=None):
    ap = argparse.ArgumentParser(
        description=(
            "Person-month / percent-effort arithmetic with an audit line. "
            "ADVISORY: not effort certification, not a system of record."
        )
    )
    sub = ap.add_subparsers(dest="cmd", required=True)

    sp_convert = sub.add_parser("convert", help="Print the conversion and proration.")
    _add_common_args(sp_convert)

    sp_certify = sub.add_parser("certify", help="Compute and append a ledger row.")
    _add_common_args(sp_certify)
    sp_certify.add_argument("--person", required=True, help="Person name or ID.")
    sp_certify.add_argument("--award", required=True, help="Award or project identifier.")
    sp_certify.add_argument("--ledger", default=LEDGER_DEFAULT, help="Path to the effort ledger CSV.")

    args = ap.parse_args(argv)

    result = resolve_inputs(args)

    if args.cmd == "convert":
        print(format_result(result))
        return 0

    # certify
    append_ledger(args.ledger, args.person, args.award, result)
    print(format_result(result))
    print(f"[effort_cert] certified and appended to {args.ledger}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
