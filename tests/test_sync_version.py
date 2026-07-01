"""Tests for tools/sync_version.py. Stdlib only; exercises the pure substitution logic."""
import os
import sys

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_REPO, "tools"))

import sync_version as S


def test_json_sub_replaces_version():
    text = '{\n  "name": "x",\n  "version": "1.18.0",\n  "y": 1\n}'
    new, old = S._json_version_sub(text, "1.30.0")
    assert old == "1.18.0"
    assert '"version": "1.30.0"' in new
    assert "1.18.0" not in new


def test_json_sub_idempotent():
    text = '{"version": "1.30.0"}'
    new, old = S._json_version_sub(text, "1.30.0")
    assert old == "1.30.0"
    assert new == text  # unchanged


def test_json_sub_no_field():
    text = '{"name": "x"}'
    new, old = S._json_version_sub(text, "1.30.0")
    assert old is None
    assert new == text


def test_toml_sub_replaces_version():
    text = '[project]\nname = "x"\nversion = "1.18.0"\n'
    new, old = S._toml_version_sub(text, "1.30.0")
    assert old == "1.18.0"
    assert 'version = "1.30.0"' in new


def test_toml_sub_idempotent():
    text = 'version = "2.0.0"\n'
    new, old = S._toml_version_sub(text, "2.0.0")
    assert old == "2.0.0"
    assert new == text


def test_toml_sub_only_matches_line_start():
    # a dependency like requests = "1.18.0" must not be mistaken for the project version
    text = 'version = "1.5.0"\nrequests_version = "9.9.9"\n'
    new, old = S._toml_version_sub(text, "1.6.0")
    assert old == "1.5.0"
    assert 'version = "1.6.0"' in new
    assert '9.9.9' in new  # untouched


def test_readme_badge_sub_replaces_version():
    text = '<img src="https://img.shields.io/badge/version-1.18.0-16C079?style=flat-square">'
    new, old = S._readme_badge_sub(text, "1.33.0")
    assert old == "1.18.0"
    assert "badge/version-1.33.0" in new
    assert "1.18.0" not in new


def test_readme_badge_sub_idempotent():
    text = "badge/version-2.0.0-16C079"
    new, old = S._readme_badge_sub(text, "2.0.0")
    assert old == "2.0.0"
    assert new == text


def test_real_changelog_version_is_semver():
    v = S.changelog_version()
    parts = v.split(".")
    assert len(parts) == 3 and all(p.isdigit() for p in parts)
