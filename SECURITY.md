# Security & Responsible Use
- **Never paste secrets, credentials, embargoed, or restricted data** into agents (see AI_GOVERNANCE.md §7-8).
- Agents are **read-only on deliverables** and **cannot send/submit/publish** — humans do that.
- The `examples/demo-mid-project` ledger intentionally contains a leakage bug for the verify board to catch; it is fictional.
- Report a vulnerability or a governance concern by opening a private issue / contacting the maintainer at [your contact].
- Run `python3 governance/validate.py` before any release; an open P0 is a blocker.
