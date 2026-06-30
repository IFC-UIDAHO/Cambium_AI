#!/usr/bin/env python3
"""gen_board_pro — the premium live Cambium run board (Cowork artifact / browser).

Reads agent_outputs/run_state.json and renders one gorgeous, self-contained, light-mode HTML board:
a hero with live progress, an animated phase rail, council-coloured agent cards with findings, a
chronological findings feed, a completion summary, and a prominent gate decision card. It is the
reopenable SIDEBAR board; tools/gen_inline_board.py renders the same run as an in-chat show_widget fragment.

  python3 tools/gen_board_pro.py [--state agent_outputs/run_state.json] [--out agent_outputs/run_board.html] [--title "<request>"]
"""
import argparse, html, json, os, sys
import cambium_io  # noqa: F401 — reconfigures stdout/stderr to UTF-8 on Windows; provides data_home()
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

COUNCIL_HUE = {
 "Orchestration": 265, "Pre-Award": 190, "Partnerships": 150, "Faculty": 330, "Scouts": 172,
 "Labs": 210, "Verification": 255, "Execution": 28, "Reporting": 95, "Support": 145, "Governance": 8}

def esc(s): return html.escape(str(s or ""))

def status_of(i, cur):
    if cur is None: return "waiting"
    if cur > i + 1: return "done"
    if cur == i + 1: return "now"
    return "waiting"

_SHORT2TITLE = {"orch":"Orchestration","preaward":"Pre-Award","partner":"Partnerships","faculty":"Faculty",
 "scout":"Scouts","lab":"Labs","verify":"Verification","exec":"Execution","reporting":"Reporting",
 "support":"Support","gov":"Governance"}

def _routed_phases(task):
    import task_router
    a2c = {a: _SHORT2TITLE.get(c, c.title()) for c, ags in task_router.CMAP.items() for a in ags}
    out = []
    for ph in task_router.route(task or "a Cambium run").get("phases", []):
        agents = []
        for grp in ph.get("groups", []):
            for a in grp.get("agents", []):
                council = a2c.get(a, "Support")
                role = a.replace("-", " ").title()
                agents.append([council, role, "cambium-institute:" + a])
        council = agents[0][0] if agents else "Support"
        out.append({"council": council, "label": ph.get("id", "phase").replace("-", " ").title(),
                    "agents": agents, "gate": ph.get("gate")})
    return out

def load(state):
    d = json.load(open(state, encoding="utf-8"))
    phases = d.get("plan", {}).get("phases", [])
    if not phases:
        task = d.get("note") or d.get("plan", {}).get("request") or ""
        try: phases = _routed_phases(task)
        except Exception: phases = []
    return d, phases, d.get("phase"), d.get("note", "")

