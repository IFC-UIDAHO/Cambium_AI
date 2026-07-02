#!/usr/bin/env python3
"""revision_matrix -- reviewer-response scaffold from a plain-text comments file.

Splits a plain-text or Markdown reviewer-comments file into numbered comments
per reviewer, and writes a Markdown table with TODO placeholders for the
response, the change made, and its location, so the author team has a
structured starting point for a response-to-reviewers letter.

Parsing heuristics (kept simple and documented, not a general NLP parser):
  1. A line matching "Reviewer <n>" or "Referee <n>" (case-insensitive, at the
     start of a line) begins a new reviewer section. Text before the first such
     line, if any, is treated as "Reviewer 1" (single-block fallback).
  2. Within a section, comments are split on lines that start a numbered item:
     "1.", "1)", "1 -" etc. If no numbered items are found in a section, the
     section is split on blank-line-separated paragraphs instead.
  3. Comment text stored in the table is the first 140 characters of the item,
     for a scannable table; the fixture text itself is not modified or lost
     (see --out for the full table; nothing here rewrites the input file).

A second mode, --stats, reads a PREVIOUSLY FILLED matrix (the same Markdown
table format this tool produces) and counts how many TODO placeholders remain
in the Response / Change made / Location columns. With --strict, it exits 1 if
any TODO remains, useful as a pre-submission gate.

Exit codes:
  0  -- matrix built, or stats reported with no --strict violation
  1  -- --stats --strict found remaining TODOs
  2  -- input file missing, unreadable, or empty

Usage:
  python3 tools/revision_matrix.py --comments reviews.txt --out matrix.md
  python3 tools/revision_matrix.py --stats --matrix matrix.md
  python3 tools/revision_matrix.py --stats --matrix matrix.md --strict
"""
from __future__ import annotations
import argparse
import os
import re
import sys

# UTF-8 stdout guard
import cambium_io  # noqa: F401

REVIEWER_HEADER_RE = re.compile(r"^\s*(Reviewer|Referee)\s+(\d+)\b", re.IGNORECASE)
NUMBERED_ITEM_RE = re.compile(r"^\s*(\d+)[.)\-]\s+")
COMMENT_MAX_LEN = 140

COLUMNS = ["#", "Reviewer", "Comment (first 140 chars)", "Response", "Change made", "Location"]


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def split_into_sections(text: str) -> list[tuple[str, str]]:
    """Return [(reviewer_label, section_text), ...].

    If no "Reviewer N" / "Referee N" header is found anywhere, the whole file
    is a single fallback section labeled "Reviewer 1".
    """
    lines = text.splitlines()
    headers: list[tuple[int, str]] = []
    for i, line in enumerate(lines):
        m = REVIEWER_HEADER_RE.match(line)
        if m:
            headers.append((i, f"{m.group(1).capitalize()} {m.group(2)}"))

    if not headers:
        return [("Reviewer 1", text)]

    sections: list[tuple[str, str]] = []
    for idx, (line_no, label) in enumerate(headers):
        start = line_no + 1
        end = headers[idx + 1][0] if idx + 1 < len(headers) else len(lines)
        section_text = "\n".join(lines[start:end])
        sections.append((label, section_text))
    return sections


def split_into_items(section_text: str) -> list[str]:
    """Split one reviewer's section text into individual comment items.

    Prefers numbered items ("1.", "2)", etc). Falls back to blank-line
    paragraphs when no numbered items are found.
    """
    lines = section_text.splitlines()
    starts = [i for i, line in enumerate(lines) if NUMBERED_ITEM_RE.match(line)]

    if starts:
        items = []
        for idx, start in enumerate(starts):
            end = starts[idx + 1] if idx + 1 < len(starts) else len(lines)
            chunk = "\n".join(lines[start:end]).strip()
            chunk = NUMBERED_ITEM_RE.sub("", chunk, count=1).strip()
            if chunk:
                items.append(chunk)
        return items

    # Fallback: blank-line paragraphs
    paragraphs = re.split(r"\n\s*\n", section_text.strip())
    return [p.strip().replace("\n", " ") for p in paragraphs if p.strip()]


