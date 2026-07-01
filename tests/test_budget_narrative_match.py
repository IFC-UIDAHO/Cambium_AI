#!/usr/bin/env python3
"""Tests for tools/budget_narrative_match.py.

Stdlib only. Runs the tool as a subprocess against tmp-dir fixtures, matching
its real CLI usage, and inspects the Markdown report it produces.
"""
from __future__ import annotations
import json
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = os.path.join(ROOT, "tools", "budget_narrative_match.py")


def run_tool(budget_path: str, narrative_path: str, out_path: str = None) -> subprocess.CompletedProcess:
    cmd = [sys.executable, TOOL, "--budget", budget_path, "--narrative", narrative_path]
    if out_path:
        cmd += ["--out", out_path]
    return subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)


def write_json(path: str, data: dict) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh)


def write_text(path: str, text: str) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


class TestBudgetNarrativeMatch(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)
        self.budget_path = os.path.join(self.tmpdir.name, "budget.json")
        self.narrative_path = os.path.join(self.tmpdir.name, "narrative.txt")
        self.out_path = os.path.join(self.tmpdir.name, "report.md")

    def _budget(self):
        return {
            "totals": {"total": 150000},
            "line_items": [
                {"category": "personnel", "amount": 100000},
                {"category": "equipment", "amount": 50000},
            ],
            "fa_rate": 55,
            "period_months": 24,
            "sections_present": ["personnel", "equipment"],
        }

    def test_matching_case_all_pass(self):
        budget = self._budget()
        write_json(self.budget_path, budget)
        narrative = (
            "This proposal requests $100,000 for personnel and $50,000 for equipment. "
            "The F&A rate is 55 percent. The total project cost is $150,000 over the period."
        )
        write_text(self.narrative_path, narrative)

        result = run_tool(self.budget_path, self.narrative_path, self.out_path)
        self.assertEqual(result.returncode, 0, msg=result.stderr)

        with open(self.out_path, encoding="utf-8") as fh:
            report = fh.read()

        self.assertIn("must still reconcile", report)
        self.assertNotIn("**FLAG**", report)
        self.assertIn("PASS", report)
        self.assertNotIn("—", report)  # no em dashes

    def test_flag_case_missing_category_and_amount(self):
        budget = self._budget()
        write_json(self.budget_path, budget)
        # Narrative never mentions equipment or its amount, and states a
        # different F&A rate and total.
        narrative = (
            "This proposal requests $100,000 for personnel. "
            "The F&A rate is 40 percent. The total project cost is $120,000."
        )
        write_text(self.narrative_path, narrative)

        result = run_tool(self.budget_path, self.narrative_path, self.out_path)
        self.assertEqual(result.returncode, 0, msg=result.stderr)

        with open(self.out_path, encoding="utf-8") as fh:
            report = fh.read()

        self.assertIn("**FLAG**", report)
        self.assertIn("Category mentioned: equipment", report)
        self.assertIn("F&A rate", report)
        self.assertIn("Total stated in narrative matches budget", report)
        self.assertNotIn("—", report)  # no em dashes

    def test_stdout_output_when_no_out_flag(self):
        budget = self._budget()
        write_json(self.budget_path, budget)
        write_text(self.narrative_path, "Personnel $100,000. Equipment $50,000. F&A 55 percent. Total $150,000.")

        result = run_tool(self.budget_path, self.narrative_path)
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("Budget-to-narrative match", result.stdout)
        self.assertNotIn("—", result.stdout)

    def test_missing_budget_file_exits_2(self):
        write_text(self.narrative_path, "irrelevant")
        missing_path = os.path.join(self.tmpdir.name, "does_not_exist.json")
        result = run_tool(missing_path, self.narrative_path)
        self.assertEqual(result.returncode, 2)
        self.assertIn("not found", result.stderr)

    def test_no_em_dash_in_source(self):
        with open(TOOL, encoding="utf-8") as fh:
            source = fh.read()
        self.assertNotIn("—", source)


if __name__ == "__main__":
    unittest.main()
