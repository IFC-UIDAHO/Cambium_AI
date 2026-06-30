"""Tests for tools/ai_disclosure.py.

Uses only stdlib and tmp dirs. Never writes to the live repo data.
"""
import os
import sys
import json
import tempfile

# Make sure tools/ is importable
_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_REPO, "tools"))

import ai_disclosure as D


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_root(tmp_path, gates_md=None, audit_jsonl=None, agent_files=None, agent_cards=None):
    """Populate a minimal fake data root and return its path."""
    gov = os.path.join(tmp_path, "governance")
    os.makedirs(gov, exist_ok=True)
    ao = os.path.join(tmp_path, "agent_outputs")
    os.makedirs(ao, exist_ok=True)

    if gates_md is not None:
        with open(os.path.join(gov, "GATES.md"), "w", encoding="utf-8") as fh:
            fh.write(gates_md)

    if audit_jsonl is not None:
        with open(os.path.join(gov, "audit_trail.jsonl"), "w", encoding="utf-8") as fh:
            for rec in audit_jsonl:
                fh.write(json.dumps(rec) + "\n")

    if agent_files is not None:
        for name, content in agent_files.items():
            with open(os.path.join(ao, name), "w", encoding="utf-8") as fh:
                fh.write(content)

    if agent_cards is not None:
        with open(os.path.join(tmp_path, "agent_cards.json"), "w", encoding="utf-8") as fh:
            json.dump(agent_cards, fh)

    return tmp_path


_GATES_MD = """# Human Approval Ledger -- Demo Project

| Gate | Decision | Approver role | Approved by (name) | Date | Notes |
|---|---|---|---|---|---|
| G1 | Pursue the NSF call | Director | Dr. Ada Lovelace | 2025-03-01 | Initial decision |
| G3 | Submit proposal | Director | Dr. Ada Lovelace | 2025-04-10 | All checks passed |
"""


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_disclosure_has_required_sections():
    """build_disclosure must produce all five labelled sections."""
    with tempfile.TemporaryDirectory() as tmp:
        _make_root(tmp, gates_md=_GATES_MD)
        text = D.build_disclosure(tmp, "Test Proposal")
    for section in ["## A. Summary", "## B. AI Systems", "## C. Human Oversight",
                    "## D. Evidence", "## E. Disclaimer"]:
        assert section in text, f"Missing section: {section}"


def test_disclosure_contains_approver_names():
    """Gate approver names must appear in the disclosure output."""
    with tempfile.TemporaryDirectory() as tmp:
        _make_root(tmp, gates_md=_GATES_MD)
        text = D.build_disclosure(tmp, "Test Proposal")
    assert "Dr. Ada Lovelace" in text


def test_honest_disclaimer_present():
    """The disclaimer must say 'advisory' and NOT say 'validate' or 'certif'."""
    with tempfile.TemporaryDirectory() as tmp:
        _make_root(tmp, gates_md=_GATES_MD)
        text = D.build_disclosure(tmp, "Test Proposal")
    lower = text.lower()
    assert "advisory" in lower
    assert "validate" not in lower
    assert "certif" not in lower or "not a certif" in lower.replace("certification", "certif")


def test_disclosure_no_em_dashes():
    """No em dashes in the output (Cambium house rule)."""
    with tempfile.TemporaryDirectory() as tmp:
        _make_root(tmp, gates_md=_GATES_MD)
        text = D.build_disclosure(tmp, "Test Proposal")
    assert "—" not in text


def test_disclosure_without_gates_file():
    """build_disclosure must complete gracefully when GATES.md is absent."""
    with tempfile.TemporaryDirectory() as tmp:
        _make_root(tmp)  # no gates_md
        text = D.build_disclosure(tmp, "No Gates Deliverable")
    assert "## A. Summary" in text
    assert "## E. Disclaimer" in text


def test_disclosure_with_audit_trail():
    """Audit trail records should appear in the evidence section."""
    records = [
        {"turn": 1, "agent": "rfp-analyst", "action": "read RFP"},
        {"turn": 2, "agent": "budget-officer", "action": "drafted budget"},
    ]
    with tempfile.TemporaryDirectory() as tmp:
        _make_root(tmp, gates_md=_GATES_MD, audit_jsonl=records)
        text = D.build_disclosure(tmp, "With Audit Trail")
    assert "audit_trail.jsonl" in text
    assert "2 record" in text


def test_disclosure_with_agent_files():
    """Agent output files should contribute agent names."""
    agent_files = {
        "rfp-analyst_output.md": "# RFP Analysis\nSome content.",
        "budget-officer_output.md": "# Budget\nDraft budget.",
    }
    with tempfile.TemporaryDirectory() as tmp:
        _make_root(tmp, gates_md=_GATES_MD, agent_files=agent_files)
        text = D.build_disclosure(tmp, "With Agents")
    assert "rfp-analyst" in text or "budget-officer" in text


def test_disclosure_cli_writes_file():
    """CLI must write to the specified output path."""
    with tempfile.TemporaryDirectory() as tmp:
        _make_root(tmp, gates_md=_GATES_MD)
        out = os.path.join(tmp, "agent_outputs", "ai_use_disclosure.md")
        rc = D.main(["--root", tmp, "--out", out, "--title", "CLI Test"])
        assert rc == 0
        assert os.path.exists(out)
        content = open(out, encoding="utf-8").read()
        assert "## E. Disclaimer" in content


def test_gates_parser_returns_list():
    """_read_gates should parse the demo GATES.md to a non-empty list."""
    with tempfile.TemporaryDirectory() as tmp:
        _make_root(tmp, gates_md=_GATES_MD)
        gates = D._read_gates(tmp)
    assert len(gates) == 2
    assert gates[0]["gate"] == "G1"
    assert "Ada Lovelace" in gates[0]["approved_by"]


def test_gates_parser_absent_file():
    """_read_gates must return [] when the file does not exist."""
    with tempfile.TemporaryDirectory() as tmp:
        assert D._read_gates(tmp) == []


def test_disclosure_human_not_author_note():
    """The disclosure must state that AI is not the author."""
    with tempfile.TemporaryDirectory() as tmp:
        _make_root(tmp, gates_md=_GATES_MD)
        text = D.build_disclosure(tmp, "Author Check")
    assert "not an author" in text.lower()
