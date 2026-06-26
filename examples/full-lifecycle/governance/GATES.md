# Human Approval Ledger — Campus Bike-Share Demand Forecaster (FICTIONAL DEMO)
*All names and dates are invented for demonstration purposes.*

Human-in-the-loop approvals recorded below. The Orchestrator did not proceed past any gate until the
named approver recorded their decision. validate.py treats a missing or empty "Approved by" as
unapproved. Separation of duties: the author of a deliverable is not its sole approver.

---

| Gate | Decision | Approver role | Approved by (name) | Date | Notes |
|---|---|---|---|---|---|
| G1 | Pursue the Campus Sustainability Office RFP on bike-share demand forecasting | Director | Dr. Amara Osei-Bonsu | 2025-02-10 | Contingent on initiating data MOU conversation with Transport Office; Co-PI from CS approved |
| G2 | Idea A (gradient-boosted trees + spatial lag) advances to aims drafting | Director + Co-PIs | Dr. Amara Osei-Bonsu; Dr. Lena Hartmann | 2025-02-17 | Spatial lag feature included; faculty reviews requested before proposal draft |
| G3a | Outreach to Transport Office re: data MOU; outreach to Computing cluster re: HPC allocation | Director | Dr. Amara Osei-Bonsu | 2025-02-24 | Director sent both emails personally; no external send by AI agents |
| G3 | Finalize and submit proposal to Campus Sustainability Office | Director only | Dr. Amara Osei-Bonsu | 2025-03-07 | All faculty concerns addressed (SR-01 train/test gap; SR-02 MAE co-metric; MLR-03 SHAP framing); budget trimmed to $178K; all co-investigators signed AI Use Statement |
| G4 | Apply fixes for Aim 2 workstream (data-leakage patch F001b; metric fix F002; SHAP framing F003) | Area Lead — Aim 2 | Dr. Lena Hartmann | 2025-09-12 | Reviewed Integrity Officer audit (F001/F001b); clean-split metrics confirmed; no open P0 remains; validator passed before this approval |
| G5 | Release annual/progress report (D11) to sponsor | Director | Dr. Amara Osei-Bonsu | 2025-11-20 | Report cites only Code-verified or Proved findings; limitations (F005 sample size) disclosed; PM Ms. Chandrasekaran compiled |
| G6 | Public / external deliverable: open-source code release (D9) + final report to sponsor | Director only + co-authors | Dr. Amara Osei-Bonsu; Dr. Lena Hartmann | 2025-11-25 | All co-authors signed AI Use Statement; validate.py passed (no open P0); Integrity Officer confirmed no claim exceeds evidence tier |

---

**Separation of duties confirmed:**
- Dr. Tanaka (Aim 2 author) did not approve Aim 2 findings — Co-PI Dr. Hartmann held G4.
- Integrity Officer (independent) raised F001 and confirmed F001b resolution before G4.
- G3 and G6 required Director plus at least one co-author AI Use Statement signature.
- No external send (email to sponsor, code release) was executed by any AI agent; all external actions were performed by the named human approvers.
