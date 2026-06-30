"""cambium_io -- UTF-8 stdout/stderr guard for Windows terminals, plus the
writable-data-home resolver for plugin-safe installs.

UTF-8 guard
-----------
On Windows the default console encoding is cp1252 (or similar narrow codepage),
which cannot represent the Unicode glyphs Cambium tools print.  Import this
module as early as possible in any tool that prints non-ASCII characters.
It reconfigures stdout and stderr to UTF-8 *in process*, so no env-var or
terminal setting is required by the caller.

data_home() -- writable run-data directory
-------------------------------------------
When Cambium is installed as a read-only plugin, ROOT (the install dir) is not
writable, so any tool that writes run state, boards, or memory caches would
fail.  data_home() separates read-only CODE from writable run-DATA:

Precedence (fully backward-compatible):

  1. CAMBIUM_HOME env var -- if set, use it (expanduser; create if missing).
  2. ROOT is writable -- return ROOT exactly.  THIS IS THE DEV/REPO/TEST CASE:
     behavior is unchanged and every existing test still passes because
     data_home() == ROOT when ROOT is writable.
  3. Read-only install fallback -- return os.path.join(os.getcwd(), ".cambium"),
     created if missing.  Run data travels with the user's project.

Convenience path helpers
------------------------
  run_state_path()    -> data_home() / agent_outputs / run_state.json
  run_board_html_path() -> data_home() / agent_outputs / run_board.html
  memory_cache_dir()  -> data_home() / .cambium_memory
"""
import os
import sys

# ---------------------------------------------------------------------------
# UTF-8 stdout/stderr guard (must execute on import)
# ---------------------------------------------------------------------------

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# ---------------------------------------------------------------------------
# Root detection (install dir = parent of this file's directory)
# ---------------------------------------------------------------------------

_TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_TOOLS_DIR)


# ---------------------------------------------------------------------------
# data_home() -- the single source of truth for where run data is written
# ---------------------------------------------------------------------------

def data_home() -> str:
    """Return the writable directory that stores all Cambium run-time data.

    Precedence:
      1. CAMBIUM_HOME env var -- expanduser; dir is created if missing.
      2. ROOT writable -- return ROOT (dev/repo/test case; no behavior change).
      3. Fallback (read-only install) -- os.path.join(os.getcwd(), ".cambium"),
         created if missing.  Run data stays with the user project.
    """
    env = os.environ.get("CAMBIUM_HOME", "").strip()
    if env:
        path = os.path.expanduser(env)
        os.makedirs(path, exist_ok=True)
        return path

    if os.access(_ROOT, os.W_OK):
        return _ROOT

    # Read-only install: per-project writable dir
    path = os.path.join(os.getcwd(), ".cambium")
    os.makedirs(path, exist_ok=True)
    return path


# ---------------------------------------------------------------------------
# Convenience helpers
# ---------------------------------------------------------------------------

def run_state_path() -> str:
    """Canonical path to agent_outputs/run_state.json under data_home()."""
    return os.path.join(data_home(), "agent_outputs", "run_state.json")


def run_board_html_path() -> str:
    """Canonical path to agent_outputs/run_board.html under data_home()."""
    return os.path.join(data_home(), "agent_outputs", "run_board.html")


def memory_cache_dir() -> str:
    """Canonical path to .cambium_memory cache dir under data_home()."""
    return os.path.join(data_home(), ".cambium_memory")
