#!/usr/bin/env python3
"""plugin_smoke.py -- packaging smoke test for the Cambium plugin.

Checks, against --root (default: this repo):
  1. .claude-plugin/plugin.json parses and carries name + version.
  2. That version matches pyproject.toml and mcp_server/pyproject.toml.
  3. Exactly one plugin.json exists in the tree (scratch dirs excluded).
  4. Every path in plugin.json documentation[] resolves: tried as-is from
     root, then docs/<path>, then docs/**/<basename>; the resolved location
     is reported (this repo keeps those files sorted under docs/ subfolders).
  5. agents/*.md and .claude/agents/*.md are the same file set (names).
  6. Every skills/*/SKILL.md has frontmatter with non-empty name + description.

Usage:
    python3 tools/plugin_smoke.py [--root DIR]

Exit 0 when every check passes; exit 1 on any FAIL.

Honest limits:
    - Frontmatter is parsed line-by-line (same approach as
      tools/check_agents.py) because the repo's skill descriptions contain
      colons that a strict YAML parser rejects; this verifies presence of the
      fields, not full YAML validity.
    - The single-plugin.json walk skips .git, node_modules, __pycache__ and
      virtualenv dirs so a dev machine does not fail on vendored packages.
    - When a documentation[] entry is matched by basename under docs/, the
      first match in sorted order is reported; duplicates are not flagged.
"""

import argparse
import glob
import json
import os
import re
import sys

import cambium_io  # noqa: F401

SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv"}
VERSION_RE = re.compile(r'(?m)^version\s*=\s*"([^"]+)"')
FM_LINE = re.compile(r"^(\w[\w-]*):\s*(.*)$")


def repo_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def parse_frontmatter(text: str):
    """Line-based frontmatter parse; returns a dict or None (no --- block)."""
    stripped = text.lstrip("﻿").lstrip()
    if not stripped.startswith("---"):
        return None
    rest = stripped[3:]
    end = rest.find("\n---")
    if end == -1:
        return None
    data = {}
    for line in rest[:end].splitlines():
        m = FM_LINE.match(line)
        if m:
            data[m.group(1)] = m.group(2).strip()
    return data


def read_version(path: str):
    """First version = "x.y.z" in a pyproject-style file, or None."""
    if not os.path.isfile(path):
        return None
    m = VERSION_RE.search(open(path, encoding="utf-8", errors="replace").read())
    return m.group(1) if m else None


def find_plugin_jsons(root: str):
    hits = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        if "plugin.json" in filenames:
            hits.append(os.path.relpath(os.path.join(dirpath, "plugin.json"), root))
    return sorted(hits)


def resolve_doc(root: str, entry: str):
    """Resolve a documentation[] entry; returns the relative path or None."""
    cand = os.path.join(root, entry)
    if os.path.isfile(cand):
        return entry
    cand = os.path.join(root, "docs", entry)
    if os.path.isfile(cand):
        return os.path.relpath(cand, root)
    base = os.path.basename(entry)
    matches = sorted(
        p for p in glob.glob(os.path.join(root, "docs", "**", base), recursive=True)
        if os.path.isfile(p)
    )
    if matches:
        return os.path.relpath(matches[0], root)
    return None


def md_names(dirpath: str):
    if not os.path.isdir(dirpath):
        return None
    return {os.path.basename(p) for p in glob.glob(os.path.join(dirpath, "*.md"))}


def run_checks(root: str):
    """Return a list of (passed, check_name, detail) tuples."""
    checks = []

    # 1. plugin.json parses
    plugin = None
    plugin_path = os.path.join(root, ".claude-plugin", "plugin.json")
    try:
        with open(plugin_path, encoding="utf-8") as fh:
            plugin = json.load(fh)
        name = plugin.get("name", "")
        version = plugin.get("version", "")
        if name and version:
            checks.append((True, "plugin-json", "name=%s version=%s" % (name, version)))
        else:
            checks.append((False, "plugin-json", "parsed but name/version missing or empty"))
    except Exception as exc:
        checks.append((False, "plugin-json", "%s: %s" % (plugin_path, exc)))

    # 2. version match across plugin.json, pyproject.toml, mcp_server/pyproject.toml
    pv = (plugin or {}).get("version")
    rv = read_version(os.path.join(root, "pyproject.toml"))
    mv = read_version(os.path.join(root, "mcp_server", "pyproject.toml"))
    detail = "plugin=%s root-pyproject=%s mcp-pyproject=%s" % (pv, rv, mv)
    checks.append((bool(pv) and pv == rv == mv, "version-match", detail))

    # 3. exactly one plugin.json in the tree
    hits = find_plugin_jsons(root)
    checks.append((len(hits) == 1, "single-plugin-json",
                   "%d found: %s" % (len(hits), ", ".join(hits[:4]) or "none")))

    # 4. documentation[] entries exist
    doc_entries = (plugin or {}).get("documentation") or []
    if not doc_entries:
        checks.append((True, "docs-exist", "no documentation[] entries listed"))
    else:
        resolved, missing = [], []
        for entry in doc_entries:
            rel = resolve_doc(root, entry)
            if rel is None:
                missing.append(entry)
            else:
                resolved.append("%s -> %s" % (entry, rel))
        if missing:
            checks.append((False, "docs-exist", "missing: " + ", ".join(missing)))
        else:
            checks.append((True, "docs-exist", "; ".join(resolved)))

    # 5. agents/ mirrors .claude/agents/
    a = md_names(os.path.join(root, "agents"))
    b = md_names(os.path.join(root, ".claude", "agents"))
    if a is None or b is None:
        checks.append((False, "agents-mirrored",
                       "missing dir: %s" % ("agents/" if a is None else ".claude/agents/")))
    elif a == b:
        checks.append((True, "agents-mirrored", "%d cards in both trees" % len(a)))
    else:
        diff = sorted(a.symmetric_difference(b))
        checks.append((False, "agents-mirrored",
                       "out of sync (%d differ): %s" % (len(diff), ", ".join(diff[:6]))))

    # 6. every skills/*/SKILL.md has frontmatter name + description
    skill_files = sorted(glob.glob(os.path.join(root, "skills", "*", "SKILL.md")))
    if not skill_files:
        checks.append((True, "skills-frontmatter", "no skills/*/SKILL.md found (nothing to check)"))
    else:
        offenders = []
        for path in skill_files:
            fm = parse_frontmatter(open(path, encoding="utf-8", errors="replace").read())
            if not fm or not fm.get("name", "").strip() or not fm.get("description", "").strip():
                offenders.append(os.path.relpath(path, root))
        if offenders:
            checks.append((False, "skills-frontmatter",
                           "missing name/description: " + ", ".join(offenders[:6])))
        else:
            checks.append((True, "skills-frontmatter",
                           "%d skills carry name + description" % len(skill_files)))

    return checks


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Packaging smoke test for the Cambium plugin.")
    ap.add_argument("--root", default=repo_root(), help="repo root to check (default: this repo)")
    args = ap.parse_args(argv)

    root = os.path.abspath(args.root)
    if not os.path.isdir(root):
        print("[plugin_smoke] ERROR: --root is not a directory: " + root, file=sys.stderr)
        return 1

    checks = run_checks(root)
    print("== plugin_smoke: %s ==" % root)
    for passed, name, detail in checks:
        print(" %-4s  %-20s %s" % ("PASS" if passed else "FAIL", name, detail))
    failed = sum(1 for passed, _, _ in checks if not passed)
    print("plugin_smoke: %d checks, %d failed" % (len(checks), failed))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
