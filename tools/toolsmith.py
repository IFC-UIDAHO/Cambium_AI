#!/usr/bin/env python3
"""Toolsmith registry — recommend existing tools for a task (reuse beats rebuild).

A curated, extensible baseline; the Toolsmith AGENT augments this with live web search. Emits a
provisioning manifest (install commands + license/maintenance flags). Installs only after human
approval (see TOOL_POLICY.md).

Usage: python3 tools/toolsmith.py "build a 3d web app"
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import task_router

def T(name, kind, install, why, license="check", note="verify currency"):
    return {"name": name, "kind": kind, "install": install, "why": why, "license": license, "note": note}

# task-type -> recommended stack (verify currency before installing)
STACKS = {
 "software": [
   T("vite","build","npm create vite@latest","fast dev/build for modern web apps","MIT"),
   T("tailwindcss","css","npm i -D tailwindcss","utility CSS, fast theming","MIT"),
   T("shadcn/ui","components","npx shadcn@latest init","accessible React components (Radix)","MIT"),
   T("21st.dev","components","via Magic MCP / web","community UI component marketplace","mixed"),
   T("motion (Framer Motion)","animation","npm i motion","production animation/gestures","MIT"),
   T("three / react-three-fiber","3d","npm i three @react-three/fiber","WebGL 3D scenes","MIT"),
   T("@modelcontextprotocol Magic MCP","mcp","add via MCP registry","pull UI components into the editor","check"),
   T("ui-ux-pro-max","skill","Cambium skill (installed)","design-system + a11y guidance","-","present"),
 ],
 "data": [
   T("pandas","pip","pip install pandas","dataframes","BSD"),
   T("duckdb","pip","pip install duckdb","fast local analytical SQL","MIT"),
   T("polars","pip","pip install polars","fast dataframes","MIT"),
   T("plotly","viz","pip install plotly","interactive charts","MIT"),
 ],
 "research": [
   T("numpy/scipy/scikit-learn","pip","pip install numpy scipy scikit-learn","core scientific stack","BSD"),
   T("statsmodels","pip","pip install statsmodels","statistical models + inference","BSD"),
   T("arxiv / semantic-scholar API","api","free API","prior-art + citation resolution","open"),
 ],
 "report": [
   T("python-pptx / docx","pip","pip install python-pptx python-docx","decks + documents","MIT"),
   T("Cambium pptx/docx skills","skill","installed","formatted deliverables","-","present"),
 ],
}
# review / grant: mostly reuse existing repo tooling; minimal new installs
STACKS["review"] = [T("ruff","pip","pip install ruff","fast lint","MIT"), T("mypy","pip","pip install mypy","type check","MIT"), T("pytest","pip","pip install pytest","tests","MIT"), T("bandit","pip","pip install bandit","security lint","Apache-2.0")]
STACKS["grant"] = [T("Cambium grants-compliance + budget-officer","agent","installed","forms/budget","-","present"), T("semantic-scholar API","api","free API","prior-art","open")]
STACKS["design"] = [
 T("brand-guidelines","skill","Cambium skill (installed)","brand colors + typography system","-","present"),
 T("canvas-design","skill","Cambium skill (installed)","posters/PNG/PDF visual design","-","present"),
 T("ckmdesign / ckmbanner-design","skill","Cambium skill (installed)","logos, banners, social images","-","present"),
 T("theme-factory","skill","Cambium skill (installed)","themeable color/font systems","-","present"),
 T("ui-ux-pro-max","skill","Cambium skill (installed)","UI/UX styles, palettes, font pairings","-","present"),
 T("cairosvg","pip","pip install cairosvg","render SVG -> PNG","LGPL"),
 T("Pillow","pip","pip install Pillow","raster image generation","HPND"),
]
# visual-design keywords route to the design stack (skills, not stats packages)
DESIGN_KW = ("logo","brand","branding","poster","banner","icon","palette","svg","mockup",
             "wordmark","visual identity","social card","favicon","illustration","design system","theme the")

def manifest(task):
    tl = task.lower()
    if any(k in tl for k in DESIGN_KW):
        typ = "design"
    else:
        typ, _ = task_router.classify(task)
    stack = STACKS.get(typ, STACKS["research"])
    return {"task": task, "type": typ, "recommended": stack,
            "policy": "Human approves at the provisioning gate before any install (TOOL_POLICY.md).",
            "principle": "reuse beats rebuild; pin versions; verify currency; check licenses"}

if __name__ == "__main__":
    t = " ".join(sys.argv[1:]) or "build a web app"
    m = manifest(t)
    print("TASK:", t, "| type:", m["type"])
    print("Recommended (verify before install; human-gated):")
    for x in m["recommended"]:
        print("  - %-28s [%s] %s   (%s)" % (x["name"], x["kind"], x["install"], x["license"]))
    print("\nPolicy:", m["policy"])
