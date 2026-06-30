#!/usr/bin/env python3
"""gen_capabilities.py -- auto-generate assets/capabilities.svg and assets/adopted-ideas.svg
from live repo data and a data file.

Usage:
    python3 tools/gen_capabilities.py            # regenerate both assets
    python3 tools/gen_capabilities.py --check    # exit 1 if either SVG differs from a fresh regen

Count sources:
    agents   : agent_cards.json["count"]  (fallback: .claude/agents/*.md with frontmatter)
    councils : len(task_router.CMAP)  (parsed from tools/task_router.py)
    gates    : consistency_check.GATES constant (parsed from tools/consistency_check.py)
    tools    : count of *.py files in tools/
    skills   : count of skills/*/SKILL.md directories
    tests    : count of "def test_" lines across tests/*.py

Data file for adopted ideas: assets/adopted_ideas.json
    list of {"source","meta","built","note","status"}
    status: "adopted" | "declined-heavy" | "roadmap"

Pure stdlib only (json, glob, os, re, argparse, sys, pathlib).
No em dashes in generated output.
"""

import argparse
import glob
import json
import os
import re
import sys
import pathlib

import cambium_io  # noqa: F401 -- UTF-8 guard for Windows

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

TOOLS_DIR = pathlib.Path(__file__).resolve().parent
ROOT = TOOLS_DIR.parent
ASSETS_DIR = ROOT / "assets"
CAP_SVG = ASSETS_DIR / "capabilities.svg"
IDEAS_SVG = ASSETS_DIR / "adopted-ideas.svg"
IDEAS_JSON = ASSETS_DIR / "adopted_ideas.json"


# ---------------------------------------------------------------------------
# Count helpers
# ---------------------------------------------------------------------------

def count_agents() -> int:
    """Return agent count from agent_cards.json["count"], or count .md files as fallback."""
    cards_path = ROOT / "agent_cards.json"
    if cards_path.exists():
        try:
            data = json.loads(cards_path.read_text(encoding="utf-8"))
            c = data.get("count")
            if isinstance(c, int) and c > 0:
                return c
        except (json.JSONDecodeError, OSError):
            pass
    # Fallback: count .claude/agents/*.md with frontmatter, excluding README
    agents_dir = ROOT / ".claude" / "agents"
    n = 0
    for p in agents_dir.glob("*.md"):
        if p.name.upper() == "README.MD":
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
            if text.startswith("---") and "name:" in text[:200]:
                n += 1
        except OSError:
            pass
    return n


def count_councils() -> int:
    """Return len(CMAP) by parsing tools/task_router.py."""
    router_path = TOOLS_DIR / "task_router.py"
    if not router_path.exists():
        return 0
    text = router_path.read_text(encoding="utf-8", errors="replace")
    # Find CMAP = { ... } block
    m = re.search(r"CMAP\s*=\s*\{([^}]+)\}", text, re.DOTALL)
    if not m:
        return 0
    block = m.group(1)
    # Count top-level string keys: lines starting with a quoted key
    keys = re.findall(r'^\s*"[^"]+"\s*:', block, re.MULTILINE)
    return len(keys)


def count_gates() -> int:
    """Return GATES constant from tools/consistency_check.py."""
    cc_path = TOOLS_DIR / "consistency_check.py"
    if not cc_path.exists():
        return 8
    text = cc_path.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"GATES\s*=\s*(\d+)", text)
    if m:
        return int(m.group(1))
    return 8


def count_tools() -> int:
    """Count *.py files directly in tools/."""
    return sum(
        1 for f in TOOLS_DIR.iterdir()
        if f.is_file() and f.suffix == ".py"
    )


def count_skills() -> int:
    """Count immediate subdirectories of skills/ containing a SKILL.md."""
    skills_dir = ROOT / "skills"
    if not skills_dir.is_dir():
        return 0
    return sum(
        1 for d in skills_dir.iterdir()
        if d.is_dir() and (d / "SKILL.md").exists()
    )


def count_tests() -> int:
    """Count 'def test_' definitions across tests/*.py."""
    tests_dir = ROOT / "tests"
    if not tests_dir.is_dir():
        return 0
    total = 0
    for p in tests_dir.glob("*.py"):
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
            total += len(re.findall(r"^\s*def test_", text, re.MULTILINE))
        except OSError:
            pass
    return total


def compute_counts() -> dict:
    """Return all six counts as a dict."""
    return {
        "agents": count_agents(),
        "councils": count_councils(),
        "gates": count_gates(),
        "tools": count_tools(),
        "skills": count_skills(),
        "tests": count_tests(),
    }


