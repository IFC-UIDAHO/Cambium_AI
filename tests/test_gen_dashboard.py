"""gen_dashboard: the eval dashboard is generated from live tool output, so it can't drift."""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import gen_dashboard as G

def test_parse_results_matches_real_file():
    text = open(os.path.join(ROOT, "evals", "enforcement_study", "RESULTS.md"), encoding="utf-8").read()
    r = G.parse_results(text)
    assert r["t_fcr"] == "0.33" and r["b_fcr"] == "0.25"
    assert r["diff"] == "+0.08" and r["p"] == "0.78"
    assert "12/36" in r["t_n"] and "9/36" in r["b_n"]

def test_render_injects_live_values_no_placeholders():
    stub = dict(grade="A", tests="999", skipped="1", gauntlet="PASS", agents="46", councils="11",
                gates="8", grounded="10", checks_total="16", model_judged="6", tools="34", policy_enforced="8", leads="3", partial="6", gap="1",
                t_fcr="0.33", t_n="12/36", t_ci="[0.20, 0.50]", b_fcr="0.25", b_n="9/36",
                b_ci="[0.14, 0.41]", h="+0.18", p="0.78", diff="+0.08", diff_ci="[-0.12, +0.28]",
                cite_t="1.00", cite_tn="13/13", cite_b="1.00", cite_bn="14/14")
    html = G.render(stub)
    assert "999" in html and "STUDY RESULT: OPEN" in html
    assert "{tests}" not in html and "{grade}" not in html  # every placeholder filled

def test_open_label_present_no_spin():
    stub = {k: "x" for k in ("grade","tests","skipped","gauntlet","agents","councils","gates","grounded","checks_total","model_judged","tools",
            "policy_enforced","leads","partial","gap","t_fcr","t_n","t_ci","b_fcr","b_n","b_ci","h","p",
            "diff","diff_ci","cite_t","cite_tn","cite_b","cite_bn")}
    html = G.render(stub).lower()
    assert "open" in html and "not spin" in html  # honesty caveat never dropped

def test_check_is_fast_and_passes_when_current():
    """--check must not re-run pytest (no recursion) and pass on the committed, current dashboard."""
    import subprocess, sys
    r = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "gen_dashboard.py"), "--check"],
                       cwd=ROOT, capture_output=True, text=True, timeout=20)
    assert r.returncode == 0 and "up to date" in r.stdout
