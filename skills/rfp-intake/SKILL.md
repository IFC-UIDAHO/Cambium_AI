---
name: rfp-intake
description: Read an RFP / solicitation / NOFO / call for proposals and produce a requirements brief plus a fit assessment, then stop at gate G1 "pursue this RFP?". Use when the user shares a funding call, says "read this RFP", "should we go for this", "analyze this solicitation", "is this a fit", or pastes/links a NSF/NIH/USDA-AFRI/DOE/foundation announcement. Delegates to the Pre-Award council (rfp-radar, rfp-analyst) and Scouts (scout-landscape) under the Orchestrator. Read-only; never fabricates eligibility, deadlines, or criteria.
---

# RFP intake — turn a solicitation into a go/no-go decision

This is a thin Cambium-way wrapper. Hand off to the **Orchestrator** and run the intake phase only;
do not draft the proposal here.

## Run it
1. **Pre-Award · rfp-analyst** — read the solicitation and extract, verbatim where possible:
   eligibility, scope, evaluation criteria + weights, required documents, page/format limits,
   budget caps (incl. indirect/F&A), cost-share, and every deadline. If a fact is not in the
   document, mark it OPEN — do not invent it.
2. **Pre-Award · rfp-radar** — score FIT against the Director's profile / project: where the call
   aligns, where it does not, and what would have to be true to win.
3. **Scouts · scout-landscape** (only if useful) — funder priorities and recent awards to mirror.

Keep a short findings ledger as you go (requirement → source line → status).

## Output
A one-page **requirements brief** (the extracted requirements) + a **fit assessment** (strengths,
gaps, effort estimate).

## Gate
Stop at gate card **G1 — "pursue this RFP?"**: the decision · options (pursue / pass / pursue-if) ·
the risks · your recommendation · APPROVE / REVISE / REJECT. Continue to ideation or proposal only
after the Director approves.
