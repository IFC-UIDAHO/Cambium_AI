#!/usr/bin/env python3
"""subaward_register -- subaward and invoice tracking with contemporaneous records.

Maintains a CSV register of subawards and a CSV log of invoices against them,
then computes burn (invoiced / total) per subaward and flags items that look
like they need a human's attention: over-invoicing, invoices dated outside
the subaward period, and low burn close to the period end.

ADVISORY: this tool tracks numbers a human enters; it does not verify
invoices against actual subrecipient performance, does not approve payment,
and is not a system of record for financial accounting. Totals, dates, and
amounts are INPUTS supplied by the caller; nothing here is looked up or
invented. A human in sponsored programs or grants accounting must review
flags and make the final determination.

Subcommands:
  add      -- append one subaward row to the register
              [id, org, pi, total, start, end]
  invoice  -- append one invoice row against a subaward id
              [id, amount, date]  (governance/SUBAWARD_INVOICES.csv)
  status   -- print per-subaward burn and flags
  report   -- write a Markdown table of all subawards, burn, and flags

Flags (per subaward):
  OVER_INVOICED       -- sum of invoices > total committed
  OUT_OF_PERIOD       -- an invoice is dated before start or after end
  LOW_BURN_NEAR_END   -- period ends within 60 days (of --today) and burn < 50%

Exit codes:
  0  -- command completed
  1  -- unknown subaward id referenced
  2  -- register/invoice file missing or unreadable, or bad date

Usage:
  python3 tools/subaward_register.py add --id SA-001 --org "State U" --pi "A. Smith" \
      --total 150000 --start 2026-01-01 --end 2026-12-31
  python3 tools/subaward_register.py invoice --id SA-001 --amount 25000 --date 2026-03-15
  python3 tools/subaward_register.py status --id SA-001 --today 2026-11-15
  python3 tools/subaward_register.py report --out report.md --today 2026-11-15
"""
from __future__ import annotations
import argparse
import csv
import os
import sys
from datetime import datetime

# UTF-8 stdout guard
import cambium_io  # noqa: F401

DATE_FMT = "%Y-%m-%d"
REGISTER_DEFAULT = os.path.join("governance", "SUBAWARDS.csv")
INVOICES_DEFAULT = os.path.join("governance", "SUBAWARD_INVOICES.csv")
REGISTER_HEADER = ["id", "org", "pi", "total", "start", "end"]
INVOICE_HEADER = ["id", "amount", "date"]
LOW_BURN_WINDOW_DAYS = 60
LOW_BURN_THRESHOLD = 0.50


# ---------------------------------------------------------------------------
# CSV IO helpers
# ---------------------------------------------------------------------------

def _parse_date(raw: str, label: str) -> datetime:
    try:
        return datetime.strptime(raw, DATE_FMT)
    except ValueError:
        print(f"[subaward_register] ERROR: {label} must be YYYY-MM-DD, got: {raw}", file=sys.stderr)
        sys.exit(2)


def _read_csv(path: str, header: list[str]) -> list[dict]:
    if not os.path.exists(path):
        return []
    try:
        with open(path, newline="", encoding="utf-8") as fh:
            return list(csv.DictReader(fh))
    except OSError as exc:
        print(f"[subaward_register] ERROR: cannot read {path}\n  {exc}", file=sys.stderr)
        sys.exit(2)


def _append_csv(path: str, header: list[str], row: list) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
    is_new = not os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        if is_new:
            w.writerow(header)
        w.writerow(row)


def load_register(path: str) -> dict[str, dict]:
    """Return {id: {org, pi, total, start, end}} keyed by subaward id."""
    rows = _read_csv(path, REGISTER_HEADER)
    out = {}
    for r in rows:
        out[r["id"]] = {
            "org": r["org"],
            "pi": r["pi"],
            "total": float(r["total"]),
            "start": r["start"],
            "end": r["end"],
        }
    return out


def load_invoices(path: str) -> list[dict]:
    rows = _read_csv(path, INVOICE_HEADER)
    return [{"id": r["id"], "amount": float(r["amount"]), "date": r["date"]} for r in rows]


# ---------------------------------------------------------------------------
# Status computation
# ---------------------------------------------------------------------------

def compute_status(sub_id: str, subaward: dict, invoices: list[dict], today: datetime) -> dict:
    """Compute burn and flags for one subaward."""
    matching = [inv for inv in invoices if inv["id"] == sub_id]
    invoiced = sum(inv["amount"] for inv in matching)
    total = subaward["total"]
    burn = (invoiced / total) if total else 0.0
    remaining = total - invoiced

    flags = []
    if invoiced > total:
        flags.append("OVER_INVOICED")

    start_dt = _parse_date(subaward["start"], f"subaward {sub_id} start")
    end_dt = _parse_date(subaward["end"], f"subaward {sub_id} end")
    for inv in matching:
        inv_dt = _parse_date(inv["date"], f"invoice date for {sub_id}")
        if inv_dt < start_dt or inv_dt > end_dt:
            flags.append("OUT_OF_PERIOD")
            break

    days_left = (end_dt - today).days
    if 0 <= days_left <= LOW_BURN_WINDOW_DAYS and burn < LOW_BURN_THRESHOLD:
        flags.append("LOW_BURN_NEAR_END")

    return {
        "id": sub_id,
        "org": subaward["org"],
        "pi": subaward["pi"],
        "total": total,
        "invoiced": invoiced,
        "burn": burn,
        "remaining": remaining,
        "days_left": days_left,
        "flags": flags,
    }


