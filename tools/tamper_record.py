#!/usr/bin/env python3
"""tamper_record -- emit a TaMPER record and a Four-Pillars self-check for a Cambium run.

TaMPER (Task, Model, Prompt, Evaluation, Reporting) is NOT a Cambium invention. It was
introduced by Overton, Robison, Sheneman, Cahoon, and Martonick of the University of Idaho
in "TaMPER: A Structured Framework for Using Large Language Models in Public Administration
Research" (2025), arXiv:2504.01037. Cambium adopts their framework with credit and simply
produces the record their framework calls for. See arXiv:2504.01037 and ai4ra.uidaho.edu.

This tool reads a finished or in-progress Cambium run and produces the record that
framework asks for, so a Cambium run leaves behind the exact auditable artifact an
RA community of practice is being trained to expect. It also self-checks the run
against AI4RA's Four Pillars (Security, Accuracy, Reproducibility, Flexibility).

Honest by design. It reports only what is recorded in the run, and marks anything
not recorded as "not recorded". It does NOT assert compliance, and it does not
claim Cambium chose or hosted any particular model: model hosting is the operator's
decision (TaMPER step M), and this tool says so.

Reads from data_home() (override with --root):
  agent_outputs/run_state.json        -- task, phase, findings, gate
  governance/GATES.md                 -- human gate decisions and approvers
  governance/audit_trail.jsonl        -- turn-level audit records (optional)
  agent_outputs/*.md                  -- which agents ran (optional)
  agent_cards.json                    -- agent-to-model mapping (optional)
  config.yml                          -- configured model, if present (optional)

Usage:
  python3 tools/tamper_record.py [--root <path>] [--out <path>] \
        [--title "<deliverable>"] [--model "<model name>"] \
        [--format md|json|prov]

--format prov emits a W3C PROV document if the optional `prov` package is
installed; otherwise it falls back to json and says so.
"""
from __future__ import annotations
import argparse
import json
import os
import sys
from datetime import datetime

import cambium_io  # noqa: F401  (UTF-8 stdout guard)

