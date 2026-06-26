# MODEL_ROUTER.md — which AI model runs each job (v3.2, WIRED)
*Claude works out of the box today; other/free models plug in later with zero code changes.*

## How it works
Each agent already declares a tier in its spec (opus / sonnet / haiku / inherit). The router maps:
`agent tier -> router tier (strong/mid/light) -> the active provider's concrete model` (from `config.yml`).
- **strong** = critical path (theory, statistics, audit boards, referee, conduct, final writing)
- **mid** = breadth (scouts, labs, execution, pre-award, reporting, support)
- **light** = bulk (cleanup, formatting, digests)

## Right now (verified)
Active provider = **anthropic**. Tested mapping of all 45 agents:
`strong (12) -> claude-opus-4-8 · mid (31) -> claude-sonnet-4-6 · light (2) -> claude-haiku-4-5-20251001`.

## Commands
```
python3 tools/model_router.py            # full agent -> model table
python3 tools/model_router.py lab-theory # resolve one agent
```

## Adding other / free models later (no code change)
In `config.yml` (copy from config.example.yml):
1. Fill a provider's `tiers:` with model names (e.g. `google` or `openai_compatible`).
2. Set its `api_key_env:` (and `base_url:` for an OpenAI-style/free endpoint).
3. Set `enabled: true` and point `active_provider:` at it (or mix — keep Claude on `strong`,
   a cheaper/free model on `mid`/`light`).
The router re-resolves automatically. Provenance records which model produced each output.
