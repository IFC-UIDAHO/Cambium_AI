# Response to the external code review (deep-research report)

A reviewer produced a "Priority Fixes" report on Cambium. We take outside review seriously — so here is an
honest, file-grounded response, produced the Cambium way (Integrity Officer mapped each fix to the actual
code; Verification confirmed; approved at a human gate).

## First, a scope caveat the review itself states

The report opens: *"Without direct access to the code, we infer a typical structure…"* — it was written
**without reading the repository**, and it describes a **different product that shares the name** (an
LLM-over-US-Census-data startup with "synthetic personas" and a "Bonnie Morris" persona demo). Cambium here
is a field-agnostic **research-institution framework**. So several "gaps" describe a system that isn't this
one. We still mapped every Priority Fix to our actual mechanisms, because the *principles* (oversight,
auditability, AI/human visibility, feedback, testing) are exactly Cambium's.

## The five Priority Fixes vs. what Cambium already enforces

| # | Priority Fix | Status in Cambium | Where (file) |
|---|--------------|-------------------|--------------|
| 1 | Mandatory human review before an AI output is final | **Already** | 8 gates with APPROVE/REVISE/REJECT (`templates/GATE_SUMMARY.md` §7), `tools/gate.py`, tamper-evident token `tools/gate_lock.py`, ledger `governance/GATES.md`; a bare APPROVE is blocked (`tools/learning_gate.py`) |
| 2 | Audit logging (query, prompt, model, output, action) | **Now closed** | Gate/claim records already existed; **added** turn-level append-only, hash-chained `tools/audit_log.py` → `governance/audit_trail.jsonl` |
| 3 | Annotate AI- vs human-authored content | **Already (logs)** | `change_ratio` + `copy_flag` + human-vs-AI diffs (`tools/learning_gate.py`, `governance/contribution_diffs/`), `AI_USE_STATEMENT.md`. Residual: sentence-span tagging inside documents (optional, not built) |
| 4 | Capture user feedback / learning loop | **Now closed** | `feedback-router` agent already existed; **added** document-level `tools/draft_diff.py` → `governance/DRAFT_CORRECTION_LEDGER.csv` recording exactly what the human changed in an AI draft |
| 5 | Basic testing & validation | **Already** | full pytest suite + CI (`.github/workflows/validate.yml`), 4-tier evidence contract `governance/validate.py`, the `tools/enforce.py` gauntlet |

**Net:** fixes 1, 3 (logs), and 5 were already met; fixes 2 and 4 had real residuals, which we built
(`audit_log.py`, `draft_diff.py`). Sentence-span annotation (#3 residual) is noted as optional and not yet
built — stated plainly rather than papered over.

## The one thing the review got right for us in practice

Separately, the Director observed the highest-value bug: typing `/cambium` sometimes produced a **plain
text answer with no run board, no named agents, no gate** — the four-act UI silently skipped. Fixed by
collapsing Act I into a single deterministic command, `tools/cambium_start.py "<task>"`, that resets state,
paints the text + HTML board, and prints a hard "do NOT answer in plain text" banner; the `/cambium`
command and `PRESENTATION.md` now lead with it. The UI is now the easy path, not an optional one.
