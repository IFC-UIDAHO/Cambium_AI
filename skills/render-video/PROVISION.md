# PROVISION.md — render-video skill (Toolsmith provisioning manifest)

**Principle: reuse beats rebuild.**
This manifest documents how to install and connect OpenMontage so the
`render-video` skill can invoke it. Nothing here is installed automatically;
every step requires a human action.

---

## License notice (read before installing)

OpenMontage (https://github.com/calesthio/OpenMontage) is licensed under the
**GNU Affero General Public License v3 (AGPLv3)**.

- You may use it freely on your own machine (local use).
- If you host it as a network-accessible service, AGPL §13 requires you to
  offer the full source of your modified version to all network users.
- Cambium itself is MIT-licensed. The two codebases must NOT be merged,
  vendored, or linked — the OS process boundary is the license boundary.

---

## Prerequisites

Install these BEFORE OpenMontage:

| Tool | Minimum version | Install |
|---|---|---|
| Python | 3.10+ | https://www.python.org/downloads/ |
| Node.js | 18+ | https://nodejs.org/ |
| FFmpeg | 5+ | https://ffmpeg.org/download.html — add to PATH |
| Git | any recent | https://git-scm.com/ |

Verify:
```bash
python3 --version   # must be 3.10+
node --version      # must be v18+
ffmpeg -version     # must be present
```

---

## Step 1 — Clone OpenMontage into a user-owned location

Choose a location outside the Cambium repo. Suggested:

```bash
mkdir -p ~/tools
git clone https://github.com/calesthio/OpenMontage ~/tools/OpenMontage
```

This keeps AGPLv3 code entirely outside the MIT tree.

---

## Step 2 — Run OpenMontage setup (human approval required)

```bash
cd ~/tools/OpenMontage
make setup
```

Review what `make setup` installs before running it. It will install Python
dependencies and Node packages declared in OpenMontage's own manifests.
Cambium does NOT know the exact list — consult OpenMontage's README and
CHANGELOG for the current dependency set.

---

## Step 3 — Set the Cambium env var

Tell Cambium where to find OpenMontage by setting `OPENMONTAGE_HOME`:

```bash
# add to your shell profile (.bashrc / .zshrc / .profile)
export OPENMONTAGE_HOME="$HOME/tools/OpenMontage"
```

The `render-video` skill constructs the subprocess call as:

```
$OPENMONTAGE_HOME/pipeline_defs/<profile> render \
    --request <request.json> \
    --output  <output_path>
```

If `OPENMONTAGE_HOME` is unset, the skill will error immediately with a clear
message rather than silently failing.

---

## Step 4 — Zero-API-key free path (optional)

OpenMontage supports a fully local, zero-cost render path using:

| Component | Purpose | Notes |
|---|---|---|
| **Piper TTS** | Text-to-speech narration | Local neural TTS, no API key |
| **Remotion** | Programmatic video assembly | Node-based, open source |
| **Archive.org** | Public domain B-roll | CC0 / PD assets |
| **NASA media** | Scientific B-roll | NASA public domain |
| **Wikimedia Commons** | Images and video | Various open licenses |
| **Pexels** | Stock photography/video | Free Pexels License (attribution) |

To use this path, follow OpenMontage's own documentation for the `local-free`
or equivalent pipeline profile. No Cambium-side configuration is needed beyond
setting `OPENMONTAGE_HOME`.

Piper TTS install reference: https://github.com/rhasspy/piper

---

## Step 5 — Verify the connection

After setup and env var are set, verify from the Cambium project root:

```bash
python3 -c "
import os, subprocess, sys
home = os.environ.get('OPENMONTAGE_HOME','')
if not home:
    sys.exit('OPENMONTAGE_HOME not set')
result = subprocess.run(['python3', '-m', 'openmontage', '--version'],
                        cwd=home, capture_output=True, text=True)
print(result.stdout or result.stderr or 'OK (no version output)')
"
```

A missing or broken OpenMontage will be reported here rather than at render
time.

---

## Provisioning gate

This step is installed at the **Toolsmith provisioning gate**, with human
approval, before any video render is requested. The Toolsmith agent records the
installation in the project's POST_AWARD_PLAN or the session log.

**Nothing in this manifest is auto-executed by Cambium.** The human must run
each command explicitly.

---

## Updating OpenMontage

```bash
cd ~/tools/OpenMontage
git pull
make setup          # re-run to update Python/Node deps
```

Review OpenMontage's own CHANGELOG for breaking changes to CLI flags or
`pipeline_defs/` profiles before updating.

---

## Uninstall

To remove OpenMontage:
```bash
rm -rf ~/tools/OpenMontage
unset OPENMONTAGE_HOME   # also remove from shell profile
```

Cambium's `skills/render-video/` folder stays; it contains no OpenMontage code.
