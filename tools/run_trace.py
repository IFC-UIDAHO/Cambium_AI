#!/usr/bin/env python3
"""run_trace — show Cambium's workflow AND its live progress, in whatever form the reader can see.

Reuses tools/task_router.py. One spine (the routed phase plan) rendered four ways, plus a LIVE board
that advances by *phase* so the Director always sees done · now · waiting and the next gate.

Static / live views:
  --text             flat checklist (works in ANY chat)            [legacy, kept for compatibility]
  (default)          Mermaid flowchart (GitHub / Claude Code)
  --svg              SVG picture of the whole plan (visual chats / Cowork)
  --status N [note]  LIVE SVG board: step N is "now working" (flat-step cursor)  [legacy]

The legendary layer (use these for the Cambium way):
  --board                    rich TEXT board: branded header + council-grouped roster + gate rail
  --board --phase N [note]   LIVE text board: phase N is running, earlier done, later waiting
  --html  [--phase N]        self-contained LIVE HTML dashboard (Cowork artifact / browser)
                             writes to agent_outputs/run_board.html under data_home() unless --out PATH
  --state state.json         overlay live detail onto any board/html: per-agent findings + leaderboard

Usage:
  python3 tools/run_trace.py --board "add useful skills to Cambium"
  python3 tools/run_trace.py --board --phase 2 "add useful skills to Cambium"
  python3 tools/run_trace.py --html  --phase 2 --state run.json "add useful skills to Cambium"
"""
import sys, os, json, html

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import task_router
import cambium_io  # reconfigures stdout/stderr to UTF-8 on Windows; provides data_home()

# ---- Cambium brand palette (the deep-forest + Cambium-lime system) ----
BG     = "#07231A"   # deep forest
PANEL  = "#0E3326"   # raised panel
PANEL2 = "#0A271D"   # recessed panel
EDGE   = "#1F4D3B"   # hairline border
LIME   = "#B7F36A"   # Cambium lime -- primary accent / "now"
EMER   = "#16C079"   # emerald -- flow / done
INK    = "#F4F7F2"   # primary text
MUTE   = "#8AA197"   # secondary text
DIM    = "#5E7468"   # waiting text


def _short(s, n=46):
    s = " ".join(str(s).split())
    return s if len(s) <= n else s[:n - 1] + "…"


def _esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ---- ordered councils (the spine every view shares) ----
COUNCIL = {"orch": "Orchestration", "preaward": "Pre-Award", "partner": "Partnerships",
           "faculty": "Faculty", "scout": "Scouts", "lab": "Labs", "verify": "Verification",
           "exec": "Execution", "reporting": "Reporting", "support": "Support", "gov": "Governance"}
_A2C = {a: c for c, ags in task_router.CMAP.items() for a in ags}
_ORDER = list(COUNCIL)
GATE_IDS = ("G0", "G1", "G2", "G3", "G3a", "G4", "G5", "G6")


def _council_of(agents):
    from collections import Counter
    cnt = Counter(_A2C.get(a, "orch") for a in agents)
    return max(cnt, key=lambda c: (cnt[c], -_ORDER.index(c)))


def pretty(agent):
    """agent id -> ("Council", "Role") for human-facing labels, e.g. scout-landscape -> Scouts, Landscape."""
    council = COUNCIL.get(_A2C.get(agent, "orch"), "Orchestration")
    role = agent
    for p in ("scout-", "lab-", "verify-", "exec-"):
        if role.startswith(p):
            role = role[len(p):]
            break
    return council, role.replace("-", " ").title()


def subagent_type(agent):
    """The dispatchable Task-tool subagent_type for a roster agent."""
    return "cambium-institute:" + agent


