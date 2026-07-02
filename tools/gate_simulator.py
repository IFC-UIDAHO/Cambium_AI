#!/usr/bin/env python3
"""gate_simulator - a governance flight simulator for Cambium's 8-gate discipline.

Purpose:
  Teach the gate discipline (G0, G1, G2, G3a, G3, G4, G5, G6) by practicing
  realistic research-governance dilemmas. For each scenario you choose
  APPROVE, REVISE, or REJECT; the simulator shows the consequence of your
  choice and explains the rubric-correct answer, grounded in the rules this
  repo actually enforces:
    - governance/GATES.md: the gate table and approver roles; separation of
      duties (the author of a deliverable is not its sole approver; G3 and G6
      need the Director plus a second human); external sends (submit,
      publish, email) are always a human action; an empty "Approved by" is
      NOT approved; a REJECT really stops the run.
    - governance/VERIFICATION_PROTOCOL.md: evidence tiers Proved,
      Code-verified, Asserted; an Asserted claim must be downgraded or
      closed before release; Code-verified means a script ran and produced
      the number, with the command and output hash recorded.

Decision semantics (from the GATE_SUMMARY one-pager used at real gates):
  APPROVE = open the gate and proceed;
  REVISE  = do not open; send the work back with named changes and re-present;
  REJECT  = do not open; stop this line of work.

Usage:
  python3 tools/gate_simulator.py --list
  python3 tools/gate_simulator.py --play 6 --choose revise
  python3 tools/gate_simulator.py --quiz            # all scenarios, no answers
  python3 tools/gate_simulator.py --key             # the answer key
  python3 tools/gate_simulator.py --interactive     # terminal session (uses input())

Exit codes: 0 normally (a wrong quiz answer is still exit 0); 1 on invalid
input (bad scenario number, --choose without --play, no mode given).

Honest limits:
  Scenarios are synthetic and generic: no real people, projects, funders, or
  numbers. The rubric encodes the gate semantics as written in this repo's
  governance files at the time this tool was built; if those files change,
  re-check the scenarios against them. This is a teaching tool only: it never
  opens, blocks, or records a real gate.
"""
import argparse
import sys

import cambium_io  # noqa: F401

CHOICES = ("approve", "revise", "reject")

