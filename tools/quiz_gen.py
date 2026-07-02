#!/usr/bin/env python3
"""quiz_gen -- deterministic quiz generator from a markdown document.

Turns a learning packet, Academy module export, or any markdown doc into a
self-contained HTML quiz plus a JSON answer key, using simple text-pattern
heuristics. This is NOT semantic understanding of the document, it is line
matching. An educator should review the generated quiz before classroom use.

Extraction heuristics (documented, not clever):
  - Term-definition pairs come from two line shapes: "**term**: definition"
    (markdown bold term, colon, definition) and "term - definition" (plain
    term, hyphen, definition). A candidate term must be <= 6 words.
  - Cloze items: the definition text with the term blanked out.
  - True/false: from short declarative sentences (<= 25 words) containing
    " is " or " are ". As written it grades True; a False variant swaps in
    a WRONG term sampled (seeded) from the OTHER extracted terms. This is a
    heuristic swap, not a fact check -- it can occasionally produce an
    accidentally-true "false" statement if two terms are near-synonyms.
  - Multiple-choice: right answer is the term; three distractor terms are
    sampled (seeded) from the other extracted terms.

Determinism: all sampling uses random.Random(seed), so the same input file
and --seed always produce the same question set and shuffled order.

Usage:
  python3 tools/quiz_gen.py --doc templates/LEARNING_PACKET.md --out agent_outputs/quiz.html
  python3 tools/quiz_gen.py --doc academy/courses.json --seed 11 --max-questions 15

Exit codes:
  0 -- quiz generated
  1 -- fewer than 3 questions could be extracted (doc too sparse)
  2 -- input file missing or unreadable
"""
from __future__ import annotations
import argparse
import html
import json
import os
import random
import re
import sys

import cambium_io  # noqa: F401  (UTF-8 stdout guard)

TERM_BOLD_RE = re.compile(r"^\s*\*\*([^*]{1,80})\*\*\s*:\s*(.+?)\s*$")
TERM_DASH_RE = re.compile(r"^\s*([A-Za-z][\w /&-]{0,60}?)\s+-\s+(.+?)\s*$")
SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")


def _word_count(s: str) -> int:
    return len(s.split())


def extract_terms(text: str) -> list[tuple[str, str]]:
    """Return [(term, definition), ...] in source line order, deduped by term (first wins)."""
    seen = set()
    pairs: list[tuple[str, str]] = []
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
        pairs.append((term, definition))
    return pairs


def extract_sentences(text: str) -> list[str]:
    """Short declarative sentences containing ' is ' or ' are ', <= 25 words."""
    body = re.sub(r"^\s{0,3}#+\s*", "", text, flags=re.MULTILINE)
    body = re.sub(r"^\s*[-*]\s*", "", body, flags=re.MULTILINE)
    body = body.replace("|", " ").replace("**", "")
    out: list[str] = []
    for chunk in body.splitlines():
        chunk = chunk.strip()
        if not chunk or len(chunk) < 8:
            continue
        for sent in SENTENCE_SPLIT_RE.split(chunk):
            sent = sent.strip()
            if not sent or sent.endswith("?"):
                continue
            if (" is " in sent or " are " in sent) and _word_count(sent) <= 25:
                out.append(sent.rstrip("."))
    seen = set()
    uniq = []
    for s in out:
        if s not in seen:
            seen.add(s)
            uniq.append(s)
    return uniq


# ---------------------------------------------------------------------------
# Question builders
# ---------------------------------------------------------------------------

def build_cloze(pairs: list[tuple[str, str]]) -> list[dict]:
    items = []
    for term, definition in pairs:
        pattern = re.compile(re.escape(term), re.IGNORECASE)
        blanked = pattern.sub("_____", definition, count=1)
        if blanked == definition:
            blanked = f"_____ : {definition}"
        items.append({"kind": "cloze", "prompt": blanked, "answer": term})
    return items


def build_true_false(sentences: list[str], terms: list[str], rng: random.Random) -> list[dict]:
    items = []
    for i, sent in enumerate(sentences):
        make_true = (i % 2 == 0)
        if make_true or len(terms) < 2:
            items.append({"kind": "tf", "prompt": sent, "answer": "True"})
            continue
        candidates = [t for t in terms if re.search(re.escape(t), sent, re.IGNORECASE)]
        if not candidates:
            items.append({"kind": "tf", "prompt": sent, "answer": "True"})
            continue
        target = candidates[0]
        others = [t for t in terms if t.lower() != target.lower()]
        if not others:
            items.append({"kind": "tf", "prompt": sent, "answer": "True"})
            continue
        wrong = others[rng.randrange(len(others))]
        swapped = re.sub(re.escape(target), wrong, sent, count=1, flags=re.IGNORECASE)
        items.append({"kind": "tf", "prompt": swapped, "answer": "False"})
    return items


def build_multiple_choice(pairs: list[tuple[str, str]], rng: random.Random) -> list[dict]:
    all_terms = [t for t, _ in pairs]
    items = []
    for term, definition in pairs:
        others = [t for t in all_terms if t.lower() != term.lower()]
        rng.shuffle(others)
        distractors = others[:3]
        choices = [term] + distractors
        rng.shuffle(choices)
        items.append({
            "kind": "mc",
            "prompt": f"Which term matches: \"{definition}\"?",
            "choices": choices,
            "answer": term,
        })
    return items


def build_questions(doc_text: str, seed: int, max_questions: int) -> list[dict]:
    rng = random.Random(seed)
    pairs = extract_terms(doc_text)
    terms = [t for t, _ in pairs]
    sentences = extract_sentences(doc_text)

    pool: list[dict] = []
    pool.extend(build_cloze(pairs))
    pool.extend(build_true_false(sentences, terms, rng))
    pool.extend(build_multiple_choice(pairs, rng))

    rng.shuffle(pool)
    for idx, q in enumerate(pool):
        q["id"] = f"q{idx}"
    return pool[:max_questions]


