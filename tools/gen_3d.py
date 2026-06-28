#!/usr/bin/env python3
"""gen_3d — generate a .glb 3D model from an image (or text) via a free Hugging Face Space.

Wires open-source text/image-to-3D into Cambium so you can make the cinematic assets (alien, ship,
station) without a local GPU. It calls a hosted HF Space (free, GPU on their side) with `gradio_client`
and downloads the resulting `.glb` into web/frontend-r3f/public/models/.

  pip install gradio_client
  python3 tools/gen_3d.py --image alien.png --out web/frontend-r3f/public/models/alien.glb
  python3 tools/gen_3d.py --image ship.png  --space tencent/Hunyuan3D-2.1
  python3 tools/gen_3d.py --list                      # print the recommended Spaces

Pipeline note: these models are mostly IMAGE-to-3D, so for "from a prompt" first make an image (any free
image generator, or your logo), then feed it here. Hunyuan3D also accepts text on its Space UI.

HONEST CEILING (read this): HF Spaces change their gradio endpoints, sleep when idle, and queue under load,
so the exact `--api-name` may need adjusting per Space (the tool prints the available endpoints if it can't
guess). Output quality is good for stylized/low-poly and still needs a human eye + cleanup. This is a
convenience wrapper around someone else's free GPU — not a guaranteed one-click. For just 3 hero models,
the Space's web UI (or Meshy/Tripo) is often more reliable than automation.
"""
import argparse, os, shutil, sys

SPACES = {
  "trellis": ("trellis-community/TRELLIS", "image-to-3D, MIT, high quality"),
  "hunyuan": ("tencent/Hunyuan3D-2.1", "text or image to 3D, Apache-2.0"),
  "triposr": ("stabilityai/TripoSR", "fast image-to-3D, MIT"),
}
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", help="input image (PNG/JPG) for image-to-3D")
    ap.add_argument("--out", default="web/frontend-r3f/public/models/model.glb")
    ap.add_argument("--space", default="trellis-community/TRELLIS", help="HF Space id (or a key: trellis|hunyuan|triposr)")
    ap.add_argument("--api-name", default=None, help="gradio endpoint, e.g. /generate (auto-detect if omitted)")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args(argv)
    if a.list:
        for k, (sid, desc) in SPACES.items(): print("  %-8s %-32s %s" % (k, sid, desc))
        print("\nUse: --space <id>   (image-to-3D needs --image; make an image first for text prompts)")
        return 0
    space = SPACES.get(a.space, (a.space,))[0]
    try:
        from gradio_client import Client, handle_file
    except ImportError:
        print("[gen_3d] need gradio_client:  pip install gradio_client"); return 1
    if not a.image:
        print("[gen_3d] --image is required (these models are image-to-3D). Make an image first."); return 1
    if not os.path.exists(a.image):
        print("[gen_3d] image not found: %s" % a.image); return 1

    print("[gen_3d] connecting to HF Space: %s" % space)
    try:
        client = Client(space)
    except Exception as e:
        print("[gen_3d] could not load the Space (%s). It may be sleeping or private; open it in a browser to wake it." % str(e)[:100]); return 1

    # Spaces differ; try the given endpoint, else show what's available.
    endpoints = []
    try:
        endpoints = [e for e in client.view_api(return_format="dict").get("named_endpoints", {})]
    except Exception:
        pass
    api = a.api_name or next((e for e in endpoints if "generat" in e.lower() or "image_to_3d" in e.lower() or "3d" in e.lower()), None)
    if not api and endpoints:
        print("[gen_3d] couldn't guess the endpoint. Available on this Space:")
        for e in endpoints: print("   ", e)
        print("Re-run with --api-name <one of the above>."); return 1

    print("[gen_3d] calling %s%s …" % (space, (" " + api) if api else ""))
    try:
        kwargs = {"api_name": api} if api else {}
        result = client.predict(handle_file(a.image), **kwargs)
    except Exception as e:
        print("[gen_3d] call failed (%s). The Space's API likely differs — run with --api-name, or use its web UI." % str(e)[:120]); return 1

    # result may be a path, a tuple, or a dict pointing at the glb
    glb = _find_glb(result)
    if not glb:
        print("[gen_3d] no .glb found in the result. Raw result: %s" % str(result)[:200]); return 1
    out = a.out if os.path.isabs(a.out) else os.path.join(ROOT, a.out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    shutil.copy(glb, out)
    print("[gen_3d] saved -> %s   (then: npx gltf-transform optimize %s %s --texture-compress webp)" % (out, out, out))
    return 0

def _find_glb(r):
    if isinstance(r, str) and r.endswith(".glb") and os.path.exists(r): return r
    if isinstance(r, (list, tuple)):
        for x in r:
            g = _find_glb(x)
            if g: return g
    if isinstance(r, dict):
        for x in r.values():
            g = _find_glb(x)
            if g: return g
    return None

if __name__ == "__main__":
    sys.exit(main())
