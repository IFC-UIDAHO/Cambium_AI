#!/usr/bin/env python3
"""handoff — durable Cambium memory across context windows (the /cambium:pause + /cambium:resume pair).

Long Cambium runs saturate the context window. Instead of letting the model auto-compact (lossy), the
Orchestrator PAUSES: it writes a dense, human-readable HANDOFF.md snapshot built from the run's own
memory (agent_outputs/run_state.json + findings_ledger.csv + synthesis/master_synthesis.md). You then
clear / open a FRESH context window and RESUME: handoff.py restores run_state.json, briefs you in a few
lines, and archives the consumed handoff. Pattern is commodity (Cline Memory Bank, LangGraph
checkpointing, Amp handoff); this is the Cambium-native, multi-agent, governance-aware version.

SINGLE-WRITER RULE: only the Orchestrator runs pause/resume. run_state.json has one writer.

Subcommands:
  pause  [--reason "..."] [--context N]   write agent_outputs/HANDOFF.md from current run state
  resume                                  restore run_state.json from HANDOFF.md, brief, archive it
  show                                    print the current HANDOFF.md (if any)

Paths: state=agent_outputs/run_state.json · handoff=agent_outputs/HANDOFF.md · archive=archive/handoffs/
"""
import sys, os, json, csv, glob, datetime

STATE = os.path.join("agent_outputs", "run_state.json")
HANDOFF = os.path.join("agent_outputs", "HANDOFF.md")
LEDGER = os.path.join("agent_outputs", "findings_ledger.csv")
SYNTH = os.path.join("synthesis", "master_synthesis.md")
ARCHIVE = os.path.join("archive", "handoffs")
MARK = "<!-- CAMBIUM_STATE (do not edit; used by `handoff.py resume`) -->"


def _opt(a, flag, default=None):
    return a[a.index(flag) + 1] if flag in a and a.index(flag) + 1 < len(a) else default


def _load_state():
    if os.path.exists(STATE):
        with open(STATE, encoding="utf-8") as fh:
            return json.load(fh)
    return {"phase": None, "note": None, "findings": {}, "leaderboard": [], "gate": None,
            "loop_position": None}


def _pretty(agent):
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import run_trace
        c, role = run_trace.pretty(agent)
        return f"{c} · {role}"
    except Exception:
        return agent


def pause(reason, context):
    st = _load_state()
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    L = []
    L.append(f"# Cambium Handoff")
    meta = f"*Written {ts}"
    if reason:
        meta += f" · reason: {reason}"
    if context:
        meta += f" · context: {context}%"
    L.append(meta + "*")
    L.append("")
    L.append("## Resume in one move")
    L.append("Open a **fresh context window**, then run `/cambium:resume` (or "
             "`python3 tools/handoff.py resume`). It restores the run state and briefs you. "
             "Nothing is finalized; any open gate still needs your APPROVE.")
    L.append("")
    L.append("## Where we are")
    L.append(f"- **Phase:** {st.get('phase')}" + (f" — {st['note']}" if st.get("note") else ""))
    g = st.get("gate")
    L.append(f"- **Open gate:** {g['id']} — {g.get('decision','')}" if g else "- **Open gate:** none")
    if st.get("loop_position") is not None:
        L.append(f"- **Loop position:** {st['loop_position']}")
    L.append("")
    if st.get("findings"):
        L.append("## Findings so far")
        for ag, f in st["findings"].items():
            L.append(f"- **{_pretty(ag)}** — {f}")
        L.append("")
    if st.get("leaderboard"):
        L.append("## Leaderboard")
        for name, score in st["leaderboard"][:8]:
            L.append(f"- {score} · {_pretty(name)}")
        L.append("")
    # ledger tail (open P0/P1 items if present)
    if os.path.exists(LEDGER):
        try:
            rows = list(csv.DictReader(open(LEDGER, encoding="utf-8")))
            openish = [r for r in rows if (r.get("status", "").lower() == "open")]
            if openish:
                L.append("## Open ledger items")
                for r in openish[:10]:
                    L.append(f"- [{r.get('severity','?')}] {r.get('issue','')} — {r.get('action','')}")
                L.append("")
        except Exception:
            pass
    if g:
        L.append("## Next action")
        L.append(f"Present / re-present gate **{g['id']}** ({g.get('decision','')}) and WAIT for the Director.")
        if g.get("recommendation"):
            L.append(f"Standing recommendation: {g['recommendation']}")
    else:
        L.append("## Next action")
        L.append(f"Continue phase {st.get('phase')}: dispatch the remaining agents, then re-emit the board.")
    L.append("")
    L.append(MARK)
    L.append("```json")
    L.append(json.dumps(st, ensure_ascii=False, indent=2))
    L.append("```")
    os.makedirs(os.path.dirname(HANDOFF) or ".", exist_ok=True)
    with open(HANDOFF, "w", encoding="utf-8") as fh:
        fh.write("\n".join(L) + "\n")
    print(f"[handoff] wrote {HANDOFF} · phase={st.get('phase')}"
          + (f" · gate {g['id']} open" if g else "") + " — clear context, then `resume`.")


def resume():
    if not os.path.exists(HANDOFF):
        print("[handoff] no HANDOFF.md to resume. Nothing to do."); return
    txt = open(HANDOFF, encoding="utf-8").read()
    # restore state from the embedded JSON block
    st = None
    if MARK in txt:
        after = txt.split(MARK, 1)[1]
        if "```json" in after:
            block = after.split("```json", 1)[1].split("```", 1)[0]
            try:
                st = json.loads(block)
            except Exception:
                st = None
    if st is not None:
        os.makedirs(os.path.dirname(STATE) or ".", exist_ok=True)
        with open(STATE, "w", encoding="utf-8") as fh:
            json.dump(st, fh, ensure_ascii=False, indent=2); fh.write("\n")
    # brief: print the human part (everything before the marker)
    brief = txt.split(MARK, 1)[0].strip()
    print(brief)
    print("\n[handoff] run_state.json restored." if st is not None else
          "\n[handoff] WARNING: could not parse embedded state; restored nothing.")
    # archive the consumed handoff
    os.makedirs(ARCHIVE, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    dest = os.path.join(ARCHIVE, f"HANDOFF_{ts}.md")
    try:
        os.replace(HANDOFF, dest)
        print(f"[handoff] archived previous handoff -> {dest}")
    except Exception as e:
        print(f"[handoff] (could not archive: {e})")


def main():
    a = sys.argv[1:]
    cmd = a[0] if a else "show"
    if cmd == "pause":
        pause(_opt(a, "--reason"), _opt(a, "--context"))
    elif cmd == "resume":
        resume()
    elif cmd == "show":
        print(open(HANDOFF, encoding="utf-8").read() if os.path.exists(HANDOFF) else "[handoff] no HANDOFF.md")
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
