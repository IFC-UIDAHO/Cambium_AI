# Pace policy — the deliberation interval (enforced)

> "Pace is a feature, not a bug." The years a funder pays for are where a scientist is made.
> Cambium accelerates the *tedious* and deliberately refuses to accelerate the *formative*. — PHILOSOPHY.md §3

For a long time this was philosophy with no tooling behind it. It is now an **enforced control**:
`tools/pace_check.py` reads the minted gate tokens and blocks when two consecutive *decision* gates were
approved closer together than the minimum deliberation interval.

## The rule
- **Minimum interval: 30 minutes** between consecutive decision gates (default; override with
  `--min-minutes` or env `CAMBIUM_MIN_GATE_MINUTES`).
- **Exempt** (may fire fast — housekeeping, not consequential judgement): `G0`, `G4`, `G5`.
- **Test/demo tokens** (`G-test*`, `G-demo*`) are local scratch and ignored.
- Re-minting the *same* gate (a revision) is not a violation; only two *distinct* gates count.

## How it is enforced
- Mint-time: `python3 tools/pace_check.py gate --gate G3` blocks the token if the prior decision gate is
  too recent.
- Audit / CI: `python3 tools/pace_check.py --strict` (run by `tools/enforce.py`) fails the run if any
  recorded pair is too close.

## Honest ceiling
This is a real time control over gates that mint tokens. It does **not** force *thought* — a team can wait
30 idle minutes and still rubber-stamp. That is why pace is paired with the Learning Gate (a substantive
contribution is required) and change-tracking (#3). Pace + contribution together are the point; neither
alone is sufficient.
