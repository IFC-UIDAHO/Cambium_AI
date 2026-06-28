#!/usr/bin/env python3
"""Generate assets/responsible-ai.svg · the centerpiece risk->control diagram.
Usage: python3 assets/gen/gen_responsible_ai.py
"""
import os
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FONT = "Inter, 'DejaVu Sans', Arial, sans-serif"
BG="#07231A"; PANEL="#0E3326"; PANEL2="#15402F"; HAIR="#1F4D3B"
CANVAS="#F4F7F2"; MUTED="#8AA197"; EMER="#16C079"; LIME="#B7F36A"
INKE="#052015"; RISK="#FF6B5E"

# (risk title, risk sub) | (control title, control sub)
PAIRS = [
 ("Overclaiming","stating more than the evidence supports",
  "4-tier evidence contract","CI fails on un-evidenced claims (validate.py)"),
 ("Fabricated or unresolvable citations","references that don't exist",
  "Citation-resolution gate","unsupported = release blocker"),
 ("Speed collapses human judgment","decisions outrun deliberation",
  "Pace check","30-min deliberation interval between gates"),
 ("AI erases the human's learning","you ship work you didn't grow into",
  "Learning Gate","a real Director contribution is required to pass"),
 ("Bias goes unexamined","unfairness ships unchecked",
  "Bias checklist (NIST AI RMF)","enforced before G4 / G5"),
 ("Sensitive data leaks","PII / regulated data escapes",
  "PII / regulated-data scanner","runs in your own account"),
 ("Authorship & accountability blur","no one is responsible",
  "Named human signature at every gate","AI is never an author"),
]

W=1200
top=96
ch=58          # card height
gap=14
n=len(PAIRS)
bottom_strip=70
H = top + n*(ch+gap) - gap + bottom_strip + 30

# column geometry
colw=440
lx=44                  # left col x
rx=W-44-colw           # right col x
midcx=W/2

def esc(t): return t.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

s=[]
s.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-family="{FONT}" role="img" aria-label="AI risks and Cambium controls">')
s.append('<defs>')
s.append(f'<linearGradient id="bgg" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="#07231A"/><stop offset="100%" stop-color="#0A2A1F"/></linearGradient>')
s.append(f'<marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{EMER}"/></marker>')
s.append('</defs>')
s.append(f'<rect width="{W}" height="{H}" fill="url(#bgg)"/>')

# title
s.append(f'<text x="{W/2}" y="46" text-anchor="middle" fill="{CANVAS}" font-size="27" font-weight="800">AI in research: the risks, and what Cambium does about each</text>')
# column headers
s.append(f'<text x="{lx+colw/2}" y="80" text-anchor="middle" fill="{RISK}" font-size="14" font-weight="700" letter-spacing="3">THE CONCERN</text>')
s.append(f'<text x="{rx+colw/2}" y="80" text-anchor="middle" fill="{EMER}" font-size="14" font-weight="700" letter-spacing="3">THE ENFORCED CONTROL</text>')

for i,(rt,rs,ct,cs) in enumerate(PAIRS):
    y=top+i*(ch+gap)
    cy=y+ch/2
    # left risk card
    s.append(f'<rect x="{lx}" y="{y}" width="{colw}" height="{ch}" rx="14" fill="{PANEL}" stroke="{RISK}" stroke-width="1.8"/>')
    s.append(f'<rect x="{lx}" y="{y}" width="6" height="{ch}" rx="3" fill="{RISK}"/>')
    s.append(f'<text x="{lx+22}" y="{y+25}" fill="{CANVAS}" font-size="16" font-weight="700">{esc(rt)}</text>')
    s.append(f'<text x="{lx+22}" y="{y+45}" fill="{MUTED}" font-size="12.5">{esc(rs)}</text>')
    # right control card
    s.append(f'<rect x="{rx}" y="{y}" width="{colw}" height="{ch}" rx="14" fill="{PANEL2}" stroke="{EMER}" stroke-width="1.8"/>')
    s.append(f'<rect x="{rx+colw-6}" y="{y}" width="6" height="{ch}" rx="3" fill="{EMER}"/>')
    s.append(f'<text x="{rx+22}" y="{y+25}" fill="{LIME}" font-size="16" font-weight="700">{esc(ct)}</text>')
    s.append(f'<text x="{rx+22}" y="{y+45}" fill="{CANVAS}" font-size="12.5">{esc(cs)}</text>')
    # connecting arrow
    s.append(f'<line x1="{lx+colw+6}" y1="{cy}" x2="{rx-6}" y2="{cy}" stroke="{EMER}" stroke-width="2" opacity="0.8" marker-end="url(#arrow)"/>')

# footer spine in lime
fy = top + n*(ch+gap) - gap + 26
s.append(f'<rect x="44" y="{fy}" width="{W-88}" height="44" rx="14" fill="{LIME}"/>')
s.append(f'<text x="{W/2}" y="{fy+29}" text-anchor="middle" fill="{INKE}" font-size="17" font-weight="800">The human stays responsible for validity, ethics, and decisions.</text>')

s.append('</svg>')
open(os.path.join(ROOT,"assets","responsible-ai.svg"),"w").write("\n".join(s))
print("[gen_responsible_ai] wrote assets/responsible-ai.svg (H=%d)"%H)
