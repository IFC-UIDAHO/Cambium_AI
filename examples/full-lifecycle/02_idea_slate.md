# 02 Idea Slate — Campus Bike-Share Demand Forecaster (FICTIONAL DEMO)
*Agent: Ideation-Facilitator | Date: demo | Input: 01_rfp_brief.md, G1 approval*

> G1 decision (Director, Dr. Amara Osei-Bonsu, 2025-02-10): **pursue**, contingent on data MOU with
> Transport Office. Co-PI from Computer Science approved.

## Three candidate approaches

### Idea A — Gradient-Boosted Trees + Weather & Calendar Features (fit 9/10)
Train a gradient-boosted model (XGBoost / LightGBM) on historical trip counts joined to weather and
academic-calendar covariates. Use SHAP values for interpretability. Fast to train, well-understood
error modes, strong baselines in the literature.
- Pros: high baseline accuracy, feature importance transparent to ops staff, short iteration cycle.
- Cons: does not capture spatial correlations between stations without engineering.
- Privacy: aggregate counts only — no individual records needed.

### Idea B — Spatial-Temporal Graph Neural Network (fit 6/10)
Model the station network as a graph; learn spatial and temporal dependencies jointly.
- Pros: state-of-the-art accuracy; captures station interdependencies.
- Cons: higher compute; interpretability harder; 18-month timeline is tight for deployment.
- Privacy: same as A.

### Idea C — Classical SARIMA per Station + Ensemble (fit 7/10)
Fit a seasonal ARIMA to each station; ensemble with a small MLP that ingests weather.
- Pros: statistician-readable, well-characterised uncertainty bounds.
- Cons: station-by-station fitting is fragile when stations have sparse history.
- Privacy: same as A.

## Recommendation
**Idea A** — maximises feasibility within the timeline and provides interpretable outputs for the
sponsor's operations audience. Enhance with a spatial lag feature (neighbour trip counts) to partially
capture station correlations without needing a full GNN.

**G2 decision needed: which idea advances?**
