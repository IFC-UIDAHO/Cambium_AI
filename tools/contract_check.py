#!/usr/bin/env python3
"""contract_check -- static MCP contract guard for mcp_server/cambium_mcp/server.py.

Never imports the mcp package or the server module (importing would require the mcp dependency
to be installed and would execute server-startup code). Instead it ast.parse()s the server
source file directly and collects every function decorated with @mcp.tool(): its name, its
ordered argument names, its default values (as repr strings, so JSON-safe), and whether it has
a docstring.

Compares this live signature list against a golden snapshot at tools/mcp_contract.json and
reports added tools, removed tools, and changed tools (arg list, defaults, or docstring
presence differs).

Usage:
  python3 tools/contract_check.py                # compare live server against the golden
  python3 tools/contract_check.py --server PATH   # check a different server.py (e.g. a doctored
                                                   # copy in a tmp dir, for drift testing)
  python3 tools/contract_check.py --golden PATH   # compare against a different golden file
  python3 tools/contract_check.py --update        # rewrite the golden from the current server

Exit codes:
  0  live server matches the golden (or --update succeeded)
  1  drift detected (added/removed/changed tools), or the server file could not be parsed
"""
from __future__ import annotations
import argparse
import ast
import json
import os
import sys

import cambium_io  # noqa: F401 -- UTF-8 stdout/stderr guard on Windows

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_SERVER = os.path.join(ROOT, "mcp_server", "cambium_mcp", "server.py")
DEFAULT_GOLDEN = os.path.join(ROOT, "tools", "mcp_contract.json")


def _is_mcp_tool_decorator(node) -> bool:
    """True if a decorator AST node is (some form of) mcp.tool(...) -- a Call whose func is an
    Attribute named 'tool' on any base name (works whether the FastMCP instance is called
    'mcp', imported under another alias, etc.), since only the attribute name is contractual."""
    if not isinstance(node, ast.Call):
        return False
    func = node.func
    return isinstance(func, ast.Attribute) and func.attr == "tool"


def _default_repr(node) -> str:
    """repr() of a default-value AST node, using ast.literal_eval where possible so the golden
    JSON holds plain values; falls back to ast.unparse() for anything non-literal."""
    try:
        return repr(ast.literal_eval(node))
    except (ValueError, TypeError, SyntaxError):
        try:
            return ast.unparse(node)
        except Exception:
            return "<unrepresentable>"


def extract_tools(source: str) -> dict:
    """Parse source and return {tool_name: {"args": [...], "defaults": [...], "has_docstring": bool}}
    for every top-level function decorated with @mcp.tool(). Raises SyntaxError if source does
    not parse."""
    tree = ast.parse(source)
    tools = {}
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if not any(_is_mcp_tool_decorator(d) for d in node.decorator_list):
            continue
        args_node = node.args
        arg_names = [a.arg for a in args_node.args]
        defaults = [_default_repr(d) for d in args_node.defaults]
        has_docstring = ast.get_docstring(node) is not None
        tools[node.name] = {
            "args": arg_names,
            "defaults": defaults,
            "has_docstring": has_docstring,
        }
    return tools


def extract_tools_from_file(server_path: str) -> dict:
    with open(server_path, encoding="utf-8") as fh:
        source = fh.read()
    return extract_tools(source)


def load_golden(golden_path: str) -> dict:
    if not os.path.exists(golden_path):
        return {}
    with open(golden_path, encoding="utf-8") as fh:
        return json.load(fh)


def save_golden(golden_path: str, tools: dict) -> None:
    os.makedirs(os.path.dirname(golden_path) or ".", exist_ok=True)
    with open(golden_path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(tools, fh, ensure_ascii=False, indent=2, sort_keys=True)
        fh.write("\n")


def diff_contracts(live: dict, golden: dict) -> dict:
    """Return {"added": [...], "removed": [...], "changed": {name: {"live": ..., "golden": ...}}}."""
    live_names, golden_names = set(live), set(golden)
    added = sorted(live_names - golden_names)
    removed = sorted(golden_names - live_names)
    changed = {}
    for name in sorted(live_names & golden_names):
        if live[name] != golden[name]:
            changed[name] = {"live": live[name], "golden": golden[name]}
    return {"added": added, "removed": removed, "changed": changed}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Static drift guard for the Cambium MCP tool contract.")
    ap.add_argument("--server", default=DEFAULT_SERVER, help="Path to the MCP server.py to check.")
    ap.add_argument("--golden", default=DEFAULT_GOLDEN, help="Path to the golden contract JSON.")
    ap.add_argument("--update", action="store_true", help="Rewrite the golden from the current server.")
    args = ap.parse_args(argv)

    if not os.path.exists(args.server):
        print(f"[contract_check] ERROR: server file not found: {args.server}", file=sys.stderr)
        return 1

    try:
        live = extract_tools_from_file(args.server)
    except SyntaxError as exc:
        print(f"[contract_check] ERROR: cannot parse {args.server}: {exc}", file=sys.stderr)
        return 1

    if args.update:
        save_golden(args.golden, live)
        print(f"[contract_check] updated golden: {len(live)} tool(s) -> {args.golden}")
        return 0

    golden = load_golden(args.golden)
    diff = diff_contracts(live, golden)

    print(f"[contract_check] {len(live)} live tool(s) vs {len(golden)} golden tool(s)")
    if diff["added"]:
        print(f"[contract_check] ADDED ({len(diff['added'])}): {', '.join(diff['added'])}")
    if diff["removed"]:
        print(f"[contract_check] REMOVED ({len(diff['removed'])}): {', '.join(diff['removed'])}")
    if diff["changed"]:
        print(f"[contract_check] CHANGED ({len(diff['changed'])}):")
        for name, delta in diff["changed"].items():
            print(f"  {name}: live={delta['live']} golden={delta['golden']}")

    if diff["added"] or diff["removed"] or diff["changed"]:
        print("[contract_check] DRIFT DETECTED.")
        return 1

    print("[contract_check] OK -- contract matches golden.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
