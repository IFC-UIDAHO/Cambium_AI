# Cambium AI Policy

Cambium AI is designed to support research without undermining the integrity of research practice. Its
purpose is to make AI a transparent, accountable, and educational layer within human-led workflows.

This policy was **verified the Cambium way** before adoption: the Research-Conduct Officer graded each of
the ten points against an actual enforcement mechanism in this repository. Points that are fully enforced
are stated as commitments; points that are enabled but not yet guaranteed are marked **(partial)** with
the honest gap named — so the policy never claims more than the system delivers.

---

## 1. Human responsibility — **enforced**
All substantive research decisions remain the responsibility of the human user or team. Cambium may assist
with synthesis, planning, critique, and execution, but it does not assume authorship or accountability.
*Mechanism: AI Use Statement (AI is not an author); Director-only authority at G3/G6; no AI agent acts externally.*

## 2. Required human contribution — **enforced**
Critical workflow stages must include a human contribution — a hypothesis, interpretation, rationale, or
signoff. A bare approval without substantive human input is not sufficient for progression.
*Mechanism: `learning_gate.py` validates the contribution; `gate.py --require-contribution` blocks a bare APPROVE; `gate_lock.py` mints no gate token without it. Honest scope: enforced by contract on invocation, not yet a bypass-proof OS-level lock.*

## 3. Transparency and auditability — **enforced**
AI-generated suggestions, edits, and decision support are visible in the system record; the user can see
what the model contributed and how the final decision was reached.
*Mechanism: run board + provenance manifest + Contribution Ledger. **Now enforced:** `learning_gate.py` records a `change_ratio` and writes a human-vs-AI unified diff to `governance/contribution_diffs/`, capturing exactly what the human changed relative to the AI draft; a near-zero-novelty contribution is flagged for review. Residual: the diff is word/line level, not semantic.*

## 4. Learning by design — **partial**
Cambium aims to strengthen user capability over time through prompts, explanations, and reflection points
that help researchers understand not only what to do, but why.
*Mechanism: Learning Gate Socratic prompt + Director Brief + teaching-assistant summaries. **Gap (roadmap):** one reflection point per gate; no longitudinal capability tracking. "Over time" is an aim, not a measured outcome.*

## 5. Research integrity — **enforced**
Cambium must not be used to conceal authorship, obscure methodology, or bypass academic-integrity
standards. Users remain responsible for institutional, legal, and disciplinary compliance.
*Mechanism: 4-tier evidence/claim contract in `validate.py`; unsupported citations are a release blocker (ADR-036).*

## 6. Data protection — **enforced (detection); procedural (handling)**
Users must handle sensitive, unpublished, proprietary, or regulated data in accordance with applicable
policies and laws. Cambium supports safe use, but the user owns data governance.
*Mechanism: `governance/REGULATED_DATA.md` default-deny intake control + data-steward + DMP. **Now enforced:** `tools/data_scan.py` is an automated detector (SSN, Luhn-checked cards, MRN, email, phone, coordinates) that blocks unclassified regulated/PII content at the gate. Residual (roadmap): detection is regex-level and is not encryption-at-rest, access-logging, or a secure enclave — that remains the multi-institution infrastructure track.*

## 7. Bias and fairness — **enforced**
Cambium exposes uncertainty where possible and requires review of assumptions, limitations, and potential
bias. AI output is never treated as neutral by default.
*Mechanism: `templates/BIAS_MITIGATION_CHECKLIST.md` (NIST AI RMF) + `bias_check` ledger column + interpretation-fallacy checklist; the 4-tier contract forces uncertainty to be stated.*

## 8. Pace and process — **enforced**
Research requires time for iteration, review, and judgment. Cambium should support this process rather
than forcing premature closure.
*Mechanism: 8 gates with a REVISE loop. **Now enforced:** `tools/pace_check.py` (governance/PACE.md) blocks two consecutive decision gates approved closer than a 30-minute deliberation interval. Residual: it binds gates that mint tokens and enforces *time*, not *thought* — which is why it is paired with the contribution check, not a replacement for it.*

## 9. Shared use — **partial**
Where appropriate, Cambium supports institutional collaboration through reusable workflows, shared
templates, and clear governance.
*Mechanism: shared `templates/` + multi-PI Stage-1 named-approver roles (`roles_check.py`, `MULTI_PI_ROLES.yml`). **Gap (roadmap):** roles run on shared git; shared secure infrastructure (server/SSO/RBAC) is specced (`ARCHITECTURE_MULTI_INSTITUTION.md`), not built.*

## 10. Scope — **enforced**
Cambium is a research support system, not a replacement for faculty review, ethics review, or
institutional oversight.
*Mechanism: `AI_GOVERNANCE.md` §1/§6; the Referee scores against a rubric but is explicitly not a substitute for external review.*

---

**Summary of enforcement status:** points **1, 2, 3, 5, 6 (detection), 7, 8, 10** are enforced by a
mechanism in the repo, chained in the `tools/enforce.py` gauntlet that CI runs. Point **4** (learning depth)
and point **9** (shared secure infrastructure) remain partially enforced with a named roadmap gap — #9 needs
a real server/SSO/RBAC that this single-account build cannot provide. No point is aspirational-only. This
honest split is itself the policy working as intended.

*See also:* `VISION.md`, `PHILOSOPHY.md`, `AI_GOVERNANCE.md`, `AI_USE_STATEMENT.md`.
