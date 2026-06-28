# Enforcement A/B v1 — Budget

What the powered, human-judged study actually costs to run. Two cost drivers: **model compute** (tiny) and
**human-rater time** (the real cost). Figures are computed in `verify_pipeline.py`-adjacent arithmetic; the
only number not fixed by the design is the **rater hourly rate**, which the Director sets (we do not invent a
wage). Model price is the published Opus 4.8 API rate, cited below.

## Inputs (stated, not invented)
- **Model:** Claude Opus 4.8 — **$5 / million input tokens, $25 / million output tokens** (standard tier;
  batch processing is 50% cheaper). Source cited at the bottom.
- **Per-run tokens (estimate):** ~1,300 input (system prompt + task + materials) and ~900 output
  (`run_arm.py` caps output at 1,200). Both arms run every task → `runs = tasks × 2`.
- **Rater effort:** 2 arm-blind raters score every output (~4 min/output), a 5-item calibration round
  (~1 hr each), and a 3rd-rater adjudication pass on the ~12% disputed items.
- **Rater rate `R`:** Director-set. Worked examples below use $25/hr (RA/grad) and $50/hr (professional annotator).

## Cost by target sample size

| Target (per arm) | Detects (baseline 0.30 →) | Model runs | Model $ (std) | Model $ (batch) | Rater hours | Cost @ $25/hr | Cost @ $50/hr |
|---|---|---|---|---|---|---|---|
| **102** (shipped task set) | 0.15 (50% rel.), 80% power | 204 | $5.92 | $2.96 | ~30.8 | **~$771** | **~$1,542** |
| 156 | 0.18 (40% rel.) | 312 | $9.05 | $4.52 | ~46.1 | ~$1,152 | ~$2,305 |
| 231 | 0.20 (33% rel.) | 462 | $13.40 | $6.70 | ~67.3 | ~$1,682 | ~$3,365 |

(Sample sizes are the pre-registered power table in `V1_DESIGN.md`, independently re-derived.)

## The honest headline
**Model compute is a rounding error — about $3–$13.** Even a 3-seed stability variant at n=102 is ~$18.
The entire real cost of this study is **~31 human-rater hours** at the shipped n=102, i.e. **≈ $0.8k–$1.5k**
depending on the rate you pay raters. Scaling to the most stringent powered design (231/arm) is still only
~67 rater-hours (≈ $1.7k–$3.4k). There is **no compute barrier** to running this — the gate is recruiting
two careful, arm-blind humans and a tie-breaker, plus the ~1–2 weeks of calendar time to schedule them.

## What the money does NOT buy
- It does not buy a *result*. A null is a real, fundable outcome and we report it as such.
- It does not remove the human judgement — the panel *is* the instrument; the model spend just produces the
  outputs they read.

## Provisioning checklist (to actually spend this)
1. Run `run_arm.py --arm both` (your `claude` login or an API key) → `runs/` populated. (~$3–$13 + an hour.)
2. `blind.py` → `panel/rater_packet.json` (give to raters) + sealed `panel/blind_manifest.json` (you keep).
3. Recruit 2 arm-blind raters + 1 adjudicator; 5-item calibration round first.
4. Each rater scores in `rater_ui.html`, exports `ratings_<id>.json`.
5. `analyze_stage2.py --ratings panel/ratings_*.json` → `RESULTS_V1.md`. Pre-commit n + seed; no peeking.

---
*Pricing source (present-day, web-verified June 2026):*
[Claude Platform — Pricing](https://platform.claude.com/docs/en/about-claude/pricing) ·
[Claude Opus 4.8 API Pricing 2026 — pricepertoken](https://pricepertoken.com/pricing-page/model/anthropic-claude-opus-4.8).
Rater rates are illustrative assumptions the Director sets, not quoted prices.
