"""gate_lock: the Learning Gate as a hard, tamper-evident runtime interlock (open thread #2)."""
import os, sys, json, subprocess, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def run(*a): return subprocess.run([sys.executable, os.path.join(ROOT, "tools", "gate_lock.py"), *a], capture_output=True, text=True)

def test_require_blocks_without_token():
    r = run("require", "G-test-noexist-xyz")
    assert r.returncode == 1 and "BLOCKED" in r.stdout

def test_mint_then_require_passes():
    g = "G-test-mint-" + str(os.getpid())
    assert run("mint", g, "--approver", "Jaslam").returncode == 0
    assert run("require", g).returncode == 0

def test_tampered_token_blocks():
    g = "G-test-tamper-" + str(os.getpid())
    run("mint", g, "--approver", "Jaslam")
    p = os.path.join(ROOT, "governance", "gate_tokens", g + ".json")
    t = json.load(open(p)); t["approver"] = "Imposter"; json.dump(t, open(p, "w"))
    assert run("require", g).returncode == 1

def test_incomplete_contribution_mints_no_token():
    g = "G-test-badcontrib-" + str(os.getpid())
    c = tempfile.mktemp(suffix=".json")
    json.dump({"hypothesis": "too short", "reasoning": "short", "choice": "A", "socratic": ""}, open(c, "w"))
    r = run("mint", g, "--approver", "Jaslam", "--contribution", c)
    assert r.returncode == 1 and "BLOCKED" in r.stdout
    assert run("require", g).returncode == 1  # no token was minted
