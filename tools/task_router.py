#!/usr/bin/env python3
"""Cambium Task Router — pick the councils a task needs, build a phase plan.

Given ANY task ("build an app", "review this code", "win an NSF grant"), classify it and emit a
custom multi-phase plan: which councils/agents activate, which run in parallel, and where the human
gates fall. Deterministic + keyword-based (no API key needed). The engine + app consume this so
council selection is Cambium's, not hand-picked.

Usage: python3 tools/task_router.py "your task here"
"""
import sys, json

# canonical council -> agents (the 46)
CMAP = {
 "orch":["orchestrator","document-office"],
 "preaward":["rfp-radar","rfp-analyst","ideation-facilitator","idea-tournament","principal-investigator","proposal-writer","budget-officer","grants-compliance"],
 "partner":["collaborator-scout","partnership-liaison","program-manager","convener"],
 "faculty":["faculty-expert"],
 "scout":["scout-prior-art","scout-methods","scout-landscape"],
 "lab":["lab-theory","lab-methods","lab-domain","lab-statistics"],
 "verify":["verify-rigor","verify-methodology","verify-evidence","verify-domain","referee"],
 "exec":["exec-experiments","exec-ablation","exec-iteration","research-engineer"],
 "reporting":["reporting-officer","deck-builder"],
 "support":["record-keeper","librarian","janitor","teaching-assistant","research-assistant","office-manager","data-steward","integrity-officer","figures","outreach","feedback-router","toolsmith"],
 "gov":["research-conduct-officer"],
}
def A(*names): return list(names)
def C(council, *only):
    ag = CMAP[council]; return [a for a in ag if (not only or a in only)]

def ph(pid, groups, gate=None): return {"id": pid, "groups": groups, "gate": gate}
def grp(label, agents, parallel=True): return {"label": label, "parallel": parallel, "agents": agents}

# ---- per-type phase templates ----
def _grant():
    return [
      ph("intake",[grp("intake",C("preaward","rfp-radar","rfp-analyst"))],{"id":"G1","decision":"pursue this RFP?"}),
      ph("ideation",[grp("scouts",C("scout")),grp("ideate",C("preaward","ideation-facilitator","idea-tournament"),False),grp("faculty",C("faculty"),False)],{"id":"G2","decision":"which idea advances?"}),
      ph("proposal",[grp("PI",C("preaward","principal-investigator"),False),grp("write",C("preaward","proposal-writer","budget-officer","grants-compliance")+C("partner","collaborator-scout","convener")+C("support","librarian","figures")),grp("review",C("verify","referee")+C("gov"),False)],{"id":"G3","decision":"finalize & submit?"}),
    ]
def _software():
    return [
      ph("design",[grp("design",C("lab","lab-methods","lab-domain")),grp("faculty",C("faculty"),False)]),
      ph("build",[grp("build",C("exec"))]),
      ph("verify",[grp("verify",C("verify")),grp("ux",C("lab","lab-domain"),False)],{"id":"G-build","decision":"accept the build?"}),
      ph("govern",[grp("conduct",C("gov"))],{"id":"G-ship","decision":"ship / deploy?"}),
    ]
def _review():
    return [
      ph("review",[grp("review",C("exec","research-engineer")+C("verify")+C("lab","lab-domain"))]),
      ph("adjudicate",[grp("referee+conduct",C("verify","referee")+C("gov"),False)],{"id":"G-fix","decision":"apply fixes / accept?"}),
    ]
def _research():
    return [
      ph("scout",[grp("scouts",C("scout"))],{"id":"G2","decision":"which direction?"}),
      ph("build",[grp("labs",C("lab"))]),
      ph("experiment",[grp("execution",C("exec"))]),
      ph("verify",[grp("verify",C("verify")),grp("conduct",C("gov"),False)],{"id":"G4","decision":"accept results?"}),
    ]
def _report():
    return [ph("report",[grp("reporting",C("reporting"))],{"id":"G5","decision":"release report?"})]
