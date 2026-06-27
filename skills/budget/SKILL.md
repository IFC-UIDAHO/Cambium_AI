---
name: budget
description: Build a proposal budget and budget justification to the solicitation's rules — personnel/effort, fringe, equipment, travel, participant costs, indirect (F&A) caps, and cost-share — and flag disallowed costs. Use when the user says "build the budget", "budget justification", "how much should we ask for", "check the F&A", "is this cost allowable", or needs the cost section of a proposal. Delegates to the Pre-Award council (budget-officer, grants-compliance) under the Orchestrator. Numbers come only from the inputs you are given; never invents figures or rates.
---

# Budget — to the funder's rules, no invented numbers

Thin Cambium-way wrapper. Hand off to the **Orchestrator**; run the budget pass. Works from the RFP
brief (run `rfp-intake` first if the caps/rules aren't known).

## Run it
1. **Pre-Award · budget-officer** — assemble the budget by category: personnel + effort, fringe,
   equipment, travel, participant/other direct costs, and indirect (F&A) within the solicitation's
   cap. Apply cost-share only if required/allowed. Every figure traces to an input you were given —
   if a rate or salary isn't provided, mark it OPEN and ask, don't guess.
2. **Pre-Award · grants-compliance** — check each line against the solicitation: disallowed costs,
   F&A cap, cost-share rules, and required budget-justification format.

## Output
A budget table + a written **justification** mapping each cost to the work, and a flagged list of any
disallowed or uncertain items. Hand back for the Director's review; pairs with the `proposal` skill
for the full submission.
