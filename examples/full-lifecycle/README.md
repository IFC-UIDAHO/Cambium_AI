# Full Lifecycle Demo — Campus Bike-Share Demand Forecaster

> **FICTIONAL DEMONSTRATION.** Every person, institution, sponsor, dataset, result, and dollar figure
> in this example is invented. Nothing here implies real funding, real affiliation, or real findings.
> The purpose is to show—as a single artifact chain—how the Cambium moves a project
> from an incoming RFP through proposal, development, verification, and a final report, with human
> gates recorded at every handoff and an output contract enforced by a runnable validator.

---

## How to read this chain

Walk the folders in order. Each stage produces one or more documents; a human gate (G1–G6) closes
each major transition before the next stage begins.

### Stage 1 — RFP Intake (→ G1)

`RFP.md` is the fictitious sponsor call. The RFP-Analyst reads it and produces `01_rfp_brief.md`:
a one-page summary that names the must-haves, flags open questions, and gives the Director enough to
decide whether to pursue. The Director signs **G1** in `governance/GATES.md`.

### Stage 2 — Ideation (→ G2)

The Ideation-Facilitator brainstorms and converges on three candidate approaches, ranked by fit,
recorded in `02_idea_slate.md`. The Director (with Co-PIs) picks one and signs **G2**.

### Stage 3 — Aims + Faculty Review (→ G3)

The PI drafts `03_aims.md`: three specific aims with hypotheses and success metrics. Two standing
faculty consultants (Statistics and Machine Learning) each write an independent review under `faculty/`.
Their reviews may raise concerns; the PI adjusts the aims before the Proposal-Writer finalises
`04_proposal_draft.md`. The Director signs **G3** (submit).

### Stage 4 — Post-Award Development (→ G4)

The team builds the demand-forecaster. Working artifacts are not shown here (they would live in
`projects/bike-share/`), but the **findings ledger** (`agent_outputs/findings_ledger.csv`) records every
finding the verification boards raised during development: the severity, the evidence, the claim tier,
and whether the issue is resolved. Critically, a **P0 data-leakage bug** is discovered by the
Integrity Officer (`F001`); the row is added with `status=open`. The Co-PI / Area Lead reviews it,
engineers apply the fix, and the row is re-added as `F001b` with `status=resolved` and
`claim_tier=Code-verified` before G4 is signed.

### Stage 5 — Report + Release (→ G5/G6)

The Reporting-Officer composes `reports/annual_report.md`, citing *only* findings whose `claim_tier`
is `Proved` or `Code-verified` and whose `status` is `resolved`. The Director signs **G5** (release
progress report) and **G6** (external send). Before any release the validator is run:

```
python3 governance/validate.py examples/full-lifecycle/agent_outputs/findings_ledger.csv
```

Because no P0 remains open, the validator exits 0 and writes `governance/provenance.json`.

---

## File map

```
examples/full-lifecycle/
  README.md                         ← you are here
  RFP.md                            ← fictitious sponsor call
  01_rfp_brief.md                   ← RFP-Analyst output
  02_idea_slate.md                  ← Ideation-Facilitator output
  03_aims.md                        ← PI specific aims
  04_proposal_draft.md              ← Proposal-Writer output
  faculty/
    statistics_review.md            ← Statistics Faculty review
    machine-learning_review.md      ← ML Faculty review
  team/
    program_plan.md                 ← Program-Manager plan
    team_roles.md                   ← role assignments
  deliverables.md                   ← Deliverables register
  agent_outputs/
    findings_ledger.csv             ← the evidence contract (validator input)
  governance/
    GATES.md                        ← human approval record (G1–G6)
  reports/
    annual_report.md                ← period report (verified results only)
```
