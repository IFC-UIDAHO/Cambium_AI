import { create } from 'zustand'
import { COUNCILS } from '../data/councils.js'
const IDS = COUNCILS.map(c => c.id)

// act: 'cosmos' (opening zoom) -> 'greeter' (alien welcome) -> 'campus' (space university) -> 'done'
export const useScene = create((set) => ({
  act: 'cosmos',
  request: '', kind: '', mode: 'offline',
  active: [], states: {}, phaseLabel: '', ticker: [], gate: null, summary: null,
  alienSays: '', alienAtUser: false,

  setAct: (act) => set({ act }),
  setMode: (mode) => set({ mode }),
  setRequest: (request) => set({ request }),
  alienSpeak: (alienSays, alienAtUser = false) => set({ alienSays, alienAtUser }),
  setActive: (active, kind) => set(s => ({
    active, kind: kind ?? s.kind,
    states: Object.fromEntries(IDS.map(id => [id, id === 'Orchestration' || active.includes(id) ? 'active' : 'dim'])),
  })),
  setState: (id, st) => set(s => ({ states: { ...s.states, [id]: st } })),
  tick: (who, fd, g) => set(s => ({ ticker: [...s.ticker, { who, fd, g, t: Date.now() }].slice(-40) })),
  setPhase: (phaseLabel) => set({ phaseLabel }),
  openGate: (gate) => set({ gate, alienAtUser: true }),
  closeGate: () => set({ gate: null, alienAtUser: false }),
  finish: (summary) => set({ summary, act: 'done' }),
  reset: () => set({ act: 'greeter', active: [], states: {}, ticker: [], gate: null, summary: null, phaseLabel: '', alienSays: 'Welcome back — what shall we work on?', request: '' }),
}))
