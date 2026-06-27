#!/usr/bin/env python3
"""learning_gate — enforce the Director's contribution at a gate (PHILOSOPHY.md §5).

A Cambium gate is not a rubber stamp. Before a gate opens, the Director must supply their OWN
hypothesis, reasoning, a justified choice, and an answer to the Orchestrator's Socratic question —
and, before a phase runs, a Director Brief. This tool checks the contribution is genuinely present
(not blank, not pasted from the AI summary) and appends it — immutable, timestamped — to the
Contribution Ledger. Deterministic; no model calls. This is what turns concerns #3 (creativity) and
#4 (learning) from "claimed" into "enforced".

Usage:
  python3 tools/learning_gate.py check --gate G2 --director "Jaslam" --contribution c.json [--ai-summary s.txt]
  python3 tools/learning_gate.py brief --phase 2 --director "Jaslam" --brief brief.json
Contribution JSON: {"hypothesis":"...","reasoning":"...","choice":"A — ...","socratic":"..."}
Brief JSON:        {"question":"...","surprise":"...","constraint":"..."}
Exit: 0 = complete (gate may open) · 1 = BLOCKED (incomplete) · 2 = complete but copy-flag REVIEW
"""
import argparse, csv, json, os, re, sys, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEDGER = os.path.join(ROOT, "governance", "CONTRIBUTION_LEDGER.csv")
MIN_WORDS = 40
COPY_THRESHOLD = 0.6

def _words(s): return re.findall(r"[a-zA-Z0-9']+", (s or "").lower())

def _jaccard(a, b):
    A, B = set(_words(a)), set(_words(b))
    if not A or not B: return 0.0
    return len(A & B) / len(A | B)

def validate_contribution(d, ai_summary=""):
    """Return (ok, problems, copy_flag). ok=True iff all four fields are genuinely present."""
    problems = []
    h, r, c, s = d.get("hypothesis", ""), d.get("reasoning", ""), d.get("choice", ""), d.get("socratic", "")
    if len(_words(h)) < MIN_WORDS: problems.append(f"hypothesis < {MIN_WORDS} words")
    if len(_words(r)) < MIN_WORDS: problems.append(f"reasoning < {MIN_WORDS} words")
    if not str(c).strip(): problems.append("choice missing")
    if not str(s).strip(): problems.append("Socratic answer blank (blocks advance)")
    copy_flag = "PASS"
    if ai_summary and _jaccard(h, ai_summary) > COPY_THRESHOLD:
        copy_flag = "REVIEW"   # hypothesis looks pasted from the AI summary
    return (len(problems) == 0, problems, copy_flag)

def validate_brief(d):
    missing = [k for k in ("question", "surprise", "constraint") if not str(d.get(k, "")).strip()]
    return (len(missing) == 0, (["brief missing: " + ", ".join(missing)] if missing else []))

def append_ledger(path, row):
    new = not os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        if new: w.writerow(["timestamp", "kind", "id", "director", "status", "copy_flag", "detail"])
        w.writerow(row)

def main(argv=None):
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd")
    pc = sub.add_parser("check"); pc.add_argument("--gate", required=True); pc.add_argument("--director", default="Director")
    pc.add_argument("--contribution", required=True); pc.add_argument("--ai-summary")
    pb = sub.add_parser("brief"); pb.add_argument("--phase", required=True); pb.add_argument("--director", default="Director")
    pb.add_argument("--brief", required=True)
    a = ap.parse_args(argv)
    ts = time.strftime("%Y-%m-%dT%H:%M:%S")
    if a.cmd == "check":
        d = json.load(open(a.contribution, encoding="utf-8"))
        ai = open(a.ai_summary, encoding="utf-8").read() if a.ai_summary and os.path.exists(a.ai_summary) else ""
        ok, probs, flag = validate_contribution(d, ai)
        append_ledger(LEDGER, [ts, "contribution", a.gate, a.director, "complete" if ok else "BLOCKED", flag, "; ".join(probs) or "ok"])
        if not ok:
            print(f"[learning_gate] ⛔ GATE {a.gate} BLOCKED — director contribution incomplete: {'; '.join(probs)}"); return 1
        if flag == "REVIEW":
            print(f"[learning_gate] ⚠ GATE {a.gate} complete, but the hypothesis looks copied from the AI summary — human review."); return 2
        print(f"[learning_gate] ✓ GATE {a.gate} — director contribution recorded; the gate may open."); return 0
    if a.cmd == "brief":
        d = json.load(open(a.brief, encoding="utf-8")); ok, probs = validate_brief(d)
        append_ledger(LEDGER, [ts, "brief", f"phase-{a.phase}", a.director, "complete" if ok else "BLOCKED", "-", "; ".join(probs) or "ok"])
        if not ok: print(f"[learning_gate] ⛔ Phase {a.phase} cannot run — {'; '.join(probs)}"); return 1
        print(f"[learning_gate] ✓ Phase {a.phase} Director Brief recorded; the phase may run."); return 0
    ap.print_help(); return 0

if __name__ == "__main__": sys.exit(main())
