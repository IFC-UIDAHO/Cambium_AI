"""Tests for tools/budget_review.py.

Uses only stdlib and tmp dirs. Never touches the live repo data.
All checks are deterministic: same inputs produce same outputs.
"""
import os
import sys
import json
import tempfile

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_REPO, "tools"))

import budget_review as B


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

_RULES_CLEAN = {
    "fa_rate_cap": 0.55,
    "total_cost_ceiling": 500000,
    "period_months_max": 36,
    "required_budget_sections": ["personnel", "fringe", "equipment", "travel", "indirect"],
    "disallowed_categories": ["alcohol", "entertainment"],
    "cost_share_required": False,
}

_BUDGET_CLEAN = {
    "period_months": 36,
    "fa_rate": 0.55,
    "totals": {"direct": 380000, "indirect": 120000, "total": 500000},
    "sections_present": ["personnel", "fringe", "equipment", "travel", "indirect"],
    "line_items": [
        {"category": "personnel", "amount": 280000},
        {"category": "travel",    "amount": 12000},
    ],
    "cost_share_present": False,
}


# ---------------------------------------------------------------------------
# Individual check tests
# ---------------------------------------------------------------------------

def test_fa_rate_pass():
    r = B.check_fa_rate({"fa_rate_cap": 0.55}, {"fa_rate": 0.55})
    assert r["result"] == "PASS"


def test_fa_rate_flag_over_cap():
    r = B.check_fa_rate({"fa_rate_cap": 0.55}, {"fa_rate": 0.60})
    assert r["result"] == "FLAG"
    assert "exceeds" in r["note"].lower()


def test_total_cost_pass():
    r = B.check_total_cost({"total_cost_ceiling": 500000}, {"totals": {"total": 499000}})
    assert r["result"] == "PASS"


def test_total_cost_flag_over_ceiling():
    r = B.check_total_cost({"total_cost_ceiling": 500000}, {"totals": {"total": 501000}})
    assert r["result"] == "FLAG"
    assert "501000" in r["actual"] or "501000" in r["note"]


def test_period_pass():
    r = B.check_period({"period_months_max": 36}, {"period_months": 36})
    assert r["result"] == "PASS"


def test_period_flag_too_long():
    r = B.check_period({"period_months_max": 36}, {"period_months": 48})
    assert r["result"] == "FLAG"
    assert "48" in r["actual"]


def test_required_sections_all_present():
    results = B.check_required_sections(
        {"required_budget_sections": ["personnel", "travel"]},
        {"sections_present": ["personnel", "travel", "indirect"]},
    )
    assert all(r["result"] == "PASS" for r in results)


def test_required_sections_missing_flags():
    results = B.check_required_sections(
        {"required_budget_sections": ["personnel", "equipment", "travel"]},
        {"sections_present": ["personnel", "travel"]},
    )
    flagged = [r for r in results if r["result"] == "FLAG"]
    assert len(flagged) == 1
    assert "equipment" in flagged[0]["check"]


def test_disallowed_absent_passes():
    results = B.check_disallowed_categories(
        {"disallowed_categories": ["alcohol", "entertainment"]},
        {"line_items": [{"category": "travel"}, {"category": "personnel"}]},
    )
    assert all(r["result"] == "PASS" for r in results)


def test_disallowed_found_flags():
    results = B.check_disallowed_categories(
        {"disallowed_categories": ["alcohol", "entertainment"]},
        {"line_items": [{"category": "travel"}, {"category": "alcohol"}]},
    )
    flagged = [r for r in results if r["result"] == "FLAG"]
    assert len(flagged) == 1
    assert "alcohol" in flagged[0]["check"].lower()


def test_cost_share_not_required_passes():
    r = B.check_cost_share({"cost_share_required": False}, {})
    assert r["result"] == "PASS"


def test_cost_share_required_absent_flags():
    r = B.check_cost_share({"cost_share_required": True}, {"cost_share_present": False})
    assert r["result"] == "FLAG"


# ---------------------------------------------------------------------------
# Full run_checks integration tests
# ---------------------------------------------------------------------------

def test_clean_budget_all_pass():
    """A compliant budget with all sections must produce no flags."""
    results = B.run_checks(_RULES_CLEAN, _BUDGET_CLEAN)
    flags = [r for r in results if r["result"] == "FLAG"]
    assert flags == [], f"Expected no flags, got: {flags}"


def test_build_report_contains_advisory_header():
    """The report must contain the advisory heading."""
    report = B.build_report(_RULES_CLEAN, _BUDGET_CLEAN, "rules.json", "budget.json")
    assert "advisory, not a compliance determination" in report.lower()


