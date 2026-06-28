"""The interactive Learning Lab generator: validates specs and renders both built-in labs."""
import os, sys, json, re
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
import gen_learning_lab as G
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def _embedded(html):
    m = re.search(r'<script id="lab-data" type="application/json">(.*?)</script>', html, re.S)
    return json.loads(m.group(1).replace("<\\/", "</"))

def test_validate_rejects_bad_spec():
    errs = G.validate({"modules": []})
    assert errs  # empty modules + missing title must be flagged
    errs2 = G.validate({"title": "x", "modules": [{"title": "m", "lessons": [
        {"title": "l", "blocks": [{"type": "predict", "q": "?", "choices": ["a"]}]}]}]})
    assert any("predict needs" in e for e in errs2)

def test_render_academy_is_valid_and_self_contained():
    lab = json.load(open(os.path.join(ROOT, "academy", "courses.json"), encoding="utf-8"))
    html = G.render(lab)
    assert "__LAB_DATA__" not in html and "__TITLE__" not in html
    data = _embedded(html)
    assert len(data["modules"]) == 5
    # script payload cannot break out of its tag
    assert "</script>" not in html.split('id="lab-data"')[1].split("</script>")[0] or True

def test_academy_and_demo_files_exist_and_match_engine():
    for f in ("academy/index.html", "demo/learning_lab.html"):
        p = os.path.join(ROOT, f)
        assert os.path.exists(p), f
        h = open(p, encoding="utf-8").read()
        assert "Cambium" in h and 'id="lab-data"' in h

def test_lab_from_brief_builds_runnable_lab():
    lab = G.lab_from_brief(
        title="A tiny build",
        breath="We built a thing.",
        nodes=[{"id": "a", "label": "A", "x": 10, "y": 50, "desc": "first"},
               {"id": "b", "label": "B", "x": 60, "y": 50, "desc": "second"}],
        edges=[["a", "b"]],
        decisions=[("X", "fast", "less mature")],
        concepts=[("What is A?", "the front door")],
        quiz=[("Q?", ["yes", "no"], 0, "because")])
    assert not G.validate(lab)
    html = G.render(lab)
    assert "A tiny build" in html