# ---- flatten the routed plan into a single ordered list of steps (legacy spine) ----
def steps(task):
    r = task_router.route(task)
    raw = [{"kind": "you", "label": "You ask, in plain words", "who": ""},
           {"kind": "work", "label": "Orchestration", "who": "routes your request"}]
    for p in r["phases"]:
        for g in p["groups"]:
            raw.append({"kind": "work", "label": COUNCIL[_council_of(g["agents"])], "who": ", ".join(g["agents"])})
        if p.get("gate"):
            gid = p["gate"]["id"]
            _kw = "GATE" if gid in GATE_IDS else "Checkpoint"
            raw.append({"kind": "gate", "label": f'{_kw} {gid} · {p["gate"].get("decision", "your decision")}', "who": ""})
    raw.append({"kind": "you", "label": "Delivered", "who": ""})
    S = []
    for st in raw:
        if S and st["kind"] == "work" and S[-1]["kind"] == "work" and S[-1]["label"] == st["label"]:
            S[-1]["who"] = ", ".join(x for x in (S[-1]["who"] + ", " + st["who"]).split(", ") if x)
        else:
            S.append(dict(st))
    return r, S


# ---- phase-level model (the spine the legendary board/html share) ----
def phases(task):
    """Ordered list of phase dicts: {n, council, label, agents:[(council,role,id)], gate:{id,decision} | None}."""
    r = task_router.route(task)
    out = []
    for i, p in enumerate(r["phases"], 1):
        agents = []
        for g in p["groups"]:
            for a in g["agents"]:
                if a == "orchestrator":
                    continue
                c, role = pretty(a)
                agents.append((c, role, a))
        # de-dup, keep order
        seen, uniq = set(), []
        for a in agents:
            if a[2] not in seen:
                seen.add(a[2]); uniq.append(a)
        lead = COUNCIL[_council_of([a[2] for a in uniq])] if uniq else "Orchestration"
        gate = None
        if p.get("gate"):
            gid = p["gate"]["id"]
            gate = {"id": gid, "decision": p["gate"].get("decision", "your decision"),
                    "kind": "GATE" if gid in GATE_IDS else "Checkpoint"}
        out.append({"n": i, "council": lead, "label": p["id"].replace("_", " ").title(),
                    "agents": uniq, "gate": gate})
    return r, out


def _resolve_plan(task, state):
    """Use a CUSTOM plan from run_state.json if present, so the board shows the REAL dispatched roster
    (not the generic routed plan). Schema:
      "plan": {"type":"cambium","phases":[
        {"council":"Faculty","label":"Council","gate":{"id":"G-x","decision":"...?"},
         "agents":[["Faculty","Principal Investigator","principal-investigator"], ...]}]}
    Falls back to the routed plan when no custom plan is given."""
    state = state or {}
    plan = state.get("plan")
    if isinstance(plan, dict) and plan.get("phases"):
        P = []
        for i, ph in enumerate(plan["phases"], 1):
            agents = []
            for a in ph.get("agents", []):
                if isinstance(a, (list, tuple)):
                    agents.append((a[0], a[1], a[2] if len(a) > 2 else a[1]))
                elif isinstance(a, dict):
                    agents.append((a.get("council", ""), a.get("role", ""), a.get("id", a.get("role", ""))))
            g = ph.get("gate")
            if isinstance(g, dict):
                gid = g.get("id", "")
                g = {"id": gid, "decision": g.get("decision", "your decision"),
                     "kind": g.get("kind", "GATE" if gid in GATE_IDS else "Checkpoint")}
            else:
                g = None
            P.append({"n": i, "council": ph.get("council") or (agents[0][0] if agents else "Orchestration"),
                      "label": ph.get("label", ""), "agents": agents, "gate": g})
        return {"type": plan.get("type", "cambium")}, P
    return phases(task)


