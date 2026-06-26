# Roadmap — Cambium

> **Scope of this document.** This roadmap describes what is planned, in what order, and why. It does
> not promise timelines or capabilities that do not yet exist. Items marked **Done** are shipped in
> the current repository. Items further out are intentions, not commitments.

---

## Current version: 1.4

**What works today:**
- 45 specialized agents across 11 councils (full charter in [`INSTITUTE.md`](INSTITUTE.md))
- Full pre-award lifecycle: RFP intake, ideation, aims/faculty review, collaborator sourcing, proposal drafting
- Full post-award lifecycle: lab development, verification (code-run), synthesis, reporting, decks
- 8 mandatory human-approval gates with recorded ledger (`governance/GATES.md`)
- Unified 5-field output contract (severity + claim tier) across all agents
- `governance/validate.py` — fails the build on open P0 or un-evidenced claim
- `AI_GOVERNANCE.md` — explicit, enforced governance policy (authorship, IRB, FERPA, dual-use, data sovereignty)
- Smart-Tier model routing (Opus / Sonnet by task)
- GitHub template + Claude plugin install paths
- Interactive org-chart dashboard (`dashboard.html`) and 60-second demo tour (`demo/tour.html`)

---

## Near-term (next release cycle)

These items address known gaps and the highest-value usability improvements.

1. **End-to-end worked example (one real project).** Publish a complete artifact chain — from RFP PDF through gate decisions, findings ledger, and final report — for one real or realistic project. This proves the pre-award/post-award integration is operational, not aspirational. (The DSFAS-AFRI project is the natural candidate.)

2. **Machine-checkable provenance manifest.** Extend `validate.py` to emit a portable, structured manifest (JSON/YAML) linking each `Code-verified` claim to its re-run script + hash, and each `Proved` claim to its checked derivation. This turns "discipline by convention" into "discipline by construction" and makes the evidence contract externally auditable.

3. **Additional domain example configs.** Ship ready-to-use `config.example.yml` files for at least two non-ML fields (e.g. social science survey research, agricultural field trials) to demonstrate field-agnosticism concretely, not just in documentation.

4. **Improved gate UX.** Refine the Orchestrator's gate summaries to a consistent one-page template: decision needed, options, risks, recommendation, and a clear accept/reject prompt. Reduce variance across agents.

5. **CITATION.cff and academic discoverability.** Ship a valid Citation File Format file so the Institute is academically citable. (Done in this sprint — see [`CITATION.cff`](CITATION.cff).)

---

## Mid-term

These require more design work or depend on near-term foundations.

6. **Community "faculty packs."** A standard schema for shareable discipline configs so users can contribute and install Faculty expertise modules (e.g., an epidemiology pack, a qualitative-methods pack) via the plugin marketplace.

7. **Richer collaborator sourcing.** Connect the Collaborator-Scout to structured researcher databases (e.g., ORCID, NSF Award Search) to surface real candidate collaborators with evidence of relevant prior work, not just web search.

8. **Connector skills for common data sources.** Pre-built skills for pulling data from USDA NASS, Census API, PubMed, ArXiv, and similar public repositories — reducing manual data prep before the Lab phase.

9. **Multi-PI / team gate model.** A formal multi-user gate protocol where multiple named humans can hold different approval roles (PI, co-PI, department head), with the ledger recording who approved what at each gate.

10. **Richer provenance in reports.** Automatically embed the provenance manifest into the final report as an appendix — every number traceable to its source run, every claim tier visible in the deliverable itself.

---

## Long-term / aspirational

These are directions, not plans. They depend on how the tool evolves and what the community needs.

11. **Community-contributed projects registry.** A public index of Institute-run projects (with consent) — demonstrating the lifecycle across many fields and providing reference examples for new users.

12. **Tighter IRB integration.** Structured handoff points for IRB submission workflows, with the Institute generating IRB application drafts and flagging protocol compliance issues during the development phase.

13. **Integration with pre-registration platforms.** Support drafting and submitting pre-registration documents (OSF, AsPredicted) during the aims phase, before experiments run — strengthening the evidence contract from the start.

14. **Offline / air-gapped mode.** Configuration paths for running entirely on local models (e.g., Ollama) for organizations with strict data-sovereignty requirements that prevent cloud API use.

---

## What is NOT on the roadmap

To be clear about what this tool is not trying to become:

- **Not a fully autonomous research engine.** The human-in-the-loop gates are a design principle, not a limitation to be removed. The goal is augmentation, not autonomy.
- **Not a substitute for peer review.** The simulated peer-review and adversarial verification inside the Institute are quality tools, not replacements for journal peer review.
- **Not a grant-funder database.** The Institute helps write and review proposals; discovering funding opportunities requires external tools (e.g., Granted AI, Grants.gov, Pivot-RP).
- **Not a wet-lab or physical-world controller.** The Institute operates on documents, code, and data. Physical experiments are run by humans; the Institute helps design, analyze, and report them.

---

*Last updated: 2026-06-25. Roadmap reflects the maintainer's current intentions; priorities may shift based on user feedback and available capacity.*
