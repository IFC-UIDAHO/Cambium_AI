"""enforce-all: pace interval, regulated-data scan, human-change tracking, and the gauntlet.

Each test proves a control actually BLOCKS (not just runs) — turning the AI_POLICY Partial points into
enforced ones (#2 tokens, #3 change-tracking, #6 data, #8 pace)."""
import json, os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def _run(tool, *a):
    return subprocess.run([sys.executable, os.path.join(ROOT, "tools", tool), *a],
                          capture_output=True, text=True)

# ---- pace_check (#8) -------------------------------------------------------
def _toks(d, pairs):
    for gate, ts in pairs:
        json.dump({"gate": gate, "approver": "Jaslam", "ts": ts}, open(os.path.join(d, gate + ".json"), "w"))

def test_pace_blocks_gates_too_close():
    d = tempfile.mkdtemp()
    _toks(d, [("G2", 1_000_000), ("G3", 1_000_000 + 5 * 60)])  # 5 min apart
    r = _run("pace_check.py", "--tokens-dir", d, "--strict")
    assert r.returncode == 1 and "BLOCKED" in r.stdout

def test_pace_passes_when_spaced():
    d = tempfile.mkdtemp()
    _toks(d, [("G2", 1_000_000), ("G3", 1_000_000 + 45 * 60)])  # 45 min apart
    r = _run("pace_check.py", "--tokens-dir", d, "--strict")
    assert r.returncode == 0 and "OK" in r.stdout

def test_pace_ignores_test_fixtures():
    d = tempfile.mkdtemp()
    _toks(d, [("G-test-a", 1_000_000), ("G-test-b", 1_000_000 + 60)])  # 1 min, but test fixtures
    assert _run("pace_check.py", "--tokens-dir", d, "--strict").returncode == 0

def test_pace_mint_time_block():
    d = tempfile.mkdtemp()
    _toks(d, [("G2", 1_000_000)])
    r = _run("pace_check.py", "--tokens-dir", d, "gate", "--gate", "G3", "--at", "1000300")  # 5 min later
    assert r.returncode == 1 and "BLOCKED" in r.stdout

# ---- data_scan (#6) --------------------------------------------------------
def test_data_scan_blocks_ssn_and_card():
    f = tempfile.mktemp(suffix=".csv")
    open(f, "w").write("name,note\nAlice,SSN 123-45-6789 card 4111 1111 1111 1111\n")
    r = _run("data_scan.py", f)
    assert r.returncode == 1 and "SSN" in r.stdout and "credit_card" in r.stdout

def test_data_scan_clean_passes():
    f = tempfile.mktemp(suffix=".csv")
    open(f, "w").write("a,b\n1,2\n3,4\n")
    assert _run("data_scan.py", f).returncode == 0

def test_data_scan_allow_does_not_block():
    f = tempfile.mktemp(suffix=".csv")
    open(f, "w").write("x\nSSN 123-45-6789\n")
    assert _run("data_scan.py", f, "--allow").returncode == 0

# ---- learning_gate change-tracking (#3) ------------------------------------
def _contrib(h, r, c="A — choice", s="a real socratic answer here"):
    return {"hypothesis": h, "reasoning": r, "choice": c, "socratic": s}

def test_change_ratio_high_for_novel_contribution():
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import learning_gate as L
    ratio, novel, total = L.contribution_delta("alpha beta gamma delta epsilon", "completely unrelated words only")
    assert ratio == 1.0 and novel == total > 0

def test_change_ratio_zero_when_pasted():
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import learning_gate as L
    ai = "the quick brown fox jumps over the lazy dog repeatedly"
    ratio, novel, _ = L.contribution_delta(ai, ai)
    assert ratio == 0.0 and novel == 0

def test_change_tracking_records_diff_and_ratio():
    """#3: a valid contribution with an AI draft records change_ratio AND writes a diff sidecar."""
    forty = ("My own distinct hypothesis here that clearly exceeds the forty word minimum threshold so it "
             "passes the length check while remaining genuinely my framing of the deliberation question for "
             "this particular gate decision today now truly indeed yes absolutely certainly without any doubt")
    reason = ("My reasoning rests on my own panel experience where single sitting decisions under deadline "
              "pressure were consistently the weakest and a forced gap surfaced objections nobody had voiced "
              "while everyone stayed anchored on the very first framing that happened to be presented early")
    c = tempfile.mktemp(suffix=".json"); ai = tempfile.mktemp(suffix=".txt")
    json.dump(_contrib(forty, reason), open(c, "w"))
    open(ai, "w").write("Unrelated AI draft about citation formatting and bibliography deduplication only.")
    g = "G-test-delta-" + str(os.getpid())
    r = _run("learning_gate.py", "check", "--gate", g, "--contribution", c, "--ai-summary", ai)
    assert r.returncode == 0
    ledger = open(os.path.join(ROOT, "governance", "CONTRIBUTION_LEDGER.csv"), encoding="utf-8").read()
    assert "change_ratio=" in ledger
    dd = os.path.join(ROOT, "governance", "contribution_diffs")
    assert any(f.startswith(g) for f in os.listdir(dd))

def test_copy_flag_review_still_fires():
    """Pasting the AI draft as the hypothesis still trips the copy-flag REVIEW (rc 2)."""
    ai_text = ("the quick brown fox jumps over the lazy dog and then the quick brown fox does it again and "
               "again and again so that this single line is comfortably and clearly over the minimum word "
               "length threshold of forty tokens today right now for certain without any doubt at all indeed")
    c = tempfile.mktemp(suffix=".json"); ai = tempfile.mktemp(suffix=".txt")
    json.dump(_contrib(ai_text, ai_text), open(c, "w")); open(ai, "w").write(ai_text)
    g = "G-test-copy-" + str(os.getpid())
    assert _run("learning_gate.py", "check", "--gate", g, "--contribution", c, "--ai-summary", ai).returncode == 2

# ---- enforce gauntlet ------------------------------------------------------
def test_enforce_blocks_on_dirty_data():
    f = tempfile.mktemp(suffix=".csv")
    open(f, "w").write("x\nSSN 123-45-6789\n")
    r = _run("enforce.py", "--data", f, "--skip", "pace,roles,evidence")
    assert r.returncode == 1 and "BLOCKED" in r.stdout

def test_enforce_passes_clean():
    r = _run("enforce.py", "--skip", "data")
    assert r.returncode == 0 and "ALL ENFORCED CONTROLS PASS" in r.stdout
