import { useRef, useMemo } from 'react'
import { useFrame, useThree } from '@react-three/fiber'
import { Float, Sparkles, MeshTransmissionMaterial, Environment, Html } from '@react-three/drei'
import { EffectComposer, Bloom, DepthOfField, Vignette, Noise, SMAA } from '@react-three/postprocessing'
import * as THREE from 'three'
import gsap from 'gsap'
import { COUNCILS, POSITIONS } from '../data/councils.js'
import { useScene } from '../state/sceneStore.js'

// --- the hero: glowing Orchestrator core ---
function Core() {
  const g = useRef()
  useFrame((s, dt) => { if (g.current) { g.current.rotation.y += dt * 0.15; g.current.children[1].rotation.y -= dt * 0.3 } })
  return (
    <group ref={g}>
      <mesh><icosahedronGeometry args={[2.1, 1]} /><meshStandardMaterial color="#1c3326" emissive="#e7c878" emissiveIntensity={1.3} metalness={0.6} roughness={0.25} flatShading /></mesh>
      <mesh><icosahedronGeometry args={[2.5, 1]} /><meshBasicMaterial color="#e7c878" wireframe transparent opacity={0.3} /></mesh>
      <mesh rotation={[Math.PI / 2, 0, 0]}><torusGeometry args={[4.2, 0.05, 12, 90]} /><meshBasicMaterial color="#e7c878" transparent opacity={0.55} /></mesh>
      <mesh rotation={[Math.PI / 2.3, 0, 0]}><torusGeometry args={[5.4, 0.035, 12, 100]} /><meshBasicMaterial color="#16c079" transparent opacity={0.4} /></mesh>
      <pointLight color="#e7c878" intensity={2.2} distance={40} />
    </group>
  )
}

// --- a floating glass council crystal ---
function Crystal({ c }) {
  const ref = useRef()
  const st = useScene(s => s.states[c.id] || 'dim')
  const target = st === 'work' ? 1.35 : st === 'active' ? 1.05 : 0.7
  useFrame(() => { if (ref.current) ref.current.scale.lerp({ x: target, y: target, z: target }, 0.07) })
  const emissive = st === 'dim' ? 0.12 : st === 'work' ? 1.8 : 0.7
  return (
    <Float speed={1.4} rotationIntensity={0.6} floatIntensity={1.2} position={POSITIONS[c.id]}>
      <group ref={ref}>
        <mesh>
          <octahedronGeometry args={[1.1, 0]} />
          <MeshTransmissionMaterial samples={6} thickness={0.9} roughness={0.12} ior={1.4}
            chromaticAberration={0.25} transmission={1} color={c.color}
            emissive={c.color} emissiveIntensity={emissive} background={null} />
        </mesh>
        <Html center distanceFactor={22} style={{ pointerEvents:'none' }}>
          <div style={{ opacity: st === 'dim' ? 0.25 : 1, color: st === 'work' ? '#b7f36a' : '#fff',
            fontWeight: 700, fontSize: 13, textShadow: '0 1px 8px #000', whiteSpace: 'nowrap', transition: 'all .4s' }}>
            {c.id}<div style={{ fontSize: 9, fontWeight: 500, color: st === 'work' ? '#b7f36a' : '#e7c878' }}>{c.role}</div>
          </div>
        </Html>
      </group>
    </Float>
  )
}

// --- volumetric-feeling beam from core to a working council ---
function Beams() {
  const states = useScene(s => s.states)
  const working = Object.entries(states).filter(([, v]) => v === 'work').map(([k]) => k)
  return working.map(id => {
    const end = POSITIONS[id]; if (!end) return null
    const mid = end.clone().multiplyScalar(0.5); mid.y += 3
    const curve = new THREE.QuadraticBezierCurve3(new THREE.Vector3(0, 0, 0), mid, end.clone())
    return <BeamMesh key={id} curve={curve} />
  })
}
function BeamMesh({ curve }) {
  const m = useRef()
  const geo = useMemo(() => new THREE.TubeGeometry(curve, 24, 0.06, 8, false), [curve])
  useFrame((s) => { if (m.current) m.current.opacity = 0.3 + Math.abs(Math.sin(s.clock.elapsedTime * 3)) * 0.6 })
  return <mesh geometry={geo}><meshBasicMaterial ref={m} color="#b7f36a" transparent opacity={0.5} blending={THREE.AdditiveBlending} /></mesh>
}

// --- cinematic camera: GSAP push-in on enter, gentle drift ---
function CameraRig() {
  const { camera } = useThree()
  const screen = useScene(s => s.screen)
  const drift = useRef(0)
  useFrame((s, dt) => {
    drift.current += dt * 0.08
    const r = screen === 'campus' ? 19 : 30
    camera.position.x += (Math.sin(drift.current) * r - camera.position.x) * 0.01
    camera.position.z += (Math.cos(drift.current) * r - camera.position.z) * 0.01
    camera.position.y += ((screen === 'campus' ? 4 : 7) - camera.position.y) * 0.02
    camera.lookAt(0, 1, 0)
  })
  return null
}

export default function MainScene() {
  return (
    <>
      <color attach="background" args={['#03100a']} />
      <fogExp2 attach="fog" args={['#041009', 0.018]} />
      <ambientLight intensity={0.5} color="#335544" />
      <pointLight position={[0, 18, 8]} intensity={1.2} color="#e7c878" />
      <pointLight position={[-16, -6, -12]} intensity={1.0} color="#16c079" />
      <Environment preset="night" />
      <Core />
      {COUNCILS.filter(c => !c.hero).map(c => <Crystal key={c.id} c={c} />)}
      <Beams />
      <Sparkles count={500} scale={[40, 30, 40]} size={2} speed={0.3} color="#b7f36a" opacity={0.5} />
      <CameraRig />
      <EffectComposer multisampling={0}>
        <Bloom intensity={1.0} luminanceThreshold={0.6} luminanceSmoothing={0.3} mipmapBlur />
        <DepthOfField focusDistance={0.01} focalLength={0.05} bokehScale={2.5} />
        <Vignette eskil={false} offset={0.2} darkness={0.85} />
        <Noise opacity={0.025} />
        <SMAA />
      </EffectComposer>
    </>
  )
}
