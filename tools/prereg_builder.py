#!/usr/bin/env python3
"""prereg_builder -- format a study spec into an OSF-style preregistration draft.

Reads a YAML or JSON study specification and renders it as a numbered,
OSF-style preregistration document in Markdown, then reports which required
sections are missing or empty. The tool formats and checks what you wrote;
it never invents hypotheses, designs, sample plans, or analysis content.
The result is a draft for the research team to complete and register
themselves. It is advisory, not a certification of preregistration quality
or of compliance with any registry's rules.

Section layout is modeled loosely on the OSF preregistration template
(Center for Open Science, https://osf.io/prereg, consulted 2026-07-01).
Registry templates change; consult the current OSF form for authoritative
wording before registering.

Required spec keys (each becomes a numbered section):
  title          string
  hypotheses     list of strings
  design         string or mapping
  sample_plan    string or mapping
  outcomes       list of strings
  analysis_plan  string or mapping

Optional keys: authors and study_type (shown in the header);
data_collection_status, exclusion_criteria, missing_data_plan (extra
numbered sections). Unknown keys are carried through verbatim under
"Additional spec fields" so nothing you wrote is silently dropped.

Exit codes:
  0  -- document rendered; completeness findings are advisory
  1  -- invalid input (missing, unreadable, or unparseable spec), or
        --strict with missing or empty required sections
  2  -- argparse usage errors (argparse default)

Usage:
  python3 tools/prereg_builder.py --template
  python3 tools/prereg_builder.py --spec study.yml
  python3 tools/prereg_builder.py --spec study.json --out prereg.md --strict
"""
from __future__ import annotations
import argparse
import json
import os
import sys

# UTF-8 stdout guard
import cambium_io  # noqa: F401

try:
    import yaml
except ImportError:  # pyyaml is expected in this repo; JSON specs work without it
    yaml = None

TOOL = "prereg_builder"

REQUIRED_SECTIONS: list[tuple[str, str]] = [
    ("title", "Title"),
    ("hypotheses", "Hypotheses"),
    ("design", "Study design"),
    ("sample_plan", "Sampling plan"),
    ("outcomes", "Outcomes and variables"),
    ("analysis_plan", "Analysis plan"),
]

OPTIONAL_SECTIONS: list[tuple[str, str]] = [
    ("data_collection_status", "Data collection status"),
    ("exclusion_criteria", "Exclusion criteria"),
    ("missing_data_plan", "Missing data plan"),
]

HEADER_KEYS = ("authors", "study_type")

KNOWN_KEYS = (
    {key for key, _ in REQUIRED_SECTIONS}
    | {key for key, _ in OPTIONAL_SECTIONS}
    | set(HEADER_KEYS)
)

TEMPLATE = """\
# Starter study spec for prereg_builder. Edit every TODO before use.
# The tool formats and checks this spec; it does not invent content.
title: "TODO: working title of the study"
authors:
  - "TODO: name, affiliation"
study_type: "TODO: experiment | observational | secondary data | meta-analysis"
hypotheses:
  - "H1: TODO state a specific, testable hypothesis"
  - "H2: TODO add or delete hypotheses as needed"
design: >-
  TODO: describe conditions, factors (within or between subjects),
  randomization, and blinding.
sample_plan: >-
  TODO: target sample size, stopping rule, and the power analysis or
  resource constraint that justifies the target.
outcomes:
  - "TODO: primary outcome, how and when it is measured"
  - "TODO: secondary outcomes, if any"
analysis_plan: >-
  TODO: statistical model, inference criteria, multiple-comparison
  handling, outlier rules, and missing-data handling.
data_collection_status: "TODO: e.g. no data collected yet"
exclusion_criteria: "TODO: participant or observation exclusion rules"
missing_data_plan: "TODO: how missing data will be treated"
"""


def _fail(msg: str) -> None:
    print(f"[{TOOL}] ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------

def load_spec(path: str) -> dict:
    if not os.path.exists(path):
        _fail(f"spec file not found: {path}")
    try:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
    except OSError as exc:
        _fail(f"cannot read spec file: {path}\n  {exc}")
    if path.lower().endswith(".json"):
        try:
            spec = json.loads(text)
        except json.JSONDecodeError as exc:
            _fail(f"spec file is not valid JSON: {path}\n  {exc}")
    else:
        if yaml is None:
            _fail("pyyaml is not installed; install pyyaml or provide a .json spec")
        try:
            spec = yaml.safe_load(text)
        except yaml.YAMLError as exc:
            _fail(f"spec file is not valid YAML: {path}\n  {exc}")
    if not isinstance(spec, dict):
        _fail(f"spec must be a mapping of keys to values, got: {type(spec).__name__}")
    return spec


# ---------------------------------------------------------------------------
# Rendering helpers -- verbatim formatting, no invention
# ---------------------------------------------------------------------------

def is_empty(value) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, (list, tuple)):
        return len(value) == 0 or all(is_empty(v) for v in value)
    if isinstance(value, dict):
        return len(value) == 0
    return False


