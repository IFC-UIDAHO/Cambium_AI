"""tests/test_okf_export.py — Tests for tools/okf_export.py

Test the OKF bundle output:
  - bundle is created in the expected layout
  - every .md has valid YAML frontmatter
  - index.md files exist (root + each subdir)
  - cross-links in findings resolve to files that exist
  - viz.html is self-contained: contains embedded JSON and a cytoscape script tag,
    no template placeholders
"""
import csv
import json
import os
import re
import sys
import tempfile
import textwrap

# Allow importing the tool module directly
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import okf_export


# ---------------------------------------------------------------------------
# Fixture builder
# ---------------------------------------------------------------------------

def _make_tmp_repo():
    """Create a minimal fake Cambium repo in a temp dir. Returns (repo_dir, out_dir)."""
    tmp = tempfile.mkdtemp()
    repo = os.path.join(tmp, "repo")
    os.makedirs(repo)

    # agent_outputs/findings_ledger.csv
    ao = os.path.join(repo, "agent_outputs")
    os.makedirs(ao)
    with open(os.path.join(ao, "findings_ledger.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["id", "issue", "agents", "severity", "claim_tier",
                    "evidence", "status", "action"])
        w.writerow(["F1", "Yield effect", "lab-statistics;verify-evidence",
                    "P2", "Code-verified",
                    "rerun `python3 code/analysis.py`", "accepted", "cmd: python3 code/analysis.py"])
        w.writerow(["F2", "Rainfall interaction", "lab-methods",
                    "P1", "Open",
                    "model not yet fit", "open", "defer to G4"])

    # agent_outputs/lab-statistics.md
    with open(os.path.join(ao, "lab-statistics.md"), "w", encoding="utf-8") as fh:
        fh.write(textwrap.dedent("""\
            # Lab Statistics Output

            Statistical analysis of yield effect.

            F1 shows significance at p<0.001.
        """))

    # agent_outputs/verify-evidence.md
    with open(os.path.join(ao, "verify-evidence.md"), "w", encoding="utf-8") as fh:
        fh.write(textwrap.dedent("""\
            # Verify Evidence Output

            Evidence verification complete. F1 code-verified via analysis.py.
        """))

    # governance/GATES.md
    gov = os.path.join(repo, "governance")
    os.makedirs(gov)
    with open(os.path.join(gov, "GATES.md"), "w", encoding="utf-8") as fh:
        fh.write(textwrap.dedent("""\
            # Human Approval Ledger

            | Gate | Decision | Approver role | Approved by (name) | Date | Notes |
            |---|---|---|---|---|---|
            | G1 | Pursue RFP | Director | Dr. Smith | 2025-02-10 | Initial go |
            | G4 | Apply fixes for F1 and F2 workstream | Area Lead | Dr. Jones | 2025-09-12 | F1 verified; F2 deferred |
        """))

    out_dir = os.path.join(tmp, "bundle")
    return repo, out_dir


# ---------------------------------------------------------------------------
# YAML frontmatter parsing (stdlib only)
# ---------------------------------------------------------------------------

