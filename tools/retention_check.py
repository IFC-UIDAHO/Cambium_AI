#!/usr/bin/env python3
"""retention_check -- data-retention scan.

ADVISORY, NEVER DELETES. Scans a directory against a retention policy (glob patterns with
a max age in days) and reports files that exceed the age their FIRST matching pattern
allows, plus files over a size ceiling. This is a report for a human data steward to act
on; it makes zero filesystem writes to the scanned directory (verified by tests: the
directory's file list and mtimes are identical before and after a run).

If tools/pii_screen.py exposes a usable scan() function, this tool runs it on flagged
.txt/.csv/.md files and marks a pii-suspect column. It degrades to "pii-check: unavailable"
if pii_screen cannot be imported or its interface differs from what this tool expects.

Usage:
  python3 tools/retention_check.py --dir DATA_DIR --policy policy.json [--today 2026-07-01]
                                    [--max-mb 100] [--out agent_outputs/retention_report]

policy.json: a list of {"pattern": glob, "max_age_days": int, "note": str}. The FIRST
pattern (in list order) that fnmatches a file's basename wins; later patterns are ignored
for that file.

Exit: 0 on a normal run (even with flags -- this is advisory). 1 on a bad --policy file.
"""
from __future__ import annotations
import argparse
import fnmatch
import importlib
import json
import os
import sys
from datetime import date, datetime, timezone

import cambium_io  # noqa: F401 -- reconfigures stdout/stderr to UTF-8 on Windows

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_MAX_MB = 100
PII_SCANNABLE_EXT = (".txt", ".csv", ".md")


def _load_policy(path: str) -> list:
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, list):
        raise ValueError("policy JSON must be a list of {pattern, max_age_days, note}")
    for rule in data:
        if "pattern" not in rule or "max_age_days" not in rule:
            raise ValueError("each policy rule needs 'pattern' and 'max_age_days': %r" % rule)
    return data


def _first_match(basename: str, policy: list):
    """Return the first policy rule (in list order) whose pattern matches, or None."""
    for rule in policy:
        if fnmatch.fnmatch(basename, rule["pattern"]):
            return rule
    return None


def _load_pii_screen():
    """Try to import tools.pii_screen and confirm it has a usable scan(text) -> (findings, engine).
    Returns the module or None if unavailable / interface mismatch."""
    try:
        sys.path.insert(0, os.path.join(ROOT, "tools"))
        mod = importlib.import_module("pii_screen")
        if not hasattr(mod, "scan") or not callable(mod.scan):
            return None
        return mod
    except Exception:
        return None


def scan_directory(root_dir: str, policy: list, today: date, max_mb: float) -> list:
    """Walk root_dir, return a list of flag dicts. Read-only: no writes, no deletes."""
    flags = []
    max_bytes = max_mb * 1024 * 1024
    for dirpath, _dirnames, filenames in os.walk(root_dir):
        for fname in sorted(filenames):
            fpath = os.path.join(dirpath, fname)
            try:
                st = os.stat(fpath)
            except OSError:
                continue
            rel = os.path.relpath(fpath, root_dir)
            age_days = (today - datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).date()).days
            size_bytes = st.st_size

            rule = _first_match(fname, policy)
            reasons = []
            if rule and age_days > rule["max_age_days"]:
                reasons.append("age %dd > policy max %dd (pattern %s: %s)" % (
                    age_days, rule["max_age_days"], rule["pattern"], rule.get("note", "")))
            if size_bytes > max_bytes:
                reasons.append("oversized %.1fMB > %.1fMB ceiling" % (size_bytes / (1024 * 1024), max_mb))
            if reasons:
                flags.append({
                    "path": rel,
                    "age_days": age_days,
                    "size_bytes": size_bytes,
                    "matched_pattern": rule["pattern"] if rule else None,
                    "reasons": reasons,
                    "pii_suspect": None,  # filled in by apply_pii_screen if available
                })
    return flags


