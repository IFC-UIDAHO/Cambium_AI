"""Cambium Bridge API — the server a web front-end calls to drive a real Cambium run.

Endpoints (full OpenAPI at /docs):
  GET  /api/health
  POST /api/run                      {task}              -> {run_id, plan}
  WS   /api/stream/{run_id}                              -> event stream (phase/agent/gate/done)
  POST /api/gate/{run_id}/decide     {decision}          -> {ok}   (APPROVE | REVISE | REJECT)

Run it:  uvicorn web.server.app:app --reload --port 8000   (from the repo root)
The front-end (web/frontend/index.html) connects to this; so can any Lovable/Stitch app — see web/API.md.
"""
import asyncio, os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import engine

app = FastAPI(title="Cambium Bridge API", version="1.0.0",
              description="Drive a real, gated Cambium institute run from a web front-end.")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class RunReq(BaseModel):
    task: str

class GateReq(BaseModel):
    decision: str   # APPROVE | REVISE | REJECT
    contribution: str | None = None

@app.get("/api/health")
def health():
    return {"ok": True, "mode": "live" if (os.environ.get("CAMBIUM_LIVE") == "1" and os.environ.get("ANTHROPIC_API_KEY")) else "simulation",
            "active_runs": len(engine.RUNS)}

@app.post("/api/run")
async def start_run(req: RunReq):
    if not req.task.strip():
        raise HTTPException(400, "task is required")
    r = engine.create_run(req.task.strip())
    asyncio.create_task(r.drive())   # background loop; events drain over the WebSocket
    return {"run_id": r.id, "plan": r.plan}

@app.post("/api/gate/{run_id}/decide")
async def decide(run_id: str, req: GateReq):
    r = engine.get_run(run_id)
    if not r:
        raise HTTPException(404, "no such run")
    if req.decision not in ("APPROVE", "REVISE", "REJECT"):
        raise HTTPException(400, "decision must be APPROVE, REVISE or REJECT")
    r.decide(req.decision)
    return {"ok": True, "run_id": run_id, "decision": req.decision}

@app.websocket("/api/stream/{run_id}")
async def stream(ws: WebSocket, run_id: str):
    await ws.accept()
    r = engine.get_run(run_id)
    if not r:
        await ws.send_json({"type": "error", "message": "no such run"}); await ws.close(); return
    try:
        while True:
            ev = await r.queue.get()
            if ev is None:
                break
            await ws.send_json(ev)
    except WebSocketDisconnect:
        pass
    finally:
        try: await ws.close()
        except Exception: pass

@app.get("/")
def root():
    return JSONResponse({"service": "Cambium Bridge API", "docs": "/docs", "health": "/api/health"})
