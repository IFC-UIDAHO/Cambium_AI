# EVALS.md — agent reliability floor (v3.1)
*Cambium should measure its own agents, not just assert quality. `validate.py` enforces evidence;
this adds a small reliability eval so the institute can gate on a quality FLOOR over time.
Approach (Agent-as-a-Judge + trajectory scoring) per current agentic-eval practice
(e.g., Holistic Agent Leaderboard, arXiv 2510.11977, 2026; GAIA / SWE-bench / Tau²-bench).*

## What we measure
- **Faithfulness** — did the agent's claims match its cited evidence? (judge)
- **Tier honesty** — were claim tiers accurate (no "Code-verified" without a run)?
- **Citation integrity** — fraction of references that resolve (target: 100%).
- **Gate discipline** — did the run stop at every required human gate?
- **Cost/latency** — tokens + wall-clock per phase (budget awareness).

## How (lightweight)
A held-out set of seeded tasks per council; an Agent-as-a-Judge pass scores each trajectory
against the rubric above; results logged to `agent_outputs/eval_scores.csv`. A council below its
floor is flagged in the run report. (Harness: `tools/agent_eval.py`, to be wired in v3.2.)

## Floors (initial, tune with data)
Citation integrity = 1.0 · Tier honesty ≥ 0.95 · Gate discipline = 1.0 · Faithfulness ≥ 0.9.
