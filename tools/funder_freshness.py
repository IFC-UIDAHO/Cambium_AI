#!/usr/bin/env python3
"""funder_freshness.py — Cambium per-funder governance corpus freshness checker.

Reads every governance/funders/*.yml file, validates required fields, and checks
staleness against freshness_window_days. Hard-fails (exit 1) on any blocker;
warns (exit 0) on approach to staleness or soft issues.

Hard FAIL (exit 1) conditions:
  - Required field missing or empty
  - Entry age > freshness_window_days (stale)
  - gate_mapping references a gate outside G0..G6
  - last_reviewed or source_date is unparseable or in the future
  - status is 'verify' on an active-mapped rule past its window

WARNING (exit 0) conditions:
  - Entry age > 75% of freshness_window_days (approaching staleness)
  - confidence: low or any field contains [VERIFY]
  - status: superseded still present

Usage:
    python3 tools/funder_freshness.py              # check all funders
    python3 tools/funder_freshness.py --path governance/funders/nih.yml  # one file

Importable API:
    from tools.funder_freshness import check_all, FreshnessResult

Exit: 0 on pass (with optional warnings), 1 on any hard fail.

Note: Uses stdlib only (no PyYAML dependency). Parses a strict subset of YAML
  sufficient for the Cambium funder corpus format (list of block-mapping entries).
"""
from __future__ import annotations

import argparse
import datetime
import glob
import os
import re
import sys
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FUNDERS_DIR = os.path.join(ROOT, "governance", "funders")

REQUIRED_FIELDS = [
    "funder",
    "rule_id",
    "summary",
    "rule_text_note",
    "source_url",
    "source_date",
    "gate_mapping",
    "last_reviewed",
    "reviewed_by",
    "review_cadence",
    "freshness_window_days",
    "status",
]

VALID_GATES = {"G0", "G1", "G2", "G3", "G3a", "G4", "G5", "G6"}
WARN_FRACTION = 0.75  # warn at 75% of window


# ---------------------------------------------------------------------------
# Minimal YAML parser (stdlib only, covers the corpus format)
# ---------------------------------------------------------------------------

def _parse_yaml_entries(text: str) -> List[Dict[str, Any]]:
    """Parse a YAML list-of-mappings using stdlib only.

    Handles the specific format used by governance/funders/*.yml:
      - Top-level list of block mappings (entries start with '- key: value')
      - Scalar string values (plain, single-quoted, double-quoted, block scalar >)
      - Nested gate_mapping list with sub-keys
      - Comment lines starting with '#'

    This is NOT a general YAML parser. It handles only the corpus format.
    Falls back to PyYAML if available for robustness.
    """
    # Try PyYAML first
    try:
        import yaml  # type: ignore
        entries = yaml.safe_load(text)
        if entries is None:
            return []
        if isinstance(entries, list):
            return entries
        return [entries]
    except ImportError:
        pass
    except Exception as e:
        raise ValueError(f"PyYAML parse error: {e}") from e

    # Stdlib fallback: line-by-line parser for the corpus format
    return _stdlib_yaml_parse(text)


