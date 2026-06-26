#!/usr/bin/env python3
"""Cambium auto-runner — turns the agent specs into running workers.

Within a phase, independent agents run CONCURRENTLY (each model call = one session) via a
thread pool; phases run in order; the run STOPS at every human gate. This is I/O-bound, so
concurrency (not CPU cores) is the lever; the real ceiling is your API rate limit + budget.

Modes:
  (default) dry-run : prints the exact execution plan — which agents run in parallel, the model
                      each uses (from the router), and where it stops for you. No API calls.
  --live            : actually calls the model per agent concurrently. Needs ANTHROPIC_API_KEY.
  --resume <phase>  : continue after you approved a gate.

Usage:
  python3 tools/cambium_run.py "<task / RFP path>"            # dry-run plan
  python3 tools/cambium_run.py "<task>" --live --max 5        # live, 5 concurrent sessions
"""
import os, sys, json, time, concurrent.futures as cf
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

def load_yaml(p):
    import yaml; return yaml.safe_load(open(p, encoding="utf-8"))

def router():
    import model_router as mr
    cfg, _ = mr.load_config(); prov, tiers = mr.active_tiers(cfg); cards = mr.load_cards()
    return prov, tiers, cards, mr

def agent_groups(phase):
    """Return ordered list of (label, [agents], concurrent?) for a phase."""
    out = []
    for key in ("parallel","then","consult","then_parallel","verify_parallel","review"):
        if key in phase:
            ags = phase[key]; conc = "parallel" in key
            out.append((key, ags, conc))
    return out

def agent_spec(name):
    import glob
    for p in glob.glob(os.path.join(ROOT,".claude","agents","*.md")):
        t = open(p, encoding="utf-8", errors="replace").read()
        if ("name: "+name) in t: return t
    return None

def call_model(model, system, user, key):
    """One model call = one session. Uses Anthropic Messages API via stdlib urllib."""
    import urllib.request, json as J
    body = J.dumps({"model": model, "max_tokens": 1200,
                    "system": system, "messages":[{"role":"user","content":user}]}).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=body,
            headers={"x-api-key": key, "anthropic-version":"2023-06-01", "content-type":"application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        d = J.loads(r.read()); return d["content"][0]["text"]

def main():
    args = sys.argv[1:]
    if not args:
        print('Usage: python3 tools/cambium_run.py "<task / RFP path>" [--live] [--max N]'); return 1
    task = args[0]
    live = "--live" in args
    maxc = int(args[args.index("--max")+1]) if "--max" in args else 5
    key  = os.environ.get("ANTHROPIC_API_KEY")
    plan = load_yaml(os.path.join(ROOT,"phases.yml"))
    prov, tiers, cards, mr = router()
    runlbl = time.strftime("%Y%m%d-%H%M%S")
    outdir = os.path.join(ROOT, "agent_outputs", "autorun-"+runlbl)

    print("="*64)
    print("CAMBIUM AUTO-RUNNER  |  task: %s" % task)
    print("mode: %s  |  provider: %s  |  max concurrent sessions: %d" %
          ("LIVE" if live else "DRY-RUN (plan only)", prov, maxc))
    if live and not key:
        print("\n[!] --live needs ANTHROPIC_API_KEY in the environment. Showing the plan instead.\n"); live=False
    if live: os.makedirs(outdir, exist_ok=True)
    print("="*64)

    def run_one(name):
        model = mr.resolve(name, cards, tiers)[1]
        if not live:
            return name, model, "(planned)"
        spec = agent_spec(name) or ("You are the %s agent for Cambium." % name)
        try:
            txt = call_model(model, spec, "TASK: %s\nDo your job per your spec. Be concise." % task, key)
            open(os.path.join(outdir, name+".md"), "w", encoding="utf-8").write(txt)
            return name, model, "done (%d chars)" % len(txt)
        except Exception as e:
            return name, model, "ERROR "+str(e)[:80]

    for ph in plan["phases"]:
        print("\n### PHASE: %s" % ph["id"])
        for label, ags, conc in agent_groups(ph):
            tag = "PARALLEL (%d sessions at once)" % min(len(ags),maxc) if conc and len(ags)>1 else "sequential"
            print("  %-14s %s" % (label+":", tag))
            if conc and len(ags)>1:
                with cf.ThreadPoolExecutor(max_workers=maxc) as ex:
                    for name, model, st in ex.map(run_one, ags):
                        print("      • %-26s -> %-26s %s" % (name, model, st))
            else:
                for name in ags:
                    nm, model, st = run_one(name)
                    print("      • %-26s -> %-26s %s" % (nm, model, st))
        if "gate" in ph:
            g = ph["gate"]
            print("  ╔═ GATE %s — %s  (approver: %s)" % (g["id"], g["decision"], g["approver"]))
            print("  ╚═ STOP. Record approval in governance/GATES.md, then: --resume %s" % ph["id"])
            print("     (human-in-the-loop: the run halts here by design)")
            if live:
                print("\n[auto-runner] paused at %s. Outputs so far in %s" % (g["id"], outdir)); return 0
    print("\n[auto-runner] plan complete." + ("" if live else "  Add --live (with ANTHROPIC_API_KEY) to execute."))
    return 0

if __name__ == "__main__":
    sys.exit(main())
