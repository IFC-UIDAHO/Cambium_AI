# Dropping in your 3D assets (aliens, ships, planets)

The scaffold renders with **placeholder shapes** so it runs today. Replace them with real `.glb` models —
generate them free from **Meshy / Tripo / Rodin** (text-to-3D) or grab CC0 packs from **Quaternius / Poly
Pizza**. Put files in `public/models/` and swap the marked `ASSET SLOT` in each scene.

## Where each asset goes
| Asset | File | Used in | Swap this placeholder |
|-------|------|---------|-----------------------|
| Cute alien greeter (idle/wave anims) | `public/models/alien.glb` | `src/scenes/AlienGreeter.jsx` | the capsule+sphere group |
| Council spaceship (1 model, reused ×11, tinted) | `public/models/ship.glb` | `src/scenes/SpaceUniversity.jsx` (`Ship`) | the cone+thruster |
| Central station + President alien | `public/models/station.glb` | `SpaceUniversity.jsx` (`Station`) | the icosahedron |
| Courier alien | reuse `alien.glb` | `SpaceUniversity.jsx` (`Courier`) | the small sphere |
| Cambium logo (for the logo-star) | `public/models/cambium-logo.png` | `src/scenes/CosmosIntro.jsx` | the gold disc |
| Space background | `public/models/space.hdr` (Poly Haven) | any scene via drei `<Environment files=...>` | — |

## How to swap (example: the alien)
```jsx
import { useGLTF, useAnimations } from '@react-three/drei'
function Alien() {
  const ref = useRef()
  const { scene, animations } = useGLTF('/models/alien.glb')
  const { actions } = useAnimations(animations, ref)
  useEffect(() => { actions['Idle']?.play() }, [actions])
  return <primitive ref={ref} object={scene} />
}
```
Tip: run `npx gltfjsx public/models/alien.glb` to get a typed React component + auto-instancing.

## Optimize before shipping
`npx gltf-transform optimize in.glb out.glb --texture-compress webp` — keeps the scene fast on phones.

The 6-scene plan (cosmos → greeter → university → ships → gates → delivery) is in `../STORYBOARD.md`.
