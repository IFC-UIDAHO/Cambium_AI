"""Tests for tools/loop_costs.py — four-cost loop guard.

All tests use temporary directories so they do not depend on the live repo state.
"""
import csv, os, sys, tempfile
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
import loop_costs as LC

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_csv(path: str, rows: list[dict]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        if rows:
            w = csv.DictWriter(fh, fieldnames=rows[0].keys())
            w.writeheader()
            w.writerows(rows)


# ---------------------------------------------------------------------------
# Cost 1: VERIFICATION DEBT
# ---------------------------------------------------------------------------

class TestVerificationDebt:
    def _ledger(self, tmp, rows):
        path = os.path.join(tmp, "agent_outputs", "findings_ledger.csv")
        _write_csv(path, rows)
        return tmp

    def test_absent_ledger_advisory_not_crash(self, tmp_path):
        ratio, flagged, detail = LC.verification_debt(str(tmp_path))
        assert not flagged
        assert "absent" in detail.lower() or "not measured" in detail.lower()

    def test_good_case_no_flag(self, tmp_path):
        rows = [
            {"claim_tier": "Proved"},
            {"claim_tier": "Code-verified"},
            {"claim_tier": "Asserted"},
            {"claim_tier": "Proved"},
            {"claim_tier": "Code-verified"},
        ]
        self._ledger(str(tmp_path), rows)
        ratio, flagged, detail = LC.verification_debt(str(tmp_path))
        assert not flagged
        assert ratio == pytest.approx(1 / 5)

    def test_high_debt_ratio_flags(self, tmp_path):
        # 3 Asserted + 2 Open out of 6 = 5/6 ~ 0.83 > 0.40
        rows = [{"claim_tier": t} for t in
                ["Asserted", "Asserted", "Open", "Asserted", "Open", "Code-verified"]]
        self._ledger(str(tmp_path), rows)
        ratio, flagged, detail = LC.verification_debt(str(tmp_path))
        assert flagged
        assert ratio > 0.40
        assert "FLAG" in detail

    def test_five_rows_zero_strong_flags(self, tmp_path):
        rows = [{"claim_tier": "Asserted"} for _ in range(5)]
        self._ledger(str(tmp_path), rows)
        ratio, flagged, detail = LC.verification_debt(str(tmp_path))
        assert flagged
        assert "zero Code-verified" in detail or "FLAG" in detail

    def test_four_rows_zero_strong_no_flag(self, tmp_path):
        # total < 5 so the zero-strong rule does not apply; ratio = 1.0 > 0.40 -> still flags
        # Let's use 4 rows with ratio < 0.40 and zero strong
        rows = [{"claim_tier": "Asserted"}, {"claim_tier": "Proved"},
                {"claim_tier": "Proved"}, {"claim_tier": "Proved"}]
        self._ledger(str(tmp_path), rows)
        ratio, flagged, detail = LC.verification_debt(str(tmp_path))
        # 1/4 = 0.25 < 0.40 and total < 5 -> should NOT flag
        assert not flagged


# ---------------------------------------------------------------------------
# Cost 2: COMPREHENSION ROT
# ---------------------------------------------------------------------------

class TestComprehensionRot:
    def test_no_artifact_flags(self, tmp_path):
        art, flagged, detail = LC.comprehension_rot(str(tmp_path))
        assert not art
        assert flagged
        assert "ABSENT" in detail or "FLAG" in detail

    def test_learning_packet_present_no_flag(self, tmp_path):
        ao = os.path.join(str(tmp_path), "agent_outputs")
        os.makedirs(ao, exist_ok=True)
        lp = os.path.join(ao, "learning_packet.md")
        open(lp, "w").write("# Learning Packet\nContent here.")
        art, flagged, detail = LC.comprehension_rot(str(tmp_path))
        assert art
        assert not flagged

    def test_learning_lab_html_present_no_flag(self, tmp_path):
        demo = os.path.join(str(tmp_path), "demo")
        os.makedirs(demo, exist_ok=True)
        open(os.path.join(demo, "learning_lab.html"), "w").write("<html/>")
        art, flagged, detail = LC.comprehension_rot(str(tmp_path))
        assert art
        assert not flagged

    def test_academy_labs_html_present_no_flag(self, tmp_path):
        lab_dir = os.path.join(str(tmp_path), "academy", "labs")
        os.makedirs(lab_dir, exist_ok=True)
        open(os.path.join(lab_dir, "lab1.html"), "w").write("<html/>")
        art, flagged, detail = LC.comprehension_rot(str(tmp_path))
        assert art
        assert not flagged

    def test_low_brief_coverage_flags(self, tmp_path):
        # Create a learning artifact so only the coverage triggers the flag
        ao = os.path.join(str(tmp_path), "agent_outputs")
        os.makedirs(ao, exist_ok=True)
        open(os.path.join(ao, "learning_packet.md"), "w").write("# LP\nFilled.")
        # Ledger with 3 briefs, only 1 complete
        gov = os.path.join(str(tmp_path), "governance")
        os.makedirs(gov, exist_ok=True)
        rows = [
            {"timestamp": "t1", "kind": "brief", "id": "p1", "director": "D",
             "status": "complete",  "copy_flag": "-", "detail": "ok"},
            {"timestamp": "t2", "kind": "brief", "id": "p2", "director": "D",
             "status": "BLOCKED",   "copy_flag": "-", "detail": "missing"},
            {"timestamp": "t3", "kind": "brief", "id": "p3", "director": "D",
             "status": "BLOCKED",   "copy_flag": "-", "detail": "missing"},
        ]
        _write_csv(os.path.join(gov, "CONTRIBUTION_LEDGER.csv"), rows)
        art, flagged, detail = LC.comprehension_rot(str(tmp_path))
        assert art
        assert flagged
        assert "brief_coverage" in detail


# ---------------------------------------------------------------------------
# Cost 3: COGNITIVE SURRENDER
# ---------------------------------------------------------------------------

class TestCognitiveSurrender:
    def _ledger(self, tmp, rows):
        gov = os.path.join(tmp, "governance")
        os.makedirs(gov, exist_ok=True)
        path = os.path.join(gov, "CONTRIBUTION_LEDGER.csv")
        _write_csv(path, rows)

    def test_absent_ledger_advisory_not_crash(self, tmp_path):
        ratio, flagged, detail = LC.cognitive_surrender(str(tmp_path))
        assert not flagged
        assert "absent" in detail.lower() or "not measured" in detail.lower()

    def test_good_case_no_flag(self, tmp_path):
        rows = [
            {"timestamp": "t1", "kind": "contribution", "id": "G1", "director": "D",
             "status": "complete", "copy_flag": "PASS", "detail": "change_ratio=0.80"},
            {"timestamp": "t2", "kind": "contribution", "id": "G2", "director": "D",
             "status": "complete", "copy_flag": "PASS", "detail": "change_ratio=0.75"},
            {"timestamp": "t3", "kind": "contribution", "id": "G3", "director": "D",
             "status": "complete", "copy_flag": "PASS", "detail": "change_ratio=0.90"},
        ]
        self._ledger(str(tmp_path), rows)
        ratio, flagged, detail = LC.cognitive_surrender(str(tmp_path))
        assert not flagged
        assert ratio == 0.0

    def test_high_low_delta_flags(self, tmp_path):
        # 4 out of 5 rows are LOW-DELTA -> surrender_ratio = 0.80 > 0.33
        rows = [
            {"timestamp": "t1", "kind": "contribution", "id": "G1", "director": "D",
             "status": "complete", "copy_flag": "LOW-DELTA", "detail": "change_ratio=0.10"},
            {"timestamp": "t2", "kind": "contribution", "id": "G2", "director": "D",
             "status": "complete", "copy_flag": "LOW-DELTA", "detail": "change_ratio=0.05"},
            {"timestamp": "t3", "kind": "contribution", "id": "G3", "director": "D",
             "status": "complete", "copy_flag": "LOW-DELTA", "detail": "change_ratio=0.08"},
            {"timestamp": "t4", "kind": "contribution", "id": "G4", "director": "D",
             "status": "complete", "copy_flag": "LOW-DELTA", "detail": "change_ratio=0.12"},
            {"timestamp": "t5", "kind": "contribution", "id": "G5", "director": "D",
             "status": "complete", "copy_flag": "PASS",      "detail": "change_ratio=0.80"},
        ]
        self._ledger(str(tmp_path), rows)
        ratio, flagged, detail = LC.cognitive_surrender(str(tmp_path))
        assert flagged
        assert ratio > 0.33
        assert "FLAG" in detail

    def test_enforcement_bypass_flags(self, tmp_path):
        # BLOCKED row with a non-standard copy_flag
        rows = [
            {"timestamp": "t1", "kind": "contribution", "id": "G1", "director": "D",
             "status": "BLOCKED", "copy_flag": "REVIEW", "detail": "incomplete"},
        ]
        self._ledger(str(tmp_path), rows)
        ratio, flagged, detail = LC.cognitive_surrender(str(tmp_path))
        assert flagged
        assert "bypass" in detail.lower() or "BLOCKED" in detail

    def test_review_copy_flag_counted_as_low_delta(self, tmp_path):
        rows = [
            {"timestamp": "t1", "kind": "contribution", "id": "G1", "director": "D",
             "status": "complete", "copy_flag": "REVIEW", "detail": "hypothesis looks copied"},
        ]
        self._ledger(str(tmp_path), rows)
        ratio, flagged, detail = LC.cognitive_surrender(str(tmp_path))
        # 1/1 = 100% > 0.33 -> flagged
        assert flagged


# ---------------------------------------------------------------------------
# Cost 4: TOKEN BLOWOUT
# ---------------------------------------------------------------------------

class TestTokenBlowout:
    def _cost_log(self, tmp, rows, subdir="run1"):
        path = os.path.join(tmp, "agent_outputs", subdir, "cost_log.csv")
        _write_csv(path, rows)

    def test_absent_logs_advisory_not_crash(self, tmp_path):
        spent, ceiling, flagged, detail = LC.token_blowout(str(tmp_path), budget=20.0)
        assert spent == 0.0
        assert not flagged
        assert "absent" in detail.lower() or "not measured" in detail.lower()

    def test_under_budget_no_flag(self, tmp_path):
        rows = [{"est_usd": "5.0"}, {"est_usd": "3.0"}]
        self._cost_log(str(tmp_path), rows)
        spent, ceiling, flagged, detail = LC.token_blowout(str(tmp_path), budget=20.0)
        assert spent == pytest.approx(8.0)
        assert ceiling == pytest.approx(20.0)
        assert not flagged

    def test_at_80pct_flags(self, tmp_path):
        rows = [{"est_usd": "16.0"}, {"est_usd": "1.0"}]  # 17/20 = 85%
        self._cost_log(str(tmp_path), rows)
        spent, ceiling, flagged, detail = LC.token_blowout(str(tmp_path), budget=20.0)
        assert flagged
        assert "APPROACHING" in detail or "FLAG" in detail

    def test_over_100pct_flags(self, tmp_path):
        rows = [{"est_usd": "22.0"}]
        self._cost_log(str(tmp_path), rows)
        spent, ceiling, flagged, detail = LC.token_blowout(str(tmp_path), budget=20.0)
        assert flagged
        assert "OVER BUDGET" in detail or "FLAG" in detail

    def test_multiple_cost_logs_summed(self, tmp_path):
        self._cost_log(str(tmp_path), [{"est_usd": "8.0"}], subdir="run1")
        self._cost_log(str(tmp_path), [{"est_usd": "7.0"}], subdir="run2")
        spent, ceiling, flagged, detail = LC.token_blowout(str(tmp_path), budget=20.0)
        assert spent == pytest.approx(15.0)
        assert not flagged

    def test_config_yml_ceiling(self, tmp_path):
        cfg = os.path.join(str(tmp_path), "config.yml")
        open(cfg, "w").write("run_budget_usd: 10.0\n")
        rows = [{"est_usd": "9.0"}]
        self._cost_log(str(tmp_path), rows)
        spent, ceiling, flagged, detail = LC.token_blowout(str(tmp_path))
        assert ceiling == pytest.approx(10.0)
        assert spent == pytest.approx(9.0)
        assert flagged  # 9/10 = 90% >= 80%

    def test_default_ceiling_when_no_config(self, tmp_path):
        rows = [{"est_usd": "1.0"}]
        self._cost_log(str(tmp_path), rows)
        spent, ceiling, flagged, detail = LC.token_blowout(str(tmp_path))
        assert ceiling == pytest.approx(LC.DEFAULT_BUDGET)


# ---------------------------------------------------------------------------
# CLI: --enforce-budget
# ---------------------------------------------------------------------------

class TestEnforceBudgetCLI:
    def _cost_log(self, tmp, usd):
        path = os.path.join(tmp, "agent_outputs", "run1", "cost_log.csv")
        _write_csv(path, [{"est_usd": str(usd)}])

    def test_enforce_exits_1_when_over(self, tmp_path):
        self._cost_log(str(tmp_path), 25.0)
        rc = LC.main(["--root", str(tmp_path), "--budget", "20.0", "--enforce-budget"])
        assert rc == 1

    def test_enforce_exits_0_when_under(self, tmp_path):
        self._cost_log(str(tmp_path), 10.0)
        rc = LC.main(["--root", str(tmp_path), "--budget", "20.0", "--enforce-budget"])
        assert rc == 0

    def test_enforce_exits_0_when_no_logs(self, tmp_path):
        rc = LC.main(["--root", str(tmp_path), "--budget", "20.0", "--enforce-budget"])
        assert rc == 0


# ---------------------------------------------------------------------------
# Full report does not crash on empty root
# ---------------------------------------------------------------------------

class TestReport:
    def test_report_all_advisory_on_empty_root(self, tmp_path):
        r = LC.report(str(tmp_path), budget=20.0)
        assert "costs" in r
        assert len(r["costs"]) == 4
        # All advisory, nothing actually flagged (no ledgers present)
        # C2 WILL flag because no learning artifact
        c2 = r["costs"]["C2_comprehension_rot"]
        assert c2["flagged"]  # expected: no artifact -> flagged
        # Others are advisory (no data -> no flag)
        for key in ("C1_verification_debt", "C3_cognitive_surrender", "C4_token_blowout"):
            assert not r["costs"][key]["flagged"]

    def test_main_exits_0_in_advisory_mode(self, tmp_path):
        rc = LC.main(["--root", str(tmp_path)])
        assert rc == 0