def _data():
    return [
      ph("prep",[grp("data",C("support","data-steward","research-assistant"))]),
      ph("analyze",[grp("stats",C("lab","lab-statistics"))]),
      ph("verify",[grp("verify",C("verify","verify-methodology","verify-evidence"))],{"id":"G4","decision":"accept analysis?"}),
    ]
def _video():
    # video deliverable via the render-video skill -> external OpenMontage (AGPLv3, separately installed)
    return [
      ph("produce",[grp("reporting",C("reporting")),grp("media",C("support","figures","outreach"),False)],{"id":"G5","decision":"release the video?"}),
      ph("publish",[grp("conduct",C("gov"))],{"id":"G6","decision":"publish / external?"}),
    ]

TYPES = [
 ("grant",      ["grant","proposal","rfp","nofo","funding","solicitation","afri","nsf","nih","usda","biosketch","budget justification"], _grant),
 ("review",     ["review","audit","harden","qa","security","vulnerab","refactor","bug","fix the","lint","test the","check the","penetration"], _review),
 ("software",   ["app","web app","website","software","build a","develop","frontend","back-end","backend","ui","ux","deploy","feature","api","dashboard","tool"], _software),
 ("video",      ["video","video abstract","explainer video","animated explainer","render video","video pitch","grant video","results explainer","teaser","trailer","montage","reel","make a video"], _video),
 ("report",     ["report","deck","slides","presentation","summary","progress report","annual report","memo","newsletter"], _report),
 ("data",       ["dataset","data analysis","clean the data","etl","wrangle","profile the","statistics on","analyze the data"], _data),
 ("research",   ["research","experiment","study","hypothesis","benchmark","method","model","theory","estimator","simulation"], _research),
]

def classify(task):
    t = task.lower(); best, score = "research", 0
    order = {n:i for i,(n,_,_) in enumerate(TYPES)}
    hits = {}
    for name, kws, _ in TYPES:
        hits[name] = sum(1 for k in kws if k in t)
    for name, _, _ in TYPES:
        if hits[name] > score or (hits[name] == score and hits[name] > 0 and order[name] < order.get(best, 99)):
            best, score = name, hits[name]
    return (best if score > 0 else "research"), hits

def _provision():
    return ph("provision",[grp("toolsmith", C("support","toolsmith"), False)],
              {"id":"G-provision","decision":"approve the toolchain (reuse beats rebuild)?"})

def _writeup():
    # final written deliverable from VERIFIED findings, with citations + figures
    return ph("writeup",[grp("write-up",C("orch","document-office")+C("support","librarian","figures"),False)])

def _closeout():
    # Support council housekeeping after EVERY task; no human gate (automatic close-out)
    return ph("closeout",[grp("close-out",C("support","record-keeper","integrity-officer","janitor"))])

def plan_for_type(typ):
    builder = dict((n,b) for n,_,b in TYPES)[typ]
    phases = builder()
    if typ in ("software","research","data","video"):
        phases = [_provision()] + phases
    if typ in ("research","report","data"):
        phases = phases + [_writeup()]
    return phases + [_closeout()]

def route(task):
    typ, hits = classify(task)
    phases = plan_for_type(typ)
    councils = sorted({c for p in phases for g in p["groups"] for c in [k for k,v in CMAP.items() if set(g["agents"]) & set(v)]})
    n_agents = len({a for p in phases for g in p["groups"] for a in g["agents"]})
    return {"task": task, "type": typ, "councils": councils, "n_agents": n_agents, "phases": phases, "signal": hits}

if __name__ == "__main__":
    task = " ".join(sys.argv[1:]) or "a sample research project"
    r = route(task)
    print("TASK:", task)
    print("TYPE:", r["type"], "| councils:", ", ".join(r["councils"]), "| agents:", r["n_agents"])
    for p in r["phases"]:
        print("  PHASE", p["id"], "+ GATE "+p["gate"]["id"] if p["gate"] else "  PHASE "+p["id"])
        for g in p["groups"]:
            print("     %s %s: %s" % ("∥" if g["parallel"] and len(g["agents"])>1 else "→", g["label"], ", ".join(g["agents"])))
