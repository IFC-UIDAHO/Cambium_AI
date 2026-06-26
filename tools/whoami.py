#!/usr/bin/env python3
"""
whoami.py — look up a person or role in the Institute.

Usage:
    python3 tools/whoami.py                     # list everyone
    python3 tools/whoami.py director            # look up by role keyword
    python3 tools/whoami.py "Dr. Co-PI A"       # look up by name
    python3 tools/whoami.py "project manager"   # partial / case-insensitive

Reads config.yml (falls back to config.example.yml if absent).
Works without PyYAML — uses a minimal hand-parser for the simple list format.
"""

import sys
import os
import re

# ── locate repo root (the directory containing config.yml / config.example.yml) ──
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT   = os.path.dirname(SCRIPT_DIR)   # tools/ is one level below root

def _find_config():
    for candidate in ["config.yml", "config.example.yml"]:
        path = os.path.join(REPO_ROOT, candidate)
        if os.path.isfile(path):
            return path, candidate
    return None, None

# ── Role metadata (authoritative source: ROLES.md) ──
# Kept inline so the script is fully self-contained.

ROLE_DESK = {
    "director": {
        "label"      : "Director  (PI / Lab Head)",
        "agents"     : [
            "00-orchestrator",
            "25-principal-investigator",
            "27-proposal-writer",
            "31-collaborator-scout",
            "32-partnership-liaison",
        ],
        "can_approve": [
            "G1 – pursue this RFP?",
            "G2 – which idea advances?",
            "G3a – who do we contact?",
            "G3 – finalize & submit proposal  (Director ONLY)",
            "G4 – apply fixes (any workstream, or delegate to Area Lead)",
            "G5 – release progress/interim report",
            "G6 – publish / external deliverable  (Director ONLY + co-author AI Use Stmt)",
        ],
        "note": (
            "Holds every top gate. Can delegate G4/G5 to the relevant Co-PI. "
            "G3 and G6 require a second human (separation of duties)."
        ),
    },
    "co-pi": {
        "label"      : "Co-PI / Area Lead",
        "agents"     : [
            "04-lab-theory", "05-lab-ml", "06-lab-forestry",
            "07-verify-proof", "08-verify-sae",
            "09-verify-experiments", "10-verify-forestry",
            "11-exec-sim", "12-exec-ablation",
        ],
        "can_approve": [
            "G4 – apply fixes within their own Aim(s) / workstream",
            "G5 – release report (when delegated by Director)",
        ],
        "note": (
            "Human-in-the-loop for their workstream. "
            "Cannot be the sole approver of their own authored deliverable "
            "(separation of duties — Verification boards and Integrity Officer are independent)."
        ),
    },
    "project-manager": {
        "label"      : "Project Manager / Coordinator",
        "agents"     : [
            "33-program-manager",
            "19-office-manager",
            "29-reporting-officer",
            "30-deck-builder",
            "14-record-keeper",
        ],
        "can_approve": [
            "NONE — compiles, schedules, and keeps the gate ledger honest",
            "  (scientific gates always need Director or Co-PI sign-off)",
        ],
        "note": "Operations authority only; no scientific approval.",
    },
    "researcher": {
        "label"      : "Researcher / Postdoc / Staff Scientist",
        "agents"     : [
            "01-scout-fh", "02-scout-spatial", "03-scout-tree-ml",
            "04-lab-theory", "05-lab-ml", "06-lab-forestry",
            "11-exec-sim", "12-exec-ablation",
            "18-ra", "28-faculty-expert",
        ],
        "can_approve": [
            "NONE alone — outputs require Area Lead sign-off before they merge",
        ],
        "note": "Drafts and runs agents; hands verified work up to Area Lead.",
    },
    "student": {
        "label"      : "Student (Trainee)",
        "agents"     : [
            "01-scout-fh", "02-scout-spatial", "03-scout-tree-ml",
            "04-lab-theory", "05-lab-ml", "06-lab-forestry",
            "11-exec-sim", "12-exec-ablation",
            "17-ta", "18-ra", "28-faculty-expert",
        ],
        "can_approve": [
            "NONE alone — same as Researcher; instructor owns grades",
        ],
        "note": "Bound by teaching/learning rules: do not outsource your learning.",
    },
    "engineer": {
        "label"      : "Engineer / Staff",
        "agents"     : [
            "11-exec-sim", "12-exec-ablation",
            "20-data-steward", "16-janitor",
            "22-figures", "15-librarian",
        ],
        "can_approve": [
            "NONE — implements and runs; flags data/reproducibility issues via P0",
        ],
        "note": "Raises P0 blockers via Integrity-Officer (21-integrity-officer). Cannot approve gates.",
    },
    "integrity": {
        "label"      : "Integrity Officer / Data Steward",
        "agents"     : [
            "21-integrity-officer",
            "20-data-steward",
            "07-verify-proof",
            "08-verify-sae",
        ],
        "can_approve": [
            "P0 FLAGS — an open P0 blocks all releases (validate.py enforces this)",
        ],
        "note": (
            "Must be independent of the author. "
            "Can stop a release; cannot approve it. "
            "No one person is both author and sole verifier."
        ),
    },
}

