#!/usr/bin/env python3
"""env_doctor.py -- machine environment doctor (complements tools/doctor.py).

tools/doctor.py checks the REPO; this checks the MACHINE the repo runs on:
  hard : Python >= 3.10, PyYAML importable, pytest importable (FAIL -> exit 1)
  soft : mcp SDK (needed only for mcp_server/), optional extras from
         requirements-optional.txt, installed versions vs constraints.txt,
         stdout encoding, git on PATH (warn only, never exit 1)

Usage:
    python3 tools/env_doctor.py [--root DIR]

Honest limits:
    - Requirement names and pins are read from requirements.txt,
      requirements-optional.txt, constraints.txt and mcp_server/pyproject.toml
      under --root; a missing file skips those rows with a warning instead of
      inventing a hardcoded list.
    - Drift against constraints.txt is reported, never enforced: those pins
      freeze CI, not your machine.
    - Importing this tool already applies the cambium_io UTF-8 shim, so the
      encoding row reports the state of THIS process, shim included.
"""

import argparse
import importlib
import importlib.metadata
import os
import re
import shutil
import subprocess
import sys

import cambium_io  # noqa: F401

REQ_LINE = re.compile(r"^([A-Za-z0-9][A-Za-z0-9._-]*)\s*(==|>=|<=|~=|!=)?\s*([^\s;#]*)")
HARD = "FAIL"
WARN = "warn"
OK = "ok"


def repo_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def read_requirements(path: str):
    """[(name, op, version)] from a pip requirements file, or None if absent."""
    if not os.path.isfile(path):
        return None
    out = []
    for line in open(path, encoding="utf-8", errors="replace"):
        line = line.strip()
        if not line or line.startswith(("#", "-")):
            continue
        m = REQ_LINE.match(line)
        if m and m.group(1):
            out.append((m.group(1), m.group(2) or "", m.group(3) or ""))
    return out


def installed_version(dist: str):
    for candidate in (dist, dist.replace("-", "_"), dist.replace("_", "-")):
        try:
            return importlib.metadata.version(candidate)
        except importlib.metadata.PackageNotFoundError:
            continue
    return None


def find_pin(sources: dict, dist: str):
    """Look a distribution up in the parsed requirement files; (spec, file)."""
    want = dist.lower().replace("_", "-")
    for fname, reqs in sources.items():
        for name, op, ver in (reqs or []):
            if name.lower().replace("_", "-") == want:
                return (name + op + ver) if op else name, fname
    return None, None


def mcp_dependency_hint(root: str):
    """Read mcp_server/pyproject.toml dependencies for the mcp pin, if any."""
    path = os.path.join(root, "mcp_server", "pyproject.toml")
    if not os.path.isfile(path):
        return None
    text = open(path, encoding="utf-8", errors="replace").read()
    m = re.search(r"dependencies\s*=\s*\[(.*?)\]", text, re.S)
    if not m:
        return None
    for spec in re.findall(r'"([^"]+)"', m.group(1)):
        if spec.lower().startswith("mcp"):
            return spec
    return None


