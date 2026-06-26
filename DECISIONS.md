# Cambium — Decision Records (ADR)
*A living log of the load-bearing decisions, so any Claude account (or human) can see WHY, not just what.
Append a new entry for every meaningful architectural/governance decision. Template: templates/DECISION_RECORD.md.*

## ADR-001: Council-based, human-gated institution (not a free agent swarm)
- Date: 2026-06 · Status: Accepted · Decider: Director
- Context: needed a research org, not just "many agents."
- Decision: organize as 11 councils / 46 agents under an Orchestrator, with 8 human gates (G0–G6) and an evidence contract.
- Consequences: every phase stops for a human; nothing ships without approval. Do NOT remove the gates.

## ADR-002: Evidence-tiered output contract, enforced in CI
- Date: 2026-06 · Status: Accepted
- Decision: claim tiers (Proved/Code-verified/Asserted/Open); `governance/validate.py` fails the build on open P0,
  un-evidenced "Code-verified", or unresolved citations.
- Consequences: honesty is a check, not a convention.

## ADR-003: Adopt verified ideas from peer systems
- Date: 2026-06 · Status: Accepted
- Decision: Elo idea-tournament (← AI Co-Scientist), referee/reproducibility/novelty gates (← AI Scientist),
  budget-aware verification (← Agent Lab), Toolsmith provisioning (reuse-beats-rebuild), Task Router, `doctor` self-check
  (← ECC/ruflo metaharness). NOT adopted: becoming a harness/swarm engine — Cambium stays the research-institution layer.
- Consequences: Cambium is the domain layer; it can run ON harnesses like ECC/ruflo, not replace them.

## ADR-004: Multi-account continuity via files + git (not a shared server, yet)
- Date: 2026-06 · Status: Accepted
- Decision: state lives in the repo (PROJECT_STATE/ledger/GATES/ADR); multiple Claude accounts continue from files.
  Hosted multi-user (server+DB+SSO) is a future phase.
- Consequences: works offline today; per-user accounts run agents on their own login (no shared keys).

## ADR-005: Set aside the web-app build; keep the core institute
- Date: 2026-06 · Status: Accepted · Decider: Director
- Decision: moved app/, campus.html, and the app plans to a recoverable trash folder; kept agents, governance, tools, docs.
- Consequences: focus stays on the institute + framework; the app can be revived from trash if wanted.

## ADR-006: Ship an MCP server (alongside the plugin)
- Date: 2026-06 · Status: Accepted · Decider: Director
- Context: Cambium was plugin/template only; users asked to also expose it like the many `npx`/MCP tools they see.
- Decision: add `mcp_server/` — a Python MCP server (official `mcp` SDK / FastMCP, stdio) exposing cambium_plan,
  provision, agents, doctor, grade, validate. Installable via `python -m cambium_mcp.server` or `uvx cambium-mcp`.
- Consequences: Cambium is now usable FROM other AI apps (Claude Desktop/Code, Cursor), not just as a plugin.
  Stays the research-institution domain layer; the MCP is a thin wrapper over existing tools.
