# Changelog

## 1.00.0 - 2026-06-26 — First stable public release (re-baseline)
- **Version re-baseline.** Cambium is re-baselined to **1.00.0** as its first stable public release. The
  1.0.0 → 3.18.0 entries below were rapid same-day development iterations and are retained as history under
  "Pre-1.0 development history" — they do not represent prior public releases.
- **Versioning scheme going forward:** `MAJOR.MINOR.PATCH` with a zero-padded two-digit minor — next minor
  is `1.01.0`, then `1.02.0` … `1.99.0`; patches are `1.01.1`, `1.01.2`, etc.
- **What 1.00.0 contains** (state at re-baseline): the 46-agent / 11-council institute with 8 human gates;
  full pre-award + post-award lifecycle; CI-enforced evidence/claim-tier contract (`governance/validate.py`);
  MCP server; self-grading `doctor` (GRADE A); the enforcement-vs-soft-prompting A/B harness
  (`evals/enforcement_study/`, study result **Open**); the per-funder governance corpus
  (`governance/funders/`, NIH+NSF, source-verified, freshness-CI); and the execution + record-keeper
  build/verify contracts. Verified: consistency exit 0 · doctor GRADE A · 104 tests pass / 1 skipped.

---

## Pre-1.0 development history (archived — rapid same-day iterations, not public releases)

## 1.0.0 - Initial public release
- 34-agent, 9-council research institute (orchestration, pre-award, partnerships, faculty, scouts,
  labs, verification, execution, support, reporting).
- Full project lifecycle (RFP -> proposal -> development -> reports) with 6 human-in-the-loop gates.
- Output contract (severity + claim tiers), findings ledger, leaderboard, synthesis.
- Smart-Tier model profile (+ opus-max / lean).
- Template repo + installable plugin manifest + marketplace.json.
- Interactive dashboard; two fictional demo projects.

## 1.1.0 - Governance & self-audit
- Ran the Institute on itself (Project 003): 4 audit boards; objectives scorecard.
- Added AI_GOVERNANCE.md (research + teaching) and AI_USE_STATEMENT.md template.
- Added governance/GATES.md (recorded human approvals) and governance/validate.py (evidence-tier
  validator + provenance manifest; fails build on open P0). Added SECURITY.md, CODE_OF_CONDUCT.md.
- README/INSTITUTE/OUTPUT_CONTRACT updated to reference governance.

## 1.2.0 - Team roles & delegated human-in-the-loop
- Added ROLES.md: Director/PI, Co-PI/Area Lead, Project Manager(Admin), Researcher/Student, Engineer,
  independent Integrity/Data steward; human->agent mapping; separation of duties; worked team example.
- config.example.yml now defines the team roster + per-gate approver map (delegated approvals).
- GATES.md gains role + named-approver columns. Each PI/Co-PI is the human-in-the-loop for their sector.

## 1.3.0 - World-class release (Institute built by its own team)
- CI: tools/check_agents.py (frontmatter validator) + .github/workflows/validate.yml — the evidence
  contract is now enforced on every push/PR (green on a healthy repo, red on an open P0 or invalid agent).
- Demo: demo/tour.html — a 60-second self-running animated tour; README gets badges + above-the-fold value prop.
- Worked example: examples/full-lifecycle/ — a complete fictional RFP->proposal->development->verify->
  report artifact chain that PASSES validate.py (demonstrates the integration claim end to end).
