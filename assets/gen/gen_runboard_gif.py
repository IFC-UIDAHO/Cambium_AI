#!/usr/bin/env python3
"""Regenerate assets/run_board.gif — an animated Cambium RUN BOARD.
Living-Layer style. A research run advances through 3 phases of named agents,
each box: queued (grey) -> working (amber pulse) -> done (emerald + finding),
with human GATE cards between phases, ending on run-complete.
Output: assets/run_board.gif  (loops forever, ~12s, < 3 MB)
  python3 assets/gen/gen_runboard_gif.py
"""
import os, math
from PIL import Image, ImageDraw, ImageFont
import imageio.v2 as imageio
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

W, H = 980, 724
BG=(7,35,26); PANEL=(14,51,38); HAIR=(31,77,59)
INK=(244,247,242); MUT=(138,161,151)
EMER=(22,192,121); LIME=(183,243,106); AMBER=(224,178,74)
VERIF=(255,107,94)
GREY=(58,82,70); GREYINK=(122,143,133)
FB="/usr/share/fonts/truetype/dejavu/"

def f(sz, bold=True):
    try: return ImageFont.truetype(FB+("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"), sz)
    except: return ImageFont.load_default()

F_H = f(24, True); F_SUB = f(15, False); F_PH = f(17, True)
F_AG = f(15, True); F_FIND = f(12, False); F_ST = f(12, True); F_GATE = f(18, True)

def hexmark(d, cx, cy, r, col, width=3):
    pts = []
    for i in range(6):
        a = math.radians(60*i - 90)
        pts.append((cx + r*math.cos(a), cy + r*math.sin(a)))
    d.line(pts + [pts[0]], fill=col, width=width, joint="curve")

# ---- run definition: 3 phases, each with named agents + findings ----
PHASES = [
    ("PHASE 1 · SCOUTS", "scope the landscape", EMER, [
        ("scout-prior-art", "nearest prior work mapped · novelty distance 0.41"),
        ("scout-landscape", "12 competing efforts · 3 open datasets located"),
    ]),
    ("PHASE 2 · LABS", "build & quantify", LIME, [
        ("lab-methods", "cross-fit estimator built · ablation-ready"),
        ("lab-statistics", "CI [0.18, 0.27] · power 0.86 at n=240"),
    ]),
    ("PHASE 3 · VERIFICATION", "reproduce every number", VERIF, [
        ("verify-evidence", "all 3 headline numbers reproduced from code"),
        ("referee", "verdict: minor revisions · soundness 4/5"),
    ]),
]
GATES = [
    "Gate G1 — your decision · APPROVE / REVISE / REJECT",
    "Gate G2 — your decision · APPROVE / REVISE / REJECT",
]

def rrect(d, box, r, fill=None, outline=None, width=1):
    d.rounded_rectangle(box, r, fill=fill, outline=outline, width=width)

def draw_header(d, prog):
    rrect(d, [14,14,W-14,H-14], 22, outline=HAIR, width=1)
    hexmark(d, 44, 50, 16, EMER, 3)
    d.text((70, 38), "CAMBIUM INSTITUTE — run board", font=F_H, fill=INK)
    # progress bar
    bx0, bx1, by = 70, W-40, 80
    rrect(d, [bx0, by, bx1, by+12], 6, fill=PANEL, outline=HAIR, width=1)
    fillx = bx0 + (bx1-bx0)*max(0.0, min(1.0, prog))
    if fillx > bx0+2:
        rrect(d, [bx0, by, fillx, by+12], 6, fill=EMER)
    d.text((bx1-46, by-22), f"{int(round(prog*100)):3d}%", font=F_SUB, fill=MUT)

def agent_box(d, x, y, w, h, name, finding, state, pulse=0.0):
    # state: 'queued','working','done'
    if state == 'queued':
        bg = (12,42,32); bd = GREY; dot = GREY; stxt="queued"; stcol=GREYINK; nmcol=GREYINK
    elif state == 'working':
        # amber pulse on border + dot
        amt = 0.45 + 0.55*abs(math.sin(pulse))
        bd = tuple(int(AMBER[i]*amt + HAIR[i]*(1-amt)) for i in range(3))
        bg = (20,56,42); dot = AMBER; stxt="working"; stcol=AMBER; nmcol=INK
    else:
        bg = (16,58,42); bd = EMER; dot = EMER; stxt="done"; stcol=EMER; nmcol=INK
    rrect(d, [x,y,x+w,y+h], 10, fill=bg, outline=bd, width=2)
    d.ellipse([x+14, y+h/2-6, x+26, y+h/2+6], fill=dot)
    d.text((x+40, y+12), name, font=F_AG, fill=nmcol)
    # status tag right
    tag = ("✓ "+stxt) if state=='done' else stxt
    tw = d.textlength(tag, font=F_ST)
    d.text((x+w-tw-14, y+12), tag, font=F_ST, fill=stcol)
    # finding line (only when done)
    if state == 'done':
        d.text((x+40, y+36), finding, font=F_FIND, fill=MUT)
    elif state == 'working':
        d.text((x+40, y+36), "running…", font=F_FIND, fill=GREYINK)

