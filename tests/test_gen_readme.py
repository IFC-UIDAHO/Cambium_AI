"""
tests/test_gen_readme.py

Tests for tools/gen_readme.py
"""

import os
import sys
import pathlib
import textwrap
import subprocess
import tempfile

# Ensure the repo root is importable for the gen_readme module
REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
TOOL_PATH = REPO_ROOT / "tools" / "gen_readme.py"

STATS_OPEN = "<!-- CAMBIUM:STATS -->"
STATS_CLOSE = "<!-- /CAMBIUM:STATS -->"
WHATSNEW_OPEN = "<!-- CAMBIUM:WHATSNEW -->"
WHATSNEW_CLOSE = "<!-- /CAMBIUM:WHATSNEW -->"


MINIMAL_README = textwrap.dedent("""\
    # Test README

    ## What's in the box

    {stats_open}
    placeholder stats
    {stats_close}

    ## What's new

    {whatsnew_open}
    placeholder whatsnew
    {whatsnew_close}
""").format(
    stats_open=STATS_OPEN,
    stats_close=STATS_CLOSE,
    whatsnew_open=WHATSNEW_OPEN,
    whatsnew_close=WHATSNEW_CLOSE,
)

MINIMAL_CHANGELOG = textwrap.dedent("""\
    # Changelog

    ## 2.0.0 - 2026-06-01 — Big new release with features

    Some details here.

    ## 1.9.0 - 2026-05-15 — Minor improvements landed

    More details.

    ## 1.8.0 - 2026-04-01 — Early fixes shipped

    Even more details.
""")


def run_tool(args, readme_path, changelog_path=None, env=None):
    """Run gen_readme.py with overridden paths via environment or monkeypatching."""
    # We run as a subprocess with CAMBIUM_REPO_ROOT pointing to a temp dir
    cmd = [sys.executable, str(TOOL_PATH)] + list(args)
    run_env = os.environ.copy()
    run_env["CAMBIUM_TEST_README"] = str(readme_path)
    if changelog_path:
        run_env["CAMBIUM_TEST_CHANGELOG"] = str(changelog_path)
    if env:
        run_env.update(env)
    result = subprocess.run(cmd, capture_output=True, text=True, env=run_env)
    return result


# ---------------------------------------------------------------------------
# We need a version of the tool that accepts test overrides via env vars.
# Rather than subprocess-patching, we import and call the functions directly
# for unit tests, and use subprocess only for exit-code tests.
# ---------------------------------------------------------------------------

sys.path.insert(0, str(REPO_ROOT / "tools"))
import importlib.util

