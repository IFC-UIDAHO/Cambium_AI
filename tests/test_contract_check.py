"""tests/test_contract_check.py -- tests for tools/contract_check.py"""
import importlib.util
import json
import os
import sys
import tempfile

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL_PATH = os.path.join(REPO_ROOT, "tools", "contract_check.py")

sys.path.insert(0, os.path.join(REPO_ROOT, "tools"))


def _load():
    spec = importlib.util.spec_from_file_location("contract_check", TOOL_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


contract_check = _load()

_FAKE_SERVER = '''\
from mcp.server.fastmcp import FastMCP
mcp = FastMCP("x")

@mcp.tool()
def tool_one(a: str, b: int = 3) -> dict:
    """Docstring for tool_one."""
    return {}

@mcp.tool()
def tool_two() -> dict:
    """Docstring for tool_two."""
    return {}

def not_a_tool():
    return 1
'''


def test_extract_tools_finds_decorated_functions_only():
    tools = contract_check.extract_tools(_FAKE_SERVER)
    assert set(tools) == {"tool_one", "tool_two"}
    assert tools["tool_one"]["args"] == ["a", "b"]
    assert tools["tool_one"]["defaults"] == ["3"]
    assert tools["tool_one"]["has_docstring"] is True
    assert tools["tool_two"]["args"] == []


def test_current_server_matches_golden_after_update():
    with tempfile.TemporaryDirectory() as tmp:
        golden = os.path.join(tmp, "golden.json")
        rc_update = contract_check.main(["--golden", golden, "--update"])
        assert rc_update == 0
        assert os.path.exists(golden)
        rc_check = contract_check.main(["--golden", golden])
        assert rc_check == 0


def test_renamed_tool_causes_drift_exit_1():
    with tempfile.TemporaryDirectory() as tmp:
        server_path = os.path.join(tmp, "server.py")
        golden_path = os.path.join(tmp, "golden.json")
        with open(server_path, "w", encoding="utf-8") as fh:
            fh.write(_FAKE_SERVER)
        contract_check.main(["--server", server_path, "--golden", golden_path, "--update"])

        doctored = _FAKE_SERVER.replace("def tool_one", "def tool_one_renamed")
        with open(server_path, "w", encoding="utf-8") as fh:
            fh.write(doctored)

        rc = contract_check.main(["--server", server_path, "--golden", golden_path])
        assert rc == 1
        live = contract_check.extract_tools_from_file(server_path)
        golden = contract_check.load_golden(golden_path)
        diff = contract_check.diff_contracts(live, golden)
        assert "tool_one_renamed" in diff["added"]
        assert "tool_one" in diff["removed"]


def test_removed_tool_detected():
    with tempfile.TemporaryDirectory() as tmp:
        server_path = os.path.join(tmp, "server.py")
        golden_path = os.path.join(tmp, "golden.json")
        with open(server_path, "w", encoding="utf-8") as fh:
            fh.write(_FAKE_SERVER)
        contract_check.main(["--server", server_path, "--golden", golden_path, "--update"])

        shrunk = _FAKE_SERVER.replace(
            '@mcp.tool()\ndef tool_two() -> dict:\n    """Docstring for tool_two."""\n    return {}\n\n',
            "")
        with open(server_path, "w", encoding="utf-8") as fh:
            fh.write(shrunk)

        rc = contract_check.main(["--server", server_path, "--golden", golden_path])
        assert rc == 1
        live = contract_check.extract_tools_from_file(server_path)
        golden = contract_check.load_golden(golden_path)
        diff = contract_check.diff_contracts(live, golden)
        assert diff["removed"] == ["tool_two"]


def test_update_writes_valid_json():
    with tempfile.TemporaryDirectory() as tmp:
        server_path = os.path.join(tmp, "server.py")
        golden_path = os.path.join(tmp, "golden.json")
        with open(server_path, "w", encoding="utf-8") as fh:
            fh.write(_FAKE_SERVER)
        contract_check.main(["--server", server_path, "--golden", golden_path, "--update"])
        with open(golden_path, encoding="utf-8") as fh:
            data = json.load(fh)
        assert "tool_one" in data and "tool_two" in data


def test_docstring_presence_recorded_true_for_all_current_repo_tools():
    live = contract_check.extract_tools_from_file(contract_check.DEFAULT_SERVER)
    assert len(live) >= 1
    for name, sig in live.items():
        assert sig["has_docstring"] is True, f"{name} missing has_docstring True"


def test_argument_and_default_change_detected():
    with tempfile.TemporaryDirectory() as tmp:
        server_path = os.path.join(tmp, "server.py")
        golden_path = os.path.join(tmp, "golden.json")
        with open(server_path, "w", encoding="utf-8") as fh:
            fh.write(_FAKE_SERVER)
        contract_check.main(["--server", server_path, "--golden", golden_path, "--update"])

        changed = _FAKE_SERVER.replace("def tool_one(a: str, b: int = 3)", "def tool_one(a: str, b: int = 9)")
        with open(server_path, "w", encoding="utf-8") as fh:
            fh.write(changed)

        rc = contract_check.main(["--server", server_path, "--golden", golden_path])
        assert rc == 1
