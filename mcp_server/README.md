# Cambium MCP server

Exposes Cambium's tools to any MCP client (Claude Desktop / Claude Code / Cursor) so the AI can call them
as native tools: `cambium_plan`, `cambium_provision`, `cambium_agents`, `cambium_doctor`, `cambium_grade`,
`cambium_validate`.

## Install & run
```
pip install "mcp[cli]" PyYAML        # SDK + dep
python -m cambium_mcp.server         # stdio server (from the mcp_server/ dir, or after `pip install -e mcp_server/`)
```
Or packaged: `uvx --from git+https://github.com/IFC-UIDAHO/Cambium_AI#subdirectory=mcp_server cambium-mcp`

## Register in Claude (claude_desktop_config.json → mcpServers)
```json
{
  "mcpServers": {
    "cambium": { "command": "python", "args": ["-m", "cambium_mcp.server"] }
  }
}
```
uvx form:
```json
{ "mcpServers": { "cambium": { "command": "uvx", "args": ["cambium-mcp"] } } }
```

## Tools
| Tool | Does |
|---|---|
| `cambium_plan(task)` | which councils/agents + gate plan for any task |
| `cambium_provision(task)` | recommended existing tools/packages (reuse-beats-rebuild) |
| `cambium_agents()` | the live roster |
| `cambium_doctor()` | repo health |
| `cambium_grade()` | self-grade A–F + risk scan |
| `cambium_validate(ledger_csv)` | evidence-ledger check (blocks fake claims) |
