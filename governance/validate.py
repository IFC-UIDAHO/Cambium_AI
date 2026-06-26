#!/usr/bin/env python3
"""Evidence-discipline validator for Cambium (v3.1 - hardened).

Enforces, from agent_outputs/findings_ledger.csv:
  - claim_tier in the allowed set (no undocumented tiers)
  - evidence-or-silence (no empty evidence)
  - 'Code-verified' MUST carry a command/run marker (else only Asserted)   [B1/F2]
  - citation_status != 'unresolved' (no fabricated/unresolved references)   [B1]
  - reproducibility: a deliverable row with repro=='missing' is flagged     [B2]
  - open P0 findings are release blockers
  - 'Asserted' claims must be downgraded/closed
Writes governance/provenance.json but NEVER clobbers a good manifest with an
empty one (a no-arg run on an empty ledger preserves the last manifest).    [F2]

Usage:  python3 governance/validate.py [path/to/findings_ledger.csv]
Optional columns honored if present: citation_status, repro.
"""
import csv, sys, json, os, datetime

TIERS = {"Proved", "Code-verified", "Asserted", "Open"}
CMD_MARKERS = ("$", "```", "python", "pytest", "rscript", "make", "sha256", "run:", "command:")
LEDGER = sys.argv[1] if len(sys.argv) > 1 else "agent_outputs/findings_ledger.csv"

def has_command(ev):
    e = ev.lower()
    return any(m in e for m in CMD_MARKERS)

def main():
    if not os.path.exists(LEDGER):
        print("[validate] no ledger at %s (nothing to check yet)" % LEDGER); return 0
    rows = list(csv.DictReader(open(LEDGER, newline="", encoding="utf-8")))
    problems, blockers, agents = [], [], set()
    by_tier = {}
    for r in rows:
        tier = (r.get("claim_tier") or "").strip()
        sev  = (r.get("severity") or "").strip().upper()
        ev   = (r.get("evidence") or "").strip()
        stt  = (r.get("status") or "").strip().lower()
        cit  = (r.get("citation_status") or "").strip().lower()
        repro= (r.get("repro") or "").strip().lower()
        for a in (r.get("agents") or "").split(","):
            if a.strip(): agents.add(a.strip())
        by_tier[tier] = by_tier.get(tier, 0) + 1
        if tier and tier not in TIERS:
            problems.append("  bad claim_tier '%s' in %s" % (tier, r.get("id")))
        if not ev:
            problems.append("  EVIDENCE-OR-SILENCE violation: %s has no evidence" % r.get("id"))
        if tier == "Code-verified" and not has_command(ev):
            blockers.append("  CODE-VERIFIED WITHOUT A COMMAND: %s - cite the run, or it is only Asserted" % r.get("id"))
        if cit == "unresolved":
            blockers.append("  UNRESOLVED CITATION: %s - librarian must resolve every reference" % r.get("id"))
        if repro == "missing":
            problems.append("  REPRODUCIBILITY CHECKLIST MISSING: %s (see templates/REPRODUCIBILITY_CHECKLIST.md)" % r.get("id"))
        if sev == "P0" and stt in ("", "open"):
            blockers.append("  OPEN P0 (release blocker): %s - %s" % (r.get("id"), str(r.get("issue",""))[:60]))
        if tier == "Asserted" and stt in ("", "open"):
            problems.append("  un-downgraded ASSERTED claim: %s" % r.get("id"))

    prov = "governance/provenance.json"
    if rows:
        manifest = {
            "generated": datetime.datetime.now().isoformat(timespec="seconds"),
            "ledger": LEDGER, "n_findings": len(rows),
            "tiers": by_tier, "agents_involved": sorted(agents),
            "model": os.environ.get("AI_MODEL", "<set AI_MODEL env to record>"),
            "note": "Provenance manifest. Pair with the AI Use Statement.",
        }
        os.makedirs("governance", exist_ok=True)
        json.dump(manifest, open(prov, "w"), indent=2)
        wrote = "provenance.json written"
    else:
        wrote = "0 rows - provenance.json preserved (not clobbered)"

    print("[validate] %d findings | tiers=%s | agents=%d | %s" % (len(rows), by_tier, len(agents), wrote))
    if problems:
        print("[validate] WARNINGS:"); print("\n".join(problems))
    if blockers:
        print("[validate] BLOCKERS (do not release):"); print("\n".join(blockers))
        print("[validate] -> FAILED."); return 1
    print("[validate] OK: no blockers."); return 0

if __name__ == "__main__":
    sys.exit(main())
