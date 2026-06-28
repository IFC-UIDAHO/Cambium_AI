import { useRef } from 'react'
import { useFrame, useThree } from '@react-three/fiber'
import { Stars, Sparkles } from '@react-three/drei'
import * as THREE from 'three'
import { useScene } from '../state/sceneStore.js'

// SCENE 0 — the film open: deep space -> push toward a single star that IS the Cambium logo -> hand off
// to the alien greeter. Choreographed with a simple eased camera dolly (swap for theatre.js for full control).
// ASSET SLOT: replace the emissive logo-star with a textured plane of your Cambium logo:
//   const logo = useTexture('/models/cambium-logo.png');  <mesh><planeGeometry/><meshBasicMaterial map={logo} transparent/></mesh>
export default function CosmosIntro() {
  const { camera } = useThree()
  const t = useRef(0)
  const star = useRef()
  const setAct = useScene(s => s.setAct)
  const done = useRef(false)

  useFrame((_, dt) => {
    t.current += dt
    const p = Math.min(1, t.current / 6)            // 6s opening
    const e = 1 - Math.pow(1 - p, 3)                 // easeOutCubic
    // dolly from far away straight toward the logo-star at origin
    camera.position.set(0, THREE.MathUtils.lerp(2, 0.2, e), THREE.MathUtils.lerp(120, 6, e))
    camera.lookAt(0, 0, 0)
    if (star.current) { star.current.rotation.z += dt * 0.3; star.current.scale.setScalar(0.4 + e * 0.8) }
    if (p >= 1 && !done.current) { done.current = true; setTimeout(() => setAct('greeter'), 200) }
  })

  return (
    <>
      <color attach="background" args={['#02060d']} />
      <Stars radius={120} depth={80} count={6000} factor={4} fade speed={1} />
      <Sparkles count={300} scale={[60, 60, 60]} size={3} speed={0.2} color="#cfe0ff" />
      {/* the logo-star (placeholder = glowing gold disc) */}
      <group ref={star}>
        <mesh>
          <circleGeometry args={[2.2, 64]} />
          <meshBasicMaterial color="#f6e4b0" transparent opacity={0.8} blending={THREE.AdditiveBlending} side={THREE.DoubleSide} />
        </mesh>
        <mesh><ringGeometry args={[2.3, 2.6, 64]} /><meshBasicMaterial color="#e7c878" transparent opacity={0.6} side={THREE.DoubleSide} /></mesh>
        <pointLight color="#e7c878" intensity={3} distance={30} />
      </group>
      <Sparkles count={120} scale={6} size={6} speed={0.5} color="#e7c878" />
    </>
  )
}
