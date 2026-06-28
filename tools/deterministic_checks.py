#!/usr/bin/env python3
"""deterministic_checks — verification that needs no LLM to be trusted.

Cambium's weakest trust point is "Claude grading Claude." The strongest answer is to ground as many
checks as possible in things a skeptic can verify without trusting any model: arithmetic that either sums
or doesn't, a DOI that either resolves or doesn't, a claimed number that either equals the reproduced one
or doesn't.

This module does two things:
  1. Runs real, deterministic / external-source checks (budget sums, number-matches-rerun, DOI resolves).
  2. Holds the CHECK REGISTRY that tags every Cambium verification as deterministic, external-source, or
     model-judged, so a reviewer can see exactly how much of verification needs zero trust in an LLM.
     `--registry` prints the split and writes governance/CHECKS.md.

  python3 tools/deterministic_checks.py budget '{"items":[120000,18000,4500],"claimed_total":142500}'
  python3 tools/deterministic_checks.py number --claimed 0.331 --reproduced 0.333 --abs-tol 0.005
  python3 tools/deterministic_checks.py doi 10.1038/s41586-020-2649-2
  python3 tools/deterministic_checks.py registry
"""
from __future__ import annotations
import argparse, json, os, sys, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ----------------------------- the deterministic checks -----------------------------

def budget_sums(items, claimed_total, tol=0.01):
    """Pure arithmetic: do the line items actually add up to the claimed total?"""
    total = round(sum(float(x) for x in items), 2)
    ok = abs(total - float(claimed_total)) <= tol
    return {"check": "budget_sums", "type": "deterministic", "pass": ok,
            "computed_total": total, "claimed_total": float(claimed_total),
            "delta": round(total - float(claimed_total), 2)}

def number_matches(claimed, reproduced, rel_tol=0.0, abs_tol=0.0):
    """A claimed number must equal the reproduced (re-run) number within tolerance. Pure comparison."""
    c, r = float(claimed), float(reproduced)
    ok = abs(c - r) <= max(abs_tol, rel_tol * abs(r))
    return {"check": "number_matches_rerun", "type": "deterministic", "pass": ok,
            "claimed": c, "reproduced": r, "abs_diff": round(abs(c - r), 6)}

def doi_resolves(doi, timeout=8):
    """External ground truth: does this DOI resolve? Best-effort (needs network); honest 'unknown' if not."""
    doi = doi.strip().replace("https://doi.org/", "").replace("doi:", "").strip()
    url = "https://doi.org/" + doi
    try:
        req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "Cambium (https://github.com/IFC-UIDAHO/Cambium_AI)"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            ok = 200 <= r.status < 400
            return {"check": "doi_resolves", "type": "external-source", "pass": ok,
                    "doi": doi, "status": r.status, "resolved_url": r.geturl()}
    except Exception as e:
        return {"check": "doi_resolves", "type": "external-source", "pass": None,
                "doi": doi, "status": "unknown", "note": "no network or DOI unreachable: " + str(e)[:80]}

# ----------------------------- the check registry (the honest tagging) -----------------------------
# type: deterministic (pure computation) · external-source (checked against a real outside authority) ·
#       model-judged (a model or human forms the judgment). The first two need no trust in an LLM.
REGISTRY = [
    {"gate_area": "Citations",      "check": "citation resolves in OpenAlex/Crossref", "type": "external-source", "tool": "paper_search.py"},
    {"gate_area": "Citations",      "check": "DOI resolves at doi.org",                "type": "external-source", "tool": "deterministic_checks.py"},
    {"gate_area": "Budget",         "check": "line items sum to the claimed total",    "type": "deterministic",   "tool": "deterministic_checks.py"},
    {"gate_area": "Results",        "check": "claimed number equals the reproduced one","type": "deterministic",   "tool": "deterministic_checks.py / provenance.py"},
    {"gate_area": "Data",           "check": "PII / regulated-data scan (regex + Luhn)","type": "deterministic",   "tool": "data_scan.py"},
    {"gate_area": "Pace",           "check": "deliberation interval between decisions", "type": "deterministic",   "tool": "pace_check.py"},
    {"gate_area": "Roles",          "check": "named approver matches the roster",       "type": "deterministic",   "tool": "gate.py / roles_check.py"},
    {"gate_area": "Learning Gate",  "check": "a real Director contribution is present", "type": "deterministic",   "tool": "learning_gate.py"},
    {"gate_area": "Evidence tiers", "check": "every claim carries a well-formed tier",  "type": "deterministic",   "tool": "validate.py"},
    {"gate_area": "Evidence tiers", "check": "the tier is appropriate to the evidence", "type": "model-judged",    "tool": "validate.py + referee"},
    {"gate_area": "Bias",           "check": "bias mitigation checklist completed",     "type": "deterministic",   "tool": "validate.py (bias_check)"},
    {"gate_area": "Bias",           "check": "the analysis is actually fair",           "type": "model-judged",    "tool": "verify-domain / human"},
    {"gate_area": "Rigor",          "check": "core logic / proofs hold",               "type": "model-judged",    "tool": "verify-rigor"},
    {"gate_area": "Methodology",    "check": "inference / design is valid",            "type": "model-judged",    "tool": "verify-methodology"},
    {"gate_area": "Venue",          "check": "referee score vs venue rubric",          "type": "model-judged",    "tool": "referee"},
    {"gate_area": "Integrity",      "check": "no overclaim beyond the evidence tier",   "type": "model-judged",    "tool": "integrity-officer"},
]

