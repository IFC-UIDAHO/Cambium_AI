#!/usr/bin/env python3
"""budget_narrative_match -- flag mismatches between a proposal budget and its
budget-justification narrative.

A common cause of desk rejects is a budget and its narrative saying different
things: a line item the narrative never explains, a dollar amount that does
not appear anywhere in the prose, or a stated F&A rate or total that does not
match the budget. This tool checks for that kind of disagreement. It does not
certify the budget, generate an official budget justification, or replace a
human reviewer.

Inputs:
  --budget    budget.json    -- same shape used by tools/budget_review.py:
                                 totals (with total), line_items (each with
                                 category and amount), fa_rate, period_months,
                                 sections_present
  --narrative narrative.txt  -- the budget justification prose

Checks (each PASS or FLAG, advisory):
  1. Every line-item category is mentioned somewhere in the narrative.
  2. Every line-item dollar amount appears in the narrative, allowing simple
     formatting differences ($50,000 vs 50000 vs 50,000.00).
  3. If the narrative states an F&A rate, it matches the budget's fa_rate.
  4. If the narrative states a total, it matches the budget's totals.total.

Exit codes:
  0  -- review complete (flags are reported in the body, not via exit code)
  2  -- input file missing or unreadable

Usage:
  python3 tools/budget_narrative_match.py --budget budget.json --narrative narrative.txt
  python3 tools/budget_narrative_match.py --budget budget.json --narrative narrative.txt --out report.md
"""
from __future__ import annotations
import argparse
import json
import os
import re
import sys
from datetime import datetime

# UTF-8 stdout guard
import cambium_io  # noqa: F401


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------

def _load_json(path: str, label: str) -> dict:
    if not os.path.exists(path):
        print(f"[budget_narrative_match] ERROR: {label} file not found: {path}", file=sys.stderr)
        sys.exit(2)
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except json.JSONDecodeError as exc:
        print(f"[budget_narrative_match] ERROR: {label} file is not valid JSON: {path}\n  {exc}", file=sys.stderr)
        sys.exit(2)
    except OSError as exc:
        print(f"[budget_narrative_match] ERROR: cannot read {label} file: {path}\n  {exc}", file=sys.stderr)
        sys.exit(2)


def _load_text(path: str, label: str) -> str:
    if not os.path.exists(path):
        print(f"[budget_narrative_match] ERROR: {label} file not found: {path}", file=sys.stderr)
        sys.exit(2)
    try:
        with open(path, encoding="utf-8") as fh:
            return fh.read()
    except OSError as exc:
        print(f"[budget_narrative_match] ERROR: cannot read {label} file: {path}\n  {exc}", file=sys.stderr)
        sys.exit(2)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _result(check: str, expected: str, actual: str, passed: bool, note: str = "") -> dict:
    return {
        "check": check,
        "expected": expected,
        "actual": actual,
        "result": "PASS" if passed else "FLAG",
        "note": note,
    }


def _normalize_amount(value) -> str:
    """Normalize a numeric amount to a plain digit string for comparison
    (strip sign, thousands separators, trailing .0 / .00)."""
    try:
        f = float(value)
    except (TypeError, ValueError):
        return ""
    if f == int(f):
        return str(int(f))
    return f"{f:.2f}".rstrip("0").rstrip(".")


def _amount_variants(value) -> list[str]:
    """Return plausible textual renderings of a dollar amount, so we can
    search for any of them in free-text narrative."""
    try:
        f = float(value)
    except (TypeError, ValueError):
        return []
    as_int = int(f) if f == int(f) else None
    variants = set()
    if as_int is not None:
        variants.add(str(as_int))
        variants.add(f"{as_int:,}")
        variants.add(f"${as_int:,}")
        variants.add(f"${as_int}")
    else:
        variants.add(f"{f:.2f}")
        variants.add(f"{f:,.2f}")
        variants.add(f"${f:,.2f}")
        variants.add(f"${f:.2f}")
    return sorted(variants)


