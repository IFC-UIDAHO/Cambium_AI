<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/logo-dark.svg">
  <img src="assets/logo.svg" alt="Cambium" width="460">
</picture>

<h1>Cambium</h1>

<p><b>A research institution you run with one sentence</b> — from RFP to verified results,<br>with a human in the loop at every gate.</p>

<p>
<a href="https://github.com/IFC-UIDAHO/Cambium_AI/actions/workflows/validate.yml"><img alt="CI" src="https://img.shields.io/github/actions/workflow/status/IFC-UIDAHO/Cambium_AI/validate.yml?style=flat-square&label=CI&color=16C079"></a>
<a href="CHANGELOG.md"><img alt="Version" src="https://img.shields.io/badge/version-1.00.0-16C079?style=flat-square"></a>
<a href="INSTITUTE.md"><img alt="Agents" src="https://img.shields.io/badge/agents-46-16C079?style=flat-square"></a>
<a href="governance/GATES.md"><img alt="Human gates" src="https://img.shields.io/badge/human_gates-8-0E8E5B?style=flat-square"></a>
<a href="MCP_INTEGRATION.md"><img alt="MCP" src="https://img.shields.io/badge/MCP-ready-0E8E5B?style=flat-square"></a>
<a href="LICENSE"><img alt="License: MIT" src="https://img.shields.io/badge/License-MIT-yellow?style=flat-square"></a>
</p>

<p><b>46 specialized agents · 11 councils · 8 human gates · a CI-enforced evidence contract</b></p>

<p>
<a href="#-why-cambium">Why</a> ·
<a href="#-the-cambium-way">The Cambium way</a> ·
<a href="#-60-second-quickstart">Quickstart</a> ·
<a href="#-how-it-works">How it works</a> ·
<a href="#-governance-by-construction">Governance</a> ·
<a href="#-run-it-as-an-mcp-server">MCP</a> ·
<a href="#-how-it-compares">Compare</a> ·
<a href="INSTALL.md">Docs</a>
</p>

<img src="assets/demo.gif" alt="Cambium in action — RFP to verified results, narrated one sentence at a time" width="820">

</div>

---

## ✦ Why Cambium

Modern AI can draft a proposal, run an experiment, or write a paper. What it **cannot** do out of the box is run the *whole research organization* — pre-award through post-award — while keeping a person in command and keeping every claim honest.

That gap is where projects quietly go wrong: an autonomous pipeline overstates a result, a "done" task was never verified, a citation never resolved, and nobody approved the thing that got sent.

> [!IMPORTANT]
> **Cambium closes the gap by construction.** It turns Claude Code / Cowork into a portable research institution — **46 subagents** in **11 councils**, a shipped governance policy, an 8-gate lifecycle, and a tool suite that *fails the build when honesty slips.* You are the **Director (PI)**; the councils do the work; you approve at every gate.

|  | Cambium |
|---|---|
| **It is** | a Claude **plugin / GitHub template** — subagents + commands + governance + tools |
| **It also is** | an **MCP server** exposing 6 tools to Claude Desktop / Code / Cursor |
| **It is not** | a single "skill" — Cambium is a whole agent *organization* |
| **Field** | agnostic — domain expertise lives in a parameterized Faculty + your project config |

> *Cambium is the thin living layer just under a tree's bark, where new growth forms. This Cambium is the layer where your research grows.*

---

## ✦ The Cambium way

Type `/cambium <task>` and the run is never a generic "Used 6 tools." You get a **live run board**: the plan up front, the **real named agents** working (`Scouts · Landscape`, `Verification · Rigor`, …), each one's finding, and the human gate where *you* decide — `APPROVE / REVISE / REJECT`.

