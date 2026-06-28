"""Cambium bridge engine — turns a request into a streamed, gated run the front-end can drive.

This is the connective tissue between a web front-end and the Cambium institute. It reuses the real
tools/task_router.py to decide which councils a request mobilizes, then emits a stream of events
(phase.start, agent.finding, gate.open, ...) that a web app renders as the live 3D campus. At a gate it
PAUSES and waits for the user's APPROVE/REVISE/REJECT — the same human-in-the-loop contract as the CLI,
and the same pause/resume shape as `cambium_run.py --resume` + `gate_lock`.

Two modes:
  - simulation (default): scripts believable council findings so a front-end works with NO API key.
  - live (CAMBIUM_LIVE=1 + ANTHROPIC_API_KEY): the hook in `run_agent_live()` is where a real Claude
    Agent SDK / Messages call goes. Left as a clearly-marked seam so the demo runs out of the box and the
    production path is obvious and honest.
"""
import asyncio, os, random, sys, time, uuid

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import task_router  # the real router — single source of truth for which councils a request needs

SHORT2TITLE = {"orch":"Orchestration","preaward":"Pre-Award","partner":"Partnerships","faculty":"Faculty",
 "scout":"Scouts","lab":"Labs","verify":"Verification","exec":"Execution","reporting":"Reporting",
 "support":"Support","gov":"Governance"}
A2C = {a: SHORT2TITLE.get(c, c.title()) for c, ags in task_router.CMAP.items() for a in ags}

FINDINGS = {
 "Scouts":["mapped 3 funder priorities to mirror","nearest prior work is 2 cycles old — clear novelty","found 2 reusable datasets"],
 "Pre-Award":["parsed eligibility, page limits, deadline","drafted the Specific Aims scaffold","budget within the F&A cap"],
 "Faculty":["the contribution is single and clear","flagged an identifiability assumption","power looks sufficient"],
 "Labs":["chose a cross-fitted estimator","ruthlessly simplified the design","added a leakage guard"],
 "Execution":["ran the pipeline; saved result tables","ablation: 2 components carry the effect","re-ran — numbers reproduce"],
 "Verification":["reproduced every headline number","no leakage; baselines are fair","one claim downgraded to Asserted"],
 "Partnerships":["3 candidate Co-PIs that fit the aims","drafted the outreach (you send it)","roles mapped, no overlap"],
 "Governance":["IRB pathway identified","no regulated data without an approved route","AI-use statement attached"],
 "Reporting":["milestones vs plan — honest status","abstract sharpened to one contribution","figures from verified numbers only"],
 "Support":["findings ledger updated","provenance hash recorded","run archived, no stray files"],
 "Orchestration":["routed the work; holding the gates","merged council outputs into one decision"]}

GATE_Q = {"G1":("Pursue this RFP / direction?","Eligibility, fit and deadline before we commit effort."),
 "G2":("Which idea advances?","Pick the aim that best wins against the criteria."),
 "G3":("Finalize & submit?","Director-only authority. Nothing is submitted without you."),
 "G4":("Accept the results?","Evidence-tiered verdict — accept, revise, or reject."),
 "G5":("Release the report?","Milestones vs plan, no spin — your release decision."),
 "G-provision":("Approve the toolchain?","Reuse beats rebuild — confirm the tools.")}

def plan_for(task):
    """Return the routed plan as front-end-friendly phases (reuses the real task_router)."""
    routed = task_router.route(task or "a Cambium run")
    phases = []
    for ph in routed.get("phases", []):
        councils, agents = [], []
        for grp in ph.get("groups", []):
            for a in grp.get("agents", []):
                c = A2C.get(a, "Support")
                if c not in councils: councils.append(c)
                agents.append({"council": c, "role": a.replace("-", " ").title(), "agent": a})
        gate = None
        if ph.get("gate"):
            gid = ph["gate"]["id"]; q, d = GATE_Q.get(gid, (ph["gate"].get("decision", "Decision?"), ""))
            gate = {"id": gid, "question": q, "detail": d}
        phases.append({"id": ph.get("id"), "label": ph.get("id", "phase").replace("-", " ").title(),
                       "councils": councils, "agents": agents, "gate": gate})
    active = sorted({c for p in phases for c in p["councils"]} | {"Orchestration"})
    return {"kind": routed.get("type", "research"), "phases": phases, "active": active}


