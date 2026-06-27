#!/usr/bin/env python3
"""run_study.py — Cambium enforcement A/B study runner.

Given two arms' judge-verdict files + the ground-truth task set, computes all
four metrics per arm and writes results.csv. This runner SCORES verdicts; it
does NOT run agents.

Study result is OPEN — no finding exists until real agents run under both arm
configurations and a blind human judge panel produces real verdict files. See
PROTOCOL.md for the full pre-registration.

Usage:
    # Demo mode (harness validation, no live agents needed):
    python3 evals/enforcement_study/run_study.py --demo

    # Real mode (after actual agent runs + judge scoring):
    python3 evals/enforcement_study/run_study.py \\
        --treatment path/to/treatment_verdicts.json \\
        --baseline  path/to/baseline_verdicts.json \\
        --tasks     evals/enforcement_study/tasks/ \\
        --out       results.csv

    # Custom output path:
    python3 evals/enforcement_study/run_study.py --demo --out /tmp/demo_results.csv

Exit: 0 on success, 1 on any error.

Seed: no randomness in this module (pure aggregation). Results are deterministic.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Path setup — allow running from repo root or from this directory
# ---------------------------------------------------------------------------
_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(os.path.dirname(_HERE))
sys.path.insert(0, _REPO_ROOT)

from evals.enforcement_study.metrics import compute_all  # noqa: E402

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_TASKS_DIR = os.path.join(_HERE, "tasks")
_FIXTURES_DIR = os.path.join(_HERE, "fixtures")
_DEMO_TREATMENT = os.path.join(_FIXTURES_DIR, "treatment_verdicts.json")
_DEMO_BASELINE = os.path.join(_FIXTURES_DIR, "baseline_verdicts.json")
_DEFAULT_OUT = os.path.join(_HERE, "results.csv")

RESULTS_COLUMNS = [
    "study_note",
    "task_id",
    "arm",
    "false_claim_rate",
    "fcr_n",
    "fcr_d",
    "over_claim_rate",
    "ocr_n",
    "ocr_d",
    "citation_integrity",
    "cir_n",
    "cir_d",
    "reproducibility_rate",
    "rr_n",
    "rr_d",
]

# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------

def load_verdicts(path: str) -> List[Dict[str, Any]]:
    """Load a verdicts JSON file; return the list of per-task verdict dicts."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict) and "verdicts" in data:
        return data["verdicts"]
    if isinstance(data, list):
        return data
    raise ValueError(f"Unrecognised verdict file format in {path!r}. "
                     "Expected dict with 'verdicts' key or a list.")


def load_task_ground_truths(tasks_dir: str) -> Dict[str, Dict[str, Any]]:
    """Load all T*.json task files; return mapping task_id -> ground_truth dict."""
    gts: Dict[str, Dict[str, Any]] = {}
    for fname in sorted(os.listdir(tasks_dir)):
        if not (fname.startswith("T") and fname.endswith(".json")):
            continue
        fpath = os.path.join(tasks_dir, fname)
        with open(fpath, encoding="utf-8") as f:
            task = json.load(f)
        tid = task.get("task_id", fname.replace(".json", ""))
        gts[tid] = task.get("ground_truth", {})
    return gts


# ---------------------------------------------------------------------------
# Core scoring
# ---------------------------------------------------------------------------

def score_arm_verdicts(
    verdicts: List[Dict[str, Any]],
    ground_truths: Dict[str, Dict[str, Any]],
    study_note: str,
) -> List[Dict[str, Any]]:
    """Score all verdict dicts against ground truths; return list of metric rows."""
    rows = []
    for verdict in verdicts:
        task_id = verdict.get("task_id", "UNKNOWN")
        gt = ground_truths.get(task_id)
        if gt is None:
            print(f"  WARNING: no ground truth found for task_id={task_id!r} — skipping.",
                  file=sys.stderr)
            continue
        result = compute_all(verdict, gt)
        result["study_note"] = study_note
        rows.append(result)
    return rows


