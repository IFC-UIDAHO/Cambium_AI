```
  ┌─ ⛩  CAMBIUM GATE  ·  {GATE_ID}
  │  {one-line gate question}
  │  Project: {slug} · Phase: {phase} · Date: {YYYY-MM-DD} · Prepared by: Orchestration
  └──────────────────────────────────────────────────────────────────
```
> The fixed one-page gate card every gate uses. Fill every section, keep it to one page, never reorder or
> drop sections — **every gate looks and reads identically**, whichever council prepared it. In Cowork the
> run-board dashboard also shows the active-gate banner (decision · recommendation · APPROVE/REVISE/REJECT)
> whenever `state.json` carries a `gate` block; this card and that banner must agree.

## 1. Decision needed
{One sentence, phrased as the exact yes/no or either-or question the human must answer.}

## 2. Where we are
{1–2 lines: what just finished, and what approving this gate unlocks next.} *(Mirror the live board: which
phases are ✓ done, which council is ▶ now, what is ○ waiting.)*

## 3. Options
| # | Option | Upside | Downside / cost | Risk |
|---|--------|--------|-----------------|------|
| A | {recommended option} | … | … | P0/P1/P2 |
| B | {alternative} | … | … | P0/P1/P2 |
| C | {do nothing / defer} | … | … | … |

## 4. Risks & open items
- **P0 (blockers):** {none — or list}
- **P1 (weakens):** {…}
- **Open / unknown:** {…}

## 5. Evidence & confidence
- Strongest evidence: {claim} — tier: {Proved | Code-verified | Asserted}
- Which agents produced it: {Council · Role, …} *(name them — the Director should know who found what)*
- Confidence in recommendation: {0–100%} — {one-line why}
- Reject-probability if we proceed: {target ≤ 15%}

## 6. Recommendation
**{Option A}** — {one line: why it is best given the evidence and risk}.

## 7. Your decision   *(Cambium will not proceed until you answer)*
Reply with one of:
- ✅ **APPROVE** — proceed with the recommendation. (Or pick another: "approve B".)
- ✏️ **REVISE** — {say what to change}; I will re-present this same one-pager.
- ⛔ **REJECT / HOLD** — stop here.

## 8. Director contribution   *(required — the decision is not recorded until this is answered)*
This is the half only you can do. Approval is not a signature — it is your thinking, on the record. A bare
"APPROVE" does not advance the run.

- **Your hypothesis / interpretation** — what do *you* think this result means, or expect next?
  *(≥ 40 words, in your own words — not pasted from the AI summary above.)*
- **Your reasoning** — why do you believe that; what evidence or principle supports it? *(≥ 40 words.)*
- **Your choice + justification** — which option (A / B / C) do you choose, and why? *(selection + a sentence.)*
- **Socratic check** — answer the one phase-specific question the Orchestrator poses here:
  *"{auto-generated question probing one assumption in your answer above}"* — a blank answer blocks ADVANCE.

These entries are appended — timestamped and immutable — to the **Contribution Ledger**
(`governance/CONTRIBUTION_LEDGER.csv`) alongside the gate record, with a copy-from-AI similarity flag.
`tools/learning_gate.py` verifies them before the gate can open. *(Per PHILOSOPHY.md §5 — this is what makes
the gate evidence of thinking, not just presence.)*

---

*On approval the Orchestrator records it in `governance/GATES.md` (gate, approver, date), then runs the
Support close-out before declaring the step done. See PRESENTATION.md (Act III–IV).*
