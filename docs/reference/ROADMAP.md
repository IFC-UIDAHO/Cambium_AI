# Roadmap — Cambium

> **Scope of this document.** This roadmap describes what is planned, in what order, and why. It does
> not promise timelines or capabilities that do not yet exist. Items marked **Done** are shipped in
> the current repository. Items further out are intentions, not commitments.

---

## Current version: 1.00.0

**What works today (shipped in this repo):** 46 agents across 11 councils; full pre-award + post-award
lifecycle; 8 human-approval gates with a recorded ledger; the 4-tier evidence contract enforced by
`governance/validate.py`; `AI_GOVERNANCE.md`; Smart-Tier model routing with `AI_MODEL` enforced in CI;
GitHub template + Claude plugin; the live run board + `dashboard.html`.

---

## Recently shipped (2026-06-27 session - all real, in this repo)

- **Grounded retrieval** - `tools/paper_search.py` (OpenAlex + Crossref) behind every citation check.
- **Per-agent speed/cost telemetry** - `cost_log` (model + tokens + latency per phase).
- **Live gate interlock** - `tools/gate.py`: blocks a gate on an open blocker or a missing Director
  contribution; `--require-contribution` mandated on every decision gate (PRESENTATION Act III).
- **Independent finding-audit** - `tools/finding_audit.py`. **Provenance manifest** - rerun cmd + output hash.
- **Per-funder corpus -> NIH / NSF / USDA-AFRI / DOE**, dated + freshness-checked.
- **Demonstrated post-award worked example** - `examples/e2e-worked-example/` (CI re-runs the ledger).
- **Enforcement A/B pilot completed** - 24 real Opus runs; result honestly **Open** (null: no measurable
  effect vs soft-prompting; diff +0.08, 95% CI [-0.12, +0.28], p=0.78). Reported, not suppressed.
- **PHILOSOPHY.md** (North Star + honest gaps) and **POSITIONING.md** (vs the field's Top-10: 3 Leads / 6 Partial / 1 Gap).
- **Learning Gate** - GATE_SUMMARY 8 + Director Brief + `tools/learning_gate.py` + Contribution Ledger.
- **NIST AI RMF bias module** - `templates/BIAS_MITIGATION_CHECKLIST.md` + `bias_check` column.
- **`citation_support="unsupported"` is a release blocker**; **regulated-data default-deny control**
  (`governance/REGULATED_DATA.md`).
- **Multi-PI Stage-1 roles** - `gate.py --required-approver` + `templates/MULTI_PI_ROLES.yml`;
  **`ARCHITECTURE_MULTI_INSTITUTION.md`** staged spec.
- **Inline gate cards** (real click-to-approve); **`run_trace.py` custom roster + light mode**.
- **Automated close-out** - `tools/closeout.py` + `templates/CLOSEOUT_CHECKLIST.md` (the Support council
  refreshes the docs after every change instead of letting them drift).
- **Learning Gate HARD LOCK** - `tools/gate_lock.py`: mints a tamper-evident approval token only when the
  ledger + Director contribution pass; post-gate steps `require` it or are blocked (a runtime interlock, not
  just a contract).
- **Multi-PI Stage-1.5 roles** - `tools/roles_check.py` validates `MULTI_PI_ROLES.yml`; `gate.py --roles`
  auto-looks-up each gate's named approver.
- **Enforcement A/B task set expanded** - 12 -> 18 held-out seeded-defect tasks (v1 target ~60/arm).

---

## Near-term (next release cycle)

1. **Learning Gate hard lock** - ✅ shipped as `tools/gate_lock.py` (token-based interlock for any step that calls `require`); a true OS-level sandbox lock remains future.
2. **V1 human-judged enforcement study** - weaker model, ~60 items/arm, a two-rater human panel.
3. **Community faculty packs** - shareable discipline configs via the plugin marketplace.
4. **Richer collaborator sourcing** - ORCID + NSF Award Search.
5. **Connector skills for public data** - USDA NASS, Census, PubMed, arXiv.

---

## Long-term / aspirational

6. **Real secure-data enclave + shared multi-institution infrastructure** - Stage-1 roles shipped;
   Stage-2 (federated SSO, RBAC, encrypted store, access logging) is specified in
   `ARCHITECTURE_MULTI_INSTITUTION.md` but unbuilt - the clearest adoption blocker for consortium grants.
7. **Community projects registry; tighter IRB integration; pre-registration support; offline/air-gapped mode.**

---

## What is NOT on the roadmap

- **Not a fully autonomous research engine.** The human gates are the point.
- **Not a substitute for journal peer review.** The internal audit boards are quality tools, not a replacement.
- **Not a grant-funder database** (use Grants.gov / Pivot-RP) and **not a wet-lab controller**.
- **Not a certified compliance platform (yet).** The per-funder corpus is gate-mapped guidance; the named PI stays accountable.

---

## Deferred Stage-2 (named from the code-aware review)

These are real, acknowledged gaps that need infrastructure a flat-file CLI can't provide — tracked here so they are honest open items, not hidden ones:

- **Web UI with click-through gates** (today: live run board + CLI).
- **Federated auth / SSO / RBAC** so identity is verified, not free-text (today: signed approver token + `CAMBIUM_USER` stamp).
- **Database + multi-tenant isolation** (today: CSV/JSONL/JSON ledgers).
- **Secrets vault** for API keys (today: env var; `doctor.py` scans for hardcoded keys).
- **Auto-feedback of corrections into agent specs** (today: `draft_diff.py` + `learning_gate.py` record them).
See `ARCHITECTURE_MULTI_INSTITUTION.md` and `REVIEW_RESPONSE2.md`.

## Deferred: the cinematic 3D web app (parked — assets + scaffold kept)

A cinematic 3D front-end (cosmos zoom → alien greeter → space-university with council ships → human gates)
was scaffolded but **deferred to a future track**: art-direction and live-render iteration need a browser
preview loop this build environment can't provide. What's kept and reusable in `web/`: the **FastAPI bridge**
(`web/server/`, proven end-to-end), the **R3F scaffold** (`web/frontend-r3f/`), the connected single-file
front-end (`web/frontend/`), the `cinematic-frontend` skill, `tools/gen_3d.py`, and three optimized GLB
assets. Resume by building the front-end in a previewing tool (Lovable/bolt/v0) against the bridge API
(`web/API.md`), or hire art direction. Not a core blocker — Cambium runs fully via CLI/Cowork today.

*Last updated: 2026-06-29. Roadmap reflects the maintainer's current intentions; priorities may shift based on user feedback and available capacity.*
