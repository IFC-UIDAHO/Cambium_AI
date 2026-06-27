#!/usr/bin/env python3
"""Render the Cambium run board as a PNG + animated GIF (no browser needed; pure PIL).

Mirrors the live HTML dashboard (deep-forest + Cambium-lime) so the README can show the legendary
"Cambium way" experience. Data comes from tools/run_trace.phases() so the picture never drifts.

Usage: python3 tools/gen_board_image.py            # writes assets/run_board.png + assets/run_board.gif
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run_trace
from PIL import Image, ImageDraw, ImageFont
import imageio.v2 as imageio

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")

# palette (RGB) — matches run_trace
BG=(7,35,26); PANEL=(14,51,38); PANEL2=(10,39,29); EDGE=(31,77,59)
LIME=(183,243,106); EMER=(22,192,121); INK=(244,247,242); MUTE=(138,161,151); DIM=(94,116,104)
GATEBG=(21,64,47)

FB = "/usr/share/fonts/truetype/dejavu/"
def F(sz, bold=True):
    try:
        return ImageFont.truetype(FB + ("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"), sz)
    except Exception:
        return ImageFont.load_default()

W, H = 1060, 624
TASK = "add useful skills to Cambium for math, stats, ML"

FINDINGS = {
    "scout-prior-art":  "math = full gap; stats/ML = partial",
    "scout-methods":    "SymPy / SciPy / sklearn are standard",
    "scout-landscape":  "8 markets; half the wishlist installed",
    "lab-theory":       "exact-math + defensible-stats end",
    "lab-statistics":   "power, CIs, multiplicity built in",
}
LEADER = [("scout-landscape", 92), ("scout-methods", 88), ("verify-rigor", 85), ("scout-prior-art", 80)]


def hexagon(d, cx, cy, r, outline, width=3, fill=None):
    import math
    pts = [(cx + r*math.cos(math.radians(60*i-90)), cy + r*math.sin(math.radians(60*i-90))) for i in range(6)]
    d.polygon(pts, outline=outline, width=width, fill=fill)


def marker(d, x, y, state, r=8):
    """done=filled check · now=lime ring+dot · todo/plan=gray ring."""
    if state == "done":
        d.ellipse([x-r, y-r, x+r, y+r], fill=EMER)
        d.line([(x-4, y), (x-1, y+3), (x+5, y-4)], fill=BG, width=2)
    elif state == "now":
        d.ellipse([x-r, y-r, x+r, y+r], outline=LIME, width=2)
        d.ellipse([x-3, y-3, x+3, y+3], fill=LIME)
    else:
        d.ellipse([x-r, y-r, x+r, y+r], outline=DIM if state != "plan" else MUTE, width=2)


def diamond(d, cx, cy, r, active):
    col = LIME if active else (DIM)
    d.polygon([(cx, cy-r), (cx+r, cy), (cx, cy+r), (cx-r, cy)], outline=col, width=2)


def render(cur_phase, show_findings, gate_active, caption):
    r, P = run_trace.phases(TASK)
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    M = 30

    def state_of(n):
        if cur_phase is None:
            return "plan"
        return "done" if n < cur_phase else "now" if n == cur_phase else "todo"

    # ---- header ----
    d.rounded_rectangle([M, M, W-M, M+96], radius=16, fill=(10,42,31), outline=EDGE, width=1)
    hexagon(d, M+34, M+34, 16, LIME, width=3)
    hexagon(d, M+34, M+34, 7, LIME, width=2)
    d.text((M+62, M+18), "CAMBIUM INSTITUTE", font=F(22), fill=INK)
    d.text((M+322, M+24), "· the Cambium way", font=F(14, False), fill=MUTE)
    d.text((M+62, M+48), "Request:  " + TASK, font=F(13, False), fill=INK)
    n_ag = sum(len(ph["agents"]) for ph in P); n_co = len({a[0] for ph in P for a in ph["agents"]})
    n_ga = sum(1 for ph in P if ph["gate"])
    d.text((M+62, M+70), f"{r['type']} workflow   ·   {n_ag} specialists   ·   {n_co} councils   ·   {n_ga} human gates",
           font=F(12, False), fill=MUTE)
    if caption:
        d.text((W-M-d.textlength(caption, font=F(12))-14, M+70), caption, font=F(12), fill=LIME)

    # ---- phase rail ----
    ry = M+128
    x = M
    for ph in P:
        s = state_of(ph["n"])
        label = ph["council"]
        w = 22 + int(d.textlength(label, font=F(11)))
        col = LIME if s == "now" else EMER if s == "done" else EDGE
        d.rounded_rectangle([x, ry, x+w, ry+30], radius=9, fill=PANEL2, outline=col, width=2 if s=="now" else 1)
        marker(d, x+13, ry+15, s, r=6)
        d.text((x+24, ry+8), label, font=F(11, s in ("now","done")), fill=INK if s!="todo" else DIM)
        x += w + 8
        if ph["gate"]:
            diamond(d, x+10, ry+15, 11, active=(s in ("now","done") or cur_phase is None))
            x += 30

    # ---- active phase card (left) ----
    ax, ay, aw = M, ry+54, W-M-330
    focus = P[cur_phase-1] if cur_phase else next((p for p in P if p["council"] == "Scouts"), P[0])
    fs = state_of(focus["n"])
    card_h = 96 + 64*len(focus["agents"])
    d.rounded_rectangle([ax, ay, ax+aw, ay+card_h], radius=14, fill=PANEL,
                        outline=LIME if fs=="now" else EDGE, width=2 if fs=="now" else 1)
    marker(d, ax+22, ay+26, fs, r=8)
    d.text((ax+40, ay+16), f"PHASE {focus['n']}  ·  {focus['council'].upper()}", font=F(15), fill=INK)
    stext = {"done":"DONE","now":"NOW","todo":"WAITING","plan":""}[fs]
    if stext:
        d.text((ax+aw-14-d.textlength(stext, font=F(10)), ay+20), stext, font=F(10), fill=LIME if fs=="now" else MUTE)
    cy = ay+52
    for (c, role, aid) in focus["agents"]:
        d.rounded_rectangle([ax+16, cy, ax+aw-16, cy+54], radius=10, fill=PANEL2,
                            outline=LIME if fs=="now" else EDGE, width=1)
        marker(d, ax+34, cy+27, fs, r=7)
        d.text((ax+52, cy+8), f"{c} · {role}", font=F(13), fill=INK)
        d.text((ax+52, cy+30), "cambium-institute:"+aid, font=F(10, False), fill=DIM)
        fnd = FINDINGS.get(aid) if show_findings and fs in ("now","done") else None
        if fnd:
            tx = ax+aw-16-360
            d.line([(tx-12, cy+10), (tx-12, cy+44)], fill=EMER, width=2)
            d.text((tx, cy+12), fnd, font=F(11, False), fill=INK)
            d.text((tx, cy+30), "Code-verified" if fs=="done" else "reporting…", font=F(9, False), fill=MUTE)
        cy += 64

    # ---- right column: leaderboard + gate ----
    rx, rw = ax+aw+18, 282
    d.rounded_rectangle([rx, ay, rx+rw, ay+150], radius=14, fill=PANEL, outline=EDGE, width=1)
    d.text((rx+16, ay+12), "LEADERBOARD", font=F(11), fill=MUTE)
    ly = ay+40
    for name, score in LEADER:
        c, role = run_trace.pretty(name)
        d.text((rx+16, ly), str(score), font=F(13), fill=LIME)
        d.text((rx+52, ly), f"{c} · {role}", font=F(12, False), fill=INK)
        ly += 26

    gy = ay+168
    if gate_active and focus["gate"]:
        g = focus["gate"]
        d.rounded_rectangle([rx, gy, rx+rw, gy+150], radius=14, fill=GATEBG, outline=LIME, width=2)
        d.text((rx+16, gy+12), f"GATE {g['id']} — your decision", font=F(12), fill=LIME)
        # wrap decision
        words = g["decision"].split(); line=""; yy=gy+38
        for wd in words:
            if d.textlength(line+" "+wd, font=F(12, False)) > rw-32:
                d.text((rx+16, yy), line, font=F(12, False), fill=INK); yy+=20; line=wd
            else:
                line = (line+" "+wd).strip()
        d.text((rx+16, yy), line, font=F(12, False), fill=INK)
        bx = rx+16; by = gy+150-40
        for lab, fill, tcol in [("APPROVE", LIME, BG), ("REVISE", None, INK), ("REJECT", None, (233,164,164))]:
            bw = 16+int(d.textlength(lab, font=F(11)))
            d.rounded_rectangle([bx, by, bx+bw, by+26], radius=8, fill=fill, outline=EDGE if not fill else None, width=1)
            d.text((bx+8, by+6), lab, font=F(11), fill=tcol)
            bx += bw + 8
    else:
        d.rounded_rectangle([rx, gy, rx+rw, gy+150], radius=14, fill=PANEL, outline=EDGE, width=1)
        d.text((rx+16, gy+12), "NEXT GATE", font=F(11), fill=MUTE)
        nxt = next((p["gate"] for p in P if p["gate"] and (cur_phase is None or p["n"] >= (cur_phase or 1))), None)
        d.text((rx+16, gy+40), (f"{nxt['id']} — {nxt['kind'].lower()}" if nxt else "—"), font=F(12, False), fill=INK)
        d.text((rx+16, gy+66), "nothing finalizes", font=F(11, False), fill=MUTE)
        d.text((rx+16, gy+84), "without your APPROVE.", font=F(11, False), fill=MUTE)

    # footer
    d.text((M, H-26), "✓ done   ▶ now   ○ waiting   ◆ human gate", font=F(11, False), fill=DIM)
    return im


def main():
    os.makedirs(ASSETS, exist_ok=True)
    # static hero = Scouts running, findings in, gate armed
    hero = render(cur_phase=2, show_findings=True, gate_active=True, caption="live — Scouts reporting")
    hero.save(os.path.join(ASSETS, "run_board.png"))
    # animated story
    frames = [
        render(None, False, False, "the plan, before any work"),
        render(2, True, False, "Scouts dispatched — live"),
        render(2, True, True, "⛩ your gate: APPROVE / REVISE / REJECT"),
        render(3, True, False, "approved — Labs advancing"),
    ]
    durs = [1.7, 1.9, 2.2, 1.7]
    imageio.mimsave(os.path.join(ASSETS, "run_board.gif"),
                    [f.convert("P", palette=Image.ADAPTIVE) for f in frames], duration=durs, loop=0)
    print("wrote", os.path.join(ASSETS, "run_board.png"))
    print("wrote", os.path.join(ASSETS, "run_board.gif"))


if __name__ == "__main__":
    main()
