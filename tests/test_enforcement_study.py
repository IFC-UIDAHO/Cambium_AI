"""tests/test_enforcement_study.py — Unit tests for the enforcement A/B study harness.

Tests:
  1. metrics.py pure functions with known inputs/outputs.
  2. Smoke test: run_study.py --demo produces results.csv with expected columns.
  3. Schema validation: all T*.json task files parse and contain required keys.
  4. No task file overlaps with examples/full-lifecycle (circularity rule).
  5. Edge cases: empty verdicts, sentinel handling, zero-division safety.

Run with: pytest tests/test_enforcement_study.py -v
"""
import csv
import json
import os
import subprocess
import sys
import tempfile

import pytest

# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVALS_DIR = os.path.join(ROOT, "evals", "enforcement_study")
TASKS_DIR = os.path.join(EVALS_DIR, "tasks")
FIXTURES_DIR = os.path.join(EVALS_DIR, "fixtures")

# Import metrics directly
sys.path.insert(0, ROOT)
from evals.enforcement_study.metrics import (
    false_claim_rate,
    over_claim_rate,
    citation_integrity,
    reproducibility_rate,
    compute_all,
)

# ---------------------------------------------------------------------------
# 1. false_claim_rate unit tests
# ---------------------------------------------------------------------------

class TestFalseClaimRate:
    def test_all_caught(self):
        """All defects caught => FCR = 0.0"""
        verdicts = [
            {"defect_id": "D1", "caught": True},
            {"defect_id": "D2", "caught": True},
        ]
        rate, n, d = false_claim_rate(verdicts, total_seeded_false_claims=2)
        assert rate == 0.0
        assert n == 0
        assert d == 2

    def test_all_missed(self):
        """No verdicts provided (no catches) => FCR = 1.0"""
        rate, n, d = false_claim_rate([], total_seeded_false_claims=3)
        assert rate == 1.0
        assert n == 3
        assert d == 3

    def test_half_caught(self):
        """Half caught => FCR = 0.5"""
        verdicts = [
            {"defect_id": "D1", "caught": True},
            {"defect_id": "D2", "caught": False},
        ]
        rate, n, d = false_claim_rate(verdicts, total_seeded_false_claims=2)
        assert rate == 0.5
        assert n == 1
        assert d == 2

    def test_one_caught_of_one(self):
        """Single defect caught => FCR = 0.0"""
        rate, n, d = false_claim_rate(
            [{"defect_id": "D1", "caught": True}], total_seeded_false_claims=1
        )
        assert rate == 0.0
        assert n == 0

    def test_invalid_denominator_raises(self):
        """Denominator < 1 must raise ValueError."""
        with pytest.raises(ValueError):
            false_claim_rate([], total_seeded_false_claims=0)

    def test_caught_count_clamps_at_zero_missed(self):
        """More caught than seeded (scoring error) should not produce negative missed."""
        # 2 caught verdicts but only 1 seeded — missed clamped to 0
        verdicts = [
            {"defect_id": "D1", "caught": True},
            {"defect_id": "D2", "caught": True},
        ]
        rate, n, d = false_claim_rate(verdicts, total_seeded_false_claims=1)
        assert n == 0
        assert rate == 0.0


# ---------------------------------------------------------------------------
# 2. over_claim_rate unit tests
# ---------------------------------------------------------------------------

class TestOverClaimRate:
    def test_no_verdicts(self):
        """Empty verdicts => (0.0, 0, 0)"""
        rate, n, d = over_claim_rate([])
        assert rate == 0.0
        assert n == 0
        assert d == 0

    def test_all_over_claimed(self):
        verdicts = [
            {"ledger_row_id": "R1", "warranted_tier": "Open",
             "actual_tier": "Proved", "over_claimed": True},
            {"ledger_row_id": "R2", "warranted_tier": "Asserted",
             "actual_tier": "Code-verified", "over_claimed": True},
        ]
        rate, n, d = over_claim_rate(verdicts)
        assert rate == 1.0
        assert n == 2
        assert d == 2

    def test_none_over_claimed(self):
        verdicts = [
            {"ledger_row_id": "R1", "warranted_tier": "Asserted",
             "actual_tier": "Asserted", "over_claimed": False},
        ]
        rate, n, d = over_claim_rate(verdicts)
        assert rate == 0.0
        assert n == 0
        assert d == 1

    def test_half_over_claimed(self):
        verdicts = [
            {"ledger_row_id": "R1", "over_claimed": True},
            {"ledger_row_id": "R2", "over_claimed": False},
        ]
        rate, n, d = over_claim_rate(verdicts)
        assert rate == 0.5
        assert n == 1
        assert d == 2


