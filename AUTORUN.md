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
