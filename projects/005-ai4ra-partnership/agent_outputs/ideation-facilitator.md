# Ideation Facilitator: Cambium Add-ons for AI4RA Partnership
*Date: 2026-06-30 | Project: 005-ai4ra-partnership*

---

## DIVERGE: 11 Candidate Add-ons

**A. Responsible-AI Audit + Disclosure Layer**
Assembles a timestamped, gate-signed AI-use disclosure document for each proposal, citing which Cambium agents acted and at what evidence tier, satisfying NIH NOT-OD-25-132 and federal AI scan requirements; consumes Vandalizer's extraction run as the documented input artifact.

**B. Budget-to-Solicitation Compliance Validator**
Reasons pairwise over Vandalizer's extracted NOFO rules and the PI's budget line items to produce a citation-backed pass/fail compliance report before submission -- the step that sits directly above extraction and requires orchestration, not just parsing.

**C. Limited-Submission Coordination and Eligibility Gate**
Tracks internal competitions at the institution level, screens PI eligibility criteria from the extracted NOFO, manages a nomination workflow with a human approval gate, and prevents duplicate submissions.

**D. Current-and-Pending / Other-Support Assembly Agent**
Pulls active and pending awards from the institutional SPS, formats them to SciENcv schemas, flags effort-commitment overlaps, and routes to PI for Cambium gate sign-off; turns a manual multi-hour task into a governed workflow.

**E. Post-Award Burn-Rate Monitor and Alert Agent**
Ingests periodic financial exports (Banner, Workday, Kuali), projects end-of-award balance trajectory, and fires role-specific alerts when spending deviates from plan; continuous orchestration over the award life rather than any point-in-time extraction.

**F. No-Cost Extension and Budget Modification Workflow**
Guides a PI through NCE justification logic using award terms extracted by Vandalizer, assembles the required narrative, and routes it through department and OSP gates before submission.

**G. Subrecipient Ongoing Risk Monitor**
Runs quarterly reasoning over a subrecipient's invoices, financial reports, and audit findings to update a risk score and flag anomalies; moves beyond the one-time setup checklist to continuous cross-time orchestration.

**H. Cross-Funder Rule Conflict Detector**
For multi-funded projects, reasons over each funder's rule set from separate Vandalizer runs to surface cost-share conflicts, period-of-performance overlaps, and IP clause incompatibilities.

**I. Proposal Narrative Consistency Checker**
Compares aims, methods, personnel, and budget sections of a draft proposal against each other and against NOFO requirements to flag internal contradictions without generating any new narrative text.

**J. MindRouter / FERPA-Safe Routing Agent**
Classifies each Cambium task by data sensitivity and directs it to MindRouter (on-premise UIdaho GPUs) vs. commercial APIs, logging the routing decision in the audit trail; addresses data-sovereignty concerns for PUI/ERI/MSI institutions.

**K. Closeout Checklist and Final Reporting Coordinator**
Orchestrates closeout tasks (final FFR, final technical report, equipment inventory, subrecipient closeout, patent disclosure) against sponsor-specific deadlines from Vandalizer, assigning tasks to named roles and gating on each confirmation.

---

## CONVERGE: Scoring Matrix

Criteria (1-4 each, higher is better):
- **Fit**: alignment with AI4RA's open, FAIR, under-resourced-institution mission
- **Gap**: urgency and reality of the unmet need
- **Strength**: degree to which Cambium's orchestration and audit trail are uniquely required
- **Proto**: speed to a working prototype (4 = small effort)

| ID | Short name | Fit | Gap | Strength | Proto | Total |
|----|---|---|---|---|---|---|
| A | AI Audit + Disclosure | 4 | 4 | 4 | 4 | **16** |
| B | Budget Compliance Validator | 4 | 4 | 4 | 3 | **15** |
| D | C&P / Other-Support Assembly | 4 | 4 | 3 | 3 | **14** |
| E | Burn-Rate Monitor | 4 | 4 | 4 | 2 | **14** |
| C | Limited-Submission Gate | 3 | 3 | 3 | 4 | **13** |
| F | NCE / Budget Mod Workflow | 4 | 3 | 3 | 3 | **13** |
| K | Closeout Coordinator | 4 | 3 | 3 | 3 | **13** |
| G | Subrecipient Risk Monitor | 3 | 3 | 4 | 2 | **12** |
| J | MindRouter Routing Agent | 3 | 3 | 4 | 2 | **12** |
| H | Cross-Funder Conflict Detector | 3 | 3 | 3 | 2 | **11** |
| I | Narrative Consistency Checker | 3 | 2 | 3 | 3 | **11** |

---

## TOP 4 PICKS

### 1. Responsible-AI Audit + Disclosure Layer -- Score 16 -- Effort: Small

Captures every Cambium agent action, evidence tier, and human gate decision into a signed disclosure document a PI can attach to a proposal or retain for audit. AI4RA would want this because compliance is immediate and mandatory under NIH NOT-OD-25-132, none of their current tools produce it, and it validates the entire Cambium-over-Vandalizer stack in one concrete deliverable. No new reasoning engine is required: the audit trail already exists inside Cambium; this is a report-assembly and gate workflow. Buildable in days once the Cambium gate infrastructure is live.

### 2. Budget-to-Solicitation Compliance Validator -- Score 15 -- Effort: Medium

Takes Vandalizer's extracted NOFO rules and the PI's budget, reasons over them pairwise, and produces a citation-backed pass/fail compliance report before submission. AI4RA stops at extraction; this is the natural next layer that only an orchestration engine with evidence-tier contracts can do reliably. The output is directly legible to sponsored-programs officers at under-resourced institutions with no dedicated compliance staff.

### 3. Current-and-Pending / Other-Support Assembly Agent -- Score 14 -- Effort: Medium

Pulls award data from the institutional SPS, formats to NIH/NSF SciENcv schemas, detects effort-commitment overlaps, and routes to the PI for gate approval. SciENcv formatting errors are a leading cause of Just-In-Time delays at the PUIs and MSIs that AI4RA was built to serve. No current AI4RA tool touches post-extraction assembly or cross-award conflict detection, so this fills genuine white space at exactly the right constituency.

### 4. Post-Award Burn-Rate Monitor and Alert Agent -- Score 14 -- Effort: Medium

Ingests financial snapshots from Banner/Workday/Kuali on a recurring schedule, projects end-of-award balance, and fires role-specific alerts before a problem becomes terminal. Continuous orchestration over time is the structural strength Cambium has that extraction tools lack by design. This add-on also extends the partnership's commercial and demonstration value from pre-award into the full research lifecycle.

---

## Ranked Top 4 (one line each)

1. Responsible-AI Audit + Disclosure -- mandatory compliance now, pure Cambium audit-trail strength, small effort, immediate partnership differentiator
2. Budget-to-Solicitation Compliance Validator -- reasons over Vandalizer output rather than stopping at it, directly legible value to OSP officers, medium effort
3. Current-and-Pending / Other-Support Assembly -- SciENcv mandate, high pain at PUIs and MSIs, governed PI sign-off gate, medium effort
4. Post-Award Burn-Rate Monitor -- extends lifecycle beyond pre-award, continuous orchestration advantage over extraction tools, medium effort
