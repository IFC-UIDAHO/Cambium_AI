#!/usr/bin/env python3
"""policy_diff -- lexical diff of two solicitation or policy text versions (advisory).

Compares an old and a new plain-text version of a solicitation, NOFO, or
policy document and reports added, removed, and changed requirement-bearing
sentences, plus a plain unified diff appendix. This is a lexical diff, not a
legal interpretation: it finds wording changes, and a human must judge what
they mean.

How it works (all deterministic, stdlib only):
  1. Text is split into units: paragraphs are separated by blank lines; a
     paragraph with two or more bullet lines is split per line; otherwise
     lines are joined and split into sentences at ., !, or ? boundaries.
  2. A unit counts as requirement-bearing when it contains one of these
     keywords (case-insensitive; 'eligib' matches eligible/eligibility):
     must, shall, required, deadline(s), limit(s), no longer, eligib...
  3. Units are normalized for comparison only (bullet markers stripped,
     lowercased, whitespace collapsed); display keeps the original text.
  4. Exact-normalized matches are unchanged and not reported. Remaining
     units are paired by best token overlap (Jaccard on word sets); pairs
     at or above 0.4 overlap are reported as CHANGED with both versions,
     the rest as REMOVED (old only) or ADDED (new only).
  5. A full unified diff of the raw lines (difflib) is appended.

Exit codes:
  0 -- diff complete (changes are reported in the body)
  1 -- invalid input (missing or unreadable file)

Usage:
  python3 tools/policy_diff.py --old nofo_v1.txt --new nofo_v2.txt
  python3 tools/policy_diff.py --old v1.txt --new v2.txt --out diff.md

Limits (honest):
  - Lexical only. The keyword list above defines 'requirement-ish'; real
    obligations phrased without those words are missed, and matched words do
    not always mark obligations.
  - Sentence splitting and pairing are heuristics; check the unified diff
    appendix for anything the summary misses. Not legal advice.
"""
from __future__ import annotations
import argparse
import difflib
import os
import re
import sys

# UTF-8 stdout guard
import cambium_io  # noqa: F401

KEYWORD_PATTERNS = (
    r"\bmust\b",
    r"\bshall\b",
    r"\brequired\b",
    r"\bdeadline",
    r"\blimit",
    r"\bno longer\b",
    r"\beligib",
)
KEYWORD_RES = [re.compile(p, re.IGNORECASE) for p in KEYWORD_PATTERNS]
BULLET_RE = re.compile(r"^\s*(?:[-*]|\d+[.)])\s+")
SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")
PAIR_THRESHOLD = 0.4  # minimum Jaccard token overlap to call two units a changed pair


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------

