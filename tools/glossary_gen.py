#!/usr/bin/env python3
"""glossary_gen -- auto-glossary generator from repo docs and skills.

Scans docs/**/*.md and skills/*/SKILL.md for three definition-line shapes:

  1. "**term**: definition"          -- markdown bold term, colon, definition.
  2. "term - definition" (line start) -- plain term (<= 6 words), hyphen,
     definition. Must start the line (after stripping leading whitespace /
     list markers) so prose sentences containing " - " mid-line are not
     misread as definitions.
  3. Skill frontmatter -- for skills/*/SKILL.md, the YAML frontmatter's
     "name:" field becomes the term and "description:" becomes the
     definition (skills declare themselves this way; see any SKILL.md).

Dedupe is case-insensitive by term; the FIRST occurrence (in scan order:
docs first alphabetically by path, then skills alphabetically by path) wins,
and the count of dropped duplicates is reported in the output header.
Entries are alphabetized by term (case-insensitive) in the final glossary,
each with a "Source:" suffix giving the relative path it was extracted from.

Output: by default writes to agent_outputs/GLOSSARY.md (or --out). Passing
--write-repo targets docs/reference/GLOSSARY.md instead -- run that path via
the normal release flow so drift/count checks see the updated file; do not
write directly to docs/ during ad hoc use.

Usage:
  python3 tools/glossary_gen.py --root .
  python3 tools/glossary_gen.py --root . --out agent_outputs/GLOSSARY.md
  python3 tools/glossary_gen.py --root . --write-repo

Exit codes:
  0 -- glossary written
  1 -- no definitions found anywhere in docs/ or skills/ (empty scan)
"""
from __future__ import annotations
import argparse
import glob
import os
import re
import sys

import cambium_io  # noqa: F401  (UTF-8 stdout guard)

TERM_BOLD_RE = re.compile(r"^\s*\*\*([^*]{1,80})\*\*\s*:\s*(.+?)\s*$")
TERM_DASH_RE = re.compile(r"^\s*([A-Za-z][\w /&-]{0,60}?)\s+-\s+(.+?)\s*$")
FRONTMATTER_NAME_RE = re.compile(r"^name:\s*(.+?)\s*$")
FRONTMATTER_DESC_RE = re.compile(r"^description:\s*(.+?)\s*$")


def _word_count(s: str) -> int:
    return len(s.split())


def _rel(path: str, root: str) -> str:
    try:
        return os.path.relpath(path, root).replace(os.sep, "/")
    except ValueError:
        return path


def extract_from_markdown(path: str, root: str) -> list[dict]:
    """Scan a plain markdown file for the two term-definition line shapes."""
    out = []
    try:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
    except OSError:
        return out
    rel = _rel(path, root)
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        m = TERM_BOLD_RE.match(line)
        if not m:
            m = TERM_DASH_RE.match(line)
        if not m:
            continue
        term = m.group(1).strip().rstrip(":")
        definition = m.group(2).strip()
        if not term or not definition or _word_count(term) > 6:
            continue
        out.append({"term": term, "definition": definition, "source": rel})
    return out


def extract_from_skill(path: str, root: str) -> list[dict]:
    """Scan a SKILL.md's YAML frontmatter for name: / description: as one glossary entry."""
    try:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
    except OSError:
        return []
    rel = _rel(path, root)
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return []
    name = None
    desc = None
    for line in lines[1:]:
        if line.strip() == "---":
            break
        m = FRONTMATTER_NAME_RE.match(line)
        if m:
            name = m.group(1).strip()
            continue
        m = FRONTMATTER_DESC_RE.match(line)
        if m:
            desc = m.group(1).strip()
    if not name or not desc:
        return []
    return [{"term": name, "definition": desc, "source": rel}]


# ---------------------------------------------------------------------------
# Scan + dedupe
# ---------------------------------------------------------------------------

def scan(root: str) -> tuple[list[dict], int]:
    """Return (deduped_entries, duplicate_count). Scan order: docs (sorted), then skills (sorted)."""
    doc_paths = sorted(glob.glob(os.path.join(root, "docs", "**", "*.md"), recursive=True))
    skill_paths = sorted(glob.glob(os.path.join(root, "skills", "*", "SKILL.md")))

    raw: list[dict] = []
    for p in doc_paths:
        raw.extend(extract_from_markdown(p, root))
    for p in skill_paths:
        raw.extend(extract_from_skill(p, root))

    seen: dict[str, dict] = {}
    dup_count = 0
    for entry in raw:
        key = entry["term"].lower()
        if key in seen:
            dup_count += 1
            continue
        seen[key] = entry

    deduped = sorted(seen.values(), key=lambda e: e["term"].lower())
    return deduped, dup_count


# ---------------------------------------------------------------------------
# Markdown rendering
# ---------------------------------------------------------------------------

def build_markdown(entries: list[dict], dup_count: int, total_scanned: int) -> str:
    lines: list[str] = []
    lines.append("# Glossary")
    lines.append("")
    lines.append(
        "> Auto-generated from **term**: definition and term - definition lines in docs/**/*.md, "
        "plus name/description frontmatter in skills/*/SKILL.md. Heuristic extraction; review "
        "before treating an entry as authoritative."
    )
    lines.append("")
    lines.append(f"**Entries:** {len(entries)}  |  **Scanned candidates:** {total_scanned}  |  "
                  f"**Duplicates dropped (first occurrence kept):** {dup_count}")
    lines.append("")
    lines.append("---")
    lines.append("")
    for e in entries:
        lines.append(f"**{e['term']}**: {e['definition']} _(source: {e['source']})_")
        lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Auto-generate a glossary from docs/**/*.md and skills/*/SKILL.md definitions."
    )
    ap.add_argument("--root", default=".", help="Repo root to scan (default: current directory).")
    ap.add_argument("--out", default=os.path.join("agent_outputs", "GLOSSARY.md"),
                     help="Output path (default: agent_outputs/GLOSSARY.md). Ignored if --write-repo is set.")
    ap.add_argument("--write-repo", action="store_true",
                     help="Write to docs/reference/GLOSSARY.md instead of --out. "
                          "Run this via the normal release flow so drift/count checks see it.")
    args = ap.parse_args(argv)

    root = os.path.abspath(args.root)
    entries, dup_count = scan(root)
    total_scanned = len(entries) + dup_count

    if not entries:
        print(f"[glossary_gen] ERROR: no definitions found under docs/ or skills/ in: {root}", file=sys.stderr)
        return 1

    md = build_markdown(entries, dup_count, total_scanned)

    if args.write_repo:
        out_path = os.path.join(root, "docs", "reference", "GLOSSARY.md")
    else:
        out_path = args.out

    out_dir = os.path.dirname(os.path.abspath(out_path)) or "."
    os.makedirs(out_dir, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(md)

    print(f"[glossary_gen] wrote {out_path} ({len(entries)} entries, {dup_count} duplicates dropped)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
