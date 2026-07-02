"""tests/test_new_skill.py -- tests for tools/new_skill.py.

Scaffolds into tmp_path roots only; never writes into the real repo.
Frontmatter is checked line-based, matching how the repo's own skill
cards are written (their descriptions may contain colons).
"""
import pathlib
import subprocess
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
TOOL = REPO_ROOT / "tools" / "new_skill.py"

GOOD_DESC = "Plan and check forest inventory sampling designs, plot layouts, and expansion factors."
EM_DASH = "\u2014"


def run_tool(*args):
    return subprocess.run([sys.executable, str(TOOL), *args],
                          capture_output=True, text=True)


def scaffold(root, name="forest-inventory", desc=GOOD_DESC, extra=()):
    return run_tool("--name", name, "--description", desc, "--root", str(root), *extra)


def test_scaffold_writes_skill_with_frontmatter_and_sections(tmp_path):
    r = scaffold(tmp_path)
    assert r.returncode == 0, r.stderr
    skill = tmp_path / "skills" / "forest-inventory" / "SKILL.md"
    assert skill.is_file()
    text = skill.read_text(encoding="utf-8")
    lines = text.splitlines()
    assert lines[0] == "---"
    assert lines[1] == "name: forest-inventory"
    assert lines[2] == "description: " + GOOD_DESC
    for section in ("## What this does", "## When to use", "## How", "## Honest limits"):
        assert section in text
    assert EM_DASH not in text


def test_name_always_matches_directory(tmp_path):
    assert scaffold(tmp_path, name="soil-carbon").returncode == 0
    skill = tmp_path / "skills" / "soil-carbon" / "SKILL.md"
    name_line = skill.read_text(encoding="utf-8").splitlines()[1]
    assert name_line == "name: " + skill.parent.name


def test_rejects_short_description_and_writes_nothing(tmp_path):
    r = scaffold(tmp_path, desc="too short")
    assert r.returncode == 1
    assert "40" in r.stderr
    assert not (tmp_path / "skills").exists()


def test_rejects_em_dash_in_description(tmp_path):
    r = scaffold(tmp_path, desc="A perfectly long description " + EM_DASH + " with a forbidden dash inside it.")
    assert r.returncode == 1
    assert "em dash" in r.stderr.lower()


def test_rejects_non_kebab_name(tmp_path):
    r = scaffold(tmp_path, name="Forest Inventory")
    assert r.returncode == 1
    assert "kebab" in r.stderr.lower()


def test_refuses_overwrite_without_force_then_force_works(tmp_path):
    assert scaffold(tmp_path).returncode == 0
    again = scaffold(tmp_path)
    assert again.returncode == 1
    assert "force" in again.stderr.lower()
    assert scaffold(tmp_path, extra=("--force",)).returncode == 0


def test_help_exits_zero():
    r = run_tool("--help")
    assert r.returncode == 0
    assert "--description" in r.stdout
