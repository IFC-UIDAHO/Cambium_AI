#!/usr/bin/env python3
"""authorship_matrix -- build a CRediT contribution matrix and statement.

CRediT (Contributor Roles Taxonomy, https://credit.niso.org/) defines 14
standard roles for describing each author's contribution to a scholarly work.
This tool reads a list of authors and their claimed roles (CSV or JSON),
validates the role names, and emits:
  - a Markdown matrix (authors x roles, with x marks)
  - a journal-style contribution statement paragraph

This is a formatting and validation aid. It does not decide who should be an
author or which roles are appropriate; that is a decision for the author team,
following their journal's and institution's authorship policy (e.g. ICMJE).

Input CSV: columns "name" and "roles" (roles is a semicolon-separated list).
Input JSON: a list of {"name": str, "roles": [str, ...]}.
Role names are matched case-insensitively against the official CRediT list.

Validation:
  - every author must have at least 1 role (exit 1 if not)
  - every role name must be a recognized CRediT role (exit 1, lists valid roles)
  - warn (stderr, exit 0) when one author holds more than 8 roles
  - warn (stderr, exit 0) when a role has no author

Exit codes:
  0  -- matrix and statement built (warnings may be printed to stderr)
  1  -- unknown role name, or an author with zero roles
  2  -- input file missing, unreadable, or malformed

Usage:
  python3 tools/authorship_matrix.py --authors authors.csv
  python3 tools/authorship_matrix.py --authors authors.json --out matrix.md
"""
from __future__ import annotations
import argparse
import csv
import json
import os
import sys

# UTF-8 stdout guard
import cambium_io  # noqa: F401

# The 14 official CRediT roles, in taxonomy order (https://credit.niso.org/)
CREDIT_ROLES = [
    "Conceptualization",
    "Data curation",
    "Formal analysis",
    "Funding acquisition",
    "Investigation",
    "Methodology",
    "Project administration",
    "Resources",
    "Software",
    "Supervision",
    "Validation",
    "Visualization",
    "Writing - original draft",
    "Writing - review & editing",
]
_ROLE_LOOKUP = {r.lower(): r for r in CREDIT_ROLES}
MAX_ROLES_BEFORE_WARN = 8


class _ToolError(Exception):
    """Private control-flow error: carries the exit code so main() can return it
    (house convention: main(argv) returns an int; sys.exit only at the bottom).
    The human-readable message is printed to stderr at the raise site."""

    def __init__(self, code: int):
        super().__init__(code)
        self.code = code


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------

