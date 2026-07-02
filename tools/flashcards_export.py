#!/usr/bin/env python3
"""flashcards_export - export Learning Lab / learning packet content as flashcards.

Purpose:
  Turn the run's own learning material into a deck a learner can drill:
  Anki-importable TSV (default, headerless: front TAB back TAB tags), CSV
  (with header), or JSON, plus an optional fixed-interval review schedule.

Real formats consumed (matching this repo's learning system):
  * Learning Lab spec JSON (tools/gen_learning_lab.py, academy/courses.json):
    modules -> lessons -> blocks. Cards come from "flashcards" blocks
    (front/back), "predict" blocks (question + the correct choice), and each
    module's mastery "quiz" items (q + the correct choice). Other block types
    (concept, reveal, diagram, worked, explain) are skipped.
  * Learning packet markdown (templates/LEARNING_PACKET.md) or any markdown:
      - explicit "Q:" / "A:" lines, including the packet's "- Q: / A:" bullets
      - the packet's Glossary two-column table (| Term | Plain meaning |)
      - the packet's Quick quiz items (numbered question + <details> answer)
      - bold or code terms followed by is/are/means/refers to
      - a heading followed by a prose paragraph (heading front, paragraph back)

Usage:
  python3 tools/flashcards_export.py --source agent_outputs/learning_packet.md
  python3 tools/flashcards_export.py --source academy/courses.json --format json --out cards.json
  python3 tools/flashcards_export.py --source packet.md --schedule plan.md --start 2026-07-01

Exit codes: 0 on success; 1 on invalid input (missing source, bad JSON,
bad --start date, or no extractable cards).

Honest limits:
  Cards come from the given source only; nothing is invented. The bold-term,
  heading, and glossary extractors are heuristics: their cards are tagged
  "auto-extracted" and must be reviewed before teaching. Cards still holding
  the template token __FILL__ are dropped as stubs. The --schedule plan is a
  fixed classic interval scheme (days 0, 1, 3, 7, 14, 30), not an adaptive
  spaced-repetition scheduler.
"""
import argparse
import csv
import datetime
import io
import json
import os
import re
import sys

import cambium_io  # noqa: F401

INTERVALS = [0, 1, 3, 7, 14, 30]
AUTO_KINDS = {"bold", "heading", "glossary"}
HEADING_STOP = {
    "flashcards", "quick quiz", "glossary", "go deeper", "contents", "usage",
    "examples", "references", "license", "answer",
}

QA_Q_RE = re.compile(r"^\s*(?:[-*]\s*)?Q:\s*(.+?)\s*$")
QA_A_RE = re.compile(r"^\s*(?:[-*]\s*)?A:\s*(.+?)\s*$")
BOLD_DEF_RE = re.compile(
    r"(?:\*\*([^*\n]+?)\*\*|`([^`\n]+?)`)\s+(is|are|means|refers to)\s+([^\n]+)")
QUIZ_DETAILS_RE = re.compile(
    r"^[ \t]*\d+[.)][ \t]*([^\n]+?)[ \t]*$\s*<details>\s*<summary>[^<]*</summary>\s*(.*?)\s*</details>",
    re.MULTILINE | re.DOTALL,
)
HEADING_RE = re.compile(r"^(#{1,3})\s+(.+?)\s*$")


def _clean(text):
    """Collapse a field to one line of plain text."""
    return re.sub(r"\s+", " ", str(text or "")).strip()


def _tagify(text):
    tag = re.sub(r"[^A-Za-z0-9_-]+", "-", str(text or "").strip()).strip("-")
    return tag.lower() or "untagged"


def make_card(front, back, tags, kind):
    front, back = _clean(front), _clean(back)
    if not front or not back:
        return None
    if "__FILL__" in front or "__FILL__" in back:
        return None  # template stub, never ship it as a card
    all_tags = list(tags)
    if kind in AUTO_KINDS and "auto-extracted" not in all_tags:
        all_tags.append("auto-extracted")
    return {"front": front, "back": back, "tags": all_tags, "kind": kind}


# ---------------------------------------------------------------------------
# Learning Lab JSON spec (the real gen_learning_lab.py shape)
# ---------------------------------------------------------------------------

