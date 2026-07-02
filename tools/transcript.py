#!/usr/bin/env python3
"""transcript - a local, hash-chained learner transcript.

Purpose:
  Keep a tamper-evident local record of what a learner completed (modules,
  labs, quizzes), show it as a markdown transcript, and verify the record's
  integrity.

State file:
  --record transcript.json (created on first `add` if absent). Layout:
    {"format": "cambium-transcript-v1",
     "entries": [{"data": {...entry...}, "hash": "<sha256 hex>"}, ...]}

Chain rule (exactly what `verify` recomputes):
  hash_i = sha256(prev_hash + canonical_json(entry_i)) where canonical_json is
  json.dumps(entry, sort_keys=True, separators=(",", ":")) and the first
  entry's prev_hash is the empty string. Entry fields are always
  learner/item/kind/score/date (score is null when not given).

Usage:
  python3 tools/transcript.py add --record t.json --learner "R. Learner" \
      --item way-module --kind module --score 92 --date 2026-07-01
  python3 tools/transcript.py show --record t.json --learner "R. Learner"
  python3 tools/transcript.py verify --record t.json [--learner "R. Learner"]

Exit codes: 0 normally; 1 on invalid input (bad date, missing record for
show/verify, unknown learner on show, corrupt JSON) and when verify finds a
broken chain.

Honest limits:
  This is a local study log, not an accredited credential, and scores are
  whatever the caller reports. The hash chain makes in-place edits and
  reordering of recorded entries detectable, but it uses no secret key: a
  party who regenerates the whole file, or truncates the tail and recomputes
  nothing, cannot be caught without an externally kept copy of the latest
  chain hash (both `add` and `verify` print it so you can keep one).
"""
import argparse
import datetime
import hashlib
import json
import os
import sys

import cambium_io  # noqa: F401

FORMAT = "cambium-transcript-v1"
KINDS = ("module", "lab", "quiz")


def canonical_json(entry):
    return json.dumps(entry, sort_keys=True, separators=(",", ":"))


def chain_hash(prev_hash, entry):
    return hashlib.sha256((prev_hash + canonical_json(entry)).encode("utf-8")).hexdigest()


