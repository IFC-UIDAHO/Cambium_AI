#!/usr/bin/env python3
"""retraction_check -- cited-DOI hygiene against Crossref update records.

Extracts DOIs from a BibTeX file (regex-based) or takes them on the
command line, then asks the Crossref REST API
(https://api.crossref.org/works/DOI) whether each work carries update
records ("updated-by" or "update-to" entries, or relation keys) of type
retraction, removal, withdrawal, expression of concern, correction,
erratum, or corrigendum.

Source and check-date semantics: the only source consulted is Crossref
(api.crossref.org; response fields as documented by Crossref, encoding
written 2026-07-01). Statuses reflect Crossref's records at the moment
the tool runs, and the report prints the check date. OK means "no such
update record was found in Crossref on the check date". It does NOT prove
the work is sound: coverage depends on what publishers deposit, and some
retractions never reach Crossref metadata. This check is advisory, not a
certification. For high-stakes work also consult the Retraction Watch
database and the publisher's site.

Statuses (severity order RETRACTED > CONCERN > CORRECTED when several
updates exist): OK, RETRACTED, CORRECTED, CONCERN (expression of
concern), UNCHECKED (network failure, DOI not found in Crossref, or no
fixture entry).

Offline behavior: any network failure marks that DOI UNCHECKED and the
run still exits 0, with a clear note to re-run online. --input-json FILE
replaces the network entirely with a JSON mapping of doi to a Crossref
response fragment (either the full response or just the "message"
object); used for fully offline tests.

DOI extraction: a regex for "10." followed by 4-9 digits, a slash, and a
suffix, applied to the raw .bib text; trailing punctuation is stripped,
so a DOI that genuinely ends in ")" or "." can be mangled (rare). DOIs
are compared lowercased (DOIs are case-insensitive).

Exit codes:
  0  -- report printed (UNCHECKED and advisory findings included)
  1  -- invalid input (missing/unreadable files, no DOIs found), or
        --strict with at least one RETRACTED DOI (only then)
  2  -- argparse usage errors (argparse default)

Usage:
  python3 tools/retraction_check.py --bib refs.bib
  python3 tools/retraction_check.py --dois 10.1000/x 10.1000/y --strict
  python3 tools/retraction_check.py --dois 10.1000/x --input-json fixture.json
  python3 tools/retraction_check.py --bib refs.bib --out hygiene.md
"""
from __future__ import annotations
import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime

# UTF-8 stdout guard
import cambium_io  # noqa: F401

TOOL = "retraction_check"

DOI_RE = re.compile(r"""10\.\d{4,9}/[^\s"'<>{},;]+""")
TRAILING_PUNCT = ".,;:)]}"
CROSSREF_API = "https://api.crossref.org/works/"
USER_AGENT = "cambium-retraction-check/1.0 (advisory research tool)"
SEVERITY = {"RETRACTED": 3, "CONCERN": 2, "CORRECTED": 1}
STATUS_ORDER = ("OK", "RETRACTED", "CORRECTED", "CONCERN", "UNCHECKED")


