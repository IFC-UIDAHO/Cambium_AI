#!/usr/bin/env python3
"""coverage_map -- tool-to-test coverage map for tools/*.py.

For every tools/*.py file (excluding __init__.py; cambium_io.py IS included -- it is a real
module other tools import and deserves the same coverage question), finds a covering test by
either rule:

  1. filename match  -- tests/test_<toolname>.py exists
  2. content match    -- any tests/*.py file contains the tool's module name as a whole word
                          (so tests that exercise several tools together, e.g. test_framework.py
                          checking many modules, still count as coverage)

Reports a table (tool, covered-by or MISSING), totals, and a percentage.

Exit codes:
  0  default -- advisory, always exits 0 regardless of coverage (unless --min-coverage is given)
  1  --min-coverage N given and computed percentage is below N

Usage:
  python3 tools/coverage_map.py
  python3 tools/coverage_map.py --tools-dir tools --tests-dir tests
  python3 tools/coverage_map.py --min-coverage 80
  python3 tools/coverage_map.py --json
"""
from __future__ import annotations
import argparse
import glob
import json
import os
import re
import sys

import cambium_io  # noqa: F401 -- UTF-8 stdout/stderr guard on Windows

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_TOOLS_DIR = os.path.join(ROOT, "tools")
DEFAULT_TESTS_DIR = os.path.join(ROOT, "tests")

SKIP_NAMES = {"__init__.py"}


def discover_tools(tools_dir: str) -> list:
    """Sorted list of tool module names (filename without .py), excluding __init__."""
    names = []
    for p in sorted(glob.glob(os.path.join(tools_dir, "*.py"))):
        base = os.path.basename(p)
        if base in SKIP_NAMES:
            continue
        names.append(base[:-3])
    return names


def _test_files(tests_dir: str) -> list:
    return sorted(glob.glob(os.path.join(tests_dir, "*.py")))


def find_covering_tests(tool_name: str, tests_dir: str, test_files: list) -> list:
    """Return a list of test file basenames that cover tool_name, via filename match or
    whole-word content match. Empty list means MISSING."""
    covering = []
    filename_match = os.path.join(tests_dir, f"test_{tool_name}.py")
    if os.path.exists(filename_match):
        covering.append(os.path.basename(filename_match))

    word_re = re.compile(r"\b" + re.escape(tool_name) + r"\b")
    for tf in test_files:
        base = os.path.basename(tf)
        if base in covering:
            continue
        try:
            with open(tf, encoding="utf-8", errors="replace") as fh:
                content = fh.read()
        except OSError:
            continue
        if word_re.search(content):
            covering.append(base)
    return covering


def build_report(tools_dir: str, tests_dir: str) -> dict:
    tool_names = discover_tools(tools_dir)
    test_files = _test_files(tests_dir)
    rows = []
    covered_n = 0
    for name in tool_names:
        covering = find_covering_tests(name, tests_dir, test_files)
        if covering:
            covered_n += 1
        rows.append({"tool": name, "covered_by": covering})
    total = len(tool_names)
    pct = round(100.0 * covered_n / total, 1) if total else 0.0
    return {
        "tools_dir": tools_dir,
        "tests_dir": tests_dir,
        "rows": rows,
        "total": total,
        "covered": covered_n,
        "missing": total - covered_n,
        "percentage": pct,
    }


def render_text(report: dict) -> str:
    lines = [f"[coverage_map] {report['tools_dir']} vs {report['tests_dir']}", ""]
    width = max((len(r["tool"]) for r in report["rows"]), default=4)
    for r in report["rows"]:
        status = ", ".join(r["covered_by"]) if r["covered_by"] else "MISSING"
        lines.append(f"  {r['tool'].ljust(width)}  {status}")
    lines.append("")
    lines.append(f"[coverage_map] {report['covered']}/{report['total']} tools covered "
                 f"({report['percentage']}%), {report['missing']} missing")
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Report tool-to-test coverage for tools/*.py.")
    ap.add_argument("--tools-dir", default=DEFAULT_TOOLS_DIR, help="Directory of tool modules.")
    ap.add_argument("--tests-dir", default=DEFAULT_TESTS_DIR, help="Directory of test files.")
    ap.add_argument("--min-coverage", type=float, default=None,
                     help="Percent threshold; exit 1 if computed coverage is below this.")
    ap.add_argument("--json", action="store_true", help="Print a JSON report instead of text.")
    args = ap.parse_args(argv)

    report = build_report(args.tools_dir, args.tests_dir)

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(render_text(report))

    if args.min_coverage is not None and report["percentage"] < args.min_coverage:
        print(f"[coverage_map] BELOW THRESHOLD: {report['percentage']}% < {args.min_coverage}%",
              file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
