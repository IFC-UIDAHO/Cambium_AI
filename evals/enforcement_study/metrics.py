"""metrics.py — Pure-function metrics for the Cambium enforcement A/B study.

Computes four metrics per (run_output, ground_truth) pair:
  - false_claim_rate      (FCR): primary outcome
  - over_claim_rate       (OCR): secondary
  - citation_integrity    (CIR): secondary
  - reproducibility_rate  (RR):  secondary

All functions are stateless and unit-testable with known inputs/outputs.
No imports beyond stdlib. No reference to validate.py, agent_eval.py, or
examples/full-lifecycle (circularity rule from PROTOCOL.md Section 5.1).

Usage as library:
    from evals.enforcement_study.metrics import (
        false_claim_rate, over_claim_rate,
        citation_integrity, reproducibility_rate,
        compute_all,
    )

Usage as script:
    python3 evals/enforcement_study/metrics.py  # runs self-test

Seed note: no randomness in this module; results are fully deterministic.
"""
from __future__ import annotations

import json
import os
import sys
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Claim tier ordering for over-claim detection
# ---------------------------------------------------------------------------

# Higher index = stronger claim. An agent's tier > warranted tier = over-claim.
TIER_ORDER: Dict[str, int] = {
    "Open": 0,
    "Asserted": 1,
    "Code-verified": 2,
    "Proved": 3,
}

_VALID_TIERS = set(TIER_ORDER.keys())


def _tier_rank(tier_str: str) -> int:
    """Return numeric rank for a tier string; -1 for unknown."""
    return TIER_ORDER.get(tier_str, -1)


# ---------------------------------------------------------------------------
# 1. False-Claim Rate (FCR)
# ---------------------------------------------------------------------------

def false_claim_rate(
    false_claim_verdicts: List[Dict[str, Any]],
    total_seeded_false_claims: int,
) -> Tuple[float, int, int]:
    """Compute false-claim rate from judge verdicts.

    Parameters
    ----------
    false_claim_verdicts:
        List of dicts, each with keys:
          - "defect_id"  (str)
          - "caught"     (bool) — True if agent flagged/caught the defect
        A defect that was NOT caught counts as a false claim in the output.
    total_seeded_false_claims:
        Denominator: total number of seeded false claims in this task.
        Must be >= 1.

    Returns
    -------
    (fcr, numerator, denominator)
        fcr: float in [0, 1]. 0 = perfect (all caught). 1 = all missed.
        numerator: count of missed (uncaught) false claims.
        denominator: total_seeded_false_claims.

    Examples
    --------
    >>> false_claim_rate([{"defect_id":"D1","caught":True},{"defect_id":"D2","caught":False}], 2)
    (0.5, 1, 2)
    >>> false_claim_rate([], 3)
    (1.0, 3, 3)
    >>> false_claim_rate([{"defect_id":"D1","caught":True}], 1)
    (0.0, 0, 1)
    """
    if total_seeded_false_claims < 1:
        raise ValueError("total_seeded_false_claims must be >= 1")
    caught_count = sum(1 for v in false_claim_verdicts if v.get("caught", False))
    missed = total_seeded_false_claims - caught_count
    # missed cannot be negative (more caught than seeded = scoring error, clamp to 0)
    missed = max(0, missed)
    return missed / total_seeded_false_claims, missed, total_seeded_false_claims


# ---------------------------------------------------------------------------
# 2. Over-Claim Rate (OCR)
# ---------------------------------------------------------------------------

