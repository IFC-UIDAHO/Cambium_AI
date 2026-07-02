"""Tests for tools/figure_lint.py.

Stdlib + tmp_path only. SVG fixtures are hand-written strings (font-size flag,
red/green colorblind-risk flag, a clean pass). PNG fixtures are hand-built
bytes using struct for chunk framing and zlib.crc32 for real CRC values, so
the fixtures are genuinely valid PNG framing (IHDR, optional pHYs, IEND),
even though this tool's parser only reads chunk length/type/data and never
verifies the CRC itself.
"""
import os
import struct
import sys
import zlib

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_REPO, "tools"))

import figure_lint as F

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _png_chunk(chunk_type: bytes, data: bytes) -> bytes:
    length = struct.pack(">I", len(data))
    crc = struct.pack(">I", zlib.crc32(chunk_type + data) & 0xFFFFFFFF)
    return length + chunk_type + data + crc


def _build_png(width: int, height: int, ppu_x: int | None = None, ppu_y: int | None = None) -> bytes:
    ihdr_data = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)  # 8-bit RGB, no interlace
    chunks = [PNG_SIGNATURE, _png_chunk(b"IHDR", ihdr_data)]
    if ppu_x is not None and ppu_y is not None:
        phys_data = struct.pack(">IIB", ppu_x, ppu_y, 1)  # unit=1 (meters)
        chunks.append(_png_chunk(b"pHYs", phys_data))
    chunks.append(_png_chunk(b"IEND", b""))
    return b"".join(chunks)


# ---------------------------------------------------------------------------
# SVG fixtures
# ---------------------------------------------------------------------------

SVG_SMALL_FONT = """<?xml version="1.0"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <text x="10" y="10" style="font-size:8px">Tiny label</text>
</svg>
"""

SVG_RED_GREEN = """<?xml version="1.0"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <rect fill="#e60000" width="10" height="10" />
  <rect fill="#00b300" width="10" height="10" />
</svg>
"""

SVG_CLEAN = """<?xml version="1.0"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <text x="10" y="10" style="font-size:14px">Readable label</text>
  <rect fill="#1f77b4" width="10" height="10" />
  <rect fill="#ff7f0e" width="10" height="10" />
</svg>
"""

SVG_NO_SIZE_INFO = """<?xml version="1.0"?>
<svg xmlns="http://www.w3.org/2000/svg">
  <text x="10" y="10" style="font-size:14px">No viewBox or width/height</text>
</svg>
"""


def test_svg_small_font_flagged(tmp_path):
    path = tmp_path / "small_font.svg"
    path.write_text(SVG_SMALL_FONT, encoding="utf-8")
    rc = F.main([str(path)])
    assert rc == 0  # warnings only, not strict
    warnings = F.lint_svg(str(path))
    assert any("font-size" in w for w in warnings)


def test_svg_red_green_pair_flagged(tmp_path):
    path = tmp_path / "red_green.svg"
    path.write_text(SVG_RED_GREEN, encoding="utf-8")
    warnings = F.lint_svg(str(path))
    assert any("colorblind" in w for w in warnings)


def test_svg_clean_passes(tmp_path):
    path = tmp_path / "clean.svg"
    path.write_text(SVG_CLEAN, encoding="utf-8")
    warnings = F.lint_svg(str(path))
    assert warnings == []
    rc = F.main([str(path), "--strict"])
    assert rc == 0


def test_svg_missing_viewbox_and_dimensions_flagged(tmp_path):
    path = tmp_path / "no_size.svg"
    path.write_text(SVG_NO_SIZE_INFO, encoding="utf-8")
    warnings = F.lint_svg(str(path))
    assert any("viewBox" in w for w in warnings)


def test_svg_strict_exits_1_when_flagged(tmp_path):
    path = tmp_path / "small_font.svg"
    path.write_text(SVG_SMALL_FONT, encoding="utf-8")
    rc = F.main([str(path), "--strict"])
    assert rc == 1


# ---------------------------------------------------------------------------
# PNG fixtures
# ---------------------------------------------------------------------------

def test_png_dimension_parse_small_image_flagged(tmp_path):
    path = tmp_path / "small.png"
    path.write_bytes(_build_png(width=200, height=200))
    warnings = F.lint_png(str(path))
    assert any("200x200" in w for w in warnings)


def test_png_dimension_parse_large_image_passes(tmp_path):
    path = tmp_path / "large.png"
    path.write_bytes(_build_png(width=1200, height=900))
    warnings = F.lint_png(str(path))
    assert not any("px minimum" in w for w in warnings)


def test_png_low_dpi_flagged_only_when_phys_present(tmp_path):
    # 200 DPI: ppu = DPI / 0.0254
    low_dpi_ppu = int(200 / 0.0254)
    path = tmp_path / "low_dpi.png"
    path.write_bytes(_build_png(width=1200, height=1200, ppu_x=low_dpi_ppu, ppu_y=low_dpi_ppu))
    warnings = F.lint_png(str(path))
    assert any("DPI" in w for w in warnings)


def test_png_no_phys_chunk_not_flagged_for_dpi(tmp_path):
    path = tmp_path / "no_phys.png"
    path.write_bytes(_build_png(width=1200, height=1200))  # no pHYs at all
    warnings = F.lint_png(str(path))
    assert not any("DPI" in w for w in warnings)


def test_png_strict_exit_code(tmp_path):
    path = tmp_path / "small.png"
    path.write_bytes(_build_png(width=200, height=200))
    rc = F.main([str(path), "--strict"])
    assert rc == 1


def test_png_strict_exit_0_when_clean(tmp_path):
    path = tmp_path / "large.png"
    path.write_bytes(_build_png(width=1200, height=900))
    rc = F.main([str(path), "--strict"])
    assert rc == 0


def test_unsupported_extension_exits_2(tmp_path):
    path = tmp_path / "figure.txt"
    path.write_text("not a figure", encoding="utf-8")
    rc = F.main([str(path)])
    assert rc == 2


def test_missing_file_exits_2(tmp_path):
    rc = F.main([str(tmp_path / "nope.svg")])
    assert rc == 2


def test_no_em_dash_in_source():
    with open(os.path.join(_REPO, "tools", "figure_lint.py"), encoding="utf-8") as fh:
        source = fh.read()
    assert chr(0x2014) not in source
