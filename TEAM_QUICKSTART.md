# Team Quickstart — Cambium
*One-page reference card. Print it, pin it, paste it in your onboarding doc.*

---

## How we work together (the loop)

```
Director sets goal
  → Co-PIs run their Aims  (Labs + Verification + Execution)
    → PM compiles schedule & reports
      → gates signed by the right approver
        → validate.py passes (no open P0)
          → Director (or delegated Co-PI) releases
```

The AI drafts, researches, verifies, and reports.  
**Humans decide at every Gate. Nothing is sent or released without a named approver.**

---

## Role cards

### Director (PI / Lab Head)
*Owns the whole project; holds all top gates.*

| Your first 3 actions | What you approve |
|---|---|
| 1. Copy `config.example.yml` → `config.yml`; set your name as `director` | **G1** – pursue this RFP? |
| 2. Say `read rfp <file>` → review the RFP brief → decide at **G1** | **G2** – which idea advances? |
| 3. Say `brainstorm` → review ranked ideas → decide at **G2** | **G3** – finalize & submit proposal |
| | **G3a** – who do we contact? |
| | **G4** – apply fixes (or delegate to Area Lead) |
| | **G5** – release report (or delegate) |
| | **G6** – publish / external deliverable |

> G3 and G6 require a second human. External sends are always yours to execute.

---

### Co-PI / Area Lead
*Owns one or more Aims; is the human-in-the-loop for their workstream.*

| Your first 3 actions | What you approve |
|---|---|
| 1. Add yourself to `config.yml` under `team:` with `role: co-pi` and your `aims: [N]` | **G4** – apply P0/P1 fixes within your Aim(s) |
| 2. Create your workstream folder: `projects/<slug>/aims/aimN/` | **G5** – release report for your Aim (when Director delegates) |
| 3. Say `run lab` on your Aim; review the issue table and decide at **G4** | |

> You cannot be the sole approver of work you authored (separation of duties).  
> Verification boards and the Integrity Officer are independent of you.

---

### Project Manager / Coordinator
*Runs operations; keeps the gate ledger honest. No scientific approval.*

| Your first 3 actions | What you approve |
|---|---|
| 1. Say `project approved` after award → Program-Manager builds the WBS + milestone calendar | Nothing — you compile and schedule |
| 2. Run monthly meeting: `office-manager` drafts agenda/minutes | |
| 3. Say `progress report` → compile with Reporting-Officer → route to Director/Co-PI for G5 | |

> Record every gate approval in `governance/GATES.md` (name + role + date).  
> An empty "Approved by" = NOT approved. `validate.py` will block release.

---

### Researcher / Postdoc / Staff Scientist
*Does the science; hands verified work up to Area Lead for sign-off.*

| Your first 3 actions | What you approve |
|---|---|
| 1. Add yourself to `config.yml` with `role: researcher` and your `aims: [N]` | Nothing alone — your outputs require Area Lead sign-off before they merge |
| 2. Run Scouts to survey prior art: `01-scout-fh`, `02-scout-spatial`, `03-scout-tree-ml` | |
| 3. Run Labs on your task: `04-lab-theory`, `05-lab-ml`, or `06-lab-forestry` | |

> Route all completed drafts to your Area Lead. Nothing crosses a gate on your authority.

---

### Student (Trainee)
*Same as Researcher, plus the learning rules.*

| Your first 3 actions | What you approve |
|---|---|
| 1. Add yourself to `config.yml` with `role: student` and your `aims: [N]` | Nothing alone — same as Researcher |
| 2. Use `17-ta` and `18-ra` to get guidance and run assigned tasks | |
| 3. Draft your section; route to Area Lead for sign-off before it merges | |

> Do not outsource your learning. The AI is a lab assistant, not your ghostwriter.  
> Your instructor/advisor owns grade and credit decisions.

---

### Engineer / Staff
*Builds tools, pipelines, and runs experiments. Flags data issues.*

| Your first 3 actions | What you approve |
|---|---|
| 1. Add yourself to `config.yml` with `role: engineer` | Nothing — flags only (P0 blockers via Integrity-Officer) |
| 2. Run `20-data-steward` to inventory data + check for leakage | |
| 3. Run `16-janitor` to keep the repo clean; `22-figures` for charts | |

> If you find a reproducibility or data integrity problem, raise a P0 immediately.  
> An open P0 blocks all releases — `validate.py` enforces it.

---

## Gate quick-reference

| Gate | Decision | Who approves |
|---|---|---|
| G1 | Pursue this RFP? | Director |
| G2 | Which idea advances? | Director (Co-PIs consulted) |
| G3a | Who do we contact? | Director |
| G3 | Finalize & submit proposal | **Director ONLY** + 2nd human |
| G4 | Apply fixes in a workstream | Co-PI / Area Lead (that Aim) |
| G5 | Release progress/interim report | Director or delegated Co-PI |
| G6 | Publish / external deliverable | **Director ONLY** + all co-authors sign AI Use Statement |

---

## Useful commands

```bash
# Find your role, desk, and gate authority
python3 tools/whoami.py                   # list everyone
python3 tools/whoami.py director          # look up by role
python3 tools/whoami.py "Dr. Co-PI A"    # look up by name

# Check that all gates are clean before any release
python3 governance/validate.py

# Lifecycle triggers (say these to the Orchestrator)
read rfp <file>          # → G1
brainstorm               # → G2
draft proposal           # → G3
project approved         # start post-award
run lab                  # one develop-verify-fix cycle → G4
progress report          # → G5 / G6
```

---

*See `ROLES.md` for the full authority model. See `governance/GATES.md` to record approvals.  
See `GETTING_STARTED.md` for A/B/C entry paths. See `OUTPUT_CONTRACT.md` for agent output format.*
