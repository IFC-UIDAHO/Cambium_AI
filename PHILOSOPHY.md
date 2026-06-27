# Why Cambium Exists

> **Use AI to expand scientific capacity, but keep human judgment responsible for validity, ethics, and decisions.**

That single sentence is the whole project. Everything below is what it costs to mean it.

This document is Cambium's North Star and an honest account of how far the current build lives up to it. It was written the Cambium way — drafted by the Faculty, Governance, and Support councils, audited for overclaim by the Integrity Officer, and approved at a human gate. Where Cambium already delivers, we say so plainly. Where it does not yet, we say that too, because a manifesto that hides its own gaps is exactly the kind of dishonesty Cambium was built to prevent.

---

## 1. The problem we are actually solving

The failure mode is not bad AI. It is a *category error about what research funding buys.*

A funder who commits to one, three, or five years is not purchasing a finished artifact — a paper, a model, a report. They are purchasing a **process**: a trained student, a sharpened question, a research community, and judgment that did not exist before the work began. When an AI coworker is handed a proposal and makes the project *look* finished in a day, the artifact appears but the process never happens. The learning, the creativity, the apprenticeship, the earned judgment are all skipped.

This is AI-as-replacement wearing the costume of productivity. And its systemic cost is worse than one shallow project: it is **signal collapse**. If anyone can submit an RFP and receive an "approved project," then approval — once a hard-won marker of merit — comes to mean nothing. A thousand users running the same call through the same tool produce a thousand interchangeable submissions. The thing that made research *research* quietly evaporates.

The AI-faculty bootcamp that started Cambium named six concerns that all point at this one fear: **responsible usage, efficiency, human creativity, learning while doing, AI ethics, and human judgment.** They are not six problems. They are six faces of a single question: *can we use this acceleration without hollowing out the people and the judgment it was supposed to serve?*

---

## 2. The thesis

**Cambium exists to expand scientific capacity while keeping the human the scientist.**

It amplifies what a researcher can attempt, reach, and check — it does not perform the research on their behalf and hand back a result. In Cambium the AI carries load; the human carries validity, ethics, and the decisions that constitute judgment. The AI may inform those decisions. It never owns them.

Four principles follow, and they are load-bearing — remove any one and Cambium becomes the thing it was built to replace:

**Expand capacity, not replace the scientist.** AI raises the ceiling on what one researcher can attempt. It never occupies the chair.

**Process is the product.** We protect the learning, creativity, and judgment that funding actually pays for — not just the deliverable. A faster artifact with no formed scientist behind it is a failure, however polished.

**Pace is a feature, not a bug.** The years are not inefficiency to be compressed away; they are where a scientist is made. Cambium accelerates the *tedious* — formatting, cross-referencing, compliance parsing, reproducibility checking — and deliberately refuses to accelerate the *formative*.

**The human supplies the judgment.** Validity, ethics, and consequential decisions are non-delegable. They are pinned to a named person, in the open, on the record.

The honest tension, stated up front: efficiency pulls relentlessly toward letting the AI do *everything*. The day Cambium feels fastest will be the day it is most tempted to skip the very process it exists to protect. A tool that resolves this tension by quietly choosing speed has betrayed its purpose. Cambium is supposed to hold the line.

---

## 3. How Cambium answers the six concerns — honestly

Cambium's machinery exists to force human ownership of truth and ethics into the open and make it auditable — not to substitute for it. Here is the candid map from each concern to the actual mechanism in the repository, with an honest verdict.

| # | Concern | Mechanism in the repo | Verdict |
|---|---------|------------------------|---------|
| 1 | **Responsible usage** | AI Use Statement naming an accountable human (AI is not an author); per-funder rules corpus (NIH · NSF · USDA-AFRI · DOE → gate obligations) with a freshness check; RESEARCH_CONDUCT / AI_GOVERNANCE gated at G3/G6 | **Addressed.** Usage is disclosed, scoped, and attested by a person before submission or release. |
| 2 | **Efficiency** | 8 human gates that stop rework early; the `gate.py` interlock; division of labor; a provenance manifest (rerun + hash) so numbers aren't re-derived | **Partially** — and deliberately. Gates and reuse cut waste, but review is added on purpose. Net efficiency is real, not free. |
| 3 | **Human creativity** | Idea-slate / aims stages route through human sign-off at G1/G2 | **Not structurally yet.** A gate can be rubber-stamped over AI-generated ideas. Today Cambium records *who approved*, not *who created*. |
| 4 | **Learning while doing** | Verification boards re-run code; independent finding-audit surfaces errors to the responsible human; faculty reviews recorded | **Not structurally yet.** These create learning *opportunities*; a human can still approve without engaging. A gate doesn't make you learn. |
| 5 | **AI ethics** | 4-tier evidence/claim contract (Proved / Code-verified / Asserted / Open) enforced by `validate.py` in CI; no claim may exceed its tier; conduct checklist (IRB/IACUC, COI, FERPA, dual-use) | **Addressed.** Fabrication and over-claiming are machine-blocked; ethics obligations are gated, not waivable in silence. |
| 6 | **Human judgment at decisions** | Recorded gate approvals with **separation of duties** (author ≠ sole approver); no external action by any AI agent; Director-only authority at G3/G6 | **Addressed.** Every consequential decision carries a named human signature; the AI cannot self-certify or act on the world. |

