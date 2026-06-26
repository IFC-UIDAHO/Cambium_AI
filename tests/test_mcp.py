import os, sys, asyncio, pytest
# Skip unless the real MCP SDK is importable (a bare local 'mcp' dir must NOT satisfy this).
pytest.importorskip("mcp.server.fastmcp")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "mcp_server"))
from cambium_mcp import server as S

def test_tools_registered():
    names = {t.name for t in asyncio.run(S.mcp.list_tools())}
    assert {"cambium_plan","cambium_provision","cambium_agents","cambium_doctor","cambium_grade","cambium_validate"} <= names

def test_plan_software():
    assert S.cambium_plan("build a web app")["type"] == "software"

def test_validate_blocks_fake():
    bad = "id,issue,agents,severity,claim_tier,evidence,status\nF1,x,a,P2,Code-verified,no command,closed"
    assert S.cambium_validate(bad)["ok"] is False
