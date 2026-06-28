# Cambium Web App — bridge server + reference front-end

This is the **production path** for a real Cambium web app: an elegant front-end where users work, with the
Cambium institute running on a server behind it. Three tiers:

```
①  web/frontend/index.html      simple CSS-3D institute (renders anywhere, incl. the Cowork artifact)
①b web/frontend/cinematic.html  REAL WebGL/Three.js institute (single-file, floating crystals + bloom)
①c web/frontend-r3f/             R3F narrative (alien greeter + cosmos zoom + space-university ships + gates);
                                npm run dev — drop .glb models per web/frontend-r3f/ASSETS.md; story in web/STORYBOARD.md
②  web/server/  (FastAPI)     the BRIDGE — REST + WebSocket; wraps Cambium + the Claude Agent SDK
③  tools/ (this repo)         the ENGINE — router, councils, gates, gate_lock, audit, enforce
```

## Run it locally (2 minutes)

```bash
pip install -r web/server/requirements.txt
uvicorn web.server.app:app --reload --port 8000        # from the repo root
# then open web/frontend/index.html in a browser (it defaults to http://127.0.0.1:8000)
```

The front-end pings `/api/health`: **server up** → it drives a real run over WebSocket; **server down** →
it falls back to a local preview so it always renders.

- **Simulation mode** (default, no key): scripts believable council findings — perfect for demos.
- **Live mode**: set `CAMBIUM_LIVE=1` and `ANTHROPIC_API_KEY`, then wire `Run.run_agent_live()` in
  `web/server/engine.py` to the Claude Agent SDK. That seam is the only thing between this and real agents.

## Point a custom / Lovable front-end at it
Build your UI anywhere, then call the API in `web/API.md`:
1. `POST /api/run` with the user's request → get `run_id` + `plan` (which councils light up).
2. Open `ws://…/api/stream/{run_id}` → render `phase.start` / `agent.finding` / `gate.open`.
3. On a gate, show APPROVE/REVISE/REJECT → `POST /api/gate/{run_id}/decide`.

**Lovable prompt starter:** *"Build a dark, gold-accented 3D institute landing page. A text box posts the
request to `POST {API}/api/run`, then opens a WebSocket to `{API}/api/stream/{run_id}`. Render each council
as a building that glows when it appears in a `phase.start` event and shows findings from `agent.finding`.
On a `gate.open` event, show a modal with APPROVE / REVISE / REJECT that POSTs to
`/api/gate/{run_id}/decide`."*

## Deploy
- **Bridge:** any container host — Railway, Render, Fly.io (`Dockerfile` included). Set `ANTHROPIC_API_KEY`
  (and `CAMBIUM_LIVE=1`) as secrets. Put it behind auth (Clerk/Auth0) and a DB (Supabase) for real users —
  see the Stage-2 items in `ROADMAP.md`.
- **Front-end:** Vercel/Netlify; point it at the bridge with `?api=https://your-bridge.example.com`.

## Honest status
The bridge + streaming + gate pause/resume are real and tested. The **live-agent seam** and **auth/DB/
multi-tenancy** are the remaining production work (named, not hidden — `REVIEW_RESPONSE2.md`, `ROADMAP.md`).