# Gate approver map — mirrors gate_approvers in config.example.yml
GATE_APPROVERS_DEFAULT = {
    "G1_pursue_rfp"      : "director",
    "G2_pick_idea"       : "director  (Co-PIs consulted)",
    "G3a_contact"        : "director",
    "G3_submit_proposal" : "director ONLY",
    "G4_apply_fixes"     : "co-pi / area-lead (for that workstream)",
    "G5_release_report"  : "director  OR  co-pi (when delegated)",
    "G6_publish"         : "director ONLY  + all co-authors sign AI Use Statement",
}

# ── YAML / hand-parser ──────────────────────────────────────────────────────

def _try_yaml(text):
    """Attempt PyYAML parse; return dict or None if unavailable/broken."""
    try:
        import yaml
        return yaml.safe_load(text)
    except ImportError:
        return None
    except Exception:
        return None

def _hand_parse(text):
    """
    Minimal hand-parser for config.yml / config.example.yml.
    Handles: institute block, team list, gate_approvers map.
    Does NOT handle YAML anchors/aliases — not needed for these files.
    """
    data = {"institute": {}, "team": [], "gate_approvers": {}}
    lines = text.splitlines()
    section     = None
    current_item: dict = {}

    def flush():
        if current_item:
            data["team"].append(dict(current_item))
        current_item.clear()

    for raw in lines:
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue

        indent = len(raw) - len(raw.lstrip())

        if indent == 0:
            if stripped == "institute:":
                section = "institute"
            elif stripped == "team:":
                section = "team"
                flush()
            elif stripped == "gate_approvers:":
                flush()
                section = "gate_approvers"
            else:
                section = None
            continue

        if section == "institute":
            m = re.match(r'\s+"?(\w[\w_]*)"?\s*:\s*"?([^"#\n]+?)"?\s*$', raw)
            if m:
                data["institute"][m.group(1)] = m.group(2).strip().strip('"')

        elif section == "team":
            if stripped.startswith("- name:"):
                flush()
                current_item.clear()
                val = stripped[len("- name:"):].strip().strip('"')
                current_item["name"] = val
            elif stripped.startswith("- "):
                flush()
                current_item.clear()
            elif ":" in stripped and current_item:
                key, _, val = stripped.partition(":")
                val = val.strip().strip('"')
                k = key.strip()
                if k == "aims":
                    nums = re.findall(r'\d+', val)
                    current_item["aims"] = [int(n) for n in nums]
                else:
                    current_item[k] = val

        elif section == "gate_approvers":
            m = re.match(r'\s+(\w+)\s*:\s*(.+)', raw)
            if m:
                data["gate_approvers"][m.group(1)] = m.group(2).strip().strip('"')

    flush()
    return data

def load_config():
    path, fname = _find_config()
    if not path:
        return None, None, None
    with open(path, "r", encoding="utf-8") as fh:
        text = fh.read()
    cfg = _try_yaml(text) or _hand_parse(text)
    return cfg, path, fname

# ── Normalise role strings from config → ROLE_DESK keys ─────────────────────

_ROLE_MAP = {
    "director"        : "director",
    "pi"              : "director",
    "co-pi"           : "co-pi",
    "co_pi"           : "co-pi",
    "copi"            : "co-pi",
    "area-lead"       : "co-pi",
    "area_lead"       : "co-pi",
    "project-manager" : "project-manager",
    "project_manager" : "project-manager",
    "pm"              : "project-manager",
    "researcher"      : "researcher",
    "postdoc"         : "researcher",
    "staff-scientist" : "researcher",
    "student"         : "student",
    "engineer"        : "engineer",
    "staff"           : "engineer",
    "integrity"       : "integrity",
    "data-steward"    : "integrity",
    "data_steward"    : "integrity",
}

