#!/usr/bin/env python3
"""analyze.py — effect sizes + 95% CIs for the enforcement pilot (stdlib only).

Reads the per-(task,arm) results.csv produced by run_study.py and computes, per metric, the pooled
proportion for each arm, the two-proportion one-sided z-test (per PROTOCOL.md H1), Cohen's h effect
size, Wilson 95% CIs per arm, and a Newcombe 95% CI for the difference. Writes RESULTS.md.

HONEST SCOPE (printed in the report): Stage-1 automated proxy judge, 12-item pilot, OCR/RR deferred
to the human panel. Per the protocol, a 12-item pilot is feasibility/calibration — report effect
sizes + CIs regardless of p, and do NOT claim a definitive result or a null from the pilot alone.

Usage: python3 evals/enforcement_study/analyze.py --results results_pilot.csv --out RESULTS.md
"""
from __future__ import annotations
import argparse, csv, math, os, sys
from collections import defaultdict

_HERE = os.path.dirname(os.path.abspath(__file__))
Z95 = 1.959963985  # two-sided 95%

def _phi(x):  # standard normal CDF
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))

def wilson(k, n, z=Z95):
    if n == 0: return (0.0, 0.0, 0.0)
    p = k / n; d = 1 + z*z/n
    center = (p + z*z/(2*n)) / d
    half = (z * math.sqrt(p*(1-p)/n + z*z/(4*n*n))) / d
    return (p, max(0.0, center-half), min(1.0, center+half))

def cohen_h(p1, p2):
    return 2*math.asin(math.sqrt(p1)) - 2*math.asin(math.sqrt(p2))

def two_prop_z(k1, n1, k2, n2, direction):
    """One-sided z. direction='less' tests p1<p2 (treatment FCR lower); 'greater' tests p1>p2."""
    if n1 == 0 or n2 == 0: return (float("nan"), float("nan"))
    p1, p2 = k1/n1, k2/n2
    pp = (k1+k2)/(n1+n2); se = math.sqrt(pp*(1-pp)*(1/n1+1/n2))
    if se == 0: return (float("inf") if p1 != p2 else 0.0, 0.0 if p1 != p2 else 1.0)
    z = (p1-p2)/se
    p = _phi(z) if direction == "less" else 1-_phi(z)
    return (z, p)

def newcombe_diff(k1, n1, k2, n2, z=Z95):
    p1, l1, u1 = wilson(k1, n1, z); p2, l2, u2 = wilson(k2, n2, z)
    d = p1 - p2
    lo = d - math.sqrt((p1-l1)**2 + (u2-p2)**2)
    hi = d + math.sqrt((u1-p1)**2 + (p2-l2)**2)
    return (d, lo, hi)

