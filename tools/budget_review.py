#!/usr/bin/env python3
"""budget_review -- deterministic budget-to-solicitation review for research proposals.

FLAGS potential issues before a human reviews the budget. Advisory only: it does not
approve, certify, or constitute a compliance determination.

Inputs (two JSON files):
  --rules  solicitation_rules.json   -- funder rules extracted from a NOFO (e.g. by AI4RA Vandalizer)
  --budget budget.json               -- structured budget for the proposal

Deterministic checks (each produces PASS or FLAG):
  1. F&A rate <= solicitation cap
  2. Total cost <= solicitation ceiling
  3. Period months <= solicitation maximum
  4. All required budget sections are present
  5. No disallowed cost categories appear in line items
  6. Cost-share is present when required

Exit codes:
  0  -- review complete (flags are reported in the body, not via exit code)
  2  -- input file missing or unreadable

Usage:
  python3 tools/budget_review.py --rules solicitation_rules.json --budget budget.json
  python3 tools/budget_review.py --rules solicitation_rules.json --budget budget.json --out report.md
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
# Data loaders
# ---------------------------------------------------------------------------

def _load_json(path: str, label: str) -> dict:
    """Load a JSON file; exit 2 with a clear message if missing or unreadable."""
    if not os.path.exists(path):
        print(f"[budget_review] ERROR: {label} file not found: {path}", file=sys.stderr)
        sys.exit(2)
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except json.JSONDecodeError as exc:
        print(f"[budget_review] ERROR: {label} file is not valid JSON: {path}\n  {exc}", file=sys.stderr)
        sys.exit(2)
    except OSError as exc:
        print(f"[budget_review] ERROR: cannot read {label} file: {path}\n  {exc}", file=sys.stderr)
        sys.exit(2)


# ---------------------------------------------------------------------------
# Individual checks -- each returns a result dict
# ---------------------------------------------------------------------------

def _result(check: str, expected: str, actual: str, passed: bool, note: str = "") -> dict:
    return {
        "check": check,
        "expected": expected,
        "actual": actual,
        "result": "PASS" if passed else "FLAG",
        "note": note,
    }


def check_fa_rate(rules: dict, budget: dict) -> dict:
    cap = rules.get("fa_rate_cap")
    rate = budget.get("fa_rate")
    if cap is None:
        return _result("F&A rate vs cap", "cap not specified in rules", str(rate), True,
                        "No cap rule to check against; skipped.")
    if rate is None:
        return _result("F&A rate vs cap", f"<= {cap}", "not stated in budget", False,
                        "Budget does not state fa_rate.")
    passed = float(rate) <= float(cap)
    return _result(
        "F&A rate vs cap",
        f"<= {cap}",
        str(rate),
        passed,
        "" if passed else f"F&A rate {rate} exceeds solicitation cap {cap}.",
    )


def check_total_cost(rules: dict, budget: dict) -> dict:
    ceiling = rules.get("total_cost_ceiling")
    totals = budget.get("totals", {})
    total = totals.get("total")
    if ceiling is None:
        return _result("Total cost vs ceiling", "ceiling not specified", str(total), True,
                        "No ceiling rule to check against; skipped.")
    if total is None:
        return _result("Total cost vs ceiling", f"<= {ceiling}", "not stated in budget", False,
                        "Budget totals.total is not stated.")
    passed = float(total) <= float(ceiling)
    return _result(
        "Total cost vs ceiling",
        f"<= {ceiling}",
        str(total),
        passed,
        "" if passed else f"Total {total} exceeds solicitation ceiling {ceiling}.",
    )


def check_period(rules: dict, budget: dict) -> dict:
    max_months = rules.get("period_months_max")
    period = budget.get("period_months")
    if max_months is None:
        return _result("Period months vs max", "max not specified", str(period), True,
                        "No period max rule to check against; skipped.")
    if period is None:
        return _result("Period months vs max", f"<= {max_months}", "not stated in budget", False,
                        "Budget does not state period_months.")
    passed = int(period) <= int(max_months)
    return _result(
        "Period months vs max",
        f"<= {max_months} months",
        f"{period} months",
        passed,
        "" if passed else f"Period {period} months exceeds solicitation maximum {max_months} months.",
    )


def check_required_sections(rules: dict, budget: dict) -> list[dict]:
    """One result per required section that is missing."""
    required = rules.get("required_budget_sections", [])
    present = set(s.lower() for s in budget.get("sections_present", []))
    results = []
    for section in required:
        is_present = section.lower() in present
        results.append(_result(
            f"Required section: {section}",
            "present",
            "present" if is_present else "MISSING",
            is_present,
            "" if is_present else f"Required budget section '{section}' is not listed in sections_present.",
        ))
    return results


def check_disallowed_categories(rules: dict, budget: dict) -> list[dict]:
    """One result per disallowed category found in line items."""
    disallowed = [c.lower() for c in rules.get("disallowed_categories", [])]
    line_items = budget.get("line_items", [])
    found_categories = [item.get("category", "").lower() for item in line_items]
    results = []
    for cat in disallowed:
        in_budget = cat in found_categories
        results.append(_result(
            f"Disallowed category: {cat}",
            "absent",
            "FOUND" if in_budget else "absent",
            not in_budget,
            f"Disallowed category '{cat}' appears in line items." if in_budget else "",
        ))
    return results


def check_cost_share(rules: dict, budget: dict) -> dict:
    required = rules.get("cost_share_required", False)
    present = budget.get("cost_share_present", None)
    if not required:
        return _result("Cost share", "not required", "n/a", True, "Cost share not required by solicitation.")
    if present is None:
        # Not stated -- treat as absent
        return _result(
            "Cost share",
            "required and present",
            "not stated in budget",
            False,
            "Solicitation requires cost share but budget does not state cost_share_present.",
        )
    passed = bool(present)
    return _result(
        "Cost share",
        "required and present",
        "present" if passed else "absent",
        passed,
        "" if passed else "Solicitation requires cost share but budget states it is absent.",
    )


# ---------------------------------------------------------------------------
# Run all checks
# ---------------------------------------------------------------------------

def run_checks(rules: dict, budget: dict) -> list[dict]:
    """Run all deterministic checks. Returns a flat list of result dicts.

    To add a new check: define a check_* function above and call it here.
    Single-result checks return a dict; multi-result checks return a list.
    """
    results: list[dict] = []
    results.append(check_fa_rate(rules, budget))
    results.append(check_total_cost(rules, budget))
    results.append(check_period(rules, budget))
    results.extend(check_required_sections(rules, budget))
    results.extend(check_disallowed_categories(rules, budget))
    results.append(check_cost_share(rules, budget))
    return results


# ---------------------------------------------------------------------------
# Report builder
# ---------------------------------------------------------------------------

def build_report(rules: dict, budget: dict, rules_path: str, budget_path: str) -> str:
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    results = run_checks(rules, budget)

    n_flags = sum(1 for r in results if r["result"] == "FLAG")
    n_pass = sum(1 for r in results if r["result"] == "PASS")

    lines: list[str] = []

    lines.append("# Budget review (advisory, not a compliance determination)")
    lines.append("")
    lines.append(
        "> This report flags potential issues for human review. "
        "It is produced by a deterministic rule-checker, not by a compliance officer. "
        "A human in sponsored programs must make the final determination."
    )
    lines.append("")
    lines.append(f"**Generated:** {now}")

    try:
        rel_rules = os.path.relpath(rules_path)
    except ValueError:
        rel_rules = rules_path
    try:
        rel_budget = os.path.relpath(budget_path)
    except ValueError:
        rel_budget = budget_path

    lines.append(f"**Rules file:** {rel_rules}")
    lines.append(f"**Budget file:** {rel_budget}")
    lines.append(f"**Checks run:** {len(results)} | **PASS:** {n_pass} | **FLAG:** {n_flags}")
    lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## Deterministic check results")
    lines.append("")
    lines.append("| Check | Expected | Actual | Result | Note |")
    lines.append("|---|---|---|---|---|")

    for r in results:
        result_cell = r["result"]
        if result_cell == "FLAG":
            result_cell = "**FLAG**"
        lines.append(
            f"| {r['check']} | {r['expected']} | {r['actual']} | {result_cell} | {r['note']} |"
        )

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Closing statement")
    lines.append("")
    lines.append(
        "**This budget review is advisory. "
        "It applies deterministic rules extracted from the solicitation and flags items that "
        "may need attention. It does not constitute approval, compliance certification, or a "
        "final determination that this budget satisfies all funder requirements. "
        "A human in sponsored programs at the submitting institution must review this budget, "
        "resolve any flagged items, and make the final determination before submission.**"
    )
    lines.append("")
    if n_flags > 0:
        lines.append(
            f"**{n_flags} item(s) flagged. Review each FLAG row above before submission.**"
        )
    else:
        lines.append(
            "**No flags raised by deterministic checks. "
            "Human review is still required before submission.**"
        )
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(
        description=(
            "Deterministic budget-to-solicitation review. Advisory only. "
            "Flags potential issues; does not certify compliance."
        )
    )
    ap.add_argument("--rules", required=True, help="Path to solicitation rules JSON file.")
    ap.add_argument("--budget", required=True, help="Path to budget JSON file.")
    ap.add_argument(
        "--out",
        default=None,
        help="Output path for the Markdown report (default: print to stdout).",
    )
    args = ap.parse_args(argv)

    rules = _load_json(args.rules, "rules")
    budget = _load_json(args.budget, "budget")

    report = build_report(rules, budget, args.rules, args.budget)

    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(report)
        print(f"[budget_review] wrote {args.out}")
    else:
        sys.stdout.write(report)

    return 0


if __name__ == "__main__":
    sys.exit(main())
