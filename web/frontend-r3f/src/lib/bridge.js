// Connects the scene to the Cambium bridge (web/server). Falls back to a local sim when no server.
import { useScene } from '../state/sceneStore.js'
import { COUNCILS } from '../data/councils.js'
const API = new URLSearchParams(location.search).get('api') || 'http://127.0.0.1:8000'
let WS = null, RUN = null

export async function probe() {
  try { const j = await (await fetch(API + '/api/health')).json(); useScene.getState().setMode(j.mode); return j.mode }
  catch { useScene.getState().setMode('offline'); return 'offline' }
}

export async function enter(task) {
  const S = useScene.getState()
  S.setRequest(task); S.setAct('campus')
  if (S.mode === 'offline') return localSim(task)
  try {
    const j = await (await fetch(API + '/api/run', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ task }) })).json()
    RUN = j.run_id; S.setActive(j.plan.active, j.plan.kind); openStream(j.run_id)
  } catch { useScene.setState({ mode:'offline' }); localSim(task) }
}
function openStream(id) {
  WS = new WebSocket(API.replace(/^http/, 'ws') + '/api/stream/' + id)
  WS.onmessage = (m) => handle(JSON.parse(m.data))
}
function handle(ev) {
  const S = useScene.getState()
  if (ev.type === 'run.started') { S.setActive(ev.active, ev.kind); S.tick('⬢ Orchestration', 'The President wakes ' + (ev.active.length - 1) + ' of 11 councils.') }
  else if (ev.type === 'orchestrator') S.tick('⬢ Orchestration', ev.text)
  else if (ev.type === 'phase.start') { S.setPhase('Phase ' + (ev.index + 1) + ' · ' + ev.label); ev.councils.forEach(c => S.setState(c, 'work')); S.tick('⬢ ' + ev.label, '') }
  else if (ev.type === 'agent.finding') S.tick(ev.council + ' · ' + ev.role, ev.finding)
  else if (ev.type === 'phase.done') {}
  else if (ev.type === 'gate.open') { S.openGate({ id: ev.gate_id, q: ev.question, d: ev.detail }); S.tick('⛩ ' + ev.gate_id, 'Paused for your decision.', 'g') }
  else if (ev.type === 'gate.decided') { Object.entries(S.states).forEach(([k, v]) => { if (v === 'work') S.setState(k, 'active') }); S.tick('⛩ ' + ev.gate_id, 'You chose ' + ev.decision + '.', 'g') }
  else if (ev.type === 'run.done') S.finish({ ...ev.summary, rejected: ev.rejected })
}
export async function decide(d) {
  const S = useScene.getState(); S.closeGate()
  if (S.mode === 'offline') return localDecide(d)
  try { await fetch(API + '/api/gate/' + RUN + '/decide', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ decision: d }) }) }
  catch { S.tick('connection', 'decide failed') }
}
export function restart() { if (WS) try { WS.close() } catch {} useScene.getState().reset() }

// ---- offline local preview (no server) ----
let SP = null, SI = 0
function route(t) { t = t.toLowerCase(); const g = a => a.some(x => t.includes(x))
  const kind = g(['proposal','grant','rfp','nsf','funding']) ? 'grant' : g(['report','quarterly','progress']) ? 'report' : g(['verify','review','audit','check','clean']) ? 'review' : 'research'
  const P = { grant:[['Scouts','Pre-Award','G1'],['Faculty','Labs','G2'],['Pre-Award','Governance','G3'],['Support',null,null]],
    report:[['Support','Scouts',null],['Reporting','Governance','G5'],['Support',null,null]],
    review:[['Execution','Support',null],['Verification','Governance','G4'],['Support',null,null]],
    research:[['Scouts','Faculty','G1'],['Labs','Faculty','G2'],['Execution','Labs',null],['Verification','Governance','G4'],['Reporting','Support','G5'],['Support',null,null]] }[kind]
  const act = ['Orchestration']; P.forEach(p => [p[0],p[1]].forEach(c => c && !act.includes(c) && act.push(c)))
  return { kind, phases: P, active: act } }
const GQ = { G1:['Pursue this direction?',"Worth the institute's effort?"], G2:['Which idea advances?','Pick the cleanest approach.'], G3:['Finalize & submit?','Director-only. Nothing submits without you.'], G4:['Accept the results?','Evidence-tiered verdict.'], G5:['Release the report?','Your release decision.'] }
const ROLE = Object.fromEntries(COUNCILS.map(c => [c.id, c.role]))
function localSim(v) { const S = useScene.getState(); SP = route(v); SI = 0; SP.task = v; SP.gates = []
  S.setActive(SP.active, SP.kind); S.tick('⬢ Orchestration', 'The President wakes ' + (SP.active.length - 1) + ' of 11 councils.'); setTimeout(simPhase, 900) }
function simPhase() { const S = useScene.getState()
  if (SI >= SP.phases.length) return S.finish({ task: SP.task, kind: SP.kind, councils: SP.active.length - 1, gates: SP.gates, revises: 0, rejected: false })
  const ph = SP.phases[SI], cs = [ph[0], ph[1]].filter(Boolean); S.setPhase('Phase ' + (SI + 1)); cs.forEach(c => S.setState(c, 'work'))
  let i = 0; (function step() { if (i < cs.length) { S.tick(cs[i], ROLE[cs[i]]); i++; setTimeout(step, 650) }
    else { cs.forEach(c => S.setState(c, 'active')); ph[2] ? setTimeout(() => S.openGate({ id: ph[2], q: GQ[ph[2]][0], d: GQ[ph[2]][1] }), 500) : (SI++, setTimeout(simPhase, 700)) } })() }
function localDecide(d) { const S = useScene.getState(); const ph = SP.phases[SI]; SP.gates.push({ gate: ph[2], decision: d })
  ;[ph[0], ph[1]].filter(Boolean).forEach(c => S.setState(c, 'active'))
  if (d === 'REJECT') return S.finish({ task: SP.task, kind: SP.kind, councils: SP.active.length - 1, gates: SP.gates, revises: 0, rejected: true }); SI++; setTimeout(simPhase, 500) }
