# EFFICIENCY.md — cost & speed guardrails (v3.2, P2)
*Best result per token. These are operating rules; they never override a human gate or the evidence contract.*

## Deep-research two-mode loop (Scouts)
- **`quick scan`** — fast triage: a few targeted searches, surface candidates + a confidence flag. Use for go/no-go and early framing.
- **`deep research`** — exhaustive: fan-out searches, fetch primary sources, adversarially verify each claim, cite with dates. Use before G2/G3 and any external claim.
Scouts default to quick scan and ESCALATE to deep research when the decision is high-stakes or contested.

## Prompt-caching guardrails
- Cache STABLE context (charter, contract, agent specs, resolved literature) to cut cost/latency.
- **Never cache volatile facts** (policies, prices, leaders, "current" anything) — those are re-fetched every run (they change; see knowledge-cutoff discipline).
- Invalidate the cache on any repo change to a cached file; record a cache key in provenance.

## Per-vendor cost telemetry
- Log per phase: model/vendor, input/output tokens, wall-clock, est. cost → `agent_outputs/cost_log.csv (now captured live by tools/cambium_run.py: per-agent wall-clock + tokens + est_usd)`.
- Surface a cost line in each run report and in `provenance.json` (`model` already recorded; add `tokens`,`cost` when available).
- Use telemetry to tune the MODEL_ROUTER (move cheap work to cheaper tiers; keep the critical path on the strongest model).

## Budget rule (recap)
Self-consistency by default; adversarial debate only for contested/high-stakes claims (see DEVELOPMENT_PLAYBOOK.md).
