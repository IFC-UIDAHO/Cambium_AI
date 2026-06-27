---
name: run-lab
description: Run the post-award research loop — provision tools, build the method, run experiments, and verify every number — then stop at gate G4 "accept results?". Use when the user says "run the lab", "project approved", "run the experiments", "build and test the method", "execute the study", or wants development → verification → synthesis on an approved project. Delegates to Support (toolsmith), Labs (theory/methods/domain/statistics), Execution (experiments/ablation/iteration/research-engineer), and Verification under the Orchestrator. Runs code; reproduces headline numbers before accepting them.
---

# Run lab — development → verification → synthesis

Thin Cambium-way wrapper. Hand off to the **Orchestrator**; run the post-award engine.

## Run it
1. **Support · toolsmith** — provision: find existing packages/datasets/MCPs before building from
   scratch (reuse beats rebuild). Pause at **G-provision** if approval is needed to install anything.
2. **Labs** — build the core contribution: lab-theory (claims/assumptions), lab-methods (the method),
   lab-domain (real-world meaning), lab-statistics (the actual numbers).
3. **Execution** — exec-experiments and exec-ablation run fair comparisons and measure each
   component's marginal value; exec-iteration tunes and re-runs; research-engineer keeps runs
   reproducible (pinned env, fixed seeds).
4. **Verification** — verify-rigor, verify-methodology, verify-evidence, verify-domain
   **reproduce every headline number from the code** and try to break the logic. Nothing is
   "code-verified" until a board reproduced it.

Keep the findings ledger current after every cycle; tag each result with its evidence tier.

## Execution build contract (enforced before any build is called done)
Any Execution agent that edits repo files or code must, before reporting done:
1. **Chunk large edits** — for files >40 lines, edit in small pieces and re-read each changed region to
   confirm it is complete and parses. A truncated single-shot rewrite that ships a SyntaxError is a
   contract violation, not a minor slip.
2. **Verify-or-flag** — run the repo checks (`tools/consistency_check.py`, `tools/doctor.py --grade`,
   `pytest -q`) and paste the real output as **Code-verified**. An agent with no shell must label results
   **Asserted** and hand verification to the Orchestrator — never imply a green build it did not run.
The Orchestrator re-runs these checks at close-out (Integrity-Officer) and does **not** declare the step
done until they are green.

## Gate
Stop at gate card **G4 — "accept results?"**: decision · options · risks · recommendation ·
APPROVE / REVISE / REJECT. Move to reporting/write-up only after approval.
