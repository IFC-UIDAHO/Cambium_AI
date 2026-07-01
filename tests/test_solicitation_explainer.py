"""Tests for tools/solicitation_explainer.py.

Uses only stdlib and tmp dirs. Never touches the live repo data.
The explainer is a pure template renderer: same inputs produce same outputs.
"""
import os
import sys
import json
import tempfile

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_REPO, "tools"))

import solicitation_explainer as SE


_RULES_FULL = {
    "solicitation_id": "TEST-2026-001",
    "fa_rate_cap": 0.55,
    "total_cost_ceiling": 500000,
    "period_months_max": 36,
    "required_budget_sections": ["personnel", "fringe", "equipment", "travel", "indirect"],
    "disallowed_categories": ["alcohol", "entertainment"],
    "cost_share_required": True,
    "required_documents": ["project narrative", "budget justification", "biosketches"],
    "deadline": "2026-09-01",
}

_RULES_SPARSE = {
    "solicitation_id": "TEST-2026-002",
}


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def test_fmt_money_formats_thousands():
    assert SE._fmt_money(500000) == "$500,000"


def test_fmt_money_none_is_not_stated():
    assert SE._fmt_money(None) == "not stated"


def test_fmt_rate_formats_percent():
    assert SE._fmt_rate(0.55) == "55.0%"


def test_fmt_rate_none_is_not_stated():
    assert SE._fmt_rate(None) == "not stated"


def test_fmt_list_empty_is_none_stated():
    assert SE._fmt_list([]) == ["none stated"]
    assert SE._fmt_list(None) == ["none stated"]


def test_fmt_list_passthrough():
    assert SE._fmt_list(["a", "b"]) == ["a", "b"]


# ---------------------------------------------------------------------------
# Explainer content -- full rules
# ---------------------------------------------------------------------------

def test_explainer_contains_ceiling():
    report = SE.build_explainer(_RULES_FULL, "rules.json")
    assert "$500,000" in report


def test_explainer_contains_required_documents():
    report = SE.build_explainer(_RULES_FULL, "rules.json")
    assert "project narrative" in report
    assert "budget justification" in report
    assert "biosketches" in report


def test_explainer_contains_required_budget_sections():
    report = SE.build_explainer(_RULES_FULL, "rules.json")
    assert "personnel" in report
    assert "equipment" in report


def test_explainer_contains_disallowed_categories():
    report = SE.build_explainer(_RULES_FULL, "rules.json")
    assert "alcohol" in report
    assert "entertainment" in report


def test_explainer_contains_deadline():
    report = SE.build_explainer(_RULES_FULL, "rules.json")
    assert "2026-09-01" in report


def test_explainer_cost_share_required_is_stated():
    report = SE.build_explainer(_RULES_FULL, "rules.json")
    assert "cost share is required" in report.lower()


def test_explainer_contains_honest_header_and_closing():
    report = SE.build_explainer(_RULES_FULL, "rules.json")
    lowered = report.lower()
    assert "not a substitute for reading the actual solicitation" in lowered
    assert "plain-language summary" in lowered


def test_explainer_no_em_dashes():
    report = SE.build_explainer(_RULES_FULL, "rules.json")
    assert "—" not in report


# ---------------------------------------------------------------------------
# Explainer content -- sparse rules (missing fields)
# ---------------------------------------------------------------------------

def test_explainer_sparse_rules_notes_missing_fields():
    report = SE.build_explainer(_RULES_SPARSE, "rules.json")
    assert "not stated" in report.lower()
    assert "none stated" in report.lower()


def test_explainer_sparse_cost_share_defaults_not_required():
    report = SE.build_explainer(_RULES_SPARSE, "rules.json")
    assert "not required" in report.lower()


def test_explainer_sparse_no_em_dashes():
    report = SE.build_explainer(_RULES_SPARSE, "rules.json")
    assert "—" not in report


# ---------------------------------------------------------------------------
# CLI end-to-end
# ---------------------------------------------------------------------------

def _write_json(path, data):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh)


def test_cli_writes_explainer_file():
    with tempfile.TemporaryDirectory() as tmp:
        rules_path = os.path.join(tmp, "rules.json")
        out_path = os.path.join(tmp, "explainer.md")
        _write_json(rules_path, _RULES_FULL)
        rc = SE.main(["--rules", rules_path, "--out", out_path])
        assert rc == 0
        assert os.path.exists(out_path)
        content = open(out_path, encoding="utf-8").read()
        assert "$500,000" in content
        assert "project narrative" in content
        assert "—" not in content


def test_cli_exits_2_on_missing_rules():
    with tempfile.TemporaryDirectory() as tmp:
        try:
            SE.main(["--rules", os.path.join(tmp, "nonexistent.json")])
            assert False, "Expected SystemExit(2)"
        except SystemExit as exc:
            assert exc.code == 2


def test_cli_exits_2_on_invalid_json():
    with tempfile.TemporaryDirectory() as tmp:
        rules_path = os.path.join(tmp, "rules.json")
        with open(rules_path, "w", encoding="utf-8") as fh:
            fh.write("{not valid json")
        try:
            SE.main(["--rules", rules_path])
            assert False, "Expected SystemExit(2)"
        except SystemExit as exc:
            assert exc.code == 2
