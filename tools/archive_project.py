#!/usr/bin/env python3
"""archive_project - retention/archival copy of run artifacts with integrity continuity.

Purpose:
  COPY (never move; deletion stays a human action) the named run artifacts into
  an archive directory and write MANIFEST.json with a SHA-256 for every file,
  the creation time, a retention note, and the source git commit when git is
  available. Every copy is re-hashed and compared to its source before the tool
  reports success. --verify re-checks an existing archive against its manifest.

What gets archived:
  --project NAME   agent_outputs/ (if present), projects/NAME/ (if present),
                   and the GATES.md approvals-log rows mentioning NAME,
                   extracted into GOVERNANCE_SUMMARY.md
  --paths P [P..]  explicit files or directories, relative to --root

Usage:
  python3 tools/archive_project.py --project NAME [--root DIR] [--out DIR] [--retention-note TEXT]
  python3 tools/archive_project.py --paths a.md dir/ [--root DIR] [--out DIR]
  python3 tools/archive_project.py --verify ARCHIVE_DIR_OR_MANIFEST

Honest limits:
  This is a plain-filesystem copy with hashes, not WORM storage: anyone with
  write access can alter the archive later (--verify would then fail). Hashes
  prove copy fidelity at archive time and file integrity at verify time; they
  do not prove the sources were correct. Deletion of originals is never done here.

Exit: 0 archived/verified clean; 1 on invalid input, any hash mismatch, or
missing files at verify time.
"""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time

import cambium_io  # noqa: F401

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST_NAME = "MANIFEST.json"


def _sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _git_commit(root):
    try:
        r = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root,
                           capture_output=True, text=True, timeout=10)
        if r.returncode == 0:
            return r.stdout.strip()
    except Exception:
        pass
    return None


def _iter_files(path):
    if os.path.isfile(path):
        yield path
        return
    for base, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for f in sorted(files):
            yield os.path.join(base, f)


def _gates_rows_mentioning(root, needle):
    """Extract Approvals-log rows from governance/GATES.md that mention needle.

    Empty needle matches every well-formed row. Returns list of raw row lines."""
    path = os.path.join(root, "governance", "GATES.md")
    if not os.path.isfile(path):
        return []
    lines = open(path, encoding="utf-8").read().splitlines()
    start = None
    for i, ln in enumerate(lines):
        if ln.strip().lower().startswith("## approvals log"):
            start = i + 1
            break
    if start is None:
        return []
    rows = []
    for ln in lines[start:]:
        s = ln.strip()
        if s.startswith("## "):
            break
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if all(c and set(c) <= set("-: ") for c in cells):
            continue
        if cells and cells[0].lower() == "gate":
            continue
        if not needle or needle.lower() in s.lower():
            rows.append(s)
    return rows