# =========================================================================
#  LEGENDARY TEXT BOARD  (--board [--phase N])
# =========================================================================
def board_text(task, cur_phase=None, note=None, state=None):
    state = state or {}
    findings = state.get("findings", {})
    r, P = _resolve_plan(task, state)
    n_council = len({a[0] for ph in P for a in ph["agents"]})
    n_agents = sum(len(ph["agents"]) for ph in P)
    n_gates = sum(1 for ph in P if ph["gate"])
    W = 66

    def rule(ch="─"):
        return "  " + ch * W

    def boxline(text, pad=W):
        return "  ║ " + text.ljust(pad - 2) + "║"

    live = cur_phase is not None
    out = []
    # Left-bar header: alignment-proof regardless of how the client renders emoji width.
    out.append("  ┌─ ⬢ CAMBIUM INSTITUTE  ·  running the Cambium way")
    out.append("  │  Request:  " + _short(task, W))
    out.append(f"  │  Plan:     {r['type']} workflow · {n_agents} specialists · {n_council} councils · {n_gates} human gate(s)")
    out.append("  └" + "─" * (W + 2))
    out.append("")

    for ph in P:
        if not live:
            mark, tag = "·", ""
        elif ph["n"] < cur_phase:
            mark, tag = "✓", "done"
        elif ph["n"] == cur_phase:
            mark, tag = "▶", "now"
        else:
            mark, tag = "○", "waiting"
        sub = ph["label"]
        title = f"{ph['council'].upper()}" + (f" · {sub}" if sub and sub.lower() not in ph["council"].lower() else "")
        head = f"  {mark} PHASE {ph['n']} · {title}"
        if tag:
            head = head.ljust(48)
            head += ("  " if not head.endswith(" ") else "") + ("▶ now" if tag == "now" else "✓ done" if tag == "done" else "○ waiting")
        out.append(head)
        for (c, role, aid) in ph["agents"]:
            am = "▶" if tag == "now" else "✓" if tag == "done" else "○" if tag == "waiting" else "·"
            line = f"      {am} {c} · {role}"
            f = findings.get(aid)
            if f:
                line = line.ljust(34)
                line += ("  " if not line.endswith(" ") else "") + _short(f, 40)
            out.append(line)
        if ph["gate"]:
            g = ph["gate"]
            gm = "⛩"
            gl = f"     {gm} {g['kind']} {g['id']} — {_short(g['decision'], 44)}   (APPROVE / REVISE / REJECT)"
            out.append(rule())
            out.append(gl)
        out.append("")

    # council strip
    strip = []
    for c in ["Orchestration", "Scouts", "Labs", "Execution", "Verification", "Support", "Governance"]:
        present = any(a[0] == c for ph in P for a in ph["agents"]) or c == "Orchestration"
        if not present:
            continue
        if not live:
            s = "·"
        else:
            phs = [ph["n"] for ph in P if any(a[0] == c for a in ph["agents"])]
            if c == "Orchestration":
                s = "✓"
            elif not phs:
                s = "·"
            elif cur_phase > max(phs):
                s = "✓"
            elif cur_phase < min(phs):
                s = "○"
            else:
                s = "▶"
        strip.append(f"{c} {s}")
    out.append("  Councils:  " + "  ·  ".join(strip))

    if live and 1 <= cur_phase <= len(P):
        cp = P[cur_phase - 1]
        who = ", ".join(f"{c}·{role}" for (c, role, _) in cp["agents"]) or "Orchestration"
        banner = f"  ▸ NOW: Phase {cp['n']} {cp['council']} — working with {_short(who, 50)}"
        if note:
            banner += f"  ({note})"
        out.append("")
        out.append(banner)
        if cp["gate"]:
            out.append(f"  ⛩ Next stop: {cp['gate']['kind']} {cp['gate']['id']} — your decision.")

    # leaderboard (if supplied)
    lb = state.get("leaderboard")
    if lb:
        out.append("")
        out.append("  Leaderboard (top findings by confidence):")
        for name, score in lb[:5]:
            c, role = pretty(name)
            out.append(f"      {str(score).rjust(3)}  {c} · {role}")

    return "\n".join(out)


# =========================================================================
#  Mermaid (standardized spine)
# =========================================================================
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