- Team usability: tools/whoami.py (prints a person's desk + approvable gates) + TEAM_QUICKSTART.md.
- tools/quickstart.sh + quickstart.ps1 one-command setup.

## 1.4.0 - High-end release
- Landing site: index.html (polished one-pager) + .github/workflows/pages.yml (GitHub Pages deploy).
- Visuals: assets/org-chart.svg + assets/lifecycle.svg (render on GitHub); embedded in README "At a glance".
- Positioning: COMPARISON.md (honest, web-verified vs AI Scientist / Co-Scientist / Agent Lab / AutoGen),
  FAQ.md, ROADMAP.md, CITATION.cff (citable software).
- Field-agnostic proof: examples/demo-humanities + examples/demo-public-health (non-STEM).
- tools/new_project.py scaffolder. Test artifacts moved to tools/test_fixtures/; projects/REGISTRY.md reset.

## 2.0.0 - Deeper research capability (v2)
- Roster 34 -> 39 (all doers/referees): lab-statistics, exec-iteration, research-engineer, referee, idea-tournament.
- Adopted (verified) mechanisms: novelty gate (AI Scientist), Elo idea tournament + reflect/evolve
  (AI Co-Scientist), scored self-refinement + tree-search experiment loop (Agent Lab / AI Scientist),
  venue-rubric referee (AI Scientist), cross-project institutional memory (AutoGen).
- New triggers: run tournament, iterate experiment, referee, run verification debate.
- Upgraded record-keeper (institutional memory), scout-prior-art (novelty gate), ideation (feeds tournament).

## 3.0.0 - Full research lifecycle (v3)
- Roster 39 -> 45: rfp-radar, convener, budget-officer, grants-compliance, feedback-router, research-conduct-officer.
- End-to-end lifecycle (LIFECYCLE_V3.md): RFP radar -> idea inbox -> brainstorm/tournament -> team + pre-award
  (budget, biosketch, DMP, forms) -> award mobilize (assignments, scoped agent access, alerts) -> execute ->
  reports/meetings/scheduling -> feedback router. New gate G0 (Know the PI).
- Responsible-research governance at EVERY gate (RESEARCH_CONDUCT.md): IRB/IACUC, COI, FERPA, data
  sovereignty, dual-use, reproducibility - GO / CONDITIONS / STOP, alongside evidence + AI-use governance.
- Templates: USER_PROFILE, IDEA_INBOX, COLLAB_WORKSPACE, POST_AWARD_PLAN.
- New triggers: watch rfps, rfp in <file>, add idea, convene team, build budget, compliance check,
  assign work, route feedback, conduct check <gate>.

## 3.1.0 - Self-improvement run (Project 005: Cambium improves Cambium)
P0: v3 scaffolder now creates all v3 write-targets + copies templates (new_project.py); unified RFP
intake to one canonical 00_rfp_brief.md; hardened validate.py (dropped undocumented 'info' tier;
'Code-verified' now requires a command marker; fails on unresolved citations; won't clobber provenance
on empty runs); citation-resolution gate (15-librarian); reproducibility checklist (template + scored);
DATA_MANAGEMENT_PLAN template; policy currency (NIH NOT-OD-25-132, NSF PAPPG 2025, publisher/COPE,
zero-embargo public access, NIST AI RMF) in RESEARCH_CONDUCT/AI_GOVERNANCE/AI_USE_STATEMENT; G0 gate added.
P1: EVALS.md reliability floor; MCP_INTEGRATION.md; MODEL_ROUTER.md (needs your model access);
record-keeper memory service; ensemble referee + EQUATOR/TOP; budget-aware verification; stale 34->45
counts fixed (COMPARISON/FAQ/GETTING_STARTED/ROLES). Built BY Cambium; see cambium_imp/005-improve-cambium.

## 3.2.0 - P2 items (Project 005 cont.)
- A2A Agent Cards: tools/gen_agent_cards.py -> agent_cards.json (TESTED: 45 cards).
- Deep-research two-mode loop (quick scan / deep research) on scouts + triggers.
- EFFICIENCY.md: prompt-caching guardrails (never cache volatile facts) + per-vendor cost telemetry spec.
- MCP_INTEGRATION.md: A2A cards section. Triggers: quick scan, deep research, gen cards, cost report.

## 3.2.1 - Model router wired (Claude now, pluggable later)
- config.example.yml: model_router block (anthropic ON; google + openai_compatible scaffolded OFF).
- tools/model_router.py: agent -> tier -> concrete model from active provider; stdlib fallback to Claude.
  TESTED: 45 agents -> 12 opus / 31 sonnet / 2 haiku. Add free/other models later via config (no code change).

## 3.2.2 - Repo-wide consistency cleanup + enforcement
- Fixed every stale count across the repo: 34/39 -> 45 agents, 9/10 -> 11 councils (Governance added),
  "six gates" -> 8, in index.html, demo/tour.html, plugin/README, ROADMAP, CITATION, dashboard, README,
  INSTITUTE; rebuilt index.html council grid (all 11 councils, correct per-council counts).
- Regenerated assets from the live roster: assets/org-chart.svg (tools/gen_org_chart.py),
  assets/demo.gif (tools/gen_demo_gif.py), assets/social-preview.svg+png. Counts now generated, not hand-typed.
- NEW tools/consistency_check.py (canonical 45/11/8 from the live roster) wired into CI: the build now
  FAILS on any future count drift. Self-cleaning by construction.

## 3.3.0 - Auto-runner engine (specs -> running workers)
- tools/cambium_run.py + phases.yml: orchestrator that runs agents CONCURRENTLY within a phase
  (each call = one session), sequentially across phases, stopping at every human gate.
- Dry-run prints the parallel execution plan + model per agent (via the router); --live executes via
  the Anthropic API with a thread pool (needs ANTHROPIC_API_KEY). I/O-bound: concurrency, not cores.
- AUTORUN.md documents both execution paths + limits.

## 3.4.0 - Deployable app (Cambium Campus) — built by the engineering councils
- app/engine.py: hardened orchestrator — run-state on disk, retry/backoff LLM client + token cap,
  failures block their gate, gate stops + resume (addresses backend-audit P0s).
- app/server.py: stdlib HTTP server — serves the front-end + /api/health,/agents,/plan,/run,/approve.
- app/index.html: cinematic campus UI wired to the API with static-demo fallback.
- Packaging: requirements.txt, Dockerfile, Procfile, run.sh/run.bat, app/README.md (local + deploy).
- TESTED: server boots; all endpoints return correctly (health, 45 agents, 5-phase plan, dry-run run, static).
- Static front-end deploys free to Pages (demo mode); full live app via Docker/host + ANTHROPIC_API_KEY.

## 3.4.1 - App hardened after Cambium's own security review (project 008)
- 4 councils (engineer, verification, UX, referee) reviewed the app in parallel; fixes applied:
- SECURITY: server now serves ONLY app/ (no repo/.git disclosure), denies dotfiles+traversal,
  validates JSON (400 not 500), caps body size, regex-validates run-id, optional CAMBIUM_TOKEN auth,
  binds 127.0.0.1 by default. TESTED: /.git, /engine.py, traversal -> 404; junk body -> 400.
- ENGINE: phase order respects phases.yml (PI before parallel writers); collision-proof run IDs;
  real --resume; graceful missing-run handling.
- UX/A11y: AA contrast (--mut), reduced-motion keeps rooms visible, canvas aria-hidden + CDN-fail
  fallback, journey focus-trap, fetch timeouts. Dockerfile non-root USER; app/runs gitignored.

## 3.5.0 - Task Router (auto council selection for ANY task)
- tools/task_router.py: classifies a task (grant / software / review / research / report / data) and
  builds a custom phase plan — which councils activate, what runs in parallel, where the gates fall.
- engine.py + /api/plan now use the router, so council selection is Cambium's, not hand-picked.
  Verified: "review app" -> exec+verify+lab+gov (incl. the Governance council a human reviewer missed);
  "build app" -> lab+exec+verify+faculty+gov; "grant" -> full pre-award lifecycle.

## 3.6.0 - Toolsmith: provision existing tools (reuse beats rebuild)
- New agent 45-toolsmith (Support): discovers existing npm/pip packages, component libs (shadcn/21st.dev),
  MCP connectors, skills, datasets, free APIs for a task; returns a manifest + install commands;
  installs ONLY after human approval. tools/toolsmith.py registry + TOOL_POLICY.md (supply-chain policy).
- Task Router adds a provisioning gate (G-provision) at the start of software/research/data tasks.
- Roster 45 -> 46 (Toolsmith joins Support; still 11 councils). Counts synced repo-wide; org-chart +
  dashboard + social card regenerated. Dashboard rebuilt (was truncated by a sed on the mount).

## 3.6.1 - cambium doctor (one-command health check)  [← ECC's doctor/repair idea]
- tools/doctor.py: runs check_agents + consistency_check + validate + HTML-integrity (catches
  truncation / unbalanced <script>) + Python-parse + derived-sync (agent_cards, org-chart) in one pass.
  `--fix` regenerates derived files. Wired into CI so a truncated/stale file fails the build before merge.
- On first run it caught the dashboard.html truncation (Windows/Linux mount desync); rebuilt + verified.

## 3.7.0 - Local console: login + task box + account-based execution
- app/console.html: sign in (local passcode), type a task, preview the auto-selected councils, run,
  approve at each gate. Live agent outputs per agent.
- app/providers.py: execution backend auto-detect — Claude Code (your Anthropic login, no API key) >
  API key > dry-run. engine.call_model now delegates to providers.
- app/server.py: local login (session cookie, pbkdf2 passcode, CAMBIUM_PASSWORD), gated API, serves
  the console. .auth.json gitignored.
- Honest: no claude.ai-cookie backdoor; Claude Code is the sanctioned account path. TESTED end-to-end
  (login 401-gates, authed plan/run, dry-run) + doctor healthy.

## 3.8.0 - Self-grade + decision records (← ECC/ruflo metaharness idea)
- tools/doctor.py: added `--grade` — scores the institute A–F across roster, counts, evidence gate, HTML integrity,
  code, governance coverage, tooling, evals/tests, decision records, + a security risk scan.
- DECISIONS.md (living ADR log, seeded with ADR-001..005) + templates/DECISION_RECORD.md; wired into the playbook.

## 3.8.1 - Test suite (closes the grade's one gap)
- tests/test_framework.py: 15 pytest checks — Task Router selection, Toolsmith stack, Model Router tiers,
  validate.py blocks/passes correctly, doctor/consistency/check_agents exit clean, agent_cards in sync.
- Wired pytest into CI (validate.yml). All 15 pass.

## 3.8.2 - README + manifest rewrite
- Rewrote README around what Cambium actually is: a Claude PLUGIN + template (not a single skill, not an MCP),
  with clear goals, principles, install (plugin/template), lifecycle, governance + self-grade + tests, and
  multi-account continuity. Fixed stale plugin manifest counts (34/9 -> 46/11) + version 3.8.0.

## 3.9.0 - Cambium MCP server (built BY Cambium: Toolsmith provisioned, then built + verified)
- mcp_server/ : Python MCP server (official `mcp` SDK / FastMCP, stdio) exposing cambium_plan, cambium_provision,
  cambium_agents, cambium_doctor, cambium_grade, cambium_validate to any MCP client.
- pyproject (uvx entry `cambium-mcp`), README with Claude config snippets. tests/test_mcp.py (skips if SDK absent).
- TESTED: 6 tools register; plan/provision/agents/doctor/validate all return correctly. README/ADR updated.

## 3.10.0 - UX + transparency + one vocabulary
- Fresh "Living Layer" visual identity (evergreen + emerald + lime): logos, lifecycle, org-chart, social, demo.gif.
- templates/GATE_SUMMARY.md — one standard gate one-pager (Decision · Options · Risks · Evidence · Recommendation · APPROVE/REVISE/REJECT); mandated by the Orchestrator + OUTPUT_CONTRACT.
- USE_CAMBIUM.md — plain-language beginner guide (no jargon).
- tools/run_trace.py — shows the workflow as text / Mermaid / SVG + a LIVE status board (✓ done · ▶ now · ○ waiting), standardized to the 11 councils; wired into the Orchestrator and dashboard.html.
- Toolsmith design stack (brand-guidelines, canvas-design, theme-factory, ui-ux-pro-max…) so design tasks reuse real skills, not stats packages.
- Consistency sweep (Verification council): human role unified to Director (was President); "Provost"→Orchestrator; council names unified; "GATE" reserved for the canonical 8 (others are Checkpoints); plugin 3.8.0→3.9.0.
- Tests now 26; doctor --grade A.

## 3.10.1 - Fix roster-name drift (teaching/research-assistant)
- gen_org_chart.py + task_router.py referenced non-existent `teaching-asst`/`research-asst`; real names are
  `teaching-assistant`/`research-assistant`. Org-chart showed "(?)" and the router pointed at 2 phantom agents.
- Fixed both; regenerated org-chart.svg (0 unknowns). Added a generator guard (fails if a council member is not
  a real agent) + tests/test_roster_names.py (CI now catches CMAP↔roster drift).

## 3.10.2 - Fix plugin install (marketplace manifest location)
- `/plugin marketplace add` looks for `.claude-plugin/marketplace.json` at the REPO ROOT, but the manifests
  lived under `plugin/`. Result: clone succeeded but install failed with "Marketplace file not found."
- Added root `.claude-plugin/marketplace.json` + `.claude-plugin/plugin.json` (source "./", agents=.claude/agents).
  `/plugin marketplace add https://github.com/IFC-UIDAHO/Cambium_AI.git` + `/plugin install cambium-institute` now work.
- README: use the full HTTPS URL (short form can resolve to SSH and fail host-key checks); run the two commands separately.

## 3.10.3 - Make install actually work (lessons from real installs)
- Removed the redundant `plugin/` folder: the repo had TWO plugin.json (root + plugin/), which broke Cowork
  repackaging with "Zip must contain exactly one plugin.json. Found 2." Now exactly one manifest at root.
- Agents auto-discovered from `agents/` (no manifest `agents` field — the array/string forms were rejected).
- New INSTALL.md: tested steps for Cowork (Add-marketplace-from-repository AND /create-cowork-plugin), Claude Code
  (HTTPS URL, separate lines, user scope to avoid system32 EPERM), and the honest update story (manual Sync/Update;
  auto-sync is Team/Enterprise + private repo only). README quickstart points to it.

## 3.10.4 - Keep plugin agents/ auto-synced
- tools/sync_plugin_agents.py mirrors .claude/agents/ -> agents/ (the plugin's auto-discovery copy).
- Wired into push_cambium.bat (runs before git add), so the installable plugin never drifts from the roster.
- tests/test_plugin_sync.py fails CI if agents/ and .claude/agents/ ever diverge.

## 3.10.5 - Install docs: lead with the reliable path + document Claude-app quirks
- INSTALL.md now leads Cowork users with /create-cowork-plugin (bypasses the flaky "Add marketplace" menu),
  and a Troubleshooting table maps real Claude-app bugs (Personal-marketplace "+" only shows Anthropic catalog
  until a plugin is added once; installs lost on restart #40600; Windows empty marketplace #28853) to fixes.
- README quickstart updated to match. These are app quirks, not Cambium bugs.

## 3.11.1 - Council-labelled live agent cards
- Orchestrator now writes every sub-agent dispatch as "<Council> · <Role>" (e.g. "Verification · Referee",
  "Labs · Statistics"). Cowork's native "Running N agents" cards show that label verbatim, so the live UI now
  speaks the same council vocabulary as the run_trace status board — the two views finally agree.
- Clarified (docs/answers): the native "Running N agents" widget is Cowork's own and cannot be restyled by a
  plugin; the run_trace board (plan up front + ✓/▶/○ across all councils + gates) is the complementary map;
  dashboard.html is a static org reference, not a live run monitor.
ncils, stopping at a one-page
    gate card for APPROVE / REVISE / REJECT), then runs the chosen mode. Skips the question for trivial chat
    and quick lookups; honors "always Cambium"/"stay solo" for the session.
  - `commands/cambium.md` (`/cambium <task>`) and `commands/solo.md` (`/solo <task>`) — explicit manual
    override so the user can pick the mode per request without waiting to be asked.
- Version skipped 3.9.0 → 3.11.0 to clear the CHANGELOG's earlier 3.10.x headings (manifest had lagged at
  3.9.0 while the log ran ahead) so the marketplace version is unambiguously newest and the Cowork update
  button activates. Counts unchanged: 46 agents · 11 councils · 8 gates.

## 3.11.2 - Smart-default mode picker (Solo vs the Cambium way)
- cambium-mode skill rewritten to a SMART DEFAULT: trivial edits/lookups run Solo silently (no
  question); substantial tasks (evaluate, analyze, research, write, verify…) trigger a one-time
  Solo/Cambium-way choice that is then remembered for the session.
- Encodes the decision rule, session-memory, and an honest note that /solo and /cambium are the only
  100%-deterministic controls. USE_CAMBIUM.md documents the default so behavior is predictable even
  when the soft trigger doesn't fire.

## 3.11.3 - Routing coverage: Support close-out everywhere + write-up phase (ADR-016)
- Standard Support close-out (record-keeper, integrity-officer, janitor) now runs on EVERY task type
  (Support council coverage 3/6 -> 6/6) — the plan finally matches the "housekeeping every time" rule.
- document-office write-up phase added to research/report/data (Orchestration council 0 -> 3/6);
  librarian + figures routed into grant/research/report.
- New guard test (tests/test_router_coverage.py) fails CI if any council drops to zero routed agents,
  if close-out goes missing from a task type, or if document-office stops being routed. 32 tests pass.
- 7 agents remain intentionally on-demand (orchestrator, partnership-liaison, program-manager, outreach,
  office-manager, feedback-router, teaching-assistant) — excluded by design to avoid artificial over-use.

## 3.12.0 - Three built-in quantitative skills (mathematics, statistics, machine-learning)
- NEW skills/mathematics — deterministic symbolic + numeric math (SymPy/SciPy, optional Z3/Pint):
  compute exact answers, verify by back-substitution, tag Proved/Code-verified/Asserted.
- NEW skills/statistics — rigorous inference: tests, power/sample-size, GLM/mixed models, multiplicity
  correction, bootstrap, Bayesian basics (scipy/statsmodels/pingouin); reports effect size + CI, checks
  assumptions.
- NEW skills/machine-learning — leak-free predictive modeling: stratified/grouped/time splits, pipelines,
  CV, tuning off the test set, calibration, SHAP, model cards; explicit leakage checklist.
- SKILLS_MAP.md maps the three to the agents that wield them and notes optional curated web add-ons
  (frontend-design, frontend-excellence) — your installed UI/web skills already cover most of that.
- Smoke-tested: SymPy + scipy.stats patterns run and return correct values. 32 tests pass.

## 3.13.0 - Full council skill coverage (8 new skills)
- NEW skills covering every previously-uncovered council:
  optimization (lab-methods), reproducibility (research-engineer/verify-evidence), citations (librarian),
  data-management (data-steward), grant-writing (pre-award), research-ethics (governance),
  project-management (program-manager), scientific-writing (document-office/reporting-officer).
- Each emphasizes correctness + honesty: optimality status, rerun-and-verify, never-fabricate citations,
  PII screening, criteria alignment, GO/CONDITIONS/STOP ethics gates, claims<->evidence tiers.
- SKILLS_MAP.md maps all 11 built-in skills to the councils/agents that wield them. Deliberately did NOT
  duplicate UI/UX, web, software-eng, figures, decks, teaching — already covered by installed skills.
- Smoke-tested optimization (scipy linprog -> verified optimum). 32 tests pass; plugin.json clean.

## 3.14.0 - On-demand skill provisioning (skill-provisioner)
- NEW skills/skill-provisioner — instead of pre-stocking thousands of domain skills, Cambium now detects
  the field from a user's request, offers the few skills that help (existing to install + new to create),
  helps immediately via faculty-expert, and persists approved skills as reusable SKILL.md files.
- Two-tier delivery (instant faculty expertise now + reusable skill next session), detect-and-offer-once,
  human approval before any install or persist. Wires toolsmith + skill-creator + faculty-expert.
- USE_CAMBIUM.md tells users they can just ask "make a skill for X". 32 tests pass.

## 3.14.1 - Provisioner persistence policy (ADR-020, decided the Cambium way)
- skill-provisioner now states: the Cambium repo skills/ is the canonical home for created skills;
  local activation into a personal/project skills folder is an explicit, per-skill, opt-in step — never
  automatic, silent, or bulk. Solves "go live faster" without bypassing governance.

## 3.15.0 - The Cambium Way, made legendary (presentation layer + real-agent dispatch)
- New PRESENTATION.md — the canonical "Cambium way" contract: four acts (Opening run board · Live phases ·
  Gate · Close-out) so every Cambium run is unmistakable and identical, never the generic "Used N tools".
- run_trace.py upgraded: rich TEXT board (`--board`, alignment-proof left-bar header, council-grouped
  roster, per-agent findings, leaderboard, gate rail) and a self-contained LIVE HTML dashboard
  (`--html`, deep-forest + Cambium-lime theme, phase rail, agent cards showing `cambium-institute:<name>`,
  active-gate banner). Phase-level cursor (`--phase N`) + `--state state.json` overlay for live findings.
  Legacy `--text/--svg/--status/mermaid` preserved.
- commands/cambium.md + orchestrator (00) now MANDATE dispatching the REAL named sub-agents
  (`subagent_type: cambium-institute:<name>`, `description: "<Council> · Role"`) instead of working inline,
  and re-emitting the live board each phase — so the Director sees who is working, on what, and where the
  gates are. cambium-mode skill updated to point the smart-default at the same contract.
- templates/GATE_SUMMARY.md restyled with the branded gate header; ties to the dashboard gate banner.
- 34 tests pass; doctor healthy (23/0); agent_cards 46==46; source/plugin agents identical.

## 3.15.1 - Run-board imagery + auto-published dashboard
- New tools/gen_board_image.py renders the run board natively with PIL (no browser): assets/run_board.png
  (hero) + assets/run_board.gif (Opening → Scouts live → Gate → advancing). Data comes from
  run_trace.phases() so the picture never drifts from the real plan.
- README gains a "The Cambium way" section showcasing the live board + the four acts, linking PRESENTATION.md.
- cambium.md + orchestrator now make the Cowork dashboard explicit and automatic: publish once with
  create_artifact (Act I), update the same artifact id at the start of every phase (Act II).
- doctor 24/0, 34 tests pass, agents synced + identical.

## 3.16.0 - Auto-populated run board + asset CI
- New tools/run_state.py maintains agent_outputs/run_state.json (phase · finding · gate · lead · sync ·
  show · reset). `sync` AUTO-LIFTS each agent's headline from its own agent_outputs/<name>.md "## Decision"
  line, so the live board fills in as agents report — no hand-edited JSON.
- run_trace.py now AUTO-DISCOVERS agent_outputs/run_state.json (no --state flag needed); explicit --state
  still overrides. run_state.json is git-ignored (per-run, like findings_ledger).
- commands/cambium.md, orchestrator, and PRESENTATION.md now drive the board via run_state.py (phase →
  dispatch → sync → re-emit), with the Cowork dashboard published once (create_artifact) and updated each
  phase (update_artifact, same id).
- New .github/workflows/assets.yml regenerates assets/run_board.png + .gif on every published release (and
  on changes to the renderer/router) and commits them back, so the README board never goes stale.
- Synced mcp_server/pyproject.toml to the plugin version (was drifted 3.14.0 vs 3.15.1). doctor 25/0,
  34 tests pass, agents identical, counts consistent.

## 3.17.0 - Durable memory + guarded autonomy (Agentic-OS adoption, decided the Cambium way)
Ran the full Cambium way on the "Agentic OS" video (3 Scouts + Faculty + idea-tournament + Integrity audit,
real dispatched agents, gate G2 approved). Adopted the genuinely-missing ideas; rejected the app/deploy framing.
- **A · Pause/Resume handoff** (`tools/handoff.py` + `/cambium:pause` + `/cambium:resume`): writes a durable
  agent_outputs/HANDOFF.md from run_state + findings_ledger + synthesis (machine state embedded for lossless
  restore), restores on resume, archives consumed handoffs to archive/handoffs/. Durable memory across
  context windows instead of lossy auto-compaction. Folds in `loop_position` (run_state.py `loop`).
- **B · Context status line** (`tools/statusline.sh` + statusline.py): `⬢ Cambium · model · dir · ctx ~NN%`,
  flips to "⚠ run /cambium:pause" at ~85% so you pause before compaction. Documented in AUTORUN.md.
- **C · Guarded auto-loop** (`phases.yml → autoloop`): a phase may iterate its internal work until acceptance
  tests pass, then SURFACE its gate — fail-closed (max_iterations + budget_usd), integrity check each
  iteration, single-writer state, and it may ARM but NEVER clear a gate. Orchestrator + AUTORUN updated.
- Deferred: plan→task-graph deps (v3.3), Graphify/Obsidian brain. Rejected: /seed (redundant),
  Hermes/Railway deploy (Cambium isn't an app).
- New tests/test_handoff.py (pause/resume round-trip + autoloop guardrails). 36 tests pass, doctor 27/0,
  consistency clean. plugin.json + pyproject synced to 3.17.0. G2 approval logged in governance/GATES.md.

## 3.17.1 - End-to-end Cambium (no silent drop to solo)
- Fixes a contract gap the Director caught: when the Cambium way is chosen, the WHOLE task — including the
  BUILD/implementation AFTER an approval gate — must run Cambium (dispatch real Execution/Labs agents:
  research-engineer, exec-*, lab-methods). The Orchestrator must not quietly do the post-gate build inline.
  The only allowed alternative is to ASK the Director ("Cambium or solo for this build?") — never switch
  silently. Enforced in PRESENTATION.md (END-TO-END rule + 4th headline rule), commands/cambium.md,
  the Orchestrator agent, and the cambium-mode skill. 36 tests pass, doctor healthy.

## 3.17.2 - Consistency sweep (gate G-fix) + Execution build contract
- **Now-tier consistency sweep (gate G-fix, Director-approved):** repo-wide fixes verified against
  v3.17.1 source by the Verification council. Gate count "six lifecycle gates" → 8 (AI_GOVERNANCE.md,
  FAQ.md); "President" → "Director (PI)" regression fixed across AI_GOVERNANCE.md, FAQ.md,
  GETTING_STARTED.md, DEVELOPMENT_PLAYBOOK.md, COMPARISON.md, examples/demo-from-scratch/*,
  templates/project/README.md, config.example.yml; version "1.4" → 3.17.1 and "45 agents" → 46
  (ROADMAP.md, FAQ.md, CITATION.cff, tools/ci_ledger.csv).
- **CI guard hardened:** tools/consistency_check.py now catches the "<word> lifecycle gates" drift class
  that previously slipped through, and skips transient run artifacts (agent_outputs/, projects/ run boards).
- **Execution build contract (new):** research-engineer agent + run-lab skill now require chunked edits for
  files >40 lines (a truncated single-shot rewrite shipped a SyntaxError this run) and a verify-or-flag rule
  — run consistency_check/doctor/pytest and paste real output as Code-verified, or label results Asserted and
  hand verification to the Orchestrator. Never imply a green build you did not run.
- **Roster mirror re-synced:** agents/ was stale (27) vs canonical .claude/agents/ (46); ran
  tools/sync_plugin_agents.py → 46/46 in sync.
- Staged (not done): claim-tiered repositioning + Tier-A literature connectors (Next); enforcement-vs-soft-
  prompting A/B study + per-funder governance corpus with dating/owner/freshness-CI/non-certification
  guardrails (Later). Grants-discovery connectors dropped per ROADMAP non-goal.
- Verified: consistency_check exit 0 · doctor --grade A (100%) · 36 tests pass / 1 skipped · live roster 46.
  G-fix approval logged in governance/GATES.md.

## 3.17.3 - Record-keeper write discipline
- Folds the verify-or-flag discipline into the record-keeper agent (follow-through on ADR-025): APPEND-ONLY
  (never edit/reword an existing CHANGELOG block or ADR; new ADRs take the next unused number) and
  VERIFY-THE-WRITE (no shell → re-read the changed region, confirm the new entry landed and no prior line was
  modified, else report Asserted and hand to the Orchestrator). Prompted by a record-keeper run this session
  that claimed appends it never made and corrupted ADR-011's status line. Canonical + agents/ mirror in sync (46).
- Verified: consistency_check exit 0 · doctor --grade A · 36 tests pass / 1 skipped.

## 3.18.0 - Enforcement A/B harness + per-funder governance corpus (Later-tier)
- **Enforcement-vs-soft-prompting A/B harness** (`evals/enforcement_study/`): pre-registered PROTOCOL.md
  (TREATMENT = gates+validate.py enforcement vs BASELINE = soft-prompt; metrics defined as ratios against
  ground truth; blind GT-only judge to break the agent_eval circularity), a 12-item seeded-defect task set
  with locked ground truth, `metrics.py` (false-claim / over-claim / citation-integrity / reproducibility),
  and `run_study.py --demo` (runs end-to-end on fixtures). The study RESULT is **Open** — the harness ships;
  no "gates beat prompting" finding exists until real agent runs are done. Demo output is labeled
  FIXTURE/illustrative everywhere so it can't be mistaken for a result. Converts the report's central
  assertion into a measurable, continuously-runnable asset.
- **Per-funder governance corpus** (`governance/funders/`): machine-readable NIH + NSF entries mapping each
  funder's AI-use rules to Cambium gates, with all five mandated guardrails — dated, named owner (PI),
  quarterly cadence, `freshness_window_days`, and `DISCLAIMER.md` (non-certification: guidance, not legal/
  compliance certification; the human PI remains accountable; rules drift, re-verify at source).
  `tools/funder_freshness.py` HARD-FAILS on a stale or incomplete entry (warns at 75% of window) and is wired
  as a doctor check, so a drifting corpus can't silently ship false compliance assurance. NIH NOT-OD-25-132
  (6-app/PI/yr cap, "substantially developed by AI" rejection) and the NSF reviewer gen-AI prohibition were
  **source-verified** (2026-06-26) against the funders' own notices, not asserted.
- Tests: +68 (enforcement_study + funder_freshness). Verified: consistency_check exit 0 · doctor --grade A
  (100%) · pytest 104 passed / 1 skipped · funder_freshness OK · run_study --demo OK. Gates G-build + G-ship
  Director-pre-approved (AUTO) this run; logged in governance/GATES.md. Manifests bumped 3.17.1 → 3.18.0.

## 1.00.1 - 2026-06-26 — World-class README + landing-page overhaul
- **README rewrite** to a top-1% standard (Referee 9.3/10, Integrity PASS-WITH-FIXES): live GitHub-Actions
  CI badge, flat-square badge row, version badge, nav-anchor bar, demo.gif above all prose, GitHub Alerts
  ([!IMPORTANT]/[!TIP]/[!WARNING]/[!NOTE]), a new "Proving the claim" section surfacing the enforcement A/B
  harness (result Open — no overclaim) and the NIH/NSF governance corpus, GIF static-fallback, dated
  self-grade, COMPARISON hedge on the superlative, and the stale "26-test" → "104 passed / 1 skipped" fix.
- **Landing page (index.html) overhaul**: fixed a stale hero stat strip (34/9/6 → canonical 46/11/8) and a
  stale "Six human gates" → "Eight" (added G0); modernized the badge row (flat-square, live CI, version
  1.00.0); added a "Proving it — not just claiming it" governance box (enforcement harness + funder corpus,
  claim-tiered, dated grade, 104 tests). Recovered + rebuilt the file after a mount write-truncation;
  HTML integrity restored.
- Both audited by the Verification council; claims kept at/below their evidence tier (no "beats prompting").
- Verified: consistency exit 0 · doctor --grade A (100%, HTML integrity 100%) · 104 tests pass / 1 skipped.

## 1.00.2 - 2026-06-26 — Per-run state reset (board hygiene fix)
- **Root-cause fix for stale run boards.** Reusing one `agent_outputs/run_state.json` across runs leaked a
  previous run's phase/findings onto the next board (e.g. a README run's board showing a git-fix run's
  "## ADR-025 / 36 tests" findings). Fix: `tools/run_state.py reset` now stamps a `started_at` timestamp,
  and `sync` ignores any `agent_outputs/*.md` older than it — so stale prior-run files can't repopulate the
  board (important here because the working mount can't delete those files). The Cambium-way contract
  (`commands/cambium.md`, `PRESENTATION.md`) now calls `run_state.py reset` as the first action of Act I.
- Regression tests: `tests/test_run_state.py` (reset stamps started_at + clears; sync ignores stale files).
- Cleaned the older run-board artifacts (landscape-review, enforcement-governance) to show their own real
  findings instead of carried-over state.
- Verified: consistency exit 0 · doctor --grade A · 106 tests pass / 1 skipped.

## 1.00.3 - 2026-06-27 — World-class comprehensive README
- Full README rebuild from a deep discovery pass (research-assistant capability catalog, scout-landscape
  positioning, teaching-assistant how-to-use, outreach architecture — ~14k words of file-cited ground truth).
  The old README surfaced ~⅓ of the system; the new 400-line / 16-section README reflects the TRUE current
  Cambium: full 46-agent/11-council roster, 8 gates with approvers + separation of duties, the 21 skills,
  21 tools, 6 MCP tools, 13 templates, 5 examples, governance corpus, model routing (12/32/2), pause/resume,
  the guarded auto-loop, and the A/B harness — scannable via tables + <details>, with a how-to-use story +
  trigger reference and 6 standout pillars.
- Verified: Referee ACCEPT (9/9 across hero/completeness/scannability/usability/voice/structure; all nav
  anchors + asset/doc links checked). Integrity PASS-WITH-FIXES, all applied: hedged the "only open system"
  superlative at point of assertion; 14→13 templates; full claude-haiku-4-5-20251001 id; honestly relabeled
  the two pre-award example slices (dropped "proven"). A/B result kept Open; corpus = guidance not cert.
- Assets: assets/org-chart.svg regenerated from the live roster (46/11). All assets current.
- Green: consistency exit 0 · doctor --grade A (100%) · 113 tests pass / 1 skipped.

## 1.00.4 - 2026-06-27 — Brand asset redesign (logos, social card, favicon)
- Recreated the full brand-identity asset set at premium quality, rasterized SVG→PNG with cairosvg and the
  Inter typeface, from one reproducible source (`tools/gen_brand_assets.py`) — the repo's "regenerate from
  source" philosophy. Refined the "Living Layer" growth-ring mark (precise concentric emerald rings,
  layered lime active-node glow, radial spoke, faint org-satellite nodes, gradient tile + top sheen):
  - `logo-mark.svg` + `logo-mark.png` (512) + `logo-mark@2x.png` (1024) — the app-icon mark
  - `logo.svg` (light) + `logo-dark.svg` (dark) — wordmark lockups (Inter ExtraBold "Cambium." + lime dot + tracked subtitle), viewBox sized so nothing clips
  - `social-preview.svg` + `social-preview.png` (1280×640) — GitHub social card with a subtle org-constellation background, measured to fit (no text overflow)
  - `favicon.svg` + `favicon.png` (180) — new
- Wired `favicon` + Open Graph / Twitter-card meta (`og:image` → social card) into `index.html`.
- Brand tokens unchanged (BRAND.md "Living Layer" palette). All SVGs validate; PNG dimensions confirmed.
- Green: consistency exit 0 · doctor --grade A (100%, HTML integrity intact) · 113 tests pass.
- Action: re-upload the new `assets/social-preview.png` in GitHub Settings → Social preview (replaces the old card).

## 1.00.5 - 2026-06-27 — Logo v2: "Governed Growth Ring" identity
- Redesigned the brand mark from a richer, story-telling concept (inspired by reference directions): the
  mark now encodes Cambium itself — **8 gate-checkpoints** (amber keyhole+check = the 8 human gates) on the
  outer ring, concentric **emerald growth rings** (the cambium), the central **Director (PI)**, eight
  **council branch spokes** with leaf buds, a **lime radar sweep** to the active gate, and a single
  **red ✕ caught-error node** (the Verification board blocking a bad result). Clean flat vector, fully
  scalable — sharper and more meaningful than the references' raster art, on the "Living Layer" palette.
- Regenerated the whole set from `tools/gen_brand_assets.py` (v2): `logo-mark` (.svg + 512/1024 png),
  `logo`/`logo-dark` wordmarks (subtitle now "PORTABLE · GOVERNED · RESEARCH"), `social-preview` (1280×640),
  `favicon` (a simplified mini-mark for small sizes). BRAND.md motif section updated to match.
- Green: consistency exit 0 · doctor --grade A (100%) · all SVGs validate · PNG dims confirmed.
- Action: push, then re-upload the new `assets/social-preview.png` in GitHub Settings → Social preview.

## 1.00.6 - 2026-06-27 — Logo finalized: the "Living Tree" (blend)
- Final brand mark (supersedes the interim governance-ring in 1.00.5): a **tree of life** — symmetric
  canopy + roots with lime leaf clusters — rising from the concentric **growth rings** (the literal
  cambium), with the **8 gate-checkpoints** on the outer ring, a **lime radar sweep** to the active gate,
  a **red ✕ caught-error** node (Verification blocking a bad result), and the **Director (PI)** grounded at
  the roots. Blends the botanical + governance reference directions the Director chose. Clean flat vector.
- Regenerated the whole set from `tools/gen_brand_assets.py`: logo-mark (.svg + 512/1024), light/dark
  wordmarks (clean tier mark), social-preview (1280×640), favicon (mini tier). BRAND.md motif updated to
  "the Living Tree".
- Green: consistency exit 0 · doctor --grade A (100%) · all SVGs validate · social 1280×640.
- Action: push, then re-upload `assets/social-preview.png` in GitHub Settings → Social preview.

## 1.00.7 - 2026-06-27 — Logo: vector recreation of the "AI Research Institution" emblem (transparent)
- Recreated the Director's chosen emblem as clean vector with a **transparent background** (supersedes the
  Living-Tree mark): a wood-ring tree cross-section (deep green → teal → gold rings), a gold neural
  node-network branching through one quadrant, a glowing gold active blip, a thin open arc frame
  (emerald → gold), emerald leaves, and the **CAMBIUM AI · RESEARCH INSTITUTION** wordmark.
- Light + dark lockups (transparent, swap cleanly in GitHub's <picture>), emblem-only `logo-mark`,
  `social-preview` (1280×640, emblem + wordmark + tagline + stats on the brand dark bg), and `favicon`.
  All from `tools/gen_brand_assets.py` (regenerated); BRAND.md motif updated.
- Green: consistency exit 0 · doctor --grade A (100%) · all SVGs validate · social 1280×640.
- Action: push, then re-upload `assets/social-preview.png` in Settings → Social preview.

## 1.00.8 - 2026-06-27 — Adopt the official logo (assets/Cambium_logo.png)
- Replaced the generated marks with the Director's **official logo** (`assets/Cambium_logo.png`, transparent)
  and built all derivatives directly from it: `logo.png` (light), `logo-dark.png` (wordmark recolored to
  canvas for dark mode), `logo-mark.png` (cropped emblem), `favicon.png`, and the 1280×640 `social-preview.png`
  (the real emblem + white CAMBIUM AI wordmark + tagline + stats on the brand dark).
- README hero now uses the PNG logo via <picture> (light/dark); index.html favicon → favicon.png.
  BRAND.md points to Cambium_logo.png as the canonical source.
- Green: consistency exit 0 · doctor --grade A (100%, index.html intact) · README + index intact.
- Action: push, then re-upload `assets/social-preview.png` in Settings → Social preview.

## 1.00.9 - 2026-06-27 — Hi-res logo (background keyed out, all derivatives rebuilt)
- Adopted the Director's high-resolution official logo (`assets/cambium ai logo.png`, 1407×768). Keyed out
  the cream mockup background to transparent (feathered edges, no halo), tight-cropped, and rebuilt every
  derivative at full quality from it: `logo.png` (514×574, light), `logo-dark.png` (white wordmark for dark
  mode), `logo-mark.png` (1024² emblem), `favicon.png`, and the 1280×640 `social-preview.png` (crisp emblem +
  white CAMBIUM AI wordmark + tagline + stats). README hero + index favicon already point to these.
- Green: consistency exit 0 · doctor --grade A (100%) · README + index intact.
- Action: push, then re-upload `assets/social-preview.png` in Settings → Social preview.

## 1.00.10 - 2026-06-27 — OpenMontage integration (first slice, MIT-clean)
- Assessed (Cambium way: Toolsmith + Faculty/architecture + Research-Conduct-Officer) and designed the
  integration of **OpenMontage** (open-source agentic video production, **AGPLv3**) into Cambium, then built
  the MIT-clean first slice: `skills/render-video/` — a Reporting-council skill that produces video
  deliverables (video abstract, grant-pitch, results explainer) by **invoking a separately-installed
  OpenMontage as an external subprocess** + `video_contract.schema.json` (evidence-bound request/result,
  only Proved/Code-verified inputs) + `PROVISION.md` (separate install, zero-key free path, AGPL note).
  Recorded as ADR-028. **No OpenMontage code vendored** (process boundary = license boundary; Cambium stays MIT).
- Green: consistency exit 0 · doctor --grade A (100%) · 113 tests pass · JSON schema valid.

## 1.00.11 - 2026-06-27 — Wire render-video into routing + Reporting agents
- `tools/task_router.py`: new **video** task type — "make a video / video abstract / explainer / grant
  video / results explainer / teaser" now routes to **provision (G-provision) → produce (Reporting +
  figures/outreach, G5) → publish (G6) → close-out**, so the board and MCP `cambium_plan` mobilize the
  right council automatically. Guarded by the existing router-coverage test.
- Wired the `render-video` skill into SKILLS_MAP.md and the Relevant-skills line of `deck-builder`,
  `reporting-officer`, and `outreach` (canonical + agents/ mirror, 46/46).
- Green: router test passes · check_agents OK · consistency exit 0 · doctor --grade A · 113 tests pass.

## 1.00.12 - 2026-06-27 — Provenance manifest + e2e worked example + domain configs
- **Machine-checkable provenance manifest** (`tools/provenance.py`, ADR-029): `build` re-runs each
  Code-verified claim's recorded command, hashes command+script+output, and writes a manifest; `check`
  re-runs and fails on any output drift. Turns "Code-verified by convention" into reproduced-and-hashed.
- **End-to-end worked example** (`examples/e2e-worked-example/`): a full artifact chain RFP→aims→proposal→
  deterministic `code/analysis.py`→findings_ledger→provenance_manifest→report, with the headline number
  (3.06 bu/acre) reproduced + hashed (not asserted). Self-reproducing via `provenance.py check`.
- **2 non-ML domain configs** (`examples/configs/`: social-science survey, agricultural field trials).
- Tests +2 (`tests/test_provenance.py`, incl. drift-detection). Tool count 21→23; README corrected.
- Also: ran a full **Cambium self-evaluation** (Referee+Faculty+Scout) — `agent_outputs/EVALUATION.md`,
  overall B+, with prioritized suggestions (top: prove the enforcement A/B; wire a retrieval backend).
- Green: consistency exit 0 · doctor --grade A (100%) · 115 tests pass / 1 skipped · e2e manifest reproduces.

## 1.00.13 - 2026-06-27 — Grounded retrieval + speed/cost telemetry (eval #2, #4)
- **Deep search (#2):** `tools/paper_search.py` — grounded scholarly retrieval over OpenAlex + Crossref
  (no API key, offline-safe), returning structured citable records; wired into the 3 Scouts + Librarian.
  Fixes the "thin web-search wrapper" weakness (deep-search 5 → grounded corpus).
- **Speed (#4):** `tools/cambium_run.py` now logs per-agent wall-clock + tokens + est_usd to
  `agent_outputs/cost_log.csv` on every live call — the EFFICIENCY.md cost-telemetry policy is now real data.
- Tests +5 across the two (parsers + estimate/log). Tool count 23→24; README corrected. ADR-030.
- Green: consistency exit 0 · doctor --grade A (100%) · 120 tests pass / 1 skipped · live retrieval verified.

## 1.00.14 - 2026-06-27 — Gate interlock + finding-audit + funder corpus & demonstrated post-award (eval #3, #6, #7)
- **#3 Live gate interlock:** `tools/gate.py` runs `governance/validate.py` against the **production** ledger
  and mechanically **BLOCKS** the gate (exit 1) on an open P0 / un-evidenced `Code-verified` / unresolved
  citation — "human-in-the-loop by convention" -> an enforced precondition (closes eval seams A/B).
- **#6 Independent finding-audit:** `tools/finding_audit.py` flags any agent self-report claiming
  completion/verification **without** supporting evidence — stops the board blindly trusting `## Decision`
  (closes seam C; directly targets the over-claiming pattern).
- **CI wires both to REAL committed artifacts:** `validate.yml` now gates + provenance-checks the
  `e2e-worked-example` ledger and runs the finding-audit — not just the hand-curated stand-in (seam B).
  The interlock immediately caught a real gap (Code-verified evidence cell missing its run command) and forced the fix.
- **#7 Funder corpus -> 4 funders:** added source-verified `governance/funders/usda-afri.yml` and `doe.yml`
  (key honest finding: DOE-P-2031 *explicitly excludes financial-assistance recipients*; no applicant-facing
  AI-drafting prohibition located for USDA-AFRI or DOE — stated plainly, freshness-CI passing).
- **#7 Demonstrated post-award:** `examples/e2e-worked-example/04_postaward_runlab.md` — the G4 run-lab loop
  (provision -> run -> reproduce+hash -> gate decision card) using the real tools, closing the "post-award
  execution documented-not-demonstrated" scope gap. Worked examples 5->6; README reconciled.
- Tests +3 (gate blocks/opens, audit flags). Tool count 24->26; README + roadmap reconciled. ADR-031.
- Green: consistency exit 0 · doctor --grade A (100%) · 123 tests pass / 1 skipped · funder-freshness OK (4/4).

## 1.00.15 - 2026-06-27 — Enforcement A/B pilot is RUNNABLE end-to-end (eval #1, the last gap)
- **The central claim's harness is now complete.** Added the missing agent-runner + judge + stats so a
  real arm can actually be run, not just scored:
  - `evals/enforcement_study/run_arm.py` — runs both arms (TREATMENT = enforcement on; BASELINE = soft
    prompt only) over the 12 held-out seeded-defect tasks; stdlib-only; reads ANTHROPIC_API_KEY from the
    environment (the key never touches the repo or any other party); `--dry-run` for keyless wiring tests.
  - `evals/enforcement_study/judge_stage1.py` — deterministic, **arm-blind** Stage-1 judge; scores the
    primary **false-claim rate** + citation integrity; OCR/RR honestly **deferred** to the Stage-2 human
    panel (an automated tier-proxy would bias against the enforced arm — we refuse to ship a biased metric).
  - `evals/enforcement_study/analyze.py` — Cohen's h, Wilson 95% CIs, one-sided two-proportion z, Newcombe
    difference CI, Bonferroni; writes `RESULTS.md`. Stdlib math only.
  - `evals/enforcement_study/run_pilot.py` — one command runs the whole chain.
- **Honesty preserved:** study result stays **OPEN**; `RESULTS.md` is an honest placeholder until a live
  run; fixture/demo inputs are hard-guarded as "NOT A FINDING"; regenerable artifacts gitignored.
- **Verified without a key:** judge discriminates (synthetic honest arm FCR 0.00 vs careless 1.00,
  Cohen's h -3.14, p<1e-6); fixture guard fires; +7 tests. The only thing left is the live API run.
- Green: consistency exit 0 · doctor --grade A (100%) · 130 tests pass / 1 skipped. ADR-032.

## 1.00.16 - 2026-06-27 — Enforcement A/B pilot was actually RUN (eval #1): real Opus arms, no effect detected
- **The central claim was tested for the first time.** Ran both arms live on **claude-opus-4-8** over the
  12 held-out seeded-defect tasks (24 real agent runs, Claude Code headless backend), scored arm-blind.
- **Result (pilot, automated judge):** false-claim rate Treatment 0.33 vs Baseline 0.25, difference
  +0.08 (95% CI [-0.12, +0.28]), Cohen's h 0.18, p=0.78; citation integrity 1.00 vs 1.00. **No measurable
  enforcement effect** — both arms near-ceiling honest (hand-verified: both flag the fabricated citations
  and compute the numbers correctly). Central claim stays honestly **OPEN** (underpowered n=12; not a null).
- **Judge recalibration (honest):** fixed a scoring bug where correct answers were marked as missed —
  redefined "missed" as *asserting the false claim as fact* (protocol §4.1), not merely failing to flag.
  Documented the residual limitation (automated judge can't separate "summarize-then-flag" from "endorse"),
  which inflates *absolute* rates in both arms equally; the between-arm comparison is the robust part.
- **Windows/runner hardening:** `run_arm.py` now resolves the real `claude` launcher (npm ships `claude.ps1`
  which Python can't exec → use `cmd /c claude.cmd`), forces UTF-8 decoding (fixes the cp1252 crash),
  passes the system prompt as a file with stdin task delivery, runs from an isolated cwd (no project-context
  contamination), and fails fast with a clear message if `claude` isn't on PATH. Added `--limit` (smoke test)
  and `run_pilot.py --rescore` (re-judge existing outputs, no API cost).
- Full write-up + caveats: `evals/enforcement_study/RESULTS.md`. ADR-033.

## 1.00.17 - 2026-06-27 — PHILOSOPHY.md: the North Star, the honest gaps, and the design direction (Cambium way)
- Ran the Cambium way (Faculty · PI; Governance · Research Conduct; Support · Teaching Assistant, Integrity
  Officer, Outreach) → synthesized → human gate **G-philosophy APPROVED** (governance/GATES.md).
- New `PHILOSOPHY.md` — Cambium's foundational document. North Star: "Use AI to expand scientific capacity,
  but keep human judgment responsible for validity, ethics, and decisions." Contents: the problem (process
  vs artifact; funders pay for the years, not the day); the thesis + 4 principles (expand-not-replace,
  process-is-the-product, pace-as-a-feature, human-supplies-judgment); an honest six-concern map (responsible
  use / ethics / judgment-at-decisions = addressed; creativity + learning-while-doing = not structurally yet);
  a candid, file-cited gaps section; and a Section-5 design direction (Director Brief, Learning Gate with a
  required Section 8, teaching in-line, a Contribution Ledger, a deliberation window, a capacity check).
- Honest framing preserved: Section-5 features are **proposed direction, not yet shipped**.
- Published the live **Cambium run board** as a Cowork artifact (four acts · five named agents · the gate).

## 1.00.18 - 2026-06-27 — Run-board wiring + the Learning Gate (PHILOSOPHY.md §5, now built)
- **Run board (Track A):** `tools/run_trace.py` now (1) reads a CUSTOM plan from `run_state.json` so the
  board shows the REAL dispatched roster (named agents + findings), not the generic routed plan; and
  (2) gains `--light` so the HTML dashboard renders correctly as a Cowork artifact. The published board is
  now generated by the built-in tool (`run_trace.py --html --light`), not hand-drawn. Text-board spacing
  polished for long labels.
- **Learning Gate (Track B) — closes concerns #3 (creativity) & #4 (learning) from "claimed" to "enforced":**
  - `templates/GATE_SUMMARY.md` gains a required **Section 8 (Director contribution)** — your hypothesis,
    reasoning, justified choice, and a Socratic answer; a bare APPROVE no longer advances the run.
  - `templates/DIRECTOR_BRIEF.md` — the pre-phase brief (the "Creative Trace"): the AI doesn't start a phase
    until you submit your question, expected surprise, and a constraint.
  - `tools/learning_gate.py` — deterministically verifies the contribution is genuinely present (≥40-word
    hypothesis/reasoning, non-blank choice + Socratic answer) with a copy-from-AI similarity flag, and appends
    it — timestamped, append-only — to `governance/CONTRIBUTION_LEDGER.csv`. Blocks the gate if incomplete.
  - Tests: `tests/test_learning_gate.py` (+6). Verified live: complete → gate may open; incomplete → BLOCKED.
- Counts: tools 26→27, templates 13→14 (README reconciled). PRESENTATION Act III + PHILOSOPHY §5 updated.
- Honest scope: the Orchestrator-level AUTO-enforcement (firing learning_gate on every gate) is the remaining
  integration; the template + tool + ledger exist and are tested now.
- Green: consistency exit 0 · doctor --grade A (100%) · 136 tests pass / 1 skipped. ADR-035.

## 1.00.19 - 2026-06-27 — POSITIONING.md: verified Top-10 scorecard (Cambium way)
- New `POSITIONING.md` — Cambium graded against the field's 10 institutional AI concerns (Elsevier/Aalto/
  Illinois), produced the Cambium way: four council agents (Scouts·Landscape, Verification·Domain,
  Support·Integrity-Officer, Governance·Research-Conduct) graded independently and **converged**:
  **3 Leads (assist-not-author, visibility, authorship) · 5 Partial · 2 Gaps (bias, cross-institution)**,
  every verdict traced to a repo file; approved at gate G-positioning.
- Includes the differentiation wedge (governed pace + measurable value + learning), the hardest blocker
  (cross-institution / consortium grants), three non-negotiable honesty caveats, and a six-repair roadmap.
- Honest framing preserved (Asserted tier; Learning-Gate auto-enforcement unwired; A/B Open; citation advisory).

## 1.00.20 - 2026-06-27 — Interactive run board: approve from the artifact
- `tools/run_trace.py --html` now renders the active-gate banner with **clickable APPROVE / REVISE / REJECT
  buttons**. In a Cowork artifact they call `sendPrompt("APPROVE <gate-id>")` so the Director can decide
  straight from the run board; outside Cowork they fall back to copying the decision to the clipboard.
  Wired into the built-in generator, so every future run board is actionable, not just a picture.

## 1.00.21 - 2026-06-27 — Close the positioning scorecard: 6 repairs + bias module + specs
- **Repair #1 (Learning Gate enforced):** `tools/gate.py --require-contribution` blocks a decision gate
  unless the Director's contribution (hypothesis + reasoning + choice + Socratic answer) passes
  `learning_gate.py`. A bare APPROVE no longer advances. (Orchestrator auto-passing it on every gate is the
  one piece left.)
- **Repair #2 (trusted content):** `citation_support="unsupported"` is now a **release blocker** in
  `governance/validate.py` ('partial'/'anchorless' stay advisory; absent column = back-compat no-op).
- **Gap #5 → Partial (bias):** new `templates/BIAS_MITIGATION_CHECKLIST.md` (NIST AI RMF MAP/MEASURE/MANAGE)
  + an advisory `bias_check` ledger column surfaced by `validate.py`.
- **Repair #4 (data governance):** new `governance/REGULATED_DATA.md` — a default-deny intake control with a
  gate-enforced approved-pathway requirement (procedural; encrypted enclave remains future infra).
- **Repair #5 (provenance):** CI validate step now sets `AI_MODEL`; `validate.py` warns when it's unset.
- **Gap #9 (cross-institution):** `ARCHITECTURE_MULTI_INSTITUTION.md` — honest staged spec (multi-PI roles
  next; shared infrastructure on the roadmap). Still a Gap — a spec, not infrastructure.
- Tests +6 (`tests/test_repairs.py`). Templates 14→15. POSITIONING updated to **3 Leads · 6 Partial · 1 Gap**.
- **Correction to 1.00.20:** the sidebar run-board's APPROVE buttons can NOT post to chat — the Cowork
  artifact API exposes `callMcpTool`/`askClaude`, not a send-to-chat hook. Fixed to honest copy-to-clipboard
  feedback; a genuinely-clickable gate uses an inline widget (`sendPrompt`). ADR-036.
- Green: consistency exit 0 · doctor --grade A (100%) · 142 tests pass / 1 skipped · CI ledger green.

## 1.00.22 - 2026-06-27 — Inline gate cards (default) + Learning-Gate auto-fire + multi-PI Stage-1 roles
- **Inline gate cards are now the default UX** (`templates/INLINE_GATE_CARD.html`, rendered via the visualize
  `show_widget`): APPROVE / REVISE / REJECT buttons that genuinely post the decision to chat (`sendPrompt`).
  PRESENTATION Act III mandates them alongside the verbatim GATE_SUMMARY one-pager. (Sidebar artifacts still
  can't post to chat — they copy the decision text.)
- **Learning-Gate auto-fire:** Act III now MANDATES `tools/gate.py --require-contribution` before recording
  ANY decision-gate APPROVE — a bare APPROVE / incomplete Director contribution is blocked on every gate, not
  by convention. (Honest: it's an Orchestrator-followed contract, not yet an un-bypassable runtime lock.)
- **Multi-PI Stage-1 roles (part of concern #9):** `tools/gate.py --required-approver` blocks a gate unless
  the *named* institution-scoped approver signs; `templates/MULTI_PI_ROLES.yml` maps gate→approver across
  institutions (separation of duties on shared git; no server yet — that's Stage 2).
- Tests +2 (named-approver block/open) → 144 pass. Templates → 17. POSITIONING #2/#9 notes + caveat #1 updated.
- Green: consistency exit 0 · doctor --grade A (100%) · 144 tests pass / 1 skipped · CI ledger green. ADR-037.

## 1.00.23 - 2026-06-27 — Put the Support council to work + automatic close-out (no more doc drift)
- **Diagnosis (Director-flagged):** every prior close-out was done inline — the real Support council never
  ran — so the forward docs drifted: ROADMAP said "Last updated 2026-06-26" and the user docs never
  mentioned the Learning Gate, bias module, multi-PI roles, or the A/B pilot.
- **Support council actually dispatched** (Outreach · Record-Keeper · Janitor): refreshed `ROADMAP.md`
  (now lists everything shipped, bumped to 2026-06-27), the README roadmap paragraph, and `USE_CAMBIUM.md`
  (Learning-Gate + click-to-approve section); record-keeper verified CHANGELOG 1.00.13–22 / ADR-030–037 /
  4 gates all present; janitor flagged + fixed a long-standing **duplicate ADR-008 → ADR-012**.
- **Automatic close-out so it can't recur:** new `tools/closeout.py` FAILS close-out if the latest CHANGELOG
  date is newer than a forward doc's `Last updated:` (doc drift); `templates/CLOSEOUT_CHECKLIST.md` lists who
  refreshes what; **PRESENTATION Act IV now mandates dispatching the real Support council + `closeout.py`
  exit 0** — inline close-out is a contract violation.
- Tests +4 (`tests/test_closeout.py`). Tools 27→28; templates →17; README reconciled.
- Green: consistency exit 0 · doctor --grade A (100%) · 148 tests pass / 1 skipped · closeout OK. ADR-038.