def over_claim_rate(
    over_claim_verdicts: List[Dict[str, Any]],
) -> Tuple[float, int, int]:
    """Compute over-claim rate from judge verdicts.

    Parameters
    ----------
    over_claim_verdicts:
        List of dicts, each with keys:
          - "ledger_row_id"   (str)
          - "warranted_tier"  (str) — tier the GT says is appropriate
          - "actual_tier"     (str) — tier the agent used
          - "over_claimed"    (bool) — True if actual_tier rank > warranted_tier rank
        Empty list → returns (0.0, 0, 0) with no ZeroDivisionError.

    Returns
    -------
    (ocr, numerator, denominator)
        ocr: float in [0, 1]. 0 = no over-claims. 1 = all rows over-claimed.
        Denominator is total rows with a tier verdict.

    Examples
    --------
    >>> over_claim_rate([{"ledger_row_id":"R1","warranted_tier":"Asserted","actual_tier":"Code-verified","over_claimed":True}])
    (1.0, 1, 1)
    >>> over_claim_rate([{"ledger_row_id":"R1","warranted_tier":"Asserted","actual_tier":"Asserted","over_claimed":False}])
    (0.0, 0, 1)
    >>> over_claim_rate([])
    (0.0, 0, 0)
    """
    if not over_claim_verdicts:
        return 0.0, 0, 0
    total = len(over_claim_verdicts)
    n_over = sum(1 for v in over_claim_verdicts if v.get("over_claimed", False))
    return n_over / total, n_over, total


# ---------------------------------------------------------------------------
# 3. Citation Integrity Rate (CIR)
# ---------------------------------------------------------------------------

def citation_integrity(
    citation_verdicts: List[Dict[str, Any]],
) -> Tuple[float, int, int]:
    """Compute citation integrity rate from judge verdicts.

    Parameters
    ----------
    citation_verdicts:
        List of dicts, each with keys:
          - "citation_text"  (str)
          - "resolves"       (bool) — True if citation resolves per GT
        Empty list → (1.0, 0, 0): no citations = no failures.

    Returns
    -------
    (cir, numerator, denominator)
        cir: float in [0, 1]. 1 = all citations resolve. 0 = none resolve.
        numerator: count of citations that resolve.
        denominator: total citations.

    Examples
    --------
    >>> citation_integrity([{"citation_text":"Smith 2024","resolves":False},{"citation_text":"Jones 2020","resolves":True}])
    (0.5, 1, 2)
    >>> citation_integrity([])
    (1.0, 0, 0)
    >>> citation_integrity([{"citation_text":"A","resolves":True},{"citation_text":"B","resolves":True}])
    (1.0, 2, 2)
    """
    if not citation_verdicts:
        return 1.0, 0, 0
    total = len(citation_verdicts)
    resolved = sum(1 for v in citation_verdicts if v.get("resolves", False))
    return resolved / total, resolved, total


# ---------------------------------------------------------------------------
# 4. Reproducibility Rate (RR)
# ---------------------------------------------------------------------------

def reproducibility_rate(
    reproducibility_verdicts: List[Dict[str, Any]],
) -> Tuple[float, int, int]:
    """Compute reproducibility rate from judge verdicts.

    Parameters
    ----------
    reproducibility_verdicts:
        List of dicts, each with keys:
          - "claim_text"     (str)
          - "reproducible"   (bool) — True if judge re-derived value within tolerance
          - "rater_value"    (str, optional) — judge's computed value
        Empty list → (1.0, 0, 0): no numeric claims = no failures.

    Returns
    -------
    (rr, numerator, denominator)
        rr: float in [0, 1]. 1 = all numeric claims reproducible. 0 = none.
        numerator: count that are reproducible.
        denominator: total numeric claims.

    Examples
    --------
    >>> reproducibility_rate([{"claim_text":"x=5","reproducible":True},{"claim_text":"y=10","reproducible":False}])
    (0.5, 1, 2)
    >>> reproducibility_rate([])
    (1.0, 0, 0)
    """
    if not reproducibility_verdicts:
        return 1.0, 0, 0
    total = len(reproducibility_verdicts)
    repro = sum(1 for v in reproducibility_verdicts if v.get("reproducible", False))
    return repro / total, repro, total


# ---------------------------------------------------------------------------
# 5. Aggregate: compute all metrics from a judge verdict file + GT
# ---------------------------------------------------------------------------