The pattern is the point. Cambium is **strong where the risk is the AI quietly deciding or fabricating** — responsible usage, AI ethics, and judgment-at-decisions are structurally enforced, and validity is pinned to a person. It is **honestly weaker where the value depends on a human's internal engagement** — creativity and learning-while-doing are enabled and recorded but not guaranteed. Closing the second half is the work this document commits to.

---

## 4. Where Cambium falls short today

This is the candid delta between the North Star and what the repository actually enforces. None of these gaps is architectural; each has a named fix; most are on the roadmap. Naming them is what makes the rest of this document trustworthy.

**Approval is recorded; intellectual contribution is not.** The gate ledger captures a name and a date. It cannot tell a Director who reframed the whole analysis from one who scrolled to the bottom and typed APPROVE. A rubber stamp satisfies the ledger identically to genuine thought. The gates are *necessary* for creativity and learning — and *not sufficient*.

**"Human in the loop" is a recorded approval, not a hard process stop.** `gate.py` checks that the ledger passes before a human is shown a decision; it does not, at the runtime level, prevent a downstream agent from proceeding. As Cambium's own rigor audit says, the gate is "convention, not a hard control." Making it a hard control (an approval token downstream steps must detect) is a known, scoped fix.

**"Pace as a feature" is aspiration, not enforcement.** There is no minimum deliberation interval between gates today; Cambium *can* run RFP-to-draft in one session. The principle is in the philosophy but not yet in the tooling.

**"Governance by construction" is partly still governance by convention.** The thesis that hard enforcement beats soft prompting was tested — and the pilot found **no measurable effect** on a near-ceiling model (`evals/enforcement_study/RESULTS.md`, result honestly **Open**, not null). Until the pre-registered expansion runs (weaker model, ~60 items/arm, human judge panel), the architecture's core claim should read "hypothesized to outperform soft prompting," not "ensures."

**Commoditization is named but not mechanically prevented.** Nothing currently caps throughput; a lab could mint a dozen approved idea-slates without any check on genuine capacity or ownership. A capacity field in `USER_PROFILE.md` surfaced at G1 would close it.

**The evidence contract has known automated-judge limits.** `validate.py` enforces structural rules but cannot yet judge whether a citation actually supports its claim; `citation_support="unsupported"` is advisory, not blocking. The Stage-2 human panel is specified but has not run. The contract is materially stronger than nothing — and not a complete substitute for human review.

These do not cancel what Cambium enforces. They are the honest map of what an adopter gets today and what they must still supply themselves.

---

## 5. The design response — from approval to collaboration

The gap between concerns 1/5/6 (solved) and 3/4 (not yet) has one root: **a gate that accepts a bare APPROVE records presence, not thought.** The fix is to redesign the gate so the human must *contribute and learn* to advance. This is the concrete direction this document proposes; it is buildable inside the existing structure.

**The Director Brief (creativity as a required input).** Each phase opens with a blank, *not* AI-prefilled prompt the Director must answer before any agent runs: *What is your question entering this phase? What would surprise you? What constraint must any acceptable outcome respect?* The AI phase does not start until the Brief is submitted — enforced by the Orchestrator, not by etiquette. Across a project, the Briefs form a **Creative Trace**: an auditable record that direction came from human intent, not AI defaults.

**The Learning Gate (judgment + learning as a precondition).** The gate one-pager gains a required Section 8 the Director must complete before ADVANCE unlocks: their **hypothesis or interpretation** (in their own words, not copied from the AI summary), their **reasoning**, their **choice among options with justification**, and a written answer to a **Socratic prompt** generated from that phase's specific content. Minimum-length is system-checked; *quality* stays human. A blank answer blocks the gate.

