---
description: Pause a Cambium run — write a durable HANDOFF.md snapshot so you can clear/restart the context window without losing the run.
---

Pause the current Cambium run for a clean context handoff.

Run `python3 tools/handoff.py pause --reason "$ARGUMENTS"` (add `--context <pct>` if you know the
context-window usage). This writes `agent_outputs/HANDOFF.md` from the run's own memory
(`run_state.json` + findings ledger + synthesis): where we are, the open gate, findings so far, and the
exact next action — with the machine-readable run state embedded for a lossless resume.

Then tell the Director: the run is safe to pause; open a **fresh context window** and run **`/cambium:resume`**
to pick up exactly where we left off. Nothing is finalized; any open gate still needs their APPROVE.

(Single-writer rule: only the Orchestrator writes run state — so pause/resume stay consistent.)