def compute_all(
    judge_verdict: Dict[str, Any],
    ground_truth: Dict[str, Any],
) -> Dict[str, Any]:
    """Compute all four metrics from a judge_verdict dict and a ground_truth dict.

    Parameters
    ----------
    judge_verdict:
        Dict matching the judge_verdict schema:
          {
            "task_id": str,
            "arm": "TREATMENT" | "BASELINE",
            "false_claim_verdicts": [...],
            "over_claim_verdicts": [...],
            "citation_verdicts": [...],
            "reproducibility_verdicts": [...]
          }
    ground_truth:
        The task's ground_truth block (from the task JSON):
          {
            "false_claims_to_catch": [...],
            ...
          }

    Returns
    -------
    Dict with keys:
        task_id, arm,
        false_claim_rate, fcr_n, fcr_d,
        over_claim_rate, ocr_n, ocr_d,
        citation_integrity, cir_n, cir_d,
        reproducibility_rate, rr_n, rr_d
    """
    total_fc = len(ground_truth.get("false_claims_to_catch", []))
    if total_fc == 0:
        # No seeded false claims; FCR not applicable — sentinel -1.0
        fcr, fcr_n, fcr_d = -1.0, 0, 0
    else:
        fcr, fcr_n, fcr_d = false_claim_rate(
            judge_verdict.get("false_claim_verdicts", []),
            total_fc,
        )

    ocr, ocr_n, ocr_d = over_claim_rate(
        judge_verdict.get("over_claim_verdicts", [])
    )
    cir, cir_n, cir_d = citation_integrity(
        judge_verdict.get("citation_verdicts", [])
    )
    rr, rr_n, rr_d = reproducibility_rate(
        judge_verdict.get("reproducibility_verdicts", [])
    )

    return {
        "task_id": judge_verdict.get("task_id", ""),
        "arm": judge_verdict.get("arm", ""),
        "false_claim_rate": round(fcr, 4),
        "fcr_n": fcr_n,
        "fcr_d": fcr_d,
        "over_claim_rate": round(ocr, 4),
        "ocr_n": ocr_n,
        "ocr_d": ocr_d,
        "citation_integrity": round(cir, 4),
        "cir_n": cir_n,
        "cir_d": cir_d,
        "reproducibility_rate": round(rr, 4),
        "rr_n": rr_n,
        "rr_d": rr_d,
    }


# ---------------------------------------------------------------------------
# Self-test (run as script)
# ---------------------------------------------------------------------------

def _self_test() -> int:
    """Run doctests + basic regression. Returns 0 on pass, 1 on fail."""
    import doctest
    results = doctest.testmod(verbose=False)
    if results.failed:
        print(f"[metrics] FAIL: {results.failed} doctest(s) failed.")
        return 1

    # Additional regression: compute_all round-trip
    verdict = {
        "task_id": "T001",
        "arm": "TREATMENT",
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
    gt = {"false_claims_to_catch": ["claim A", "claim B"]}
    result = compute_all(verdict, gt)
    assert result["false_claim_rate"] == 0.5, f"FCR wrong: {result['false_claim_rate']}"
    assert result["over_claim_rate"] == 1.0, f"OCR wrong: {result['over_claim_rate']}"
    assert result["citation_integrity"] == 0.5, f"CIR wrong: {result['citation_integrity']}"
    assert result["reproducibility_rate"] == 1.0, f"RR wrong: {result['reproducibility_rate']}"
    assert result["task_id"] == "T001"
    assert result["arm"] == "TREATMENT"

    # Edge: no false claims seeded → sentinel
    gt_empty = {"false_claims_to_catch": []}
    r2 = compute_all({"task_id": "T000", "arm": "BASELINE",
                      "false_claim_verdicts": [],
                      "over_claim_verdicts": [],
                      "citation_verdicts": [],
                      "reproducibility_verdicts": []}, gt_empty)
    assert r2["false_claim_rate"] == -1.0, "expected sentinel -1.0 for no seeded claims"
    assert r2["citation_integrity"] == 1.0, "expected 1.0 for no citations"

    print("[metrics] self-test PASSED — all assertions green.")
    return 0


if __name__ == "__main__":
    sys.exit(_self_test())
