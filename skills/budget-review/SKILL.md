---
name: budget-review
description: Run a deterministic budget-to-solicitation review that flags potential issues before a human checks the budget. Use when the user says "check the budget against the NOFO", "flag budget issues", "pre-award budget review", "does our budget fit the solicitation", "check F&A cap", or wants a structural check before submission. Consumes a structured rules file (from Vandalizer or manual extraction) and a structured budget. Advisory only; does not approve or certify.
---

# Budget review skill

Deterministic, rule-based budget review that flags items for human attention before
submission. Sits above document extraction: AI4RA's Vandalizer (or a human) extracts
the rules from the NOFO; this tool applies those rules mechanically to the budget and
reports every flag with the rule cited and the actual value found.

## Deterministic checks (always run, always the same for the same inputs)

| Check | Rule applied |
|---|---|
| F&A rate vs cap | budget fa_rate must be <= rules fa_rate_cap |
| Total cost vs ceiling | budget totals.total must be <= rules total_cost_ceiling |
| Period length vs max | budget period_months must be <= rules period_months_max |
| Required sections present | every section in rules required_budget_sections must appear in budget sections_present |
| Disallowed categories absent | no item in budget line_items.category may appear in rules disallowed_categories |
| Cost share present if required | if rules cost_share_required is true, budget cost_share_present must be true |

To add a new check: define a `check_<name>(rules, budget)` function in tools/budget_review.py
and call it in the `run_checks()` function. No other changes required.

## Reasoned (non-deterministic) flags -- agent layer

The grants-compliance agent (`.claude/agents/42-grants-compliance.md`) can add non-deterministic
flags on top of the deterministic ones. These are clearly separated from the deterministic results
and labeled as agent judgment, not mechanical checks. Examples:

- Flagging that a personnel cost looks low relative to the stated effort level
- Noting that a travel budget is unusually high for the project scope
- Identifying budget categories that are allowed but unusual for this sponsor

These agent-layer flags appear in a separate section of the output if the grants-compliance agent
is invoked in addition to the tool.

## How to run

```
python3 tools/budget_review.py \
    --rules examples/ai4ra/solicitation_rules.example.json \
    --budget examples/ai4ra/budget.example.json \
    [--out <path/to/report.md>]
```

Exit 0 always (flags are in the report, not the exit code). Exit 2 if an input file is missing.

## What the review does and does not do

DOES: apply the extracted solicitation rules to the budget structure and flag mismatches.
DOES NOT: certify compliance, constitute institutional approval, replace sponsored-programs
review, or guarantee the budget meets all funder requirements. The human in sponsored programs
at the submitting institution makes the final determination.

## Pairing with AI4RA Vandalizer

Vandalizer extracts structured rules from the NOFO PDF. Those rules drop into the
solicitation_rules.json format this tool consumes. Cambium then adds governance (gate sign-off,
human oversight records, evidence tiers) on top of Vandalizer's extraction layer.

## Input schemas

**solicitation_rules.json**
```json
{
  "fa_rate_cap": 0.55,
  "total_cost_ceiling": 500000,
  "period_months_max": 36,
  "required_budget_sections": ["personnel","fringe","equipment","travel","indirect"],
  "disallowed_categories": ["alcohol","entertainment"],
  "cost_share_required": false
}
```

**budget.json**
```json
{
  "period_months": 36,
  "fa_rate": 0.55,
  "totals": {"direct": 380000, "indirect": 120000, "total": 500000},
  "sections_present": ["personnel","fringe","travel","indirect"],
  "line_items": [{"category": "travel", "amount": 12000}]
}
```
