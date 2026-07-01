#!/usr/bin/env python3
"""Tests for tools/checklist_builder.py.

Stdlib only. Runs the tool as a subprocess against tmp-dir fixtures, matching
its real CLI usage, and inspects the Markdown checklist it produces.
"""
from __future__ import annotations
import json
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = os.path.join(ROOT, "tools", "checklist_builder.py")


def run_tool(rules_path: str, out_path: str = None) -> subprocess.CompletedProcess:
    cmd = [sys.executable, TOOL, "--rules", rules_path]
    if out_path:
        cmd += ["--out", out_path]
    return subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)


def write_json(path: str, data: dict) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh)


class TestChecklistBuilder(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)
        self.rules_path = os.path.join(self.tmpdir.name, "rules.json")
        self.out_path = os.path.join(self.tmpdir.name, "checklist.md")

    def test_full_rules_produce_all_sections(self):
        rules = {
            "required_budget_sections": ["personnel", "equipment"],
            "disallowed_categories": ["alcohol", "lobbying"],
            "cost_share_required": True,
            "fa_rate_cap": 55,
            "total_cost_ceiling": 500000,
            "period_months_max": 36,
            "required_documents": ["project narrative", "biosketches"],
            "deadline": "2026-09-01",
        }
        write_json(self.rules_path, rules)

        result = run_tool(self.rules_path, self.out_path)
        self.assertEqual(result.returncode, 0, msg=result.stderr)

        with open(self.out_path, encoding="utf-8") as fh:
            checklist = fh.read()

        self.assertIn("Required documents", checklist)
        self.assertIn("project narrative", checklist)
        self.assertIn("Required budget sections", checklist)
        self.assertIn("personnel", checklist)
        self.assertIn("Limits to respect", checklist)
        self.assertIn("55", checklist)
        self.assertIn("500000", checklist)
        self.assertIn("36 months", checklist)
        self.assertIn("alcohol", checklist)
        self.assertIn("Cost-share", checklist)
        self.assertIn("cost-share commitment is included", checklist)
        self.assertIn("Deadline", checklist)
        self.assertIn("2026-09-01", checklist)
        self.assertIn("[ ]", checklist)
        self.assertNotIn("—", checklist)  # no em dashes

    def test_minimal_rules_flags_missing_optional_fields(self):
        rules = {
            "required_budget_sections": [],
            "disallowed_categories": [],
            "cost_share_required": False,
        }
        write_json(self.rules_path, rules)

        result = run_tool(self.rules_path, self.out_path)
        self.assertEqual(result.returncode, 0, msg=result.stderr)

        with open(self.out_path, encoding="utf-8") as fh:
            checklist = fh.read()

        self.assertIn("No required documents were listed", checklist)
        self.assertIn("No required budget sections were listed", checklist)
        self.assertIn("No numeric limits or disallowed categories were listed", checklist)
        self.assertIn("cost-share is not required", checklist)
        self.assertIn("No deadline was listed", checklist)
        self.assertNotIn("—", checklist)  # no em dashes

    def test_stdout_output_when_no_out_flag(self):
        rules = {
            "required_budget_sections": ["personnel"],
            "disallowed_categories": [],
            "cost_share_required": False,
        }
        write_json(self.rules_path, rules)

        result = run_tool(self.rules_path)
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("Submission checklist", result.stdout)
        self.assertNotIn("—", result.stdout)

    def test_missing_rules_file_exits_2(self):
        missing_path = os.path.join(self.tmpdir.name, "does_not_exist.json")
        result = run_tool(missing_path)
        self.assertEqual(result.returncode, 2)
        self.assertIn("not found", result.stderr)

    def test_no_em_dash_in_source(self):
        with open(TOOL, encoding="utf-8") as fh:
            source = fh.read()
        self.assertNotIn("—", source)


if __name__ == "__main__":
    unittest.main()
