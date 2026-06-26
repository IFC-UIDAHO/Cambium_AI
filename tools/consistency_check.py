#!/usr/bin/env python3
"""Consistency check (v3.2) — keeps the repo's stated numbers honest.

Canonical truth:
  AGENTS   = live count of .claude/agents/*.md (with frontmatter)
  COUNCILS = 11   GATES = 8
Scans docs/site/assets for "<n> agents", "<n> councils", "<word|n> gates" and FAILS on any
mismatch. History files (CHANGELOG) and the private cambium_imp are skipped.
Run in CI so stale counts can never ship again.

Usage: python3 tools/consistency_check.py
"""
import os, re, glob, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COUNCILS, GATES = 11, 8
GATE_WORDS = {"six":6,"seven":7,"eight":8,"nine":9}
SKIP = ("CHANGELOG","cambium_imp",".git/")
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
                if (n in (34,39) or n>=20) and n!=AGENTS:
                    bad.append(f"{rel}:{ln}: '{m.group(0)}' (should be {AGENTS} agents)")
            for m in re.finditer(r"agents-(\d+)",line):
                if int(m.group(1))!=AGENTS: bad.append(f"{rel}:{ln}: badge 'agents-{m.group(1)}' (should be agents-{AGENTS})")
            for m in re.finditer(r"\b(\d+)\s+councils\b",line):
                if int(m.group(1))!=COUNCILS: bad.append(f"{rel}:{ln}: '{m.group(0)}' (should be {COUNCILS} councils)")
            for m in re.finditer(r"\b(\w+)\s+(?:named\s+|mandatory\s+)?gates\b",line):
                w=m.group(1).lower()
                if w in GATE_WORDS and GATE_WORDS[w]!=GATES: bad.append(f"{rel}:{ln}: '{m.group(0)}' (should be {GATES} gates)")
                if w.isdigit() and int(w)!=GATES: bad.append(f"{rel}:{ln}: '{m.group(0)}' (should be {GATES} gates)")
    print(f"[consistency] canonical: {AGENTS} agents · {COUNCILS} councils · {GATES} gates")
    if bad:
        print(f"[consistency] {len(bad)} MISMATCH(es):"); print("\n".join("  "+b for b in bad))
        print("[consistency] -> FAILED."); return 1
    print("[consistency] OK: all stated counts match."); return 0

if __name__=="__main__":
    sys.exit(main())