SCENARIOS = [
    {
        "id": 1,
        "gate": "G0",
        "question": "is the PI profile ready?",
        "approver": "Director",
        "title": "Brainstorm before the profile",
        "situation": (
            "A new project is starting. USER_PROFILE.md does not exist yet: "
            "nobody has recorded the researcher's interests, expertise, or "
            "constraints. The orchestrator proposes to start brainstorming "
            "project ideas immediately and fill in the profile later."),
        "options": {
            "approve": ("You open the gate. Ideas arrive fast, but they are "
                        "generic: nothing anchors them to the researcher's "
                        "actual expertise, so the idea slate becomes rework "
                        "once the profile finally exists."),
            "revise": ("You hold the gate and ask for the profile first: "
                       "interests, expertise, constraints. Brainstorming "
                       "starts one step later and lands on ideas the "
                       "researcher can actually own."),
            "reject": ("You stop the project outright. Nothing was wrong "
                       "with the goal; the only gap was a missing profile, "
                       "so stopping everything throws away a viable line of "
                       "work."),
        },
        "correct": "revise",
        "why": ("G0 exists exactly for this case: the gate question is 'is "
                "the PI profile ready?' and the recorded rule is that Cambium "
                "does not brainstorm until the PI is known. The work is not "
                "bad, it is premature: REVISE (complete the profile, then "
                "re-present the gate) is proportionate. REJECT is reserved "
                "for lines of work that should stop."),
        "rules": ["governance/GATES.md: G0 requires USER_PROFILE.md to exist "
                  "before ideation begins."],
    },
    {
        "id": 2,
        "gate": "G1",
        "question": "pursue this RFP?",
        "approver": "Director",
        "title": "Ineligible but exciting",
        "situation": (
            "A funding call fits the team's topic almost perfectly. Reading "
            "the eligibility section closely, sub-awards under this program "
            "are restricted to external institutions, and your institution "
            "is the prime on the same award, so it cannot apply through this "
            "mechanism. The team is enthusiastic and suggests pursuing "
            "anyway while clarifying eligibility later."),
        "options": {
            "approve": ("Weeks of proposal work end at an administrative "
                        "rejection that no reviewer ever reads. The "
                        "eligibility clause was knowable on day one."),
            "revise": ("You send the fit assessment back for another pass, "
                       "but no revision changes the eligibility rule: you "
                       "spend more effort to reach the same wall."),
            "reject": ("You record REJECT with the eligibility clause as the "
                       "reason. The team pivots to a mechanism it can "
                       "actually use, and the decision plus its reason sits "
                       "in the ledger so no future run rediscovers it."),
        },
        "correct": "reject",
        "why": ("G1 asks 'pursue this RFP?', and eligibility is a hard "
                "constraint, not a fit score to be improved. When no "
                "revision can cure the defect, REJECT is the honest gate "
                "decision: it genuinely stops the line of work and records "
                "why. A different mechanism or partner is a new decision at "
                "a new gate, not a patch on this one."),
        "rules": ["governance/GATES.md: G1 'pursue this RFP?' is a Director "
                  "decision; gate decisions are recorded with their reasons, "
                  "and a REJECT stops the run."],
    },
    {
        "id": 3,
        "gate": "G2",
        "question": "which idea advances?",
        "approver": "Director (+Co-PIs)",
        "title": "The tournament produced a winner",
        "situation": (
            "Three candidate ideas went through a ranked tournament. Idea B "
            "ranked first: the scouts checked its novelty against prior "
            "work, its key citation resolves to a real paper, and the scope "
            "fits the available budget. You have written your own hypothesis "
            "and reasoning for the gate record. The only argument anyone "
            "offers for waiting is a vague wish for one more review round."),
        "options": {
            "approve": ("Idea B advances. The ledger records the evidence "
                        "and your own contribution next to the decision, and "
                        "the run keeps its momentum."),
            "revise": ("Another review round runs, finds nothing new, and "
                       "costs a week. Gates are checkpoints, not brakes for "
                       "their own sake; indefinite re-review is where runs "
                       "stall."),
            "reject": ("You discard verified, in-scope work with no stated "
                       "defect. The ledger then shows a decision with no "
                       "reason, which is its own governance smell."),
        },
        "correct": "approve",
        "why": ("The discipline cuts both ways: a gate must stop unready "
                "work, and it must open for ready work. Here the evidence is "
                "verified, the scope fits, and the Director's own hypothesis "
                "and reasoning are recorded (the learning gate requires that "
                "contribution before the gate opens). Withholding approval "
                "with no named defect records nothing anyone can act on."),
        "rules": ["governance/GATES.md: G2 'which idea advances?' is decided "
                  "by the Director with Co-PIs; the contribution ledger "
                  "records the Director's own hypothesis and reasoning at "
                  "every gate."],
    },
    {
        "id": 4,
        "gate": "G3a",
        "question": "who to contact?",
        "approver": "Director",
        "title": "The contact list nobody checked",
        "situation": (
            "The outreach step produced a list of eight potential "
            "collaborators with names, affiliations, and email addresses. "
            "Spot-checking two of them, one does not appear to exist at the "
            "named institution: the address looks guessed from a name "
            "pattern. The draft invitation emails are otherwise good."),
        "options": {
            "approve": ("Emails go out to guessed addresses. Some bounce; "
                        "one reaches a stranger with a similar name. The "
                        "project's first impression with real collaborators "
                        "is now cleanup."),
            "revise": ("You send the list back for verification: every "
                       "contact confirmed to exist, unverifiable entries "
                       "dropped. The list shrinks to five real people, and "
                       "the drafts go to the Director to send."),
            "reject": ("You discard the whole outreach effort even though "
                       "most entries were verifiable and the drafts were "
                       "sound. Disproportionate to a curable defect."),
        },
        "correct": "revise",
        "why": ("The rule behind G3a is the same one behind citations: never "
                "fabricate, and verify that people exist before anyone is "
                "contacted. The defect is curable, so REVISE, not REJECT. "
                "And whatever the list says, the sending itself stays a "
                "human action."),
        "rules": ["governance/GATES.md: external sends (submit, publish, "
                  "email) are always a human action.",
                  "Cambium's collaborator scouting rule: verify people "
                  "exist; never fabricate names or contacts."],
    },
    {
        "id": 5,
        "gate": "G3",
        "question": "finalize and submit the proposal?",
        "approver": "Director only, plus a second human",
        "title": "Deadline pressure versus unfinished compliance",
        "situation": (
            "The proposal narrative is strong and the deadline is close. "
            "The compliance check shows the data-management plan still "
            "contains template __FILL__ tokens, and the budget "
            "justification cites a fringe rate that appears in no input "
            "document anyone provided. The team asks you to approve now and "
            "patch after submission."),
        "options": {
            "approve": ("A proposal with stub tokens and an unsourced rate "
                        "goes out under your institution's name. If the "
                        "screener catches it, it dies unreviewed; if not, "
                        "you have certified an invented number."),
            "revise": ("You hold the gate: fill the plan, and replace the "
                       "invented rate with the institution's real one or "
                       "remove the line. If the fix cannot land before the "
                       "deadline, the honest outcome is missing this cycle, "
                       "not submitting invented numbers."),
            "reject": ("You abandon a strong proposal over hours of curable "
                       "work. The defect list is short and named; stopping "
                       "the whole effort fixes nothing."),
        },
        "correct": "revise",
        "why": ("Two hard rules bind at G3. Budget figures come only from "
                "provided inputs: a rate that appears in no source is a "
                "fabrication, and the evidence-tier system has no rung for "
                "it. And a document still holding __FILL__ tokens is, by "
                "this repo's own delivery checks, not a filled artifact. "
                "Deadlines do not bend gates; REVISE names the two fixes and "
                "re-presents."),
        "rules": ["governance/GATES.md: G3 'finalize & submit proposal' is "
                  "Director only, and G3 needs the Director plus a second "
                  "human (separation of duties).",
                  "Budget rule: numbers come only from the inputs given; "
                  "figures and rates are never invented.",
                  "Delivery rule: a file containing __FILL__ is a stub, not "
                  "a filled artifact."],
    },
    {
        "id": 6,
        "gate": "G4",
        "question": "accept these results / apply fixes?",
        "approver": "Area Lead for that aim",
        "title": "The headline number nobody reran",
        "situation": (
            "The results memo leads with a 12 percent improvement. In the "
            "findings ledger that claim's evidence tier is Asserted: a "
            "script exists that should reproduce the number, but there is "
            "no record that anyone ran it, and no output hash. Every other "
            "claim in the memo is Code-verified. The team wants the results "
            "accepted today."),
        "options": {
            "approve": ("You accept a memo whose headline is Asserted. If a "
                        "later rerun disagrees, the retraction costs far "
                        "more than the day you saved, and the ledger shows "
                        "you accepted an unverified number."),
            "revise": ("You hold acceptance until verification reruns the "
                       "script and records the command and output hash, "
                       "flipping the claim to Code-verified; if it will not "
                       "reproduce, the memo drops or downgrades the "
                       "headline. Either way the memo ends honest."),
            "reject": ("You throw away a memo whose other claims are all "
                       "Code-verified. Disproportionate: the cure is one "
                       "rerun, not a stopped workstream."),
        },
        "correct": "revise",
        "why": ("The verification protocol is explicit: Code-verified means "
                "a script ran and produced the number, with the command and "
                "output hash recorded; an Asserted claim must be downgraded "
                "or closed before release. The cure exists and is cheap, so "
                "REVISE. REJECT is for results that verification actually "
                "broke; this repo's own ledger records a G4 REJECT doing "
                "exactly that, stopping a run."),
        "rules": ["governance/VERIFICATION_PROTOCOL.md: tiers are Proved / "
                  "Code-verified / Asserted; Asserted must be downgraded or "
                  "closed before release.",
                  "governance/GATES.md: G4 is approved by the Area Lead for "
                  "that aim."],
    },
    {
        "id": 7,
        "gate": "G5",
        "question": "release this report?",
        "approver": "Director or Area Lead",
        "title": "The honest bad-news report",
        "situation": (
            "The quarterly report is ready. Every number traces to the "
            "findings ledger and is Code-verified. One milestone slipped by "
            "six weeks, and the report says so plainly, with the cause and "
            "a revised date. A teammate suggests holding the release until "
            "the slip can be reframed as a scope adjustment."),
        "options": {
            "approve": ("You release the report as written. The funder reads "
                        "an accurate status; the slip is on record with its "
                        "cause and new date; trust survives contact with "
                        "reality."),
            "revise": ("You send an accurate report back to be made less "
                       "accurate. Softening disclosed facts is spin, and "
                       "spin is what this gate exists to catch."),
            "reject": ("You block an accurate report because reality "
                       "underperformed the plan. The team learns that slips "
                       "should be hidden next time, which is how small slips "
                       "become large surprises."),
        },
        "correct": "approve",
        "why": ("G5 asks 'release report?', and the reporting standard here "
                "is honest status, no spin: reports carry only verified "
                "results. The gate guards against overclaiming and unverified "
                "numbers, not against bad news. A Code-verified report that "
                "states a slip plainly is exactly what a healthy release "
                "looks like."),
        "rules": ["governance/GATES.md: G5 'release report' is approved by "
                  "the Director or the Area Lead.",
                  "Reporting standard: honest status, no spin; only verified "
                  "results are reported."],
    },
    {
        "id": 8,
        "gate": "G6",
        "question": "publish / send externally?",
        "approver": "Director only, plus co-authors",
        "title": "One click from an external send",
        "situation": (
            "The paper is ready for submission to a venue. You are the "
            "Director and also the lead author. One co-author has not yet "
            "recorded a decision on the gate, their 'Approved by' line is "
            "empty, and the orchestrator helpfully offers to email the "
            "submission itself the moment you approve."),
        "options": {
            "approve": ("A single-approver external send: as author and sole "
                        "approver you just overrode separation of duties, "
                        "and the machine performed the send. If the "
                        "co-author later objects, the paper is already "
                        "outside."),
            "revise": ("You hold the gate: the missing co-author records "
                       "their decision first, and the send, when it happens, "
                       "is done by a human. Cost: a day or two. The approval "
                       "ledger stays truthful."),
            "reject": ("Nothing is wrong with the paper itself; stopping the "
                       "publication does not fix an approval-process gap, it "
                       "just wastes finished, verified work."),
        },
        "correct": "revise",
        "why": ("Two recorded rules bind at once. Separation of duties: the "
                "author of a deliverable is not its sole approver, and G6 "
                "needs the Director plus a second human (the co-authors), "
                "so the lead author "
                "cannot be the only sign-off; an empty 'Approved by' is NOT "
                "approved. And external sends (submit, publish, email) are "
                "always a human action, never the orchestrator's. Both gaps "
                "are curable, so REVISE."),
        "rules": ["governance/GATES.md: G6 'publish / external send' needs "
                  "the Director plus co-authors; the author is not the sole "
                  "approver; an empty 'Approved by' = NOT approved.",
                  "governance/GATES.md: external sends are always a human "
                  "action."],
    },
]


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

