#!/usr/bin/env python3
"""Cambium model router (v3.2).

Maps each agent to a concrete model via:
  agent's own tier (opus/sonnet/haiku/inherit, from agent_cards.json)
    -> router tier name (strong/mid/light)
      -> concrete model string of the ACTIVE provider (from config.yml).

Claude works out of the box. To use other/free models later: in config.yml fill a provider's
tiers, set its api_key_env (and base_url for openai_compatible), flip enabled:true, and set
active_provider. Nothing else changes.

Usage:
  python3 tools/model_router.py            # print the full agent->model table
  python3 tools/model_router.py <agent>    # resolve one agent (e.g. lab-theory)
"""
import os, sys, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# agent model-tier (opus/sonnet/haiku/inherit) -> router tier (strong/mid/light)
TIER_OF = {"opus": "strong", "inherit": "strong", "sonnet": "mid", "haiku": "light"}

def load_config():
    for name in ("config.yml", "config.example.yml"):
        p = os.path.join(ROOT, name)
        if os.path.exists(p):
            try:
                import yaml
                return yaml.safe_load(open(p, encoding="utf-8")), name
            except Exception:
                break
    # stdlib fallback: built-in Claude defaults
    return {"model_router": {"active_provider": "anthropic", "providers": {"anthropic": {"enabled": True,
            "tiers": {"strong": "claude-opus-4-8", "mid": "claude-sonnet-4-6",
                      "light": "claude-haiku-4-5-20251001"}}}}}, "(built-in defaults)"

def active_tiers(cfg):
    mr = cfg.get("model_router", {})
    prov = mr.get("active_provider", "anthropic")
    p = mr.get("providers", {}).get(prov, {})
    if not p.get("enabled", False):
        raise SystemExit("[router] active_provider '%s' is not enabled in config." % prov)
    tiers = p.get("tiers", {})
    missing = [t for t in ("strong", "mid", "light") if not tiers.get(t)]
    if missing:
        raise SystemExit("[router] provider '%s' is missing models for tiers: %s" % (prov, missing))
    return prov, tiers

def load_cards():
    p = os.path.join(ROOT, "agent_cards.json")
    if not os.path.exists(p):
        raise SystemExit("[router] agent_cards.json not found - run tools/gen_agent_cards.py first.")
    return {a["name"]: a.get("model", "inherit") for a in json.load(open(p))["agents"]}

def resolve(name, cards, tiers):
    agent_tier = cards.get(name, "inherit")
    rt = TIER_OF.get(agent_tier, "mid")
    return rt, tiers[rt]

def main():
    cfg, src = load_config()
    prov, tiers = active_tiers(cfg)
    cards = load_cards()
    if len(sys.argv) > 1:
        name = sys.argv[1]
        rt, model = resolve(name, cards, tiers)
        print("[router] %s -> tier=%s -> %s (provider=%s)" % (name, rt, model, prov))
        return 0
    print("[router] config=%s | provider=%s | %d agents" % (src, prov, len(cards)))
    counts = {}
    for name in sorted(cards):
        rt, model = resolve(name, cards, tiers)
        counts[rt] = counts.get(rt, 0) + 1
    for rt in ("strong", "mid", "light"):
        print("  %-7s (%2d agents) -> %s" % (rt, counts.get(rt, 0), tiers[rt]))
    return 0

if __name__ == "__main__":
    sys.exit(main())