_NUMBER_RE = re.compile(r"\$?\s*([0-9][0-9,]*(?:\.[0-9]+)?)")


def _numbers_in_text(text: str) -> set:
    """Extract every number-like token from text and normalize it, so we can
    compare against normalized budget amounts regardless of formatting."""
    found = set()
    for m in _NUMBER_RE.finditer(text):
        raw = m.group(1).replace(",", "")
        try:
            f = float(raw)
        except ValueError:
            continue
        found.add(_normalize_amount(f))
    return found


def _percent_in_text(text: str) -> set:
    """Extract percentage-like numbers (e.g. '55%', '55 percent', 'rate of 55')."""
    found = set()
    for m in re.finditer(r"([0-9]+(?:\.[0-9]+)?)\s*(?:%|percent)", text, re.IGNORECASE):
        found.add(_normalize_amount(float(m.group(1))))
    return found


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def check_categories_mentioned(budget: dict, narrative: str) -> list[dict]:
    """One result per line-item category: FLAG if the category name never
    appears in the narrative text (case-insensitive substring match)."""
    line_items = budget.get("line_items", [])
    narrative_lower = narrative.lower()
    results = []
    for item in line_items:
        category = item.get("category", "")
        if not category:
            continue
        mentioned = category.lower() in narrative_lower
        results.append(_result(
            f"Category mentioned: {category}",
            "appears in narrative",
            "found" if mentioned else "not found",
            mentioned,
            "" if mentioned else f"Line-item category '{category}' does not appear anywhere in the narrative text.",
        ))
    return results


def check_amounts_mentioned(budget: dict, narrative: str) -> list[dict]:
    """One result per line-item amount: FLAG if no plausible rendering of the
    dollar amount appears anywhere in the narrative."""
    line_items = budget.get("line_items", [])
    narrative_numbers = _numbers_in_text(narrative)
    results = []
    for item in line_items:
        category = item.get("category", "(uncategorized)")
        amount = item.get("amount")
        if amount is None:
            continue
        normalized = _normalize_amount(amount)
        mentioned = normalized != "" and normalized in narrative_numbers
        variants = _amount_variants(amount)
        example = variants[0] if variants else str(amount)
        results.append(_result(
            f"Amount mentioned: {category} ({example})",
            "appears in narrative",
            "found" if mentioned else "not found",
            mentioned,
            "" if mentioned else f"Amount for '{category}' ({example}) does not appear in the narrative in any recognized format.",
        ))
    return results


def check_fa_rate_match(budget: dict, narrative: str) -> dict:
    """FLAG if the narrative states an F&A rate that differs from the budget."""
    budget_rate = budget.get("fa_rate")
    narrative_percents = _percent_in_text(narrative)
    if budget_rate is None:
        return _result("F&A rate stated in narrative matches budget", "n/a", "budget does not state fa_rate", True,
                        "Budget does not state fa_rate; skipped.")
    normalized_budget_rate = _normalize_amount(budget_rate)
    if not narrative_percents:
        return _result("F&A rate stated in narrative matches budget", f"{budget_rate}", "not stated in narrative", True,
                        "Narrative does not state a percentage; nothing to compare.")
    matched = normalized_budget_rate in narrative_percents
    return _result(
        "F&A rate stated in narrative matches budget",
        f"{budget_rate}",
        ", ".join(sorted(narrative_percents)),
        matched,
        "" if matched else f"Narrative states a percentage that does not match the budget's F&A rate of {budget_rate}.",
    )


