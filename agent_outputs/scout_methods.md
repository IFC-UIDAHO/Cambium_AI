## Decision

Adopt two patterns with real lift: **PAUL Pause/Resume handoff** (Cambium has no context-window recovery mechanism) and a **lightweight /goal autonomous loop** (Cambium stops at every gate by design, but has no intra-phase "keep going until done" primitive). Everything else is redundant or low-fit.

---

## Per-Pattern Analysis

| # | Pattern | One-line description | Cambium equivalent? | Field alternatives | Adoption value |
|---|---------|---------------------|--------------------|--------------------|----------------|
| 1 | **SEED interview → planning doc** | Structured Q&A converts a vague idea into a clean spec before any build starts | **Partial** — `IDEA_INBOX.md` (drop raw ideas) + `new_project.py` (scaffold) cover this. No interactive interview loop exists. | LangChain `ChatPromptTemplate` chains; OpenAI Assistants thread interviews | **Low** — Cambium's pre-award lifecycle (RFP radar → ideation → G1 gate) already elicits the same information more rigorously and with evidence tiers. Replacing it with a one-shot `/seed` chat would strip governance. |
| 2 | **PAUL state file (project position + loop position)** | A machine-readable file captures current phase, milestone, and loop counter so any new session starts in the right place | **Partial** — `run_state.json` tracks phase, findings, leaderboard, gate. No "loop position within a phase" counter. | Prefect `FlowRun` state store; LangGraph `StateGraph` checkpointer | **Medium** — `run_state.json` already does the heavy lifting. Adding a `loop_position` field (e.g., which sub-phase step within a phase) is a small targeted lift, not a full adoption. |
| 3 | **PAUL Pause/Resume handoff document** | Running `/paul pause` writes a dense snapshot of exact session context; `/paul resume` in a fresh window re-injects it and archives the old snapshot | **None** — Cambium has no context-window recovery path. When a long Orchestrator session fills up, there is no structured re-entry. The closest is `--resume <phase>` in `cambium_run.py`, which resumes by phase but not by exact intra-phase position or conversation state. | [PAUL on GitHub](https://github.com/ChristopherKahler/paul) v1.4 (verified June 2026); LangGraph `MemorySaver` checkpoint/restore | **High** — Real gap. Long multi-phase Cambium runs (46 agents, research lifecycles) routinely saturate context. A `cambium pause` / `cambium resume` command writing a structured HANDOFF.md and archiving old ones would solve a practical pain point without touching governance. Evidence tier: Code-verified (PAUL repo exists, npm package `paul-framework` verified). |
| 4 | **GOAL autonomous loop (run until done, pause only at human checkpoints)** | A `/goal` command sets a completion condition; the agent loops Plan→Apply→Unify by itself, surfacing only mandatory human-verification checkpoints | **Partial** — Cambium's phase loop is explicit-dispatch (Orchestrator dispatches each agent group, then re-emits the board). There is no intra-phase "keep looping until this phase's acceptance tests pass" primitive. The AUTORUN `--live` mode is close but halts at every gate, not at acceptance criteria. | Native Claude Code `/goal` (v2.1.139+, [official docs](https://code.claude.com/docs/en/goal)); ARIS autonomous research loop (wanshuiyin/auto-claude-code-research-in-sleep) | **Medium-High** — Worth a constrained version: an "autorun phase" command that loops within a single phase until the phase's acceptance test passes, then surfaces the gate. Preserves all human gates while removing the need for the Director to manually prompt each micro-iteration. Evidence tier: Asserted (PAUL's GOAL is a slash command on top of Claude Code's native `/goal`; Cambium would implement its own bounded version). |
| 5 | **Graphify + Obsidian knowledge graph** | Static AST-based graph of all codebase assets, exported to Obsidian for visual browsing and queryable from Claude Code (71x token savings claimed) | **None** — Cambium has no asset graph. `run_trace.py` renders a workflow plan but not a relationship graph of agent files. | [Graphify](https://graphify.net/) (verified June 2026, 20 languages, zero-token AST mode); `code2flow`; `py2cfg` | **Low for now** — Cambium is a research/proposal tool, not a deep codebase. Its ~32 Python files and ~80 Markdown files are small enough that context pressure from re-reading is minimal. Revisit at v2.0 when agent count grows. |
| 6 | **Status line (context % display)** | A shell script piped to Claude Code's status bar shows live context-window percentage, preventing silent compaction mid-run | **None explicit** — No status line in Cambium. Context exhaustion is a real risk during long Orchestrator runs. | Native Claude Code `/statusline` ([official docs](https://code.claude.com/docs/en/statusline), verified); `ccusage` tool | **Medium** — Cheap to add (one `/statusline` invocation in Orchestrator setup). Directly enables the Pause/Resume pattern: user sees context % rising and knows when to pause. Document in AUTORUN.md. Evidence tier: Code-verified (native Claude Code feature). |
| 7 | **Hermes model-agnostic VPS agent** | A separate always-on VPS agent receives Claude Code skills via MCP and is reachable from Slack/phone anywhere | **None — and out of scope** — Cambium is explicitly local; AUTORUN.md does not deploy anywhere. | [Hermes Agent](https://github.com/NousResearch/hermes-agent) (verified, Nous Research, Feb 2026, 100K+ stars); n8n on VPS | **Low** — Cambium is not a web app and does not deploy to hosting. Hermes is purpose-built for personal productivity dashboards. Hard mismatch with research-institution lifecycle tool. |
| 8 | **Railway deployment + mobile access** | Pushes the built app to Railway for persistent web hosting, accessible as a mobile app | **Out of scope** — ROADMAP.md explicitly: "Not a web app. Does not deploy to hosting." | Railway CLI; Render; Fly.io | **Redundant** — Doesn't apply. |

---

## Evidence tiers used

- **Code-verified**: PAUL on GitHub (real npm package `paul-framework`, active as of June 2026); Claude Code `/goal` (official docs); Claude Code `/statusline` (official docs); Graphify (live site + GitHub repo).
- **Asserted**: Token savings claims (71x figure from Graphify community articles — not independently reproduced here; faculty discipline in ML systems benchmarking should weigh in before adopting this number). PAUL's GOAL slash command behavior as described in video — real, but evaluation data on multi-agent sessions is absent.
- **Open**: Whether PAUL's handoff quality degrades for long multi-agent runs vs. single-session coding projects (no published evaluation found).

---

## Main weakness of adopting these patterns

PAUL Pause/Resume was designed for single-developer coding sessions, not 46-agent parallel institution runs. A Cambium handoff must capture which agents have reported, what the current `run_state.json` contains, and which gate is pending — not just "loop position 0102." Naively copying PAUL's format would underspecify the multi-agent state. **The right move is a Cambium-native `cambium pause` command that serializes `run_state.json` + a human-readable HANDOFF.md**, borrowing the pattern but not the implementation verbatim.

---

## Next action

1. **Implement `cambium pause` / `cambium resume`** — add to `tools/run_state.py` or a new `tools/handoff.py`: serialize `run_state.json` + phase/gate/finding summary into `agent_outputs/HANDOFF.md`; on resume, re-inject it and archive the old one. Estimated: small tool, one sprint.
2. **Document `/statusline` setup in AUTORUN.md** as standard practice for Orchestrator sessions — zero-code, immediate benefit.
3. **Defer `/goal` loop** until Pause/Resume is stable; then prototype an `autorun_phase` function in `cambium_run.py` that loops within a phase until acceptance criteria pass before surfacing the gate.

---

## Confidence

**High** on the gap diagnosis (no context recovery, no intra-phase loop primitive). **Medium** on the GOAL adoption value — the benefit depends on how often Directors drive multi-iteration phases vs. accepting first-pass agent output. Faculty/Orchestrator discipline must weigh in before the GOAL loop is opened to phases that contain governance-sensitive steps (G2, G3).

*Generated by SCOUT-METHODS · 2026-06-26*
