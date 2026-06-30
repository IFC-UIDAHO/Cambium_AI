#!/usr/bin/env python3
"""ai_disclosure -- assemble an AI-use disclosure and audit summary for a research deliverable.

Addresses newly required AI-use disclosure policies (e.g. NIH NOT-OD-25-132). Documents WHAT
AI did and that a HUMAN signed off. Does NOT assert compliance or serve as a legal certification.

Reads from data_home():
  governance/GATES.md           -- gate decisions and approvers
  governance/audit_trail.jsonl  -- turn-level audit records (optional)
  governance/CONTRIBUTION_LEDGER.csv -- contribution records (optional)
  agent_outputs/*.md            -- which agents ran (optional)
  agent_cards.json              -- agent-to-model mapping (optional)

Output: a Markdown disclosure with five sections:
  (a) Summary
  (b) AI systems and models used
  (c) Human oversight: gates, approvers, dates
  (d) Evidence and audit trail
  (e) Honest disclaimer

Usage:
  python3 tools/ai_disclosure.py [--root <path>] [--out <path>] [--title "<deliverable>"]

The --root flag overrides data_home() (useful in tests and CI).
"""
from __future__ import annotations
import argparse
import csv
import json
import os
import re
import sys
from datetime import datetime

# UTF-8 stdout guard -- must happen before any print
import cambium_io  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ---------------------------------------------------------------------------
# Source readers -- all return gracefully when the file is absent
# ---------------------------------------------------------------------------

def _read_gates(root: str) -> list[dict]:
    """Parse gate rows from governance/GATES.md.

    Looks for a Markdown table with columns: Gate, Decision, Approver role, Approved by (name), Date.
    Returns a list of dicts; returns [] if the file is absent or has no parseable table rows.
    """
    path = os.path.join(root, "governance", "GATES.md")
    if not os.path.exists(path):
        return []
    gates = []
    header_seen = False
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line.startswith("|"):
                continue
            cells = [c.strip() for c in line.strip("|").split("|")]
            if not header_seen:
                # Detect the header row
                lower = [c.lower() for c in cells]
                if "gate" in lower and ("approved by" in " ".join(lower) or "approver" in " ".join(lower)):
                    header_seen = True
                continue
            # Skip the separator row (---|---|...)
            if all(re.match(r"^-+$", c.replace(" ", "")) for c in cells if c):
                continue
            if len(cells) >= 5:
                gates.append({
                    "gate": cells[0],
                    "decision": cells[1],
                    "approver_role": cells[2],
                    "approved_by": cells[3],
                    "date": cells[4],
                    "notes": cells[5] if len(cells) > 5 else "",
                })
    return gates


def _read_audit_jsonl(root: str) -> list[dict]:
    """Read governance/audit_trail.jsonl. Returns [] if absent."""
    path = os.path.join(root, "governance", "audit_trail.jsonl")
    if not os.path.exists(path):
        return []
    records = []
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return records


def _read_contribution_ledger(root: str) -> list[dict]:
    """Read governance/CONTRIBUTION_LEDGER.csv. Returns [] if absent."""
    path = os.path.join(root, "governance", "CONTRIBUTION_LEDGER.csv")
    if not os.path.exists(path):
        return []
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            return list(csv.DictReader(fh))
    except Exception:
        return []


def _read_agent_outputs(root: str) -> list[str]:
    """List .md filenames (basenames) in agent_outputs/. Returns [] if absent."""
    dirpath = os.path.join(root, "agent_outputs")
    if not os.path.isdir(dirpath):
        return []
    return sorted(
        f for f in os.listdir(dirpath)
        if f.endswith(".md") and not f.startswith("ai_use_disclosure")
    )


def _read_agent_cards(root: str) -> dict:
    """Read agent_cards.json for agent-to-model mapping. Returns {} if absent."""
    path = os.path.join(root, "agent_cards.json")
    if not os.path.exists(path):
        return {}
    try:
        return json.loads(open(path, encoding="utf-8").read())
    except Exception:
        return {}


