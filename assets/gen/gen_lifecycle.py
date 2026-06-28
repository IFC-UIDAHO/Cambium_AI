#!/usr/bin/env python3
"""Generate assets/lifecycle.svg — research lifecycle with the 8 human gates.
Usage: python3 assets/gen/gen_lifecycle.py
"""
import os, math
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FONT = "Inter, 'DejaVu Sans', Arial, sans-serif"
BG="#07231A"; PANEL="#0E3326"; PANEL2="#15402F"; HAIR="#1F4D3B"
CANVAS="#F4F7F2"; MUTED="#8AA197"; EMER="#16C079"; LIME="#B7F36A"
INKE="#052015"; GOLD="#E0B24A"

W=1100; H=300
# phases along the flow
PHASES=["Intake","Pre-Award","Lab","Verification","Reporting","Publish"]
# 8 gates: id, one-word purpose
GATES=[
 ("G0","intake"),
 ("G1","pursue"),
 ("G2","approach"),
 ("G3","submit"),     # Director-only
 ("G3a","budget"),
 ("G4","accept"),
 ("G5","release"),
 ("G6","publish"),
]
DIRONLY={"G3"}

def shield(cx, cy, r, fill, stroke):
    # shield glyph path centred at cx,cy with half-width r
    top=cy-r; w=r; bot=cy+r*1.15
    return (f'<path d="M {cx-w} {top} L {cx+w} {top} L {cx+w} {cy+r*0.25} '
            f'Q {cx+w} {cy+r*0.7} {cx} {bot} Q {cx-w} {cy+r*0.7} {cx-w} {cy+r*0.25} Z" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="2" stroke-linejoin="round"/>')

s=[]
s.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-family="{FONT}" role="img" aria-label="Cambium research lifecycle — 8 human gates">')
s.append('<defs>')
s.append(f'<linearGradient id="bgg" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="#07231A"/><stop offset="100%" stop-color="#0A2A1F"/></linearGradient>')
s.append(f'<linearGradient id="flow" x1="0" y1="0" x2="1" y2="0"><stop offset="0%" stop-color="{EMER}"/><stop offset="100%" stop-color="{LIME}"/></linearGradient>')
s.append('</defs>')
s.append(f'<rect width="{W}" height="{H}" fill="url(#bgg)"/>')

# title
s.append(f'<text x="{W/2}" y="40" text-anchor="middle" fill="{CANVAS}" font-size="22" font-weight="800">The research lifecycle — 8 human gates</text>')
s.append(f'<text x="{W/2}" y="62" text-anchor="middle" fill="{MUTED}" font-size="13" font-weight="500">a named human signs off at every gate before work proceeds</text>')

# flow line geometry
fy=178
x0=60; x1=W-60
s.append(f'<line x1="{x0}" y1="{fy}" x2="{x1}" y2="{fy}" stroke="url(#flow)" stroke-width="4"/>')

# phase labels above the line, evenly spaced
np=len(PHASES)
seg=(x1-x0)/np
phase_y=104
for i,p in enumerate(PHASES):
    px=x0+seg*(i+0.5)
    s.append(f'<rect x="{px-58}" y="{phase_y-22}" width="116" height="32" rx="14" fill="{PANEL2}" stroke="{HAIR}" stroke-width="1.2"/>')
    s.append(f'<text x="{px}" y="{phase_y}" text-anchor="middle" fill="{CANVAS}" font-size="14" font-weight="700">{p}</text>')
    if i<np-1:
        ax=x0+seg*(i+1)
        s.append(f'<text x="{ax}" y="{phase_y}" text-anchor="middle" fill="{EMER}" font-size="16" font-weight="800">&#8594;</text>')

# gates along the line
ng=len(GATES)
gx0=x0+24; gx1=x1-24
for i,(gid,purpose) in enumerate(GATES):
    gx=gx0+(gx1-gx0)*i/(ng-1)
    dir_only = gid in DIRONLY
    fill = GOLD if dir_only else LIME
    stroke = "#9C7A1E" if dir_only else "#0B2E22"
    # connector tick to flow
    s.append(f'<circle cx="{gx:.1f}" cy="{fy}" r="4" fill="{INKE}" stroke="{LIME}" stroke-width="1.5"/>')
    # shield above-ish, centred on line
    syc=fy
    s.append(shield(gx, syc-1, 17, fill, stroke))
    s.append(f'<text x="{gx:.1f}" y="{syc+3}" text-anchor="middle" fill="{INKE}" font-size="11" font-weight="800">{gid}</text>')
    # purpose label below
    py=fy+44
    s.append(f'<text x="{gx:.1f}" y="{py}" text-anchor="middle" fill="{CANVAS}" font-size="12" font-weight="600">{purpose}</text>')
    if dir_only:
        s.append(f'<text x="{gx:.1f}" y="{py+15}" text-anchor="middle" fill="{GOLD}" font-size="9.5" font-weight="700" letter-spacing="0.5">DIRECTOR-ONLY</text>')

# legend
ly=H-22
s.append(shield(74, ly-2, 9, LIME, "#0B2E22"))
s.append(f'<text x="90" y="{ly+2}" fill="{MUTED}" font-size="12">human gate</text>')
s.append(shield(190, ly-2, 9, GOLD, "#9C7A1E"))
s.append(f'<text x="206" y="{ly+2}" fill="{MUTED}" font-size="12">Director-only gate</text>')
s.append(f'<rect x="350" y="{ly-9}" width="34" height="16" rx="8" fill="none" stroke="url(#flow)" stroke-width="3"/>')
s.append(f'<text x="392" y="{ly+2}" fill="{MUTED}" font-size="12">emerald flow line</text>')

s.append('</svg>')
open(os.path.join(ROOT,"assets","lifecycle.svg"),"w").write("\n".join(s))
print("[gen_lifecycle] wrote assets/lifecycle.svg")
