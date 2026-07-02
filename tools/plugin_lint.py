#!/usr/bin/env python3
"""plugin_lint -- lint a Cambium extension directory (a third-party plugin layout).

Standalone linter for any directory laid out like a Cambium plugin: agents/*.md,
.claude/agents/*.md, skills/*/SKILL.md, and an optional .claude-plugin/plugin.json. Does not
import tools/check_agents.py -- the minimal frontmatter-parsing logic is copied here so this
linter works on a directory outside the Cambium repo, with no dependency on repo layout.

Checks:
  - every agents/*.md and .claude/agents/*.md has frontmatter with name, description, model
    (in the allowed set: inherit, opus, sonnet, haiku), tools
  - agent names are unique across the whole directory
  - every skills/*/SKILL.md has frontmatter name + non-empty description
  - .claude-plugin/plugin.json (if present) parses as JSON and has a semver "version" field

Cambium's real roster stores each agent twice by convention: .claude/agents/<file>.md and
agents/<file>.md are meant to be identical mirrors (see tools/sync_plugin_agents.py), so a
mirror pair sharing the same filename is NOT treated as a name collision. Two files with
DIFFERENT filenames that declare the same frontmatter name are still flagged -- that is a real
collision.

Output: a human-readable report by default; --json prints a machine-readable report instead.
Exit codes:
  0  no violations
  1  one or more violations found

Usage:
  python3 tools/plugin_lint.py /path/to/plugin-dir
  python3 tools/plugin_lint.py /path/to/plugin-dir --json
"""
from __future__ import annotations
import argparse
import glob
import json
import os
import re
import sys

import cambium_io  # noqa: F401 -- UTF-8 stdout/stderr guard on Windows

VALID_MODELS = {"inherit", "opus", "sonnet", "haiku"}
_SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+([-+].+)?$")


def parse_frontmatter(path: str):
    """Return the key:value pairs from a --- fenced YAML frontmatter block, or None.

    Deliberately the same minimal parser as tools/check_agents.py, copied (not imported) so
    this tool has zero dependency on the Cambium repo it may be run against.
    """
    with open(path, encoding="utf-8") as fh:
        content = fh.read()
    stripped = content.lstrip("﻿").lstrip()
    if not stripped.startswith("---"):
        return None
    rest = stripped[3:]
    end = rest.find("\n---")
    if end == -1:
        return None
    fm_block = rest[:end]
    data = {}
    for line in fm_block.splitlines():
        m = re.match(r"^(\w[\w-]*):\s*(.*)$", line)
        if m:
            key, val = m.group(1).strip(), m.group(2).strip()
            val = re.sub(r"\s+#.*$", "", val).strip()
            data[key] = val
    return data


def _agent_files(plugin_dir: str):
    found = []
    for sub in (os.path.join(".claude", "agents"), "agents"):
        for p in sorted(glob.glob(os.path.join(plugin_dir, sub, "*.md"))):
            if os.path.basename(p).upper() != "README.MD":
                found.append(p)
    return found


def _skill_files(plugin_dir: str):
    return sorted(glob.glob(os.path.join(plugin_dir, "skills", "*", "SKILL.md")))


def lint_agents(plugin_dir: str):
    """Return (violations: list[str], checked: int)."""
    violations = []
    seen_names = {}   # declared name -> basename of the first file that used it
    files = _agent_files(plugin_dir)
    for path in files:
        rel = os.path.relpath(path, plugin_dir)
        base = os.path.basename(path)
        fm = parse_frontmatter(path)
        if fm is None:
            violations.append(f"{rel}: missing or malformed YAML frontmatter")
            continue
        name = fm.get("name", "").strip()
        if not name:
            violations.append(f"{rel}: 'name' is missing or empty")
        description = fm.get("description", "").strip()
        if not description:
            violations.append(f"{rel}: 'description' is missing or empty")
        model = fm.get("model", "").strip().lower()
        if not model:
            violations.append(f"{rel}: 'model' is missing or empty")
        elif model not in VALID_MODELS:
            violations.append(f"{rel}: 'model' is {model!r}, must be one of {sorted(VALID_MODELS)}")
        tools = fm.get("tools", "").strip()
        if not tools:
            violations.append(f"{rel}: 'tools' is missing or empty")
        if name:
            if name in seen_names and seen_names[name] != base:
                violations.append(
                    f"{rel}: duplicate agent name {name!r} (also used by a differently named "
                    f"file: {seen_names[name]})")
            else:
                seen_names[name] = base
    return violations, len(files)


def lint_skills(plugin_dir: str):
    """Return (violations: list[str], checked: int)."""
    violations = []
    files = _skill_files(plugin_dir)
    for path in files:
        rel = os.path.relpath(path, plugin_dir)
        fm = parse_frontmatter(path)
        if fm is None:
            violations.append(f"{rel}: missing or malformed YAML frontmatter")
            continue
        if not fm.get("name", "").strip():
            violations.append(f"{rel}: 'name' is missing or empty")
        if not fm.get("description", "").strip():
            violations.append(f"{rel}: 'description' is missing or empty")
    return violations, len(files)


def lint_plugin_json(plugin_dir: str):
    """Return (violations: list[str], checked: int). checked is 0 if the file is absent
    (its presence is optional)."""
    path = os.path.join(plugin_dir, ".claude-plugin", "plugin.json")
    if not os.path.exists(path):
        return [], 0
    rel = os.path.relpath(path, plugin_dir)
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except (json.JSONDecodeError, OSError) as exc:
        return [f"{rel}: does not parse as JSON ({exc})"], 1
    version = str(data.get("version", ""))
    if not _SEMVER_RE.match(version):
        return [f"{rel}: 'version' {version!r} is not valid semver (expected MAJOR.MINOR.PATCH)"], 1
    return [], 1


def lint(plugin_dir: str) -> dict:
    """Run every check; return a report dict (violations, counts, ok)."""
    agent_v, agent_n = lint_agents(plugin_dir)
    skill_v, skill_n = lint_skills(plugin_dir)
    plugin_v, plugin_n = lint_plugin_json(plugin_dir)
    violations = agent_v + skill_v + plugin_v
    return {
        "plugin_dir": plugin_dir,
        "agents_checked": agent_n,
        "skills_checked": skill_n,
        "plugin_json_checked": plugin_n,
        "violations": violations,
        "ok": len(violations) == 0,
    }


def render_text(report: dict) -> str:
    lines = [f"[plugin_lint] {report['plugin_dir']}",
             f"[plugin_lint] agents checked: {report['agents_checked']}  "
             f"skills checked: {report['skills_checked']}  "
             f"plugin.json checked: {report['plugin_json_checked']}"]
    if report["violations"]:
        lines.append(f"[plugin_lint] {len(report['violations'])} VIOLATION(s):")
        for v in report["violations"]:
            lines.append("  " + v)
        lines.append("[plugin_lint] FAILED.")
    else:
        lines.append("[plugin_lint] OK -- no violations.")
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Lint a Cambium extension (plugin) directory.")
    ap.add_argument("plugin_dir", help="Path to the plugin directory to lint.")
    ap.add_argument("--json", action="store_true", help="Print a JSON report instead of text.")
    args = ap.parse_args(argv)

    plugin_dir = os.path.abspath(args.plugin_dir)
    if not os.path.isdir(plugin_dir):
        print(f"[plugin_lint] ERROR: not a directory: {plugin_dir}", file=sys.stderr)
        return 1

    report = lint(plugin_dir)

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(render_text(report))

    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
