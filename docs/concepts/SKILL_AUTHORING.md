# Cambium skill-authoring standard

Every strong Cambium skill follows a common anatomy so the institute's skills read consistently and fail
loudly when work is unsound. The structural patterns here (exit criteria, anti-rationalization table, red
flags, routing) are adapted with attribution from addyosmani/agent-skills (MIT); all wording is original
Cambium text. See [/ATTRIBUTION.md](../../ATTRIBUTION.md).

## Two tiers (do not over-apply)

Not every skill needs the full anatomy. Forcing six sections onto a short reference skill turns it into
boilerplate nobody reads.

- **Procedural skills** (a process that produces artifacts: reproducibility, statistics, version-control,
  test-driven-research-code) use the **full anatomy** below.
- **Reference skills** (look-up or knowledge skills: citations, a domain reference) use only the **light
  set**: a trigger-rich description, when-to-use, and red flags.

## The full anatomy (procedural skills)

### Frontmatter `description` (with triggers)
One paragraph: what the skill does, when to use it, and an explicit **Trigger on "…"** clause listing the
literal phrases that should invoke it. End with **Pairs with <council/skill>** so routing is discoverable.

### When to use / when NOT to use
- **Use when:** three to five concrete situations.
- **Do NOT use when:** two to three cases that belong to a sibling skill, and route them there.

### Core process (numbered)
Three to seven numbered, imperative steps, each producing a checkable artifact (a file, a logged value, a
tagged claim), not just advice.

### Anti-rationalization table
Three to four rows. Column 1 is the tempting shortcut ("If you're tempted to…"); column 2 is why it fails
by the field's standard; column 3 is what to do instead.

| If you're tempted to… | Why it fails | Do this instead |
|---|---|---|

### Exit criteria
A checklist that defines done. The skill is complete only when every box is true. Phrase them as verifiable
post-conditions, not intentions.

### Red flags (stop and escalate)
Symptoms that mean the work is unsound, each naming who to route to (a council or sibling skill).

## Credit line
Any skill whose structure was inspired by addyosmani/agent-skills carries a one-line credit in its
description: `Structure adapted from agent-skills (MIT). See /ATTRIBUTION.md.`