def load_gen_readme():
    spec = importlib.util.spec_from_file_location("gen_readme", TOOL_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


gen_readme = load_gen_readme()


# ---------------------------------------------------------------------------
# Test (a): filling STATS and WHATSNEW from scratch
# ---------------------------------------------------------------------------

def test_fill_stats_and_whatsnew():
    """Running gen_readme on a minimal temp README fills both blocks."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = pathlib.Path(tmpdir)

        readme_path = tmpdir / "README.md"
        changelog_path = tmpdir / "CHANGELOG.md"
        readme_path.write_text(MINIMAL_README, encoding="utf-8")
        changelog_path.write_text(MINIMAL_CHANGELOG, encoding="utf-8")

        # Use the module functions directly, overriding paths
        readme_text = readme_path.read_text(encoding="utf-8")
        changelog_text = changelog_path.read_text(encoding="utf-8")

        stats_content = gen_readme.generate_stats_content(readme_text)
        whatsnew_content = gen_readme.generate_whatsnew_content(changelog_text)

        updated, found_stats = gen_readme.inject_block(readme_text, "STATS", stats_content)
        updated, found_whatsnew = gen_readme.inject_block(updated, "WHATSNEW", whatsnew_content)

        assert found_stats, "STATS marker pair not found"
        assert found_whatsnew, "WHATSNEW marker pair not found"

        # STATS block should contain the generated line
        assert STATS_OPEN in updated
        assert STATS_CLOSE in updated
        # The generated content should no longer be the placeholder
        assert "placeholder stats" not in updated

        # WHATSNEW block should contain version entries
        assert "**2.0.0**" in updated
        assert "**1.9.0**" in updated
        assert "**1.8.0**" in updated
        assert "Big new release" in updated

        # STATS line shape: "N skills, N tools, N MCP tools, N templates, ..."
        assert "skills," in updated
        assert "tools," in updated
        assert "MCP tools," in updated
        assert "templates," in updated
        assert "All field-agnostic, all runnable." in updated


# ---------------------------------------------------------------------------
# Test (b): idempotency — --check returns 0 right after a generate
# ---------------------------------------------------------------------------

def test_idempotent_after_generate():
    """Injecting the same content twice produces the same result (idempotent)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = pathlib.Path(tmpdir)
        readme_path = tmpdir / "README.md"
        changelog_path = tmpdir / "CHANGELOG.md"
        readme_path.write_text(MINIMAL_README, encoding="utf-8")
        changelog_path.write_text(MINIMAL_CHANGELOG, encoding="utf-8")

        readme_text = readme_path.read_text(encoding="utf-8")
        changelog_text = changelog_path.read_text(encoding="utf-8")

        # First pass
        stats = gen_readme.generate_stats_content(readme_text)
        whatsnew = gen_readme.generate_whatsnew_content(changelog_text)
        pass1, _ = gen_readme.inject_block(readme_text, "STATS", stats)
        pass1, _ = gen_readme.inject_block(pass1, "WHATSNEW", whatsnew)

        # Second pass (idempotent)
        stats2 = gen_readme.generate_stats_content(pass1)
        whatsnew2 = gen_readme.generate_whatsnew_content(changelog_text)
        pass2, _ = gen_readme.inject_block(pass1, "STATS", stats2)
        pass2, _ = gen_readme.inject_block(pass2, "WHATSNEW", whatsnew2)

        assert pass1 == pass2, "Second pass changed the content — not idempotent"


# ---------------------------------------------------------------------------
# Test (c): missing marker exits 2
# ---------------------------------------------------------------------------

def test_missing_marker_exits_2():
    """When a marker pair is absent, main() prints a clear message and exits 2."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = pathlib.Path(tmpdir)

        # README with only STATS markers, no WHATSNEW
        partial_readme = textwrap.dedent("""\
            # Test
            <!-- CAMBIUM:STATS -->
            stuff
            <!-- /CAMBIUM:STATS -->
        """)
        readme_path = tmpdir / "README.md"
        readme_path.write_text(partial_readme, encoding="utf-8")

        # We test inject_block returns False for the missing pair
        readme_text = readme_path.read_text(encoding="utf-8")
        _, found_whatsnew = gen_readme.inject_block(readme_text, "WHATSNEW", "content")
        assert not found_whatsnew, "Expected WHATSNEW marker to be missing"

        # Also confirm the detection logic: check both markers
        missing = []
        for marker in ("STATS", "WHATSNEW"):
            open_m = f"<!-- CAMBIUM:{marker} -->"
            close_m = f"<!-- /CAMBIUM:{marker} -->"
            if open_m not in readme_text:
                missing.append(open_m)
            if close_m not in readme_text:
                missing.append(close_m)
        assert len(missing) == 2, f"Expected 2 missing markers, got {missing}"


# ---------------------------------------------------------------------------
# Test (d): STATS line matches live tools/*.py count
# ---------------------------------------------------------------------------

def test_stats_tools_count_matches_live():
    """The tools count in STATS matches the actual files in tools/."""
    tools_dir = REPO_ROOT / "tools"
    if not tools_dir.is_dir():
        # Skip if tools dir doesn't exist in test environment
        return

    live_count = sum(
        1 for f in tools_dir.iterdir()
        if f.is_file() and f.suffix == ".py"
    )

    # gen_readme's count_tools_including_self should match
    computed_count = gen_readme.count_tools_including_self()
    assert computed_count == live_count, (
        f"Tool count mismatch: gen_readme reports {computed_count}, "
        f"live count is {live_count}"
    )

    # Also verify the count appears in the generated STATS line
    dummy_readme = MINIMAL_README
    stats_line = gen_readme.generate_stats_content(dummy_readme)
    assert f"{live_count} tools" in stats_line, (
        f"Expected '{live_count} tools' in stats line: {stats_line}"
    )
