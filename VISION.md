# Cambium — Project Vision

> **Use AI to expand scientific capacity, but keep human judgment responsible for validity, ethics, and decisions.**

This document is Cambium's canonical statement of purpose. It was adopted from an external reviewer's
read of the project and then **fact-checked the Cambium way** — the Integrity Officer and the Research-
Conduct Officer graded every claim against an actual mechanism in this repository (CONFIRMED / PARTIAL /
NOT-YET), approved at a human gate (G-vision, see `governance/GATES.md`). Where a claim is fully enforced
we state it plainly; where it is enabled but not yet guaranteed we mark it **(partial)** rather than
overclaim — because overclaiming is the exact failure Cambium exists to prevent.

---

## Project vision

Cambium is **human-led research infrastructure** for teams that want the benefits of AI without
surrendering judgment, accountability, or learning. It accelerates research work while preserving the
human role in interpretation, decision-making, and authorship.

## Why Cambium exists

Research is not only about producing outputs. It is also about forming judgment, building skill, testing
ideas, and developing a community of inquiry. Cambium exists because a system that makes research faster
but removes the learning and reasoning that research is meant to create has failed its deeper purpose.
(The long-form argument — "process is the product," signal collapse, the six bootcamp concerns — is in
`PHILOSOPHY.md`.)

## Design principles — and how far each is actually enforced

| Principle | Status | Mechanism (file) |
|---|:--:|---|
| Human judgment stays central | **Confirmed** | 8 gates + Director-only authority at G3/G6; no AI agent self-certifies or acts externally (`governance/GATES.md`, `ROLES.md`) |
| AI assists, does not replace interpretation or responsibility | **Confirmed** | AI Use Statement (AI is not an author); separation of duties (`AI_USE_STATEMENT.md`) |
| Every major decision requires a human contribution | **Enforced** | The Learning Gate blocks a bare APPROVE and now records what the human changed vs the AI draft (`learning_gate.py` change_ratio + diff); a tamper-evident token (`gate_lock.py`) is required downstream. **Residual:** binds steps that call the lock, not an OS-level sandbox |
| Transparency is mandatory — AI use visible and auditable | **Confirmed** | Live named-agent run board + provenance manifest (rerun + hash) + immutable decision log (`run_trace.py`, `tools/provenance.py`) |
| Learning is part of the workflow | **Partial** | Director Brief + Socratic prompt + Contribution Ledger create learning *moments* (`GATE_SUMMARY.md` §8). **Limit:** a human can still approve without engaging; depth isn't measured |
| Pace matters — support real cadence, not collapse it | **Enforced** | `tools/pace_check.py` (governance/PACE.md) blocks two consecutive decision gates closer than a 30-min deliberation interval. **Residual:** enforces time, not thought — paired with the contribution check |
| The human record stays clear, traceable, accountable | **Enforced** | Named, dated, role-attributed gate ledger (`governance/GATES.md`) **plus** a recorded change_ratio + human-vs-AI diff per contribution (`governance/contribution_diffs/`). **Residual:** records are markdown, not cryptographically signed |

## What Cambium does

Cambium helps teams plan, analyze, critique, and move through research workflows with AI support. It
surfaces options, stress-tests reasoning, and reduces manual overhead while **requiring human input at
key gates**. The result is faster execution with preserved rigor. *(Confirmed: idea tournament, referee,
verification boards that re-run code, bias and interpretation-fallacy checklists.)*

## What Cambium does not do

Cambium does not aim to automate research into completion. It does not replace researchers, faculty
judgment, or academic responsibility. It is designed to strengthen human-led inquiry, not bypass it.
*(Confirmed: no AI agent sends, publishes, or self-approves anything.)*

## Who it is for

Universities, researchers, labs, and industry teams that need AI-assisted research workflows with clear
accountability — especially where trust, reproducibility, and intellectual formation matter as much as
speed.

## Core commitments

- **Preserve human authorship.** *(Confirmed — AI Use Statement.)*
- **Make AI usage transparent.** *(Confirmed — run board + provenance.)*
- **Protect research integrity.** *(Confirmed — 4-tier evidence contract in `validate.py`; unsupported citations block release.)*
- **Support learning through the workflow.** *(Partial — enabled and recorded, not guaranteed.)*
- **Keep decisions auditable.** *(Enforced — recorded, dated, and the human-vs-AI change is diff-tracked; not yet cryptographically signed.)*
- **Treat judgment as a required research output.** *(Partial — a substantive contribution is required at the gate; its depth is not measured.)*

---

*Governing policy:* `AI_POLICY.md` · *Long-form rationale:* `PHILOSOPHY.md` · *Competitive read:* `POSITIONING.md`
*Claim-by-claim verification:* `agent_outputs/integrity-officer.md`, `agent_outputs/research-conduct-officer.md`