def _quiz_card(item, tags, kind):
    q = item.get("q") or item.get("question") or ""
    choices = item.get("choices") or []
    ans = item.get("answer")
    if not q or not isinstance(ans, int) or not (0 <= ans < len(choices)):
        return None
    back = _clean(choices[ans])
    explain = _clean(item.get("explain"))
    if explain:
        back = "%s. Why: %s" % (back.rstrip("."), explain)
    return make_card(q, back, tags, kind)


def extract_from_lab(lab, base_tag):
    """Cards from a Learning Lab spec dict (modules -> lessons -> blocks)."""
    cards = []
    for module in lab.get("modules") or []:
        tags = [base_tag, _tagify(module.get("id") or module.get("title") or "module")]
        for lesson in module.get("lessons") or []:
            for block in lesson.get("blocks") or []:
                btype = block.get("type")
                if btype == "flashcards":
                    for c in block.get("cards") or []:
                        cards.append(make_card(c.get("front"), c.get("back"),
                                               tags, "lab-flashcard"))
                elif btype == "predict":
                    cards.append(_quiz_card(block, tags, "lab-predict"))
        for item in module.get("quiz") or []:
            cards.append(_quiz_card(item, tags, "lab-quiz"))
    return [c for c in cards if c]


# ---------------------------------------------------------------------------
# Markdown (learning packet or generic)
# ---------------------------------------------------------------------------

def _extract_qa(lines, tags):
    cards = []
    i = 0
    while i < len(lines):
        m = QA_Q_RE.match(lines[i])
        if m:
            for j in range(i + 1, min(i + 4, len(lines))):
                ma = QA_A_RE.match(lines[j])
                if ma:
                    cards.append(make_card(m.group(1), ma.group(1), tags, "qa"))
                    i = j
                    break
        i += 1
    return cards


def _extract_glossary_table(lines, tags):
    cards = []
    in_gloss, rows_seen = False, 0
    for line in lines:
        if re.match(r"^#{1,6}\s+.*glossar", line, re.IGNORECASE):
            in_gloss, rows_seen = True, 0
            continue
        if in_gloss:
            if re.match(r"^\s*\|", line):
                cells = [c.strip().strip("*").strip("`").strip()
                         for c in line.strip().strip("|").split("|")]
                rows_seen += 1
                if rows_seen == 1 or (cells and set(cells[0]) <= set("-: ")):
                    continue  # header or separator row
                if len(cells) >= 2 and cells[0] and cells[1]:
                    cards.append(make_card(cells[0], cells[1], tags, "glossary"))
            elif line.strip():
                if rows_seen:
                    in_gloss = False
                elif line.startswith("#"):
                    in_gloss = False
    return cards


def _extract_quiz_details(text, tags):
    cards = []
    for q, a in QUIZ_DETAILS_RE.findall(text):
        cards.append(make_card(q, a, tags, "quiz"))
    return cards


def _extract_bold_defs(text, tags):
    cards = []
    for g1, g2, verb, rest in BOLD_DEF_RE.findall(text):
        term = (g1 or g2).strip().rstrip(".:")
        sm = re.match(r"(.+?\.)\s", rest + " ")
        sentence = (sm.group(1) if sm else rest).strip()
        if term and len(sentence) >= 10:
            cards.append(make_card(term, "%s %s %s" % (term, verb, sentence),
                                   tags, "bold"))
    return cards


def _extract_headings(lines, tags):
    cards = []
    for i, line in enumerate(lines):
        m = HEADING_RE.match(line)
        if not m:
            continue
        head = m.group(2).strip().rstrip(":")
        if head.lower() in HEADING_STOP or "glossar" in head.lower():
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
        body = " ".join(para)
        if len(body) >= 30 and body[0].isalpha():
            cards.append(make_card(head, body, tags, "heading"))
    return cards


def extract_from_markdown(text, base_tag):
    lines = text.splitlines()
    tags = [base_tag]
    cards = []
    cards += _extract_qa(lines, tags)
    cards += _extract_glossary_table(lines, tags)
    cards += _extract_quiz_details(text, tags)
    cards += _extract_bold_defs(text, tags)
    cards += _extract_headings(lines, tags)
    seen, out = set(), []
    for c in cards:
        if not c:
            continue
        key = (c["front"].casefold(), c["back"].casefold())
        if key not in seen:
            seen.add(key)
            out.append(c)
    return out


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

def render_tsv(cards):
    rows = []
    for c in cards:
        rows.append("%s\t%s\t%s" % (c["front"].replace("\t", " "),
                                    c["back"].replace("\t", " "),
                                    " ".join(c["tags"])))
    return "\n".join(rows) + "\n"


