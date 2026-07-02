#!/usr/bin/env python3
"""cost_report - institutional cost and usage roll-up from run logs plus user rates.

Purpose:
  Aggregate model usage into per-model, per-run, and monthly totals, priced ONLY
  with user-supplied rates. Two input sources:
    1. agent_outputs/**/cost_log.csv under --root, the log cambium_run.py writes
       and tools/loop_costs.py reads. Real schema:
       run,phase,agent,model,input_tokens,output_tokens,wall_s,est_usd
       (these rows carry no date; they land in the "undated" month bucket, and
       their est_usd column is reported separately as an informational figure).
    2. an optional --usage CSV with columns: model,input_tokens,output_tokens,run,date

Rates:
  --rates YAML maps each model name to {input_per_mtok, output_per_mtok} in USD
  per million tokens. This tool ships NO built-in prices and never invents one:
  if usage exists and rates are missing, or a used model has no rate, it refuses
  and exits 1.

Usage:
  python3 tools/cost_report.py --rates rates.yml [--root DIR] [--usage usage.csv] [--strict]

Honest limits:
  Costs are user-supplied rates applied to user-supplied usage records. This is
  not API billing data and not an invoice; token counts are only as good as the
  logs. Advisory report, not a certification.

Exit: 0 normally; 1 on missing/invalid rates, a used model without a rate, or
malformed usage rows under --strict.
"""
import argparse
import csv
import glob
import os
import re
import sys

import cambium_io  # noqa: F401

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MONTH_RE = re.compile(r"^\d{4}-\d{2}")

REFUSAL = ("[cost_report] REFUSING to price usage: no usable --rates given. This tool "
           "ships NO built-in prices and will not invent them. Provide --rates "
           "rates.yml mapping each model to {input_per_mtok, output_per_mtok} in USD.")


def _to_int(s):
    return int(float(str(s).strip()))


def collect_log_rows(root):
    """Read every agent_outputs/**/cost_log.csv under root (loop_costs schema)."""
    rows, logged_est = [], 0.0
    pattern = os.path.join(root, "agent_outputs", "**", "cost_log.csv")
    for path in sorted(glob.glob(pattern, recursive=True)):
        try:
            with open(path, newline="", encoding="utf-8") as fh:
                for r in csv.DictReader(fh):
                    model = (r.get("model") or "").strip()
                    if not model:
                        continue
                    try:
                        it = _to_int(r.get("input_tokens") or 0)
                        ot = _to_int(r.get("output_tokens") or 0)
                    except ValueError:
                        continue
                    rows.append({"model": model, "run": (r.get("run") or "").strip() or "(unknown)",
                                 "date": "", "input_tokens": it, "output_tokens": ot,
                                 "source": os.path.relpath(path, root)})
                    for col in ("est_usd", "cost_usd", "usd", "cost"):
                        if col in r:
                            try:
                                logged_est += float(r[col])
                            except (TypeError, ValueError):
                                pass
                            break
        except OSError:
            continue
    return rows, logged_est


def read_usage(path):
    """Read the optional usage CSV. Returns (rows, malformed[(line_no, reason)])."""
    rows, malformed = [], []
    with open(path, newline="", encoding="utf-8") as fh:
        for i, r in enumerate(csv.DictReader(fh), start=2):
            model = (r.get("model") or "").strip()
            if not model:
                malformed.append((i, "empty model"))
                continue
            try:
                it = _to_int(r.get("input_tokens") or "")
                ot = _to_int(r.get("output_tokens") or "")
            except ValueError:
                malformed.append((i, "non-numeric token count"))
                continue
            rows.append({"model": model, "run": (r.get("run") or "").strip() or "(unknown)",
                         "date": (r.get("date") or "").strip(),
                         "input_tokens": it, "output_tokens": ot,
                         "source": os.path.basename(path)})
    return rows, malformed


def load_rates(path):
    """Load the rates YAML. Returns dict model -> (in_per_mtok, out_per_mtok) or None."""
    if not path or not os.path.isfile(path):
        return None
    try:
        import yaml
        data = yaml.safe_load(open(path, encoding="utf-8")) or {}
    except ImportError:
        data = _mini_yaml(path)
    except Exception:
        return None
    rates = {}
    if not isinstance(data, dict):
        return None
    for model, v in data.items():
        if not isinstance(v, dict):
            return None
        try:
            rates[str(model)] = (float(v["input_per_mtok"]), float(v["output_per_mtok"]))
        except (KeyError, TypeError, ValueError):
            return None
    return rates or None


def _mini_yaml(path):
    """Fallback parser for the flat two-level rates file if pyyaml is absent."""
    data, current = {}, None
    for raw in open(path, encoding="utf-8"):
        line = raw.rstrip()
        if not line.strip() or line.strip().startswith("#"):
            continue
        if not line.startswith((" ", "\t")) and line.rstrip().endswith(":"):
            current = line.strip()[:-1].strip("'\"")
            data[current] = {}
        elif current and ":" in line:
            k, _, v = line.strip().partition(":")
            try:
                data[current][k.strip()] = float(v.split("#")[0].strip())
            except ValueError:
                pass
    return data


