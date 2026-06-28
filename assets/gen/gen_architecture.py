#!/usr/bin/env python3
"""Generate assets/architecture.svg — Orchestrator -> 11 councils -> 46 agents.
Roster mirrors tools/gen_org_chart.py (single source of truth, re-stated + verified).
Usage: python3 assets/gen/gen_architecture.py
"""
import os, json
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FONT = "Inter, 'DejaVu Sans', Arial, sans-serif"
BG="#07231A"; PANEL="#0E3326"; PANEL2="#15402F"; HAIR="#1F4D3B"
CANVAS="#F4F7F2"; MUTED="#8AA197"; EMER="#16C079"; LIME="#B7F36A"
INKE="#052015"; ORCH="#7C5CFF"

COUNCILS = [
 ("Orchestration","#7C5CFF",["orchestrator","document-office"]),
 ("Pre-Award","#2BB8C4",["rfp-analyst","rfp-radar","ideation-facilitator","idea-tournament","principal-investigator","proposal-writer","budget-officer","grants-compliance"]),
 ("Partnerships","#37C97E",["collaborator-scout","partnership-liaison","program-manager","convener"]),
 ("Faculty","#FF7AA8",["faculty-expert"]),
 ("Scouts","#19C0A6",["scout-prior-art","scout-methods","scout-landscape"]),
 ("Labs","#3D8BFF",["lab-theory","lab-methods","lab-domain","lab-statistics"]),
 ("Verification","#FF6B5E",["verify-rigor","verify-methodology","verify-evidence","verify-domain","referee"]),
 ("Execution","#16C079",["exec-experiments","exec-ablation","exec-iteration","research-engineer"]),
 ("Reporting","#E0B24A",["reporting-officer","deck-builder"]),
 ("Support","#E08A4A",["record-keeper","librarian","janitor","teaching-assistant","research-assistant","office-manager","data-steward","integrity-officer","figures","outreach","feedback-router","toolsmith"]),
 ("Governance","#9B8CFF",["research-conduct-officer"]),
]
try:
    cards={a["name"] for a in json.load(open(os.path.join(ROOT,"agent_cards.json")))["agents"]}
    missing=[m for _,_,mm in COUNCILS for m in mm if m not in cards]
    if missing: print("[gen_architecture] WARN missing in cards:", missing)
    total=len(cards)
except Exception:
    total=sum(len(m) for _,_,m in COUNCILS)
ncouncils=len(COUNCILS)
nagents=sum(len(m) for _,_,m in COUNCILS)

def esc(t): return t.replace("&","&amp;")
def two_lines(name):
    # split a hyphenated agent name into <=2 balanced lines
    parts=name.split("-")
    if len(parts)==1: return [name]
    # greedy: first line until ~half the chars
    half=len(name)/2; l1=parts[0]; i=1
    while i<len(parts) and len(l1)+1+len(parts[i])<=half+2:
        l1+="-"+parts[i]; i+=1
    l2="-".join(parts[i:]) if i<len(parts) else ""
    return [l1] if not l2 else [l1+"-", l2]

W=1000
pad=22
ncol=len(COUNCILS)
colgap=9
colw=(W-2*pad-(ncol-1)*colgap)/ncol
top=152
hdr_h=42
chip_h=30          # taller chip to hold 2 lines
chip_gap=6
maxagents=max(len(m) for _,_,m in COUNCILS)
col_body=maxagents*(chip_h+chip_gap)+8
H=top+hdr_h+12+col_body+40

s=[]
s.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H:.0f}" width="{W}" height="{H:.0f}" font-family="{FONT}" role="img" aria-label="Cambium architecture — one orchestrator, 11 councils, 46 agents">')
s.append('<defs>')
s.append(f'<linearGradient id="bgg" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="#07231A"/><stop offset="100%" stop-color="#0A2A1F"/></linearGradient>')
s.append('</defs>')
s.append(f'<rect width="{W}" height="{H:.0f}" fill="url(#bgg)"/>')

# faint background tree-ring arcs behind orchestrator
import math
for i,r in enumerate(range(40,150,18)):
    s.append(f'<circle cx="{W/2}" cy="103" r="{r}" fill="none" stroke="{ORCH}" stroke-width="1" opacity="{0.08+(i%2)*0.04:.2f}"/>')

s.append(f'<text x="{W/2}" y="40" text-anchor="middle" fill="{CANVAS}" font-size="24" font-weight="800">One Orchestrator &#183; {ncouncils} councils &#183; {nagents} specialist agents</text>')
s.append(f'<text x="{W/2}" y="62" text-anchor="middle" fill="{MUTED}" font-size="13">field-agnostic &#183; human-in-the-loop at every gate</text>')

ow=300; oh=46; ox=(W-ow)/2; oy=80
s.append(f'<rect x="{ox}" y="{oy}" width="{ow}" height="{oh}" rx="14" fill="{PANEL2}" stroke="{ORCH}" stroke-width="2.4"/>')
s.append(f'<circle cx="{ox+26}" cy="{oy+oh/2}" r="8" fill="{ORCH}"/>')
s.append(f'<text x="{W/2+8}" y="{oy+29}" text-anchor="middle" fill="{CANVAS}" font-size="17" font-weight="800">ORCHESTRATOR</text>')

for i,(name,hue,agents) in enumerate(COUNCILS):
    cx=pad+i*(colw+colgap); mx=cx+colw/2
    s.append(f'<path d="M {W/2} {oy+oh} C {W/2} {top-34}, {mx:.1f} {top-34}, {mx:.1f} {top}" fill="none" stroke="{hue}" stroke-width="1.4" opacity="0.5"/>')
    s.append(f'<rect x="{cx:.1f}" y="{top}" width="{colw:.1f}" height="{hdr_h}" rx="10" fill="{hue}"/>')
    s.append(f'<text x="{mx:.1f}" y="{top+18}" text-anchor="middle" fill="{INKE}" font-size="10.5" font-weight="800">{esc(name)}</text>')
    s.append(f'<text x="{mx:.1f}" y="{top+33}" text-anchor="middle" fill="{INKE}" font-size="9.5" font-weight="700" opacity="0.85">{len(agents)}</text>')
    ay=top+hdr_h+12
    for a in agents:
        s.append(f'<rect x="{cx:.1f}" y="{ay}" width="{colw:.1f}" height="{chip_h}" rx="7" fill="{PANEL}" stroke="{hue}" stroke-width="1"/>')
        lines=two_lines(a)
        if len(lines)==1:
            s.append(f'<text x="{mx:.1f}" y="{ay+19}" text-anchor="middle" fill="{CANVAS}" font-size="8.5" font-weight="600">{esc(lines[0])}</text>')
        else:
            s.append(f'<text x="{mx:.1f}" y="{ay+13}" text-anchor="middle" fill="{CANVAS}" font-size="8.5" font-weight="600">{esc(lines[0])}</text>')
            s.append(f'<text x="{mx:.1f}" y="{ay+24}" text-anchor="middle" fill="{CANVAS}" font-size="8.5" font-weight="600">{esc(lines[1])}</text>')
        ay+=chip_h+chip_gap

s.append(f'<text x="{W/2}" y="{H-16:.0f}" text-anchor="middle" fill="{MUTED}" font-size="11">colors = council hue (Living Layer) &#183; each chip is one named specialist agent</text>')
s.append('</svg>')
open(os.path.join(ROOT,"assets","architecture.svg"),"w").write("\n".join(s))
print("[gen_architecture] wrote assets/architecture.svg | councils=%d agents=%d cards=%d H=%.0f"%(ncouncils,nagents,total,H))
