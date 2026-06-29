#!/usr/bin/env python3
"""okf_export.py — Export a Cambium run as an Open Knowledge Format (OKF) bundle.

OKF = markdown files with YAML frontmatter, cross-linked, with auto-generated
index.md files for progressive disclosure, plus a self-contained interactive
HTML visualizer powered by Cytoscape.js (force-directed graph).

Inputs (read what exists; degrade gracefully):
  agent_outputs/findings_ledger.csv
  agent_outputs/*.md
  governance/GATES.md
  examples/e2e-worked-example/provenance_manifest.json

Output bundle layout under --out <dir>:
  findings/<id>.md
  gates/<gate-id>.md
  agents/<name>.md
  index.md (root)
  findings/index.md, gates/index.md, agents/index.md
  viz.html  (self-contained Cytoscape graph)

Usage:
  python3 tools/okf_export.py --out okf_bundle [--root .]
"""

import argparse
import csv
import json
import os
import re
import sys
import datetime

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _slug(s):
    """Convert a string to a safe filename slug."""
    s = re.sub(r"[^\w\s-]", "", s.lower())
    s = re.sub(r"[\s_-]+", "-", s.strip())
    return s or "item"


def _yaml_str(value):
    """Render a Python value as a YAML scalar or list item (single-line safe)."""
    if isinstance(value, list):
        if not value:
            return "[]"
        items = "\n".join(f"  - {json.dumps(str(v))}" for v in value)
        return "\n" + items
    if value is None:
        return '""'
    s = str(value)
    # Quote if contains special YAML characters
    if any(c in s for c in (':', '#', '[', ']', '{', '}', ',', '&', '*', '?', '|',
                              '-', '<', '>', '=', '!', '%', '@', '`', '"', "'")):
        return json.dumps(s)
    return s or '""'


def _frontmatter(fields):
    """Build a YAML frontmatter block from an ordered list of (key, value) pairs."""
    lines = ["---"]
    for key, value in fields:
        if isinstance(value, list):
            if not value:
                lines.append(f"{key}: []")
            else:
                lines.append(f"{key}:")
                for item in value:
                    lines.append(f"  - {json.dumps(str(item))}")
        elif value is None:
            lines.append(f'{key}: ""')
        else:
            s = str(value)
            # Use json.dumps quoting if the value contains YAML-special chars
            if any(c in s for c in (':', '#', '[', ']', '{', '}', '&', '*', '|',
                                     '<', '>', '!', '%', '@', '`', '"', "'")):
                lines.append(f"{key}: {json.dumps(s)}")
            elif s == "":
                lines.append(f'{key}: ""')
            else:
                lines.append(f"{key}: {s}")
    lines.append("---")
    return "\n".join(lines)


def _write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)


