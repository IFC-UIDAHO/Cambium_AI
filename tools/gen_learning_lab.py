#!/usr/bin/env python3
"""gen_learning_lab — turn a learning spec into an interactive Cambium Learning Lab page.

One engine (templates/learning_lab_template.html) powers both:
  - the Cambium Academy   (academy/courses.json  -> academy/index.html)
  - the per-run Learning Lab that the teaching-assistant produces after a build/analysis.

The spec is a small JSON "lab": modules -> lessons -> blocks, where a block is one of
concept | predict | reveal | flashcards | diagram | worked | explain, plus a per-module
mastery quiz. The mechanics are evidence-based: active recall (predict/reveal/quiz),
spaced repetition (flashcards, Leitner boxes), dual coding (clickable diagram),
worked-example + faded practice (worked/your-turn), and self-explanation (explain).

Usage:
  python3 tools/gen_learning_lab.py --academy                 # build the Academy
  python3 tools/gen_learning_lab.py --demo                    # build demo/learning_lab.html
  python3 tools/gen_learning_lab.py --spec lab.json --out out.html [--brand "Learning Lab"]

The teaching-assistant can build a spec from a run with lab_from_brief(...) and hand it here.
"""
import argparse, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE = os.path.join(ROOT, "templates", "learning_lab_template.html")

REQUIRED_BLOCK_TYPES = {"concept","predict","reveal","flashcards","diagram","worked","explain"}

def validate(lab):
    """Cheap structural checks so a malformed spec fails loudly, not silently in the browser."""
    errs = []
    if not isinstance(lab, dict): return ["lab must be an object"]
    if not lab.get("title"): errs.append("lab.title is required")
    mods = lab.get("modules")
    if not isinstance(mods, list) or not mods: errs.append("lab.modules must be a non-empty list")
    for mi, m in enumerate(mods or []):
        if not m.get("title"): errs.append(f"module[{mi}].title is required")
        if not isinstance(m.get("lessons"), list) or not m["lessons"]:
            errs.append(f"module[{mi}].lessons must be a non-empty list")
        for li, les in enumerate(m.get("lessons", [])):
            for bi, b in enumerate(les.get("blocks", [])):
                t = b.get("type")
                if t not in REQUIRED_BLOCK_TYPES:
                    errs.append(f"module[{mi}].lesson[{li}].block[{bi}] has unknown type {t!r}")
                if t == "predict" and (not b.get("choices") or "answer" not in b):
                    errs.append(f"module[{mi}].lesson[{li}].block[{bi}] predict needs choices+answer")
    return errs

def render(lab):
    errs = validate(lab)
    if errs:
        raise ValueError("invalid lab spec:\n  - " + "\n  - ".join(errs))
    html = open(TEMPLATE, encoding="utf-8").read()
    # escape </script> so the JSON payload cannot break out of its <script> tag
    data = json.dumps(lab, ensure_ascii=False).replace("</", "<\\/")
    html = html.replace("__LAB_DATA__", data)
    html = html.replace("__TITLE__", lab.get("title", "Cambium Learning Lab"))
    html = html.replace("__SUBTITLE__", lab.get("subtitle", ""))
    return html

def lab_from_brief(title, breath, nodes, edges, decisions, concepts, quiz, brand="Learning Lab"):
    """Convenience the teaching-assistant uses: map a run's facts into a one-module lab.

    nodes/edges -> the architecture diagram (dual coding);
    concepts    -> list of (front, back) turned into flashcards + one explain-back;
    decisions   -> list of (choice, why, tradeoff) rows;
    quiz        -> list of (q, [choices], answer_index, explain).
    """
    deck = {"type": "flashcards", "cards": [{"front": f, "back": b} for f, b in concepts]}
    drows = "".join(f"<tr><td>{c}</td><td>{w}</td><td>{t}</td></tr>" for c, w, t in decisions)
    table = ("<table class='tbl'><tr><th>Choice</th><th>Why</th><th>Traded away</th></tr>"
             + drows + "</table>")
    blocks = [
        {"type": "concept", "title": "In one breath", "html": f"<p>{breath}</p>"},
        {"type": "diagram", "caption": "How the pieces connect", "nodes": nodes, "edges": edges},
        deck,
        {"type": "concept", "title": "The decisions, and what we traded", "html": table},
        {"type": "explain", "prompt": "Explain what we built and why, in your own words.",
         "model": f"<p>{breath}</p>"},
    ]
    return {"id": "run", "brand": brand, "title": title,
            "subtitle": "An interactive walkthrough of this run.",
            "modules": [{"id": "build", "title": title, "lessons":
                         [{"id": "l1", "title": "Understand and own this build", "blocks": blocks}],
                         "quiz": [{"q": q, "choices": c, "answer": a, "explain": e}
                                  for (q, c, a, e) in quiz]}]}

def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--academy", action="store_true")
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--spec")
    ap.add_argument("--out")
    ap.add_argument("--brand")
    a = ap.parse_args(argv)
    jobs = []
    if a.academy: jobs.append((os.path.join(ROOT, "academy", "courses.json"),
                               os.path.join(ROOT, "academy", "index.html")))
    if a.demo: jobs.append((os.path.join(ROOT, "templates", "learning_lab_demo.json"),
                            os.path.join(ROOT, "demo", "learning_lab.html")))
    if a.spec: jobs.append((a.spec, a.out or os.path.splitext(a.spec)[0] + ".html"))
    if not jobs:
        ap.error("nothing to do: pass --academy, --demo, or --spec")
    for spec, out in jobs:
        lab = json.load(open(spec, encoding="utf-8"))
        if a.brand: lab["brand"] = a.brand
        html = render(lab)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        open(out, "w", encoding="utf-8").write(html)
        print(f"[learning-lab] {os.path.relpath(spec, ROOT)} -> {os.path.relpath(out, ROOT)} "
              f"({len(html)//1024} KB, {sum(len(m['lessons']) for m in lab['modules'])} lessons)")
    return 0

if __name__ == "__main__":
    sys.exit(main())
