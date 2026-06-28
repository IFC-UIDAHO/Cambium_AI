# Cambium AI governance approval packet

A single document an AI-governance, IRB-adjacent, or sponsored-programs committee can read in one meeting
and sign. It maps each standard institutional concern to the Cambium control that addresses it and where to
verify that control in the repository. Where a control is enforced we say so. Where it is enabled but not
yet guaranteed we mark it partial, because overclaiming is the failure Cambium exists to prevent.

## What is being approved
Use of Cambium as human-led research infrastructure, configured by the institution profile at
`governance/institution/PROFILE.example.yml`, run in the institution's own environment.

## Concern to control map

| Institutional concern | The committee's question | Cambium control | Enforced? | Verify at |
|---|---|---|---|---|
| AI authorship and accountability | Is a human accountable for every decision? | Eight signed human gates; a named human signs each in the gates ledger; AI is never an author; author may not be the approver | enforced | `governance/GATES.md`, `tools/gate.py` |
| Human oversight of speed | Can the system rubber-stamp at full speed? | Pace check enforces a deliberation interval; the Learning Gate requires a real human contribution | enforced | `tools/pace_check.py`, `tools/learning_gate.py` |
| Research integrity and overclaiming | Can it assert more than the evidence supports? | Four-tier evidence contract; CI fails the build on a claim past its tier; an integrity audit flags overclaims | enforced (format), model-judged (tier appropriateness) | `governance/validate.py`, `governance/CHECKS.md` |
| Trustworthy verification | Is it just AI grading AI? | 10 of 16 verification checks are grounded with no LLM needed (arithmetic, DOI, citation resolution) | partial, by design | `governance/CHECKS.md`, `tools/deterministic_checks.py` |
| Citations | Can it cite work that does not exist? | A citation that does not resolve in OpenAlex or Crossref is a release blocker | enforced | `tools/paper_search.py` |
| Data governance and privacy | Will sensitive or regulated data leak? | Default-deny intake for regulated data; PII and regulated-data scanner; runs in your own account | enforced (detection); procedural (handling) | `governance/REGULATED_DATA.md`, `tools/data_scan.py` |
| FERPA, IRB, export control | Are subject and export rules respected? | Profile flags require IRB for human subjects, export-control review, and FERPA handling; research-conduct officer checks each gate | partial (checklist and flags) | `governance/institution/PROFILE.example.yml`, research-conduct officer |
| Conflict of interest and disclosure | Is AI use disclosed and COI handled? | AI use disclosure is required; COI checks run in governance | enforced (disclosure) | profile `policy.ai_use_disclosure_required` |
| Bias and fairness | Is bias examined, not ignored? | A NIST AI RMF bias checklist is required before the results gates | partial (required checklist) | `templates/BIAS_MITIGATION_CHECKLIST.md` |
| Reproducibility | Can claimed numbers be reproduced? | Pinned environment, fixed seeds, and a claimed-number-equals-reproduced-number check | enforced (where code runs) | `tools/deterministic_checks.py`, `tools/provenance.py` |
| Named, institution-scoped approval | Can the wrong person approve? | Required-approver gates check the signer against the institution roster | enforced | `templates/MULTI_PI_ROLES.yml`, `tools/gate.py` |
| Cost control | Is spend predictable? | Per-project and monthly budget ceilings in the profile; model routing | partial (ceilings declared; hard interlock on the roadmap) | profile `budget`, `MODEL_ROUTER` |
| Vendor and data residency | Does our data leave our environment? | Runs in the institution's own account; open models can run on the institution's own cluster | enforced (self-hosted path) | profile `allowed_models` |
| Auditability | Is there a tamper-evident record? | Hash-chained audit trail and an immutable decision log | enforced | `tools/audit_log.py`, `governance/GATES.md` |

## Honest limits to read before signing
- Some checks are still model-judged (proof soundness, fairness, tier appropriateness). The split is published in `governance/CHECKS.md`.
- The cost interlock today declares ceilings; a hard runtime halt is on the roadmap.
- Cambium is not a secure-data enclave. It adds default-deny intake and detection, not RBAC or encryption at rest.

## Sign-off

| Role | Name | Decision (approve / approve with conditions / decline) | Conditions | Date |
|---|---|---|---|---|
| AI governance chair |  |  |  |  |
| Sponsored programs |  |  |  |  |
| Research computing |  |  |  |  |
| IRB or data steward |  |  |  |  |

Approved profile on file: `governance/institution/PROFILE.example.yml` (validate with `python3 tools/institution_profile.py <profile>`).
