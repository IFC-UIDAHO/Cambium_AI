#!/usr/bin/env python3
"""
gen_lifecycle.py - emit assets/lifecycle.svg

A richer lifecycle diagram than a bare gate line. It shows the eight
phases of a Cambium run, which councils act in each phase, and the human
gate that closes each phase. The structure lives in PHASES below, so the
picture stays a faithful map of the real workflow.

Run:  python3 tools/gen_lifecycle.py
The only output is assets/lifecycle.svg. No third-party dependencies.
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "lifecycle.svg")

# brand palette
BG = "#07231A"
INK = "#F4F7F2"
MUTED = "#8AA197"
PANEL = "#0E3326"
LINE = "#1F4D3B"
LIME = "#B7F36A"
GOLD = "#E0B24A"
GREEN = "#16C079"

# council hues
HUE = {
    "Orchestration": "#7C5CFF",
    "Pre-Award": "#2BB8C4",
    "Scouts": "#19C0A6",
    "Labs": "#3D8BFF",
    "Verification": "#FF6B5E",
    "Execution": "#16C079",
    "Reporting": "#E0B24A",
    "Support": "#E08A4A",
    "Governance": "#9B8CFF",
}

# one row per phase: name, subtitle, gate id, gate label, director-only?, councils
PHASES = [
    ("Intake",          "know the PI and RFP", "G0",  "intake",   False, ["Orchestration", "Support"]),
    ("Pre-Award",       "ideas, team, aims",   "G1",  "pursue?",  False, ["Pre-Award", "Scouts"]),
    ("Design",          "approach, budget",    "G2",  "approach", False, ["Pre-Award", "Labs"]),
    ("Submit",          "proposal final",      "G3",  "submit",   True,  ["Governance", "Orchestration"]),
    ("Build / Run-Lab", "run the work",        "G3a", "budget",   False, ["Labs", "Execution"]),
    ("Verify",          "reproduce numbers",   "G4",  "accept",   False, ["Verification"]),
    ("Report",          "findings, deck",      "G5",  "release",  False, ["Reporting", "Support"]),
    ("Publish",         "release, closeout",   "G6",  "publish",  False, ["Governance", "Reporting"]),
]

W, H = 1080, 412
LEFT, RIGHT = 40, 1040
COL = (RIGHT - LEFT) / len(PHASES)            # 125
CENTERS = [int(LEFT + COL / 2 + i * COL) for i in range(len(PHASES))]


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build():
    p = []
    p.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
        f'font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,Helvetica,Arial,sans-serif" '
        f'role="img" aria-label="The Cambium research lifecycle: eight phases (Intake, '
        f'Pre-Award, Design, Submit, Build/Run-Lab, Verify, Report, Publish), each showing the '
        f'councils that act in it and the human gate that closes it. A named person signs every gate.">'
    )
    p.append('<defs>')
    p.append('<linearGradient id="lbg" x1="0" y1="0" x2="0" y2="1">'
             '<stop offset="0%" stop-color="#0b2c20"/><stop offset="100%" stop-color="#07231a"/></linearGradient>')
    p.append('<linearGradient id="flow" x1="0" y1="0" x2="1" y2="0">'
             '<stop offset="0%" stop-color="#16C079"/><stop offset="100%" stop-color="#B7F36A"/></linearGradient>')
    p.append('</defs>')

    p.append(f'<rect width="{W}" height="{H}" rx="18" fill="url(#lbg)"/>')
    p.append(f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="17" fill="none" stroke="{LINE}"/>')

    # title
    p.append(f'<text x="40" y="38" font-size="24" font-weight="800" fill="{INK}">The Cambium research lifecycle</text>')
    p.append(f'<text x="40" y="60" font-size="13" fill="{MUTED}">Eight human gates. A named person signs each one before work proceeds.</text>')

    # flow line
    p.append(f'<line x1="{LEFT}" y1="206" x2="{RIGHT}" y2="206" stroke="url(#flow)" stroke-width="5" stroke-linecap="round"/>')

    # phase blocks + arrows
    for i, (name, sub, *_rest) in enumerate(PHASES):
        c = CENTERS[i]
        x = c - 56
        p.append(f'<rect x="{x}" y="84" width="112" height="72" rx="12" fill="{PANEL}" stroke="{LINE}"/>')
        p.append(f'<text x="{c}" y="116" text-anchor="middle" font-size="13" font-weight="700" fill="{INK}">{esc(name)}</text>')
        p.append(f'<text x="{c}" y="135" text-anchor="middle" font-size="9.5" fill="{MUTED}">{esc(sub)}</text>')
        if i < len(PHASES) - 1:
            midx = (CENTERS[i] + CENTERS[i + 1]) / 2
            p.append(f'<text x="{midx}" y="126" text-anchor="middle" font-size="17" fill="{GREEN}">&#8250;</text>')

    # gate badges on the line + labels
    for i, (_n, _s, gid, glabel, director, _co) in enumerate(PHASES):
        c = CENTERS[i]
        fill = GOLD if director else LIME
        stroke = "#9C7A1E" if director else "#0B2E22"
        p.append(f'<rect x="{c-24}" y="194" width="48" height="24" rx="7" fill="{fill}" stroke="{stroke}"/>')
        p.append(f'<text x="{c}" y="210" text-anchor="middle" font-size="11" font-weight="800" fill="#062013">{esc(gid)}</text>')
        p.append(f'<text x="{c}" y="240" text-anchor="middle" font-size="11.5" fill="{INK}">{esc(glabel)}</text>')
        if director:
            p.append(f'<text x="{c}" y="254" text-anchor="middle" font-size="9" font-weight="700" fill="{GOLD}">Director only</text>')

    # council band
    p.append(f'<text x="40" y="284" font-size="10" letter-spacing="1.5" fill="{MUTED}">WHO ACTS IN EACH PHASE</text>')
    for i, (_n, _s, _g, _l, _d, councils) in enumerate(PHASES):
        c = CENTERS[i]
        n = len(councils)
        # one pill centered, or two stacked
        ys = [302] if n == 1 else [294, 320]
        for j, council in enumerate(councils):
            hue = HUE[council]
            y = ys[j]
            p.append(f'<rect x="{c-54}" y="{y}" width="108" height="22" rx="11" fill="{hue}" fill-opacity="0.15" stroke="{hue}" stroke-opacity="0.6"/>')
            p.append(f'<text x="{c}" y="{y+15}" text-anchor="middle" font-size="9.5" font-weight="700" fill="{hue}">{esc(council)}</text>')

    # legend
    ly = 364
    p.append(f'<rect x="40" y="{ly-12}" width="16" height="14" rx="4" fill="{LIME}"/>')
    p.append(f'<text x="62" y="{ly}" font-size="11.5" fill="{MUTED}">human gate</text>')
    p.append(f'<rect x="178" y="{ly-12}" width="16" height="14" rx="4" fill="{GOLD}"/>')
    p.append(f'<text x="200" y="{ly}" font-size="11.5" fill="{MUTED}">Director-only gate</text>')
    p.append(f'<rect x="350" y="{ly-12}" width="16" height="14" rx="7" fill="{HUE["Scouts"]}" fill-opacity="0.2" stroke="{HUE["Scouts"]}"/>')
    p.append(f'<text x="372" y="{ly}" font-size="11.5" fill="{MUTED}">council acting in this phase</text>')

    # honest footer
    p.append(f'<text x="40" y="396" font-size="11" fill="#6f8a7e">Gates are prompt-level and token-checked, not a hard OS lock. The point is that a person decides at each one.</text>')

    p.append('</svg>')
    return "\n".join(p)


def main():
    svg = build()
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(svg)
    assert chr(0x2014) not in svg, "em dash found in lifecycle.svg"
    print(f"[gen_lifecycle] wrote {os.path.relpath(OUT, ROOT)} ({len(PHASES)} phases)")


if __name__ == "__main__":
    main()
