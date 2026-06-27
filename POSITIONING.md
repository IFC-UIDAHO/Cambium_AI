# Cambium vs. the Field's Top 10 Concerns — verified positioning

These ten concerns are the emerging consensus across research institutions and publishers (Elsevier, Aalto,
Illinois GenAI, and peers) about AI in research. This scorecard was produced **the Cambium way** — four
council agents graded Cambium independently against the ten (Scouts·Landscape for the competitive read,
Verification·Domain for institutional realism, Support·Integrity-Officer for overclaim, Governance·Research-
Conduct for the ethics subset), every verdict traced to a file in the repo, then approved at a human gate.

Grades: **Leads** · **Partial** · **Gap**. **Tally (post-repair, 2026-06-27): 3 Leads · 6 Partial · 1 Gap** —
the scorecard below is updated to reflect the repairs shipped in CHANGELOG 1.00.21 (the bias module moved #5
from Gap to Partial; #2/#4/#6/#9 were strengthened). The original council grading was 3 Leads · 5 Partial · 2 Gaps.

## Scorecard

| # | Concern | Grade | Landscape | Why — and the honest limit (file-grounded) |
|---|---------|:----:|-----------|---------------------------------------------|
| 1 | **AI assists, not authors** | **Leads** | crowded (policy), differentiated (mechanism) | AI Use Statement (AI not an author), Director-only authority at G3/G6, separation of duties, no AI external send. Constructional, not advisory. Policies elsewhere are prose; Cambium operationalizes them. |
| 2 | **Don't erase educational value** | **Partial** | **white space — differentiated** | The Learning Gate (`learning_gate.py` + GATE_SUMMARY §8 + Director Brief) is real and tested — almost no peer treats *learning* as a design goal. **Now:** the PRESENTATION Act III contract MANDATES `gate.py --require-contribution` on **every** decision gate (a bare APPROVE / incomplete contribution is blocked). Ceiling stays Partial: it is an Orchestrator-followed contract, not yet a hard runtime lock. |
| 3 | **Every AI contribution visible** | **Leads** | crowded (disclosure), differentiated (depth) | Live named-agent run board (`run_trace.py`) + provenance manifest (rerun + hash) + immutable decision log — machine-verifiable traceability beyond a disclosure sentence. Best-in-class as an *integration* claim, not a SOTA claim. |
| 4 | **Outputs rest on trusted content** | **Partial** | somewhat crowded (Elicit, Consensus) | Grounded retrieval (OpenAlex + Crossref, `paper_search.py`), citation-resolution gate, evidence-tier contract, boards that re-run code. **Now fixed:** `citation_support="unsupported"` is a **release blocker** (`validate.py`, ADR-036). Remaining limit: automated support-judgment still needs the human Stage-2 panel. |
| 5 | **Bias needs explicit mitigation** | **Partial** *(was Gap)* | white space (no one ships tooling) | **Now shipped:** `templates/BIAS_MITIGATION_CHECKLIST.md` (NIST AI RMF MAP/MEASURE/MANAGE) + a `bias_check` ledger column surfaced by `validate.py`, required before G4/G5. Ceiling is Partial: the checklist is enforced as an advisory + gate obligation, not an automated fairness analyzer. |
| 6 | **Strong data governance** | **Partial** | white space at the implementation level | Data-steward, DATA_MANAGEMENT_PLAN, FERPA/IRB/CARE/dual-use checks, and it runs in *your own account* (no third-party cloud). **Limit:** checklist + self-hosting, **not** a secure-data platform — no RBAC/encryption/access-logging. **Now added:** `governance/REGULATED_DATA.md` — a default-deny intake control enforced at the gate (a `data_class=regulated` finding without an approved pathway blocks). Still not a secure enclave; that's the multi-institution build. |
| 7 | **Authorship & responsibility clear** | **Leads** | crowded (frameworks), differentiated (enforced) | Every consequential decision carries a named human signature in `GATES.md`; author ≠ sole approver; AI cannot self-certify. Minor caveat: records are markdown, not cryptographically signed. |
| 8 | **Preserve pace, don't collapse it** | **Partial** | **white space — differentiated** | Cambium is one of the *only* systems that names "pace as a feature" and resists speed-collapse by design. **Limit:** the deliberation window (no all-gates-in-one-day) is philosophy, not enforced tooling yet. |
| 9 | **Collaboration scales across institutions** | **Gap** | behind (Lifebit et al.) | Single-account file + git today; no federated identity, shared RBAC, or multi-institution data-use workflow. The clearest **adoption blocker for consortium grants**. **Now (Stage 1):** named institution-scoped approvers are enforced at the gate — `gate.py --required-approver` blocks a gate unless the *named* Co-PI approves (`templates/MULTI_PI_ROLES.yml`); plus the `ARCHITECTURE_MULTI_INSTITUTION.md` staged spec. Still a Gap — roles work on shared git, but shared *infrastructure* (server/SSO/RBAC) is unbuilt. |
| 10 | **Value measurable in real terms** | **Partial** | white space (rivals ship no metrics) | Cambium *measures honestly*: per-agent cost/latency telemetry, a pre-registered enforcement A/B it actually ran (reporting a **null**, no spin), a self-grading `doctor`. **Limit:** no demonstrated real-project outcome gains (time-to-award, quality, training). Honest measurement, unproven outcomes. |

## The wedge — where Cambium is genuinely differentiated

The strengths cluster on the **human-judgment and process** concerns (1, 3, 7) and the **white-space** ones
the autonomous "AI scientist" tools ignore by design (2 learning, 8 pace, 10 measurement). The single
deepest moat the Landscape scout identified is **governed pace + measurable value (#8 + #10), reinforced by
the Learning Gate (#2)**: every serious competitor races to *collapse* research time; Cambium is the only
system in view that architecturally *resists* that collapse **and** ran a pre-registered experiment to
measure the trade-off. That combination is uncrowded, hard to copy quickly, and maps onto exactly what a
program officer or IRB checks before approving an AI-augmented workflow.

## The hardest blocker — name it plainly

**Cross-institution collaboration (#9).** Cambium is an institution-in-a-box per user; consortium grants
need shared infrastructure that does not exist yet. This is the one concern where well-funded platforms
already outclass it, and the most common reason a multi-PI center couldn't adopt it today.

## Three honesty caveats that must never be dropped (Integrity Officer)

Any pitch deck, brief, or condensed version of this scorecard **must** carry these — dropping them would be
the exact overclaim Cambium exists to prevent:

1. **The Learning Gate fires by contract, not by a hard lock** — Act III now mandates `gate.py
   --require-contribution` on every decision gate, but it is an Orchestrator-followed contract, not a runtime
   interlock that is impossible to bypass. So #2 is Partial, never Leads.
2. **The enforcement thesis is Open, not proven** — the A/B pilot found *no measurable effect* on Opus
   (diff +0.08, 95% CI [−0.12, +0.28], p=0.78). "Governance by construction" is an aim, not a finding.
3. **Citation-support is advisory, not blocking** — trusted-content handling is not a hard gate.

## The roadmap these grades imply (six repairs to reach "certified platform")

Status after CHANGELOG 1.00.21: (1) Learning Gate now enforced at the gate via `gate.py --require-contribution` — ✅ *partial* (Orchestrator auto-fire on every gate is the last step); (2) `citation_support` blocking — ✅ **done**; (3) NIST AI RMF **bias checklist** — ✅ **done**; (4) **regulated-data** default-deny control — ✅ **done** (procedural; enclave infra remains); (5) **AI_MODEL** enforced in CI — ✅ **done**; (6) **v1 human-judged** enforcement study — ⏳ open (needs raters + budget); plus the cross-institution infrastructure track (#9) — ⏳ spec'd, not built.

## Bottom line

Cambium is **strongest precisely where the field's concern is most human and least commoditized** — keeping
the researcher the author, the process educational, the contributions visible, accountability clear — and it
is honest about the **infrastructure and ML-safety** concerns (bias, shared platforms) where it lags. The
credible position is not "best at all ten." It is: **"Cambium is the governance-and-judgment layer for
research AI — the part that keeps the human the scientist — adopt it today as a structured pilot tool, not
yet a certified institutional platform, and here are the six repairs that close the gap."** That honesty is
itself the brand, and against concerns #1–#3 and #7 it is a strong, defensible one.

---

*Verified the Cambium way · Scouts·Landscape · Verification·Domain · Support·Integrity-Officer ·
Governance·Research-Conduct · approved at gate G-positioning (2026-06-27). Verdicts are Asserted
(sourced to repo mechanisms + a competitive scan), not experimentally proven.*
