"""Lock the three formerly-idle Support agents into routed plans, and check the Learning Brief exists."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
import task_router as T

def _agents_for(task):
    return {a for p in T.route(task)["phases"] for g in p["groups"] for a in g["agents"]}

def test_teaching_assistant_fires_on_build_and_analysis():
    assert "teaching-assistant" in _agents_for("build a machine learning model and backend api")
    assert "teaching-assistant" in _agents_for("clean and analyze this dataset")

def test_office_manager_and_feedback_router_fire_every_run():
    for task in ("draft an nsf proposal", "write the quarterly report", "research soil carbon"):
        ag = _agents_for(task)
        assert "office-manager" in ag and "feedback-router" in ag

def test_learn_phase_present_for_software():
    ids = [p["id"] for p in T.route("build a backend api")["phases"]]
    assert "learn" in ids

def test_learning_brief_template_exists():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    assert os.path.exists(os.path.join(root, "templates", "LEARNING_BRIEF.md"))
