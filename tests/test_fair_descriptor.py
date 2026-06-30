"""Tests for tools/fair_descriptor.py. Stdlib + tmp dirs only."""
import os
import sys
import json
import tempfile

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_REPO, "tools"))

import fair_descriptor as F


def _seed(root):
    os.makedirs(os.path.join(root, "agent_outputs"), exist_ok=True)
    os.makedirs(os.path.join(root, "governance"), exist_ok=True)
    with open(os.path.join(root, "agent_outputs", "fit_map.md"), "w", encoding="utf-8") as fh:
        fh.write("# fit map\n")
    with open(os.path.join(root, "governance", "audit_trail.jsonl"), "w", encoding="utf-8") as fh:
        fh.write('{"turn": 1}\n')


def test_descriptor_is_valid_data_package_shape():
    with tempfile.TemporaryDirectory() as root:
        _seed(root)
        d = F.build_descriptor(root, "pkg")
        assert d["name"] == "pkg"
        assert d["profile"] == "data-package"
        assert isinstance(d["resources"], list) and d["resources"]


def test_resources_have_required_fields():
    with tempfile.TemporaryDirectory() as root:
        _seed(root)
        d = F.build_descriptor(root, "pkg")
        for r in d["resources"]:
            assert r["name"] and r["path"] and r["format"] and r["mediatype"]


def test_fair_block_has_four_facets():
    with tempfile.TemporaryDirectory() as root:
        _seed(root)
        d = F.build_descriptor(root, "pkg")
        for facet in ("findable", "accessible", "interoperable", "reusable"):
            assert facet in d["fair"]


def test_license_is_present():
    with tempfile.TemporaryDirectory() as root:
        _seed(root)
        d = F.build_descriptor(root, "pkg")
        assert d["licenses"][0]["name"] == "MIT"


def test_empty_root_yields_zero_resources():
    with tempfile.TemporaryDirectory() as root:
        d = F.build_descriptor(root, "pkg")
        assert d["resources"] == []


def test_no_em_dash():
    with tempfile.TemporaryDirectory() as root:
        _seed(root)
        d = F.build_descriptor(root, "pkg")
        assert chr(0x2014) not in json.dumps(d)


def test_cli_writes_datapackage(tmp_path):
    root = str(tmp_path)
    _seed(root)
    out = os.path.join(root, "datapackage.json")
    rc = F.main(["--root", root, "--out", out, "--name", "cambium-run-outputs"])
    assert rc == 0
    parsed = json.loads(open(out, encoding="utf-8").read())
    assert parsed["name"] == "cambium-run-outputs"
    assert len(parsed["resources"]) >= 2