# ---------------------------------------------------------------------------
# capabilities.svg renderer
# ---------------------------------------------------------------------------

def render_capabilities_svg(counts: dict) -> str:
    """Return the full capabilities SVG string with live counts injected."""
    agents = counts["agents"]
    councils = counts["councils"]
    gates = counts["gates"]
    tools = counts["tools"]
    skills = counts["skills"]
    tests = counts["tests"]

    aria = (
        f"What is inside Cambium: capacity band ({agents} agents, {councils} councils, "
        f"{gates} gates, {tools} tools, {skills} skills, {tests} tests) and six engineering "
        "clusters: orchestration and router, human gates and audit, the evidence contract, "
        "memory and knowledge graph, the learning system, and research-administration tools, "
        "each naming its real file."
    )

    return f"""\
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1100 640" font-family="-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif" role="img" aria-label="{aria}">
<defs>
<linearGradient id="cbg" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#0b2c20"/><stop offset="100%" stop-color="#07231a"/></linearGradient>
</defs>
<rect width="1100" height="640" rx="20" fill="url(#cbg)"/>
<rect x="1" y="1" width="1098" height="638" rx="19" fill="none" stroke="#1F4D3B"/>

<text x="40" y="50" font-size="27" font-weight="800" fill="#eafaf0">What is inside Cambium</text>
<text x="40" y="76" font-size="14" fill="#8AA197">The engineering, made visible. Each cluster names the real file. Every number is reproducible from the repo.</text>

<!-- capacity band -->
<g transform="translate(40,98)">
<rect width="1020" height="58" rx="12" fill="#0E3326" stroke="#1F4D3B"/>
<g font-family="-apple-system,Segoe UI,sans-serif">
<text x="70" y="33" text-anchor="middle" font-size="24" font-weight="800" fill="#16C079">{agents}</text><text x="70" y="49" text-anchor="middle" font-size="11.5" fill="#8AA197">agents</text>
<text x="240" y="33" text-anchor="middle" font-size="24" font-weight="800" fill="#16C079">{councils}</text><text x="240" y="49" text-anchor="middle" font-size="11.5" fill="#8AA197">councils</text>
<text x="410" y="33" text-anchor="middle" font-size="24" font-weight="800" fill="#16C079">{gates}</text><text x="410" y="49" text-anchor="middle" font-size="11.5" fill="#8AA197">human gates</text>
<text x="580" y="33" text-anchor="middle" font-size="24" font-weight="800" fill="#16C079">{tools}</text><text x="580" y="49" text-anchor="middle" font-size="11.5" fill="#8AA197">tools</text>
<text x="750" y="33" text-anchor="middle" font-size="24" font-weight="800" fill="#16C079">{skills}</text><text x="750" y="49" text-anchor="middle" font-size="11.5" fill="#8AA197">skills</text>
<text x="930" y="33" text-anchor="middle" font-size="24" font-weight="800" fill="#16C079">{tests}</text><text x="930" y="49" text-anchor="middle" font-size="11.5" fill="#8AA197">tests</text>
</g>
</g>

<!-- 6 capability cards, 2 rows x 3 -->
<g font-family="-apple-system,Segoe UI,sans-serif">
<!-- row 1 -->
<g transform="translate(40,178)">
<rect width="328" height="138" rx="12" fill="#10392a" stroke="#1F4D3B" stroke-left="3"/>
<rect width="4" height="138" rx="2" fill="#7C5CFF"/>
<text x="20" y="32" font-size="16.5" font-weight="700" fill="#eafaf0">Orchestration + router</text>
<text x="20" y="56" font-size="13" fill="#bcd3c8">Decomposes a goal, dispatches the</text>
<text x="20" y="74" font-size="13" fill="#bcd3c8">named agents, routes by task type.</text>
<text x="20" y="112" font-size="11.5" font-family="ui-monospace,monospace" fill="#8AA197">tools/task_router.py</text>
</g>
<g transform="translate(386,178)">
<rect width="328" height="138" rx="12" fill="#10392a" stroke="#1F4D3B"/>
<rect width="4" height="138" rx="2" fill="#16C079"/>
<text x="20" y="32" font-size="16.5" font-weight="700" fill="#eafaf0">Human gates + audit</text>
<text x="20" y="56" font-size="13" fill="#bcd3c8">Approval-token checks plus a run</text>
<text x="20" y="74" font-size="13" fill="#bcd3c8">contract, and a hash-chained trail.</text>
<text x="20" y="112" font-size="11.5" font-family="ui-monospace,monospace" fill="#8AA197">gate_lock.py, audit_log.py</text>
</g>
<g transform="translate(732,178)">
<rect width="328" height="138" rx="12" fill="#10392a" stroke="#1F4D3B"/>
<rect width="4" height="138" rx="2" fill="#FF6B5E"/>
<text x="20" y="32" font-size="16.5" font-weight="700" fill="#eafaf0">Evidence contract</text>
<text x="20" y="56" font-size="13" fill="#bcd3c8">Four tiers: proved, code-verified,</text>
<text x="20" y="74" font-size="13" fill="#bcd3c8">asserted, open. Overclaims flagged.</text>
<text x="20" y="112" font-size="11.5" font-family="ui-monospace,monospace" fill="#8AA197">tools/finding_audit.py</text>
</g>
<!-- row 2 -->
<g transform="translate(40,330)">
<rect width="328" height="138" rx="12" fill="#10392a" stroke="#1F4D3B"/>
<rect width="4" height="138" rx="2" fill="#3D8BFF"/>
<text x="20" y="32" font-size="16.5" font-weight="700" fill="#eafaf0">Memory + knowledge graph</text>
<text x="20" y="56" font-size="13" fill="#bcd3c8">Recall past findings, walk a local</text>
<text x="20" y="74" font-size="13" fill="#bcd3c8">graph, contradictions flagged not solved.</text>
<text x="20" y="112" font-size="11.5" font-family="ui-monospace,monospace" fill="#8AA197">memory_recall.py, concept_graph.py</text>
</g>
<g transform="translate(386,330)">
<rect width="328" height="138" rx="12" fill="#10392a" stroke="#1F4D3B"/>
<rect width="4" height="138" rx="2" fill="#E0B24A"/>
<text x="20" y="32" font-size="16.5" font-weight="700" fill="#eafaf0">Learning system</text>
<text x="20" y="56" font-size="13" fill="#bcd3c8">Every build teaches you. Ten Academy</text>
<text x="20" y="74" font-size="13" fill="#bcd3c8">modules and a per-run lab. Enforced.</text>
<text x="20" y="112" font-size="11.5" font-family="ui-monospace,monospace" fill="#8AA197">learning_delivery.py, the Academy</text>
</g>
<g transform="translate(732,330)">
<rect width="328" height="138" rx="12" fill="#10392a" stroke="#1F4D3B"/>
<rect width="4" height="138" rx="2" fill="#2BB8C4"/>
<text x="20" y="32" font-size="16.5" font-weight="700" fill="#eafaf0">Research-admin tools</text>
<text x="20" y="56" font-size="13" fill="#bcd3c8">AI-use disclosure and an advisory</text>
<text x="20" y="74" font-size="13" fill="#bcd3c8">budget-to-solicitation review.</text>
<text x="20" y="112" font-size="11.5" font-family="ui-monospace,monospace" fill="#8AA197">ai_disclosure.py, budget_review.py</text>
</g>
</g>

<!-- footer -->
<rect x="40" y="500" width="1020" height="50" rx="12" fill="#15402F" stroke="#1F4D3B"/>
<text x="60" y="531" font-size="13.5" fill="#cfe4d9">MIT licensed  &#183;  local-first, data-sovereign  &#183;  a Claude Code / Cowork plugin with an MCP server  &#183;  pure-stdlib tools, no heavy dependencies</text>

<text x="40" y="588" font-size="12.5" fill="#6f8a7e">Honest by design: a capability is labeled enforced (with its mechanism) or partial / roadmap. The live web mode is a simulation; the cross-institution layer is roadmap.</text>
</svg>
"""


