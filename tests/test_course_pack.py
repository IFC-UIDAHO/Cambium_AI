"""Tests for tools/course_pack.py. Synthetic packets/refs in tmp_path; offline."""
import os
import subprocess
import sys

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_REPO, "tools"))
import course_pack as CP

SCRIPT = os.path.join(_REPO, "tools", "course_pack.py")

PACKET_A = """# Learning Packet: Gates and approvals

## What a gate is

Body.

## Separation of duties

Body.

## Flashcards

- Q: x
  A: y
"""

PACKET_B = """# Evidence tiers

## Proved versus Code-verified

Body.
"""

REFS_BIB = """@article{smith2020,
  author = {Smith, A. and Jones, B.},
  title = {Honest Reporting in Research},
  year = {2020}
}
@book{lee2021,
  author = {Lee, C.},
  title = {Gatekeeping for Good},
  year = {2021},
}
@misc{doe2022, title = {Verification Basics}, year = {2022}}
"""


def _run(args):
    r = subprocess.run([sys.executable, SCRIPT] + args, capture_output=True, text=True)
    return r.returncode, r.stdout, r.stderr


def _labs(tmp_path):
    labs = tmp_path / "labs"
    labs.mkdir()
    (labs / "a-gates.md").write_text(PACKET_A, encoding="utf-8")
    (labs / "b-tiers.md").write_text(PACKET_B, encoding="utf-8")
    return labs


def test_help_exits_zero():
    rc, out, _ = _run(["--help"])
    assert rc == 0
    assert "--weeks" in out


def test_basic_pack(tmp_path):
    labs = _labs(tmp_path)
    rc, out, _ = _run(["--title", "Course X", "--weeks", "3", "--labs", str(labs)])
    assert rc == 0
    assert out.startswith("# Course X")
    for w in (1, 2, 3):
        assert "## Week %d:" % w in out
    assert "Instructor note" in out
    assert "auto-extracted, review before teaching" in out
    # objectives come from packet headings, boilerplate headings excluded
    assert "- What a gate is" in out
    assert "Flashcards" not in out.split("## Week 1")[1].split("## Week 2")[0]


def test_refs_round_robin(tmp_path):
    labs = _labs(tmp_path)
    refs = tmp_path / "refs.bib"
    refs.write_text(REFS_BIB, encoding="utf-8")
    rc, out, _ = _run(["--title", "C", "--weeks", "2", "--labs", str(labs),
                       "--refs", str(refs)])
    assert rc == 0
    week1 = out.split("## Week 1")[1].split("## Week 2")[0]
    week2 = out.split("## Week 2")[1]
    # file order, cyclic: ref1+ref3 -> week1, ref2 -> week2
    assert "Honest Reporting in Research" in week1
    assert "Verification Basics" in week1
    assert "Gatekeeping for Good" in week2
    assert "(2020)" in week1 and "Smith, A. and Jones, B." in week1


def test_outline_topics(tmp_path):
    labs = _labs(tmp_path)
    outline = tmp_path / "outline.yml"
    outline.write_text("1: Foundations\n2: Verification\n", encoding="utf-8")
    rc, out, _ = _run(["--title", "C", "--weeks", "2", "--labs", str(labs),
                       "--outline", str(outline)])
    assert rc == 0
    assert "## Week 1: Foundations" in out
    assert "## Week 2: Verification" in out


def test_deterministic(tmp_path):
    labs = _labs(tmp_path)
    args = ["--title", "C", "--weeks", "4", "--labs", str(labs)]
    rc1, out1, _ = _run(args)
    rc2, out2, _ = _run(args)
    assert rc1 == rc2 == 0
    assert out1 == out2


def test_invalid_inputs(tmp_path):
    rc, _, err = _run(["--title", "C", "--labs", str(tmp_path / "nope")])
    assert rc == 1
    assert "not found" in err
    rc, _, err = _run(["--title", "C"])  # nothing to build from
    assert rc == 1
    labs = _labs(tmp_path)
    rc, _, err = _run(["--title", "C", "--weeks", "0", "--labs", str(labs)])
    assert rc == 1
