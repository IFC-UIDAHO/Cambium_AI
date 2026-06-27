---
name: cambium-mode
description: Smart default for HOW to run a task — Solo (plain, fast, no gates) or the Cambium way (Orchestrator + councils + a human approval gate). Trivial edits and quick lookups run Solo silently with NO question. For any SUBSTANTIAL task — evaluate, review, analyze, research, brainstorm, design a study, write a proposal/report/paper, build a budget, check or reproduce results, prepare a deck — ask the user which way BEFORE starting, then remember their choice for the rest of the session. Do NOT ask for casual chat, simple factual questions, or tiny one-step edits.
---

# Cambium mode — smart default

Cambium does not take over automatically. This skill decides, per task, whether to run **Solo** or
**the Cambium way**, using a smart default so the user is only asked when it actually matters.

## The decision rule (follow every time a new task arrives)

1. **Is a mode already set for this session?** If the user earlier said "always Cambium" / "stay solo,"
   or just answered the choice, **run that mode and do NOT ask again.** Slash commands `/cambium <task>`
   and `/solo <task>` also count as the answer — run that mode, no question.

2. **Is the task TRIVIAL?** A quick factual question, a one-line lookup, casual chat, or a tiny
   single-step edit → **just do it Solo, silently. Ask nothing.** This is the "smart" part: no friction
   on small things.

3. **Is the task SUBSTANTIAL?** Multiple steps or a real deliverable — *evaluate / review / assess,
   analyze, research a topic, brainstorm or rank ideas, design a study or experiment, write a
   proposal / report / paper / draft, build a budget, check or reproduce results, prepare a deck* →
   **ask the choice once, BEFORE starting**, then remember it for the session.

When a borderline case is genuinely unclear, ask briefly rather than guess.

## Asking the choice (only for substantial tasks)

Offer two options and wait (in Cowork, render as a quick pick; otherwise one short line):

- **Solo** — plain Claude handles it directly. Fast, conversational, no councils, no gate.
  Best for drafts, quick looks, low-stakes work.
- **Cambium way** — run the institute. The **Orchestrator** dispatches only the councils the task
  needs (Scouts for prior work, Labs to build, **Verification** to audit, Execution to run experiments,
  **Support** to record + check + tidy at close-out), and **stops at a one-page gate card**
  (*decision · options · risks · recommendation · APPROVE / REVISE / REJECT*) before anything is
  finalized. Best for decisions, evaluations, anything that must be trustworthy or submitted.

## Honoring the answer
- **Solo** → do the task directly. No councils, no gate.
- **Cambium way** → hand to the Orchestrator and present the run as the four acts in **PRESENTATION.md**:
  open with the live run board (`tools/run_trace.py --board`, plus the `--html` dashboard in Cowork);
  **dispatch the real named sub-agents** (`subagent_type: cambium-institute:<name>`, `description:
  "<Council> · Role"`) so the Director sees who is working; re-emit the board each phase; keep the findings
  ledger; present the gate card for APPROVE / REVISE / REJECT; run the Support close-out. Never finalize,
  submit, or publish without that approval.
- **End-to-end.** Cambium runs the WHOLE task — including the BUILD/implementation *after* an approval gate
  — by dispatching real agents (Execution/Labs). Do NOT silently drop to solo for the post-gate work. If
  solo would genuinely be better for a trivial step, **ask** the Director first; otherwise finish Cambium.
- **Remember it.** Once chosen (or set with "always Cambium" / "stay solo"), skip the question for the
  rest of the session and run that mode by default until the user changes it.

## The honest guarantee
The only 100%-deterministic control is the user typing **`/solo`** or **`/cambium`**. This skill makes
the *default* behave well — silent Solo on trivial work, a one-time ask on substantial work — but if it
ever runs something without asking and the user wanted the other mode, they can just say
**"run this the Cambium way"** or **"/solo"** and it switches immediately. The user is always the Director.
