# Faculty Review — Statistics (FICTIONAL DEMO)
*Agent: Faculty-Expert (Statistics) | Date: demo | Input: 03_aims.md*

## Decision / Verdict
Conditional approval. Aims are scientifically sound; two concerns must be addressed before proposal is finalised.

## Findings

| id | severity | evidence | claim_tier | fix |
|---|---|---|---|---|
| SR-01 | P1 | 03_aims.md Aim2: test set defined as "last 3 months" with no stated gap from training end — temporal leakage possible if forecasts overlap training window | Asserted | Add explicit gap: test set starts at least 24 h after last training observation |
| SR-02 | P2 | 03_aims.md Aim2: MAPE is undefined when counts are zero (off-peak stations) | Asserted | Add RMSE or MAE as co-primary metric; document zero-count handling |
| SR-03 | P2 | 03_aims.md Aim1: ASSUMPTION block — MOU not yet signed | Asserted | Add contingency plan in proposal (synthetic data fallback) |

## Score
7 / 10 — conditional on SR-01 fix before G3.

## Next action
PI to revise Aim 2 success metric language to include explicit train/test gap and add MAE as co-primary metric.

## Confidence
0.82 — strong expertise in time-series validation; uncertainty on campus-specific data sparsity.
