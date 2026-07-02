#!/usr/bin/env python3
"""power_calc -- deterministic power and sample-size calculator (normal approximations).

Computes required per-group sample size, or achieved power with --n, for
three common designs, using large-sample normal approximations and nothing
beyond the Python standard library. Results are fully deterministic.

Notation: Phi is the standard normal CDF; z_a = Phi-inverse(1 - alpha) for
a one-sided test or Phi-inverse(1 - alpha/2) for two-sided; z_b =
Phi-inverse(power); q = 1 - p.

Subcommands and formulas:

  two-prop   two independent proportions, pooled variance under H0, no
             continuity correction (Fleiss, Statistical Methods for Rates
             and Proportions, 2nd ed., 1981):
               n per group = (z_a*sqrt(2*pb*qb) + z_b*sqrt(p1*q1 + p2*q2))^2
                             / (p1 - p2)^2,   pb = (p1 + p2)/2
               power at n  = Phi((|p1-p2|*sqrt(n) - z_a*sqrt(2*pb*qb))
                                 / sqrt(p1*q1 + p2*q2))

  two-mean   two independent means, standardized effect size Cohen's d,
             normal approximation to the two-sample t test (Cohen,
             Statistical Power Analysis for the Behavioral Sciences,
             2nd ed., 1988):
               n per group = 2 * ((z_a + z_b) / d)^2
               power at n  = Phi(|d|*sqrt(n/2) - z_a)

  corr       one Pearson correlation against zero, Fisher z transform
             (Cohen 1988):
               n total     = ((z_a + z_b) / atanh(|r|))^2 + 3
               power at n  = Phi(atanh(|r|)*sqrt(n - 3) - z_a)

Formulas encoded 2026-07-01 from the sources named above.

Honest limits: these are large-sample approximations. They ignore the t
distribution's heavier tails, continuity corrections, unequal group sizes,
clustering, and attrition, so small-sample answers can differ from exact
methods by a few units. Output is advisory, not a certification. Have a
statistician confirm the calculation for high-stakes, regulatory, or
grant-critical designs.

Exit codes:
  0  -- calculation printed
  1  -- invalid input values
  2  -- argparse usage errors (argparse default)

Usage:
  python3 tools/power_calc.py two-prop --p1 0.30 --p2 0.15 --alpha 0.05 --tail one --power 0.80
  python3 tools/power_calc.py two-prop --p1 0.30 --p2 0.15 --tail one --n 95
  python3 tools/power_calc.py two-mean --d 0.5
  python3 tools/power_calc.py corr --r 0.3 --out power.md
"""
from __future__ import annotations
import argparse
import math
import os
import sys
from statistics import NormalDist

# UTF-8 stdout guard
import cambium_io  # noqa: F401

TOOL = "power_calc"
_ND = NormalDist()

HONEST_NOTE = (
    "Large-sample normal approximations: the t distribution, continuity "
    "corrections, unequal groups, clustering, and attrition are not modeled, "
    "so small-sample answers can differ from exact methods by a few units. "
    "This output is advisory, not a certification. Have a statistician "
    "confirm the calculation for high-stakes, regulatory, or grant-critical "
    "designs."
)


