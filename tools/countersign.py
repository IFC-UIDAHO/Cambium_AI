#!/usr/bin/env python3
"""countersign -- second-human rule for release gates (separation of duties, recorded).

G3 (finalize & submit proposal) and G6 (publish / external send) require the Director
PLUS a second human per GATES.md. This tool records that second signature and checks
the approvals log for compliance: every G3/G6 row needs a countersign by someone whose
NAME differs from the gate's approver (substring-matched case-insensitively, so
"Director (Jaslam)" and "Jaslam" are treated as the SAME person and rejected).

ADVISORY: this enforces separation-of-duties RECORDING. It cannot verify identity --
anyone typing a different string is accepted. It is a paper trail, not an identity check.

Usage:
  python3 tools/countersign.py record --gate G3 --run RUN_ID --name "A. Reyes" --role "Co-PI" [--ledger PATH]
  python3 tools/countersign.py check [--ledger PATH] [--gates-md PATH] [--strict]

Exit: record -> 0 on success, 1 on bad args.
      check   -> 0 always unless --strict and a G3/G6 lacks a valid countersign (then 1).
"""
from __future__ import annotations
import argparse
import csv
import os
import re
import sys
from datetime import date

import cambium_io  # noqa: F401 -- reconfigures stdout/stderr to UTF-8 on Windows

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_LEDGER = os.path.join(ROOT, "governance", "COUNTERSIGNS.csv")
DEFAULT_GATES_MD = os.path.join(ROOT, "governance", "GATES.md")
DUAL_HUMAN_GATES = {"G3", "G6"}
FIELDS = ["gate", "run", "name", "role", "date"]


def _same_person(a: str, b: str) -> bool:
    """Substring-match, case-insensitive: 'Director (Jaslam)' and 'Jaslam' are the same person."""
    a, b = (a or "").strip().lower(), (b or "").strip().lower()
    if not a or not b:
        return False
    return a in b or b in a


def record(ledger: str, gate: str, run: str, name: str, role: str, iso_date: str = None) -> dict:
    row = {
        "gate": gate,
        "run": run,
        "name": name,
        "role": role,
        "date": iso_date or date.today().isoformat(),
    }
    os.makedirs(os.path.dirname(ledger), exist_ok=True)
    is_new = not os.path.exists(ledger)
    with open(ledger, "a", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        if is_new:
            w.writeheader()
        w.writerow(row)
    return row


def load_countersigns(ledger: str) -> list:
    if not os.path.exists(ledger):
        return []
    with open(ledger, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def parse_gates_approvals(gates_md: str) -> tuple:
    """Parse the '## Approvals log' 5-cell rows. Returns (rows, warnings).

    Each row: {"gate": str, "date": str, "approver": str, "decision": str, "notes": str}.
    A malformed row (not exactly 5 cells) is skipped with a warning, not a crash.
    """
    if not os.path.exists(gates_md):
        return [], ["GATES.md not found at %s" % gates_md]
    text = open(gates_md, encoding="utf-8", errors="replace").read()
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.strip().lower().startswith("## approvals log"):
            start = i + 1
            break
    if start is None:
        return [], ["'## Approvals log' section missing in GATES.md"]

    rows, warnings = [], []
    header_skipped = False
    for lineno, line in enumerate(lines[start:], start + 1):
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if all(re.match(r"^[-:]+$", c) for c in cells if c):
            continue  # markdown separator row
        if len(cells) != 5:
            warnings.append("GATES.md:%d has %d cell(s) (want 5): fused or truncated row, skipped" % (lineno, len(cells)))
            continue
        if not header_skipped and cells[0].lower() == "gate":
            header_skipped = True
            continue
        rows.append({"gate": cells[0], "date": cells[1], "approver": cells[2], "decision": cells[3], "notes": cells[4]})
    return rows, warnings


def check(ledger: str, gates_md: str) -> dict:
    """Return {"rows": [...], "warnings": [...], "ok": bool} for every G3/G6 approvals row."""
    gate_rows, warnings = parse_gates_approvals(gates_md)
    countersigns = load_countersigns(ledger)

    report_rows = []
    all_ok = True
    for g in gate_rows:
        gate_id = g["gate"]
        if gate_id not in DUAL_HUMAN_GATES:
            continue
        approver = g["approver"]
        matches = [c for c in countersigns if c.get("gate") == gate_id and not _same_person(c.get("name", ""), approver)]
        valid = bool(matches)
        if not valid:
            all_ok = False
        report_rows.append({
            "gate": gate_id,
            "date": g["date"],
            "approver": approver,
            "countersigned_by": matches[0]["name"] if matches else "-",
            "valid": valid,
        })
    return {"rows": report_rows, "warnings": warnings, "ok": all_ok}


def render_report(result: dict) -> str:
    lines = ["# Countersign check (separation of duties, recording only)", ""]
    lines.append("> ADVISORY: verifies a differently-named record exists. It cannot verify identity.")
    lines.append("")
    if result["warnings"]:
        lines.append("## Warnings")
        for w in result["warnings"]:
            lines.append("- %s" % w)
        lines.append("")
    lines.append("| Gate | Date | Approver | Countersigned by | Valid |")
    lines.append("|---|---|---|---|---|")
    for r in result["rows"]:
        lines.append("| %s | %s | %s | %s | %s |" % (r["gate"], r["date"], r["approver"], r["countersigned_by"], "yes" if r["valid"] else "NO"))
    if not result["rows"]:
        lines.append("| - | - | - | - | - |")
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd")

    pr = sub.add_parser("record")
    pr.add_argument("--gate", required=True)
    pr.add_argument("--run", required=True)
    pr.add_argument("--name", required=True)
    pr.add_argument("--role", required=True)
    pr.add_argument("--ledger", default=DEFAULT_LEDGER)

    pc = sub.add_parser("check")
    pc.add_argument("--ledger", default=DEFAULT_LEDGER)
    pc.add_argument("--gates-md", default=DEFAULT_GATES_MD)
    pc.add_argument("--strict", action="store_true")

    args = ap.parse_args(argv)

    if args.cmd == "record":
        row = record(args.ledger, args.gate, args.run, args.name, args.role)
        print("[countersign] recorded: %s / %s / %s (%s)" % (row["gate"], row["run"], row["name"], row["role"]))
        return 0

    if args.cmd == "check":
        result = check(args.ledger, args.gates_md)
        print(render_report(result))
        if args.strict and not result["ok"]:
            return 1
        return 0

    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
