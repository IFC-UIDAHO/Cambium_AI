#!/usr/bin/env python3
"""run_pilot.py — one command to run the whole enforcement A/B pilot end to end.

  run_arm (TREATMENT + BASELINE)  ->  judge_stage1 (both)  ->  run_study (aggregate)  ->  analyze

LIVE run — EASY (uses your existing Claude Code login; no API key):
    python3 evals/enforcement_study/run_pilot.py
LIVE run — API key alternative:
    ANTHROPIC_API_KEY=sk-... python3 evals/enforcement_study/run_pilot.py --backend api

Dry run (no key, placeholder outputs — proves the wiring):
    python3 evals/enforcement_study/run_pilot.py --dry-run

Outputs: runs/<arm>/*.md, <arm>_verdicts.json, results_pilot.csv, RESULTS.md
"""
from __future__ import annotations
import argparse, os, subprocess, sys
_HERE = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable

def step(title, args):
    print(f"\n=== {title} ===")
    r = subprocess.run([PY] + args, cwd=_HERE)
    if r.returncode != 0:
        print(f"[run_pilot] step failed: {title}"); sys.exit(r.returncode)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--model", default="opus")
    ap.add_argument("--backend", choices=["claude-code","api"], default="claude-code")
    ap.add_argument("--rescore", action="store_true",
                    help="skip the agent calls; re-judge the EXISTING runs/ outputs (no API cost)")
    a = ap.parse_args()
    if not a.rescore:
        run_args = ["run_arm.py", "--arm", "both", "--backend", a.backend, "--model", a.model] + (["--dry-run"] if a.dry_run else [])
        step("1/4  Run both arms (agent-under-test)", run_args)
    else:
        print("\n=== 1/4  Run both arms — SKIPPED (--rescore: using existing runs/ outputs) ===")
    step("2/4  Stage-1 blind judge", ["judge_stage1.py", "--arm", "both"])
    step("3/4  Aggregate metrics", ["run_study.py",
         "--treatment", os.path.join(_HERE, "treatment_verdicts.json"),
         "--baseline",  os.path.join(_HERE, "baseline_verdicts.json"),
         "--tasks", os.path.join(_HERE, "tasks"),
         "--out", os.path.join(_HERE, "results_pilot.csv")])
    step("4/4  Effect sizes + 95% CIs", ["analyze.py",
         "--results", os.path.join(_HERE, "results_pilot.csv"),
         "--out", os.path.join(_HERE, "RESULTS.md")])
    print("\n[run_pilot] complete -> evals/enforcement_study/RESULTS.md")
    if a.dry_run:
        print("[run_pilot] (dry-run: outputs are placeholders; numbers are not a finding.)")

if __name__ == "__main__":
    main()
