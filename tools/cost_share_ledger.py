#!/usr/bin/env python3
"""cost_share_ledger -- cost-share (match) commitment and documentation tracking.

Tracks cost-share (match) commitments per award against documented
contributions, and flags gaps a human should look at: a shortfall between
committed and documented totals, contributions with no supporting document
reference, and third-party in-kind contributions that typically need a
letter of commitment from the contributing organization.

ADVISORY: totals, sources, and document references are INPUTS a human
enters. This tool does not verify that a "doc" field points to a real,
adequate document, does not confirm a letter of commitment exists, and is
not a system of record for institutional cost-share accounting. A human in
sponsored programs must review flags and make the final determination.

Commitments CSV rows: [award, source, type, committed]
  type is "cash" or "in-kind"

Contributions CSV rows: [award, date, source, amount, doc]
  doc is a reference to supporting documentation (a file name, receipt
  number, etc.); an empty doc field is flagged as undocumented match.

Subcommands:
  commit       -- append one commitment row
  contribute   -- append one contribution row
  status       -- print per-award committed vs documented totals and flags
  report       -- write a Markdown report for all awards

Flags (per award):
  SHORTFALL              -- documented contributions < committed total
  UNDOCUMENTED_MATCH      -- one or more contributions have an empty doc field
  IN_KIND_NEEDS_LETTER    -- a contribution has type in-kind (from the
                             matching commitment row) and its source is not
                             the institution named by --institution

Exit codes:
  0  -- command completed
  1  -- unknown award referenced by status --award
  2  -- ledger file missing or unreadable, or bad numeric input

Usage:
  python3 tools/cost_share_ledger.py commit --award NSF-123 --source "State U" --type cash --committed 50000
  python3 tools/cost_share_ledger.py contribute --award NSF-123 --date 2026-03-01 --source "State U" --amount 10000 --doc receipt_001.pdf
  python3 tools/cost_share_ledger.py status --award NSF-123 --institution "State U"
  python3 tools/cost_share_ledger.py report --out report.md --institution "State U"
"""
from __future__ import annotations
import argparse
import csv
import os
import sys
from datetime import datetime

# UTF-8 stdout guard
import cambium_io  # noqa: F401

COMMITMENTS_DEFAULT = os.path.join("governance", "COST_SHARE_COMMITMENTS.csv")
CONTRIBUTIONS_DEFAULT = os.path.join("governance", "COST_SHARE_CONTRIBUTIONS.csv")
COMMITMENT_HEADER = ["award", "source", "type", "committed"]
CONTRIBUTION_HEADER = ["award", "date", "source", "amount", "doc"]
VALID_TYPES = ("cash", "in-kind")


# ---------------------------------------------------------------------------
# CSV IO helpers
# ---------------------------------------------------------------------------

def _read_csv(path: str) -> list[dict]:
    if not os.path.exists(path):
        return []
    try:
        with open(path, newline="", encoding="utf-8") as fh:
            return list(csv.DictReader(fh))
    except OSError as exc:
        print(f"[cost_share_ledger] ERROR: cannot read {path}\n  {exc}", file=sys.stderr)
        sys.exit(2)


def _append_csv(path: str, header: list[str], row: list) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
    is_new = not os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        if is_new:
            w.writerow(header)
        w.writerow(row)


def load_commitments(path: str) -> list[dict]:
    rows = _read_csv(path)
    return [
        {"award": r["award"], "source": r["source"], "type": r["type"], "committed": float(r["committed"])}
        for r in rows
    ]


def load_contributions(path: str) -> list[dict]:
    rows = _read_csv(path)
    return [
        {"award": r["award"], "date": r["date"], "source": r["source"], "amount": float(r["amount"]), "doc": r.get("doc", "")}
        for r in rows
    ]


# ---------------------------------------------------------------------------
# Status computation
# ---------------------------------------------------------------------------

def awards_in(commitments: list[dict], contributions: list[dict]) -> list[str]:
    """All award ids seen in either commitments or contributions, sorted."""
    ids = {c["award"] for c in commitments} | {c["award"] for c in contributions}
    return sorted(ids)


def compute_status(award: str, commitments: list[dict], contributions: list[dict], institution: str) -> dict:
    """Compute committed vs documented totals and flags for one award."""
    award_commitments = [c for c in commitments if c["award"] == award]
    award_contributions = [c for c in contributions if c["award"] == award]

    committed_total = sum(c["committed"] for c in award_commitments)
    documented_total = sum(c["amount"] for c in award_contributions)

    flags = []
    if documented_total < committed_total:
        flags.append("SHORTFALL")

    undocumented = [c for c in award_contributions if not c["doc"].strip()]
    if undocumented:
        flags.append("UNDOCUMENTED_MATCH")

    # in-kind sources committed by parties other than the institution need a letter.
    in_kind_sources = {c["source"] for c in award_commitments if c["type"] == "in-kind"}
    needs_letter = [
        c for c in award_contributions
        if c["source"] in in_kind_sources and c["source"] != institution
    ]
    if needs_letter:
        flags.append("IN_KIND_NEEDS_LETTER")

    return {
        "award": award,
        "committed": committed_total,
        "documented": documented_total,
        "shortfall": committed_total - documented_total,
        "undocumented_count": len(undocumented),
        "needs_letter_count": len(needs_letter),
        "flags": flags,
    }


