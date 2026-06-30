#!/usr/bin/env python3
"""fair_descriptor -- describe a Cambium run's outputs as a FAIR Data Package.

AI4RA's Objective 1 is FAIR data: Findable, Accessible, Interoperable, Reusable.
This tool writes a Frictionless-style datapackage.json that catalogs the files a
Cambium run produced (agent outputs, governance records, ledgers), so another
system or person can find, read, and reuse them without guessing.

Stdlib-first. If the optional `frictionless` package is installed, the descriptor
is validated and a one-line validity note is added. Without it, a minimal but
valid Data Package descriptor is still written.

Reads from data_home() (override with --root). Writes datapackage.json there.

Usage:
  python3 tools/fair_descriptor.py [--root <path>] [--out <path>] [--name <pkg-name>]
"""
from __future__ import annotations
import argparse
import os
import sys
from datetime import datetime

import cambium_io  # noqa: F401  (UTF-8 stdout guard)
import json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# directories and extensions that make up a run's reusable outputs
_SCAN = [
    ("agent_outputs", (".md", ".json", ".jsonl", ".csv")),
    ("governance", (".md", ".jsonl", ".csv")),
    ("findings", (".md", ".json", ".csv")),
]

_MEDIATYPE = {
    ".md": "text/markdown",
    ".json": "application/json",
    ".jsonl": "application/x-ndjson",
    ".csv": "text/csv",
    ".txt": "text/plain",
}


def _slug(path: str) -> str:
    base = os.path.splitext(os.path.basename(path))[0]
    out = "".join(c if (c.isalnum() or c in "-_") else "-" for c in base.lower())
    return out.strip("-") or "resource"


def collect_resources(root: str) -> list[dict]:
    """Build Frictionless resource descriptors for the run's output files."""
    resources: list[dict] = []
    seen = set()
    for subdir, exts in _SCAN:
        d = os.path.join(root, subdir)
        if not os.path.isdir(d):
            continue
        for fn in sorted(os.listdir(d)):
            ext = os.path.splitext(fn)[1].lower()
            if ext not in exts:
                continue
            rel = os.path.join(subdir, fn).replace(os.sep, "/")
            if rel in seen:
                continue
            seen.add(rel)
            name = _slug(rel.replace("/", "-"))
            res = {
                "name": name,
                "path": rel,
                "format": ext.lstrip("."),
                "mediatype": _MEDIATYPE.get(ext, "application/octet-stream"),
            }
            try:
                res["bytes"] = os.path.getsize(os.path.join(root, rel))
            except OSError:
                pass
            resources.append(res)
    return resources


def build_descriptor(root: str, name: str) -> dict:
    """Assemble a Data Package descriptor (dict). Pure function."""
    now = datetime.utcnow().strftime("%Y-%m-%d")
    return {
        "name": name,
        "profile": "data-package",
        "title": "Cambium run outputs",
        "description": "A FAIR catalog of the files produced by a Cambium run, so they can be "
                       "found, accessed, interpreted, and reused.",
        "created": now,
        "licenses": [{"name": "MIT", "path": "https://opensource.org/license/mit"}],
        "fair": {
            "findable": "Every output is named and listed with a stable relative path.",
            "accessible": "Files are plain text or JSON, openable without proprietary software.",
            "interoperable": "Frictionless data-package profile, a widely supported open standard.",
            "reusable": "An explicit MIT license and a creation date accompany the catalog.",
        },
        "resources": collect_resources(root),
    }


def _maybe_validate(descriptor: dict) -> str:
    """Validate with frictionless if available. Returns a one-line note."""
    try:
        from frictionless import Package  # optional dependency
    except Exception:
        return "frictionless not installed: descriptor written without external validation."
    try:
        pkg = Package(descriptor)
        report = pkg.validate()
        if getattr(report, "valid", False):
            return "frictionless: descriptor is valid."
        return "frictionless: descriptor written, validation reported issues (see frictionless docs)."
    except Exception as e:  # pragma: no cover - depends on optional lib internals
        return f"frictionless present but validation could not run: {e}"


def main(argv=None):
    ap = argparse.ArgumentParser(description="Write a FAIR Data Package descriptor for a Cambium run.")
    ap.add_argument("--root", default=None, help="Data root (overrides data_home()).")
    ap.add_argument("--out", default=None, help="Output path (default <root>/datapackage.json).")
    ap.add_argument("--name", default="cambium-run-outputs", help="Data package name (slug).")
    args = ap.parse_args(argv)

    root = args.root if args.root else cambium_io.data_home()
    descriptor = build_descriptor(root, args.name)
    note = _maybe_validate(descriptor)

    out = args.out if args.out else os.path.join(root, "datapackage.json")
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(descriptor, indent=2, ensure_ascii=False))
    print(f"[fair_descriptor] wrote {out} ({len(descriptor['resources'])} resource(s)). {note}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
