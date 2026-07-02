#!/usr/bin/env python3
"""audit_bundle - build a one-command evidence pack (zip) for an external auditor.

Purpose:
  Collect the governance evidence a non-technical auditor needs into one zip:
    - governance/GATES.md, the human approval ledger
    - the turn-level audit trail used by tools/audit_log.py (path discovered
      from that module), with its hash chain VERIFIED by calling audit_log.verify()
    - provenance manifests (provenance*.json) under examples/ and projects/
    - .claude-plugin/plugin.json for framework version identity
    - a generated INDEX.md at the zip root: a plain-language description and a
      SHA-256 for every included file, plus the chain verdict

Usage:
  python3 tools/audit_bundle.py [--root DIR] [--out bundle.zip] [--project NAME]

Honest limits:
  This is an EVIDENCE PACK, not a certification or an audit opinion. It copies
  records as they exist at --root and reports a hash-chain verdict; it cannot
  show events that were never recorded. If chain verification FAILS, the bundle
  is still written, marked FAILED, and the tool exits 1.

Exit: 0 bundle written, verification passed or nothing to verify;
      1 invalid input or hash-chain verification FAILED.
"""
import argparse
import contextlib
import glob
import hashlib
import io
import json
import os
import sys
import time
import zipfile

import cambium_io  # noqa: F401

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(TOOLS_DIR)

FOOTER = ("This bundle is an evidence pack assembled from repository records as they "
          "exist at build time. It is advisory material for an auditor. It is NOT a "
          "certification, an audit opinion, or a compliance guarantee.")

DESCRIPTIONS = {
    "governance/GATES.md":
        "The human approval ledger: which gate decisions were made, by whom, on what "
        "date, with notes. This is the record of human sign-off in the project.",
    ".claude-plugin/plugin.json":
        "Framework identity and version at the time this bundle was built.",
    "INDEX.md": "This file: a plain-language guide to the bundle.",
}


def _sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _import_audit_log():
    if TOOLS_DIR not in sys.path:
        sys.path.insert(0, TOOLS_DIR)
    import audit_log
    return audit_log


def verify_trail(root):
    """Locate the audit trail under root and verify it via audit_log.verify().

    Returns (trail_path, verdict, verify_output). verdict is one of
    PASSED / FAILED / NO TRAIL. The verify() function is the real one from
    tools/audit_log.py, pointed at the trail file under --root.
    """
    mod = _import_audit_log()
    rel = os.path.relpath(mod.TRAIL, mod.ROOT)
    trail = os.path.normpath(os.path.join(root, rel))
    old = mod.TRAIL
    mod.TRAIL = trail
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            rc = mod.verify()
    finally:
        mod.TRAIL = old
    out = buf.getvalue().strip()
    if not os.path.isfile(trail):
        return trail, "NO TRAIL", out
    return trail, ("PASSED" if rc == 0 else "FAILED"), out


def _describe(arcname):
    if arcname in DESCRIPTIONS:
        return DESCRIPTIONS[arcname]
    if arcname.endswith(".jsonl") and "audit_trail" in arcname:
        return ("Turn-level, hash-chained audit trail written by tools/audit_log.py. "
                "Each row links a query, agent, model, and human action by content "
                "hash. The chain verdict in this index says whether the file has "
                "been altered since it was written.")
    if "provenance" in os.path.basename(arcname).lower():
        return ("A machine-written provenance manifest: for verified claims it "
                "records the rerun command and content hashes that reproduce them.")
    return "Supporting record included from the repository."


def collect(root, project=None):
    """Return a list of (arcname, source_path) pairs for files that exist."""
    pairs = []

    def _add(rel):
        src = os.path.join(root, rel)
        if os.path.isfile(src):
            pairs.append((rel.replace(os.sep, "/"), src))
            return True
        return False

    _add(os.path.join("governance", "GATES.md"))
    _add(os.path.join(".claude-plugin", "plugin.json"))

    manifests = []
    for base in ("examples", "projects"):
        pattern = os.path.join(root, base, "**", "provenance*.json")
        manifests.extend(glob.glob(pattern, recursive=True))
    for src in sorted(set(manifests)):
        rel = os.path.relpath(src, root)
        if project and project.lower() not in rel.lower():
            continue
        pairs.append((rel.replace(os.sep, "/"), src))
    return pairs


