#!/usr/bin/env python3
"""Generate assets/architecture.svg - Orchestrator -> 11 councils -> 46 agents.
Dimensional org-chart: gradient council headers with count badges, raised agent
chips with a hue dot each, a glowing orchestrator, smoother connectors.
Roster mirrors tools/gen_org_chart.py (single source of truth, re-stated + verified).
Usage: python3 assets/gen/gen_architecture.py
"""
import os, json
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FONT = "Inter, 'Segoe UI', 'DejaVu Sans', Arial, sans-serif"
PANEL2 = "#15402F"; CANVAS = "#F4F7F2"; MUTED = "#8AA197"; ORCH = "#7C5CFF"

COUNCILS = [
 ("Orchestration", "#7C5CFF", ["orchestrator", "document-office"]),
 ("Pre-Award", "#2BB8C4", ["rfp-analyst", "rfp-radar", "ideation-facilitator", "idea-tournament", "principal-investigator", "proposal-writer", "budget-officer", "grants-compliance"]),
 ("Partnerships", "#37C97E", ["collaborator-scout", "partnership-liaison", "program-manager", "convener"]),
 ("Faculty", "#FF7AA8", ["faculty-expert"]),
 ("Scouts", "#19C0A6", ["scout-prior-art", "scout-methods", "scout-landscape"]),
 ("Labs", "#3D8BFF", ["lab-theory", "lab-methods", "lab-domain", "lab-statistics"]),
 ("Verification", "#FF6B5E", ["verify-rigor", "verify-methodology", "verify-evidence", "verify-domain", "referee"]),
 ("Execution", "#16C079", ["exec-experiments", "exec-ablation", "exec-iteration", "research-engineer"]),
 ("Reporting", "#E0B24A", ["reporting-officer", "deck-builder"]),
 ("Support", "#E08A4A", ["record-keeper", "librarian", "janitor", "teaching-assistant", "research-assistant", "office-manager", "data-steward", "integrity-officer", "figures", "outreach", "feedback-router", "toolsmith"]),
 ("Governance", "#9B8CFF", ["research-conduct-officer"]),
]
try:
    cards = {a["name"] for a in json.load(open(os.path.join(ROOT, "agent_cards.json")))["agents"]}
    missing = [m for _, _, mm in COUNCILS for m in mm if m not in cards]
    if missing:
        print("[gen_architecture] WARN missing in cards:", missing)
    total = len(cards)
except Exception:
    total = sum(len(m) for _, _, m in COUNCILS)

ncouncils = len(COUNCILS)
nagents = sum(len(m) for _, _, m in COUNCILS)


def esc(t):
    return t.replace("&", "&amp;")


def dk(h, f):
    h = h.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return "#%02x%02x%02x" % (int(r * f), int(g * f), int(b * f))


def two_lines(name):
    parts = name.split("-")
    if len(parts) == 1:
        return [name]
    half = len(name) / 2
    l1 = parts[0]
    i = 1
    while i < len(parts) and len(l1) + 1 + len(parts[i]) <= half + 2:
        l1 += "-" + parts[i]
        i += 1
    l2 = "-".join(parts[i:]) if i < len(parts) else ""
    return [l1] if not l2 else [l1 + "-", l2]


W = 1000
pad = 22
ncol = ncouncils
colgap = 9
colw = (W - 2 * pad - (ncol - 1) * colgap) / ncol
top = 158
hdr_h = 46
chip_h = 32
chip_gap = 7
maxa = max(len(m) for _, _, m in COUNCILS)
H = top + hdr_h + 14 + maxa * (chip_h + chip_gap) + 8 + 44

s = []
s.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H:.0f}" width="{W}" height="{H:.0f}" font-family="{FONT}" role="img" aria-label="Cambium architecture: one orchestrator, 11 councils, 46 named agents">')
s.append('<defs>')
s.append('<radialGradient id="bgg" cx="50%" cy="13%" r="95%"><stop offset="0%" stop-color="#0d3a29"/><stop offset="52%" stop-color="#07231a"/><stop offset="100%" stop-color="#051911"/></radialGradient>')
s.append('<linearGradient id="orch" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="#8f78ff"/><stop offset="55%" stop-color="#7C5CFF"/><stop offset="100%" stop-color="#19C0A6"/></linearGradient>')
s.append('<linearGradient id="chip" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#15402F"/><stop offset="100%" stop-color="#0c2c20"/></linearGradient>')
s.append('<filter id="ds" x="-25%" y="-25%" width="150%" height="170%"><feDropShadow dx="0" dy="2.2" stdDeviation="3" flood-color="#000" flood-opacity="0.5"/></filter>')
s.append('<filter id="glow" x="-80%" y="-80%" width="260%" height="260%"><feGaussianBlur stdDeviation="7" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>')
s.append('<filter id="soft" x="-90%" y="-90%" width="280%" height="280%"><feGaussianBlur stdDeviation="13"/></filter>')
for i, (n, hue, a) in enumerate(COUNCILS):
    s.append(f'<linearGradient id="h{i}" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="{hue}"/><stop offset="100%" stop-color="{dk(hue, 0.72)}"/></linearGradient>')
s.append('</defs>')
s.append(f'<rect width="{W}" height="{H:.0f}" fill="url(#bgg)"/>')
for i, r in enumerate(range(46, 170, 20)):
    s.append(f'<circle cx="{W/2}" cy="108" r="{r}" fill="none" stroke="{ORCH}" stroke-width="1" opacity="{0.10-(i*0.012):.3f}"/>')
