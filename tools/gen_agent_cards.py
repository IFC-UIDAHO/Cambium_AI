#!/usr/bin/env python3
"""Generate A2A-style Agent Cards for Cambium's roster (P2).

Reads .claude/agents/*.md YAML frontmatter and emits agent_cards.json - a machine-readable
capability manifest (name, description, model tier, tools) so agents (and external A2A clients)
can discover what each Cambium agent does. Inspired by the Agent-to-Agent (A2A) "Agent Card" idea.

Usage: python3 tools/gen_agent_cards.py
"""
import os, json, glob, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AGENTS = os.path.join(ROOT, ".claude", "agents")

def parse_frontmatter(text):
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    fm = {}
    for line in text[3:end].splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            fm[k.strip()] = v.strip()
    return fm

def main():
    cards = []
    for path in sorted(glob.glob(os.path.join(AGENTS, "*.md"))):
        base = os.path.basename(path)
        if base.upper() == "README.MD":
            continue
        with open(path, encoding="utf-8", errors="replace") as f:
            fm = parse_frontmatter(f.read())
        if not fm.get("name"):
            continue
        cards.append({
            "id": base.split("-")[0],
            "name": fm.get("name", ""),
            "model": fm.get("model", "inherit"),
            "tools": [t.strip() for t in fm.get("tools", "").split(",") if t.strip()],
            "description": fm.get("description", ""),
            "file": ".claude/agents/" + base,
        })
    out = {"schema": "cambium.agent-cards/v1", "count": len(cards), "agents": cards}
    dest = os.path.join(ROOT, "agent_cards.json")
    json.dump(out, open(dest, "w"), indent=2)
    print("[gen_agent_cards] wrote %s with %d cards" % (dest, len(cards)))
    return 0

if __name__ == "__main__":
    sys.exit(main())
