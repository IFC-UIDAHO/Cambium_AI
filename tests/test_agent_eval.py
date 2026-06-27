"""Behavioral coverage: the bundled full-lifecycle trajectory must clear the
EVALS.md reliability floors. This turns the example into an integration fixture
and gives CI real agent-behavior coverage (not just frontmatter/schema checks).
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))
import agent_eval  # noqa: E402

TRAJ = os.path.join(os.path.dirname(__file__), "..", "examples", "full-lifecycle")


def test_example_trajectory_meets_floors():
    s = agent_eval.evaluate(TRAJ)
    assert s["passed"], "example trajectory below EVALS floors: " + "; ".join(s["failures"])


def test_gate_discipline_is_total():
    s = agent_eval.evaluate(TRAJ)
    assert s["gate_discipline"] == 1.0  # every required gate has a human approver


def test_no_open_p0():
    s = agent_eval.evaluate(TRAJ)
    assert s["open_p0"] == []


def test_code_verified_rows_cite_a_command():
    s = agent_eval.evaluate(TRAJ)
    assert s["tier_honesty"] >= agent_eval.FLOORS["tier_honesty"]


def test_floors_constant_matches_evals_doc():
    # Guardrail: if someone weakens a floor, this flags it for review.
    assert agent_eval.FLOORS == {
        "gate_discipline": 1.0,
        "citation_integrity": 1.0,
        "tier_honesty": 0.95,
        "faithfulness": 0.9,
    }
