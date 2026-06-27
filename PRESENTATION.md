# The Cambium Way — Presentation Contract

> This is the single source of truth for **how a Cambium run looks and feels**. When the Director
> chooses *the Cambium way* (or types `/cambium`), the Orchestrator MUST present the run as the four
> acts below. The point is that every Cambium run is unmistakable, legible, and the same every time —
> the Director always sees *which named agents are working, on what, and where the gates are.*
>
> Solo runs ignore this file. This contract is only for the Cambium way.

The anti-goal is the generic experience: opaque "Used 6 tools / Created 3 files" lines with no named
agents, no visible plan, no live progress. That is what this contract exists to replace.

---

## The brand (use everywhere)

- Mark: **⬢ CAMBIUM INSTITUTE** · tagline *"the Cambium way"*.
- Palette: deep forest `#07231A`, panels `#0E3326`, hairline `#1F4D3B`, **Cambium lime `#B7F36A`** (primary
  accent / "now"), emerald `#16C079` (flow / done), ink `#F4F7F2`, muted `#8AA197`.
- Status glyphs, used identically in every view: **✓ done · ▶ now · ○ waiting · ⛩ human gate · ▸ NOW line**.
- Council vocabulary (always title-case, always "Council · Role"): Orchestration, Pre-Award,
  Partnerships, Faculty, Scouts, Labs, Verification, Execution, Reporting, Support, Governance.

All boards are produced by `tools/run_trace.py` so the vocabulary never drifts. Never hand-draw a board.

---

## Act I — OPENING (before any work)

Transparency before action. The moment the Cambium way starts, show the plan so the Director sees the
whole institute that is about to mobilize.

0. **Reset run state (first, always):** `python3 tools/run_state.py reset --note "<request>"` — clears any prior run's phase/findings/gate and stamps a fresh `started_at`, so `sync` ignores stale `agent_outputs/*.md` left by earlier runs. Skipping this is what leaks a previous run's findings onto the new board.
1. **Text board (always):** `python3 tools/run_trace.py --board "<request>"` — branded header +
   council-grouped roster + the gate rail. This renders in ANY client and is the non-negotiable baseline.
2. **In Cowork / visual clients (also):**
   - Live dashboard: `python3 tools/run_trace.py --html --out <project>/run_board.html "<request>"`,
     then publish it as an artifact (`create_artifact`) titled *"Cambium run board"*. This is the
     persistent, re-openable view.
   - Optional inline picture: `python3 tools/run_trace.py --svg "<request>"`.
3. One plain sentence under it: *"Here's the institute I'll run for this — N specialists across M
   councils, with K gates where you decide. Starting now."*

Never start dispatching before the opening board is shown.

---

## Act II — LIVE PHASES (dispatch real agents, narrate by phase)

This is the heart of the upgrade: **dispatch the real, named sub-agents** — do not do their work inline.

**END-TO-END RULE (non-negotiable).** If the Director chose the Cambium way, the *entire* task runs the
Cambium way — including the BUILD/implementation phases that come **after** an approval gate. The
Orchestrator dispatches the real Execution/Labs agents (`research-engineer`, `exec-experiments`,
`exec-iteration`, `lab-methods`, …) to do the work; it does **not** quietly do the build itself inline.
Doing the post-gate work solo is a contract violation. The only allowed alternative is to **ask the
Director first** — e.g. "the build is mechanical; run it Cambium (dispatch Execution) or drop to solo for
speed?" — and honor their answer. Never switch to solo silently.

**Dispatch rule (mandatory).** For each agent in a phase, spawn it with the Task tool:
- `subagent_type` = `cambium-institute:<agent-name>` (e.g. `cambium-institute:scout-landscape`,
  `cambium-institute:verify-rigor`, `cambium-institute:lab-statistics`).
- `description` = the **"Council · Role"** label (e.g. `Scouts · Landscape`). Cowork's native
  "Running agent" cards show this verbatim, so the live UI speaks the same vocabulary as the board.
- Agents in the same phase that are independent are dispatched **in parallel** (one message, multiple
  Task calls).

**Per-phase narration (mandatory).** At the start of every phase, re-emit the LIVE board so the Director
sees ✓/▶/○ advance:
- Text: `python3 tools/run_trace.py --board "<request>"`
- Cowork dashboard: regenerate `run_board.html` and `update_artifact` (same id).

