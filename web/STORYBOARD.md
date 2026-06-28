# Cambium — cinematic storyboard (the alien / space-university experience)

The Director's vision, broken into buildable scenes. Each scene names the **technique** (code) and the
**asset** (model/sound) it needs. The run logic (which councils activate, the gates) comes from the bridge
(`web/server/`) — already built. This doc is the production plan; build it scene-by-scene in `web/frontend-r3f`.

| # | Scene | What the user sees | Technique (code) | Asset needed |
|---|-------|--------------------|------------------|--------------|
| 0 | **Cosmos open** | Zoom from deep space → Milky Way → Earth → down to the surface → camera tilts up to the stars → one star is the **Cambium logo** → push into it | theatre.js / GSAP camera dolly along a path; drei `<Stars>` + `<Sparkles>`; atmosphere shader; the logo as an emissive plane/sprite that resolves from a "star" | space HDRI (Poly Haven); Earth texture (free); the Cambium logo PNG (have it) |
| 1 | **Alien greeter** | A small cute alien waves: *"Welcome to the Cambium Institute — we're the aliens from Cambium AI. How can we help?"* You **type or speak** your request | GLTF alien with idle/wave animation (`useGLTF` + `useAnimations`); speech bubble (drei `Html`); **Web Speech API** TTS (alien talks) + STT (you speak) | 1 alien model (Meshy/Rodin/Quaternius) + idle/wave clips; a friendly voice |
| 2 | **The space university** | The alien flies you to a huge orbital **station**; 11 **council spaceships** are docked around it; the **President** (a big alien) sits in the central control room | station + 11 ship models (Quaternius LowPoly Spaceships pack); president alien; orbit layout | station + ship pack + president model |
| 3 | **The President mobilizes** | The President lights up only the councils the request needs; those **ships undock, rise, work** (animated), then **descend and re-dock**; the little alien **ferries the result** to the next ship | bridge `run.started`/`phase.start` → activate ships; GSAP undock→work→dock timeline per ship; the alien flies a path between ships; beams (meshline) | ship "thruster" glow + SFX |
| 4 | **The gate (you decide)** | After a ship docks, the little alien zips over to **you**: *"All set, bro — approve?"* You pick **APPROVE / REVISE / REJECT**; it flies the answer back (REVISE → ship re-launches) | bridge `gate.open` pauses; alien flies to camera + speaks; 3 buttons `POST /api/gate/decide`; `gate.decided` resumes | alien "ask" pose + voice line |
| 5 | **Delivery** | The institute completes; the alien hands you the verified result; gentle warp-out | particle burst; summary panel; warp shader | celebratory SFX |

## Build order (so it stays previewable, never a blind mega-build)
1. **Scene 0 cosmos zoom** with placeholder sphere → confirm the camera choreography feels filmic.
2. **Scene 1 alien greeter** with one generated alien + Web Speech voice.
3. **Scenes 2–4** ships + president + the bridge-driven activation/gate loop.
4. Polish: lighting, bloom, sound, mobile.

## Honest production note
This is asset-driven. The fastest route to quality: generate the alien + ships + president with **Meshy or
Tripo** (free tiers, `.glb`), grab a space HDRI from **Poly Haven**, then assemble + choreograph in R3F with
**theatre.js/GSAP**. Voice is free via the browser's **Web Speech API**. Budget it as a few focused days,
not one prompt. See `skills/cinematic-frontend/` for the toolkit.
