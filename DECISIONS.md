# Cambium — Decision Records (ADR)
*A living log of the load-bearing decisions, so any Claude account (or human) can see WHY, not just what.
Append a new entry for every meaningful architectural/governance decision. Template: templates/DECISION_RECORD.md.*

## ADR-001: Council-based, human-gated institution (not a free agent swarm)
- Date: 2026-06 · Status: Accepted · Decider: Director
- Context: needed a research org, not just "many agents."
- Decision: organize as 11 councils / 46 agents under an Orchestrator, with 8 human gates (G0–G6) and an evidence contract.
- Consequences: every phase stops for a human; nothing ships without approval. Do NOT remove the gates.

## ADR-002: Evidence-tiered output contract, enforced in CI
- Date: 2026-06 · Status: Accepted
- Decision: claim tiers (Proved/Code-verified/Asserted/Open); `governance/validate.py` fails the build on open P0,
  un-evidenced "Code-verified", or unresolved citations.
- Consequences: honesty is a check, not a convention.

## ADR-003: Adopt verified ideas from peer systems
- Date: 2026-06 · Status: Accepted
- Decision: Elo idea-tournament (← AI Co-Scientist), referee/reproducibility/novelty gates (← AI Scientist),
  budget-aware verification (← Agent Lab), Toolsmith provisioning (reuse-beats-rebuild), Task Router, `doctor` self-check
  (← ECC/ruflo metaharness). NOT adopted: becoming a harness/swarm engine — Cambium stays the research-institution layer.
- Consequences: Cambium is the domain layer; it can run ON harnesses like ECC/ruflo, not replace them.

## ADR-004: Multi-account continuity via files + git (not a shared server, yet)
- Date: 2026-06 · Status: Accepted
- Decision: state lives in the repo (PROJECT_STATE/ledger/GATES/ADR); multiple Claude accounts continue from files.
  Hosted multi-user (server+DB+SSO) is a future phase.
- Consequences: works offline today; per-user accounts run agents on their own login (no shared keys).

## ADR-005: Set aside the web-app build; keep the core institute
- Date: 2026-06 · Status: Accepted · Decider: Director
- Decision: moved app/, campus.html, and the app plans to a recoverable trash folder; kept agents, governance, tools, docs.
- Consequences: focus stays on the institute + framework; the app can be revived from trash if wanted.

## ADR-006: Ship an MCP server (alongside the plugin)
- Date: 2026-06 · Status: Accepted · Decider: Director
- Context: Cambium was plugin/template only; users asked to also expose it like the many `npx`/MCP tools they see.
- Decision: add `mcp_server/` — a Python MCP server (official `mcp` SDK / FastMCP, stdio) exposing cambium_plan,
  provision, agents, doctor, grade, validate. Installable via `python -m cambium_mcp.server` or `uvx cambium-mcp`.
- Consequences: Cambium is now usable FROM other AI apps (Claude Desktop/Code, Cursor), not just as a plugin.
  Stays the research-institution domain layer; the MCP is a thin wrapper over existing tools.

## ADR-007: Add real citation verification (SemanticCite) behind a gate -- ACCEPTED
- Date: 2026-06-26 - Status: **Accepted** (human approved 2026-06-26, Director)
- **Implemented (additive, optional, advisory):** `tools/cite_check.py` (import-guarded shim: semanticcite -> local Ollama -> deterministic lexical fallback / advisory no-op; writes `governance/cite_audit.json`; optional non-destructive `<ledger>.cited.csv` sidecar). `governance/validate.py` honors an optional `citation_support` column as an ADVISORY WARNING (never a blocker; absent column = back-compat no-op). One optional line on the `verify-evidence` card (count stays 46). ARS refinements folded in: per-claim `locator` anchors + calibrated 20-tuple gold set (`tests/fixtures/cite_gold.csv`, FNR<0.15/FPR<0.10) + `tests/test_cite_check.py`. SemanticCite recorded at the provisioning gate but NOT installed (TOOL_POLICY.md). Green: consistency 46-11-8, doctor healthy, pytest.