def build_index(root, entries, verdict, verify_out, version, project):
    lines = []
    lines.append("# Evidence bundle index")
    lines.append("")
    lines.append("Generated: %s" % time.strftime("%Y-%m-%dT%H:%M:%S"))
    lines.append("Source root: %s" % root)
    lines.append("Framework version: %s" % (version or "unknown"))
    if project:
        lines.append("Project filter: %s" % project)
    lines.append("")
    lines.append("## Audit-trail hash-chain verdict: %s" % verdict)
    lines.append("")
    lines.append("Checked by calling verify() from tools/audit_log.py against the trail "
                 "file under the source root. Output:")
    lines.append("")
    lines.append("    %s" % (verify_out or "(no output)"))
    lines.append("")
    if verdict == "FAILED":
        lines.append("WARNING: the hash chain did NOT verify. At least one recorded row "
                     "was edited, inserted, or deleted after it was written. Treat the "
                     "trail as evidence of tampering, not as a clean record.")
        lines.append("")
    lines.append("## What is in this bundle")
    lines.append("")
    lines.append("| File in bundle | SHA-256 | What it is |")
    lines.append("|---|---|---|")
    for arcname, src in entries:
        lines.append("| %s | %s | %s |" % (arcname, _sha256_file(src), _describe(arcname)))
    missing = []
    if not any(a == "governance/GATES.md" for a, _ in entries):
        missing.append("governance/GATES.md (approval ledger) was not found at the root")
    if verdict == "NO TRAIL":
        missing.append("governance/audit_trail.jsonl does not exist yet; there is no "
                       "turn-level trail to verify")
    if missing:
        lines.append("")
        lines.append("## Not present at build time")
        lines.append("")
        for m in missing:
            lines.append("- " + m)
    lines.append("")
    lines.append("---")
    lines.append(FOOTER)
    lines.append("")
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Build a zip evidence pack (ledger, audit trail, provenance, "
                    "version) with a plain-language INDEX.md for an auditor.")
    ap.add_argument("--root", default=REPO_ROOT, help="repository root (default: this repo)")
    ap.add_argument("--out", default="bundle.zip", help="output zip path (default: bundle.zip)")
    ap.add_argument("--project", default=None, help="only include provenance manifests whose path mentions this project")
    a = ap.parse_args(argv)

    root = os.path.abspath(a.root)
    if not os.path.isdir(root):
        print("[audit_bundle] ERROR: root does not exist: %s" % root)
        return 1

    trail, verdict, verify_out = verify_trail(root)
    entries = collect(root, a.project)
    if os.path.isfile(trail):
        rel = os.path.relpath(trail, root).replace(os.sep, "/")
        entries.append((rel, trail))
    entries = sorted(set(entries))

    if not any(arc == "governance/GATES.md" for arc, _ in entries):
        print("[audit_bundle] WARNING: governance/GATES.md not found at root; noted in INDEX.md")

    version = None
    for arc, src in entries:
        if arc == ".claude-plugin/plugin.json":
            try:
                version = json.load(open(src, encoding="utf-8")).get("version")
            except Exception:
                version = None

    index_md = build_index(root, entries, verdict, verify_out, version, a.project)

    out = os.path.abspath(a.out)
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("INDEX.md", index_md)
        for arcname, src in entries:
            zf.write(src, arcname)

    print("[audit_bundle] root: %s" % root)
    for arcname, src in entries:
        print("  + %s" % arcname)
    print("  + INDEX.md (generated)")
    print("[audit_bundle] audit-trail verdict: %s" % verdict)
    print("[audit_bundle] wrote %s (%d files + INDEX.md)" % (out, len(entries)))
    print("BUNDLE_SHA256 %s  %s" % (_sha256_file(out), out))
    print("[audit_bundle] evidence pack, not a certification; see INDEX.md footer.")
    return 1 if verdict == "FAILED" else 0


if __name__ == "__main__":
    sys.exit(main())
