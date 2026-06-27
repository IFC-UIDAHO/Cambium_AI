---
name: skill-provisioner
description: Grow Cambium's skills on demand instead of pre-stocking thousands. Use when a request needs domain expertise or a capability NOT already covered by an installed skill — e.g. silviculture, wildlife, soil science, entomology, plant pathology, geospatial, a specific engineering or web-tooling task — or when the user says "add a skill for X", "what skills do I need", "can you make a skill for my study". Detects the domain from the user's words, offers the few skills that actually help, then (on approval) helps immediately via faculty-expert AND writes a reusable SKILL.md. Pairs with toolsmith (install existing), skill-creator (author new), faculty-expert (instant expertise).
---

# Skill provisioner — the right skills, on demand

Cambium does **not** ship a skill for every field. That would be unmaintainable bloat and a security
risk. Instead, this skill detects what *this* user needs and provisions only that — vetted, approved,
and tailored to their study.

## When to act
Trigger when a request leans on a domain or capability with **no matching installed skill** (check the
installed skills first), or when the user explicitly asks to add/create a skill. Do **not** trigger when
an existing skill already covers it (e.g. stats → `statistics`, modeling → `machine-learning`, UI →
`ui-ux-pro-max`). Offer **once** per new domain, then proceed — no nagging.

## The flow

**1. Detect the domain.** Pull the field + capability keywords from the request.
*"write a silviculture prescription"* → forestry / silviculture + prescription-writing.
*"classify wildlife camera-trap images"* → wildlife ecology + image classification (→ existing
`machine-learning`) + a domain layer.

**2. Clarify only if ambiguous (1–2 short questions max).** Sub-field, the specific deliverable, the
study system, region/standards. Skip if the request is already clear.

**3. Offer two short lists** (keep each to the few that truly help — not a catalog):

> **Available now** (install/curate via toolsmith): existing skills/plugins/MCPs that fit.
> **Can create for you** (new, via skill-creator): proposed custom SKILL.md(s), each with one line on
> why it helps *your* study and what it would contain.

Present them and ask which to add — APPROVE the subset / REVISE / SKIP.

**4. Deliver both tiers** on approval:
- **Now (instant):** invoke `faculty-expert` with the discipline so the user gets expert help this
  session — no waiting on a file. This always works, even before any skill is registered.
- **Persistent (reusable):** author the approved skill(s) into the **Cambium repo** as
  `skills/<name>/SKILL.md` — this is the single, version-controlled, CI-checked home (use skill-creator
  patterns: tight trigger description, clear workflow, domain guardrails). Install approved existing ones
  via toolsmith. The repo copy is always canonical.

**5. State the loading reality honestly, and offer a fast path — never auto.** A newly written skill
becomes a *registered* skill only after the plugin reloads/re-installs. Say so: "I've helped you now via
the faculty expert; the saved skill goes live next session / after you reinstall or sync." Never imply a
just-created file is already auto-loaded.

   Then **offer** (do not perform automatically) a one-step **"activate it locally now"**: only on an
   explicit per-skill yes, also place that single skill where it registers after a reload — the active
   project's `.claude/skills/` if present, else the user's personal skills folder. Never write to a
   personal/global skills location silently, automatically, or in bulk; each local activation is one
   deliberate, approved action. The repo copy stays the source of truth (ADR-020).

## Authoring a good custom skill (skill-creator essentials)
- **Frontmatter:** `name` (kebab-case, matches folder) + a `description` that names concrete trigger
  phrases and what it does (this is what makes it fire later).
- **Body:** a short workflow, the key tools/libraries with `pip`/CLI lines, domain-specific guardrails,
  and an honesty rule (cite real sources, tag claims, state assumptions).
- Keep it focused on one capability; one skill, one job.

## Guardrails
- **Reuse beats rebuild:** always check installed + marketplace skills before proposing to build.
- **Offer few, relevant skills** — resist listing dozens; this is curation, not a dump.
- **Approval before install or persist:** toolsmith installs only after the human says yes; never run
  untrusted code automatically.
- **Repo is canonical; local activation is opt-in.** Default-write to the governed repo `skills/`;
  only copy a skill into a personal/project skills folder on explicit per-skill approval (never auto).
- **No fabricated capability:** if a domain needs real tools/data you don't have, say so rather than
  fake a skill that can't deliver.
