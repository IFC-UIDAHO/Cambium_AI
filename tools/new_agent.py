#!/usr/bin/env python3
"""new_agent.py -- scaffold a Cambium agent card pair (agents/ and .claude/agents/).

Writes the SAME card to agents/<name>.md and .claude/agents/<name>.md so the
mirror stays in sync (tests/test_plugin_sync.py checks byte equality), with
frontmatter that passes tools/check_agents.py (name, description, model, tools).

Usage:
    python3 tools/new_agent.py --name soil-scientist --council Labs \
        --description "Reviews soil sampling designs and lab protocols." \
        [--model sonnet] [--tools "Read, Grep, Glob, Write"] [--root DIR] [--force]

Honest limits:
    - Scaffolds the two card files only. It does NOT update roster docs,
      agent_cards.json, or the org chart; run the printed next steps.
    - The card body is a skeleton with TODO markers; a human writes the duties.
    - Name uniqueness across the whole roster is enforced by
      tools/check_agents.py, not by this scaffolder.
"""

import argparse
import json
import os
import re
import sys

import cambium_io  # noqa: F401

KEBAB = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
EM_DASH = "\u2014"


def repo_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def build_card(name: str, council: str, description: str, model: str, tools: str) -> str:
    """Return the full card text (frontmatter + body skeleton).

    The description is emitted as a double-quoted YAML scalar (json.dumps) so
    the frontmatter stays parseable by strict YAML even when the description
    contains colons; name/model/tools stay plain scalars because
    tools/check_agents.py compares the model value literally.
    """
    title = name.replace("-", " ").upper()
    note = name.replace("-", "_")
    lines = [
        "---",
        "name: " + name,
        "description: " + json.dumps(description),
        "model: " + model,
        "tools: " + tools,
        "---",
        "You are the " + title + ". " + description,
        "Council: " + council + ".",
        "",
        "DUTIES:",
        "- TODO: list the 3-5 concrete duties this agent owns.",
        "- TODO: name the files it reads and the single note it writes.",
        "- Never edit the deliverable or protected files outside your own note.",
        "",
        "OUTPUT CONTRACT: Decision, Evidence, Next action, Confidence.",
        "WRITE agent_outputs/" + note + "_note.md. Return <=120 words.",
        "",
    ]
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="Scaffold a Cambium agent card into agents/ and .claude/agents/."
    )
    ap.add_argument("--name", required=True, help="agent name, kebab-case (e.g. soil-scientist)")
    ap.add_argument("--council", required=True, help="council the agent belongs to (e.g. Labs)")
    ap.add_argument("--description", required=True, help="one-line description for the frontmatter")
    ap.add_argument("--model", default="sonnet", choices=["haiku", "sonnet", "opus"],
                    help="model tier (default: sonnet)")
    ap.add_argument("--tools", default="Read, Grep, Glob, Write",
                    help='comma list of tools (default: "Read, Grep, Glob, Write")')
    ap.add_argument("--root", default=repo_root(), help="repo root to write into (default: this repo)")
    ap.add_argument("--force", action="store_true", help="overwrite existing card files")
    args = ap.parse_args(argv)

    name = args.name.strip()
    if not KEBAB.match(name):
        print("[new_agent] ERROR: --name must be kebab-case (lowercase letters, digits, hyphens): "
              + repr(name), file=sys.stderr)
        return 1

    description = args.description.strip()
    if not description:
        print("[new_agent] ERROR: --description must not be empty", file=sys.stderr)
        return 1
    for label, value in (("--description", description), ("--council", args.council)):
        if EM_DASH in value:
            print("[new_agent] ERROR: " + label + " contains an em dash; use a plain hyphen "
                  "(repo style: no em dashes)", file=sys.stderr)
            return 1

    tools = ", ".join(t.strip() for t in args.tools.split(",") if t.strip())
    if not tools:
        print("[new_agent] ERROR: --tools must list at least one tool", file=sys.stderr)
        return 1

    root = os.path.abspath(args.root)
    targets = [
        os.path.join(root, "agents", name + ".md"),
        os.path.join(root, ".claude", "agents", name + ".md"),
    ]
    existing = [t for t in targets if os.path.exists(t)]
    if existing and not args.force:
        for t in existing:
            print("[new_agent] REFUSED: already exists (use --force to overwrite): " + t,
                  file=sys.stderr)
        return 1

    card = build_card(name, args.council.strip(), description, args.model, tools)
    for t in targets:
        os.makedirs(os.path.dirname(t), exist_ok=True)
        with open(t, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(card)
        print("[new_agent] wrote " + t)

    print("[new_agent] next steps:")
    print("  1. Fill in the TODO duties in both copies (keep them byte-identical).")
    print("  2. Add the agent to the council roster docs "
          "(docs/concepts/FACULTY_ROSTER.md, docs/concepts/ROLES.md).")
    print("  3. Validate the roster:  python3 tools/check_agents.py")
    print("  4. Refresh derived counts:  python3 tools/gen_agent_cards.py "
          "(agent_cards.json must match the roster or tools/doctor.py fails)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
