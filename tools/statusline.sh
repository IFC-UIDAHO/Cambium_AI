#!/usr/bin/env bash
# Cambium status line wrapper for Claude Code (/statusline → command: bash tools/statusline.sh).
# Pipes Claude Code's JSON status payload (stdin) to the Python renderer.
exec python3 "$(dirname "$0")/statusline.py"
