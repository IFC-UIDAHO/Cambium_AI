# Sponsored-programs mapping

How Cambium's artifacts line up with common sponsored-programs and funder requirements. This is support for
your existing process, not a replacement for it. Always defer to the funder's current solicitation and your
office's rules; the per-funder rule packs live in `governance/funders/`.

| Funder requirement | Cambium artifact that supports it | Notes |
|---|---|---|
| Data Management and Sharing Plan | `templates/DATA_MANAGEMENT_PLAN.md`, data-steward council | Drafts the plan; you approve it |
| Responsible Conduct of Research | research-conduct officer checks at every gate | Advisory plus gate sign-off |
| Conflict of Interest disclosure | governance COI check; AI-use disclosure required | Disclosure enforced; the determination is yours |
| Budget and budget justification | `cambium-institute:budget` skill; deterministic budget-sums check | Numbers come only from your inputs; arithmetic is checked |
| Biosketches, current and pending | grants-compliance council assembles the required forms | Format and completeness, not the science |
| Facilities, equipment, other resources | grants-compliance council | Drafts from your inputs |
| AI-use disclosure | required by the institution profile and the AI use statement | `docs/governance/AI_USE_STATEMENT.md` |
| Reproducibility and data integrity | pinned env, seeds, claimed-equals-reproduced check | `tools/deterministic_checks.py` |
| Human subjects (IRB) | profile flag requires IRB; research-ethics skill flags it | You hold the IRB determination |
| Export control | profile flag requires review | Flag and checklist, not a legal determination |

## Per-funder rule packs
- NSF: `governance/funders/nsf.yml`
- NIH: `governance/funders/nih.yml`
- USDA-AFRI: `governance/funders/usda-afri.yml`
- DOE: `governance/funders/doe.yml`

These are source-verified and freshness-checked in CI, but a rule pack is a convenience, not authority. The
solicitation and your sponsored-programs office are authoritative.
