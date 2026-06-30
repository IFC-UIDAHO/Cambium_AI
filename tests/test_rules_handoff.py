"""Tests for tools/rules_handoff.py and the handoff schema. Stdlib + tmp dirs only."""
import os
import sys
import json
import tempfile

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_REPO, "tools"))

import rules_handoff as H

_SCHEMA_PATH = os.path.join(_REPO, "examples", "ai4ra", "vandalizer_handoff.schema.json")

_VALID = {
    "solicitation_id": "NSF-25-001",
    "fa_rate_cap": 0.55,
    "total_cost_ceiling": 500000,
    "period_months_max": 36,
    "required_budget_sections": ["personnel", "fringe", "indirect"],
    "disallowed_categories": ["alcohol"],
    "cost_share_required": False,
}


def _schema():
    return json.loads(open(_SCHEMA_PATH, encoding="utf-8").read())


def test_schema_file_exists_and_parses():
    s = _schema()
    assert s["title"].startswith("Vandalizer")
    assert "required_budget_sections" in s["properties"]


def test_minimal_check_passes_valid():
    assert H.minimal_check(_VALID) == []


def test_minimal_check_flags_missing_required():
    bad = dict(_VALID)
    del bad["cost_share_required"]
    problems = H.minimal_check(bad)
    assert any("cost_share_required" in p for p in problems)


def test_minimal_check_flags_wrong_type():
    bad = dict(_VALID)
    bad["required_budget_sections"] = "personnel"  # should be a list
    problems = H.minimal_check(bad)
    assert any("must be a list" in p for p in problems)


def test_minimal_check_allows_null_numbers():
    ok = dict(_VALID)
    ok["fa_rate_cap"] = None
    ok["total_cost_ceiling"] = None
    ok["period_months_max"] = None
    assert H.minimal_check(ok) == []


def test_validate_returns_method_and_problems():
    problems, method = H.validate(_VALID, _schema())
    assert problems == []
    assert isinstance(method, str) and method


def test_validate_catches_bad_doc():
    bad = {"required_budget_sections": ["x"]}  # missing two required keys
    problems, _ = H.validate(bad, _schema())
    assert len(problems) >= 1


def test_cli_valid(tmp_path, capsys):
    p = tmp_path / "rules.json"
    p.write_text(json.dumps(_VALID), encoding="utf-8")
    rc = H.main(["--rules", str(p)])
    assert rc == 0


def test_cli_invalid(tmp_path):
    bad = dict(_VALID)
    del bad["disallowed_categories"]
    p = tmp_path / "rules.json"
    p.write_text(json.dumps(bad), encoding="utf-8")
    rc = H.main(["--rules", str(p)])
    assert rc == 1


def test_valid_handoff_feeds_budget_review(tmp_path):
    """The whole point: a valid handoff is accepted by budget_review unchanged."""
    sys.path.insert(0, os.path.join(_REPO, "tools"))
    import budget_review as B
    budget = {
        "period_months": 36,
        "fa_rate": 0.55,
        "totals": {"total": 500000},
        "sections_present": ["personnel", "fringe", "indirect"],
        "line_items": [{"category": "personnel"}],
        "cost_share_present": False,
    }
    results = B.run_checks(_VALID, budget)
    assert all(r["result"] == "PASS" for r in results)
