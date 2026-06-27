"""tests/test_funder_freshness.py — Unit tests for tools/funder_freshness.py.

Tests:
  1. Fresh entries pass (exit 0).
  2. Stale entries fail (exit 1).
  3. Missing required field fails (exit 1).
  4. Approaching-staleness warning (exit 0, but warns).
  5. Invalid gate reference fails.
  6. Future last_reviewed fails.
  7. Real nih.yml and nsf.yml pass with today's date.
  8. CLI --demo flag integration via subprocess.

Run with: pytest tests/test_funder_freshness.py -v
"""
import datetime
import os
import subprocess
import sys
import tempfile

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FUNDERS_DIR = os.path.join(ROOT, "governance", "funders")

sys.path.insert(0, ROOT)
from tools.funder_freshness import (
    check_all,
    check_file,
    _check_entry,
    FreshnessResult,
    EntryResult,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

TODAY = datetime.date(2026, 6, 26)

def _make_valid_entry(
    rule_id="TEST-001",
    funder="NIH",
    last_reviewed=None,
    source_date="2025-07-17",
    freshness_window_days=120,
    status="active",
    confidence="high",
    gate="G2",
):
    """Return a minimal valid entry dict."""
    if last_reviewed is None:
        last_reviewed = TODAY.isoformat()
    return {
        "funder": funder,
        "rule_id": rule_id,
        "summary": "Test rule summary.",
        "rule_text_note": "Paraphrase of the rule; see source_url.",
        "source_url": "https://example.com/rule",
        "source_date": source_date,
        "gate_mapping": [
            {"gate": gate, "obligation": "Test obligation.", "owner_role": "PI", "action": "surface"}
        ],
        "last_reviewed": last_reviewed,
        "reviewed_by": "Test User",
        "review_cadence": "quarterly",
        "freshness_window_days": freshness_window_days,
        "status": status,
        "confidence": confidence,
    }


def _write_yml(tmpdir, content: str, name: str = "test_funder.yml") -> str:
    path = os.path.join(tmpdir, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


# ---------------------------------------------------------------------------
# 1. Valid entry passes
# ---------------------------------------------------------------------------

class TestValidEntry:
    def test_fresh_entry_passes(self):
        entry = _make_valid_entry()
        result = _check_entry(entry, "test.yml", today=TODAY)
        assert result.status == "PASS", f"Expected PASS, got {result.status}; blockers={result.blockers}"
        assert not result.blockers

    def test_fresh_entry_has_no_blockers(self):
        entry = _make_valid_entry(last_reviewed=TODAY.isoformat(), freshness_window_days=120)
        result = _check_entry(entry, "test.yml", today=TODAY)
        assert len(result.blockers) == 0


# ---------------------------------------------------------------------------
# 2. Stale entry fails
# ---------------------------------------------------------------------------

class TestStaleEntry:
    def test_stale_entry_fails(self):
        """Entry reviewed 150 days ago with 120-day window is stale."""
        old_date = (TODAY - datetime.timedelta(days=150)).isoformat()
        entry = _make_valid_entry(last_reviewed=old_date, freshness_window_days=120)
        result = _check_entry(entry, "test.yml", today=TODAY)
        assert result.status == "FAIL"
        assert any("STALE" in b for b in result.blockers), \
            f"Expected STALE blocker; got: {result.blockers}"

    def test_exactly_at_window_is_not_stale(self):
        """Reviewed exactly at freshness_window_days is NOT stale (boundary: age == window is ok)."""
        on_day = (TODAY - datetime.timedelta(days=120)).isoformat()
        entry = _make_valid_entry(last_reviewed=on_day, freshness_window_days=120)
        result = _check_entry(entry, "test.yml", today=TODAY)
        # age == window: not stale (stale = age > window)
        assert not any("STALE" in b for b in result.blockers)

    def test_one_day_over_window_is_stale(self):
        over = (TODAY - datetime.timedelta(days=121)).isoformat()
        entry = _make_valid_entry(last_reviewed=over, freshness_window_days=120)
        result = _check_entry(entry, "test.yml", today=TODAY)
        assert any("STALE" in b for b in result.blockers)


# ---------------------------------------------------------------------------
# 3. Missing required field fails
# ---------------------------------------------------------------------------

class TestMissingField:
    @pytest.mark.parametrize("missing_field", [
        "funder", "rule_id", "summary", "rule_text_note",
        "source_url", "source_date", "gate_mapping",
        "last_reviewed", "reviewed_by", "review_cadence",
        "freshness_window_days", "status",
    ])
    def test_missing_required_field_fails(self, missing_field):
        entry = _make_valid_entry()
        del entry[missing_field]
        result = _check_entry(entry, "test.yml", today=TODAY)
        assert result.status == "FAIL", \
            f"Expected FAIL when '{missing_field}' is missing; got {result.status}"
        assert any(missing_field in b for b in result.blockers), \
            f"Expected blocker mentioning '{missing_field}'; got: {result.blockers}"

    def test_empty_required_field_fails(self):
        entry = _make_valid_entry()
        entry["reviewed_by"] = ""
        result = _check_entry(entry, "test.yml", today=TODAY)
        assert result.status == "FAIL"


# ---------------------------------------------------------------------------
# 4. Warning on approaching staleness
# ---------------------------------------------------------------------------

class TestApproachingStaleness:
    def test_at_75_percent_warns(self):
        """Reviewed 91 days ago with 120-day window (75.8%) should warn."""
        warn_date = (TODAY - datetime.timedelta(days=91)).isoformat()
        entry = _make_valid_entry(last_reviewed=warn_date, freshness_window_days=120)
        result = _check_entry(entry, "test.yml", today=TODAY)
        # Should warn but not fail (age 91 < 120 but > 0.75*120=90)
        assert result.status == "WARN", \
            f"Expected WARN at 91 days / 120-day window; got {result.status}; " \
            f"blockers={result.blockers}, warnings={result.warnings}"
        assert not result.blockers

    def test_below_75_percent_passes_cleanly(self):
        """Reviewed 89 days ago with 120-day window (74%) — no warn."""
        ok_date = (TODAY - datetime.timedelta(days=89)).isoformat()
        entry = _make_valid_entry(last_reviewed=ok_date, freshness_window_days=120)
        result = _check_entry(entry, "test.yml", today=TODAY)
        assert result.status == "PASS"
        assert not result.blockers


# ---------------------------------------------------------------------------
# 5. Invalid gate reference fails
# ---------------------------------------------------------------------------

class TestGateValidation:
    def test_invalid_gate_fails(self):
        entry = _make_valid_entry(gate="G99")
        result = _check_entry(entry, "test.yml", today=TODAY)
        assert result.status == "FAIL"
        assert any("invalid gate" in b.lower() for b in result.blockers), \
            f"Expected invalid gate blocker; got: {result.blockers}"

    def test_valid_gates_pass(self):
        for gate in ["G0", "G1", "G2", "G3", "G3a", "G4", "G5", "G6"]:
            entry = _make_valid_entry(gate=gate)
            result = _check_entry(entry, "test.yml", today=TODAY)
            assert not any("invalid gate" in b.lower() for b in result.blockers), \
                f"Gate {gate!r} should be valid; blockers={result.blockers}"


# ---------------------------------------------------------------------------
# 6. Future date fails
# ---------------------------------------------------------------------------

class TestFutureDate:
    def test_future_last_reviewed_fails(self):
        future = (TODAY + datetime.timedelta(days=30)).isoformat()
        entry = _make_valid_entry(last_reviewed=future)
        result = _check_entry(entry, "test.yml", today=TODAY)
        assert result.status == "FAIL"
        assert any("future" in b.lower() for b in result.blockers), \
            f"Expected 'future' blocker; got: {result.blockers}"


# ---------------------------------------------------------------------------
# 7. Real nih.yml and nsf.yml pass
# ---------------------------------------------------------------------------

class TestRealFunderFiles:
    def test_nih_yml_passes(self):
        path = os.path.join(FUNDERS_DIR, "nih.yml")
        if not os.path.exists(path):
            pytest.skip(f"nih.yml not found at {path}")
        entry_results, file_errors = check_file(path, today=TODAY)
        assert not file_errors, f"File-level errors: {file_errors}"
        assert len(entry_results) >= 1, "nih.yml should have at least 1 entry"
        blockers = [b for er in entry_results for b in er.blockers]
        assert not blockers, f"nih.yml has blockers: {blockers}"

    def test_nsf_yml_passes(self):
        path = os.path.join(FUNDERS_DIR, "nsf.yml")
        if not os.path.exists(path):
            pytest.skip(f"nsf.yml not found at {path}")
        entry_results, file_errors = check_file(path, today=TODAY)
        assert not file_errors, f"File-level errors: {file_errors}"
        assert len(entry_results) >= 1, "nsf.yml should have at least 1 entry"
        blockers = [b for er in entry_results for b in er.blockers]
        assert not blockers, f"nsf.yml has blockers: {blockers}"

    def test_check_all_passes_on_real_corpus(self):
        if not os.path.isdir(FUNDERS_DIR):
            pytest.skip(f"Funders dir not found: {FUNDERS_DIR}")
        result = check_all(funders_dir=FUNDERS_DIR, today=TODAY)
        assert result.passed, (
            f"check_all failed on real corpus (today={TODAY}):\n"
            + "\n".join(f"  X {b}" for b in result.blockers)
        )


# ---------------------------------------------------------------------------
# 8. Stale file via check_all (with temp dir)
# ---------------------------------------------------------------------------

class TestCheckAllWithTempFiles:
    def _yml_content(self, last_reviewed: str, window: int = 120) -> str:
        return f"""- funder: TEST
  rule_id: TEST-STALE-001
  summary: A test rule.
  rule_text_note: A test paraphrase.
  source_url: "https://example.com"
  source_date: "2025-01-01"
  gate_mapping:
    - gate: G2
      obligation: Test obligation.
      owner_role: PI
      action: surface
  last_reviewed: "{last_reviewed}"
  reviewed_by: "Test User"
  review_cadence: quarterly
  freshness_window_days: {window}
  status: active
  confidence: high
"""

    def test_stale_file_causes_fail(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            old = (TODAY - datetime.timedelta(days=200)).isoformat()
            path = _write_yml(tmpdir, self._yml_content(old))
            result = check_all(funders_dir=tmpdir, today=TODAY)
            assert not result.passed, "Expected check_all to fail on stale entry"
            assert any("STALE" in b for b in result.blockers)

    def test_fresh_file_passes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fresh = TODAY.isoformat()
            path = _write_yml(tmpdir, self._yml_content(fresh))
            result = check_all(funders_dir=tmpdir, today=TODAY)
            assert result.passed, (
                f"Expected fresh entry to pass; blockers={result.blockers}"
            )

    def test_missing_field_via_check_all_fails(self):
        content = """- funder: TEST
  rule_id: TEST-MISSING-001
  summary: Missing some fields.
  source_url: "https://example.com"
  last_reviewed: "2026-06-26"
  reviewed_by: "Test User"
  freshness_window_days: 120
  status: active
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            _write_yml(tmpdir, content)
            result = check_all(funders_dir=tmpdir, today=TODAY)
            assert not result.passed, "Expected failure on missing required fields"


# ---------------------------------------------------------------------------
# 9. CLI subprocess tests
# ---------------------------------------------------------------------------

class TestCLI:
    def test_cli_passes_on_real_corpus(self):
        result = subprocess.run(
            [sys.executable, os.path.join(ROOT, "tools", "funder_freshness.py"),
             "--date", TODAY.isoformat()],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, (
            f"CLI exited {result.returncode}.\n"
            f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )
        assert "OK" in result.stdout, "Expected 'OK' in output"

    def test_cli_fails_on_stale_yml(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            old = (TODAY - datetime.timedelta(days=200)).isoformat()
            yml_content = f"""- funder: TEST
  rule_id: CLI-STALE-001
  summary: Stale entry.
  rule_text_note: Paraphrase.
  source_url: "https://example.com"
  source_date: "2025-01-01"
  gate_mapping:
    - gate: G2
      obligation: Obligation.
      owner_role: PI
      action: surface
  last_reviewed: "{old}"
  reviewed_by: "Test User"
  review_cadence: quarterly
  freshness_window_days: 120
  status: active
  confidence: high
"""
            yml_path = os.path.join(tmpdir, "stale_test.yml")
            with open(yml_path, "w") as f:
                f.write(yml_content)
            result = subprocess.run(
                [sys.executable, os.path.join(ROOT, "tools", "funder_freshness.py"),
                 "--funders-dir", tmpdir,
                 "--date", TODAY.isoformat()],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            assert result.returncode == 1, (
                f"Expected exit 1 on stale entry; got {result.returncode}.\n"
                f"STDOUT:\n{result.stdout}"
            )
