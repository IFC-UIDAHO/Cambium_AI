#!/usr/bin/env python3
"""Cambium status line — shows live context-window heat so you pause BEFORE auto-compaction.

Claude Code pipes a JSON status payload to this script on stdin. We render a one-line gauge:

  ⬢ Cambium · <model> · <dir> · ctx ~62% [█████░░░] · ✦ pause at 85%

When estimated context use crosses the threshold (default 85%), it flips to a warning telling you to run
`/cambium:pause` — write a HANDOFF.md, clear the window, and `/cambium:resume` with full memory instead of
letting the model lossily compact. Context % is ESTIMATED from the transcript (chars/4 ≈ tokens) against a
budget (default 200k, override with CAMBIUM_CTX_BUDGET); it's a heat gauge, not an exact meter.

Install (Claude Code): /statusline  →  command: bash tools/statusline.sh
"""
import sys, os, json

BUDGET = int(os.environ.get("CAMBIUM_CTX_BUDGET", "200000"))
WARN = float(os.environ.get("CAMBIUM_CTX_WARN", "0.85"))


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        print("⬢ Cambium"); return
    model = (data.get("model") or {}).get("display_name") or (data.get("model") or {}).get("id") or "Claude"
    cwd = (data.get("workspace") or {}).get("current_dir") or data.get("cwd") or ""
    short = os.path.basename(cwd.rstrip("/\\")) if cwd else ""

    pct = None
    tp = data.get("transcript_path")
    if tp and os.path.exists(tp):
        try:
            approx_tokens = os.path.getsize(tp) / 4.0   # ~4 chars/token
            pct = max(0.0, min(1.0, approx_tokens / BUDGET))
        except Exception:
            pct = None
    if data.get("exceeds_200k_tokens"):
        pct = max(pct or 0.0, 0.99)

    seg = [f"⬢ Cambium · {model}"]
    if short:
        seg.append(short)
    if pct is not None:
        bars = int(round(pct * 8))
        gauge = "█" * bars + "░" * (8 - bars)
        if pct >= WARN:
            seg.append(f"⚠ ctx ~{pct*100:.0f}% [{gauge}] — run /cambium:pause")
        else:
            seg.append(f"ctx ~{pct*100:.0f}% [{gauge}]")
    else:
        seg.append("✦ /cambium:pause when context runs high")
    print("  ·  ".join(seg))


if __name__ == "__main__":
    main()