def load_record(path, must_exist):
    if not os.path.exists(path):
        if must_exist:
            raise ValueError("record not found: %s" % path)
        return {"format": FORMAT, "entries": []}
    try:
        data = json.load(open(path, encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise ValueError("cannot read record %s: %s" % (path, exc))
    if not isinstance(data, dict) or not isinstance(data.get("entries"), list):
        raise ValueError("record %s is not a transcript file (want format %s)"
                         % (path, FORMAT))
    return data


def save_record(path, data):
    parent = os.path.dirname(os.path.abspath(path))
    os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=1, ensure_ascii=False)
        fh.write("\n")


def verify_chain(entries):
    """Recompute the chain. Return (ok, first_broken_index_0based_or_None)."""
    prev = ""
    for i, e in enumerate(entries):
        data, stored = e.get("data"), e.get("hash")
        if not isinstance(data, dict) or chain_hash(prev, data) != stored:
            return (False, i)
        prev = stored
    return (True, None)


# ---------------------------------------------------------------------------
# Subcommands
# ---------------------------------------------------------------------------

def cmd_add(a):
    if a.date:
        try:
            date = datetime.date.fromisoformat(a.date).isoformat()
        except ValueError:
            print("[transcript] invalid --date (want YYYY-MM-DD): %s" % a.date,
                  file=sys.stderr)
            return 1
    else:
        date = datetime.date.today().isoformat()
    try:
        record = load_record(a.record, must_exist=False)
    except ValueError as exc:
        print("[transcript] %s" % exc, file=sys.stderr)
        return 1
    entry = {"learner": a.learner, "item": a.item, "kind": a.kind,
             "score": a.score, "date": date}
    prev = record["entries"][-1]["hash"] if record["entries"] else ""
    h = chain_hash(prev, entry)
    record["entries"].append({"data": entry, "hash": h})
    save_record(a.record, record)
    print("[transcript] recorded %s / %s (%s) for %s on %s"
          % (a.item, a.kind, "score %s" % a.score if a.score is not None else "no score",
             a.learner, date))
    print("[transcript] latest chain hash: %s (keep a copy outside the file "
          "to detect truncation)" % h)
    return 0


def cmd_show(a):
    try:
        record = load_record(a.record, must_exist=True)
    except ValueError as exc:
        print("[transcript] %s" % exc, file=sys.stderr)
        return 1
    rows = [e["data"] for e in record["entries"]
            if isinstance(e.get("data"), dict) and e["data"].get("learner") == a.learner]
    if not rows:
        print("[transcript] no entries for learner %r in %s" % (a.learner, a.record),
              file=sys.stderr)
        return 1
    lines = [
        "# Transcript: %s" % a.learner,
        "",
        "Record: %s (local, hash-chained; verifiable with `verify`; "
        "not an accredited credential)." % a.record,
        "",
        "| Date | Item | Kind | Score |",
        "|---|---|---|---|",
    ]
    for r in rows:
        score = "-" if r.get("score") is None else ("%g" % r["score"])
        lines.append("| %s | %s | %s | %s |" % (r.get("date", "-"), r.get("item", "-"),
                                                r.get("kind", "-"), score))
    kinds = {k: sum(1 for r in rows if r.get("kind") == k) for k in KINDS}
    scored = [r["score"] for r in rows if r.get("score") is not None]
    lines += [
        "",
        "Totals: %d entries (modules: %d, labs: %d, quizzes: %d)."
        % (len(rows), kinds["module"], kinds["lab"], kinds["quiz"]),
    ]
    if scored:
        lines.append("Average score: %.1f over %d scored entries."
                     % (sum(scored) / len(scored), len(scored)))
    else:
        lines.append("Average score: no scored entries.")
    if record["entries"]:
        lines.append("Latest chain hash: %s" % record["entries"][-1].get("hash", "?"))
    print("\n".join(lines))
    return 0


def cmd_verify(a):
    try:
        record = load_record(a.record, must_exist=True)
    except ValueError as exc:
        print("[transcript] %s" % exc, file=sys.stderr)
        return 1
    entries = record["entries"]
    ok, broken = verify_chain(entries)
    if not ok:
        bad = entries[broken].get("data") or {}
        print("[transcript] BROKEN chain at entry %d of %d (learner: %s, item: %s): "
              "recomputed hash does not match the stored one. The file was "
              "modified after that entry was recorded."
              % (broken + 1, len(entries), bad.get("learner", "?"), bad.get("item", "?")))
        return 1
    n = len(entries)
    print("[transcript] chain intact: %d entries verified." % n)
    if a.learner:
        mine = sum(1 for e in entries if e["data"].get("learner") == a.learner)
        print("[transcript] entries for %s: %d." % (a.learner, mine))
    if entries:
        print("[transcript] latest chain hash: %s (keep a copy outside the "
              "file; truncation of the tail is otherwise undetectable)"
              % entries[-1]["hash"])
    print("[transcript] note: local record, verifiable against in-place "
          "tampering of the file; not an accredited credential.")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="Local, hash-chained learner transcript.")
    sub = ap.add_subparsers(dest="cmd")

    p_add = sub.add_parser("add", help="record a completed module/lab/quiz")
    p_add.add_argument("--record", required=True, help="transcript.json (created if absent)")
    p_add.add_argument("--learner", required=True)
    p_add.add_argument("--item", required=True, help="module or lab id")
    p_add.add_argument("--kind", required=True, choices=KINDS)
    p_add.add_argument("--score", type=float, help="optional numeric score")
    p_add.add_argument("--date", help="YYYY-MM-DD (default: today)")

    p_show = sub.add_parser("show", help="markdown transcript table + totals")
    p_show.add_argument("--record", required=True)
    p_show.add_argument("--learner", required=True)

    p_ver = sub.add_parser("verify", help="recompute the hash chain")
    p_ver.add_argument("--record", required=True)
    p_ver.add_argument("--learner", help="optionally also report this learner's entry count")

    a = ap.parse_args(argv)
    if a.cmd == "add":
        return cmd_add(a)
    if a.cmd == "show":
        return cmd_show(a)
    if a.cmd == "verify":
        return cmd_verify(a)
    ap.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
