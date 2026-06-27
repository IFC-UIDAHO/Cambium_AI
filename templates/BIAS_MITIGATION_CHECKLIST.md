# Bias-Mitigation Checklist (NIST AI RMF — MAP / MEASURE / MANAGE)

> Closes concern #5 ("bias needs explicit mitigation"). Complete this before G4 (accept results) and G5
> (release) for any analysis that classifies, predicts, scores, or generalizes about people, places, or
> groups. Record the outcome in the findings ledger column `bias_check` (one of: `clean` · `mitigated` ·
> a short flag like `representativeness` / `label` / `proxy` / `measurement`). A flag surfaces as a
> `validate.py` WARNING until a mitigation is recorded. Aligned to NIST AI RMF (AI 100-1) + GenAI Profile.

## MAP — name the bias surface (where could it enter?)
- **Data representativeness:** does the sample cover the population the claim generalizes to? Who/what is
  under- or over-represented? Note the gap.
- **Label / ground-truth bias:** were labels produced by a process that encodes human or historical bias?
- **Proxy / feature bias:** does any feature stand in for a protected or sensitive attribute (zip → race,
  prior arrests → policing intensity)?
- **Measurement bias:** does the instrument measure the same construct equally across subgroups?
- **Aggregation bias:** is one model applied where subgroups need different models (Simpson's risk — see
  INTERPRETATION_FALLACY_CHECKLIST.md)?
- **Deployment / framing bias:** could the AI's own summary framing steer the conclusion?

## MEASURE — quantify it (don't assert "looks fine")
- Report subgroup performance / outcome rates where subgroups are defined and ethical to compute.
- Where a fairness metric applies, state which (demographic parity, equalized odds, calibration-by-group)
  and the value — and say plainly which you chose and why (they trade off; you cannot satisfy all).
- State the uncertainty (small subgroups → wide CIs; say so).

## MANAGE — mitigate and disclose
- The mitigation taken (re-sampling, re-weighting, removing a proxy, a subgroup-aware model, or scoping the
  claim to the population actually covered).
- **Residual risk** stated honestly — what bias remains after mitigation, and who it could affect.
- If human-subjects / social data: the research-conduct-officer and IRB obligations are also in scope.

## Record
`bias_check = clean` (no bias surface), `mitigated` (flagged + handled, residual stated), or a one-word
flag naming the open surface. The Director attests the mitigation at G4/G5; it is not the AI's call.
