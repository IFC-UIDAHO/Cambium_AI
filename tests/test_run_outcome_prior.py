"""Tests for tools/run_outcome_prior.py

All tests use tmp directories to avoid touching real repo state.
Standard-library only; no API calls.
"""
import os
import sys
import csv
import tempfile
import textwrap

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import run_outcome_prior as rop


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_cost_log(directory, rows, filename="cost_log.csv"):
    """Write a cost_log.csv with header + given rows to directory."""
    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, filename)
    header = ["run", "phase", "agent", "model", "input_tokens", "output_tokens", "wall_s", "est_usd"]
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        for r in rows:
            w.writerow(r)
    return path


def _make_gates_md(directory, entries):
    """
    Write governance/GATES.md with a fake approvals log.

    entries: list of (gate_id, decision_keyword) e.g. ("G1", "APPROVE")
    """
    gov_dir = os.path.join(directory, "governance")
    os.makedirs(gov_dir, exist_ok=True)
    path = os.path.join(gov_dir, "GATES.md")
    lines = [
        "# Human Approval Ledger",
        "",
        "## Approvals log",
        "| Date | Gate | Run | Decision | Approver |",
        "|---|---|---|---|---|",
    ]
    for gid, decision in entries:
        lines.append("| 2026-01-01 | %s | test-run | %s | Director |" % (gid, decision))
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    return path


# ---------------------------------------------------------------------------
# Cost tests
# ---------------------------------------------------------------------------

class TestCostWithHistory:
    """With crafted cost_log history, cost uses history and is in a sane range."""

    def test_uses_history_not_price_table(self):
        with tempfile.TemporaryDirectory() as tmp:
            ao = os.path.join(tmp, "agent_outputs")
            _make_cost_log(
                ao,
                [
                    ["r1", "scout", "scout-prior-art", "claude-sonnet-4-6", 2000, 800, 1.5, "0.018"],
                    ["r1", "scout", "scout-methods",   "claude-sonnet-4-6", 2000, 800, 1.4, "0.018"],
                    ["r1", "lab",   "lab-theory",      "claude-sonnet-4-6", 2000, 800, 1.6, "0.018"],
                ],
            )
            # Craft a minimal plan with 6 agent slots
            plan = {
                "task": "test task",
                "type": "research",
                "n_agents": 6,
                "phases": [
                    {"id": "scout", "groups": [
                        {"label": "scouts", "parallel": True, "agents": ["a", "b", "c"]},
                    ], "gate": None},
                    {"id": "build", "groups": [
                        {"label": "labs", "parallel": True, "agents": ["d", "e", "f"]},
                    ], "gate": None},
                ],
            }
            result = rop.predict(plan, root=tmp)
            cost = result["predicted_cost_usd"]
            assert cost["calibrated"] is True, "should be calibrated from history"
            # avg per agent = 0.018; 6 agents => point = 0.108
            assert abs(cost["point"] - 0.018 * 6) < 1e-6
            assert cost["low"] < cost["point"] < cost["high"]
            assert "historical" in result["basis"]["cost"]

    def test_range_brackets_point(self):
        with tempfile.TemporaryDirectory() as tmp:
            ao = os.path.join(tmp, "agent_outputs")
            _make_cost_log(ao, [
                ["r1", "ph", "agentA", "claude-sonnet-4-6", 1000, 400, 1.0, "0.010"],
                ["r1", "ph", "agentB", "claude-sonnet-4-6", 1000, 400, 1.0, "0.020"],
            ])
            plan = {
                "task": "t",
                "type": "research",
                "n_agents": 2,
                "phases": [{"id": "p", "groups": [
                    {"label": "g", "parallel": True, "agents": ["agentA", "agentB"]}
                ], "gate": None}],
            }
            result = rop.predict(plan, root=tmp)
            c = result["predicted_cost_usd"]
            assert c["low"] < c["point"]
            assert c["point"] < c["high"]

    def test_top_level_cost_log_found(self):
        """cambium_run.py writes to agent_outputs/cost_log.csv at top level."""
        with tempfile.TemporaryDirectory() as tmp:
            ao = os.path.join(tmp, "agent_outputs")
            os.makedirs(ao)
            # Write directly at top level (not a subdirectory)
            path = os.path.join(ao, "cost_log.csv")
            with open(path, "w", newline="") as fh:
                w = csv.writer(fh)
                w.writerow(["run","phase","agent","model","input_tokens","output_tokens","wall_s","est_usd"])
                w.writerow(["r1","p","a","claude-sonnet-4-6",1000,400,1.0,"0.050"])
            plan = {
                "task": "t", "type": "research", "n_agents": 1,
                "phases": [{"id": "p", "groups": [
                    {"label": "g", "parallel": False, "agents": ["a"]}
                ], "gate": None}],
            }
            result = rop.predict(plan, root=tmp)
            assert result["predicted_cost_usd"]["calibrated"] is True
            assert abs(result["predicted_cost_usd"]["point"] - 0.050) < 1e-6


