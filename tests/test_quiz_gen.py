"""Tests for tools/quiz_gen.py -- deterministic quiz generation from markdown."""
import json
import os
import shutil
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
import quiz_gen as QG

RICH_DOC = """# Sample module

**Agent**: A named specialist with a single job.
**Council**: A team of related agents.
Gate - A checkpoint where a run pauses for a human decision.
Evidence tier - A label for how well a claim is backed.

The orchestrator is the chief of staff of a run.
Verification is a separate council from the one that built the result.
A gate is a stop-and-decide checkpoint in the lifecycle.
"""

SPARSE_DOC = """# Nearly empty

Just some prose with no structure at all.
"""


def _tmpdir():
    return tempfile.mkdtemp()


def test_extract_terms_counts_on_rich_fixture():
    pairs = QG.extract_terms(RICH_DOC)
    terms = {t for t, _ in pairs}
    assert terms == {"Agent", "Council", "Gate", "Evidence tier"}
    assert len(pairs) == 4


def test_extract_sentences_finds_is_are_sentences():
    sentences = QG.extract_sentences(RICH_DOC)
    assert any("orchestrator is the chief of staff" in s for s in sentences)
    assert any("Verification is a separate council" in s for s in sentences)


def test_determinism_same_seed_identical_key():
    d = _tmpdir()
    try:
        doc_path = os.path.join(d, "doc.md")
        with open(doc_path, "w", encoding="utf-8") as fh:
            fh.write(RICH_DOC)
        out1 = os.path.join(d, "quiz1.html")
        out2 = os.path.join(d, "quiz2.html")
        rc1 = QG.main(["--doc", doc_path, "--out", out1, "--seed", "7"])
        rc2 = QG.main(["--doc", doc_path, "--out", out2, "--seed", "7"])
        assert rc1 == 0 and rc2 == 0
        key1 = json.load(open(os.path.splitext(out1)[0] + "_key.json", encoding="utf-8"))
        key2 = json.load(open(os.path.splitext(out2)[0] + "_key.json", encoding="utf-8"))
        assert key1["questions"] == key2["questions"]
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_repeat_run_same_seed_is_stable():
    d = _tmpdir()
    try:
        doc_path = os.path.join(d, "doc.md")
        with open(doc_path, "w", encoding="utf-8") as fh:
            fh.write(RICH_DOC)
        out_a = os.path.join(d, "a.html")
        rc = QG.main(["--doc", doc_path, "--out", out_a, "--seed", "3"])
        assert rc == 0
        key_a1 = json.load(open(os.path.splitext(out_a)[0] + "_key.json", encoding="utf-8"))
        rc = QG.main(["--doc", doc_path, "--out", out_a, "--seed", "3"])
        assert rc == 0
        key_a2 = json.load(open(os.path.splitext(out_a)[0] + "_key.json", encoding="utf-8"))
        assert key_a1 == key_a2
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_sparse_doc_exit_1():
    d = _tmpdir()
    try:
        doc_path = os.path.join(d, "sparse.md")
        with open(doc_path, "w", encoding="utf-8") as fh:
            fh.write(SPARSE_DOC)
        out = os.path.join(d, "quiz.html")
        rc = QG.main(["--doc", doc_path, "--out", out])
        assert rc == 1
        assert not os.path.exists(out)
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_html_contains_form_and_no_raw_script_from_content():
    d = _tmpdir()
    try:
        doc_path = os.path.join(d, "doc.md")
        # embed a script-like string as a definition to prove it gets escaped
        malicious = RICH_DOC + '\n**Payload**: <script>alert(1)</script> definition text\n'
        with open(doc_path, "w", encoding="utf-8") as fh:
            fh.write(malicious)
        out = os.path.join(d, "quiz.html")
        rc = QG.main(["--doc", doc_path, "--out", out])
        assert rc == 0
        html_text = open(out, encoding="utf-8").read()
        assert "<form" in html_text
        # the only literal <script> tags allowed are the tool's own JS block
        assert "<script>alert(1)</script>" not in html_text
        assert "&lt;script&gt;" in html_text
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_key_matches_embedded_answers():
    d = _tmpdir()
    try:
        doc_path = os.path.join(d, "doc.md")
        with open(doc_path, "w", encoding="utf-8") as fh:
            fh.write(RICH_DOC)
        out = os.path.join(d, "quiz.html")
        rc = QG.main(["--doc", doc_path, "--out", out, "--seed", "7"])
        assert rc == 0
        html_text = open(out, encoding="utf-8").read()
        key = json.load(open(os.path.splitext(out)[0] + "_key.json", encoding="utf-8"))
        for q in key["questions"]:
            assert f'data-id="{q["id"]}"' in html_text
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_max_questions_caps_output():
    d = _tmpdir()
    try:
        doc_path = os.path.join(d, "doc.md")
        with open(doc_path, "w", encoding="utf-8") as fh:
            fh.write(RICH_DOC)
        out = os.path.join(d, "quiz.html")
        rc = QG.main(["--doc", doc_path, "--out", out, "--max-questions", "3"])
        assert rc == 0
        key = json.load(open(os.path.splitext(out)[0] + "_key.json", encoding="utf-8"))
        assert len(key["questions"]) == 3
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_missing_doc_exits_2():
    d = _tmpdir()
    try:
        with pytest.raises(SystemExit) as excinfo:
            QG.main(["--doc", os.path.join(d, "nope.md"), "--out", os.path.join(d, "q.html")])
        assert excinfo.value.code == 2
    finally:
        shutil.rmtree(d, ignore_errors=True)
