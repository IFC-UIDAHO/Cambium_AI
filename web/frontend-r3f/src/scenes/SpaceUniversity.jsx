import { useRef } from 'react'
import { useFrame, useThree } from '@react-three/fiber'
import { Sparkles, Html, Float } from '@react-three/drei'
import * as THREE from 'three'
import { COUNCILS } from '../data/councils.js'
import { DOCKS } from '../data/ships.js'
import { useScene } from '../state/sceneStore.js'
import Model from '../components/Model.jsx'

// placeholders (used only until the .glb files exist)
function ShipPlaceholder({ color, st }) {
  const emissive = st === 'work' ? 1.6 : st === 'dim' ? 0.12 : 0.6
  return <mesh rotation={[Math.PI / 2, 0, 0]}><coneGeometry args={[0.7, 1.6, 6]} /><meshStandardMaterial color="#14241c" emissive={color} emissiveIntensity={emissive} metalness={0.6} roughness={0.3} flatShading /></mesh>
}
function StationPlaceholder() {
  return <mesh><icosahedronGeometry args={[2.4, 1]} /><meshStandardMaterial color="#1c3326" emissive="#e7c878" emissiveIntensity={1.2} metalness={0.7} roughness={0.25} flatShading /></mesh>
}

function Ship({ c }) {
  const ref = useRef()
  const st = useScene(s => s.states[c.id] || 'dim')
  const dock = DOCKS[c.id]
  useFrame((s) => {
    if (!ref.current) return
    const rise = st === 'work' ? 4 : 0
    ref.current.position.lerp(new THREE.Vector3(dock.x, dock.y + rise, dock.z), 0.06)
    ref.current.rotation.y += (st === 'work' ? 0.03 : 0.005)
    const sc = st === 'dim' ? 0.7 : st === 'work' ? 1.25 : 1
    ref.current.scale.lerp(new THREE.Vector3(sc, sc, sc), 0.08)
  })
  return (
    <group ref={ref} position={dock}>
      <Model url="/ship.glb" targetSize={1.8} fallback={<ShipPlaceholder color={c.color} st={st} />} />
      {/* thruster glow while working */}
      {st === 'work' && <pointLight color="#b7f36a" intensity={2} distance={6} />}
      <Html center distanceFactor={26} style={{ pointerEvents: 'none' }}>
        <div style={{ opacity: st === 'dim' ? 0.3 : 1, color: st === 'work' ? '#b7f36a' : '#fff', fontWeight: 700, fontSize: 12, textShadow: '0 1px 8px #000', whiteSpace: 'nowrap', transition: 'all .4s' }}>{c.id}</div>
      </Html>
    </group>
  )
}

function Station() {
  const g = useRef()
  useFrame((_, dt) => { if (g.current) g.current.rotation.y += dt * 0.1 })
  return (
    <group ref={g}>
      <Model url="/station.glb" targetSize={6} fallback={<StationPlaceholder />} />
      <mesh rotation={[Math.PI / 2, 0, 0]}><torusGeometry args={[4.6, 0.07, 12, 90]} /><meshBasicMaterial color="#e7c878" transparent opacity={0.6} /></mesh>
      <pointLight color="#e7c878" intensity={2.4} distance={50} />
      <Html center distanceFactor={30} style={{ pointerEvents: 'none' }}><div style={{ color: '#e7c878', fontWeight: 800, fontSize: 13, textShadow: '0 1px 8px #000' }}>President · Orchestration</div></Html>
    </group>
  )
}

function Courier() {
  const ref = useRef()
  const atUser = useScene(s => s.alienAtUser)
  const { camera } = useThree()
  useFrame(() => {
    if (!ref.current) return
    const tgt = atUser ? new THREE.Vector3(camera.position.x * 0.5, 1, camera.position.z * 0.5) : new THREE.Vector3(0, 5, 0)
    ref.current.position.lerp(tgt, 0.05)
  })
  return (
    <Float speed={3} floatIntensity={1.5}>
      <group ref={ref} position={[0, 5, 0]}>
        <Model url="/alien.glb" targetSize={1.1} fallback={<mesh><sphereGeometry args={[0.6, 20, 20]} /><meshStandardMaterial color="#9af0c8" emissive="#16c079" emissiveIntensity={0.6} /></mesh>} />
      </group>
    </Float>
  )
}

export default function SpaceUniversity() {
  const { camera } = useThree()
  const drift = useRef(0)
  useFrame((s, dt) => {
    drift.current += dt * 0.06
    camera.position.x += (Math.sin(drift.current) * 20 - camera.position.x) * 0.02
    camera.position.z += (Math.cos(drift.current) * 20 - camera.position.z) * 0.02
    camera.position.y += (6 - camera.position.y) * 0.02
    camera.lookAt(0, 1, 0)
  })
  return (
    <>
      <color attach="background" args={['#03060d']} />
      <fogExp2 attach="fog" args={['#03060d', 0.012]} />
      <ambientLight intensity={0.5} color="#335544" />
      <pointLight position={[0, 18, 8]} intensity={1.2} color="#e7c878" />
      <Sparkles count={600} scale={[60, 40, 60]} size={2} speed={0.2} color="#b7f36a" opacity={0.5} />
      <Station />
      {COUNCILS.filter(c => !c.hero).map(c => <Ship key={c.id} c={c} />)}
      <Courier />
    </>
  )
}
