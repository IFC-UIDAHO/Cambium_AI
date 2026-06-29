# Contributing to Cambium

Thank you for helping make Cambium a top-1% research tool. This document explains how to contribute effectively.

## Table of Contents

- [Working Together (read this first)](#working-together-read-this-first)
- [Quick Start](#quick-start)
- [Development Environment](#development-environment)
- [How to Contribute](#how-to-contribute)
- [Agent Guidelines](#agent-guidelines)
- [Code Standards](#code-standards)
- [Pull Request Process](#pull-request-process)
- [Issue Reporting](#issue-reporting)
- [License](#license)

---

## Working Together (read this first)

If two people both commit straight to `main`, you get the exact mess this project already hit once: two sets of changes land in the same files, the push gets rejected, and someone untangles it by hand. One rule prevents it.

Nobody commits directly to `main`. Each person works on their own branch and merges through a pull request.

```bash
# 1. Start from the latest main
git checkout main
git pull origin main

# 2. Branch for your work, named after what you are doing
git checkout -b academy-expansion        # or security-fixes, readme-rewrite, etc.

# 3. Work, committing as you go
git add -A
git commit -m "clear message about what changed"

# 4. Sync with main again before the PR, so you resolve any overlap on your side
git pull origin main --rebase

# 5. Push the branch and open a pull request
git push origin academy-expansion
```

Open the PR, let CI run, merge once it is green. Because the merge happens in a PR, overlaps show up as visible conflicts instead of silently overwriting each other on `main`.

One Cambium-specific warning: if you run anything that auto-commits to `main` on a timer (a "save" task, for example), turn it off or point it at a branch. Timed auto-commits to `main` are how half-finished work slipped in last time.

---

## Quick Start

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/Cambium_AI.git`
3. Install dependencies: `pip install -r requirements.txt`
4. Run tests: `pytest`
5. Make your changes
6. Run tests again: `pytest`
7. Submit a PR

---

## Development Environment

### Requirements

- Python 3.10+
- Git
- (Optional) Node.js 18+ if working on the web frontend

### Setup

```bash
# Clone
git clone https://github.com/IFC-UIDAHO/Cambium_AI.git
cd Cambium_AI

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Verify setup
pytest
python tools/doctor.py --grade
```

### Running the web bridge locally

```bash
# Terminal 1: start the server
cd web/server
uvicorn app:app --reload --port 8000

# Terminal 2: serve the frontend
# Option A: open academy/index.html directly in browser
# Option B: use a local server
python -m http.server 8080
# Then open http://localhost:8080/academy/index.html
```

---

## How to Contribute

### Areas where help is especially welcome

| Area | What we need | Skill level |
|------|-------------|-------------|
| **New agents** | Domain-specific specialists (e.g., hydrology, genomics, economics) | Intermediate |
| **Academy courses** | New lessons, especially Practitioner and Expert tier | Any |
| **Security** | Penetration testing, vulnerability reports | Advanced |
| **Accessibility** | WCAG compliance, screen-reader testing | Intermediate |
| **Translations** | Multi-language support for the Academy | Any |
| **Documentation** | Tutorials, case studies, video guides | Any |
| **Tests** | Expand test coverage | Intermediate |

### What we do NOT need

- Agents that do not follow the output contract (severity + evidence tier)
- Fabricated citations or benchmarks
- Claims that exceed their evidence tier
- Solutions that remove human gates

---

## Agent Guidelines

Agents are Cambium's specialists. Every agent must:

1. **Have a single job** — one lane, one responsibility
2. **Use YAML frontmatter** with `name`, `description`, `model`, `tools`
3. **Follow the OUTPUT CONTRACT** — every finding must have `severity` (P0/P1/P2) and `evidence_tier` (Proved/Code-verified/Asserted/Open)
4. **Be testable** — include a test in `tests/test_agent_*.py` or explain why not
5. **Live in `.claude/agents/`** — the canonical source (mirrored to `agents/` by `tools/sync_plugin_agents.py`)

### Agent template

```markdown
---
name: my-agent
description: What this agent does in one sentence.
model: sonnet
tools: read, write, search
---

# My Agent

## Job

[Single-sentence description]

## Output Contract

- severity: P0/P1/P2
- evidence_tier: Proved / Code-verified / Asserted / Open

## Example

[Worked example]
```

---

## Code Standards

### Python

- Follow PEP 8
- Use type hints where practical
- Write docstrings for public functions
- Keep functions under 50 lines when possible
- No `print()` for debugging; use `logging`

### JavaScript/HTML

- Use semantic HTML (`<section>`, `<article>`, `<nav>`)
- Add `aria-label` and `aria-describedby` for interactive elements
- Never use `innerHTML` with user input (use `textContent` or sanitize)
- Support keyboard navigation (`Tab`, `Enter`, `Escape`)

### Security

- No hardcoded secrets (use environment variables)
- No `allow_origins=["*"]` in CORS (use `CAMBIUM_CORS_ORIGINS`)
- Validate all user inputs
- Use parameterized queries or list arguments for subprocess

---

## Pull Request Process

1. **Open an issue first** for anything large (new agent, new feature, breaking change)
2. **Create a branch** from `main`: `git checkout -b feature/my-feature`
3. **Write tests** for new functionality
4. **Run the full test suite**: `pytest`
5. **Run the doctor**: `python tools/doctor.py --grade`
6. **Sync agents** if you modified `.claude/agents/`: `python tools/sync_plugin_agents.py`
7. **Update CHANGELOG.md** under `## [Unreleased]`
8. **Submit PR** with a clear description:
   - What changed
   - Why it changed
   - How to test it
   - Any breaking changes

### PR checklist

- [ ] Branched off `main` and ran `git pull origin main --rebase` before opening this PR
- [ ] Tests pass (`pytest`)
- [ ] Ran `python3 tools/gen_dashboard.py` (dashboard test count current) and `python3 tools/gen_readme.py` if counts changed
- [ ] Doctor passes (`python tools/doctor.py`)
- [ ] Agent sync passes (`python tools/sync_plugin_agents.py`) if agents changed
- [ ] No hardcoded secrets, and no em dashes in prose or generated assets
- [ ] Documentation updated if user-facing
- [ ] CHANGELOG.md updated

---

## Issue Reporting

### Bug reports

Use the bug report template (if available) or include:

1. **What you expected to happen**
2. **What actually happened**
3. **Steps to reproduce**
4. **Environment**: OS, Python version, browser (if UI)
5. **Error message or screenshot**

### Feature requests

1. **What problem does this solve?**
2. **Who is it for?** (students, faculty, PIs, administrators)
3. **How would it work?**
4. **Have you tried workarounds?**

### Security vulnerabilities

**DO NOT open a public issue.** Email the maintainer directly or use GitHub's private vulnerability reporting.

---

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

## Questions?

- Open a [Discussion](https://github.com/IFC-UIDAHO/Cambium_AI/discussions) for questions
- Open an [Issue](https://github.com/IFC-UIDAHO/Cambium_AI/issues) for bugs
- Email: pkjaslamagrico@gmail.com (maintainer)

**Thank you for making Cambium better.**
