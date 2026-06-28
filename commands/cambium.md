---
description: Run a task the Cambium way — Orchestrator + the needed councils, with a live run board, real named agents, and a human approval gate before anything is finalized.
argument-hint: <what you want done>
---

Run the following request **the Cambium way**, not solo.

Request: $ARGUMENTS

> ⛔ **FIRST PAINT — do this literally before writing ANY prose.** Your very first action is to run:
>
> ```
> python3 tools/cambium_start.py "$ARGUMENTS"
> ```
>
> Show its output (the branded run board). It resets the run state, prints the text board, writes
> `agent_outputs/run_board.html`, and tells you what to do next. **In Cowork, paint the in-chat live board:
> run `python3 tools/gen_inline_board.py` and pass its stdout to `mcp__visualize__show_widget` (title
> "Cambium run board") so the Director sees the agent boxes + clickable gate in chat — and also publish
> `run_board.html` as a reopenable artifact with `create_artifact` (keep its id). Re-render both each phase.**
> Do NOT answer this request in plain text. If you find yourself about to reply without having shown the
> board, STOP and run the command above first. A plain-text answer to `/cambium` is the one failure this
> command exists to prevent.

Hand off to the **Orchestrator** and present the run as the four acts in **PRESENTATION.md** (read it; it
is the contract). The Cambium way must never look generic — the Director always sees which **named agents**
are working, on what, and where the gates are.

**Act I — Opening (before any work).** The `cambium_start.py` call above IS Act I. After the board is shown
(and, in Cowork, published as the "Cambium run board" artifact), add one plain sentence: how many
specialists, councils, and gates are about to run. Then, as you proceed, keep the live board current with
`python3 tools/run_state.py phase <N>` + `python3 tools/run_trace.py --html --out agent_outputs/run_board.html "$ARGUMENTS"`
and push it to the SAME artifact with `update_artifact`. Do not dispatch before the opening board is shown.

**Act II — Live phases (dispatch REAL agents).** Decompose the goal and dispatch only the councils the
task needs — Scouts (prior-art / methods / landscape), Labs (theory / methods / domain / statistics),
**Verification** (rigor / methodology / evidence / domain + referee), Execution (experiments / ablation /
iteration), Support (record / docs / figures / tidy), plus Pre-Award / Faculty / Governance when relevant.
For each agent, **spawn the real sub-agent** with the Task tool: `subagent_type` = `cambium-institute:<agent-name>`
(e.g. `cambium-institute:scout-landscape`, `cambium-institute:verify-rigor`), and `description` = its
**"Council · Role"** label so the native cards read consistently. Run independent agents in the same phase
**in parallel**. Maintain the live board with `tools/run_state.py` (no hand-edited JSON): at the start of a
phase run `python3 tools/run_state.py phase <N> --note "<what's happening>"`; after the agents write their
`agent_outputs/<name>.md`, run `python3 tools/run_state.py sync --phase <N>` to auto-lift each agent's
finding, then re-emit `python3 tools/run_trace.py --board "$ARGUMENTS"` (it auto-discovers
`agent_outputs/run_state.json`) and, in Cowork, regenerate `run_board.html` and push it with
`update_artifact` (same id) — so the Director watches ✓ done · ▶ now · ○ waiting advance live, with each
agent's one-line finding. Keep `agent_outputs/findings_ledger.csv` current.

**Act III — The gate (stop and wait).** At every gate, render `templates/GATE_SUMMARY.md` VERBATIM (the 7
sections, ≤ 1 page) and show the dashboard gate banner. End with the explicit **APPROVE / REVISE / REJECT**
prompt and WAIT. Record the answer in `governance/GATES.md`. Never submit, publish, or finalize without an
APPROVE.

**End-to-end (non-negotiable).** Once the Director chose the Cambium way, the WHOLE task stays Cambium —
including the BUILD/implementation after an approval gate. Dispatch the real Execution/Labs agents
(`research-engineer`, `exec-experiments`, `exec-iteration`, `lab-methods`, …) to do the work; do NOT quietly
build it inline yourself. If solo would genuinely be better (e.g. a trivial mechanical edit), **ask the
Director first** ("run the build Cambium or drop to solo for speed?") — never switch to solo silently.

**Act IV — Close-out (part of done).** After approval and the build, run the Support council automatically
(CHANGELOG + decision record, refreshed docs, verified numbers, stray-file check), then show the final
all-✓ board and a 3–5 line "what shipped" summary.

If the request is missing detail you need (which file, what the deliverable is, where to save it), ask one
short clarifying question first, then proceed.

**Shortcut — `/cambium run example`.** If the request is `run e