# ---------------------------------------------------------------------------
# adopted-ideas.svg renderer
# ---------------------------------------------------------------------------

# Status accent palette
_STATUS_STYLES = {
    "adopted": {
        "src_stroke": "#5e4a26",
        "src_text": "#f0d9b6",
        "src_meta": "#a9936a",
        "built_accent": "#16C079",
        "built_dash": "",
    },
    "declined-heavy": {
        "src_stroke": "#b75778",
        "src_text": "#f7c0d4",
        "src_meta": "#c89aac",
        "built_accent": "#16C079",
        "built_dash": "",
    },
    "roadmap": {
        "src_stroke": "#2bb8c4",
        "src_text": "#bfeef3",
        "src_meta": "#8fcdd4",
        "built_accent": "#E0B24A",
        "built_dash": ' stroke-dasharray="4 3"',
    },
}

_ROW_HEIGHT = 82   # vertical stride between rows
_ROW_H = 64        # rect height per row
_HEADER_Y = 108    # y-offset where rows start


def _render_row(item: dict, y_offset: int) -> str:
    """Render one source->built row as SVG group fragment."""
    status = item.get("status", "adopted")
    st = _STATUS_STYLES.get(status, _STATUS_STYLES["adopted"])
    src = _xml_escape(item.get("source", ""))
    meta = _xml_escape(item.get("meta", ""))
    built = _xml_escape(item.get("built", ""))
    note = _xml_escape(item.get("note", ""))
    dash = st["built_dash"]

    return (
        f'<g transform="translate(0,{y_offset})">\n'
        f'<g transform="translate(40,0)">'
        f'<rect width="420" height="{_ROW_H}" rx="11" fill="#0E3326" stroke="{st["src_stroke"]}"/>'
        f'<text x="18" y="28" font-size="16" font-weight="700" fill="{st["src_text"]}">{src}</text>'
        f'<text x="18" y="48" font-size="12" fill="{st["src_meta"]}">{meta}</text>'
        f'</g>\n'
        f'<path d="M468 32 H 502" stroke="#3a6e57" stroke-width="2" marker-end="url(#ar)"/>\n'
        f'<g transform="translate(510,0)">'
        f'<rect width="550" height="{_ROW_H}" rx="11" fill="#10392a" stroke="#1F4D3B"{dash}/>'
        f'<rect width="4" height="{_ROW_H}" rx="2" fill="{st["built_accent"]}"/>'
        f'<text x="20" y="28" font-size="15" font-weight="600" fill="#eafaf0">{built}</text>'
        f'<text x="20" y="48" font-size="12" fill="#8AA197" font-family="ui-monospace,monospace">{note}</text>'
        f'</g>\n'
        f'</g>'
    )


