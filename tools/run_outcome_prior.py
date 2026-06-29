#!/usr/bin/env python3
"""
run_outcome_prior.py -- Heuristic prior over historical logs for Cambium runs.

HONESTY NOTE: This is a statistical prior derived from past run history, NOT a
learned latent-space world model. It never blocks a run. On small samples
(< 5 historical gates) it refuses to fabricate a risk estimate. Cost estimates
from price-table fallback are labeled "uncalibrated". Treat all outputs as
rough guidance to inform dry-run planning, not as guarantees.

Usage:
  python3 tools/run_outcome_prior.py "<task>" [--root <path>]
"""

import os
import sys
import csv
import re
import glob as _glob

ROOT_DEFAULT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Price table (USD per 1M tokens, input and output) -- mirrors cambium_run.py.
# Update when model pricing changes.
PRICE = {
    "claude-opus-4-8":           (15.0, 75.0),
    "claude-sonnet-4-6":         (3.0,  15.0),
    "claude-haiku-4-5-20251001": (0.80,  4.0),
}
# Default token assumption when no history exists (documented assumption).
DEFAULT_INPUT_TOKENS  = 2_000   # typical system + task prompt
DEFAULT_OUTPUT_TOKENS = 800     # typical response
DEFAULT_MODEL         = "claude-sonnet-4-6"

MIN_GATES_FOR_RISK = 5  # refuse fabricating a rate below this threshold


# ---------------------------------------------------------------------------
# Cost estimation
# ---------------------------------------------------------------------------

def _collect_cost_logs(root):
    """
    Return list of dicts parsed from all cost_log.csv files under agent_outputs/.

    Uses glob with recursive=True so agent_outputs/cost_log.csv (top-level, written
    by cambium_run.py) and any sub-directory cost_log.csv files are all captured.
    Deduplicates by resolved path to avoid double-counting.
    """
    pattern = os.path.join(root, "agent_outputs", "**", "cost_log.csv")
    seen = set()
    rows = []
    for path in _glob.glob(pattern, recursive=True):
        norm = os.path.normcase(os.path.abspath(path))
        if norm in seen:
            continue
        seen.add(norm)
        try:
            with open(path, newline="", encoding="utf-8", errors="replace") as fh:
                reader = csv.DictReader(fh)
                for row in reader:
                    rows.append(row)
        except Exception:
            continue
    return rows


def _avg_cost_per_agent_from_history(rows):
    """
    Return (avg_usd_per_agent, agent_count_in_history) from parsed cost log rows.
    Averages est_usd across all individual agent invocations.
    """
    costs = []
    for row in rows:
        try:
            val = float(row.get("est_usd", "") or 0)
            costs.append(val)
        except (ValueError, TypeError):
            continue
    if not costs:
        return None, 0
    return sum(costs) / len(costs), len(costs)


def _price_table_cost_per_agent(model=DEFAULT_MODEL):
    """
    Fallback cost estimate using the PRICE table and documented default token counts.
    Returns (point_usd, note_string).
    """
    pin, pout = PRICE.get(model, PRICE[DEFAULT_MODEL])
    cost = (DEFAULT_INPUT_TOKENS / 1e6 * pin) + (DEFAULT_OUTPUT_TOKENS / 1e6 * pout)
    note = (
        "uncalibrated (price-table fallback; assumes %d input + %d output tokens per agent "
        "at %s pricing; no historical data available)"
        % (DEFAULT_INPUT_TOKENS, DEFAULT_OUTPUT_TOKENS, model)
    )
    return cost, note


def _count_agents_in_plan(plan):
    """Count total agent invocations across all phases and groups in a route() plan."""
    total = 0
    for phase in plan.get("phases", []):
        for group in phase.get("groups", []):
            total += len(group.get("agents", []))
    return total


