"""
gen_readme.py — Auto-sync factual blocks in README.md between marker pairs.

Usage:
    python3 tools/gen_readme.py           # rewrite README.md in place
    python3 tools/gen_readme.py --check   # exit 1 if stale, 0 if clean

Markers handled:
    <!-- CAMBIUM:STATS -->  ...  <!-- /CAMBIUM:STATS -->
    <!-- CAMBIUM:WHATSNEW -->  ...  <!-- /CAMBIUM:WHATSNEW -->

Exit codes:
    0  clean / updated successfully
    1  (--check only) README is stale
    2  a required marker pair is missing from README.md
"""

import os
import re
import sys
import difflib
import pathlib

# ---------------------------------------------------------------------------
# Repo-root discovery: assume this script lives in <root>/tools/
# ---------------------------------------------------------------------------
REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

README_PATH = REPO_ROOT / "README.md"
CHANGELOG_PATH = REPO_ROOT / "CHANGELOG.md"
TOOLS_DIR = REPO_ROOT / "tools"
SKILLS_DIR = REPO_ROOT / "skills"
TEMPLATES_DIR = REPO_ROOT / "templates"

# Templates to exclude (runtime artifacts listed by name)
TEMPLATES_RUNTIME_EXCLUSIONS = {"findings_ledger.csv", "leaderboard.md", "master_plan.md"}
# Extensions that count as templates
TEMPLATES_VALID_EXTENSIONS = {".md", ".html", ".yml", ".yaml", ".json"}


# ---------------------------------------------------------------------------
# Count helpers
# ---------------------------------------------------------------------------

def count_tools() -> int:
    """Count *.py files directly in tools/."""
    if not TOOLS_DIR.is_dir():
        return 0
    return sum(
        1 for f in TOOLS_DIR.iterdir()
        if f.is_file() and f.suffix == ".py" and f.name != "gen_readme.py"
    )


def count_tools_including_self() -> int:
    """Count *.py files directly in tools/ including gen_readme.py itself."""
    if not TOOLS_DIR.is_dir():
        return 0
    return sum(1 for f in TOOLS_DIR.iterdir() if f.is_file() and f.suffix == ".py")


def count_skills() -> int:
    """Count immediate subdirectories under skills/ that contain a SKILL.md."""
    if not SKILLS_DIR.is_dir():
        return 0
    count = 0
    for d in SKILLS_DIR.iterdir():
        if d.is_dir() and (d / "SKILL.md").exists():
            count += 1
    return count


def count_templates() -> int:
    """
    Count files directly in templates/ (not subdirectories) that:
    - have a valid template extension (.md, .html, .yml, .yaml, .json)
    - are NOT in the runtime exclusions list
    """
    if not TEMPLATES_DIR.is_dir():
        return 0
    count = 0
    for f in TEMPLATES_DIR.iterdir():
        if not f.is_file():
            continue
        if f.name in TEMPLATES_RUNTIME_EXCLUSIONS:
            continue
        if f.suffix.lower() in TEMPLATES_VALID_EXTENSIONS:
            count += 1
    return count


def read_mcp_from_readme(readme_text: str) -> int:
    """
    Extract the MCP count from the existing README STATS block, or scan the
    broader text for the 'N MCP tools' pattern. Falls back to 6.
    """
    # Try to read from the existing STATS block first
    stats_match = re.search(
        r"<!--\s*CAMBIUM:STATS\s*-->(.*?)<!--\s*/CAMBIUM:STATS\s*-->",
        readme_text,
        re.DOTALL,
    )
    if stats_match:
        inner = stats_match.group(1)
        m = re.search(r"(\d+)\s+MCP\s+tools", inner, re.IGNORECASE)
        if m:
            return int(m.group(1))
    # Fall back: scan the full README
    m = re.search(r"(\d+)\s+MCP\s+tools", readme_text, re.IGNORECASE)
    if m:
        return int(m.group(1))
    return 6


# ---------------------------------------------------------------------------
# CHANGELOG parser
# ---------------------------------------------------------------------------

