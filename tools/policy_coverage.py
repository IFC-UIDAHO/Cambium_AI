#!/usr/bin/env python3
"""policy_coverage -- policy-to-mechanism coverage report.

Parses docs/governance/AI_POLICY.md points (the same "## N. Title -- **enforced**" /
"**partial**" convention tools/gen_dashboard.py already reads), derives which mechanism
file(s) each point cites by scanning its body text for `X.py`-style code-span references
(bare filenames like `learning_gate.py`, prefixed ones like `tools/data_scan.py`, and
ones with trailing CLI flags like `gate.py --require-contribution`), resolves each to a
real repo path (tries tools/ then governance/, the two dirs AI_POLICY.md cites from),
and checks the resolved file actually exists. Any point that CLAIMS enforced whose cited
mechanism file cannot be found gets FLAGGED.

ADVISORY: this checks that a cited file exists on disk. It does not verify the file
actually implements the claimed behavior -- that is a code-review judgment, not this
tool's job.

Usage:
  python3 tools/policy_coverage.py [--policy PATH] [--root PATH] [--out PATH] [--json PATH] [--strict]

Exit: 0 normally. 1 with --strict when any point is flagged.
"""
from __future__ import annotations
import argparse
import json
import os
import re
import sys

import cambium_io  # noqa: F401 -- reconfigures stdout/stderr to UTF-8 on Windows

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_POLICY = os.path.join(ROOT, "docs", "governance", "AI_POLICY.md")
MECHANISM_DIRS = ("tools", "governance")  # search order when a citation has no directory prefix

# Matches "## 1. Human responsibility -- **enforced**" (also an em-dash variant,
# **partial**, or "**enforced (detection); procedural (handling)**").
_POINT_HEAD = re.compile(r"^##\s+(\d+)\.\s+(.*?)\s+[-—]{1,2}\s+\*\*(.+?)\*\*\s*$", re.M)
# A backtick code span naming a .py file, optionally directory-prefixed, optionally
# followed by CLI flags inside the same span, e.g. `gate.py --require-contribution`.
_MECHANISM_SPAN = re.compile(r"`((?:[A-Za-z0-9_./-]+/)?[A-Za-z0-9_-]+\.py)(?:\s[^`]*)?`")


def _resolve_mechanism(cited: str, root: str) -> str:
    """Resolve a cited filename to a repo-relative path. Tries the cited path as-is, then
    each of MECHANISM_DIRS with the bare filename. Returns the first path that exists, or
    the as-cited path (normalized) if none resolve, so a missing file still shows clearly."""
    cited = cited.strip("/")
    if "/" in cited:
        return cited
    for d in MECHANISM_DIRS:
        candidate = "%s/%s" % (d, cited)
        if os.path.exists(os.path.join(root, candidate)):
            return candidate
    return "tools/%s" % cited  # default guess when nothing resolves, kept visible in the report


def parse_policy(text: str) -> list:
    """Return a list of point dicts: {number, title, status_raw, status, body, mechanisms}.

    status is normalized to "enforced", "partial", or "other" from status_raw, matching
    the gen_dashboard.py convention of matching "**enforced" at a "## N. ..." heading.
    mechanisms is a sorted set of cited *.py filenames as they literally appear (resolved
    to repo paths later in check_coverage, which has --root available).
    """
    heads = list(_POINT_HEAD.finditer(text))
    points = []
    for i, m in enumerate(heads):
        number, title, status_raw = m.group(1), m.group(2).strip(), m.group(3).strip()
        body_start = m.end()
        body_end = heads[i + 1].start() if i + 1 < len(heads) else len(text)
        body = text[body_start:body_end]
        status_l = status_raw.lower()
        if status_l.startswith("enforced"):
            status = "enforced"
        elif status_l.startswith("partial"):
            status = "partial"
        else:
            status = "other"
        mechanisms = sorted(set(_MECHANISM_SPAN.findall(body)))
        points.append({
            "number": int(number),
            "title": title,
            "status_raw": status_raw,
            "status": status,
            "body": body,
            "mechanisms": mechanisms,
        })
    return points