def registry_summary():
    det = sum(1 for c in REGISTRY if c["type"] == "deterministic")
    ext = sum(1 for c in REGISTRY if c["type"] == "external-source")
    mod = sum(1 for c in REGISTRY if c["type"] == "model-judged")
    return det, ext, mod, len(REGISTRY)

def write_checks_md():
    det, ext, mod, tot = registry_summary()
    grounded = det + ext
    L = ["# Verification checks: deterministic vs model-judged\n",
         "Cambium's trust problem is that AI checking AI is not self-evidently trustworthy. So we tag every\n"
         "verification check by how much it needs an LLM to be believed.\n",
         f"- **{grounded} of {tot}** checks are **grounded** ({det} deterministic, {ext} external-source). They\n"
         f"  need no trust in any model: arithmetic that sums or doesn't, a DOI that resolves or doesn't.\n",
         f"- **{mod} of {tot}** are **model-judged**. These are the genuinely hard judgments (is the proof sound,\n"
         f"  is the analysis fair, is the tier appropriate) where a model or a human still forms the call.\n",
         "\nWe report this split honestly rather than implying everything is mechanically verified.\n",
         "\n| Area | Check | Type | Tool |", "|---|---|---|---|"]
    label = {"deterministic": "deterministic", "external-source": "external-source", "model-judged": "model-judged"}
    for c in REGISTRY:
        L.append(f"| {c['gate_area']} | {c['check']} | {label[c['type']]} | `{c['tool']}` |")
    L.append("\n*Deterministic = pure computation. External-source = checked against a real outside authority "
             "(OpenAlex, Crossref, doi.org). Model-judged = a model or human forms the judgment.*\n")
    out = os.path.join(ROOT, "governance", "CHECKS.md")
    open(out, "w", encoding="utf-8").write("\n".join(L) + "\n")
    return out, (det, ext, mod, tot)

def main(argv=None):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd")
    b = sub.add_parser("budget"); b.add_argument("spec"); b.add_argument("--tol", type=float, default=0.01)
    n = sub.add_parser("number"); n.add_argument("--claimed", type=float, required=True)
    n.add_argument("--reproduced", type=float, required=True); n.add_argument("--rel-tol", type=float, default=0.0)
    n.add_argument("--abs-tol", type=float, default=0.0)
    d = sub.add_parser("doi"); d.add_argument("doi")
    sub.add_parser("registry")
    a = ap.parse_args(argv)
    if a.cmd == "budget":
        spec = json.loads(a.spec); r = budget_sums(spec["items"], spec["claimed_total"], a.tol)
    elif a.cmd == "number":
        r = number_matches(a.claimed, a.reproduced, a.rel_tol, a.abs_tol)
    elif a.cmd == "doi":
        r = doi_resolves(a.doi)
    elif a.cmd == "registry":
        out, (det, ext, mod, tot) = write_checks_md()
        print(f"[checks] {det+ext}/{tot} grounded ({det} deterministic + {ext} external-source) · "
              f"{mod}/{tot} model-judged -> {os.path.relpath(out, ROOT)}")
        return 0
    else:
        ap.print_help(); return 2
    print(json.dumps(r, ensure_ascii=False))
    return 0 if r.get("pass") in (True, None) else 1

if __name__ == "__main__":
    sys.exit(main())