def build_rows(root: str):
    """Return [(level, check, detail, fix)] for every environment check."""
    rows = []
    sources = {
        "requirements.txt": read_requirements(os.path.join(root, "requirements.txt")),
        "requirements-optional.txt": read_requirements(
            os.path.join(root, "requirements-optional.txt")),
        "constraints.txt": read_requirements(os.path.join(root, "constraints.txt")),
    }
    for fname, reqs in sources.items():
        if reqs is None:
            rows.append((WARN, "reqs-file", fname + " missing under --root; its rows are skipped",
                         "expected at " + os.path.join(root, fname)))

    # hard: python version
    v = sys.version_info
    ver_str = "%d.%d.%d" % (v.major, v.minor, v.micro)
    if (v.major, v.minor) >= (3, 10):
        rows.append((OK, "python", ver_str + " (need >= 3.10)", ""))
    else:
        rows.append((HARD, "python", ver_str + " is too old (need >= 3.10)",
                     "install Python 3.10 or newer and re-run"))

    # hard: yaml + pytest importable
    for module, dist in (("yaml", "PyYAML"), ("pytest", "pytest")):
        try:
            importlib.import_module(module)
            rows.append((OK, module, "importable (%s %s)"
                         % (dist, installed_version(dist) or "version unknown"), ""))
        except ImportError:
            spec, fname = find_pin(sources, dist)
            fix = ("pip install '%s' (from %s)" % (spec, fname)) if spec else "pip install " + dist
            rows.append((HARD, module, "NOT importable; Cambium tools and tests need it", fix))

    # soft: mcp SDK
    try:
        importlib.import_module("mcp")
        rows.append((OK, "mcp-sdk", "importable (mcp %s); mcp_server/ can run"
                     % (installed_version("mcp") or "version unknown"), ""))
    except ImportError:
        pin = mcp_dependency_hint(root)
        fix = "pip install '%s' (from mcp_server/pyproject.toml)" % pin if pin else "pip install mcp"
        rows.append((WARN, "mcp-sdk",
                     "not installed; only mcp_server/ needs it, CLI tools are unaffected", fix))

    # soft: optional extras, honestly reported
    for name, op, ver in (sources["requirements-optional.txt"] or []):
        have = installed_version(name)
        if have:
            rows.append((OK, "optional:" + name, have + " installed", ""))
        else:
            rows.append((WARN, "optional:" + name,
                         "not installed (optional; tools degrade gracefully without it)",
                         "pip install -r requirements-optional.txt"))

    # soft: constraints drift (report, never fail)
    for name, op, ver in (sources["constraints.txt"] or []):
        if op != "==":
            continue
        have = installed_version(name)
        if have is None:
            rows.append((WARN, "pin:" + name, "pinned %s in constraints.txt but not installed" % ver,
                         "pip install -c constraints.txt %s" % name))
        elif have != ver:
            rows.append((WARN, "pin:" + name, "drift: installed %s != pinned %s" % (have, ver),
                         "pip install %s==%s to match CI exactly (optional)" % (name, ver)))
        else:
            rows.append((OK, "pin:" + name, "%s matches constraints.txt" % have, ""))

    # soft: stdout encoding
    enc = getattr(sys.stdout, "encoding", "") or ""
    shim = "yes" if os.path.isfile(os.path.join(root, "tools", "cambium_io.py")) else "no"
    if "utf" in enc.lower():
        rows.append((OK, "stdout-utf8", "stdout=%s (cambium_io shim present: %s)" % (enc, shim), ""))
    else:
        rows.append((WARN, "stdout-utf8", "stdout=%s; non-UTF-8 consoles garble tool output" % enc,
                     "tools import cambium_io, which reconfigures stdout to UTF-8 on Windows "
                     "(shim present: %s)" % shim))

    # soft: git on PATH
    git = shutil.which("git")
    if git:
        try:
            out = subprocess.run(["git", "--version"], capture_output=True, text=True, timeout=10)
            detail = (out.stdout or "").strip() or git
        except Exception:
            detail = git
        rows.append((OK, "git", detail, ""))
    else:
        rows.append((WARN, "git", "not found on PATH",
                     "install git; tools/api_stability.py --old/--new and release flows need it"))

    return rows


def exit_code(rows) -> int:
    return 1 if any(level == HARD for level, _, _, _ in rows) else 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Check the machine environment for Cambium development.")
    ap.add_argument("--root", default=repo_root(),
                    help="repo root holding requirements/constraints files (default: this repo)")
    args = ap.parse_args(argv)
    root = os.path.abspath(args.root)

    rows = build_rows(root)
    print("== env_doctor: %s ==" % root)
    counts = {OK: 0, WARN: 0, HARD: 0}
    for level, check, detail, fix in rows:
        counts[level] += 1
        line = " %-4s  %-28s %s" % (level, check, detail)
        if fix and level != OK:
            line += "  -> fix: " + fix
        print(line)
    code = exit_code(rows)
    print("env_doctor: %d ok, %d warn, %d fail -> exit %d"
          % (counts[OK], counts[WARN], counts[HARD], code))
    if code:
        print("env_doctor: a HARD requirement failed (python/yaml/pytest); fix it before developing.",
              file=sys.stderr)
    return code


if __name__ == "__main__":
    sys.exit(main())