def check_coverage(points: list, root: str) -> list:
    """Attach resolved paths, file-exists checks, and a flag to each point."""
    out = []
    for p in points:
        resolved = {cited: _resolve_mechanism(cited, root) for cited in p["mechanisms"]}
        exists = {cited: os.path.exists(os.path.join(root, path)) for cited, path in resolved.items()}
        missing = [resolved[cited] for cited in p["mechanisms"] if not exists[cited]]
        flagged = p["status"] == "enforced" and bool(p["mechanisms"]) and bool(missing)
        out.append({
            "number": p["number"],
            "title": p["title"],
            "status": p["status"],
            "status_raw": p["status_raw"],
            "cited": p["mechanisms"],
            "resolved": [resolved[c] for c in p["mechanisms"]],
            "file_exists": {resolved[c]: exists[c] for c in p["mechanisms"]},
            "missing": missing,
            "flagged": flagged,
        })
    return out


def render_markdown(rows: list) -> str:
    lines = ["# Policy-to-mechanism coverage report", ""]
    lines.append("> ADVISORY: confirms a cited mechanism file exists on disk. It does not verify "
                  "the file implements the claimed behavior.")
    lines.append("")
    n_enforced = sum(1 for r in rows if r["status"] == "enforced")
    n_flagged = sum(1 for r in rows if r["flagged"])
    lines.append("**Points parsed:** %d &nbsp; **Claimed enforced:** %d &nbsp; **Flagged (missing mechanism):** %d" % (len(rows), n_enforced, n_flagged))
    lines.append("")
    lines.append("| # | Point | Claimed status | Mechanism file(s) | Exists | Flag |")
    lines.append("|---|---|---|---|---|---|")
    for r in rows:
        mech = ", ".join("`%s`" % f for f in r["resolved"]) or "-"
        exists_col = ", ".join("yes" if r["file_exists"].get(f) else "NO" for f in r["resolved"]) or "-"
        flag_col = "FLAGGED" if r["flagged"] else ""
        lines.append("| %d | %s | %s | %s | %s | %s |" % (r["number"], r["title"], r["status_raw"], mech, exists_col, flag_col))
    if n_flagged:
        lines.append("")
        lines.append("## Flagged points")
        for r in rows:
            if r["flagged"]:
                lines.append("- Point %d (%s): claims enforced but missing %s" % (r["number"], r["title"], ", ".join("`%s`" % f for f in r["missing"])))
    return "\n".join(lines)


def _write(path: str, content: str) -> None:
    d = os.path.dirname(os.path.abspath(path))
    if d:
        os.makedirs(d, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--policy", default=DEFAULT_POLICY, help="Path to AI_POLICY.md.")
    ap.add_argument("--root", default=ROOT, help="Repo root to resolve mechanism files against.")
    ap.add_argument("--out", default=None, help="Write the Markdown report here (default: agent_outputs/policy_coverage.md).")
    ap.add_argument("--json", default=None, help="Also write a JSON report here.")
    ap.add_argument("--strict", action="store_true", help="Exit 1 if any point is flagged.")
    args = ap.parse_args(argv)

    if not os.path.exists(args.policy):
        print("[policy_coverage] ERROR: policy file not found: %s" % args.policy, file=sys.stderr)
        return 1

    text = open(args.policy, encoding="utf-8", errors="replace").read()
    points = parse_policy(text)
    rows = check_coverage(points, args.root)

    out_path = args.out or os.path.join(args.root, "agent_outputs", "policy_coverage.md")
    report = render_markdown(rows)
    _write(out_path, report)
    print(report)
    print("\n[policy_coverage] wrote %s" % out_path)

    if args.json:
        _write(args.json, json.dumps(rows, indent=2))
        print("[policy_coverage] wrote %s" % args.json)

    n_flagged = sum(1 for r in rows if r["flagged"])
    if args.strict and n_flagged:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