class TestCostFallback:
    """With no history, cost falls back to price table and is labeled uncalibrated."""

    def test_no_history_uncalibrated(self):
        with tempfile.TemporaryDirectory() as tmp:
            plan = {
                "task": "t", "type": "research", "n_agents": 3,
                "phases": [{"id": "p", "groups": [
                    {"label": "g", "parallel": True, "agents": ["a", "b", "c"]}
                ], "gate": None}],
            }
            result = rop.predict(plan, root=tmp)
            cost = result["predicted_cost_usd"]
            assert cost["calibrated"] is False
            assert "uncalibrated" in result["basis"]["cost"]
            assert cost["point"] > 0
            assert cost["low"] < cost["point"] < cost["high"]

    def test_uncalibrated_note_in_confidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            plan = {
                "task": "t", "type": "data", "n_agents": 2,
                "phases": [{"id": "p", "groups": [
                    {"label": "g", "parallel": False, "agents": ["a", "b"]}
                ], "gate": None}],
            }
            result = rop.predict(plan, root=tmp)
            assert "uncalibrated" in result["confidence"]


# ---------------------------------------------------------------------------
# Risk tests
# ---------------------------------------------------------------------------

class TestRiskWithSufficientHistory:
    """With >= 5 gates of known mix, risk maps correctly."""

    def test_all_approve_is_low(self):
        with tempfile.TemporaryDirectory() as tmp:
            entries = [("G%d" % i, "APPROVE") for i in range(8)]
            _make_gates_md(tmp, entries)
            result = rop.estimate_risk(tmp)
            assert result["risk_level"] == "low"
            assert result["revise_reject_rate"] == 0.0
            assert result["total_gates"] == 8

    def test_half_revise_is_high(self):
        with tempfile.TemporaryDirectory() as tmp:
            entries = (
                [("G%d" % i, "APPROVE") for i in range(3)] +
                [("G%d" % i, "REVISE")  for i in range(3, 9)]
            )
            _make_gates_md(tmp, entries)
            result = rop.estimate_risk(tmp)
            # 6/9 REVISE -> rate=0.667 -> high
            assert result["risk_level"] == "high"
            assert result["revise_reject_rate"] > 0.40

    def test_medium_band(self):
        with tempfile.TemporaryDirectory() as tmp:
            # 2 bad out of 10 = 0.20 -> medium
            entries = (
                [("G%d" % i, "APPROVE") for i in range(8)] +
                [("G%d" % i, "REVISE")  for i in range(8, 10)]
            )
            _make_gates_md(tmp, entries)
            result = rop.estimate_risk(tmp)
            assert result["risk_level"] == "medium"
            assert 0.15 <= result["revise_reject_rate"] <= 0.40

    def test_reject_counts_as_bad(self):
        with tempfile.TemporaryDirectory() as tmp:
            entries = (
                [("G%d" % i, "APPROVE") for i in range(5)] +
                [("G%d" % i, "REJECT")  for i in range(5, 10)]
            )
            _make_gates_md(tmp, entries)
            result = rop.estimate_risk(tmp)
            # 5/10 -> 0.5 -> high
            assert result["risk_level"] == "high"


