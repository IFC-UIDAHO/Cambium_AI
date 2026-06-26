#!/usr/bin/env bash
# quickstart.sh — one-command setup for the Cambium
# Usage: bash tools/quickstart.sh
# Safe: read-only except copying config.example.yml → config.yml (only if missing).

set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo ""
echo "======================================================"
echo "  Cambium — Quickstart"
echo "======================================================"
echo ""

# ── 1. Copy config if missing ──────────────────────────────────────────────
if [ ! -f config.yml ]; then
    cp config.example.yml config.yml
    echo "[setup] config.yml created from config.example.yml"
    echo "        -> Edit it now: set institute.name, director, and your team."
else
    echo "[setup] config.yml already exists — skipping copy."
fi

# ── 2. Validate agents and governance (smoke test) ─────────────────────────
echo ""
echo "[setup] Running agent frontmatter check..."
python3 tools/check_agents.py

echo ""
echo "[setup] Running governance validate (CI ledger)..."
python3 governance/validate.py tools/ci_ledger.csv

# ── 3. Next steps ──────────────────────────────────────────────────────────
echo ""
echo "======================================================"
echo "  Next steps"
echo "======================================================"
echo ""
echo "  1. Edit config.yml  — set your lab name, director, and team."
echo "  2. Open dashboard.html in a browser to see your institute org chart."
echo "  3. Say a trigger phrase in Claude to begin:"
echo ""
echo "  Trigger phrases:"
echo "    'new project: <name>'        — register a project folder"
echo "    'read rfp <file/link>'       — start from an RFP (Gate G1)"
echo "    'project approved'           — flip to mid-project mode"
echo "    'run lab'                    — develop → verify → synthesize"
echo "    'progress report'            — generate a progress report"
echo ""
echo "  Full guide: GETTING_STARTED.md"
echo "======================================================"
echo ""