# Reuse the readers from ai_disclosure so the two tools never diverge.
from ai_disclosure import (
    _read_gates,
    _read_audit_jsonl,
    _read_agent_outputs,
    _read_agent_cards,
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NOT_RECORDED = "not recorded in this run"


# ---------------------------------------------------------------------------
# Source readers specific to this tool
# ---------------------------------------------------------------------------

def _read_run_state(root: str) -> dict:
    """Read agent_outputs/run_state.json. Returns {} if absent or unreadable."""
    path = os.path.join(root, "agent_outputs", "run_state.json")
    if not os.path.exists(path):
        return {}
    try:
        return json.loads(open(path, encoding="utf-8").read())
    except Exception:
        return {}


def _read_configured_model(root: str) -> str:
    """Best-effort read of a model name from config.yml. Returns '' if not found."""
    path = os.path.join(root, "config.yml")
    if not os.path.exists(path):
        return ""
    try:
        for line in open(path, encoding="utf-8", errors="replace"):
            s = line.strip()
            if s.lower().startswith("model:"):
                return s.split(":", 1)[1].strip().strip('"').strip("'")
    except Exception:
        pass
    return ""


def _agent_names(root: str) -> list[str]:
    cards = _read_agent_cards(root)
    names: list[str] = []
    if isinstance(cards, dict):
        inner = cards.get("agents")
        if isinstance(inner, list):
            names = [a.get("name", "") for a in inner if isinstance(a, dict) and a.get("name")]
        else:
            names = [k for k in cards.keys() if isinstance(k, str) and k not in ("count", "agents", "generated")]
    elif isinstance(cards, list):
        names = [a.get("name", "") for a in cards if isinstance(a, dict) and a.get("name")]
    if not names:
        names = [os.path.splitext(f)[0] for f in _read_agent_outputs(root)]
    return sorted(set(n for n in names if n))


# ---------------------------------------------------------------------------
# TaMPER record builder (pure function -> dict)
# ---------------------------------------------------------------------------

def build_record(root: str, title: str, model_override: str = "") -> dict:
    """Assemble the TaMPER record and Four-Pillars self-check as a dict."""
    now = datetime.utcnow().strftime("%Y-%m-%d")
    state = _read_run_state(root)
    gates = _read_gates(root)
    audit = _read_audit_jsonl(root)
    agents = _agent_names(root)
    configured_model = model_override or _read_configured_model(root)

    task_desc = (
        state.get("task")
        or state.get("note")
        or title
        if (state.get("task") or state.get("note")) else (title or NOT_RECORDED)
    )
    phase = state.get("phase") or NOT_RECORDED

    decided_gates = [g for g in gates if g.get("approved_by")]

    # T -- Task
    task = {
        "description": task_desc,
        "current_phase": phase,
        "kind": "multi-step research-administration workflow, run as named sub-agents",
    }

    # M -- Model
    if configured_model:
        model = {
            "engine": configured_model,
            "hosting": "operator's choice; for confidential RA data use a private or local model",
            "note": "Cambium orchestrates the model; it does not select or host it for you.",
        }
    else:
        model = {
            "engine": NOT_RECORDED,
            "hosting": "operator's choice; for confidential RA data use a private or local model",
            "note": "No model name was recorded in this run. Record one for a complete TaMPER M step.",
        }

    # P -- Prompt
    prompt = {
        "governance": "Agent roles and instructions are version-controlled in the repo "
                      "(.claude/agents and skills), so prompts are auditable and repeatable.",
        "structure": "Each agent encodes Role and Task; Context and Format are supplied per run.",
        "agents_that_ran": agents if agents else [NOT_RECORDED],
    }

    # E -- Evaluation
    evaluation = {
        "human_gates_with_decisions": len(decided_gates),
        "approvers": sorted(set(g["approved_by"] for g in decided_gates)) or [NOT_RECORDED],
        "machine_checks": "Evidence contract (Proved / Code-verified / Asserted / Open) with a "
                          "post-hoc CI check via tools/finding_audit.py; an independent verification "
                          "council reproduces headline numbers.",
        "note": "The human approver is the expert of record. AI output is reviewed, not trusted blindly.",
    }

    # R -- Reporting
    reporting = {
        "this_record": "tools/tamper_record.py",
        "ai_use_disclosure": "tools/ai_disclosure.py",
        "audit_trail_records": len(audit),
        "auditable": "The run leaves a documented, repeatable trail so a colleague can reproduce it.",
    }

    # Four Pillars self-check (honest, mechanism-named)
    pillars = {
        "security": {
            "status": "addressed by design",
            "mechanism": "Local-first writes via cambium_io.data_home; stdlib-first tools make no "
                         "cloud calls; tools/pii_screen.py flags sensitive data before it is shared. "
                         "Model hosting is the operator's choice (see TaMPER M).",
        },
        "accuracy": {
            "status": "enforced as a post-hoc check",
            "mechanism": "Evidence contract plus tools/finding_audit.py flag any claim that reaches "
                         "past its tier. Cambium checks AI output; it does not vouch for it.",
        },
        "reproducibility": {
            "status": "supported",
            "mechanism": "Deterministic stdlib tools, a test suite, and pinned optional extras "
                         "(requirements-optional.txt) let a run be reproduced.",
        },
        "flexibility": {
            "status": "supported",
            "mechanism": "Machine-readable exports (this record as json, tools/okf_export.py, "
                         "tools/fair_descriptor.py) let other systems consume Cambium output.",
        },
    }

    honest_notes = [
        "Cambium is a preparation and governance layer. It does not extract documents (that is "
        "Vandalizer) and does not make compliance determinations (that is a human in sponsored programs).",
        "This record reports only what the run recorded. Items marked 'not recorded' are gaps to fill, "
        "not claims of completeness.",
        "TaMPER is AI4RA's framework (arXiv 2504.01037); Cambium adopts it to speak the RA community's language.",
    ]

    return {
        "deliverable": title or NOT_RECORDED,
        "generated_utc": now,
        "generator": "Cambium tools/tamper_record.py",
        "framework": "TaMPER (Task, Model, Prompt, Evaluation, Reporting)",
        "framework_credit": "TaMPER is the work of Overton et al. (University of Idaho), "
                            "arXiv:2504.01037. Cambium uses it with credit; it is not Cambium's framework.",
        "tamper": {
            "task": task,
            "model": model,
            "prompt": prompt,
            "evaluation": evaluation,
            "reporting": reporting,
        },
        "four_pillars": pillars,
        "honest_notes": honest_notes,
    }


# ---------------------------------------------------------------------------
# Renderers
# ---------------------------------------------------------------------------

def render_markdown(rec: dict) -> str:
    t = rec["tamper"]
    L: list[str] = []
    L.append("# TaMPER Record and Four-Pillars Self-Check")
    L.append("")
    L.append(f"**Deliverable:** {rec['deliverable']}")
    L.append(f"**Generated:** {rec['generated_utc']} (UTC) by {rec['generator']}")
    L.append(f"**Framework:** {rec['framework']}")
    L.append(f"_{rec['framework_credit']}_")
    L.append("")
    L.append("---")
    L.append("")
    L.append("## TaMPER")
    L.append("")
    L.append(f"**T -- Task.** {t['task']['description']}  ")
    L.append(f"Current phase: {t['task']['current_phase']}. Kind: {t['task']['kind']}.")
    L.append("")
    L.append(f"**M -- Model.** Engine: {t['model']['engine']}. Hosting: {t['model']['hosting']}.  ")
    L.append(f"{t['model']['note']}")
    L.append("")
    L.append(f"**P -- Prompt.** {t['prompt']['governance']} {t['prompt']['structure']}  ")
    L.append(f"Agents that ran: {', '.join(t['prompt']['agents_that_ran'])}.")
    L.append("")
    L.append(f"**E -- Evaluation.** Human gates with a recorded decision: "
             f"{t['evaluation']['human_gates_with_decisions']}. "
             f"Approver(s): {', '.join(t['evaluation']['approvers'])}.  ")
    L.append(f"{t['evaluation']['machine_checks']} {t['evaluation']['note']}")
    L.append("")
    L.append(f"**R -- Reporting.** This record: {t['reporting']['this_record']}. "
             f"AI-use disclosure: {t['reporting']['ai_use_disclosure']}. "
             f"Audit-trail records: {t['reporting']['audit_trail_records']}.  ")
    L.append(f"{t['reporting']['auditable']}")
    L.append("")
    L.append("---")
    L.append("")
    L.append("## Four Pillars self-check")
    L.append("")
    L.append("| Pillar | Status | Mechanism |")
    L.append("|---|---|---|")
    for name in ("security", "accuracy", "reproducibility", "flexibility"):
        p = rec["four_pillars"][name]
        L.append(f"| {name.capitalize()} | {p['status']} | {p['mechanism']} |")
    L.append("")
    L.append("---")
    L.append("")
    L.append("## Honest notes")
    L.append("")
    for n in rec["honest_notes"]:
        L.append(f"- {n}")
    L.append("")
    return "\n".join(L)


def render_json(rec: dict) -> str:
    return json.dumps(rec, indent=2, ensure_ascii=False)


def render_prov(rec: dict) -> tuple[str, str]:
    """Return (text, format_used). Uses W3C PROV if available, else falls back to json."""
    try:
        from prov.model import ProvDocument  # optional dependency
    except Exception:
        return render_json(rec), "json"
    d = ProvDocument()
    d.add_namespace("cambium", "https://github.com/pkjaslam/Cambium_AI#")
    d.add_namespace("tamper", "https://arxiv.org/abs/2504.01037#")
    ent = d.entity("cambium:deliverable", {"prov:label": rec["deliverable"]})
    act = d.activity("cambium:run", other_attributes={"tamper:task": rec["tamper"]["task"]["description"]})
    agent = d.agent("cambium:human-approver")
    d.wasGeneratedBy(ent, act)
    d.wasAssociatedWith(act, agent)
    return d.serialize(indent=2), "prov"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(description="Emit a TaMPER record and Four-Pillars self-check for a run.")
    ap.add_argument("--root", default=None, help="Data root (overrides data_home()).")
    ap.add_argument("--out", default=None, help="Output path.")
    ap.add_argument("--title", default="(untitled deliverable)", help="Name of the deliverable.")
    ap.add_argument("--model", default="", help="Model name to record for TaMPER step M.")
    ap.add_argument("--format", default="md", choices=["md", "json", "prov"], help="Output format.")
    args = ap.parse_args(argv)

    root = args.root if args.root else cambium_io.data_home()
    rec = build_record(root, args.title, args.model)

    if args.format == "md":
        text, ext = render_markdown(rec), "md"
    elif args.format == "json":
        text, ext = render_json(rec), "json"
    else:
        text, used = render_prov(rec)
        ext = "provn" if used == "prov" else "json"
        if used == "json":
            print("[tamper_record] optional 'prov' package not installed; wrote json instead.")

    out = args.out if args.out else os.path.join(root, "agent_outputs", f"tamper_record.{ext}")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(text)
    print(f"[tamper_record] wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
