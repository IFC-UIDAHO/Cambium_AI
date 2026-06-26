<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/logo-dark.svg">
  <img src="assets/logo.svg" alt="Cambium" width="460">
</picture>

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Made with Claude](https://img.shields.io/badge/made%20with-Claude-blueviolet?logo=anthropic)](https://claude.ai)
[![Agents](https://img.shields.io/badge/agents-46-4f8cff)](INSTITUTE.md)
[![Governed](https://img.shields.io/badge/AI%20policy-governed-e5534b)](AI_GOVERNANCE.md)
[![CI: evidence-checked](https://img.shields.io/badge/CI-evidence--checked-46c46a)](.github/workflows/validate.yml)
[![Self-grade: A](https://img.shields.io/badge/doctor%20--grade-A-46c46a)](tools/doctor.py)

<h1 align="center">Cambium</h1>

### A research institution you run with one sentence — from RFP to verified results, with a human in the loop at every gate.

**46 specialized agents · 11 councils · 8 human gates · governed, evidence-checked, self-grading.**

</div>

---

## What Cambium is (and isn't)

Cambium is a **Claude plugin** (and a copy-me **GitHub template**) that turns Claude Code / Cowork into a
**research organization**. It is a portable layer of **46 subagents** organized into **11 councils**, plus a
governance policy, a lifecycle, and a set of framework tools. You are the **Director (PI)**; the councils do
the work; you approve at every gate.

- ✅ **It is** a *plugin / template* — a bundle of Claude Code **subagents** + commands + governance + tools.
- ❌ **It is not** a single "skill" (a skill is one capability; Cambium is a whole agent *organization*).
- ✅ **It can also be an MCP server** — `mcp/` exposes its tools (plan, provision, validate, doctor, grade) to any MCP client (Claude Desktop/Code, Cursor) via `python -m cambium_mcp.server` or `uvx cambium-mcp`.
- 🔗 **It runs on** Claude Code, and *complements* agent-harness systems (ECC, ruflo) — Cambium is the
  research-institution **domain layer** that can sit on top of a harness, not replace it.

*Cambium is the thin living layer just under a tree's bark — where new growth forms. This Cambium is the
layer where your research grows.*

## Goals

1. **Take any project, in any field, through its whole lifecycle** — RFP → idea → proposal → development →
   verified results → reports — without changing tools.
2. **Keep a human in command.** Nothing is brainstormed, submitted, sent, or published without the
   responsible person approving at a gate.
3. **Make honesty mechanical, not optional** — every claim carries an evidence tier; CI fails on an open P0,
   an un-evidenced "Code-verified" claim, or an unresolved citation.
4. **Be responsible by construction** — research-conduct + AI-use governance checked at every gate.
5. **Survive handoffs** — state lives in files (ledger, gates, decision records) so another Claude account, or
   a collaborator, can continue exactly where the last left off.
6. **Reuse before rebuild** — a Toolsmith finds existing packages/skills/MCPs before anyone writes from scratch.

## Principles

Human-in-the-loop · Evidence over assertion · Governed at every gate · Reuse beats rebuild · Any field.

## Install & use

**A — Plugin (recommended).**
```
/plugin marketplace add IFC-UIDAHO/Cambium_AI
/plugin install cambium-institute
```

**B — Template.** Click **"Use this template"** on GitHub (or clone), then copy `.claude/agents/` into your
project. Open `dashboard.html` to see the org.

Then just say what you need:

| Say… | What runs |
|---|---|
| `read rfp <file/link>` | RFP intake → requirements brief → **Gate G1** |
| `brainstorm` → `run tournament` | Ideation + Elo idea-tournament + faculty → ranked slate → **Gate G2** |
| `draft proposal` → `referee` | PI aims + Proposal-Writer → draft; referee scores it → **Gate G3** |
| `project approved` → `run lab` | development → verification → synthesis → **Gate G4** |
| `progress report` / `make deck` | Reporting Office → **Gates G5/G6** |
| `conduct check <gate>` | Research-Conduct-Officer → GO / CONDITIONS / STOP |

## The lifecycle (8 human gates)

G0 know the PI · G1 pursue the RFP · G2 pick the idea · G3a who to contact · G3 submit · G4 accept results ·
G5 release report · G6 publish. Full map: [`LIFECYCLE_V3.md`](LIFECYCLE_V3.md). Charter: [`INSTITUTE.md`](INSTITUTE.md).

## The 11 councils

Orchestration · Pre-Award · Partnerships · Faculty · Scouts · Labs · Verification · Execution · Reporting ·
Support · Governance. Interactive org chart: [`dashboard.html`](dashboard.html) · roster: [`.claude/agents/`](.claude/agents).

## Governed & self-checking

- **Evidence validator** — [`governance/validate.py`](governance/validate.py): fails the build on open P0,
  un-evidenced claims, or unresolved citations.
- **Governance policy** — [`AI_GOVERNANCE.md`](AI_GOVERNANCE.md) + [`RESEARCH_CONDUCT.md`](RESEARCH_CONDUCT.md)
  + a recorded human-approval ledger ([`governance/GATES.md`](governance/GATES.md)) + [`TOOL_POLICY.md`](TOOL_POLICY.md).
- **Self-grade** — `python3 tools/doctor.py --grade` scores the institute A–F (roster, governance, tooling,
  tests, decisions) + a security scan. Currently **A**.
- **Consistency + tests + CI** — `tools/consistency_check.py`, a `tests/` pytest suite, and a GitHub Action
  that runs all of it on every push.
- **Decision records** — [`DECISIONS.md`](DECISIONS.md) logs *why*, for clean multi-account handoffs.

## Framework tools (`tools/`)

`doctor` (health + `--grade`) · `task_router` (auto-selects councils for any task) · `toolsmith` (provision
existing tools) · `model_router` (per-agent model tier) · `consistency_check` · `check_agents` ·
`gen_agent_cards` / `gen_org_chart` · `new_project`.

## Built for a team — and multiple accounts

Configure your roster in `config.yml` (Director, Co-PIs, students, RAs…) with per-gate approvers
([`ROLES.md`](ROLES.md)). Because everything lives in files, **several people — each on their own Claude
account — can continue one project**, with the ledger, gates, and decision records keeping it coherent.

## Docs

[`GETTING_STARTED.md`](GETTING_STARTED.md) · [`INSTITUTE.md`](INSTITUTE.md) · [`LIFECYCLE_V3.md`](LIFECYCLE_V3.md) ·
[`DEVELOPMENT_PLAYBOOK.md`](DEVELOPMENT_PLAYBOOK.md) · [`OUTPUT_CONTRACT.md`](OUTPUT_CONTRACT.md) ·
[`ROLES.md`](ROLES.md) · [`AI_GOVERNANCE.md`](AI_GOVERNANCE.md) · [`COMPARISON.md`](COMPARISON.md) ·
[`DECISIONS.md`](DECISIONS.md) · [`FAQ.md`](FAQ.md) · [`ROADMAP.md`](ROADMAP.md) · [`CITATION.cff`](CITATION.cff).

## License

MIT — see [`LICENSE`](LICENSE). Created by M. Jaslam (University of Idaho · Intermountain Forestry Cooperative).
Use it, fork it, rename it, build your own institute.
