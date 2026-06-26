#!/usr/bin/env python3
"""run_trace — show Cambium's workflow AND its live progress, in whatever form the reader can see.

Reuses tools/task_router.py. Renders three static views + a LIVE status board:
  --text             plain checklist (works in ANY chat)
  (default)          Mermaid flowchart (GitHub / Claude Code)
  --svg              SVG picture of the whole plan (visual chats / Cowork)
  --status N [note]  LIVE board: step N is "now working", earlier steps done, later waiting.
                     The Orchestrator re-emits this as it advances, so the human sees WHERE it is now.

Usage:
  python3 tools/run_trace.py "draft the grant proposal"
  python3 tools/run_trace.py --text "draft the grant proposal"
  python3 tools/run_trace.py --svg  "draft the grant proposal"
  python3 tools/run_trace.py --status 4 "checking the statistics" "draft the grant proposal"
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import task_router

def _short(s, n=46):
    s = " ".join(str(s).split())
    return s if len(s) <= n else s[:n-1] + "…"

def _esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

# ---- ordered steps (council-standardized; the spine all views share) ----
COUNCIL = {"orch":"Orchestration","preaward":"Pre-Award","partner":"Partnerships",
           "faculty":"Faculty","scout":"Scouts","lab":"Labs","verify":"Verification",
           "exec":"Execution","reporting":"Reporting","support":"Support","gov":"Governance"}
_A2C = {a: c for c, ags in task_router.CMAP.items() for a in ags}
_ORDER = list(COUNCIL)

def _council_of(agents):
    from collections import Counter
    cnt = Counter(_A2C.get(a, "orch") for a in agents)
    return max(cnt, key=lambda c: (cnt[c], -_ORDER.index(c)))

def steps(task):
    r = task_router.route(task)
    raw = [{"kind": "you", "label": "You ask, in plain words", "who": ""},
           {"kind": "work", "label": "Orchestration", "who": "routes your request"}]
    for p in r["phases"]:
        for g in p["groups"]:
            raw.append({"kind": "work", "label": COUNCIL[_council_of(g["agents"])], "who": ", ".join(g["agents"])})
        if p.get("gate"):
            gid = p["gate"]["id"]
            _kw = "GATE" if gid in ("G0","G1","G2","G3","G3a","G4","G5","G6") else "Checkpoint"
            raw.append({"kind": "gate", "label": f'{_kw} {gid} \u00b7 {p["gate"].get("decision","your decision")}', "who": ""})
    raw.append({"kind": "you", "label": "Delivered", "who": ""})
    S = []
    for st in raw:
        if S and st["kind"] == "work" and S[-1]["kind"] == "work" and S[-1]["label"] == st["label"]:
            S[-1]["who"] = ", ".join(x for x in (S[-1]["who"] + ", " + st["who"]).split(", ") if x)
        else:
            S.append(dict(st))
    return r, S

# ---- universal text ----
def text(task, cur=None, note=None):
    r, S = steps(task)
    head = f"Cambium plan for: {task}  ({r['type']}, {r['n_agents']} helpers)"
    out = [head, ""]
    for i, s in enumerate(S):
        if s["kind"] == "you": continue
        if cur is None:   mark = "·"
        elif i < cur:     mark = "✓"
        elif i == cur:    mark = "▶"
        else:             mark = "○"
        line = f"  {mark} {s['label']}" + (f" — {_short(s['who'],60)}" if s["who"] else "")
        if s["kind"] == "gate": line += "   (you APPROVE / REVISE / REJECT)"
        out.append(line)
    if cur is not None and 0 <= cur < len(S):
        c = S[cur]
        banner = (f"\n>> NOW: {c['label']} — {_short(c['who'],60)}" if c["kind"] == "work"
                  else f"\n>> WAITING FOR YOU: {c['label']}")
        if note: banner += f"  ({note})"
        out.append(banner)
    return "\n".join(out)

# ---- Mermaid (standardized) ----
def mermaid(task):
    r, S = steps(task)
    L = ["flowchart TD"]; prev = None
    for i, st in enumerate(S):
        nid = "N%d" % i
        if st["kind"] == "gate":
            node = nid + '{"\U0001F6A6 ' + st["label"] + '"}:::gate'
        elif st["kind"] == "you":
            node = nid + '(["' + st["label"] + '"]):::you'
        else:
            sub = ("<br/>" + _short(st["who"], 42)) if st["who"] else ""
            node = nid + '["<b>' + st["label"] + '</b>' + sub + '"]:::work'
        L.append("  " + node if prev is None else "  %s --> %s" % (prev, node))
        prev = nid
    L += ["  classDef you fill:#B7F36A,stroke:#0E8E5B,color:#052015;",
          "  classDef work fill:#0E3326,stroke:#16C079,color:#F4F7F2;",
          "  classDef gate fill:#15402F,stroke:#B7F36A,color:#B7F36A;"]
    return "\n".join(L)

# ---- SVG (plan when cur=None; live status board when cur set) ----
def _svg(task, cur=None, note=None):
    r, S = steps(task)
    W, top, step = 740, 96, 58
    cys = [top + i*step + 18 for i in range(len(S))]
    H = cys[-1] + 36
    P = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Cambium workflow status" font-family="Inter,system-ui,sans-serif">',
         '<defs><marker id="ar" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0 L10 5 L0 10 z" fill="#16C079"/></marker></defs>',
         f'<rect x="0" y="0" width="{W}" height="{H}" rx="16" fill="#07231A" stroke="#1F4D3B"/>',
         f'<text x="30" y="40" fill="#F4F7F2" font-size="18" font-weight="700">Cambium — {"live progress" if cur is not None else "what runs for your request"}</text>',
         f'<text x="30" y="60" fill="#8AA197" font-size="12">{_esc(_short(task,72))}</text>']
    if cur is not None and 0 <= cur < len(S):
        c = S[cur]
        msg = (f"▶ NOW: {c['label']} — {_short(c['who'],46)}" if c["kind"]=="work" else f"🚦 Waiting for your decision")
        if note: msg += f" · {note}"
        P.append(f'<rect x="30" y="70" width="{W-60}" height="20" rx="6" fill="#103a2b"/>'
                 f'<text x="40" y="84" fill="#B7F36A" font-size="12" font-weight="700">{_esc(_short(msg,86))}</text>')
        for i in range(len(cys)): cys[i] += 14
        H2 = cys[-1] + 36
        P[2] = f'<rect x="0" y="0" width="{W}" height="{H2}" rx="16" fill="#07231A" stroke="#1F4D3B"/>'
        P[0] = f'<svg viewBox="0 0 {W} {H2}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Cambium live progress" font-family="Inter,system-ui,sans-serif">'
    for i in range(len(S)-1):
        P.append(f'<line x1="370" y1="{cys[i]+17}" x2="370" y2="{cys[i+1]-17}" stroke="#16C079" stroke-width="2" marker-end="url(#ar)"/>')
    for i, (s, cy) in enumerate(zip(S, cys)):
        if cur is None: state = "plan"
        elif i < cur:   state = "done"
        elif i == cur:  state = "now"
        else:           state = "todo"
        if s["kind"] == "you":
            fill = "#B7F36A" if state in ("plan","done","now") else "#2c4a39"
            P.append(f'<rect x="260" y="{cy-15}" width="220" height="30" rx="15" fill="{fill}"/>'
                     f'<text x="370" y="{cy+5}" text-anchor="middle" fill="#052015" font-size="13" font-weight="700">{_esc(s["label"])}</text>')
            continue
        if s["kind"] == "gate":
            stroke = "#B7F36A" if state in ("plan","now","done") else "#3a5a48"
            P.append(f'<polygon points="370,{cy-21} 530,{cy} 370,{cy+21} 210,{cy}" fill="#15402F" stroke="{stroke}" stroke-width="{3 if state=="now" else 1.6}"/>'
                     f'<text x="370" y="{cy+5}" text-anchor="middle" fill="{"#B7F36A" if state!="todo" else "#5E7468"}" font-size="12" font-weight="700">{_esc(_short(s["label"],30))}</text>')
            continue
        # work node, with state styling + who sub-line
        fills = {"plan":"#0E3326","done":"#0E3326","now":"#0f3f2d","todo":"#0a271d"}
        strokes = {"plan":"#16C079","done":"#2A5A45","now":"#B7F36A","todo":"#1F4D3B"}
        txt = {"plan":"#F4F7F2","done":"#86998F","now":"#F4F7F2","todo":"#5E7468"}
        pre = {"plan":"","done":"✓ ","now":"▶ ","todo":"○ "}[state]
        sw = 3 if state == "now" else 1.4
        P.append(f'<rect x="180" y="{cy-19}" width="380" height="40" rx="9" fill="{fills[state]}" stroke="{strokes[state]}" stroke-width="{sw}"/>')
        who = _short(s["who"], 52)
        P.append(f'<text x="370" y="{cy-2}" text-anchor="middle" fill="{txt[state]}" font-size="13" font-weight="600">{_esc(pre + s["label"])}</text>')
        if who:
            P.append(f'<text x="370" y="{cy+13}" text-anchor="middle" fill="{"#B7F36A" if state=="now" else "#8AA197" if state!="todo" else "#4d6358"}" font-size="10">{_esc(who)}</text>')
    P.append('</svg>')
    return "\n".join(P)

def svg(task): return _svg(task, None)
def status(task, cur, note=None): return _svg(task, cur, note)

def main():
    a = sys.argv[1:]
    if "--status" in a:
        i = a.index("--status"); cur = int(a[i+1])
        rest = [x for j, x in enumerate(a) if x not in ("--status",) and j != i+1]
        note = None
        # optional quoted note = first leftover that isn't part of the task? keep simple: task is everything
        task = " ".join(x for x in rest if not x.startswith("--")) or "do a research task"
        print(status(task, cur, note)); return
    mode = "svg" if "--svg" in a else "text" if "--text" in a else "mermaid"
    task = " ".join(x for x in a if not x.startswith("--")) or "do a research task"
    print({"text": text, "svg": svg, "mermaid": mermaid}[mode](task))

if __name__ == "__main__":
    main()
