# AUTORUN.md — the Cambium engine (turning specs into running workers)
*`tools/cambium_run.py` + `phases.yml`. Each agent spec becomes a model call (a "session").
Within a phase, independent agents run CONCURRENTLY; phases run in order; every gate stops for a human.*

## Try the plan (no key, no cost)
```
python3 tools/cambium_run.py "USDA-AFRI forest carbon RFP"
```
Prints which agents run in parallel, the model each uses, and where it halts for your approval.

## Two ways to actually execute
1. **Conductor-driven (inside a Claude session, e.g. Cowork):** the orchestrator dispatches agents
   as real parallel sub-sessions. No API key needed; this is how Project 005 ran. Best for interactive,
   gated work.
2. **Script-driven (`--live`, headless/automated):** the engine calls the model itself, concurrently.
   ```
   export ANTHROPIC_API_KEY=<your-key>           # your key
   python3 tools/cambium_run.py "<task>" --live --max 5   # 5 concurrent sessions
   ```
   Writes each agent's output to agent_outputs/autorun-<ts>/, then pauses at the first gate.

## The real limits (honest)
- **It is I/O-bound** — speed = concurrent requests, not CPU cores. `--max N` sets simultaneous sessions.
- **Ceiling = your API rate limit + budget.** 46 agents × calls costs tokens; Opus on the critical path,
  Sonnet/Haiku elsewhere (the router already optimizes this).
- **Gates still stop it** — by design. Fully autonomous end-to-end would mean removing human approval,
  which Cambium intentionally does not do.
- `--resume <phase>` continues after you record the gate approval in governance/GATES.md.

## Durable memory across context windows (pause / resume)
Long runs fill the context window. Instead of lossy auto-compaction, PAUSE and RESUME with full memory:
```
python3 tools/handoff.py pause --reason "context high"   # writes agent_outputs/HANDOFF.md
# …open a FRESH context window…
python3 tools/handoff.py resume                          # restores run_state.json, briefs you, archives the handoff
```
Slash commands wrap these: `/cambium:pause` and `/cambium:resume`. The handoff is built from the run's own
memory (run_state.json + findings_ledger.csv + synthesis) and embeds the machine-readable state for a
lossless restore. **Single-writer rule:** only the Orchestrator writes `run_state.json`.

## See your context heat (status line)
Add the Cambium status line so you know when to pause *before* compaction:
```
/statusline      →  command:  bash tools/statusline.sh
```
It shows `⬢ Cambium · <model> · <dir> · ctx ~NN% [▓▓▓░░]` and flips to "⚠ run /cambium:pause" at ~85%
(override with CAMBIUM_CTX_BUDGET / CAMBIUM_CTX_WARN). The % is an estimate (transcript size), a heat gauge.

## Guarded autonomous loop (the safe version of "run until the goal")
`phases.yml → autoloop` lets a listed phase iterate its internal work (plan → apply → verify) until its
acceptance tests pass, then **surface its gate and stop**. It is fail-closed: `max_iterations` and
`budget_usd` are hard caps, an integrity check runs each iteration (a P0 stops it), and the loop may **arm**
a gate but **never clear** one — every gate is still a human APPROVE. This keeps throughput high inside a
phase without ever removing the human from a gate.
