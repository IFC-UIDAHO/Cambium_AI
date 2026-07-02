#!/usr/bin/env python3
"""control_map - self-assessment map of Cambium mechanisms to NIST AI RMF 1.0.

Purpose:
  Print a markdown matrix mapping real, shipping Cambium mechanisms to the four
  NIST AI RMF 1.0 functions (GOVERN, MAP, MEASURE, MANAGE). Source framework:
  NIST AI RMF 1.0 (NIST AI 100-1, January 2023). The mapping is data inside
  this tool; every evidence pointer is checked on disk at --root and the row is
  downgraded to status "absent" with a warning if the file is missing.

Usage:
  python3 tools/control_map.py [--root DIR] [--out FILE] [--strict]

Honest limits:
  This is a SELF-ASSESSMENT written by the Cambium project about itself. It is
  not an official NIST crosswalk, not a certification, and not an assessment by
  any accredited body. Function-level mapping only; no subcategory claims.
  Statuses mean: enforced = a machine check blocks on violation; partial = the
  mechanism exists but coverage or triggering is limited; absent = no evidence
  found at this root.

Exit: 0 normally; 1 on invalid input, or with --strict if any evidence pointer
is missing at --root.
"""
import argparse
import os
import sys
import time

import cambium_io  # noqa: F401

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

STATUSES = ("enforced", "partial", "absent")

# (rmf_function, rmf_area, cambium_mechanism, evidence_pointer, status, note)
MAPPING = [
    ("GOVERN", "Accountability and human oversight",
     "Human approval gates locked by one-time gate_lock tokens; a bare APPROVE cannot advance a run",
     "tools/gate_lock.py", "enforced",
     "runtime interlock; resume requires a minted token"),
    ("GOVERN", "Decision records and roles",
     "GATES.md approvals ledger records gate, date, approver, decision, and notes for every human decision",
     "governance/GATES.md", "partial",
     "human-maintained record; format is machine-checked, append-only by convention"),
    ("GOVERN", "Policy made operational",
     "enforce.py gauntlet runs every machine-checkable governance control and blocks on failure",
     "tools/enforce.py", "enforced",
     "run locally and in CI; a red run means a control tripped"),
    ("GOVERN", "Transparency to stakeholders",
     "ai_disclosure.py assembles an AI-use disclosure and audit summary from run records",
     "tools/ai_disclosure.py", "partial",
     "assembles existing records; not a compliance certification"),

    ("MAP", "Provenance and claim context",
     "provenance.py re-runs each Code-verified claim's command and hashes script plus output",
     "tools/provenance.py", "partial",
     "covers only claims that carry a cmd: rerun marker"),
    ("MAP", "Data sensitivity and privacy context",
     "pii_screen.py screens text for likely PII before it is handled or shared, and can redact",
     "tools/pii_screen.py", "partial",
     "pattern-based detection; a human decides what to redact"),
    ("MAP", "Model identity and attribution",
     "model_router.py maps each agent to a concrete model tier and records the AI_MODEL used",
     "tools/model_router.py", "partial",
     "attribution depends on runs going through the router"),

    ("MEASURE", "Evidence quality measurement",
     "validate.py enforces evidence tiers on the findings ledger; an open P0 or an un-evidenced Code-verified claim blocks the gate",
     "governance/validate.py", "enforced",
     "called by gate.py before a gate can open"),
    ("MEASURE", "Tamper evidence on the record",
     "audit_log.py keeps a turn-level hash-chained trail; verify() detects edited, inserted, or deleted rows",
     "tools/audit_log.py", "partial",
     "chain verifies when a trail exists; logging depends on tools being invoked"),
    ("MEASURE", "Internal consistency of stated facts",
     "consistency_check.py fails when stated counts drift from live repository truth",
     "tools/consistency_check.py", "enforced",
     "part of the CI gauntlet"),
    ("MEASURE", "Process fidelity measurement",
     "run_fidelity.py close-out scorecard makes orchestrator skips visible against the routed plan",
     "tools/run_fidelity.py", "partial",
     "advisory and post-hoc; never blocks a run"),

    ("MANAGE", "Resource and cost limits",
     "loop_costs.py budget cap aborts a run at or over the spend ceiling with --enforce-budget",
     "tools/loop_costs.py", "enforced",
     "four-cost guard; the budget cap is the run-aborting control"),
    ("MANAGE", "Risk response and halt authority",
     "a human REJECT at a gate halts the run and is recorded in the approvals ledger",
     "governance/GATES.md", "partial",
     "demonstrated in the ledger (G4 REJECT row); relies on the gate contract plus tokens"),
    ("MANAGE", "Ongoing control verification",
     "enforce.py re-runs the whole control gauntlet on every push so regressions surface",
     "tools/enforce.py", "enforced",
     "same gauntlet as GOVERN row; listed here for the recurring-check duty"),
]

