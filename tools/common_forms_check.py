#!/usr/bin/env python3
"""common_forms_check -- NIH/NSF Common Forms readiness pre-flight (advisory).

Reads one or more per-person YAML files for senior/key personnel and flags
readiness gaps before the biosketch and current & pending (other) support
documents are generated and certified in SciENcv. Advisory only: this is a
review aid, not a validation, and it certifies nothing. SciENcv produces the
official certified PDFs; this tool checks that the raw material looks ready.

Encoded external expectations (source: NIH implementation of the Common Forms
for the biographical sketch and current & pending (other) support, as
summarized by institutional research offices, e.g. the Stanford ORA summary of
January 2026; verify against current NIH/NSF guidance before relying on it):
  - Common Forms are required for NIH applications due on or after 2026-01-25.
  - The biosketch and current & pending (other) support must be generated in
    SciENcv and certified by the individual.
  - An ORCID iD is required for senior/key personnel.
  - Product limits: up to 5 products closely related to the project and up to
    5 other significant products.

Per-person YAML shape:
  name: Dr. Ada Example
  orcid: 0000-0002-1825-0097
  certified: true
  biosketch:
    products_related: [item, ...]   # up to 5
    products_other:   [item, ...]   # up to 5
    positions:        [item, ...]
    education:        [item, ...]
  current_pending:
    - {project: P1, sponsor: NSF, months: 1.5, status: current}

Checks (PASS or FLAG):
  1. ORCID present and plausibly formatted (four groups of four, last
     character may be X, e.g. 0000-0002-1825-009X; a leading
     https://orcid.org/ prefix is accepted).
  2. biosketch.products_related has at most 5 entries.
  3. biosketch.products_other has at most 5 entries.
  4. certified is true.
  5. Required sections non-empty: biosketch.education, biosketch.positions,
     biosketch.products_related.
  6. Every current_pending entry has a numeric months value.

Exit codes:
  0 -- review complete (flags are reported in the body)
  1 -- invalid input (missing, unreadable, or malformed YAML), or any FLAG
       when --strict is given

Usage:
  python3 tools/common_forms_check.py --person pi.yml
  python3 tools/common_forms_check.py --person pi.yml --person copi.yml --strict
  python3 tools/common_forms_check.py --person pi.yml --out readiness.md

Limits (honest):
  - Checks are lexical and local to your YAML. The tool does not contact
    SciENcv, ORCID, or any sponsor system. A well-formed ORCID string is not
    proof the iD exists or belongs to the person.
  - Policy details change. Confirm dates and limits against the current
    solicitation and agency guidance; this tool checks readiness only.
"""
from __future__ import annotations
import argparse
import os
import re
import sys

import yaml

# UTF-8 stdout guard
import cambium_io  # noqa: F401

ORCID_RE = re.compile(r"^(?:https?://orcid\.org/)?\d{4}-\d{4}-\d{4}-\d{3}[\dX]$")
PRODUCT_LIMIT = 5
REQUIRED_SECTIONS = ("education", "positions", "products_related")


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------

