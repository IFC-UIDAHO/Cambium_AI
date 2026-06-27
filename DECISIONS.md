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
- Date: 2026-06 · Status: Accepted (Director approved) · Decider: Director
- Context: Verification sweep found 11 namings/version inconsistencies that consistency_check (counts-only) misses.
- Decision (applied): human role unified to **Director** (was President); Orchestrator council label unified (was "Provost"); council display names unified to the bare README set (Pre-Award, Partnerships, Reporting, Support); run_trace reserves "GATE" for the canonical 8 (G0–G6+G3a) and labels task-specific approvals "Checkpoint"; INSTITUTE.md stage table gains the G0 row; plugin manifests bumped 3.8.0→3.9.0; dashboard hero/literals moved off old navy hex to green tokens.
- Consequences: chat, GitHub, dashboard, charter, agents now use identical terms. check_agents OK · consistency OK · doctor healthy · 26 tests pass · counts 46·11·8.

## ADR-012: Support council runs automatically at close-out
- Date: 2026-06 · Status: Accepted (Director approved) · Decider: Director
- Context: across this session the housekeeping (CHANGELOG, README freshness, hygiene) was done by the orchestrator by hand; the Support council never ran its part, so docs drifted (stale "18-test", missing new tools).
- Decision: the Orchestrator now treats Support close-out as part of "done" — after any accepted change, Record-Keeper logs the CHANGELOG, Outreach refreshes user-facing docs, Integrity-Officer verifies numbers, Janitor checks hygiene. The human should not have to remember it.
- Consequences: docs stay in sync automatically; this session's drift fixed (README 18→26-test + new tools/guide; CHANGELOG 3.10.0). 26 tests, doctor healthy.

## ADR-013: Installable-everywhere (real-world install fixes)
- Date: 2026-06 · Status: Accepted · Decider: Director (from two real install sessions)
- Context: Cambium would not install cleanly. Three independent packaging/instruction bugs surfaced only when
  real users tried: (1) two plugin.json (root + plugin/) → Cowork "Found 2"; (2) `agents` manifest field
  rejected as string AND as array-of-dir; (3) README told users the SSH-resolving short form and stacked commands.
- Decision: one manifest at repo root (`.claude-plugin/`), agents auto-discovered from `agents/` (no manifest
  field), and a tested INSTALL.md covering Cowork (Add-marketplace-from-repository + /create-cowork-plugin),
  Claude Code (HTTPS, separate lines, user scope), and the honest manual-update story. README points to it.
- Consequences: `cambium-institute` installs directly from the public repo in Cowork and Claude Code. Two agent
  dirs exist (`.claude/agents` source + `agents/` plugin copy) — kept in sync at package time. 28 tests, doctor A.

## ADR-014 - Council-labelled dispatch so live cards match the run_trace board
- Context: user saw Cowork's native "Running 6 agents" cards (raw per-task labels) during a Verification run and
  expected the styled council board. The native widget is Anthropic's and a plugin can't replace it; but its card
  titles come from the per-dispatch task description the Orchestrator writes.
- Decision: mandate dispatch labels of the form "<Council> · <Role>" in 00-orchestrator.md (synced to plugin
  agents/ copy). No change to the 46 agent frontmatter descriptions (avoids perturbing agent selection).
- Consequences: live cards now read "Verification · Referee" etc., matching the run_trace vocabulary. Version
  bumped to 3.11.1 so installed copies see an Update. Native widget still owns moment-to-moment display; the
  styled board remains the full-journey + gates map; dashboard.html stays a static reference.