def _stdlib_yaml_parse(text: str) -> List[Dict[str, Any]]:
    """Stdlib-only YAML parser for the Cambium funder corpus format."""
    entries: List[Dict[str, Any]] = []
    current: Optional[Dict[str, Any]] = None
    current_key: Optional[str] = None
    in_block_scalar = False
    block_scalar_lines: List[str] = []
    block_scalar_indent: int = 0
    in_gate_mapping = False
    current_gate: Optional[Dict[str, Any]] = None

    def flush_block_scalar():
        nonlocal current_key, block_scalar_lines, in_block_scalar
        if current is not None and current_key is not None:
            current[current_key] = " ".join(block_scalar_lines).strip()
        block_scalar_lines = []
        in_block_scalar = False
        current_key = None

    def flush_gate():
        nonlocal current_gate
        if current_gate and current:
            current.setdefault("gate_mapping", []).append(current_gate)
        current_gate = None

    lines = text.splitlines()
    i = 0
    while i < len(lines):
        raw = lines[i]
        stripped = raw.rstrip()
        content = stripped.lstrip()

        # Skip comments and empty lines
        if not content or content.startswith("#"):
            if in_block_scalar:
                flush_block_scalar()
            i += 1
            continue

        indent = len(raw) - len(raw.lstrip())

        # In block scalar mode: accumulate lines
        if in_block_scalar:
            if indent > block_scalar_indent or (indent == block_scalar_indent and not content.startswith("-") and ":" not in content[:30]):
                block_scalar_lines.append(content)
                i += 1
                continue
            else:
                flush_block_scalar()

        # New top-level entry
        if content.startswith("- ") and indent == 0:
            flush_gate()
            if current is not None:
                entries.append(current)
            current = {}
            in_gate_mapping = False
            current_gate = None
            rest = content[2:].strip()
            if rest and ":" in rest:
                key, _, val = rest.partition(":")
                key = key.strip()
                val = val.strip()
                if val.startswith(">"):
                    in_block_scalar = True
                    block_scalar_indent = indent + 2
                    current_key = key
                    block_scalar_lines = []
                elif val:
                    current[key] = _clean_value(val)
                    current_key = key
            i += 1
            continue

        # Sub-list item (gate_mapping entry)
        if content.startswith("- ") and indent >= 4:
            flush_gate()
            current_gate = {}
            rest = content[2:].strip()
            if rest and ":" in rest:
                key, _, val = rest.partition(":")
                key = key.strip()
                val = val.strip()
                if val.startswith(">"):
                    in_block_scalar = True
                    block_scalar_indent = indent + 4
                    current_key = f"__gate_{key}"
                    block_scalar_lines = []
                elif val:
                    current_gate[key] = _clean_value(val)
            i += 1
            continue

        # Key: value line
        if ":" in content and not content.startswith("-"):
            key, _, val = content.partition(":")
            key = key.strip()
            val = val.strip()

            # Detect gate_mapping section
            if key == "gate_mapping" and not val:
                in_gate_mapping = True
                i += 1
                continue

            # Gate sub-key
            if in_gate_mapping and indent >= 6 and current_gate is not None:
                if val.startswith(">"):
                    in_block_scalar = True
                    block_scalar_indent = indent + 2
                    current_key = f"__gate_{key}"
                    block_scalar_lines = []
                else:
                    current_gate[key] = _clean_value(val)
                i += 1
                continue

            # Regular top-level key
            if current is not None and indent <= 2:
                in_gate_mapping = False
                if val.startswith(">"):
                    in_block_scalar = True
                    block_scalar_indent = indent + 2
                    current_key = key
                    block_scalar_lines = []
                elif val:
                    current[key] = _clean_value(val)
                    current_key = key
                else:
                    current[key] = ""
                    current_key = key

        i += 1

    # Flush remaining
    if in_block_scalar:
        flush_block_scalar()
    flush_gate()
    if current is not None:
        entries.append(current)

    return entries


def _clean_value(val: str) -> Any:
    """Strip quotes, convert types for scalar YAML values."""
    # Remove inline comments
    if " #" in val:
        val = val[:val.index(" #")].strip()
    # Boolean
    if val.lower() in ("true", "yes"):
        return True
    if val.lower() in ("false", "no"):
        return False
    # Strip quotes
    if (val.startswith('"') and val.endswith('"')) or \
       (val.startswith("'") and val.endswith("'")):
        return val[1:-1]
    # Integer
    try:
        return int(val)
    except ValueError:
        pass
    # Float
    try:
        return float(val)
    except ValueError:
        pass
    return val


# ---------------------------------------------------------------------------
# Date helpers
# ---------------------------------------------------------------------------

def _parse_date(value: Any) -> Optional[datetime.date]:
    """Parse ISO date string; return None if unparseable."""
    if isinstance(value, datetime.date):
        return value
    s = str(value).strip().strip('"').strip("'")
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y"):
        try:
            return datetime.datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------

@dataclass
class EntryResult:
    file: str
    rule_id: str
    funder: str
    status: str  # "PASS" | "WARN" | "FAIL"
    blockers: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    age_days: Optional[int] = None
    window_days: Optional[int] = None


