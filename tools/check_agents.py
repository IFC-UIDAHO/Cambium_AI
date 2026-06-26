#!/usr/bin/env python3
"""Agent frontmatter validator for the Cambium.

Scans .claude/agents/*.md and asserts that every agent has valid YAML frontmatter:
  - name        (required, non-empty string)
  - description (required, non-empty string)
  - model       (required; one of: inherit / opus / sonnet / haiku)
  - tools       (required, non-empty string or list)
  - names must be unique across all agents

Dependency-free (stdlib only).  Exits non-zero on any problem.

Usage:  python3 tools/check_agents.py [path/to/.claude/agents/]
"""

import sys
import os
import re
import glob

AGENTS_DIR = sys.argv[1] if len(sys.argv) > 1 else ".claude/agents"
VALID_MODELS = {"inherit", "opus", "sonnet", "haiku"}


def parse_frontmatter(path):
    """Return the key:value pairs from a --- fenced YAML frontmatter block, or None."""
    with open(path, encoding="utf-8") as fh:
        content = fh.read()
    # Must start (after optional BOM) with ---
    stripped = content.lstrip("﻿").lstrip()
    if not stripped.startswith("---"):
        return None
    # Find closing ---
    rest = stripped[3:]
    end = rest.find("\n---")
    if end == -1:
        return None
    fm_block = rest[:end]
    data = {}
    for line in fm_block.splitlines():
        # Simple key: value parser (no nested YAML needed)
        m = re.match(r"^(\w[\w-]*):\s*(.*)$", line)
        if m:
            key, val = m.group(1).strip(), m.group(2).strip()
            # Strip inline comments
            val = re.sub(r"\s+#.*$", "", val).strip()
            data[key] = val
    return data


def main():
    pattern = os.path.join(AGENTS_DIR, "*.md")
    files = sorted(glob.glob(pattern))
    if not files:
        print("[check_agents] ERROR: no agent files found under {!r}".format(AGENTS_DIR))
        return 1

    errors = []
    seen_names = {}   # name -> first file that used it
    valid_count = 0

    for path in files:
        base = os.path.basename(path)
        fm = parse_frontmatter(path)

        if fm is None:
            errors.append("  {}: missing or malformed YAML frontmatter (no --- block)".format(base))
            continue

        file_ok = True

        name = fm.get("name", "").strip()
        if not name:
            errors.append("  {}: 'name' is missing or empty".format(base))
            file_ok = False

        description = fm.get("description", "").strip()
        if not description:
            errors.append("  {}: 'description' is missing or empty".format(base))
            file_ok = False

        model = fm.get("model", "").strip().lower()
        if not model:
            errors.append("  {}: 'model' is missing or empty".format(base))
            file_ok = False
        elif model not in VALID_MODELS:
            errors.append(
                "  {}: 'model' is {!r} — must be one of {}".format(base, model, sorted(VALID_MODELS))
            )
            file_ok = False

        tools = fm.get("tools", "").strip()
        if not tools:
            errors.append("  {}: 'tools' is missing or empty".format(base))
            file_ok = False

        # Uniqueness check
        if name:
            if name in seen_names:
                errors.append(
                    "  {}: duplicate name {!r} (first seen in {})".format(base, name, seen_names[name])
                )
                file_ok = False
            else:
                seen_names[name] = base

        if file_ok:
            valid_count += 1

    total = len(files)
    print("[check_agents] scanned {} agent file(s) in {!r}".format(total, AGENTS_DIR))
    print("[check_agents] valid: {} / {}".format(valid_count, total))

    if errors:
        print("[check_agents] ERRORS ({}):".format(len(errors)))
        print("\n".join(errors))
        print("[check_agents] FAILED — fix the errors above before pushing.")
        return 1

    print("[check_agents] OK — all {} agents have valid frontmatter, names are unique.".format(valid_count))
    return 0


if __name__ == "__main__":
    sys.exit(main())
