"""tests/test_env_doctor.py -- tests for tools/env_doctor.py.

The default run uses this repo's own requirement files (offline, read-only);
fixture roots in tmp_path exercise drift reporting and missing files.
The exit-code rule is unit-tested by importing the module directly.
"""
import importlib.util
import pathlib
import subprocess
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
TOOL = REPO_ROOT / "tools" / "env_doctor.py"


def run_tool(*args):
    return subprocess.run([sys.executable, str(TOOL), *args],
                          capture_output=True, text=True)


def load_module():
    sys.path.insert(0, str(REPO_ROOT / "tools"))
    try:
        spec = importlib.util.spec_from_file_location("env_doctor", TOOL)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    finally:
        sys.path.pop(0)


def test_real_environment_passes_hard_checks():
    # This test suite itself needs python>=3.10, yaml and pytest, so the
    # hard rows must be ok here and the tool must exit 0.
    r = run_tool()
    assert r.returncode == 0, r.stdout + r.stderr
    assert "== env_doctor" in r.stdout
    assert " python " in r.stdout.replace("python", " python ", 1)
    assert "0 fail" in r.stdout


def test_constraint_drift_is_warn_not_fail(tmp_path):
    (tmp_path / "constraints.txt").write_text("pytest==0.0.1\n", encoding="utf-8")
    r = run_tool("--root", str(tmp_path))
    assert r.returncode == 0
    assert "drift" in r.stdout
    assert "0.0.1" in r.stdout


def test_missing_requirement_files_reported_not_fatal(tmp_path):
    r = run_tool("--root", str(tmp_path))
    assert r.returncode == 0
    assert "missing under --root" in r.stdout


def test_git_row_present():
    r = run_tool()
    assert r.returncode == 0
    assert "git" in r.stdout


def test_exit_code_rule_hard_fail_vs_warn():
    mod = load_module()
    assert mod.exit_code([("FAIL", "python", "too old", "upgrade")]) == 1
    assert mod.exit_code([("warn", "git", "missing", "install"),
                          ("ok", "python", "3.12", "")]) == 0


def test_pin_lookup_reads_requirement_files(tmp_path):
    mod = load_module()
    (tmp_path / "requirements.txt").write_text("pytest>=7.0\n# comment\n", encoding="utf-8")
    sources = {"requirements.txt": mod.read_requirements(str(tmp_path / "requirements.txt"))}
    spec, fname = mod.find_pin(sources, "pytest")
    assert spec == "pytest>=7.0"
    assert fname == "requirements.txt"


def test_help_exits_zero():
    r = run_tool("--help")
    assert r.returncode == 0
    assert "--root" in r.stdout
