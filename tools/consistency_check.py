#!/usr/bin/env python3
"""Consistency check (v3.3) — keeps the repo's stated numbers honest.

Canonical truth:
  AGENTS   = live count of .claude/agents/*.md (with frontmatter)
  COUNCILS = 11   GATES = 8
Scans docs/site/assets for "<n> agents", "<n> councils", "<word|n> gates" and FAILS on any
mismatch. History files (CHANGELOG), the private cambium_imp, and transient run artifacts
(agent_outputs/, projects/ run boards) are skipped — those quote the very strings being checked.
Run in CI so stale counts can never ship again.

Usage: python3 tools/consistency_check.py
"""
import os, re, glob, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COUNCILS, GATES = 11, 8
GATE_WORDS = {"six":6,"seven":7,"eight":8,"nine":9}
SKIP = ("CHANGELOG","cambium_imp",".git/","agent_outputs","projects/",os.sep+"run_board")
EXTS = ("*.md","*.html","*.svg","*.cff","*.yml","*.yaml","*.json")

def n_agents():
    c=0
    for p in glob.glob(os.path.join(ROOT,".claude","agents","*.md")):
        if os.path.basename(p).upper()=="README.MD": continue
        t=open(p,encoding="utf-8",errors="replace").read()
        if t.startswith("---") and "name:" in t[:200]: c+=1
    return c

def files():
    for ext in EXTS:
        for p in glob.glob(os.path.join(ROOT,"**",ext),recursive=True):
            rel=os.path.relpath(p,ROOT)
            if any(s in rel for s in SKIP): continue
            yield rel,p

def main():
    AGENTS=n_agents()
    bad=[]
    for rel,p in files():
        if rel=="tools/consistency_check.py": continue
        txt=open(p,encoding="utf-8",errors="replace").read()
        for ln,line in enumerate(txt.splitlines(),1):
            for m in re.finditer(r"\b(\d+)\s+agents\b",line):
                n=int(m.group(1))
                # skip range upper-bounds like "15-25 agents across phases" (a per-phase range, not a total claim)
                if re.search(r"\d+\s*[-–—]\s*$", line[:m.start(1)]):
                    continue
                if (n in (34,39) or n>=20) and n!=AGENTS:
                    bad.append(f"{rel}:{ln}: '{m.group(0)}' (should be {AGENTS} agents)")
            for m in re.finditer(r"agents-(\d+)",line):
                if int(m.group(1))!=AGENTS: bad.append(f"{rel}:{ln}: badge 'agents-{m.group(1)}' (should be agents-{AGENTS})")
            for m in re.finditer(r"\b(\d+)\s+councils\b",line):
                if int(m.group(1))!=COUNCILS: bad.append(f"{rel}:{ln}: '{m.group(0)}' (should be {COUNCILS} councils)")
            # Pattern 1: "<word|digit> [named|mandatory] gates" (direct adjacency)
            for m in re.finditer(r"\b(\w+)\s+(?:named\s+|mandatory\s+)?gates\b",line):
                w=m.group(1).lower()
                if w in GATE_WORDS and GATE_WORDS[w]!=GATES: bad.append(f"{rel}:{ln}: '{m.group(0)}' (should be {GATES} gates)")
                if w.isdigit() and int(w)!=GATES: bad.append(f"{rel}:{ln}: '{m.group(0)}' (should be {GATES} gates)")
            # Pattern 2: "<word> lifecycle gates" — catches "six lifecycle gates" which the
            # direct-adjacency pattern misses because "lifecycle" intervenes between the
            # count word and "gates". This class of drift caused the CI gap in v3.2.
            for m in re.finditer(r"\b(\w+)\s+lifecycle\s+gates\b",line):
                w=m.group(1).lower()
                if w in GATE_WORDS and GATE_WORDS[w]!=GATES: bad.append(f"{rel}:{ln}: '{m.group(0)}' (should be {GATES} lifecycle gates)")
                if w.isdigit() and int(w)!=GATES: bad.append(f"{rel}:{ln}: '{m.group(0)}' (should be {GATES} lifecycle gates)")
    print(f"[consistency] canonical: {AGENTS} agents \u00b7 {COUNCILS} councils \u00b7 {GATES} gates")
    if bad:
        print(f"[consistency] {len(bad)} MISMATCH(es):")
        for b in bad:
            print("  " + b)
        print("[consistency] -> FAILED.")
        return 1
    print("[consistency] OK: all stated counts match.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
