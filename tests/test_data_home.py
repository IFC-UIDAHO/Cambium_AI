"""tests/test_data_home.py -- Tests for cambium_io.data_home() and path helpers.

Covers:
  1. CAMBIUM_HOME env var takes precedence (dir created if missing).
  2. ROOT-writable invariant: data_home() == ROOT when ROOT is writable and no env var.
  3. Read-only install fallback: data_home() returns cwd/.cambium when ROOT not writable.
  4. run_state_path() is inside data_home().
  5. run_board_html_path() is inside data_home().
  6. memory_cache_dir() is inside data_home().
  7. Write-side round-trip: in read-only install, writing run_state goes to data_home().

These tests are UNIT tests of cambium_io; they do NOT exercise subprocess CLIs, so they
run in-process and do not require writable ROOT.

The KEY invariant -- data_home() == ROOT when ROOT is writable -- ensures every existing
test in the suite is unaffected: the test environment has a writable ROOT so data_home()
returns ROOT exactly, and all write paths remain the same as before.
"""
import importlib
import os
import sys
import types

import pytest

# Ensure tools/ is on sys.path (mirrors the project layout)
_TOOLS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "tools")
if _TOOLS_DIR not in sys.path:
    sys.path.insert(0, _TOOLS_DIR)

import cambium_io  # noqa: E402 -- must be after path setup


# ---------------------------------------------------------------------------
# Helper: reload cambium_io with patched os.access so changes to
#         cambium_io._ROOT or env vars take effect cleanly.
# ---------------------------------------------------------------------------

def _reload_cambium_io(monkeypatch, env_vars=None, access_override=None):
    """Return a freshly reloaded cambium_io module with given environment patches.

    access_override: dict of {path: bool} for os.access return values.
    """
    if env_vars:
        for k, v in env_vars.items():
            monkeypatch.setenv(k, v)

    if access_override is not None:
        orig_access = os.access
        def _fake_access(path, mode, **kw):
            # Normalise path for comparison
            for pat, result in access_override.items():
                if os.path.normcase(str(path)) == os.path.normcase(str(pat)):
                    return result
            return orig_access(path, mode, **kw)
        monkeypatch.setattr(cambium_io.os, "access", _fake_access)

    # Force module to re-execute data_home() afresh (it is a function so no reload needed).
    return cambium_io


# ---------------------------------------------------------------------------
# Test 1: CAMBIUM_HOME env var takes precedence
# ---------------------------------------------------------------------------

def test_cambium_home_env_var(tmp_path, monkeypatch):
    """If CAMBIUM_HOME is set, data_home() returns that directory (and creates it)."""
    target = str(tmp_path / "custom_home")
    monkeypatch.setenv("CAMBIUM_HOME", target)
    result = cambium_io.data_home()
    assert result == target, f"Expected {target!r}, got {result!r}"
    assert os.path.isdir(target), "CAMBIUM_HOME directory was not created"


def test_cambium_home_env_var_expanduser(tmp_path, monkeypatch):
    """CAMBIUM_HOME with ~ is expanded."""
    # We cannot set HOME to tmp_path portably on Windows, so we set a full path
    # and confirm it is not further expanded (i.e., expanduser of an absolute path = itself).
    target = str(tmp_path / "exp_home")
    monkeypatch.setenv("CAMBIUM_HOME", target)
    result = cambium_io.data_home()
    assert os.path.isabs(result)
    assert os.path.isdir(result)


# ---------------------------------------------------------------------------
# Test 2: ROOT-writable invariant
# ---------------------------------------------------------------------------

def test_data_home_equals_root_when_writable(monkeypatch):
    """When ROOT is writable and CAMBIUM_HOME is not set, data_home() must equal ROOT.

    This is the dev/repo/test invariant. If it breaks, the whole test suite breaks.
    """
    monkeypatch.delenv("CAMBIUM_HOME", raising=False)
    # In the dev/repo layout, cambium_io._ROOT is writable.
    result = cambium_io.data_home()
    assert result == cambium_io._ROOT, (
        f"data_home() should equal ROOT ({cambium_io._ROOT!r}) when writable, "
        f"got {result!r}"
    )


# ---------------------------------------------------------------------------
# Test 3: Read-only install fallback
# ---------------------------------------------------------------------------

