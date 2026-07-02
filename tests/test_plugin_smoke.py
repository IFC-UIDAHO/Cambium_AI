"""tests/test_plugin_smoke.py -- tests for tools/plugin_smoke.py.

Builds tiny fixture repos in tmp_path for the failure modes, and runs the
real check against this repo itself (which must stay green).
"""
import json
import pathlib
import subprocess
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
TOOL = REPO_ROOT / "tools" / "plugin_smoke.py"


def run_tool(root):
    return subprocess.run([sys.executable, str(TOOL), "--root", str(root)],
                          capture_output=True, text=True)


def make_repo(root):
    """A minimal repo tree that passes every plugin_smoke check."""
    (root / ".claude-plugin").mkdir(parents=True)
    (root / ".claude-plugin" / "plugin.json").write_text(json.dumps({
        "name": "demo-plugin",
        "version": "1.2.3",
        "documentation": ["ROOT_DOC.md", "NESTED.md"],
    }), encoding="utf-8")
    (root / "pyproject.toml").write_text(
        '[project]\nname = "demo"\nversion = "1.2.3"\n', encoding="utf-8")
    (root / "mcp_server").mkdir()
    (root / "mcp_server" / "pyproject.toml").write_text(
        '[project]\nname = "demo-mcp"\nversion = "1.2.3"\n', encoding="utf-8")
    (root / "ROOT_DOC.md").write_text("at the root\n", encoding="utf-8")
    (root / "docs" / "sub").mkdir(parents=True)
    (root / "docs" / "sub" / "NESTED.md").write_text("nested under docs/\n", encoding="utf-8")
    for d in ("agents", ".claude/agents"):
        p = root / d
        p.mkdir(parents=True)
        (p / "librarian.md").write_text("---\nname: librarian\n---\nbody\n", encoding="utf-8")
    sd = root / "skills" / "demo-skill"
    sd.mkdir(parents=True)
    (sd / "SKILL.md").write_text(
        "---\nname: demo-skill\ndescription: A demo skill: does one thing well.\n---\nbody\n",
        encoding="utf-8")
    return root


def test_green_fixture_passes(tmp_path):
    r = run_tool(make_repo(tmp_path))
    assert r.returncode == 0, r.stdout + r.stderr
    assert "0 failed" in r.stdout
    assert "NESTED.md -> " in r.stdout  # docs/ resolution is reported


def test_version_mismatch_fails(tmp_path):
    make_repo(tmp_path)
    (tmp_path / "mcp_server" / "pyproject.toml").write_text(
        '[project]\nversion = "9.9.9"\n', encoding="utf-8")
    r = run_tool(tmp_path)
    assert r.returncode == 1
    assert "FAIL" in r.stdout and "version-match" in r.stdout


def test_missing_documentation_entry_fails(tmp_path):
    make_repo(tmp_path)
    plugin = tmp_path / ".claude-plugin" / "plugin.json"
    data = json.loads(plugin.read_text(encoding="utf-8"))
    data["documentation"].append("DOES_NOT_EXIST.md")
    plugin.write_text(json.dumps(data), encoding="utf-8")
    r = run_tool(tmp_path)
    assert r.returncode == 1
    assert "DOES_NOT_EXIST.md" in r.stdout


def test_agents_out_of_sync_fails(tmp_path):
    make_repo(tmp_path)
    (tmp_path / "agents" / "extra.md").write_text("---\nname: extra\n---\n", encoding="utf-8")
    r = run_tool(tmp_path)
    assert r.returncode == 1
    assert "agents-mirrored" in r.stdout and "extra.md" in r.stdout


def test_skill_without_description_fails(tmp_path):
    make_repo(tmp_path)
    bad = tmp_path / "skills" / "bad-skill"
    bad.mkdir()
    (bad / "SKILL.md").write_text("---\nname: bad-skill\n---\nbody\n", encoding="utf-8")
    r = run_tool(tmp_path)
    assert r.returncode == 1
    assert "skills-frontmatter" in r.stdout and "bad-skill" in r.stdout


def test_second_plugin_json_fails(tmp_path):
    make_repo(tmp_path)
    (tmp_path / "stray").mkdir()
    (tmp_path / "stray" / "plugin.json").write_text("{}", encoding="utf-8")
    r = run_tool(tmp_path)
    assert r.returncode == 1
    assert "single-plugin-json" in r.stdout and "2 found" in r.stdout


def test_real_repo_is_green():
    r = run_tool(REPO_ROOT)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "0 failed" in r.stdout


def test_help_exits_zero():
    r = subprocess.run([sys.executable, str(TOOL), "--help"], capture_output=True, text=True)
    assert r.returncode == 0
    assert "--root" in r.stdout
