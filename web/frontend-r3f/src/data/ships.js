import { Vector3 } from 'three'
import { COUNCILS } from './councils.js'
// docked ring positions around the central station; each council = one ship.
export const DOCKS = (() => {
  const orbit = COUNCILS.filter(c => !c.hero); const n = orbit.length; const out = {}
  orbit.forEach((c, k) => {
    const a = (k / n) * Math.PI * 2
    out[c.id] = new Vector3(Math.cos(a) * 12, Math.sin(a * 2) * 2.5, Math.sin(a) * 12)
  })
  return out
})()
