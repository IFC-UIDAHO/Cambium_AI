#!/usr/bin/env python3
"""pace_check — enforce "pace as a feature" (POSITIONING #8, AI_POLICY §8) as a real control.

Cambium's principle is that research years are where a scientist is made: consecutive *decision* gates
must not be rammed through in minutes. Until now that was philosophy, not tooling. This makes it an
enforced, deterministic check.

It reads the minted gate tokens (governance/gate_tokens/*.json — each carries gate, approver, ts) and
verifies that no two DISTINCT decision gates were approved closer together than the minimum deliberation
interval. A run that approves G3 four minutes after G2 is blocked; the human must let real time pass.

  python3 tools/pace_check.py [--min-minutes N] [--tokens-dir DIR] [--strict]
  python3 tools/pace_check.py gate --gate G3 --at <epoch> [--min-minutes N]   # mint-time pre-check

Policy default: 30 minutes between consecutive decision gates (governance/PACE.md; override --min-minutes
or env CAMBIUM_MIN_GATE_MINUTES). Exit: 0 ok . 1 violation (with --strict, or always in `gate` mode).
Honest ceiling: it binds gates that mint tokens; a step that never mints is not paced. It is a real time
control, not a guarantee of *thought* — that is the Learning Gate's job. The two together are the point.
"""
import argparse, glob, json, os, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOKDIR = os.path.join(ROOT, "governance", "gate_tokens")
EXEMPT = {"G0", "G4", "G5"}                 # housekeeping gates may fire fast
TEST_PREFIXES = ("G-test", "G-demo")        # local scratch (gate_tokens/ is gitignored), never real gates

def _is_real(g):
    return g not in EXEMPT and not any(g.startswith(p) for p in TEST_PREFIXES)

def _default_min():
    try: return float(os.environ.get("CAMBIUM_MIN_GATE_MINUTES", "30"))
    except ValueError: return 30.0

def _load_tokens(tokens_dir):
    toks = []
    for p in sorted(glob.glob(os.path.join(tokens_dir, "*.json"))):
        try:
            d = json.load(open(p, encoding="utf-8"))
            toks.append((str(d.get("gate", os.path.basename(p)[:-5])), float(d.get("ts", 0))))
        except Exception:
            continue
    return toks

def violations(tokens, min_minutes):
    """Return list of (gate_a, gate_b, gap_minutes) for distinct decision gates closer than min."""
    paced = [(g, ts) for g, ts in tokens if _is_real(g) and ts > 0]
    paced.sort(key=lambda x: x[1])
    out = []
    for (ga, ta), (gb, tb) in zip(paced, paced[1:]):
        if ga == gb:                        # same gate re-minted (revision) — not a pace violation
            continue
        gap = (tb - ta) / 60.0
        if gap < min_minutes:
            out.append((ga, gb, gap))
    return out

def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-minutes", type=float, default=None)
    ap.add_argument("--tokens-dir", default=TOKDIR)
    ap.add_argument("--strict", action="store_true")
    sub = ap.add_subparsers(dest="cmd")
    pg = sub.add_parser("gate"); pg.add_argument("--gate", required=True)
    pg.add_argument("--at", type=float, default=None)
    a = ap.parse_args(argv)
    mn = a.min_minutes if a.min_minutes is not None else _default_min()
    toks = _load_tokens(a.tokens_dir)

    if a.cmd == "gate":
        at = a.at if a.at is not None else time.time()
        if a.gate in EXEMPT:
            print("[pace] %s is exempt (housekeeping); no interval enforced." % a.gate); return 0
        prior = [(g, ts) for g, ts in toks if _is_real(g) and g != a.gate and ts > 0]
        if prior:
            g0, t0 = max(prior, key=lambda x: x[1])
            gap = (at - t0) / 60.0
            if gap < mn:
                print("[pace] BLOCKED GATE %s — only %.1f min since %s; minimum deliberation interval is "
                      "%.0f min. Let real time pass before deciding." % (a.gate, gap, g0, mn))
                return 1
        print("[pace] OK %s clears the deliberation interval (%.0f min)." % (a.gate, mn)); return 0

    vs = violations(toks, mn)
    if not vs:
        print("[pace] OK: all consecutive decision gates >= %.0f min apart (%d token(s))." % (mn, len(toks))); return 0
    print("[pace] %s: gates approved faster than the %.0f-min interval:" % ("BLOCKED" if a.strict else "WARNING", mn))
    for ga, gb, gap in vs:
        print("   %s -> %s: %.1f min apart" % (ga, gb, gap))
    return 1 if a.strict else 0

if __name__ == "__main__":
    sys.exit(main())
