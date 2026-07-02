"""Tests for tools/syllabus_builder.py -- dated syllabus from Academy modules."""
import json
import os
import re
import shutil
import sys
import tempfile
from datetime import datetime, timedelta

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
import syllabus_builder as SB

FIXTURE_COURSES = {
    "id": "academy",
    "modules": [
        {"id": "way", "title": "The Cambium way", "summary": "How a goal becomes verified results."},
        {"id": "evidence", "title": "Evidence tiers", "summary": "Say only what evidence supports."},
        {"id": "gates", "title": "Human gates", "summary": "The case for stopping to ask a person."},
        {"id": "verify", "title": "Verification", "summary": "How to check a result so it holds."},
    ],
}


def _tmp_academy():
    """Return (tmpdir, courses_json_path) with a fixture academy/courses.json."""
    d = tempfile.mkdtemp()
    academy_dir = os.path.join(d, "academy")
    os.makedirs(academy_dir, exist_ok=True)
    courses_path = os.path.join(academy_dir, "courses.json")
    with open(courses_path, "w", encoding="utf-8") as fh:
        json.dump(FIXTURE_COURSES, fh)
    return d, courses_path


def test_module_discovery_from_tmp_fixture():
    d, courses_path = _tmp_academy()
    try:
        courses = SB._load_courses(courses_path)
        modules = SB.discover_modules(courses)
        assert [m["id"] for m in modules] == ["way", "evidence", "gates", "verify"]
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_weekly_date_math_per_week_1_lands_7_days_apart():
    d, courses_path = _tmp_academy()
    try:
        courses = SB._load_courses(courses_path)
        modules = SB.select_modules(courses, "all")
        start = datetime(2026, 9, 1)
        sessions = SB.schedule_sessions(modules, start, per_week=1)
        dates = [s["date"] for s in sessions]
        assert dates[0] == start
        for i in range(1, len(dates)):
            assert (dates[i] - dates[i - 1]).days == 7
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_per_week_2_splits_two_sessions_into_same_week():
    d, courses_path = _tmp_academy()
    try:
        courses = SB._load_courses(courses_path)
        modules = SB.select_modules(courses, "all")
        start = datetime(2026, 9, 1)
        sessions = SB.schedule_sessions(modules, start, per_week=2)
        # sessions 0 and 1 (0-indexed) both belong to week 1
        assert sessions[0]["week"] == 1
        assert sessions[1]["week"] == 1
        # sessions 2 and 3 both belong to week 2
        assert sessions[2]["week"] == 2
        assert sessions[3]["week"] == 2
        # week 2's first session starts 7 days after week 1's first session
        assert (sessions[2]["date"] - sessions[0]["date"]).days == 7
        # within a week, the two sessions do not land on the same day
        assert sessions[1]["date"] != sessions[0]["date"]
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_unknown_module_exits_1_listing_valid():
    d, courses_path = _tmp_academy()
    try:
        with pytest.raises(SystemExit) as excinfo:
            SB.main(["--modules", "nonexistent_module", "--start", "2026-09-01",
                     "--courses", courses_path, "--out", os.path.join(d, "syl.md")])
        assert excinfo.value.code == 1
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_ics_vevent_count_equals_sessions():
    d, courses_path = _tmp_academy()
    try:
        out_md = os.path.join(d, "syllabus.md")
        out_ics = os.path.join(d, "syllabus.ics")
        rc = SB.main([
            "--modules", "all", "--start", "2026-09-01",
            "--courses", courses_path, "--out", out_md, "--ics", out_ics,
        ])
        assert rc == 0
        ics_text = open(out_ics, encoding="utf-8").read()
        vevent_count = len(re.findall(r"BEGIN:VEVENT", ics_text))
        assert vevent_count == 4
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_markdown_contains_objectives():
    d, courses_path = _tmp_academy()
    try:
        out_md = os.path.join(d, "syllabus.md")
        rc = SB.main([
            "--modules", "way,evidence", "--start", "2026-09-01",
            "--courses", courses_path, "--out", out_md,
        ])
        assert rc == 0
        md_text = open(out_md, encoding="utf-8").read()
        assert "How a goal becomes verified results." in md_text
        assert "Say only what evidence supports." in md_text
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_specific_module_order_overrides_academy_order():
    d, courses_path = _tmp_academy()
    try:
        courses = SB._load_courses(courses_path)
        modules = SB.select_modules(courses, "verify,way")
        assert [m["id"] for m in modules] == ["verify", "way"]
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_missing_courses_file_exits_2():
    d = tempfile.mkdtemp()
    try:
        with pytest.raises(SystemExit) as excinfo:
            SB.main(["--modules", "all", "--start", "2026-09-01",
                     "--courses", os.path.join(d, "nope.json"), "--out", os.path.join(d, "syl.md")])
        assert excinfo.value.code == 2
    finally:
        shutil.rmtree(d, ignore_errors=True)