# =========================================================================
#  SVG (plan when cur=None; live status board when cur set) -- legacy flat spine
# =========================================================================
def _svg(task, cur=None, note=None):
    r, S = steps(task)
    W, top, step = 740, 96, 58
    cys = [top + i * step + 18 for i in range(len(S))]
    H = cys[-1] + 36
    P = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Cambium workflow status" font-family="Inter,system-ui,sans-serif">',
         f'<defs><marker id="ar" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0 L10 5 L0 10 z" fill="{EMER}"/></marker></defs>',
         f'<rect x="0" y="0" width="{W}" height="{H}" rx="16" fill="{BG}" stroke="{EDGE}"/>',
         f'<text x="30" y="40" fill="{INK}" font-size="18" font-weight="700">Cambium — {"live progress" if cur is not None else "what runs for your request"}</text>',
         f'<text x="30" y="60" fill="{MUTE}" font-size="12">{_esc(_short(task, 72))}</text>']
    if cur is not None and 0 <= cur < len(S):
        c = S[cur]
        msg = (f"▶ NOW: {c['label']} — {_short(c['who'], 46)}" if c["kind"] == "work" else "\U0001f6a6 Waiting for your decision")
        if note:
            msg += f" · {note}"
        P.append(f'<rect x="30" y="70" width="{W-60}" height="20" rx="6" fill="#103a2b"/>'
                 f'<text x="40" y="84" fill="{LIME}" font-size="12" font-weight="700">{_esc(_short(msg, 86))}</text>')
        for i in range(len(cys)):
            cys[i] += 14
        H2 = cys[-1] + 36
        P[2] = f'<rect x="0" y="0" width="{W}" height="{H2}" rx="16" fill="{BG}" stroke="{EDGE}"/>'
        P[0] = f'<svg viewBox="0 0 {W} {H2}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Cambium live progress" font-family="Inter,system-ui,sans-serif">'
    for i in range(len(S) - 1):
        P.append(f'<line x1="370" y1="{cys[i]+17}" x2="370" y2="{cys[i+1]-17}" stroke="{EMER}" stroke-width="2" marker-end="url(#ar)"/>')
    for i, (s, cy) in enumerate(zip(S, cys)):
        if cur is None:
            state = "plan"
        elif i < cur:
            state = "done"
        elif i == cur:
            state = "now"
        else:
            state = "todo"
        if s["kind"] == "you":
            fill = LIME if state in ("plan", "done", "now") else "#2c4a39"
            P.append(f'<rect x="260" y="{cy-15}" width="220" height="30" rx="15" fill="{fill}"/>'
                     f'<text x="370" y="{cy+5}" text-anchor="middle" fill="#052015" font-size="13" font-weight="700">{_esc(s["label"])}</text>')
            continue
        if s["kind"] == "gate":
            stroke = LIME if state in ("plan", "now", "done") else "#3a5a48"
            P.append(f'<polygon points="370,{cy-21} 530,{cy} 370,{cy+21} 210,{cy}" fill="#15402F" stroke="{stroke}" stroke-width="{3 if state=="now" else 1.6}"/>'
                     f'<text x="370" y="{cy+5}" text-anchor="middle" fill="{LIME if state!="todo" else "#5E7468"}" font-size="12" font-weight="700">{_esc(_short(s["label"], 30))}</text>')
            continue
        fills = {"plan": PANEL, "done": PANEL, "now": "#0f3f2d", "todo": PANEL2}
        strokes = {"plan": EMER, "done": "#2A5A45", "now": LIME, "todo": EDGE}
        txt = {"plan": INK, "done": "#86998F", "now": INK, "todo": DIM}
        pre = {"plan": "", "done": "✓ ", "now": "▶ ", "todo": "○ "}[state]
        sw = 3 if state == "now" else 1.4
        P.append(f'<rect x="180" y="{cy-19}" width="380" height="40" rx="9" fill="{fills[state]}" stroke="{strokes[state]}" stroke-width="{sw}"/>')
        who = _short(s["who"], 52)
        P.append(f'<text x="370" y="{cy-2}" text-anchor="middle" fill="{txt[state]}" font-size="13" font-weight="600">{_esc(pre + s["label"])}</text>')
        if who:
            P.append(f'<text x="370" y="{cy+13}" text-anchor="middle" fill="{LIME if state=="now" else "#8AA197" if state!="todo" else "#4d6358"}" font-size="10">{_esc(who)}</text>')
    P.append('</svg>')
    return "\n".join(P)


# ---- legacy flat-text checklist ----
def text(task, cur=None, note=None):
    r, S = steps(task)
    head = f"Cambium plan for: {task}  ({r['type']}, {r['n_agents']} helpers)"
    out = [head, ""]
    for i, s in enumerate(S):
        if s["kind"] == "you":
            continue
        if cur is None:
            mark = "·"
        elif i < cur:
            mark = "✓"
        elif i == cur:
            mark = "▶"
        else:
            mark = "○"
        line = f"  {mark} {s['label']}" + (f" — {_short(s['who'], 60)}" if s["who"] else "")
        if s["kind"] == "gate":
            line += "   (you APPROVE / REVISE / REJECT)"
        out.append(line)
    if cur is not None and 0 <= cur < len(S):
        c = S[cur]
        banner = (f"\n>> NOW: {c['label']} — {_short(c['who'], 60)}" if c["kind"] == "work" else f"\n>> WAITING FOR YOU: {c['label']}")
        if note:
            banner += f"  ({note})"
        out.append(banner)
    return "\n".join(out)


