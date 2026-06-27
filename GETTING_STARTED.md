# Getting Started — three doors, pick yours

*The Institute meets you wherever your project is. Install once, then jump to A, B, or C.*

## Install (once)

1. **Template:** clone or "Use this template", then copy `.claude/agents/` into your project root.
   (Or install the plugin — see `INSTALL.md`.)
2. Copy `config.example.yml` → `config.yml` and set your lab name + default model profile.
3. Open `dashboard.html` to see the org chart and command list.
4. Create your project: say **`new project: <name>`** → it scaffolds `projects/<slug>/` from
   `templates/project/` and registers it in `projects/REGISTRY.md`.

> **The rule that never changes:** you are the Director (PI). The Institute drafts, researches, verifies,
> and reports; **you decide at every Gate.** Nothing is sent, submitted, or released without you.

---

## A. From scratch — you have an RFP / call for proposals {#a-from-scratch}

This is the full pre-award path.

1. **`read rfp <file or link>`** — the **RFP-Analyst** extracts requirements, eligibility, evaluation
   criteria + weights, budget, and deadlines → `01_rfp_brief.md`. → **Gate G1:** you confirm pursue/pivot.
2. **`brainstorm`** — the **Ideation-Facilitator** (pulling in **Faculty**) generates and ranks an idea
   slate against the criteria → `02_idea_slate.md`. → **Gate G2:** you pick the winning idea.
3. **`convene faculty <fields>`** — discipline experts (e.g. statistics, ML, your domain) critique the
   direction → `faculty/*_review.md`. The **PI** writes the Specific Aims → `03_aims.md`.
4. **`find collaborators <categories>`** — the **Collaborator-Scout** builds a *verified* candidate
   list (universities, agencies, industry, partners); the **Partnership-Liaison** drafts outreach
   emails + a one-page brief + meeting agendas. → **Gate G3a:** you approve who to contact; **you send.**
5. **`draft proposal`** — the **Proposal-Writer** produces the full draft (significance, approach,
   timeline, deliverables, budget narrative, criteria-alignment) → `04_proposal_draft.md`. → **Gate G3:**
   you finalize and **submit.**

---

## B. Already awarded / mid-project — you're building {#b-mid-project}

This is the post-award **Development Playbook** (full detail in `DEVELOPMENT_PLAYBOOK.md`).

1. **`project approved`** — flips the project to Development; the **Program-Manager** builds the
   work-breakdown across PIs/Co-PIs/students/staff, the milestone + monthly-meeting calendar, and the
   deliverables register → `team/program_plan.md`, `deliverables.md`.
2. **`run lab`** — one development cycle: **Scouts + Labs + Execution** build and run → **Verification
   boards** (Opus) attack it and reproduce the numbers → the **Orchestrator** synthesizes one issue
   table → **Gate G4:** you approve which P0/P1 fixes to apply → the **Document Office** applies them.
3. Repeat `run lab` / `run verification` per work-package. Everyone on the team uses the **same
   `.claude/agents/` + project template**, so outputs are comparable and the Program-Manager merges them.

> **Mid-project entry tip:** point the agents at your existing repo. The **Data-Steward** inventories
> your data, the **Record-Keeper** seeds the ledger from what exists, and `run verification` gives you
> an honest current-state audit before you change anything.

---

## C. Writing & reporting phase {#c-reporting}

For periodic reporting, papers, and decks — at any point.

- **`progress report`** / **`semi-annual report`** / **`annual report`** — the **Reporting-Officer**
  assembles milestones plan-vs-actual + verified results + risks + next-period plan → `reports/`.
  → **Gate G5/G6:** you approve release.
- **`make deck`** — the **Deck-Builder** turns a report or proposal into a clean PPT/HTML deck (with the
  **Figures** studio's charts).
- **Final deliverables** — the **Document Office** writes the paper/thesis from verified findings; the
  **Outreach** agent prepares the repo/README/demo; the **Program-Manager** tracks the deliverables
  register (paper, thesis, tool, GitHub, dataset).

---

## The five-field output contract (why 46 agents stay coherent)

Every agent returns: **Decision · Evidence · Next action · Risk · Confidence**, each finding tagged
with a **severity** (P0/P1/P2) and a **claim tier** (Proved / Code-verified / Asserted / Open).
Conflicts resolve by *code-verified beats asserted*. See `OUTPUT_CONTRACT.md`.

## Model profiles

Default **Smart-Tier** (Opus on theory + the 3 audit boards, Sonnet elsewhere). Switch anytime:
`make everything opus` (max power) or `go lean` (Opus on verification only). Set the default in
`config.yml`.

## A 10-minute test drive

Try the bundled fictional demo: `examples/demo-from-scratch/` (a tiny RFP → idea → aims walk-through)
and `examples/demo-mid-project/` (a small repo the verification boards audit). Nothing real, nothing
private — just enough to see the machine move.
