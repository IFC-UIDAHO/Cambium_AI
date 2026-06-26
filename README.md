<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/logo-dark.svg">
  <img src="assets/logo.svg" alt="Cambium" width="460">
</picture>

<h1>Cambium</h1>

### A research institution you run with one sentence — from RFP to verified results, with a human in the loop at every gate.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Agents](https://img.shields.io/badge/agents-46-4f8cff)](INSTITUTE.md)
[![AI policy](https://img.shields.io/badge/AI%20policy-governed-e5534b)](AI_GOVERNANCE.md)
[![CI](https://img.shields.io/badge/CI-evidence--checked-46c46a)](.github/workflows/validate.yml)
[![Self-grade](https://img.shields.io/badge/doctor%20--grade-A-46c46a)](tools/doctor.py)
[![MCP](https://img.shields.io/badge/MCP-ready-8a63d2)](MCP_INTEGRATION.md)

**46 specialized agents · 11 councils · 8 human gates · governed, evidence-checked, self-grading.**

<br>

<img src="assets/demo.gif" alt="Cambium in action — RFP to verified results, narrated by one sentence at a time" width="760">

</div>

---

## ✦ Why Cambium

Modern AI can draft a proposal, run an experiment, or write a paper. What it *cannot* do out of the box is run the **whole research organization** — pre-award through post-award — while keeping a person in command and keeping every claim honest.

That gap is where projects go wrong: an autonomous pipeline overstates a result, a "done" task was never verified, a citation never resolved, and nobody approved the thing that got sent.

**Cambium closes the gap by construction.** It turns Claude Code / Cowork into a portable research institution: **46 subagents** organized into **11 councils**, a governance policy, an 8-gate lifecycle, and a tool suite that *fails the build* when honesty slips. You are the **Director (PI)**; the councils do the work; you approve at every gate.

> *Cambium is the thin living layer just under a tree's bark, where new growth forms. This Cambium is the layer where your research grows.*

|  | Cambium |
|---|---|
| **It is** | a Claude **plugin / GitHub template** — subagents + commands + governance + tools |
| **It also is** | an **MCP server** exposing 6 tools to Claude Desktop / Code / Cursor |
| **It is not** | a single "skill" — Cambium is a whole agent *organization* |
| **Field** | agnostic — domain expertise lives in a parameterized Faculty + your project config |

---

## ⚡ 60-second quickstart

**A — Plugin (recommended).**
```
/plugin marketplace add IFC-UIDAHO/Cambium_AI
/plugin install cambium-institute
```

**B — Template.** Click **"Use this template"** on GitHub (or clone), then copy `.claude/agents/` into your project and open `dashboard.html` to see the org.

Then just **say what you need** — one sentence at a time:

| Say… | What runs | Gate |
|---|---|---|
| `read rfp <file/link>` | RFP intake → requirements brief | **G1** pursue? |
| `brainstorm` → `run tournament` | Ideation + Elo idea-tournament + faculty → ranked slate | **G2** which idea? |
| `draft proposal` → `referee` | PI aims + Proposal-Writer → draft; referee scores it | **G3** submit? |
| `project approved` → `run lab` | development → verification → synthesis | **G4** accept results? |
| `progress report` / `make deck` | Reporting Office → report + slides | **G5/G6** release? |
| `conduct check <gate>` | Research-Conduct-Officer → GO / CONDITIONS / STOP | — |

---

## 🔬 How it works

Cambium runs your project through a single lifecycle with **8 named human gates** — nothing is brainstormed, submitted, sent, or published without the responsible person approving.

<div align="center">
<img src="assets/lifecycle.svg" alt="The Cambium lifecycle — 8 human gates from G0 to G6 plus G3a" width="860">
</div>

> **G0** know the PI · **G1** pursue the RFP · **G2** pick the idea · **G3a** who to contact · **G3** submit · **G4** accept results · **G5** release report · **G6** publish.

Behind each gate, an **organization of 46 agents in 11 councils** does the work. The Orchestrator routes the task, the right councils execute, the Verification board reproduces numbers, and you get a one-page decision summary at every **G**.

<div align="center">
<img src="assets/org-chart.svg" alt="The Cambium org chart — 46 agents across 11 councils" width="860">
</div>

<details>
<summary><b>Deep dive: the 11 councils</b></summary>

| Council | Role |
|---|---|
| **Orchestration** | routes tasks, runs gates, holds the line on human-in-the-loop |
| **Pre-Award** | RFP analysis, ideation, aims, proposal drafting |
| **Partnerships** | collaborator sourcing, liaison, program management |
| **Faculty** | standing consultants — one parameterized expert per discipline, spun up on demand |
| **Scouts** | prior-art, methods, and landscape reconnaissance |
| **Labs** | theory, methods, domain, and statistics development |
| **Verification** | rigor, methodology, evidence, and domain checks — *runs your code* |
| **Execution** | experiments, ablation, iteration, research engineering |
| **Reporting** | reporting officer + deck builder |
| **Support** | record-keeping, librarian, data steward, figures, integrity, and more |
| **Governance** | research-conduct + AI-use policy, enforced at every gate |

Faculty are parameterized: statistics, math, CS, ML, economics, or your project's own field — new disciplines on demand. Full roster: [`.claude/agents/`](.claude/agents) · interactive chart: [`dashboard.html`](dashboard.html).
</details>

---

## 🛡️ Governance by construction

The differentiator is not "more agents." It is that **honesty is mechanical, not optional.** Every claim any agent makes carries an evidence tier:

| Tier | Meaning |
|---|---|
| **Proved** | formally or mathematically established |
| **Code-verified** | reproduced by *running the code* |
| **Asserted** | model-generated, not yet verified |
| **Open** | unresolved / unknown |

CI **fails the build** on an open **P0**, an un-evidenced "Code-verified" claim, or an unresolved citation:

- **Evidence validator** — [`governance/validate.py`](governance/validate.py) blocks fake claims at the ledger.
- **Self-grade** — `python3 tools/doctor.py --grade` scores the institute A–F across roster, governance, tooling, tests, and decisions, plus a security scan. **Currently A.**
- **Tests + CI** — an **18-test** pytest suite (`tests/`) plus `tools/consistency_check.py`, run on every push by a **GitHub Action**.
- **Policy + ledger** — [`AI_GOVERNANCE.md`](AI_GOVERNANCE.md) + [`RESEARCH_CONDUCT.md`](RESEARCH_CONDUCT.md) + a recorded human-approval ledger ([`governance/GATES.md`](governance/GATES.md)) + decision records ([`DECISIONS.md`](DECISIONS.md)).

*Human-in-the-loop is enforced by the architecture — not just by convention.*

---

## 🔌 Run it as an MCP server

Beyond the plugin, `mcp_server/` ships an MCP server (official `mcp` SDK / FastMCP, stdio) that exposes **6 tools** to any MCP client — Claude Desktop, Claude Code, or Cursor:

| Tool | Does |
|---|---|
| `cambium_plan(task)` | which councils/agents + gate plan for any task |
| `cambium_provision(task)` | recommended existing tools/packages (reuse-beats-rebuild) |
| `cambium_agents()` | the live 46-agent roster |
| `cambium_doctor()` | repo health |
| `cambium_grade()` | self-grade A–F + risk scan |
| `cambium_validate(ledger_csv)` | evidence-ledger check (blocks fake claims) |

Register it in `claude_desktop_config.json`:
```json
{ "mcpServers": { "cambium": { "command": "uvx", "args": ["cambium-mcp"] } } }
```
Details: [`mcp_server/README.md`](mcp_server/README.md) · [`MCP_INTEGRATION.md`](MCP_INTEGRATION.md).

---

## 🆚 How it compares

| | Raw Claude Code | Bare agent harness | **Cambium** |
|---|:---:|:---:|:---:|
| Multi-agent research org | build it yourself | substrate only | **46 agents · 11 councils, ready** |
| Mandatory human gates | — | optional | **8 named gates (G0–G6 + G3a)** |
| Evidence tiers + CI enforcement | — | — | **Proved / Code-verified / Asserted / Open, build-failing** |
| Shipped governance policy | — | — | **AI-use + research-conduct, enforced** |
| Full lifecycle (RFP → reports) | — | — | **pre-award + post-award, one contract** |
| Field-agnostic | n/a | n/a | **yes — parameterized Faculty** |

No existing system joins pre-award and post-award under one evidence contract, with mandatory human gates at every phase boundary and a shipped, enforceable governance policy. Honest, web-verified positioning vs. Sakana, AI Co-Scientist, Agent Laboratory, Virtual Lab, AutoGen/CrewAI: [`COMPARISON.md`](COMPARISON.md).

---

## 👥 Built for a team — and multiple accounts

Configure your roster in `config.yml` (Director, Co-PIs, students, RAs…) with per-gate approvers ([`ROLES.md`](ROLES.md)). Because everything lives in files — ledger, gates, decision records — **several people, each on their own Claude account, can continue one project** without losing coherence. Reuse beats rebuild: a Toolsmith finds existing packages/skills/MCPs before anyone writes from scratch.

---

## 🗺️ Roadmap

Planned: more shared tools as least-privilege MCP servers (web search, code run, citation resolver, data store); cross-agent handoffs over MCP **Tasks** / A2A when the spec lands; agent cards as a published capability directory. Human gates stay **above** the protocol. See [`ROADMAP.md`](ROADMAP.md).

## 🤝 Contributing

Issues and PRs welcome. CI runs the evidence validator, consistency check, and the 18-test suite on every push — keep the grade at **A**. Start with [`GETTING_STARTED.md`](GETTING_STARTED.md), then [`INSTITUTE.md`](INSTITUTE.md) and [`DECISIONS.md`](DECISIONS.md) for the *why*.

## 📑 Citation

If Cambium supports your work, please cite it — see [`CITATION.cff`](CITATION.cff).

## License

MIT — see [`LICENSE`](LICENSE). Created by **M. Jaslam** · University of Idaho · Intermountain Forestry Cooperative. Use it, fork it, rename it, build your own institute.

<div align="center">
<br>
<img src="assets/social-preview.png" alt="Cambium — a research institution you run with one sentence" width="640">
</div>
