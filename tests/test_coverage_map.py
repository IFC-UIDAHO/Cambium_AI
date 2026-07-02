"""tests/test_coverage_map.py -- tests for tools/coverage_map.py"""
import importlib.util
import os
import sys
import tempfile

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL_PATH = os.path.join(REPO_ROOT, "tools", "coverage_map.py")

sys.path.insert(0, os.path.join(REPO_ROOT, "tools"))


def _load():
    spec = importlib.util.spec_from_file_location("coverage_map", TOOL_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


coverage_map = _load()


def _write(path, content=""):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)


def _fake_tree(tools_dir, tests_dir):
    # covered via matching filename test_alpha.py
    _write(os.path.join(tools_dir, "alpha.py"), "# tool alpha\n")
    _write(os.path.join(tests_dir, "test_alpha.py"), "import alpha\n")
    # covered only via content grep inside an unrelated-named test file
    _write(os.path.join(tools_dir, "beta.py"), "# tool beta\n")
    _write(os.path.join(tests_dir, "test_bundle.py"), "import beta\nfrom beta import x\n")
    # not covered anywhere
    _write(os.path.join(tools_dir, "gamma.py"), "# tool gamma\n")
    # __init__.py must be excluded from the tool list
    _write(os.path.join(tools_dir, "__init__.py"), "")


def test_covered_via_filename():
    with tempfile.TemporaryDirectory() as tmp:
        tools_dir, tests_dir = os.path.join(tmp, "tools"), os.path.join(tmp, "tests")
        _fake_tree(tools_dir, tests_dir)
        report = coverage_map.build_report(tools_dir, tests_dir)
        row = next(r for r in report["rows"] if r["tool"] == "alpha")
        assert "test_alpha.py" in row["covered_by"]


def test_covered_via_content_grep():
    with tempfile.TemporaryDirectory() as tmp:
        tools_dir, tests_dir = os.path.join(tmp, "tools"), os.path.join(tmp, "tests")
        _fake_tree(tools_dir, tests_dir)
        report = coverage_map.build_report(tools_dir, tests_dir)
        row = next(r for r in report["rows"] if r["tool"] == "beta")
        assert "test_bundle.py" in row["covered_by"]


def test_missing_detected():
    with tempfile.TemporaryDirectory() as tmp:
        tools_dir, tests_dir = os.path.join(tmp, "tools"), os.path.join(tmp, "tests")
        _fake_tree(tools_dir, tests_dir)
        report = coverage_map.build_report(tools_dir, tests_dir)
        row = next(r for r in report["rows"] if r["tool"] == "gamma")
        assert row["covered_by"] == []
        tool_names = {r["tool"] for r in report["rows"]}
        assert "__init__" not in tool_names


def test_threshold_pass_and_fail_exit_codes():
    with tempfile.TemporaryDirectory() as tmp:
        tools_dir, tests_dir = os.path.join(tmp, "tools"), os.path.join(tmp, "tests")
        _fake_tree(tools_dir, tests_dir)
        # 2 of 3 tools covered = 66.7%
        rc_pass = coverage_map.main(["--tools-dir", tools_dir, "--tests-dir", tests_dir,
                                      "--min-coverage", "50"])
        assert rc_pass == 0
        rc_fail = coverage_map.main(["--tools-dir", tools_dir, "--tests-dir", tests_dir,
                                      "--min-coverage", "90"])
        assert rc_fail == 1


def test_percentage_math():
    with tempfile.TemporaryDirectory() as tmp:
        tools_dir, tests_dir = os.path.join(tmp, "tools"), os.path.join(tmp, "tests")
        _fake_tree(tools_dir, tests_dir)
        report = coverage_map.build_report(tools_dir, tests_dir)
        assert report["total"] == 3
        assert report["covered"] == 2
        assert report["missing"] == 1
        assert abs(report["percentage"] - (200.0 / 3)) < 0.1


def test_default_exit_0_regardless_of_coverage():
    with tempfile.TemporaryDirectory() as tmp:
        tools_dir, tests_dir = os.path.join(tmp, "tools"), os.path.join(tmp, "tests")
        _write(os.path.join(tools_dir, "uncovered.py"), "# nothing covers this\n")
        rc = coverage_map.main(["--tools-dir", tools_dir, "--tests-dir", tests_dir])
        assert rc == 0


# ---------------------------------------------------------------------------
# Integration test against the real repo (any coverage value; just must compute).
# ---------------------------------------------------------------------------

def test_real_repo_coverage_computes_and_checklist_builder_is_covered():
    report = coverage_map.build_report(coverage_map.DEFAULT_TOOLS_DIR, coverage_map.DEFAULT_TESTS_DIR)
    assert report["total"] > 0
    assert isinstance(report["percentage"], float)
    row = next((r for r in report["rows"] if r["tool"] == "checklist_builder"), None)
    assert row is not None, "checklist_builder.py not found in real tools/ tree"
    assert row["covered_by"], "checklist_builder should be covered by tests/test_checklist_builder.py"
