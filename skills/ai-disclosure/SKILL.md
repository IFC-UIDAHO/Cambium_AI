---
name: ai-disclosure
description: Assemble an AI-use disclosure and audit summary for a research deliverable, drawing on Cambium's own governance records (GATES.md, audit trail, agent outputs). Use when the user says "generate the AI disclosure", "AI use statement for submission", "NIH AI disclosure", "document what AI did", "prepare the disclosure for the sponsor", or needs to attach an AI-use record at G3 (submit), G5 (report release), or G6 (public release). Reads existing governance records; does NOT create new compliance certifications. Advisory only.
---

# AI-use disclosure skill

Generates a structured Markdown disclosure documenting AI assistance used in a deliverable,
the human oversight applied at each gate, and an evidence summary. Addresses requirements
such as NIH NOT-OD-25-132 and similar funder AI-use disclosure policies.

## When to generate

- **G3 (submit):** Attach to the proposal before external submission. The disclosure documents
  what AI did in drafting and which human approved each phase.
- **G5 (report release):** Attach to the progress or annual report. Documents AI assistance in
  analysis, writing, and any data processing.
- **G6 (public release):** Attach to any public deliverable, code release, or journal submission.
  All named co-authors should have signed the AI Use Statement (docs/governance/AI_USE_STATEMENT.md).

## How agents use it

1. The Orchestrator calls `tools/ai_disclosure.py --root <data_home> --title "<deliverable>"`.
2. The tool reads governance/GATES.md, governance/audit_trail.jsonl (if present),
   governance/CONTRIBUTION_LEDGER.csv (if present), and agent_outputs/*.md automatically.
3. Output is written to agent_outputs/ai_use_disclosure.md and the path is printed.
4. The Director reviews the output, adds any venue-specific wording required (see
   docs/governance/AI_USE_STATEMENT.md for venue language guidance), and attaches it to the
   submission package.

## What the disclosure does and does not do

DOES: document what AI contributed, which agents ran, and which humans approved each gate.
DOES NOT: certify regulatory compliance, constitute a legal determination, or replace
institutional review. The named human approver is responsible for all content.

## Honest language rule

The word "validate" or "validation" must not appear in the output. The tool uses "review",
"flag", and "document". Compliance is for the human to determine, not the tool.

## Command

```
python3 tools/ai_disclosure.py --title "NSF Proposal -- Soil Carbon Monitoring" \
    [--root <data_home>] [--out <path>]
```

Pairs with: `budget-review` (for pre-award submissions), `reporting` (for G5/G6 releases).