def write_results_csv(rows: List[Dict[str, Any]], out_path: str) -> None:
    """Write metric rows to CSV at out_path."""
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=RESULTS_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def print_summary(rows: List[Dict[str, Any]], label: str) -> None:
    """Print a concise per-arm summary to stdout."""
    arm_rows: Dict[str, List[Dict[str, Any]]] = {}
    for r in rows:
        arm = r.get("arm", "UNKNOWN")
        arm_rows.setdefault(arm, []).append(r)

    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}")

    for arm, arm_data in sorted(arm_rows.items()):
        # Exclude sentinel -1.0 from FCR averaging
        fcr_vals = [r["false_claim_rate"] for r in arm_data if r["false_claim_rate"] >= 0]
        ocr_vals = [r["over_claim_rate"] for r in arm_data if r["ocr_d"] > 0]
        cir_vals = [r["citation_integrity"] for r in arm_data if r["cir_d"] > 0]
        rr_vals  = [r["reproducibility_rate"] for r in arm_data if r["rr_d"] > 0]

        def avg(vals: list) -> str:
            return f"{sum(vals)/len(vals):.3f}" if vals else "n/a"

        print(f"\n  ARM: {arm}  (n={len(arm_data)} tasks)")
        print(f"    false_claim_rate    (FCR): {avg(fcr_vals)}  [lower is better]")
        print(f"    over_claim_rate     (OCR): {avg(ocr_vals)}  [lower is better]")
        print(f"    citation_integrity  (CIR): {avg(cir_vals)}  [higher is better]")
        print(f"    reproducibility_rate (RR): {avg(rr_vals)}   [higher is better]")

    note = rows[0].get("study_note", "") if rows else ""
    if "FIXTURE" in note or "DEMO" in note.upper():
        print(f"\n  *** {note} ***")
        print("  These numbers are synthetic fixture data for harness validation.")
        print("  They are NOT findings. Study result: OPEN.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Cambium enforcement A/B study scorer.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run with bundled fixture outputs (FIXTURE/illustrative — not a real finding).",
    )
    parser.add_argument(
        "--treatment",
        metavar="PATH",
        help="Path to treatment arm verdict JSON file.",
    )
    parser.add_argument(
        "--baseline",
        metavar="PATH",
        help="Path to baseline arm verdict JSON file.",
    )
    parser.add_argument(
        "--tasks",
        metavar="DIR",
        default=_TASKS_DIR,
        help=f"Directory containing T*.json task files (default: {_TASKS_DIR}).",
    )
    parser.add_argument(
        "--out",
        metavar="PATH",
        default=_DEFAULT_OUT,
        help=f"Output CSV path (default: {_DEFAULT_OUT}).",
    )
    args = parser.parse_args(argv)

    # Determine verdict sources
    if args.demo:
        treatment_path = _DEMO_TREATMENT
        baseline_path = _DEMO_BASELINE
        study_note = (
            "FIXTURE/illustrative — synthetic demo data; NOT a real finding; study result: OPEN"
        )
        print("[run_study] DEMO MODE — using bundled fixture outputs.")
        print(f"  Treatment verdicts: {treatment_path}")
        print(f"  Baseline verdicts:  {baseline_path}")
    else:
        if not args.treatment or not args.baseline:
            print("ERROR: --treatment and --baseline are required unless --demo is set.",
                  file=sys.stderr)
            parser.print_help(sys.stderr)
            return 1
        treatment_path = args.treatment
        baseline_path = args.baseline
        study_note = "real-run — verify study result is OPEN until judge scoring complete"

    # Verify paths
    for label, path in [("treatment", treatment_path), ("baseline", baseline_path)]:
        if not os.path.exists(path):
            print(f"ERROR: {label} file not found: {path!r}", file=sys.stderr)
            return 1

    tasks_dir = args.tasks
    if not os.path.isdir(tasks_dir):
        print(f"ERROR: tasks directory not found: {tasks_dir!r}", file=sys.stderr)
        return 1

    # Load ground truths
    print(f"[run_study] Loading tasks from: {tasks_dir}")
    ground_truths = load_task_ground_truths(tasks_dir)
    print(f"  Loaded {len(ground_truths)} task ground truth(s): {sorted(ground_truths.keys())}")

    # Load verdicts
    print("[run_study] Loading verdicts...")
    treatment_verdicts = load_verdicts(treatment_path)
    baseline_verdicts = load_verdicts(baseline_path)
    print(f"  TREATMENT: {len(treatment_verdicts)} task verdict(s)")
    print(f"  BASELINE:  {len(baseline_verdicts)} task verdict(s)")

    # Score
    print("[run_study] Scoring...")
    treatment_rows = score_arm_verdicts(treatment_verdicts, ground_truths, study_note)
    baseline_rows  = score_arm_verdicts(baseline_verdicts, ground_truths, study_note)
    all_rows = treatment_rows + baseline_rows

    # Write CSV
    out_path = args.out
    write_results_csv(all_rows, out_path)
    print(f"[run_study] Wrote {len(all_rows)} rows to: {out_path}")

    # Print summary
    print_summary(all_rows, label="Results Summary")

    if args.demo:
        print("\n[run_study] REMINDER: --demo output is FIXTURE/illustrative data.")
        print("  Study result is OPEN. No finding exists until real agent runs complete.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