def _read(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return fh.read()
    except FileNotFoundError:
        return None


# ---------------------------------------------------------------------------
# Parsers
# ---------------------------------------------------------------------------

def parse_ledger(root):
    """Parse agent_outputs/findings_ledger.csv. Returns list of row dicts."""
    path = os.path.join(root, "agent_outputs", "findings_ledger.csv")
    if not os.path.exists(path):
        return []
    try:
        with open(path, newline="", encoding="utf-8") as fh:
            return list(csv.DictReader(fh))
    except OSError:
        return []  # file present per stat but unreadable; degrade gracefully


def parse_gates(root):
    """Parse governance/GATES.md markdown table. Returns list of gate dicts."""
    path = os.path.join(root, "governance", "GATES.md")
    content = _read(path)
    if not content:
        # Fall back to full-lifecycle example
        path = os.path.join(root, "examples", "full-lifecycle", "governance", "GATES.md")
        content = _read(path)
    if not content:
        return []
    gates = []
    header = None
    for line in content.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        # Skip separator rows like |---|---|
        if all(re.match(r"^[-:]+$", c) for c in cells if c):
            continue
        if header is None:
            header = [c.lower().replace(" ", "_") for c in cells]
            continue
        if len(cells) < len(header):
            cells += [""] * (len(header) - len(cells))
        row = dict(zip(header, cells))
        gate_id = row.get("gate", "").strip()
        if gate_id:
            gates.append(row)
    return gates


def parse_agent_outputs(root):
    """Find agent_outputs/*.md files. Returns list of (name, content) tuples."""
    outdir = os.path.join(root, "agent_outputs")
    if not os.path.isdir(outdir):
        return []
    results = []
    for fname in sorted(os.listdir(outdir)):
        if fname.endswith(".md"):
            path = os.path.join(outdir, fname)
            content = _read(path)
            if content is not None:
                name = fname[:-3]  # strip .md
                results.append((name, content))
    return results


def parse_provenance(root):
    """Parse provenance_manifest.json if present. Returns dict or None."""
    path = os.path.join(root, "examples", "e2e-worked-example", "provenance_manifest.json")
    content = _read(path)
    if content:
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return None
    return None


# ---------------------------------------------------------------------------
# Cross-link inference
# ---------------------------------------------------------------------------

def _agents_for_finding(finding_row):
    """Return list of agent names referenced in a finding row."""
    raw = finding_row.get("agents", "")
    return [a.strip() for a in raw.split(";") if a.strip()] or \
           [a.strip() for a in raw.split(",") if a.strip()]


def _gate_for_finding(finding_row, gates):
    """Try to match a finding to a gate by scanning gate rationale/notes for the finding id."""
    fid = (finding_row.get("id") or "").strip()
    action = (finding_row.get("action") or "").lower()
    status = (finding_row.get("status") or "").lower()
    if not fid:
        return None
    for gate in gates:
        # Check notes/rationale columns for the finding id
        notes_cols = [v for k, v in gate.items() if k in ("notes", "rationale", "decision")]
        combined = " ".join(str(v) for v in notes_cols).lower()
        if fid.lower() in combined:
            return gate.get("gate", "").strip()
        # Check if the action references a gate
        gate_id = gate.get("gate", "").strip().lower()
        if gate_id and gate_id in action:
            return gate.get("gate", "").strip()
    return None


def _findings_for_gate(gate, findings):
    """Return list of finding ids that reference this gate or are referenced in gate notes."""
    gate_id = (gate.get("gate") or "").strip()
    notes_cols = [v for k, v in gate.items() if k in ("notes", "rationale", "decision")]
    combined = " ".join(str(v) for v in notes_cols).lower()
    result = []
    for f in findings:
        fid = (f.get("id") or "").strip()
        if not fid:
            continue
        # Finding action references this gate
        action = (f.get("action") or "").lower()
        if gate_id.lower() and gate_id.lower() in action:
            result.append(fid)
        # Gate notes reference this finding
        elif fid.lower() in combined:
            result.append(fid)
    return result


# ---------------------------------------------------------------------------
# Writers
# ---------------------------------------------------------------------------

NOW = datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def write_findings(out_dir, findings, gates, agent_names):
    """Write findings/<id>.md for each ledger row."""
    written = []
    for row in findings:
        fid = (row.get("id") or "").strip()
        if not fid:
            continue
        title = (row.get("issue") or fid).strip()
        agents_list = _agents_for_finding(row)
        gate_id = _gate_for_finding(row, gates)

        links = []
        # Link to each agent that produced it
        for ag in agents_list:
            if ag in agent_names:
                links.append(f"../agents/{_slug(ag)}.md")
        # Link to the gate if inferable
        if gate_id:
            links.append(f"../gates/{_slug(gate_id)}.md")

        tags = []
        tier = (row.get("claim_tier") or "").strip()
        sev = (row.get("severity") or "").strip()
        status = (row.get("status") or "").strip()
        if tier:
            tags.append(tier.lower().replace(" ", "-"))
        if sev:
            tags.append(sev.lower())
        if status:
            tags.append(status.lower())

        fm = _frontmatter([
            ("type", "finding"),
            ("id", fid),
            ("title", title),
            ("claim_tier", tier),
            ("evidence_tier", tier),
            ("agents", agents_list),
            ("severity", sev),
            ("status", status),
            ("timestamp", NOW),
            ("tags", tags),
            ("links", links),
        ])

        # Build body: issue description + evidence
        body_parts = [f"# {fid}: {title}", ""]
        evidence = (row.get("evidence") or "").strip()
        if evidence:
            body_parts += ["## Evidence", "", evidence, ""]
        action = (row.get("action") or "").strip()
        if action:
            body_parts += ["## Action", "", action, ""]
        # Cross-links section
        if links:
            body_parts += ["## Cross-links", ""]
            for lnk in links:
                label = os.path.basename(lnk).replace(".md", "")
                body_parts.append(f"- [{label}]({lnk})")
            body_parts.append("")

        content = fm + "\n\n" + "\n".join(body_parts)
        path = os.path.join(out_dir, "findings", f"{_slug(fid)}.md")
        _write(path, content)
        written.append((fid, title, _slug(fid)))
    return written


def write_gates(out_dir, gates, findings):
    """Write gates/<gate-id>.md for each gate row."""
    written = []
    for gate in gates:
        gate_id = (gate.get("gate") or "").strip()
        if not gate_id:
            continue
        decision = (gate.get("decision") or "").strip()
        approver = (gate.get("approved_by_(name)") or
                    gate.get("approved_by") or
                    gate.get("approver_role") or "").strip()
        date = (gate.get("date") or "").strip()
        notes = (gate.get("notes") or gate.get("rationale") or "").strip()

        ref_findings = _findings_for_gate(gate, findings)
        links = [f"../findings/{_slug(fid)}.md" for fid in ref_findings]

        tags = ["gate"]
        if date:
            tags.append(date[:4])  # year

        fm = _frontmatter([
            ("type", "gate"),
            ("id", gate_id),
            ("title", decision or gate_id),
            ("approver", approver),
            ("decision", decision),
            ("date", date),
            ("timestamp", NOW),
            ("tags", tags),
            ("links", links),
        ])

        body_parts = [f"# Gate {gate_id}", ""]
        if decision:
            body_parts += [f"**Decision:** {decision}", ""]
        if approver:
            body_parts += [f"**Approved by:** {approver}", ""]
        if date:
            body_parts += [f"**Date:** {date}", ""]
        if notes:
            body_parts += ["## Rationale", "", notes, ""]
        if links:
            body_parts += ["## Referenced Findings", ""]
            for lnk in links:
                label = os.path.basename(lnk).replace(".md", "")
                body_parts.append(f"- [{label}]({lnk})")
            body_parts.append("")

        content = fm + "\n\n" + "\n".join(body_parts)
        path = os.path.join(out_dir, "gates", f"{_slug(gate_id)}.md")
        _write(path, content)
        written.append((gate_id, decision or gate_id, _slug(gate_id)))
    return written


def write_agents(out_dir, agent_outputs):
    """Write agents/<name>.md for each agent output markdown."""
    written = []
    for name, content in agent_outputs:
        # Extract title from first H1 if present
        title = name
        for line in content.splitlines():
            line = line.strip()
            if line.startswith("# "):
                title = line[2:].strip()
                break

        # Collect any markdown links already in the content
        links = re.findall(r"\[.*?\]\(([^)]+\.md)\)", content)
        # Deduplicate
        links = list(dict.fromkeys(links))

        tags = ["agent", _slug(name)]

        fm = _frontmatter([
            ("type", "agent"),
            ("id", _slug(name)),
            ("title", title),
            ("name", name),
            ("timestamp", NOW),
            ("tags", tags),
            ("links", links),
        ])

        body = fm + "\n\n" + content
        path = os.path.join(out_dir, "agents", f"{_slug(name)}.md")
        _write(path, body)
        written.append((name, title, _slug(name)))
    return written


# ---------------------------------------------------------------------------
# Index files
# ---------------------------------------------------------------------------

def write_subdir_index(out_dir, subdir, items, desc):
    """Write subdir/index.md listing all items."""
    lines = [f"# {subdir.capitalize()} Index", "", desc, ""]
    for item_id, title, slug in items:
        lines.append(f"- [{item_id}: {title}]({slug}.md)")
    lines.append("")
    content = "\n".join(lines)
    _write(os.path.join(out_dir, subdir, "index.md"), content)


def write_root_index(out_dir, findings, gates, agents):
    """Write root index.md with progressive disclosure."""
    lines = [
        "# OKF Knowledge Bundle",
        "",
        "Auto-generated by `tools/okf_export.py`. "
        "Open `viz.html` for an interactive graph view.",
        "",
        "## Findings",
        "",
    ]
    for fid, title, slug in findings:
        lines.append(f"- [{fid}: {title}](findings/{slug}.md)")
    lines += ["", "## Gates", ""]
    for gid, title, slug in gates:
        lines.append(f"- [Gate {gid}: {title}](gates/{slug}.md)")
    lines += ["", "## Agent Outputs", ""]
    for name, title, slug in agents:
        lines.append(f"- [{name}](agents/{slug}.md)")
    lines += [
        "",
        "---",
        "",
        "See also: [Interactive Graph](viz.html)",
        "",
    ]
    _write(os.path.join(out_dir, "index.md"), "\n".join(lines))


# ---------------------------------------------------------------------------
# viz.html builder
# ---------------------------------------------------------------------------

_VIZ_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>OKF Knowledge Graph</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.29.2/cytoscape.min.js"
        crossorigin="anonymous"
        referrerpolicy="no-referrer"></script>
<style>
  *{box-sizing:border-box;margin:0;padding:0}
  body{font-family:system-ui,sans-serif;display:flex;height:100vh;overflow:hidden;background:#f8f9fa}
  #sidebar{width:320px;min-width:200px;display:flex;flex-direction:column;border-right:1px solid #dee2e6;background:#fff;overflow:hidden}
  #controls{padding:12px;border-bottom:1px solid #dee2e6}
  #controls h1{font-size:1rem;color:#212529;margin-bottom:8px}
  #search{width:100%;padding:6px 8px;border:1px solid #ced4da;border-radius:4px;font-size:0.85rem}
  #type-filter{display:flex;flex-wrap:wrap;gap:4px;margin-top:8px}
  .filter-btn{padding:3px 10px;border:1px solid #ced4da;border-radius:12px;background:#fff;font-size:0.78rem;cursor:pointer;transition:all .15s}
  .filter-btn.active{background:#0d6efd;border-color:#0d6efd;color:#fff}
  #detail{flex:1;overflow-y:auto;padding:12px}
  #detail h2{font-size:0.95rem;margin-bottom:6px;color:#343a40}
  #detail .fm-table{width:100%;border-collapse:collapse;font-size:0.8rem;margin-bottom:10px}
  #detail .fm-table td{padding:3px 6px;border-bottom:1px solid #f0f0f0;vertical-align:top}
  #detail .fm-table td:first-child{color:#6c757d;white-space:nowrap;font-weight:500;width:40%}
  #detail .body-text{font-size:0.82rem;line-height:1.5;color:#495057;white-space:pre-wrap;word-break:break-word}
  #detail .backlinks{margin-top:10px}
  #detail .backlinks h3{font-size:0.82rem;color:#6c757d;margin-bottom:4px}
  #detail .backlinks a{display:block;font-size:0.8rem;color:#0d6efd;text-decoration:none;padding:1px 0}
  #detail .backlinks a:hover{text-decoration:underline}
  #cy-wrap{flex:1;position:relative;overflow:hidden}
  #cy{width:100%;height:100%}
  #legend{position:absolute;bottom:10px;right:10px;background:rgba(255,255,255,0.9);border:1px solid #dee2e6;border-radius:6px;padding:8px 12px;font-size:0.78rem}
  #legend div{display:flex;align-items:center;gap:6px;margin-bottom:3px}
  .dot{width:12px;height:12px;border-radius:50%;display:inline-block}
  .dot-finding{background:#2196F3}
  .dot-gate{background:#FF9800}
  .dot-agent{background:#4CAF50}
  #placeholder{display:flex;align-items:center;justify-content:center;height:100%;color:#adb5bd;font-size:0.9rem;text-align:center;padding:20px}
</style>
</head>
<body>
<div id="sidebar">
  <div id="controls">
    <h1>OKF Knowledge Graph</h1>
    <input id="search" type="text" placeholder="Search nodes..." />
    <div id="type-filter">
      <button class="filter-btn active" data-type="all">All</button>
      <button class="filter-btn active" data-type="finding">Findings</button>
      <button class="filter-btn active" data-type="gate">Gates</button>
      <button class="filter-btn active" data-type="agent">Agents</button>
    </div>
  </div>
  <div id="detail">
    <div id="placeholder">Click a node to see details</div>
  </div>
</div>
<div id="cy-wrap">
  <div id="cy"></div>
  <div id="legend">
    <div><span class="dot dot-finding"></span> Finding</div>
    <div><span class="dot dot-gate"></span> Gate</div>
    <div><span class="dot dot-agent"></span> Agent</div>
  </div>
</div>
<script>
const BUNDLE = __BUNDLE_JSON__;

// Build Cytoscape elements from bundle
const colorMap = {finding: '#2196F3', gate: '#FF9800', agent: '#4CAF50'};
const elements = [];
const nodeIds = new Set(BUNDLE.nodes.map(n => n.id));

BUNDLE.nodes.forEach(n => {
  elements.push({
    data: {
      id: n.id,
      label: n.title || n.id,
      type: n.type,
      color: colorMap[n.type] || '#999',
      ...n
    }
  });
});

BUNDLE.edges.forEach((e, i) => {
  if (nodeIds.has(e.source) && nodeIds.has(e.target)) {
    elements.push({data: {id: 'e'+i, source: e.source, target: e.target}});
  }
});

// Build backlinks map
const backlinks = {};
BUNDLE.edges.forEach(e => {
  if (!backlinks[e.target]) backlinks[e.target] = [];
  backlinks[e.target].push(e.source);
});

const cy = cytoscape({
  container: document.getElementById('cy'),
  elements,
  style: [
    {selector: 'node', style: {
      'background-color': 'data(color)',
      'label': 'data(label)',
      'color': '#1a1a2e',
      'font-size': 11,
      'text-valign': 'bottom',
      'text-halign': 'center',
      'text-margin-y': 4,
      'text-background-opacity': 0.85,
      'text-background-color': '#fff',
      'text-background-shape': 'roundrectangle',
      'text-background-padding': '2px',
      'width': 30,
      'height': 30,
      'border-width': 2,
      'border-color': '#fff',
    }},
    {selector: 'node.highlighted', style: {'border-color': '#333', 'border-width': 3}},
    {selector: 'node.dimmed', style: {'opacity': 0.25}},
    {selector: 'node.hidden', style: {'display': 'none'}},
    {selector: 'edge', style: {
      'width': 1.5,
      'line-color': '#adb5bd',
      'target-arrow-color': '#adb5bd',
      'target-arrow-shape': 'triangle',
      'curve-style': 'bezier',
      'opacity': 0.7,
    }},
  ],
  layout: {name: 'cose', animate: false, randomize: false, padding: 30},
  userZoomingEnabled: true,
  userPanningEnabled: true,
});

// Detail panel
function showDetail(nodeData) {
  const detail = document.getElementById('detail');
  const bl = (backlinks[nodeData.id] || []).map(sid => {
    const src = BUNDLE.nodes.find(n => n.id === sid);
    return src ? `<a href="#" data-nid="${sid}">${src.title || sid}</a>` : '';
  }).join('');

  const fmRows = Object.entries(nodeData.frontmatter || {})
    .filter(([k]) => !['links','tags'].includes(k))
    .map(([k,v]) => `<tr><td>${k}</td><td>${Array.isArray(v) ? v.join(', ') : v}</td></tr>`)
    .join('');

  const tagHtml = (nodeData.tags || []).map(t => `<span style="background:#e9ecef;padding:2px 6px;border-radius:10px;font-size:0.75rem;margin-right:3px">${t}</span>`).join('');

  detail.innerHTML = `
    <h2>${nodeData.title || nodeData.id}</h2>
    ${tagHtml ? `<div style="margin-bottom:8px">${tagHtml}</div>` : ''}
    ${fmRows ? `<table class="fm-table"><tbody>${fmRows}</tbody></table>` : ''}
    <div class="body-text">${(nodeData.body || '').slice(0, 1200)}${(nodeData.body||'').length > 1200 ? '\n...' : ''}</div>
    ${bl ? `<div class="backlinks"><h3>Cited by</h3>${bl}</div>` : ''}
  `;
  // Allow clicking cited-by links
  detail.querySelectorAll('[data-nid]').forEach(a => {
    a.addEventListener('click', ev => {
      ev.preventDefault();
      const nd = cy.getElementById(a.dataset.nid);
      if (nd.length) { cy.animate({center:{eles:nd},zoom:1.5}); nd.emit('tap'); }
    });
  });
}

cy.on('tap', 'node', evt => {
  cy.nodes().removeClass('highlighted dimmed');
  const n = evt.target;
  const connected = n.closedNeighborhood();
  connected.nodes().addClass('highlighted');
  cy.nodes().not(connected.nodes()).addClass('dimmed');
  showDetail(n.data());
});

cy.on('tap', evt => {
  if (evt.target === cy) {
    cy.nodes().removeClass('highlighted dimmed');
    document.getElementById('detail').innerHTML = '<div id="placeholder">Click a node to see details</div>';
  }
});

// Search
document.getElementById('search').addEventListener('input', function() {
  const q = this.value.trim().toLowerCase();
  if (!q) { cy.nodes().removeClass('hidden'); return; }
  cy.nodes().forEach(n => {
    const match = (n.data('label')||'').toLowerCase().includes(q) ||
                  (n.data('body')||'').toLowerCase().includes(q) ||
                  (n.data('id')||'').toLowerCase().includes(q);
    n.toggleClass('hidden', !match);
  });
});

// Type filter
const activeTypes = new Set(['finding','gate','agent']);
document.querySelectorAll('.filter-btn[data-type]').forEach(btn => {
  btn.addEventListener('click', () => {
    const t = btn.dataset.type;
    if (t === 'all') {
      const allOn = activeTypes.size === 3;
      if (allOn) { activeTypes.clear(); }
      else { activeTypes.add('finding'); activeTypes.add('gate'); activeTypes.add('agent'); }
      document.querySelectorAll('.filter-btn[data-type]:not([data-type="all"])').forEach(b => {
        b.classList.toggle('active', !allOn);
      });
      btn.classList.toggle('active', !allOn);
    } else {
      if (activeTypes.has(t)) { activeTypes.delete(t); btn.classList.remove('active'); }
      else { activeTypes.add(t); btn.classList.add('active'); }
      const allBtn = document.querySelector('.filter-btn[data-type="all"]');
      allBtn.classList.toggle('active', activeTypes.size === 3);
    }
    cy.nodes().forEach(n => n.toggleClass('hidden', !activeTypes.has(n.data('type'))));
  });
});
</script>
</body>
</html>
"""


def build_viz_json(findings_written, gates_written, agents_written,
                   finding_rows, gate_rows, agent_outputs_list):
    """Build the JSON bundle embedded in viz.html."""
    nodes = []
    edges = []

    # Build lookup maps
    finding_by_slug = {_slug(fid): row for fid, _, _ in findings_written
                       for row in finding_rows if (row.get("id") or "").strip() == fid}
    # Rebuild properly
    finding_row_by_id = {(r.get("id") or "").strip(): r for r in finding_rows}
    gate_row_by_id = {(g.get("gate") or "").strip(): g for g in gate_rows}
    agent_content_by_slug = {_slug(name): content for name, content in agent_outputs_list}

    for fid, title, slug in findings_written:
        row = finding_row_by_id.get(fid, {})
        tier = (row.get("claim_tier") or "").strip()
        status = (row.get("status") or "").strip()
        sev = (row.get("severity") or "").strip()
        evidence = (row.get("evidence") or "").strip()
        agents_list = _agents_for_finding(row)
        tags = [x for x in [tier.lower().replace(" ", "-") if tier else None,
                             sev.lower() if sev else None,
                             status.lower() if status else None] if x]
        body = f"Issue: {title}\nSeverity: {sev}\nStatus: {status}\nEvidence: {evidence}"
        nodes.append({
            "id": f"finding:{slug}",
            "type": "finding",
            "title": f"{fid}: {title}",
            "tags": tags,
            "body": body,
            "frontmatter": {
                "claim_tier": tier,
                "severity": sev,
                "status": status,
                "agents": agents_list,
            },
        })
        # Edges: finding -> agent
        for ag in agents_list:
            ag_slug = _slug(ag)
            if any(s == ag_slug for _, _, s in agents_written):
                edges.append({"source": f"finding:{slug}", "target": f"agent:{ag_slug}"})
        # Edge: finding -> gate
        gate_id = _gate_for_finding(row, gate_rows)
        if gate_id:
            g_slug = _slug(gate_id)
            if any(s == g_slug for _, _, s in gates_written):
                edges.append({"source": f"finding:{slug}", "target": f"gate:{g_slug}"})

    for gid, title, slug in gates_written:
        row = gate_row_by_id.get(gid, {})
        approver = (row.get("approved_by_(name)") or
                    row.get("approved_by") or
                    row.get("approver_role") or "").strip()
        decision = (row.get("decision") or "").strip()
        date = (row.get("date") or "").strip()
        notes = (row.get("notes") or row.get("rationale") or "").strip()
        tags = ["gate"]
        if date:
            tags.append(date[:4])
        body = f"Gate {gid}\nDecision: {decision}\nApprover: {approver}\n{notes}"
        nodes.append({
            "id": f"gate:{slug}",
            "type": "gate",
            "title": f"Gate {gid}: {title[:60]}",
            "tags": tags,
            "body": body,
            "frontmatter": {
                "approver": approver,
                "decision": decision[:80] if decision else "",
                "date": date,
            },
        })
        # Edges: gate -> findings it references
        ref_findings = _findings_for_gate(row, finding_rows)
        for rfid in ref_findings:
            r_slug = _slug(rfid)
            if any(s == r_slug for _, _, s in findings_written):
                edges.append({"source": f"gate:{slug}", "target": f"finding:{r_slug}"})

    for name, title, slug in agents_written:
        content = agent_content_by_slug.get(slug, "")
        tags = ["agent", slug]
        nodes.append({
            "id": f"agent:{slug}",
            "type": "agent",
            "title": f"Agent: {name}",
            "tags": tags,
            "body": content[:500],
            "frontmatter": {"name": name},
        })

    return {"nodes": nodes, "edges": edges}


def write_viz(out_dir, bundle):
    """Write viz.html with embedded bundle JSON."""
    escaped = json.dumps(bundle, ensure_ascii=False).replace("</", "<\\/")
    html = _VIZ_TEMPLATE.replace("__BUNDLE_JSON__", escaped)
    _write(os.path.join(out_dir, "viz.html"), html)
    return html


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def export(root, out_dir):
    """Full export: parse inputs, write bundle, return summary."""
    os.makedirs(out_dir, exist_ok=True)

    # Parse inputs
    finding_rows = parse_ledger(root)
    gate_rows = parse_gates(root)
    agent_outputs_list = parse_agent_outputs(root)
    provenance = parse_provenance(root)  # available if needed

    # Collect agent names (slugged) for cross-link validation
    agent_names_raw = {name for name, _ in agent_outputs_list}
    agent_name_slugs = {_slug(n) for n in agent_names_raw}

    # Write all node files
    findings_written = write_findings(out_dir, finding_rows, gate_rows, agent_names_raw)
    gates_written = write_gates(out_dir, gate_rows, finding_rows)
    agents_written = write_agents(out_dir, agent_outputs_list)

    # Write index files
    write_subdir_index(out_dir, "findings", findings_written,
                       "All findings from the run ledger.")
    write_subdir_index(out_dir, "gates", gates_written,
                       "Human approval gates from governance/GATES.md.")
    write_subdir_index(out_dir, "agents", agents_written,
                       "Agent output markdowns from agent_outputs/.")
    write_root_index(out_dir, findings_written, gates_written, agents_written)

    # Build and write viz.html
    bundle = build_viz_json(findings_written, gates_written, agents_written,
                            finding_rows, gate_rows, agent_outputs_list)
    write_viz(out_dir, bundle)

    return {
        "findings": len(findings_written),
        "gates": len(gates_written),
        "agents": len(agents_written),
        "nodes": len(bundle["nodes"]),
        "edges": len(bundle["edges"]),
    }


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Export a Cambium run as an Open Knowledge Format (OKF) bundle."
    )
    ap.add_argument("--out", default="okf_bundle",
                    help="Output directory for the OKF bundle (default: okf_bundle)")
    ap.add_argument("--root", default=".",
                    help="Root of the Cambium repo (default: current directory)")
    args = ap.parse_args(argv)

    root = os.path.abspath(args.root)
    out_dir = os.path.abspath(args.out)

    print(f"[okf-export] root={root}")
    print(f"[okf-export] out={out_dir}")

    summary = export(root, out_dir)

    print(f"[okf-export] findings={summary['findings']}  gates={summary['gates']}  "
          f"agents={summary['agents']}")
    print(f"[okf-export] graph: {summary['nodes']} nodes, {summary['edges']} edges")
    print(f"[okf-export] bundle written -> {out_dir}")
    print(f"[okf-export] open {os.path.join(out_dir, 'viz.html')} in a browser")
    return 0


if __name__ == "__main__":
    sys.exit(main())
