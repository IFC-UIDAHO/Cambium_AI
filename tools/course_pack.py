#!/usr/bin/env python3
"""course_pack - assemble a markdown course pack from learning packets and refs.

Purpose:
  Build one instructor-ready markdown course pack: a syllabus header, one
  section per week (topic, objectives auto-drawn from packet headings,
  readings assigned round-robin from a refs.bib, and a lab pointer), and an
  instructor note stating that everything derives from the named sources.

Inputs:
  --title TEXT          course title (required)
  --weeks N             number of weeks (default 6)
  --labs DIR [DIR ...]  directories of learning packets / explainer markdown,
                        e.g. academy/labs or a dir holding filled
                        learning_packet.md copies
  --refs refs.bib       optional BibTeX, parsed with a light regex
                        (title / author / year fields only)
  --outline FILE        optional YAML mapping week number -> topic
  --out FILE            write here instead of stdout

Usage:
  python3 tools/course_pack.py --title "Responsible AI Research" --weeks 6 \
      --labs academy/labs --refs refs.bib --outline outline.yml --out pack.md

Exit codes: 0 on success; 1 on invalid input (missing dir/file, bad outline,
weeks < 1, or nothing at all to build from).

Honest limits:
  Nothing is invented: topics come from your outline or the packet titles,
  objectives are packet headings taken verbatim (auto-extracted, review
  before teaching), and readings come only from the given refs.bib. The
  BibTeX parser is a light regex: it reads simple brace- or quote-delimited
  title/author/year fields and does not resolve nested braces; entries it
  cannot parse keep only their citation key. Ordering is deterministic
  (packets sorted by path, refs in file order, round-robin assignment).
"""
import argparse
import datetime
import glob
import os
import re
import sys

import cambium_io  # noqa: F401

HEADING_STOP = {
    "flashcards", "quick quiz", "glossary", "go deeper", "contents",
    "references", "license", "answer",
}

BIB_FIELD_RE = re.compile(r'(\w+)\s*=\s*[{"]([^{}"]*)[}"]')


def parse_packet(path):
    """Title (first h1) and objective headings (h2/h3) from one packet file."""
    text = open(path, encoding="utf-8", errors="replace").read()
    title, headings = None, []
    for line in text.splitlines():
        m = re.match(r"^(#{1,3})\s+(.+?)\s*$", line)
        if not m:
            continue
        level = len(m.group(1))
        htext = m.group(2).strip().rstrip(":")
        htext = re.sub(r"^Learning Packet:\s*", "", htext, flags=re.IGNORECASE)
        if level == 1 and title is None:
            title = htext
        elif level >= 2 and htext.lower() not in HEADING_STOP and "__FILL__" not in htext:
            headings.append(htext)
    stem = os.path.splitext(os.path.basename(path))[0]
    return {"path": path.replace(os.sep, "/"),
            "title": title or stem,
            "objectives": headings[:5]}


def scan_packets(dirs):
    """All *.md under the given dirs, sorted by path for determinism."""
    files = []
    for d in dirs:
        if not os.path.isdir(d):
            raise ValueError("labs directory not found: %s" % d)
        files.extend(glob.glob(os.path.join(d, "**", "*.md"), recursive=True))
    return [parse_packet(p) for p in sorted(set(files))]


def parse_bib(path):
    """Light regex BibTeX parser: key + title/author/year per entry, file order."""
    if not os.path.isfile(path):
        raise ValueError("refs file not found: %s" % path)
    text = open(path, encoding="utf-8", errors="replace").read()
    refs = []
    for chunk in re.split(r"(?m)^\s*@", text)[1:]:
        m = re.match(r"(\w+)\s*\{\s*([^,\s]+)\s*,", chunk)
        if not m or m.group(1).lower() in ("comment", "preamble", "string"):
            continue
        fields = {k.lower(): v.strip() for k, v in BIB_FIELD_RE.findall(chunk)}
        refs.append({"key": m.group(2),
                     "title": fields.get("title", ""),
                     "author": fields.get("author", ""),
                     "year": fields.get("year", "")})
    return refs


def fmt_ref(r):
    parts = []
    if r["author"]:
        parts.append(r["author"])
    if r["year"]:
        parts.append("(%s)" % r["year"])
    lead = " ".join(parts)
    title = r["title"] or "(title not parsed)"
    if lead:
        return "%s. %s. [%s]" % (lead, title.rstrip("."), r["key"])
    return "%s. [%s]" % (title.rstrip("."), r["key"])


