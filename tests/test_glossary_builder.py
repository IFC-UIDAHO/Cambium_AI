"""Tests for tools/glossary_builder.py. Synthetic markdown in tmp_path; offline."""
import os
import subprocess
import sys

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_REPO, "tools"))
import glossary_builder as GB

SCRIPT = os.path.join(_REPO, "tools", "glossary_builder.py")

DOC_A = """# Notes on governance

A **gate** is a checkpoint where the run pauses for a human decision.
The `orchestrator` refers to the chief of staff that dispatches specialists.

- Zebra term: a deliberately late-alphabet entry for ordering checks.

## Evidence tier

Evidence tier means the grade of support behind a claim. Second sentence here.
"""

DOC_B = """# Other notes

An **agent** is a named specialist with a single job.

Note: this label line must be skipped.
"""


def _run(args):
    r = subprocess.run([sys.executable, SCRIPT] + args, capture_output=True, text=True)
    return r.returncode, r.stdout, r.stderr


def _write(tmp_path):
    d = tmp_path / "docs"
    d.mkdir()
    (d / "a.md").write_text(DOC_A, encoding="utf-8")
    (d / "b.md").write_text(DOC_B, encoding="utf-8")
    return d


def test_help_exits_zero():
    rc, out, _ = _run(["--help"])
    assert rc == 0
    assert "--quiz" in out


def test_rules_and_banner(tmp_path):
    d = _write(tmp_path)
    rc, out, _ = _run(["--sources", str(d)])
    assert rc == 0
    assert "auto-extracted, review before teaching" in out
    assert "- **gate**: is a checkpoint" in out            # bold + is
    assert "- **orchestrator**: refers to the chief" in out  # code + refers to
    assert "- **Zebra term**: a deliberately late-alphabet" in out  # Term: line
    assert "- **Evidence tier**: Evidence tier means the grade" in out  # heading rule
    assert "Second sentence" not in out                    # first sentence only
    assert "**Note**" not in out                           # label stoplist


def test_alphabetized_with_sources(tmp_path):
    d = _write(tmp_path)
    rc, out, _ = _run(["--sources", str(d)])
    assert rc == 0
    entries = [l for l in out.splitlines() if l.startswith("- **")]
    terms = [l.split("**")[1] for l in entries]
    assert terms == sorted(terms, key=str.casefold)
    assert all("(source: " in l and ".md)" in l for l in entries)


def test_quiz_blanks_term(tmp_path):
    d = _write(tmp_path)
    rc, out, _ = _run(["--sources", str(d), "--quiz"])
    assert rc == 0
    assert "Fill-in-the-blank quiz" in out
    quiz = out.split("Fill-in-the-blank quiz")[1]
    # the heading-rule entry repeats its term in the definition: must be blanked
    assert "____ means the grade of support" in quiz
    assert "Evidence tier means the grade" not in quiz
    assert "<summary>Answer</summary>" in quiz


def test_guards(tmp_path):
    d = _write(tmp_path)
    rc, out, _ = _run(["--sources", str(d), "--max-terms", "2"])
    assert rc == 0
    assert sum(1 for l in out.splitlines() if l.startswith("- **")) == 2
    rc, out, _ = _run(["--sources", str(d), "--min-len", "6"])
    assert rc == 0
    assert "- **gate**" not in out          # 4 chars, filtered
    assert "- **orchestrator**" in out
    rc, _, _ = _run(["--sources", str(d), "--max-terms", "0"])
    assert rc == 1


def test_single_file_source(tmp_path):
    f = tmp_path / "one.md"
    f.write_text(DOC_B, encoding="utf-8")
    rc, out, _ = _run(["--sources", str(f)])
    assert rc == 0
    assert "- **agent**" in out


def test_invalid_inputs(tmp_path):
    rc, _, err = _run(["--sources", str(tmp_path / "missing.md")])
    assert rc == 1
    assert "not found" in err
    empty = tmp_path / "empty.md"
    empty.write_text("nothing that defines anything\n", encoding="utf-8")
    rc, _, err = _run(["--sources", str(empty)])
    assert rc == 1
    assert "no term/definition patterns" in err
