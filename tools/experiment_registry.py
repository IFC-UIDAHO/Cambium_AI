#!/usr/bin/env python3
"""experiment_registry -- local preregistration ledger for hypotheses and analysis plans.

The point: a hypothesis, analysis plan, or protocol registered BEFORE the study
or analysis runs is later provably unchanged. This tool computes a sha256 of the
registered content (a file or inline text) and appends one CSV row to a ledger.
Later, `verify` recomputes the hash of the current file/text and compares it to
the row recorded at registration time, so tampering (or honest drift) is caught.

This is a local, append-only ledger, not a public preregistration service (such
as OSF Registries or ClinicalTrials.gov). It proves internal consistency between
what was registered and what exists now; it does not provide a third-party
timestamp or public attestation. For that, use a public registry as well.

Subcommands:
  register  --file plan.md [--title "..."] [--ledger path.csv]
  register  --text "..."   --title "..."   [--ledger path.csv]
  verify    --id <id> [--file plan.md | --text "..."] [--ledger path.csv]
  verify    --title "..."  [--file plan.md | --text "..."] [--ledger path.csv]
  list      [--ledger path.csv]

Ledger columns: id, date_iso, title, sha256, source (file path or "(inline)")

Exit codes:
  0  -- success (registered / verified match / listed)
  1  -- verify found a mismatch (tampered or drifted content), or missing row
  2  -- bad input (missing file, no content given, missing ledger, bad args)

Usage:
  python3 tools/experiment_registry.py register --file plan.md --title "H1 analysis plan"
  python3 tools/experiment_registry.py register --text "H1: X > Y" --title "H1"
  python3 tools/experiment_registry.py verify --title "H1" --file plan.md
  python3 tools/experiment_registry.py list
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import os
import sys
from datetime import datetime, timezone

# UTF-8 stdout guard
import cambium_io  # noqa: F401

DEFAULT_LEDGER = os.path.join("governance", "EXPERIMENT_REGISTRY.csv")
FIELDS = ["id", "date_iso", "title", "sha256", "source"]


# ---------------------------------------------------------------------------
# Content + hashing
# ---------------------------------------------------------------------------

def _read_content(file_path: str | None, text: str | None, label: str) -> tuple[str, str]:
    """Return (content, source_label). Exits 2 if neither or both are missing/unreadable."""
    if file_path and text is not None:
        print(f"[experiment_registry] ERROR: give --file OR --text for {label}, not both", file=sys.stderr)
        sys.exit(2)
    if file_path:
        if not os.path.exists(file_path):
            print(f"[experiment_registry] ERROR: file not found: {file_path}", file=sys.stderr)
            sys.exit(2)
        try:
            with open(file_path, encoding="utf-8") as fh:
                return fh.read(), file_path
        except OSError as exc:
            print(f"[experiment_registry] ERROR: cannot read {file_path}\n  {exc}", file=sys.stderr)
            sys.exit(2)
    if text is not None:
        return text, "(inline)"
    print(f"[experiment_registry] ERROR: give --file or --text for {label}", file=sys.stderr)
    sys.exit(2)


def _sha256(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Ledger I/O
# ---------------------------------------------------------------------------

def _read_ledger(ledger_path: str) -> list[dict]:
    if not os.path.exists(ledger_path):
        return []
    with open(ledger_path, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def _write_ledger(ledger_path: str, rows: list[dict]) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(ledger_path)) or ".", exist_ok=True)
    with open(ledger_path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in FIELDS})


def _next_id(rows: list[dict]) -> str:
    n = 0
    for row in rows:
        rid = row.get("id", "")
        if rid.startswith("EXP") and rid[3:].isdigit():
            n = max(n, int(rid[3:]))
    return f"EXP{n + 1:04d}"


# ---------------------------------------------------------------------------
# Subcommands
# ---------------------------------------------------------------------------

def cmd_register(args) -> int:
    content, source = _read_content(args.file, args.text, "register")
    title = args.title or ""
    if not title:
        print("[experiment_registry] ERROR: --title is required for register", file=sys.stderr)
        return 2

    rows = _read_ledger(args.ledger)
    for row in rows:
        if row.get("title", "").strip().lower() == title.strip().lower():
            print(
                f"[experiment_registry] WARNING: a row already exists with title '{title}' "
                f"(id {row.get('id')}). Registering a new row anyway; titles are not unique keys.",
                file=sys.stderr,
            )
            break

    row = {
        "id": _next_id(rows),
        "date_iso": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "title": title,
        "sha256": _sha256(content),
        "source": source,
    }
    rows.append(row)
    _write_ledger(args.ledger, rows)
    print(f"[experiment_registry] registered {row['id']} '{title}' sha256={row['sha256'][:12]}... -> {args.ledger}")
    return 0


def cmd_verify(args) -> int:
    if not os.path.exists(args.ledger):
        print(f"[experiment_registry] ERROR: ledger not found: {args.ledger}", file=sys.stderr)
        return 1

    rows = _read_ledger(args.ledger)
    match = None
    if args.id:
        match = next((r for r in rows if r.get("id") == args.id), None)
        key_desc = f"id '{args.id}'"
    elif args.title:
        matches = [r for r in rows if r.get("title", "").strip().lower() == args.title.strip().lower()]
        match = matches[-1] if matches else None
        key_desc = f"title '{args.title}'"
    else:
        print("[experiment_registry] ERROR: verify needs --id or --title", file=sys.stderr)
        return 2

    if match is None:
        print(f"[experiment_registry] TAMPERED/MISSING: no registered row found for {key_desc}", file=sys.stderr)
        return 1

    content, _source = _read_content(args.file, args.text, "verify")
    current_hash = _sha256(content)
    registered_hash = match.get("sha256", "")

    if current_hash == registered_hash:
        print(f"[experiment_registry] OK: content matches registered row {match['id']} '{match['title']}' "
              f"(registered {match['date_iso']}). sha256={current_hash[:12]}...")
        return 0

    print(
        f"[experiment_registry] TAMPERED: content does NOT match registered row {match['id']} "
        f"'{match['title']}' (registered {match['date_iso']}).\n"
        f"  registered sha256: {registered_hash}\n"
        f"  current    sha256: {current_hash}",
        file=sys.stderr,
    )
    return 1


def cmd_list(args) -> int:
    if not os.path.exists(args.ledger):
        print(f"[experiment_registry] ledger not found: {args.ledger} (nothing registered yet)")
        return 0
    rows = _read_ledger(args.ledger)
    if not rows:
        print(f"[experiment_registry] ledger is empty: {args.ledger}")
        return 0
    widths = {f: max(len(f), max((len(r.get(f, "")) for r in rows), default=0)) for f in FIELDS}
    header = " | ".join(f.ljust(widths[f]) for f in FIELDS)
    print(header)
    print("-+-".join("-" * widths[f] for f in FIELDS))
    for r in rows:
        print(" | ".join(r.get(f, "").ljust(widths[f]) for f in FIELDS))
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Local preregistration ledger: register a hypothesis/plan, verify it later is unchanged."
    )
    ap.add_argument("--ledger", default=DEFAULT_LEDGER, help="Path to the ledger CSV (default: governance/EXPERIMENT_REGISTRY.csv).")
    sub = ap.add_subparsers(dest="cmd", required=True)

    reg = sub.add_parser("register", help="Register a hypothesis or analysis plan.")
    reg.add_argument("--file", default=None, help="Path to the plan file.")
    reg.add_argument("--text", default=None, help="Inline plan text (alternative to --file).")
    reg.add_argument("--title", default=None, help="Title for this registration (required).")

    ver = sub.add_parser("verify", help="Verify current content matches a registered row.")
    ver.add_argument("--file", default=None, help="Path to the current plan file to check.")
    ver.add_argument("--text", default=None, help="Inline current plan text (alternative to --file).")
    ver.add_argument("--id", default=None, help="Registered row id to check against (e.g. EXP0001).")
    ver.add_argument("--title", default=None, help="Registered row title to check against.")

    sub.add_parser("list", help="Print the ledger as a table.")

    args = ap.parse_args(argv)

    if args.cmd == "register":
        return cmd_register(args)
    if args.cmd == "verify":
        return cmd_verify(args)
    if args.cmd == "list":
        return cmd_list(args)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
