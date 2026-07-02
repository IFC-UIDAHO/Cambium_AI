"""tests/test_agent_scaffold.py -- tests for tools/agent_scaffold.py"""
import importlib.util
import os
import re
import sys
import tempfile

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL_PATH = os.path.join(REPO_ROOT, "tools", "agent_scaffold.py")

sys.path.insert(0, os.path.join(REPO_ROOT, "tools"))


def _load():
    spec = importlib.util.spec_from_file_location("agent_scaffold", TOOL_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


agent_scaffold = _load()


def _parse_frontmatter(path):
    """Minimal, test-local YAML frontmatter reader (mirrors tools/check_agents.py)."""
    with open(path, encoding="utf-8") as fh:
        content = fh.read()
    assert content.startswith("---")
    rest = content[3:]
    end = rest.find("\n---")
    fm_block = rest[:end]
    data = {}
    for line in fm_block.splitlines():
        m = re.match(r"^(\w[\w-]*):\s*(.*)$", line)
        if m:
            data[m.group(1)] = m.group(2)
    return data


def test_agent_files_created_with_parseable_frontmatter_all_required_keys():
    with tempfile.TemporaryDirectory() as tmp:
        rc = agent_scaffold.main([
            "--kind", "agent", "--name", "my-test-agent",
            "--description", "Does test things.", "--council", "lab",
            "--model", "sonnet", "--dir", tmp,
        ])
        assert rc == 0
        dot_path = os.path.join(tmp, ".claude", "agents", "my-test-agent.md")
        plain_path = os.path.join(tmp, "agents", "my-test-agent.md")
        assert os.path.exists(dot_path)
        assert os.path.exists(plain_path)
        fm = _parse_frontmatter(dot_path)
        for key in ("name", "description", "model", "tools"):
            assert key in fm and fm[key].strip()
        assert fm["name"] == "my-test-agent"
        assert fm["model"] == "sonnet"


def test_dual_copies_identical():
    with tempfile.TemporaryDirectory() as tmp:
        rc = agent_scaffold.main([
            "--kind", "agent", "--name", "dual-copy-agent",
            "--description", "Dual copy check.", "--dir", tmp,
        ])
        assert rc == 0
        dot_path = os.path.join(tmp, ".claude", "agents", "dual-copy-agent.md")
        plain_path = os.path.join(tmp, "agents", "dual-copy-agent.md")
        with open(dot_path, encoding="utf-8") as fh:
            a = fh.read()
        with open(plain_path, encoding="utf-8") as fh:
            b = fh.read()
        assert a == b


def test_skill_frontmatter_valid():
    with tempfile.TemporaryDirectory() as tmp:
        rc = agent_scaffold.main([
            "--kind", "skill", "--name", "my-test-skill",
            "--description", "Does test skill things.", "--dir", tmp,
        ])
        assert rc == 0
        path = os.path.join(tmp, "skills", "my-test-skill", "SKILL.md")
        assert os.path.exists(path)
        fm = _parse_frontmatter(path)
        assert fm.get("name") == "my-test-skill"
        assert fm.get("description", "").strip()


def test_collision_exits_1():
    with tempfile.TemporaryDirectory() as tmp:
        args = ["--kind", "agent", "--name", "collide-agent",
                "--description", "First write.", "--dir", tmp]
        assert agent_scaffold.main(args) == 0
        assert agent_scaffold.main(args) == 1


def test_bad_model_value_exits_1():
    with tempfile.TemporaryDirectory() as tmp:
        rc = agent_scaffold.main([
            "--kind", "agent", "--name", "bad-model-agent",
            "--description", "Bad model.", "--model", "gpt5", "--dir", tmp,
        ])
        assert rc == 1
        assert not os.path.exists(os.path.join(tmp, ".claude", "agents", "bad-model-agent.md"))


def test_kebab_case_enforced():
    with tempfile.TemporaryDirectory() as tmp:
        for bad_name in ("Bad_Name", "bad name", "-bad", "bad-", "bad--name", "UPPER"):
            rc = agent_scaffold.main([
                "--kind", "skill", "--name", bad_name,
                "--description", "x", "--dir", tmp,
            ])
            assert rc == 1, f"expected rejection for {bad_name!r}"
        assert agent_scaffold.is_kebab_case("good-kebab-name")
        assert agent_scaffold.is_kebab_case("name123")
        assert not agent_scaffold.is_kebab_case("Name")
