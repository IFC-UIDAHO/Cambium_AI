#!/usr/bin/env python3
"""solicitation_explainer -- render structured solicitation rules into a plain-language
one-page explainer for a new principal investigator.

This is a template renderer of the structured facts you give it. There is no model
call and no interpretation beyond restating the fields in plain sentences. It is a
plain-language summary of the structured facts provided, not a substitute for
reading the actual solicitation or NOFO.

Input (--rules rules.json), fields (all optional, missing fields are noted as such):
  solicitation_id
  fa_rate_cap
  total_cost_ceiling
  period_months_max
  required_budget_sections   (list)
  disallowed_categories      (list)
  cost_share_required        (bool)
  required_documents         (list)
  deadline

Exit codes:
  0  -- explainer built and printed (or written)
  2  -- input file missing or unreadable

Usage:
  python3 tools/solicitation_explainer.py --rules rules.json
  python3 tools/solicitation_explainer.py --rules rules.json --out explainer.md
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
        print(f"[solicitation_explainer] ERROR: {label} file not found: {path}", file=sys.stderr)
        sys.exit(2)
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except json.JSONDecodeError as exc:
        print(f"[solicitation_explainer] ERROR: {label} file is not valid JSON: {path}\n  {exc}", file=sys.stderr)
        sys.exit(2)
    except OSError as exc:
        print(f"[solicitation_explainer] ERROR: cannot read {label} file: {path}\n  {exc}", file=sys.stderr)
        sys.exit(2)


# ---------------------------------------------------------------------------
# Field helpers
# ---------------------------------------------------------------------------

def _fmt_money(value) -> str:
    if value is None:
        return "not stated"
    try:
        return f"${float(value):,.0f}"
    except (TypeError, ValueError):
        return str(value)


def _fmt_rate(value) -> str:
    if value is None:
        return "not stated"
    try:
        return f"{float(value) * 100:.1f}%"
    except (TypeError, ValueError):
        return str(value)


def _fmt_list(items) -> list[str]:
    if not items:
        return ["none stated"]
    return [str(i) for i in items]


# ---------------------------------------------------------------------------
# Explainer builder
# ---------------------------------------------------------------------------

def build_explainer(rules: dict, rules_path: str) -> str:
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    solicitation_id = rules.get("solicitation_id") or "not stated"
    fa_rate_cap = rules.get("fa_rate_cap")
    total_cost_ceiling = rules.get("total_cost_ceiling")
    period_months_max = rules.get("period_months_max")
    required_budget_sections = rules.get("required_budget_sections", [])
    disallowed_categories = rules.get("disallowed_categories", [])
    cost_share_required = rules.get("cost_share_required", False)
    required_documents = rules.get("required_documents", [])
    deadline = rules.get("deadline") or "not stated"

    try:
        rel_rules = os.path.relpath(rules_path)
    except ValueError:
        rel_rules = rules_path

    lines: list[str] = []

    lines.append("# Solicitation explainer (plain-language summary)")
    lines.append("")
    lines.append(
        "> This is a plain-language summary of the structured facts provided in the "
        "rules file below. It is a template renderer, not a model, and it is not a "
        "substitute for reading the actual solicitation or NOFO."
    )
    lines.append("")
    lines.append(f"**Generated:** {now}")
    lines.append(f"**Rules file:** {rel_rules}")
    lines.append(f"**Solicitation ID:** {solicitation_id}")
    lines.append("")
    lines.append("---")
    lines.append("")

    lines.append("## At a glance")
    lines.append("")
    lines.append(f"- Total cost ceiling: {_fmt_money(total_cost_ceiling)}.")
    if period_months_max is None:
        lines.append("- Maximum project period: not stated.")
    else:
        lines.append(f"- Maximum project period: {period_months_max} months.")
    lines.append(f"- F&A (indirect cost) rate cap: {_fmt_rate(fa_rate_cap)}.")
    lines.append(f"- Deadline: {deadline}.")
    lines.append("")

    lines.append("## What you must include")
    lines.append("")
    lines.append("Required documents:")
    lines.append("")
    for doc in _fmt_list(required_documents):
        lines.append(f"- {doc}")
    lines.append("")
    lines.append("Required budget sections:")
    lines.append("")
    for section in _fmt_list(required_budget_sections):
        lines.append(f"- {section}")
    lines.append("")

    lines.append("## What is not allowed")
    lines.append("")
    lines.append("Disallowed cost categories:")
    lines.append("")
    for cat in _fmt_list(disallowed_categories):
        lines.append(f"- {cat}")
    lines.append("")

    lines.append("## Cost share")
    lines.append("")
    if cost_share_required:
        lines.append("Cost share is required by this solicitation.")
    else:
        lines.append("Cost share is not required by this solicitation, based on the fields provided.")
    lines.append("")

    lines.append("## Deadline")
    lines.append("")
    lines.append(f"The deadline stated in the rules file is: {deadline}.")
    lines.append("Confirm this against the sponsor's official posting before relying on it.")
    lines.append("")

    lines.append("---")
    lines.append("")
    lines.append(
        "**This is a plain-language summary of the structured facts provided. "
        "It is not a substitute for reading the actual solicitation. A new principal "
        "investigator should still read the full solicitation and consult sponsored "
        "programs before proceeding.**"
    )
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(
        description=(
            "Render structured solicitation rules into a plain-language one-page "
            "explainer. Template renderer only; not a substitute for reading the "
            "actual solicitation."
        )
    )
    ap.add_argument("--rules", required=True, help="Path to solicitation rules JSON file.")
    ap.add_argument("--out", default=None, help="Output path for the Markdown explainer (default: stdout).")
    args = ap.parse_args(argv)

    rules = _load_json(args.rules, "rules")
    explainer = build_explainer(rules, args.rules)

    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(explainer)
        print(f"[solicitation_explainer] wrote {args.out}")
    else:
        sys.stdout.write(explainer)

    return 0


if __name__ == "__main__":
    sys.exit(main())
