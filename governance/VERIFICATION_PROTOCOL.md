# Verification protocol — how the Verification council earns "Code-verified"

Cambium's signature claim is that the audit boards don't read and opine — they **re-run your code and
reproduce the numbers**. This protocol makes that concrete and repeatable, so "Code-verified" always means
the same thing: a script actually ran and the headline number came out.

## The tier contract (enforced by `governance/validate.py`)
| Tier | What it means | Bar to claim it |
|------|---------------|-----------------|
| **Proved** | mathematically established | a proof or a closed-form derivation, stated |
| **Code-verified** | a script ran and produced the number | a command/run marker in the evidence (`$`, ```` ``` ````, `python`, `pytest`, `make`, `sha256`, …) |
| **Asserted** | claimed but not yet verified | must be downgraded or closed before release |
| **Open** | acknowledged unknown | stated honestly, not hidden |
No claim may exceed its tier. `validate.py` blocks release on an over-tier or un-evidenced claim.

## The reproduce checklist (run for every headline number)
1. **Pin the environment** — record Python/pkg versions; set seeds; `requirements`/lockfile committed.
2. **Re-run from a clean state** — fresh working dir, not the author's cached run. The *re-run*, not the
   first run, is the evidence.
3. **Match the number** — the reproduced value equals the reported one within a stated tolerance; record the
   exact command + the output hash in the findings ledger (this is what flips a claim to Code-verified).
4. **Leakage audit** — confirm train/test (or fit/eval) separation; no target leakage; the metric covers
   what it claims to cover.
5. **Baseline fairness** — comparisons use the same data/splits/budget; no cherry-picked baseline.
6. **Ablation** — remove each component; if the number doesn't move, say so (don't credit dead weight).
7. **Provenance** — `validate.py` records the model (`AI_MODEL`) in `governance/provenance.json` and warns
   if `AI_MODEL` is unset; `tools/provenance.py` records the rerun hash per Code-verified claim.

## Decision
- All headline numbers reproduce within tolerance, no leakage, fair baselines → **accept** (G4).
- Any number doesn't reproduce, or a leakage/baseline flaw is found → **block**; downgrade the claim to
  Asserted/Open and route back. The verdict is **evidence-tiered**, never a rubber stamp.

## Honest ceilings (stated, per Cambium's own contract)
- Reproduction is within a stated tolerance + the available environment; it is not a formal proof.
- The audit catches what it checks; novel failure modes need new checks (add them when found).
- Pairs with: `verify-rigor`, `verify-methodology`, `verify-evidence`, `verify-domain` agents;
  `tools/finding_audit.py`; the `reproducibility` skill.
