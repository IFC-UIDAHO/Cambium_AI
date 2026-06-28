# Skills Map — which Claude skill each agent wields

*Skills are capabilities; agents are the workers that invoke them. The right way to extend: (1) map
installed skills to agents; (2) install marketplace skills/plugins you approve; (3) forge custom
skills with skill-creator. There is no safe "download all skills from the internet" - running
untrusted code is a security risk.*

| Skill (if installed) | Agents | Purpose |
|---|---|---|
| docx / pdf | document-office, RA, reporting-officer, data-steward | read/produce documents |
| pptx / ckmslides | deck-builder, figures, reporting-officer | decks |
| xlsx | data-steward, RA, reporting-officer, exec-* | tables, trackers |
| deep-research | scouts, RA, librarian, collaborator-scout | multi-source search + verify |
| learn | teaching-assistant | explainers, quizzes |
| doc-coauthoring | document-office, TA | structured drafting |
| internal-comms | office-manager, reporting-officer, partnership-liaison | status, outreach |
| canvas-design / algorithmic-art / theme-factory | figures, outreach | diagrams, figures |
| brand-guidelines / ui-ux-pro-max / web-artifacts-builder | outreach, figures | landing pages, dashboards |
| schedule | office-manager | recurring reports / meetings |
| data (statistical-analysis, create-viz, explore-data, validate-data, build-dashboard) | data-steward, RA, figures, exec-* | stats, charts, QA, result dashboards |
| mcp-builder / skill-creator | orchestrator, RA | build custom tools/skills the lab needs |
| **paper_search** (`tools/paper_search.py`) | scout-prior-art, scout-methods, scout-landscape, librarian | grounded scholarly retrieval — OpenAlex/Crossref, no API key; real titles/DOIs/citations |
| **render-video** *(needs external OpenMontage — AGPLv3, installed separately)* | reporting-officer, deck-builder, outreach, figures | produce video deliverables (video abstract, grant pitch, results explainer) by invoking a separately-installed OpenMontage; see `skills/render-video/` |

Marketplace plugins worth considering: **data** (stats + viz + dashboards), domain-specific research
connectors. Install only what you approve.

## New built-in domain skills (ship with Cambium, v3.12.0)

| Skill | Agents | Purpose |
|---|---|---|
| **mathematics** | lab-theory, lab-methods, faculty-expert (math), verify-rigor, RA | exact symbolic + numeric math (SymPy/SciPy/Z3/Pint) — compute, don't estimate |
| **statistics** | lab-statistics, verify-methodology, faculty-expert (statistics), data-steward | rigorous inference — tests, power, GLM/mixed models, multiplicity, bootstrap, Bayesian |
| **machine-learning** | lab-methods, exec-experiments, research-engineer, verify-evidence | leak-free predictive modeling — pipelines, CV, calibration, SHAP, model cards |

## Curated external add-ons (optional install — web/frontend)

Your installed `ui-ux-pro-max`, `ckmdesign`, and `web-artifacts-builder` already cover most web/UI work.
If you want more frontend depth, these community skills are worth a look (install only what you vet):
- **frontend-design** — production-grade, non-generic UI (React/Vue/Svelte/HTML).
- **frontend-excellence** — React/Next/TypeScript/Tailwind scaffolding, bundle analysis, a11y.

Find them via the marketplaces in DECISIONS.md ADR-017. Cambium does not bundle untrusted external code.

## Built-in domain skills — wave 2 (full council coverage, v3.13.0)

| Skill | Council · agents | Purpose |
|---|---|---|
| **optimization** | Labs · lab-methods | LP/MILP/convex/nonlinear (scipy.optimize, cvxpy, PuLP, OR-Tools); reports optimality status |
| **reproducibility** | Execution · research-engineer; Verification · verify-evidence | pinned env, seeds, Makefile/CI, rerun-and-verify headline numbers |
| **citations** | Support · librarian | DOI/Crossref verify, BibTeX, dedup; never fabricate a reference |
| **data-management** | Support · data-steward | inventory, schema/units, provenance, quality checks, PII/privacy |
| **grant-writing** | Pre-Award · proposal-writer, grants-compliance | Specific Aims, criteria alignment, NSF/NIH/USDA structure |
| **research-ethics** | Governance · research-conduct-officer | IRB/IACUC, COI, FERPA/sovereignty, dual-use; GO/CONDITIONS/STOP |
| **project-management** | Partnerships · program-manager, convener | WBS, milestones, deliverables register, RACI, risk log |
| **scientific-writing** | Orchestration · document-office; Reporting · reporting-officer | IMRaD, one-contribution rule, claims↔evidence tiers |

After wave 2, every one of the 11 councils has at least one dedicated skill.

## On-demand skill provisioning (v3.14.0)

| Skill | Council · agents | Purpose |
|---|---|---|
| **skill-provisioner** | Support · toolsmith; Faculty · faculty-expert | front door for growing skills on demand — detect the domain, offer the few skills that help, deliver instantly via faculty-expert + persist a reusable SKILL.md on approval |

This is why Cambium does **not** pre-ship thousands of domain skills: it provisions exactly what each
user needs, vetted and approved. Existing installs come via toolsmith; new skills via skill-creator.
