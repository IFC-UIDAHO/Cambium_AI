#!/usr/bin/env python3
"""agent_scaffold -- generate contract-valid extension files for a Cambium fork or add-on.

Writes a new agent or skill definition into a TARGET DIRECTORY OF YOUR CHOOSING. --dir is
required and never defaults to the live repo, so running this tool cannot silently change the
canonical roster count that tools/consistency_check.py and tools/check_agents.py enforce.

If the intent is to add the new file to the REAL Cambium roster, copy the generated file(s) into
.claude/agents/ (and agents/, kept identical by tools/sync_plugin_agents.py) or skills/, then run
tools/gen_readme.py and tools/check_agents.py so the counts stay honest everywhere they are stated.

Agent kind writes two identical copies (the dual-directory convention used by the real roster):
  <dir>/.claude/agents/<name>.md
  <dir>/agents/<name>.md

Skill kind writes one file:
  <dir>/skills/<name>/SKILL.md

Both kinds use YAML frontmatter fenced by --- lines, matching the format tools/check_agents.py
parses. Agent frontmatter requires name, description, model, tools. Skill frontmatter requires
name, description.

Refuses to overwrite an existing file (exit 1) so scaffolding never clobbers real content.

Usage:
  python3 tools/agent_scaffold.py --kind agent --name my-new-agent \\
      --description "What this agent does." --council lab --model sonnet --dir /tmp/sandbox
  python3 tools/agent_scaffold.py --kind skill --name my-new-skill \\
      --description "What this skill is for." --dir /tmp/sandbox

Exit codes:
  0  file(s) written
  1  bad arguments, name collision, or target already exists
"""
from __future__ import annotations
import argparse
import os
import re
import sys

import cambium_io  # noqa: F401 -- UTF-8 stdout/stderr guard on Windows

# Same allowed model set enforced by tools/check_agents.py -- kept in lockstep by hand since
# this tool must stand on its own (no import of check_agents, matching its stdlib-only design).
VALID_MODELS = {"inherit", "opus", "sonnet", "haiku"}

_KEBAB_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def is_kebab_case(name: str) -> bool:
    """True if name is lowercase, digits, and single hyphens between words (no leading/trailing
    hyphen, no double hyphen, no underscore, no uppercase)."""
    return bool(_KEBAB_RE.match(name))


def _agent_frontmatter(name: str, description: str, model: str, tools: str) -> str:
    return (
        "---\n"
        f"name: {name}\n"
        f"description: {description}\n"
        f"model: {model}\n"
        f"tools: {tools}\n"
        "---\n"
    )


def _agent_body(name: str, description: str, council: str) -> str:
    title = name.replace("-", " ").title()
    return (
        f"You are {title.upper()}, a scaffolded Cambium agent in the {council} council.\n\n"
        f"PURPOSE: {description}\n\n"
        "## Core duties\n"
        "DO: (fill in what this agent does).\n"
        "DON'T: (fill in what this agent must not do).\n\n"
        "OUTPUT CONTRACT: Decision, Evidence, Next action, Risk, Confidence; concise.\n"
    )


def _skill_frontmatter(name: str, description: str) -> str:
    return f"---\nname: {name}\ndescription: {description}\n---\n"


def _skill_body(name: str, description: str) -> str:
    title = name.replace("-", " ").title()
    return f"\n# Skill: {title} ({name})\n\n{description}\n"


def scaffold_agent(target_dir: str, name: str, description: str, council: str, model: str) -> list:
    """Write the dual agent copies. Returns the two paths written. Raises FileExistsError if
    either target already exists."""
    fm = _agent_frontmatter(name, description, model, "Read, Write, Grep, Glob")
    body = _agent_body(name, description, council)
    content = fm + body

    dot_path = os.path.join(target_dir, ".claude", "agents", f"{name}.md")
    plain_path = os.path.join(target_dir, "agents", f"{name}.md")

    for p in (dot_path, plain_path):
        if os.path.exists(p):
            raise FileExistsError(p)

    for p in (dot_path, plain_path):
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(content)

    return [dot_path, plain_path]


def scaffold_skill(target_dir: str, name: str, description: str) -> list:
    """Write the single SKILL.md. Returns the path written. Raises FileExistsError if it
    already exists."""
    fm = _skill_frontmatter(name, description)
    body = _skill_body(name, description)
    content = fm + body

    path = os.path.join(target_dir, "skills", name, "SKILL.md")
    if os.path.exists(path):
        raise FileExistsError(path)

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(content)

    return [path]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Generate contract-valid Cambium agent or skill scaffolding.")
    ap.add_argument("--kind", required=True, choices=["agent", "skill"], help="What to scaffold.")
    ap.add_argument("--name", required=True, help="kebab-case identifier, e.g. my-new-agent.")
    ap.add_argument("--description", required=True, help="One-line description for frontmatter.")
    ap.add_argument("--council", default="lab", help="Council label for agent body text (agent kind only).")
    ap.add_argument("--model", default="sonnet", help="Model tier: inherit/opus/sonnet/haiku (agent kind only).")
    ap.add_argument("--dir", required=True, help="Target directory to write into. Never the live repo.")

    # Names may legitimately start with a hyphen (a kebab-case violation we want to REPORT,
    # not have argparse choke on). Fold "--name X" into "--name=X" so option-like values such
    # as "-bad" reach is_kebab_case() and fail there with rc 1, like every other bad name.
    argv = list(sys.argv[1:] if argv is None else argv)
    for i, tok in enumerate(argv):
        if tok == "--name" and i + 1 < len(argv):
            argv[i:i + 2] = ["--name=" + argv[i + 1]]
            break

    try:
        args = ap.parse_args(argv)
    except SystemExit as exc:
        if exc.code == 0:  # --help / --version: let the clean exit propagate
            raise
        return 2  # argparse already printed its usage error to stderr

    if not is_kebab_case(args.name):
        print(f"[agent_scaffold] ERROR: --name {args.name!r} is not kebab-case "
              "(lowercase letters, digits, single hyphens between words).", file=sys.stderr)
        return 1

    if args.kind == "agent" and args.model.strip().lower() not in VALID_MODELS:
        print(f"[agent_scaffold] ERROR: --model {args.model!r} is not one of "
              f"{sorted(VALID_MODELS)}.", file=sys.stderr)
        return 1

    if not args.description.strip():
        print("[agent_scaffold] ERROR: --description must not be empty.", file=sys.stderr)
        return 1

    target_dir = os.path.abspath(args.dir)

    try:
        if args.kind == "agent":
            written = scaffold_agent(target_dir, args.name, args.description, args.council,
                                      args.model.strip().lower())
        else:
            written = scaffold_skill(target_dir, args.name, args.description)
    except FileExistsError as exc:
        print(f"[agent_scaffold] ERROR: refusing to overwrite existing file: {exc}", file=sys.stderr)
        return 1

    for p in written:
        print(f"[agent_scaffold] wrote {p}")
    print("[agent_scaffold] NOTE: this only wrote files under --dir. Adding this to the REAL "
          "Cambium roster (copying into the live .claude/agents/, agents/, or skills/) changes "
          "canonical counts and requires running tools/gen_readme.py and tools/check_agents.py "
          "afterward so stated numbers stay honest.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
