import { Canvas } from '@react-three/fiber'
import { Suspense } from 'react'
import { EffectComposer, Bloom, Vignette } from '@react-three/postprocessing'
import { useScene } from './state/sceneStore.js'
import CosmosIntro from './scenes/CosmosIntro.jsx'
import AlienGreeter from './scenes/AlienGreeter.jsx'
import SpaceUniversity from './scenes/SpaceUniversity.jsx'
import HUD from './components/ui/HUD.jsx'

function Stage() {
  const act = useScene(s => s.act)
  return (
    <>
      {act === 'cosmos' && <CosmosIntro />}
      {act === 'greeter' && <AlienGreeter />}
      {(act === 'campus' || act === 'done') && <SpaceUniversity />}
      <EffectComposer>
        <Bloom intensity={1.0} luminanceThreshold={0.6} luminanceSmoothing={0.3} mipmapBlur />
        <Vignette offset={0.2} darkness={0.8} />
      </EffectComposer>
    </>
  )
}

export default function App() {
  return (
    <>
      <Canvas dpr={[1, 2]} camera={{ position: [0, 2, 120], fov: 55 }} gl={{ antialias: true }}>
        <Suspense fallback={null}><Stage /></Suspense>
      </Canvas>
      <HUD />
    </>
  )
}