@dataclass
class FreshnessResult:
    files_checked: int
    entries_checked: int
    blockers: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    entry_results: List[EntryResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return len(self.blockers) == 0


# ---------------------------------------------------------------------------
# Entry checker
# ---------------------------------------------------------------------------

def _check_entry(
    entry: Dict[str, Any],
    file_path: str,
    today: datetime.date,
) -> EntryResult:
    """Check a single rule entry; return EntryResult."""
    rule_id = str(entry.get("rule_id", "UNKNOWN"))
    funder = str(entry.get("funder", "UNKNOWN"))
    result = EntryResult(
        file=file_path,
        rule_id=rule_id,
        funder=funder,
        status="PASS",
    )

    # 1. Required fields
    for field_name in REQUIRED_FIELDS:
        val = entry.get(field_name)
        if val is None or str(val).strip() == "":
            result.blockers.append(
                f"{rule_id}: required field '{field_name}' is missing or empty"
            )

    if result.blockers:
        result.status = "FAIL"
        return result

    # 2. Date validation: last_reviewed
    last_reviewed = _parse_date(entry["last_reviewed"])
    if last_reviewed is None:
        result.blockers.append(
            f"{rule_id}: 'last_reviewed' is unparseable: {entry['last_reviewed']!r}"
        )
        result.status = "FAIL"
        return result
    if last_reviewed > today:
        result.blockers.append(
            f"{rule_id}: 'last_reviewed' {last_reviewed} is in the future (today={today})"
        )

    # 3. Date validation: source_date
    source_date = _parse_date(entry["source_date"])
    if source_date is None:
        result.blockers.append(
            f"{rule_id}: 'source_date' is unparseable: {entry['source_date']!r}"
        )
        result.status = "FAIL"
        return result
    if source_date > today:
        result.blockers.append(
            f"{rule_id}: 'source_date' {source_date} is in the future (today={today})"
        )

    # 4. Freshness window
    try:
        window = int(entry["freshness_window_days"])
    except (ValueError, TypeError):
        result.blockers.append(
            f"{rule_id}: 'freshness_window_days' is not an integer: "
            f"{entry['freshness_window_days']!r}"
        )
        result.status = "FAIL"
        return result

    age = (today - last_reviewed).days
    result.age_days = age
    result.window_days = window

    if age > window:
        result.blockers.append(
            f"{rule_id}: STALE — age {age} days exceeds freshness_window_days {window}"
        )
    elif age > WARN_FRACTION * window:
        result.warnings.append(
            f"{rule_id}: approaching staleness — age {age} days "
            f"({age/window*100:.0f}% of {window}-day window)"
        )

    # 5. Gate mapping validation
    gate_mapping = entry.get("gate_mapping", [])
    if isinstance(gate_mapping, list):
        for gm in gate_mapping:
            if isinstance(gm, dict):
                gate = str(gm.get("gate", "")).strip()
                if gate and gate not in VALID_GATES:
                    result.blockers.append(
                        f"{rule_id}: gate_mapping references invalid gate "
                        f"'{gate}'; valid: {sorted(VALID_GATES)}"
                    )

    # 6. Status: 'verify' past window is a hard fail
    status_val = str(entry.get("status", "")).lower()
    if status_val == "verify" and age >= window:
        result.blockers.append(
            f"{rule_id}: status='verify' (known-unconfirmed) and entry is stale "
            f"(age={age}, window={window}) — must be resolved before use"
        )

    # 7. Warnings: confidence low, [VERIFY] markers, superseded
    confidence = str(entry.get("confidence", "")).lower()
    if confidence == "low":
        result.warnings.append(f"{rule_id}: confidence=low — escalate to PI before use")

    # Check for [VERIFY] in any string field
    for k, v in entry.items():
        if isinstance(v, str) and "[VERIFY]" in v:
            result.warnings.append(
                f"{rule_id}: field '{k}' contains [VERIFY] marker — "
                "human re-verification required"
            )

    if status_val == "superseded":
        result.warnings.append(
            f"{rule_id}: status='superseded' — consider removing from corpus"
        )

    if result.blockers:
        result.status = "FAIL"
    elif result.warnings:
        result.status = "WARN"

    return result


# ---------------------------------------------------------------------------
# File checker
# ---------------------------------------------------------------------------

def check_file(
    path: str,
    today: Optional[datetime.date] = None,
) -> Tuple[List[EntryResult], List[str]]:
    """Check a single YAML funder file; return (entry_results, file_level_errors)."""
    if today is None:
        today = datetime.date.today()

    file_errors: List[str] = []
    try:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    except OSError as e:
        file_errors.append(f"Cannot read {path}: {e}")
        return [], file_errors

    try:
        entries = _parse_yaml_entries(text)
    except Exception as e:
        file_errors.append(f"YAML parse error in {path}: {e}")
        return [], file_errors

    if not entries:
        file_errors.append(f"{path}: no entries found (empty or unreadable YAML)")
        return [], file_errors

    results = []
    for entry in entries:
        if not isinstance(entry, dict):
            file_errors.append(f"{path}: entry is not a dict: {type(entry)}")
            continue
        er = _check_entry(entry, path, today)
        results.append(er)

    return results, file_errors


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def check_all(
    funders_dir: Optional[str] = None,
    today: Optional[datetime.date] = None,
) -> FreshnessResult:
    """Check all *.yml files in funders_dir; return FreshnessResult."""
    if funders_dir is None:
        funders_dir = FUNDERS_DIR
    if today is None:
        today = datetime.date.today()

    result = FreshnessResult(files_checked=0, entries_checked=0)

    yml_files = sorted(glob.glob(os.path.join(funders_dir, "*.yml")))
    if not yml_files:
        result.blockers.append(
            f"No *.yml files found in {funders_dir} — corpus is empty"
        )
        return result

    for path in yml_files:
        result.files_checked += 1
        entry_results, file_errors = check_file(path, today)
        result.entry_results.extend(entry_results)
        result.entries_checked += len(entry_results)
        for fe in file_errors:
            result.blockers.append(fe)
        for er in entry_results:
            result.blockers.extend(er.blockers)
            result.warnings.extend(er.warnings)

    return result


# ---------------------------------------------------------------------------
# CLI output
# ---------------------------------------------------------------------------

def _print_results(result: FreshnessResult, quiet: bool = False) -> None:
    """Print a formatted summary of freshness check results."""
    print("[funder_freshness] Cambium per-funder governance corpus check")
    print(f"  Files checked:   {result.files_checked}")
    print(f"  Entries checked: {result.entries_checked}")

    if not quiet:
        for er in result.entry_results:
            status_icon = {"PASS": "ok  ", "WARN": "WARN", "FAIL": "FAIL"}.get(er.status, "?   ")
            age_info = ""
            if er.age_days is not None and er.window_days is not None:
                age_info = f"  (age={er.age_days}d / window={er.window_days}d)"
            print(f"  {status_icon}  {er.funder}/{er.rule_id}{age_info}")

    if result.warnings:
        print(f"\n  WARNINGS ({len(result.warnings)}):")
        for w in result.warnings:
            print(f"    ! {w}")

    if result.blockers:
        print(f"\n  BLOCKERS ({len(result.blockers)}) — HARD FAIL:")
        for b in result.blockers:
            print(f"    X {b}")
        print("\n[funder_freshness] -> FAILED.")
    else:
        print(f"\n[funder_freshness] OK: all {result.entries_checked} "
              f"entries pass freshness check.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Cambium funder corpus freshness checker. Exit 1 on hard fail.",
    )
    parser.add_argument(
        "--path",
        metavar="FILE",
        help="Check a single YAML file instead of all files in governance/funders/.",
    )
    parser.add_argument(
        "--funders-dir",
        metavar="DIR",
        default=FUNDERS_DIR,
        help=f"Directory containing *.yml funder files (default: {FUNDERS_DIR}).",
    )
    parser.add_argument(
        "--date",
        metavar="YYYY-MM-DD",
        help="Override today's date for testing (ISO format).",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress per-entry status lines; show only summary and blockers.",
    )
    args = parser.parse_args(argv)

    today: Optional[datetime.date] = None
    if args.date:
        today = _parse_date(args.date)
        if today is None:
            print(f"ERROR: --date value {args.date!r} is not a valid ISO date.",
                  file=sys.stderr)
            return 1

    if args.path:
        # Single-file mode
        entry_results, file_errors = check_file(args.path, today)
        result = FreshnessResult(
            files_checked=1,
            entries_checked=len(entry_results),
            entry_results=entry_results,
        )
        for fe in file_errors:
            result.blockers.append(fe)
        for er in entry_results:
            result.blockers.extend(er.blockers)
            result.warnings.extend(er.warnings)
    else:
        result = check_all(funders_dir=args.funders_dir, today=today)

    _print_results(result, quiet=args.quiet)
    return 0 if result.passed else 1


if __name__ == "__main__":
    sys.exit(main())
