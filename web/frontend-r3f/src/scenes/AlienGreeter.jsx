import { useRef, useEffect } from 'react'
import { useFrame } from '@react-three/fiber'
import { Float, Sparkles } from '@react-three/drei'
import { useScene } from '../state/sceneStore.js'
import { speak } from '../lib/voice.js'
import Model from '../components/Model.jsx'

// placeholder shown only until /alien.glb is present
function AlienPlaceholder() {
  return (
    <group>
      <mesh><capsuleGeometry args={[0.7, 0.8, 8, 16]} /><meshStandardMaterial color="#7fe3b0" emissive="#16c079" emissiveIntensity={0.5} roughness={0.4} /></mesh>
      <mesh position={[0, 0.95, 0]}><sphereGeometry args={[0.55, 24, 24]} /><meshStandardMaterial color="#9af0c8" emissive="#16c079" emissiveIntensity={0.4} roughness={0.3} /></mesh>
      <mesh position={[0, 1.0, 0.45]}><sphereGeometry args={[0.22, 16, 16]} /><meshStandardMaterial color="#06140d" emissive="#b7f36a" emissiveIntensity={0.6} /></mesh>
      <mesh position={[0, 1.65, 0]}><cylinderGeometry args={[0.02, 0.02, 0.5]} /><meshBasicMaterial color="#e7c878" /></mesh>
      <mesh position={[0, 1.95, 0]}><sphereGeometry args={[0.1, 12, 12]} /><meshBasicMaterial color="#e7c878" /></mesh>
    </group>
  )
}

// SCENE 1 — the greeter. Loads /alien.glb if present (auto-fit), else the placeholder. Speaks the welcome.
export default function AlienGreeter() {
  const ref = useRef()
  const alienSpeak = useScene(s => s.alienSpeak)
  useEffect(() => {
    const line = "Welcome to the Cambium Institute! We are the little aliens from Cambium AI. How can we help you today?"
    alienSpeak(line); speak(line)
  }, [])
  useFrame((s) => { if (ref.current) { ref.current.position.y = Math.sin(s.clock.elapsedTime * 1.5) * 0.15; ref.current.rotation.y = Math.sin(s.clock.elapsedTime * 0.6) * 0.25 } })
  return (
    <>
      <color attach="background" args={['#05101a']} />
      <ambientLight intensity={0.7} color="#9fd0ff" />
      <pointLight position={[2, 3, 4]} intensity={2} color="#bfe6ff" />
      <Sparkles count={250} scale={[24, 16, 24]} size={2} speed={0.2} color="#bfe6ff" />
      <Float speed={2} floatIntensity={1.4} rotationIntensity={0.4}>
        <group ref={ref}>
          <Model url="/alien.glb" targetSize={2.6} fallback={<AlienPlaceholder />} />
        </group>
      </Float>
    </>
  )
}
