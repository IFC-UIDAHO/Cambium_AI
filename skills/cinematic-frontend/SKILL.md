---
name: cinematic-frontend
description: Build a cinematic, "3D-movie" front-end — floating glass crystals, bloom, particle dust, volumetric beams, and choreographed camera — with React Three Fiber. Use when the user wants a premium/cinematic/3D/VFX-rich web UI, a Three.js scene, a "wow" landing page, or a front-end for the Cambium web app. Trigger on "3D front-end", "cinematic", "WebGL", "Three.js", "React Three Fiber", "glass crystal", "bloom", "make it look like a movie", "floating", "VFX". Stack: three + @react-three/fiber + @react-three/drei + @react-three/postprocessing + gsap + custom GLSL shaders. Scaffold in web/frontend-r3f/. Honest: this is a real Vite/npm project — it builds in a browser/Node, NOT inside a Cowork artifact (the sandbox blocks the Three.js CDN), and the cinematic result must be judged in a real browser.
---

# Cinematic 3D front-end — build it like a trailer, not a UI

The difference between "primitive" and "cinematic" is **material physics + light + camera choreography**,
not more objects. CSS 3D and a single `<canvas>` with hand-rolled Three.js look flat. Use the React Three
Fiber (R3F) ecosystem so you get real transmission glass, post-processing bloom/DOF, and timed camera moves.

## The stack (install exactly this)
```
npm install three @react-three/fiber @react-three/drei @react-three/postprocessing \
  gsap @gsap/react zustand three-custom-shader-material meshline leva r3f-perf
```
- **three / @react-three/fiber** — scene graph, camera, render loop (`useFrame`, `useThree`).
- **@react-three/drei** — the fast path to the look: `Float`, `Sparkles`, `MeshTransmissionMaterial`,
  `Environment`, `ContactShadows`, `shaderMaterial`, `CameraControls`, `Html`, loaders.
- **@react-three/postprocessing** — `Bloom`, `DepthOfField`, `Vignette`, `Noise`, `SMAA` (the "movie grade").
- **gsap (+@gsap/react)** — keyframed camera paths, scene reveals, pulsing beams, synchronized beats.
- **zustand** — scene/run state (which councils are active, the current gate).
- **three-custom-shader-material / meshline** — glossy glass + glowing volumetric beams.
- **leva / r3f-perf** — dev-only tuning + FPS overlay (strip for production).

## The seven rules that make it read as a 3D movie
1. **One hero object.** A single luminous core (the Orchestrator) the eye returns to; everything else
   supports it. Do not let 11 objects compete.
2. **Slow, deliberate camera.** Script the shot with GSAP: push-in → drift → pause → rotate → settle.
   `OrbitControls`/`CameraControls` are for *debug*; the final experience is choreographed, not user-orbited.
3. **Strong light contrast + controlled bloom.** Dark frame, few lights, emissive accents. Bloom
   `intensity ~0.8–1.2`, high `luminanceThreshold (~0.6)` so only the bright edges glow — not the whole screen.
4. **Real glass.** `MeshTransmissionMaterial` (transmission, roughness variation, IOR, thickness, chromatic
   aberration) + an `Environment` HDRI for reflections. This is what sells "glossy crystal".
5. **Atmosphere.** A slow-drifting `Sparkles`/instanced-points dust field with depth fade; volumetric-feeling
   beams (meshline or tube with additive emissive). Particles **support**, never out-bright, the subject.
6. **Minimal UI.** Overlay HUD in a separate DOM layer (or drei `Html`), sparse and gold-on-dark. The 3D is
   the star.
7. **Beat-based motion.** Reveal councils on timed beats, ease everything (`power2.inOut`), and consider
   audio-reactive pulses for extra drama. Respect `prefers-reduced-motion`.

## Recommended structure (scaffolded in `web/frontend-r3f/`)
```
src/
  scenes/MainScene.jsx          one hero core + 11 council crystals + camera rig + post FX
  components/webgl/  CameraRig · LightingRig · PostFX · EnvironmentRig
  components/council/ CouncilCore · CouncilCrystal · CouncilNameplate
  components/vfx/    DustField · Beam · GlowOrb
  components/materials/ GlassMaterial · BeamMaterial (custom GLSL)
  components/ui/     HUD · Overlay · GatePanel
  hooks/  useCameraPath · useSceneState · useReducedMotion · useResponsiveDPR
  state/  sceneStore.js (zustand)
  data/   councils.js · cameraPaths.js · palette.js
  shaders/ glass/ beam/ crystal/  (vertex.glsl + fragment.glsl, via vite-plugin-glsl)
```