# ---------------------------------------------------------------------------
# 3. citation_integrity unit tests
# ---------------------------------------------------------------------------

class TestCitationIntegrity:
    def test_no_citations(self):
        """No citations => (1.0, 0, 0)"""
        rate, n, d = citation_integrity([])
        assert rate == 1.0
        assert n == 0
        assert d == 0

    def test_all_resolve(self):
        verdicts = [
            {"citation_text": "Smith 2024", "resolves": True},
            {"citation_text": "Jones 2020", "resolves": True},
        ]
        rate, n, d = citation_integrity(verdicts)
        assert rate == 1.0
        assert n == 2
        assert d == 2

    def test_none_resolve(self):
        verdicts = [
            {"citation_text": "Fake 2099", "resolves": False},
        ]
        rate, n, d = citation_integrity(verdicts)
        assert rate == 0.0
        assert n == 0
        assert d == 1

    def test_half_resolve(self):
        verdicts = [
            {"citation_text": "Good 2020", "resolves": True},
            {"citation_text": "Bad 2024", "resolves": False},
        ]
        rate, n, d = citation_integrity(verdicts)
        assert rate == 0.5
        assert n == 1
        assert d == 2


# ---------------------------------------------------------------------------
# 4. reproducibility_rate unit tests
# ---------------------------------------------------------------------------

class TestReproducibilityRate:
    def test_no_claims(self):
        """No numeric claims => (1.0, 0, 0)"""
        rate, n, d = reproducibility_rate([])
        assert rate == 1.0
        assert n == 0
        assert d == 0

    def test_all_reproducible(self):
        verdicts = [
            {"claim_text": "x=5", "reproducible": True},
            {"claim_text": "y=10", "reproducible": True},
        ]
        rate, n, d = reproducibility_rate(verdicts)
        assert rate == 1.0
        assert n == 2
        assert d == 2

    def test_none_reproducible(self):
        verdicts = [
            {"claim_text": "x=999", "reproducible": False},
        ]
        rate, n, d = reproducibility_rate(verdicts)
        assert rate == 0.0
        assert n == 0
        assert d == 1

    def test_half_reproducible(self):
        verdicts = [
            {"claim_text": "good=5", "reproducible": True},
            {"claim_text": "bad=999", "reproducible": False},
        ]
        rate, n, d = reproducibility_rate(verdicts)
        assert rate == 0.5
        assert n == 1
        assert d == 2


# ---------------------------------------------------------------------------
# 5. compute_all integration test
# ---------------------------------------------------------------------------

class TestComputeAll:
    def _make_verdict(self, task_id="T001", arm="TREATMENT"):
        return {
            "task_id": task_id,
            "arm": arm,
            "false_claim_verdicts": [
                {"defect_id": "D1", "caught": True},
                {"defect_id": "D2", "caught": False},
            ],
            "over_claim_verdicts": [
                {"ledger_row_id": "R1", "warranted_tier": "Asserted",
                 "actual_tier": "Code-verified", "over_claimed": True},
            ],
            "citation_verdicts": [
                {"citation_text": "Smith 2024", "resolves": False},
                {"citation_text": "Jones 2020", "resolves": True},
            ],
            "reproducibility_verdicts": [
                {"claim_text": "x=5", "reproducible": True},
            ],
        }

    def _make_gt(self, n_false_claims=2):
        return {"false_claims_to_catch": [f"claim_{i}" for i in range(n_false_claims)]}

    def test_known_outputs(self):
        result = compute_all(self._make_verdict(), self._make_gt(2))
        assert result["false_claim_rate"] == 0.5
        assert result["over_claim_rate"] == 1.0
        assert result["citation_integrity"] == 0.5
        assert result["reproducibility_rate"] == 1.0
        assert result["task_id"] == "T001"
        assert result["arm"] == "TREATMENT"

    def test_sentinel_when_no_seeded_claims(self):
        """FCR = -1.0 when no false claims are seeded."""
        result = compute_all(self._make_verdict(), self._make_gt(0))
        assert result["false_claim_rate"] == -1.0
        assert result["fcr_n"] == 0
        assert result["fcr_d"] == 0

    def test_perfect_treatment(self):
        """All-caught, all-resolved, no over-claims, all reproducible => perfect scores."""
        verdict = {
            "task_id": "T001",
            "arm": "TREATMENT",
            "false_claim_verdicts": [{"defect_id": "D1", "caught": True}],
            "over_claim_verdicts": [
                {"ledger_row_id": "R1", "over_claimed": False}
            ],
            "citation_verdicts": [{"citation_text": "Good 2020", "resolves": True}],
            "reproducibility_verdicts": [{"claim_text": "x=5", "reproducible": True}],
        }
        result = compute_all(verdict, {"false_claims_to_catch": ["claim_a"]})
        assert result["false_claim_rate"] == 0.0
        assert result["over_claim_rate"] == 0.0
        assert result["citation_integrity"] == 1.0
        assert result["reproducibility_rate"] == 1.0

    def test_worst_baseline(self):
        """All-missed, all-unresolved, all over-claimed, none reproducible => worst scores."""
        verdict = {
            "task_id": "T001",
            "arm": "BASELINE",
            "false_claim_verdicts": [{"defect_id": "D1", "caught": False}],
            "over_claim_verdicts": [{"ledger_row_id": "R1", "over_claimed": True}],
            "citation_verdicts": [{"citation_text": "Fake 2099", "resolves": False}],
            "reproducibility_verdicts": [{"claim_text": "x=999", "reproducible": False}],
        }
        result = compute_all(verdict, {"false_claims_to_catch": ["claim_a"]})
        assert result["false_claim_rate"] == 1.0
        assert result["over_claim_rate"] == 1.0
        assert result["citation_integrity"] == 0.0
        assert result["reproducibility_rate"] == 0.0


