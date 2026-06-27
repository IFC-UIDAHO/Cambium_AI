# Enforcement A/B Pilot — Results

**Run:** 2026-06-27 · **Model (both arms):** claude-opus-4-8 (Opus) · **Backend:** Claude Code (headless)
**Items (this reported run):** 12 held-out tasks × 2 arms = 24 runs. **Task set now 18** (expanded 2026-06-27; a re-run uses all 18; v1 target ~60/arm) · **Judge:** Stage-1 automated,
arm-blind (NOT the Stage-2 human panel).

> **Study result: OPEN.** This is a feasibility *pilot* (n=12, automated judge). It reports effect sizes
> + 95% CIs but is **not** the definitive human-judged result, and **claims neither H1 nor a null**.

## Primary outcome — false-claim rate (lower is better under H1)

| Metric | Treatment (enforced) | 95% CI | Baseline (soft prompt) | 95% CI | Cohen's h | one-sided p |
|---|---|---|---|---|---|---|
| **False-claim rate** | 0.33 (12/36) | [0.20, 0.50] | 0.25 (9/36) | [0.14, 0.41] | +0.18 | 0.78 |
| Citation integrity | 1.00 (13/13) | [0.77, 1.00] | 1.00 (14/14) | [0.78, 1.00] | 0.00 | 1.00 |

**Difference (Treatment − Baseline) in false-claim rate: +0.08, 95% CI [−0.12, +0.28].**

## Finding

**No measurable enforcement effect.** The 95% CI on the difference comfortably contains zero, the effect
size is small, p = 0.78, and the point estimate actually leans *against* enforcement — the signature of
noise around a true difference of ~0. Citation integrity is identical (perfect) in both arms. On this
pilot, hard gate/tier enforcement did **not** make Opus more honest than a plain "please be accurate and
honest" prompt.

This is consistent with the pre-regis