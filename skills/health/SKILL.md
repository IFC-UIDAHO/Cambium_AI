---
name: health
description: Show Cambium's repo health and self-grade in chat without a terminal — roster validity, governance coverage, tooling, tests, version consistency, and a risk scan. Use when the user says "check Cambium's health", "is the institute healthy", "self-grade", "run the doctor", "what grade is the repo", or wants a status check on the framework itself (not on a research project). Prefers the Cambium MCP tools; falls back to the bundled Python tools. Reports the grade honestly, including any failing dimension.
---

# Health — repo self-check, no terminal needed

This surfaces the framework's own health to a Cowork user who has no shell. Run a check and report
the result plainly; do not "fix" anything here — just diagnose.

## How to run (in order of preference)
1. **Cambium MCP tools**, if the `cambium` MCP server is connected: call `cambium_grade()` for the
   A–F self-grade + risk scan and `cambium_doctor()` for full health (counts, HTML integrity, parses,
   derived-sync). Use `cambium_validate()` on a ledger if one is in scope.
2. **Bundled tools via Bash**, if no MCP and a shell is available:
   `python3 tools/doctor.py --grade` (grade + risks) and `python3 tools/doctor.py` (full health).
3. **Neither available** — say so and point the user to install the MCP server
   (`uvx cambium-mcp`, registered in `claude_desktop_config.json`) or run the tools in a terminal.

## Report
Give the user, in plain language:
- the **overall grade** (A–F) and the **per-dimension** scores (roster, governance, tooling, tests,
  docs, decisions, version consistency, security),
- any **dimension below 100%** and what it means,
- the **risk scan** result (or "none found").

Be honest: if a dimension fails or a tool can't run, say so rather than reporting a clean bill.