def _fail(msg: str) -> None:
    print(f"[common_forms_check] ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def _load_person(path: str) -> dict:
    if not os.path.exists(path):
        _fail(f"person file not found: {path}")
    try:
        with open(path, encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
    except yaml.YAMLError as exc:
        _fail(f"person file is not valid YAML: {path}\n  {exc}")
    except OSError as exc:
        _fail(f"cannot read person file: {path}\n  {exc}")
    if not isinstance(data, dict):
        _fail(f"person file must be a YAML mapping: {path}")
    return data


# ---------------------------------------------------------------------------
# Individual checks -- each returns a result dict (or a list of them)
# ---------------------------------------------------------------------------

def _row(check: str, passed: bool, note: str = "") -> dict:
    return {"check": check, "result": "PASS" if passed else "FLAG", "note": note}


def _is_number(value) -> bool:
    if isinstance(value, bool):
        return False
    if isinstance(value, (int, float)):
        return True
    if isinstance(value, str):
        try:
            float(value)
            return True
        except ValueError:
            return False
    return False


def check_orcid(person: dict) -> dict:
    orcid = person.get("orcid")
    if orcid is None or str(orcid).strip() == "":
        return _row("ORCID present and plausibly formatted", False,
                    "No orcid stated. An ORCID iD is expected for senior/key personnel.")
    ok = bool(ORCID_RE.match(str(orcid).strip()))
    return _row("ORCID present and plausibly formatted", ok,
                "" if ok else f"'{orcid}' does not match the expected pattern 0000-0000-0000-000X.")


def check_product_limits(person: dict) -> list[dict]:
    bios = person.get("biosketch") or {}
    rows = []
    for field, label in (("products_related", "related"), ("products_other", "other significant")):
        items = bios.get(field) or []
        n = len(items) if isinstance(items, list) else 0
        ok = n <= PRODUCT_LIMIT
        rows.append(_row(
            f"biosketch.{field} within limit of {PRODUCT_LIMIT}",
            ok,
            f"{n} listed." if ok else f"{n} {label} products listed; the limit is {PRODUCT_LIMIT}.",
        ))
    return rows


def check_certified(person: dict) -> dict:
    ok = person.get("certified") is True
    return _row("certified flag is true", ok,
                "" if ok else "certified is not true. The individual certifies in SciENcv; "
                              "this flag records that step in your tracking file.")


def check_required_sections(person: dict) -> list[dict]:
    bios = person.get("biosketch") or {}
    rows = []
    for section in REQUIRED_SECTIONS:
        items = bios.get(section)
        ok = isinstance(items, list) and len(items) > 0
        rows.append(_row(f"biosketch.{section} non-empty", ok,
                         "" if ok else f"Section '{section}' is empty or missing."))
    return rows


def check_months_numeric(person: dict) -> list[dict]:
    entries = person.get("current_pending") or []
    if not isinstance(entries, list) or not entries:
        return [_row("current_pending months numeric", True,
                     "No current_pending entries to check; confirm that is accurate.")]
    bad = []
    for i, entry in enumerate(entries, start=1):
        months = entry.get("months") if isinstance(entry, dict) else None
        if not _is_number(months):
            label = entry.get("project", f"entry {i}") if isinstance(entry, dict) else f"entry {i}"
            bad.append((str(label), months))
    if not bad:
        return [_row("current_pending months numeric", True, f"{len(entries)} entries checked.")]
    return [_row("current_pending months numeric", False,
                 f"'{label}' has a non-numeric months value: {months!r}.")
            for label, months in bad]


def check_person(person: dict) -> list[dict]:
    """Run all readiness checks for one person. Returns a flat list of rows."""
    rows: list[dict] = [check_orcid(person)]
    rows.extend(check_product_limits(person))
    rows.append(check_certified(person))
    rows.extend(check_required_sections(person))
    rows.extend(check_months_numeric(person))
    return rows


# ---------------------------------------------------------------------------
# Report builder
# ---------------------------------------------------------------------------

def _cell(text) -> str:
    return str(text).replace("|", "\\|")


def build_report(people: list[tuple[str, str, list[dict]]]) -> str:
    """people: list of (display name, source file, check rows)."""
    total_pass = sum(1 for _, _, rows in people for r in rows if r["result"] == "PASS")
    total_flag = sum(1 for _, _, rows in people for r in rows if r["result"] == "FLAG")

    lines: list[str] = []
    lines.append("# Common Forms readiness check (advisory, not a validation)")
    lines.append("")
    lines.append(
        "> Readiness review aid for NIH/NSF Common Forms material. SciENcv produces the "
        "official certified biosketch and current & pending (other) support PDFs; this tool "
        "only checks that your local inputs look ready. It is not a compliance determination."
    )
    lines.append("")
    lines.append(f"**People checked:** {len(people)} | **PASS:** {total_pass} | **FLAG:** {total_flag}")
    lines.append("")

    for name, src, rows in people:
        lines.append("---")
        lines.append("")
        lines.append(f"## {name}")
        lines.append("")
        lines.append(f"Source file: {src}")
        lines.append("")
        lines.append("| Check | Result | Note |")
        lines.append("|---|---|---|")
        for r in rows:
            result_cell = "**FLAG**" if r["result"] == "FLAG" else "PASS"
            lines.append(f"| {_cell(r['check'])} | {result_cell} | {_cell(r['note'])} |")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## Closing statement")
    lines.append("")
    lines.append(
        "**This check is advisory: review, not validation. It flags readiness gaps in the "
        "material you supplied and certifies nothing. SciENcv generates the official "
        "certified documents, and a human in sponsored programs must make the final "
        "readiness determination against current NIH/NSF guidance.**"
    )
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description=(
            "Advisory NIH/NSF Common Forms readiness pre-flight for senior/key personnel "
            "YAML files. Review aid only; SciENcv produces the official certified PDFs."
        )
    )
    ap.add_argument("--person", action="append", required=True,
                    help="Path to a per-person YAML file. Repeat for multiple people.")
    ap.add_argument("--strict", action="store_true",
                    help="Exit 1 if any check FLAGs.")
    ap.add_argument("--out", default=None,
                    help="Output path for the Markdown report (default: print to stdout).")
    args = ap.parse_args(argv)

    checked: list[tuple[str, str, list[dict]]] = []
    for path in args.person:
        data = _load_person(path)
        name = str(data.get("name") or os.path.basename(path))
        checked.append((name, os.path.basename(path), check_person(data)))

    report = build_report(checked)

    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(report)
        print(f"[common_forms_check] wrote {args.out}")
    else:
        sys.stdout.write(report)

    n_flags = sum(1 for _, _, rows in checked for r in rows if r["result"] == "FLAG")
    if args.strict and n_flags > 0:
        print(f"[common_forms_check] --strict: {n_flags} flag(s) raised.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
