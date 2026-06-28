---
name: test-driven-research-code
description: Apply lightweight test-driven development to research code so analysis logic is trustworthy. Write a failing test for each transform or metric before implementing, and guard known-correct values. Use when writing data-cleaning, feature, or metric code whose correctness affects a reported number. Trigger on "test this function", "is the metric right", "regression test", "guard the value". Pairs with reproducibility and statistics. Structure adapted from agent-skills (MIT). See /ATTRIBUTION.md.
---
# Test-driven research code

## When to use
Data transforms, metric and estimator implementations, anything feeding a headline number.

## Core process
1. Write a failing test with a hand-checked expected value before coding the transform.
2. Implement minimally until it passes; keep the test as a regression guard.
3. Add an edge-case test (empty, NaN, single row, off-by-one window).
4. Run the suite in the `make` or CI path so it gates every rerun.

## Anti-rationalization table
| If you're tempted to… | Why it fails | Do this instead |
|---|---|---|
| "the function is simple, it doesn't need a test" | Simple transforms are where silent off-by-one and unit bugs hide | Write one value-checked test anyway |
| "I'll test it after the deadline" | Untested analysis code can move a headline number without anyone noticing | Test before the result is reported |

## Exit criteria
- [ ] Each result-feeding function has at least one value-checked test, run in CI.
- [ ] The statistical correctness of the chosen metric is confirmed with the statistics council.

## Red flags
- A metric implementation with no test. Do not let its output become a reported number.
- A test that asserts the code's own output rather than an independently known value.
