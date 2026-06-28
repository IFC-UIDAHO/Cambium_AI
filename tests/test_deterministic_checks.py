"""Tests for the deterministic / external-source verification checks."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
import deterministic_checks as D

def test_budget_sums_pass():
    r = D.budget_sums([100, 50, 25], 175)
    assert r["pass"] is True and r["type"] == "deterministic" and r["delta"] == 0.0

def test_budget_sums_fail_catches_real_mismatch():
    r = D.budget_sums([120000, 18000, 4500], 150000)
    assert r["pass"] is False and r["delta"] == -7500.0

def test_number_matches_within_tol():
    assert D.number_matches(0.331, 0.333, abs_tol=0.005)["pass"] is True

def test_number_matches_catches_mismatch():
    r = D.number_matches(0.45, 0.33, abs_tol=0.005)
    assert r["pass"] is False and r["abs_diff"] == 0.12

def test_registry_is_majority_grounded():
    det, ext, mod, tot = D.registry_summary()
    assert det + ext + mod == tot
    assert (det + ext) > mod  # most checks need no LLM trust

def test_registry_types_are_valid():
    assert all(c["type"] in ("deterministic", "external-source", "model-judged") for c in D.REGISTRY)
    assert all({"gate_area", "check", "type", "tool"} <= set(c) for c in D.REGISTRY)

def test_checks_md_generates():
    out, (det, ext, mod, tot) = D.write_checks_md()
    assert os.path.exists(out)
    assert "deterministic" in open(out, encoding="utf-8").read()
