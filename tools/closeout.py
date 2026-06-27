#!/usr/bin/env python3
"""closeout — the Support council's automatic close-out sweep (PRESENTATION Act IV).

Run this after ANY change. It is the mechanical answer to "the support staff just sit": it FAILS if the
institute's forward memory drifted behind the code. Specifically it checks that the latest CHANGELOG date
is not newer than the forward docs' 'Last updated' date (i.e. someone shipped a change but never refreshed
ROADMAP / the user docs), runs the consistency check, and prints the CLOSEOUT_CHECKLIST so Support refreshes
EVERY doc — not just the CHANGELOG.

Usage: python3 tools/closeout.py
Exit: 0 = memory is current · 1 = drift / a check failed (close-out is NOT done).
"""
import os, re, sys, subprocess
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FORWARD_DOCS = ["ROADMAP.md"]  # docs that carry a 'Last updated: YYYY-MM-DD' line

def latest_changelog_date():
    p = os.path.join(ROOT, "CHANGELOG.md")
    if not os.path.exists(p): return None
    dates = re.findall(r"^## \d[\d.]*\s*-\s*(\d{4}-\d{2}-\d{2})", open(p, encoding="utf-8").read(), re.M)
    return max(dates) if dates else None

def doc_last_updated(rel):
    p = os.path.join(ROOT, rel)
    if not os.path.exists(p): return None
    m = re.search(r"Last updated:\s*(\d{4}-\d{2}-\d{2})", open(p, encoding="utf-8").read())
    return m.group(1) if m else None

def check_drift():
    problems = []
    cl = latest_changelog_date()
    for rel in FORWARD_DOCS:
        d = doc_last_updated(rel)
        if cl and d and d < cl:
            problems.append(f"{rel} 'Last updated' {d} is OLDER than the latest CHANGELOG entry {cl} — refresh it.")
        elif cl and d is None:
            problems.append(f"{rel} has no 'Last updated:' date to check.")
    return problems

CHECKLIST = """  CLOSE-OUT CHECKLIST (the Support council refreshes ALL of these, not just the CHANGELOG):
    [ ] CHANGELOG.md — new entry      [ ] DECISIONS.md — ADR (if architectural)
    [ ] governance/GATES.md — gate    [ ] README — counts + roadmap paragraph
    [ ] ROADMAP.md — + bump 'Last updated'   [ ] USE_CAMBIUM.md / FAQ.md (if user-facing)
    [ ] POSITIONING.md / PHILOSOPHY.md (if claims moved)   [ ] consistency_check + doctor + pytest green
    [ ] janitor — no stray files / doc drift"""

def check_readme_tools():
    """README must state the right tool count AND name every tool somewhere in the docs (catches prose drift)."""
    import glob, re
    problems = []
    tools = [os.path.basename(p)[:-3] for p in glob.glob(os.path.join(ROOT, "tools", "*.py"))]
    docs = ""
    for d in ("README.md", "ROADMAP.md", "INSTITUTE.md"):
        p = os.path.join(ROOT, d)
        if os.path.exists(p): docs += open(p, encoding="utf-8").read()
    rd = os.path.join(ROOT, "README.md")
    if os.path.exists(rd):
        m = re.search(r"(\d+)\s+tools", open(rd, encoding="utf-8").read())
        if m and int(m.group(1)) != len(tools):
            problems.append(f"README says '{m.group(1)} tools' but tools/ has {len(tools)} .py files.")
    unref = [t for t in tools if t not in docs]
    return problems, unref

def main():
    problems = check_drift()
    rp, unref = check_readme_tools(); problems += rp
    r = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "consistency_check.py")],
                       capture_output=True, text=True)
    if r.returncode != 0:
        problems.append("consistency_check FAILED — counts drifted.")
    print(CHECKLIST)
    if unref: print("  (advisory) tools not named in any doc: " + ", ".join(unref))
    print(f"  latest CHANGELOG date: {latest_changelog_date()} · ROADMAP last-updated: {doc_last_updated('ROADMAP.md')}")
    if problems:
        print("\n[closeout] DRIFT / FAILURES (close-out is NOT done):")
        for p in problems: print("  ✗ " + p)
        return 1
    print("\n[closeout] OK: forward docs are current and consistency passes.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
