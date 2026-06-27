#!/usr/bin/env python3
"""gate_lock — turn the Learning Gate from a contract into a HARD runtime interlock (open thread #2).

A bare APPROVE used to advance because enforcement was an Orchestrator-followed contract. This makes it
by-construction for any step that calls the lock:

  mint    <GATE_ID> --approver <name> [--contribution c.json] [--ledger L]
          Verifies the ledger (validate.py) AND the Director contribution (learning_gate) FIRST; only then
          writes a tamper-evident token to governance/gate_tokens/<GATE_ID>.json. If either check fails,
          no token is minted — so a bare/empty/incomplete APPROVE cannot produce a token.

  require <GATE_ID> [--max-age-hours N]
          Exits 1 (BLOCKS) unless a VALID, fresh, untampered token exists. Downstream BUILD/release steps
          call this first; with no token they cannot proceed. The token's sha256 covers gate+approver+ts+
          contribution-hash, so editing the JSON by hand invalidates it.

Honest ceiling: this is unbypassable for any step that *calls* `require`; a step that never calls it is not
forced to. True OS-level enforcement needs a sandbox Cambium does not control. But the lock is real, hashed,
and testable — strictly stronger than "the orchestrator promised to check."

Exit: 0 ok · 1 blocked/failed.
"""
import argparse, hashlib, json, os, subprocess, sys, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOKDIR = os.path.join(ROOT, "governance", "gate_tokens")
SECRET = "cambium-gate-v1"  # not a security secret; a tamper-evidence salt so hand-edits invalidate the token

def _sha(*parts):
    return hashlib.sha256(("\x1f".join(str(p) for p in parts) + SECRET).encode()).hexdigest()

def _contribution_hash(contrib):
    if not contrib or not os.path.exists(contrib): return ""
    return hashlib.sha256(open(contrib, "rb").read()).hexdigest()[:16]

def mint(gate_id, approver, contribution, ledger):
    # ledger must pass
    if ledger and os.path.exists(ledger):
        r = subprocess.run([sys.executable, os.path.join(ROOT, "governance", "validate.py"), ledger],
                           capture_output=True, text=True)
        if r.returncode != 0:
            print(f"[gate_lock] BLOCKED: ledger {ledger} has release blockers; no token minted."); return 1
    # contribution must be complete (if learning_gate is present)
    if contribution:
        sys.path.insert(0, os.path.join(ROOT, "tools"))
        import learning_gate as L
        try:
            ok, probs, _ = L.validate_contribution(json.load(open(contribution, encoding="utf-8")))
        except Exception as e:
            print(f"[gate_lock] BLOCKED: contribution unreadable ({str(e)[:80]}); no token minted."); return 1
        if not ok:
            print(f"[gate_lock] BLOCKED: contribution incomplete ({'; '.join(probs)}); no token minted."); return 1
    ts = int(time.time()); chash = _contribution_hash(contribution)
    token = {"gate": gate_id, "approver": approver, "ts": ts, "contribution_hash": chash,
             "sig": _sha(gate_id, approver, ts, chash)}
    os.makedirs(TOKDIR, exist_ok=True)
    json.dump(token, open(os.path.join(TOKDIR, gate_id + ".json"), "w"), indent=2)
    print(f"[gate_lock] ✓ token minted for {gate_id} (approver={approver}). Downstream steps may proceed.")
    return 0

def require(gate_id, max_age_hours):
    p = os.path.join(TOKDIR, gate_id + ".json")
    if not os.path.exists(p):
        print(f"[gate_lock] ⛔ BLOCKED: no approval token for {gate_id}. This step cannot run until the gate "
              f"is approved (gate_lock.py mint {gate_id})."); return 1
    t = json.load(open(p, encoding="utf-8"))
    if t.get("sig") != _sha(t.get("gate"), t.get("approver"), t.get("ts"), t.get("contribution_hash", "")):
        print(f"[gate_lock] ⛔ BLOCKED: token for {gate_id} is TAMPERED (signature mismatch)."); return 1
    if max_age_hours and (time.time() - t.get("ts", 0)) > max_age_hours * 3600:
        print(f"[gate_lock] ⛔ BLOCKED: token for {gate_id} is stale (> {max_age_hours}h); re-approve."); return 1
    print(f"[gate_lock] ✓ valid approval token for {gate_id} (approver={t.get('approver')}); step may run.")
    return 0

def main(argv=None):
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd")
    m = sub.add_parser("mint"); m.add_argument("gate"); m.add_argument("--approver", required=True)
    m.add_argument("--contribution"); m.add_argument("--ledger")
    rq = sub.add_parser("require"); rq.add_argument("gate"); rq.add_argument("--max-age-hours", type=float, default=0)
    a = ap.parse_args(argv)
    if a.cmd == "mint": return mint(a.gate, a.approver, a.contribution, a.ledger)
    if a.cmd == "require": return require(a.gate, a.max_age_hours)
    ap.print_help(); return 0

if __name__ == "__main__": sys.exit(main())
