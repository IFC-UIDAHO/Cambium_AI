import os, sys, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import task_router

def _roster():
    return {a["name"] for a in json.load(open(os.path.join(ROOT, "agent_cards.json")))["agents"]}

def test_every_cmap_agent_is_real():
    roster = _roster()
    phantom = sorted({a for ags in task_router.CMAP.values() for a in ags if a not in roster})
    assert not phantom, f"router references non-existent agents: {phantom}"

def test_org_chart_has_no_unknowns():
    svg = open(os.path.join(ROOT, "assets", "org-chart.svg"), encoding="utf-8").read()
    assert "(?)" not in svg, "org-chart.svg has unresolved agent names"
