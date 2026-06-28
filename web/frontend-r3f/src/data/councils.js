// 11 councils on a golden-spiral sphere; Orchestration is the hero core (no orbit position).
export const PALETTE = { bg:'#03100a', gold:'#e7c878', lime:'#b7f36a', emer:'#16c079' }
export const COUNCILS = [
  { id:'Orchestration', color:'#e7c878', role:"President · routes & holds gates", hero:true },
  { id:'Pre-Award',     color:'#2bb8c4', role:'finds & wins funding' },
  { id:'Scouts',        color:'#19c0a6', role:'maps the landscape' },
  { id:'Faculty',       color:'#ff7aa8', role:'domain expertise' },
  { id:'Labs',          color:'#4f8cff', role:'designs the method' },
  { id:'Partnerships',  color:'#37c97e', role:'builds the team' },
  { id:'Execution',     color:'#ff9c4a', role:'runs experiments' },
  { id:'Verification',  color:'#9b8cff', role:'re-runs the numbers' },
  { id:'Governance',    color:'#e5564a', role:'ethics & compliance' },
  { id:'Reporting',     color:'#b7f36a', role:'writes the report' },
  { id:'Support',       color:'#16c079', role:'records & tidies' },
]
import { Vector3 } from 'three'
const R = 11
export const POSITIONS = (() => {
  const orbit = COUNCILS.filter(c => !c.hero); const n = orbit.length; const out = {}
  orbit.forEach((c, k) => {
    const y = 1 - (k / (n - 1)) * 2, rad = Math.sqrt(1 - y * y), th = k * 2.399963
    out[c.id] = new Vector3(Math.cos(th) * rad * R, y * 8.5, Math.sin(th) * rad * R)
  })
  out['Orchestration'] = new Vector3(0, 0, 0)
  return out
})()