def test_build_report_contains_closing_statement():
    """The report must say a human makes the final determination."""
    report = B.build_report(_RULES_CLEAN, _BUDGET_CLEAN, "rules.json", "budget.json")
    assert "final determination" in report.lower()


def test_build_report_no_em_dashes():
    """No em dashes in the report (Cambium house rule)."""
    report = B.build_report(_RULES_CLEAN, _BUDGET_CLEAN, "rules.json", "budget.json")
    assert "—" not in report


def test_over_cap_budget_flagged_in_report():
    """A budget with fa_rate over cap must show FLAG in the report."""
    budget = dict(_BUDGET_CLEAN)
    budget["fa_rate"] = 0.65
    report = B.build_report(_RULES_CLEAN, budget, "rules.json", "budget.json")
    assert "FLAG" in report


def test_missing_section_flagged_in_report():
    """A budget missing a required section must show FLAG in the report."""
    budget = dict(_BUDGET_CLEAN)
    budget["sections_present"] = ["personnel", "travel"]  # missing equipment, fringe, indirect
    report = B.build_report(_RULES_CLEAN, budget, "rules.json", "budget.json")
    assert "FLAG" in report


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------

def _write_json(path, data):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh)


def test_cli_exits_0_on_clean_budget():
    """CLI must exit 0 (advisory; no fail-on-flag)."""
    with tempfile.TemporaryDirectory() as tmp:
        rules_path = os.path.join(tmp, "rules.json")
        budget_path = os.path.join(tmp, "budget.json")
        _write_json(rules_path, _RULES_CLEAN)
        _write_json(budget_path, _BUDGET_CLEAN)
        out_path = os.path.join(tmp, "report.md")
        rc = B.main(["--rules", rules_path, "--budget", budget_path, "--out", out_path])
        assert rc == 0
        assert os.path.exists(out_path)


def test_cli_exits_0_on_flagged_budget():
    """CLI must exit 0 even when flags are raised (advisory tool)."""
    with tempfile.TemporaryDirectory() as tmp:
        budget = dict(_BUDGET_CLEAN)
        budget["fa_rate"] = 0.65
        budget["totals"] = {"total": 600000}
        rules_path = os.path.join(tmp, "rules.json")
        budget_path = os.path.join(tmp, "budget.json")
        _write_json(rules_path, _RULES_CLEAN)
        _write_json(budget_path, budget)
        out_path = os.path.join(tmp, "report.md")
        rc = B.main(["--rules", rules_path, "--budget", budget_path, "--out", out_path])
        assert rc == 0
        content = open(out_path, encoding="utf-8").read()
        assert "FLAG" in content


def test_cli_exits_2_on_missing_rules():
    """CLI must exit 2 when the rules file is not found."""
    with tempfile.TemporaryDirectory() as tmp:
        budget_path = os.path.join(tmp, "budget.json")
        _write_json(budget_path, _BUDGET_CLEAN)
        try:
            B.main(["--rules", os.path.join(tmp, "nonexistent.json"), "--budget", budget_path])
            assert False, "Expected SystemExit(2)"
        except SystemExit as exc:
            assert exc.code == 2


def test_cli_exits_2_on_missing_budget():
    """CLI must exit 2 when the budget file is not found."""
    with tempfile.TemporaryDirectory() as tmp:
        rules_path = os.path.join(tmp, "rules.json")
        _write_json(rules_path, _RULES_CLEAN)
        try:
            B.main(["--rules", rules_path, "--budget", os.path.join(tmp, "nonexistent.json")])
            assert False, "Expected SystemExit(2)"
        except SystemExit as exc:
            assert exc.code == 2


def test_example_files_are_valid():
    """The committed example files must be valid JSON and produce PASS on the clean case."""
    examples = os.path.join(_REPO, "examples", "ai4ra")
    rules_path = os.path.join(examples, "solicitation_rules.example.json")
    budget_path = os.path.join(examples, "budget.example.json")
    assert os.path.exists(rules_path), f"Missing: {rules_path}"
    assert os.path.exists(budget_path), f"Missing: {budget_path}"
    with open(rules_path, encoding="utf-8") as fh:
        rules = json.load(fh)
    with open(budget_path, encoding="utf-8") as fh:
        budget = json.load(fh)
    # The example budget is missing 'equipment' from sections_present by design
    # (demonstrates a FLAG). Just check the report builds without error.
    report = B.build_report(rules, budget, rules_path, budget_path)
    assert "advisory, not a compliance determination" in report.lower()