def build_archive(root, out_dir, project, paths, retention_note):
    """Copy sources into out_dir, verify copy hashes, write MANIFEST.json.

    Returns (n_files, mismatches)."""
    os.makedirs(out_dir, exist_ok=True)
    out_abs = os.path.abspath(out_dir)
    sources = []  # (source_abs, arc_rel)

    def _add_tree(rel_or_abs):
        src = rel_or_abs if os.path.isabs(rel_or_abs) else os.path.join(root, rel_or_abs)
        src = os.path.normpath(src)
        if not os.path.exists(src):
            return False
        for f in _iter_files(src):
            fa = os.path.abspath(f)
            if fa.startswith(out_abs + os.sep) or fa == out_abs:
                continue  # never archive the archive
            arc = os.path.relpath(fa, root) if fa.startswith(os.path.abspath(root) + os.sep) \
                else os.path.join("external", os.path.basename(fa))
            sources.append((fa, arc))
        return True

    missing_inputs = []
    if project:
        _add_tree("agent_outputs")
        if not _add_tree(os.path.join("projects", project)):
            print("[archive_project] note: projects/%s not present; skipping." % project)
    for p in paths or []:
        if not _add_tree(p):
            missing_inputs.append(p)
    if missing_inputs:
        print("[archive_project] ERROR: input path(s) not found under root: %s"
              % ", ".join(missing_inputs))
        return None, missing_inputs

    entries, mismatches = [], []
    for src, arc in sorted(set(sources)):
        dst = os.path.join(out_dir, arc)
        os.makedirs(os.path.dirname(dst) or out_dir, exist_ok=True)
        shutil.copy2(src, dst)
        src_sha, dst_sha = _sha256_file(src), _sha256_file(dst)
        if src_sha != dst_sha:
            mismatches.append(arc)
        entries.append({"path": arc.replace(os.sep, "/"), "sha256": dst_sha,
                        "bytes": os.path.getsize(dst), "origin": "copied"})

    rows = _gates_rows_mentioning(root, project or "")
    summary = os.path.join(out_dir, "GOVERNANCE_SUMMARY.md")
    with open(summary, "w", encoding="utf-8") as fh:
        fh.write("# Governance summary (extracted)\n\n")
        fh.write("Extracted from governance/GATES.md Approvals log on %s. Filter: %s.\n"
                 "The full ledger remains in the source repository.\n\n"
                 % (time.strftime("%Y-%m-%d"), project or "(none: all rows)"))
        fh.write("| Gate | Date | Approver | Decision | Notes |\n|---|---|---|---|---|\n")
        for r in rows:
            fh.write(r + "\n")
        if not rows:
            fh.write("\n(no matching approvals-log rows found)\n")
    entries.append({"path": "GOVERNANCE_SUMMARY.md", "sha256": _sha256_file(summary),
                    "bytes": os.path.getsize(summary), "origin": "generated"})

    manifest = {
        "schema": "cambium-archive-1",
        "created": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "root": os.path.abspath(root),
        "project": project,
        "retention_note": retention_note or "",
        "source_commit": _git_commit(root),
        "note": ("Copies only; originals were not moved or deleted. Hashes prove "
                 "copy fidelity at archive time, not the correctness of the sources."),
        "files": entries,
    }
    with open(os.path.join(out_dir, MANIFEST_NAME), "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)
    return len(entries), mismatches


def verify_archive(target):
    """Re-check an archive dir (or manifest path) against its MANIFEST.json."""
    manifest_path = target if target.endswith(".json") else os.path.join(target, MANIFEST_NAME)
    if not os.path.isfile(manifest_path):
        print("[archive_project] ERROR: manifest not found: %s" % manifest_path)
        return 1
    base = os.path.dirname(os.path.abspath(manifest_path))
    m = json.load(open(manifest_path, encoding="utf-8"))
    bad = 0
    for e in m.get("files", []):
        p = os.path.join(base, e["path"])
        if not os.path.isfile(p):
            print("  MISSING  %s" % e["path"]); bad += 1; continue
        if _sha256_file(p) != e["sha256"]:
            print("  ALTERED  %s (hash mismatch)" % e["path"]); bad += 1
        else:
            print("  ok       %s" % e["path"])
    if bad:
        print("[archive_project] VERIFY FAILED: %d file(s) missing or altered." % bad)
        return 1
    print("[archive_project] VERIFY OK: %d file(s) match the manifest." % len(m.get("files", [])))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Copy run artifacts into an archive dir with a hashed "
                    "MANIFEST.json; --verify re-checks an existing archive.")
    ap.add_argument("--root", default=REPO_ROOT, help="repository root (default: this repo)")
    ap.add_argument("--project", default=None, help="project name to archive")
    ap.add_argument("--paths", nargs="*", default=None, help="explicit paths (relative to root)")
    ap.add_argument("--out", default=None,
                    help="archive dir (default: <root>/archive/<name>-<YYYYMMDD>/)")
    ap.add_argument("--retention-note", default="", help="why this is kept and for how long")
    ap.add_argument("--verify", default=None, metavar="ARCHIVE",
                    help="verify an existing archive dir or MANIFEST.json and exit")
    a = ap.parse_args(argv)

    if a.verify:
        return verify_archive(a.verify)

    if not a.project and not a.paths:
        print("[archive_project] ERROR: give --project NAME or --paths P [P ...] (or --verify).")
        return 1
    root = os.path.abspath(a.root)
    if not os.path.isdir(root):
        print("[archive_project] ERROR: root does not exist: %s" % root)
        return 1

    name = a.project or "paths"
    out_dir = a.out or os.path.join(root, "archive", "%s-%s" % (name, time.strftime("%Y%m%d")))
    n, mismatches = build_archive(root, out_dir, a.project, a.paths, a.retention_note)
    if n is None:
        return 1
    if mismatches:
        print("[archive_project] HASH MISMATCH after copy: %s" % ", ".join(mismatches))
        return 1
    print("[archive_project] archived %d file(s) to %s" % (n, out_dir))
    print("[archive_project] copies only; no originals were moved or deleted. "
          "Advisory record, not WORM storage; re-check anytime with --verify.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
