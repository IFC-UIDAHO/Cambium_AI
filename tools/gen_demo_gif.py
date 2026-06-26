#!/usr/bin/env python3
"""Generate assets/demo.gif from current counts (read from agent_cards.json).
Usage: python3 tools/gen_demo_gif.py
"""
import os, json
from PIL import Image, ImageDraw, ImageFont
import imageio.v2 as imageio

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
N = json.load(open(os.path.join(ROOT,"agent_cards.json")))["count"]
COUNCILS = 11; GATES = 8
W,H = 760,422; BG=(11,16,32); GOLD=(231,184,75); INK=(232,237,247); MUT=(159,176,208); GREEN=(70,196,106)
FB="/usr/share/fonts/truetype/dejavu/"
def f(sz,bold=True): 
    try: return ImageFont.truetype(FB+("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"), sz)
    except: return ImageFont.load_default()
def ctext(d,y,s,fnt,col):
    w=d.textlength(s,font=fnt); d.text(((W-w)/2,y),s,font=fnt,fill=col); return w

def frame(lines):
    im=Image.new("RGB",(W,H),BG); d=ImageDraw.Draw(im)
    d.ellipse([W/2-30,42,W/2+30,102],outline=GOLD,width=3); ctext(d,55,"\U0001F332",f(30),GREEN)
    yy=130
    for s,sz,col,bold in lines: ctext(d,yy,s,f(sz,bold),col); yy+=sz+16
    return im

scenes=[
 [("Cambium",54,GOLD,True),("research that grows",20,MUT,False)],
 [("From RFP to verified results",30,INK,True),("with a human at every gate",20,MUT,False)],
 [(f"{N} agents  ·  {COUNCILS} councils",34,INK,True),(f"{GATES} human gates (G0–G6)",20,MUT,False)],
 [("Governed by construction",30,INK,True),("conduct + evidence + AI policy",20,MUT,False),("CI fails on un-evidenced claims",18,GREEN,False)],
 [("Cambium",46,GOLD,True),("github.com/IFC-UIDAHO/Cambium_AI",18,MUT,False)],
]
frames=[]
for sc in scenes:
    base=frame(sc)
    for a in (90,160,230,255):  # fade-in
        im=Image.new("RGB",(W,H),BG); im=Image.blend(im,base,a/255.0); frames.append(im)
    for _ in range(10): frames.append(base)  # hold

imgs=[f.convert("P",palette=Image.ADAPTIVE,colors=128) for f in frames]
out=os.path.join(ROOT,"assets","demo.gif")
imageio.mimsave(out,[__import__("numpy").array(i.convert("RGB")) for i in frames],duration=0.08,loop=0)
print("[gen_demo_gif] wrote %s | %d frames | %d agents %d councils %d gates"%(out,len(frames),N,COUNCILS,GATES))