class Run:
    """One in-flight run: holds its plan, an event queue the WebSocket drains, and a gate latch."""
    def __init__(self, task):
        self.id = uuid.uuid4().hex[:12]
        self.task = task
        self.plan = plan_for(task)
        self.queue = asyncio.Queue()
        self.gate_event = asyncio.Event()
        self.gate_decision = None
        self.decisions = []
        self.revises = 0
        self.done = False

    async def emit(self, **ev):
        ev["ts"] = round(time.time(), 3)
        await self.queue.put(ev)

    async def run_agent_live(self, council, role):
        """SEAM for production: call the Claude Agent SDK / Messages API here and return the agent's text.
        Left unimplemented on purpose so the demo runs without a key; flip CAMBIUM_LIVE=1 and wire this."""
        raise NotImplementedError("live mode: wire the Claude Agent SDK here")

    async def finding_for(self, council, role):
        if os.environ.get("CAMBIUM_LIVE") == "1" and os.environ.get("ANTHROPIC_API_KEY"):
            try:
                return await self.run_agent_live(council, role)
            except Exception as e:
                return "(live agent unavailable: %s)" % str(e)[:60]
        return random.choice(FINDINGS.get(council, ["working…"]))

    async def drive(self, step=None):
        step = float(os.environ.get('CAMBIUM_STEP', '0.7')) if step is None else step
        """The run loop: emit phase/agent/gate events; pause at each gate until decided."""
        p = self.plan
        await self.emit(type="run.started", run_id=self.id, kind=p["kind"], active=p["active"],
                        phases=[{"label": ph["label"], "councils": ph["councils"],
                                 "gate": ph["gate"]["id"] if ph["gate"] else None} for ph in p["phases"]])
        await self.emit(type="orchestrator", text="The President reads the request and mobilizes %d of 11 councils; the rest stay dim." % (len(p["active"]) - 1))
        i = 0
        while i < len(p["phases"]):
            ph = p["phases"][i]
            await self.emit(type="phase.start", index=i, label=ph["label"], councils=ph["councils"])
            await asyncio.sleep(step)
            for ag in ph["agents"]:
                fd = await self.finding_for(ag["council"], ag["role"])
                await self.emit(type="agent.finding", council=ag["council"], role=ag["role"], finding=fd)
                await asyncio.sleep(step)
            await self.emit(type="phase.done", index=i)
            if ph["gate"]:
                g = ph["gate"]
                await self.emit(type="gate.open", gate_id=g["id"], question=g["question"], detail=g["detail"])
                self.gate_event.clear()
                await self.gate_event.wait()                      # PAUSE — wait for the human
                d = self.gate_decision
                self.decisions.append({"gate": g["id"], "decision": d})
                await self.emit(type="gate.decided", gate_id=g["id"], decision=d)
                if d == "REJECT":
                    await self.emit(type="run.done", rejected=True, summary=self.summary())
                    self.done = True; await self.queue.put(None); return
                if d == "REVISE":
                    self.revises += 1
                    await self.emit(type="orchestrator", text="Routing back — %s revises and returns to the gate." % ph["label"])
                    await asyncio.sleep(step * 1.5)
                    continue                                       # re-run this phase's gate
            i += 1
        await self.emit(type="run.done", rejected=False, summary=self.summary())
        self.done = True
        await self.queue.put(None)

    def decide(self, decision):
        self.gate_decision = decision
        self.gate_event.set()

    def summary(self):
        return {"task": self.task, "kind": self.plan["kind"],
                "councils": len(self.plan["active"]) - 1,
                "gates": self.decisions, "revises": self.revises}


RUNS = {}
def create_run(task):
    r = Run(task); RUNS[r.id] = r; return r
def get_run(rid): return RUNS.get(rid)
