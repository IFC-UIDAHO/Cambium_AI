#!/usr/bin/env python3
"""Cambium 'AI Research Institution' emblem · vector recreation of the uploaded ring+node-network logo,
TRANSPARENT background. Wood-ring tree cross-section (green->teal->gold), a gold neural/branch node-network
in one quadrant, a glowing active blip, leaves, and an open arc frame. + CAMBIUM AI wordmark."""
import os, math, random, cairosvg
OUT=os.environ.get("OUT","/tmp/ringlogo"); os.makedirs(OUT,exist_ok=True)
BG="#07231A";PANEL="#0E3326";LINE="#1F4D3B"
DEEP="#0B2E22";GREEN="#1B5E20";EMER="#16C079";TEAL="#19C0A6";GOLD="#E0B24A";GOLD_L="#F6D88A"
LIME="#B7F36A";INK="#15302B";MIST="#7E948B";CANVAS="#F4F7F2"
FONT="Inter,'DejaVu Sans',sans-serif"
def P(x): return f"{x:.2f}"
def lerp(a,b,t):
    a=[int(a[i:i+2],16) for i in (1,3,5)]; b=[int(b[i:i+2],16) for i in (1,3,5)]
    return "#%02x%02x%02x"%tuple(int(a[i]+(b[i]-a[i])*t) for i in range(3))

def emblem(cx,cy,R):
    s=[f'<g>']
    # base disc (subtle radial)
    s.append(f'<circle cx="{P(cx)}" cy="{P(cy)}" r="{P(R)}" fill="url(#disc)"/>')
    # concentric wood rings: deep green -> emerald -> teal -> gold band -> green
    n=22
    for i in range(n):
        r=R*(0.07+0.92*i/(n-1)); t=i/(n-1)
        if t<0.5: col=lerp(DEEP,TEAL,t/0.5)
        elif t<0.72: col=lerp(TEAL,GOLD,(t-0.5)/0.22)
        else: col=lerp(GOLD,GREEN,(t-0.72)/0.28)
        sw=R*(0.012+0.006*math.sin(i*1.3))
        s.append(f'<circle cx="{P(cx)}" cy="{P(cy)}" r="{P(r)}" fill="none" stroke="{col}" stroke-width="{P(sw)}" opacity="{0.85 if t<0.72 else 0.9}"/>')
    # clip the network/leaves to the disc edge softly via the disc only (no hard clip)
    # --- gold node-network in the upper-right quadrant ---
    random.seed(5)
    pts=[]
    for _ in range(13):
        ang=math.radians(random.uniform(-15,80)); rr=R*random.uniform(0.18,0.9)
        pts.append((cx+rr*math.cos(ang), cy-rr*math.sin(ang)))
    # edges: connect each to nearest 2
    for i,(x,y) in enumerate(pts):
        d=sorted(range(len(pts)), key=lambda j:(x-pts[j][0])**2+(y-pts[j][1])**2)
        for j in d[1:3]:
            s.append(f'<line x1="{P(x)}" y1="{P(y)}" x2="{P(pts[j][0])}" y2="{P(pts[j][1])}" stroke="{GOLD}" stroke-width="{P(R*0.012)}" opacity="0.9"/>')
    for x,y in pts:
        s.append(f'<circle cx="{P(x)}" cy="{P(y)}" r="{P(R*0.027)}" fill="{GOLD_L}"/>')
        s.append(f'<circle cx="{P(x)}" cy="{P(y)}" r="{P(R*0.022)}" fill="none" stroke="{GOLD}" stroke-width="{P(R*0.006)}"/>')
    # --- glowing active blip (center-left) ---
    bx,by=cx-R*0.22, cy-R*0.04
    s.append(f'<circle cx="{P(bx)}" cy="{P(by)}" r="{P(R*0.16)}" fill="url(#blip)"/>')
    s.append(f'<circle cx="{P(bx)}" cy="{P(by)}" r="{P(R*0.04)}" fill="{GOLD_L}"/>')
    # small inner radar arcs near blip
    for rr in [0.10,0.17,0.24]:
        s.append(f'<circle cx="{P(bx)}" cy="{P(by)}" r="{P(R*rr)}" fill="none" stroke="{GOLD_L}" stroke-width="{P(R*0.006)}" opacity="{0.5-rr}"/>')
    s.append('</g>')
    # --- open arc frame (green->gold), drawn around outside ---
    fr=R*1.16
    def arc(a0,a1,grad):
        x0,y0=cx+fr*math.cos(math.radians(a0)),cy+fr*math.sin(math.radians(a0))
        x1,y1=cx+fr*math.cos(math.radians(a1)),cy+fr*math.sin(math.radians(a1))
        large=1 if (a1-a0)%360>180 else 0
        return f'<path d="M{P(x0)} {P(y0)} A {P(fr)} {P(fr)} 0 {large} 1 {P(x1)} {P(y1)}" fill="none" stroke="{grad}" stroke-width="{P(R*0.03)}" stroke-linecap="round"/>'
    s.append(arc(150,35,"url(#arc)"))      # one clean open ring, gap lower-right
    # --- two leaves at top-right edge ---
    lx,ly=cx+R*0.78, cy-R*0.72
    def leaf(x,y,rot,sc):
        return (f'<g transform="translate({P(x)},{P(y)}) rotate({rot}) scale({sc})">'
                f'<path d="M0 0 Q 14 -10 26 -2 Q 16 8 0 0 Z" fill="{EMER}"/>'
                f'<path d="M2 -1 Q 14 -4 24 -2" fill="none" stroke="{LIME}" stroke-width="1.2" opacity="0.7"/></g>')
    s.append(leaf(lx,ly,-18,R*0.011))
    s.append(leaf(lx+R*0.10,ly-R*0.05,-48,R*0.009))
    return "\n".join(s)

