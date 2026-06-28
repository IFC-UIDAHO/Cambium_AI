# TOOL_POLICY.md — provisioning & dependency policy
*How Cambium acquires tools. Reuse beats rebuild — but installing third-party code is a supply-chain
risk, so the Toolsmith RECOMMENDS and the human APPROVES before anything is installed.*

## Principles
1. **Reuse first.** Prefer a maintained package / component / skill / MCP over writing from scratch.
2. **Human gate before install.** The Toolsmith outputs a manifest; nothing is installed until the
   Director (or delegate) approves at the **provisioning gate**.
3. **Pin & verify.** Pin exact versions; record the source; prefer popular, actively-maintained,
   permissively-licensed packages; flag anything unmaintained or of unknown provenance.
4. **Sandbox first.** Install into a venv / throwaway env and test before adopting into the project.
5. **License hygiene.** Record each dependency's license; avoid copyleft where it conflicts with the
   project's license; keep attribution (e.g. SRI hash + credit for CDN libs).
6. **Least privilege for MCP connectors.** Only connect what the task needs; log tool calls.

## The provisioning gate (G-provision)
Added by the Task Router at the start of software/research/data tasks. The run STOPS with the manifest;
approve, edit, or decline. Approved installs are recorded (date, versions, approver).

## Sources the Toolsmith may use
npm / PyPI · shadcn/ui · 21st.dev · Magic MCP · the MCP connector registry · Cambium skills ·
open datasets · free/open APIs. Always web-verify currency before recommending.

## Approved provisioning records
| date | tool | version | approver | scope / notes |
| --- | --- | --- | --- | --- |
| 2026-06-26 | SemanticCite (optional) | pin at install | Director (ADR-007) | Optional claim<->source verifier for `tools/cite_check.py`. MIT, arXiv 2511.16198. Prefer the local-Ollama path (no API key, no data leaves the box). NOT yet installed on the host -- the shim runs in advisory no-op mode until `pip install semanticcite` (or a configured `OLLAMA_HOST`) is present. Install is performed on the human's machine, not in the agent sandbox. |