def build_rows(text: str) -> list[dict]:
    rows: list[dict] = []
    n = 0
    for label, section_text in split_into_sections(text):
        items = split_into_items(section_text)
        for item in items:
            n += 1
            comment = item.replace("\n", " ").strip()
            if len(comment) > COMMENT_MAX_LEN:
                comment = comment[:COMMENT_MAX_LEN - 3] + "..."
            rows.append({
                "n": n,
                "reviewer": label,
                "comment": comment,
            })
    return rows


# ---------------------------------------------------------------------------
# Markdown table
# ---------------------------------------------------------------------------

def _escape_cell(text: str) -> str:
    return text.replace("|", "\\|")


def build_table(rows: list[dict]) -> str:
    lines: list[str] = []
    lines.append("# Reviewer response matrix")
    lines.append("")
    lines.append(
        "> Scaffold generated from a reviewer-comments file by a simple, documented "
        "line-splitting heuristic. Review every row against the original comments file "
        "before relying on it; the parser can miscount comments that do not use plain "
        "numbered items."
    )
    lines.append("")
    lines.append("| " + " | ".join(COLUMNS) + " |")
    lines.append("|" + "|".join(["---"] * len(COLUMNS)) + "|")
    for r in rows:
        lines.append(
            f"| {r['n']} | {_escape_cell(r['reviewer'])} | {_escape_cell(r['comment'])} | TODO | TODO | TODO |"
        )
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# --stats mode
# ---------------------------------------------------------------------------

def count_todos(matrix_text: str) -> int:
    """Count TODO occurrences in table rows (excludes the header/legend text)."""
    count = 0
    for line in matrix_text.splitlines():
        if not line.strip().startswith("|"):
            continue
        if line.strip().startswith("|---") or line.strip().startswith("| #"):
            continue
        count += line.count("TODO")
    return count


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _load_text(path: str, label: str) -> str:
    if not os.path.exists(path):
        print(f"[revision_matrix] ERROR: {label} file not found: {path}", file=sys.stderr)
        sys.exit(2)
    try:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
    except OSError as exc:
        print(f"[revision_matrix] ERROR: cannot read {label} file: {path}\n  {exc}", file=sys.stderr)
        sys.exit(2)
    if not text.strip():
        print(f"[revision_matrix] ERROR: {label} file is empty: {path}", file=sys.stderr)
        sys.exit(2)
    return text


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Build a reviewer-response scaffold, or report TODO stats on a filled matrix."
    )
    ap.add_argument("--comments", default=None, help="Path to the plain-text/Markdown reviewer comments file.")
    ap.add_argument("--out", default=None, help="Output path for the Markdown matrix (default: stdout).")
    ap.add_argument("--stats", action="store_true", help="Report TODO counts on a previously filled matrix.")
    ap.add_argument("--matrix", default=None, help="Path to a previously filled matrix (required with --stats).")
    ap.add_argument("--strict", action="store_true", help="With --stats, exit 1 if any TODO remains.")
    args = ap.parse_args(argv)

    if args.stats:
        if not args.matrix:
            print("[revision_matrix] ERROR: --stats requires --matrix <path>", file=sys.stderr)
            return 2
        text = _load_text(args.matrix, "matrix")
        remaining = count_todos(text)
        print(f"[revision_matrix] {remaining} TODO placeholder(s) remaining in {args.matrix}")
        if remaining > 0 and args.strict:
            return 1
        return 0

    if not args.comments:
        print("[revision_matrix] ERROR: --comments <path> is required (or use --stats)", file=sys.stderr)
        return 2

    text = _load_text(args.comments, "comments")
    rows = build_rows(text)
    table = build_table(rows)

    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(table)
        print(f"[revision_matrix] wrote {args.out} ({len(rows)} comment row(s))")
    else:
        sys.stdout.write(table)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