def compute_all_statuses(register: dict, invoices: list[dict], today: datetime) -> list[dict]:
    return [compute_status(sid, sub, invoices, today) for sid, sub in register.items()]


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def build_report(statuses: list[dict], today: datetime) -> str:
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    lines: list[str] = []
    lines.append("# Subaward register (advisory, not a system of record)")
    lines.append("")
    lines.append(
        "> This report tracks subaward totals and invoices entered by a human. "
        "It does not verify performance or approve payment. A human in sponsored "
        "programs or grants accounting must review flags and make the final call."
    )
    lines.append("")
    lines.append(f"**Generated:** {now}")
    lines.append(f"**As of:** {today.strftime(DATE_FMT)}")
    lines.append(f"**Subawards:** {len(statuses)}")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Register")
    lines.append("")
    lines.append("| ID | Org | PI | Total | Invoiced | Burn | Remaining | Days left | Flags |")
    lines.append("|---|---|---|---|---|---|---|---|---|")
    for s in sorted(statuses, key=lambda r: r["id"]):
        flag_cell = ", ".join(s["flags"]) if s["flags"] else "none"
        lines.append(
            f"| {s['id']} | {s['org']} | {s['pi']} | {s['total']:.2f} | {s['invoiced']:.2f} | "
            f"{s['burn'] * 100:.1f}% | {s['remaining']:.2f} | {s['days_left']} | {flag_cell} |"
        )
    lines.append("")
    n_flagged = sum(1 for s in statuses if s["flags"])
    lines.append("---")
    lines.append("")
    if n_flagged:
        lines.append(f"**{n_flagged} of {len(statuses)} subaward(s) have at least one flag. Review before payment.**")
    else:
        lines.append("**No flags raised. Human review is still required before payment.**")
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Subaward and invoice tracking with contemporaneous records. Advisory only."
    )
    sub = ap.add_subparsers(dest="cmd", required=True)

    sp_add = sub.add_parser("add", help="Add a subaward to the register.")
    sp_add.add_argument("--id", required=True)
    sp_add.add_argument("--org", required=True)
    sp_add.add_argument("--pi", required=True)
    sp_add.add_argument("--total", required=True, type=float)
    sp_add.add_argument("--start", required=True, help="YYYY-MM-DD")
    sp_add.add_argument("--end", required=True, help="YYYY-MM-DD")
    sp_add.add_argument("--register", default=REGISTER_DEFAULT)

    sp_inv = sub.add_parser("invoice", help="Append an invoice against a subaward id.")
    sp_inv.add_argument("--id", required=True)
    sp_inv.add_argument("--amount", required=True, type=float)
    sp_inv.add_argument("--date", required=True, help="YYYY-MM-DD")
    sp_inv.add_argument("--register", default=REGISTER_DEFAULT)
    sp_inv.add_argument("--invoices", default=INVOICES_DEFAULT)

    sp_status = sub.add_parser("status", help="Print burn and flags for one or all subawards.")
    sp_status.add_argument("--id", default=None, help="Limit to one subaward id (default: all).")
    sp_status.add_argument("--register", default=REGISTER_DEFAULT)
    sp_status.add_argument("--invoices", default=INVOICES_DEFAULT)
    sp_status.add_argument("--today", default=None, help="YYYY-MM-DD; default: current UTC date.")

    sp_report = sub.add_parser("report", help="Write a Markdown report of all subawards.")
    sp_report.add_argument("--register", default=REGISTER_DEFAULT)
    sp_report.add_argument("--invoices", default=INVOICES_DEFAULT)
    sp_report.add_argument("--today", default=None, help="YYYY-MM-DD; default: current UTC date.")
    sp_report.add_argument("--out", default=None, help="Output path (default: stdout).")

    args = ap.parse_args(argv)

    if args.cmd == "add":
        _parse_date(args.start, "--start")
        _parse_date(args.end, "--end")
        _append_csv(args.register, REGISTER_HEADER, [args.id, args.org, args.pi, args.total, args.start, args.end])
        print(f"[subaward_register] added {args.id} to {args.register}")
        return 0

    if args.cmd == "invoice":
        register = load_register(args.register)
        if args.id not in register:
            print(f"[subaward_register] ERROR: unknown subaward id: {args.id}", file=sys.stderr)
            sys.exit(1)
        _parse_date(args.date, "--date")
        _append_csv(args.invoices, INVOICE_HEADER, [args.id, args.amount, args.date])
        print(f"[subaward_register] invoice of {args.amount} recorded for {args.id}")
        return 0

    # status / report both need the full picture
    register = load_register(args.register)
    invoices = load_invoices(args.invoices)
    today = _parse_date(args.today, "--today") if args.today else datetime.utcnow()

    if args.cmd == "status":
        if args.id is not None:
            if args.id not in register:
                print(f"[subaward_register] ERROR: unknown subaward id: {args.id}", file=sys.stderr)
                sys.exit(1)
            statuses = [compute_status(args.id, register[args.id], invoices, today)]
        else:
            statuses = compute_all_statuses(register, invoices, today)
        for s in statuses:
            flag_txt = ", ".join(s["flags"]) if s["flags"] else "none"
            print(
                f"{s['id']}: invoiced={s['invoiced']:.2f} total={s['total']:.2f} "
                f"burn={s['burn'] * 100:.1f}% remaining={s['remaining']:.2f} "
                f"days_left={s['days_left']} flags={flag_txt}"
            )
        return 0

    # report
    statuses = compute_all_statuses(register, invoices, today)
    report = build_report(statuses, today)
    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(report)
        print(f"[subaward_register] wrote {args.out}")
    else:
        sys.stdout.write(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