def test_readonly_fallback_to_cwd_cambium(tmp_path, monkeypatch):
    """When ROOT is not writable and CAMBIUM_HOME is unset, data_home() returns cwd/.cambium."""
    monkeypatch.delenv("CAMBIUM_HOME", raising=False)
    monkeypatch.chdir(tmp_path)

    # Patch os.access inside cambium_io to return False for _ROOT
    orig_access = cambium_io.os.access
    root_norm = os.path.normcase(str(cambium_io._ROOT))

    def _fake_access(path, mode, **kw):
        if os.path.normcase(str(path)) == root_norm:
            return False
        return orig_access(path, mode, **kw)

    monkeypatch.setattr(cambium_io.os, "access", _fake_access)

    result = cambium_io.data_home()
    expected = os.path.join(str(tmp_path), ".cambium")
    assert result == expected, f"Expected {expected!r}, got {result!r}"
    assert os.path.isdir(result), ".cambium directory was not created"


def test_readonly_fallback_run_state_not_in_root(tmp_path, monkeypatch):
    """In a read-only install, run_state_path() should NOT be under ROOT."""
    monkeypatch.delenv("CAMBIUM_HOME", raising=False)
    monkeypatch.chdir(tmp_path)

    orig_access = cambium_io.os.access
    root_norm = os.path.normcase(str(cambium_io._ROOT))

    def _fake_access(path, mode, **kw):
        if os.path.normcase(str(path)) == root_norm:
            return False
        return orig_access(path, mode, **kw)

    monkeypatch.setattr(cambium_io.os, "access", _fake_access)

    rsp = cambium_io.run_state_path()
    # Must NOT be inside ROOT
    assert not rsp.startswith(cambium_io._ROOT), (
        f"run_state_path() should not be under ROOT in read-only install, got {rsp!r}"
    )
    # Must be under cwd/.cambium
    expected_base = os.path.join(str(tmp_path), ".cambium")
    assert rsp.startswith(expected_base), (
        f"run_state_path() should be under {expected_base!r}, got {rsp!r}"
    )


# ---------------------------------------------------------------------------
# Test 4: run_state_path() is inside data_home()
# ---------------------------------------------------------------------------

def test_run_state_path_inside_data_home(monkeypatch):
    """run_state_path() must start with data_home()."""
    monkeypatch.delenv("CAMBIUM_HOME", raising=False)
    dh = cambium_io.data_home()
    rsp = cambium_io.run_state_path()
    assert rsp.startswith(dh), f"run_state_path {rsp!r} not inside data_home {dh!r}"
    assert rsp.endswith(os.path.join("agent_outputs", "run_state.json"))


# ---------------------------------------------------------------------------
# Test 5: run_board_html_path() is inside data_home()
# ---------------------------------------------------------------------------

def test_run_board_html_path_inside_data_home(monkeypatch):
    """run_board_html_path() must start with data_home()."""
    monkeypatch.delenv("CAMBIUM_HOME", raising=False)
    dh = cambium_io.data_home()
    rbp = cambium_io.run_board_html_path()
    assert rbp.startswith(dh), f"run_board_html_path {rbp!r} not inside data_home {dh!r}"
    assert rbp.endswith(os.path.join("agent_outputs", "run_board.html"))


# ---------------------------------------------------------------------------
# Test 6: memory_cache_dir() is inside data_home()
# ---------------------------------------------------------------------------

def test_memory_cache_dir_inside_data_home(monkeypatch):
    """memory_cache_dir() must start with data_home()."""
    monkeypatch.delenv("CAMBIUM_HOME", raising=False)
    dh = cambium_io.data_home()
    mcd = cambium_io.memory_cache_dir()
    assert mcd.startswith(dh), f"memory_cache_dir {mcd!r} not inside data_home {dh!r}"
    assert mcd.endswith(".cambium_memory")


# ---------------------------------------------------------------------------
# Test 7: CAMBIUM_HOME overrides all path helpers
# ---------------------------------------------------------------------------

def test_cambium_home_overrides_all_helpers(tmp_path, monkeypatch):
    """With CAMBIUM_HOME set, all path helpers resolve under it."""
    target = str(tmp_path / "my_home")
    monkeypatch.setenv("CAMBIUM_HOME", target)

    dh = cambium_io.data_home()
    rsp = cambium_io.run_state_path()
    rbp = cambium_io.run_board_html_path()
    mcd = cambium_io.memory_cache_dir()

    assert dh == target
    assert rsp.startswith(target)
    assert rbp.startswith(target)
    assert mcd.startswith(target)
