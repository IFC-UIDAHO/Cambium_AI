# Cambium Bridge API — contract

The bridge turns a research request into a streamed, **gated** Cambium run a web front-end can drive.
Base URL example: `http://localhost:8000`. Interactive OpenAPI: **`/docs`**.

## REST

### `GET /api/health`
→ `{ "ok": true, "mode": "simulation" | "live", "active_runs": 0 }`
`mode` is `live` only when `CAMBIUM_LIVE=1` **and** `ANTHROPIC_API_KEY` are set on the server.

### `POST /api/run`
Body `{ "task": "write an NSF proposal on wildfire recovery" }`
→ `{ "run_id": "abc123", "plan": { "kind": "grant", "active": ["Orchestration","Pre-Award",…],
       "phases": [ { "label": "...", "councils": [...], "agents": [...], "gate": {"id":"G1","question":"…","detail":"…"} | null } ] } }`
Starts the run in the background; events stream over the WebSocket below.

### `POST /api/gate/{run_id}/decide`
Body `{ "decision": "APPROVE" | "REVISE" | "REJECT", "contribution": "optional rationale" }`
→ `{ "ok": true }`. This is the human-in-the-loop step — the run is **paused** until it arrives.
`APPROVE` advances · `REVISE` re-runs the phase and returns to the gate · `REJECT` ends the run.

## WebSocket — `GET /api/stream/{run_id}`
Emits JSON events (drive the 3D campus from these):

| event | fields | render |
|---|---|---|
| `run.started` | `kind, active[], phases[]` | light `active` councils, dim the rest |
| `orchestrator` | `text` | President narration |
| `phase.start` | `index, label, councils[]` | set `councils` to "working", draw flow lines |
| `agent.finding` | `council, role, finding` | append to the behind-the-scenes ticker |
| `phase.done` | `index` | mark councils done, clear flow |
| `gate.open` | `gate_id, question, detail` | **show the gate modal and wait** |
| `gate.decided` | `gate_id, decision` | record the decision, continue |
| `run.done` | `rejected, summary{task,kind,councils,gates[],revises}` | show the close-out |

## The loop (what makes it feel alive)
`POST /run` → stream `phase`/`agent` events → `gate.open` (run pauses) → user clicks → `POST /decide` →
`gate.decided` → next phase → `run.done`. Same human-gate contract as the CLI's `--resume` + `gate_lock`.
