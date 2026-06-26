# MCP_INTEGRATION.md — agent/tool wire protocol (v3.2 target)
*The Model Context Protocol (MCP) is now an open standard governed under the Linux Foundation; the 2026
roadmap adds agent-to-agent Tasks and OAuth. Adopting it gives Cambium's 46 agents an audited,
discoverable interface to tools and to each other. Source: modelcontextprotocol.io/roadmap (2026-03-09).*

## Plan
- Expose Cambium's shared tools (web search, code run, repo I/O, citation resolver, data store) as **MCP servers**.
- Each agent declares the MCP tools it may call (least privilege; logged).
- Cross-agent handoffs move to MCP **Tasks** when the spec lands (A2A "Agent Cards" for discovery).
- Keep human gates ABOVE the protocol: MCP transports calls; humans still approve at every gate.

## Why
Audited tool calls + provenance, interoperability with the wider agent ecosystem, and a clean place to
enforce access scope (ties to ROLES.md group permissions). Status: design — not yet wired.

## A2A Agent Cards (P2 — shipped: generator)
`tools/gen_agent_cards.py` emits `agent_cards.json` — a machine-readable capability manifest for all 45
agents (name, model tier, tools, description). This is the discovery layer for agent-to-agent (A2A)
interop: other agents/clients can read the cards to know who does what. Regenerate after roster changes:
`python3 tools/gen_agent_cards.py`. When MCP Tasks/A2A land, these cards become the published directory.