def estimate_cost(plan, root):
    """
    Estimate run cost given a route() plan dict and repo root.

    Returns dict with keys: point_usd, low_usd, high_usd, basis, calibrated.
    """
    n_agents = _count_agents_in_plan(plan)
    if n_agents == 0:
        n_agents = 1

    rows = _collect_cost_logs(root)
    avg, history_count = _avg_cost_per_agent_from_history(rows)

    if avg is not None:
        point = avg * n_agents
        # Uncertainty band: +/-50% (heuristic; real variance can be larger)
        low  = point * 0.5
        high = point * 1.5
        basis = (
            "historical average $%.5f/agent over %d logged invocations; "
            "plan has %d agent slots; point = avg x slots"
            % (avg, history_count, n_agents)
        )
        calibrated = True
    else:
        per_agent, fallback_note = _price_table_cost_per_agent()
        point = per_agent * n_agents
        low  = point * 0.5
        high = point * 2.0   # wider band when uncalibrated
        basis = fallback_note + ("; plan has %d agent slots" % n_agents)
        calibrated = False

    return {
        "point_usd": round(point, 6),
        "low_usd":   round(low,   6),
        "high_usd":  round(high,  6),
        "basis":     basis,
        "calibrated": calibrated,
    }


# ---------------------------------------------------------------------------
# Risk estimation
# ---------------------------------------------------------------------------

# Match outcome keywords in the GATES.md approval-log table rows.
_APPROVE_RE = re.compile(r"\bAPPROVE\b", re.IGNORECASE)
_REVISE_RE  = re.compile(r"\bREVISE\b",  re.IGNORECASE)
_REJECT_RE  = re.compile(r"\bREJECT\b",  re.IGNORECASE)


def _parse_gates_md(root):
    """
    Parse governance/GATES.md for historical gate outcomes.

    Returns (n_approve, n_revise_or_reject, total_gates).
    Only counts rows from the '## Approvals log' section that have a
    recognisable APPROVE/REVISE/REJECT keyword in the Decision column.
    """
    gates_path = os.path.join(root, "governance", "GATES.md")
    if not os.path.isfile(gates_path):
        return 0, 0, 0

    try:
        text = open(gates_path, encoding="utf-8", errors="replace").read()
    except Exception:
        return 0, 0, 0

    # Locate the approvals log section
    log_start = text.find("## Approvals log")
    if log_start == -1:
        log_start = 0
    log_text = text[log_start:]

    n_approve = 0
    n_revise_reject = 0

    # Parse markdown table rows: lines starting with '|' that are not header/separator
    for line in log_text.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        # Skip header and separator rows
        if re.match(r"^\|\s*[-:]+", line) or ("Gate" in line and "Decision" in line):
            continue
        # Check for outcome keywords anywhere in the line
        has_approve = bool(_APPROVE_RE.search(line))
        has_revise  = bool(_REVISE_RE.search(line))
        has_reject  = bool(_REJECT_RE.search(line))
        if has_approve or has_revise or has_reject:
            if has_revise or has_reject:
                n_revise_reject += 1
            else:
                n_approve += 1

    total = n_approve + n_revise_reject
    return n_approve, n_revise_reject, total


