# 03 Specific Aims — Campus Bike-Share Demand Forecaster (FICTIONAL DEMO)
*Agent: PI-agent | Date: demo | Input: G2 approval (Idea A), faculty pre-review*

> G2 decision (Director Dr. Amara Osei-Bonsu + Co-PI Dr. Lena Hartmann, 2025-02-17): **Idea A
> selected.** Spatial lag feature included. Faculty reviews requested before proposal draft.

---

## Overview
We propose to build and validate an open-source, station-level bike-share demand forecaster using
gradient-boosted trees with weather, calendar, and spatial-lag covariates. The model will produce
1–24 h ahead trip-count forecasts with SHAP-based explanations for operations staff.

---

## Aim 1 — Data acquisition and feature engineering
**Hypothesis:** A curated dataset joining anonymised aggregate trip counts with weather observations,
academic-calendar events, and same-hour neighbour-station counts will be sufficient to train an
accurate forecaster without individual rider records.

**Success metric:** Clean, reproducible dataset covering ≥ 18 months of history across all stations;
data-sharing MOU executed; IRB protocol confirmed as exempt (aggregate-only, no personal data).

---

## Aim 2 — Model development and validation
**Hypothesis:** A gradient-boosted model trained on Aim 1 features will achieve mean absolute
percentage error (MAPE) ≤ 15 % at 1 h horizon and ≤ 25 % at 24 h horizon on a held-out test set.

**Success metric:** MAPE measured on a temporally separated test set (last 3 months of data).
A persistent-naive baseline (yesterday's same hour) must be beaten by ≥ 10 percentage points at
each horizon.

---

## Aim 3 — Interpretability dashboard and operations handoff
**Hypothesis:** A SHAP-based explanation layer will allow non-technical operations staff to
understand and trust the forecasts sufficiently to act on them without researcher mediation.

**Success metric:** Post-handoff usability evaluation (5-point Likert, n ≥ 8 staff) mean score ≥ 3.5;
open-source code released with a documented reproducibility guide.

---

## Timeline (high level)
| Quarter | Activities |
|---|---|
| Q1 | Data MOU; IRB; data pipeline (Aim 1) |
| Q2–Q3 | Model development, ablation, validation (Aim 2) |
| Q4–Q5 | Dashboard; staff evaluation; open-source release (Aim 3) |
| Q6 | Final report; reproducibility audit |

## [ASSUMPTION] Data access
The Transport Office has indicated informal willingness to share anonymised aggregate data. A formal
MOU is **not yet signed** at the time of proposal submission.

## [NEEDS-DATA] Baseline MAPE
The 15 % / 25 % MAPE targets are based on published results on comparable systems (Divvy Chicago,
Capital Bikeshare). Actual achievable MAPE depends on local data quality.
