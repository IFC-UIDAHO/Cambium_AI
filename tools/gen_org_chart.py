#!/usr/bin/env python3
"""Generate assets/org-chart.svg from agent_cards.json (so the count is never stale).
Usage: python3 tools/gen_org_chart.py   (run gen_agent_cards.py first)
"""
import os, json, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
cards = {a["name"]: a for a in json.load(open(os.path.join(ROOT,"agent_cards.json")))["agents"]}

# council -> ordered agent names (single source of truth for grouping)
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
placed = sum(len(a) for _,_,a in COUNCILS)
total = len(cards)
W=980; pad=22; x0=pad; y=70; chipw=150; chiph=26; gapx=10; gapy=8; perrow=(W-2*pad)//(chipw+gapx)
rows=[]
rows.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="HEIGHT" font-family="DejaVu Sans, Arial, sans-serif">')
rows.append(f'<rect width="{W}" height="HEIGHT" fill="#07231A"/>')
rows.append(f'<text x="{W//2}" y="38" text-anchor="middle" font-size="22" font-weight="700" fill="#16C079">Cambium — {total} agents · {len(COUNCILS)} councils</text>')
for cname,col,members in COUNCILS:
    rows.append(f'<text x="{x0}" y="{y}" font-size="13" font-weight="700" fill="{col}">{cname} ({len(members)})</text>')
    y+=12
    cx=x0; cy=y; n=0
    for m in members:
        nm = m if m in cards else m+" (?)"
        rows.append(f'<rect x="{cx}" y="{cy}" width="{chipw}" height="{chiph}" rx="6" fill="{col}22" stroke="{col}66"/>')
        rows.append(f'<text x="{cx+8}" y="{cy+17}" font-size="11" fill="#F4F7F2">{nm}</text>')
        n+=1; cx+=chipw+gapx
        if n%perrow==0: cx=x0; cy+=chiph+gapy
    rows_used = (len(members)+perrow-1)//perrow
    y = cy + (chiph+gapy if len(members)%perrow else 0) + (chiph+gapy)*0 + 18
    if len(members)%perrow!=0: y=cy+chiph+gapy+10
    else: y=cy+10
H=int(y+30)
svg="\n".join(rows).replace("HEIGHT",str(H))
svg+=f'\n<text x="{W//2}" y="{H-10}" text-anchor="middle" font-size="10" fill="#8AA197">Cambium · {len(COUNCILS)} councils · {total} agents · field-agnostic · human-in-the-loop at every gate</text>\n</svg>'
open(os.path.join(ROOT,"assets","org-chart.svg"),"w").write(svg)
missing=[m for _,_,mm in COUNCILS for m in mm if m not in cards]
if missing:
    print("[gen_org_chart] MISSING ROSTER NAME(S) (not in agent_cards.json): %s" % ", ".join(missing)); sys.exit(1)
print("[gen_org_chart] wrote assets/org-chart.svg | councils=%d placed=%d total_cards=%d %s"%(len(COUNCILS),placed,total,"OK" if placed==total else "MISMATCH!"))
