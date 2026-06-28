#!/usr/bin/env python3
"""gen_example_gif — record `cambium_run.py example` into a scrolling terminal GIF for the README demo.

The README "5-minute demo" promised something to *watch*; this renders the real dry-run output (phase
ladder, named agents, models, the 8 gates) into an animated terminal GIF so GitHub shows an actual
recording, not just a command. No external recorder — captures the tool's own output and paints frames.

  python3 tools/gen_example_gif.py   ->  assets/demo_example.gif
"""
import os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont
import imageio.v2 as imageio

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "demo_example.gif")
BG=(7,35,26); PANEL=(10,39,29); INK=(244,247,242); MUT=(138,161,151); LIME=(183,243,106); EMER=(22,192,121); DIM=(94,116,104)
W=860; PAD=24; LINE=20; VIEW=22                      # viewport: 22 lines tall
FB="/usr/share/fonts/truetype/dejavu/"
def mono(sz):
    try: return ImageFont.truetype(FB+"DejaVuSansMono.ttf", sz)
    except: return ImageFont.load_default()
def monob(sz):
    try: return ImageFont.truetype(FB+"DejaVuSansMono-Bold.ttf", sz)
    except: return ImageFont.load_default()
F=mono(14); FB_=monob(14); FT=monob(15)

def color_for(line):
    s=line.strip()
    if s.startswith("### PHASE"): return EMER, FB_
    if "GATE G" in line or s.startswith("╚═") or s.startswith("╔═"): return LIME, FB_
    if "->" in line or "(planned)" in line: return MUT, F
    if s.startswith("•"): return INK, F
    if s.startswith("CAMBIUM AUTO-RUNNER") or "===" in line: return LIME, FB_
    return INK, F

def render(lines, top):
    H = PAD*2 + 30 + VIEW*LINE
    img = Image.new("RGB",(W,H),BG); d=ImageDraw.Draw(img)
    d.rounded_rectangle([8,8,W-8,H-8],14,outline=(31,77,59),width=1,fill=PANEL)
    # title bar
    d.text((PAD,16),"⬢ CAMBIUM  ·  /cambium run example  (dry-run, no API key)",font=FT,fill=LIME)
    for i,btn in enumerate([(231,90,90),(232,184,75),(22,192,121)]):
        d.ellipse([W-PAD-18-(i*22),18,W-PAD-6-(i*22),30],fill=btn)
    y=PAD+30
    for line in lines[top:top+VIEW]:
        col,fnt=color_for(line)
        d.text((PAD,y),line[:96],font=fnt,fill=col); y+=LINE
    return img

def main():
    out = subprocess.run([sys.executable,"tools/cambium_run.py","example"],cwd=ROOT,capture_output=True,text=True)
    lines=[l.rstrip() for l in out.stdout.splitlines() if l.strip()!=""] or ["(no output)"]
    frames=[]; 
    # hold on first frame, then scroll a few lines per frame, then hold on last
    maxtop=max(0,len(lines)-VIEW)
    tops=[0]*4 + list(range(0,maxtop+1,2)) + [maxtop]*6
    for t in tops:
        frames.append(render(lines,t))
    imageio.mimsave(OUT,[f for f in frames],duration=0.5,loop=0)
    print("[gen_example_gif] wrote %s (%d frames, %d lines)" % (os.path.relpath(OUT,ROOT),len(frames),len(lines)))

if __name__=="__main__":
    main()
