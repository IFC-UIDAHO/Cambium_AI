#!/usr/bin/env python3
"""rules_handoff -- validate a Vandalizer-to-Cambium rules handoff for budget_review.

AI4RA's Vandalizer extracts solicitation rules from a NOFO. This tool checks that
the extracted rules match the agreed handoff shape
(examples/ai4ra/vandalizer_handoff.schema.json), so they can be passed straight to
tools/budget_review.py as --rules with no manual conversion. This is the
interoperability seam (AI4RA Pillar: Flexibility).

Cambium does not do the extraction. It only validates the shape of what was handed
over and reports whether it is ready for the deterministic budget review.

If the optional `jsonschema` package is installed, full JSON Schema validation is
used. Without it, a minimal required-keys and type check runs instead, and the tool
says which check it used.

Usage:
  python3 tools/rules_handoff.py --rules solicitation_rules.json
  python3 tools/rules_handoff.py --rules solicitation_rules.json --schema <path>

Exit codes:
  0  -- handoff is valid and ready for budget_review
  1  -- handoff is invalid (problems are printed)
  2  -- input or schema file missing or unreadable
"""
from __future__ import annotations
import argparse
import json
import os
import sys

import cambium_io  # noqa: F401  (UTF-8 stdout guard)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_SCHEMA = os.path.join(ROOT, "examples", "ai4ra", "vandalizer_handoff.schema.json")

_REQUIRED = ("required_budget_sections", "disallowed_categories", "cost_share_required")


def _load(path: str, label: str) -> dict:
    if not os.path.exists(path):
        print(f"[rules_handoff] ERROR: {label} not found: {path}", file=sys.stderr)
        sys.exit(2)
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (json.JSONDecodeError, OSError) as exc:
        print(f"[rules_handoff] ERROR: cannot read {label}: {path}\n  {exc}", file=sys.stderr)
        sys.exit(2)


def minimal_check(data: dict) -> list[str]:
    """Stdlib fallback validation. Returns a list of problem strings (empty means valid)."""
    problems: list[str] = []
    for key in _REQUIRED:
        if key not in data:
            problems.append(f"missing required key: {key}")
    if "required_budget_sections" in data and not isinstance(data["required_budget_sections"], list):
        problems.append("required_budget_sections must be a list")
    if "disallowed_categories" in data and not isinstance(data["disallowed_categories"], list):
        problems.append("disallowed_categories must be a list")
    if "cost_share_required" in data and not isinstance(data["cost_share_required"], bool):
        problems.append("cost_share_required must be a boolean")
    for num_key in ("fa_rate_cap", "total_cost_ceiling"):
        if num_key in data and data[num_key] is not None and not isinstance(data[num_key], (int, float)):
            problems.append(f"{num_key} must be a number or null")
    if "period_months_max" in data and data["period_months_max"] is not None \
            and not isinstance(data["period_months_max"], int):
        problems.append("period_months_max must be an integer or null")
    return problems


def validate(data: dict, schema: dict) -> tuple[list[str], str]:
    """Return (problems, method). Uses jsonschema if a usable validator is available,
    otherwise falls back to the stdlib minimal check. Picks the newest validator the
    installed jsonschema offers, so an older jsonschema still works."""
    try:
        import jsonschema  # optional dependency
    except Exception:
        return minimal_check(data), "minimal stdlib check (install jsonschema for full validation)"
    validator_cls = (
        getattr(jsonschema, "Draft202012Validator", None)
        or getattr(jsonschema, "Draft201909Validator", None)
        or getattr(jsonschema, "Draft7Validator", None)
        or getattr(jsonschema, "Draft4Validator", None)
    )
    if validator_cls is None:
        return minimal_check(data), "minimal stdlib check (installed jsonschema has no usable validator)"
    validator = validator_cls(schema)
    problems = [f"{'/'.join(str(p) for p in e.path) or '(root)'}: {e.message}"
                for e in validator.iter_errors(data)]
    return problems, f"jsonschema full validation ({validator_cls.__name__})"


def main(argv=None):
    ap = argparse.ArgumentParser(description="Validate a Vandalizer-to-Cambium rules handoff for budget_review.")
    ap.add_argument("--rules", required=True, help="Path to the extracted solicitation rules JSON.")
    ap.add_argument("--schema", default=DEFAULT_SCHEMA, help="Path to the handoff JSON Schema.")
    args = ap.parse_args(argv)

    data = _load(args.rules, "rules")
    schema = _load(args.schema, "schema")
    problems, method = validate(data, schema)

    print(f"[rules_handoff] validated with: {method}")
    if problems:
        print(f"[rules_handoff] INVALID: {len(problems)} problem(s):")
        for p in problems:
            print(f"  - {p}")
        return 1
    print("[rules_handoff] valid. Ready to pass to budget_review.py as --rules.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
