"""The research-led Academy build: pillars/tiers/resources present, links external, honesty fix held."""
import os, re, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def _courses():
    return json.load(open(os.path.join(ROOT, "academy", "courses.json"), encoding="utf-8"))

def test_every_module_has_pillars_tier_badge_and_resources():
    valid = {"Research integrity", "Open science", "Responsible-AI reasoning"}
    for m in _courses()["modules"]:
        assert m.get("pillars") and set(m["pillars"]) <= valid, m.get("title")
        assert m.get("tier") == "Foundation"
        assert m.get("badge", {}).get("foundation") and m["badge"].get("practitioner")
        assert 2 <= len(m.get("resources", [])) <= 3, m.get("title")

def test_go_deeper_resources_are_external_links():
    for m in _courses()["modules"]:
        for r in m["resources"]:
            assert r["url"].startswith("http") and r.get("title") and r.get("org")

def test_no_spaced_repetition_overclaim_anywhere():
    # the phrase Faculty flagged must not survive in the data or the rendered hub
    cj = open(os.path.join(ROOT, "academy", "courses.json"), encoding="utf-8").read().lower()
    hub = open(os.path.join(ROOT, "academy", "index.html"), encoding="utf-8").read().lower()
    assert "spaced repetition" not in cj
    assert "spaced repetition" not in hub

def test_engine_has_cross_session_spacing_and_cumulative_check():
    eng = open(os.path.join(ROOT, "templates", "learning_lab_template.html"), encoding="utf-8").read()
    for needle in ("FC_BOX_DELAYS", "buildCumulativeQuiz", "renderGoDeeper"):
        assert needle in eng, needle