s.append(f'<text x="{W/2}" y="42" text-anchor="middle" fill="{CANVAS}" font-size="25" font-weight="800" letter-spacing="-0.3">One Orchestrator &#183; {ncouncils} councils &#183; {nagents} specialist agents</text>')
s.append(f'<text x="{W/2}" y="66" text-anchor="middle" fill="{MUTED}" font-size="13" letter-spacing="0.3">field-agnostic &#183; human-in-the-loop at every gate</text>')
oy = 84
oh = 50
ow = 320
ox = (W - ow) / 2
for i, (n, hue, a) in enumerate(COUNCILS):
    cx = pad + i * (colw + colgap)
    mx = cx + colw / 2
    s.append(f'<path d="M {W/2} {oy+oh} C {W/2} {top-40}, {mx:.1f} {top-40}, {mx:.1f} {top}" fill="none" stroke="{hue}" stroke-width="1.8" opacity="0.5"/>')
    s.append(f'<circle cx="{mx:.1f}" cy="{top}" r="2.6" fill="{hue}"/>')
s.append(f'<rect x="{ox-6}" y="{oy-6}" width="{ow+12}" height="{oh+12}" rx="18" fill="{ORCH}" opacity="0.22" filter="url(#soft)"/>')
s.append(f'<g filter="url(#glow)"><rect x="{ox}" y="{oy}" width="{ow}" height="{oh}" rx="15" fill="{PANEL2}" stroke="url(#orch)" stroke-width="2.6"/></g>')
hx = ox + 32
hy = oy + oh / 2
s.append(f'<polygon points="{hx},{hy-15} {hx+13},{hy-7.5} {hx+13},{hy+7.5} {hx},{hy+15} {hx-13},{hy+7.5} {hx-13},{hy-7.5}" fill="#0E3326" stroke="url(#orch)" stroke-width="2"/>')
s.append(f'<path d="M {hx+5} {hy-6} A 8 8 0 1 0 {hx+5} {hy+6}" fill="none" stroke="url(#orch)" stroke-width="2.4" stroke-linecap="round"/>')
s.append(f'<text x="{W/2+14}" y="{oy+31}" text-anchor="middle" fill="{CANVAS}" font-size="18" font-weight="800" letter-spacing="1.5">ORCHESTRATOR</text>')
for i, (name, hue, agents) in enumerate(COUNCILS):
    cx = pad + i * (colw + colgap)
    mx = cx + colw / 2
    s.append(f'<rect x="{cx:.1f}" y="{top}" width="{colw:.1f}" height="{hdr_h}" rx="11" fill="{hue}" opacity="0.28" filter="url(#soft)"/>')
    s.append(f'<rect x="{cx:.1f}" y="{top}" width="{colw:.1f}" height="{hdr_h}" rx="11" fill="url(#h{i})" stroke="{dk(hue,0.6)}" stroke-width="0.8" filter="url(#ds)"/>')
    s.append(f'<rect x="{cx+3:.1f}" y="{top+2}" width="{colw-6:.1f}" height="2.5" rx="1.2" fill="#ffffff" opacity="0.28"/>')
    s.append(f'<text x="{mx:.1f}" y="{top+20}" text-anchor="middle" fill="#0a1f14" font-size="10.5" font-weight="800">{esc(name)}</text>')
    by = top + 34
    s.append(f'<circle cx="{mx:.1f}" cy="{by}" r="8.5" fill="#0a1f14" opacity="0.55"/>')
    s.append(f'<text x="{mx:.1f}" y="{by+3.4}" text-anchor="middle" fill="#ffffff" font-size="10" font-weight="800">{len(agents)}</text>')
    ay = top + hdr_h + 14
    for a in agents:
        s.append(f'<rect x="{cx:.1f}" y="{ay}" width="{colw:.1f}" height="{chip_h}" rx="8" fill="url(#chip)" stroke="{hue}" stroke-width="1.1" stroke-opacity="0.7" filter="url(#ds)"/>')
        s.append(f'<rect x="{cx+3:.1f}" y="{ay+1.5}" width="{colw-6:.1f}" height="1.6" rx="0.8" fill="#ffffff" opacity="0.10"/>')
        s.append(f'<circle cx="{cx+9:.1f}" cy="{ay+chip_h/2}" r="2.6" fill="{hue}"/>')
        lines = two_lines(a)
        tx = mx + 4
        if len(lines) == 1:
            s.append(f'<text x="{tx:.1f}" y="{ay+chip_h/2+3.2:.1f}" text-anchor="middle" fill="{CANVAS}" font-size="8.6" font-weight="600">{esc(lines[0])}</text>')
        else:
            s.append(f'<text x="{tx:.1f}" y="{ay+13}" text-anchor="middle" fill="{CANVAS}" font-size="8.6" font-weight="600">{esc(lines[0])}</text>')
            s.append(f'<text x="{tx:.1f}" y="{ay+24}" text-anchor="middle" fill="{CANVAS}" font-size="8.6" font-weight="600">{esc(lines[1])}</text>')
        ay += chip_h + chip_gap
s.append(f'<text x="{W/2}" y="{H-16:.0f}" text-anchor="middle" fill="{MUTED}" font-size="11">colors = council hue &#183; each chip is one named specialist agent &#183; the verification board is independent</text>')
s.append('</svg>')
open(os.path.join(ROOT, "assets", "architecture.svg"), "w").write("\n".join(s))
print("[gen_architecture] wrote assets/architecture.svg | councils=%d agents=%d cards=%d H=%.0f" % (ncouncils, nagents, total, H))
