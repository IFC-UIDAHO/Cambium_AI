#!/usr/bin/env python3
"""figure_lint -- advisory publication-figure checks for SVG and PNG files.

Never modifies the figure file. Prints warnings by default (exit 0); with
--strict, exits 1 if any check flags something. This is a heuristic lint, not
a publisher's figure-requirements checker or an accessibility guarantee: a
clean pass here does not mean a journal will accept the figure, and a flag
does not always mean the figure is wrong.

SVG checks (stdlib xml.etree.ElementTree):
  - font-size < 11 (in a text element's style/font-size attribute or inline
    style="font-size:...") is flagged as likely too small to read at print size.
  - missing BOTH viewBox and (width AND height) on the root <svg> is flagged,
    since the figure may not scale predictably when placed in a document.
  - colorblind risk: every fill/stroke hex color used anywhere in the file is
    collected, converted to HSL via colorsys, and bucketed by hue. If a
    red-family hue (approximately 340-360 or 0-20 degrees) and a green-family
    hue (approximately 80-160 degrees) both appear AND their lightness values
    are within 0.15 of each other, it is flagged as a red/green pair that may
    be hard to distinguish for red-green colorblindness. This is a coarse hue-
    window heuristic, not a simulation of any specific colorblindness type; it
    will both miss real problems and flag some fine color pairs.

PNG checks (stdlib struct, header bytes only, no decompression of pixel data):
  - width or height < 600 px is flagged as likely too small for print
    reproduction.
  - DPI is read from the optional pHYs chunk (pixels-per-meter -> DPI = ppm *
    0.0254) and flagged if < 300, but ONLY when a pHYs chunk is present; a PNG
    with no pHYs chunk has no recorded DPI and is not flagged for DPI.

Exit codes:
  0  -- linted; warnings (if any) printed to stdout
  1  -- --strict was given and at least one check flagged something
  2  -- input file missing, unreadable, or not a recognized SVG/PNG

Usage:
  python3 tools/figure_lint.py figure.svg
  python3 tools/figure_lint.py figure.png --strict
"""
from __future__ import annotations
import argparse
import colorsys
import os
import re
import struct
import sys
import xml.etree.ElementTree as ET

# UTF-8 stdout guard
import cambium_io  # noqa: F401


class _ToolError(Exception):
    """Private control-flow error carrying the exit code, so lint helpers never
    call sys.exit(): main() catches this and returns the code."""

    def __init__(self, code: int):
        super().__init__(code)
        self.code = code


MIN_FONT_SIZE = 11.0
MIN_PNG_DIM = 600
MIN_DPI = 300.0
RED_HUE_WINDOWS = [(340.0, 360.0), (0.0, 20.0)]
GREEN_HUE_WINDOW = (80.0, 160.0)
LIGHTNESS_TOLERANCE = 0.15

HEX_COLOR_RE = re.compile(r"#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b")
FONT_SIZE_RE = re.compile(r"font-size\s*:\s*([0-9.]+)")


# ---------------------------------------------------------------------------
# SVG checks
# ---------------------------------------------------------------------------

