# Changelog

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