def _fail(msg: str) -> None:
    print(f"[{TOOL}] ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def _z_alpha(alpha: float, tail: str) -> float:
    return _ND.inv_cdf(1 - alpha) if tail == "one" else _ND.inv_cdf(1 - alpha / 2)


def _ceil(x: float) -> int:
    return int(math.ceil(round(x, 10)))


def _check_alpha_power(args) -> None:
    if not 0.0 < args.alpha < 1.0:
        _fail(f"--alpha must be strictly between 0 and 1, got {args.alpha}")
    if args.n is None and not 0.0 < args.power < 1.0:
        _fail(f"--power must be strictly between 0 and 1, got {args.power}")


# ---------------------------------------------------------------------------
# Formulas (see docstring for sources)
# ---------------------------------------------------------------------------

def two_prop_n(p1: float, p2: float, alpha: float, power: float, tail: str) -> float:
    za, zb = _z_alpha(alpha, tail), _ND.inv_cdf(power)
    pb = (p1 + p2) / 2.0
    num = (za * math.sqrt(2.0 * pb * (1.0 - pb))
           + zb * math.sqrt(p1 * (1.0 - p1) + p2 * (1.0 - p2))) ** 2
    return num / (p1 - p2) ** 2


def two_prop_power(p1: float, p2: float, n: int, alpha: float, tail: str) -> float:
    za = _z_alpha(alpha, tail)
    pb = (p1 + p2) / 2.0
    zb = ((abs(p1 - p2) * math.sqrt(n) - za * math.sqrt(2.0 * pb * (1.0 - pb)))
          / math.sqrt(p1 * (1.0 - p1) + p2 * (1.0 - p2)))
    return _ND.cdf(zb)


def two_mean_n(d: float, alpha: float, power: float, tail: str) -> float:
    za, zb = _z_alpha(alpha, tail), _ND.inv_cdf(power)
    return 2.0 * ((za + zb) / abs(d)) ** 2


def two_mean_power(d: float, n: int, alpha: float, tail: str) -> float:
    za = _z_alpha(alpha, tail)
    return _ND.cdf(abs(d) * math.sqrt(n / 2.0) - za)


def corr_n(r: float, alpha: float, power: float, tail: str) -> float:
    za, zb = _z_alpha(alpha, tail), _ND.inv_cdf(power)
    return ((za + zb) / math.atanh(abs(r))) ** 2 + 3.0


def corr_power(r: float, n: int, alpha: float, tail: str) -> float:
    za = _z_alpha(alpha, tail)
    return _ND.cdf(math.atanh(abs(r)) * math.sqrt(n - 3.0) - za)


# ---------------------------------------------------------------------------
# Report builder
# ---------------------------------------------------------------------------

def build_report(test_desc: str, inputs_desc: str, formula: str,
                 mode_lines: list[str], alpha: float, tail: str, za: float) -> str:
    lines: list[str] = []
    lines.append("# Power calculation (normal approximation, advisory)")
    lines.append("")
    lines.append(f"- Test: {test_desc}")
    lines.append(f"- Inputs: {inputs_desc}")
    lines.append(f"- Tail: {tail}-sided, alpha={alpha:g}, z_alpha={za:.6f}")
    lines.append("")
    lines.append("## Result")
    lines.append("")
    lines.extend(mode_lines)
    lines.append("")
    lines.append("## Formula used")
    lines.append("")
    lines.append(f"    {formula}")
    lines.append("")
    lines.append("## Honest note")
    lines.append("")
    lines.append(HONEST_NOTE)
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Subcommand runners
# ---------------------------------------------------------------------------

def run_two_prop(args) -> str:
    for name, p in (("--p1", args.p1), ("--p2", args.p2)):
        if not 0.0 < p < 1.0:
            _fail(f"{name} must be strictly between 0 and 1, got {p}")
    if args.p1 == args.p2:
        _fail("--p1 and --p2 must differ; there is no effect to detect when they are equal")
    _check_alpha_power(args)
    za = _z_alpha(args.alpha, args.tail)
    desc = "two independent proportions (pooled z test, no continuity correction)"
    formula = ("n per group = (z_a*sqrt(2*pb*(1-pb)) + z_b*sqrt(p1*(1-p1)+p2*(1-p2)))^2"
               " / (p1-p2)^2")
    if args.n is not None:
        if args.n < 2:
            _fail("--n must be at least 2 per group")
        power = two_prop_power(args.p1, args.p2, args.n, args.alpha, args.tail)
        mode = [f"- Achieved power = {power:.4f} at n = {args.n} per group (total N = {2 * args.n})"]
        inputs = f"p1={args.p1:g}, p2={args.p2:g}, n={args.n} per group"
    else:
        exact = two_prop_n(args.p1, args.p2, args.alpha, args.power, args.tail)
        n = _ceil(exact)
        power_at = two_prop_power(args.p1, args.p2, n, args.alpha, args.tail)
        mode = [
            f"- Required n = {n} per group (unrounded {exact:.3f})",
            f"- Total N = {2 * n}",
            f"- Power at n={n} per group: {power_at:.4f} (target {args.power:g})",
        ]
        inputs = f"p1={args.p1:g}, p2={args.p2:g}, target power={args.power:g}"
    return build_report(desc, inputs, formula, mode, args.alpha, args.tail, za)


def run_two_mean(args) -> str:
    if args.d == 0:
        _fail("--d must be nonzero; there is no effect to detect at d = 0")
    _check_alpha_power(args)
    za = _z_alpha(args.alpha, args.tail)
    desc = ("two independent means, standardized effect (Cohen's d), "
            "normal approximation to the two-sample t test")
    formula = "n per group = 2 * ((z_a + z_b) / d)^2"
    if args.n is not None:
        if args.n < 2:
            _fail("--n must be at least 2 per group")
        power = two_mean_power(args.d, args.n, args.alpha, args.tail)
        mode = [f"- Achieved power = {power:.4f} at n = {args.n} per group (total N = {2 * args.n})"]
        inputs = f"d={args.d:g}, n={args.n} per group"
    else:
        exact = two_mean_n(args.d, args.alpha, args.power, args.tail)
        n = _ceil(exact)
        power_at = two_mean_power(args.d, n, args.alpha, args.tail)
        mode = [
            f"- Required n = {n} per group (unrounded {exact:.3f})",
            f"- Total N = {2 * n}",
            f"- Power at n={n} per group: {power_at:.4f} (target {args.power:g})",
        ]
        inputs = f"d={args.d:g}, target power={args.power:g}"
    return build_report(desc, inputs, formula, mode, args.alpha, args.tail, za)


def run_corr(args) -> str:
    if not 0.0 < abs(args.r) < 1.0:
        _fail(f"--r must satisfy 0 < |r| < 1, got {args.r}")
    _check_alpha_power(args)
    za = _z_alpha(args.alpha, args.tail)
    desc = "one Pearson correlation against zero (Fisher z transform)"
    formula = "n = ((z_a + z_b) / atanh(|r|))^2 + 3"
    if args.n is not None:
        if args.n < 4:
            _fail("--n must be at least 4 for the Fisher z approximation")
        power = corr_power(args.r, args.n, args.alpha, args.tail)
        mode = [f"- Achieved power = {power:.4f} at n = {args.n} (single sample)"]
        inputs = f"r={args.r:g}, n={args.n}"
    else:
        exact = corr_n(args.r, args.alpha, args.power, args.tail)
        n = _ceil(exact)
        power_at = corr_power(args.r, n, args.alpha, args.tail)
        mode = [
            f"- Required n = {n} (single sample; unrounded {exact:.3f})",
            f"- Power at n={n}: {power_at:.4f} (target {args.power:g})",
        ]
        inputs = f"r={args.r:g}, target power={args.power:g}"
    return build_report(desc, inputs, formula, mode, args.alpha, args.tail, za)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(
        description=(
            "Deterministic power and sample-size calculator using large-sample "
            "normal approximations. Advisory, not a certification; have a "
            "statistician confirm high-stakes designs."
        )
    )
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--alpha", type=float, default=0.05,
                        help="Type I error rate (default 0.05).")
    common.add_argument("--power", type=float, default=0.80,
                        help="Target power when solving for n (default 0.80).")
    common.add_argument("--tail", choices=("one", "two"), default="two",
                        help="One- or two-sided test (default two).")
    common.add_argument("--n", type=int, default=None,
                        help="If given, report achieved power at this n instead of solving for n.")
    common.add_argument("--out", default=None,
                        help="Output path (default: print to stdout).")

    sub = ap.add_subparsers(dest="command", required=True)
    sp = sub.add_parser("two-prop", parents=[common],
                        help="Two independent proportions (pooled z test).")
    sp.add_argument("--p1", type=float, required=True, help="Proportion in group 1.")
    sp.add_argument("--p2", type=float, required=True, help="Proportion in group 2.")
    sm = sub.add_parser("two-mean", parents=[common],
                        help="Two independent means via Cohen's d.")
    sm.add_argument("--d", type=float, required=True,
                    help="Standardized effect size (Cohen's d), nonzero.")
    sc = sub.add_parser("corr", parents=[common],
                        help="One Pearson correlation against zero (Fisher z).")
    sc.add_argument("--r", type=float, required=True,
                    help="Expected correlation, 0 < |r| < 1.")
    args = ap.parse_args(argv)

    if args.command == "two-prop":
        report = run_two_prop(args)
    elif args.command == "two-mean":
        report = run_two_mean(args)
    else:
        report = run_corr(args)

    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(report)
        print(f"[{TOOL}] wrote {args.out}")
    else:
        sys.stdout.write(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
