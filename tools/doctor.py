#!/usr/bin/env python3
"""Cambium doctor — repo health + self-grade (inspired by ECC/ruflo metaharness).

  python3 tools/doctor.py          # health check (exit 1 on any problem)
  python3 tools/doctor.py --fix    # regenerate derived files, then check
  python3 tools/doctor.py --grade  # score the institute's setup (A-F) + flag risks
"""
import os, sys, ast, glob, json, subprocess, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIX  = "--fix" in sys.argv
GRADE= "--grade" in sys.argv
ok, bad = [], []
def good(m): ok.append(m); print("  ok  " + m)
def fail(m): bad.append(m); print("  X   " + m)
def run(cmd):
    r = subprocess.run([sys.executable]+cmd, cwd=ROOT, capture_output=True, text=True)
    return r.returncode == 0, (r.stdout.strip().splitlines() or [""])[-1]
def exists(*p): return os.path.exists(os.path.join(ROOT, *p))
def html_files():
    return sorted(glob.glob(os.path.join(ROOT,"*.html"))+glob.glob(os.path.join(ROOT,"app","*.html"))+glob.glob(os.path.join(ROOT,"demo","*.html")))
def n_agents():
    return len([p for p in glob.glob(os.path.join(ROOT,".claude","agents","*.md")) if os.path.basename(p).upper()!="README.MD"])

print("== Cambium doctor ==")
if FIX:
    print("\n[fix] regenerating derived files…"); run(["tools/gen_agent_cards.py"]); run(["tools/gen_org_chart.py"])

print("\n[1] agent frontmatter"); a_ok,a_t = run(["tools/check_agents.py"]); (good if a_ok else fail)(a_t[:90])
print("\n[2] stated counts");     c_ok,c_t = run(["tools/consistency_check.py"]); (good if c_ok else fail)(c_t[:90])
print("\n[3] evidence ledger");   v_ok,v_t = run(["governance/validate.py","tools/ci_ledger.csv"]); (good if v_ok else fail)(v_t[:90])
print("\n[4] HTML integrity"); h_ok=True
for f in html_files():
    s=open(f,encoding="utf-8",errors="replace").read(); rel=os.path.relpath(f,ROOT)
    if not s.strip(): fail(rel+" EMPTY"); h_ok=False
    elif not s.rstrip().endswith("</html>"): fail(rel+" truncated"); h_ok=False
    elif s.count("<script")!=s.count("</script>"): fail(rel+" unbalanced <script>"); h_ok=False
    else: good(rel+" intact")
print("\n[5] Python parses"); p_ok=True
for f in sorted(glob.glob(os.path.join(ROOT,"tools","*.py"))+glob.glob(os.path.join(ROOT,"governance","*.py"))):
    rel=os.path.relpath(f,ROOT)
    try: ast.parse(open(f,encoding="utf-8").read()); good(rel)
    except Exception as e: fail(rel+" -> "+str(e)[:60]); p_ok=False
print("\n[6] derived in sync"); nf=n_agents()
d_ok=True
if exists("agent_cards.json"):
    n=json.load(open(os.path.join(ROOT,"agent_cards.json")))["count"]; (good if n==nf else fail)("agent_cards %d==%d agents"%(n,nf)); d_ok=d_ok and n==nf
else: fail("agent_cards.json missing"); d_ok=False

# ---------- self-grade ----------
if GRADE:
    print("\n== SELF-GRADE ==")
    gov=["RESEARCH_CONDUCT.md","AI_GOVERNANCE.md","AI_USE_STATEMENT.md",("governance","GATES.md"),("governance","validate.py"),"TOOL_POLICY.md"]
    tools=[("tools","doctor.py"),("tools","task_router.py"),("tools","toolsmith.py"),("tools","model_router.py"),("tools","consistency_check.py"),("tools","gen_agent_cards.py")]
    docs=["README.md","CHANGELOG.md","INSTITUTE.md","LIFECYCLE_V3.md","ROLES.md"]
    frac=lambda items: sum(1 for it in items if (exists(*it) if isinstance(it,tuple) else exists(it)))/len(items)
    dims={
      "Roster valid": 1.0 if a_ok else 0.0,
      "Counts consistent": 1.0 if c_ok else 0.0,
      "Evidence gate": 1.0 if v_ok else 0.0,
      "HTML integrity": 1.0 if h_ok else 0.0,
      "Code parses": 1.0 if p_ok else 0.0,
      "Derived in sync": 1.0 if d_ok else 0.0,
      "Governance coverage": frac(gov),
      "Tooling completeness": frac(tools),
      "Docs present": frac(docs),
      "Evals + tests": (0.5 if exists("EVALS.md") else 0)+(0.5 if exists("tests") else 0),
      "Decision records": 1.0 if exists("DECISIONS.md") else 0.0,
    }
    # risk scan
    risks=[]
    if exists("app",".auth.json") or exists(".auth.json"): risks.append("committed auth secret (.auth.json)")
    for f in glob.glob(os.path.join(ROOT,"**","*"),recursive=True):
        if os.path.isfile(f) and f.endswith((".md",".py",".yml",".json",".html")) and "cambium_imp" not in f:
            try:
                if re.search(r"ANTHROPIC_API_KEY\s*[=:]\s*sk-[A-Za-z0-9_-]{16,}", open(f,encoding="utf-8",errors="replace").read()): risks.append("hardcoded API key in "+os.path.relpath(f,ROOT)); break
            except Exception: pass
    for k,val in dims.items(): print("  %-22s %3d%%  %s" % (k, round(val*100), "#"*int(val*20)))
    sec = max(0.0, 1.0 - 0.25*len(risks))
    print("  %-22s %3d%%  %s" % ("Security (risk scan)", round(sec*100), "#"*int(sec*20)))
    overall = (sum(dims.values())/len(dims))*0.85 + sec*0.15
    pct=round(overall*100); letter = "A" if pct>=90 else "B" if pct>=80 else "C" if pct>=70 else "D" if pct>=60 else "F"
    print("\n  OVERALL: %d%%  ->  GRADE %s" % (pct, letter))
    if risks: print("  RISKS:"); [print("    ! "+r) for r in risks]
    else: print("  RISKS: none found")

print("\n== %d ok, %d problem(s) ==" % (len(ok), len(bad)))
if bad: print("DOCTOR: problems found." + ("" if FIX else "  Try --fix")); sys.exit(1)
print("DOCTOR: healthy."); sys.exit(0)
