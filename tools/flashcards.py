#!/usr/bin/env python3
"""flashcards -- spaced-repetition deck generator from a markdown document.

Extracts term-definition pairs from a markdown document (same two heuristic
line shapes as quiz_gen.py, deliberately re-implemented here so this tool
stays standalone) and produces two artifacts:

  1. An Anki-importable TSV file: front<TAB>back, one card per line. Anki's
     TSV import convention is followed for escaping: a literal tab inside a
     field becomes a single space, and a literal newline becomes "<br>"
     (Anki renders <br> as a line break in HTML mode).
  2. A self-contained HTML reviewer implementing a simplified SM-2
     spaced-repetition algorithm entirely in browser JS memory: each card
     tracks an ease factor and interval, updated by a quality button (0-5)
     the learner clicks after seeing the answer.

Honesty note: card state (ease/interval/last-quality) lives ONLY in the
page's JS memory. Closing or reloading the page loses all progress. The
page has an "Export progress" button that serializes the current state into
a visible textarea (JSON) so the learner can copy/save it manually; there is
no localStorage and no auto-save, by design (self-contained, no hidden
persistence).

Extraction heuristics (documented, not clever): "**term**: definition" and
"term - definition", term <= 6 words, first occurrence of a term wins
(dedupe, case-insensitive). Card order follows source document order
(deterministic; --seed is accepted for interface parity with quiz_gen but
does not change anything today, reserved for a future shuffle mode).

Usage:
  python3 tools/flashcards.py --doc templates/LEARNING_PACKET.md --out agent_outputs/deck.html
  python3 tools/flashcards.py --doc academy/courses.json --tsv agent_outputs/deck.tsv

Exit codes:
  0 -- deck generated
  1 -- no term-definition pairs extractable (doc too sparse / empty)
  2 -- input file missing or unreadable
"""
from __future__ import annotations
import argparse
import html
import json
import os
import re
import sys

import cambium_io  # noqa: F401  (UTF-8 stdout guard)

TERM_BOLD_RE = re.compile(r"^\s*\*\*([^*]{1,80})\*\*\s*:\s*(.+?)\s*$")
TERM_DASH_RE = re.compile(r"^\s*([A-Za-z][\w /&-]{0,60}?)\s+-\s+(.+?)\s*$")


def _word_count(s: str) -> int:
    return len(s.split())


def extract_cards(text: str) -> list[tuple[str, str]]:
    """Return [(front, back), ...] in source line order, deduped by front (first wins)."""
    seen = set()
    cards: list[tuple[str, str]] = []
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
        key = term.lower()
        if key in seen:
            continue
        seen.add(key)
        cards.append((term, definition))
    return cards


# ---------------------------------------------------------------------------
# TSV (Anki import) -- tabs replaced with spaces, newlines with <br>
# ---------------------------------------------------------------------------

def _anki_escape(field: str) -> str:
    return field.replace("\t", " ").replace("\r\n", "<br>").replace("\n", "<br>").replace("\r", "<br>")


def build_tsv(cards: list[tuple[str, str]]) -> str:
    lines = [f"{_anki_escape(front)}\t{_anki_escape(back)}" for front, back in cards]
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# HTML reviewer (self-contained SM-2 in JS memory)
# ---------------------------------------------------------------------------

def render_html(title: str, cards: list[tuple[str, str]]) -> str:
    esc = html.escape
    deck = [{"front": esc(f), "back": esc(b)} for f, b in cards]
    deck_json = json.dumps(deck, ensure_ascii=False).replace("</", "<\\/")

    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><title>{esc(title)}</title>