## ADR-008: Add an Interpretation-Fallacy Checklist (experiment-agent ADAPT) -- ACCEPTED
- Date: 2026-06-26 · Status: **Accepted** (human approved 2026-06-26, Director) · Decider: Director
- Context: scan of `experiment-agent` (https://github.com/Imbad0202/experiment-agent, CC-BY-NC-4.0). Its `run`/`manage`/repro-rerun capabilities **duplicate** Cambium's exec-experiments + research-engineer + research-conduct-officer + `lab-statistics` + `verify-rigor` + `templates/REPRODUCIBILITY_CHECKLIST.md` (router grounded: the task routes through 18 agents). The ONE narrow real gap: `grep -ri "fallacy|simpson|survivorship"` = 0 hits — Cambium audited "rigor" abstractly but enumerated no **interpretation-fallacy** taxonomy for a reviewer to run against a results section.
- **Implemented (additive, optional, advisory, framework-only, no CC-BY-NC content copied):** new `templates/INTERPRETATION_FALLACY_CHECKLIST.md` (freshly authored; ~12 fallacies: Simpson's, ecological, survivorship/selection, base-rate neglect, multiple-comparisons/p-hacking, HARKing, optional-stopping, regression-to-mean, confounding, correlation≠causation, overfitting-as-result, significance≠importance), mirroring the REPRODUCIBILITY_CHECKLIST pattern. `governance/validate.py` honors an optional `fallacy_check` column as an ADVISORY WARNING (never a blocker; absent column / clean value = back-compat no-op), mirroring ADR-007's `citation_support`. One optional reference line each on `.claude/agents/34-lab-statistics.md` and `.claude/agents/07-verify-rigor.md` (count stays 46). Tests `test_validate_fallacy_flag_is_advisory_not_blocker` + `test_validate_fallacy_clean_is_silent` in `tests/test_framework.py`. No dependency/install (prose checklist). Counts unchanged: 46·11·8.
- Consequences: reviewers now have a concrete fallacy checklist that lab-statistics runs before reporting numbers and verify-rigor runs when breaking a results claim; fully back-compat (ledgers without the column behave exactly as before). meta-research (https://github.com/AmberLJC/meta-research) evaluated same scan → SKIP (duplicates LIFECYCLE_V3 + phases.yml; "autonomous" framing conflicts with ADR-001/ADR-003). Detail: `cambium_imp/skill-scan/2026-06-26-1046.md`. Green: consistency 46-11-8, doctor healthy, pytest.

## ADR-008: Visible gate UX + live run-trace (transparency)
- Date: 2026-06 · Status: Accepted (Director approved) · Decider: Director
- Context: A non-technical user couldn't tell when "Cambium" was working vs plain Claude, and couldn't see what was happening behind a request.
- Decision: (1) one fixed gate one-pager `templates/GATE_SUMMARY.md`, mandated by the Orchestrator + OUTPUT_CONTRACT (kills cross-agent variance). (2) `tools/run_trace.py` — turns any request into a workflow in 4 forms: text checklist (any chat), Mermaid (GitHub/Claude Code), SVG picture (Cowork), and a LIVE status board (`--status N`: ✓ done · ▶ now working + "NOW with <council/agents>" · ○ waiting). Orchestrator shows the plan first and re-emits the live board as it advances. Plus `USE_CAMBIUM.md`, a jargon-free beginner guide.
- Consequences: every interface shows who is working now and where the human decides. Reuse-first: run_trace wraps task_router (no new engine). 24 tests, doctor healthy, counts 46·11·8.

## ADR-009: Toolsmith design stack + dashboard live run-view
- Date: 2026-06 · Status: Accepted (Director approved) · Decider: Director
- Context: Toolsmith recommended stats packages for design tasks (a blind spot); dashboard didn't show a live run.
- Decision: (1) toolsmith.py gains a `design` stack (brand-guidelines, canvas-design, ckmdesign/banner, theme-factory, ui-ux-pro-max, cairosvg, Pillow) + keyword detection, so visual-design tasks reuse real skills not statsmodels. (2) dashboard.html gains an animated, client-side "live run-view" (✓ done · ▶ now working · ○ waiting) so anyone opening it sees a run progress.
- Consequences: reuse-beats-rebuild now works for design; the dashboard demonstrates live progress. 26 tests, doctor healthy, HTML intact, counts 46·11·8.

## ADR-010: Standardize the run-view to the canonical council structure
- Date: 2026-06 · Status: Accepted (Director approved) · Decider: Director
- Context: run_trace showed ad-hoc internal labels (intake/ideate/PI/write/review/build/ux/stats) that do not match Cambium's real org — confusing, inconsistent ("1000 different items").
- Decision: every view (text/Mermaid/SVG/live-status + dashboard) now labels each step by its CANONICAL COUNCIL (reverse-mapped from task_router.CMAP — single source of truth) and merges consecutive same-council steps. Fixed structure everywhere: You → Orchestration → [the 11 councils as needed] → 8 gates → Delivered.
- Consequences: one standard vocabulary across chat/GitHub/dashboard; far fewer items; mirrors INSTITUTE.md (Director → councils → agents → gates). 26 tests, doctor healthy, counts 46·11·8.

## ADR-011: Consistency sweep — one vocabulary (Verification council)
- Date: 2026-06 · Status: Accepted (Director approved at gate G-fix) · Decider: Director
- Context: Verification sweep found 11 namings/version inconsistencies that consistency_check (counts-only) misses.
- Decision (applied): human role unified to **Director** (was President); Orchestrator council label unified (was "Provost"); council display names unified to the bare README set (Pre-Award, Partnerships, Reporting, Support); run_trace reserves "GATE" for the canonical 8 (G0–G6+G3a) and labels task-specific approvals "Checkpoint"; INSTITUTE.md stage table gains the G0 row; plugin manifests bumped 3.8.0→3.9.0; dashboard hero/literals moved off old navy hex to green tokens.
- Consequences: chat, GitHub, dashboard, charter, agents now use identical terms. check_agents OK · consistency OK · doctor healthy · 26 tests pass · counts 46·11·8.

## ADR-012: Support council runs automatically at close-out
- Date: 2026-06 · Status: Accepted (Director approved) · Decider: Director
- Context: across this session the housekeeping (CHANGELOG, README freshness, hygiene) was done by the orchestrator by hand; the Support council never ran its part, so docs drifted (stale "18-test", missing new tools).
- Decision: the Orchestrator now treats Support close-out as part of "done" — after any accepted change, Record-Keeper logs the CHANGELOG, Outreach refreshes user-facing docs, Integrity-Officer verifies numbers, Janitor checks hygiene. The human should not have to remember it.
- Consequences: docs stay in sync automatically; this session's drift fixed (README 18→26-test + new tools/guide; CHANGELOG 3.10.0). 26 tests, doctor healthy.

## ADR-013: Output-Coverage Checklist + decision-record integrity (Paper Circle / Graphiti ADAPT) -- ACCEPTED (implementation pending)
- Date: 2026-06-26 · Status: **Accepted** (Director approved 2026-06-26) — **implementation PENDING**, to be done in a normal dev session, NOT in the autonomous self-improve run (the gated items touch `templates/`, `.claude/agents/08-verify-evidence.md`, and `governance/validate.py`, which the autonomous run must not edit, and `pytest` must be run before publishing). · Decider: Director
- Context: 2026-06-26 1706 self-improvement scan of three NEW in-lane candidates. **ckg-mcp** (https://github.com/Yarmoluk/ckg-mcp, MIT) → **SKIP**: a pre-compiled-KG MCP routing layer duplicates `task_router.CMAP` (the ADR-010 "single source of truth," rendered by run_trace); its 53 bundled domains are off-domain; adopting = a third-party MCP install with no fit. **Graphiti** (https://github.com/getzep/graphiti, Apache-2.0, 27.8k★) → **ADAPT (concept only)**: the engine itself (Neo4j/FalkorDB + Docker + API key) is **re-architecture (forbidden)** and conflicts with ADR-004 (file-based, offline-first continuity) and ADR-003 (domain layer, not infra) — but its bi-temporal-fact + supersession-provenance concept exposes a live defect: `templates/DECISION_RECORD.md` prescribes `Superseded by ADR-<n>` yet nothing enforces it, and `DECISIONS.md` currently has **two ADR-008 headings**. **Paper Circle** (https://arxiv.org/abs/2604.06170) → **ADAPT (concept only)**: its multi-agent analysis duplicates Cambium's councils + REPRODUCIBILITY_CHECKLIST, but its **CoverageChecker** (figure/table/section/equation coverage, "no silent omissions") fills a real gap — `grep -riE "coverage|omission|completeness"` finds no deliverable-completeness check; Cambium audits rigor (ADR-008) and citations (ADR-007) but not whether an output delivers everything it promised.
- **Proposed (gated; NOT implemented; framework-only; no third-party content copied; nothing installed; counts stay 46·11·8):** (1) new `templates/OUTPUT_COVERAGE_CHECKLIST.md` (freshly authored; figures/tables present + captioned, all promised sections/appendices delivered, every abstract claim supported in body, all OUTPUT_CONTRACT deliverables attached, no placeholders, cross-refs resolve), mirroring REPRODUCIBILITY/FALLACY checklist pattern, consulted by verify-evidence/referee before G5; (2) one optional reference line on `.claude/agents/08-verify-evidence.md` (count stays 46); (3) an advisory-only **decision-record integrity check** (read-only): ADR ids unique + `Superseded by ADR-<n>` links resolve, surfaced as a WARNING never a blocker, like ADR-007/008 columns — would have caught the duplicate ADR-008; (4) **housekeeping (human-owned):** renumber the duplicate ADR-008 — flagged only, NOT auto-applied (renumbering canonical decisions is the human's call).
- Acceptance: checklist catches a planted omission while clean outputs stay green; integrity check flags the duplicate ADR-008 while clean files stay silent; `consistency_check`, `doctor`, and the test suite stay green with template/column absent (back-compat). Detail: `cambium_imp/skill-scan/2026-06-26-1706.md`. This run: consistency 46·11·8 OK, doctor 21-ok/0-problem healthy; `pytest` not runnable in this sandbox (not installed; install forbidden) — re-run in the dev env before publishing. Only `.md` files written this run.