def price(rows, rates):
    """Attach cost_usd to each row. Returns sorted list of models missing a rate."""
    missing = sorted({r["model"] for r in rows if r["model"] not in rates})
    if missing:
        return missing
    for r in rows:
        in_rate, out_rate = rates[r["model"]]
        r["cost_usd"] = (r["input_tokens"] / 1e6) * in_rate + (r["output_tokens"] / 1e6) * out_rate
    return []


def _agg(rows, key):
    out = {}
    for r in rows:
        k = key(r)
        cur = out.setdefault(k, {"rows": 0, "input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0})
        cur["rows"] += 1
        cur["input_tokens"] += r["input_tokens"]
        cur["output_tokens"] += r["output_tokens"]
        cur["cost_usd"] += r["cost_usd"]
    return out


def render(rows, logged_est, rates_path):
    out = []
    out.append("# Cost and usage roll-up")
    out.append("")
    out.append("Usage rows priced: %d. Rates file: %s." % (len(rows), rates_path))
    out.append("")
    out.append("## Per model")
    out.append("")
    out.append("| Model | Rows | Input tokens | Output tokens | Cost (USD) |")
    out.append("|---|---|---|---|---|")
    for k, v in sorted(_agg(rows, lambda r: r["model"]).items()):
        out.append("| %s | %d | %d | %d | %.2f |"
                   % (k, v["rows"], v["input_tokens"], v["output_tokens"], v["cost_usd"]))
    out.append("")
    out.append("## Per run")
    out.append("")
    out.append("| Run | Rows | Cost (USD) |")
    out.append("|---|---|---|")
    for k, v in sorted(_agg(rows, lambda r: r["run"]).items()):
        out.append("| %s | %d | %.2f |" % (k, v["rows"], v["cost_usd"]))
    out.append("")
    out.append("## Monthly roll-up")
    out.append("")
    out.append("| Month | Rows | Cost (USD) |")
    out.append("|---|---|---|")
    monthly = _agg(rows, lambda r: r["date"][:7] if MONTH_RE.match(r["date"]) else "undated")
    for k, v in sorted(monthly.items()):
        out.append("| %s | %d | %.2f |" % (k, v["rows"], v["cost_usd"]))
    total = sum(r["cost_usd"] for r in rows)
    out.append("")
    out.append("GRAND TOTAL: %.2f USD" % total)
    if logged_est:
        out.append("")
        out.append("Informational: the cost_log.csv files also carry their own runtime "
                   "est_usd column summing to %.4f USD. That figure was written by the "
                   "runner at run time and is NOT computed by this tool." % logged_est)
    out.append("")
    out.append("---")
    out.append("Costs above are computed from USER-SUPPLIED rates applied to "
               "USER-SUPPLIED usage records. No built-in prices exist in this tool. "
               "This is an advisory estimate, not API billing and not an invoice.")
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Roll up model usage (cost_log.csv plus optional usage CSV) "
                    "into per-model/per-run/monthly totals using user-supplied rates.")
    ap.add_argument("--root", default=REPO_ROOT, help="repo root holding agent_outputs/ (default: this repo)")
    ap.add_argument("--usage", default=None, help="optional CSV: model,input_tokens,output_tokens,run,date")
    ap.add_argument("--rates", default=None, help="YAML: model -> {input_per_mtok, output_per_mtok} (required to price)")
    ap.add_argument("--strict", action="store_true", help="exit 1 on malformed usage rows")
    a = ap.parse_args(argv)

    root = os.path.abspath(a.root)
    if not os.path.isdir(root):
        print("[cost_report] ERROR: root does not exist: %s" % root)
        return 1

    rows, logged_est = collect_log_rows(root)
    malformed = []
    if a.usage:
        if not os.path.isfile(a.usage):
            print("[cost_report] ERROR: usage file not found: %s" % a.usage)
            return 1
        urows, malformed = read_usage(a.usage)
        rows.extend(urows)
        for line_no, reason in malformed:
            print("[cost_report] WARNING: malformed usage row at line %d: %s (skipped)"
                  % (line_no, reason))

    if not rows:
        print("[cost_report] no usage found (no cost_log.csv under %s and no --usage rows). "
              "Nothing to price." % os.path.join(root, "agent_outputs"))
        if a.strict and malformed:
            print("[cost_report] STRICT: %d malformed usage row(s); exit 1." % len(malformed))
            return 1
        return 0

    if a.rates and not os.path.isfile(a.rates):
        print("[cost_report] ERROR: rates file not found: %s" % a.rates)
        return 1
    rates = load_rates(a.rates)
    if rates is None:
        print(REFUSAL)
        return 1
    missing = price(rows, rates)
    if missing:
        print("[cost_report] REFUSING to price usage: no rate supplied for model(s): %s. "
              "Add them to the --rates file; prices are never invented." % ", ".join(missing))
        return 1

    print(render(rows, logged_est, a.rates))
    if a.strict and malformed:
        print("\n[cost_report] STRICT: %d malformed usage row(s); exit 1." % len(malformed))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
