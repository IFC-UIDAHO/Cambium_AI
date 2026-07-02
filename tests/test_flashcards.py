"""Tests for tools/flashcards.py -- spaced-repetition deck generation from markdown."""
import os
import shutil
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
import flashcards as FC

FIXTURE_DOC = """# Deck source

**Agent**: A named specialist with a single job.
**Council**: A team of related agents.
Gate - A checkpoint where a run pauses for a human decision.
Evidence tier - A label for how well a claim is backed.
"""

EMPTY_DOC = """# Nothing here

Just prose, no term-definition lines.
"""


def _tmpdir():
    return tempfile.mkdtemp()


def test_extract_cards_matches_fixture_terms():
    cards = FC.extract_cards(FIXTURE_DOC)
    fronts = {f for f, _ in cards}
    assert fronts == {"Agent", "Council", "Gate", "Evidence tier"}
    assert len(cards) == 4


def test_anki_escape_handles_tab_and_newline():
    field = "line one\twith a tab\nand a newline"
    escaped = FC._anki_escape(field)
    assert "\t" not in escaped
    assert "\n" not in escaped
    assert "<br>" in escaped
    assert "with a tab" in escaped and "and a newline" in escaped


def test_tsv_output_escapes_tab_and_newline_in_definition():
    cards = [("Term", "A definition\twith a tab\nand a newline")]
    tsv = FC.build_tsv(cards)
    lines = tsv.strip("\n").split("\n")
    assert len(lines) == 1
    front, back = lines[0].split("\t")
    assert front == "Term"
    assert "\t" not in back
    assert "\n" not in back
    assert "<br>" in back


def test_deck_size_matches_fixture_terms_end_to_end():
    d = _tmpdir()
    try:
        doc_path = os.path.join(d, "doc.md")
        with open(doc_path, "w", encoding="utf-8") as fh:
            fh.write(FIXTURE_DOC)
        out = os.path.join(d, "deck.html")
        rc = FC.main(["--doc", doc_path, "--out", out])
        assert rc == 0
        tsv_path = os.path.join(d, "deck.tsv")
        tsv_lines = open(tsv_path, encoding="utf-8").read().strip("\n").split("\n")
        assert len(tsv_lines) == 4
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_html_is_self_contained_no_http_src():
    d = _tmpdir()
    try:
        doc_path = os.path.join(d, "doc.md")
        with open(doc_path, "w", encoding="utf-8") as fh:
            fh.write(FIXTURE_DOC)
        out = os.path.join(d, "deck.html")
        rc = FC.main(["--doc", doc_path, "--out", out])
        assert rc == 0
        html_text = open(out, encoding="utf-8").read()
        assert "http://" not in html_text
        assert "https://" not in html_text
        assert "src=\"http" not in html_text
        assert "localStorage" not in html_text
        assert "Export progress" in html_text
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_determinism_same_input_same_tsv():
    d = _tmpdir()
    try:
        doc_path = os.path.join(d, "doc.md")
        with open(doc_path, "w", encoding="utf-8") as fh:
            fh.write(FIXTURE_DOC)
        out1 = os.path.join(d, "deck1.html")
        out2 = os.path.join(d, "deck2.html")
        rc1 = FC.main(["--doc", doc_path, "--out", out1])
        rc2 = FC.main(["--doc", doc_path, "--out", out2])
        assert rc1 == 0 and rc2 == 0
        tsv1 = open(os.path.join(d, "deck1.tsv"), encoding="utf-8").read()
        tsv2 = open(os.path.join(d, "deck2.tsv"), encoding="utf-8").read()
        assert tsv1 == tsv2
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_empty_doc_exits_1():
    d = _tmpdir()
    try:
        doc_path = os.path.join(d, "empty.md")
        with open(doc_path, "w", encoding="utf-8") as fh:
            fh.write(EMPTY_DOC)
        out = os.path.join(d, "deck.html")
        rc = FC.main(["--doc", doc_path, "--out", out])
        assert rc == 1
        assert not os.path.exists(out)
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_missing_doc_exits_2():
    d = _tmpdir()
    try:
        with pytest.raises(SystemExit) as excinfo:
            FC.main(["--doc", os.path.join(d, "nope.md"), "--out", os.path.join(d, "deck.html")])
        assert excinfo.value.code == 2
    finally:
        shutil.rmtree(d, ignore_errors=True)
