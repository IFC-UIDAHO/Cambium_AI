# Annual Report — Campus Bike-Share Demand Forecaster (FICTIONAL DEMO)
*Agent: Reporting-Officer | Date: demo (Month 18) | Approved: G5 (Dr. Osei-Bonsu, 2025-11-20)*
*Cites only findings with claim_tier=Code-verified or Proved and status=resolved in the findings ledger.*

> FICTIONAL DEMONSTRATION. No real data, no real findings, no real sponsor.

---

## Project summary
This project delivered an open-source, station-level demand forecaster for the campus bike-share
system. Three specific aims were completed: (1) data acquisition and feature engineering; (2) model
development and temporally rigorous validation; (3) a SHAP-based interpretability dashboard with
a staff usability evaluation. All code is released publicly under an MIT licence.

---

## Verified results (Code-verified findings only)

### Model accuracy (Aim 2)
The gradient-boosted model was evaluated on a **temporally separated test set with a mandatory 24-hour
gap** after the last training observation, following the correction of a data-leakage issue identified
by the Integrity Officer (ledger F001 -> F001b). On the clean split:

- 1-hour horizon: **MAPE = 13.2 %, MAE = 1.8 trips**
- 24-hour horizon: **MAPE = 22.7 %, MAE = 3.1 trips**

Both horizons beat the persistent-naive baseline (same-hour yesterday) by more than 10 percentage
points (naive MAPE: 28.4 % at 1 h; 41.1 % at 24 h). Both targets (MAPE <=15 % at 1 h; <=25 % at
24 h) were met.

Evidence: `model_metrics_clean.json` (committed 2025-09-10); gap audit `audit_split_log_F001b.txt`.
Claim tier: **Code-verified** (ledger F001b, F004).

### Metric transparency
MAPE was computed on non-zero-count station-hours only (11 zero-count hours excluded). For those
hours, MAE is reported separately. This limitation is disclosed in the validation report (D6, line 47)
and in ledger row F002 (Code-verified, resolved).

### Interpretability dashboard (Aim 3)
Staff usability evaluation (n=10, Likert 1–5): mean = 3.8, SD = 0.9. The pre-specified threshold
(mean >=3.5) was met at the point estimate. The 95 % confidence interval lower bound (3.2) is below
threshold; this limitation is disclosed (ledger F005, Asserted, resolved). Recommendation: expand
evaluation in any follow-on work.

Dashboard tooltip language was corrected to scope SHAP explanations as model-feature-weighting
descriptions, not causal claims (ledger F003, Code-verified, resolved).

---

## Limitations and disclosures
1. **Data leakage (resolved):** An early model evaluation used a contaminated test split. The issue
   was caught by the Integrity Officer, fixed by the engineering team, and independently verified
   before any results were reported. All numbers in this report reflect the clean-split evaluation.
2. **MAPE targets:** Literature-anchored from comparable systems. Campus system characteristics
   differ; targets may not generalise to other institutions without recalibration.
3. **Usability evaluation:** Small sample (n=10); point estimate exceeds threshold; CI is wide.
4. **SHAP causality:** SHAP values indicate feature weights in the model's forecasts; they do not
   establish causal relationships between weather or calendar events and trip demand.

---

## AI use disclosure
AI agents were used for literature search, draft writing, code execution, and findings logging.
All claims in this report are drawn from Code-verified ledger entries. Human gates (G1–G6) were
recorded and signed by named investigators before each major transition. The Director and Co-PI
signed the AI Use Statement before public release.

---

## Provenance
Validate.py was run on the findings ledger before G5 and G6 approvals. Result: no open P0; all
findings resolved or disclosed. Provenance manifest: `governance/provenance.json`.
