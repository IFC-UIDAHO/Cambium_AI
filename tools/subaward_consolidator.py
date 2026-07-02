#!/usr/bin/env python3
"""subaward_consolidator -- multi-site proposal budget roll-up (advisory).

Rolls up direct and indirect (F&A) costs across a prime site and subaward
sites, per year and overall, showing every arithmetic step. Advisory only:
this is a review aid, not a rate agreement, not an institutional approval,
and not a compliance determination. All numbers come from your input file;
the tool invents no rates, caps, or exclusions. MTDC is named here only as a
base label you assign; its regulatory definition lives in 2 CFR 200.1 and is
not encoded or applied by this tool.

Input (--sites YAML):
  sites:
    - name: Prime U
      role: prime                    # prime | sub
      direct_costs: [100000, 105000] # one entry per budget year
      fna_rate: 0.55                 # decimal fraction: 0.55 means 55 percent
      fna_base: mtdc                 # mtdc | tdc
      exclusions:                    # optional; applied only when fna_base is mtdc
        - {label: equipment, amounts: [20000, 0]}
      first25k_amounts: [25000, 0]   # optional add-back, see below
    - name: Sub College
      role: sub
      direct_costs: [50000, 52000]
      fna_rate: 0.40
      fna_base: tdc

Base arithmetic per site and year:
  - tdc:  base = direct_costs[year]
  - mtdc: base = direct_costs[year] - sum(exclusion amounts[year])
          (+ first25k_amounts[year] when first25k_amounts is provided)
  - indirect = base x fna_rate;  total = direct + indirect

First-25k handling is applied ONLY where you supply first25k_amounts: the
includable first-25000 portion of each subaward, per year, computed by you.
The tool never assumes or derives a 25k split on its own.

Flags:
  - missing fna_rate (indirect reported as 0.00 and marked not computed)
  - fna_rate above 1.0 (over 100 percent) or negative
  - negative direct costs, exclusion amounts, first25k amounts, or a
    negative MTDC base after exclusions
  - exclusions supplied with a tdc base (ignored under tdc, as stated)
  - zero or more than one prime site
  - a site listing fewer years of direct costs than the longest site
    (missing years treated as 0.00)
  - a sub site's overall total above --ceiling, when --ceiling is given

Exit codes:
  0 -- roll-up complete (flags are reported in the body)
  1 -- invalid input (missing, unreadable, or malformed YAML; non-numeric
       amounts; unknown role or fna_base), or any FLAG when --strict is given

Usage:
  python3 tools/subaward_consolidator.py --sites sites.yml
  python3 tools/subaward_consolidator.py --sites sites.yml --ceiling 250000 --strict
  python3 tools/subaward_consolidator.py --sites sites.yml --out rollup.md

Limits (honest):
  - Arithmetic on stated inputs only. The tool does not know negotiated rate
    agreements, sponsor caps, or what your institution counts in MTDC.
  - Display is rounded to 2 decimals; computation uses full float precision.
"""
from __future__ import annotations
import argparse
import os
import sys

import yaml

# UTF-8 stdout guard
import cambium_io  # noqa: F401

ROLES = ("prime", "sub")
BASES = ("mtdc", "tdc")
EPS = 1e-9


# ---------------------------------------------------------------------------
# Loader and validation
# ---------------------------------------------------------------------------