def _fail(msg: str) -> None:
    print(f"[{TOOL}] ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# DOI extraction
# ---------------------------------------------------------------------------

def extract_dois(text: str) -> list[str]:
    """Extract unique, lowercased DOIs from raw text, in order of appearance."""
    found: list[str] = []
    for raw in DOI_RE.findall(text):
        doi = raw.rstrip(TRAILING_PUNCT).lower()
        if doi and doi not in found:
            found.append(doi)
    return found


# ---------------------------------------------------------------------------
# Classification of Crossref work metadata
# ---------------------------------------------------------------------------

def classify_update_type(raw_type: str) -> str | None:
    t = raw_type.lower().replace("_", " ").replace("-", " ")
    if "retract" in t or "removal" in t or "withdraw" in t:
        return "RETRACTED"
    if "concern" in t:
        return "CONCERN"
    if "correct" in t or "erratum" in t or "corrigendum" in t:
        return "CORRECTED"
    return None


def classify_message(message: dict) -> tuple[str, str]:
    """Inspect updated-by / update-to / relation fields of a works record."""
    findings: list[tuple[str, str]] = []
    for key in ("updated-by", "update-to"):
        entries = message.get(key)
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            status = classify_update_type(str(entry.get("type", "")))
            if status:
                notice = str(entry.get("DOI", "")).lower() or "notice DOI not given"
                findings.append((status, f"{key}: {entry.get('type')} ({notice})"))
    relation = message.get("relation")
    if isinstance(relation, dict):
        for rel_key in relation:
            status = classify_update_type(str(rel_key))
            if status:
                findings.append((status, f"relation: {rel_key}"))
    if not findings:
        return "OK", "no retraction, correction, or concern update records found"
    findings.sort(key=lambda f: -SEVERITY[f[0]])
    detail = "; ".join(d for _, d in findings)
    return findings[0][0], detail


# ---------------------------------------------------------------------------
# Crossref fetch (network) -- graceful on any failure
# ---------------------------------------------------------------------------

def check_online(doi: str, timeout: float) -> tuple[str, str, bool]:
    """Query Crossref for one DOI. Return (status, detail, network_failed)."""
    url = CROSSREF_API + urllib.parse.quote(doi, safe="")
    req = urllib.request.Request(
        url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="replace"))
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return ("UNCHECKED",
                    "DOI not found in Crossref (may be registered elsewhere, e.g. DataCite)",
                    False)
        return "UNCHECKED", f"Crossref HTTP error {exc.code}; re-run to retry", True
    except Exception as exc:
        return ("UNCHECKED",
                f"network failure ({type(exc).__name__}); re-run with connectivity",
                True)
    message = data.get("message") if isinstance(data, dict) else None
    if not isinstance(message, dict):
        return "UNCHECKED", "unexpected Crossref response shape", True
    status, detail = classify_message(message)
    return status, detail, False


# ---------------------------------------------------------------------------
# Report builder
# ---------------------------------------------------------------------------

