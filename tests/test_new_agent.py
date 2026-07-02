"""tests/test_new_agent.py -- tests for tools/new_agent.py.

Scaffolds into tmp_path roots only; never writes into the real repo.
Runs the tool as a subprocess (like a user would) and validates the
generated frontmatter with strict YAML plus the repo's own validator.
"""
import pathlib
import subprocess
import sys

import yaml

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
TOOL = REPO_ROOT / "tools" / "new_agent.py"
CHECKER = REPO_ROOT / "tools" / "check_agents.py"

DESC = "Reviews soil sampling designs: protocols, depths, and lab QA."


def run_tool(*args):
    return subprocess.run([sys.executable, str(TOOL), *args],
                          capture_output=True, text=True)


def scaffold(root, name="soil-scientist", extra=()):
    return run_tool("--name", name, "--council", "Labs",
                    "--description", DESC, "--root", str(root), *extra)


def frontmatter(path):
    text = path.read_text(encoding="utf-8")
    return yaml.safe_load(text.split("---")[1])


def test_scaffold_writes_both_copies_with_required_fields(tmp_path):
    r = scaffold(tmp_path)
    assert r.returncode == 0, r.stderr
    card_a = tmp_path / "agents" / "soil-scientist.md"
    card_b = tmp_path / ".claude" / "agents" / "soil-scientist.md"
    assert card_a.is_file() and card_b.is_file()
    fm = frontmatter(card_a)
    assert fm["name"] == "soil-scientist"
    assert fm["description"] == DESC
    assert fm["model"] == "sonnet"
    assert fm["tools"] == "Read, Grep, Glob, Write"


def test_both_copies_are_byte_identical(tmp_path):
    assert scaffold(tmp_path).returncode == 0
    a = (tmp_path / "agents" / "soil-scientist.md").read_bytes()
    b = (tmp_path / ".claude" / "agents" / "soil-scientist.md").read_bytes()
    assert a == b


def test_refuses_overwrite_without_force_then_force_works(tmp_path):
    assert scaffold(tmp_path).returncode == 0
    again = scaffold(tmp_path)
    assert again.returncode == 1
    assert "force" in again.stderr.lower()
    forced = scaffold(tmp_path, extra=("--force",))
    assert forced.returncode == 0


def test_rejects_non_kebab_name(tmp_path):
    r = scaffold(tmp_path, name="Soil_Scientist")
    assert r.returncode == 1
    assert "kebab" in r.stderr.lower()
    assert not (tmp_path / "agents").exists()


def test_generated_card_passes_repo_validator(tmp_path):
    assert scaffold(tmp_path).returncode == 0
    r = subprocess.run(
        [sys.executable, str(CHECKER), str(tmp_path / ".claude" / "agents")],
        capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr


def test_opus_model_and_custom_tools_land_in_frontmatter(tmp_path):
    r = scaffold(tmp_path, extra=("--model", "opus", "--tools", "Read,Bash"))
    assert r.returncode == 0, r.stderr
    fm = frontmatter(tmp_path / "agents" / "soil-scientist.md")
    assert fm["model"] == "opus"
    assert fm["tools"] == "Read, Bash"


def test_help_exits_zero():
    r = run_tool("--help")
    assert r.returncode == 0
    assert "--council" in r.stdout
