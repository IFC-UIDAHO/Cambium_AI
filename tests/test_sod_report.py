"""Tests for tools/sod_report.py: separation-of-duties attestation over GATES.md."""
import os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import sod_report as SR

HEADER = ("# Ledger\n\n## Approvals log\n"
          "| Gate | Date | Approver | Decision | Notes |\n"
          "|---|---|---|---|---|\n")


def run(*args):
    return subprocess.run([sys.executable, os.path.join(ROOT, "tools", "sod_report.py"), *args],
                          capture_output=True, text=True)


def _gates(tmp_path, body):
    p = tmp_path / "GATES.md"
    p.write_text(HEADER + body, encoding="utf-8")
    return str(p)


def test_help_exits_0():
    r = run("--help")
    assert r.returncode == 0


def test_clean_ledger_no_flags_strict_ok(tmp_path):
    p = _gates(tmp_path,
               "| G1 | 2026-01-01 | Alice | APPROVE | fine |\n"
               "| G2 | 2026-01-02 | Bob | APPROVE | fine |\n")
    r = run("--gates", p, "--strict")
    assert r.returncode == 0, r.stdout
    assert "No flags" in r.stdout
    assert "| Alice | 1 |" in r.stdout and "| Bob | 1 |" in r.stdout


def test_single_person_concentration_reported_not_flagged(tmp_path):
    p = _gates(tmp_path,
               "| G1 | 2026-01-01 | Alice | APPROVE | a |\n"
               "| G2 | 2026-01-02 | Alice | APPROVE | b |\n")
    r = run("--gates", p, "--strict")
    assert r.returncode == 0  # observation, not a strict flag
    assert "single" in r.stdout and "Alice" in r.stdout


def test_empty_approver_flagged_strict_fails(tmp_path):
    p = _gates(tmp_path, "| G1 | 2026-01-01 |  | APPROVE | who? |\n")
    r = run("--gates", p)
    assert r.returncode == 0 and "EMPTY approver" in r.stdout
    r2 = run("--gates", p, "--strict")
    assert r2.returncode == 1


def test_malformed_row_flagged(tmp_path):
    p = _gates(tmp_path, "| G1 | 2026-01-01 | Alice | APPROVE |\n")  # 4 cells
    r = run("--gates", p, "--strict")
    assert r.returncode == 1 and "malformed" in r.stdout


def test_g3_without_second_party_advisory(tmp_path):
    p = _gates(tmp_path, "| G3 | 2026-01-01 | Director (Jaslam) | APPROVE | submitted solo |\n")
    r = run("--gates", p)
    assert r.returncode == 0 and "ADVISORY" in r.stdout and "second" in r.stdout
    assert run("--gates", p, "--strict").returncode == 1


def test_g6_with_second_party_passes(tmp_path):
    p = _gates(tmp_path,
               "| G6 | 2026-01-01 | Director (Jaslam) + Co-PI (Kim) | APPROVE | co-signed release |\n")
    r = run("--gates", p, "--strict")
    assert r.returncode == 0, r.stdout


def test_missing_file_and_missing_section_exit_1(tmp_path):
    assert run("--gates", str(tmp_path / "nope.md")).returncode == 1
    p = tmp_path / "empty.md"
    p.write_text("# nothing here\n", encoding="utf-8")
    r = run("--gates", str(p))
    assert r.returncode == 1 and "Approvals log" in r.stdout


def test_parser_skips_blockquotes_and_blank_lines():
    text = HEADER + "\n> provenance note\n\n| G1 | d | A | APPROVE | n |\n\n| G2 | d | B | APPROVE | n |\n"
    rows, malformed = SR.parse_approvals(text)
    assert len(rows) == 2 and not malformed
