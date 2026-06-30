"""Tests for the JSON export added to tools/ai_disclosure.py. Stdlib + tmp dirs only."""
import os
import sys
import json
import tempfile

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_REPO, "tools"))

import ai_disclosure as A


def _seed(root):
    os.makedirs(os.path.join(root, "agent_outputs"), exist_ok=True)
    os.makedirs(os.path.join(root, "governance"), exist_ok=True)
    with open(os.path.join(root, "governance", "GATES.md"), "w", encoding="utf-8") as fh:
        fh.write(
            "| Gate | Decision | Approver role | Approved by | Date |\n"
            "|---|---|---|---|---|\n"
            "| G4 | accept | Director | Jaslam | 2026-06-30 |\n"
        )


def test_data_has_schema_and_disclaimer():
    with tempfile.TemporaryDirectory() as root:
        _seed(root)
        d = A.build_disclosure_data(root, "Deliverable")
        assert d["schema"] == "cambium.ai_use_disclosure/1"
        assert "not a certification" in d["disclaimer"].lower()


def test_data_lists_gates():
    with tempfile.TemporaryDirectory() as root:
        _seed(root)
        d = A.build_disclosure_data(root, "Deliverable")
        assert d["human_gates"][0]["approved_by"] == "Jaslam"


def test_data_no_em_dash():
    with tempfile.TemporaryDirectory() as root:
        _seed(root)
        d = A.build_disclosure_data(root, "Deliverable")
        assert chr(0x2014) not in json.dumps(d)


def test_cli_json_format_writes_valid_json(tmp_path):
    root = str(tmp_path)
    _seed(root)
    out = os.path.join(root, "disc.json")
    rc = A.main(["--root", root, "--title", "X", "--format", "json", "--out", out])
    assert rc == 0
    parsed = json.loads(open(out, encoding="utf-8").read())
    assert parsed["deliverable"] == "X"


def test_cli_md_still_works(tmp_path):
    root = str(tmp_path)
    _seed(root)
    out = os.path.join(root, "disc.md")
    rc = A.main(["--root", root, "--title", "X", "--format", "md", "--out", out])
    assert rc == 0
    assert "AI-Use Disclosure" in open(out, encoding="utf-8").read()