def _parse_frontmatter(md_content):
    """Extract and parse YAML frontmatter from a markdown string.

    Returns a dict (possibly empty) or raises AssertionError on malformed FM.
    Only handles the scalar/list types we produce.
    """
    lines = md_content.splitlines()
    if not lines or lines[0].strip() != "---":
        return None  # no frontmatter
    end = None
    for i, line in enumerate(lines[1:], 1):
        if line.strip() == "---":
            end = i
            break
    if end is None:
        return None
    fm_lines = lines[1:end]
    result = {}
    current_key = None
    current_list = None
    for line in fm_lines:
        # List item
        if line.startswith("  - "):
            val = line[4:].strip()
            # strip surrounding quotes if json-quoted
            try:
                val = json.loads(val)
            except (json.JSONDecodeError, ValueError):
                pass
            if current_list is not None:
                current_list.append(val)
            continue
        # Key: value
        if ":" in line:
            colon = line.index(":")
            key = line[:colon].strip()
            val_raw = line[colon + 1:].strip()
            current_key = key
            current_list = None
            if val_raw == "" or val_raw == "[]":
                if val_raw == "[]":
                    result[key] = []
                else:
                    # Might be start of a list
                    result[key] = []
                    current_list = result[key]
            else:
                try:
                    result[key] = json.loads(val_raw)
                except (json.JSONDecodeError, ValueError):
                    result[key] = val_raw
    return result


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_bundle_created():
    """The export creates the expected directory structure."""
    repo, out_dir = _make_tmp_repo()
    summary = okf_export.export(repo, out_dir)
    assert os.path.isdir(out_dir), "bundle dir not created"
    assert summary["findings"] == 2
    assert summary["gates"] == 2
    assert summary["agents"] == 2


def test_all_md_have_valid_frontmatter():
    """Every .md in the bundle has parseable YAML frontmatter with required keys."""
    repo, out_dir = _make_tmp_repo()
    okf_export.export(repo, out_dir)

    required_by_type = {
        "finding": {"type", "id", "title", "timestamp"},
        "gate": {"type", "id", "timestamp"},
        "agent": {"type", "id", "title", "timestamp"},
    }

    for dirpath, dirnames, filenames in os.walk(out_dir):
        for fname in filenames:
            if not fname.endswith(".md") or fname == "index.md":
                continue
            path = os.path.join(dirpath, fname)
            content = open(path, encoding="utf-8").read()
            fm = _parse_frontmatter(content)
            assert fm is not None, f"{path}: no YAML frontmatter found"
            assert "type" in fm, f"{path}: frontmatter missing 'type'"
            node_type = fm.get("type", "")
            for key in required_by_type.get(node_type, {"type", "id", "timestamp"}):
                assert key in fm, f"{path}: frontmatter missing required key '{key}'"


def test_index_files_exist():
    """Root index.md and each subdir index.md must exist."""
    repo, out_dir = _make_tmp_repo()
    okf_export.export(repo, out_dir)

    expected = [
        os.path.join(out_dir, "index.md"),
        os.path.join(out_dir, "findings", "index.md"),
        os.path.join(out_dir, "gates", "index.md"),
        os.path.join(out_dir, "agents", "index.md"),
    ]
    for path in expected:
        assert os.path.isfile(path), f"index.md missing: {path}"


def test_crosslinks_resolve():
    """Every cross-link listed in a finding's frontmatter must resolve to an existing file."""
    repo, out_dir = _make_tmp_repo()
    okf_export.export(repo, out_dir)

    findings_dir = os.path.join(out_dir, "findings")
    for fname in os.listdir(findings_dir):
        if fname == "index.md" or not fname.endswith(".md"):
            continue
        path = os.path.join(findings_dir, fname)
        content = open(path, encoding="utf-8").read()
        fm = _parse_frontmatter(content)
        links = fm.get("links", []) if fm else []
        if not isinstance(links, list):
            links = [links]
        for link in links:
            if not link:
                continue
            # Resolve relative to findings/
            abs_link = os.path.normpath(os.path.join(findings_dir, link))
            assert os.path.isfile(abs_link), \
                f"Cross-link {link!r} in {fname} does not resolve to an existing file"


def test_viz_html_self_contained():
    """viz.html must be a single self-contained file with:
       - embedded JSON bundle (contains 'nodes' and 'edges')
       - cytoscape script tag
       - no template placeholders (__...__).
    """
    repo, out_dir = _make_tmp_repo()
    okf_export.export(repo, out_dir)

    viz_path = os.path.join(out_dir, "viz.html")
    assert os.path.isfile(viz_path), "viz.html not found"
    html = open(viz_path, encoding="utf-8").read()

    # Must contain cytoscape script tag
    assert "cytoscape" in html.lower(), "viz.html has no cytoscape reference"

    # Must contain embedded JSON blob with nodes/edges
    assert '"nodes"' in html, "viz.html missing embedded nodes JSON"
    assert '"edges"' in html, "viz.html missing embedded edges JSON"

    # Must have no template placeholders
    placeholders = re.findall(r"__[A-Z_]+__", html)
    assert not placeholders, f"viz.html has unresolved placeholders: {placeholders}"


