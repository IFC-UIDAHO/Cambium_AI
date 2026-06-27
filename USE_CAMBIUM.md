# How to use Cambium — the simple version

*No coding. No jargon. If you can chat, you can run Cambium.*

## The whole idea in one breath
**You talk in plain words. Cambium does the work. It stops and asks you a simple question whenever a real
decision comes up. You answer. Repeat until you're done.** That's it. You are the boss ("the Director"); the
46 helpers do the work; nothing important happens without your "yes".

## How to actually use it (3 things)
1. **Just say what you want, in normal English.** You don't need magic commands.
   - "I have this grant call — should we go for it?" (attach or paste it)
   - "Give me three research ideas and rank them."
   - "Write the first draft of the proposal."
   - "Check these results are solid before I trust them."
2. **Watch for the checkpoint ("gate").** Cambium will stop and show you a **one-page card**:
   *what the decision is · the options · the risks · its recommendation · and APPROVE / REVISE / REJECT.*
3. **Answer with one word.** Reply **approve**, **revise** (say what to change), or **reject**.
   Cambium continues only after you answer. Then you say the next thing you want.

## How to tell Cambium is actually doing it (not just chatting)
When Cambium runs properly, you'll see it **name the team it's using** and **show you a gate card** before
anything is finalized. If you ever just get an answer with no checkpoint, say:
**"run this the Cambium way, with the councils and a gate."**

## A 4-step example (a grant proposal)
1. You: *"Here's a funding call — worth pursuing?"* → Cambium reads it → **card: pursue or skip?** → you: **approve**
2. You: *"Brainstorm ideas and pick the best."* → it ranks ideas → **card: which idea?** → you: **approve B**
3. You: *"Draft the proposal."* → it writes a draft, a reviewer scores it → **card: submit?** → you: **revise the budget**
4. You: *"Now make a short report."* → it writes the report → **card: release?** → you: **approve**
5. You: *"Make a 60-second video abstract of it."* → it plans a video, asks you to set up the video tool (OpenMontage) once, then produces it from your **verified** results → **card: release the video?** → you: **approve**

> **Make a video.** Say *"make a video abstract"*, *"explainer video"*, *"grant pitch video"*, or *"results explainer"* and Cambium mobilizes the Reporting team to produce it — using only facts that were already verified, and stopping for your approval at release. (Needs the free, separately-installed **[OpenMontage](https://github.com/calesthio/OpenMontage)** video tool — see `skills/render-video/PROVISION.md`.)

## Word-decoder (so the docs make sense)
| You'll see… | It just means… |
|---|---|
| **Gate** | a yes/no checkpoint where Cambium waits for you |
| **Council** | a team of helpers (e.g. the "Verification" team double-checks the work) |
| **RFP** | a funding call / request for proposals |
| **Pre-award / Post-award** | before you win the money / after you win it |
| **Ledger** | the running record of what was found and what you approved |
| **Director / PI** | you — the person who decides |

## Solo vs the Cambium way (you choose, every time)
Cambium does **not** take over on its own. For each real task you decide how it runs:

- **Solo** — plain Claude does it directly: fast, no councils, no gate. Good for drafts and quick looks.
- **Cambium way** — the Orchestrator runs the needed councils and **stops at a gate card** for your
  approve / revise / reject. Good for evaluations, decisions, anything you'll trust or submit.

**The smart default:** quick questions and tiny edits just run **Solo** (no interruption). For anything **substantial** — evaluate, analyze, research, write a proposal/report, check results — Cambium **asks you once** which way, then remembers your pick for the session.

Three ways to pick:
1. **Let it ask you.** On a substantial task (evaluate, analyze, research, write a proposal…), Cambium
   pops up a quick **Solo / Cambium-way** choice — just tap one.
2. **Type a command.** `/cambium <what you want>` runs it the Cambium way; `/solo <what you want>` runs
   it plain. Use these when you already know which you want.
3. **Set it once.** Say *"from now on, always the Cambium way"* (or *"stay solo"*) and it sticks for the
   session until you change it.

If you ever get a plain answer with no council named and no gate card, say:
**"run this the Cambium way, with the councils and a gate."**

## The one rule that never changes
Cambium never sends, submits, publishes, or finalizes anything without your approval at a gate.
If you're ever unsure, you can always say **"stop"** or **"explain that simpler."**

## Need a skill for your field? Just ask
Cambium doesn't pre-load thousands of skills. Working on silviculture, wildlife, soil science,
entomology, a web tool, a dashboard — anything? Say *"I'm working on X — what skills would help?"* (or
*"make a skill for X"*). Cambium detects your domain, offers the few skills that actually fit, helps you
**right now** via a faculty expert, and — if you approve — **saves a reusable skill** for next time. You
approve before anything is added; nothing untrusted runs on its own.


## The Learning Gate - your contribution is required, not optional

Every decision gate now carries a **Section 8: Director Contribution**. Before the gate advances you must
write - in your own words - your hypothesis or interpretation for this phase, your reasoning, and your
choice among the options. A blank answer, or one copied verbatim from the AI summary, is flagged and blocks
the gate. This is enforced by `tools/gate.py --require-contribution`, not just by convention, and every
entry is appended to an immutable Contribution Ledger - so the record shows not just that a human was
present, but that a human thought.

**Inline click-to-approve.** In Cowork, each gate renders as a live card - you click APPROVE / REVISE /
REJECT in the card instead of typing. The click runs the same contribution check; nothing bypasses it.