def _fail(msg: str) -> None:
    print(f"[subaward_consolidator] ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def _load_yaml(path: str) -> dict:
    if not os.path.exists(path):
        _fail(f"sites file not found: {path}")
    try:
        with open(path, encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
    except yaml.YAMLError as exc:
        _fail(f"sites file is not valid YAML: {path}\n  {exc}")
    except OSError as exc:
        _fail(f"cannot read sites file: {path}\n  {exc}")
    if not isinstance(data, dict) or not isinstance(data.get("sites"), list) or not data["sites"]:
        _fail(f"sites file must be a YAML mapping with a non-empty 'sites' list: {path}")
    return data


def _num(value, ctx: str) -> float:
    if isinstance(value, bool) or value is None:
        _fail(f"amount is not numeric for {ctx}: {value!r}")
    try:
        return float(value)
    except (TypeError, ValueError):
        _fail(f"amount is not numeric for {ctx}: {value!r}")
    return 0.0  # unreachable


def _num_list(values, ctx: str) -> list[float]:
    if not isinstance(values, list):
        _fail(f"{ctx} must be a list of numbers, got: {values!r}")
    return [_num(v, f"{ctx}[{i}]") for i, v in enumerate(values)]


def _pad(values: list[float], years: int) -> list[float]:
    return values + [0.0] * (years - len(values))


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------

def analyze(data: dict, ceiling: float | None = None) -> dict:
    """Compute per-site and rolled-up costs. Returns sites, rollup, years, flags."""
    flags: list[str] = []
    raw_sites = data["sites"]

    parsed = []
    for si, site in enumerate(raw_sites, start=1):
        if not isinstance(site, dict):
            _fail(f"sites[{si}] is not a mapping")
        name = str(site.get("name") or f"site {si}")
        role = site.get("role")
        if role not in ROLES:
            _fail(f"{name}: unknown role {role!r} (expected one of: {', '.join(ROLES)})")
        base_kind = site.get("fna_base")
        if base_kind not in BASES:
            _fail(f"{name}: unknown fna_base {base_kind!r} (expected one of: {', '.join(BASES)})")
        directs = _num_list(site.get("direct_costs"), f"{name} direct_costs")
        rate = site.get("fna_rate")
        if rate is not None:
            rate = _num(rate, f"{name} fna_rate")
        exclusions = []
        for ei, exc in enumerate(site.get("exclusions") or [], start=1):
            if not isinstance(exc, dict):
                _fail(f"{name}: exclusions[{ei}] is not a mapping")
            exclusions.append({
                "label": str(exc.get("label") or f"exclusion {ei}"),
                "amounts": _num_list(exc.get("amounts"), f"{name} exclusions[{ei}].amounts"),
            })
        first25k = site.get("first25k_amounts")
        if first25k is not None:
            first25k = _num_list(first25k, f"{name} first25k_amounts")
        parsed.append({"name": name, "role": role, "base_kind": base_kind,
                       "directs": directs, "rate": rate, "exclusions": exclusions,
                       "first25k": first25k})

    years = max(len(s["directs"]) for s in parsed)

    n_prime = sum(1 for s in parsed if s["role"] == "prime")
    if n_prime != 1:
        flags.append(f"Expected exactly one prime site; found {n_prime}.")

    sites_out = []
    for s in parsed:
        name = s["name"]
        if len(s["directs"]) < years:
            flags.append(f"{name}: lists {len(s['directs'])} year(s) of direct costs while the "
                         f"budget spans {years}; missing years treated as 0.00.")
        directs = _pad(s["directs"], years)
        rate = s["rate"]
        if rate is None:
            flags.append(f"{name}: fna_rate is missing; indirects reported as 0.00, not computed.")
        else:
            if rate > 1.0 + EPS:
                flags.append(f"{name}: fna_rate {rate:g} is greater than 1.0 "
                             f"(over 100 percent). Check the stated rate.")
            if rate < 0:
                flags.append(f"{name}: fna_rate {rate:g} is negative.")
        if s["exclusions"] and s["base_kind"] == "tdc":
            flags.append(f"{name}: exclusions supplied but fna_base is tdc; exclusions were "
                         f"ignored, as documented.")

        excl_by_year = [0.0] * years
        for exc in s["exclusions"]:
            amounts = _pad(exc["amounts"], years)
            for y in range(years):
                if amounts[y] < 0:
                    flags.append(f"{name}: negative exclusion amount {amounts[y]:g} "
                                 f"({exc['label']}, year {y + 1}).")
                excl_by_year[y] += amounts[y]
        add_by_year = _pad(s["first25k"], years) if s["first25k"] is not None else [0.0] * years

        per_year = []
        for y in range(years):
            direct = directs[y]
            if direct < 0:
                flags.append(f"{name}: negative direct cost {direct:g} in year {y + 1}.")
            add = add_by_year[y]
            if add < 0:
                flags.append(f"{name}: negative first25k amount {add:g} in year {y + 1}.")
            if s["base_kind"] == "mtdc":
                base = direct - excl_by_year[y] + add
                arithmetic = (f"base = {direct:.2f} - {excl_by_year[y]:.2f} (exclusions)"
                              + (f" + {add:.2f} (first-25k add-back)" if s["first25k"] is not None else "")
                              + f" = {base:.2f}")
                if base < -EPS:
                    flags.append(f"{name}: MTDC base is negative in year {y + 1} "
                                 f"({base:.2f}). Check exclusions.")
            else:
                base = direct
                arithmetic = f"base = {direct:.2f} (tdc)"
            if rate is None:
                indirect = 0.0
                arithmetic += "; indirect = 0.00 (no rate stated, not computed)"
            else:
                indirect = base * rate
                arithmetic += f"; indirect = {base:.2f} x {rate:.4f} = {indirect:.2f}"
            total = direct + indirect
            arithmetic += f"; total = {direct:.2f} + {indirect:.2f} = {total:.2f}"
            per_year.append({"direct": direct, "exclusions": excl_by_year[y], "add": add,
                             "base": base, "indirect": indirect, "total": total,
                             "arithmetic": arithmetic})

        overall = {
            "direct": sum(r["direct"] for r in per_year),
            "indirect": sum(r["indirect"] for r in per_year),
            "total": sum(r["total"] for r in per_year),
        }
        if ceiling is not None and s["role"] == "sub" and overall["total"] > ceiling + EPS:
            flags.append(f"{name}: sub overall total {overall['total']:.2f} exceeds the "
                         f"--ceiling of {ceiling:.2f}.")
        sites_out.append({"name": name, "role": s["role"], "base_kind": s["base_kind"],
                          "rate": rate, "has_first25k": s["first25k"] is not None,
                          "per_year": per_year, "overall": overall})

    rollup_per_year = []
    for y in range(years):
        rollup_per_year.append({
            "direct": sum(s["per_year"][y]["direct"] for s in sites_out),
            "indirect": sum(s["per_year"][y]["indirect"] for s in sites_out),
            "total": sum(s["per_year"][y]["total"] for s in sites_out),
        })
    rollup_overall = {
        "direct": sum(r["direct"] for r in rollup_per_year),
        "indirect": sum(r["indirect"] for r in rollup_per_year),
        "total": sum(r["total"] for r in rollup_per_year),
    }

    return {"sites": sites_out, "years": years, "flags": flags,
            "rollup": {"per_year": rollup_per_year, "overall": rollup_overall}}


# ---------------------------------------------------------------------------
# Report builder
# ---------------------------------------------------------------------------

def _cell(text) -> str:
    return str(text).replace("|", "\\|")


def build_report(analysis: dict, src_path: str, ceiling: float | None = None) -> str:
    sites = analysis["sites"]
    years = analysis["years"]
    n_prime = sum(1 for s in sites if s["role"] == "prime")
    n_sub = len(sites) - n_prime

    lines: list[str] = []
    lines.append("# Subaward budget roll-up (advisory, not an approval)")
    lines.append("")
    lines.append(
        "> Arithmetic roll-up of the site budgets you supplied. Rates, bases, exclusions, "
        "and first-25k amounts all come from the input file; nothing is assumed. This is a "
        "review aid, not a rate agreement or compliance determination."
    )
    lines.append("")
    lines.append(f"**Sites file:** {os.path.basename(src_path)}")
    lines.append(f"**Sites:** {len(sites)} (prime: {n_prime}, sub: {n_sub}) | "
                 f"**Years:** {years} | **Flags:** {len(analysis['flags'])}")
    if ceiling is not None:
        lines.append(f"**Sub-total ceiling checked:** {ceiling:.2f}")
    lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## Per-site computations")
    lines.append("")
    for s in sites:
        rate_txt = f"{s['rate']:.4f}" if s["rate"] is not None else "not stated"
        lines.append(f"### {s['name']} ({s['role']}) -- F&A rate {rate_txt} on {s['base_kind']}")
        lines.append("")
        if s["base_kind"] == "mtdc" and all(r["exclusions"] == 0 for r in s["per_year"]):
            lines.append("No MTDC exclusions were provided; stated direct costs were used as the base.")
            lines.append("")
        lines.append("| Year | Direct | Exclusions | First-25k add-back | Base | Indirect | Total |")
        lines.append("|---|---|---|---|---|---|---|")
        for y, r in enumerate(s["per_year"], start=1):
            add_txt = f"{r['add']:.2f}" if s["has_first25k"] else "n/a"
            lines.append(f"| Y{y} | {r['direct']:.2f} | {r['exclusions']:.2f} | {add_txt} | "
                         f"{r['base']:.2f} | {r['indirect']:.2f} | {r['total']:.2f} |")
        o = s["overall"]
        lines.append(f"| All | {o['direct']:.2f} |  |  |  | {o['indirect']:.2f} | {o['total']:.2f} |")
        lines.append("")
        lines.append("Arithmetic:")
        lines.append("")
        for y, r in enumerate(s["per_year"], start=1):
            lines.append(f"- Y{y}: {r['arithmetic']}")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## Roll-up to prime totals (all sites)")
    lines.append("")
    lines.append("Sub site totals appear in the prime budget as subaward costs; the roll-up "
                 "below is the simple sum of every site's stated costs.")
    lines.append("")
    lines.append("| Year | Direct (all sites) | Indirect (all sites) | Total |")
    lines.append("|---|---|---|---|")
    for y, r in enumerate(analysis["rollup"]["per_year"], start=1):
        lines.append(f"| Y{y} | {r['direct']:.2f} | {r['indirect']:.2f} | {r['total']:.2f} |")
    o = analysis["rollup"]["overall"]
    lines.append(f"| Overall | {o['direct']:.2f} | {o['indirect']:.2f} | {o['total']:.2f} |")
    lines.append("")
    lines.append("## Per-site overall totals")
    lines.append("")
    lines.append("| Site | Role | Direct | Indirect | Total |")
    lines.append("|---|---|---|---|---|")
    for s in sites:
        o = s["overall"]
        lines.append(f"| {_cell(s['name'])} | {s['role']} | {o['direct']:.2f} | "
                     f"{o['indirect']:.2f} | {o['total']:.2f} |")
    lines.append("")

    lines.append("## Flags")
    lines.append("")
    if analysis["flags"]:
        lines.extend(f"- {f}" for f in analysis["flags"])
    else:
        lines.append("- No flags.")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Closing statement")
    lines.append("")
    lines.append(
        "**This roll-up is advisory: review, not validation. It applies the rates and bases "
        "you stated to the costs you stated, with first-25k handling only where you supplied "
        "the amounts. It does not verify rate agreements, MTDC definitions, or sponsor caps. "
        "A human in sponsored programs must review the arithmetic and make the final "
        "determination.**"
    )
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description=(
            "Advisory multi-site budget roll-up. Computes per-site indirects from stated "
            "rates and bases, rolls up to prime totals, and flags data smells. "
            "Not an approval."
        )
    )
    ap.add_argument("--sites", required=True, help="Path to sites YAML file.")
    ap.add_argument("--ceiling", type=float, default=None,
                    help="Optional ceiling; flag any sub site whose overall total exceeds it.")
    ap.add_argument("--strict", action="store_true",
                    help="Exit 1 if any FLAG is raised.")
    ap.add_argument("--out", default=None,
                    help="Output path for the Markdown report (default: print to stdout).")
    args = ap.parse_args(argv)

    data = _load_yaml(args.sites)
    analysis = analyze(data, ceiling=args.ceiling)
    report = build_report(analysis, args.sites, ceiling=args.ceiling)

    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(report)
        print(f"[subaward_consolidator] wrote {args.out}")
    else:
        sys.stdout.write(report)

    if args.strict and analysis["flags"]:
        print(f"[subaward_consolidator] --strict: {len(analysis['flags'])} flag(s) raised.",
              file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
