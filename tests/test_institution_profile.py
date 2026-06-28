"""Tests for the institution profile validator."""
import os, sys
import pytest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
import institution_profile as IP

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXAMPLE = os.path.join(ROOT, "governance", "institution", "PROFILE.example.yml")
CASCADIA = os.path.join(ROOT, "governance", "institution", "PROFILE.cascadia_example.yml")

def test_files_exist():
    assert os.path.exists(EXAMPLE) and os.path.exists(CASCADIA)

def test_worked_example_validates_clean():
    pytest.importorskip("yaml")
    prof, problems = IP.validate(CASCADIA)
    assert prof is not None
    hard = [p for p in problems if not p.startswith("note:")]
    assert hard == []   # funders resolve, roster resolves, all sections present

def test_summary_mentions_institution():
    pytest.importorskip("yaml")
    prof, _ = IP.validate(CASCADIA)
    s = IP.summarize(prof)
    assert "Cascadia" in s and "approved funder" in s

def test_missing_section_is_flagged(tmp_path):
    pytest.importorskip("yaml")
    p = tmp_path / "bad.yml"
    p.write_text("institution:\n  name: X\napproved_funders: [NSF]\n", encoding="utf-8")
    prof, problems = IP.validate(str(p))
    assert any("missing required section" in x for x in problems)

def test_unknown_funder_is_flagged(tmp_path):
    pytest.importorskip("yaml")
    p = tmp_path / "bad2.yml"
    p.write_text("institution: {name: X}\napproved_funders: [MADE_UP_FUNDER]\n"
                 "data_handling: {}\nallowed_models: {}\nbudget: {per_project_cap_usd: 1}\n"
                 "approvers: {}\ngates: {}\npolicy: {}\n", encoding="utf-8")
    _, problems = IP.validate(str(p))
    assert any("no rule pack" in x for x in problems)
