# Close-out checklist (Support council — run after EVERY change)

> The institute must learn from what just happened and propagate it everywhere. Act IV is NOT "append a
> CHANGELOG line" — it is the Support council dispatched to refresh the whole memory. `tools/closeout.py`
> mechanically fails close-out if the forward docs drifted behind the code.

| Owner (Support) | Refresh |
|---|---|
| Record-Keeper | `CHANGELOG.md` entry · `DECISIONS.md` ADR (if architectural) · `governance/GATES.md` (if a gate) |
| Outreach | `README.md` (counts + the roadmap paragraph) · `ROADMAP.md` (+ bump `Last updated:`) · `USE_CAMBIUM.md` / `FAQ.md` / `COMPARISON.md` if user-facing |
| Integrity-Officer | `POSITIONING.md` / `PHILOSOPHY.md` if any claim/grade moved · no overclaim · run `consistency_check` + `doctor` + `pytest` |
| Janitor | stray files, gitignore, doc drift (`tools/closeout.py`) |

Then: `python3 tools/closeout.py` must exit 0 before close-out is declared done.
