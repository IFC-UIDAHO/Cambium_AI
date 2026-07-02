"""Tests for tools/subaward_consolidator.py.

Offline, deterministic, tmp_path only. Plain asserts.
"""
import os
import subprocess
import sys

import yaml

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_REPO, "tools"))

import subaward_consolidator as S

_TOOL = os.path.join(_REPO, "tools", "subaward_consolidator.py")


def _site(**overrides):
    site = {"name": "Prime U", "role": "prime", "direct_costs": [100000],
            "fna_rate": 0.5, "fna_base": "tdc"}
    site.update(overrides)
    return site


def _write(tmp_path, sites):
    p = tmp_path / "sites.yml"
    p.write_text(yaml.safe_dump({"sites": sites}), encoding="utf-8")
    return str(p)


def test_tdc_arithmetic():
    a = S.analyze({"sites": [_site()]})
    y1 = a["sites"][0]["per_year"][0]
    assert abs(y1["base"] - 100000.0) < 1e-6
    assert abs(y1["indirect"] - 50000.0) < 1e-6
    assert abs(y1["total"] - 150000.0) < 1e-6


def test_mtdc_exclusions_and_first25k_add_back():
    site = _site(fna_base="mtdc",
                 exclusions=[{"label": "equipment", "amounts": [20000]}],
                 first25k_amounts=[25000])
    a = S.analyze({"sites": [site]})
    y1 = a["sites"][0]["per_year"][0]
    assert abs(y1["base"] - 105000.0) < 1e-6  # 100000 - 20000 + 25000
    assert abs(y1["indirect"] - 52500.0) < 1e-6
    assert "first-25k add-back" in y1["arithmetic"]


def test_missing_rate_flags_and_indirect_zero():
    site = _site()
    del site["fna_rate"]
    a = S.analyze({"sites": [site]})
    assert any("fna_rate is missing" in f for f in a["flags"])
    assert a["sites"][0]["per_year"][0]["indirect"] == 0.0


def test_rate_over_100_percent_and_negative_direct_flag():
    sites = [_site(fna_rate=1.2),
             _site(name="Sub College", role="sub", direct_costs=[-5000], fna_rate=0.4)]
    a = S.analyze({"sites": sites})
    assert any("over 100 percent" in f for f in a["flags"])
    assert any("negative direct cost" in f for f in a["flags"])


def test_rollup_totals_across_sites():
    sites = [_site(),
             _site(name="Sub College", role="sub", direct_costs=[50000], fna_rate=0.4)]
    a = S.analyze({"sites": sites})
    y1 = a["rollup"]["per_year"][0]
    assert abs(y1["direct"] - 150000.0) < 1e-6
    assert abs(y1["indirect"] - 70000.0) < 1e-6   # 50000 + 20000
    assert abs(y1["total"] - 220000.0) < 1e-6
    assert abs(a["rollup"]["overall"]["total"] - 220000.0) < 1e-6


def test_sub_ceiling_flag_and_strict_exit(tmp_path):
    sites = [_site(),
             _site(name="Sub College", role="sub", direct_costs=[100000], fna_rate=0.5)]
    a = S.analyze({"sites": sites}, ceiling=100000)
    assert any("Sub College" in f and "ceiling" in f for f in a["flags"])
    path = _write(tmp_path, sites)
    out = str(tmp_path / "r.md")
    assert S.main(["--sites", path, "--out", out]) == 0
    assert S.main(["--sites", path, "--ceiling", "100000", "--out", out, "--strict"]) == 1


def test_report_shows_arithmetic_and_is_advisory(tmp_path):
    path = _write(tmp_path, [_site()])
    out = tmp_path / "r.md"
    assert S.main(["--sites", path, "--out", str(out)]) == 0
    text = out.read_text(encoding="utf-8")
    assert "base = 100000.00 (tdc)" in text
    assert "indirect = 100000.00 x 0.5000 = 50000.00" in text
    assert "advisory" in text.lower()
    assert "—" not in text


def test_help_exits_zero():
    proc = subprocess.run([sys.executable, _TOOL, "--help"],
                          capture_output=True, text=True)
    assert proc.returncode == 0
    assert "--ceiling" in proc.stdout