def _normalise_role(raw: str) -> str:
    return _ROLE_MAP.get(raw.lower().replace("_", "-").strip(), raw.lower().strip())

# ── Display ──────────────────────────────────────────────────────────────────

_SEP  = "─" * 62
_SEP2 = "═" * 62

def _print_member(member: dict, role_key: str, gate_map: dict):
    meta   = ROLE_DESK.get(role_key, {})
    name   = member.get("name", "(unnamed)")
    aims   = member.get("aims", [])
    label  = meta.get("label", role_key)

    print(_SEP)
    print(f"  {name}")
    print(f"  Role     : {label}")
    if aims:
        print(f"  Aims     : {aims}  ← human-in-the-loop for these workstreams")
    print()

    agents = meta.get("agents", [])
    if agents:
        print("  Their desk  (agents they typically drive):")
        for a in agents:
            print(f"    • {a}")
        print()

    approvals = meta.get("can_approve", [])
    print("  Gates they can approve:")
    for g in approvals:
        print(f"    ✓ {g}")

    if gate_map:
        # Show any gate_approvers entries from config that match this role
        matches = [
            (k, v) for k, v in gate_map.items()
            if role_key in str(v).lower().replace("_", "-")
        ]
        if matches:
            print()
            print("  (config.yml gate_approvers that map to this role):")
            for k, v in matches:
                print(f"    {k:<30} → {v}")

    note = meta.get("note", "")
    if note:
        print()
        print(f"  Note: {note}")
    print()

def _print_gate_map(gate_map: dict):
    print(_SEP2)
    print("  Gate approver map:")
    # Merge defaults with anything extra in the config
    merged = dict(GATE_APPROVERS_DEFAULT)
    for k, v in gate_map.items():
        merged[k] = v
    for gate, approver in merged.items():
        print(f"    {gate:<26} → {approver}")
    print(_SEP2)

def print_everyone(cfg: dict):
    team = cfg.get("team", [])
    inst = cfg.get("institute", {})
    gate_map = cfg.get("gate_approvers", {})

    print(_SEP2)
    print(f"  Institute : {inst.get('name', '(not set — edit config.yml)')}")
    print(f"  Director  : {inst.get('director', '(not set)')}")
    print(_SEP2)
    print(f"  Team ({len(team)} member(s))\n")

    for member in team:
        role_key = _normalise_role(member.get("role", ""))
        _print_member(member, role_key, gate_map)

    _print_gate_map(gate_map)

def find_members(cfg: dict, query: str):
    """
    Return list of (member, role_key) whose name or role matches query
    (case-insensitive, partial).
    """
    q    = query.lower().strip()
    hits = []
    for member in cfg.get("team", []):
        name     = member.get("name", "")
        role_raw = member.get("role", "")
        role_key = _normalise_role(role_raw)
        label    = ROLE_DESK.get(role_key, {}).get("label", role_key).lower()

        if (q in name.lower()
                or q == role_raw.lower()
                or q == role_key
                or q in role_key
                or q in label):
            hits.append((member, role_key))
    return hits

# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    cfg, _, fname = load_config()

    if cfg is None:
        print(f"ERROR: No config.yml or config.example.yml found under: {REPO_ROOT}")
        sys.exit(1)

    banner = f"(reading {fname})"

    if len(sys.argv) < 2:
        print(f"\n  {banner}\n")
        print_everyone(cfg)
        return

    query = sys.argv[1]
    hits  = find_members(cfg, query)

    if not hits:
        print(f"\n  No match for '{query}' in {fname}.")
        print("  Tip — search by name or role keyword:")
        print("    python3 tools/whoami.py director")
        print("    python3 tools/whoami.py co-pi")
        print("    python3 tools/whoami.py project-manager")
        print("    python3 tools/whoami.py researcher | student | engineer")
        sys.exit(1)

    print(f"\n  {banner}   query='{query}'\n")
    gate_map = cfg.get("gate_approvers", {})
    for member, role_key in hits:
        _print_member(member, role_key, gate_map)

if __name__ == "__main__":
    main()
