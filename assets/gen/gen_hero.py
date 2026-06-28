#!/usr/bin/env python3
"""Generate assets/hero.svg — the README hero banner ("Living Layer" style).
Usage: python3 assets/gen/gen_hero.py
"""
import os
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
W, H = 1280, 360
FONT = "Inter, 'DejaVu Sans', Arial, sans-serif"
BG="#07231A"; PANEL="#0E3326"; PANEL2="#15402F"; HAIR="#1F4D3B"
CANVAS="#F4F7F2"; MUTED="#8AA197"; EMER="#16C079"; EMERD="#0E8E5B"
LIME="#B7F36A"; INKE="#052015"

def hexpts(cx, cy, r):
    import math
    pts=[]
    for i in range(6):
        a=math.radians(60*i-90)
        pts.append(f"{cx+r*math.cos(a):.1f},{cy+r*math.sin(a):.1f}")
    return " ".join(pts)

s=[]
s.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-family="{FONT}" role="img" aria-label="Cambium — Responsible-AI Research Institute">')
s.append('<defs>')
s.append(f'<linearGradient id="bgg" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="#07231A"/><stop offset="100%" stop-color="#0A2A1F"/></linearGradient>')
s.append(f'<linearGradient id="hexg" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="{LIME}"/><stop offset="100%" stop-color="{EMER}"/></linearGradient>')
s.append(f'<radialGradient id="glow" cx="50%" cy="50%" r="50%"><stop offset="0%" stop-color="{LIME}" stop-opacity="0.30"/><stop offset="100%" stop-color="{LIME}" stop-opacity="0"/></radialGradient>')
s.append(f'<clipPath id="card"><rect x="0" y="0" width="{W}" height="{H}" rx="0"/></clipPath>')
s.append('</defs>')
s.append(f'<rect width="{W}" height="{H}" fill="url(#bgg)"/>')

# background tree-ring arcs (low opacity) anchored bottom-right
s.append(f'<g clip-path="url(#card)" opacity="0.5">')
rcx, rcy = 1180, 300
import math
for i,r in enumerate(range(70, 620, 34)):
    op = 0.05 + (i%3)*0.02
    col = EMER if i%2==0 else EMERD
    s.append(f'<circle cx="{rcx}" cy="{rcy}" r="{r}" fill="none" stroke="{col}" stroke-width="1.4" opacity="{op:.2f}"/>')
# faint node-network dots on a couple rings
for ang,rr in [(200,240),(225,310),(170,380),(250,210),(150,450)]:
    a=math.radians(ang); x=rcx+rr*math.cos(a); y=rcy+rr*math.sin(a)
    s.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="3" fill="{LIME}" opacity="0.30"/>')
s.append('</g>')

# left hex mark
hx, hy, hr = 110, 150, 58
s.append(f'<circle cx="{hx}" cy="{hy}" r="92" fill="url(#glow)"/>')
s.append(f'<polygon points="{hexpts(hx,hy,hr)}" fill="none" stroke="url(#hexg)" stroke-width="5" stroke-linejoin="round"/>')
s.append(f'<polygon points="{hexpts(hx,hy,hr-16)}" fill="{LIME}" opacity="0.14"/>')
# inner concentric mini-rings inside hex
for r in (10,20,30):
    s.append(f'<circle cx="{hx}" cy="{hy}" r="{r}" fill="none" stroke="{EMER}" stroke-width="1.4" opacity="0.55"/>')
s.append(f'<circle cx="{hx}" cy="{hy}" r="5" fill="{LIME}"/>')

# wordmark
wx=200
s.append(f'<text x="{wx}" y="128" fill="{CANVAS}" font-size="64" font-weight="800" letter-spacing="2">CAMBIUM<tspan fill="{LIME}">.</tspan></text>')
s.append(f'<text x="{wx+3}" y="162" fill="{MUTED}" font-size="17" font-weight="600" letter-spacing="6">RESPONSIBLE-AI RESEARCH INSTITUTE</text>')

# vertical divider
s.append(f'<line x1="{wx}" y1="196" x2="730" y2="196" stroke="{HAIR}" stroke-width="1.4"/>')

# tagline (emerald), wrapped
tag1="Use AI to expand scientific capacity —"
tag2="keep human judgment responsible for"
tag3="validity, ethics, and decisions."
tx=wx
s.append(f'<text x="{tx}" y="232" fill="{EMER}" font-size="25" font-weight="700">{tag1}</text>')
s.append(f'<text x="{tx}" y="262" fill="{CANVAS}" font-size="25" font-weight="500">{tag2}</text>')
s.append(f'<text x="{tx}" y="292" fill="{CANVAS}" font-size="25" font-weight="500">{tag3}</text>')

# right-side stat block (big numbers)
def stat(x, num, lab):
    s.append(f'<text x="{x}" y="150" text-anchor="middle" fill="{LIME}" font-size="52" font-weight="800">{num}</text>')
    s.append(f'<text x="{x}" y="176" text-anchor="middle" fill="{MUTED}" font-size="13" font-weight="600" letter-spacing="1">{lab}</text>')
sx=860
for i,(n,l) in enumerate([("46","AGENTS"),("11","COUNCILS"),("8","HUMAN GATES")]):
    stat(sx+i*145, n, l)
s.append(f'<line x1="{sx-60}" y1="76" x2="{sx-60}" y2="190" stroke="{HAIR}" stroke-width="1.4"/>')

# bottom pills strip
pills=["46 agents","11 councils","8 human gates","evidence contract","MIT"]
px=200; py=340
s.append(f'<g font-size="14" font-weight="600">')
for p in pills:
    w=len(p)*8.2+30
    fill = f'{LIME}' if p=="MIT" else PANEL2
    txt = INKE if p=="MIT" else CANVAS
    stroke = LIME if p=="MIT" else HAIR
    s.append(f'<rect x="{px}" y="{py-20}" width="{w:.0f}" height="28" rx="14" fill="{fill}" stroke="{stroke}" stroke-width="1.2"/>')
    s.append(f'<text x="{px+w/2:.0f}" y="{py-1}" text-anchor="middle" fill="{txt}">{p}</text>')
    px+=w+12
s.append('</g>')

s.append('</svg>')
open(os.path.join(ROOT,"assets","hero.svg"),"w").write("\n".join(s))
print("[gen_hero] wrote assets/hero.svg")
