# Demo GIF — recording script (~30 seconds)

Goal: a looping GIF for the README top + the GitHub social card that shows Cambium
"moving" in 30 seconds. You record it; everything you need is already in the repo.

## Tool (free, Windows)
**ScreenToGif** (https://www.screentogif.com) — record a screen region, trim, export GIF.
(Mac/Linux: Kap, or `peek`. Or record MP4 with OBS and convert with ffmpeg — see bottom.)

## Setup before recording
- Open `demo/tour.html` in your browser, full-screen the browser (F11), let it auto-play once.
- Recording region: the browser content area only (no toolbar). Target ~1200×675 (16:9).
- ScreenToGif: 15 fps is plenty for a GIF; keep it under ~8 MB so GitHub displays it inline.

## Shot list (30 s) — record the auto-running tour, OR drive it manually:
| Time | Scene (tour.html slide / action) | What viewers see |
|---|---|---|
| 0–4 s  | Slide 0 — Welcome (🌲 Cambium, stats) | the brand + "34 / 9 / 6 / MIT" |
| 4–9 s  | Slide 2 — Lifecycle strip animates in | RFP → … → Report with the 6 gold gates |
| 9–15 s | Slide 3 — the 9 councils / 34 agents grid | the org filling in, color-coded |
| 15–21 s| Slide 4 — Evidence contract + governance | claim tiers + gates + principles |
| 21–27 s| Slide 5 — "Start where you are" (3 doors) | the three entry commands |
| 27–30 s| back to Slide 0 (loop point) | clean loop |

Tip: press **R** in the tour to restart so the GIF loops cleanly from the welcome slide.

## Alternative shot: the interactive dashboard (also great)
Record `dashboard.html`: hover/click a few agent cards so they expand, then click 2–3 council
filters (Verification, Faculty, Pre-Award). ~20 s. Shows it's interactive.

## Export + add to the repo
1. Export as `assets/demo.gif` (loop = forever, 15 fps, width ~1000 px).
2. Add to README top, e.g. right under the badges:
   `<p align="center"><img src="assets/demo.gif" alt="Cambium in 30 seconds" width="820"></p>`
3. Commit + push with `push_cambium.bat`.

## (Optional) MP4 → GIF with ffmpeg (smaller, sharper)
```
ffmpeg -i demo.mp4 -vf "fps=15,scale=1000:-1:flags=lanczos,palettegen" palette.png
ffmpeg -i demo.mp4 -i palette.png -vf "fps=15,scale=1000:-1:flags=lanczos,paletteuse" assets/demo.gif
```

## Social card
Upload `assets/social-preview.png` (1280×640) at: repo → Settings → General → "Social preview" → Edit.
