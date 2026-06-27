#!/usr/bin/env python3
"""roles_check — validate a multi-PI roles file and look up a gate's required approver (open thread #9, Stage-1.5).

Stage-1 added `gate.py --required-approver "<name>"` (you typed the name). Stage-1.5 makes it config-driven:
the roles file (templates/MULTI_PI_ROLES.yml) maps every gate to its named, institution-scoped approver, and
`tools/gate.py --roles <file>` looks the approver up automatically. This tool validates that file so a typo'd
or undefined approver can't slip through.

Usage:
  python3 tools/roles_check.py <roles.yml>                 # validate; exit 1 if invalid
  python3 tools/roles_check.py <roles.yml> --gate G4       # print the required approver for a gate
"""
import argparse, os, sys

def load(path):
    import yaml
    return yaml.safe_load(open(path, encoding="utf-8"))

def lookup_approver(roles, gate_id):
    return (roles.get("gate_approvers") or {}).get(gate_id)

def validate(roles):
    problems = []
    people = {p.get("name") for p in (roles.get("people") or []) if isinstance(p, dict)}
    insts = {i.get("name") for i in (roles.get("institutions") or []) if isinstance(i, dict)}
    if not people: problems.append("no 'people' defined")
    for p in (roles.get("people") or []):
        if isinstance(p, dict) and p.get("institution") and p["institution"] not in insts:
            problems.append(f"person '{p.get('name')}' references unknown institution '{p['institution']}'")
    ga = roles.get("gate_approvers") or {}
    if not ga: problems.append("no 'gate_approvers' map")
    for gate, who in ga.items():
        if who not in people:
            problems.append(f"gate {gate}: required approver '{who}' is not a defined person")
    return problems

def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("roles"); ap.add_argument("--gate")
    a = ap.parse_args(argv)
    if not os.path.exists(a.roles):
        print(f"[roles_check] no roles file at {a.roles}"); return 1
    roles = load(a.roles)
    if a.gate:
        who = lookup_approver(roles, a.gate)
        print(who if who else f"[roles_check] no required approver defined for {a.gate}")
        return 0 if who else 1
    problems = validate(roles)
    if problems:
        print("[roles_check] INVALID roles file:")
        for p in problems: print("  ✗ " + p)
        return 1
    n = len(roles.get("gate_approvers") or {})
    print(f"[roles_check] OK: {len(roles.get('people') or [])} people, {n} gate→approver mappings, all valid.")
    return 0

if __name__ == "__main__": sys.exit(main())
