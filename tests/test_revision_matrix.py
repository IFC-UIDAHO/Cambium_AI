"""Tests for tools/revision_matrix.py.

Stdlib + tmp_path only. Traces the documented parsing heuristics by hand
against small fixtures: "Reviewer N" / "Referee N" headers begin a section,
numbered lines split comments within a section, blank-paragraph fallback when
no numbers are present, and single-block fallback when no reviewer header
exists at all.
"""
import os
import sys

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_REPO, "tools"))

import revision_matrix as V

TWO_REVIEWER_FIXTURE = """Reviewer 1
1. The methodology section needs more detail on the sampling procedure.
2. Figure 3 axis labels are too small to read.

Reviewer 2
1. Please clarify the statistical test used in Table 2.
"""

SINGLE_BLOCK_FIXTURE = """Thanks for the submission. A few notes below.

The introduction could use one more citation for the background claim.

The discussion section is a bit long and could be trimmed.
"""


def test_two_reviewer_fixture_parses_to_expected_row_count(tmp_path):
    comments = tmp_path / "reviews.txt"
    comments.write_text(TWO_REVIEWER_FIXTURE, encoding="utf-8")
    out = tmp_path / "matrix.md"

    rc = V.main(["--comments", str(comments), "--out", str(out)])
    assert rc == 0

    text = out.read_text(encoding="utf-8")
    assert text.count("| TODO | TODO | TODO |") == 3
    assert "Reviewer 1" in text
    assert "Reviewer 2" in text
    assert "sampling procedure" in text
    assert "Table 2" in text


def test_single_block_fallback_works(tmp_path):
    comments = tmp_path / "reviews.txt"
    comments.write_text(SINGLE_BLOCK_FIXTURE, encoding="utf-8")
    out = tmp_path / "matrix.md"

    rc = V.main(["--comments", str(comments), "--out", str(out)])
    assert rc == 0

    text = out.read_text(encoding="utf-8")
    # No numbered items and no "Reviewer N" header -> blank-paragraph fallback
    # under a single "Reviewer 1" section; 3 paragraphs in the fixture.
    assert text.count("| TODO | TODO | TODO |") == 3
    assert "Reviewer 1" in text


def test_empty_file_exits_2(tmp_path, capsys):
    comments = tmp_path / "empty.txt"
    comments.write_text("   \n\n", encoding="utf-8")
    rc = V.main(["--comments", str(comments)])
    assert rc == 2
    assert "empty" in capsys.readouterr().err.lower()


def test_missing_comments_file_exits_2(tmp_path):
    rc = V.main(["--comments", str(tmp_path / "nope.txt")])
    assert rc == 2


def test_stats_counts_todos(tmp_path, capsys):
    matrix = tmp_path / "matrix.md"
    matrix.write_text(
        "| # | Reviewer | Comment (first 140 chars) | Response | Change made | Location |\n"
        "|---|---|---|---|---|---|\n"
        "| 1 | Reviewer 1 | comment one | TODO | TODO | TODO |\n"
        "| 2 | Reviewer 1 | comment two | Done, see reply. | Added a paragraph. | TODO |\n",
        encoding="utf-8",
    )
    rc = V.main(["--stats", "--matrix", str(matrix)])
    assert rc == 0
    out = capsys.readouterr().out
    assert "4 TODO" in out  # row 1 has 3, row 2 has 1


def test_stats_strict_exits_1_when_todos_remain(tmp_path):
    matrix = tmp_path / "matrix.md"
    matrix.write_text(
        "| # | Reviewer | Comment (first 140 chars) | Response | Change made | Location |\n"
        "|---|---|---|---|---|---|\n"
        "| 1 | Reviewer 1 | comment one | TODO | TODO | TODO |\n",
        encoding="utf-8",
    )
    rc = V.main(["--stats", "--matrix", str(matrix), "--strict"])
    assert rc == 1


def test_stats_strict_exits_0_when_all_filled(tmp_path):
    matrix = tmp_path / "matrix.md"
    matrix.write_text(
        "| # | Reviewer | Comment (first 140 chars) | Response | Change made | Location |\n"
        "|---|---|---|---|---|---|\n"
        "| 1 | Reviewer 1 | comment one | Done. | Fixed. | Section 2. |\n",
        encoding="utf-8",
    )
    rc = V.main(["--stats", "--matrix", str(matrix), "--strict"])
    assert rc == 0


def test_stats_requires_matrix_arg(tmp_path):
    rc = V.main(["--stats"])
    assert rc == 2


def test_comment_truncated_to_140_chars(tmp_path):
    long_comment = "1. " + ("x" * 200)
    comments = tmp_path / "reviews.txt"
    comments.write_text(long_comment + "\n", encoding="utf-8")
    out = tmp_path / "matrix.md"
    rc = V.main(["--comments", str(comments), "--out", str(out)])
    assert rc == 0
    text = out.read_text(encoding="utf-8")
    assert "x" * 200 not in text
    assert "..." in text


def test_no_em_dash_in_source():
    with open(os.path.join(_REPO, "tools", "revision_matrix.py"), encoding="utf-8") as fh:
        source = fh.read()
    assert chr(0x2014) not in source