def svg(task):
    return _svg(task, None)


def status(task, cur, note=None):
    return _svg(task, cur, note)


# =========================================================================
#  LIVE HTML DASHBOARD  (--html [--phase N] [--state s.json])
# =========================================================================
def dashboard_html(task, cur_phase=None, note=None, state=None, light=False):
    state = state or {}
    findings = state.get("findings", {})
    lb = state.get("leaderboard", [])
    gate_override = state.get("gate")
    r, P = _resolve_plan(task, state)
    n_agents = sum(len(ph["agents"]) for ph in P)
    n_council = len({a[0] for ph in P for a in ph["agents"]})
    n_gates = sum(1 for ph in P if ph["gate"])
    live = cur_phase is not None
    bodycls = "light" if light else ""
    LIGHTCSS = "body.light{background:#ffffff;color:#10241c}body.light .hero .brand,body.light .hero .req{color:#eafff2}body.light .hero .meta{color:#9fe7c1}body.light .phase,body.light .panel{background:#f6faf7;border-color:#dfe7e2}body.light .agent,body.light .rail-step{background:#eef4f0;border-color:#dfe7e2}body.light .arole{color:#10241c}body.light .acouncil,body.light .pstate,body.light .panel h4,body.light .rl span,body.light .gatebar em{color:#5b6f66}body.light .pn,body.light .rail-gate,body.light .gatebar,body.light .ag-h{color:#176c34}body.light .rail-gate,body.light .gatebar{border-color:#176c34}body.light .afind{border-left-color:#0f8a4f;color:#10241c}body.light .badge{background:#e7f1ea;color:#5b6f66;border-color:#dfe7e2}body.light .agent.now .badge{color:#176c34;border-color:#176c34}body.light .agent.done .badge{color:#0f8a4f;border-color:#0f8a4f}body.light .atype{color:#9aa9a1}body.light table.lb .sc{color:#176c34}body.light .activegate{background:#eafaf0;border-color:#176c34}body.light .ag-q{color:#10241c}body.light .approve{background:#176c34;color:#ffffff}body.light .pstate{border-color:#dfe7e2}body.light footer{color:#9aa9a1}body.light .phase.now,body.light .agent.now{border-color:#176c34;box-shadow:none}body.light .phase.todo{opacity:.72}" if light else ""

    def st(n):
        if not live:
            return "plan"
        return "done" if n < cur_phase else "now" if n == cur_phase else "todo"

    rail = []
    for ph in P:
        s = st(ph["n"])
        rail.append(
            f'<div class="rail-step {s}"><div class="dot"></div>'
            f'<div class="rl"><b>Phase {ph["n"]}</b><span>{html.escape(ph["council"])}</span></div></div>')
        if ph["gate"]:
            gs = "done" if (live and cur_phase > ph["n"]) else "now" if (live and cur_phase == ph["n"]) else "plan" if not live else "todo"
            rail.append(f'<div class="rail-gate {gs}" title="{html.escape(ph["gate"]["decision"])}">⛩ {html.escape(ph["gate"]["id"])}</div>')

    cards = []
    for ph in P:
        s = st(ph["n"])
        chips = []
        for (c, role, aid) in ph["agents"]:
            f = findings.get(aid, "")
            badge = {"done": "✓", "now": "▶", "todo": "○", "plan": ""}[s]
            chips.append(
                f'<div class="agent {s}"><div class="atop"><span class="badge">{badge}</span>'
                f'<span class="acouncil">{html.escape(c)}</span><span class="arole">{html.escape(role)}</span></div>'
                + (f'<div class="afind">{html.escape(_short(f, 80))}</div>' if f else '')
                + f'<div class="atype">cambium-institute:{html.escape(aid)}</div></div>')
        gate_html = ""
        if ph["gate"]:
            gate_html = f'<div class="gatebar">⛩ {html.escape(ph["gate"]["kind"])} {html.escape(ph["gate"]["id"])} — {html.escape(ph["gate"]["decision"])} <em>APPROVE / REVISE / REJECT</em></div>'
        cards.append(
            f'<section class="phase {s}"><h3><span class="pn">Phase {ph["n"]}</span> {html.escape(ph["council"])} '
            f'<span class="pstate">{s}</span></h3><div class="agents">{"".join(chips)}</div>{gate_html}</section>')

    lb_html = ""
    if lb:
        rows = ""
        for name, score in lb[:6]:
            c, role = pretty(name)
            rows += f'<tr><td class="sc">{html.escape(str(score))}</td><td>{html.escape(c)} · {html.escape(role)}</td></tr>'
        lb_html = f'<div class="panel"><h4>Leaderboard</h4><table class="lb">{rows}</table></div>'

    gate_banner = ""
    if live and gate_override:
        gate_banner = (
            f'<div class="activegate"><div class="ag-h">⛩ {html.escape(gate_override.get("kind","GATE"))} '
            f'{html.escape(gate_override.get("id",""))} — your decision</div>'
            f'<div class="ag-q">{html.escape(gate_override.get("decision",""))}</div>'
            + (f'<div class="ag-r">Recommendation: <b>{html.escape(str(gate_override.get("recommendation","")))}</b></div>' if gate_override.get("recommendation") else "")
            + '<div class="ag-b">'
            '<button class="approve" onclick="cwGate(\'APPROVE\')">APPROVE</button>'
            '<button class="revise" onclick="cwGate(\'REVISE\')">REVISE</button>'
            '<button class="reject" onclick="cwGate(\'REJECT\')">REJECT</button></div>'
            '<div class="ag-hint">Click to copy your decision, then paste it in chat.</div></div>')

    now_line = ""
    if live and 1 <= cur_phase <= len(P):
        cp = P[cur_phase - 1]
        who = ", ".join(f"{c}·{role}" for (c, role, _) in cp["agents"]) or "Orchestration"
        now_line = f'▸ NOW: Phase {cp["n"]} {html.escape(cp["council"])} — working with {html.escape(_short(who, 70))}' + (f' · {html.escape(note)}' if note else "")

    payload = json.dumps({"task": task, "type": r["type"], "phase": cur_phase}, ensure_ascii=False)
    gate_js = json.dumps((gate_override or {}).get("id", ""))

    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Cambium — run board</title>
