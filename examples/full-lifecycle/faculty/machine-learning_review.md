# Faculty Review — Machine Learning (FICTIONAL DEMO)
*Agent: Faculty-Expert (Machine Learning) | Date: demo | Input: 03_aims.md, statistics_review.md*

## Decision / Verdict
Approved with minor comments. Idea A (gradient-boosted trees) is well-matched to the scope and timeline. No P0 issues found.

## Findings

| id | severity | evidence | claim_tier | fix |
|---|---|---|---|---|
| MLR-01 | P2 | 03_aims.md Aim2: MAPE targets (15%/25%) cited from external literature (Divvy, Capital Bikeshare) with no stated adjustment for campus-system characteristics — smaller fleet, more cyclic academic calendar | Asserted | Add footnote: targets may be revised after EDA in Q1; preliminary targets are anchors, not guarantees |
| MLR-02 | P2 | 03_aims.md Aim2: no mention of hyperparameter search protocol — reproducibility risk | Asserted | Specify CV strategy (time-series CV, 5 folds) and search budget in Aim 2 |
| MLR-03 | P1 | 03_aims.md Aim3: SHAP values will "explain" predictions — SHAP explains the model, not necessarily the underlying causal mechanism; risk of over-claiming to operations staff | Asserted | Scope the language: SHAP explains which features the model weighted, not why demand changed causally |

## Score
8 / 10 — strong technical merit; minor communication risk on SHAP framing.

## Next action
Proposal-Writer to adjust Aim 3 language on SHAP before G3.

## Confidence
0.88 — direct expertise in gradient boosting and SHAP; campus transit domain is adjacent, not primary.
