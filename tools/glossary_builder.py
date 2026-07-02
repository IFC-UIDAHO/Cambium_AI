#!/usr/bin/env python3
"""glossary_builder - extract an alphabetized glossary from markdown sources.

Purpose:
  Pull candidate term/definition pairs out of course material (learning
  packets, explainers, docs) so an educator can review and reuse them.

Extraction rules (all regex heuristics, applied in this order per file):
  1. Bold or code terms followed by a defining verb:
       **term** is|are|means|refers to <sentence>
  2. Explicit "Term: definition" lines: a short term (1-6 words) at the start
     of a line or bullet, a colon, then the definition. Common labels are
     skipped (Q, A, Note, Usage, Warning, Example, Tip, Source, Answer,
     Input, Output, Exit, TODO).
  3. Heading terms: a level 1-3 heading of 1-6 words, defined by the first
     sentence of the prose paragraph right below it. Boilerplate headings from
     this repo's learning packet template are skipped (Flashcards, Quick quiz,
     Glossary, Go deeper, In one breath, The picture, and similar).

Usage:
  python3 tools/glossary_builder.py --sources academy/labs docs/notes.md
  python3 tools/glossary_builder.py --sources packet.md --quiz --out GLOSSARY.md
  python3 tools/glossary_builder.py --sources docs/ --min-len 4 --max-terms 50

Exit codes: 0 on success; 1 on invalid input (missing path, no markdown
files, or zero extractable terms).

Honest limits:
  Every definition is auto-extracted, review before teaching: the regexes
  will both miss valid definitions and catch non-definitions. Definitions are
  copied verbatim from the sources, never invented or reworded. Duplicate
  terms keep the first occurrence in deterministic file order; --max-terms
  keeps the first N found, then the output is alphabetized.
"""
import argparse
import glob
import os
import re
import sys

import cambium_io  # noqa: F401

BOLD_DEF_RE = re.compile(
    r"(?:\*\*([^*\n]+?)\*\*|`([^`\n]+?)`)\s+(is|are|means|refers to)\s+([^\n]+)")
TERM_LINE_RE = re.compile(
    r"^\s*(?:[-*]\s+)?(?:\*\*)?([A-Za-z][A-Za-z0-9 /()'&+._-]{0,58}?)(?:\*\*)?\s*:\s+(\S.+?)\s*$")
HEADING_RE = re.compile(r"^(#{1,3})\s+(.+?)\s*$")

LABEL_STOP = {
    "q", "a", "note", "usage", "warning", "example", "tip", "source",
    "answer", "input", "output", "exit", "todo", "see", "hint",
}
HEADING_STOP = {
    "flashcards", "quick quiz", "glossary", "go deeper", "contents", "usage",
    "examples", "references", "license", "answer", "in one breath",
    "the picture", "introduction", "overview", "summary",
}


def _first_sentence(text):
    text = re.sub(r"\s+", " ", text).strip()
    m = re.match(r"(.+?[.!?])(?:\s|$)", text)
    return (m.group(1) if m else text).strip()


def _wc(term):
    return len(term.split())


def extract_terms(text, source, min_len):
    """Return [{term, definition, source, rule}] found in one file's text."""
    lines = text.splitlines()
    found = []

    def add(term, definition, rule):
        term = re.sub(r"\s+", " ", str(term)).strip().strip("*`").strip()
        definition = re.sub(r"\s+", " ", str(definition)).strip()
        if (len(term) < min_len or len(term) > 60 or not (1 <= _wc(term) <= 6)
                or len(definition) < 10):
            return
        if "__FILL__" in term or "__FILL__" in definition:
            return  # template stub
        if term.lower() in LABEL_STOP or "http" in term.lower():
            return
        found.append({"term": term, "definition": definition,
                      "source": source, "rule": rule})

    # Rule 1: bold/code term + defining verb
    for g1, g2, verb, rest in BOLD_DEF_RE.findall(text):
        term = (g1 or g2).strip().rstrip(".:")
        add(term, "%s %s" % (verb, _first_sentence(rest)), "bold-verb")

    # Rule 2: explicit "Term: definition" lines
    for line in lines:
        if line.strip().startswith("|") or line.strip().startswith("#"):
            continue
        m = TERM_LINE_RE.match(line)
        if m:
            add(m.group(1), m.group(2), "term-colon")

    # Rule 3: heading + first sentence of the paragraph below
    for i, line in enumerate(lines):
        m = HEADING_RE.match(line)
        if not m:
            continue
        head = m.group(2).strip().rstrip(":")
        if head.lower() in HEADING_STOP or "glossar" in head.lower():
            continue
        if not (1 <= _wc(head) <= 6):
            continue
        para = []
        for nxt in lines[i + 1:]:
            if not nxt.strip():
                if para:
                    break
                continue
            if re.match(r"^\s*([#>|<*-]|\d+[.)])", nxt):
                break
            para.append(nxt.strip())
        if para:
            add(head, _first_sentence(" ".join(para)), "heading")
    return found