k-only; no third-party content copied; nothing installed; counts stay 46·11·8):** (1) new `templates/OUTPUT_COVERAGE_CHECKLIST.md` (freshly authored; figures/tables present + captioned, all promised sections/appendices delivered, every abstract claim supported in body, all OUTPUT_CONTRACT deliverables attached, no placeholders, cross-refs resolve), mirroring REPRODUCIBILITY/FALLACY checklist pattern, consulted by verify-evidence/referee before G5; (2) one optional reference line on `.claude/agents/08-verify-evidence.md` (count stays 46); (3) an advisory-only **decision-record integrity check** (read-only): ADR ids unique + `Superseded by ADR-<n>` links resolve, surfaced as a WARNING never a blocker, like ADR-007/008 columns — would have caught the duplicate ADR-008; (4) **housekeeping (human-owned):** renumber the duplicate ADR-008 — flagged only, NOT auto-applied (renumbering canonical decisions is the human's call).
- Acceptance: checklist catches a planted omission while clean outputs stay green; integrity check flags the duplicate ADR-008 while clean files stay silent; `consistency_check`, `doctor`, and the test suite stay green with template/column absent (back-compat). Detail: `cambium_imp/skill-scan/2026-06-26-1706.md`. This run: consistency 46·11·8 OK, doctor 21-ok/0-problem healthy; `pytest` not runnable in this sandbox (not installed; install forbidden) — re-run in the dev env before publishing. Only `.md` files written this run.

## ADR-015 - Smart-default mode selection, with honest reliability bounds
- Context: a plugin cannot force an interactive "Solo or Cambium-way?" popup on every message; skill
  triggers are model-judged, so the ask fired inconsistently. User chose a smart default over
  always-ask / always-Cambium.
- Decision: encode the smart default in skills/cambium-mode/SKILL.md — trivial→Solo silent,
  substantial→ask once→remember; document the default in USE_CAMBIUM.md; keep /solo & /cambium as the
  deterministic guarantee. No hard hook (Cowork support uncertain; would add complexity for <100% gain).
- Consequences: predictable behavior for new users; the ask still won't fire 100% of the time, but the
  documented default + one-way override make that safe. Version 3.11.2.

## ADR-016 - Routing coverage: deliberate council use, guarded against regression
- Context: a coverage audit of task_router.py found Support routed in only 3/6 task types (via toolsmith
  only) and 13 orphan agents, while close-out was mandated in prose but never in the plan. Nothing was
  over-used (no agent in 5+/6 types), so the fix was additive, not a trim.
- Decision: add _closeout() (record-keeper, integrity-officer, janitor) to every task type via
  plan_for_type(); add _writeup() (document-office, librarian, figures) to research/report/data; add
  librarian+figures to grant; add tests/test_router_coverage.py as a regression guard. Leave 7 on-demand
  agents unrouted by design. Ran the Cambium way; approved at a human gate.
- Consequences: all 11 councils reachable; Support 6/6; plan now reflects close-out. No new human gates.
  Version 3.11.3.

## ADR-017 - Add quantitative built-in skills (math, statistics, ML); curate web rather than rebuild
- Context: user requested skills for math, statistics, ML, web, UI/UX, software. Inventory of the live
  setup showed UI/UX (ui-ux-pro-max, ckmdesign), web (web-artifacts-builder), and software (the packaged
  software-engineering plugin) already covered; the real gaps were mathematics (nothing installed) and
  rigorous statistics / leak-free ML (data plugin is analysis-flavored). Ran the Cambium way; Scouts
  surveyed 8 skill marketplaces; approved at a gate (Option B).
- Decision: BUILD three skills under skills/ (mathematics, statistics, machine-learning) emphasizing
  deterministic computation, assumption checks, and leakage guards; CURATE web/frontend by pointing to
  vetted external skills in SKILLS_MAP.md rather than bundling untrusted code. Skills auto-discover via
  skills/*/SKILL.md; no agent changes.
- Consequences: Cambium ships exact-math + defensible-stats + honest-ML capability. Version 3.12.0.
  Marketplaces referenced: awesomeclaude.ai, github.com/travisvn/awesome-claude-skills,
  github.com/Data-Wise/claude-plugins.

## ADR-018 - Built-in skill coverage for every council (wave 2)
- Context: user asked to think through all councils/agents and implement every skill they need. A
  coverage map showed Faculty/Scouts/Reporting/Labs(stats,theory) covered by installed + wave-1 skills,
  leaving 8 real gaps. Ran the Cambium way; approved at a gate.
- Decision: BUILD 8 skills (optimization, reproducibility, citations, data-management, grant-writing,
  research-ethics, project-management, scientific-writing) under skills/, each owned by a council and
  written around correctness/honesty guardrails. Did NOT build skills where installed ones already
  suffice (UI/UX, web, software-eng, figures, decks, teaching) to avoid bloat.
- Consequences: all 11 councils now have >=1 dedicated skill; 12 skill dirs total (incl. cambium-mode
  + wave 1). Auto-discovered via skills/*/SKILL.md; no agent changes. Version 3.13.0.

## ADR-019 - Provision skills on demand instead of pre-stocking a giant catalog
- Context: there are effectively unlimited domains (silviculture, wildlife, soil science, entomology,
  pathology, engineering, web tools, dashboards, ...). Pre-building a skill for each is unmaintainable
  bloat and a security risk. User proposed: detect need from the request, offer + create skills on demand,
  user approves. Chosen settings: both tiers (instant + persistent), detect-and-offer-once.
- Decision: add skills/skill-provisioner as the front door, coordinating faculty-expert (instant domain
  expertise), toolsmith (install vetted existing skills), and skill-creator (author new ones). Persistence
  via SKILL.md; honest about the reload/reinstall needed to register a newly created skill.
- Consequences: Cambium grows to fit each user instead of shipping everything. No giant catalog. Version
  3.14.0. Reuse-beats-rebuild and human-approval-before-install are enforced by the skill.

## ADR-020 - New skills: repo is canonical; local activation is opt-in, never auto
- Context: should skill-provisioner auto-write created skills into the user's personal/global skills
  folder for faster registration? Deliberated the Cambium way across Governance, Verification, Support,
  Faculty(systems), Outreach.
- Decision: NO auto-write. The Cambium repo skills/ is the single canonical, CI-checked home. Offer an
  explicit, per-skill "activate it locally now" that (only on a yes) also places that one skill in the
  project's .claude/skills/ (or personal skills dir) so it registers after a reload. Never silent,
  automatic, or bulk.
- Rationale: honors human-approval-before-config-change and single-source-of-truth/governance; still
  solves the user's speed concern via an opt-in fast path. Faculty noted personal skill paths are
  platform-dependent/sometimes protected, so silent writes are unreliable anyway.
- Consequences: skill-provisioner updated to encode this. Version 3.14.1.

## ADR-021: A presentation contract for the Cambium way (real agents, live board)
- Date: 2026-06 · Status: Accepted · Decider: Director
- Context: the Cambium way looked generic to users — opaque "Used N tools / Created 3 files" lines, no named
  agents, no visible plan or live progress. The machinery existed (run_trace, councils) but runs did work
  inline and only narrated councils in prose, so no real agent cards ever appeared.
- Decision: codify PRESENTATION.md (four acts) and make it binding on commands/cambium.md + the Orchestrator:
  (1) always open with the live run board before any work; (2) dispatch the REAL sub-agents
  (`cambium-institute:<name>`, labelled `Council · Role`) — never fake the names by working inline; (3)
  re-emit the board every phase and at the gate. All views come only from tools/run_trace.py and
  templates/GATE_SUMMARY.md so the vocabulary never drifts.
- Consequences: more sub-agent dispatch (higher token cost) in exchange for an authentic, legible, identical
  run experience. Do NOT revert to inline work for the Cambium way — that is the regression this fixes.

## ADR-022: Run-board state is auto-populated, not hand-maintained
- Date: 2026-06 · Status: Accepted · Decider: Director
- Context: the live board needed per-agent findings, but hand-editing state JSON each phase is brittle and
  easy to skip — which would quietly regress the Cambium way back to a generic-looking run.
- Decision: agents already write agent_outputs/<name>.md with a "## Decision" headline; tools/run_state.py
  `sync` lifts that line into agent_outputs/run_state.json automatically, and run_trace.py auto-discovers
  that file. The Orchestrator's loop is phase → dispatch → sync → re-emit. State is git-ignored (per-run).
  A release GitHub Action regenerates the README board imagery so it never drifts from the real roster.
- Consequences: the board stays honest and current with near-zero manual bookkeeping; the only authored
  bits are the optional leaderboard and the gate decision text. Do NOT reintroduce mandatory hand-edited
  state JSON.

## ADR-023: Adopt durable handoff memory + guarded autonomy from the "Agentic OS" scan
- Date: 2026-06-26 · Status: Accepted · Decider: Director (gate G2)
- Context: a YouTube "Agentic OS" build (Seed/Paul/Graphify/Hermes) was evaluated the Cambium way. Scouts +
  Faculty + idea-tournament + Integrity found most of it redundant or out-of-scope for a governed,
  human-gated research plugin (Cambium is not a web app), but three real gaps stood out. Prior art showed
  the handoff/memory pattern is commodity (Cline Memory Bank, RooFlow, LangGraph, Claude Code memory), so we
  emulate the best-in-class, Cambium-native, not Paul's single-developer implementation.
- Decision: adopt (A) pause/resume HANDOFF + archive, (B) context status line with proactive pause, (C) a
  guarded per-phase auto-loop that never auto-clears a gate; defer plan→task-graph deps and the
  Obsidian/Graphify brain; reject /seed (redundant with the pre-award lifecycle) and Hermes/Railway deploy.
- Consequences: long runs survive context limits without lossy compaction; throughput rises inside a phase
  while every gate stays a human APPROVE; single-writer run_state.json avoids multi-agent races. Do NOT let
  the auto-loop clear gates, and do NOT chase the "agentic OS dashboard/deploy" framing — Cambium is a
  governed institution, not a hosted app.

## ADR-024: Cambium way runs end-to-end (the post-gate build is not silently solo)
- Date: 2026-06-26 · Status: Accepted · Decider: Director
- Context: in the agentic-os adoption run, the pre-gate evaluation correctly used real dispatched agents, but
  the post-approval BUILD was done inline (effectively solo). The Director ruled this a violation: choosing
  the Cambium way must mean Cambium for the entire task, build included.
- Decision: the Orchestrator dispatches real Execution/Labs agents for post-gate implementation too; it may
  never drop to solo silently. If solo is genuinely better for a trivial mechanical step, it must ASK the
  Director first and honor the answer. Codified across PRESENTATION.md, commands/cambium.md, the Orchestrator,
  and the cambium-mode skill.
- Consequences: consistent, auditable, end-to-end runs; slightly higher token cost on build phases, accepted
  as the price of the guarantee. Do NOT reintroduce silent inline builds under the Cambium way.

## ADR-025: Now-tier consistency sweep + Execution build contract (gate G-fix)
- Date: 2026-06-26 · Status: Accepted (Director approved at gate G-fix) · Decider: Director (Jaslam)
- Context: A landscape review surfaced stale-doc inconsistencies (gate count, "President" regression,
  version/agent-count drift) and, during the post-gate build, the Execution agent shipped a truncated patch
  (SyntaxError, grade dropped to B) and a record-keeper agent claimed CHANGELOG/ADR writes it did not make
  (it instead corrupted ADR-011's status line). Both were caught by orchestrator-side live verification.
- Decision: (1) apply the Now-tier consistency fixes repo-wide toward canonical truth (46 agents · 11
  councils · 8 gates · "Director (PI)"); (2) harden consistency_check.py against the "<word> lifecycle gates"
  drift class; (3) add an Execution build contract (research-engineer + run-lab): chunk edits for files >40
  lines and verify-or-flag (paste real check output as Code-verified, else mark Asserted and hand to the
  Orchestrator); (4) re-sync the agents/ mirror; (5) repositioning is staged and must be claim-tiered — no
  comparative "beats soft-prompting" claim until the A/B enforcement study is Code-verified; (6) grants-
  discovery connectors dropped per the ROADMAP non-goal; (7) the per-funder governance corpus is permitted
  Later only with dating + named owner + freshness-as-CI-blocker + a non-certification disclaimer.
- Consequences: governance docs now state their own mechanism correctly; truncated/over-claimed builds are
  guarded by an explicit contract plus close-out re-verification. consistency_check exit 0 · doctor GRADE A ·
  36 tests pass · roster 46/46 in sync.
  Reporter, Piv
## ADR-026: Ship the enforcement A/B harness (result Open) + per-funder governance corpus
- Date: 2026-06-26 · Status: Accepted (Director pre-approved gates G-build + G-ship for this run) · Decider: Director (Jaslam)
- Context: the landscape review named two Later-tier assets as the durable moat: (1) PROOF that hard
  enforcement beats soft prompting, and (2) a living per-funder governance corpus. Both were deferred; the
  Director authorized building them now, auto-approving the run's gates.
- Decision: (A) ship a pre-registered enforcement-vs-soft-prompting A/B HARNESS (evals/enforcement_study/) —
  protocol + seeded-defect task set with locked ground truth + metrics + a fixture-driven runner — with the
  study RESULT explicitly **Open**: the harness is Code-verified (it runs in CI), but the comparative finding
  does not exist until real agent runs are done, and the README/positioning may NOT claim "beats prompting"
  until then. (B) ship the per-funder governance corpus (governance/funders/, NIH+NSF) with the five
  mandated guardrails (dating, named owner, quarterly cadence, freshness window, non-certification
  disclaimer) and a hard-failing freshness CI (tools/funder_freshness.py) so it is fail-safe under drift.
  NIH NOT-OD-25-132 and the NSF reviewer gen-AI prohibition were source-verified before sign-off.
- Consequences: the central enforcement claim is now continuously measurable instead of merely asserted;
  the corpus cannot silently rot. Owner duty: the PI must re-verify each funder entry quarterly or CI fails.
  Result honesty is load-bearing — do NOT report the demo fixtures as a finding. consistency exit 0 ·
  doctor GRADE A · pytest 104 pass · funder_freshness OK · run_study --demo OK.

## ADR-027: Run-board state is reset per run (no cross-run findings leak)
- Date: 2026-06-26 · Status: Accepted (Director approved) · Decider: Director (Jaslam)
- Context: the live run board pulls from a single `agent_outputs/run_state.json`. Across several runs in one
  session it was never reset, so `sync` (which lifts findings from every `agent_outputs/*.md`) re-surfaced
  earlier runs' findings and left later template phases marked TODO — the board misrepresented a finished run.
  The working mount cannot delete the stale files, so simple cleanup wasn't possible mid-session.
- Decision: `run_state.py reset` stamps `started_at`; `sync` skips files older than it; the Cambium-way
  contract resets state at the start of Act I. Guarded by `tests/test_run_state.py`.
- Consequences: each run's board reflects only that run. Boards are a per-run view, not a cumulative log;
  durable history stays in CHANGELOG/DECISIONS/GATES. Counts unchanged 46·11·8.

## ADR-028: Integrate OpenMontage as an external, process-isolated AGPLv3 tool (MIT-clean)
- Date: 2026-06-27 · Status: Accepted (Director approved at gate G-integrate) · Decider: Director (Jaslam)
- Context: OpenMontage (https://github.com/calesthio/OpenMontage) is an open-source agentic video-production
  system — architecturally a sibling of Cambium (pipelines/director-skills/registry-tools, 7-dim scored
  provider selection, quality gates + post-render self-review, decision-audit trail, budget governance).
  It is **AGPLv3**; Cambium is **MIT**. Councils (Toolsmith, Faculty/architecture, Research-Conduct-Officer)
  converged on integrating it for video deliverables (video abstracts, grant-pitch videos, results explainers).
- Decision: integrate by **invocation, not incorporation** — a single Cambium skill `skills/render-video/`
  (Reporting council; consumed by Outreach) shells out to a **separately user-installed** OpenMontage across a
  process boundary, crossing a versioned JSON contract (`video_contract.schema.json`:
  VideoDeliverableRequest → VideoResult). Inputs accept only **Proved/Code-verified** ledger ids (no fabricated
  data on screen); outputs fold OpenMontage's decision-log + cost back into `governance/provenance.json` + the
  AI Use Statement. Creative approvals map to gates **G5/G6**. Install is a provisioning-gate step (PROVISION.md).
- Consequences: Cambium gains video deliverables without leaving its evidence/governance model.
  **Non-negotiable license boundary:** OpenMontage stays an external AGPLv3 program Cambium *invokes* — zero
  OpenMontage code/skills/prompts vendored, forked, or linked into the MIT repo (that would relicense Cambium
  to AGPL), and hosting it as a service triggers AGPL §13 on the operator. Governance: GO-WITH-CONDITIONS
  (provenance per asset, provider ToS + stock licenses honored, AI imagery disclosed, no non-consensual
  synthetic likeness, budget cap). MIT-clean verified: no code files under skills/render-video/ (md+json only).
  Green: consistency 46·11·8 · doctor GRADE A · 113 tests pass.
he
  `urlhealth` package, else a stdlib liveness + Wayback-availability fallback; any error degrades to
  'unchecked'; always exits 0). Writes `governance/url_audit.json`; optional non-destructive
  `<ledger>.urlcheck.csv` sidecar via `--sidecar`. (2) **`governance/validate.py`** — honors an optional
  `url_status` column as an **ADVISORY WARNING only, never a blocker**; `hallucinated`/`stale-archived` →
  warning, `live`/`unchecked`/absent → silent (back-compat no-op). (3) **`tests/test_url_health.py`** — offline
  determinism, audit-json written, graceful-on-missing-ledger, and advisory-not-blocker / clean-is-silent for
  the validator column.
- Deviations from the proposal (recorded honestly): (a) the optional one-line references on the `librarian`
  and `integrity-officer` agent cards were **NOT added** — `.claude/agents/` is a protected path in this
  session and edits were blocked; agent counts are unchanged (46·11·8) regardless, and the cards can get the
  cosmetic line later. (b) `urlhealth` + Wayback API were NOT installed (provisioning recorded only, per
  TOOL_POLICY.md). (c) Claim discipline kept: the paper's 3–13% figures are cited as external measurement, not
  as a Cambium result.
- Verification (this run): `python3 -m py_compile` OK on url_health.py + the rewritten validate.py + the test;
  validator behavior matrix confirmed (hallucinated/stale → WARNING + exit 0; live/unchecked/absent → silent +
  exit 0); url_health offline run = all 'unchecked', audit-json + sidecar correct, missing-ledger graceful,
  `extract_urls` ordered+de-duplicated; `consistency_check.py` exit 0 (46·11·8). NOTE: in THIS sandbox the bash
  mount served a stale, truncated copy of the in-place-edited `validate.py`, so `doctor.py` reported a false
  `'{' was never closed (line 90)` + the dependent ledger check — the authoritative Windows file is complete
  and valid (verified end-to-end via Read; py_compile passes on a faithful copy). `pytest` is unavailable in
  the sandbox (install prohibited) so the new tests were validated by logic-equivalent runs. Re-run
  `doctor.py` + `pytest -q` on Windows before publishing to confirm green.
- Alternatives weighed & rejected this run: **DeepVerifier** (https://arxiv.org/abs/2601.15808) — SKIP,
  duplicates referee + verify-* boards + exec-iteration + the fallacy checklist; **AI-Supervisor**
  (https://arxiv.org/abs/2603.24402) — SKIP, duplicates Orchestrator + record-keeper + ledger + run_trace and
  its "autonomous supervision" framing conflicts with the human-gate doctrine (ADR-001/ADR-003).
- Consequences: Cambium now tests the *resolvability* of references, not just their identity, closing the gap
  between README/CI policy and shipped capability — additive, back-compat, offline-safe. Constraint: keep it
  advisory (never a build blocker without a separate decision), keep counts 46·11·8, never enable network
  probing in CI by default. Detail: `cambium_imp/skill-scan/2026-06-27-0506.md`.

## ADR-029: Integrate OpenMontage as an external, process-isolated AGPLv3 tool (MIT-clean)
- Date: 2026-06-27 · Status: Accepted · Decider: Director
## Context
OpenMontage (https://github.com/calesthio/OpenMontage, AGPLv3) is the leading open-source AI video
production pipeline. The Reporting council needs a video-deliverable capability — video abstracts,
grant-pitch videos, and results explainers — that Cambium itself cannot provide without significant
multimedia engineering. Pre-building a full video stack inside a MIT-licensed repo would either vendor
AGPLv3 code (creating a license incompatibility) or reinvent substantial prior art (violating
reuse-beats-rebuild). The gap: Cambium had no video-production skill.
## Decision
Integrate OpenMontage as an **external, separately-installed subprocess** — never vendored, never linked,
never forked into the Cambium tree. The design:

1. **`skills/render-video/SKILL.md`** — a Reporting-council skill (triggers: "make a video",
   "video abstract", "render explainer", "grant video"). Owned by Reporting; consumed by Outreach.
   Creative approval at gates **G5** (internal release) and **G6** (external publish).
2. **`skills/render-video/video_contract.schema.json`** — JSON Schema draft-07 defining
   `VideoDeliverableRequest` (input, with `source_ledger_ids` enforcing evidence-bound content) and
   `VideoResult` (output, with `providers_used`, `ai_assets_disclosed`, `decision_log_ref`,
   `cost_actual_usd`, `self_review_passed`).
3. **`skills/render-video/PROVISION.md`** — Toolsmith provisioning manifest: user clones OpenMontage
   separately (`git clone … ~/tools/OpenMontage; make setup`), sets `OPENMONTAGE_HOME`; zero-API-key
   free path documented (Piper TTS + Remotion + Archive.org/NASA/Wikimedia/Pexels).
4. Outputs fold back: OpenMontage's decision log + cost record → `governance/provenance.json` + the
   AI Use Statement; all AI-generated assets disclosed; stock licenses verified; budget cap enforced.
5. No non-consensual synthetic likeness or voice; provider ToS honored.

**License boundary (non-negotiable):** The OS process boundary is the license boundary.
- No OpenMontage source code, skill text, prompts, or files may ever be copied, pasted, forked, or
  transcribed into this repo.
- Cambium references OpenMontage only by its public URL and public CLI/file-name conventions.
- Hosting OpenMontage as a network-accessible service triggers AGPL §13 on the operator; local
  single-machine use does not.
- This boundary must survive every future change. If a future integration would require linking or
  vendoring OpenMontage code, that integration must be rejected or a new ADR + legal review obtained.

## Alternatives considered
- **Build a native video stack in Cambium (MIT):** rejected — major engineering investment, duplicates
  OpenMontage's already-proven FFmpeg/Remotion/TTS pipeline; violates reuse-beats-rebuild.
- **Vendor OpenMontage as a submodule:** rejected — AGPLv3 submodule inside MIT repo creates a license
  incompatibility (combined work, AGPL §5).
- **Use a proprietary SaaS video API:** rejected — introduces a hidden cost dependency, breaks the
  zero-API-key free path, and adds vendor lock-in.
- **Skip video capability entirely:** rejected — real user need (grant pitches, journal video abstracts)
  with no alternative inside Cambium.

## Consequences
- The render-video skill is additive; no existing skill, agent, or gate is changed; counts stay 46·11·8.
- Every video render requires human approval at G5/G6 — never automatic.
- Evidence integrity is enforced structurally: `source_ledger_ids` must be Proved/Code-verified; the
  schema rejects requests without them.
- The AGPLv3 boundary is load-bearing and must not be relaxed without a new ADR + legal sign-off.
- Future maintainers must NOT: copy OpenMontage prompts into SKILL.md, import its Python packages as
  a library, or shell out to it from CI without a human gate.
- Verification: SKILL.md, video_contract.schema.json (valid JSON, draft-07), and PROVISION.md written
  and read-verified. `consistency_check.py` counts unchanged (46·11·8). Schema JSON parses cleanly.
  `doctor.py` and full pytest suite: **Asserted** (cannot run in this sandbox — hand to Orchestrator
  for Windows-side re-run before publishing).

## ADR-029: Machine-checkable provenance manifest for Code-verified claims
- Date: 2026-06-27 · Status: Accepted (Director approved) · Decider: Director (Jaslam)
- Context: ROADMAP near-term item + the self-evaluation's top finding — "Code-verified" in validate.py was
  satisfied by a command *string*, not an actual rerun. Honesty needed reproduction, not assertion.
- Decision: ship `tools/provenance.py` — `build` re-runs each Code-verified claim's `cmd:` in the ledger,
  hashes the command + referenced script(s) + captured output, and writes a manifest linking claim →
  rerun + script_sha256 + output_sha256; `check` re-runs and FAILS (exit 1) if any output hash drifts.
  Demonstrated end-to-end in `examples/e2e-worked-example/` (RFP→aims→proposal→deterministic
  `code/analysis.py`→ledger→manifest→report; headline 3.06 bu/acre reproduced + hashed). Tests:
  `tests/test_provenance.py` (build+check pass; check fails on output drift).
- Consequences: Code-verified becomes reproducible-by-construction where a rerun command exists; the worked
  example proves the full artifact chain + provenance. Also shipped 2 non-ML domain configs
  (`examples/configs/social-science-survey.yml`, `agricultural-field-trials.yml`). Counts: 23 tools (was 21;
  README updated). Green: consistency 46·11·8 · doctor GRADE A · 115 tests pass.

## ADR-030: Grounded retrieval backend + live speed/cost telemetry (eval suggestions #2, #4)
- Date: 2026-06-27 · Status: Accepted (Director approved) · Decider: Director (Jaslam)
- Context: the self-evaluation (agent_outputs/EVALUATION.md) scored Deep-search 5/10 ("thin web-search
  wrapper, no retrieval backend") and Speed 6/10 ("zero measured latency/cost data — policy only").
- Decision: (#2) ship `tools/paper_search.py` — grounded scholarly retrieval over **OpenAlex (CC0) +
  Crossref**, no API key, offline-safe; returns structured citable records (title/authors/year/venue/DOI/
  citations/abstract). Wired into scout-prior-art, scout-methods, scout-landscape, and librarian.
  (#4) instrument `tools/cambium_run.py` to capture per-agent **wall-clock + input/output tokens + est_usd**
  to `agent_outputs/cost_log.csv` on every live call (turns the EFFICIENCY.md cost-telemetry policy into real
  data). Tests: `tests/test_paper_search.py` (parsers), `tests/test_cost_telemetry.py` (estimate + log).
- Consequences: scouts ground citations in a 250M-work corpus instead of ad-hoc web tool use; runs now emit
  measurable speed/cost. Tool count 23→24 (README corrected). Live retrieval verified (real OpenAlex
  results). Green: consistency 46·11·8 · doctor GRADE A · 120 tests pass.

## ADR-031: Gate interlock + independent finding-audit + funder corpus & demonstrated post-award (eval #3, #6, #7)
- Date: 2026-06-27 · Status: Accepted (Director approved) · Decider: Director (Jaslam)
- Context: the self-evaluation found the central gap "documented != enforced" — four seams where the spec is
  A-grade but the mechanical guarantee lags: (A) live gate is convention, (B) CI tests a stand-in ledger,
  (C) the board trusts agents' self-reports, (D) `Code-verified` is a string match. Plus Scope/Knowledge gaps:
  only 2 funders, and post-award execution documented-not-demonstrated.
- Decision:
  (#3) `tools/gate.py` — wraps `governance/validate.py` over the **production** ledger; exit 1 BLOCKS the gate
  on any release-blocker. CI now also gates + provenance-checks the committed `e2e-worked-example` ledger and
  runs the audit, so CI exercises a real artifact, not only `ci_ledger.csv` (closes seams A/B). The interlock
  caught a genuine evidence-cell gap on first run and forced the fix.
  (#6) `tools/finding_audit.py` — independent scan flagging completion/verification claims that lack evidence
  markers; advisory in CI (closes seam C). Seam D was already closed by the provenance manifest (ADR-029).
  (#7) added source-verified `governance/funders/usda-afri.yml` + `doe.yml` (corpus 2->4); the honest finding
  that DOE-P-2031 excludes financial-assistance recipients is recorded rather than glossed. Added
  `examples/e2e-worked-example/04_postaward_runlab.md` demonstrating the G4 run-lab loop end-to-end.
- Consequences: the validator-checkable surface is now enforced by construction, not convention; CI fails on a
  broken real ledger; over-claiming is independently flagged; funder coverage and a demonstrated post-award
  example close the Scope/Knowledge gaps. Tool count 24->26; worked examples 5->6 (README + roadmap reconciled).
  Remaining for grade A: eval #1 — run a real arm of the enforcement A/B and report effect size + CIs (needs an
  API key + budget; the central claim stays honestly **Open** until then).
- Green: consistency 46·11·8 exit 0 · doctor GRADE A (100%) · 123 tests pass / 1 skipped · funder-freshness 4/4.

## ADR-032: Complete the enforcement A/B harness so a real arm can be RUN (eval #1)
- Date: 2026-06-27 · Status: Accepted (Director approved) · Decider: Director (Jaslam)
- Context: eval #1 — the single move from B+ to A — needs a REAL arm of the enforcement study with effect
  sizes + CIs. The pre-registered harness scored hand-made verdicts but had no agent-runner or judge, so no
  one could actually run it. The central claim was honestly Open with no path to evidence.
- Decision: build the missing pieces — `run_arm.py` (runs both arms via the API, key read from the user's
  own env, never handled by the assistant), `judge_stage1.py` (deterministic ARM-BLIND judge scoring the
  primary false-claim rate + citation integrity; OCR/RR deferred to the human panel rather than scored by a
  biased automated proxy), `analyze.py` (Cohen's h + Wilson/Newcombe 95% CIs + one-sided two-proportion z +
  Bonferroni -> RESULTS.md), and `run_pilot.py` (one-command orchestrator). Honest scope baked in: result
  stays OPEN until a live run; 12-item pilot is feasibility (report effect sizes + CIs, claim no definitive
  result/null); fixture inputs hard-guarded; regenerable artifacts gitignored; RESULTS.md a tracked deliverable.
- Why the human runs the live arm: API keys are credentials — the assistant must never handle one. The user
  runs `run_pilot.py` in their own terminal with their key in their environment; the harness reads it from
  os.environ and never writes or prints it. Outputs land in the repo for scoring + reporting.
- Consequences: the last eval suggestion is now executable; a live run converts the central claim from Open to
  pilot-evidenced (and a v1 60-item + human-panel run to definitive). Verified keyless: judge discriminates
  (synthetic h=-3.14, p<1e-6), fixture guard fires, +7 tests. New files live under evals/ (tools/ stays 26).
- Green: consistency 46·11·8 exit 0 · doctor GRADE A (100%) · 130 tests pass / 1 skipped.

## ADR-033: Ran the enforcement A/B pilot for real (eval #1) — honest null, claim stays Open
- Date: 2026-06-27 · Status: Accepted (Director ran it) · Decider: Director (Jaslam)
- Context: eval #1 (B+ -> A) required actually RUNNING a real arm of the pre-registered enforcement study,
  not just shipping the harness. The Director ran it on their own machine (Claude Code login; no API key
  handled by the assistant).
- What happened: live run on claude-opus-4-8, 12 tasks x 2 arms = 24 real agent runs, arm-blind Stage-1
  scoring. Getting a CLEAN run took several iterations — fixed context contamination (isolated cwd), a
  Windows cp1252 encoding crash (force UTF-8), and a launcher failure (npm's `claude.ps1` isn't
  Python-executable -> resolve and run `claude.cmd` via `cmd /c`). Also recalibrated the judge after
  reading transcripts by hand: it was marking CORRECT answers as misses; redefined "missed" as asserting
  the false claim as fact (protocol §4.1).
- Result: false-claim rate Treatment 0.33 vs Baseline 0.25 (diff +0.08, 95% CI [-0.12, +0.28], h=0.18,
  p=0.78); citation integrity 1.00 vs 1.00. No measurable enforcement effect; both arms near-ceiling honest.
- Decision: report it honestly. The central claim stays **OPEN** — the pilot neither supports H1 nor
  establishes a null (underpowered n=12; near-ceiling model; automated judge whose absolute rates are
  unreliable though its between-arm comparison is robust). This restraint IS the evidence contract applied
  to Cambium itself: we ran the experiment we said we'd run and reported the unflattering result.
- Consequences: eval #1 is now *executed*, not just buildable. Grade stays at the honest B+/A boundary on
  EVIDENCE rather than on a manufactured positive. Next experiments (per RESULTS.md): weaker model (Haiku),
  v1 60-item set, two-rater human panel for absolute-rate validity.
- Files: evals/enforcement_study/RESULTS.md (+ results_pilot.csv, runs/, *_verdicts.json). Recalibrated
  judge_stage1.py; hardened run_arm.py; run_pilot.py gains --rescore/--limit.

## ADR-034: Adopt PHILOSOPHY.md as Cambium's North Star (and name the unshipped design direction)
- Date: 2026-06-27 · Status: Accepted (Director approved at gate G-philosophy) · Decider: Director (Jaslam)
- Context: the Director surfaced the founding concern from an AI-faculty bootcamp — AI can make a multi-year
  project *look* done in a day, but funders pay for the process (learning, creativity, community, judgment),
  not the artifact; and "human in the loop" via a rubber-stampable gate is still "AI does everything."
- Decision: write and adopt PHILOSOPHY.md, drafted the Cambium way (5 agents across Faculty/Governance/Support,
  integrity-audited for overclaim). It fixes the North Star, maps the six concerns to real mechanisms with
  honest verdicts (1/5/6 addressed; 3/4 not structurally yet), states six file-cited gaps, and proposes a
  design direction (Director Brief + Learning Gate Section 8 + teaching in-line + Contribution Ledger +
  deliberation window + capacity check) that would turn "AI does, human approves" into "AI scaffolds, human
  thinks, AI teaches."
- Crucial honesty: the Section-5 design is **proposed, not shipped**; the doc says so, and the gaps section is
  what makes the rest trustworthy. Adopting the document does NOT build the features — that is a separate
  future gate.
- Consequences: Cambium now has an explicit purpose statement and an honest self-assessment; the natural next
  gate is to BUILD the Learning Gate so concerns #3 (creativity) and #4 (learning) move from "claimed" to
  "structurally enforced."
- Files: PHILOSOPHY.md; governance/GATES.md (G-philosophy APPROVE); README link; Cowork artifact "cambium-run-board".

## ADR-035: Build the Learning Gate + wire the run board to Cowork (PHILOSOPHY.md §5)
- Date: 2026-06-27 · Status: Accepted (Director: "do both and all") · Decider: Director (Jaslam)
- Context: PHILOSOPHY.md §5 proposed turning "AI does, human approves" into "AI scaffolds, human thinks, AI
  teaches" — but it was unshipped; and the run board the Director asked to see was hand-drawn rather than
  generated by the built-in tool (which was dark-only and showed the generic roster).
- Decision (two tracks):
  (A) `tools/run_trace.py` reads a custom plan from `run_state.json` (real roster on the board) and gains a
  `--light` mode so its HTML is a proper Cowork artifact — the generator is now the single source, no more
  hand-drawing.
  (B) The Learning Gate: a required Section 8 on `templates/GATE_SUMMARY.md`, a `templates/DIRECTOR_BRIEF.md`,
  and `tools/learning_gate.py` that enforces a genuine human contribution (≥40-word hypothesis + reasoning,
  choice, Socratic answer; copy-from-AI flag) and records it append-only to `governance/CONTRIBUTION_LEDGER.csv`.
  A bare APPROVE no longer advances; concerns #3/#4 move from claimed to enforced.
- Consequences: tools 26→27, templates 13→14; +6 tests (136 pass). The remaining integration is wiring the
  Orchestrator to FIRE learning_gate automatically at every gate (today the tool + template exist and are
  tested; the auto-trigger is the next step). Honest: this is the build, not yet the full runtime lock.
- Files: tools/run_trace.py, tools/learning_gate.py, templates/GATE_SUMMARY.md (§8), templates/DIRECTOR_BRIEF.md,
  governance/CONTRIBUTION_LEDGER.csv, tests/test_learning_gate.py; PHILOSOPHY.md §5 + PRESENTATION.md Act III updated.

## ADR-036: Close the positioning scorecard — enforcement repairs + bias module + honest specs
- Date: 2026-06-27 · Status: Accepted (Director approved at gate G-repairs) · Decider: Director (Jaslam)
- Context: the verified POSITIONING scorecard named 6 repairs + 2 gaps. The Director said "both" — do all.
- Decision: ship the tractable engineering and write honest specs for the infrastructure-heavy items:
  (1) `gate.py --require-contribution` enforces the Learning Gate at a decision gate; (2) `citation_support
  =unsupported` becomes a release blocker in `validate.py`; (3/#5) a NIST AI RMF bias-mitigation checklist +
  `bias_check` column (moves #5 Gap→Partial); (4) a default-deny `REGULATED_DATA.md` intake control; (5)
  AI_MODEL enforced on the CI validate step; (#9) `ARCHITECTURE_MULTI_INSTITUTION.md` staged design spec.
- Honest boundaries kept: Orchestrator auto-firing the Learning Gate on every run, a real encrypted enclave,
  shared multi-institution infrastructure, and the v1 human-judged A/B remain open — labeled as such, not
  overclaimed. POSITIONING updated to 3 Leads · 6 Partial · 1 Gap with a dated post-repair note.
- Also corrected a 1.00.20 overclaim: Cowork artifacts cannot post to chat (no send-to-chat API), so the
  run-board APPROVE buttons can't auto-approve; honest clipboard feedback instead, inline widget for true clicks.
- Files: tools/gate.py, governance/validate.py, templates/BIAS_MITIGATION_CHECKLIST.md, governance/REGULATED_DATA.md,
  ARCHITECTURE_MULTI_INSTITUTION.md, .github/workflows/validate.yml, tests/test_repairs.py; POSITIONING/PHILOSOPHY/README updated.
- Green: consistency 46·11·8 · doctor GRADE A · 142 tests pass / 1 skipped · CI ledger green.

## ADR-037: Inline gate cards default + Learning-Gate auto-fire + multi-PI Stage-1 roles
- Date: 2026-06-27 · Status: Accepted (Director approved at gate G-stage1, via the inline card button) · Decider: Director (Jaslam)
- Context: after the scorecard repairs, three threads remained: (1) make click-to-approve real (the sidebar
  artifact couldn't post to chat), (2) move the Learning Gate from enforced-when-invoked to fired-on-every-gate,
  (3) take the smallest real step on the #9 cross-institution gap.
- Decision: (1) inline gate cards (`show_widget`, `sendPrompt`) become the default gate surface, mandated in
  PRESENTATION Act III; (2) Act III mandates `gate.py --require-contribution` before recording any decision-gate
  APPROVE; (3) `gate.py --required-approver` enforces a named institution-scoped approver, with
  `templates/MULTI_PI_ROLES.yml` mapping gate→approver — Stage 1 of ARCHITECTURE_MULTI_INSTITUTION.md.
- Honest boundaries: the Learning-Gate enforcement is an Orchestrator-followed CONTRACT, not an un-bypassable
  runtime lock (#2 stays Partial); multi-PI roles work on shared git but shared INFRASTRUCTURE (server/SSO/RBAC)
  is unbuilt (#9 stays a Gap, Stage 1 only). Both stated in POSITIONING.
- Files: tools/gate.py, templates/INLINE_GATE_CARD.html, templates/MULTI_PI_ROLES.yml, PRESENTATION.md (Act III),
  tests/test_repairs.py; POSITIONING/README updated.
- Green: consistency 46·11·8 · doctor GRADE A · 144 tests pass / 1 skipped · CI ledger green.