DEFS=f'''<defs>
 <radialGradient id="disc" cx="42%" cy="40%" r="60%"><stop offset="0%" stop-color="{TEAL}" stop-opacity="0.25"/><stop offset="60%" stop-color="{PANEL}" stop-opacity="0.9"/><stop offset="100%" stop-color="{DEEP}"/></radialGradient>
 <radialGradient id="blip" cx="50%" cy="50%" r="50%"><stop offset="0%" stop-color="{GOLD_L}" stop-opacity="0.95"/><stop offset="35%" stop-color="{GOLD}" stop-opacity="0.5"/><stop offset="100%" stop-color="{GOLD}" stop-opacity="0"/></radialGradient>
 <linearGradient id="arc" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="{EMER}"/><stop offset="100%" stop-color="{GOLD}"/></linearGradient>
 <linearGradient id="arc2" x1="1" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="{GOLD}"/><stop offset="100%" stop-color="{EMER}"/></linearGradient>
</defs>'''

def lockup(dark=False, W=1024, H=580):
    from PIL import ImageFont
    txt = CANVAS if dark else "#15322C"
    sub = "#9FB3AA" if dark else "#5C7068"
    cx,cy,R=W/2, 236, 172
    # measure to center wordmark + place leaf at the end of the subtitle
    fxb=ImageFont.truetype("/sessions/brave-jolly-brahmagupta/.fonts/Inter-ExtraBold.ttf",60)
    fsb=ImageFont.truetype("/sessions/brave-jolly-brahmagupta/.fonts/Inter-SemiBold.ttf",22)
    sub_txt="RESEARCH INSTITUTION"; track=8
    subw=fsb.getlength(sub_txt)+track*(len(sub_txt)-1)
    leafx=W/2+subw/2+22
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}">{DEFS}
 {emblem(cx,cy,R)}
 <text x="{W/2}" y="492" text-anchor="middle" font-family="{FONT}" font-weight="800" font-size="60" letter-spacing="2" fill="{txt}">CAMBIUM AI</text>
 <text x="{W/2}" y="532" text-anchor="middle" font-family="{FONT}" font-weight="600" font-size="22" letter-spacing="{track}" fill="{sub}">{sub_txt}</text>
 <g transform="translate({leafx},525) rotate(-22) scale(1.05)"><path d="M0 0 Q 12 -9 22 -1 Q 13 7 0 0 Z" fill="{EMER}"/><path d="M3 -1 Q 12 -4 20 -1" fill="none" stroke="{LIME}" stroke-width="1.1" opacity="0.7"/></g>
