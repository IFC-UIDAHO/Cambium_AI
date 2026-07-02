#!/usr/bin/env python3
"""new_skill.py -- scaffold a Cambium skill folder (skills/<name>/SKILL.md).

Creates skills/<name>/SKILL.md with the frontmatter the plugin listing needs
(name + description) and an honest body skeleton (What this does, When to use,
How, Honest limits).

Usage:
    python3 tools/new_skill.py --name forest-inventory \
        --description "Plan and check forest inventory sampling designs, plot layout, and expansion factors." \
        [--root DIR] [--force]

Lints enforced before writing (exit 1 on violation):
    - name is kebab-case and becomes the directory name (so they always match)
    - description is one line, at least 40 characters, and has no em dash
      (a too-short description makes the plugin listing useless)

Honest limits:
    - Scaffolds one SKILL.md; the plugin discovers skills/ by directory scan,
      so nothing else is registered.
    - The description is written unquoted on one line, matching every existing
      skill card in this repo; strict YAML parsers may reject colons inside it,
      exactly as they would for the existing cards.
    - The body is a TODO skeleton; a human must fill in real guidance.
"""

import argparse
import os
import re
import sys

import cambium_io  # noqa: F401

KEBAB = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
EM_DASH = "\u2014"
MIN_DESC = 40


def repo_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def build_skill(name: str, description: str) -> str:
    title = name.replace("-", " ").capitalize()
    lines = [
        "---",
        "name: " + name,
        "description: " + description,
        "---",
        "",
        "# " + title,
        "",
        "## What this does",
        "TODO: one paragraph on the capability this skill adds.",
        "",
        "## When to use",
        "TODO: the user phrases and situations that should trigger this skill.",
        "",
        "## How",
        "TODO: the concrete steps, commands, or checklists the skill applies.",
        "",
        "## Honest limits",
        "TODO: what this skill cannot verify or guarantee, and when to hand off to a human.",
        "",
    ]
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Scaffold a Cambium skill (skills/<name>/SKILL.md).")
    ap.add_argument("--name", required=True, help="skill name, kebab-case; also the directory name")
    ap.add_argument("--description", required=True,
                    help="one-line description, minimum {} characters".format(MIN_DESC))
    ap.add_argument("--root", default=repo_root(), help="repo root to write into (default: this repo)")
    ap.add_argument("--force", action="store_true", help="overwrite an existing SKILL.md")
    args = ap.parse_args(argv)

    name = args.name.strip()
    if not KEBAB.match(name):
        print("[new_skill] ERROR: --name must be kebab-case (lowercase letters, digits, hyphens): "
              + repr(name), file=sys.stderr)
        return 1

    description = args.description.strip()
    if "\n" in description or "\r" in description:
        print("[new_skill] ERROR: --description must be a single line", file=sys.stderr)
        return 1
    if EM_DASH in description:
        print("[new_skill] ERROR: --description contains an em dash; use a plain hyphen "
              "(repo style: no em dashes)", file=sys.stderr)
        return 1
    if len(description) < MIN_DESC:
        print("[new_skill] ERROR: --description is {} characters; need at least {} so the "
              "plugin listing is never empty".format(len(description), MIN_DESC), file=sys.stderr)
        return 1

    root = os.path.abspath(args.root)
    skill_dir = os.path.join(root, "skills", name)
    target = os.path.join(skill_dir, "SKILL.md")
    if os.path.exists(target) and not args.force:
        print("[new_skill] REFUSED: already exists (use --force to overwrite): " + target,
              file=sys.stderr)
        return 1

    os.makedirs(skill_dir, exist_ok=True)
    with open(target, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(build_skill(name, description))
    print("[new_skill] wrote " + target)
    print("[new_skill] next steps:")
    print("  1. Replace the TODO sections with real guidance and real limits.")
    print("  2. Smoke-test the packaging:  python3 tools/plugin_smoke.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