def scenario_header(s):
    return ("=== Scenario %d of %d: %s, %s ===\nGate question: %s (approver: %s)"
            % (s["id"], len(SCENARIOS), s["gate"], s["title"], s["question"],
               s["approver"]))


def print_list():
    print("Gate simulator scenarios (%d). Play one with: "
          "--play N --choose approve|revise|reject" % len(SCENARIOS))
    for s in SCENARIOS:
        print("  %d. [%s] %s" % (s["id"], s["gate"], s["title"]))


def print_scenario(s, show_options=True):
    print(scenario_header(s))
    print()
    print("Situation: %s" % s["situation"])
    if show_options:
        print()
        print("Options: APPROVE (open the gate) | REVISE (send back, "
              "re-present) | REJECT (stop this line of work)")


def evaluate(s, choice):
    print_scenario(s, show_options=False)
    print()
    print("Your choice: %s" % choice.upper())
    print("Consequence: %s" % s["options"][choice])
    print()
    if choice == s["correct"]:
        print("Verdict: correct, this matches the rubric.")
    else:
        print("Verdict: not the rubric answer. Rubric-correct choice: %s."
              % s["correct"].upper())
    print("Why: %s" % s["why"])
    print("Grounding:")
    for rule in s["rules"]:
        print("  - %s" % rule)


