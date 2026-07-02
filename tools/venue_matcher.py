#!/usr/bin/env python3
"""venue_matcher -- coarse lexical matcher from an abstract to candidate venues.

Scores candidate publication venues by transparent keyword overlap with an
abstract: a venue's score is the number of distinct profile keywords found
in the abstract text, and every matched term is reported so you can see
exactly why a venue ranked where it did. This is a coarse lexical
heuristic, advisory only. It is not editorial advice, not a quality
signal, and knows nothing about your paper beyond word overlap. Discuss
venue choice with coauthors and mentors.

Ships a small built-in starter set of 12 real, well-known venues with
deliberately coarse descriptors (author-curated starter list, written
2026-07-01; these are editable examples, edit for your field). Replace
the set entirely with --profiles profiles.yml:

  - name: Journal of X
    scope: [keyword, "multi word phrase"]
    methods: [keyword]
    notes: one honest line about the venue

Matching: the abstract is lowercased and tokenized on alphanumeric runs.
Single-word keywords match whole tokens; multi-word keywords match as
phrases in the normalized text. There is no stemming, so singular and
plural forms must match exactly. Scope and methods keywords are weighted
equally; ties are broken alphabetically for determinism.

Exit codes:
  0  -- report printed (including the zero-overlap case)
  1  -- invalid input (missing/unreadable/empty abstract, malformed profiles)
  2  -- argparse usage errors (argparse default)

Usage:
  python3 tools/venue_matcher.py --abstract abstract.txt
  python3 tools/venue_matcher.py --abstract abstract.txt --k 3
  python3 tools/venue_matcher.py --abstract abstract.txt --profiles my_field.yml --out venues.md
"""
from __future__ import annotations
import argparse
import os
import re
import sys

# UTF-8 stdout guard
import cambium_io  # noqa: F401

try:
    import yaml
except ImportError:  # pyyaml is expected in this repo
    yaml = None

TOOL = "venue_matcher"

# Author-curated starter list, written 2026-07-01. Editable examples with
# deliberately coarse descriptors, not an authoritative ranking of venues.
# Replace the whole set with --profiles for your field.
BUILTIN_PROFILES: list[dict] = [
    {
        "name": "Nature",
        "scope": ["multidisciplinary", "biology", "physics", "chemistry",
                  "medicine", "earth science", "climate"],
        "methods": ["experiment", "observation", "theory", "modeling"],
        "notes": "Highly selective multidisciplinary journal; expects advances of broad interest.",
    },
    {
        "name": "Science",
        "scope": ["multidisciplinary", "biology", "physics", "chemistry",
                  "medicine", "policy", "climate"],
        "methods": ["experiment", "observation", "theory", "modeling"],
        "notes": "Highly selective multidisciplinary journal published by AAAS.",
    },
    {
        "name": "PNAS",
        "scope": ["multidisciplinary", "biology", "social science",
                  "physical science", "medicine"],
        "methods": ["experiment", "observation", "modeling", "statistics"],
        "notes": "Broad-scope journal of the US National Academy of Sciences.",
    },
    {
        "name": "Nature Communications",
        "scope": ["multidisciplinary", "biology", "physics", "chemistry", "earth science"],
        "methods": ["experiment", "modeling", "data analysis"],
        "notes": "Open-access multidisciplinary journal; selective, broader than Nature.",
    },
    {
        "name": "Scientific Reports",
        "scope": ["multidisciplinary", "natural science", "engineering", "psychology"],
        "methods": ["experiment", "observation", "modeling"],
        "notes": "Open-access mega-journal; reviews for soundness rather than perceived impact.",
    },
    {
        "name": "PLOS ONE",
        "scope": ["multidisciplinary", "science", "medicine", "engineering"],
        "methods": ["experiment", "observation", "statistics", "meta-analysis"],
        "notes": "Open-access mega-journal; soundness-based review, broad scope.",
    },
    {
        "name": "NeurIPS",
        "scope": ["machine learning", "artificial intelligence", "neural network",
                  "deep learning", "reinforcement learning"],
        "methods": ["benchmark", "algorithm", "optimization", "theory", "training"],
        "notes": "Top machine-learning conference; values novelty with strong empirical or theoretical support.",
    },
    {
        "name": "ICML",
        "scope": ["machine learning", "deep learning", "artificial intelligence",
                  "representation learning"],
        "methods": ["algorithm", "optimization", "benchmark", "theory", "generalization"],
        "notes": "Top machine-learning conference with a methodological focus.",
    },
    {
        "name": "Bioinformatics (Oxford)",
        "scope": ["bioinformatics", "computational biology", "genomics", "sequence", "omics"],
        "methods": ["software", "algorithm", "pipeline", "database", "statistics"],
        "notes": "Methods and software for biological data analysis.",
    },
    {
        "name": "Ecology Letters",
        "scope": ["ecology", "biodiversity", "species", "ecosystem",
                  "community ecology", "population"],
        "methods": ["field experiment", "meta-analysis", "modeling", "observation"],
        "notes": "Selective ecology journal favoring concise, high-novelty papers.",
    },
    {
        "name": "Forest Ecology and Management",
        "scope": ["forest", "forestry", "silviculture", "timber", "stand",
                  "wildfire", "plantation"],
        "methods": ["field experiment", "inventory", "growth model", "remote sensing"],
        "notes": "Applied forest science and management; strong practitioner readership.",
    },
    {
        "name": "IEEE TPAMI",
        "scope": ["computer vision", "pattern recognition", "image",
                  "machine learning", "video"],
        "methods": ["algorithm", "benchmark", "deep learning", "segmentation", "detection"],
        "notes": "Selective journal for computer vision and pattern analysis.",
    },
]