def _fail(msg: str) -> None:
    print(f"[policy_diff] ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def _read_text(path: str, label: str) -> str:
    if not os.path.exists(path):
        _fail(f"{label} file not found: {path}")
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except OSError as exc:
        _fail(f"cannot read {label} file: {path}\n  {exc}")
    return ""  # unreachable


# ---------------------------------------------------------------------------
# Unit extraction and normalization
# ---------------------------------------------------------------------------

def split_units(text: str) -> list[str]:
    """Split text into sentence/bullet units. Deterministic heuristic."""
    units: list[str] = []
    for para in re.split(r"\n\s*\n", text):
        lines = [ln for ln in para.splitlines() if ln.strip()]
        if not lines:
            continue
        bullet_count = sum(1 for ln in lines if BULLET_RE.match(ln))
        if bullet_count >= 2 or (len(lines) == 1 and BULLET_RE.match(lines[0])):
            chunks = [ln.strip() for ln in lines]
        else:
            chunks = [" ".join(ln.strip() for ln in lines)]
        for chunk in chunks:
            for sent in SENTENCE_SPLIT_RE.split(chunk):
                sent = sent.strip()
                if sent:
                    units.append(sent)
    return units


def normalize(unit: str) -> str:
    """Normalized form for comparison only: bullet stripped, lowercased, spaces collapsed."""
    stripped = BULLET_RE.sub("", unit)
    return re.sub(r"\s+", " ", stripped).strip().lower()


def is_requirement(unit: str) -> bool:
    return any(rx.search(unit) for rx in KEYWORD_RES)


def _tokens(norm: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", norm))


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 0.0
    return len(a & b) / len(a | b)


# ---------------------------------------------------------------------------
# Requirement diff
# ---------------------------------------------------------------------------

def diff_requirements(old_units: list[str], new_units: list[str]) -> tuple[list, list, list]:
    """Return (added, removed, changed) among requirement-bearing units.

    added/removed are display strings; changed is a list of
    {old, new, overlap} dicts paired by best token overlap.
    """
    old_reqs = [u for u in old_units if is_requirement(u)]
    new_reqs = [u for u in new_units if is_requirement(u)]
    old_norm = [normalize(u) for u in old_reqs]
    new_norm = [normalize(u) for u in new_reqs]

    matched_new = [False] * len(new_reqs)
    old_left: list[int] = []
    for i, n in enumerate(old_norm):
        hit = next((j for j in range(len(new_reqs))
                    if not matched_new[j] and new_norm[j] == n), None)
        if hit is None:
            old_left.append(i)
        else:
            matched_new[hit] = True
    new_left = [j for j in range(len(new_reqs)) if not matched_new[j]]

    candidates = []
    for i in old_left:
        toks_i = _tokens(old_norm[i])
        for j in new_left:
            overlap = _jaccard(toks_i, _tokens(new_norm[j]))
            if overlap >= PAIR_THRESHOLD:
                candidates.append((-overlap, i, j))
    candidates.sort()

    used_old: set[int] = set()
    used_new: set[int] = set()
    changed = []
    for neg_overlap, i, j in candidates:
        if i in used_old or j in used_new:
            continue
        used_old.add(i)
        used_new.add(j)
        changed.append({"old": old_reqs[i], "new": new_reqs[j], "overlap": -neg_overlap})

    removed = [old_reqs[i] for i in old_left if i not in used_old]
    added = [new_reqs[j] for j in new_left if j not in used_new]
    return added, removed, changed


# ---------------------------------------------------------------------------
# Report builder
# ---------------------------------------------------------------------------

def build_report(old_text: str, new_text: str, old_path: str, new_path: str) -> str:
    old_units = split_units(old_text)
    new_units = split_units(new_text)
    added, removed, changed = diff_requirements(old_units, new_units)
    n_old_reqs = sum(1 for u in old_units if is_requirement(u))
    n_new_reqs = sum(1 for u in new_units if is_requirement(u))

    lines: list[str] = []
    lines.append("# Policy version diff (lexical, advisory, not legal interpretation)")
    lines.append("")
    lines.append(
        "> Lexical comparison of requirement-bearing sentences between two versions of a "
        "document. It finds wording changes; it does not interpret them. A human must read "
        "both versions and judge what each change means."
    )
    lines.append("")
    lines.append(f"**Old file:** {os.path.basename(old_path)}")
    lines.append(f"**New file:** {os.path.basename(new_path)}")
    lines.append(f"**Requirement-bearing units:** {n_old_reqs} (old) / {n_new_reqs} (new)")
    lines.append(f"**Added:** {len(added)} | **Removed:** {len(removed)} | "
                 f"**Changed:** {len(changed)}")
    lines.append("")
    lines.append("---")
    lines.append("")

    lines.append("## Added requirements (in new, not matched in old)")
    lines.append("")
    if added:
        lines.extend(f"- {a}" for a in added)
    else:
        lines.append("- None found.")
    lines.append("")
    lines.append("## Removed requirements (in old, not matched in new)")
    lines.append("")
    if removed:
        lines.extend(f"- {r}" for r in removed)
    else:
        lines.append("- None found.")
    lines.append("")
    lines.append("## Changed requirement sentences (paired by token overlap)")
    lines.append("")
    if changed:
        for k, pair in enumerate(changed, start=1):
            lines.append(f"{k}. Token overlap {pair['overlap']:.2f}")
            lines.append(f"   - OLD: {pair['old']}")
            lines.append(f"   - NEW: {pair['new']}")
    else:
        lines.append("- None found.")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Unified diff appendix (full raw text)")
    lines.append("")
    lines.append("```diff")
    diff = difflib.unified_diff(
        old_text.splitlines(), new_text.splitlines(),
        fromfile=os.path.basename(old_path), tofile=os.path.basename(new_path), lineterm="",
    )
    diff_lines = list(diff)
    if diff_lines:
        lines.extend(diff_lines)
    else:
        lines.append("(no line-level differences)")
    lines.append("```")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Closing statement")
    lines.append("")
    lines.append(
        "**This diff is advisory and strictly lexical: review, not validation, and not "
        "legal interpretation. Requirement detection is keyword-based (must, shall, "
        "required, deadline, limit, no longer, eligib...), so it can miss obligations and "
        "flag non-obligations. A human in sponsored programs must read both versions and "
        "make the final determination of what changed and what it requires.**"
    )
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description=(
            "Advisory lexical diff of two solicitation/policy text versions: added, "
            "removed, and changed requirement-bearing sentences plus a unified diff. "
            "Not legal interpretation."
        )
    )
    ap.add_argument("--old", required=True, help="Path to the old version (plain text).")
    ap.add_argument("--new", required=True, help="Path to the new version (plain text).")
    ap.add_argument("--out", default=None,
                    help="Output path for the Markdown report (default: print to stdout).")
    args = ap.parse_args(argv)

    old_text = _read_text(args.old, "old")
    new_text = _read_text(args.new, "new")
    report = build_report(old_text, new_text, args.old, args.new)

    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(report)
        print(f"[policy_diff] wrote {args.out}")
    else:
        sys.stdout.write(report)

    return 0


if __name__ == "__main__":
    sys.exit(main())
