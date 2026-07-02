"""tests/test_plugin_lint.py -- tests for tools/plugin_lint.py"""
import importlib.util
import json
import os
import sys
import tempfile

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL_PATH = os.path.join(REPO_ROOT, "tools", "plugin_lint.py")

sys.path.insert(0, os.path.join(REPO_ROOT, "tools"))


def _load():
    spec = importlib.util.spec_from_file_location("plugin_lint", TOOL_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


plugin_lint = _load()

_GOOD_AGENT = (
    "---\n"
    "name: {name}\n"
    "description: Does a thing.\n"
    "model: sonnet\n"
    "tools: Read, Write\n"
    "---\n"
    "Body text.\n"
)

_GOOD_SKILL = (
    "---\n"
    "name: {name}\n"
    "description: A useful skill.\n"
    "---\n"
    "\n# Skill body\n"
)


def _write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)


def _clean_plugin(tmp):
    _write(os.path.join(tmp, ".claude", "agents", "agent-a.md"), _GOOD_AGENT.format(name="agent-a"))
    _write(os.path.join(tmp, "agents", "agent-a.md"), _GOOD_AGENT.format(name="agent-a"))
    _write(os.path.join(tmp, "skills", "my-skill", "SKILL.md"), _GOOD_SKILL.format(name="my-skill"))
    _write(os.path.join(tmp, ".claude-plugin", "plugin.json"), json.dumps({"name": "x", "version": "1.2.3"}))
    return tmp


def test_clean_fixture_passes_exit_0():
    with tempfile.TemporaryDirectory() as tmp:
        _clean_plugin(tmp)
        rc = plugin_lint.main([tmp])
        assert rc == 0
        report = plugin_lint.lint(tmp)
        assert report["ok"] is True
        assert report["violations"] == []


def test_missing_description_caught():
    with tempfile.TemporaryDirectory() as tmp:
        _clean_plugin(tmp)
        bad = "---\nname: agent-b\nmodel: sonnet\ntools: Read\n---\nBody.\n"
        _write(os.path.join(tmp, ".claude", "agents", "agent-b.md"), bad)
        report = plugin_lint.lint(tmp)
        assert report["ok"] is False
        assert any("description" in v for v in report["violations"])


def test_bad_model_caught():
    with tempfile.TemporaryDirectory() as tmp:
        _clean_plugin(tmp)
        bad = "---\nname: agent-c\ndescription: x\nmodel: gpt5\ntools: Read\n---\nBody.\n"
        _write(os.path.join(tmp, ".claude", "agents", "agent-c.md"), bad)
        report = plugin_lint.lint(tmp)
        assert report["ok"] is False
        assert any("model" in v for v in report["violations"])


def test_duplicate_name_caught():
    with tempfile.TemporaryDirectory() as tmp:
        _clean_plugin(tmp)
        # A second agent file (different filename) reusing the same frontmatter name.
        _write(os.path.join(tmp, ".claude", "agents", "agent-a-dupe.md"),
               _GOOD_AGENT.format(name="agent-a"))
        report = plugin_lint.lint(tmp)
        assert report["ok"] is False
        assert any("duplicate" in v for v in report["violations"])


def test_broken_plugin_json_caught():
    with tempfile.TemporaryDirectory() as tmp:
        _clean_plugin(tmp)
        _write(os.path.join(tmp, ".claude-plugin", "plugin.json"), "{not valid json")
        report = plugin_lint.lint(tmp)
        assert report["ok"] is False
        assert any("plugin.json" in v for v in report["violations"])


def test_bad_semver_caught():
    with tempfile.TemporaryDirectory() as tmp:
        _clean_plugin(tmp)
        _write(os.path.join(tmp, ".claude-plugin", "plugin.json"), json.dumps({"version": "not-semver"}))
        report = plugin_lint.lint(tmp)
        assert report["ok"] is False
        assert any("semver" in v for v in report["violations"])


def test_empty_skill_description_caught():
    with tempfile.TemporaryDirectory() as tmp:
        _clean_plugin(tmp)
        _write(os.path.join(tmp, "skills", "empty-desc", "SKILL.md"),
               "---\nname: empty-desc\ndescription: \n---\nBody.\n")
        report = plugin_lint.lint(tmp)
        assert report["ok"] is False
        assert any("empty-desc" in v and "description" in v for v in report["violations"])


def test_json_output_is_valid_json():
    with tempfile.TemporaryDirectory() as tmp:
        _clean_plugin(tmp)
        report = plugin_lint.lint(tmp)
        text = json.dumps(report)
        parsed = json.loads(text)
        assert parsed["ok"] is True
