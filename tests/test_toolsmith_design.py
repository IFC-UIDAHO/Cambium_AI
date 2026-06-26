import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import toolsmith

def test_design_task_gets_design_skills_not_stats():
    m = toolsmith.manifest("redesign the brand logo and svg visual assets")
    assert m["type"] == "design"
    names = " ".join(x["name"] for x in m["recommended"]).lower()
    assert "brand-guidelines" in names and "canvas-design" in names
    assert "statsmodels" not in names  # the old wrong answer

def test_nondesign_unchanged():
    assert toolsmith.manifest("build a web app dashboard")["type"] == "software"