<div align="center">
<img src="assets/run_board.gif" alt="The Cambium way — live run board: plan, named agents working, the gate" width="860">
<details><summary><sub>static preview (if the GIF doesn't load)</sub></summary><img src="assets/run_board.png" alt="Cambium live run board — static preview" width="860"></details>
</div>

Every run follows four acts (full contract in **[PRESENTATION.md](PRESENTATION.md)**):

1. **Opening** — the live board shows the whole institute about to mobilize *before* any work starts.
2. **Live phases** — the Orchestrator dispatches the **real** sub-agents (`cambium-institute:<name>`, labelled `Council · Role`) and re-emits the board each phase, so you watch ✓ done · ▶ now · ○ waiting advance.
3. **The gate** — a one-page decision card; nothing finalizes without your `APPROVE`.
4. **Close-out** — the Support council records the changelog, refreshes docs, verifies numbers, and tidies up.

The board renders as plain text in any client, a branded SVG, and a self-contained live HTML dashboard — all from `tools/run_trace.py`, so the vocabulary never drifts.

---

## ⚡ 60-second quickstart

> [!TIP]
> New to Cambium? Start with **[`USE_CAMBIUM.md`](USE_CAMBIUM.md)** — a plain-language guide that walks you through your first run, step by step.

**Install it — directly from this repo** (full steps + gotchas in **[`INSTALL.md`](INSTALL.md)**):

- **Claude Desktop / Cowork** *(no terminal — easiest)*: type **`/create-cowork-plugin`**, paste `https://github.com/IFC-UIDAHO/Cambium_AI`, choose **Full working bundle**, press **Install**.
- **Claude Code** *(terminal)* — run on separate lines (full HTTPS URL; pick **user scope**), then `/reload-plugins`:
  ```
  /plugin marketplace add https://github.com/IFC-UIDAHO/Cambium_AI.git
  /plugin install cambium-institute
  ```
- **Template:** click **"Use this template"** on GitHub, or `git clone` and connect the folder to your project.

> [!WARNING]
> If the plugin marketplace **"+"** only shows Anthropic's catalog, run the `/create-cowork-plugin` step once first — see **[`INSTALL.md`](INSTALL.md)**.

Then just **say what you need** — one sentence at a time:

| Say… | What runs | Gate |
|---|---|---|
| `read rfp <file/link>` | RFP intake → requirements brief | **G1** pursue? |
| `brainstorm` → `run tournament` | ideation + Elo idea-tournament + faculty → ranked slate | **G2** which idea? |
| `draft proposal` → `referee` | PI aims + Proposal-Writer → draft; referee scores it | **G3** submit? |
| `project approved` → `run lab` | development → verification → synthesis | **G4** accept results? |
| `progress report` / `make deck` | Reporting → report + slides | **G5/G6** release? |
| `conduct check <gate>` | Research-Conduct-Officer → GO / CONDITIONS / STOP | — |

---

## 🔬 How it works

Cambium runs your project through one lifecycle with **8 named human gates** — nothing is brainstormed, submitted, sent, or published without the responsible person approving.

<div align="center">
<img src="assets/lifecycle.svg" alt="The Cambium lifecycle — 8 human gates from G0 to G6 plus G3a" width="860">
</div>

> **G0** know the PI · **G1** pursue the RFP · **G2** pick the idea · **G3a** who to contact · **G3** submit · **G4** accept results · **G5** release report · **G6** publish.

Behind each gate, an **organization of 46 agents in 11 councils** does the work. The Orchestrator routes the task, the right councils execute, the Verification board reproduces numbers, and you get a one-page decision summary at every gate.

<div align="center">
<img src="assets/org-chart.svg" alt="The Cambium org chart — 46 agents across 11 councils" width="860">
</div>

<details>
<summary><b>Deep dive: the 11 councils</b></summary>

<br>

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
- **Self-grade** — `python3 tools/doctor.py --grade` scores the institute **A–F** across roster, governance, tooling, tests, and decisions, plus a security scan. Currently **A** (graded 2026-06-26; reproduce it yourself with that command). ![doctor grade A](https://img.shields.io/badge/doctor%20--grade-A-16C079?style=flat-square)
- **Tests + CI** — a pytest suite (**104 passed / 1 skipped**, 2026-06-26) plus `tools/consistency_check.py`, run on every push by a GitHub Action.
- **Policy + ledger** — [`AI_GOVERNANCE.md`](AI_GOVERNANCE.md) + [`RESEARCH_CONDUCT.md`](RESEARCH_CONDUCT.md) + a recorded human-approval ledger ([`governance/GATES.md`](governance/GATES.md)) + decision records ([`DECISIONS.md`](DECISIONS.md)).

#### Proving the claim, not just asserting it

Cambium ships the infrastructure to **measure its own core thesis** — that hard gates + a claim-tier ledger produce fewer false claims than soft prompting — instead of only asserting it:

- **Enforcement A/B harness** — [`evals/enforcement_study/`](evals/enforcement_study): a pre-registered protocol (enforced-gates vs soft-prompt arm), a seeded-defect task set with locked ground truth, and a runnable metrics pipeline.

> [!NOTE]
> The harness is shipped and runs in CI; the comparative **result is Open** — no "enforcement beats prompting" claim is made until real runs are complete. That restraint *is* the evidence contract applied to Cambium itself.

- **Per-funder governance corpus** — [`governance/funders/`](governance/funders): NIH + NSF AI-use rules mapped to gates, each entry dated, owned, and guarded by a hard-failing freshness check (`tools/funder_freshness.py`) so it can never silently go stale. It is guidance, not compliance certification — the named PI stays accountable.

*Human-in-the-loop is enforced by the architecture — not just by convention.*

---

## 🔌 Run it as an MCP server

Beyond the plugin, [`mcp_server/`](mcp_server) ships an MCP server (official `mcp` SDK / FastMCP, stdio) exposing **6 tools** to any MCP client — Claude Desktop, Claude Code, or Cursor:

| Tool | Does |
|---|---|
| `cambium_plan(task)` | which councils/agents + gate plan for any task |
| `cambium_provision(task)` | recommended existing tools/packages (reuse-beats-rebuild) |
| `cambium_agents()` | the live 46-agent roster |
| `cambium_doctor()` | repo health |
| `cambium_grade()` | self-grade A–F + risk scan |
| `cambium_validate(ledger_csv)` | evidence-ledger check (blocks fake claims) |

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
| Shipped governance policy | — | — | **AI-use + research-conduct, enforced** || Full lifecycle (RFP → reports) | — | — | **pre-award + post-award, one contract** |
| Field-agnostic | n/a | n/a | **yes — parameterized Faculty** |

No existing system joins pre-award and post-award under one evidence contract, with mandatory human gates at every phase boundary and a shipped, enforceable governance policy. That is a claim about *integration and category* — every primitive exists in some other shipped system; the **combination** is what doesn't. Honest, web-verified positioning vs. Sakana, AI Co-Scientist, Agent Laboratory, Virtual Lab, AutoGen/CrewAI: **[`COMPARISON.md`](COMPARISON.md)**.

---

## 👥 Built for a team — and multiple accounts

Configure your roster in `config.yml` (Director, Co-PIs, students, RAs…) with per-gate approvers ([`ROLES.md`](ROLES.md)). Because everything lives in files — ledger, gates, decision records — **several people, each on their own Claude account, can continue one project** without losing coherence. Reuse beats rebuild: a Toolsmith finds existing packages/skills/MCPs before anyone writes from scratch.

---

## 🗺️ Roadmap · 🤝 Contributing · 📓 Cite

**Roadmap** — more shared tools as least-privilege MCP servers (web search, code run, citation resolver, data store); cross-agent handoffs over MCP **Tasks** / A2A; agent cards as a published capability directory. Human gates stay **above** the protocol. See [`ROADMAP.md`](ROADMAP.md).

**Contributing** — issues and PRs welcome. CI runs the evidence validator, consistency check, and the **104-test** suite on every push — keep the grade at **A**. Start with [`GETTING_STARTED.md`](GETTING_STARTED.md), then [`INSTITUTE.md`](INSTITUTE.md) and [`DECISIONS.md`](DECISIONS.md) for the *why*.

**Cite** — Cambium is built for academic work; a [`CITATION.cff`](CITATION.cff) is included, so GitHub's "Cite this repository" button just works.

<div align="center">
<br>
<sub>Built by the <a href="https://www.uidaho.edu/">University of Idaho</a> · Intermountain Forestry Cooperative · MIT licensed · the Cambium way ⬢</sub>
</div>