def render_csv(cards):
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["front", "back", "tags"])
    for c in cards:
        w.writerow([c["front"], c["back"], " ".join(c["tags"])])
    return buf.getvalue()


def render_json(cards, source):
    payload = {
        "source": source,
        "count": len(cards),
        "note": ("Cards extracted from the source only, nothing invented. "
                 "Cards tagged auto-extracted are heuristic: "
                 "auto-extracted, review before teaching."),
        "cards": cards,
    }
    return json.dumps(payload, indent=1, ensure_ascii=False) + "\n"


def render_schedule(count, source, start):
    rows = []
    for i, day in enumerate(INTERVALS, 1):
        date = start + datetime.timedelta(days=day)
        rows.append("| %d | %d | %s | %d |" % (i, day, date.isoformat(), count))
    return "\n".join([
        "# Flashcard review schedule",
        "",
        "Deck: %d cards from %s." % (count, source),
        "Start date: %s." % start.isoformat(),
        "",
        "| Session | Day | Date | Cards due |",
        "|---|---|---|---|",
    ] + rows + [
        "",
        "Note: this is a fixed classic interval scheme (days 0, 1, 3, 7, 14, 30),",
        "not an adaptive scheduler. Real spaced-repetition software (for example",
        "Anki) adapts per card based on your recall; use this plan as a starting",
        "scaffold. Auto-extracted cards need review before teaching.",
        "",
    ])


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Export Learning Lab / learning packet content as flashcards.")
    ap.add_argument("--source", required=True,
                    help="learning packet .md, Learning Lab spec .json, or any markdown")
    ap.add_argument("--format", choices=["tsv", "csv", "json"], default="tsv",
                    help="tsv (default, Anki-importable) | csv | json")
    ap.add_argument("--out", help="write the deck here instead of stdout")
    ap.add_argument("--schedule", help="also write a fixed-interval review plan (markdown) here")
    ap.add_argument("--start", help="schedule start date YYYY-MM-DD (default: today)")
    a = ap.parse_args(argv)

    if not os.path.isfile(a.source):
        print("[flashcards] source not found: %s" % a.source, file=sys.stderr)
        return 1
    try:
        text = open(a.source, encoding="utf-8", errors="replace").read()
    except OSError as exc:
        print("[flashcards] cannot read %s: %s" % (a.source, exc), file=sys.stderr)
        return 1

    base_tag = _tagify(os.path.splitext(os.path.basename(a.source))[0])
    is_json = a.source.lower().endswith(".json") or text.lstrip()[:1] == "{"
    if is_json:
        try:
            lab = json.loads(text)
        except json.JSONDecodeError as exc:
            print("[flashcards] invalid JSON in %s: %s" % (a.source, exc), file=sys.stderr)
            return 1
        if not isinstance(lab, dict) or not lab.get("modules"):
            print("[flashcards] %s is not a Learning Lab spec (no modules list)" % a.source,
                  file=sys.stderr)
            return 1
        cards = extract_from_lab(lab, base_tag)
    else:
        cards = extract_from_markdown(text, base_tag)

    if not cards:
        print("[flashcards] no flashcard patterns found in %s "
              "(Q:/A: lines, glossary table, quiz, bold-term definitions, headings)"
              % a.source, file=sys.stderr)
        return 1

    body = {"tsv": render_tsv, "csv": render_csv}.get(a.format, lambda c: render_json(c, a.source))(cards)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as fh:
            fh.write(body)
    else:
        sys.stdout.write(body)

    if a.schedule:
        try:
            start = (datetime.date.fromisoformat(a.start) if a.start
                     else datetime.date.today())
        except ValueError:
            print("[flashcards] invalid --start date (want YYYY-MM-DD): %s" % a.start,
                  file=sys.stderr)
            return 1
        with open(a.schedule, "w", encoding="utf-8") as fh:
            fh.write(render_schedule(len(cards), a.source, start))
        print("[flashcards] schedule -> %s" % a.schedule, file=sys.stderr)

    auto = sum(1 for c in cards if "auto-extracted" in c["tags"])
    note = " (%d auto-extracted, review before teaching)" % auto if auto else ""
    dest = a.out or "stdout"
    print("[flashcards] %d cards from %s -> %s%s" % (len(cards), a.source, dest, note),
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