# ---------------------------------------------------------------------------
# HTML rendering (self-contained, html.escape'd content)
# ---------------------------------------------------------------------------

def render_html(title: str, questions: list[dict]) -> str:
    esc = html.escape
    body_parts = []
    for q in questions:
        qid = esc(q["id"])
        prompt = esc(q["prompt"])
        if q["kind"] == "mc":
            opts = "".join(
                f'<label class="opt"><input type="radio" name="{qid}" value="{esc(c)}"> {esc(c)}</label><br>'
                for c in q["choices"]
            )
            body_parts.append(f'<div class="q" data-id="{qid}" data-answer="{esc(q["answer"])}">'
                               f'<p>{prompt}</p>{opts}</div>')
        elif q["kind"] == "tf":
            body_parts.append(
                f'<div class="q" data-id="{qid}" data-answer="{esc(q["answer"])}"><p>{prompt}</p>'
                f'<label class="opt"><input type="radio" name="{qid}" value="True"> True</label><br>'
                f'<label class="opt"><input type="radio" name="{qid}" value="False"> False</label></div>'
            )
        else:  # cloze
            body_parts.append(
                f'<div class="q" data-id="{qid}" data-answer="{esc(q["answer"])}"><p>{prompt}</p>'
                f'<input type="text" class="cloze-input" name="{qid}" placeholder="type the missing term"></div>'
            )
    body = "\n".join(body_parts)

    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><title>{esc(title)}</title>
<style>
body {{ font-family: system-ui, sans-serif; max-width: 720px; margin: 2rem auto; padding: 0 1rem; color: #1a1a1a; }}
h1 {{ font-size: 1.4rem; }}
.q {{ border: 1px solid #ddd; border-radius: 8px; padding: 0.75rem 1rem; margin-bottom: 0.75rem; }}
.opt {{ display: inline-block; margin: 0.15rem 0; }}
.cloze-input {{ width: 100%; padding: 0.4rem; box-sizing: border-box; }}
button {{ background: #2b6cb0; color: white; border: none; padding: 0.6rem 1.2rem; border-radius: 6px; cursor: pointer; }}
#score {{ font-weight: bold; margin-top: 1rem; }}
.note {{ color: #555; font-size: 0.85rem; }}
</style></head>
<body>
<h1>{esc(title)}</h1>
<p class="note">Auto-generated by heuristic text extraction (quiz_gen.py). Review before classroom use.</p>
<form id="quiz-form">
{body}
<button type="button" onclick="gradeQuiz()">Grade</button>
</form>
<div id="score"></div>
<script>
function gradeQuiz() {{
  var qs = document.querySelectorAll('.q');
  var correct = 0;
  qs.forEach(function(q) {{
    var answer = q.getAttribute('data-answer');
    var given = null;
    var radio = q.querySelector('input[type="radio"]:checked');
    var text = q.querySelector('input[type="text"]');
    if (radio) {{ given = radio.value; }}
    else if (text) {{ given = text.value.trim(); }}
    var ok = given !== null && given.toLowerCase() === answer.toLowerCase();
    if (ok) {{ correct += 1; q.style.borderColor = '#2f855a'; }}
    else {{ q.style.borderColor = '#c53030'; }}
  }});
  document.getElementById('score').textContent = 'Score: ' + correct + ' / ' + qs.length;
}}
</script>
</body></html>
"""


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _load_doc_text(path: str) -> str:
    if not os.path.exists(path):
        print(f"[quiz_gen] ERROR: doc not found: {path}", file=sys.stderr)
        sys.exit(2)
    try:
        with open(path, encoding="utf-8") as fh:
            return fh.read()
    except OSError as exc:
        print(f"[quiz_gen] ERROR: cannot read doc: {path}\n  {exc}", file=sys.stderr)
        sys.exit(2)


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Generate a deterministic quiz (HTML + answer key JSON) from a markdown document."
    )
    ap.add_argument("--doc", required=True, help="Path to the source markdown document.")
    ap.add_argument("--out", default=os.path.join("agent_outputs", "quiz.html"),
                     help="Output HTML path (default: agent_outputs/quiz.html).")
    ap.add_argument("--seed", type=int, default=7, help="Random seed for distractor/order sampling (default: 7).")
    ap.add_argument("--max-questions", type=int, default=20, help="Cap on questions emitted (default: 20).")
    args = ap.parse_args(argv)

    doc_text = _load_doc_text(args.doc)
    questions = build_questions(doc_text, args.seed, args.max_questions)

    if len(questions) < 3:
        print(
            f"[quiz_gen] ERROR: doc too sparse -- only {len(questions)} question(s) extractable "
            f"(need >= 3): {args.doc}",
            file=sys.stderr,
        )
        return 1

    title = f"Quiz: {os.path.basename(args.doc)}"
    out_html = render_html(title, questions)

    out_dir = os.path.dirname(os.path.abspath(args.out)) or "."
    os.makedirs(out_dir, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(out_html)

    key_path = os.path.splitext(args.out)[0] + "_key.json"
    key = {
        "doc": args.doc,
        "seed": args.seed,
        "questions": [{"id": q["id"], "kind": q["kind"], "answer": q["answer"]} for q in questions],
    }
    with open(key_path, "w", encoding="utf-8") as fh:
        json.dump(key, fh, indent=2)

    print(f"[quiz_gen] wrote {args.out} ({len(questions)} questions), key: {key_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
