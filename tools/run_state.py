#!/usr/bin/env python3
"""run_state — maintain the live run-board state (agent_outputs/run_state.json).

The Orchestrator updates this file as a Cambium run advances; tools/run_trace.py auto-discovers it and
draws the live board + HTML dashboard from it — so findings, leaderboard, and the gate banner populate
WITHOUT hand-editing JSON. The headline win is `sync`: it reads each agent's own output file and lifts a
one-line finding automatically, so the board fills in as agents report back.

Subcommands (state file defaults to agent_outputs/run_state.json; override with --file PATH):
  phase N [--note "..."]                       set the current phase (+ optional now-note)
  finding <agent> "<one-line>"                 record one agent's headline finding
  loop <position>                              set loop_position (intra-phase iterate cursor, for handoff)
  gate <ID> "<decision>" [--rec R] [--kind K]  arm the gate banner (K = GATE | Checkpoint)
  cleargate                                    remove the gate banner (after APPROVE)
  lead "agent:score,agent:score,..."           set the leaderboard
  sync [--phase N] [--from DIR]                auto-fill findings from <DIR>/*.md "## Decision" lines
  show                                         print the JSON
  reset                                        start a fresh state file

Typical loop the Orchestrator runs each phase:
  python3 tools/run_state.py phase 2 --note "Scouts surveying the landscape"
  # … dispatch the real agents; they each write agent_outputs/<name>.md …
  python3 tools/run_state.py sync --phase 2          # lifts each agent's Decision line into the board
  python3 tools/run_trace.py --board "<request>"     # auto-reads run_state.json
"""
import sys, os, json, glob, re

ROOT = os.getcwd()
DEFAULT = os.path.join("agent_outputs", "run_state.json")
SKIP = {"run_state.json", "findings_ledger.csv", "master_synthesis.md", "leaderboard.md"}


def _file(args):
    if "--file" in args:
        return args[args.index("--file") + 1]
    return DEFAULT


def _opt(args, flag, default=None):
    return args[args.index(flag) + 1] if flag in args else default


def load(path):
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    return {"phase": None, "note": None, "findings": {}, "leaderboard": [], "gate": None, "loop_position": None}


def save(path, st):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(st, fh, ensure_ascii=False, indent=2)
        fh.write("\n")


def _agent_from_file(p):
    return os.path.basename(p)[:-3].replace("_", "-")


def _decision_line(md):
    """First substantive line under a '## Decision' (or '## Decision (…)') heading; else first non-heading line."""
    lines = md.splitlines()
    idx = next((i for i, l in enumerate(lines) if re.match(r"##\s+Decision", l.strip(), re.I)), None)
    pool = lines[idx + 1:] if idx is not None else lines
    for l in pool:
        s = l.strip().lstrip("-*0123456789. ").strip()
        if s and not s.startswith("#") and not s.startswith("*Generated"):
            s = re.sub(r"\s+", " ", s)
            return s[:119] + "…" if len(s) > 120 else s
    return None


def cmd_sync(st, args):
    src = _opt(args, "--from", "agent_outputs")
    ph = _opt(args, "--phase")
    if ph is not None:
        st["phase"] = int(ph)
    n = 0
    for p in sorted(glob.glob(os.path.join(src, "*.md"))):
        if os.path.basename(p) in SKIP:
            continue
        try:
            line = _decision_line(open(p, encoding="utf-8").read())
        except Exception:
            line = None
        if line:
            st["findings"][_agent_from_file(p)] = line
            n += 1
    print(f"[run_state] synced {n} finding(s) from {src}/")
    return st


def main():
    a = sys.argv[1:]
    if not a:
        print(__doc__); return
    cmd = a[0]
    path = _file(a)
    st = load(path)

    if cmd == "reset":
        st = {"phase": None, "note": None, "findings": {}, "leaderboard": [], "gate": None, "loop_position": None}
    elif cmd == "phase":
        st["phase"] = int(a[1])
        note = _opt(a, "--note")
        if note is not None:
            st["note"] = note
    elif cmd == "loop":
        st["loop_position"] = a[1]
    elif cmd == "finding":
        st["findings"][a[1]] = a[2]
    elif cmd == "gate":
        st["gate"] = {"id": a[1], "decision": a[2],
                      "kind": _opt(a, "--kind", "GATE"),
                      "recommendation": _opt(a, "--rec", "")}
    elif cmd == "cleargate":
        st["gate"] = None
    elif cmd == "lead":
        pairs = []
        for tok in a[1].split(","):
            if ":" in tok:
                name, sc = tok.rsplit(":", 1)
                try:
                    pairs.append([name.strip(), int(sc)])
                except ValueError:
                    pass
        st["leaderboard"] = pairs
    elif cmd == "sync":
        st = cmd_sync(st, a)
    elif cmd == "show":
        print(json.dumps(st, ensure_ascii=False, indent=2)); return
    else:
        print(f"unknown subcommand: {cmd}\n"); print(__doc__); return

    save(path, st)
    print(f"[run_state] {path} · phase={st['phase']} · {len(st['findings'])} finding(s)"
          + (" · gate armed" if st.get('gate') else ""))


if __name__ == "__main__":
    main()
