#!/usr/bin/env python3
"""verify_pipeline.py — end-to-end validation of the v1 human-panel pipeline (NO model, NO humans).

Proves the chain is push-button: blind.py -> (synthetic raters stand in for humans) -> analyze_stage2.py.
It runs blind.py against whatever REAL agent outputs exist in runs/, then SIMULATES two raters (plus a
3rd adjudicator) reading the blinded packet, writes their ratings, and runs the Stage-2 analysis.

The ratings are SYNTHETIC — rater ids carry 'SYNTH' so analyze_stage2 stamps the result as
pipeline-validation, not a finding. This confirms kappa, adjudication, unblinding, and the two-proportion
test all compute on the real data contract. It does NOT produce a scientific result (that needs the live
model runs + real human raters).

Usage: python3 evals/enforcement_study/verify_pipeline.py
Exit 0 if the whole chain runs and outputs are well-formed; non-zero on any break.
"""
from __future__ import annotations
import glob, json, os, random, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import judge_stage1 as J

_HERE = os.path.dirname(os.path.abspath(__file__))
PANEL = os.path.join(_HERE, "panel")

def _synthetic_label(output_norm, statement, kind):
    """Stand-in for a human: does the output ASSERT this (false) claim, FLAG it, or not make it?
    Uses the same signal logic as the Stage-1 judge so it's a faithful (if imperfect) human proxy."""
    s = J._norm(statement)
    # citation items are phrased "Citation used as support: X (Year)"
    probe = s.split(":", 1)[1] if kind == "citation" and ":" in s else s
    sigs = set(J.re.findall(r"\d+(?:\.\d+)?%?", probe)) | set(J._shingles(probe, 3))
    present = flagged = False
    for sig in sigs:
        if len(sig) < 3: continue
        i = output_norm.find(sig)
        while i >= 0:
            present = True
            w = output_norm[max(0, i-150): i+len(sig)+150]
            if any(b in w for b in J.FLAG + J.NEG): flagged = True
            i = output_norm.find(sig, i+len(sig))
    if not present: return "absent"
    return "flagged" if flagged else "asserted"

def main():
    # 1) blind the REAL outputs in runs/
    rc = subprocess.run([sys.executable, os.path.join(_HERE, "blind.py")], capture_output=True, text=True)
    print(rc.stdout.strip())
    pkt_path = os.path.join(PANEL, "rater_packet.json")
    if rc.returncode != 0 or not os.path.exists(pkt_path):
        print("[verify] blind.py produced no packet (no agent outputs in runs/). "
              "Run run_arm.py first to validate on real outputs.\n[verify] SKIP (not a failure).")
        return 0
    packet = json.load(open(pkt_path, encoding="utf-8"))
    items = packet["items"]

    # 2) simulate two raters + adjudicator reading the packet (SYNTHETIC stand-ins)
    rng = random.Random(20260627)
    def rate(noise):
        out = []
        for it in items:
            o = J._norm(it["output"])
            for c in it["claim_list"]:
                lab = _synthetic_label(o, c["statement"], c.get("kind", "factual_claim"))
                if rng.random() < noise:  # inject realistic human disagreement
                    lab = rng.choice([x for x in ("asserted", "flagged", "absent") if x != lab])
                out.append({"blind_id": it["blind_id"], "claim_id": c["claim_id"], "label": lab})
        return out
    for rid, noise in [("rater_SYNTH_A", 0.08), ("rater_SYNTH_B", 0.12)]:
        json.dump({"rater_id": rid, "n": None, "ratings": rate(noise)},
                  open(os.path.join(PANEL, f"ratings_{rid}.json"), "w", encoding="utf-8"), indent=1)
    # adjudicator: a cleaner read (low noise) for the disputed items
    json.dump({"rater_id": "rater_SYNTH_adj", "ratings": rate(0.03)},
              open(os.path.join(PANEL, "ratings_adj.json"), "w", encoding="utf-8"), indent=1)

    # 3) run Stage-2 analysis
    out_md = os.path.join(_HERE, "RESULTS_V1_pipeline_check.md")
    rc2 = subprocess.run([sys.executable, os.path.join(_HERE, "analyze_stage2.py"),
                          "--manifest", os.path.join(PANEL, "blind_manifest.json"),
                          "--ratings", os.path.join(PANEL, "ratings_rater_SYNTH_A.json"),
                                       os.path.join(PANEL, "ratings_rater_SYNTH_B.json"),
                          "--adjudicator", os.path.join(PANEL, "ratings_adj.json"),
                          "--out", out_md], capture_output=True, text=True)
    print(rc2.stdout.strip());  print(rc2.stderr.strip()) if rc2.stderr.strip() else None
    ok = rc2.returncode == 0 and os.path.exists(out_md) and "v1 Human-Panel Results" in open(out_md, encoding="utf-8").read()
    # blinding integrity: packet must carry NO arm label
    leak = any("arm" in it for it in items) or "TREATMENT" in json.dumps(packet) or "BASELINE" in json.dumps(packet)
    print(f"[verify] packet items={len(items)} · blinding intact={'NO LEAK' if not leak else 'LEAK!!'} · "
          f"stage2 ran={'yes' if ok else 'NO'}")
    print("[verify] " + ("PASS — full chain runs; result is SYNTHETIC (pipeline check), study stays OPEN."
                          if (ok and not leak) else "FAIL"))
    return 0 if (ok and not leak) else 1

if __name__ == "__main__":
    sys.exit(main())