def load(results):
    agg = defaultdict(lambda: defaultdict(lambda: [0, 0]))  # metric -> arm -> [num, den]
    with open(results, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            arm = r["arm"]
            for m, (nk, dk) in {"FCR": ("fcr_n","fcr_d"), "OCR": ("ocr_n","ocr_d"),
                                "CIR": ("cir_n","cir_d"), "RR": ("rr_n","rr_d")}.items():
                agg[m][arm][0] += int(float(r[nk] or 0)); agg[m][arm][1] += int(float(r[dk] or 0))
    note = ""
    try:
        with open(results, encoding="utf-8") as f:
            note = next(csv.DictReader(f)).get("study_note", "")
    except Exception: pass
    return agg, note

# metric -> (better_direction, z-direction for H1, human label)
META = {
    "FCR": ("lower", "less",    "False-claim rate (PRIMARY) — lower is better"),
    "CIR": ("higher", "greater","Citation integrity (secondary) — higher is better"),
    "OCR": ("lower", "less",    "Over-claim rate (secondary)"),
    "RR":  ("higher", "greater","Reproducibility (secondary)"),
}

def analyze(results, out):
    agg, note = load(results)
    fixture = ("FIXTURE" in note or "DEMO" in note.upper())
    scored = [m for m in ("FCR","CIR","OCR","RR") if agg[m]["TREATMENT"][1] or agg[m]["BASELINE"][1]]
    bonf = max(1, len(scored))
    L = []
    L.append("# Enforcement A/B Pilot — Results (effect sizes + 95% CIs)\n")
    if fixture:
        L.append("> ⚠️ **FIXTURE/DEMO INPUT — NOT A REAL FINDING. Study result remains OPEN.** "
                 "These numbers are synthetic harness-validation data.\n")
    else:
        L.append("> **Stage-1 automated proxy judge · 12-item pilot · OCR/RR deferred to the human panel.** "
                 "Per the pre-registered protocol a 12-item pilot is feasibility/calibration: effect sizes + "
                 "CIs are reported, but this is **not** the definitive human-judged result and **no null** is "
                 "claimed from the pilot alone.\n")
    L.append(f"\n*Bonferroni correction across {bonf} scored comparison(s): significance threshold "
             f"alpha = 0.05 / {bonf} = {0.05/bonf:.4f} (one-sided).*\n")
    L.append("\n| Metric | Treatment | 95% CI (T) | Baseline | 95% CI (B) | Cohen's h | z | p (1-sided) | sig? |")
    L.append("|---|---|---|---|---|---|---|---|---|")
    verdict_lines = []
    for m in scored:
        kt, nt = agg[m]["TREATMENT"]; kb, nb = agg[m]["BASELINE"]
        pt, lt, ut = wilson(kt, nt); pb, lb, ub = wilson(kb, nb)
        direction = META[m][1]
        z, p = two_prop_z(kt, nt, kb, nb, direction)
        h = cohen_h(pt, pb)
        sig = (not math.isnan(p)) and p < (0.05/bonf)
        L.append(f"| {m} | {pt:.2f} ({kt}/{nt}) | [{lt:.2f}, {ut:.2f}] | {pb:.2f} ({kb}/{nb}) | "
                 f"[{lb:.2f}, {ub:.2f}] | {h:+.2f} | {z:+.2f} | {p:.4f} | {'**yes**' if sig else 'no'} |")
        d, dlo, dhi = newcombe_diff(kt, nt, kb, nb)
        verdict_lines.append(f"- **{META[m][2]}**: Treatment {pt:.2f} vs Baseline {pb:.2f}; "
                             f"difference {d:+.2f} (95% CI [{dlo:+.2f}, {dhi:+.2f}]), Cohen's h = {h:+.2f}, "
                             f"one-sided p = {p:.4f}{' (significant after Bonferroni)' if (not math.isnan(p) and p < 0.05/bonf) else ''}.")
    L.append("\n## Per-metric detail (difference CIs)\n")
    L += verdict_lines
    # interpretation
    L.append("\n## Interpretation\n")
    if fixture:
        L.append("No interpretation — fixture data. Run `run_arm.py` live, then re-run.")
    else:
        fcr = agg["FCR"]
        if fcr["TREATMENT"][1] and fcr["BASELINE"][1]:
            pt = fcr["TREATMENT"][0]/fcr["TREATMENT"][1]; pb = fcr["BASELINE"][0]/fcr["BASELINE"][1]
            _, p = two_prop_z(*fcr["TREATMENT"], *fcr["BASELINE"], "less")
            if pt < pb and not math.isnan(p) and p < 0.05/bonf:
                L.append(f"On the **primary** outcome, enforcement **lowered** the false-claim rate "
                         f"({pb:.2f} → {pt:.2f}), significant after Bonferroni in this pilot. Directional support "
                         f"for H1; the central enforcement claim moves from **Open** to **pilot-evidenced** "
                         f"(automated judge, n=12) — still short of the definitive human-judged study.")
            elif pt < pb:
                L.append(f"Enforcement lowered the primary false-claim rate ({pb:.2f} → {pt:.2f}), but the pilot "
                         f"is **underpowered** and the effect is not significant after Bonferroni. Directional, "
                         f"not conclusive — the claim stays **Open**, now with a measured pilot effect size.")
            else:
                L.append(f"In this pilot, enforcement did **not** lower the false-claim rate ({pb:.2f} → {pt:.2f}). "
                         f"No support for H1 here; the claim stays **Open**. (One pilot cannot establish a null — "
                         f"see the protocol power note.)")
        L.append("\nNext step to a definitive result: expand to the v1 task set (≈60 items/arm), add the "
                 "two-rater **human** judge panel (Cohen's κ), and pre-commit before unblinding — exactly as "
                 "`PROTOCOL.md` specifies.")
    open(out, "w", encoding="utf-8").write("\n".join(L) + "\n")
    print(f"[analyze] wrote {out}  ({len(scored)} metric(s) scored; fixture={fixture})")
    return 0

def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default=os.path.join(_HERE, "results_pilot.csv"))
    ap.add_argument("--out", default=os.path.join(_HERE, "RESULTS.md"))
    a = ap.parse_args(argv)
    if not os.path.exists(a.results):
        print(f"[analyze] no results at {a.results} — run run_study.py first."); return 1
    return analyze(a.results, a.out)

if __name__ == "__main__":
    sys.exit(main())
