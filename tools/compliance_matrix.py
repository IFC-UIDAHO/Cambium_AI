#!/usr/bin/env python3
"""compliance_matrix -- requirement-to-section crosswalk for a proposal draft.

Reads a list of requirements (id, text, optional keywords) and a proposal
Markdown file, and for each requirement finds the best-matching section by
scanning headings and paragraphs for keyword hits or a distinctive 3+ word
phrase drawn from the requirement text.

ADVISORY, NOT LEGAL REVIEW: keyword matching is a screen to help a human find
where a requirement might be addressed. It cannot tell whether the addressed
content is actually adequate, complete, or compliant. A strong keyword match
does not mean the requirement is satisfied, and a miss does not necessarily
mean it's absent, just that the matcher did not find it. A human must read
the proposal against the actual requirement text before submission.

Inputs:
  --rules requirements.json   -- a JSON list of objects:
                                  {"id": "...", "text": "...", "keywords": [...]}
                                  ("keywords" is optional; if omitted, only
                                  the distinctive-phrase check is used.)
  --proposal proposal.md      -- a Markdown proposal draft

Matching, per requirement:
  - A "hit" is any heading or paragraph (case-insensitive) containing a
    keyword, OR containing a distinctive 3+ word phrase extracted from the
    requirement text (stopwords stripped, first 3+ word run kept).
  - status = met          -- 2 or more distinct keyword/phrase hits, or a
                              phrase hit (phrase hits are treated as strong)
  - status = manual-check  -- exactly 1 keyword hit (weak signal)
  - status = unmet         -- no hits at all
  - best-matching section is the heading immediately above the first hit
    paragraph (or the hit heading itself, if the hit was a heading line)

Output: a Markdown matrix (--out or stdout) plus a one-line summary
  (met / manual-check / unmet counts).

Exit codes:
  0  -- matrix built (default; met/manual-check/unmet counts do not affect exit)
  1  -- --strict was given and at least one requirement is unmet
  2  -- input file missing or unreadable

Usage:
  python3 tools/compliance_matrix.py --rules requirements.json --proposal draft.md
  python3 tools/compliance_matrix.py --rules requirements.json --proposal draft.md --out matrix.md --strict
"""
from __future__ import annotations
import argparse
import json
import os
import re
import sys
from datetime import datetime

# UTF-8 stdout guard
import cambium_io  # noqa: F401

STOPWORDS = {
    "the", "a", "an", "and", "or", "of", "to", "in", "on", "for", "with",
    "must", "shall", "should", "will", "be", "is", "are", "that", "this",
    "as", "by", "at", "from", "all", "any", "each", "not", "if", "when",
}


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------

def _load_json(path: str, label: str) -> object:
    if not os.path.exists(path):
        print(f"[compliance_matrix] ERROR: {label} file not found: {path}", file=sys.stderr)
        sys.exit(2)
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except json.JSONDecodeError as exc:
        print(f"[compliance_matrix] ERROR: {label} file is not valid JSON: {path}\n  {exc}", file=sys.stderr)
        sys.exit(2)
    except OSError as exc:
        print(f"[compliance_matrix] ERROR: cannot read {label} file: {path}\n  {exc}", file=sys.stderr)
        sys.exit(2)


def _load_text(path: str, label: str) -> str:
    if not os.path.exists(path):
        print(f"[compliance_matrix] ERROR: {label} file not found: {path}", file=sys.stderr)
        sys.exit(2)
    try:
        with open(path, encoding="utf-8") as fh:
            return fh.read()
    except OSError as exc:
        print(f"[compliance_matrix] ERROR: cannot read {label} file: {path}\n  {exc}", file=sys.stderr)
        sys.exit(2)


