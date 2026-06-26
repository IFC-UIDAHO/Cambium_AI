#!/usr/bin/env python3
"""Cambium MCP server — exposes Cambium's tools to any MCP client (Claude Desktop/Code, Cursor, …).

Tools: cambium_plan, cambium_provision, cambium_agents, cambium_doctor, cambium_grade, cambium_validate.
Run (stdio):  python -m cambium_mcp.server   |   uvx cambium-mcp
"""
import os, sys, json, tempfile, subprocess
from mcp.server.fastmcp import FastMCP

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))            # mcp/ -> Cambium_ai
sys.path.insert(0, os.path.join(REPO, "tools"))
mcp = FastMCP("cambium")

def _run(rel, *args):
    r = subprocess.run([sys.executable, rel, *args], cwd=REPO, capture_output=True, text=True)
    return {"ok": r.returncode == 0, "output": (r.stdout or r.stderr).strip()[-4000:]}

@mcp.tool()
def cambium_plan(task: str) -> dict:
    """Auto-select which Cambium councils/agents run for a task, with the phased gate plan."""
    import task_router; return task_router.route(task)

@mcp.tool()
def cambium_provision(task: str) -> dict:
    """Recommend existing tools/packages/skills/MCPs for a task (reuse beats rebuild)."""
    import toolsmith; return toolsmith.manifest(task)

@mcp.tool()
def cambium_agents() -> dict:
    """The Cambium roster — agents, councils, model tiers."""
    p = os.path.join(REPO, "agent_cards.json")
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {"agents": [], "count": 0}

@mcp.tool()
def cambium_doctor() -> dict:
    """Run Cambium's repo health check (counts, HTML integrity, code parses, derived sync)."""
    return _run("tools/doctor.py")

@mcp.tool()
def cambium_grade() -> dict:
    """Self-grade the institute A-F across roster, governance, tooling, tests + a security scan."""
    return _run("tools/doctor.py", "--grade")

@mcp.tool()
def cambium_validate(ledger_csv: str) -> dict:
    """Validate an evidence ledger (CSV text). Blocks open P0, un-evidenced 'Code-verified', unresolved citations."""
    fd, path = tempfile.mkstemp(suffix=".csv"); os.close(fd)
    open(path, "w", encoding="utf-8").write(ledger_csv)
    try: return _run("governance/validate.py", path)
    finally:
        try: os.remove(path)
        except Exception: pass

def main():
    mcp.run()   # stdio transport

if __name__ == "__main__":
    main()
