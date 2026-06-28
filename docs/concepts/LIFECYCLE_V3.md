# LIFECYCLE_V3 — Cambium end-to-end, human-in-the-loop
*How Cambium runs a research program from a funding call to delivery — AI-heavy, but a human approves
every gate, and `research-conduct-officer` signs off responsibly at each one.*

| # | Stage | Agents | You do | Gate |
|---|---|---|---|---|
| 0 | **Know the PI** | (profile) record-keeper | fill `USER_PROFILE.md` | **G0** profile ready |
| 1 | **RFP radar** | rfp-radar | confirm which call + targetable areas | **G1** pursue? |
| 2 | **Ideas + brainstorm** | idea-inbox → ideation → idea-tournament → faculty; scout-prior-art novelty gate | drop ideas; pick the winner | **G2** idea chosen |
| 3 | **Team + pre-award** | convener, collaborator-scout, PI, proposal-writer, budget-officer, grants-compliance | recruit team; approve aims/budget/docs | **G3** submit |
| 4 | **Award → mobilize** | program-manager, convener, office-manager | confirm assignments, groups, access | (post-award kickoff) |
| 5 | **Execute** | labs, lab-statistics, exec-iteration, research-engineer, faculty, verify boards, referee | steer; approve fixes/results | **G4** results verified |
| 6 | **Run the lab** | reporting-officer, deck-builder, office-manager, feedback-router, scheduler | approve reports; give feedback | **G5/G6** report/release |

**Cross-cutting at every gate:** `research-conduct-officer` (RESEARCH_CONDUCT.md) + `integrity-officer`
(evidence tiers) + `AI_GOVERNANCE.md` (AI use). Nothing advances on an open STOP.

## Triggers
`watch rfps` · `rfp in <file/link>` · `add idea` / `brainstorm` · `run tournament` · `convene team` ·
`find collaborators <cats>` · `build budget` · `compliance check` · `draft proposal` · `referee` ·
`project approved` · `assign work` · `iterate experiment` · `run verification` · `progress report` ·
`route feedback` · `conduct check <gate>`.

## Alerts & scheduling
Cadenced reports/meetings and milestone reminders are set up as scheduled tasks; the alert map lives in
each project's `POST_AWARD_PLAN.md` so the *right human* is pinged at the right time.

## Human-in-the-loop, always
No call pursued, idea chosen, email sent, proposal submitted, task assigned, report released, or claim
made beyond its evidence — without the responsible human.
