# Cambium front-end — React Three Fiber (cinematic)

A real WebGL/Three.js front-end built with the cinematic stack: **R3F + Drei + postprocessing + GSAP +
zustand**. Floating glass council crystals (`MeshTransmissionMaterial`), a glowing Orchestrator core,
bloom + depth-of-field + vignette + grain, a `Sparkles` dust field, volumetric beams, and a choreographed
camera. Wired to the Cambium bridge (`web/server/`) with a local-preview fallback.

## Run it
```bash
cd web/frontend-r3f
npm install
npm run dev          # http://localhost:5173
```
Start the bridge too (`uvicorn web.server.app:app --port 8000` from the repo root) and it drives real,
gated runs; with no server it runs a local preview. Point at a deployed bridge with `?api=https://your-bridge`.

## Build / deploy (free)
```bash
npm run build        # -> dist/  ; deploy on Cloudflare Pages / Vercel / Netlify / GitHub Pages
```

## Tune the look (see skills/cinematic-frontend)
- Glass: `MeshTransmissionMaterial` (`thickness`, `roughness`, `ior`, `chromaticAberration`) in `scenes/MainScene.jsx`.
- Glow: `<Bloom intensity luminanceThreshold>` — raise the threshold so only bright edges bloom.
- Camera: `CameraRig` (swap the drift for a GSAP timeline of push-in → pause → reveal for a trailer feel).
- Add `leva` + `r3f-perf` while tuning, then remove for production.

**Honest note:** this is a real Vite app — it renders in a browser, not inside a Cowork artifact. Judge the
cinematic result in your browser and iterate.
