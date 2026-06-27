# Multi-Institution Cambium — design spec (concern #9)

> **Status: DESIGN SPEC, not shipped.** Concern #9 ("collaboration should scale across institutions") is
> Cambium's clearest gap: today it is single-account, file + git, one institution at a time. Real shared
> infrastructure (servers, federated identity, encrypted storage) cannot be built in a working session —
> this document is the honest architecture for it, so the gap is *scoped*, not hand-waved. It pairs with
> `governance/REGULATED_DATA.md` (the data-control half).

## What "scales across institutions" actually requires
A consortium grant (NSF EPSCoR, USDA multi-state, NIH U01) needs several things Cambium does not yet have:

1. **Shared identity** — Co-PIs at different institutions, each authenticating with their own credentials
   (federated SSO / InCommon / ORCID), not a shared login. *(Cambium: ADR-004 — hosted multi-user is future.)*
2. **Roles & access control (RBAC)** — Director, Co-PI, area lead, student, integrity/data steward, each
   with scoped permissions per project and per gate. *(Cambium has the ROLES.md model on paper; no enforced
   RBAC.)*
3. **A shared, authoritative ledger** — one findings ledger + GATES.md + run state that all partners read
   and append to, with per-partition write rights and an immutable audit trail. *(Today: per-user git repo.)*
4. **Data-use agreements & per-partner data governance** — each institution's regulated-data rules
   (REGULATED_DATA.md) enforced at its boundary; no partner's restricted data crosses without an agreement.
5. **Per-partner approval at shared gates** — a multi-PI gate where each institution's approver signs for
   their scope (extends the existing separation-of-duties model to N institutions).

## The staged path (smallest real step first)
- **Stage 0 (today):** single-account, file+git; collaboration by sharing the repo. Honest baseline.
- **Stage 1 (small, buildable next):** a **multi-PI config + roles model** in `config.yml` — named Co-PIs
  per institution, a per-gate approver map across institutions, and a `gate.py` extension that requires the
  *named* approver for that scope (not just any human). This is a config + check, no server — a real
  increment that makes the *roles* enforceable even on shared git.
- **Stage 2 (infrastructure):** a hosted shared ledger + service (server + DB + federated SSO + RBAC +
  encrypted storage + audit log). This is the genuine "shared infrastructure" the concern asks for, and is
  a build, not a session task. It also supplies the encrypted enclave REGULATED_DATA.md defers to.
- **Stage 3:** cross-institution dashboards + the run board served to all partners live.

## Honest bottom line
Cambium is an institution-in-a-box per user today, and that is the right unit to *start* from — but a
consortium cannot adopt it as shared infrastructure until at least Stage 2. The credible claim is "strong
single-institution governance now; multi-institution roles next (Stage 1); shared infrastructure on the
roadmap (Stage 2)." Anything stronger would be the overclaim Cambium exists to prevent.

*Pairs with: governance/REGULATED_DATA.md · ROLES.md · ADR-004 (single-account today) · ADR-036.*
