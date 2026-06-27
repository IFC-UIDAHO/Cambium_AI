"""Repairs from the positioning scorecard: citation blocking, bias advisory, gate-requires-contribution."""
import os, sys, json, subprocess, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def run(rel, *a): return subprocess.run([sys.executable, os.path.join(ROOT, rel), *a], capture_output=True, text=True)
HDR = "id,issue,agents,severity,claim_tier,evidence,status,citation_status,citation_support,bias_check\n"
def _ledger(*rows):
    d = tempfile.mkdtemp(); p = os.path.join(d, "l.csv")
    open(p, "w").write(HDR + "".join(r + "\n" for r in rows)); return p

def test_unsupported_citation_is_a_blocker():
    p = _ledger("C2,bad cite,verify,P2,Asserted,argued,accepted,resolved,unsupported,")
    r = run("governance/validate.py", p)
    assert r.returncode == 1 and "UNSUPPORTED" in r.stdout

def test_supported_citation_passes():
    p = _ledger("C1,ok,verify,P2,Asserted,argued,accepted,resolved,,")
    r = run("governance/validate.py", p)
    assert r.returncode == 0

def test_bias_flag_is_advisory_not_blocker():
    p = _ledger("C3,bias,verify,P2,Asserted,argued,accepted,resolved,,representativeness")
    r = run("governance/validate.py", p)
    assert r.returncode == 0 and "BIAS ADVISORY" in r.stdout

def test_bias_clean_is_silent():
    p = _ledger("C4,fine,verify,P2,Asserted,argued,accepted,resolved,,clean")
    r = run("governance/validate.py", p)
    assert r.returncode == 0 and "BIAS ADVISORY" not in r.stdout

def test_gate_requires_contribution_blocks_without_one():
    p = _ledger("C1,ok,verify,P2,Asserted,argued,accepted,resolved,,")
    r = run("tools/gate.py", "G-x", "--ledger", p, "--require-contribution")
    assert r.returncode == 1 and "BLOCKED" in r.stdout

def test_gate_opens_with_complete_contribution():
    p = _ledger("C1,ok,verify,P2,Asserted,argued,accepted,resolved,,")
    H = ("I expect the result to hold under the planned robustness check because the paired design controls the "
         "main confounder, the per-unit gains are consistent in sign across every single unit, and the measured "
         "effect is large relative to the residual noise we observed among all of the units we measured in this "
         "particular study over the full period, which leaves me fairly but not fully confident in the direction.")
    R = ("The confidence interval excludes the null by a comfortable margin, the per-unit pattern is consistent in "
         "direction across the entire block, and the magnitude is several times the residual standard error, so "
         "ordinary sampling noise is an implausible account of a gap of this size; a genuine effect is by a wide "
         "margin the simplest and most parsimonious reading of these particular paired results from this one study.")
    c = tempfile.mktemp(suffix=".json")
    json.dump({"hypothesis": H, "reasoning": R, "choice": "A — accept", "socratic": "Riskiest assumption: independence."}, open(c, "w"))
    r = run("tools/gate.py", "G-x", "--ledger", p, "--require-contribution", "--contribution", c)
    assert r.returncode == 0 and "open for APPROVE" in r.stdout

def test_gate_blocks_wrong_named_approver():
    p = _ledger("C1,ok,verify,P2,Asserted,argued,accepted,resolved,,")
    r = run("tools/gate.py", "G3", "--ledger", p, "--required-approver", "Co-PI Smith", "--approver", "Jaslam")
    assert r.returncode == 1 and "BLOCKED" in r.stdout

def test_gate_opens_for_correct_named_approver():
    p = _ledger("C1,ok,verify,P2,Asserted,argued,accepted,resolved,,")
    r = run("tools/gate.py", "G3", "--ledger", p, "--required-approver", "Smith", "--approver", "Co-PI Smith (Partner U)")
    assert r.returncode == 0 and "open for APPROVE" in r.stdout
