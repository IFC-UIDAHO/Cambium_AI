#!/usr/bin/env python3
"""learning_gate — enforce the Director's contribution at a gate (PHILOSOPHY.md §5).

A Cambium gate is not a rubber stamp. Before a gate opens, the Director must supply their OWN
hypothesis, reasoning, a justified choice, and an answer to the Orchestrator's Socratic question —
and, before a phase runs, a Director Brief. This tool checks the contribution is genuinely present
(not blank, not pasted from the AI summary) and appends it — immutable, timestamped — to the
Contribution Ledger. Deterministic; no model calls. This is what turns concerns #3 (creativity) and
#4 (learning) from "claimed" into "enforced".

NEW (enforce-all, AI_POLICY §3): when an --ai-summary is supplied, the gate also records *what the
human changed* relative to the AI draft — a change_ratio (fraction of the human's words that are NOT in
the AI summary) plus a human-vs-AI unified diff written to governance/contribution_diffs/. A contribution
that is <15% novel against the AI draft is flagged LOW-DELTA for review. This closes the "we record that
a human added something, but not what they changed" gap.

Usage:
  python3 tools/learning_gate.py check --gate G2 --director "Jaslam" --contribution c.json [--ai-summary s.txt]
  python3 tools/learning_gate.py brief --phase 2 --director "Jaslam" --brief brief.json
Contribution JSON: {"hypothesis":"...","reasoning":"...","choice":"A — ...","socratic":"..."}
Brief JSON:        {"question":"...","surprise":"...","constraint":"..."}
Exit: 0 = complete (gate may open) · 1 = BLOCKED (incomplete) · 2 = complete but copy-flag / LOW-DELTA REVIEW
"""
import argparse, csv, difflib, json, os, re, sys, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEDGER = os.path.join(ROOT, "governance", "CONTRIBUTION_LEDGER.csv")
DIFFDIR = os.path.join(ROOT, "governance", "contribution_diffs")
MIN_WORDS = 40
COPY_THRESHOLD = 0.6
LOW_DELTA = 0.15   # < 15% novel words vs the AI draft -> flag for review

def _words(s): return re.findall(r"[a-zA-Z0-9']+", (s or "").lower())

def _jaccard(a, b):
    A, B = set(_words(a)), set(_words(b))
    if not A or not B: return 0.0
    return len(A & B) / len(A | B)

def contribution_delta(human_text, ai_summary):
    """What did the human change vs the AI draft? Return (change_ratio, novel_count, total).
    change_ratio = fraction of the human's (deduplicated) words absent from the AI summary."""
    H, A = set(_words(human_text)), set(_words(ai_summary))
    if not H: return (0.0, 0, 0)
    novel = H - A
    return (len(novel) / len(H), len(novel), len(H))

def write_diff(gate, human_text, ai_summary, ts):
    os.makedirs(DIFFDIR, exist_ok=True)
    path = os.path.join(DIFFDIR, "%s-%s.diff" % (gate, ts.replace(":", "")))
    diff = difflib.unified_diff(
        (ai_summary or "").splitlines(), (human_text or "").splitlines(),
        fromfile="ai_draft", tofile="human_contribution", lineterm="")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(diff) or "(no line-level difference)")
    return path

def validate_contribution(d, ai_summary=""):
    """Return (ok, problems, copy_flag). ok=True iff all four fields are genuinely present."""
    problems = []
    h, r, c, s = d.get("hypothesis", ""), d.get("reasoning", ""), d.get("choice", ""), d.get("socratic", "")
    if len(_words(h)) < MIN_WORDS: problems.append("hypothesis < %d words" % MIN_WORDS)
    if len(_words(r)) < MIN_WORDS: problems.append("reasoning < %d words" % MIN_WORDS)
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
        detail = "; ".join(probs) or "ok"
        delta_flag = ""
        if ai:
            human_text = (d.get("hypothesis", "") + "\n" + d.get("reasoning", "")).strip()
            ratio, novel, total = contribution_delta(human_text, ai)
            dpath = write_diff(a.gate, human_text, ai, ts)
            detail = "%s | change_ratio=%.2f (%d/%d novel words) | diff=%s" % (
                detail, ratio, novel, total, os.path.relpath(dpath, ROOT))
            if ok and ratio < LOW_DELTA:
                delta_flag = "LOW-DELTA"
        append_ledger(LEDGER, [ts, "contribution", a.gate, a.director,
                               "complete" if ok else "BLOCKED",
                               (delta_flag or flag), detail])
        if not ok:
            print("[learning_gate] BLOCKED GATE %s — director contribution incomplete: %s" % (a.gate, "; ".join(probs))); return 1
        if flag == "REVIEW":
            print("[learning_gate] REVIEW GATE %s — hypothesis looks copied from the AI summary." % a.gate); return 2
        if delta_flag == "LOW-DELTA":
            print("[learning_gate] REVIEW GATE %s complete, but the contribution is <%.0f%% novel vs the AI draft "
                  "(change recorded in the ledger) — human review." % (a.gate, LOW_DELTA * 100)); return 2
        print("[learning_gate] OK GATE %s — director contribution recorded (change tracked); the gate may open." % a.gate); return 0
    if a.cmd == "brief":
        d = json.load(open(a.brief, encoding="utf-8")); ok, probs = validate_brief(d)
        append_ledger(LEDGER, [ts, "brief", "phase-%s" % a.phase, a.director, "complete" if ok else "BLOCKED", "-", "; ".join(probs) or "ok"])
        if not ok: print("[learning_gate] BLOCKED Phase %s cannot run — %s" % (a.phase, "; ".join(probs))); return 1
        print("[learning_gate] OK Phase %s Director Brief recorded; the phase may run." % a.phase); return 0
    ap.print_help(); return 0

if __name__ == "__main__": sys.exit(main())
