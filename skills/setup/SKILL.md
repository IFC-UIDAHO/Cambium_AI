---
name: setup
description: First-run setup for a Cambium project — detect a missing config.yml, scaffold it from config.example.yml, and fill in the Director and project name. Use when the user says "set up Cambium", "configure the institute", "first-time setup", "create my config", "who's the director", "onboard my lab", or when any Cambium run can't find config.yml. Guides a non-terminal Cowork user through the minimum needed to run. Never overwrites an existing config.yml without explicit confirmation.
---

# Setup — get a project ready to run

Make a new Cambium project runnable with the fewest questions. Do not start research here; just
establish the config.

## Run it
1. **Check for `config.yml`** at the repo root (Read it / list the directory).
   - If it **exists**, confirm the Director and project name back to the user and stop — setup is
     already done. Offer to edit only if they ask.
   - If it is **missing**, continue.
2. **Scaffold** by copying `config.example.yml` → `config.yml` (Bash: `cp config.example.yml config.yml`,
   or write the file from the example's contents if no shell). Never clobber an existing `config.yml`.
3. **Ask only the essentials** (one short prompt, not a survey):
   - **Director (PI / lab head)** — the accountable human who approves the top gates.
   - **Project name / slug** — what this project is called.
   Optionally: any Co-PIs and which Aims they own (this sets the delegated gate approvers).
4. **Write those answers into `config.yml`** (`institute.director`, the project name, and any team
   entries). Leave the rest of the example defaults in place.
5. **Confirm** the resulting Director + gate-approver map back to the user, and point them at the next
   step: `rfp-intake` (pre-award) or `run-lab` (post-award).

## Guardrails
- The Director set here is the human-in-the-loop who approves submit/publish/budget gates — make sure
  it is a real person, not an agent.
- If `config.example.yml` is absent, say so rather than inventing a schema.
