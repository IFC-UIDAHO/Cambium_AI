#!/usr/bin/env python3
"""sync_version -- stamp the latest CHANGELOG version into the three manifests.

The release version lives in one place: the newest "## X.Y.Z" heading in CHANGELOG.md.
Three files must agree with it, or the plugin will not update and CI fails:
  .claude-plugin/plugin.json        ("version": "...")
  .claude-plugin/marketplace.json   (plugins[0].version, "version": "...")
  mcp_server/pyproject.toml         (version = "...")

This tool reads the CHANGELOG version and writes it into all three, using a targeted
regex replace so the files are not reformatted. It is idempotent: if a file already
matches, it is left untouched.

Run it before every commit (the push script calls it):
    python3 tools/sync_version.py
Check-only mode for CI (exit 1 if any file drifts, writes nothing):
    python3 tools/sync_version.py --check
"""
from __future__ import annotations
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

_PLUGIN = os.path.join(ROOT, ".claude-plugin", "plugin.json")
_MARKET = os.path.join(ROOT, ".claude-plugin", "marketplace.json")
_PYPROJECT = os.path.join(ROOT, "mcp_server", "pyproject.toml")
_README = os.path.join(ROOT, "README.md")


def changelog_version() -> str:
    """Return the newest X.Y.Z from CHANGELOG.md, or raise if none is found."""
    path = os.path.join(ROOT, "CHANGELOG.md")
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            m = re.match(r"^##\s+(\d+\.\d+\.\d+)\b", line.strip())
            if m:
                return m.group(1)
    raise SystemExit("[sync_version] ERROR: no '## X.Y.Z' heading found in CHANGELOG.md")


# each target: (path, regex that captures the version, a formatter old->new line)
def _json_version_sub(text: str, version: str) -> tuple[str, str | None]:
    """Replace the first '"version": "..."' in a JSON file. Returns (new_text, old)."""
    m = re.search(r'("version"\s*:\s*")(\d+\.\d+\.\d+)(")', text)
    if not m:
        return text, None
    old = m.group(2)
    if old == version:
        return text, old
    new = text[:m.start()] + m.group(1) + version + m.group(3) + text[m.end():]
    return new, old


def _toml_version_sub(text: str, version: str) -> tuple[str, str | None]:
    """Replace 'version = "..."' in a pyproject.toml. Returns (new_text, old)."""
    m = re.search(r'(?m)^(version\s*=\s*")(\d+\.\d+\.\d+)(")', text)
    if not m:
        return text, None
    old = m.group(2)
    if old == version:
        return text, old
    new = text[:m.start()] + m.group(1) + version + m.group(3) + text[m.end():]
    return new, old


def _readme_badge_sub(text: str, version: str) -> tuple[str, str | None]:
    """Replace the shields.io version badge (badge/version-X) in README.md."""
    m = re.search(r'(badge/version-)(\d+\.\d+\.\d+)', text)
    if not m:
        return text, None
    old = m.group(2)
    if old == version:
        return text, old
    new = text[:m.start()] + m.group(1) + version + text[m.end():]
    return new, old


def _apply(path: str, sub, version: str, check: bool) -> tuple[str, bool]:
    """Return (status_line, drifted). Writes the file unless check is True."""
    rel = os.path.relpath(path, ROOT)
    if not os.path.exists(path):
        return f"  {rel}: MISSING", False
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    new_text, old = sub(text, version)
    if old is None:
        return f"  {rel}: no version field found", False
    if old == version:
        return f"  {rel}: {version} (ok)", False
    if check:
        return f"  {rel}: {old} -> {version} (DRIFT)", True
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(new_text)
    return f"  {rel}: {old} -> {version} (updated)", True


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    check = "--check" in argv
    version = changelog_version()
    print(f"[sync_version] CHANGELOG version: {version}")

    results = [
        _apply(_PLUGIN, _json_version_sub, version, check),
        _apply(_MARKET, _json_version_sub, version, check),
        _apply(_PYPROJECT, _toml_version_sub, version, check),
        _apply(_README, _readme_badge_sub, version, check),
    ]
    drifted = any(d for _, d in results)
    for line, _ in results:
        print(line)

    if check and drifted:
        print("[sync_version] --check: version drift found. Run 'python3 tools/sync_version.py' to fix.")
        return 1
    if not check and drifted:
        print("[sync_version] manifests stamped to match CHANGELOG.")
    else:
        print("[sync_version] all manifests already match CHANGELOG.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
