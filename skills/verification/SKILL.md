---
name: verification
description: Adversarially audit a result, analysis, draft, or claim — reproduce every headline number and try to break the logic — and return an evidence-tiered verdict. Use when the user says "verify this", "check these results", "audit this analysis", "is this claim sound", "reproduce these numbers", "referee this", or wants a rigorous second opinion before trusting or shipping something. Delegates to the Verification council (verify-rigor, verify-methodology, verify-evidence, verify-domain, referee) under the Orchestrator. Read-only on the deliverable; executes code to reproduce. Never rubber-stamps.
---

# Verification — reproduce, don't trust

Thin Cambium-way wrapper. Hand off to the **Orchestrator** and convene the Verification board. The
job is to **falsify**, not to confirm.

## Run it
1. **Verification · verify-evidence** — reproduce every headline number from the code/data. Flag
   leakage, unfair baselines, and anything that won't re-run.
2. **Verification · verify-rigor** — attack the core logic/proofs: counterexamples, hidden
   assumptions, asymptotic/inferential validity.
3. **Verification · verify-methodology** — check the inferential method, uncertainty quantification,
   sampling/design assumptions, and what each estimate actually covers.
4. **Verification · verify-domain** — confirm units, conventions, credible data, and real decision
   utility for the field.
5. **Verification · referee** — score against the target rubric: accept / minor / major / reject
   with the decisive weaknesses.

## Output
An **evidence ledger**: one line per claim with its tier — **proved · code-verified · asserted ·
open** — plus the exact command/output that establishes any "code-verified" claim, and a ranked list
of the weaknesses that matter. Mark overclaims explicitly. Do not finalize anything; report the
verdict and hand back to the Director.