def phase_label(d, x, y, title, sub, col):
    d.rectangle([x, y+2, x+5, y+26], fill=col)
    d.text((x+16, y), title, font=F_PH, fill=col)
    tw = d.textlength(title, font=F_PH)
    d.text((x+16+tw+14, y+3), sub, font=F_SUB, fill=MUT)

# layout: list of phase blocks down the board
def board(states, prog, pulse, gate_active=None, complete=False):
    """states: dict (pi, ai) -> state string for each agent.
    gate_active: index of gate to highlight, or None."""
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    draw_header(d, prog)
    y = 108
    BX, BW, BH = 50, W-100, 54
    for pi, (title, sub, col, agents) in enumerate(PHASES):
        phase_label(d, BX, y, title, sub, col)
        y += 32
        for ai, (name, finding) in enumerate(agents):
            st = states.get((pi, ai), 'queued')
            agent_box(d, BX, y, BW, BH, name, finding, st, pulse)
            y += BH + 8
        # gate after phase 1 and 2
        if pi < len(GATES):
            active = (gate_active == pi)
            gy = y + 2
            gcol = LIME if active else HAIR
            gbg = (20,48,30) if active else (12,42,32)
            rrect(d, [BX, gy, BX+BW, gy+34], 9, fill=gbg, outline=gcol, width=2 if active else 1)
            txt = " " + GATES[pi]
            d.text((BX+16, gy+8), txt, font=F_GATE if active else F_ST,
                   fill=LIME if active else GREYINK)
            y = gy + 34 + 10
        else:
            y += 6
    if complete:
        # overlay bottom banner
        by = H - 56
        rrect(d, [50, by, W-50, by+40], 10, fill=(16,58,42), outline=EMER, width=2)
        msg = "✓ run complete — every number reproduced before release."
        tw = d.textlength(msg, font=F_PH)
        d.text(((W-tw)/2, by+9), msg, font=F_PH, fill=LIME)
    return im

# ---- build the animation timeline ----
frames = []
durs = []
agents_flat = [(pi, ai) for pi in range(3) for ai in range(2)]
total_agents = len(agents_flat)
states = {a: 'queued' for a in agents_flat}

def progress_for(done_count, gate_steps_done):
    # 6 agents + 2 gates = 8 units of progress
    return (done_count + gate_steps_done) / (total_agents + len(GATES))

def add(im, dur=0.08):
    frames.append(im); durs.append(dur)

# opening hold
for _ in range(6):
    add(board(states, 0.0, 0.0), 0.09)

done_count = 0
gate_steps_done = 0
pulse = 0.0
for pi in range(3):
    for ai in range(2):
        key = (pi, ai)
        # queued -> working (pulse a few frames)
        states[key] = 'working'
        for k in range(7):
            pulse += 0.7
            add(board(states, progress_for(done_count, gate_steps_done), pulse), 0.07)
        # working -> done
        states[key] = 'done'
        done_count += 1
        # hold to reveal finding
        for k in range(7):
            add(board(states, progress_for(done_count, gate_steps_done), pulse), 0.08)
    # gate after phase 0 and 1
    if pi < len(GATES):
        # highlight gate, pulse the lime card
        for k in range(12):
            add(board(states, progress_for(done_count, gate_steps_done),
                      pulse, gate_active=pi), 0.09)
        gate_steps_done += 1
        # brief approved beat
        for k in range(3):
            add(board(states, progress_for(done_count, gate_steps_done),
                      pulse, gate_active=pi), 0.07)

# completion
final = board(states, 1.0, pulse, complete=True)
for _ in range(26):
    add(final, 0.09)

# quantize to keep size down
arrs = [np.array(im.convert("P", palette=Image.ADAPTIVE, colors=80).convert("RGB")) for im in frames]
out = os.path.join(ROOT, "assets", "run_board.gif")
imageio.mimsave(out, arrs, duration=durs, loop=0)
print("[gen_runboard_gif] wrote %s | %d frames | total %.1fs"
      % (out, len(frames), sum(durs)))
