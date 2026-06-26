# Human Roles & Access — how a whole team runs the Institute

*The agents are the **org**; this file is the **people**. It maps your real team — PI, Co-PIs, project
manager, postdocs, students, staff — onto the Institute so that **each person is the human-in-the-loop
for their own sector**, with control delegated, not bottlenecked through one person. Titles are
configurable in `config.yml`; the roles and the gate-authority are what matter.*

> **Naming.** The demo called the single approver "President." For a real lab the accountable top role is
> the **Director (PI / lab head)**. "Admin" in this framework means the **Project Manager / Coordinator**
> (operations), **not** scientific authority. Rename freely in `config.yml`.

## 1. The human roles

| Role | Who | What they own | Their authority |
|---|---|---|---|
| **Director** (PI / lab head) | the accountable lead | the whole project; cross-cutting decisions | approves **top gates**: submit proposal, publish, budget, external sends; can delegate the rest |
| **Co-PI / Area Lead** | leads one or more Aims | a workstream / Aim | is the **human-in-the-loop for their sector** — approves fixes & reports within their Aim |
| **Project Manager** (Admin / Coordinator) | ops | schedule, meetings, reports, deliverables register, the gate ledger | runs operations; **no scientific approval** |
| **Researcher** (postdoc / staff scientist) | does the science | assigned tasks/experiments | drafts & runs agents; outputs need their Area Lead's sign-off to merge |
| **Student** | trainee | assigned tasks | same as Researcher **+** bound by the teaching/learning rules (don't outsource your learning; instructor owns grades) |
| **Engineer / Staff** | builds | code, tools, data pipeline, the repo | implements & runs experiments; flags data/reproducibility issues |
| **Integrity / Data steward** | independent check | honesty + data | can be a named person **or** the agent + a spot-checker; must be **independent of the author** |

A small lab collapses roles (the PI may also be an Area Lead; a postdoc may be the PM). A big,
multi-institution grant expands them (one Area Lead per institution). The **authority** travels with the
role, not the person.

## 2. Who approves which gate (delegated human-in-the-loop)

This is the heart of it: **authority is delegated by sector**, so every PI/Co-PI is a real approver, not
a spectator.

| Gate | Decision | Approver (default) |
|---|---|---|
| G1 | pursue this RFP? | **Director** (PM advises) |
| G2 | which idea advances? | **Director** + the relevant Co-PIs |
| G3a | who do we contact? | **Director** (PM drafts the outreach; Director sends) |
| G3 | finalize & **submit** proposal | **Director only** (all co-PIs sign the AI Use Statement) |
| G4 | apply audited fixes in a workstream | **the Co-PI / Area Lead who owns that workstream** |
| G5 | release a progress/interim report | **PM compiles → Director or delegated Co-PI approves** |
| G6 | **publish** / external deliverable | **Director only** + every co-author signs the AI Use Statement |

**Separation of duties (non-negotiable):** the person who *authored* a deliverable is **not** its sole
approver; the Verification boards and the Integrity Officer are **independent**; any external release (G3,
G6) needs the Director plus a second human. Record each approval in `governance/GATES.md` with name + role
+ date — an empty approver means **not approved**.

## 3. Which agents each human drives ("your desk")

Everyone uses the **same 45 agents**; roles differ in *which* they typically drive and *what they can
approve*.

| Human role | Agents they drive | Can approve |
|---|---|---|
| **Director** | Orchestrator, PI-agent, Proposal-Writer, Collaborator-Scout | all gates |
| **Co-PI / Area Lead** | Labs, Verification boards, Execution (on their Aim) | G4/G5 for their Aim |
| **Project Manager** | Program-Manager, Office-Manager, Reporting-Officer, Deck-Builder, Record-Keeper | none (compiles, schedules) |
| **Researcher / Student** | Scouts, Labs, Execution, Research-Assistant, Faculty (convene) | nothing alone — sign-off goes up |
| **Engineer / Staff** | Execution, Data-Steward, Janitor, Figures, Librarian | none |
| **Integrity / Data steward** | Integrity-Officer, Data-Steward, Verify-Evidence | flags blockers (P0) |

Note the deliberate independence: the **Verification boards** and **Integrity Officer** are not "owned"
by the author of the work — anyone can trigger them, and an open **P0** they raise blocks release
(`governance/validate.py` enforces it).

## 4. How a real team works, day to day

A 5-person lab running one project:

1. **Director** sets the goal, runs `read rfp` / `brainstorm`, approves the idea (G2), and owns the
   submission (G3).
2. Each **Co-PI** takes an Aim, works in their workstream folder, runs `run lab` on their slice, and
   **approves the fixes for their own Aim (G4)** — they are the human-in-the-loop there.
3. **Researchers/Students** run Scouts/Labs/Execution on assigned tasks and hand verified drafts to their
   Area Lead; nothing merges without that sign-off.
4. The **Project Manager** runs the **monthly meeting** (Office-Manager drafts the agenda/minutes),
   keeps the **deliverables register** (Program-Manager), and compiles **reports** (Reporting-Officer) for
   the Director/Co-PI to release (G5).
5. Before any external release, **`python3 governance/validate.py`** must pass (no open P0), and the
   **Integrity Officer** confirms no claim exceeds its evidence tier. Every co-author signs the
   **AI Use Statement**.

**Multi-institution:** each partner institution is its own Area Lead with its own workstream folder and
its own gate approvals; the Program-Manager merges across institutions; the Director holds the top gates.
Everyone runs the **same template** (copy `.claude/agents/` + the project folder), so outputs are
comparable and mergeable.

## 5. Where each person is "human-in-the-loop"

- **Director** → strategy, submission, publication, budget, external relationships.
- **Co-PI / Area Lead** → everything inside their Aim (which fixes to apply, which results to release).
- **Project Manager** → schedule, reporting cadence, keeping the gate ledger honest.
- **Researcher / Student / Engineer** → the quality of their own work before it goes up for sign-off.
- **Integrity / Data steward** → an independent "stop" on fabrication, leakage, or privacy.

No one is replaced; everyone is **in the loop for their sector**, and the AI never crosses a gate or
sends anything externally on its own.

## 6. Set it up (`config.yml`)
Define your team and the gate-approver map once (see `config.example.yml`). The Orchestrator reads it to
know **who must approve what** before it proceeds. Change a title, add a Co-PI, or re-assign a gate
without touching any agent.