GAPS = [
    "No third-party or independent audit has been performed; every status here is self-reported.",
    "No incident-response or breach playbook ships with the framework.",
    "No continuous monitoring of deployed models: Cambium governs a research workflow; it does not deploy or watch production model endpoints.",
    "No formal bias or impact evaluation of the underlying LLMs themselves; controls act on the workflow around the models.",
    "Mapping is at the RMF function level only; no subcategory-by-subcategory crosswalk is claimed.",
]

DISCLAIMER = (
    "SELF-ASSESSMENT: this mapping was produced by the Cambium project about "
    "itself against NIST AI RMF 1.0 (NIST AI 100-1, January 2023). It is "
    "advisory evidence for a reviewer, not a certification, not an official "
    "NIST crosswalk, and not an assessment by an accredited body.")


def assess(root):
    """Check every evidence pointer under root.

    Returns (rows, missing) where rows are 6-tuples with status possibly
    downgraded to absent, and missing is the list of pointers not found.
    """
    rows, missing = [], []
    for func, area, mech, pointer, status, note in MAPPING:
        path = os.path.join(root, pointer)
        if os.path.exists(path):
            rows.append((func, area, mech, pointer, status, note))
        else:
            missing.append(pointer)
            rows.append((func, area, mech, pointer, "absent",
                         "evidence pointer not found at this root; " + note))
    return rows, missing


def render(root, rows, missing):
    out = []
    out.append("# Cambium control map: NIST AI RMF 1.0 (self-assessment)")
    out.append("")
    out.append("Generated: %s" % time.strftime("%Y-%m-%dT%H:%M:%S"))
    out.append("Root assessed: %s" % root)
    out.append("Source framework: NIST AI RMF 1.0 (NIST AI 100-1, January 2023).")
    out.append("")
    out.append("Status legend: enforced = a machine check blocks on violation; "
               "partial = mechanism exists, coverage or triggering is limited; "
               "absent = no evidence found at this root.")
    for func in ("GOVERN", "MAP", "MEASURE", "MANAGE"):
        out.append("")
        out.append("## %s" % func)
        out.append("")
        out.append("| RMF area | Cambium mechanism | Evidence pointer | Status | Note |")
        out.append("|---|---|---|---|---|")
        for f, area, mech, pointer, status, note in rows:
            if f == func:
                out.append("| %s | %s | %s | %s | %s |" % (area, mech, pointer, status, note))
    out.append("")
    out.append("## Honest gaps (not covered by any mechanism above)")
    out.append("")
    for g in GAPS:
        out.append("- " + g)
    if missing:
        out.append("")
        out.append("## Missing evidence at this root")
        out.append("")
        for p in missing:
            out.append("- %s (status downgraded to absent)" % p)
    out.append("")
    out.append("---")
    out.append(DISCLAIMER)
    out.append("")
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Self-assessment mapping of Cambium mechanisms to the four "
                    "NIST AI RMF 1.0 functions; verifies evidence pointers on disk.")
    ap.add_argument("--root", default=REPO_ROOT, help="repository root to assess (default: this repo)")
    ap.add_argument("--out", default=None, help="also write the markdown to this file")
    ap.add_argument("--strict", action="store_true",
                    help="exit 1 if any evidence pointer is missing at --root")
    a = ap.parse_args(argv)

    root = os.path.abspath(a.root)
    if not os.path.isdir(root):
        print("[control_map] ERROR: root does not exist: %s" % root)
        return 1

    rows, missing = assess(root)
    for p in missing:
        print("[control_map] WARNING: evidence pointer missing: %s (status downgraded to absent)" % p)
    md = render(root, rows, missing)
    print(md)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as fh:
            fh.write(md)
        print("[control_map] wrote %s" % a.out)
    if a.strict and missing:
        print("[control_map] STRICT: %d evidence pointer(s) missing; exit 1." % len(missing))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