<style>
 :root{{--bg:{BG};--panel:{PANEL};--panel2:{PANEL2};--edge:{EDGE};--lime:{LIME};--emer:{EMER};--ink:{INK};--mute:{MUTE};--dim:{DIM};}}
 *{{box-sizing:border-box}}
 body{{margin:0;background:var(--bg);color:var(--ink);font:14px/1.5 Inter,system-ui,Segoe UI,sans-serif;}}
 .wrap{{max-width:1080px;margin:0 auto;padding:22px;}}
 .hero{{border:1px solid var(--edge);border-radius:16px;padding:18px 20px;background:linear-gradient(135deg,#0a2a1f,#07231a);}}
 .hero .brand{{display:flex;align-items:center;gap:10px;font-weight:800;font-size:18px;letter-spacing:.3px}}
 .hero .brand .hex{{color:var(--lime);font-size:22px}}
 .hero .req{{margin-top:6px;color:var(--ink);font-size:15px}}
 .hero .meta{{margin-top:4px;color:var(--mute);font-size:12.5px}}
 .nowline{{margin-top:12px;color:var(--lime);font-weight:700;font-size:13px}}
 .rail{{display:flex;flex-wrap:wrap;align-items:center;gap:8px;margin:18px 0}}
 .rail-step{{display:flex;align-items:center;gap:7px;border:1px solid var(--edge);border-radius:10px;padding:7px 11px;background:var(--panel2)}}
 .rail-step .dot{{width:9px;height:9px;border-radius:50%;background:var(--dim)}}
 .rail-step.done .dot{{background:var(--emer)}} .rail-step.now .dot{{background:var(--lime);box-shadow:0 0 0 4px rgba(183,243,106,.18)}}
 .rail-step.now{{border-color:var(--lime)}} .rail-step.done{{border-color:#2a5a45}}
 .rl b{{font-size:12px}} .rl span{{display:block;color:var(--mute);font-size:10.5px}}
 .rail-gate{{color:var(--lime);border:1px dashed var(--lime);border-radius:10px;padding:7px 9px;font-weight:700;font-size:12px;opacity:.55}}
 .rail-gate.now{{opacity:1;box-shadow:0 0 0 3px rgba(183,243,106,.12)}} .rail-gate.done{{opacity:.4}}
 .grid{{display:grid;grid-template-columns:1fr;gap:14px}}
 .cols{{display:grid;grid-template-columns:2fr 1fr;gap:14px;align-items:start}}
 @media(max-width:760px){{.cols{{grid-template-columns:1fr}}}}
 .phase{{border:1px solid var(--edge);border-radius:14px;padding:14px;background:var(--panel)}}
 .phase.now{{border-color:var(--lime);box-shadow:0 0 0 1px rgba(183,243,106,.25)}}
 .phase.todo{{opacity:.62}} .phase.done{{opacity:.82}}
 .phase h3{{margin:0 0 10px;font-size:14.5px;display:flex;align-items:center;gap:9px}}
 .phase h3 .pn{{color:var(--lime);font-weight:800}}
 .pstate{{margin-left:auto;font-size:10px;text-transform:uppercase;letter-spacing:1px;color:var(--mute);border:1px solid var(--edge);border-radius:6px;padding:2px 7px}}
 .phase.now .pstate{{color:var(--lime);border-color:var(--lime)}}
 .agents{{display:grid;grid-template-columns:repeat(auto-fill,minmax(190px,1fr));gap:9px}}
 .agent{{border:1px solid var(--edge);border-radius:10px;padding:9px 10px;background:var(--panel2)}}
 .agent.now{{border-color:var(--lime)}} .agent.done{{border-color:#2a5a45}}
 .atop{{display:flex;align-items:center;gap:7px}}
 .badge{{width:18px;height:18px;border-radius:50%;display:inline-flex;align-items:center;justify-content:center;font-size:11px;background:#0c2c20;color:var(--mute);border:1px solid var(--edge)}}
 .agent.now .badge{{color:var(--lime);border-color:var(--lime)}} .agent.done .badge{{color:var(--emer);border-color:var(--emer)}}
 .acouncil{{color:var(--mute);font-size:11px}} .arole{{font-weight:700;font-size:12.5px}}
 .afind{{margin-top:6px;color:var(--ink);font-size:11.5px;border-left:2px solid var(--emer);padding-left:7px}}
 .atype{{margin-top:6px;color:var(--dim);font-size:10px;font-family:ui-monospace,monospace}}
 .gatebar{{margin-top:11px;border:1px dashed var(--lime);border-radius:10px;padding:9px 11px;color:var(--lime);font-weight:700;font-size:12.5px}}
 .gatebar em{{float:right;font-style:normal;color:var(--mute);font-weight:600}}
 .panel{{border:1px solid var(--edge);border-radius:14px;padding:14px;background:var(--panel)}}
 .panel h4{{margin:0 0 9px;font-size:12px;text-transform:uppercase;letter-spacing:1px;color:var(--mute)}}
 table.lb{{width:100%;border-collapse:collapse;font-size:12.5px}}
 table.lb td{{padding:5px 4px;border-bottom:1px solid var(--edge)}} table.lb .sc{{color:var(--lime);font-weight:800;width:34px}}
 .activegate{{margin-top:14px;border:1px solid var(--lime);border-radius:14px;padding:16px;background:linear-gradient(135deg,#15402f,#0e3326)}}
 .ag-h{{color:var(--lime);font-weight:800;font-size:14px}} .ag-q{{margin-top:5px;font-size:14px}}
 .ag-r{{margin-top:5px;color:var(--mute);font-size:12.5px}}
 .ag-b{{margin-top:11px;display:flex;gap:9px}}
 .ag-b span{{padding:7px 14px;border-radius:9px;font-weight:800;font-size:12px}}
 .ag-b button{{cursor:pointer;font-family:inherit;border:none;padding:8px 16px;border-radius:9px;font-weight:800;font-size:12px}}
 .ag-hint{{margin-top:8px;color:var(--mute);font-size:11px}}
 .approve{{background:var(--lime);color:#052015}} .revise{{border:1px solid var(--mute);color:var(--ink)}} .reject{{border:1px solid #6b2b2b;color:#e9a4a4}}
 footer{{margin-top:16px;color:var(--dim);font-size:11px;text-align:center}}
{LIGHTCSS}</style></head>
<body class="{bodycls}"><div class="wrap">
 <div class="hero">
   <div class="brand"><span class="hex">⬢</span> CAMBIUM INSTITUTE <span style="color:var(--mute);font-weight:600;font-size:12px">· the Cambium way</span></div>
   <div class="req">{html.escape(task)}</div>
   <div class="meta">{html.escape(r['type'])} workflow · {n_agents} specialists · {n_council} councils · {n_gates} human gate(s)</div>
   {f'<div class="nowline">{now_line}</div>' if now_line else ''}
 </div>
 <div class="rail">{''.join(rail)}</div>
 <div class="cols">
   <div class="grid">{''.join(cards)}</div>
   <div class="grid">{lb_html}{gate_banner}</div>
 </div>
 <footer>Cambium run board · ✓ done · ▶ now · ○ waiting · ⛩ human gate — nothing finalizes without your APPROVE.</footer>
</div>
<script>window.__CAMBIUM_RUN__={payload};var CAMBIUM_GATE={gate_js};
function cwGate(d){{var m=d+' '+(CAMBIUM_GATE||'this gate');var b=document.getElementById('cw-echo');if(!b){{b=document.createElement('div');b.id='cw-echo';b.style.cssText='margin-top:10px;padding:10px 12px;border:1px solid #176c34;border-radius:10px;background:#eafaf0;color:#10241c;font-weight:600';var p=document.querySelector('.activegate');if(p){{p.appendChild(b);}}}}b.textContent='--> type this in chat to decide: '+m;try{{navigator.clipboard.writeText(m);b.textContent='copied — paste in chat to decide: '+m;}}catch(e){{}}if(window.sendPrompt){{sendPrompt(m);}}}}</script>
</body></html>"""


# =========================================================================
#  CLI
# =========================================================================
def _take_flag_val(a, flag):
    if flag in a:
        i = a.index(flag)
        if i + 1 < len(a):
            return a[i + 1]
    return None


def main():
    a = sys.argv[1:]

    state = None
    sp = _take_flag_val(a, "--state")
    if not sp:
        # auto-discover the live run state so --board/--html pick up findings without --state
        cand = os.path.join("agent_outputs", "run_state.json")
        if os.path.exists(cand):
            sp = cand
    if sp and os.path.exists(sp):
        with open(sp, encoding="utf-8") as fh:
            state = json.load(fh)

    phase = None
    pv = _take_flag_val(a, "--phase")
    if pv is not None:
        try:
            phase = int(pv)
        except ValueError:
            phase = None
    if phase is None and state and "phase" in state:
        phase = state["phase"]
    note = (state or {}).get("note")

    consumed = {"--state", sp, "--phase", pv, "--out", _take_flag_val(a, "--out"),
                "--status", "--board", "--html", "--svg", "--text", "--light"}
    task = " ".join(x for j, x in enumerate(a)
                    if not x.startswith("--") and x not in consumed) or "do a research task"

    if "--status" in a:
        i = a.index("--status"); cur = int(a[i + 1])
        print(status(task, cur, note)); return

    if "--board" in a:
        print(board_text(task, phase, note, state)); return

    if "--html" in a:
        # Default write location is under data_home(), not the (potentially read-only) tools dir.
        out = _take_flag_val(a, "--out") or os.path.join(
            cambium_io.data_home(), "agent_outputs", "run_board.html")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, "w", encoding="utf-8") as fh:
            fh.write(dashboard_html(task, phase, note, state, light=("--light" in a)))
        print(out); return
    mode = "svg" if "--svg" in a else "text" if "--text" in a else "mermaid"
    print({"text": lambda t: text(t, phase, note), "svg": svg, "mermaid": mermaid}[mode](task))


if __name__ == "__main__":
    main()
