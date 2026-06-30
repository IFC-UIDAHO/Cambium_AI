#!/usr/bin/env python3
"""cambium_start -- Act I "first paint" in ONE command, so /cambium can never silently fall back to plain text.

The Cambium way is a contract (docs/concepts/PRESENTATION.md), and contracts get skipped under load. The most common
failure the Director sees is: typed `/cambium <task>`, got a plain text answer -- no live run board, no
named agents, no gate. The cause is that Act I used to be three separate tool calls; the easy path was to
skip them. This collapses Act I to a single deterministic call:

  python3 tools/cambium_start.py "<task>"

It (1) resets the run state, (2) prints the branded text board (renders in ANY client), (3) writes the
live HTML board, and (4) prints an explicit FIRST-PAINT banner telling the model exactly what to do next
(publish the HTML as a 'Cambium run board' artifact, then dispatch Phase 1). One call = the UI is painted.

  --out PATH   where to write the HTML board (default: agent_outputs/run_board.html under data_home())
  --no-reset   keep the existing run state (for mid-run re-paints)
Exit: 0 always (first paint must never block the run).
"""
import os, subprocess, sys
import cambium_io  # reconfigures stdout/stderr to UTF-8 on Windows; also provides data_home()
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PYX = sys.executable

def _run(cmd):
    return subprocess.run([PYX] + cmd, cwd=ROOT, capture_output=True, text=True)

def main(argv=None):
    args = argv if argv is not None else sys.argv[1:]
    task = next((a for a in args if not a.startswith("--")), "")
    # Default out: agent_outputs/run_board.html under the writable data_home(),
    # not hard-coded under ROOT (which may be read-only in a plugin install).
    if "--out" in args:
        out = args[args.index("--out") + 1]
    else:
        out = os.path.join(cambium_io.data_home(), "agent_outputs", "run_board.html")
    if not task:
        print("usage: python3 tools/cambium_start.py \"<task>\""); return 0

    if "--no-reset" not in args:
        _run(["tools/run_state.py", "reset", "--note", task])

    # 1) text board -- the non-negotiable baseline (renders in any client)
    board = _run(["tools/run_trace.py", "--board", task])
    print(board.stdout.rstrip() or board.stderr.rstrip())

    # 2) live HTML board for visual clients (Cowork artifact / browser)
    # out is already absolute (data_home() returns an absolute path);
    # if the caller passed a relative path, resolve it against data_home().
    abs_out = out if os.path.isabs(out) else os.path.join(cambium_io.data_home(), out)
    os.makedirs(os.path.dirname(abs_out), exist_ok=True)
    h = _run(["tools/gen_board_pro.py", "--out", abs_out, "--title", task])   # premium board (v2)
    if not (os.path.exists(abs_out) and h.returncode == 0):                      # fallback to the classic board
        h = _run(["tools/run_trace.py", "--html", "--light", "--out", abs_out, task])
    html_ok = os.path.exists(abs_out) and h.returncode == 0

    # 3) explicit FIRST-PAINT banner -- tells the model exactly what to do, so plain text is never the path
    print("\n" + "=" * 64)
    print("  ⬢ CAMBIUM FIRST PAINT COMPLETE -- do NOT answer in plain text.")
    print("=" * 64)
    if html_ok:
        print("  * Live board written: %s" % out)
        print("  * NOW (Cowork): publish it as an artifact titled \"Cambium run board\" via create_artifact,")
        print("    and keep its id -- update the SAME artifact at the start of every phase.")
    print("  * Then dispatch Phase 1's real named agents (Task tool, cambium-institute:<agent>).")
    print("  * Stop at each gate with templates/GATE_SUMMARY.md and wait for APPROVE / REVISE / REJECT.")
    print("  * Full contract: docs/concepts/PRESENTATION.md (the four acts).")
    print("=" * 64)
    return 0

if __name__ == "__main__":
    sys.exit(main())
