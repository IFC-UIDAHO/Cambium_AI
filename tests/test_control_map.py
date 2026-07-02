"""Tests for tools/control_map.py: NIST AI RMF 1.0 self-assessment matrix."""
import os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import control_map as CM


def run(*args):
    return subprocess.run([sys.executable, os.path.join(ROOT, "tools", "control_map.py"), *args],
                          capture_output=True, text=True)


def test_help_exits_0():
    r = run("--help")
    assert r.returncode == 0 and "self-assessment" in (r.stdout + r.stderr).lower()


def test_mapping_data_shape_and_real_pointers():
    per_func = {}
    for func, area, mech, pointer, status, note in CM.MAPPING:
        assert func in ("GOVERN", "MAP", "MEASURE", "MANAGE")
        assert status in CM.STATUSES
        per_func[func] = per_func.get(func, 0) + 1
        # every shipped pointer must be a real file in this repo
        assert os.path.exists(os.path.join(ROOT, pointer)), pointer
    assert set(per_func) == {"GOVERN", "MAP", "MEASURE", "MANAGE"}
    for func, n in per_func.items():
        assert 3 <= n <= 6, (func, n)


def test_real_repo_all_functions_and_disclaimer():
    r = run("--root", ROOT)
    assert r.returncode == 0, r.stdout + r.stderr
    for section in ("## GOVERN", "## MAP", "## MEASURE", "## MANAGE", "Honest gaps"):
        assert section in r.stdout
    assert "SELF-ASSESSMENT" in r.stdout
    assert "January 2023" in r.stdout
    assert "third-party" in r.stdout  # gaps name the missing external audit


def test_real_repo_strict_passes():
    r = run("--root", ROOT, "--strict")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "WARNING" not in r.stdout


def test_empty_root_downgrades_to_absent(tmp_path):
    r = run("--root", str(tmp_path))
    assert r.returncode == 0
    assert "WARNING" in r.stdout and "absent" in r.stdout
    assert "Missing evidence at this root" in r.stdout


def test_empty_root_strict_exits_1(tmp_path):
    r = run("--root", str(tmp_path), "--strict")
    assert r.returncode == 1


def test_out_file_written(tmp_path):
    out = tmp_path / "map.md"
    r = run("--root", ROOT, "--out", str(out))
    assert r.returncode == 0 and out.exists()
    assert "NIST AI RMF 1.0" in out.read_text(encoding="utf-8")
