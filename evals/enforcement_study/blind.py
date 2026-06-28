#!/usr/bin/env python3
"""blind.py — build the arm-BLIND rater packet for the v1 human panel (PROTOCOL §5.2, V1_DESIGN §Judging).

The human panel must never see which arm produced an output. This tool takes both arms' agent outputs
(runs/treatment/*.md, runs/baseline/*.md), assigns each a random blind_id, SHUFFLES the combined set,
and writes two things kept strictly apart:

  1. rater_packet.json      — what raters see: [{blind_id, prompt, claim_list, output}] in shuffled order.
                              Contains NO arm label and NO task_id-to-arm hint.
  2. blind_manifest.json    — the SEALED key: {blind_id -> {arm, task_id}}. Held by the study lead only;
                              fed to analyze.py AFTER both raters submit (no peeking / no optional stopping).

Determinism: the shuffle is seeded (--seed, default 1729) so the packet is reproducible and the seed is
pre-registered. The claim_list shown to raters is the union of the task's checkable claims (the seeded
false claims + the resolvable/unresolvable citations) with the TRUTH LABELS REMOVED — the rater decides
true/false/unsupported themselves.

Usage:
    python3 evals/enforcement_study/blind.py                       # both arms -> packet + manifest
    python3 evals/enforcement_study/blind.py --seed 1729 --out-dir panel/
"""
from __future__ import annotations
import argparse, glob, hashlib, json, os, random, sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_TASKS = os.path.join(_HERE, "tasks")
_RUNS = os.path.join(_HERE, "runs")

def _claim_list(task: dict) -> list[dict]:
    """The checkable items shown to the rater — TRUTH LABELS STRIPPED. Rater assigns the label."""
    gt = task["ground_truth"]
    items = []
    # every seeded false claim is a checkable statement (rater decides true/false/unsupported)
    for i, c in enumerate(gt.get("false_claims_to_catch", [])):
        items.append({"claim_id": f"C{i+1}", "statement": c, "kind": "factual_claim"})
    # citations the agent might lean on (rater decides whether the agent used them as support unflagged)
    base = len(items)
    for j, c in enumerate(gt.get("citations_that_do_not_resolve", [])):
        items.append({"claim_id": f"C{base+j+1}", "statement": f"Citation used as support: {c}", "kind": "citation"})
    return items

def _blind_id(arm: str, task_id: str, salt: str) -> str:
    h = hashlib.sha256(f"{salt}|{arm}|{task_id}".encode()).hexdigest()[:10]
    return "B" + h

def build(seed: int, out_dir: str, salt: str):
    os.makedirs(out_dir, exist_ok=True)
    tasks = {json.load(open(p, encoding="utf-8"))["task_id"]: json.load(open(p, encoding="utf-8"))
             for p in glob.glob(os.path.join(_TASKS, "T*.json"))}
    rows, missing = [], []
    for arm in ("TREATMENT", "BASELINE"):
        rundir = os.path.join(_RUNS, arm.lower())
        for tid, task in tasks.items():
            op = os.path.join(rundir, tid + ".md")
            if not os.path.exists(op):
                missing.append((arm, tid)); continue
            output = open(op, encoding="utf-8", errors="replace").read()
            bid = _blind_id(arm, tid, salt)
            rows.append({"blind_id": bid, "arm": arm, "task_id": tid, "category": task["category"],
                         "prompt": task["prompt"], "claim_list": _claim_list(task), "output": output})
    if not rows:
        print(f"[blind] no agent outputs found under {_RUNS}/{{treatment,baseline}}/.\n"
              f"        run_arm.py must run first (needs your `claude` login or API key). nothing written.")
        return 1
    rng = random.Random(seed)
    rng.shuffle(rows)
    # packet: raters see no arm/task — only blind_id + content
    packet = [{"blind_id": r["blind_id"], "category": r["category"], "prompt": r["prompt"],
               "claim_list": r["claim_list"], "output": r["output"]} for r in rows]
    manifest = {r["blind_id"]: {"arm": r["arm"], "task_id": r["task_id"], "category": r["category"]} for r in rows}
    pkt_path = os.path.join(out_dir, "rater_packet.json")
    man_path = os.path.join(out_dir, "blind_manifest.json")
    json.dump({"_blind": "Raters see this. No arm labels. Shuffled, seed=%d." % seed,
               "n_items": len(packet), "items": packet}, open(pkt_path, "w", encoding="utf-8"), indent=1)
    json.dump({"_sealed": "STUDY LEAD ONLY. Do not open before both raters submit (no optional stopping).",
               "seed": seed, "salt_sha256": hashlib.sha256(salt.encode()).hexdigest()[:16],
               "key": manifest}, open(man_path, "w", encoding="utf-8"), indent=1)
    n_t = sum(1 for r in rows if r["arm"] == "TREATMENT"); n_b = len(rows) - n_t
    print(f"[blind] {len(rows)} items ({n_t} treatment + {n_b} baseline), shuffled seed={seed}")
    print(f"[blind]   rater packet  -> {os.path.relpath(pkt_path, _HERE)}  (give to raters)")
    print(f"[blind]   sealed key    -> {os.path.relpath(man_path, _HERE)}  (study lead only)")
    if missing:
        print(f"[blind]   note: {len(missing)} (arm,task) outputs missing — packet covers only completed runs.")
    return 0

def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=1729, help="pre-registered shuffle seed")
    ap.add_argument("--salt", default="cambium-v1-blind", help="blind-id salt (keep stable within a study)")
    ap.add_argument("--out-dir", default=os.path.join(_HERE, "panel"))
    a = ap.parse_args(argv)
    return build(a.seed, a.out_dir, a.salt)

if __name__ == "__main__":
    sys.exit(main())
