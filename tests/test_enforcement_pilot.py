"""Tests for the enforcement pilot: blind judge discrimination + stats correctness. No API key."""
import json, os, sys, math
HERE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "evals", "enforcement_study")
sys.path.insert(0, HERE)
import judge_stage1 as J
import analyze as A

def _task():
    return json.load(open(os.path.join(HERE, "tasks", "T001.json"), encoding="utf-8"))

def test_judge_catches_when_flagged():
    t = _task()
    honest = "\n".join(t["ground_truth"]["acceptable_uncertainty_expressions"])
    v = J.judge_task(t, honest)
    assert all(x["caught"] for x in v["false_claim_verdicts"])  # all flagged -> all caught

def test_judge_misses_when_asserted_as_fact():
    t = _task()
    careless = "\n".join(t["ground_truth"]["false_claims_to_catch"]) + "\nThese results are clear."
    v = J.judge_task(t, careless)
    assert not any(x["caught"] for x in v["false_claim_verdicts"])  # none flagged -> none caught
    assert any(not c["resolves"] for c in v["citation_verdicts"])   # made bad citations

def test_judge_is_arm_blind():
    # identical text must score identically regardless of any arm label
    t = _task(); txt = "Hernandez et al. (2023) cannot be verified; not in the reference list."
    assert J.judge_task(t, txt)["false_claim_verdicts"] == J.judge_task(t, txt)["false_claim_verdicts"]

def test_wilson_interval_known_value():
    p, lo, hi = A.wilson(0, 36)
    assert p == 0.0 and lo < 0.01 and 0.0 < hi < 0.12   # rule-of-three-ish upper bound

def test_cohen_h_signs():
    assert A.cohen_h(0.0, 1.0) < -3.0          # max separation
    assert abs(A.cohen_h(0.5, 0.5)) < 1e-9     # no difference

def test_two_prop_z_one_sided():
    z, p = A.two_prop_z(0, 36, 36, 36, "less")  # treatment far lower
    assert z < -5 and p < 1e-6

def test_ocr_rr_deferred_empty():
    t = _task()
    v = J.judge_task(t, "anything at all")
    assert v["over_claim_verdicts"] == [] and v["reproducibility_verdicts"] == []