def build_report(rows: list[tuple[str, str, str]], source_desc: str,
                 checked_desc: str, network_failures: int) -> tuple[str, dict]:
    counts = {status: 0 for status in STATUS_ORDER}
    for _, status, _ in rows:
        counts[status] += 1

    lines: list[str] = []
    lines.append("# Cited-DOI hygiene report (Crossref update records, advisory)")
    lines.append("")
    lines.append(f"- Source: {source_desc}")
    lines.append(f"- Checked: {checked_desc}")
    lines.append("- Statuses: OK, RETRACTED, CORRECTED, CONCERN, UNCHECKED")
    lines.append("")
    lines.append("| DOI | Status | Detail |")
    lines.append("|---|---|---|")
    for doi, status, detail in rows:
        lines.append(f"| {doi} | {status} | {detail.replace('|', '/')} |")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- DOIs checked: {len(rows)}")
    for status in STATUS_ORDER:
        lines.append(f"- {status}: {counts[status]}")
    lines.append("")
    if network_failures:
        lines.append(
            f"NOTE: {network_failures} DOI(s) could not be checked because the "
            "network or Crossref was unavailable; they are marked UNCHECKED and "
            "the exit code stays 0. Re-run with connectivity to complete the check."
        )
        lines.append("")
    lines.append(
        "OK means no retraction, correction, or expression-of-concern update "
        "record was found in Crossref at check time. Coverage depends on what "
        "publishers deposit, so the absence of a flag is not proof of "
        "integrity. This report is advisory, not a certification; for "
        "high-stakes work also consult the Retraction Watch database and the "
        "publisher's site."
    )
    lines.append("")
    return "\n".join(lines), counts


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(
        description=(
            "Check cited DOIs against Crossref update records (retraction, "
            "correction, expression of concern). Advisory, not a certification: "
            "OK only means no update record was found in Crossref at check time."
        )
    )
    ap.add_argument("--bib", default=None,
                    help="BibTeX file; DOIs are extracted with a regex.")
    ap.add_argument("--dois", nargs="+", default=None,
                    help="One or more DOIs to check.")
    ap.add_argument("--input-json", dest="input_json", default=None,
                    help="JSON fixture mapping doi -> Crossref response fragment; "
                         "replaces the network entirely (for offline tests).")
    ap.add_argument("--timeout", type=float, default=10.0,
                    help="Per-request network timeout in seconds (default 10).")
    ap.add_argument("--out", default=None,
                    help="Output path (default: print to stdout).")
    ap.add_argument("--strict", action="store_true",
                    help="Exit 1 if any DOI is RETRACTED (only then).")
    args = ap.parse_args(argv)

    if not args.bib and not args.dois:
        _fail("provide --bib and/or --dois")

    dois: list[str] = []
    source_bits: list[str] = []
    if args.bib:
        if not os.path.exists(args.bib):
            _fail(f"bib file not found: {args.bib}")
        try:
            with open(args.bib, encoding="utf-8", errors="replace") as fh:
                bib_text = fh.read()
        except OSError as exc:
            _fail(f"cannot read bib file: {args.bib}\n  {exc}")
        bib_dois = extract_dois(bib_text)
        dois.extend(bib_dois)
        source_bits.append(f"{args.bib} ({len(bib_dois)} DOIs extracted)")
    if args.dois:
        for raw in args.dois:
            match = DOI_RE.search(raw)
            if not match:
                _fail(f"not a recognizable DOI: {raw}")
            doi = match.group(0).rstrip(TRAILING_PUNCT).lower()
            if doi not in dois:
                dois.append(doi)
        source_bits.append(f"{len(args.dois)} DOI(s) from --dois")
    if not dois:
        _fail("no DOIs found in the inputs")
    source_desc = "; ".join(source_bits)

    fixture = None
    if args.input_json:
        if not os.path.exists(args.input_json):
            _fail(f"fixture file not found: {args.input_json}")
        try:
            with open(args.input_json, encoding="utf-8") as fh:
                raw_map = json.load(fh)
        except (OSError, json.JSONDecodeError) as exc:
            _fail(f"cannot parse fixture file: {args.input_json}\n  {exc}")
        if not isinstance(raw_map, dict):
            _fail("fixture must be a JSON object mapping doi -> response fragment")
        fixture = {str(k).lower(): v for k, v in raw_map.items()}

    rows: list[tuple[str, str, str]] = []
    network_failures = 0
    for doi in dois:
        if fixture is not None:
            fragment = fixture.get(doi)
            if fragment is None:
                rows.append((doi, "UNCHECKED",
                             "no fixture entry for this DOI (fixture mode; network not used)"))
                continue
            if isinstance(fragment, dict) and isinstance(fragment.get("message"), dict):
                message = fragment["message"]
            else:
                message = fragment
            if not isinstance(message, dict):
                rows.append((doi, "UNCHECKED", "fixture entry is not an object"))
                continue
            status, detail = classify_message(message)
            rows.append((doi, status, detail))
        else:
            status, detail, failed = check_online(doi, args.timeout)
            if failed:
                network_failures += 1
            rows.append((doi, status, detail))

    if fixture is not None:
        checked_desc = "fixture mode (offline test data; no network queries made)"
    else:
        today = datetime.utcnow().strftime("%Y-%m-%d")
        checked_desc = f"{today} via api.crossref.org (statuses reflect Crossref records on this date)"

    report, counts = build_report(rows, source_desc, checked_desc, network_failures)

    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(report)
        print(f"[{TOOL}] wrote {args.out}")
    else:
        sys.stdout.write(report)

    if counts["RETRACTED"]:
        print(f"[{TOOL}] advisory: {counts['RETRACTED']} RETRACTED DOI(s) found",
              file=sys.stderr)
        if args.strict:
            print(f"[{TOOL}] STRICT: retracted work cited, exiting 1", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
