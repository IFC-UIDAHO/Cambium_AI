# Cambium — Charter

*A general-purpose AI research organization. It takes any project from a sponsor's RFP to delivered
results and reports - with the President (you) approving at every gate. Field-agnostic: domain
expertise lives in the parameterized Faculty and your project config.*

## The lifecycle (two halves, eight gates)
```
  PRE-AWARD                                   |  POST-AWARD (after sponsor approval)
  RFP > G1 > Ideate > G2 > Aims+Faculty       |  Develop > Verify > G4 > Revise > Report > G5/G6
       > Collaborators > G3a > Proposal > G3  |
```
| Stage | Lead | Output | Gate (President decides) |
|---|---|---|---|
| 1 RFP intake | RFP-Analyst | 00_rfp_brief.md | **G1** pursue? |
| 2 Ideation | Ideation-Facilitator + Faculty | 02_idea_slate.md | **G2** which idea? |
| 3 Aims + faculty review | PI + Faculty | 03_aims.md, faculty/* | (internal) |
| 3b Collaborators | Collaborator-Scout + Liaison | partners/* | **G3a** who to contact (you send) |
| 4 Proposal draft | Proposal-Writer | 04_proposal_draft.md | **G3** submit? |
| 5 Development | Labs + Execution + Faculty | working artifacts | (internal) |
| 6 Verify | Verification boards | agent_outputs/*, ledger | **G4** apply fixes? |
| 7 Report | Reporting-Officer + Deck-Builder | reports/* | **G5/G6** release? |

Post-award development runs the **Development Playbook** (`DEVELOPMENT_PLAYBOOK.md`).

## The 11 councils (46 workers)
President (you) · Provost/Orchestration (00, 13) · Pre-Award (24-27) · Partnerships (31-33) ·
Faculty (28, parameterized) · Scouts (01-03) · Labs (04-06) · Verification (07-10) · Execution (11-12) ·
Support Staff (14-23) · Reporting (29-30). See `.claude/agents/` and `dashboard.html`.

Faculty are standing consultants: one parameterized agent spawned **per discipline** as needed -
statistics, mathematics, CS, ML, AI, economics, or the project's own field. New disciplines on demand
(`FACULTY_ROSTER.md`).

## Human-in-the-loop gates (non-negotiable)
At each **G**, the Orchestrator stops and presents a one-page summary, the decision needed, options,
risks, and a recommendation. It proceeds only on the President's approval. No proposal is submitted,
no deliverable edited, no report released, no claim strengthened beyond its evidence, without you.

## Projects
Each project = `projects/<slug>/` (from `templates/project/`), registered in `projects/REGISTRY.md`,
with its own RFP brief, idea slate, aims, faculty reviews, proposal, partners, team, reports, outputs.

## Standing principles
Evidence-or-silence · claim tiers · code-verified beats opinion · Smart-Tier models · single-writer
files · **President approves at every gate.**

## Governance
The Institute ships an explicit **AI Governance & Responsible-Use Policy** (`AI_GOVERNANCE.md`) covering
research and teaching (authorship/disclosure, research integrity, IRB & data sovereignty, FERPA, data
governance, bias, dual-use, provenance, incident response), a recorded human-approval ledger
(`governance/GATES.md`), an AI Use Statement template (`AI_USE_STATEMENT.md`), and a runnable validator
(`governance/validate.py`) that fails on an open P0 or an un-evidenced claim. Human-in-the-loop is thus
enforced by construction, not only by convention.