</svg>'''

def mark(S=512):
    cx,cy,R=S/2,S/2,S*0.40
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {S} {S}">{DEFS}{emblem(cx,cy,R)}</svg>'

for name,svg,w,h in [("logo",lockup(False),1024,560),("logo-dark",lockup(True),1024,560)]:
    open(f"{OUT}/{name}.svg","w").write(svg)
    cairosvg.svg2png(bytestring=svg.encode(),write_to=f"{OUT}/{name}.png",output_width=2048,output_height=int(2048*h/w))
open(f"{OUT}/logo-mark.svg","w").write(mark(512))
cairosvg.svg2png(bytestring=mark(512).encode(),write_to=f"{OUT}/logo-mark.png",output_width=1024,output_height=1024)


def social(W=1280,H=640):
    import random as _r
    _r.seed(7); nodes=[(_r.uniform(60,W-60),_r.uniform(50,H-50)) for _ in range(22)]
    con=['<g opacity="0.08">']
    for i,(x,y) in enumerate(nodes):
        bj=min((j for j in range(len(nodes)) if j!=i), key=lambda j:(x-nodes[j][0])**2+(y-nodes[j][1])**2)
        con.append(f'<line x1="{x:.0f}" y1="{y:.0f}" x2="{nodes[bj][0]:.0f}" y2="{nodes[bj][1]:.0f}" stroke="{EMER}" stroke-width="1"/>')
    con+=[f'<circle cx="{x:.0f}" cy="{y:.0f}" r="2.2" fill="{EMER}"/>' for x,y in nodes]; con.append('</g>')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}">{DEFS}
 <rect width="{W}" height="{H}" fill="{BG}"/><rect width="{W}" height="{H}" fill="url(#disc)" opacity="0.5"/>
 {''.join(con)}
 <rect x="20" y="20" width="{W-40}" height="{H-40}" rx="28" fill="none" stroke="{LINE}" stroke-width="1.5" opacity="0.8"/>
 {emblem(300,322,170)}
 <text x="560" y="300" font-family="{FONT}" font-weight="800" font-size="96" letter-spacing="2" fill="{CANVAS}">CAMBIUM<tspan fill="{GOLD_L}"> AI</tspan></text>
 <text x="560" y="346" font-family="{FONT}" font-weight="600" font-size="27" letter-spacing="6" fill="#9FB3AA">RESEARCH INSTITUTION</text>
 <text x="560" y="414" font-family="{FONT}" font-weight="500" font-size="26" fill="{MIST}">A research institution you run with one sentence ·</text>
 <text x="560" y="450" font-family="{FONT}" font-weight="500" font-size="26" fill="{MIST}">RFP to verified results, human-in-the-loop.</text>
 <g font-family="{FONT}" font-weight="700" font-size="31">
  <text x="560" y="522" fill="{EMER}">46<tspan fill="{CANVAS}" font-weight="600"> agents</tspan></text>
  <text x="730" y="522" fill="#5C7068" font-weight="400">·</text>
  <text x="756" y="522" fill="{EMER}">11<tspan fill="{CANVAS}" font-weight="600"> councils</tspan></text>
  <text x="956" y="522" fill="#5C7068" font-weight="400">·</text>
  <text x="982" y="522" fill="{GOLD_L}">8<tspan fill="{CANVAS}" font-weight="600"> gates</tspan></text>
 </g>
 <text x="560" y="582" font-family="{FONT}" font-weight="500" font-size="21" fill="{EMER}" letter-spacing="1" opacity="0.8">MIT · open source · runs in your Claude · the Cambium way</text>
</svg>'''

def favicon(S=64):
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {S} {S}">{DEFS}<rect width="{S}" height="{S}" rx="{S*0.22}" fill="{BG}"/>{emblem(S/2,S/2,S*0.40)}</svg>'

if True:
    open(f"{OUT}/social-preview.svg","w").write(social())
    cairosvg.svg2png(bytestring=social().encode(),write_to=f"{OUT}/social-preview.png",output_width=1280,output_height=640)
    open(f"{OUT}/favicon.svg","w").write(favicon(64))
    cairosvg.svg2png(bytestring=favicon(64).encode(),write_to=f"{OUT}/favicon.png",output_width=180,output_height=180)
    print("social+favicon done")

print("done")
