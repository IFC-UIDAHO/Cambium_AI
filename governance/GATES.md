# Human Approval Ledger (the gates)

*Human-in-the-loop, recorded and delegated by role (see ROLES.md). The Orchestrator must NOT proceed
past a gate until the named approver records it here. `validate.py` treats an open P0 or a missing
required gate as a blocker. An empty "Approved by" = NOT approved.*

There are **8 gates (G0–G6, plus G3a)**. G0 is new in v3: Cambium does not brainstorm until the PI is known.

**Presentation format:** every gate is presented with the fixed one-pager `templates/GATE_SUMMARY.md` (Decision needed · Where we are · Options · Risks · Evidence & confidence · Recommendation · APPROVE/REVISE/REJECT). Approval is then recorded in the table below.

| Gate | Decision | Approver role | Approved by (name) | Date | Notes |
|---|---|---|---|---|---|
| G0  | is the PI profile ready?   | Director       |  |  | USER_PROFILE.md exists |
| G1  | pursue this RFP?            | Director       |  |  |  |
| G2  | which idea advances?       | Director (+Co-PIs) |  |  |  |
| G3a | who to contact?            | Director       |  |  |  |
| G3  | finalize & submit proposal | Director only  |  |  |  |
| G4  | apply fixes (workstream)   | Area Lead (that Aim) |  |  |  |
| G5  | release report             | Director or Area Lead |  |  |  |
| G6  | publish / external send    | Director only + co-authors |  |  |  |

Separation of duties: the author of a deliverable is not its sole approver; G3 and G6 need the Director
**plus** a second human. External sends (submit, publish, email) are always a human action.

## Approvals log
| Date | Gate | Run | Decision | Approver |
|---|---|---|---|---|
| 2026-06-26 | G2 | agentic-os-adoption | APPROVE — adopt A (pause/resume handoff) + B (context statusline) + C (guarded auto-loop); defer D, G; reject F, H | Director (Jaslam) |

| G-fix | 2026-06-26 | Director (Jaslam) | APPROVE (Option A) | Apply Now-tier consistency fixes via Execution; stage positioning+lit-connectors (Next); defer enforcement study + per-funder corpus (Later); drop grants-discovery connectors per ROADMAP non-goal. |

| G-build | 2026-06-26 | Director (Jaslam) | APPROVE (AUTO — pre-authorized for this run) | Accept A/B-harness protocol (blind GT-only judge, 24-item pilot) + NIH/NSF corpus design (5 guardrails, funder_freshness.py hard-fail). Proceed to build. |

| G-ship | 2026-06-26 | Director (Jaslam) | APPROVE (AUTO — pre-authorized) | Ship A/B enforcement harness (result OPEN) + NIH/NSF governance corpus (source-verified, freshness-CI). |

| G-repair | 2026-06-26 | Director (Jaslam) | APPROVE | Repaired corrupted .git metadata (HEAD/index/reflog) from backups; data intact, fsck clean. Commit blocked in-sandbox by an unremovable stale index.lock (mount forbids deletes) — finish natively on Windows. |

| G-readme | 2026-06-26 | Director (Jaslam) | APPROVE | Ship world-class README rewrite (Referee 9.3/10 top-1| G-landing | 2026-06-26 | Director (Jaslam) | APPROVE | Ship index.html landing overhaul (canonical counts, modern badges, Eight gates, Proving-it box); doctor A, HTML integrity 100%. |
| G-outline | 2026-06-26 | Director (Jaslam) | APPROVE | Write the full 16-section world-class README to the approved architecture; then assets pass + verify. |
| G-ship | 2026-06-27 | Director (Jaslam) | APPROVE | Ship the world-class comprehensive README (400 lines, 16 sections; Referee accept 9s, Integrity PASS-WITH-FIXES all applied) + regenerated org-chart. |
| G-assets | 2026-06-27 | Director (Jaslam) | APPROVE | Recreate the brand asset set (mark, wordmarks, social card, favicon) at premium quality from a reproducible generator. |
| G-logo2 | 2026-06-27 | Director (Jaslam) | APPROVE | Adopt the "Governed Growth Ring" mark v2 (8 gates + PI + sweep + caught-error) across logo/wordmark/social/favicon. |
| G-logo3 | 2026-06-27 | Director (Jaslam) | APPROVE (blend) | Final "Living Tree" mark — tree of life + growth rings + 8 gates + sweep + caught-error + PI at roots. |
| G-logo4 | 2026-06-27 | Director (Jaslam) | APPROVE (use directly) | Vector recreation of the uploaded ring+node-network emblem, transparent bg, across the asset set. |
| G-logo5 | 2026-06-27 | Director (Jaslam) | APPROVE (use directly) | Adopt the official Cambium_logo.png; all derivatives built from it. |
| G-logo6 | 2026-06-27 | Director (Jaslam) | APPROVE | Hi-res official logo, cream bg keyed out, all derivatives rebuilt. |
| G-integrate | 2026-06-27 | Director (Jaslam) | APPROVE | Build the MIT-clean OpenMontage integration first slice: render-video skill + JSON contract + provisioning manifest + ADR (no AGPL code vendored). |