def parse_outline(path):
    """YAML week -> topic mapping. Falls back to 'N: topic' lines without pyyaml."""
    if not os.path.isfile(path):
        raise ValueError("outline file not found: %s" % path)
    text = open(path, encoding="utf-8", errors="replace").read()
    try:
        import yaml  # pyyaml is an allowed dependency; fallback below if absent
        data = yaml.safe_load(text)
    except ImportError:
        data = {}
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith("#") or ":" not in line:
                continue
            k, v = line.split(":", 1)
            data[k.strip()] = v.strip().strip("'\"")
    if not isinstance(data, dict):
        raise ValueError("outline must be a mapping of week number -> topic")
    out = {}
    for k, v in data.items():
        try:
            out[int(k)] = str(v).strip()
        except (TypeError, ValueError):
            raise ValueError("outline keys must be week numbers, got %r" % (k,))
    return out


def build_pack(title, weeks, packets, refs, outline, sources):
    today = datetime.date.today().isoformat()
    lines = [
        "# %s" % title,
        "",
        "A %d-week course pack. Generated %s by tools/course_pack.py." % (weeks, today),
        "",
        "## Sources",
        "",
    ]
    lines += ["- %s" % s for s in sources] or ["- (none)"]
    lines += [
        "",
        "> Instructor note: all content in this pack derives from the sources",
        "> named above; nothing was invented. Weekly objectives are packet",
        "> headings taken verbatim (auto-extracted, review before teaching).",
        "> Review and edit the whole pack before running the course.",
        "",
    ]
    week_refs = {w: [] for w in range(1, weeks + 1)}
    for i, r in enumerate(refs):
        week_refs[(i % weeks) + 1].append(r)

    for w in range(1, weeks + 1):
        packet = packets[(w - 1) % len(packets)] if packets else None
        topic = outline.get(w) or (packet["title"] if packet else "To be set by the instructor")
        lines += ["## Week %d: %s" % (w, topic), ""]
        if packet:
            lines.append("Lab: %s" % packet["path"])
            if packet["objectives"]:
                lines += ["",
                          "Objectives (auto-drawn from packet headings, review before teaching):",
                          ""]
                lines += ["- %s" % o for o in packet["objectives"]]
        else:
            lines.append("Lab: none assigned (no packets found in the given directories).")
        lines += ["", "Readings:"]
        assigned = week_refs[w]
        if assigned:
            lines += ["- %s" % fmt_ref(r) for r in assigned]
        else:
            lines.append("- none assigned this week")
        lines.append("")
    return "\n".join(lines) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Build a markdown course pack from learning packets and refs.")
    ap.add_argument("--title", required=True, help="course title")
    ap.add_argument("--weeks", type=int, default=6, help="number of weeks (default 6)")
    ap.add_argument("--labs", nargs="+", default=[],
                    help="directories holding learning packets (*.md)")
    ap.add_argument("--refs", help="optional refs.bib (light regex parse)")
    ap.add_argument("--outline", help="optional YAML mapping week -> topic")
    ap.add_argument("--out", help="write the pack here instead of stdout")
    a = ap.parse_args(argv)

    if a.weeks < 1:
        print("[course_pack] --weeks must be at least 1", file=sys.stderr)
        return 1
    try:
        packets = scan_packets(a.labs) if a.labs else []
        refs = parse_bib(a.refs) if a.refs else []
        outline = parse_outline(a.outline) if a.outline else {}
    except ValueError as exc:
        print("[course_pack] %s" % exc, file=sys.stderr)
        return 1
    if not packets and not refs:
        print("[course_pack] nothing to build from: pass --labs with packets "
              "and/or --refs", file=sys.stderr)
        return 1

    sources = ["labs dir: %s" % d for d in a.labs]
    if a.refs:
        sources.append("refs: %s" % a.refs)
    if a.outline:
        sources.append("outline: %s" % a.outline)

    pack = build_pack(a.title, a.weeks, packets, refs, outline, sources)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as fh:
            fh.write(pack)
    else:
        sys.stdout.write(pack)
    print("[course_pack] %d weeks, %d packets, %d refs -> %s"
          % (a.weeks, len(packets), len(refs), a.out or "stdout"), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