# ---------------------------------------------------------------------------
# 6. Smoke test: run_study.py --demo produces results.csv with expected columns
# ---------------------------------------------------------------------------

class TestRunStudyDemo:
    def _run_demo(self, extra_args=None):
        """Run run_study.py --demo in a temp dir; return (returncode, out_path)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = os.path.join(tmpdir, "demo_results.csv")
            cmd = [
                sys.executable,
                os.path.join(EVALS_DIR, "run_study.py"),
                "--demo",
                "--out", out_path,
            ]
            if extra_args:
                cmd.extend(extra_args)
            result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
            rows = []
            if os.path.exists(out_path):
                with open(out_path, newline="", encoding="utf-8") as f:
                    rows = list(csv.DictReader(f))
            return result.returncode, result.stdout, result.stderr, rows

    def test_demo_exits_zero(self):
        rc, stdout, stderr, _ = self._run_demo()
        assert rc == 0, f"run_study.py --demo exited {rc}.\nSTDOUT:\n{stdout}\nSTDERR:\n{stderr}"

    def test_demo_produces_results_csv(self):
        rc, stdout, stderr, rows = self._run_demo()
        assert rc == 0
        assert len(rows) > 0, "results.csv has no rows"

    def test_demo_csv_has_expected_columns(self):
        from evals.enforcement_study.run_study import RESULTS_COLUMNS
        rc, stdout, stderr, rows = self._run_demo()
        assert rc == 0
        assert len(rows) > 0
        for col in RESULTS_COLUMNS:
            assert col in rows[0], f"Missing column {col!r} in results.csv"

    def test_demo_has_both_arms(self):
        rc, stdout, stderr, rows = self._run_demo()
        assert rc == 0
        arms = {r["arm"] for r in rows}
        assert "TREATMENT" in arms, "TREATMENT arm missing from results.csv"
        assert "BASELINE" in arms, "BASELINE arm missing from results.csv"

    def test_demo_study_note_is_fixture_labeled(self):
        """The study_note column must contain FIXTURE/illustrative marker."""
        rc, stdout, stderr, rows = self._run_demo()
        assert rc == 0
        for row in rows:
            assert "FIXTURE" in row["study_note"], (
                f"study_note does not contain 'FIXTURE': {row['study_note']!r}"
            )

    def test_demo_treatment_better_than_baseline_on_fcr(self):
        """Fixture data designed so TREATMENT FCR < BASELINE FCR."""
        rc, stdout, stderr, rows = self._run_demo()
        assert rc == 0
        treatment = [r for r in rows if r["arm"] == "TREATMENT"]
        baseline  = [r for r in rows if r["arm"] == "BASELINE"]

        def avg_fcr(arm_rows):
            vals = [float(r["false_claim_rate"]) for r in arm_rows
                    if float(r["false_claim_rate"]) >= 0]
            return sum(vals) / len(vals) if vals else float("nan")

        t_fcr = avg_fcr(treatment)
        b_fcr = avg_fcr(baseline)
        assert t_fcr < b_fcr, (
            f"Fixture should have TREATMENT FCR ({t_fcr:.3f}) < BASELINE FCR ({b_fcr:.3f})"
        )


# ---------------------------------------------------------------------------
# 7. Task file schema validation
# ---------------------------------------------------------------------------

REQUIRED_TASK_KEYS = {"task_id", "category", "prompt", "materials",
                      "seeded_defects", "ground_truth", "scoring_notes"}
REQUIRED_GT_KEYS = {"correct_claim_tier", "correct_answer",
                    "citations_that_resolve", "citations_that_do_not_resolve",
                    "reproduced_numbers", "false_claims_to_catch",
                    "acceptable_uncertainty_expressions"}
VALID_CATEGORIES = {"citation_defect", "number_defect", "tier_defect",
                    "fabrication", "overclaim", "mixed"}


class TestTaskFiles:
    @pytest.fixture(autouse=True)
    def _load_tasks(self):
        self._task_files = sorted(
            f for f in os.listdir(TASKS_DIR)
            if f.startswith("T") and f.endswith(".json")
        )
        assert len(self._task_files) >= 12, (
            f"Expected at least 12 task files in {TASKS_DIR}; found {len(self._task_files)}"
        )

    def test_all_tasks_parse_as_json(self):
        for fname in self._task_files:
            path = os.path.join(TASKS_DIR, fname)
            with open(path, encoding="utf-8") as f:
                data = json.load(f)  # raises if invalid JSON
            assert isinstance(data, dict), f"{fname}: expected dict at top level"

    def test_all_tasks_have_required_keys(self):
        for fname in self._task_files:
            with open(os.path.join(TASKS_DIR, fname), encoding="utf-8") as f:
                data = json.load(f)
            missing = REQUIRED_TASK_KEYS - set(data.keys())
            assert not missing, f"{fname}: missing required keys: {missing}"

    def test_all_tasks_have_valid_category(self):
        for fname in self._task_files:
            with open(os.path.join(TASKS_DIR, fname), encoding="utf-8") as f:
                data = json.load(f)
            cat = data.get("category", "")
            assert cat in VALID_CATEGORIES, (
                f"{fname}: invalid category {cat!r}; must be one of {VALID_CATEGORIES}"
            )

    def test_all_tasks_have_ground_truth_keys(self):
        for fname in self._task_files:
            with open(os.path.join(TASKS_DIR, fname), encoding="utf-8") as f:
                data = json.load(f)
            gt = data.get("ground_truth", {})
            missing = REQUIRED_GT_KEYS - set(gt.keys())
            assert not missing, f"{fname}: ground_truth missing keys: {missing}"

    def test_task_ids_are_unique(self):
        ids = []
        for fname in self._task_files:
            with open(os.path.join(TASKS_DIR, fname), encoding="utf-8") as f:
                data = json.load(f)
            ids.append(data.get("task_id"))
        assert len(ids) == len(set(ids)), f"Duplicate task_ids: {ids}"

    def test_no_task_overlaps_with_full_lifecycle(self):
        """Circularity rule: no task may reuse the CI fixture content."""
        full_lifecycle_dir = os.path.join(ROOT, "examples", "full-lifecycle")
        if not os.path.isdir(full_lifecycle_dir):
            pytest.skip("examples/full-lifecycle not present; skipping overlap check")

        # Collect prompt texts from tasks
        task_prompts = set()
        for fname in self._task_files:
            with open(os.path.join(TASKS_DIR, fname), encoding="utf-8") as f:
                data = json.load(f)
            task_prompts.add(data.get("prompt", "")[:100])  # first 100 chars as fingerprint

        # Collect text snippets from full-lifecycle
        fl_texts = set()
        for dirpath, _, filenames in os.walk(full_lifecycle_dir):
            for fn in filenames:
                if fn.endswith((".md", ".txt", ".csv", ".json")):
                    try:
                        content = open(
                            os.path.join(dirpath, fn), encoding="utf-8", errors="replace"
                        ).read()
                        fl_texts.add(content[:100])
                    except Exception:
                        pass

        overlap = task_prompts & fl_texts
        assert not overlap, (
            f"Task prompts overlap with examples/full-lifecycle content: {overlap}"
        )


# ---------------------------------------------------------------------------
# 8. Fixture file validation
# ---------------------------------------------------------------------------

class TestFixtureFiles:
    def test_treatment_fixture_loads(self):
        path = os.path.join(FIXTURES_DIR, "treatment_verdicts.json")
        assert os.path.exists(path), f"Missing: {path}"
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        assert "verdicts" in data or isinstance(data, list), "Unexpected fixture format"

    def test_baseline_fixture_loads(self):
        path = os.path.join(FIXTURES_DIR, "baseline_verdicts.json")
        assert os.path.exists(path), f"Missing: {path}"
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        assert "verdicts" in data or isinstance(data, list), "Unexpected fixture format"

    def test_fixtures_labeled_as_fixture(self):
        """Both fixture files must carry the FIXTURE note."""
        for fname in ("treatment_verdicts.json", "baseline_verdicts.json"):
            path = os.path.join(FIXTURES_DIR, fname)
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            note = data.get("_fixture_note", "")
            assert "FIXTURE" in note, (
                f"{fname}: '_fixture_note' must contain 'FIXTURE'; got: {note!r}"
            )
