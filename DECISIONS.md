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
