"""Tests for tools/policy_coverage.py.

Verifies against the REAL repo policy: >=8 enforced points, zero flags. Also verifies:
a doctored policy fixture citing a missing tools/nope.py flags it, partial points are
never flagged, --json is valid JSON, and --strict exits 1 on a flag.
"""
import json
import os
import sys
import tempfile
import textwrap

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_REPO, "tools"))

import policy_coverage as PC

REAL_POLICY = os.path.join(_REPO, "docs", "governance", "AI_POLICY.md")


def test_real_repo_yields_at_least_8_enforced_points_zero_flags():
    text = open(REAL_POLICY, encoding="utf-8").read()
    points = PC.parse_policy(text)
    rows = PC.check_coverage(points, _REPO)
    n_enforced = sum(1 for r in rows if r["status"] == "enforced")
    n_flagged = sum(1 for r in rows if r["flagged"])
    assert n_enforced >= 8, "expected >=8 enforced points, got %d" % n_enforced
    assert n_flagged == 0, "expected zero flags on the real repo, got: %s" % [r for r in rows if r["flagged"]]


def test_real_repo_has_ten_points_parsed():
    text = open(REAL_POLICY, encoding="utf-8").read()
    points = PC.parse_policy(text)
    assert len(points) == 10


def _doctored_policy(tmp):
    path = os.path.join(tmp, "AI_POLICY.md")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(textwrap.dedent("""\
            # Cambium AI Policy

            ## 1. Fake enforced point -- **enforced**
            *Mechanism: `tools/nope.py` is the enforcement mechanism.*

            ## 2. Fake partial point -- **partial**
            *Mechanism: `tools/nope.py` would be nice but this is only partial.*

            ## 3. Real enforced point -- **enforced**
            *Mechanism: `tools/gate.py` blocks a bare APPROVE.*
        """))
    return path


def test_doctored_fixture_flags_missing_file():
    tmp = tempfile.mkdtemp()
    policy = _doctored_policy(tmp)
    text = open(policy, encoding="utf-8").read()
    points = PC.parse_policy(text)
    rows = PC.check_coverage(points, _REPO)
    flagged_nums = {r["number"] for r in rows if r["flagged"]}
    assert 1 in flagged_nums, "point 1 cites a missing file and claims enforced -- must be flagged"


def test_partial_points_never_flagged_even_with_missing_mechanism():
    tmp = tempfile.mkdtemp()
    policy = _doctored_policy(tmp)
    text = open(policy, encoding="utf-8").read()
    points = PC.parse_policy(text)
    rows = PC.check_coverage(points, _REPO)
    point2 = next(r for r in rows if r["number"] == 2)
    assert point2["status"] == "partial"
    assert point2["flagged"] is False


def test_real_mechanism_file_not_flagged():
    tmp = tempfile.mkdtemp()
    policy = _doctored_policy(tmp)
    text = open(policy, encoding="utf-8").read()
    points = PC.parse_policy(text)
    rows = PC.check_coverage(points, _REPO)
    point3 = next(r for r in rows if r["number"] == 3)
    assert point3["flagged"] is False
    assert point3["file_exists"]["tools/gate.py"] is True


def test_json_output_is_valid():
    tmp = tempfile.mkdtemp()
    policy = _doctored_policy(tmp)
    out_json = os.path.join(tmp, "out.json")
    out_md = os.path.join(tmp, "out.md")
    PC.main(["--policy", policy, "--root", _REPO, "--out", out_md, "--json", out_json])
    data = json.loads(open(out_json, encoding="utf-8").read())
    assert isinstance(data, list)
    assert len(data) == 3


def test_strict_exit_1_on_flag():
    tmp = tempfile.mkdtemp()
    policy = _doctored_policy(tmp)
    out_md = os.path.join(tmp, "out.md")
    rc = PC.main(["--policy", policy, "--root", _REPO, "--out", out_md, "--strict"])
    assert rc == 1


def test_non_strict_exits_0_even_with_flag():
    tmp = tempfile.mkdtemp()
    policy = _doctored_policy(tmp)
    out_md = os.path.join(tmp, "out.md")
    rc = PC.main(["--policy", policy, "--root", _REPO, "--out", out_md])
    assert rc == 0


def test_missing_policy_file_exits_1():
    tmp = tempfile.mkdtemp()
    rc = PC.main(["--policy", os.path.join(tmp, "nope.md"), "--root", _REPO])
    assert rc == 1


def test_bare_filename_citation_resolves_to_tools_dir():
    resolved = PC._resolve_mechanism("gate.py", _REPO)
    assert resolved == "tools/gate.py"


def test_prefixed_citation_kept_as_is():
    resolved = PC._resolve_mechanism("governance/validate.py", _REPO)
    assert resolved == "governance/validate.py"


def test_markdown_report_lists_flag_marker():
    tmp = tempfile.mkdtemp()
    policy = _doctored_policy(tmp)
    out_md = os.path.join(tmp, "out.md")
    PC.main(["--policy", policy, "--root", _REPO, "--out", out_md])
    report = open(out_md, encoding="utf-8").read()
    assert "FLAGGED" in report
    assert "nope.py" in report
