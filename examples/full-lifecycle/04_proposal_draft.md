# 04 Proposal Draft — Campus Bike-Share Demand Forecaster (FICTIONAL DEMO)
*Agent: Proposal-Writer | Date: demo | Input: 03_aims.md (revised), faculty reviews, G2 approval*
*Revisions: SR-01 train/test gap added; SR-02 MAE co-metric added; MLR-03 SHAP framing scoped.*

> G3 decision needed (Director only): **finalize and submit this proposal?**

---

## Project title
Open-Source Station-Level Bike-Share Demand Forecasting with Interpretable Machine Learning

## Investigators
- Director / PI: Dr. Amara Osei-Bonsu, Department of Statistics (FICTIONAL)
- Co-PI: Dr. Lena Hartmann, Department of Computer Science (FICTIONAL)
- Project Manager: Ms. Priya Chandrasekaran (FICTIONAL)

## Abstract (150 words)
We will build and validate an open-source demand forecaster for the campus bike-share system, producing
station-level trip-count predictions at 1–24 h horizons. Using gradient-boosted trees with weather,
academic-calendar, and spatial-lag covariates, and SHAP-based feature-importance explanations for
operations staff, we will address the sponsor's priorities: accuracy, interpretability, open code, and
rider privacy. Three specific aims cover (1) data acquisition and feature engineering, (2) model
development and temporally rigorous validation, and (3) an interpretability dashboard with a staff
usability evaluation. All data handling is aggregate-only; no individual rider records are used. Code
and a reproducibility guide will be released publicly on project completion. ENTIRELY FICTIONAL —
this abstract is a demonstration of proposal format only.

---

## Specific Aims (summary — see 03_aims.md for full text)

### Aim 1 — Data acquisition and feature engineering
Deliver a clean, reproducible dataset of anonymised aggregate trip counts joined to weather and
calendar covariates, with a data-sharing MOU executed and IRB exemption confirmed.

### Aim 2 — Model development and validation
Train a gradient-boosted model; evaluate on a temporally separated test set with a minimum 24 h gap
after the last training observation. Primary metrics: MAPE and MAE at 1 h and 24 h horizons. Target:
MAPE <=15 % at 1 h and <=25 % at 24 h, each beating a persistent-naive baseline by >=10 pp. Targets
are literature-informed anchors subject to revision after Q1 exploratory data analysis; any revision
will be disclosed in the interim report.

### Aim 3 — Interpretability dashboard and operations handoff
Deliver a SHAP-based explanation layer that shows which input features the model weighted most heavily
for each forecast (note: SHAP explains the model's weighting, not causal mechanisms). Staff usability
evaluation: mean Likert score >=3.5 (n>=8).

---

## Data management and ethics
- All data: anonymised aggregate trip counts (no individual-level records; no GPS trajectories).
- Data-sharing MOU with Transport Office to be executed before Q1 data access begins.
- IRB protocol: anticipated exempt (aggregate, non-identifiable). Confirmation required in Q1.
- Code released under MIT licence; data released as aggregate summary tables under CC-BY.
- Contingency if MOU is delayed: synthetic dataset generated from published Divvy Chicago counts for
  model development; switch to campus data when available.

## AI use statement
AI-assisted drafting was used for proposal text generation and literature search. All claims were
reviewed and approved by the PI and Co-PI. Authorship and intellectual responsibility remain with
the named investigators. Full AI Use Statement to be co-signed by all investigators at G3.

## Budget overview (entirely fictional — demo only)
| Category | Y1 ($K) | Y2 ($K) | Total ($K) |
|---|---|---|---|
| Personnel (1 postdoc + 0.5 RA) | 72 | 72 | 144 |
| Computing (cloud + HPC) | 8 | 4 | 12 |
| Dissemination | 6 | 6 | 12 |
| Indirect (fictional 10%) | 8.6 | 8.2 | 16.8 |
| **Total** | **94.6** | **90.2** | **184.8** |

(Over ceiling — to be trimmed before submission. Demo only.)

---

## G3 checklist (Director reviews before signing)
- [ ] Faculty reviews addressed (SR-01, SR-02, MLR-01, MLR-02, MLR-03)
- [ ] Budget within ceiling
- [ ] Data MOU status confirmed
- [ ] All co-investigators have signed the AI Use Statement
- [ ] Proposal-Writer sign-off