def _xml_escape(s: str) -> str:
    return (
        s.replace("&", "&amp;")
         .replace("<", "&lt;")
         .replace(">", "&gt;")
         .replace('"', "&quot;")
    )


def render_ideas_svg(ideas: list) -> str:
    """Return the full adopted-ideas SVG string from the ideas list."""
    n = len(ideas)
    # viewBox height: header ~108 + rows + 40 footer gap + 30 text line
    footer_text_y = _HEADER_Y + n * _ROW_HEIGHT + 14
    vh = footer_text_y + 24
    vh = max(vh, 200)

    aria_parts = []
    for item in ideas:
        src = item.get("source", "")
        built = item.get("built", "")
        aria_parts.append(f"{src} became {built}")
    aria = (
        "Ideas Cambium adopted from other work, with attribution: "
        + "; ".join(aria_parts) + "."
    )

    rows_svg = []
    for i, item in enumerate(ideas):
        y_offset = _HEADER_Y + i * _ROW_HEIGHT
        rows_svg.append(_render_row(item, y_offset))

    rows_block = "\n".join(rows_svg)

    return f"""\
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1100 {vh}" font-family="-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif" role="img" aria-label="{_xml_escape(aria)}">
<defs>
<linearGradient id="abg" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#0b2c20"/><stop offset="100%" stop-color="#07231a"/></linearGradient>
</defs>
<rect width="1100" height="{vh}" rx="20" fill="url(#abg)"/>
<rect x="1" y="1" width="1098" height="{vh - 2}" rx="19" fill="none" stroke="#1F4D3B"/>

<text x="40" y="50" font-size="27" font-weight="800" fill="#eafaf0">Standing on shoulders, honestly</text>
<text x="40" y="76" font-size="14" fill="#8AA197">Ideas we adopted from other work, and what we built from them. We name the source, and we say where we declined.</text>

<g font-family="-apple-system,Segoe UI,sans-serif">
<text x="250" y="98" text-anchor="middle" font-size="11.5" letter-spacing="1.5" fill="#E0B24A">THE SOURCE</text>
<text x="800" y="98" text-anchor="middle" font-size="11.5" letter-spacing="1.5" fill="#16C079">WHAT CAMBIUM BUILT</text>
</g>

<!-- rows -->
<g font-family="-apple-system,Segoe UI,sans-serif">
{rows_block}
</g>

<text x="40" y="{footer_text_y}" font-size="12.5" fill="#6f8a7e">Where we took only the idea, we say so. Where we declined the dependency, we say that too. Attribution lives in ATTRIBUTION.md.</text>

<defs>
<marker id="ar" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 z" fill="#3a6e57"/></marker>
</defs>
</svg>
"""


# ---------------------------------------------------------------------------
# Seed data for adopted_ideas.json
# ---------------------------------------------------------------------------

