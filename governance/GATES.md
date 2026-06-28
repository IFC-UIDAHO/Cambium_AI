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
| G-philosophy | 2026-06-27 | Director (Jaslam) | APPROVE | Adopt PHILOSOPHY.md (North Star + honest six-concern map + candid gaps + Section-5 design direction) as Cambium's foundational document. |
| G-positioning | 2026-06-27 | Director (Jaslam) | APPROVE | Adopt POSITIONING.md — verified Top-10 scorecard (3 Leads / 5 Partial / 2 Gaps), council-graded + integrity-audited. |
| G-repairs | 2026-06-27 | Director (Jaslam) | APPROVE | Accept the scorecard repairs: gate.py Learning-Gate enforcement, citation_support blocking, NIST bias module, regulated-data control, AI_MODEL CI, + multi-institution spec. |
| G-stage1 | 2026-06-27 | Director (Jaslam) | APPROVE | Accept inline gate cards (default), Learning-Gate auto-fire on every decision gate (Act III contract), and multi-PI Stage-1 named-approver roles (gate.py --required-approver + MULTI_PI_ROLES.yml). |
| G-support | 2026-06-27 | Director (Jaslam) | APPROVE | Accept the Support-council doc refresh (ROADMAP/README/USE_CAMBIUM), duplicate-ADR fix, and the automatic close-out (tools/closeout.py + CLOSEOUT_CHECKLIST + Act IV mandate) that fails close-out on doc drift. |
| G-threads | 2026-06-27 | Director (Jaslam) | APPROVE | Accept the Learning-Gate hard runtime lock (gate_lock.py token interlock), the A/B task set expansion 12->18, and multi-PI Stage-1.5 (roles_check.py + gate.py --roles auto-lookup). |
| G-readme-fix | 2026-06-27 | Director (Jaslam) | (drift fix) | README prose refreshed for gate_lock/roles/18-tasks; closeout.py hardened to catch README tool-count + unreferenced-tool drift. |

> **Provenance note (2026-06-28 session):** this was a rapid same-day improvement sprint. Gates marked APPROVE on 2026-06-28 carry the Director's running approval given in chat; a few early rows were recorded in-flight rather than at a hard stop. From the premium-board work onward (G-ux, G-bridge) each gate was presented and the Director clicked/typed the decision before it was recorded. Future runs stop at every gate by default.
| G-vision | 2026-06-28 | Director (Jaslam) | APPROVE | Adopt VISION.md + AI_POLICY.md as canonical — reviewer's writeup fact-checked the Cambium way (Integrity + Research-Conduct), partials hedged honestly. |
| G-enforce-all | 2026-06-28 | Director (Jaslam) | APPROVE | Make the Partial policy points enforced: pace_check.py (deliberation interval), learning_gate change-tracking (#3), data_scan.py (#6 detection), enforce.py gauntlet + CI (#2). #9 stays honestly Partial. |
| G-dean | 2026-06-28 | Director (Jaslam) | APPROVE | Ship the dean's three changes: 5-minute demo (README top), evaluation/benchmark dashboard (assets/benchmark_dashboard.html, real numbers + honest A/B Open), and one-command quickstart `/cambium run example`. Integrity audit fixed a README↔dashboard test-count contradiction (now 168 everywhere). |
| G-dashboard-auto | 2026-06-28 | Director (Jaslam) | APPROVE | Make the eval dashboard self-updating: tools/gen_dashboard.py regenerates assets/benchmark_dashboard.html from live tool output; CI regenerates + git-diffs so the dashboard can never drift from reality. |
| G-ui | 2026-06-28 | Director (Jaslam) | APPROVE | Ship the /cambium first-paint fix (cambium_start.py + command/PRESENTATION rewrite) and the two genuine review gaps: audit_log.py (turn-level hash-chained trail) + draft_diff.py (AI-vs-human document change ledger). Review mapping in REVIEW_RESPONSE.md. |
| G-demo-gif | 2026-06-28 | Director (Jaslam) | (asset) | Added assets/demo_example.gif (real recording of `cambium_run.py example`) + tools/gen_example_gif.py; reworded the README 5-minute demo so the ▶ section has something to watch instead of implying a missing video. |
| G-resume | 2026-06-28 | Director (Jaslam) | APPROVE | Ship the enforced --resume loop (gate_lock require + pace_check), gate.py --mint as the approval act, audit_log wiring + CAMBIUM_USER identity, and the honest 14-point REVIEW_RESPONSE2 with Stage-2 deferrals named in ROADMAP. |
| G-ux | 2026-06-28 | Director (Jaslam) | APPROVE | Ship the premium run board (gen_board_pro.py) + interactive gate as the default Cambium experience; wired into cambium_start first-paint with a routed-plan fallback. Run was painted as a live artifact and stopped at this gate for real. |
| G-bridge | 2026-06-28 | Director (Jaslam) | APPROVE | Ship the Cambium Web App backend: FastAPI bridge (web/server) + connected 3D front-end (web/frontend) + API.md/README/Dockerfile. Proven end-to-end against a real uvicorn server (POST /run → WS stream → gate pause → POST decide → resume). |
| G-harden | 2026-06-28 | Director (Jaslam) | APPROVE | Accept the consolidate & harden pass: README counts fixed (22 skills, gen_brand_assets documented), dashboard regenerated, honest gate-ledger provenance note added, web app deferred to ROADMAP with assets kept. |
| G-improve | 2026-06-28 | Director (Jaslam) | APPROVE | Accept three core improvements: VERIFICATION_PROTOCOL.md (reproduce-the-numbers), evals v1 A/B design (powered, human-judged, ~95/arm), and FIRST_RUN.md Director onboarding. Integrity-audited; AI_MODEL attribution fix applied. |
| G-study-v1 | 2026-06-28 | Director (Jaslam) | APPROVE | Execute the v1 A/B study infrastructure: task set 18→102 (gen_tasks.py, 20/core category, objective ground truth), blind.py (sealed manifest, no arm leak), rater_ui.html (arm-blind), analyze_stage2.py (Cohen's κ + adjudication + pre-registered z/h/CIs/Bonferroni), BUDGET.md (~31 rater-hours; compute ~$3–$13), verify_pipeline.py (E2E PASS). verify-evidence audit PASS; tautology-overclaim corrected. Study RESULT stays Open: needs live model runs + 2 human raters + adjudicator. |
| G-runux | 2026-06-28 | Director (Jaslam) | APPROVE | Ship the premium in-chat run board as the default /cambium experience: gen_inline_board.py (agent boxes + progress + live gate as a show_widget fragment), upgraded clickable INLINE_GATE_CARD.html, gen_board_pro findings-feed + completion summary, and PRESENTATION/command wiring so every run paints the in-chat board + reopenable sidebar artifact. Cinematic 3D web app stays on the roadmap. Verified: renders, HTML parses, consistency green. |
