#!/usr/bin/env python3
"""loop_costs — Four-Cost Loop Guard for Cambium (Loop Engineering paper defense).

Reports Cambium's defense against the four silent costs of agentic loops and flags
weak points.  Deterministic; std-lib only; no model calls.

Costs:
  1. VERIFICATION DEBT   — unverified claims accumulate as Asserted/Open tiers.
  2. COMPREHENSION ROT   — team stops engaging with learning artifacts.
  3. COGNITIVE SURRENDER — humans copy AI output rather than contributing genuinely.
  4. TOKEN BLOWOUT       — uncapped spend races past the project budget.

Usage:
  python3 tools/loop_costs.py [--root .] [--budget N]
  python3 tools/loop_costs.py --enforce-budget [--root .] [--budget N]

Exit codes (normal mode): 0 always (advisory).
Exit codes (--enforce-budget): 0 = under ceiling, 1 = at or over ceiling (run-aborting).
"""
from __future__ import annotations
import argparse, csv, glob as _glob, os, sys

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _read_csv(path: str) -> list[dict]:
    """Read a CSV into a list of dicts; return [] if absent or unreadable."""
    if not os.path.isfile(path):
        return []
    try:
        with open(path, newline="", encoding="utf-8") as fh:
            return list(csv.DictReader(fh))
    except Exception:
        return []


def _read_config(root: str) -> dict:
    """Read config.yml (if present) and return a plain dict (no yaml dep)."""
    cfg_path = os.path.join(root, "config.yml")
    if not os.path.isfile(cfg_path):
        return {}
    result: dict = {}
    try:
        with open(cfg_path, encoding="utf-8") as fh:
            for line in fh:
                stripped = line.strip()
                if stripped.startswith("#") or ":" not in stripped:
                    continue
                k, _, v = stripped.partition(":")
                result[k.strip()] = v.strip().split("#")[0].strip()
    except Exception:
        pass
    return result


def _heuristic_delta_col(rows: list[dict]) -> str | None:
    """Return the name of the column that tracks human-vs-AI delta/similarity."""
    candidates = ["change_ratio", "delta", "similarity", "change_ratio_or_delta"]
    for col in candidates:
        if any(col in row for row in rows):
            return col
    # Fallback: look for any column whose name contains one of the keywords
    if rows:
        for col in rows[0].keys():
            for kw in ("change", "ratio", "delta", "similar", "novel"):
                if kw in col.lower():
                    return col
    return None

# ---------------------------------------------------------------------------
# Cost 1: VERIFICATION DEBT
# ---------------------------------------------------------------------------

VALID_TIERS = {"Proved", "Code-verified", "Asserted", "Open"}
STRONG_TIERS = {"Proved", "Code-verified"}
WEAK_TIERS   = {"Asserted", "Open"}
DEBT_FLAG_RATIO   = 0.40
MIN_ROWS_FOR_ZERO_STRONG = 5


def verification_debt(root: str) -> tuple[float, bool, str]:
    """Return (debt_ratio, flagged, detail).

    debt_ratio = (Asserted + Open) / total.
    Flags if debt_ratio > 0.40, or total >= 5 with zero Code-verified/Proved.
    Gracefully degrades to advisory if ledger is absent.
    """
    ledger = os.path.join(root, "agent_outputs", "findings_ledger.csv")
    rows = _read_csv(ledger)

    if not rows:
        advisory = ("findings_ledger.csv absent — not measured (run produces no ledger yet). "
                    "Advisory: create agent_outputs/findings_ledger.csv with a claim_tier column.")
        return (0.0, False, advisory)

    # Detect the tier column (spec says claim_tier; be resilient)
    tier_col = None
    for candidate in ("claim_tier", "tier", "evidence_tier", "Tier"):
        if candidate in (rows[0].keys() if rows else {}):
            tier_col = candidate
            break
    if tier_col is None and rows:
        for col in rows[0].keys():
            if "tier" in col.lower():
                tier_col = col
                break

    if tier_col is None:
        return (0.0, False, "claim_tier column not found in findings_ledger.csv — cannot assess.")

    tiers = [r.get(tier_col, "").strip() for r in rows]
    total = len(tiers)
    if total == 0:
        return (0.0, False, "findings_ledger.csv is empty.")

    weak_count  = sum(1 for t in tiers if t in WEAK_TIERS)
    strong_count = sum(1 for t in tiers if t in STRONG_TIERS)
    ratio = weak_count / total

    flagged = False
    reasons = []
    if ratio > DEBT_FLAG_RATIO:
        reasons.append(f"debt_ratio={ratio:.2f} > threshold {DEBT_FLAG_RATIO}")
        flagged = True
    if total >= MIN_ROWS_FOR_ZERO_STRONG and strong_count == 0:
        reasons.append(f"total={total} claims but zero Code-verified/Proved")
        flagged = True

    detail = (
        f"total={total}, weak(Asserted+Open)={weak_count}, "
        f"strong(Proved+Code-verified)={strong_count}, "
        f"debt_ratio={ratio:.2f}"
    )
    if reasons:
        detail += " | FLAG: " + "; ".join(reasons)
    return (ratio, flagged, detail)