def render(state_path, title):
    d, phases, cur, note = load(state_path)
    n_ag = sum(len(p.get("agents", [])) for p in phases)
    n_co = len({a[0] for p in phases for a in p.get("agents", [])})
    n_gt = sum(1 for p in phases if p.get("gate"))
    done = sum(1 for i, _ in enumerate(phases) if status_of(i, cur) == "done")
    total = len(phases) or 1
    pct = round(100 * done / total)
    req = title or d.get("plan", {}).get("request") or note or "Cambium run"

    rail = []
    for i, p in enumerate(phases):
        st = status_of(i, cur)
        rail.append(f'<div class="chip {st}"><span class="dot"></span><b>P{i+1}</b><span>{esc(p.get("council",""))}</span></div>')
        if i < len(phases) - 1:
            rail.append(f'<div class="conn {("done" if st=="done" else "")}"></div>')

    cards = []
    for i, p in enumerate(phases):
        st = status_of(i, cur)
        hue = COUNCIL_HUE.get(p.get("council"), 150)
        agents = []
        for a in p.get("agents", []):
            council, role, atype = (a + ["", "", ""])[:3]
            ah = COUNCIL_HUE.get(council, 150)
            finding = a[3] if len(a) > 3 else ""
            glyph = {"done": "✓", "now": "▶", "waiting": "○"}[st]
            agents.append(
                f'<div class="agent {st}" style="--h:{ah}">'
                f'<div class="atop"><span class="badge">{glyph}</span>'
                f'<span class="acouncil">{esc(council)}</span><span class="arole">{esc(role)}</span></div>'
                + (f'<div class="afind">{esc(finding)}</div>' if finding else "")
                + f'<div class="atype">{esc(atype)}</div></div>')
        gate = ""
        if p.get("gate"):
            g = p["gate"]; gst = "cleared" if st == "done" else ("pending" if st == "now" else "upcoming")
            gate = (f'<div class="gaterow {gst}">⛩ Gate {esc(g.get("id"))} — {esc(g.get("decision"))}'
                    f'<em>{"APPROVED" if gst=="cleared" else ("YOUR DECISION" if gst=="pending" else "upcoming")}</em></div>')
        cards.append(
            f'<section class="phase {st}" style="--h:{hue}">'
            f'<h3><span class="pn">Phase {i+1}</span> {esc(p.get("label",""))}'
            f'<span class="pstate">{st}</span></h3>'
            f'<div class="agents">{"".join(agents)}</div>{gate}</section>')

    active_gate = next((p["gate"] for i, p in enumerate(phases)
                        if p.get("gate") and status_of(i, cur) == "now"), None)
    gatecard = ""
    if active_gate:
        gatecard = (
          f'<div class="activegate"><div class="ag-h">⛩ GATE {esc(active_gate.get("id"))} — your decision</div>'
          f'<div class="ag-q">{esc(active_gate.get("decision"))}</div>'
          f'<div class="ag-b"><span class="approve">APPROVE</span><span class="revise">REVISE</span><span class="reject">REJECT</span></div>'
          f'<div class="ag-hint">Type your choice in chat — nothing finalizes without it.</div></div>')

    feed_items = []
    for i, p in enumerate(phases):
        st = status_of(i, cur)
        if st == "waiting": continue
        for a in p.get("agents", []):
            if len(a) > 3 and a[3]:
                feed_items.append(f'<li><span class="fc">{esc(a[0])}</span> {esc(a[1])} — {esc(a[3])}</li>')
    feed = (f'<div class="feed"><h4>Findings feed</h4><ul>{"".join(feed_items)}</ul></div>'
            if feed_items else "")

    complete = ""
    if cur and cur > total:
        complete = (f'<div class="complete">✓ Run complete — {n_gt} gate(s) cleared · {n_ag} specialists · '
                    f'{n_co} councils · every number reproduced before release.</div>')

    nowline = note or ("complete" if (cur and cur > total) else "running")
    return TEMPLATE.format(req=esc(req), pct=pct, done=done, total=total, n_ag=n_ag, n_co=n_co, n_gt=n_gt,
                           rail="".join(rail), cards="".join(cards), gatecard=gatecard, nowline=esc(nowline),
                           feed=feed, complete=complete)

