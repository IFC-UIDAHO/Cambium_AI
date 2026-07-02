"""Tests for tools/glossary_gen.py -- auto-glossary from docs and skills.

All tests use tmp fixture roots. This suite never writes into the real
repo's docs/ directory.
"""
import os
import shutil
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
import glossary_gen as GG


def _write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)


def _tmp_root():
    return tempfile.mkdtemp()


def test_extracts_bold_colon_pattern():
    root = _tmp_root()
    try:
        _write(os.path.join(root, "docs", "a.md"), "**Gate**: A checkpoint where a run pauses.\n")
        entries, dup = GG.scan(root)
        assert dup == 0
        assert any(e["term"] == "Gate" and "checkpoint" in e["definition"] for e in entries)
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_extracts_dash_pattern_at_line_start():
    root = _tmp_root()
    try:
        _write(os.path.join(root, "docs", "b.md"), "Council - A team of related agents.\n")
        entries, dup = GG.scan(root)
        assert any(e["term"] == "Council" and "team of related agents" in e["definition"] for e in entries)
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_dash_pattern_mid_sentence_not_misread():
    root = _tmp_root()
    try:
        _write(os.path.join(root, "docs", "c.md"),
               "This is a long prose sentence about something - and it continues here with more words.\n")
        entries, dup = GG.scan(root)
        # the "term" before " - " here is way more than 6 words, so it must not be captured
        assert not any(_word_over_limit(e) for e in entries)
    finally:
        shutil.rmtree(root, ignore_errors=True)


def _word_over_limit(entry):
    return len(entry["term"].split()) > 6


def test_dedupe_with_duplicate_counting():
    root = _tmp_root()
    try:
        _write(os.path.join(root, "docs", "a.md"), "**Gate**: First definition wins.\n")
        _write(os.path.join(root, "docs", "z.md"), "**gate**: A different, later definition.\n")
        entries, dup = GG.scan(root)
        gate_entries = [e for e in entries if e["term"].lower() == "gate"]
        assert len(gate_entries) == 1
        assert gate_entries[0]["definition"] == "First definition wins."
        assert dup == 1
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_alphabetical_order():
    root = _tmp_root()
    try:
        _write(os.path.join(root, "docs", "a.md"),
               "**Zebra**: last alphabetically.\n**Apple**: first alphabetically.\n**Mango**: middle.\n")
        entries, dup = GG.scan(root)
        terms = [e["term"] for e in entries]
        assert terms == sorted(terms, key=str.lower)
        assert terms.index("Apple") < terms.index("Mango") < terms.index("Zebra")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_source_attribution_in_markdown_output():
    root = _tmp_root()
    try:
        _write(os.path.join(root, "docs", "sub", "topic.md"), "**Term**: A definition.\n")
        entries, dup = GG.scan(root)
        assert entries[0]["source"] == "docs/sub/topic.md"
        md = GG.build_markdown(entries, dup, len(entries) + dup)
        assert "docs/sub/topic.md" in md
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_skill_frontmatter_extraction():
    root = _tmp_root()
    try:
        skill_md = (
            "---\n"
            "name: statistics\n"
            "description: Rigorous statistical inference done correctly.\n"
            "---\n\n# Statistics\n"
        )
        _write(os.path.join(root, "skills", "statistics", "SKILL.md"), skill_md)
        entries, dup = GG.scan(root)
        assert any(e["term"] == "statistics" and "Rigorous statistical inference" in e["definition"]
                   for e in entries)
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_empty_scan_exits_1():
    root = _tmp_root()
    try:
        os.makedirs(os.path.join(root, "docs"), exist_ok=True)
        os.makedirs(os.path.join(root, "skills"), exist_ok=True)
        with pytest.raises(SystemExit) as excinfo:
            GG.main(["--root", root, "--out", os.path.join(root, "out.md")])
        assert excinfo.value.code == 1
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_write_repo_flag_targets_docs_reference_path_in_tmp_root():
    root = _tmp_root()
    try:
        _write(os.path.join(root, "docs", "a.md"), "**Gate**: A checkpoint.\n")
        rc = GG.main(["--root", root, "--write-repo"])
        assert rc == 0
        expected = os.path.join(root, "docs", "reference", "GLOSSARY.md")
        assert os.path.exists(expected)
    finally:
        shutil.rmtree(root, ignore_errors=True)
