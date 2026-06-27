# Development Playbook — the post-award engine

*The proven build-verify-synthesize-revise loop, run once a project is in Development. Budget is
unlimited; waste is not (`OUTPUT_CONTRACT.md`).*

## Trigger phrases
| Say | Runs |
|---|---|
| `run lab` | Full dev cycle: Scouts+Labs+Execution -> Verification -> Synthesis -> (approve) Revision -> Validation |
| `run lab review-only` | Reports + synthesis, no edits |
| `run verification` | The audit boards re-attack the current work |
| `run scouts` | Refresh prior-art / methods / landscape |
| `apply P0` | Document Office applies approved fixes |
| `run research lab` | Innovation mode: find a stronger contribution |

## Phases
A **Generate & run** (Scouts, Labs, Execution - parallel) ->
B **Verify** (the 3 Opus boards + domain board run the code) ->
C **Synthesize** (Orchestrator -> `synthesis/master_synthesis.md` + ledger + leaderboard;
  conflicts: code-verified wins; priority Theory>Evidence>Literature>Experiments>Writing) ->
D **Revise** (approval-gated: P0 auto, P1 before/after, P2 recommendations; logged in change_log.md) ->
E **Validate** (re-run 07/08/09 + a scout; emit accept/minor/major/reject + reject-probability).

## Stop condition
No unresolved P0 and reject-probability <=15%.

## Why this is the strong configuration
Verification runs code (findings are evidence, not opinion) · one contract + one ledger make many
agents mergeable · specialize -> verify -> synthesize -> (gated) write keeps unverified claims out of
the deliverable · resumable + single-writer + lane discipline means re-runs cost only what changed.

## v2 loops & triggers (deeper research)
| Say | Runs |
|---|---|
| `run tournament` | Idea-Tournament: Elo pairwise ranking + faculty judging + evolve rounds -> ranked slate (before G2) |
| `iterate experiment` | exec-iteration: budget-aware diagnose->tune->re-run with branch/prune tree-search |
| `referee` / `referee for <venue>` | Referee scores the deliverable vs the venue rubric (accept/major/minor/reject) before G3/G6 |
| `run verification debate` | two verify boards argue opposing sides of a contested claim; a third judges |
Novelty gate: `01-scout-prior-art` returns a novelty score + nearest prior art automatically before G2;
a near-duplicate idea is flagged for the Director (PI). Institutional memory: `14-record-keeper` recalls
relevant prior projects before dispatch.

## v3.1 — budget-aware verification
Default to SELF-CONSISTENCY (sample-and-agree) for routine checks — current evidence shows it matches or
beats full multi-agent debate per token. Reserve adversarial DEBATE (`run verification debate`) for
CONTESTED or high-stakes claims. Reserve Opus for the critical path; record tokens/runtime per phase.

## v3.2 triggers (P2)
| Say | Runs |
|---|---|
| `quick scan` | Scouts in fast-triage mode |
| `deep research` | Scouts in exhaustive, verified mode |
| `gen cards` | rebuild agent_cards.json (A2A capability manifest) |
| `cost report` | summarize per-vendor token/cost telemetry for the run |

## Decision records (ADR) + self-grade
- `decision`: record a load-bearing decision in DECISIONS.md (template: templates/DECISION_RECORD.md) — context, decision, alternatives, consequences. Append; never rewrite history.
- `cambium grade` / `python3 tools/doctor.py --grade`: score the institute's setup (roster, governance, tooling, evals, decisions) A–F + flag security risks. Run before a release or handoff.