def print_quiz(with_key=False):
    print("Gate simulator quiz: decide APPROVE, REVISE, or REJECT for each.")
    print("(No solutions shown here; print the key with --key. "
          "Scenarios are synthetic and generic.)")
    for s in SCENARIOS:
        print()
        print_scenario(s)
    if with_key:
        print()
        print_key()


def print_key():
    print("Answer key (rubric-correct choices):")
    for s in SCENARIOS:
        print("  %d. [%s] %s: %s" % (s["id"], s["gate"], s["title"],
                                     s["correct"].upper()))
    print("Reminder: the rubric encodes governance/GATES.md and "
          "governance/VERIFICATION_PROTOCOL.md as written; re-check if those "
          "files change.")


def run_interactive():  # pragma: no cover (uses input(); skipped in tests)
    print("Cambium gate simulator: %d scenarios. Type approve, revise, "
          "reject, skip, or quit." % len(SCENARIOS))
    score, answered = 0, 0
    for s in SCENARIOS:
        print()
        print_scenario(s)
        while True:
            try:
                raw = input("Your decision> ").strip().lower()
            except EOFError:
                raw = "quit"
            if raw in ("quit", "q"):
                print("Session ended. Score: %d correct of %d answered."
                      % (score, answered))
                return 0
            if raw == "skip":
                break
            if raw in CHOICES:
                answered += 1
                if raw == s["correct"]:
                    score += 1
                print()
                evaluate(s, raw)
                break
            print("Please type approve, revise, reject, skip, or quit.")
    print()
    print("Done. Score: %d correct of %d answered." % (score, answered))
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Practice Cambium's 8-gate discipline on canned scenarios.")
    ap.add_argument("--list", action="store_true", help="list the scenarios")
    ap.add_argument("--play", type=int, metavar="N", help="play scenario N")
    ap.add_argument("--choose", choices=CHOICES,
                    help="your decision for --play (non-interactive)")
    ap.add_argument("--quiz", action="store_true",
                    help="print all scenarios without answers")
    ap.add_argument("--key", action="store_true", help="print the answer key")
    ap.add_argument("--interactive", action="store_true",
                    help="interactive terminal session (uses input())")
    a = ap.parse_args(argv)

    if a.interactive:
        return run_interactive()
    if a.list:
        print_list()
        return 0
    if a.play is not None:
        if not (1 <= a.play <= len(SCENARIOS)):
            print("[gate_simulator] no scenario %s (valid: 1-%d)"
                  % (a.play, len(SCENARIOS)), file=sys.stderr)
            return 1
        s = SCENARIOS[a.play - 1]
        if a.choose:
            evaluate(s, a.choose)
        else:
            print_scenario(s)
            print()
            print("Decide with: --play %d --choose approve|revise|reject" % a.play)
        return 0
    if a.choose:
        print("[gate_simulator] --choose needs --play N", file=sys.stderr)
        return 1
    if a.quiz:
        print_quiz(with_key=a.key)
        return 0
    if a.key:
        print_key()
        return 0
    ap.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
