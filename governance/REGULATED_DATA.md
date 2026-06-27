# Regulated-Data Intake Control (default-deny)

> Closes the technical half of concern #6 ("strong data governance") that policy alone cannot: a **control**,
> not just a checklist. Cambium runs in the user's own account (no third-party cloud), but that is not a
> compliant enclave. This document defines the **default-deny intake rule** for regulated data and the only
> approved pathway. Honest scope: this is an enforceable *policy + procedure* control; encrypted-enclave
> infrastructure (RBAC, KMS, audit logging) is the multi-institution build (see ARCHITECTURE_MULTI_INSTITUTION.md).

## The rule (default deny)
Regulated data **must not be pasted into prompts, agent inputs, or the ledger** unless an approved pathway
is in place. Regulated classes include: FERPA student records, HIPAA/PHI, CUI / export-controlled (ITAR/EAR),
human-subjects identifiable data under IRB, and Indigenous/Tribal-controlled data under CARE. When in doubt,
treat as regulated.

## Approved pathways (pick one before any regulated data enters a run)
1. **De-identify first** — strip direct + quasi-identifiers; run on the de-identified extract; record the
   method. Re-identification stays outside Cambium.
2. **Reference, don't ingest** — keep the data in its compliant system of record; pass Cambium only
   non-regulated summaries/metadata the data steward has cleared.
3. **Approved enclave** — run inside an institutionally-approved secure environment with RBAC, encryption at
   rest/in transit, and access logging. (Cambium does not provide this today; it must be supplied.)

## Procedure (enforced at the gate)
- The **data-steward** classifies every dataset at intake; the classification is recorded.
- A `data_class = regulated` finding without a recorded approved pathway is a **G2/G4 blocker** (the
  research-conduct-officer must sign the pathway before the work proceeds).
- The Director attests at G3/G6 that no regulated data entered a prompt without an approved pathway.

## What is NOT yet enforced by code (stated plainly)
There is no automatic DLP scanner that *detects* regulated content in a prompt and refuses it. The control
above is procedural + gate-enforced. A content-inspection interceptor is on the roadmap; until then, the
control depends on the data-steward and the Director, on the record.
