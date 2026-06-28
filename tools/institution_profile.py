#!/usr/bin/env python3
"""institution_profile — load, validate, and summarize a Cambium institution profile.

A research-computing or sponsored-programs office sets governance/institution/PROFILE.example.yml ONCE.
This makes that profile a real, checked object rather than a dead document: it validates the required
sections, confirms each approved funder has a rule pack in governance/funders/, confirms the approver
roster file exists, and prints a one-line summary a committee can read. Gates can consult it later
(budget ceilings, allowed models, required approvers).

  python3 tools/institution_profile.py governance/institution/PROFILE.cascadia_example.yml
  python3 tools/institution_profile.py <profile.yml> --strict   # exit 1 on any problem
"""
from __future__ import annotations
import argparse, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REQUIRED = ["institution", "approved_funders", "data_handling", "allowed_models", "budget", "approvers", "gates", "policy"]

def _load(path):
    try:
        import yaml
        return yaml.safe_load(open(path, encoding="utf-8")), None
    except ImportError:
        return None, "PyYAML not installed (pip install pyyaml) — cannot parse the profile"
    except Exception as e:
        return None, "could not parse YAML: " + str(e)[:120]

def validate(path):
    prof, err = _load(path)
    problems = []
    if err:
        return None, [err]
    if not isinstance(prof, dict):
        return None, ["profile is empty or not a mapping"]
    for k in REQUIRED:
        if k not in prof:
            problems.append(f"missing required section: {k}")
    # funders must have rule packs
    funder_dir = os.path.join(ROOT, "governance", "funders")
    have = set()
    if os.path.isdir(funder_dir):
        have = {d.upper() for d in os.listdir(funder_dir)} | {os.path.splitext(d)[0].upper() for d in os.listdir(funder_dir)}
    for f in prof.get("approved_funders", []) or []:
        if str(f).upper().replace("-", "") not in {h.replace("-", "") for h in have}:
            problems.append(f"approved funder '{f}' has no rule pack in governance/funders/")
    # approver roster must exist
    roster = (prof.get("approvers") or {}).get("roster_file")
    if roster and not os.path.exists(os.path.join(ROOT, roster)):
        problems.append(f"approver roster_file not found: {roster}")
    # budget sanity
    b = prof.get("budget") or {}
    if b.get("per_project_cap_usd", 0) == 0:
        problems.append("note: per_project_cap_usd is 0 — a per-project budget must be set before any run")
    return prof, problems

def summarize(prof):
    name = (prof.get("institution") or {}).get("name") or "(unnamed institution)"
    funders = prof.get("approved_funders", []) or []
    b = prof.get("budget") or {}
    g = prof.get("gates") or {}
    return (f"{name}: {len(funders)} approved funder(s) [{', '.join(map(str, funders))}] · "
            f"per-project cap ${b.get('per_project_cap_usd','?')} · "
            f"{len(g.get('required_approver_gates', []) or [])} approver-signed gate(s) · "
            f"regulated-data default = {(prof.get('data_handling') or {}).get('regulated_data_default','?')}")

def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("profile")
    ap.add_argument("--strict", action="store_true", help="exit 1 if any problem (notes excluded)")
    a = ap.parse_args(argv)
    if not os.path.exists(a.profile):
        print(f"[profile] not found: {a.profile}"); return 2
    prof, problems = validate(a.profile)
    if prof is None:
        print("[profile] INVALID:"); [print("   -", p) for p in problems]; return 1
    print("[profile] " + summarize(prof))
    hard = [p for p in problems if not p.startswith("note:")]
    for p in problems:
        print(("   ! " if not p.startswith("note:") else "   · ") + p)
    if not problems:
        print("[profile] OK: all sections present, funders and roster resolve.")
    return 1 if (a.strict and hard) else 0

if __name__ == "__main__":
    sys.exit(main())