def parse_changelog_top3(changelog_text: str) -> list:
    """
    Parse CHANGELOG.md and return the top 3 version entries as
    list of (version, headline_first_sentence) tuples.

    Expects headings of the form:
        ## {version} - {date} — {headline}
    or:
        ## {version} - {date} - {headline}
    """
    # Match lines like: ## 1.15.0 - 2026-06-28 — Headline text
    heading_pattern = re.compile(
        r"^##\s+([\d.]+)\s+-\s+[\d-]+\s+[—\-]+\s+(.+)$",
        re.MULTILINE,
    )
    entries = []
    for m in heading_pattern.finditer(changelog_text):
        version = m.group(1).strip()
        headline = m.group(2).strip()
        # First sentence: up to first period, !, or ? followed by space or end
        sentence_match = re.match(r"([^.!?]+[.!?]?)(?:\s|$)", headline)
        first_sentence = sentence_match.group(1).rstrip() if sentence_match else headline
        entries.append((version, first_sentence))
        if len(entries) == 3:
            break
    return entries


# ---------------------------------------------------------------------------
# Content generators
# ---------------------------------------------------------------------------

def generate_stats_content(readme_text: str) -> str:
    """Return the one-line STATS content (no surrounding markers)."""
    tools = count_tools_including_self()
    skills = count_skills()
    templates = count_templates()
    mcp = read_mcp_from_readme(readme_text)
    return (
        f"{skills} skills, {tools} tools, {mcp} MCP tools, {templates} templates, "
        "and a set of worked examples. All field-agnostic, all runnable."
    )


def generate_whatsnew_content(changelog_text: str) -> str:
    """Return the WHATSNEW markdown list (no surrounding markers)."""
    entries = parse_changelog_top3(changelog_text)
    if not entries:
        return "_(no CHANGELOG entries found)_"
    lines = [f"- **{v}**: " + h.replace("\u2014","-").replace("\u2013","-") for v, h in entries]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Marker injection
# ---------------------------------------------------------------------------

def inject_block(readme_text: str, marker: str, new_content: str) -> tuple:
    """
    Replace the content between <!-- CAMBIUM:{marker} --> and
    <!-- /CAMBIUM:{marker} --> with new_content.

    Returns (updated_text, found_bool).
    """
    open_marker = f"<!-- CAMBIUM:{marker} -->"
    close_marker = f"<!-- /CAMBIUM:{marker} -->"

    if open_marker not in readme_text or close_marker not in readme_text:
        return readme_text, False

    pattern = re.compile(
        re.escape(open_marker) + r"(.*?)" + re.escape(close_marker),
        re.DOTALL,
    )
    replacement = f"{open_marker}\n{new_content}\n{close_marker}"
    updated = pattern.sub(replacement, readme_text)
    return updated, True


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    check_mode = "--check" in sys.argv

    # Read README
    if not README_PATH.exists():
        print(f"ERROR: README.md not found at {README_PATH}", file=sys.stderr)
        sys.exit(2)

    readme_text = README_PATH.read_text(encoding="utf-8")

    # Read CHANGELOG
    changelog_text = ""
    if CHANGELOG_PATH.exists():
        changelog_text = CHANGELOG_PATH.read_text(encoding="utf-8")

    # Verify both marker pairs exist before doing anything
    missing = []
    for marker in ("STATS", "WHATSNEW"):
        open_m = f"<!-- CAMBIUM:{marker} -->"
        close_m = f"<!-- /CAMBIUM:{marker} -->"
        if open_m not in readme_text:
            missing.append(open_m)
        if close_m not in readme_text:
            missing.append(close_m)

    if missing:
        for m in missing:
            print(f"ERROR: missing marker in README.md: {m}")
        sys.exit(2)

    # Generate new content
    stats_content = generate_stats_content(readme_text)
    whatsnew_content = generate_whatsnew_content(changelog_text)

    # Inject
    updated, _ = inject_block(readme_text, "STATS", stats_content)
    updated, _ = inject_block(updated, "WHATSNEW", whatsnew_content)

    if check_mode:
        if updated == readme_text:
            print("README auto-synced blocks are up to date.")
            sys.exit(0)
        else:
            diff = list(
                difflib.unified_diff(
                    readme_text.splitlines(keepends=True),
                    updated.splitlines(keepends=True),
                    fromfile="README.md (current)",
                    tofile="README.md (generated)",
                )
            )
            print("README auto-synced blocks are STALE. Diff:")
            print("".join(diff))
            sys.exit(1)
    else:
        README_PATH.write_text(updated, encoding="utf-8")
        if updated != readme_text:
            print("README.md updated (STATS and WHATSNEW blocks refreshed).")
        else:
            print("README.md already up to date, no changes written.")


if __name__ == "__main__":
    main()
