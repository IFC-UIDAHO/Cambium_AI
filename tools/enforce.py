#!/usr/bin/env python3
"""enforce — the single "enforce all" gauntlet for Cambium's governance controls.

One command runs every machine-checkable enforcement control and BLOCKS (exit 1) if any fails. This is
what makes the AI_POLICY / VISION commitments enforced rather than asserted: CI runs `enforce.py` and a
red run means a real control tripped.

Controls (each maps to a policy point):
  evidence    governance/validate.py        — tiers, citations, open-P0 (AI_POLICY §5)
  pace        tools/pace_check.py --strict   — deliberation interval between gates (AI_POLICY §8)
  roles       tools/roles_check.py           — named multi-PI approver validity (AI_POLICY §9)
  data        tools/data_scan.py <path>      — regulated/PII detection (AI_POLICY §6) [only if --data]
  tokens      tools/gate_lock.py require <G> — a valid contribution-bound token exists (AI_POLICY §2) [only if --require-gate]

  python3 tools/enforce.py [--ledger PATH] [--data PATH] [--require-gate Gx ...] [--pace-min N] [--skip pace,data]
Exit: 0 = every enforced control passed · 1 = at least one control BLOCKED.
"""
import argparse, os, subprocess, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = sys.executable

def run(label, cmd):
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    out = ((r.stdout or "") + (r.stderr or "")).strip()
    return (label, r.returncode == 0, out)

def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--ledger", default="tools/ci_ledger.csv")
    ap.add_argument("--data", help="path to scan for regulated/PII content")
    ap.add_argument("--require-gate", nargs="*", default=[], help="gate IDs that must have a valid token")
    ap.add_argument("--pace-min", type=float, default=None)
    ap.add_argument("--roles", default="templates/MULTI_PI_ROLES.yml")
    ap.add_argument("--skip", default="", help="comma-list of controls to skip: pace,data,roles,evidence,tokens")
    a = ap.parse_args(argv)
    skip = {s.strip() for s in a.skip.split(",") if s.strip()}
    results = []

    if "evidence" not in skip:
        results.append(run("evidence", [PY, "governance/validate.py", a.ledger]))
    if "pace" not in skip:
        cmd = [PY, "tools/pace_check.py", "--strict"]
        if a.pace_min is not None: cmd = [PY, "tools/pace_check.py", "--min-minutes", str(a.pace_min), "--strict"]
        results.append(run("pace", cmd))
    if "roles" not in skip and os.path.exists(os.path.join(ROOT, a.roles)):
        try:
            import yaml  # noqa: F401 — roles_check needs PyYAML; degrade gracefully if absent
            results.append(run("roles", [PY, "tools/roles_check.py", a.roles]))
        except ImportError:
            print("  [SKIP] roles    (PyYAML not installed — `pip install pyyaml`; advisory, not a block)")
    if "data" not in skip and a.data:
        results.append(run("data", [PY, "tools/data_scan.py", a.data]))
    for g in a.require_gate:
        if "tokens" not in skip:
            results.append(run("token:%s" % g, [PY, "tools/gate_lock.py", "require", g]))

    print("=== Cambium enforcement gauntlet ===")
    width = max((len(l) for l, _, _ in results), default=8)
    allok = True
    for label, ok, out in results:
        print("  [%s] %-*s" % ("PASS" if ok else "BLOCK", width, label))
        if not ok:
            allok = False
            for line in out.splitlines()[-4:]:
                print("        %s" % line)
    if not results:
        print("  (no controls selected)")
    print("=== %s ===" % ("ALL ENFORCED CONTROLS PASS" if allok else "BLOCKED — a control failed"))
    return 0 if allok else 1

if __name__ == "__main__":
    sys.exit(main())
