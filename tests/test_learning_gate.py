"""Tests: the Learning Gate enforces a real director contribution (PHILOSOPHY.md §5)."""
import os, sys, json, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
import learning_gate as L

H = ("I think the treatment genuinely raised yield in this trial, because the paired design controls "
     "for plot-level variation, the per-plot gains are consistent in their sign across every plot, and the "
     "measured effect size is large relative to the residual spread we observed among all twelve "
     "experimental plots in the field over the full growing season this year, which makes me fairly confident.")
R = ("The confidence interval excludes zero by a wide margin, the per-plot gains are consistent in sign "
     "across the whole block, and the magnitude is several times the residual standard error, so random "
     "plot noise is an implausible explanation for a difference of this size; a real agronomic effect is "
     "by far the most parsimonious reading of these particular paired results from this single-season trial.")

def test_complete_contribution_passes():
    ok, probs, flag = L.validate_contribution({"hypothesis": H, "reasoning": R, "choice": "A — proceed", "socratic": "Confounding by irrigation is my main worry."})
    assert ok and flag == "PASS" and probs == []

def test_short_hypothesis_blocks():
    ok, probs, _ = L.validate_contribution({"hypothesis": "looks fine", "reasoning": R, "choice": "A", "socratic": "x"})
    assert not ok and any("hypothesis" in p for p in probs)

def test_blank_socratic_blocks():
    ok, probs, _ = L.validate_contribution({"hypothesis": H, "reasoning": R, "choice": "A", "socratic": "  "})
    assert not ok and any("Socratic" in p for p in probs)

def test_pasted_hypothesis_flags_review():
    ok, probs, flag = L.validate_contribution({"hypothesis": H, "reasoning": R, "choice": "A", "socratic": "ok"}, ai_summary=H)
    assert ok and flag == "REVIEW"   # identical to AI summary -> copy flag

def test_brief_requires_all_three():
    assert L.validate_brief({"question": "q", "surprise": "s", "constraint": "c"})[0]
    assert not L.validate_brief({"question": "q", "surprise": "", "constraint": "c"})[0]

def test_ledger_append_header_then_rows():
    d = tempfile.mkdtemp(); p = os.path.join(d, "led.csv")
    L.append_ledger(p, ["t", "contribution", "G2", "Jaslam", "complete", "PASS", "ok"])
    L.append_ledger(p, ["t2", "brief", "phase-2", "Jaslam", "complete", "-", "ok"])
    lines = open(p).read().strip().splitlines()
    assert lines[0].startswith("timestamp,kind,id") and len(lines) == 3
