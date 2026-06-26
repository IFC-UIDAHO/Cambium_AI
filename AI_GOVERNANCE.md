# AI Governance & Responsible-Use Policy

*For any lab adopting the Cambium. It encodes one stance — **AI augments researchers and
teachers; it does not replace them, and a named human is accountable for every output.** This policy is
written to satisfy mainstream research-integrity, funder, journal, and teaching norms (COPE, ICMJE,
NSF/NIH AI guidance, FERPA, IRB / CARE principles). Adapt the bracketed items to your institution; it is
guidance, not legal advice.*

**Status in the framework:** this policy is *enforced by construction* where possible — the
human-in-the-loop gates, the evidence/claim-tier contract, the Integrity Officer, and the
`governance/validate.py` checker — and *by commitment* elsewhere. See §13 for the enforcement map.

---

## 1. Scope & guiding principle
Applies to all use of the Institute's agents in **research and teaching**. Guiding principle:
**augment, not replace.** The AI proposes, drafts, searches, runs code, and checks; **humans decide,
approve, and take responsibility.** No output is "the AI's" — every output has a named human owner.

## 2. Human-in-the-loop & accountability
- A named **Principal Investigator / instructor (the "President")** is accountable for every deliverable.
- The six lifecycle **gates** are mandatory human approvals. Nothing is **submitted, sent, published,
  released, or graded** without a recorded human approval (`governance/GATES.md`).
- The AI never executes external actions on its own behalf — no sending email, submitting proposals,
  moving money, or contacting people. It **drafts; the human sends.**

## 3. Authorship & AI disclosure
- **AI is not an author** (per ICMJE/COPE): it cannot take responsibility, so it is not credited as an
  author or co-author.
- **Disclose AI use.** Every paper, proposal, thesis, or report produced with the Institute ships an
  **AI Use Statement** (`AI_USE_STATEMENT.md`): which agents/models were used, for what (e.g. drafting,
  literature search, code, figures), and the human verification performed.
- Follow the specific disclosure wording required by your target **journal/funder** (they differ).

## 4. Research integrity
- **No fabrication or falsification.** Numbers come only from real runs/data; the Institute's
  `verify-evidence` board reproduces headline numbers, and **never fabricates a citation** (the Librarian
  verifies every reference; unverifiable ones are flagged, not invented).
- **Claim tiers are binding:** no claim may be stated above its evidence tier (Proved / Code-verified /
  Asserted / Open). The Integrity Officer audits for overclaims before anything ships.
- **Reproducibility:** record the model + version, seeds, and commands (the provenance manifest, §11).

## 5. Human subjects, IRB & data sovereignty
- If the work involves **human subjects**, an **IRB / ethics gate** precedes data work; the AI does not
  begin analysis of human-subjects data without recorded IRB approval [insert your IRB process].
- Respect **Indigenous data sovereignty** (CARE principles) and any tribal/community data agreements;
  the Data Steward flags restricted data and the work pauses for the data owner's consent.
- Obtain and honor **consent** terms; do not repurpose data beyond its consent.

## 6. Teaching use & student-data privacy (FERPA)
- **Student records are protected.** Do not paste personally identifiable student data (names, IDs,
  grades, submissions) into the AI without a lawful basis and institutional approval [FERPA / your LMS
  policy].
- **No autonomous grading or high-stakes decisions.** The Teaching-Assistant may explain, draft
  feedback, or build study materials, but **an instructor reviews and owns** any grade or evaluation.
- **Academic integrity for students:** instructors set and disclose the rules for student AI use;
  the Institute is a teaching aid, not a substitute for student learning or for the instructor's
  judgment.

## 7. Data governance
- Track each dataset's **source, license, provenance, retention, and sensitivity** (the Data Steward's
  inventory). Do not upload data whose license or agreement forbids third-party model processing.
- **De-identify / minimize** PII before any AI processing; the Data Steward runs a PII check.
- Keep restricted, embargoed, or proprietary data out of model prompts unless an approved, compliant
  pathway exists.

## 8. Confidentiality of prompts & content
- Do not paste **confidential, embargoed, proprietary, or sponsor-restricted** material into the AI
  unless your agreement and the model's data-use terms permit it.
- Treat unpublished ideas and unfiled proposals as confidential; the Partnership-Liaison drafts but the
  human controls what is shared externally.

## 9. Bias & fairness
- AI outputs can reflect model bias. **Review for bias** in framing, citations (representation), and
  conclusions; the relevant Faculty discipline weighs in. Seek diverse and primary sources.

## 10. Dual-use & safety
- Do not use the Institute to facilitate harmful or **dual-use** research, weapons, or activities barred
  by **export controls** or your institution. The Faculty/Integrity Officer flags such requests and the
  work stops pending human review.

## 11. Model provenance & reproducibility
- Record, per deliverable, a **provenance manifest**: model name + version, the agents/skills used, key
  prompts or their summaries, data versions, seeds, and the commands run. `governance/validate.py`
  emits a starter manifest from the findings ledger.
- Prefer reproducible runs; store seeds and environment.

## 12. Incident response
- On a discovered **fabrication, leakage, privacy breach, or material error**: stop, record it in the
  ledger, notify the President, correct the record, and — if already shared — issue a correction/
  disclosure to the affected venue. Honesty over reputation.

## 13. Roles & enforcement map
| Clause | Enforced by | How |
|---|---|---|
| HITL gates (§2) | Orchestrator + `governance/GATES.md` | recorded human approval required to proceed |
| No fabrication, claim tiers (§3,4) | Integrity Officer + `validate.py` | flags overclaims & unverified citations |
| Reproduce numbers (§4,11) | Verify-Evidence board | runs the code, emits provenance |
| Citations verified (§3,4) | Librarian | DOI/venue check; unverifiable flagged |
| Data license/PII/sovereignty (§5,7) | Data Steward | inventory + PII + restricted-data flag |
| External sends (§2,8) | (none — human only) | the human sends/submits/publishes |
| Teaching/FERPA (§6) | instructor (human) | review & ownership of any evaluation |

**Adoption note:** drop this file in your repo, fill the bracketed institutional items, and add a link
to it from your README. Pair it with `AI_USE_STATEMENT.md` for every deliverable.

## v3.1 — alignment with external policy (web-verified, mid-2026)
- **Proposals:** do NOT let AI "substantially develop" a proposal where the funder forbids it (NIH NOT-OD-25-132); honor per-PI submission caps; AI-assisted text is the proposer's responsibility (NSF PAPPG 2025).
- **Peer review:** never put confidential proposals/manuscripts into non-approved AI (NSF; publisher policies). Cambium's Referee is an INTERNAL pre-check, not a substitute for confidential external review.
- **Authorship & disclosure:** AI is never an author; disclose AI assistance per venue (see AI_USE_STATEMENT.md; ICMJE-2026 extends disclosure to AI used in data analysis).
- **Risk vocabulary:** NIST AI RMF + GenAI Profile (AI 600-1).