# ---------------------------------------------------------------------------
# Model tier mapper -- simple heuristic from agent name / card info
# ---------------------------------------------------------------------------

_ROLE_TO_PURPOSE = {
    "rfp": "funding-call reading and extraction",
    "idea": "idea generation and drafting",
    "budget": "budget drafting and cost review",
    "grant": "grant writing and proposal drafting",
    "verif": "evidence verification and reproduction",
    "rigor": "logic and rigor review",
    "method": "methodology review",
    "domain": "domain knowledge review",
    "referee": "peer-style scoring",
    "data": "data management and stewardship",
    "integ": "integrity and overclaim review",
    "report": "reporting and narrative drafting",
    "learning": "learning delivery",
    "provenance": "provenance and reproducibility tracking",
    "compliance": "compliance flagging (advisory)",
}


def _infer_purpose(agent_name: str) -> str:
    name_lower = agent_name.lower()
    for key, purpose in _ROLE_TO_PURPOSE.items():
        if key in name_lower:
            return purpose
    return "AI-assisted research support"


# ---------------------------------------------------------------------------
# Disclosure builder
# ---------------------------------------------------------------------------

def build_disclosure(root: str, title: str) -> str:
    """Assemble the Markdown disclosure. Pure function -- no side effects."""
    now = datetime.utcnow().strftime("%Y-%m-%d")

    gates = _read_gates(root)
    audit_records = _read_audit_jsonl(root)
    contributions = _read_contribution_ledger(root)
    agent_files = _read_agent_outputs(root)
    agent_cards = _read_agent_cards(root)

    # Derive agent names from output files and/or agent_cards
    agent_names: list[str] = []
    if agent_cards:
        # agent_cards may be a list of dicts with "name" or a dict keyed by name
        if isinstance(agent_cards, list):
            agent_names = [a.get("name", "") for a in agent_cards if a.get("name")]
        elif isinstance(agent_cards, dict):
            agent_names = list(agent_cards.keys())
    if not agent_names and agent_files:
        # Derive agent names from output filenames (e.g. "lab-methods_output.md")
        agent_names = [os.path.splitext(f)[0] for f in agent_files]

    # Approvers from gate records
    approvers = [g["approved_by"] for g in gates if g.get("approved_by")]

    # Audit trail presence
    has_audit = bool(audit_records) or bool(contributions)
    audit_source = []
    if audit_records:
        audit_source.append(f"audit_trail.jsonl ({len(audit_records)} record(s))")
    if contributions:
        audit_source.append(f"CONTRIBUTION_LEDGER.csv ({len(contributions)} row(s))")

    lines: list[str] = []

    # Title
    lines.append(f"# AI-Use Disclosure")
    lines.append(f"")
    lines.append(f"**Deliverable:** {title}")
    lines.append(f"**Generated:** {now} (UTC) by Cambium `tools/ai_disclosure.py`")
    lines.append(f"")

    # Section a: Summary
    lines.append("---")
    lines.append("")
    lines.append("## A. Summary")
    lines.append("")
    lines.append(
        f"This deliverable was produced with AI assistance from Cambium "
        f"(a responsible-AI research institute). "
        f"AI agents contributed to phases including information gathering, drafting, and review. "
        f"Human oversight was exercised at every gate: a named human reviewed AI outputs, "
        f"recorded a decision, and took responsibility for the work before it advanced."
    )
    if gates:
        lines.append(
            f"A total of {len(gates)} named gate decision(s) are recorded in governance/GATES.md."
        )
    lines.append("")

    # Section b: AI systems and models
    lines.append("---")
    lines.append("")
    lines.append("## B. AI Systems and Models Used")
    lines.append("")
    lines.append(
        "Cambium orchestrates named AI sub-agents (Claude-based) that each handle one part of the work. "
        "No single agent authors the whole deliverable."
    )
    lines.append("")
    if agent_names:
        lines.append("| Agent | Inferred purpose |")
        lines.append("|---|---|")
        for name in sorted(set(agent_names)):
            purpose = _infer_purpose(name)
            # check agent_cards for model info
            model_info = ""
            _cards = agent_cards.get("agents", []) if isinstance(agent_cards, dict) else (agent_cards or [])
            for _c in _cards:
                if isinstance(_c, dict) and _c.get("name") == name:
                    model_info = _c.get("model", "")
                    break
            if model_info:
                lines.append(f"| {name} | {purpose} (model: {model_info}) |")
            else:
                lines.append(f"| {name} | {purpose} |")
        lines.append("")
    else:
        lines.append(
            "_No agent output files or agent_cards.json found in the root. "
            "List the agents and their roles here manually if needed._"
        )
        lines.append("")

    # Section c: Human oversight
    lines.append("---")
    lines.append("")
    lines.append("## C. Human Oversight: Gate Decisions")
    lines.append("")
    if gates:
        lines.append(
            "The following human gate decisions are on record in governance/GATES.md. "
            "At each gate the named approver reviewed the AI output and recorded a decision. "
            "No phase advanced without that sign-off."
        )
        lines.append("")
        lines.append("| Gate | Decision (summary) | Approver role | Approved by | Date |")
        lines.append("|---|---|---|---|---|")
        for g in gates:
            decision_short = (g["decision"][:80] + "...") if len(g["decision"]) > 80 else g["decision"]
            lines.append(
                f"| {g['gate']} | {decision_short} | {g['approver_role']} "
                f"| {g['approved_by']} | {g['date']} |"
            )
        lines.append("")
    else:
        lines.append(
            "_governance/GATES.md was not found or contained no parseable gate table. "
            "Add the gate record here if this deliverable was approved._"
        )
        lines.append("")

    # Section d: Evidence and audit trail
    lines.append("---")
    lines.append("")
    lines.append("## D. Evidence and Audit Trail")
    lines.append("")
    lines.append(
        "Cambium's evidence contract requires every factual claim to carry a tier: "
        "Proved, Code-verified, Asserted, or Open. "
        "A CI evidence check fails if a claim reaches past its tier."
    )
    lines.append("")
    if has_audit:
        lines.append(
            f"An audit trail is present: {'; '.join(audit_source)}. "
            "This records the turn-by-turn AI contributions so a reviewer can trace what the AI did."
        )
    else:
        lines.append(
            "_No audit_trail.jsonl or CONTRIBUTION_LEDGER.csv was found. "
            "If Cambium's audit_log tool was run, the record will appear here automatically._"
        )
    lines.append("")

    # Section e: Honest disclaimer
    lines.append("---")
    lines.append("")
    lines.append("## E. Disclaimer")
    lines.append("")
    lines.append(
        "**This document is a disclosure of AI use in producing this deliverable. "
        "It is NOT a certification of regulatory compliance, a legal determination, "
        "or a guarantee that all requirements of any specific funder policy have been met. "
        "The named human approver(s) above are responsible for the content of this deliverable "
        "and for ensuring it meets the requirements of the target venue or sponsor. "
        "Cambium is an advisory tool; it does not replace human judgment, legal review, "
        "or institutional sponsored-programs oversight.**"
    )
    lines.append("")
    if approvers:
        lines.append(f"Named responsible human(s): {', '.join(sorted(set(approvers)))}")
        lines.append("")
    lines.append(
        "_AI is not an author of this work (per ICMJE/COPE policy). "
        "A named human takes responsibility for all content._"
    )
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Assemble an AI-use disclosure for a research deliverable."
    )
    ap.add_argument(
        "--root",
        default=None,
        help="Data root (overrides data_home()). Useful for tests.",
    )
    ap.add_argument(
        "--out",
        default=None,
        help="Output path (default: <root>/agent_outputs/ai_use_disclosure.md).",
    )
    ap.add_argument(
        "--title",
        default="(untitled deliverable)",
        help="Human-readable name of the deliverable.",
    )
    args = ap.parse_args(argv)

    root = args.root if args.root else cambium_io.data_home()
    out = args.out if args.out else os.path.join(root, "agent_outputs", "ai_use_disclosure.md")

    disclosure = build_disclosure(root, args.title)

    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(disclosure)

    print(f"[ai_disclosure] wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
