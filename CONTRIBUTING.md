# Contributing

Thanks for improving the Cambium! Ways to help:

- **New faculty disciplines** - none needed in code (the faculty agent is parameterized); add a row to
  `FACULTY_ROSTER.md` if it's a common chair.
- **New agents** - add a `.claude/agents/NN-name.md` with YAML front matter (`name`, `description`,
  `model`, `tools`) and the five-field OUTPUT CONTRACT in the body. Keep it one lane, one job.
- **Domain packs** - a `packs/<field>/` with example faculty prompts, datasets-schema notes, and a
  demo project. PRs welcome.
- **Model profiles** - tune `config.yml` profiles; justify with a cost/quality note.

Rules: agents are read-only on the deliverable; only the Document Office writes it, post-approval, from
verified findings. Never add fabricated citations or benchmarks. Keep claims at their evidence tier.

Open an issue first for anything large. By contributing you agree to the MIT license.