TEMPLATE = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>Cambium - run board</title>
<style>
 :root{{color-scheme:light;--bg:#f4f8f5;--card:#ffffff;--edge:#e2ebe5;--ink:#10241c;--mut:#5b6f66;--dim:#9aa9a1;--forest:#176c34;--lime:#3a9d4e;--emer:#0f8a4f}}
 *{{box-sizing:border-box}} body{{margin:0;background:var(--bg);color:var(--ink);font:14px/1.55 Inter,system-ui,Segoe UI,sans-serif}}
 .wrap{{max-width:1000px;margin:0 auto;padding:20px}}
 .hero{{border:1px solid var(--edge);border-radius:18px;padding:20px 22px;background:linear-gradient(135deg,#ffffff,#eef5f0)}}
 .brand{{display:flex;align-items:center;gap:10px;font-weight:800;font-size:17px;color:var(--forest)}}
 .brand .hex{{font-size:20px}} .brand .tag{{color:var(--mut);font-weight:600;font-size:12px}}
 .req{{margin-top:8px;font-size:18px;font-weight:600}}
 .meta{{margin-top:6px;color:var(--mut);font-size:12.5px}}
 .prog{{margin-top:14px;height:10px;border-radius:99px;background:#e7efe9;overflow:hidden}}
 .prog>span{{display:block;height:100%;width:0;border-radius:99px;background:linear-gradient(90deg,#0f8a4f,#3a9d4e);animation:fill 1.1s cubic-bezier(.2,.8,.2,1) forwards}}
 @keyframes fill{{to{{width:{pct}%}}}}
 .pl{{display:flex;justify-content:space-between;margin-top:5px;color:var(--dim);font-size:11px}}
 .rail{{display:flex;flex-wrap:wrap;align-items:center;gap:6px;margin:18px 0}}
 .chip{{display:flex;align-items:center;gap:6px;border:1px solid var(--edge);border-radius:10px;padding:6px 10px;background:var(--card);font-size:12px}}
 .chip .dot{{width:8px;height:8px;border-radius:50%;background:var(--dim)}}
 .chip.done .dot{{background:var(--emer)}} .chip.now{{border-color:var(--forest);box-shadow:0 0 0 3px rgba(23,108,52,.10)}}
 .chip.now .dot{{background:var(--forest);animation:pulse 1.4s infinite}}
 @keyframes pulse{{0%,100%{{box-shadow:0 0 0 0 rgba(23,108,52,.5)}}50%{{box-shadow:0 0 0 5px rgba(23,108,52,0)}}}}
 .conn{{width:16px;height:2px;background:var(--edge)}} .conn.done{{background:var(--emer)}}
 .phase{{border:1px solid var(--edge);border-left:3px solid hsl(var(--h) 55% 45%);border-radius:0 14px 14px 0;padding:14px 16px;margin-bottom:12px;background:var(--card)}}
 .phase.now{{box-shadow:0 2px 14px rgba(23,108,52,.08)}} .phase.waiting{{opacity:.6}}
 .phase h3{{margin:0 0 10px;font-size:14.5px;display:flex;align-items:center;gap:9px;font-weight:600}}
 .phase h3 .pn{{color:hsl(var(--h) 55% 38%);font-weight:800}}
 .pstate{{margin-left:auto;font-size:10px;text-transform:uppercase;letter-spacing:1px;color:var(--mut);border:1px solid var(--edge);border-radius:6px;padding:2px 7px}}
 .phase.now .pstate{{color:var(--forest);border-color:var(--forest)}}
 .agents{{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:9px}}
 .agent{{border:1px solid var(--edge);border-radius:11px;padding:10px 11px;background:#fbfdfc}}
 .agent.now{{border-color:hsl(var(--h) 55% 50%)}}
 .atop{{display:flex;align-items:center;gap:7px}}
 .badge{{width:19px;height:19px;border-radius:50%;display:inline-flex;align-items:center;justify-content:center;font-size:11px;background:hsl(var(--h) 50% 95%);color:hsl(var(--h) 45% 38%);border:1px solid hsl(var(--h) 40% 85%)}}
 .acouncil{{color:hsl(var(--h) 35% 45%);font-size:11px;font-weight:600}} .arole{{font-weight:700;font-size:12.5px}}
 .afind{{margin-top:7px;color:var(--ink);font-size:11.5px;border-left:2px solid var(--emer);padding-left:8px}}
 .atype{{margin-top:7px;color:var(--dim);font-size:10px;font-family:ui-monospace,SFMono-Regular,monospace}}
 .gaterow{{margin-top:11px;border:1px dashed var(--forest);border-radius:10px;padding:8px 11px;color:var(--forest);font-weight:700;font-size:12.5px}}
 .gaterow em{{float:right;font-style:normal;color:var(--mut);font-weight:600}}
 .gaterow.cleared{{border-style:solid;border-color:var(--emer);color:var(--emer)}} .gaterow.cleared em{{color:var(--emer)}}
 .activegate{{margin:16px 0;border:1px solid var(--forest);border-radius:16px;padding:18px;background:linear-gradient(135deg,#eafaf0,#ffffff)}}
 .ag-h{{color:var(--forest);font-weight:800;font-size:14px}} .ag-q{{margin-top:6px;font-size:16px;font-weight:600}}
 .ag-b{{margin-top:13px;display:flex;gap:9px}} .ag-b span{{padding:9px 18px;border-radius:10px;font-weight:800;font-size:12.5px}}
 .approve{{background:var(--forest);color:#fff}} .revise{{border:1px solid var(--mut);color:var(--ink)}} .reject{{border:1px solid #b65; color:#a14040}}
 .ag-hint{{margin-top:9px;color:var(--mut);font-size:11px}}
 .complete{{margin:14px 0;border:1px solid var(--emer);border-radius:14px;padding:14px 16px;background:linear-gradient(135deg,#eafaf0,#ffffff);color:var(--emer);font-weight:700;font-size:13.5px}}
 .feed{{margin:16px 0;border:1px solid var(--edge);border-radius:14px;padding:14px 16px;background:var(--card)}}
 .feed h4{{margin:0 0 9px;font-size:12px;text-transform:uppercase;letter-spacing:1px;color:var(--mut)}}
 .feed ul{{margin:0;padding:0;list-style:none;display:flex;flex-direction:column;gap:7px}}
 .feed li{{font-size:12.5px;color:var(--ink);line-height:1.5;border-left:2px solid var(--emer);padding-left:9px}}
 .feed .fc{{font-weight:700;color:var(--forest)}}
 footer{{margin-top:18px;color:var(--dim);font-size:11px;text-align:center}}
</style></head><body><div class="wrap">
 <div class="hero">
   <div class="brand"><span class="hex">⬢</span> CAMBIUM INSTITUTE <span class="tag">· the Cambium way</span></div>
   <div class="req">{req}</div>
   <div class="meta">{n_ag} specialists · {n_co} councils · {n_gt} human gate(s) · {done}/{total} phases complete</div>
   <div class="prog"><span></span></div>
   <div class="pl"><span>▸ {nowline}</span><span>{pct}%</span></div>
 </div>
 {complete}
 <div class="rail">{rail}</div>
 {gatecard}
 {cards}
 {feed}
 <footer>Cambium run board · ✓ done · ▶ now · ○ waiting · ⛩ human gate — nothing finalizes without your APPROVE.</footer>
</div></body></html>"""

def main(argv=None):
    ap = argparse.ArgumentParser()
    # Defaults use data_home() so writes go to the writable location even in a read-only plugin install.
    # In the dev/repo/test case data_home() == ROOT, so behavior is unchanged.
    ap.add_argument("--state", default=os.path.join(cambium_io.data_home(), "agent_outputs", "run_state.json"))
    ap.add_argument("--out", default=os.path.join(cambium_io.data_home(), "agent_outputs", "run_board.html"))
    ap.add_argument("--title", default="")
    a = ap.parse_args(argv)
    if not os.path.exists(a.state):
        print("[gen_board_pro] no run state at %s" % a.state); return 1
    # Resolve relative --out against data_home(), not ROOT, so plugin writes stay writable.
    out = a.out if os.path.isabs(a.out) else os.path.join(cambium_io.data_home(), a.out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, "w", encoding="utf-8").write(render(a.state, a.title))
    try:
        shown = os.path.relpath(out, ROOT)
    except ValueError:   # out and ROOT on different drives (Windows): show the absolute path
        shown = out
    print("[gen_board_pro] wrote %s" % shown)
    return 0

if __name__ == "__main__":
    sys.exit(main())