# ---------------------------------------------------------------------------
# Cost 2: COMPREHENSION ROT
# ---------------------------------------------------------------------------

COVERAGE_THRESHOLD = 0.50


def comprehension_rot(root: str) -> tuple[bool, bool, str]:
    """Return (artifact_present, flagged, detail).

    Checks for a learning artifact and optional brief_coverage from the ledger.
    Flags if no artifact found, or if brief_coverage < 0.50.
    """
    # Possible learning artifacts
    artifact_candidates = [
        os.path.join(root, "agent_outputs", "learning_packet.md"),
        os.path.join(root, "demo", "learning_lab.html"),
    ]
    # Also glob academy/labs/*.html
    academy_pattern = os.path.join(root, "academy", "labs", "*.html")
    academy_files = _glob.glob(academy_pattern)

    artifact_path = None
    for path in artifact_candidates:
        if os.path.isfile(path) and os.path.getsize(path) > 0:
            artifact_path = path
            break
    if artifact_path is None and academy_files:
        artifact_path = academy_files[0]

    artifact_present = artifact_path is not None

    # Optional: brief_coverage from contribution ledger
    ledger_path = os.path.join(root, "governance", "CONTRIBUTION_LEDGER.csv")
    rows = _read_csv(ledger_path)
    coverage: float | None = None

    if rows:
        # brief_coverage = fraction of rows with kind=="brief" and status=="complete"
        brief_rows = [r for r in rows if r.get("kind", "").strip() == "brief"]
        if brief_rows:
            complete = sum(1 for r in brief_rows if r.get("status", "").strip() == "complete")
            coverage = complete / len(brief_rows)

    flagged = False
    reasons = []
    if not artifact_present:
        reasons.append("no learning artifact found (agent_outputs/learning_packet.md, "
                       "demo/learning_lab.html, or academy/labs/*.html)")
        flagged = True
    if coverage is not None and coverage < COVERAGE_THRESHOLD:
        reasons.append(f"brief_coverage={coverage:.2f} < threshold {COVERAGE_THRESHOLD}")
        flagged = True

    detail_parts = []
    detail_parts.append(f"artifact={'found: ' + os.path.relpath(artifact_path, root) if artifact_present else 'ABSENT'}")
    if coverage is not None:
        detail_parts.append(f"brief_coverage={coverage:.2f}")
    else:
        detail_parts.append("brief_coverage=N/A (no ledger or no brief rows)")
    if reasons:
        detail_parts.append("FLAG: " + "; ".join(reasons))

    return (artifact_present, flagged, " | ".join(detail_parts))

# ---------------------------------------------------------------------------
# Cost 3: COGNITIVE SURRENDER
# ---------------------------------------------------------------------------

SURRENDER_FLAG_RATIO = 0.33
LOW_DELTA_THRESHOLD  = 0.15   # matches learning_gate.py LOW_DELTA


