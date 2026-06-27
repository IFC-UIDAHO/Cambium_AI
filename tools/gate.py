#!/usr/bin/env python3
"""gate — the live gate interlock (eval #3) + Learning-Gate enforcement (PHILOSOPHY.md §5, repair #1).

A human gate can open only when BOTH are true:
  1. the production findings ledger passes governance/validate.py (no open P0, no un-evidenced
     Code-verified, no unresolved/unsupported citation); and
  2. (for a decision gate) the Director's contribution is present — hypothesis, reasoning, a justified
     choice, and a Socratic answer — verified by tools/learning_gate.py. A bare APPROVE cannot advance.

This makes "human-in-the-loop" enforced by construction on the validator-checkable surface: the Director
never reaches APPROVE on a broken ledger OR without having actually thought.

Usage:
  python3 tools/gate.py <GATE_ID> [--ledger PATH]
  python3 tools/gate.py <GATE_ID> --require-contribution --contribution contrib.json [--ai-summary s.txt]
Exit: 1 = BLOCKED · 0 = open for the Director's APPROVE / REVISE / REJECT.
"""
import sys, os, json, subprocess
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def _ledger_ok(gate_id, ledger):
    r = subprocess.run([sys.executable, os.path.join(ROOT, "governance", "validate.py"), ledger],
                       capture_output=True, text=True)
    out = (r.stdout or "").strip() or (r.stderr or "").strip()
    if out: print(out)
    if r.returncode != 0:
        print(f"\n  ⛩ GATE {gate_id} — BLOCKED. Release-blocking findings in {ledger}; resolve them first.")
        return False
    return True

def _contribution_ok(gate_id, contrib_path, ai_summary):
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import learning_gate as L
    if not contrib_path or not os.path.exists(contrib_path):
        print(f"  ⛩ GATE {gate_id} — BLOCKED: a Director contribution is required to open this gate, "
              f"but no --contribution <file> was given (see templates/GATE_SUMMARY.md §8)."); return False
    try:
        d = json.load(open(contrib_path, encoding="utf-8"))
    except Exception as e:
        print(f"  ⛩ GATE {gate_id} — BLOCKED: contribution file unreadable ({str(e)[:80]})."); return False
    ai = open(ai_summary, encoding="utf-8").read() if ai_summary and os.path.exists(ai_summary) else ""
    ok, probs, flag = L.validate_contribution(d, ai)
    if not ok:
        print(f"  ⛩ GATE {gate_id} — BLOCKED: Director contribution incomplete — {'; '.join(probs)}."); return False
    if flag == "REVIEW":
        print(f"  ⚠ GATE {gate_id} — contribution complete but the hypothesis looks copied from the AI summary (REVIEW).")
    return True

def main():
    a = sys.argv[1:]
    if not a: print(__doc__); return 0
    gate_id = a[0]
    ledger = a[a.index("--ledger")+1] if "--ledger" in a else os.path.join(ROOT, "agent_outputs", "findings_ledger.csv")
    require = "--require-contribution" in a
    contrib = a[a.index("--contribution")+1] if "--contribution" in a else None
    ai_sum  = a[a.index("--ai-summary")+1] if "--ai-summary" in a else None
    approver = a[a.index("--approver")+1] if "--approver" in a else None
    req_appr = a[a.index("--required-approver")+1] if "--required-approver" in a else None
    roles_f  = a[a.index("--roles")+1] if "--roles" in a else None
    if roles_f and not req_appr and os.path.exists(roles_f):       # Stage-1.5: look the approver up from the roles file
        sys.path.insert(0, os.path.join(ROOT, "tools"))
        import roles_check as RC
        try: req_appr = RC.lookup_approver(RC.load(roles_f), gate_id)
        except Exception: req_appr = None

    if os.path.exists(ledger):
        if not _ledger_ok(gate_id, ledger): return 1
    else:
        print(f"[gate] no production ledger at {ledger} — nothing to block on the ledger side.")

    # multi-PI Stage-1: this gate's scope requires a NAMED approver (separation of duties across institutions)
    if req_appr:
        a_l, r_l = (approver or "").lower(), req_appr.lower()
        if not approver or not (r_l in a_l or a_l in r_l):
            print(f"  ⛩ GATE {gate_id} — BLOCKED: this gate must be approved by '{req_appr}', "
                  f"but the approver is '{approver or 'unspecified'}' (see ROLES.md / multi-PI roles)."); return 1

    if require or contrib:
        if not _contribution_ok(gate_id, contrib, ai_sum): return 1
        tail = " AND Director contribution recorded"
    else:
        tail = ""
    who = f" by {approver}" if approver else ""
    print(f"\n  ⛩ GATE {gate_id} — ledger clear{tail}; open for APPROVE / REVISE / REJECT{who}.")
    return 0

if __name__ == "__main__": sys.exit(main())