def _fail(msg: str) -> None:
    print(f"[{TOOL}] ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


# ---------------------------------------------------------------------------
# Profile loading
# ---------------------------------------------------------------------------

def load_profiles(path: str | None) -> tuple[list[dict], str]:
    """Return (profiles, source description). Built-ins unless --profiles given."""
    if path is None:
        desc = (f"built-in starter list, {len(BUILTIN_PROFILES)} venues "
                "(author-curated examples; edit for your field)")
        return BUILTIN_PROFILES, desc
    if yaml is None:
        _fail("pyyaml is not installed; install pyyaml to use --profiles")
    if not os.path.exists(path):
        _fail(f"profiles file not found: {path}")
    try:
        with open(path, encoding="utf-8") as fh:
            data = yaml.safe_load(fh.read())
    except (OSError, yaml.YAMLError) as exc:
        _fail(f"cannot parse profiles file: {path}\n  {exc}")
    if not isinstance(data, list) or not data:
        _fail(f"profiles file must be a non-empty YAML list of venue mappings: {path}")
    profiles: list[dict] = []
    for i, item in enumerate(data):
        if not isinstance(item, dict) or not str(item.get("name", "")).strip():
            _fail(f"profiles[{i}] must be a mapping with a non-empty 'name'")
        profiles.append({
            "name": str(item["name"]).strip(),
            "scope": [str(k) for k in (item.get("scope") or [])],
            "methods": [str(k) for k in (item.get("methods") or [])],
            "notes": str(item.get("notes", "")).strip(),
        })
    return profiles, f"user profiles from {path}, {len(profiles)} venues"


# ---------------------------------------------------------------------------
# Scoring -- transparent keyword overlap
# ---------------------------------------------------------------------------

def match_profile(profile: dict, token_set: set[str], padded_text: str) -> list[str]:
    """Return the distinct normalized keywords of this profile found in the abstract."""
    matched: list[str] = []
    for kw in list(profile.get("scope") or []) + list(profile.get("methods") or []):
        kw_tokens = _tokens(str(kw))
        if not kw_tokens:
            continue
        norm = " ".join(kw_tokens)
        if norm in matched:
            continue
        if len(kw_tokens) == 1:
            hit = norm in token_set
        else:
            hit = f" {norm} " in padded_text
        if hit:
            matched.append(norm)
    return matched


# ---------------------------------------------------------------------------
# Report builder
# ---------------------------------------------------------------------------

def build_report(profiles: list[dict], source_desc: str, abstract_path: str,
                 tokens: list[str], k: int) -> str:
    token_set = set(tokens)
    padded_text = " " + " ".join(tokens) + " "
    scored = []
    for prof in profiles:
        matched = match_profile(prof, token_set, padded_text)
        scored.append((len(matched), prof, matched))
    scored.sort(key=lambda item: (-item[0], item[1]["name"].lower()))
    nonzero = [s for s in scored if s[0] > 0]
    top = nonzero[:k]

    lines: list[str] = []
    lines.append("# Venue match report (coarse lexical heuristic, advisory)")
    lines.append("")
    lines.append(f"- Abstract: {abstract_path} ({len(tokens)} tokens)")
    lines.append(f"- Profiles: {source_desc}")
    lines.append("- Scoring: count of distinct profile keywords found in the abstract")
    lines.append("")
    if not top:
        lines.append("## Matches")
        lines.append("")
        lines.append(
            "No venue had any keyword overlap with the abstract. That is a "
            "statement about word overlap, not about your paper. Edit the "
            "venue profiles for your field (--profiles) or check that the "
            "abstract file is the right one."
        )
    else:
        lines.append(f"## Top {len(top)} matches (of {len(nonzero)} venues with any overlap)")
        lines.append("")
        for rank, (score, prof, matched) in enumerate(top, 1):
            lines.append(f"### {rank}. {prof['name']} (score {score})")
            lines.append("")
            lines.append(f"- Matched terms: {', '.join(matched)}")
            if prof.get("notes"):
                lines.append(f"- Notes: {prof['notes']}")
            lines.append("")
        if len(nonzero) < k:
            lines.append(f"Only {len(nonzero)} venue(s) had any keyword overlap; "
                         f"fewer than the {k} requested.")
    lines.append("")
    lines.append("## Caveat")
    lines.append("")
    lines.append(
        "Scores are raw keyword-overlap counts between the abstract and each "
        "venue profile: a coarse lexical heuristic, advisory only, not "
        "editorial advice, and not a certification of fit. There is no "
        "stemming (singular and plural forms must match exactly) and no "
        "understanding of content or quality. The built-in profiles are an "
        "author-curated starter list of examples; edit them for your field "
        "with --profiles. Discuss venue choice with coauthors and mentors."
    )
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(
        description=(
            "Rank candidate venues by transparent keyword overlap with an "
            "abstract. Coarse lexical heuristic; advisory only, not editorial advice."
        )
    )
    ap.add_argument("--abstract", required=True,
                    help="Plain-text file containing the abstract.")
    ap.add_argument("--profiles", default=None,
                    help="YAML list of venue profiles; replaces the built-in starter set.")
    ap.add_argument("--k", type=int, default=5,
                    help="How many top venues to report (default 5).")
    ap.add_argument("--out", default=None,
                    help="Output path (default: print to stdout).")
    args = ap.parse_args(argv)

    if args.k < 1:
        _fail(f"--k must be at least 1, got {args.k}")
    if not os.path.exists(args.abstract):
        _fail(f"abstract file not found: {args.abstract}")
    try:
        with open(args.abstract, encoding="utf-8") as fh:
            text = fh.read()
    except OSError as exc:
        _fail(f"cannot read abstract file: {args.abstract}\n  {exc}")
    tokens = _tokens(text)
    if not tokens:
        _fail(f"abstract file contains no words: {args.abstract}")

    profiles, source_desc = load_profiles(args.profiles)
    report = build_report(profiles, source_desc, args.abstract, tokens, args.k)

    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(report)
        print(f"[{TOOL}] wrote {args.out}")
    else:
        sys.stdout.write(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