def check_total_match(budget: dict, narrative: str) -> dict:
    """FLAG if the narrative states a total that differs from budget totals.total."""
    totals = budget.get("totals", {})
    budget_total = totals.get("total")
    narrative_numbers = _numbers_in_text(narrative)
    if budget_total is None:
        return _result("Total stated in narrative matches budget", "n/a", "budget does not state totals.total", True,
                        "Budget does not state totals.total; skipped.")
    normalized_total = _normalize_amount(budget_total)
    matched = normalized_total in narrative_numbers
    return _result(
        "Total stated in narrative matches budget",
        f"{_amount_variants(budget_total)[0] if _amount_variants(budget_total) else budget_total}",
        "found in narrative" if matched else "not found in narrative",
        matched,
        "" if matched else (
            f"Budget total ({budget_total}) does not appear anywhere in the narrative. "
            "If the narrative states a different total, reconcile the two documents."
        ),
    )


def run_checks(budget: dict, narrative: str) -> list[dict]:
    """Run all checks. Returns a flat list of result dicts.

    To add a new check: define a check_* function above and call it here.
    Single-result checks return a dict; multi-result checks return a list.
    """
    results: list[dict] = []
    results.extend(check_categories_mentioned(budget, narrative))
    results.extend(check_amounts_mentioned(budget, narrative))
    results.append(check_fa_rate_match(budget, narrative))
    results.append(check_total_match(budget, narrative))
    return results


# ---------------------------------------------------------------------------
# Report builder
# ---------------------------------------------------------------------------

def build_report(budget: dict, narrative: str, budget_path: str, narrative_path: str) -> str:
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    results = run_checks(budget, narrative)

    n_flags = sum(1 for r in results if r["result"] == "FLAG")
    n_pass = sum(1 for r in results if r["result"] == "PASS")

    lines: list[str] = []

    lines.append("# Budget-to-narrative match (advisory, not a compliance determination)")
    lines.append("")
    lines.append(
        "> This report flags where the budget and the budget-justification narrative may "
        "disagree. It is produced by a deterministic text-matching checker, not by a "
        "compliance officer. It does not certify the budget, does not generate an official "
        "budget justification, and does not replace human reconciliation of the two documents."
    )
    lines.append("")
    lines.append(f"**Generated:** {now}")

    try:
        rel_budget = os.path.relpath(budget_path)
    except ValueError:
        rel_budget = budget_path
    try:
        rel_narrative = os.path.relpath(narrative_path)
    except ValueError:
        rel_narrative = narrative_path

    lines.append(f"**Budget file:** {rel_budget}")
    lines.append(f"**Narrative file:** {rel_narrative}")
    lines.append(f"**Checks run:** {len(results)} | **PASS:** {n_pass} | **FLAG:** {n_flags}")
    lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## Match results")
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
        "**This report is advisory. It flags places where the budget and the narrative may not "
        "agree, using simple text matching. It does not certify that the budget and narrative are "
        "consistent, does not generate an official budget justification, and does not replace a "
        "human review. A person in sponsored programs must reconcile any flagged items before "
        "submission.**"
    )
    lines.append("")
    if n_flags > 0:
        lines.append(
            f"**{n_flags} item(s) flagged. A human must reconcile each FLAG row above before submission.**"
        )
    else:
        lines.append(
            "**No flags raised by text matching. A human must still reconcile the budget and "
            "narrative before submission; this check cannot see meaning, only text.**"
        )
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(
        description=(
            "Flag disagreements between a proposal budget and its budget-justification "
            "narrative. Advisory only; does not certify the budget or replace human review."
        )
    )
    ap.add_argument("--budget", required=True, help="Path to budget JSON file.")
    ap.add_argument("--narrative", required=True, help="Path to budget-justification narrative text file.")
    ap.add_argument(
        "--out",
        default=None,
        help="Output path for the Markdown report (default: print to stdout).",
    )
    args = ap.parse_args(argv)

    budget = _load_json(args.budget, "budget")
    narrative = _load_text(args.narrative, "narrative")

    report = build_report(budget, narrative, args.budget, args.narrative)

    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(report)
        print(f"[budget_narrative_match] wrote {args.out}")
    else:
        sys.stdout.write(report)

    return 0


if __name__ == "__main__":
    sys.exit(main())