def load_requirements(path: str) -> list[dict]:
    data = _load_json(path, "rules")
    if not isinstance(data, list):
        print(f"[compliance_matrix] ERROR: rules file must be a JSON list: {path}", file=sys.stderr)
        sys.exit(2)
    reqs = []
    for i, entry in enumerate(data):
        if not isinstance(entry, dict) or "id" not in entry or "text" not in entry:
            print(
                f"[compliance_matrix] ERROR: rules[{i}] must be an object with 'id' and 'text'",
                file=sys.stderr,
            )
            sys.exit(2)
        reqs.append({
            "id": entry["id"],
            "text": entry["text"],
            "keywords": [str(k) for k in entry.get("keywords", [])],
        })
    return reqs


# ---------------------------------------------------------------------------
# Proposal parsing -- split into (heading_context, line_text, is_heading) tuples
# ---------------------------------------------------------------------------

def parse_proposal_lines(markdown: str) -> list[dict]:
    """Return a list of {heading, line, is_heading} for every non-blank line,
    where 'heading' is the most recent heading line seen so far (or '(no heading)')."""
    current_heading = "(no heading)"
    out = []
    for raw_line in markdown.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        is_heading = bool(re.match(r"^#{1,6}\s+", line))
        if is_heading:
            current_heading = re.sub(r"^#{1,6}\s+", "", line).strip()
        out.append({"heading": current_heading, "line": line, "is_heading": is_heading})
    return out


# ---------------------------------------------------------------------------
# Distinctive phrase extraction
# ---------------------------------------------------------------------------

def extract_phrase(text: str, min_words: int = 3) -> str | None:
    """Extract the first run of min_words+ consecutive non-stopword tokens
    from requirement text. Returns None if no such run exists."""
    tokens = re.findall(r"[A-Za-z][A-Za-z\-']*", text)
    run: list[str] = []
    for tok in tokens:
        if tok.lower() in STOPWORDS:
            if len(run) >= min_words:
                return " ".join(run)
            run = []
            continue
        run.append(tok)
    if len(run) >= min_words:
        return " ".join(run)
    return None


def extract_phrases(text: str, window: int = 3) -> list[str]:
    """All candidate distinctive phrases from requirement text: sliding window-word
    windows over each run of consecutive content words (stopwords split the runs,
    so no candidate contains or borders a stopword). Lowercased, order-preserving,
    de-duplicated."""
    tokens = [t.lower() for t in re.findall(r"[A-Za-z][A-Za-z\-']*", text)]
    runs: list[list[str]] = []
    run: list[str] = []
    for tok in tokens:
        if tok in STOPWORDS:
            if run:
                runs.append(run)
                run = []
        else:
            run.append(tok)
    if run:
        runs.append(run)

    seen: set[str] = set()
    phrases: list[str] = []
    for r in runs:
        for i in range(len(r) - window + 1):
            cand = " ".join(r[i:i + window])
            if cand not in seen:
                seen.add(cand)
                phrases.append(cand)
    return phrases


# ---------------------------------------------------------------------------
# Matching
# ---------------------------------------------------------------------------

def match_requirement(req: dict, lines: list[dict]) -> dict:
    """Find keyword and phrase hits for one requirement across proposal lines."""
    keyword_hits: list[dict] = []
    phrase_hits: list[dict] = []

    keywords_lower = [k.lower() for k in req["keywords"] if k.strip()]
    phrase = extract_phrase(req["text"])
    candidates = extract_phrases(req["text"])

    for entry in lines:
        line_lower = entry["line"].lower()
        for kw in keywords_lower:
            if kw in line_lower:
                keyword_hits.append(entry)
                break  # one hit counted per line per requirement
        if any(cand in line_lower for cand in candidates):
            phrase_hits.append(entry)  # one hit counted per line

    distinct_keyword_lines = len(keyword_hits)
    distinct_phrase_lines = len(phrase_hits)

    if distinct_phrase_lines == 1:
        # Exactly one proposal line carries a distinctive phrase from the
        # requirement text: a strong, unambiguous signal.
        status = "met"
        best = phrase_hits[0]
    elif distinct_keyword_lines >= 2:
        status = "met"
        best = keyword_hits[0]
    elif distinct_keyword_lines == 1:
        status = "manual-check"
        best = keyword_hits[0]
    elif distinct_phrase_lines >= 2:
        # Phrase found in several places: ambiguous, a human should look.
        status = "manual-check"
        best = phrase_hits[0]
    else:
        status = "unmet"
        best = None

    section = best["heading"] if best else "(not found)"

    return {
        "id": req["id"],
        "text": req["text"],
        "status": status,
        "section": section,
        "keyword_hits": distinct_keyword_lines,
        "phrase": phrase,
        "phrase_matched": distinct_phrase_lines == 1,
    }


