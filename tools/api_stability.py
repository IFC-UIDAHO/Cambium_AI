#!/usr/bin/env python3
"""api_stability.py -- diff Cambium's public CLI/MCP surface between two versions.

The public surface is, for every tools/*.py: the argparse option strings
(from add_argument) and subcommand names (from add_parser); plus the MCP tool
functions decorated with @mcp.tool() in mcp_server/cambium_mcp/server.py.

Usage:
    python3 tools/api_stability.py --old v1.35.0 --new HEAD [--root DIR]
    python3 tools/api_stability.py --old-dir OLD_TREE --new-dir NEW_TREE

Git refs are read with `git show REF:path` (cwd = repo root, GIT_DIR removed
from the environment); --old-dir/--new-dir compare two plain directory trees
and need no git at all (this is what the tests use).

Exit 0 after a successful diff, whatever it finds; exit 1 on invalid input
(unknown ref, missing dir, git unavailable).

Honest limits:
    - Extraction is regex-based, not an AST walk: it sees literal string
      option names in add_argument(...) / add_parser(...) calls. Dynamically
      built flags and positional argument names are not tracked, and only the
      leading run of option strings per call is captured. Good for drift
      detection, not a formal API spec.
    - The semver advice is mechanical (any removal = major, any addition =
      minor, otherwise patch); a human still decides the release number.
"""

import argparse
import glob
import os
import re
import subprocess
import sys

import cambium_io  # noqa: F401

QUOTED = re.compile(r"[\"']([^\"']*)[\"']")
ADD_ARGUMENT = re.compile(r"\badd_argument\(")
ADD_PARSER = re.compile(r"\badd_parser\(\s*[\"']([^\"']+)[\"']")
MCP_TOOL = re.compile(r"@mcp\.tool\([^)]*\)\s*\n(?:\s*@[^\n]*\n)*\s*def\s+(\w+)")
TOOL_FILE = re.compile(r"^tools/[^/]+\.py$")
WINDOW = 300


def repo_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def option_strings(window: str):
    """Leading run of quoted option strings (starting with -) in one call."""
    out = []
    pos = 0
    for m in QUOTED.finditer(window):
        between = window[pos:m.start()]
        if "=" in between or ")" in between:
            break
        token = m.group(1)
        if not token.startswith("-"):
            break
        out.append(token)
        pos = m.end()
    return out


def extract_surface(src: str):
    """Return (flags, subcommands) sets for one tool source text."""
    flags = set()
    for m in ADD_ARGUMENT.finditer(src):
        flags.update(option_strings(src[m.end():m.end() + WINDOW]))
    subs = set(ADD_PARSER.findall(src))
    return flags, subs


def extract_mcp_tools(src: str):
    return set(MCP_TOOL.findall(src))


MCP_REL = os.path.join("mcp_server", "cambium_mcp", "server.py")


def load_dir_tree(dirpath: str):
    """Surface from a plain directory tree: ({tool: (flags, subs)}, mcp set)."""
    if not os.path.isdir(dirpath):
        print("[api_stability] ERROR: not a directory: " + dirpath, file=sys.stderr)
        sys.exit(1)
    tools = {}
    for p in sorted(glob.glob(os.path.join(dirpath, "tools", "*.py"))):
        src = open(p, encoding="utf-8", errors="replace").read()
        tools[os.path.basename(p)] = extract_surface(src)
    mcp_path = os.path.join(dirpath, MCP_REL)
    mcp_src = ""
    if os.path.isfile(mcp_path):
        mcp_src = open(mcp_path, encoding="utf-8", errors="replace").read()
    return tools, extract_mcp_tools(mcp_src)


def _git_env():
    env = dict(os.environ)
    env.pop("GIT_DIR", None)
    return env


def _git(root, *args):
    try:
        return subprocess.run(["git", *args], cwd=root, env=_git_env(),
                              capture_output=True, text=True)
    except FileNotFoundError:
        print("[api_stability] ERROR: git is not on PATH; use --old-dir/--new-dir instead",
              file=sys.stderr)
        sys.exit(1)


