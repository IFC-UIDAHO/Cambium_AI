"""tests/test_api_stability.py -- tests for tools/api_stability.py.

Uses --old-dir/--new-dir fixture trees only: offline, no git required.
"""
import pathlib
import subprocess
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
TOOL = REPO_ROOT / "tools" / "api_stability.py"

BASE_TOOL = '''import argparse
p = argparse.ArgumentParser()
p.add_argument("--input", required=True)
p.add_argument("-q", "--quiet", action="store_true")
sub = p.add_subparsers(dest="cmd")
sub.add_parser("build")
'''

MCP_SRC = '''@mcp.tool()
def cambium_alpha(task: str) -> dict:
    """One tool."""
    return {}
'''


def make_tree(root, tool_src=BASE_TOOL, mcp_src=MCP_SRC):
    (root / "tools").mkdir(parents=True)
    (root / "tools" / "alpha.py").write_text(tool_src, encoding="utf-8")
    mcp_dir = root / "mcp_server" / "cambium_mcp"
    mcp_dir.mkdir(parents=True)
    (mcp_dir / "server.py").write_text(mcp_src, encoding="utf-8")
    return root


def run_diff(old, new):
    return subprocess.run(
        [sys.executable, str(TOOL), "--old-dir", str(old), "--new-dir", str(new)],
        capture_output=True, text=True)


def test_identical_trees_advise_patch(tmp_path):
    old = make_tree(tmp_path / "old")
    new = make_tree(tmp_path / "new")
    r = run_diff(old, new)
    assert r.returncode == 0, r.stderr
    assert "PATCH" in r.stdout
    assert "tools removed : none" in r.stdout


def test_added_flag_and_subcommand_advise_minor(tmp_path):
    old = make_tree(tmp_path / "old")
    new = make_tree(tmp_path / "new",
                    tool_src=BASE_TOOL + 'p.add_argument("--verbose")\nsub.add_parser("deploy")\n')
    r = run_diff(old, new)
    assert r.returncode == 0
    assert "MINOR" in r.stdout
    assert "added --verbose" in r.stdout
    assert "added subcommand deploy" in r.stdout


def test_removed_flag_advises_major(tmp_path):
    old = make_tree(tmp_path / "old")
    new = make_tree(tmp_path / "new",
                    tool_src=BASE_TOOL.replace('p.add_argument("-q", "--quiet", action="store_true")\n', ""))
    r = run_diff(old, new)
    assert r.returncode == 0
    assert "MAJOR" in r.stdout
    assert "removed --quiet" in r.stdout and "removed -q" in r.stdout


def test_removed_tool_file_advises_major(tmp_path):
    old = make_tree(tmp_path / "old")
    new = make_tree(tmp_path / "new")
    (old / "tools" / "beta.py").write_text('import argparse\n', encoding="utf-8")
    r = run_diff(old, new)
    assert r.returncode == 0
    assert "tools removed : beta.py" in r.stdout
    assert "MAJOR" in r.stdout


def test_added_mcp_tool_advises_minor(tmp_path):
    old = make_tree(tmp_path / "old")
    new = make_tree(tmp_path / "new",
                    mcp_src=MCP_SRC + '\n@mcp.tool()\ndef cambium_extra(x: str) -> dict:\n    return {}\n')
    r = run_diff(old, new)
    assert r.returncode == 0
    assert "mcp added     : cambium_extra" in r.stdout
    assert "MINOR" in r.stdout


def test_aliases_and_keyword_strings_are_separated(tmp_path):
    # help="..." strings must not be mistaken for option strings
    src = 'import argparse\np = argparse.ArgumentParser()\np.add_argument("-n", "--num", help="how many --items to keep")\n'
    old = make_tree(tmp_path / "old", tool_src=src)
    new = make_tree(tmp_path / "new", tool_src=src.replace('"-n", "--num"', '"-n", "--num", "--count"'))
    r = run_diff(old, new)
    assert r.returncode == 0
    assert "added --count" in r.stdout
    assert "--items" not in r.stdout


def test_missing_dir_exits_one(tmp_path):
    old = make_tree(tmp_path / "old")
    r = run_diff(old, tmp_path / "does-not-exist")
    assert r.returncode == 1
    assert "not a directory" in r.stderr


def test_help_exits_zero():
    r = subprocess.run([sys.executable, str(TOOL), "--help"], capture_output=True, text=True)
    assert r.returncode == 0
    assert "--old-dir" in r.stdout and "--new" in r.stdout
