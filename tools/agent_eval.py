#!/usr/bin/env python3
"""agent_eval.py - deterministic reliability eval for a Cambium trajectory.

EVALS.md defines a quality FLOOR (gate discipline, citation integrity, tier
honesty, faithfulness) and says the harness is "to be wired in v3.2" via an
Agent-as-a-Judge pass. This is the deterministic core of that harness: it scores
a *completed* trajectory from the artifacts it leaves behind (human-approval
ledger + findings ledger) with NO LLM judge and NO API key, so it can run in CI
and gate on the floor every push.

Command-marker definition is imported from governance/validate.py so the eval
and the canonical evidence validator can never disagree about what counts as a
"Code-verified" run. (Guarded by tests/test_agent_eval.py.)

Scores (all from files already in the trajectory):
  - Gate discipline    = gates with a recorded human approver / total. Floor 1.0
  - Citation integrity = 1 - unresolved / tracked references.         Floor 1.0
  - Tier honesty       = Code-verified rows citing a command / all.   Floor 0.95
  - Faithfulness*      = rows carrying evidence / all rows.           Floor 0.9
  - Open-P0 blocker    = any unresolved P0 finding fails the run.

Usage:  python3 tools/agent_eval.py [trajectory_dir] [--json]
Exit 0 iff every floor is met and no open P0 remains; else 1.
"""
import csv
import datetime
import json
import os
import re
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "governance"))
try:
    from validate import CMD_MARKERS, has_command
except Exception:
    CMD_MARKERS = ("$", "```", "python", "pytest", "rscript", "make",
                   "sha256", "run:", "command:")

    def has_command(ev):
        e = (ev or "").lower()
        return any(m in e for m in CMD_MARKERS)

CLOSED = {"resolved", "superseded", "closed", "done"}
FLOORS = {"gate_discipline": 1.0, "citation_integrity": 1.0,
          "tier_honesty": 0.95, "faithfulness": 0.9}


def score_gates(gates_md):
    if not os.path.exists(gates_md):
        return None, []
    total = 0
    approved = 0
    rows = []
    for line in open(gates_md, encoding="utf-8"):
        if not line.lstrip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 4 or not re.match(r"^G\d", cells[0]):
            continue
        total += 1
        name = cells[3]
        ok = bool(name) and name not in ("-", "TBD")
        approved += 1 if ok else 0
        rows.append((cells[0], ok))
    if total == 0:
        return None, []
    return approved / total, rows


def score_ledger(ledger_csv):
    if not os.path.exists(ledger_csv):
        return None
    rows = list(csv.DictReader(open(ledger_csv, newline="", encoding="utf-8")))
    n = len(rows) or 1
    cv = 0
    cv_ok = 0
    cited = 0
    unresolved = 0
    with_ev = 0
    open_p0 = []
    for r in rows:
        tier = (r.get("claim_tier") or "").strip()
        ev = (r.get("evidence") or "").strip()
        sev = (r.get("severity") or "").strip().upper()
        stt = (r.get("status") or "").strip().lower()
        cit = (r.get("citation_status") or "").strip().lower()
        if ev:
            with_ev += 1
        if tier == "Code-verified":
            cv += 1
            cv_ok += 1 if has_command(ev) else 0
        if cit:
            cited += 1
            unresolved += 1 if cit == "unresolved" else 0
        if sev == "P0" and stt not in CLOSED:
            open_p0.append(r.get("id"))
    return {
        "rows": len(rows),
        "citation_integrity": 1.0 if cited == 0 else (cited - unresolved) / cited,
        "tier_honesty": 1.0 if cv == 0 else cv_ok / cv,
        "faithfulness": with_ev / n,
        "open_p0": open_p0,
    }


def evaluate(traj):
    gd, _ = score_gates(os.path.join(traj, "governance", "GATES.md"))
    led = score_ledger(os.path.join(traj, "agent_outputs", "findings_ledger.csv"))
    s = {
        "trajectory": traj,
        "gate_discipline": gd,
        "citation_integrity": led["citation_integrity"] if led else None,
        "tier_honesty": led["tier_honesty"] if led else None,
        "faithfulness": led["faithfulness"] if led else None,
        "open_p0": led["open_p0"] if led else [],
    }
    failures = []
    for k, floor in FLOORS.items():
        v = s.get(k)
        if v is None:
            failures.append("%s: not measurable (missing artifact)" % k)
        elif v < floor:
            failures.append("%s=%.3f < floor %s" % (k, v, floor))
    if s["open_p0"]:
        failures.append("open P0 finding(s): " + ", ".join(s["open_p0"]))
    s["passed"] = not failures
    s["failures"] = failures
    return s


def _log(traj, s):
    out_dir = os.path.join(traj, "agent_outputs")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "eval_scores.csv")
    new = not os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["timestamp", "gate_discipline", "citation_integrity",
                        "tier_honesty", "faithfulness", "open_p0", "passed"])
        w.writerow([datetime.datetime.now().isoformat(timespec="seconds"),
                    s["gate_discipline"], s["citation_integrity"], s["tier_honesty"],
                    s["faithfulness"], ";".join(s["open_p0"]) or "none", s["passed"]])


def main(argv):
    as_json = "--json" in argv
    args = [a for a in argv if not a.startswith("--")]
    traj = args[0] if args else "examples/full-lifecycle"
    s = evaluate(traj)
    _log(traj, s)
    if as_json:
        print(json.dumps(s, indent=2))
        return 0 if s["passed"] else 1
    print("[agent_eval] trajectory: %s" % traj)
    for k, floor in FLOORS.items():
        v = s[k]
        mark = "ok  " if (v is not None and v >= floor) else "FAIL"
        shown = "n/a" if v is None else ("%.3f" % v)
        print("  %s  %-18s %s  (floor %s)" % (mark, k, shown, floor))
    print("  open P0: %s" % (", ".join(s["open_p0"]) or "none"))
    verdict = "PASS" if s["passed"] else ("FAIL - " + "; ".join(s["failures"]))
    print("[agent_eval] " + verdict)
    return 0 if s["passed"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
