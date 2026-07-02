#!/usr/bin/env python3
"""sod_report - separation-of-duties attestation over the gate approval ledger.

Purpose:
  Parse the '## Approvals log' table in governance/GATES.md (5 cells per row:
  Gate | Date | Approver | Decision | Notes) and report, in a form an auditor
  can read: approvals per approver, whether every approval traces to a single
  person, G3 or G6 rows that lack evidence of a second human (ROLES require the
  Director plus a second human for those gates), rows with an empty approver,
  and malformed rows.

Usage:
  python3 tools/sod_report.py [--gates PATH] [--strict]

Honest limits:
  ADVISORY. This reads the ledger as written; it cannot detect approvals made
  outside the ledger, shared accounts, or a second human who reviewed but was
  never recorded. Second-party detection is textual (names joined by +, &, and,
  or a co-sign mention in Notes) and can miss or over-match. Not a certification.

Exit: 0 normally (advisory); 1 on invalid input (missing file or missing
Approvals log section) or, with --strict, if any flag is raised.
"""
import argparse
import collections
import os
import re
import sys

import cambium_io  # noqa: F401

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_GATES = os.path.join(REPO_ROOT, "governance", "GATES.md")

DUAL_GATES = ("G3", "G6")  # per ROLES: Director plus a second human
SECOND_PARTY_RE = re.compile(
    r"(\+|&|;|,| and |co-sign|cosign|co-author|coauthor|second (?:human|approver|review)|"
    r"countersign|witness)", re.IGNORECASE)


def _cells(line):
    parts = line.split("|")
    if parts and parts[0].strip() == "":
        parts = parts[1:]
    if parts and parts[-1].strip() == "":
        parts = parts[:-1]
    return [p.strip() for p in parts]


def _is_separator(cells):
    return bool(cells) and all(c and set(c) <= set("-: ") for c in cells)


def _is_header(cells):
    low = [c.lower() for c in cells]
    return "gate" in low[:1] and "approver" in low


def parse_approvals(text):
    """Return (rows, malformed). rows are dicts with gate/date/approver/decision/notes/line_no.

    malformed are (line_no, raw_line) for pipe rows inside the Approvals log
    section that do not have exactly 5 cells. Raises ValueError if the
    '## Approvals log' section is missing.
    """
    lines = text.splitlines()
    start = None
    for i, ln in enumerate(lines):
        if ln.strip().lower().startswith("## approvals log"):
            start = i + 1
            break
    if start is None:
        raise ValueError("no '## Approvals log' section found")

    rows, malformed = [], []
    for i in range(start, len(lines)):
        ln = lines[i]
        stripped = ln.strip()
        if stripped.startswith("## "):
            break
        if not stripped.startswith("|"):
            continue
        cells = _cells(stripped)
        if _is_separator(cells) or _is_header(cells):
            continue
        if len(cells) != 5:
            malformed.append((i + 1, stripped))
            continue
        rows.append({"gate": cells[0], "date": cells[1], "approver": cells[2],
                     "decision": cells[3], "notes": cells[4], "line_no": i + 1})
    return rows, malformed


def has_second_party(row):
    """Textual evidence of a second human in Approver or Notes."""
    return bool(SECOND_PARTY_RE.search(row["approver"]) or
                SECOND_PARTY_RE.search(row["notes"]))


def analyze(rows, malformed):
    per_approver = collections.Counter()
    empty_approver, dual_flags = [], []
    for r in rows:
        name = r["approver"] or "(empty)"
        per_approver[name] += 1
        if not r["approver"]:
            empty_approver.append(r)
        gate_id = r["gate"].upper().split()[0] if r["gate"] else ""
        if gate_id in DUAL_GATES and not has_second_party(r):
            dual_flags.append(r)
    named = [a for a in per_approver if a != "(empty)"]
    flags = []
    for r in dual_flags:
        flags.append("ADVISORY: %s row (line %d, %s) shows no evidence of a second "
                     "human in Approver or Notes; ROLES require the Director plus a "
                     "second human for %s." % (r["gate"], r["line_no"], r["date"], r["gate"]))
    for r in empty_approver:
        flags.append("FLAG: row at line %d (%s, %s) has an EMPTY approver; an empty "
                     "approver means NOT approved." % (r["line_no"], r["gate"], r["date"]))
    for line_no, raw in malformed:
        flags.append("FLAG: malformed row at line %d (expected 5 cells): %s"
                     % (line_no, raw[:100]))
    return {"per_approver": per_approver, "named_approvers": named,
            "dual_flags": dual_flags, "empty_approver": empty_approver,
            "malformed": malformed, "flags": flags}


def render(path, rows, result):
    out = []
    out.append("# Separation-of-duties attestation (advisory)")
    out.append("")
    out.append("Ledger: %s" % path)
    out.append("Rows parsed: %d well-formed, %d malformed"
               % (len(rows), len(result["malformed"])))
    out.append("")
    out.append("## Approvals per approver")
    out.append("")
    out.append("| Approver | Approvals |")
    out.append("|---|---|")
    for name, n in result["per_approver"].most_common():
        out.append("| %s | %d |" % (name, n))
    if not result["per_approver"]:
        out.append("| (no rows) | 0 |")
    out.append("")
    out.append("## Concentration")
    out.append("")
    named = result["named_approvers"]
    if len(named) == 1 and rows:
        out.append("OBSERVATION: every recorded approval (%d row(s)) traces to a single "
                   "person: %s. Separation of duties cannot be demonstrated from this "
                   "ledger alone." % (len(rows), named[0]))
    elif rows:
        out.append("%d distinct named approver(s) appear in the ledger." % len(named))
    else:
        out.append("No approval rows recorded yet.")
    out.append("")
    out.append("## Findings")
    out.append("")
    if result["flags"]:
        for f in result["flags"]:
            out.append("- " + f)
    else:
        out.append("- No flags: no empty approvers, no malformed rows, and no "
                   "G3/G6 row lacking second-party evidence.")
    out.append("")
    out.append("---")
    out.append("ADVISORY attestation assembled from the ledger as written. It cannot "
               "detect approvals made outside the ledger or an unrecorded second "
               "reviewer, and second-party detection is textual. Not a certification.")
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Separation-of-duties attestation over the GATES.md approvals log.")
    ap.add_argument("--gates", default=DEFAULT_GATES,
                    help="path to GATES.md (default: governance/GATES.md)")
    ap.add_argument("--strict", action="store_true", help="exit 1 if any flag is raised")
    a = ap.parse_args(argv)

    if not os.path.isfile(a.gates):
        print("[sod_report] ERROR: gates ledger not found: %s" % a.gates)
        return 1
    text = open(a.gates, encoding="utf-8").read()
    try:
        rows, malformed = parse_approvals(text)
    except ValueError as e:
        print("[sod_report] ERROR: %s in %s" % (e, a.gates))
        return 1
    result = analyze(rows, malformed)
    print(render(a.gates, rows, result))
    if a.strict and result["flags"]:
        print("\n[sod_report] STRICT: %d flag(s) raised; exit 1." % len(result["flags"]))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