def estimate_risk(root):
    """
    Estimate risk category from historical REVISE+REJECT rate at gates.

    Returns dict with keys: risk_level, revise_reject_rate, total_gates, basis.
    """
    n_approve, n_bad, total = _parse_gates_md(root)

    if total < MIN_GATES_FOR_RISK:
        return {
            "risk_level": "unknown (insufficient history)",
            "revise_reject_rate": None,
            "total_gates": total,
            "basis": (
                "only %d historical gate outcome(s) found; need >= %d for a reliable "
                "base-rate estimate; refusing to fabricate a risk level"
                % (total, MIN_GATES_FOR_RISK)
            ),
        }

    rate = n_bad / total
    if rate < 0.15:
        level = "low"
    elif rate > 0.40:
        level = "high"
    else:
        level = "medium"

    return {
        "risk_level": level,
        "revise_reject_rate": round(rate, 4),
        "total_gates": total,
        "basis": (
            "%d gates parsed; %d APPROVE, %d REVISE/REJECT; "
            "base rate %.1f%% maps to '%s'"
            % (total, n_approve, n_bad, rate * 100, level)
        ),
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def predict(task_or_plan, root="."):
    """
    Predict cost and risk for a Cambium run BEFORE it executes.

    Parameters
    ----------
    task_or_plan : str or dict
        A task string (passed through task_router.route) or an already-routed
        plan dict.
    root : str
        Repo root directory.

    Returns
    -------
    dict with keys:
        predicted_cost_usd  -- dict: point, low, high, calibrated
        predicted_risk      -- str: low / medium / high / unknown ...
        basis               -- dict: cost_basis, risk_basis
        confidence          -- str: plain-language confidence note
    """
    root = os.path.abspath(root)

    # --- resolve plan ---
    if isinstance(task_or_plan, dict):
        plan = task_or_plan
        task_str = plan.get("task", "<plan>")
    else:
        task_str = str(task_or_plan)
        # Import task_router from the tools directory next to this file
        tools_dir = os.path.join(root, "tools")
        if tools_dir not in sys.path:
            sys.path.insert(0, tools_dir)
        import task_router
        plan = task_router.route(task_str)

    cost_info = estimate_cost(plan, root)
    risk_info = estimate_risk(root)

    calibrated = cost_info["calibrated"]
    risk_level = risk_info["risk_level"]
    total_gates = risk_info["total_gates"]

    # Build confidence note
    parts = []
    if not calibrated:
        parts.append("cost is uncalibrated (no run history; price-table fallback used)")
    else:
        parts.append("cost calibrated from run history")
    if total_gates < MIN_GATES_FOR_RISK:
        parts.append("risk unknown (< %d historical gates)" % MIN_GATES_FOR_RISK)
    else:
        parts.append("risk based on %d historical gates" % total_gates)
    parts.append(
        "this is a heuristic prior to inform the dry-run plan, not a guarantee; "
        "small samples make it unreliable; it never blocks a run"
    )
    confidence = "; ".join(parts)

    return {
        "task": task_str,
        "plan_type": plan.get("type", "unknown"),
        "n_agents": plan.get("n_agents", 0),
        "predicted_cost_usd": {
            "point":      cost_info["point_usd"],
            "low":        cost_info["low_usd"],
            "high":       cost_info["high_usd"],
            "calibrated": calibrated,
        },
        "predicted_risk": risk_level,
        "basis": {
            "cost": cost_info["basis"],
            "risk": risk_info["basis"],
        },
        "confidence": confidence,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _fmt(result):
    lines = [
        "=" * 64,
        "CAMBIUM RUN-OUTCOME PRIOR",
        "=" * 64,
        "Task            : %s" % result["task"],
        "Plan type       : %s  |  Agent slots: %d" % (result["plan_type"], result["n_agents"]),
        "",
        "--- COST ESTIMATE ---",
        "  Point estimate : $%.5f" % result["predicted_cost_usd"]["point"],
        "  Range          : $%.5f -- $%.5f" % (
            result["predicted_cost_usd"]["low"],
            result["predicted_cost_usd"]["high"],
        ),
        "  Calibrated?    : %s" % (
            "yes (historical data)" if result["predicted_cost_usd"]["calibrated"]
            else "NO (uncalibrated; price-table fallback)"
        ),
        "  Basis          : %s" % result["basis"]["cost"],
        "",
        "--- RISK ESTIMATE ---",
        "  Risk level     : %s" % result["predicted_risk"],
        "  Basis          : %s" % result["basis"]["risk"],
        "",
        "--- CONFIDENCE ---",
        "  %s" % result["confidence"],
        "",
        "[!] HEURISTIC PRIOR, NOT A WORLD MODEL; small-sample caveats apply.",
        "    This prior informs the dry-run plan only and never blocks a run.",
        "=" * 64,
    ]
    return "\n".join(lines)


def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(
            "Usage: python3 tools/run_outcome_prior.py \"<task>\" [--root <path>]\n"
            "       Prints a heuristic cost+risk prior from historical run logs.\n"
            "       NOT a world model; never blocks a run."
        )
        return 0

    task = args[0]
    root = "."
    if "--root" in args:
        i = args.index("--root")
        if i + 1 < len(args):
            root = args[i + 1]

    result = predict(task, root=root)
    print(_fmt(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
