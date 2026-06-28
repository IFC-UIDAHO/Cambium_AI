# Frequently Asked Questions — Cambium

---

## 1. Does this replace researchers?

No. The Institute is explicitly designed as an **augmentation tool, not a replacement**.

You — the "Director (PI)" — are accountable for every deliverable. The 8 lifecycle gates (G0–G6, plus G3a) are mandatory human approval points: no proposal is submitted, no report released, no claim strengthened beyond its evidence without your recorded approval. The AI proposes, drafts, searches, runs code, and checks; humans decide and take responsibility.

See [`AI_GOVERNANCE.md`](../governance/AI_GOVERNANCE.md) §1–2 and [`INSTITUTE.md`](../concepts/INSTITUTE.md) for the gates.

---

## 2. Is the AI listed as an author?

No. The Institute follows [ICMJE](https://www.icmje.org/recommendations/browse/roles-and-responsibilities/defining-the-role-of-authors-and-contributors.html) and [COPE](https://publicationethics.org/cope-position-statements/ai-author) authorship standards: AI cannot take responsibility for the work, so it is not credited as an author or co-author on any paper, proposal, or report.

Every deliverable produced with the Institute ships an **AI Use Statement** (`AI_USE_STATEMENT.md`) disclosing which agents and models were used, for what purpose, and what human verification was performed. Follow the specific disclosure wording required by your target journal or funder (they differ).

See [`AI_GOVERNANCE.md`](../governance/AI_GOVERNANCE.md) §3 and [`AI_USE_STATEMENT.md`](../governance/AI_USE_STATEMENT.md).

---

## 3. What research fields does this work for?

Any field. The Institute is **field-agnostic by design**: domain expertise lives in a parameterized `faculty-expert` agent that you configure for your discipline (statistics, mathematics, CS, ML, economics, biology, social sciences, agriculture, etc.). New disciplines can be added on demand.

The 46 agents handle the research *process* (intake, proposal, verification, reporting); the Faculty handle *domain content*. Point the Faculty at your field, and the process works.

See [`FACULTY_ROSTER.md`](../concepts/FACULTY_ROSTER.md) and the `faculty/` section of [`INSTITUTE.md`](../concepts/INSTITUTE.md).

---

## 4. Is my data or my unpublished ideas sent anywhere?

This depends entirely on **which model and API you configure**. The Institute runs on Claude (via the Anthropic API or the Claude desktop application). Your prompts and content are subject to Anthropic's data-use terms, not the Institute's.

Practical guidance from [`AI_GOVERNANCE.md`](../governance/AI_GOVERNANCE.md) §7–8:
- Do not paste confidential, embargoed, proprietary, or sponsor-restricted material unless your agreement and the model's data-use terms permit it.
- Treat unpublished ideas and unfiled proposals as confidential; the Partnership Liaison drafts but **the human controls what is shared externally**.
- The Institute never sends email, submits proposals, or contacts anyone on its own. It drafts; you send.

If data sovereignty is a concern, use a private API deployment or consult your institution's IT policy before use.

---

## 5. How is this different from the Sakana AI Scientist?

The [Sakana AI Scientist](https://sakana.ai/ai-scientist/) ([paper](https://arxiv.org/abs/2408.06292)) is an impressive, fully autonomous system that takes an ML idea to a complete LaTeX paper with simulated peer review for about $15. It is designed to run **without human intervention** and is scoped to **machine learning** with PyTorch/GPU.

The Cambium differs in three ways:
1. **Scope**: The Institute covers the entire lifecycle from **RFP reading to grant proposal to post-award science to final reports**. Sakana covers idea-to-paper only.
2. **Human governance**: The Institute has **mandatory human gates at every phase boundary**. Sakana is autonomous by design.
3. **Field**: The Institute works for **any research domain**. Sakana requires ML code templates and GPU infrastructure.

If you need autonomous ML paper production, Sakana is excellent. If you need a governed, field-agnostic research operating system from funding to deliverable, use the Institute.

---

## 6. How is this different from Google's AI Co-Scientist?

[Google DeepMind's AI Co-Scientist](https://deepmind.google/blog/co-scientist-a-multi-agent-ai-partner-to-accelerate-research/) (published in Nature, 2026) is a powerful hypothesis-generation engine: it runs an "idea tournament" across specialized agents to surface and rank novel, literature-grounded hypotheses. It is primarily validated in **biomedicine** and is available as a **cloud service** via Gemini for Science.

The Institute differs:
- Co-Scientist operates at the **front of the funnel** (ideation/hypothesis). It does not draft grant proposals, run or verify experiment code, or produce reports and decks.
- The Institute is a **lifecycle operating system** — it starts where Co-Scientist ends, and extends further into funding, execution, and reporting.
- Co-Scientist is a **managed cloud service**; the Institute is a **self-hosted template** that runs in your Claude project, keeping your data under your control.

---

## 7. Can a whole research team use it?

Yes, with coordination. The Institute is designed for a **single Claude project** with one Director (PI) (the principal investigator) and the agents acting as the team. Multiple people can use it if you:
- Share access to the Claude project (or repository).
- Agree on who approves each gate (the Director role must be a named human).
- Keep the `governance/GATES.md` ledger updated with who approved what.

There is currently no built-in multi-user concurrent session support; the Institute is best suited to a **PI-led workflow** where one person holds the "Director (PI)" role and others contribute via the project files. Team use across concurrent sessions is on the roadmap.

See [`ROLES.md`](../concepts/ROLES.md) and the [`TEAM_QUICKSTART.md`](TEAM_QUICKSTART.md).

---

## 8. What does it cost?

The Institute itself is **free and MIT-licensed**. You pay only for the **Claude API or Claude plan** you already use.

Token costs depend on your project size, the number of agents invoked, and which model tier you configure. The Institute uses "Smart-Tier" model routing (Opus for adversarial reasoning, Sonnet for most tasks) to minimize cost without sacrificing quality where it matters.

There is no SaaS subscription, no per-user fee, and no metered plan. See [`LICENSE`](../../LICENSE).

---

## 9. What is the evidence/claim-tier system and why does it matter?

Every agent output in the Institute carries two mandatory fields:
- **Severity**: P0 (critical — blocks progress), P1 (important), P2 (advisory)
- **Claim tier**: `Proved` / `Code-verified` / `Asserted` / `Open`

These are not decorative labels. The **Verification board** actually runs your code and reproduces headline numbers before any claim can be elevated above `Asserted`. The `governance/validate.py` script **fails the build** if a P0 issue is open or a claim is stated above its evidence tier.

This means honesty is enforced by construction, not just by policy. A claim tagged `Code-verified` must link to a re-run script; a claim tagged `Proved` must link to a checked derivation. If it can't be verified, it stays `Asserted` or `Open`, and that label travels with the deliverable.

See [`OUTPUT_CONTRACT.md`](../governance/OUTPUT_CONTRACT.md) and [`AI_GOVERNANCE.md`](../governance/AI_GOVERNANCE.md) §4.

---

## 10. Does the Institute handle IRB / ethics review for human-subjects research?

The Institute **flags the need** for IRB approval but does not replace the IRB process. If your project involves human subjects, the Orchestrator will pause before any data analysis and require a recorded IRB approval before proceeding (per [`AI_GOVERNANCE.md`](../governance/AI_GOVERNANCE.md) §5).

The Data Steward agent also flags restricted data, data sovereignty obligations (CARE principles for Indigenous data), and consent requirements. The work pauses for human resolution — the Institute does not make ethics decisions autonomously.

---

## 11. Can I use this for teaching, not just research?

Yes, with appropriate precautions. The Institute includes guidance for teaching use in [`AI_GOVERNANCE.md`](../governance/AI_GOVERNANCE.md) §6:
- **Student records are protected** (FERPA): do not paste personally identifiable student data into the AI without institutional approval.
- **No autonomous grading**: the Teaching-Assistant agent may draft feedback or study materials, but an instructor reviews and owns any grade or evaluation.
- Instructors must set and disclose rules for student AI use; the Institute is a teaching aid, not a substitute for student learning.

---

## 12. How do I cite this tool in a paper or proposal?

Use the `CITATION.cff` file at the root of this repository. Most reference managers and GitHub's "Cite this repository" button will parse it automatically.

If your target journal requires a specific format, the key fields are: title = "Cambium", type = software, version = 1.00.0, license = MIT, year = 2026. See [`CITATION.cff`](../../CITATION.cff) for the full citation.

Also ship an [`AI_USE_STATEMENT.md`](../governance/AI_USE_STATEMENT.md) with your deliverable disclosing which agents an