def run_matrix(requirements: list[dict], markdown: str) -> list[dict]:
    lines = parse_proposal_lines(markdown)
    return [match_requirement(r, lines) for r in requirements]


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def build_report(results: list[dict], rules_path: str, proposal_path: str) -> str:
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    n_met = sum(1 for r in results if r["status"] == "met")
    n_manual = sum(1 for r in results if r["status"] == "manual-check")
    n_unmet = sum(1 for r in results if r["status"] == "unmet")

    lines: list[str] = []
    lines.append("# Compliance matrix (advisory screen, NOT legal review)")
    lines.append("")
    lines.append(
        "> Keyword matching is a screen to help find where a requirement might be "
        "addressed. It is not legal review and cannot judge whether content is "
        "adequate. A human must verify every row against the actual requirement text."
    )
    lines.append("")
    lines.append(f"**Generated:** {now}")
    lines.append(f"**Rules file:** {rules_path}")
    lines.append(f"**Proposal file:** {proposal_path}")
    lines.append(f"**Requirements:** {len(results)} | **met:** {n_met} | **manual-check:** {n_manual} | **unmet:** {n_unmet}")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Matrix")
    lines.append("")
    lines.append("| ID | Requirement | Status | Best-matching section |")
    lines.append("|---|---|---|---|")
    for r in results:
        status_cell = r["status"]
        if status_cell == "unmet":
            status_cell = "**unmet**"
        elif status_cell == "manual-check":
            status_cell = "*manual-check*"
        text_short = r["text"] if len(r["text"]) <= 120 else r["text"][:117] + "..."
        lines.append(f"| {r['id']} | {text_short} | {status_cell} | {r['section']} |")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(f"**Summary: {n_met} met, {n_manual} manual-check, {n_unmet} unmet (of {len(results)} requirements).**")
    lines.append("")
    lines.append(
        "**This matrix is a screen, not a compliance determination. A human must read the "
        "proposal against every requirement's actual text before submission.**"
    )
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(
        description=(
            "Requirement-to-section crosswalk for a proposal draft. "
            "Advisory screen; NOT legal review."
        )
    )
    ap.add_argument("--rules", required=True, help="Path to requirements JSON file (list of {id, text, keywords}).")
    ap.add_argument("--proposal", required=True, help="Path to proposal Markdown file.")
    ap.add_argument("--out", default=None, help="Output path for the Markdown matrix (default: stdout).")
    ap.add_argument("--strict", action="store_true", help="Exit 1 if any requirement is unmet.")
    args = ap.parse_args(argv)

    requirements = load_requirements(args.rules)
    markdown = _load_text(args.proposal, "proposal")

    results = run_matrix(requirements, markdown)
    report = build_report(results, args.rules, args.proposal)

    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(report)
        print(f"[compliance_matrix] wrote {args.out}")
    else:
        sys.stdout.write(report)

    n_unmet = sum(1 for r in results if r["status"] == "unmet")
    print(
        f"[compliance_matrix] {len(results)} requirement(s): "
        f"{sum(1 for r in results if r['status'] == 'met')} met, "
        f"{sum(1 for r in results if r['status'] == 'manual-check')} manual-check, "
        f"{n_unmet} unmet"
    )

    if args.strict and n_unmet > 0:
        raise SystemExit(1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
