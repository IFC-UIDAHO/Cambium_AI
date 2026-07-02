"""Tests for tools/common_forms_check.py.

Offline, deterministic, tmp_path only. Plain asserts.
"""
import os
import subprocess
import sys

import yaml

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_REPO, "tools"))

import common_forms_check as C

_TOOL = os.path.join(_REPO, "tools", "common_forms_check.py")


def _person(**overrides):
    data = {
        "name": "Dr. Ada Example",
        "orcid": "0000-0002-1825-0097",
        "certified": True,
        "biosketch": {
            "products_related": ["paper one", "paper two"],
            "products_other": ["dataset"],
            "positions": ["Professor, Example University"],
            "education": ["PhD, Example Institute"],
        },
        "current_pending": [
            {"project": "P1", "sponsor": "NSF", "months": 1.5, "status": "current"},
        ],
    }
    data.update(overrides)
    return data


def _flags(rows):
    return [r for r in rows if r["result"] == "FLAG"]


def test_clean_person_all_pass():
    assert _flags(C.check_person(_person())) == []


def test_bad_or_missing_orcid_flags():
    bad = C.check_person(_person(orcid="1234-56"))
    missing = C.check_person(_person(orcid=None))
    assert any("ORCID" in r["check"] for r in _flags(bad))
    assert any("ORCID" in r["check"] for r in _flags(missing))


def test_products_related_over_limit_flags():
    p = _person()
    p["biosketch"]["products_related"] = ["a", "b", "c", "d", "e", "f"]
    rows = C.check_person(p)
    assert any("products_related" in r["check"] for r in _flags(rows))
    # five exactly is fine
    p["biosketch"]["products_related"] = ["a", "b", "c", "d", "e"]
    assert not any("products_related" in r["check"] for r in _flags(C.check_person(p)))


def test_uncertified_and_nonnumeric_months_flag():
    p = _person(certified=False)
    p["current_pending"][0]["months"] = "two"
    flagged_checks = " ".join(r["check"] for r in _flags(C.check_person(p)))
    assert "certified" in flagged_checks
    assert "months" in flagged_checks


def test_empty_required_section_flags():
    p = _person()
    p["biosketch"]["education"] = []
    rows = C.check_person(p)
    assert any("education" in r["check"] for r in _flags(rows))


def test_strict_exits_one_on_flags(tmp_path):
    src = tmp_path / "person.yml"
    src.write_text(yaml.safe_dump(_person(orcid="bad")), encoding="utf-8")
    out = tmp_path / "report.md"
    assert C.main(["--person", str(src), "--out", str(out)]) == 0
    assert C.main(["--person", str(src), "--out", str(out), "--strict"]) == 1


def test_report_mentions_sciencv_advisory_and_no_em_dash(tmp_path):
    src = tmp_path / "person.yml"
    src.write_text(yaml.safe_dump(_person()), encoding="utf-8")
    out = tmp_path / "report.md"
    assert C.main(["--person", str(src), "--out", str(out)]) == 0
    text = out.read_text(encoding="utf-8")
    assert "SciENcv" in text
    assert "advisory" in text.lower()
    assert "readiness" in text.lower()
    assert "—" not in text


def test_help_exits_zero():
    proc = subprocess.run([sys.executable, _TOOL, "--help"],
                          capture_output=True, text=True)
    assert proc.returncode == 0
    assert "--person" in proc.stdout
