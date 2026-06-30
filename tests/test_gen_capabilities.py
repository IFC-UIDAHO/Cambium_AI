"""tests/test_gen_capabilities.py

Tests for tools/gen_capabilities.py (7 tests per spec).

1. All six counts are positive integers.
2. capabilities.svg contains the live tools count.
3. adopted_ideas.json parses correctly and has the seven seeded rows.
4. adopted-ideas.svg contains a known source string.
5. --check exits 0 right after a fresh regen (idempotent).
6. No em dashes in the generated SVG output (neither file).
7. Individual count functions return int >= 0.
"""

import importlib.util
import json
import pathlib
import sys
import tempfile

# ---------------------------------------------------------------------------
# Load the module under test
# ---------------------------------------------------------------------------

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
TOOL_PATH = REPO_ROOT / "tools" / "gen_capabilities.py"

sys.path.insert(0, str(REPO_ROOT / "tools"))


def _load_gen_capabilities():
    spec = importlib.util.spec_from_file_location("gen_capabilities", TOOL_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


gc = _load_gen_capabilities()


# ---------------------------------------------------------------------------
# Test 1: all six counts are positive integers
# ---------------------------------------------------------------------------

def test_all_six_counts_are_positive_integers():
    counts = gc.compute_counts()
    assert isinstance(counts, dict), "compute_counts() must return a dict"
    expected_keys = {"agents", "councils", "gates", "tools", "skills", "tests"}
    assert expected_keys == set(counts.keys()), f"Unexpected keys: {counts.keys()}"
    for key, val in counts.items():
        assert isinstance(val, int), f"{key} count is not an int: {val!r}"
        assert val > 0, f"{key} count is not positive: {val}"


# ---------------------------------------------------------------------------
# Test 2: capabilities.svg contains the live tools count
# ---------------------------------------------------------------------------

def test_capabilities_svg_contains_live_tools_count():
    tools_count = gc.count_tools()
    assert isinstance(tools_count, int) and tools_count > 0

    counts = gc.compute_counts()
    svg = gc.render_capabilities_svg(counts)

    # The tools count must appear as a standalone integer in the SVG band
    assert str(tools_count) in svg, (
        f"Expected tools count {tools_count} to appear in the rendered capabilities SVG."
    )


# ---------------------------------------------------------------------------
# Test 3: adopted_ideas.json parses and has seven seeded rows
# ---------------------------------------------------------------------------

def test_adopted_ideas_json_parses_with_seven_rows():
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)
        tmp_json = tmp / "adopted_ideas.json"

        # Write seed data directly (bypasses relative_to issues in non-repo temp dirs)
        seed_data = json.dumps(gc.SEED_IDEAS, indent=2, ensure_ascii=False)
        tmp_json.write_text(seed_data, encoding="utf-8")

        original = gc.IDEAS_JSON
        gc.IDEAS_JSON = tmp_json
        try:
            ideas = gc.ensure_ideas_json()
        finally:
            gc.IDEAS_JSON = original

        assert isinstance(ideas, list), "adopted_ideas.json must be a JSON list"
        assert len(ideas) == 7, f"Expected 7 seeded rows, got {len(ideas)}"

        required_keys = {"source", "meta", "built", "note", "status"}
        for i, item in enumerate(ideas):
            missing = required_keys - set(item.keys())
            assert not missing, f"Row {i} missing keys: {missing}"
            assert item["status"] in {"adopted", "declined-heavy", "roadmap"}, (
                f"Row {i} has invalid status: {item['status']}"
            )


# ---------------------------------------------------------------------------
# Test 4: adopted-ideas.svg contains a known source string
# ---------------------------------------------------------------------------

def test_adopted_ideas_svg_contains_known_source():
    ideas = gc.SEED_IDEAS
    svg = gc.render_ideas_svg(ideas)
    # "Loop Engineering" must appear
    assert "Loop Engineering" in svg, (
        "Expected 'Loop Engineering' to appear in the rendered adopted-ideas SVG."
    )
    # "MindRouter" must appear
    assert "MindRouter" in svg, (
        "Expected 'MindRouter' to appear in the rendered adopted-ideas SVG."
    )
    # "GraphRAG" must appear
    assert "GraphRAG" in svg, (
        "Expected 'GraphRAG' to appear in the rendered adopted-ideas SVG."
    )


# ---------------------------------------------------------------------------
# Test 5: --check exits 0 right after a fresh regen
# ---------------------------------------------------------------------------

def test_check_exits_zero_after_regen():
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)

        # Create a mock assets dir
        assets_dir = tmp / "assets"
        assets_dir.mkdir()

        # Pre-write the JSON seed (avoids relative_to issue when seeding)
        tmp_json = assets_dir / "adopted_ideas.json"
        tmp_json.write_text(
            json.dumps(gc.SEED_IDEAS, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        # Patch module-level paths
        original_cap = gc.CAP_SVG
        original_ideas = gc.IDEAS_SVG
        original_json = gc.IDEAS_JSON
        original_assets = gc.ASSETS_DIR

        gc.ASSETS_DIR = assets_dir
        gc.CAP_SVG = assets_dir / "capabilities.svg"
        gc.IDEAS_SVG = assets_dir / "adopted-ideas.svg"
        gc.IDEAS_JSON = tmp_json

        try:
            # Regen
            counts = gc.compute_counts()
            ideas = gc.ensure_ideas_json()

            cap_content = gc.render_capabilities_svg(counts)
            ideas_content = gc.render_ideas_svg(ideas)

            gc.CAP_SVG.write_text(cap_content, encoding="utf-8")
            gc.IDEAS_SVG.write_text(ideas_content, encoding="utf-8")

            # Now --check must return 0
            result = gc.check_mode()
            assert result == 0, f"--check returned {result} after fresh regen (expected 0)"
        finally:
            gc.CAP_SVG = original_cap
            gc.IDEAS_SVG = original_ideas
            gc.IDEAS_JSON = original_json
            gc.ASSETS_DIR = original_assets


# ---------------------------------------------------------------------------
# Test 6: no em dashes in the generated output
# ---------------------------------------------------------------------------

def test_no_em_dashes_in_generated_svgs():
    counts = gc.compute_counts()
    cap_svg = gc.render_capabilities_svg(counts)
    ideas_svg = gc.render_ideas_svg(gc.SEED_IDEAS)

    EM_DASH = "—"
    assert EM_DASH not in cap_svg, (
        "Em dash found in capabilities.svg output -- replace with hyphen."
    )
    assert EM_DASH not in ideas_svg, (
        "Em dash found in adopted-ideas.svg output -- replace with hyphen."
    )


# ---------------------------------------------------------------------------
# Test 7: individual count functions return int >= 0
# ---------------------------------------------------------------------------

def test_individual_count_functions_return_int():
    for fn_name in ("count_agents", "count_councils", "count_gates",
                    "count_tools", "count_skills", "count_tests"):
        fn = getattr(gc, fn_name)
        result = fn()
        assert isinstance(result, int), f"{fn_name}() must return int, got {type(result)}"
        assert result >= 0, f"{fn_name}() must be non-negative, got {result}"
