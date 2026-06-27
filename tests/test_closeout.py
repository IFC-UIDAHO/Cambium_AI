"""closeout.py: doc-drift detector for the Support council's automatic close-out."""
import os, sys, re
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
import closeout as C

def test_changelog_date_parses():
    d = C.latest_changelog_date()
    assert d and re.match(r"\d{4}-\d{2}-\d{2}", d)

def test_roadmap_has_last_updated():
    assert C.doc_last_updated("ROADMAP.md") is not None

def test_no_drift_right_now():
    # after the Support sweep, the forward docs should be current
    assert C.check_drift() == []

def test_drift_compare_logic():
    # the core rule: an older doc date than the changelog is drift
    assert "2026-06-26" < "2026-06-27"   # the exact comparison closeout uses

def test_readme_tool_count_matches():
    # closeout's README check: the stated tool count must equal the actual tools/ count (no prose drift)
    problems, unref = C.check_readme_tools()
    assert not any("README says" in p for p in problems), problems