def apply_pii_screen(flags: list, root_dir: str) -> str:
    """Mutates flags in place with a pii_suspect bool for scannable extensions.
    Returns a status string describing what happened."""
    mod = _load_pii_screen()
    if mod is None:
        for f in flags:
            f["pii_suspect"] = "pii-check: unavailable"
        return "pii-check: unavailable"
    for f in flags:
        _, ext = os.path.splitext(f["path"])
        if ext.lower() not in PII_SCANNABLE_EXT:
            f["pii_suspect"] = "n/a (not a scannable text type)"
            continue
        try:
            text = open(os.path.join(root_dir, f["path"]), encoding="utf-8", errors="replace").read()
            findings, _engine = mod.scan(text)
            f["pii_suspect"] = "yes (%d finding(s))" % len(findings) if findings else "no"
        except Exception:
            f["pii_suspect"] = "pii-check: error on this file"
    return "pii-check: ran via tools/pii_screen.py"


def render_markdown(flags: list, root_dir: str, today: date, max_mb: float, pii_status: str) -> str:
    lines = ["# Data retention scan (advisory -- never deletes)", ""]
    lines.append("> ADVISORY: this report flags candidates for a human data steward to review and "
                  "act on. It never deletes or modifies scanned files.")
    lines.append("")
    lines.append("**Scanned:** `%s` &nbsp; **As of:** %s &nbsp; **Oversized ceiling:** %.1f MB &nbsp; **%s**" % (
        root_dir, today.isoformat(), max_mb, pii_status))
    lines.append("")
    lines.append("**Flagged files:** %d" % len(flags))
    lines.append("")
    if flags:
        lines.append("| Path | Age (days) | Size (bytes) | Pattern | PII suspect | Reasons |")
        lines.append("|---|---|---|---|---|---|")
        for f in flags:
            lines.append("| %s | %d | %d | %s | %s | %s |" % (
                f["path"], f["age_days"], f["size_bytes"], f["matched_pattern"] or "-",
                f["pii_suspect"] or "-", "; ".join(f["reasons"])))
    else:
        lines.append("No files exceeded their retention policy or the size ceiling.")
    return "\n".join(lines)


def _write(path: str, content: str) -> None:
    d = os.path.dirname(os.path.abspath(path))
    if d:
        os.makedirs(d, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--dir", required=True, help="Directory to scan.")
    ap.add_argument("--policy", required=True, help="Path to a retention policy JSON file.")
    ap.add_argument("--today", default=None, help="Override 'today' as YYYY-MM-DD, for determinism.")
    ap.add_argument("--max-mb", type=float, default=DEFAULT_MAX_MB, help="Oversized ceiling in MB (default 100).")
    ap.add_argument("--out", default=None, help="Output path stem (writes .md and .json; default agent_outputs/retention_report).")
    args = ap.parse_args(argv)

    try:
        policy = _load_policy(args.policy)
    except (OSError, ValueError, json.JSONDecodeError) as e:
        print("[retention_check] ERROR: bad policy file: %s" % e, file=sys.stderr)
        return 1

    today = date.fromisoformat(args.today) if args.today else date.today()

    if not os.path.isdir(args.dir):
        print("[retention_check] ERROR: --dir not found: %s" % args.dir, file=sys.stderr)
        return 1

    flags = scan_directory(args.dir, policy, today, args.max_mb)
    pii_status = apply_pii_screen(flags, args.dir)

    stem = args.out or os.path.join(ROOT, "agent_outputs", "retention_report")
    md_path, json_path = stem + ".md", stem + ".json"
    report = render_markdown(flags, args.dir, today, args.max_mb, pii_status)
    _write(md_path, report)
    _write(json_path, json.dumps({"scanned_dir": args.dir, "as_of": today.isoformat(),
                                   "max_mb": args.max_mb, "pii_status": pii_status,
                                   "flags": flags}, indent=2))
    print(report)
    print("\n[retention_check] wrote %s and %s" % (md_path, json_path))
    return 0


if __name__ == "__main__":
    sys.exit(main())
