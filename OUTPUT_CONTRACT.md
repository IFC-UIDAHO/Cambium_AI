# OUTPUT CONTRACT & EFFICIENCY RULES

*Binding on every agent. Many narrow agents produce comparable, mergeable, evidence-anchored output so
the Orchestrator can synthesize without re-reading the whole repo.*

## 1. The five-field report (every agent, every time)
One markdown file in `agent_outputs/<name>.md`, <=1 page:
1. **Decision / Verdict** - one line.
2. **Findings** - each: `id | severity | evidence | claim-tier | fix`.
3. **Score** - the lane's score (0-10 or pass/major/reject).
4. **Next action** - the single most valuable follow-up.
5. **Confidence** - 0-1 + one-line why.
The chat return is a <=150-word summary, never the full report.

## 2. Severity
- **P0** fatal: invalid claim, a claim stated as proved that isn't, a result that flips under a fair
  test, or leakage/fabrication. Blocks release.
- **P1** weakens defensibility. **P2** polish.

## 3. Claim tiers (tag every finding)
**Proved** (checked proof) · **Code-verified** (a script the agent ran - cite command+result) ·
**Asserted** (stated, not shown) · **Open** (acknowledged unresolved).
On conflict, **Code-verified beats Asserted**; the agent who ran the code wins.

## 4. Evidence-or-silence
No finding without `file:line`, a quoted sentence, or a command + output. **Never fabricate a
citation**; flag unverifiable ones. A claim you cannot evidence does not go in the report.

## 5. Efficiency rules
1. **Read the index first** (`findings_ledger.csv`, your prior report, named peer reports) - extend,
   don't re-derive.
2. **Model tiers** (Smart-Tier default): Opus on theory + the 3 audit boards; Sonnet elsewhere;
   inherit for Orchestrator + Document Office.
3. **Single-writer per file.** 4. **Resumable** - if your output is current, return "no change".
5. **Bounded runs** (<=40s; reduce reps and say so). 6. **Lane discipline** - note out-of-lane finds
   as a one-line pointer. 7. **Read-only during review** - only the Document Office writes the
   deliverable, post-approval, from Proved/Code-verified findings.

## 6. The ledger
Every accepted finding -> one row in `agent_outputs/findings_ledger.csv`
(`id,issue,agents,severity,claim_tier,evidence,status,action`). It is the institute's shared memory
and the input to `synthesis/master_synthesis.md` and `leaderboard.md`.

## 7. Governance (enforced)
This contract is checked by `governance/validate.py` (run it before any release): it flags claims above
their tier, un-evidenced findings, and open P0s (a release blocker), and emits `governance/provenance.json`.
Human approvals are recorded in `governance/GATES.md`. Full policy: `AI_GOVERNANCE.md`.