The board's live detail comes from **`agent_outputs/run_state.json`**, which `run_trace.py`
**auto-discovers** — so you do NOT pass `--state` and you do NOT hand-edit JSON. Maintain it with
`tools/run_state.py`, which lifts each agent's headline finding from its own output file automatically:
```bash
python3 tools/run_state.py phase 2 --note "Scouts surveying the landscape"
# … dispatch the real agents; each writes agent_outputs/<name>.md …
python3 tools/run_state.py sync --phase 2          # auto-fills findings from every agent's "## Decision"
python3 tools/run_state.py lead "scout-landscape:92,scout-methods:88"   # optional leaderboard
python3 tools/run_state.py gate G2 "which idea advances?" --rec "A"     # arm the gate banner
python3 tools/run_trace.py --board "<request>"     # reads run_state.json; no --state needed
```
`run_state.json` is the live, per-run state (git-ignored). Schema:
`{ "phase": N, "note": "…", "findings": {"<agent>": "one line"},
   "leaderboard": [["<agent>", score]], "gate": {"id","kind","decision","recommendation"} }`.
Findings keys are agent names; the board prints them next to each agent. (You may still pass an explicit
`--state path.json` to override auto-discovery.)

Between phases, keep the findings ledger (`agent_outputs/findings_ledger.csv`) and the master synthesis
current, exactly as INSTITUTE.md / the Orchestrator spec require. The board is the *view*; the ledger is
the *record*.

---

## Act III — THE GATE (stop, show one page, wait)

At every gate, render the gate card and STOP. Three synchronized surfaces:
- **The one-pager:** fill `templates/GATE_SUMMARY.md` VERBATIM — the 7 sections **plus the required Section 8 (Director contribution)**, in order,
  ≤ 1 page. Never improvise the structure.
- **The inline gate card (default):** render `templates/INLINE_GATE_CARD.html` with `mcp__visualize__show_widget`
  (fill `{GATE_ID}` / `{DECISION}`). Its APPROVE / REVISE / REJECT buttons actually post the decision to chat
  (`sendPrompt`) — a sidebar artifact canNOT, so the inline card is the canonical clickable gate.
- **The sidebar run board (Cowork):** the dashboard shows the active-gate banner; its buttons only copy the
  decision text (a sidebar artifact has no send-to-chat hook).

**ENFORCE BEFORE RECORDING (mandatory).** Before recording any DECISION-gate APPROVE in `governance/GATES.md`,
the Orchestrator MUST run the gate interlock — and it does not record an APPROVE if the interlock blocks:
```
python3 tools/gate.py <GATE_ID> --require-contribution --contribution <director.json> [--ai-summary <card.txt>] \
        [--required-approver "<named approver from templates/MULTI_PI_ROLES.yml>" --approver "<who is approving>"]
```
This makes the Learning Gate (a real Director contribution) and — for multi-institution projects — the
named-approver / separation-of-duties check fire on **every** decision gate, not by convention. A bare APPROVE,
an incomplete contribution, or the wrong approver is blocked.

End with the explicit **APPROVE / REVISE / REJECT** prompt and WAIT. Record the answer in
`governance/GATES.md` only after `gate.py` opens the gate. Never submit, publish, or finalize without an APPROVE.

---

## Act IV — CLOSE-OUT (every time something ships)

After a change is approved, **dispatch the real Support council** (do NOT do close-out inline — that is
what lets the support staff "just sit" and the docs drift): Record-Keeper appends the CHANGELOG + ADR +
GATES; **Outreach refreshes the forward docs — README counts + roadmap paragraph, ROADMAP.md (+ bump
`Last updated:`), USE_CAMBIUM / FAQ / COMPARISON if user-facing**; Integrity-Officer updates POSITIONING /
PHILOSOPHY if any claim moved and runs tests/doctor; Janitor checks for stray files. Follow
`templates/CLOSEOUT_CHECKLIST.md`. **Then `python3 tools/closeout.py` MUST exit 0** — it fails close-out if a
forward doc drifted behind the latest CHANGELOG. Close-out is not "done" until it passes.

Then show the **final board** with every phase ✓ and a 3–5 line "what shipped" summary
(`--board --phase <last>`), and in Cowork a final dashboard update. Housekeeping is not optional and not
the Director's job to remember.

---

## The contract in one screen

| Act | What the Director see