def cognitive_surrender(root: str) -> tuple[float, bool, str]:
    """Return (surrender_ratio, flagged, detail).

    Reads governance/CONTRIBUTION_LEDGER.csv.
    surrender_ratio = rows with low delta (copy-from-AI) / total gate rows.
    Also flags enforcement bypass: BLOCKED row that appears accepted.
    """
    ledger_path = os.path.join(root, "governance", "CONTRIBUTION_LEDGER.csv")
    rows = _read_csv(ledger_path)

    if not rows:
        return (0.0, False,
                "CONTRIBUTION_LEDGER.csv absent — not measured. Advisory: use "
                "learning_gate.py to record director contributions.")

    delta_col = _heuristic_delta_col(rows)
    col_note = f"delta_col='{delta_col}'" if delta_col else "delta_col=NOT FOUND (no change_ratio/delta column)"

    total_gate_rows = len(rows)
    surrender_count = 0
    bypass_count    = 0
    bypass_detail   = []

    for r in rows:
        status   = r.get("status", "").strip()
        copy_flag = r.get("copy_flag", "").strip()

        # Low-delta detection: either copy_flag is LOW-DELTA/REVIEW or change_ratio < threshold
        low_delta = False
        if copy_flag in ("LOW-DELTA", "REVIEW"):
            low_delta = True
        elif delta_col and delta_col in r:
            raw = r[delta_col].strip()
            # The detail cell may contain "change_ratio=0.05 ..." — extract float
            import re as _re
            m = _re.search(r"change_ratio=([0-9.]+)", raw)
            val_str = m.group(1) if m else raw
            try:
                val = float(val_str)
                # change_ratio < LOW_DELTA means < 15% novel -> high copy
                if val < LOW_DELTA_THRESHOLD:
                    low_delta = True
            except ValueError:
                pass

        if low_delta:
            surrender_count += 1

        # Enforcement bypass: BLOCKED status but row is present without re-submission
        # Heuristic: a BLOCKED row whose gate_id also has a subsequent "complete" row
        # is fine; but a BLOCKED row with no following complete sibling is suspicious only
        # if somehow the run continued. We flag literal status==BLOCKED appearing with
        # a copy_flag that says something other than BLOCKED/incomplete.
        if status == "BLOCKED" and copy_flag not in ("", "-", "BLOCKED", "incomplete"):
            bypass_count += 1
            bypass_detail.append(r.get("id", "?"))

    ratio = surrender_count / total_gate_rows if total_gate_rows else 0.0
    flagged = False
    reasons = []
    if ratio > SURRENDER_FLAG_RATIO:
        reasons.append(f"surrender_ratio={ratio:.2f} > threshold {SURRENDER_FLAG_RATIO}")
        flagged = True
    if bypass_count > 0:
        reasons.append(f"enforcement bypass detected: {bypass_count} BLOCKED row(s) appear accepted "
                       f"(gates: {', '.join(bypass_detail)})")
        flagged = True

    detail = (f"total_rows={total_gate_rows}, low_delta={surrender_count}, "
              f"surrender_ratio={ratio:.2f}, {col_note}")
    if reasons:
        detail += " | FLAG: " + "; ".join(reasons)
    return (ratio, flagged, detail)

# ---------------------------------------------------------------------------
# Cost 4: TOKEN BLOWOUT
# ---------------------------------------------------------------------------

BUDGET_WARN_PCT  = 0.80
BUDGET_HARD_PCT  = 1.00
DEFAULT_BUDGET   = 20.0


def token_blowout(root: str, budget: float | None = None) -> tuple[float, float, bool, str]:
    """Return (spent_usd, ceiling_usd, flagged, detail).

    Sums est_usd across agent_outputs/**/cost_log.csv.
    Reads run_budget_usd from config.yml if budget not supplied.
    Flags at >= 80% (warn) and >= 100% (hard cap).
    """
    # Determine ceiling
    if budget is not None:
        ceiling = float(budget)
        ceiling_src = "CLI --budget"
    else:
        cfg = _read_config(root)
        raw = cfg.get("run_budget_usd", "")
        try:
            ceiling = float(raw) if raw else DEFAULT_BUDGET
            ceiling_src = "config.yml" if raw else f"default ({DEFAULT_BUDGET})"
        except ValueError:
            ceiling = DEFAULT_BUDGET
            ceiling_src = f"default ({DEFAULT_BUDGET}) — config.yml value unreadable"

    # Find cost_log files
    cost_log_pattern = os.path.join(root, "agent_outputs", "**", "cost_log.csv")
    cost_logs = _glob.glob(cost_log_pattern, recursive=True)

    if not cost_logs:
        detail = (f"cost_log.csv absent — not measured (only written in --live runs). "
                  f"ceiling={ceiling:.2f} ({ceiling_src}).")
        return (0.0, ceiling, False, detail)

    spent = 0.0
    missing_col_files = []
    for path in cost_logs:
        rows = _read_csv(path)
        col_found = False
        for r in rows:
            for col in ("est_usd", "cost_usd", "usd", "cost"):
                if col in r:
                    try:
                        spent += float(r[col])
                        col_found = True
                    except ValueError:
                        pass
                    break
        if not col_found and rows:
            missing_col_files.append(os.path.relpath(path, root))

    pct = spent / ceiling if ceiling else 0.0
    flagged = pct >= BUDGET_WARN_PCT

    reasons = []
    if pct >= BUDGET_HARD_PCT:
        reasons.append(f"OVER BUDGET: spent={spent:.4f} >= ceiling={ceiling:.2f} (100%)")
    elif pct >= BUDGET_WARN_PCT:
        reasons.append(f"APPROACHING BUDGET: spent={spent:.4f} is {pct:.0%} of ceiling={ceiling:.2f}")

    detail = (f"spent={spent:.4f} USD, ceiling={ceiling:.2f} USD ({ceiling_src}), "
              f"pct={pct:.1%}, cost_logs={len(cost_logs)}")
    if missing_col_files:
        detail += f" | WARNING: est_usd col absent in: {', '.join(missing_col_files)}"
    if reasons:
        detail += " | FLAG: " + "; ".join(reasons)
    return (spent, ceiling, flagged, detail)

# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def report(root: str, budget: float | None = None) -> dict:
    """Run all four cost checks and return a result dict."""
    root = os.path.abspath(root)

    debt_ratio,  c1_flag, c1_detail = verification_debt(root)
    _art,        c2_flag, c2_detail = comprehension_rot(root)
    surr_ratio,  c3_flag, c3_detail = cognitive_surrender(root)
    spent, ceil, c4_flag, c4_detail = token_blowout(root, budget)

    return {
        "root": root,
        "costs": {
            "C1_verification_debt":   {"flagged": c1_flag, "detail": c1_detail},
            "C2_comprehension_rot":   {"flagged": c2_flag, "detail": c2_detail},
            "C3_cognitive_surrender": {"flagged": c3_flag, "detail": c3_detail},
            "C4_token_blowout":       {"flagged": c4_flag, "detail": c4_detail},
        },
        "any_flagged": any([c1_flag, c2_flag, c3_flag, c4_flag]),
    }


def _print_report(r: dict) -> None:
    print("=" * 72)
    print("Cambium Four-Cost Loop Guard")
    print(f"Root: {r['root']}")
    print("=" * 72)
    labels = {
        "C1_verification_debt":   "Cost 1  VERIFICATION DEBT",
        "C2_comprehension_rot":   "Cost 2  COMPREHENSION ROT",
        "C3_cognitive_surrender": "Cost 3  COGNITIVE SURRENDER",
        "C4_token_blowout":       "Cost 4  TOKEN BLOWOUT",
    }
    for key, label in labels.items():
        v = r["costs"][key]
        status = "FLAG" if v["flagged"] else "ok  "
        print(f"  [{status}] {label}")
        print(f"          {v['detail']}")
    print("-" * 72)
    if r["any_flagged"]:
        print("RESULT: one or more costs flagged — review before continuing the run.")
    else:
        print("RESULT: all four costs within thresholds.")
    print("=" * 72)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Cambium four-cost loop guard (loop engineering paper defense).")
    ap.add_argument("--root", default=".", help="project root (default: cwd)")
    ap.add_argument("--budget", type=float, default=None,
                    help="override run_budget_usd ceiling (USD)")
    ap.add_argument("--enforce-budget", action="store_true",
                    help="exit 1 if Cost 4 >= 100%% of ceiling (run-aborting cap)")
    a = ap.parse_args(argv)

    root = os.path.abspath(a.root)

    if a.enforce_budget:
        spent, ceiling, flagged, detail = token_blowout(root, a.budget)
        pct = spent / ceiling if ceiling else 0.0
        at_or_over = pct >= BUDGET_HARD_PCT
        print(f"[loop_costs --enforce-budget] {detail}")
        if at_or_over:
            print("ABORT: run budget ceiling reached or exceeded. Halt before spawning more work.")
            return 1
        print("OK: under budget ceiling.")
        return 0

    r = report(root, a.budget)
    _print_report(r)
    return 0


if __name__ == "__main__":
    sys.exit(main())
