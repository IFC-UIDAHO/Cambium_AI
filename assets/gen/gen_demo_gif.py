#!/usr/bin/env python3
"""Regenerate assets/demo.gif · Cambium brand loop (responsible-AI framing).
Living-Layer style. Counts read from agent_cards.json (46/11/8).
Output: assets/demo.gif  (loops forever, < 3 MB)
  python3 assets/gen/gen_demo_gif.py
"""
import os, json
from PIL import Image, ImageDraw, ImageFont
import imageio.v2 as imageio
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
N = json.load(open(os.path.join(ROOT, "agent_cards.json")))["count"]
COUNCILS = 11; GATES = 8

W, H = 920, 512
BG=(7,35,26); PANEL=(14,51,38); HAIR=(31,77,59)
INK=(244,247,242); MUT=(138,161,151)
EMER=(22,192,121); LIME=(183,243,106); AMBER=(224,178,74)
FB="/usr/share/fonts/truetype/dejavu/"

def f(sz, bold=True):
    try: return ImageFont.truetype(FB+("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"), sz)
    except: return ImageFont.load_default()

def ctext(d, y, s, fnt, col):
    w = d.textlength(s, font=fnt)
    d.text(((W-w)/2, y), s, font=fnt, fill=col)
    return w

def hexmark(d, cx, cy, r, col, width=4):
    import math
    pts = []
    for i in range(6):
        a = math.radians(60*i - 90)
        pts.append((cx + r*math.cos(a), cy + r*math.sin(a)))
    d.line(pts + [pts[0]], fill=col, width=width, joint="curve")

def base_frame(lines, accent_line=None):
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    # subtle panel vignette
    d.rounded_rectangle([16,16,W-16,H-16], 22, outline=HAIR, width=1)
    # hex mark up top
    hexmark(d, W/2, 78, 30, EMER, width=4)
    ctext(d, 60, "C", f(30), LIME)
    yy = 196
    for (s, sz, col, bold) in lines:
        ctext(d, yy, s, f(sz, bold), col)
        yy += sz + 20
    return im

scenes = [
    [("Cambium", 60, EMER, True),
     ("responsible-AI research institute", 24, MUT, False)],
    [("Use AI to expand capacity,", 36, INK, True),
     ("keep human judgment in charge", 30, INK, True)],
    [(f"{N} agents  ·  {COUNCILS} councils  ·  {GATES} human gates", 34, INK, True),
     ("from RFP to verified results", 24, MUT, False)],
    [("Governed by construction", 36, INK, True),
     ("evidence contract · CI fails on un-evidenced claims", 22, LIME, False)],
    [("Cambium", 54, EMER, True),
     ("github.com/IFC-UIDAHO/Cambium_AI", 22, MUT, False)],
]

frames = []
for sc in scenes:
    base = base_frame(sc)
    blank = Image.new("RGB", (W, H), BG)
    # fade-in
    for a in (70, 130, 190, 235, 255):
        frames.append(Image.blend(blank, base, a/255.0))
    # hold (~1.5s at 0.08s/frame)
    for _ in range(18):
        frames.append(base)
    # fade-out tail (short)
    for a in (200, 120):
        frames.append(Image.blend(blank, base, a/255.0))

# quantize for small size
arrs = [np.array(im.convert("P", palette=Image.ADAPTIVE, colors=96).convert("RGB")) for im in frames]
out = os.path.join(ROOT, "assets", "demo.gif")
imageio.mimsave(out, arrs, duration=0.08, loop=0)
print("[gen_demo_gif] wrote %s | %d frames | %d agents %d councils %d gates"
      % (out, len(frames), N, COUNCILS, GATES))
