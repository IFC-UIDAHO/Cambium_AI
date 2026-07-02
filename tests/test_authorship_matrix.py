"""Tests for tools/authorship_matrix.py.

Stdlib + tmp_path only. Validates the 14 CRediT roles, checks matrix and
statement content, and confirms CSV/JSON input parity.
"""
import json
import os
import sys

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_REPO, "tools"))

import authorship_matrix as A


def _write_json_authors(path, authors):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(authors, fh)


def _write_csv_authors(path, rows):
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write("name,roles\n")
        for name, roles in rows:
            fh.write(f'{name},"{";".join(roles)}"\n')


def test_valid_input_produces_matrix_and_statement(tmp_path):
    authors_path = tmp_path / "authors.json"
    _write_json_authors(str(authors_path), [
        {"name": "Ada Lovelace", "roles": ["Conceptualization", "Methodology"]},
        {"name": "Grace Hopper", "roles": ["Software", "writing - original draft"]},
    ])
    out = tmp_path / "matrix.md"

    rc = A.main(["--authors", str(authors_path), "--out", str(out)])
    assert rc == 0

    text = out.read_text(encoding="utf-8")
    assert "Ada Lovelace" in text
    assert "Grace Hopper" in text
    assert "Conceptualization" in text
    assert "Contribution statement" in text
    assert "AL: Conceptualization, Methodology." in text
    assert "GH: Software, Writing - original draft." in text


def test_unknown_role_exits_1(tmp_path, capsys):
    authors_path = tmp_path / "authors.json"
    _write_json_authors(str(authors_path), [
        {"name": "Bad Role Author", "roles": ["Not A Real Role"]},
    ])
    rc = A.main(["--authors", str(authors_path)])
    assert rc == 1
    captured = capsys.readouterr()
    assert "unknown" in captured.err.lower()
    assert "Conceptualization" in captured.err  # lists valid roles


def test_zero_role_author_exits_1(tmp_path, capsys):
    authors_path = tmp_path / "authors.json"
    _write_json_authors(str(authors_path), [
        {"name": "No Roles Author", "roles": []},
    ])
    rc = A.main(["--authors", str(authors_path)])
    assert rc == 1
    captured = capsys.readouterr()
    assert "zero roles" in captured.err.lower()


def test_over_concentration_warning(tmp_path, capsys):
    authors_path = tmp_path / "authors.json"
    _write_json_authors(str(authors_path), [
        {"name": "Does Everything", "roles": A.CREDIT_ROLES[:9]},  # 9 roles > 8
    ])
    out = tmp_path / "matrix.md"
    rc = A.main(["--authors", str(authors_path), "--out", str(out)])
    assert rc == 0
    captured = capsys.readouterr()
    assert "holds 9 roles" in captured.err


def test_role_with_nobody_warns(tmp_path, capsys):
    authors_path = tmp_path / "authors.json"
    _write_json_authors(str(authors_path), [
        {"name": "Sole Author", "roles": ["Conceptualization"]},
    ])
    out = tmp_path / "matrix.md"
    rc = A.main(["--authors", str(authors_path), "--out", str(out)])
    assert rc == 0
    captured = capsys.readouterr()
    assert "no author holds the role 'Data curation'" in captured.err


def test_json_and_csv_parity(tmp_path):
    json_path = tmp_path / "authors.json"
    csv_path = tmp_path / "authors.csv"
    _write_json_authors(str(json_path), [
        {"name": "Parity Author", "roles": ["Methodology", "Validation"]},
    ])
    _write_csv_authors(str(csv_path), [("Parity Author", ["Methodology", "Validation"])])

    out_json = tmp_path / "from_json.md"
    out_csv = tmp_path / "from_csv.md"
    rc1 = A.main(["--authors", str(json_path), "--out", str(out_json)])
    rc2 = A.main(["--authors", str(csv_path), "--out", str(out_csv)])
    assert rc1 == 0 and rc2 == 0
    assert out_json.read_text(encoding="utf-8") == out_csv.read_text(encoding="utf-8")


def test_credit_roles_list_has_14_entries():
    assert len(A.CREDIT_ROLES) == 14


def test_missing_authors_file_exits_2(tmp_path):
    rc = A.main(["--authors", str(tmp_path / "nope.json")])
    assert rc == 2


def test_no_em_dash_in_source():
    with open(os.path.join(_REPO, "tools", "authorship_matrix.py"), encoding="utf-8") as fh:
        source = fh.read()
    assert chr(0x2014) not in source