<style>
body {{ font-family: system-ui, sans-serif; max-width: 640px; margin: 2rem auto; padding: 0 1rem; color: #1a1a1a; }}
h1 {{ font-size: 1.4rem; }}
.card {{ border: 1px solid #ddd; border-radius: 10px; padding: 1.5rem; min-height: 6rem; display: flex;
         align-items: center; justify-content: center; text-align: center; font-size: 1.1rem; }}
.controls {{ margin-top: 1rem; display: flex; gap: 0.4rem; flex-wrap: wrap; justify-content: center; }}
button {{ background: #2b6cb0; color: white; border: none; padding: 0.5rem 0.9rem; border-radius: 6px; cursor: pointer; }}
button.show {{ background: #444; }}
#stats {{ margin-top: 0.75rem; font-size: 0.9rem; color: #444; }}
.note {{ color: #555; font-size: 0.85rem; }}
#exportArea {{ width: 100%; height: 8rem; margin-top: 0.5rem; box-sizing: border-box; }}
</style></head>
<body>
<h1>{esc(title)}</h1>
<p class="note">Spaced-repetition reviewer (simplified SM-2), auto-generated by flashcards.py.
Progress lives only in this page's memory -- reloading or closing the tab loses it. Use
"Export progress" to save your state before you leave.</p>
<div class="card" id="cardFace">Loading...</div>
<div class="controls">
  <button class="show" onclick="showAnswer()">Show answer</button>
  <button onclick="grade(0)">0 - blackout</button>
  <button onclick="grade(1)">1 - wrong</button>
  <button onclick="grade(2)">2 - hard wrong</button>
  <button onclick="grade(3)">3 - hard right</button>
  <button onclick="grade(4)">4 - good</button>
  <button onclick="grade(5)">5 - easy</button>
</div>
<div id="stats"></div>
<div class="controls"><button onclick="exportProgress()">Export progress</button></div>
<textarea id="exportArea" readonly placeholder="Exported JSON state appears here."></textarea>
<script>
var DECK = {deck_json};
var state = DECK.map(function(c, i) {{
  return {{ id: i, front: c.front, back: c.back, ease: 2.5, interval: 0, reps: 0, lastQuality: null, showingBack: false }};
}});
var idx = 0;

function renderCard() {{
  var el = document.getElementById('cardFace');
  if (state.length === 0) {{ el.textContent = 'No cards.'; return; }}
  var c = state[idx];
  el.textContent = c.showingBack ? c.back : c.front;
  document.getElementById('stats').textContent =
    'Card ' + (idx + 1) + ' / ' + state.length +
    ' | ease ' + c.ease.toFixed(2) + ' | interval ' + c.interval + ' day(s) | reps ' + c.reps;
}}

function showAnswer() {{
  if (state.length === 0) return;
  state[idx].showingBack = true;
  renderCard();
}}

function sm2(card, quality) {{
  // Simplified SM-2: quality 0-5, ease floor 1.3.
  if (quality < 3) {{
    card.reps = 0;
    card.interval = 1;
  }} else {{
    card.reps += 1;
    if (card.reps === 1) card.interval = 1;
    else if (card.reps === 2) card.interval = 6;
    else card.interval = Math.round(card.interval * card.ease);
  }}
  card.ease = card.ease + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02));
  if (card.ease < 1.3) card.ease = 1.3;
  card.lastQuality = quality;
}}

function grade(quality) {{
  if (state.length === 0) return;
  sm2(state[idx], quality);
  state[idx].showingBack = false;
  idx = (idx + 1) % state.length;
  renderCard();
}}

function exportProgress() {{
  document.getElementById('exportArea').value = JSON.stringify(state, null, 2);
}}

renderCard();
</script>
</body></html>
"""


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _load_doc_text(path: str) -> str:
    if not os.path.exists(path):
        print(f"[flashcards] ERROR: doc not found: {path}", file=sys.stderr)
        sys.exit(2)
    try:
        with open(path, encoding="utf-8") as fh:
            return fh.read()
    except OSError as exc:
        print(f"[flashcards] ERROR: cannot read doc: {path}\n  {exc}", file=sys.stderr)
        sys.exit(2)


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Generate a spaced-repetition flashcard deck (TSV + self-contained HTML reviewer) from markdown."
    )
    ap.add_argument("--doc", required=True, help="Path to the source markdown document.")
    ap.add_argument("--out", default=os.path.join("agent_outputs", "deck.html"),
                     help="Output HTML path (default: agent_outputs/deck.html).")
    ap.add_argument("--tsv", default=None,
                     help="Output TSV path (default: same basename as --out, .tsv extension).")
    ap.add_argument("--seed", type=int, default=7,
                     help="Reserved for future shuffle mode; card order is source order today (default: 7).")
    args = ap.parse_args(argv)

    doc_text = _load_doc_text(args.doc)
    cards = extract_cards(doc_text)

    if not cards:
        print(f"[flashcards] ERROR: no term-definition pairs extractable from: {args.doc}", file=sys.stderr)
        return 1

    title = f"Flashcards: {os.path.basename(args.doc)}"
    out_html = render_html(title, cards)

    out_dir = os.path.dirname(os.path.abspath(args.out)) or "."
    os.makedirs(out_dir, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(out_html)

    tsv_path = args.tsv or (os.path.splitext(args.out)[0] + ".tsv")
    tsv_dir = os.path.dirname(os.path.abspath(tsv_path)) or "."
    os.makedirs(tsv_dir, exist_ok=True)
    with open(tsv_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(build_tsv(cards))

    print(f"[flashcards] wrote {args.out} ({len(cards)} cards), tsv: {tsv_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