def test_viz_html_contains_finding_ids():
    """The embedded JSON in viz.html should reference the finding IDs."""
    repo, out_dir = _make_tmp_repo()
    okf_export.export(repo, out_dir)

    html = open(os.path.join(out_dir, "viz.html"), encoding="utf-8").read()
    assert "F1" in html, "viz.html does not mention F1"
    assert "F2" in html, "viz.html does not mention F2"


def test_finding_md_body_has_evidence():
    """Each finding .md body should contain the evidence text."""
    repo, out_dir = _make_tmp_repo()
    okf_export.export(repo, out_dir)

    f1_path = os.path.join(out_dir, "findings", "f1.md")
    assert os.path.isfile(f1_path), "findings/f1.md not found"
    content = open(f1_path, encoding="utf-8").read()
    assert "analysis.py" in content, "F1 evidence text not found in findings/f1.md"


def test_gate_md_has_approver():
    """Each gate .md body should contain the approver name."""
    repo, out_dir = _make_tmp_repo()
    okf_export.export(repo, out_dir)

    g1_path = os.path.join(out_dir, "gates", "g1.md")
    assert os.path.isfile(g1_path), "gates/g1.md not found"
    content = open(g1_path, encoding="utf-8").read()
    assert "Smith" in content, "Approver 'Dr. Smith' not found in gates/g1.md"


def test_agents_md_created():
    """Each agent output .md should produce an agents/<name>.md."""
    repo, out_dir = _make_tmp_repo()
    okf_export.export(repo, out_dir)

    for slug in ["lab-statistics", "verify-evidence"]:
        path = os.path.join(out_dir, "agents", f"{slug}.md")
        assert os.path.isfile(path), f"agents/{slug}.md not found"


def test_graceful_on_missing_inputs():
    """Export must succeed (degrade gracefully) even when no inputs exist."""
    tmp = tempfile.mkdtemp()
    repo = os.path.join(tmp, "empty_repo")
    os.makedirs(repo)
    out_dir = os.path.join(tmp, "empty_bundle")

    # Should not raise
    summary = okf_export.export(repo, out_dir)
    assert summary["findings"] == 0
    assert summary["gates"] == 0
    assert summary["agents"] == 0
    # Root index and viz.html should still be written
    assert os.path.isfile(os.path.join(out_dir, "index.md"))
    assert os.path.isfile(os.path.join(out_dir, "viz.html"))


def test_slug_is_deterministic():
    """The slug function must be stable (deterministic)."""
    assert okf_export._slug("lab-statistics") == "lab-statistics"
    assert okf_export._slug("F1") == "f1"
    assert okf_export._slug("G4") == "g4"
    assert okf_export._slug("verify evidence") == "verify-evidence"


def test_parse_ledger_returns_correct_rows():
    """parse_ledger must return exactly the rows written."""
    repo, out_dir = _make_tmp_repo()
    rows = okf_export.parse_ledger(repo)
    assert len(rows) == 2
    ids = [r.get("id") for r in rows]
    assert "F1" in ids and "F2" in ids


def test_parse_gates_returns_correct_rows():
    """parse_gates must return the two gates we wrote."""
    repo, out_dir = _make_tmp_repo()
    gates = okf_export.parse_gates(repo)
    assert len(gates) == 2
    gate_ids = [g.get("gate") for g in gates]
    assert "G1" in gate_ids and "G4" in gate_ids