class TestRiskInsufficientHistory:
    """With < 5 historical gates, risk must be 'unknown'."""

    def test_zero_gates_unknown(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = rop.estimate_risk(tmp)
            assert "unknown" in result["risk_level"]
            assert result["revise_reject_rate"] is None

    def test_four_gates_unknown(self):
        with tempfile.TemporaryDirectory() as tmp:
            entries = [("G%d" % i, "APPROVE") for i in range(4)]
            _make_gates_md(tmp, entries)
            result = rop.estimate_risk(tmp)
            assert "unknown" in result["risk_level"]
            assert result["total_gates"] == 4

    def test_exactly_five_gates_produces_level(self):
        with tempfile.TemporaryDirectory() as tmp:
            entries = [("G%d" % i, "APPROVE") for i in range(5)]
            _make_gates_md(tmp, entries)
            result = rop.estimate_risk(tmp)
            assert result["risk_level"] in ("low", "medium", "high")


# ---------------------------------------------------------------------------
# Never-raises contract
# ---------------------------------------------------------------------------

class TestNeverRaises:
    """predict() must not raise under adversarial or missing inputs."""

    def test_missing_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            nonexistent = os.path.join(tmp, "no_such_dir")
            result = rop.predict("build something", root=nonexistent)
            assert "predicted_cost_usd" in result
            assert "predicted_risk" in result

    def test_corrupted_cost_log(self):
        with tempfile.TemporaryDirectory() as tmp:
            ao = os.path.join(tmp, "agent_outputs")
            os.makedirs(ao)
            with open(os.path.join(ao, "cost_log.csv"), "w") as fh:
                fh.write("not,valid,csv\n!!!\x00garbage")
            plan = {
                "task": "t", "type": "research", "n_agents": 2,
                "phases": [{"id": "p", "groups": [
                    {"label": "g", "parallel": False, "agents": ["a", "b"]}
                ], "gate": None}],
            }
            result = rop.predict(plan, root=tmp)
            assert result["predicted_cost_usd"]["point"] >= 0

    def test_corrupted_gates_md(self):
        with tempfile.TemporaryDirectory() as tmp:
            gov = os.path.join(tmp, "governance")
            os.makedirs(gov)
            with open(os.path.join(gov, "GATES.md"), "w") as fh:
                fh.write("\x00\xff\xfe garbage binary-like content")
            result = rop.estimate_risk(tmp)
            assert "unknown" in result["risk_level"] or result["risk_level"] in ("low","medium","high")

    def test_task_string_routes_and_predicts(self):
        """predict() with a task string (not a plan) must not raise."""
        with tempfile.TemporaryDirectory() as tmp:
            result = rop.predict("write a research proposal on soil carbon", root=ROOT)
            assert "predicted_cost_usd" in result
            assert "predicted_risk" in result
            assert "confidence" in result

    def test_empty_plan(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = rop.predict({"task": "t", "type": "research", "n_agents": 0, "phases": []}, root=tmp)
            assert result["predicted_cost_usd"]["point"] >= 0


# ---------------------------------------------------------------------------
# predict() integration shape
# ---------------------------------------------------------------------------

class TestPredictShape:
    def test_full_output_keys(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = rop.predict("run some experiments", root=ROOT)
            for key in ("task", "plan_type", "n_agents", "predicted_cost_usd",
                        "predicted_risk", "basis", "confidence"):
                assert key in result, "missing key: %s" % key
            for sub in ("point", "low", "high", "calibrated"):
                assert sub in result["predicted_cost_usd"]
            assert "cost" in result["basis"] and "risk" in result["basis"]

    def test_honesty_note_always_in_confidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = rop.predict("grant proposal", root=tmp)
            assert "heuristic prior" in result["confidence"]
            assert "never blocks" in result["confidence"]