def _load_authors(path: str) -> list[dict]:
    if not os.path.exists(path):
        print(f"[authorship_matrix] ERROR: authors file not found: {path}", file=sys.stderr)
        raise _ToolError(2)
    ext = os.path.splitext(path)[1].lower()
    try:
        if ext == ".json":
            with open(path, encoding="utf-8") as fh:
                data = json.load(fh)
            if not isinstance(data, list):
                raise ValueError("JSON authors file must contain a list")
            authors = []
            for i, item in enumerate(data):
                if not isinstance(item, dict) or "name" not in item:
                    raise ValueError(f"authors[{i}] must be an object with a 'name' key")
                roles = item.get("roles", [])
                if not isinstance(roles, list):
                    raise ValueError(f"authors[{i}]['roles'] must be a list")
                authors.append({"name": str(item["name"]), "roles": [str(r) for r in roles]})
            return authors
        else:
            with open(path, encoding="utf-8", newline="") as fh:
                reader = csv.DictReader(fh)
                if reader.fieldnames is None or "name" not in reader.fieldnames:
                    raise ValueError("CSV authors file must have a 'name' column")
                authors = []
                for row in reader:
                    raw_roles = (row.get("roles") or "").strip()
                    roles = [r.strip() for r in raw_roles.split(";") if r.strip()]
                    authors.append({"name": row["name"].strip(), "roles": roles})
                return authors
    except (json.JSONDecodeError, ValueError) as exc:
        print(f"[authorship_matrix] ERROR: authors file is malformed: {path}\n  {exc}", file=sys.stderr)
        raise _ToolError(2)
    except OSError as exc:
        print(f"[authorship_matrix] ERROR: cannot read authors file: {path}\n  {exc}", file=sys.stderr)
        raise _ToolError(2)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_authors(authors: list[dict]) -> tuple[list[dict], list[str]]:
    """Normalize role names to official casing. Returns (normalized_authors, warnings).

    Raises _ToolError(1) (message already on stderr) on an unknown role or a
    zero-role author; main() turns that into return code 1.
    """
    normalized: list[dict] = []
    unknown: list[str] = []
    zero_role: list[str] = []

    for author in authors:
        name = author["name"]
        norm_roles = []
        for role in author["roles"]:
            official = _ROLE_LOOKUP.get(role.strip().lower())
            if official is None:
                unknown.append(f"{name}: '{role}'")
            else:
                norm_roles.append(official)
        if not norm_roles:
            zero_role.append(name)
        normalized.append({"name": name, "roles": norm_roles})

    if unknown:
        valid_list = "\n  - ".join(CREDIT_ROLES)
        print(
            "[authorship_matrix] ERROR: unknown CRediT role name(s):\n  "
            + "\n  ".join(unknown)
            + "\nValid CRediT roles are:\n  - " + valid_list,
            file=sys.stderr,
        )
        raise _ToolError(1)

    if zero_role:
        print(
            "[authorship_matrix] ERROR: author(s) with zero roles: " + ", ".join(zero_role),
            file=sys.stderr,
        )
        raise _ToolError(1)

    warnings: list[str] = []
    for author in normalized:
        if len(author["roles"]) > MAX_ROLES_BEFORE_WARN:
            warnings.append(
                f"'{author['name']}' holds {len(author['roles'])} roles "
                f"(more than {MAX_ROLES_BEFORE_WARN}); confirm this is intentional."
            )
    covered_roles = {r for a in normalized for r in a["roles"]}
    for role in CREDIT_ROLES:
        if role not in covered_roles:
            warnings.append(f"no author holds the role '{role}'.")

    return normalized, warnings


# ---------------------------------------------------------------------------
# Renderers
# ---------------------------------------------------------------------------

def build_matrix_markdown(authors: list[dict]) -> str:
    lines: list[str] = []
    lines.append("# CRediT contribution matrix")
    lines.append("")
    lines.append(
        "> Built from the CRediT Contributor Roles Taxonomy (https://credit.niso.org/). "
        "This is a formatting aid; the author team decides authorship and role assignment."
    )
    lines.append("")
    header = "| Author | " + " | ".join(CREDIT_ROLES) + " |"
    sep = "|---|" + "|".join(["---"] * len(CREDIT_ROLES)) + "|"
    lines.append(header)
    lines.append(sep)
    for author in authors:
        cells = ["x" if role in author["roles"] else "" for role in CREDIT_ROLES]
        lines.append(f"| {author['name']} | " + " | ".join(cells) + " |")
    lines.append("")
    return "\n".join(lines)


def build_statement(authors: list[dict]) -> str:
    parts = []
    for author in authors:
        initials = "".join(w[0].upper() for w in author["name"].split() if w)
        parts.append(f"{initials or author['name']}: {', '.join(author['roles'])}.")
    return " ".join(parts)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Build a CRediT contribution matrix and journal-style statement from an authors file."
    )
    ap.add_argument("--authors", required=True, help="Path to authors CSV or JSON file.")
    ap.add_argument("--out", default=None, help="Output path for the Markdown matrix + statement (default: stdout).")
    args = ap.parse_args(argv)

    try:
        raw_authors = _load_authors(args.authors)
        if not raw_authors:
            print("[authorship_matrix] ERROR: no authors found in input file", file=sys.stderr)
            return 2
        authors, warnings = validate_authors(raw_authors)
    except _ToolError as exc:
        return exc.code
    for w in warnings:
        print(f"[authorship_matrix] WARNING: {w}", file=sys.stderr)

    matrix_md = build_matrix_markdown(authors)
    statement = build_statement(authors)

    output = matrix_md + "\n## Contribution statement\n\n" + statement + "\n"

    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(output)
        print(f"[authorship_matrix] wrote {args.out}")
    else:
        sys.stdout.write(output)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
