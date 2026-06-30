# Cambium and AI4RA: how the pieces line up

This maps Cambium to the AI4RA initiative (University of Idaho, NSF GRANTED award 2427549:
"Crossing the Innovation Valley of Death: Democratizing Data and Artificial Intelligence for
Research Administration"). It is written to be honest, not promotional. Sources: ai4ra.uidaho.edu
(About, the Four Pillars, the TaMPER framework) and the NSF award page.

Cambium is not a system of record and not a document extractor. It is the preparation, governance,
evidence, and auditable-disclosure layer that sits between an extractor (such as AI4RA's Vandalizer)
and a system of record (such as iRIS). It augments the research administrator, never replaces them,
which is AI4RA's own Objective 2.

## The three objectives

| AI4RA objective | Where Cambium fits | The value | Honest gap |
|---|---|---|---|
| 1. FAIR open data infrastructure | `fair_descriptor.py` writes a Frictionless data-package catalog of a run's outputs; `okf_export.py` exports an interoperable bundle | A run leaves Findable, Accessible, Interoperable, Reusable outputs without extra work | Cambium describes its own outputs, not an institution's full RA data estate |
| 2. Trustworthy, tested AI tools that augment staff | Human gates (`gate_lock.py`), the evidence contract and `finding_audit.py`, `ai_disclosure.py`, `budget_review.py` | Every step is human-approved, every claim is tiered, and AI use is disclosed | Cambium checks AI output, it does not certify compliance or do extraction |
| 3. Scalable, sustainable community of practice | MIT license, the skills and plugin architecture, machine-readable exports | Other institutions can adopt and extend the pieces openly | Running Cambium today assumes a Claude Code or Cowork seat |

## The Four Pillars

| Pillar | Mechanism in Cambium | Status |
|---|---|---|
| Security | Local-first writes via `cambium_io.data_home`; stdlib-first tools make no cloud calls; model hosting is the operator's choice | Addressed by design |
| Accuracy | Evidence contract (Proved / Code-verified / Asserted / Open) plus `finding_audit.py` flag any claim beyond its tier | Enforced as a post-hoc check |
| Reproducibility | Deterministic stdlib tools, a test suite, pinned optional extras (`requirements-ai4ra.txt`) | Supported |
| Flexibility | `tamper_record.py --format json`, `ai_disclosure.py --format json`, `fair_descriptor.py`, `okf_export.py`, the `rules_handoff` schema | Supported |

## The TaMPER workflow

| TaMPER step | Where Cambium records it |
|---|---|
| Task | The run's task and phase, from `run_state.json`, captured by `tamper_record.py` |
| Model | Recorded if configured; otherwise marked "not recorded". Cambium orchestrates a model, it does not select or host it |
| Prompt | Agent roles and instructions are version-controlled in the repo, so prompts are auditable and repeatable |
| Evaluation | Human gate decisions plus the evidence contract and the independent verification council |
| Reporting | `tamper_record.py` and `ai_disclosure.py` produce the documented, repeatable, auditable record |

## What was built for this alignment

- `tools/tamper_record.py` - a TaMPER record and Four-Pillars self-check for any run (md, json, or W3C PROV).
- `tools/fair_descriptor.py` - a FAIR data-package descriptor of a run's outputs.
- `tools/rules_handoff.py` and `examples/ai4ra/vandalizer_handoff.schema.json` - a validated handoff so an
  extractor's solicitation rules feed `budget_review.py` directly.
- `tools/ai_disclosure.py --format json` - a schema-aligned AI-use disclosure export.

All four adopted libraries (jsonschema, frictionless, prov, pip-tools) are optional. Each tool runs and
produces a useful result without them, and reports which path it used.

## What Cambium deliberately does not claim

It does not extract documents, it does not make compliance determinations, and its records are plain
files, not cryptographically signed. A named human in sponsored programs makes the final call.
