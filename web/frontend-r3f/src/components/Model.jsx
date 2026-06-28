import { useState, useEffect, useMemo, Suspense } from 'react'
import { useGLTF } from '@react-three/drei'
import { Box3, Vector3 } from 'three'

// Auto-loads a .glb if it exists, auto-fits it to a target size (so any model is the right scale),
// and falls back to a placeholder when the file isn't there yet. Drop a model in /public and it appears.
function Gltf({ url, targetSize = 2, spin = false, ...props }) {
  const { scene } = useGLTF(url)
  const obj = useMemo(() => {
    const s = scene.clone(true)
    const box = new Box3().setFromObject(s)
    const size = box.getSize(new Vector3())
    const maxDim = Math.max(size.x, size.y, size.z) || 1
    const k = targetSize / maxDim
    s.scale.setScalar(k)
    const center = box.getCenter(new Vector3()).multiplyScalar(k)
    s.position.sub(center)                 // recenter at origin
    return s
  }, [scene, targetSize])
  return <primitive object={obj} {...props} />
}

export default function Model({ url, fallback = null, ...props }) {
  const [ok, setOk] = useState(null)
  useEffect(() => {
    let alive = true
    fetch(url, { method: 'HEAD' }).then(r => alive && setOk(r.ok)).catch(() => alive && setOk(false))
    return () => { alive = false }
  }, [url])
  if (ok !== true) return fallback              // checking or missing -> placeholder
  return <Suspense fallback={fallback}><Gltf url={url} {...props} /></Suspense>
}