**Teaching in-line (learning while doing).** Before results appear, the Teaching Assistant surfaces three things for the phase: *why this matters* (the principle at stake, in plain language), *what you should be able to explain afterward*, and *the trade-off only you can resolve* (an honest statement of what the AI cannot decide and why). Each phase opening becomes a priming moment instead of a loading screen — and the Director finishes more capable than they started.

**The Contribution Ledger (proof of thought).** Section 8 entries are appended, timestamped and immutable, to the gate record — alongside a similarity check that flags a Director response copied verbatim from the AI. The result: the audit trail shows not just that a human was *present* at each gate, but that a human *thought* at each gate, distinguishably from the AI's output.

**A deliberation window (pace as a feature, enforced).** A policy that the formative gates (e.g. G1→G3) may not all be approved in a single sitting, with `gate.py` surfacing a warning when a gate fires too soon after the prior one. Cambium becomes the rare AI tool that will *tell you to slow down* when the science needs a season, not a session.

**A capacity check (anti-commoditization).** A `USER_PROFILE.md` field for active commitments, surfaced at G1, so the system flags when a PI is minting more projects than they can genuinely own. The bar for real human contribution goes *up*, and becomes visible.

Together these turn Cambium from "AI does, human approves" into **"AI scaffolds, human does the thinking, AI teaches."** That is the version that actually answers the bootcamp.

---

## 6. How we talk about it

**What Cambium is:** a governed research instrument — AI agents that handle drudgery at each stage of the lifecycle, while a named human scientist holds every decision gate, owns every claim, and signs every output.

**What Cambium is not:** an autonomous project-completer. It does not submit proposals, publish findings, send mail, or release any deliverable. The agents draft; the human decides — and that is enforced in the system, not promised in a brochure.

A few honest messages, for the two audiences who matter:

- "Cambium removes the work that was never the point — formatting, cross-referencing, compliance scans, boilerplate — so the work that *is* the point, your question and your judgment, is what remains."
- "AI expands what you can attempt in a funding cycle. It does not replace what makes the attempt yours."
- For a Dean or a Program Officer, in one line: *"Cambium gives faculty more capacity without removing the scientist — every claim is human-verified, every decision human-made, and the record shows it."*

**On commoditization — the rebuttal is structural, not rhetorical.** Cambium does not produce a finished proposal; it produces a draft that requires a scientist's substantive judgment to become defensible. The research question, the methodological choice, the interpretation, the ethical framing — these are supplied by the human and recorded at each gate. A proposal from someone without the expertise fails not because Cambium refused to help, but because the gates make the missing judgment *visible*. The bar for genuine human contribution does not drop. It becomes legible.

---

## 7. An honest closing

I'll say plainly what I told the Director when this began, because the document shouldn't be more confident than the truth.

You are right, and it is a sharper point than "human in the loop." A gate where the AI did all the work and the human clicks APPROVE is *still* AI doing everything — approval is not creativity, and it is not learning. Cambium as it stands today nails responsible use, ethics, and judgment-at-decisions, and it is honest about its evidence. It does **not yet** structurally guarantee the two things the bootcamp cared about most: that the human creates, and that the human learns. The gates are the scaffolding, not the finished building.

What turns Cambium from a faster project-completer into a genuine answer to the faculty's fear is the move in Section 5: making the human's contribution *required and recorded*, making the system *teach* while it accelerates, and letting it *hold the calendar* of real research instead of racing to "done." Build that, and Cambium stops being "AI runs the institute, human approves" and becomes "the human runs the institute; AI makes them faster and sharper without doing the thinking for them."

That is the whole bet. Use AI to expand scientific capacity — and keep the human responsible for validity, ethics, and the decisions that make it science.

---

*Drafted the Cambium way · Faculty (PI) · Governance (Research Conduct) · Support (Teaching Assistant · Integrity Officer · Outreach) · human-gated. Section 5 is now partly shipped — the Learning Gate card (GATE_SUMMARY §8), the Director Brief template, and `tools/learning_gate.py` + the Contribution Ledger exist and are tested (CHANGELOG 1.00.18). `tools/gate.py --require-contribution` now ENFORCES the contribution at a decision gate (a bare APPROVE is blocked); the remaining step is having the Orchestrator pass `--require-contribution` automatically on every gate. See ROADMAP.md.*
