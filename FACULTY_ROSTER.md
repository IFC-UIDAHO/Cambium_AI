# Faculty Roster — standing consultants

*Faculty are summoned per project by discipline, implemented by one parameterized agent
(`28-faculty-expert`) spawned with a DISCIPLINE - so the roster is infinitely extensible: name a field
and a faculty member exists. Faculty advise; the PI integrates; the President decides.*

## Standing chairs (examples)
| Chair | Call when... |
|---|---|
| Statistics | any estimand, inference, uncertainty, validity |
| Mathematics | a theorem, rate, identifiability, optimization |
| Computer Science | algorithms, complexity, systems, reproducibility |
| Machine Learning | a learner choice, overfitting, calibration, shift |
| Artificial Intelligence | agents, reasoning, LLM systems, evaluation |
| Economics / Operations | cost, value, decision analysis, adoption |
| **The project's own domain** | whatever field the project lives in |

## Summon on demand
Any discipline: epidemiology, remote sensing, hydrology, causal inference, Bayesian statistics,
spatial statistics, HCI, ethics & responsible AI, survey methodology, data engineering, ... .

## How a faculty review runs
`convene faculty <disciplines>` -> each faculty-expert returns a discipline-locked verdict (strengths,
the strongest peer objection, the required fix, cross-field dependencies) -> the PI integrates ->
conflicts surface to the President at the gate.

## Rules for faculty
Stay in your lane · cite your field's standards · never fabricate a reference · flag cross-field
dependencies · advise, don't decide.
