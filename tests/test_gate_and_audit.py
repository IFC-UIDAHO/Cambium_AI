"""Tests: gate interlock blocks on open P0; finding_audit flags unsupported self-reports."""
import os, sys, subprocess, tempfile
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def run(tool,*a): return subprocess.run([sys.executable,os.path.join(ROOT,"tools",tool),*a],capture_output=True,text=True)
def test_gate_blocks_on_open_p0():
    d=tempfile.mkdtemp(); p=os.path.join(d,"l.csv")
    open(p,"w").write("id,issue,agents,severity,claim_tier,evidence,status,action\n"
                      "F1,fatal bug,verify,P0,Open,none,open,fix\n")
    r=run("gate.py","G4","--ledger",p); assert r.returncode==1 and "BLOCKED" in r.stdout
def test_gate_opens_on_clean_ledger():
    d=tempfile.mkdtemp(); p=os.path.join(d,"l.csv")
    open(p,"w").write("id,issue,agents,severity,claim_tier,evidence,status,action\n"
                      "F1,minor,verify,P2,Asserted,argued,accepted,n/a\n")
    r=run("gate.py","G4","--ledger",p); assert r.returncode==0 and "open for" in r.stdout
def test_finding_audit_flags_unsupported():
    d=tempfile.mkdtemp()
    open(os.path.join(d,"a.md"),"w").write("## Decision\nAll green, Code-verified, shipped.\n")     # no evidence
    open(os.path.join(d,"b.md"),"w").write("## Decision\nDone — `$ pytest` 120 passed, doctor A.\n")  # has evidence
    r=run("finding_audit.py","--dir",d); assert r.returncode==1 and "a.md" in r.stdout and "b.md" not in r.stdout
