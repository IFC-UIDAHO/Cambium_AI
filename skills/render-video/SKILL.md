---
name: render-video
description: Produce a video deliverable — video abstract, grant-pitch video, results explainer, or teaser — by invoking a separately-installed OpenMontage as an external subprocess. Use when the user says "make a video", "video abstract", "render explainer", "grant video", "video pitch", "results explainer", or "make a teaser". Owned by the Reporting council; consumed by Outreach. Requires OpenMontage installed separately (see PROVISION.md). No video renders without human approval at G5/G6.
---

# render-video — evidence-bound video production via OpenMontage (subprocess)

This skill lets Cambium produce a video deliverable by shelling out to a
**separately-installed, AGPLv3-licensed OpenMontage** process. Cambium itself
remains MIT-licensed; the license boundary is the OS process boundary.

---

## 1. Ownership and governance

| Property | Value |
|---|---|
| **Owning council** | Reporting (reporting-officer, deck-builder, figures) |
| **Consuming council** | Outreach (outreach, record-keeper) |
| **Creative-approval gates** | **G5** (release — internal) and **G6** (publish / external) |
| **Evidence gate** | Claims in the video must be Proved or Code-verified in the findings ledger |

---

## 2. License boundary — non-negotiable

OpenMontage (https://github.com/calesthio/OpenMontage) is **AGPLv3**.
Cambium is **MIT**.

**The boundary is the process boundary:**

- Cambium ONLY calls OpenMontage as an external subprocess (CLI) via `OPENMONTAGE_HOME`.
- No OpenMontage source code, skill text, prompts, or vendored files may be copied,
  pasted, forked, or transcribed into this repository.
- Hosting OpenMontage as a network-accessible service triggers AGPL §13 on the
  operator — this must be disclosed to any team running it as a server. Running it
  locally on the same machine that invoked it does not.
- References to OpenMontage in this skill use only its public command names and
  file conventions from its published README.

---

## 3. Inputs are evidence-bound

The video script and on-screen data may show **only** facts and numbers that carry
a **Proved** or **Code-verified** tier in the findings ledger. Pass the ledger IDs
(`source_ledger_ids`) in the `VideoDeliverableRequest`.

- Asserted or Open findings must NOT appear as on-screen claims.
- No fabricated statistics, illustrative numbers, or paraphrased results that change
  the meaning.
- All source data is cross-referenced in `governance/provenance.json` before render.

---

## 4. Outputs fold back into Cambium governance

After every render, capture into Cambium:

1. **`governance/provenance.json`** — append an entry with:
   - providers/models used by OpenMontage (from its decision log)
   - actual cost vs budget cap
   - `decision_log_ref` (path or URL to OpenMontage's own log file)
2. **AI Use Statement** (`AI_USE_STATEMENT.md`) — disclose:
   - which AI providers and which models were used for narration, imagery, music
   - what each was used for (voice synthesis, B-roll selection, colour grading, etc.)
   - that a human verified the output before G5/G6 approval
3. **Asset disclosures** (`ai_assets_disclosed`) — every AI-generated or
   AI-selected asset listed explicitly (no silent AI imagery).
4. **Stock / archive licenses** — verify that every third-party clip, image, or
   audio track used from Pexels, Archive.org, NASA, or Wikimedia carries a license
   compatible with the intended distribution platform; record the license for each.
5. **Budget cap** — `cost_actual_usd` must not exceed `budget_cap_usd`; if it
   would, STOP and bring back to the Director before rendering.

---

## 5. Consent and safety guardrails

- No non-consensual synthetic likeness or voice. If a real person's voice or face is
  synthesised, obtain and document explicit written consent before rendering.
- Honor each AI provider's Terms of Service; flag any ToS incompatibility to the
  Director before use.
- Do not use `real_footage_only=false` for grant submissions to funders that prohibit
  AI-generated imagery without explicit disclosure; check funder rules first.

---

## 6. Flow

```
Reporting drafts VideoDeliverableRequest
  ↓  (validate source_ledger_ids — must be Proved/Code-verified)
  ↓
Human approval — Gate G5 (internal release) or G6 (external publish)
  ↓  APPROVE → proceed  |  REVISE → rework  |  REJECT → stop
  ↓
Skill shells out:
  $OPENMONTAGE_HOME/pipeline_defs/ <profile> render \
      --request <request.json> \
      --output  <output_path>
  ↓
OpenMontage runs in its own process (AGPLv3 boundary preserved)
  ↓
Skill captures VideoResult → provenance.json + AI Use Statement
  ↓
Human reviews rendered output — G5 (release) or G6 (publish)
```

---

## 7. Schema reference

Input/output contracts: `skills/render-video/video_contract.schema.json`
Provisioning: `skills/render-video/PROVISION.md`

---

## 8. Self-review checklist (before returning VideoResult)

- [ ] All `source_ledger_ids` resolve to Proved or Code-verified findings.
- [ ] `cost_actual_usd <= budget_cap_usd`.
- [ ] Every AI-generated asset is listed in `ai_assets_disclosed`.
- [ ] Stock footage licenses verified and recorded.
- [ ] No non-consensual synthetic likeness or voice.
- [ ] `decision_log_ref` written to `governance/provenance.json`.
- [ ] AI Use Statement updated.
- [ ] `self_review_passed: true` only when ALL checks pass.
