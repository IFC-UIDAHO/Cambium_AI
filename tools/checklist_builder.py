#!/usr/bin/env python3
"""checklist_builder -- turn a structured solicitation rules file into a
submission checklist a human works through.

Takes the same rules shape validated by tools/rules_handoff.py (the shape
tools/budget_review.py checks against) and produces a plain Markdown
checklist grouped by section. This is a preparation aid: it assembles the
rules into checkable items. It is not a compliance determination and does
not replace a human review of the actual solicitation and proposal.

Input:
  --rules rules.json  -- required_budget_sections, disallowed_categories,
                          cost_share_required, and optionally fa_rate_cap,
                          total_cost_ceiling, period_months_max,
                          required_documents (list of strings), deadline (string)

Output: a Markdown checklist with [ ] checkboxes grouped into:
  - Required documents
  - Required budget sections
  - Limits to respect (F&A cap, cost ceiling, period)
  - Cost-share
  - Deadline

Exit codes:
  0  -- checklist built
  2  -- input file missing or unreadable

Usage:
  python3 tools/checklist_builder.py --rules rules.json
  python3 tools/checklist_builder.py --rules rules.json --out checklist.md
"""
from __future__ import annotations
import argparse
import json
import os
import sys
from datetime import datetime

# UTF-8 stdout guard
import cambium_io  # noqa: F401


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------

def _load_json(path: str, label: str) -> dict:
    if not os.path.exists(path):
        print(f"[checklist_builder] ERROR: {label} file not found: {path}", file=sys.stderr)
        sys.exit(2)
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except json.JSONDecodeError as exc:
        print(f"[checklist_builder] ERROR: {label} file is not valid JSON: {path}\n  {exc}", file=sys.stderr)
        sys.exit(2)
    except OSError as exc:
        print(f"[checklist_builder] ERROR: cannot read {label} file: {path}\n  {exc}", file=sys.stderr)
        sys.exit(2)


# ---------------------------------------------------------------------------
# Section builders -- each returns a list of Markdown lines (may be empty)
# ---------------------------------------------------------------------------

def build_documents_section(rules: dict) -> list[str]:
    documents = rules.get("required_documents", [])
    lines = ["## Required documents", ""]
    if not documents:
        lines.append("- No required documents were listed in the rules file. Confirm this against the solicitation directly.")
        lines.append("")
        return lines
    for doc in documents:
        lines.append(f"- [ ] Confirm that '{doc}' is prepared and included in the submission package.")
    lines.append("")
    return lines


def build_budget_sections_section(rules: dict) -> list[str]:
    sections = rules.get("required_budget_sections", [])
    lines = ["## Required budget sections", ""]
    if not sections:
        lines.append("- No required budget sections were listed in the rules file. Confirm this against the solicitation directly.")
        lines.append("")
        return lines
    for section in sections:
        lines.append(f"- [ ] Confirm the budget includes the '{section}' section.")
    lines.append("")
    return lines


def build_limits_section(rules: dict) -> list[str]:
    fa_cap = rules.get("fa_rate_cap")
    ceiling = rules.get("total_cost_ceiling")
    period_max = rules.get("period_months_max")
    disallowed = rules.get("disallowed_categories", [])

    lines = ["## Limits to respect", ""]
    any_limit = False

    if fa_cap is not None:
        any_limit = True
        lines.append(f"- [ ] Confirm the proposed F&A rate does not exceed the cap of {fa_cap}.")
    if ceiling is not None:
        any_limit = True
        lines.append(f"- [ ] Confirm the total proposed cost does not exceed the ceiling of {ceiling}.")
    if period_max is not None:
        any_limit = True
        lines.append(f"- [ ] Confirm the period of performance does not exceed {period_max} months.")
    if disallowed:
        any_limit = True
        lines.append("- [ ] Confirm none of the following disallowed categories appear in the budget line items:")
        for cat in disallowed:
            lines.append(f"  - [ ] {cat}")

    if not any_limit:
        lines.append("- No numeric limits or disallowed categories were listed in the rules file. Confirm this against the solicitation directly.")

    lines.append("")
    return lines


def build_cost_share_section(rules: dict) -> list[str]:
    required = rules.get("cost_share_required", False)
    lines = ["## Cost-share", ""]
    if required:
        lines.append("- [ ] Confirm a cost-share commitment is included, since the solicitation requires cost-share.")
        lines.append("- [ ] Confirm the cost-share source and amount are documented and approved.")
    else:
        lines.append("- [ ] Confirm cost-share is not required for this solicitation (rules file states it is not required).")
    lines.append("")
    return lines


def build_deadline_section(rules: dict) -> list[str]:
    deadline = rules.get("deadline")
    lines = ["## Deadline", ""]
    if deadline:
        lines.append(f"- [ ] Confirm the submission is planned for on or before the stated deadline: {deadline}.")
        lines.append("- [ ] Confirm the deadline above matches the current solicitation text, in case of amendments.")
    else:
        lines.append("- No deadline was listed in the rules file. Confirm the deadline against the solicitation directly.")
    lines.append("")
    return lines


# ---------------------------------------------------------------------------
# Report builder
# ---------------------------------------------------------------------------

def build_checklist(rules: dict, rules_path: str) -> str:
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    lines: list[str] = []
    lines.append("# Submission checklist (preparation aid, not a compliance determination)")
    lines.append("")
    lines.append(
        "> This checklist is assembled from a structured rules file extracted from a "
        "solicitation or NOFO. It is a preparation aid to help a human work through "
        "submission requirements. It does not determine compliance, does not certify "
        "the proposal, and does not replace reading the solicitation itself."
    )
    lines.append("")
    lines.append(f"**Generated:** {now}")

    try:
        rel_rules = os.path.relpath(rules_path)
    except ValueError:
        rel_rules = rules_path
    lines.append(f"**Rules file:** {rel_rules}")
    lines.append("")
    lines.append("---")
    lines.append("")

    lines.extend(build_documents_section(rules))
    lines.extend(build_budget_sections_section(rules))
    lines.extend(build_limits_section(rules))
    lines.extend(build_cost_share_section(rules))
    lines.extend(build_deadline_section(rules))

    lines.append("---")
    lines.append("")
    lines.append("## Closing statement")
    lines.append("")
    lines.append(
        "**This checklist is a preparation aid assembled from the structured rules file above. "
        "Checking every box here does not mean the proposal is compliant with the solicitation. "
        "A person in sponsored programs must verify each item against the actual solicitation "
        "text and make the final determination before submission.**"
    )
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(
        description=(
            "Build a submission checklist from a structured solicitation rules file. "
            "Preparation aid only; does not determine compliance."
        )
    )
    ap.add_argument("--rules", required=True, help="Path to solicitation rules JSON file.")
    ap.add_argument(
        "--out",
        default=None,
        help="Output path for the Markdown checklist (default: print to stdout).",
    )
    args = ap.parse_args(argv)

    rules = _load_json(args.rules, "rules")
    checklist = build_checklist(rules, args.rules)

    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(checklist)
        print(f"[checklist_builder] wrote {args.out}")
    else:
        sys.stdout.write(checklist)

    return 0


if __name__ == "__main__":
    sys.exit(main())
