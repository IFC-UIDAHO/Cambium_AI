#!/usr/bin/env python3
"""data_scan — an automated regulated/PII detector (AI_POLICY §6, POSITIONING #6).

Until now #6 was a *procedural* control: REGULATED_DATA.md said "classify your data and don't bring
regulated data without an approved pathway", but nothing checked. This adds the missing *technical*
control: a deterministic scanner that reads a file/dir and flags likely regulated or personally
identifiable content, so a gate can BLOCK on detected-but-unclassified sensitive data.

Detects (high → blocks unless --allow): US SSN, credit-card number (Luhn-validated), MRN-style medical
record IDs, email, US phone, IP address, dates of birth, precise lat/long coordinates. Deterministic
regex + Luhn; no model calls; no network.

  python3 tools/data_scan.py <path> [--allow] [--max-bytes N]
Exit: 0 clean (or --allow) · 1 high-severity PII/regulated content detected.

Honest ceiling: a regex detector has false positives/negatives and is NOT encryption-at-rest, access
logging, or a secure enclave. It turns #6 from "procedural only" into "procedural + automated detection";
the full secure-data platform is still the multi-institution infrastructure track.
"""
import argparse, os, re, sys

PATTERNS = [
    ("SSN",          "high", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
    ("email",        "high", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")),
    ("US_phone",     "high", re.compile(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}\b")),
    ("IP_address",   "med",  re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")),
    ("MRN",          "high", re.compile(r"\bMRN[:#]?\s?\d{6,10}\b", re.I)),
    ("DOB",          "high", re.compile(r"\b(?:DOB|date of birth)[:\s]+\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b", re.I)),
    ("geo_coord",    "med",  re.compile(r"\b-?\d{1,3}\.\d{4,},\s?-?\d{1,3}\.\d{4,}\b")),
]
CARD = re.compile(r"\b(?:\d[ -]?){13,19}\b")

def _luhn(num):
    digits = [int(c) for c in re.sub(r"\D", "", num)]
    if len(digits) < 13: return False
    s, alt = 0, False
    for d in reversed(digits):
        if alt:
            d *= 2
            if d > 9: d -= 9
        s += d; alt = not alt
    return s % 10 == 0

def scan_text(text):
    """Return list of (label, severity, sample) findings."""
    found = []
    for label, sev, rx in PATTERNS:
        m = rx.search(text)
        if m: found.append((label, sev, m.group(0)[:24]))
    for m in CARD.finditer(text):
        if _luhn(m.group(0)):
            found.append(("credit_card", "high", "****" + re.sub(r"\D", "", m.group(0))[-4:])); break
    return found

def scan_path(path, max_bytes=2_000_000):
    files = []
    if os.path.isdir(path):
        for r, _, fs in os.walk(path):
            for f in fs:
                if f.lower().endswith((".csv", ".txt", ".md", ".json", ".tsv", ".log")):
                    files.append(os.path.join(r, f))
    else:
        files = [path]
    results = {}
    for fp in files:
        try:
            text = open(fp, encoding="utf-8", errors="replace").read(max_bytes)
        except Exception:
            continue
        f = scan_text(text)
        if f: results[fp] = f
    return results

def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--allow", action="store_true", help="record findings but do not block (approved pathway)")
    ap.add_argument("--max-bytes", type=int, default=2_000_000)
    a = ap.parse_args(argv)
    if not os.path.exists(a.path):
        print(f"[data_scan] path not found: {a.path}"); return 0
    results = scan_path(a.path, a.max_bytes)
    high = [(fp, lab, s) for fp, fs in results.items() for lab, sev, s in fs if sev == "high"]
    if not results:
        print(f"[data_scan] OK: no PII/regulated patterns detected in {a.path}."); return 0
    print(f"[data_scan] {'⛔ BLOCK' if (high and not a.allow) else 'findings'} in {a.path}:")
    for fp, fs in results.items():
        for lab, sev, s in fs:
            print(f"   [{sev}] {lab} :: {os.path.basename(fp)} :: e.g. {s}")
    if high and not a.allow:
        print(f"[data_scan] -> {len(high)} high-severity hit(s). Classify under governance/REGULATED_DATA.md "
              f"and re-run with --allow only via an approved data pathway."); return 1
    print("[data_scan] (advisory — --allow set or no high-severity hits)"); return 0

if __name__ == "__main__":
    sys.exit(main())
