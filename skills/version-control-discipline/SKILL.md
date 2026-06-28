---
name: version-control-discipline
description: Keep research code and results traceable through git with atomic commits, meaningful messages, tagged result-producing commits, and never committing large data or secrets. Use when starting a repo, before a result is reported, or when history is messy. Trigger on "commit", "git history", "tag the run", "what commit produced this". Pairs with reproducibility and research-engineer. Structure adapted from agent-skills (MIT). See /ATTRIBUTION.md.
---
# Version-control discipline

## When to use
Any repository whose outputs will be reported or handed off.

## Core process
1. One logical change per commit; the message states why, not just what.
2. Tag the exact commit that produced each reported figure or table (`git tag result-<id>`).
3. Keep data and secrets out of git: use `.gitignore`, a fetch script, and a checksum.
4. Before reporting a number, confirm the working tree is clean and record the commit hash next to it.

## Anti-rationalization table
| If you're tempted to… | Why it fails | Do this instead |
|---|---|---|
| "I'll squash later, just commit everything now" | A giant commit hides which change moved a metric | Commit one logical change at a time |
| "the data is small, just commit it" | History bloats and you can leak something you can't remove | Gitignore data; fetch + checksum it |

## Exit criteria
- [ ] Every headline result traces to a tagged, clean commit hash.
- [ ] No data or secrets in history; large inputs are fetched and checksummed.

## Red flags
- A reported number with no commit hash beside it. Stop and record it.
- A dirty working tree at report time. Commit or stash before you cite the result.