def _fmt_scalar(value) -> str:
    if isinstance(value, dict):
        return "; ".join(f"{k}: {_fmt_scalar(v)}" for k, v in value.items())
    if isinstance(value, (list, tuple)):
        return "; ".join(_fmt_scalar(v) for v in value)
    return str(value).strip()


def render_value(value) -> list[str]:
    """Render a spec value as Markdown lines, verbatim."""
    if isinstance(value, (list, tuple)):
        return [f"{i}. {_fmt_scalar(item)}" for i, item in enumerate(value, 1)]
    if isinstance(value, dict):
        return [f"- {k}: {_fmt_scalar(v)}" for k, v in value.items()]
    return [str(value).strip()]


# ---------------------------------------------------------------------------
# Document builder
# ---------------------------------------------------------------------------

def build_document(spec: dict, spec_path: str) -> tuple[str, list[str]]:
    """Return (markdown document, list of missing/empty required keys)."""
    lines: list[str] = []
    missing: list[str] = []

    title = spec.get("title")
    title_text = _fmt_scalar(title) if not is_empty(title) else "(untitled: title missing from spec)"

    lines.append(f"# Preregistration draft: {title_text}")
    lines.append("")
    lines.append(
        "> Assembled mechanically from the study spec by prereg_builder. "
        "It contains only what the spec contains and invents nothing. "
        "Advisory, not a certification: review, complete, and register it "
        "yourself (for example on OSF)."
    )
    lines.append("")
    lines.append(f"**Spec file:** {spec_path}")
    for key in HEADER_KEYS:
        if not is_empty(spec.get(key)):
            label = key.replace("_", " ").capitalize()
            lines.append(f"**{label}:** {_fmt_scalar(spec[key])}")
    lines.append("")
    lines.append("---")
    lines.append("")

    number = 0
    for key, heading in REQUIRED_SECTIONS:
        number += 1
        lines.append(f"## {number}. {heading}")
        lines.append("")
        value = spec.get(key)
        if is_empty(value):
            missing.append(key)
            lines.append(f"*Not provided in the spec (key: {key}). Fill this in before registering.*")
        else:
            lines.extend(render_value(value))
        lines.append("")

    for key, heading in OPTIONAL_SECTIONS:
        if is_empty(spec.get(key)):
            continue
        number += 1
        lines.append(f"## {number}. {heading}")
        lines.append("")
        lines.extend(render_value(spec[key]))
        lines.append("")

    extras = sorted(k for k in spec if k not in KNOWN_KEYS and not is_empty(spec.get(k)))
    if extras:
        number += 1
        lines.append(f"## {number}. Additional spec fields")
        lines.append("")
        lines.append("Carried through verbatim so nothing you wrote is dropped:")
        lines.append("")
        for k in extras:
            lines.append(f"- {k}: {_fmt_scalar(spec[k])}")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## Completeness check (advisory)")
    lines.append("")
    lines.append(f"- Required sections: {len(REQUIRED_SECTIONS)}")
    lines.append(f"- Present and non-empty: {len(REQUIRED_SECTIONS) - len(missing)}")
    if missing:
        lines.append(f"- Missing or empty: {', '.join(missing)}")
    else:
        lines.append("- Missing or empty: none. All required sections are present.")
    lines.append("")
    lines.append(
        "**This draft contains only what the study spec contains. The "
        "completeness check is advisory, not a certification. A human must "
        "review, complete, and submit the actual registration.**"
    )
    lines.append("")
    return "\n".join(lines), missing


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(
        description=(
            "Format a YAML or JSON study spec into an OSF-style preregistration "
            "draft with a completeness check. Formats and checks only; invents "
            "nothing. Advisory, not a certification."
        )
    )
    source = ap.add_mutually_exclusive_group(required=True)
    source.add_argument("--spec", help="Path to a YAML or JSON study spec.")
    source.add_argument("--template", action="store_true",
                        help="Print a starter spec (YAML) and exit.")
    ap.add_argument("--out", default=None,
                    help="Output path (default: print to stdout).")
    ap.add_argument("--strict", action="store_true",
                    help="Exit 1 if any required section is missing or empty.")
    args = ap.parse_args(argv)

    if args.template:
        text = TEMPLATE
        missing: list[str] = []
    else:
        spec = load_spec(args.spec)
        text, missing = build_document(spec, args.spec)

    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(text)
        print(f"[{TOOL}] wrote {args.out}")
    else:
        sys.stdout.write(text)

    if missing:
        print(f"[{TOOL}] advisory: missing or empty required sections: {', '.join(missing)}",
              file=sys.stderr)
        if args.strict:
            print(f"[{TOOL}] STRICT: incomplete spec, exiting 1", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