SEED_IDEAS = [
    {
        "source": "agent-skills",
        "meta": "open source, MIT, attributed",
        "built": "Skill-authoring patterns + two engineering skills",
        "note": "version-control-discipline, test-driven-research-code - ATTRIBUTION.md",
        "status": "adopted",
    },
    {
        "source": "Loop Engineering",
        "meta": "a research paper, the idea",
        "built": "A four-cost loop guard + a run-aborting budget cap",
        "note": "loop_costs.py",
        "status": "adopted",
    },
    {
        "source": "Google Open Knowledge Format",
        "meta": "a standard, the idea",
        "built": "An OKF export with a self-contained graph viewer",
        "note": "okf_export.py - inspired by, not compliant with",
        "status": "adopted",
    },
    {
        "source": "Meta V-JEPA",
        "meta": "de-branded to a heuristic",
        "built": "A run-outcome prior that predicts cost and risk",
        "note": "run_outcome_prior.py - a prior, not a world model",
        "status": "adopted",
    },
    {
        "source": "GraphRAG / Graphiti / MemPalace",
        "meta": "reviewed, heavy stack declined",
        "built": "A lean local knowledge graph + recall, no servers",
        "note": "concept_graph.py, memory_recall.py - no Neo4j, no cloud",
        "status": "declined-heavy",
    },
    {
        "source": "OpenMontage",
        "meta": "AGPLv3, separate process",
        "built": "Video deliverables, called as a subprocess",
        "note": "render-video skill - the OS process is the license boundary",
        "status": "adopted",
    },
    {
        "source": "MindRouter (UIdaho RCDS)",
        "meta": "institutional partner, roadmap",
        "built": "A sovereign, FERPA-safe inference path",
        "note": "integration scope - roadmap, not yet wired",
        "status": "roadmap",
    },
]


def ensure_ideas_json() -> list:
    """Write assets/adopted_ideas.json with seed data if it does not yet exist.
    Return the list of ideas loaded from the (possibly freshly-written) file."""
    if not IDEAS_JSON.exists():
        IDEAS_JSON.write_text(
            json.dumps(SEED_IDEAS, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        print(f"[gen_capabilities] seeded {IDEAS_JSON.relative_to(ROOT)}")
    return json.loads(IDEAS_JSON.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Write helpers
# ---------------------------------------------------------------------------

def _write(path: pathlib.Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------------
# --check logic
# ---------------------------------------------------------------------------

def check_mode() -> int:
    """Return 0 if committed SVGs match a fresh regen, else 1."""
    counts = compute_counts()
    ideas = ensure_ideas_json()

    fresh_cap = render_capabilities_svg(counts)
    fresh_ideas = render_ideas_svg(ideas)

    cap_ok = CAP_SVG.exists() and CAP_SVG.read_text(encoding="utf-8") == fresh_cap
    ideas_ok = IDEAS_SVG.exists() and IDEAS_SVG.read_text(encoding="utf-8") == fresh_ideas

    if cap_ok and ideas_ok:
        print("[gen_capabilities] --check: both SVGs are up to date.")
        return 0

    if not cap_ok:
        print(f"[gen_capabilities] --check: {CAP_SVG.name} is STALE (rerun without --check to fix).")
    if not ideas_ok:
        print(f"[gen_capabilities] --check: {IDEAS_SVG.name} is STALE (rerun without --check to fix).")
    return 1


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Regenerate assets/capabilities.svg and assets/adopted-ideas.svg from live repo data."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit 1 if either committed SVG differs from a fresh regen.",
    )
    args = parser.parse_args()

    if args.check:
        return check_mode()

    # Regen mode
    counts = compute_counts()
    ideas = ensure_ideas_json()

    cap_svg = render_capabilities_svg(counts)
    ideas_svg = render_ideas_svg(ideas)

    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    _write(CAP_SVG, cap_svg)
    _write(IDEAS_SVG, ideas_svg)

    try:
        rel_cap = CAP_SVG.relative_to(ROOT)
        rel_ideas = IDEAS_SVG.relative_to(ROOT)
    except ValueError:
        rel_cap = CAP_SVG
        rel_ideas = IDEAS_SVG

    print(
        f"[gen_capabilities] counts used: "
        f"agents={counts['agents']}, councils={counts['councils']}, "
        f"gates={counts['gates']}, tools={counts['tools']}, "
        f"skills={counts['skills']}, tests={counts['tests']}"
    )
    print(f"[gen_capabilities] wrote {rel_cap}")
    print(f"[gen_capabilities] wrote {rel_ideas}  ({len(ideas)} idea rows)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
