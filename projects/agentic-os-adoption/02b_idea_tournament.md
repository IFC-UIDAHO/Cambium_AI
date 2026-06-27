# 02b — Idea Tournament: Agentic-OS Adoption for Cambium
*Date: 2026-06-26 | Judge panel: scout-prior-art, scout-methods, scout-landscape, faculty-expert, research-conduct-officer*

---

## Pairwise Matchup Log (condensed)

| Match | Winner | Margin | Verdict |
|-------|--------|--------|---------|
| B vs E | B | +12 | B enables A; E is a one-liner inside B's work |
| A vs C | A | +6 | A fills the harder durable-memory gap; C is phase-scoped only |
| A vs B | A | +4 | A is the payoff; B is the enabler — score together |
| C vs D | C | +9 | C is governance-safe; D is medium-effort with lower immediate return |
| D vs E | D | +15 | D has structural value; E is a stub field |
| E vs F | E | +30 | E fills a real state gap; F is redundant by design |
| F vs G | tie | — | Both deferred/rejected for different reasons |
| G vs H | G | +25 | G is at least future-plausible; H is out-of-scope entirely |

---

## Ranked Slate

| Rank | ID | Score | One-line rationale | Decision |
|------|----|-------|--------------------|----------|
| 1 | A | 91 | Fills the single biggest operational gap (durable cross-context memory) with near-zero governance risk; reuses run_state.json/ledger; commodity pattern = low implementation risk | ADOPT |
| 2 | B | 88 | Near-zero code cost; prerequisite for A; context-% line prevents silent compaction loss; already implicit in AUTORUN.md's `--resume` pattern | ADOPT |
| 3 | C | 79 | Bounded per-phase autorun respects all governance gates by definition; addresses the real latency of human-gated iteration without crossing gate boundaries | ADOPT |
| 4 | D | 62 | Task-graph with explicit deps has value for 46-agent concurrency, but medium effort and partial coverage by existing phases.yml; defer to v3.2 | DEFER |
| 5 | E | 55 | loop_position field is a one-line JSON addition; useful but only meaningful after A and C land; include as a sub-task of A/C, not standalone | ADOPT (sub-task) |
| 6 | F | 10 | /seed ideation command explicitly duplicated by Cambium's existing G1→G2 ideation lifecycle | REJECT |
| 7 | G | 8 | Obsidian knowledge-graph interesting in principle; repo too small; no agent infrastructure to feed it; revisit at v4 | DEFER |
| 8 | H | 0 | Hermes/Railway/mobile are out of scope by Cambium's own NOT-ON-ROADMAP declaration | REJECT |

---

## Evolution Round: Top-3 Strengthened

**A (evolved):** Merge E's loop_position field directly into the HANDOFF_{gate}.md schema. The handoff doc becomes the single source of truth: last gate, context %, loop_position, pointer to run_state.json snapshot. Cost stays low; eliminates a separate E implementation pass.

**B (evolved):** Wire the context-% statusline to *proactively draft* a handoff doc at 85 % context — not just surface a number. Human still resumes; the draft removes friction at the gate.

**C (evolved):** Constrain the autonomous loop to emit a mini-ledger entry per iteration (record-keeper pattern), so the bounded loop is auditable without a human watching each cycle. Aligns with AI_GOVERNANCE.md §11 (provenance per deliverable).

---

## Next Action

Director approves A + B + C for v3.2 sprint at G2. D queues for v3.3 planning. E absorbed into A spec. F and H formally closed.

## Confidence: High (panel unanimous on top-3; D deferral is the only close call — pairwise margin vs C was +9)