def compute_all_statuses(commitments: list[dict], contributions: list[dict], institution: str) -> list[dict]:
    return [compute_status(a, commitments, contributions, institution) for a in awards_in(commitments, contributions)]


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def build_report(statuses: list[dict], institution: str) -> str:
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    lines: list[str] = []
    lines.append("# Cost-share ledger (advisory, not a system of record)")
    lines.append("")
    lines.append(
        "> Totals, sources, and document references are entered by a human. This tool "
        "does not verify documentation adequacy or confirm letters of commitment exist. "
        "A human in sponsored programs must review flags and make the final determination."
    )
    lines.append("")
    lines.append(f"**Generated:** {now}")
    lines.append(f"**Institution (for in-kind letter check):** {institution}")
    lines.append(f"**Awards:** {len(statuses)}")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Ledger")
    lines.append("")
    lines.append("| Award | Committed | Documented | Shortfall | Flags |")
    lines.append("|---|---|---|---|---|")
    for s in statuses:
        flag_cell = ", ".join(s["flags"]) if s["flags"] else "none"
        lines.append(
            f"| {s['award']} | {s['committed']:.2f} | {s['documented']:.2f} | "
            f"{max(s['shortfall'], 0):.2f} | {flag_cell} |"
        )
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Flags detail")
    lines.append("")
    any_flags = False
    for s in statuses:
        if not s["flags"]:
            continue
        any_flags = True
        parts = []
        if "SHORTFALL" in s["flags"]:
            parts.append(f"shortfall of {s['shortfall']:.2f}")
        if "UNDOCUMENTED_MATCH" in s["flags"]:
            parts.append(f"{s['undocumented_count']} contribution(s) with no doc reference")
        if "IN_KIND_NEEDS_LETTER" in s["flags"]:
            parts.append(f"{s['needs_letter_count']} third-party in-kind contribution(s) may need a letter")
        lines.append(f"- **{s['award']}**: " + "; ".join(parts))
    if not any_flags:
        lines.append("- No flags raised across any award.")
    lines.append("")
    lines.append(
        "**This ledger is advisory. A human in sponsored programs must review flags and "
        "confirm cost-share documentation before close-out or audit.**"
    )
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Cost-share (match) commitment and documentation tracking. Advisory only."
    )
    sub = ap.add_subparsers(dest="cmd", required=True)

    sp_commit = sub.add_parser("commit", help="Add a cost-share commitment.")
    sp_commit.add_argument("--award", required=True)
    sp_commit.add_argument("--source", required=True)
    sp_commit.add_argument("--type", required=True, choices=VALID_TYPES)
    sp_commit.add_argument("--committed", required=True, type=float)
    sp_commit.add_argument("--commitments", default=COMMITMENTS_DEFAULT)

    sp_contrib = sub.add_parser("contribute", help="Record a documented contribution.")
    sp_contrib.add_argument("--award", required=True)
    sp_contrib.add_argument("--date", required=True, help="YYYY-MM-DD")
    sp_contrib.add_argument("--source", required=True)
    sp_contrib.add_argument("--amount", required=True, type=float)
    sp_contrib.add_argument("--doc", default="", help="Reference to supporting documentation (may be omitted).")
    sp_contrib.add_argument("--contributions", default=CONTRIBUTIONS_DEFAULT)

    sp_status = sub.add_parser("status", help="Print committed vs documented totals and flags.")
    sp_status.add_argument("--award", default=None, help="Limit to one award (default: all).")
    sp_status.add_argument("--commitments", default=COMMITMENTS_DEFAULT)
    sp_status.add_argument("--contributions", default=CONTRIBUTIONS_DEFAULT)
    sp_status.add_argument("--institution", required=True, help="Institution name for the in-kind letter check.")

    sp_report = sub.add_parser("report", help="Write a Markdown report for all awards.")
    sp_report.add_argument("--commitments", default=COMMITMENTS_DEFAULT)
    sp_report.add_argument("--contributions", default=CONTRIBUTIONS_DEFAULT)
    sp_report.add_argument("--institution", required=True, help="Institution name for the in-kind letter check.")
    sp_report.add_argument("--out", default=None, help="Output path (default: stdout).")

    args = ap.parse_args(argv)

    if args.cmd == "commit":
        _append_csv(args.commitments, COMMITMENT_HEADER, [args.award, args.source, args.type, args.committed])
        print(f"[cost_share_ledger] committed {args.committed} ({args.type}) for {args.award} from {args.source}")
        return 0

    if args.cmd == "contribute":
        _append_csv(args.contributions, CONTRIBUTION_HEADER, [args.award, args.date, args.source, args.amount, args.doc])
        print(f"[cost_share_ledger] contribution of {args.amount} recorded for {args.award}")
        return 0

    commitments = load_commitments(args.commitments)
    contributions = load_contributions(args.contributions)

    if args.cmd == "status":
        known_awards = awards_in(commitments, contributions)
        if args.award is not None:
            if args.award not in known_awards:
                print(f"[cost_share_ledger] ERROR: unknown award: {args.award}", file=sys.stderr)
                sys.exit(1)
            statuses = [compute_status(args.award, commitments, contributions, args.institution)]
        else:
            statuses = compute_all_statuses(commitments, contributions, args.institution)
        for s in statuses:
            flag_txt = ", ".join(s["flags"]) if s["flags"] else "none"
            print(
                f"{s['award']}: committed={s['committed']:.2f} documented={s['documented']:.2f} "
                f"shortfall={max(s['shortfall'], 0):.2f} flags={flag_txt}"
            )
        return 0

    # report
    statuses = compute_all_statuses(commitments, contributions, args.institution)
    report = build_report(statuses, args.institution)
    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(report)
        print(f"[cost_share_ledger] wrote {args.out}")
    else:
        sys.stdout.write(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