def _local_tag(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def _hex_to_hsl(hex_color: str) -> tuple[float, float, float]:
    if len(hex_color) == 3:
        hex_color = "".join(c * 2 for c in hex_color)
    r = int(hex_color[0:2], 16) / 255.0
    g = int(hex_color[2:4], 16) / 255.0
    b = int(hex_color[4:6], 16) / 255.0
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    return h * 360.0, s, l


def _hue_in_window(hue: float, window: tuple[float, float]) -> bool:
    return window[0] <= hue <= window[1]


def lint_svg(path: str) -> list[str]:
    warnings: list[str] = []
    try:
        tree = ET.parse(path)
    except ET.ParseError as exc:
        print(f"[figure_lint] ERROR: not valid XML/SVG: {path}\n  {exc}", file=sys.stderr)
        raise _ToolError(2)
    root = tree.getroot()

    if _local_tag(root.tag) != "svg":
        print(f"[figure_lint] ERROR: root element is not <svg>: {path}", file=sys.stderr)
        raise _ToolError(2)

    # viewBox / width+height check
    has_viewbox = root.get("viewBox") is not None
    has_wh = root.get("width") is not None and root.get("height") is not None
    if not has_viewbox and not has_wh:
        warnings.append("SVG root has neither viewBox nor both width and height set; it may not scale predictably.")

    # font-size check
    for elem in root.iter():
        if _local_tag(elem.tag) not in ("text", "tspan"):
            continue
        size = None
        fs_attr = elem.get("font-size")
        if fs_attr:
            m = re.match(r"([0-9.]+)", fs_attr)
            if m:
                size = float(m.group(1))
        style_attr = elem.get("style", "")
        m2 = FONT_SIZE_RE.search(style_attr)
        if m2:
            size = float(m2.group(1))
        if size is not None and size < MIN_FONT_SIZE:
            snippet = (elem.text or "").strip()[:40]
            warnings.append(f"text element with font-size {size}pt (< {MIN_FONT_SIZE}pt): '{snippet}'")

    # colorblind risk check
    with open(path, encoding="utf-8", errors="replace") as fh:
        raw = fh.read()
    hex_colors = {m.group(1).lower() for m in HEX_COLOR_RE.finditer(raw)}

    red_hsl = []
    green_hsl = []
    for hexc in hex_colors:
        try:
            hue, sat, light = _hex_to_hsl(hexc)
        except ValueError:
            continue
        if any(_hue_in_window(hue, w) for w in RED_HUE_WINDOWS):
            red_hsl.append((hexc, light))
        elif _hue_in_window(hue, GREEN_HUE_WINDOW):
            green_hsl.append((hexc, light))

    for r_hex, r_light in red_hsl:
        for g_hex, g_light in green_hsl:
            if abs(r_light - g_light) <= LIGHTNESS_TOLERANCE:
                warnings.append(
                    f"possible red/green colorblind risk: #{r_hex} and #{g_hex} are both used "
                    f"and have similar lightness ({r_light:.2f} vs {g_light:.2f}); consider "
                    "adding a shape/pattern/label cue in addition to color."
                )

    return warnings


# ---------------------------------------------------------------------------
# PNG checks
# ---------------------------------------------------------------------------

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def lint_png(path: str) -> list[str]:
    warnings: list[str] = []
    try:
        with open(path, "rb") as fh:
            data = fh.read()
    except OSError as exc:
        print(f"[figure_lint] ERROR: cannot read PNG file: {path}\n  {exc}", file=sys.stderr)
        raise _ToolError(2)

    if not data.startswith(PNG_SIGNATURE):
        print(f"[figure_lint] ERROR: not a valid PNG (bad signature): {path}", file=sys.stderr)
        raise _ToolError(2)

    width = height = None
    dpi = None
    offset = len(PNG_SIGNATURE)
    while offset + 8 <= len(data):
        length = struct.unpack(">I", data[offset:offset + 4])[0]
        chunk_type = data[offset + 4:offset + 8]
        chunk_data = data[offset + 8:offset + 8 + length]

        if chunk_type == b"IHDR" and len(chunk_data) >= 8:
            width, height = struct.unpack(">II", chunk_data[0:8])
        elif chunk_type == b"pHYs" and len(chunk_data) >= 9:
            ppu_x, _ppu_y, unit = struct.unpack(">IIB", chunk_data[0:9])
            if unit == 1:  # meters
                dpi = ppu_x * 0.0254
        elif chunk_type == b"IEND":
            break

        offset += 8 + length + 4  # length + type + data + CRC

    if width is None or height is None:
        print(f"[figure_lint] ERROR: no IHDR chunk found (malformed PNG): {path}", file=sys.stderr)
        raise _ToolError(2)

    if width < MIN_PNG_DIM or height < MIN_PNG_DIM:
        warnings.append(f"PNG dimensions {width}x{height}px are below the {MIN_PNG_DIM}px minimum in at least one axis.")

    if dpi is not None and dpi < MIN_DPI:
        warnings.append(f"PNG DPI (from pHYs chunk) is {dpi:.0f}, below the {MIN_DPI:.0f} DPI minimum.")

    return warnings


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def lint_file(path: str) -> list[str]:
    ext = os.path.splitext(path)[1].lower()
    if ext == ".svg":
        return lint_svg(path)
    if ext == ".png":
        return lint_png(path)
    print(f"[figure_lint] ERROR: unsupported file type (expected .svg or .png): {path}", file=sys.stderr)
    raise _ToolError(2)


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Advisory publication-figure lint for SVG and PNG files. Never modifies the file."
    )
    ap.add_argument("figure", help="Path to an .svg or .png figure file.")
    ap.add_argument("--strict", action="store_true", help="Exit 1 if any check flags something.")
    args = ap.parse_args(argv)

    if not os.path.exists(args.figure):
        print(f"[figure_lint] ERROR: file not found: {args.figure}", file=sys.stderr)
        return 2

    try:
        warnings = lint_file(args.figure)
    except _ToolError as exc:
        return exc.code

    if not warnings:
        print(f"[figure_lint] OK: no issues flagged in {args.figure}")
        return 0

    print(f"[figure_lint] {len(warnings)} issue(s) flagged in {args.figure}:")
    for w in warnings:
        print(f"  - {w}")
    print("[figure_lint] advisory only: a clean pass does not guarantee journal acceptance, "
          "and a flag does not always mean the figure is wrong.")

    return 1 if args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
