---
description: Resume a paused Cambium run — restore run state from HANDOFF.md, get briefed, and continue exactly where you left off.
---

Resume a paused Cambium run in this (ideally fresh) context window.

Run `python3 tools/handoff.py resume`. It restores `agent_outputs/run_state.json` from the latest
`agent_outputs/HANDOFF.md`, prints the briefing (where we are · open gate · findings · next action), and
archives the consumed handoff to `archive/handoffs/`.

Then continue the Cambium way (docs/concepts/PRESENTATION.md): re-emit the live board
`python3 tools/run_trace.py --board "<request>"` (it auto-discovers the restored run_state), and pick up
the next action from the briefing. If a gate was open, re-present it and WAIT for the Director — resuming
never skips an approval.
