# Your first Cambium run — a Director's 30-minute walkthrough

For a new PI (Director) who isn't a developer. By the end you'll have driven the institute through a real
research task and decided at every gate. You don't write code — you decide.

## 0 · One-time setup (≈5 min)
1. Install Cambium (Claude Code/Cowork plugin or GitHub template) — see `INSTALL.md`.
2. Run setup: `python3 tools/new_project.py "my-first-proposal"` (scaffolds the project folders) and, if
   prompted, the **setup** skill fills `config.yml` with your name as Director.
3. Sanity check: `python3 tools/cambium_run.py example` — you'll see the whole institute's plan print with
   **no API key needed**. If you see the phase ladder, you're ready.

## 1 · Start a real run (the one sentence)
Type, in chat: **`/cambium write an NSF proposal on <your topic>`** (or `/cambium run example` to rehearse).
You'll get the **run board** up front — the councils that will work and the gates where you decide.

## 2 · What happens, and what you do
The institute moves through phases; **it stops at each gate and waits for you.** At every gate you'll see a
one-page card (Decision · Where we are · Options · Risks · Evidence · Recommendation) and three choices:

- **APPROVE** — you agree; it continues. *(Tip: a real APPROVE asks for your one-line reasoning — that's the
  Learning Gate. Say why, briefly. A blank approval is blocked on purpose.)*
- **REVISE** — tell it what to change; it redoes that step and returns to the gate.
- **REJECT** — stop here. Nothing ships without you.

Typical gates: **G1** pursue this RFP? · **G2** which idea? · **G3** finalize & submit? (Director-only) ·
**G4** accept the results? · **G5** release the report?

## 3 · The golden rules (so it stays honest)
- **You are accountable, not the AI.** The AI Use Statement says the AI is not an author.
- **Every number is tiered.** "Code-verified" means a script actually ran (see `governance/VERIFICATION_PROTOCOL.md`).
- **Don't rush the gates.** Pace is a feature; the deliberation interval is enforced (`pace_check.py`).
- **Your contribution is recorded.** What you decide and why is logged (`governance/GATES.md`, Contribution Ledger).

## 4 · When you're done
The Support council closes out: records the decision log, refreshes docs, verifies numbers, tidies up. You'll
get a short "what shipped" summary. Then `git add -A && git commit && git push` to save your work.

## Common first-run questions
- **"It answered in plain text with no board."** Re-run `/cambium <task>`; the first action should paint the
  board. If not, tell it "show the run board first."
- **"Do I need an API key?"** Not for the demo/plan. For live agent work, add `ANTHROPIC_API_KEY`.
- **"Can I stop and come back?"** Yes — `pause`/`resume` (handoff). Your run state is saved.
- **"Is my data safe?"** It runs in your own account; regulated/PII data is screened (`data_scan.py`,
  `governance/REGULATED_DATA.md`). You own data governance.

## Where to go next
`USE_CAMBIUM.md` (deeper guide) · `PHILOSOPHY.md` (why) · `VISION.md` + `AI_POLICY.md` (the commitments) ·
`README.md` (full capability catalog).
