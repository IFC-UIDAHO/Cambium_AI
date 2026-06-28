# Verification checks: deterministic vs model-judged

Cambium's trust problem is that AI checking AI is not self-evidently trustworthy. So we tag every
verification check by how much it needs an LLM to be believed.

- **10 of 16** checks are **grounded** (8 deterministic, 2 external-source). They
  need no trust in any model: arithmetic that sums or doesn't, a DOI that resolves or doesn't.

- **6 of 16** are **model-judged**. These are the genuinely hard judgments (is the proof sound,
  is the analysis fair, is the tier appropriate) where a model or a human still forms the call.


We report this split honestly rather than implying everything is mechanically verified.


| Area | Check | Type | Tool |
|---|---|---|---|
| Citations | citation resolves in OpenAlex/Crossref | external-source | `paper_search.py` |
| Citations | DOI resolves at doi.org | external-source | `deterministic_checks.py` |
| Budget | line items sum to the claimed total | deterministic | `deterministic_checks.py` |
| Results | claimed number equals the reproduced one | deterministic | `deterministic_checks.py / provenance.py` |
| Data | PII / regulated-data scan (regex + Luhn) | deterministic | `data_scan.py` |
| Pace | deliberation interval between decisions | deterministic | `pace_check.py` |
| Roles | named approver matches the roster | deterministic | `gate.py / roles_check.py` |
| Learning Gate | a real Director contribution is present | deterministic | `learning_gate.py` |
| Evidence tiers | every claim carries a well-formed tier | deterministic | `validate.py` |
| Evidence tiers | the tier is appropriate to the evidence | model-judged | `validate.py + referee` |
| Bias | bias mitigation checklist completed | deterministic | `validate.py (bias_check)` |
| Bias | the analysis is actually fair | model-judged | `verify-domain / human` |
| Rigor | core logic / proofs hold | model-judged | `verify-rigor` |
| Methodology | inference / design is valid | model-judged | `verify-methodology` |
| Venue | referee score vs venue rubric | model-judged | `referee` |
| Integrity | no overclaim beyond the evidence tier | model-judged | `integrity-officer` |

*Deterministic = pure computation. External-source = checked against a real outside authority (OpenAlex, Crossref, doi.org). Model-judged = a model or human forms the judgment.*

