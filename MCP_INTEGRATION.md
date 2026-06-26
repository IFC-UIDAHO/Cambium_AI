# MCP_INTEGRATION.md — Cambium over the Model Context Protocol

*The Model Context Protocol (MCP) is an open standard (governed under the Linux Foundation) that lets any
AI client call external tools through a uniform, audited interface. Source: modelcontextprotocol.io
(roadmap 2026-03-09).*

## Status: SHIPPED
Cambium ships an MCP server in [`mcp_server/`](mcp_server/) (official `mcp` SDK / FastMCP, stdio). It exposes
Cambium's tools to any MCP client (Claude Desktop / Claude Code / Cursor):

| MCP tool | Wraps |
|---|---|
| `cambium_plan(task)` | `tools/task_router.py` — councils + gate plan |
| `cambium_provision(task)` | `tools/toolsmith.py` — reuse-beats-rebuild manifest |
| `cambium_agents()` | `agent_cards.json` — the live roster |
| `cambium_doctor()` | `tools/doctor.py` — repo health |
| `cambium_grade()` | `tools/doctor.py --grade` — A–F + risk scan |
| `cambium_validate(ledger_csv)` | `governance/validate.py` — evidence gate |

Register it (`claude_desktop_config.json`):
```json
{ "mcpServers": { "cambium": { "command": "uvx", "args": ["cambium-mcp"] } } }
```
Install/run details: [`mcp_server/README.md`](mcp_server/README.md).

## Discovery: A2A Agent Cards
`tools/gen_agent_cards.py` emits `agent_cards.json` — a machine-readable capability manifest for all 46
agents (name, model tier, tools, description). Other agents/clients read the cards to know who does what.
Regenerate after roster changes: `python3 tools/gen_agent_cards.py`.

## Roadmap (not yet wired)
- Expose more shared tools (web search, code run, citation resolver, data store) as MCP servers, each agent
  declaring least-privilege scope (ties to `ROLES.md`).
- Move cross-agent handoffs to MCP **Tasks** / A2A when the spec lands; the cards become the published directory.
- Human gates stay ABOVE the protocol: MCP transports calls; humans still approve at every gate.