## Wire it to Cambium (so it's not just pretty — it's live)
The scene is driven by the bridge in `web/server/` (see `web/API.md`):
`POST /api/run` → light the `active` councils · `WebSocket /api/stream/{id}` → `phase.start` brightens a
council + fires a beam, `agent.finding` adds a HUD line, `gate.open` pauses the camera and shows the gate
panel → `POST /api/gate/{id}/decide` resumes. Keep all run state in the zustand store; let R3F components
subscribe. Same human-gate contract as the CLI's `--resume` + `gate_lock`.

## Performance & honesty
- Cap DPR (`min(devicePixelRatio, 2)`), use `frameloop="demand"` when idle, instance the dust, lazy-load
  the HDRI, and gate heavy post-FX on a quality toggle for low-end GPUs.
- **This is a real Vite/npm app** — it runs via `npm run dev` in a browser or on a static host
  (Cloudflare/Vercel/GitHub Pages), and **cannot** render inside a Cowork artifact (CDN-blocked). Build the
  scene, then judge the cinematic result in a real browser and iterate. Don't claim a look you can't see.

## The full studio toolkit (for narrative / character cinematics)
Code alone can't make a "3D movie" — you need **assets** (models, animations) and a **sequencer**. Add:

**Cinematic sequencing & camera**
- `theatre.js` (`@theatre/core` + `@theatre/studio`) — a visual timeline/keyframe editor for camera and
  object animation; the right tool for "zoom universe → Earth → star → reveal" film shots.
- `gsap` (+ `@gsap/react`) — code-driven timelines, easing, beat sync. `camera-controls` / drei
  `CameraControls` for scripted moves.
- drei: `useGLTF` (load models), `useAnimations` (play a model's clips), `Float`, `Html`, `Stars`,
  `Sparkles`, `Cloud`, `Environment`, `PerspectiveCamera`, `ScrollControls` for scroll-driven cinematics.

**3D assets — free, CC0 (no cost, commercial-OK)**
- Quaternius (quaternius.com), Poly Pizza (poly.pizza), Kenney (kenney.nl), OpenGameArt, Poly Haven (HDRIs
  + textures), the `awesome-cc0` list. Great for low-poly aliens, **spaceship packs**, props.

**3D assets — AI-generated (make your alien / ships / logo-star from a prompt)**
- Meshy.ai (best all-round, free tier), Tripo AI (~8s/model, free tier), Rodin (best for characters/aliens),
  Luma Genie (fast concepts), Hunyuan3D (open-source, local, free if you have a GPU). All export `.glb`.

**Voice (the talking alien + the user speaking)**
- Web Speech API — **built into the browser, free**: `speechSynthesis` (alien talks) + `SpeechRecognition`
  (user speaks their request). ElevenLabs for premium custom alien voices.

**Audio / music**: Pixabay, Freesound (CC0) for ambient space pads + UI blips. Howler.js to play them.

## How to build an asset-heavy narrative (the only path that yields quality)
1. **Generate/collect assets first** (Meshy/Tripo for the alien + president + 11 council ships + logo-star;
   Poly Haven HDRI for space). Optimize with `gltf-transform` / `gltfjsx` (drei) → React components.
2. **Block the scenes** with placeholders, wire the **bridge events** to scene state (which ship activates).
3. **Choreograph** the camera with theatre.js/GSAP (cosmos zoom, office push-in, ship undock/dock).
4. **Iterate in a browser** — judge every shot on screen; never claim a look you can't see.
Honest: this is a multi-day asset+code project, not a one-shot. Code is ~30% of it; assets + art direction
are the rest. Use AI 3D generators to compress the asset time from weeks to hours.

## Generate the 3D models with open-source AI (wired into Cambium)
You don't have to draw models by hand or pay a subscription — open-source generators make `.glb` from a
prompt/image, and `tools/gen_3d.py` calls them on free cloud GPUs (no local GPU needed):
- **TRELLIS** (Microsoft, MIT) — best image→3D quality. **Hunyuan3D-2.1** (Tencent, Apache-2.0) — text *or*
  image→3D. **TripoSR** (Stability+Tripo, MIT) — fastest image→3D.
- They are mostly **image→3D**, so the flow is *text → image → 3D*: make an image (any free image tool, or
  your logo), then `python3 tools/gen_3d.py --image alien.png --out web/frontend-r3f/public/models/alien.glb`.
- Honest ceiling: HF Spaces change endpoints, sleep, and queue; quality is good for stylized/low-poly and
  still needs a human eye. For a few hero assets the Space's web UI (or Meshy/Tripo) is often more reliable
  than automation. Always optimize: `npx gltf-transform optimize in.glb out.glb --texture-compress webp`.
