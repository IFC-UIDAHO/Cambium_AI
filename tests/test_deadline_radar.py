#!/usr/bin/env python3
"""Tests for tools/deadline_radar.py.

Stdlib only. Uses tmp_path for input files; never touches the live repo data.
Covers sorting/bucket edges with frozen --today, ICS content, mixed-source
merge and dedupe, and bad date exits 2.
"""
from __future__ import annotations
import json
import os
import sys
from datetime import datetime

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_REPO, "tools"))

import pytest
import deadline_radar as D


# ---------------------------------------------------------------------------
# Bucket edges
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "days_left,expected_bucket",
    [
        (-1, "OVERDUE"),
        (0, "<14d"),
        (13, "<14d"),
        (14, "<30d"),
        (29, "<30d"),
        (30, "<90d"),
        (89, "<90d"),
        (90, "later"),
        (365, "later"),
    ],
)
def test_bucket_edges(days_left, expected_bucket):
    assert D.bucket_for(days_left) == expected_bucket


def test_sorting_by_days_left():
    items = [
        {"name": "C", "funder": "F", "deadline": "2026-09-01"},
        {"name": "A", "funder": "F", "deadline": "2026-07-05"},
        {"name": "B", "funder": "F", "deadline": "2026-08-01"},
    ]
    today = datetime(2026, 7, 1)
    rows = D.compute_rows(items, today)
    assert [r["name"] for r in rows] == ["A", "B", "C"]
    assert rows[0]["days_left"] < rows[1]["days_left"] < rows[2]["days_left"]


def test_overdue_sorts_first():
    items = [
        {"name": "Future", "funder": "F", "deadline": "2026-12-01"},
        {"name": "Past", "funder": "F", "deadline": "2026-01-01"},
    ]
    today = datetime(2026, 7, 1)
    rows = D.compute_rows(items, today)
    assert rows[0]["name"] == "Past"
    assert rows[0]["bucket"] == "OVERDUE"


# ---------------------------------------------------------------------------
# ICS export
# ---------------------------------------------------------------------------

def test_ics_contains_vevent_and_dtstart():
    items = [{"name": "NSF CAREER", "funder": "NSF", "deadline": "2026-07-20"}]
    rows = D.compute_rows(items, datetime(2026, 7, 1))
    ics = D.build_ics(rows)
    assert "BEGIN:VCALENDAR" in ics
    assert "BEGIN:VEVENT" in ics
    assert "DTSTART;VALUE=DATE:20260720" in ics
    assert "END:VEVENT" in ics
    assert "END:VCALENDAR" in ics


def test_ics_one_vevent_per_item():
    items = [
        {"name": "A", "funder": "F", "deadline": "2026-07-20"},
        {"name": "B", "funder": "F", "deadline": "2026-08-20"},
    ]
    rows = D.compute_rows(items, datetime(2026, 7, 1))
    ics = D.build_ics(rows)
    assert ics.count("BEGIN:VEVENT") == 2


def test_ics_contains_valarm():
    items = [{"name": "A", "funder": "F", "deadline": "2026-07-20"}]
    rows = D.compute_rows(items, datetime(2026, 7, 1))
    ics = D.build_ics(rows)
    assert "BEGIN:VALARM" in ics
    assert "TRIGGER:-P14D" in ics


# ---------------------------------------------------------------------------
# Mixed input sources merge and dedupe
# ---------------------------------------------------------------------------

def test_mixed_sources_merge(tmp_path):
    rules_obj = {"name": "NSF CAREER", "funder": "NSF", "deadline": "2026-07-20"}
    rules_list = [
        {"name": "DOE EFRC", "funder": "DOE", "deadline": "2026-08-01"},
        {"name": "NIH R01", "funder": "NIH", "deadline": "2026-09-15"},
    ]
    obj_path = tmp_path / "rules_obj.json"
    list_path = tmp_path / "rules_list.json"
    obj_path.write_text(json.dumps(rules_obj), encoding="utf-8")
    list_path.write_text(json.dumps(rules_list), encoding="utf-8")

    items = D.items_from_rules_file(str(obj_path)) + D.items_from_rules_file(str(list_path))
    items.append(D.item_from_add_string("name=USDA NIFA,funder=USDA,deadline=2026-10-01"))
    merged = D.merge_and_dedupe(items)
    assert len(merged) == 4
    names = {i["name"] for i in merged}
    assert names == {"NSF CAREER", "DOE EFRC", "NIH R01", "USDA NIFA"}


def test_dedupe_same_name_and_date():
    items = [
        {"name": "NSF CAREER", "funder": "NSF", "deadline": "2026-07-20"},
        {"name": "NSF CAREER", "funder": "NSF (dup)", "deadline": "2026-07-20"},
        {"name": "NSF CAREER", "funder": "NSF", "deadline": "2026-08-20"},  # different date, kept
    ]
    merged = D.merge_and_dedupe(items)
    assert len(merged) == 2


def test_cli_mixed_sources_full_run(tmp_path):
    rules_obj = {"name": "NSF CAREER", "funder": "NSF", "deadline": "2026-07-20"}
    rules_path = tmp_path / "rules.json"
    rules_path.write_text(json.dumps(rules_obj), encoding="utf-8")
    out_path = tmp_path / "radar.md"
    ics_path = tmp_path / "radar.ics"

    rc = D.main([
        "--rules", str(rules_path),
        "--add", "name=USDA NIFA,funder=USDA,deadline=2026-10-01",
        "--today", "2026-07-01",
        "--out", str(out_path),
        "--ics", str(ics_path),
    ])
    assert rc == 0
    content = out_path.read_text(encoding="utf-8")
    assert "NSF CAREER" in content
    assert "USDA NIFA" in content
    assert "—" not in content  # no em dashes
    ics_content = ics_path.read_text(encoding="utf-8")
    assert ics_content.count("BEGIN:VEVENT") == 2


# ---------------------------------------------------------------------------
# Bad date exits 2
# ---------------------------------------------------------------------------

def test_bad_date_in_rules_file_exits_2(tmp_path):
    bad = {"name": "Bad", "funder": "F", "deadline": "not-a-date"}
    path = tmp_path / "bad_rules.json"
    path.write_text(json.dumps(bad), encoding="utf-8")
    with pytest.raises(SystemExit) as exc:
        D.main(["--rules", str(path)])
    assert exc.value.code == 2


def test_bad_date_in_add_flag_exits_2():
    with pytest.raises(SystemExit) as exc:
        D.main(["--add", "name=X,funder=Y,deadline=2026-13-40"])
    assert exc.value.code == 2


def test_missing_rules_file_exits_2(tmp_path):
    missing = tmp_path / "nope.json"
    with pytest.raises(SystemExit) as exc:
        D.main(["--rules", str(missing)])
    assert exc.value.code == 2


def test_add_missing_deadline_key_exits_2():
    with pytest.raises(SystemExit) as exc:
        D.main(["--add", "name=X,funder=Y"])
    assert exc.value.code == 2