def load_git_tree(root: str, ref: str):
    """Surface from a git ref of the repo at root."""
    ls = _git(root, "ls-tree", "-r", "--name-only", ref, "--", "tools")
    if ls.returncode != 0:
        print("[api_stability] ERROR: cannot read ref %r: %s"
              % (ref, ls.stderr.strip() or "git ls-tree failed"), file=sys.stderr)
        sys.exit(1)
    tools = {}
    for rel in sorted(l.strip() for l in ls.stdout.splitlines()):
        if not TOOL_FILE.match(rel):
            continue
        show = _git(root, "show", "%s:%s" % (ref, rel))
        if show.returncode == 0:
            tools[os.path.basename(rel)] = extract_surface(show.stdout)
    mcp_show = _git(root, "show", "%s:%s" % (ref, "mcp_server/cambium_mcp/server.py"))
    mcp_src = mcp_show.stdout if mcp_show.returncode == 0 else ""
    return tools, extract_mcp_tools(mcp_src)


def fmt(names):
    return ", ".join(sorted(names)) if names else "none"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Diff the public CLI/MCP surface between two versions.")
    ap.add_argument("--old", help="old git ref (needs git; pair with --new)")
    ap.add_argument("--new", help="new git ref (needs git; pair with --old)")
    ap.add_argument("--old-dir", help="old tree as a plain directory (pair with --new-dir)")
    ap.add_argument("--new-dir", help="new tree as a plain directory (pair with --old-dir)")
    ap.add_argument("--root", default=repo_root(), help="repo root for git mode (default: this repo)")
    args = ap.parse_args(argv)

    git_mode = bool(args.old or args.new)
    dir_mode = bool(args.old_dir or args.new_dir)
    if git_mode == dir_mode or (git_mode and not (args.old and args.new)) \
            or (dir_mode and not (args.old_dir and args.new_dir)):
        print("[api_stability] ERROR: pass either --old REF --new REF or --old-dir DIR --new-dir DIR",
              file=sys.stderr)
        return 1

    if dir_mode:
        old_label, new_label = args.old_dir, args.new_dir
        old_tools, old_mcp = load_dir_tree(args.old_dir)
        new_tools, new_mcp = load_dir_tree(args.new_dir)
    else:
        root = os.path.abspath(args.root)
        old_label, new_label = args.old, args.new
        old_tools, old_mcp = load_git_tree(root, args.old)
        new_tools, new_mcp = load_git_tree(root, args.new)

    tools_added = set(new_tools) - set(old_tools)
    tools_removed = set(old_tools) - set(new_tools)

    changes = {}  # tool name -> list of human-readable change parts
    for name in sorted(set(old_tools) & set(new_tools)):
        (of, osub), (nf, nsub) = old_tools[name], new_tools[name]
        parts = []
        parts += ["added " + f for f in sorted(nf - of)]
        parts += ["removed " + f for f in sorted(of - nf)]
        parts += ["added subcommand " + s for s in sorted(nsub - osub)]
        parts += ["removed subcommand " + s for s in sorted(osub - nsub)]
        if parts:
            changes[name] = parts

    mcp_added = new_mcp - old_mcp
    mcp_removed = old_mcp - new_mcp

    print("== api_stability: old=%s -> new=%s ==" % (old_label, new_label))
    print("tools added   : " + fmt(tools_added))
    print("tools removed : " + fmt(tools_removed))
    if changes:
        print("flag changes:")
        for name in sorted(changes):
            print("  %s: %s" % (name, "; ".join(changes[name])))
    else:
        print("flag changes  : none")
    print("mcp added     : " + fmt(mcp_added))
    print("mcp removed   : " + fmt(mcp_removed))

    any_removed = bool(tools_removed or mcp_removed
                       or any("removed" in p for parts in changes.values() for p in parts))
    any_added = bool(tools_added or mcp_added
                     or any(p.startswith("added") for parts in changes.values() for p in parts))
    if any_removed:
        advice = "MAJOR (something was removed; removals break callers)"
    elif any_added:
        advice = "MINOR (additions only; nothing was removed)"
    else:
        advice = "PATCH (no public-surface changes detected)"
    print("semver advice : " + advice)
    return 0


if __name__ == "__main__":
    sys.exit(main())