def collect_sources(paths):
    """Expand files/dirs into a deterministic sorted list of markdown files."""
    files = []
    for p in paths:
        if os.path.isdir(p):
            files.extend(glob.glob(os.path.join(p, "**", "*.md"), recursive=True))
        elif os.path.isfile(p):
            files.append(p)
        else:
            raise ValueError("source not found: %s" % p)
    return sorted(set(files))


def build_glossary(files, min_len, max_terms):
    entries, seen = [], set()
    for path in files:
        text = open(path, encoding="utf-8", errors="replace").read()
        for e in extract_terms(text, path.replace(os.sep, "/"), min_len):
            key = e["term"].casefold()
            if key not in seen:
                seen.add(key)
                entries.append(e)
    entries = entries[:max_terms]
    return sorted(entries, key=lambda e: e["term"].casefold())


def render_glossary(entries, files, quiz):
    lines = [
        "# Glossary",
        "",
        "> auto-extracted, review before teaching. Every entry below was",
        "> pattern-matched out of the named sources (rules documented in",
        "> tools/glossary_builder.py); expect misses and false catches.",
        "> Definitions are verbatim from the sources, nothing was invented.",
        "",
        "Entries: %d (from %d source files)." % (len(entries), len(files)),
        "",
    ]
    for e in entries:
        lines.append("- **%s**: %s (source: %s)" % (e["term"], e["definition"], e["source"]))
    if quiz:
        lines += [
            "",
            "## Fill-in-the-blank quiz (auto-extracted, review before teaching)",
            "",
        ]
        for i, e in enumerate(entries, 1):
            blanked = re.sub(re.escape(e["term"]), "____", e["definition"],
                             flags=re.IGNORECASE)
            if blanked == e["definition"]:
                q = "Which term matches this definition: %s" % e["definition"]
            else:
                q = blanked if blanked.startswith("____") else "____ " + blanked
            lines += ["%d. %s" % (i, q), "", "<details>", "<summary>Answer</summary>",
                      "", e["term"], "", "</details>", ""]
    return "\n".join(lines).rstrip() + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Extract an alphabetized glossary from markdown sources.")
    ap.add_argument("--sources", nargs="+", required=True,
                    help="markdown files and/or directories (dirs scanned for **/*.md)")
    ap.add_argument("--quiz", action="store_true",
                    help="also emit fill-in-the-blank questions")
    ap.add_argument("--min-len", type=int, default=3,
                    help="minimum term length in characters (default 3)")
    ap.add_argument("--max-terms", type=int, default=200,
                    help="cap on glossary entries (default 200)")
    ap.add_argument("--out", help="write here instead of stdout")
    a = ap.parse_args(argv)

    if a.min_len < 1 or a.max_terms < 1:
        print("[glossary] --min-len and --max-terms must be positive", file=sys.stderr)
        return 1
    try:
        files = collect_sources(a.sources)
    except ValueError as exc:
        print("[glossary] %s" % exc, file=sys.stderr)
        return 1
    if not files:
        print("[glossary] no markdown files found under: %s" % ", ".join(a.sources),
              file=sys.stderr)
        return 1

    entries = build_glossary(files, a.min_len, a.max_terms)
    if not entries:
        print("[glossary] no term/definition patterns found in %d files "
              "(rules: bold/code + is/are/means/refers to; Term: definition "
              "lines; headings with a first-sentence definition)" % len(files),
              file=sys.stderr)
        return 1

    body = render_glossary(entries, files, a.quiz)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as fh:
            fh.write(body)
    else:
        sys.stdout.write(body)
    print("[glossary] %d terms from %d files -> %s (auto-extracted, review "
          "before teaching)" % (len(entries), len(files), a.out or "stdout"),
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
