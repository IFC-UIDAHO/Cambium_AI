# quickstart.ps1 - one-command setup for the Cambium
# Usage: pwsh tools/quickstart.ps1
# Safe: read-only except copying config.example.yml -> config.yml (only if missing).

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

Write-Host ""
Write-Host "======================================================"
Write-Host "  Cambium - Quickstart"
Write-Host "======================================================"
Write-Host ""

if (-not (Test-Path "config.yml")) {
    Copy-Item "config.example.yml" "config.yml"
    Write-Host "[setup] config.yml created from config.example.yml"
    Write-Host "        -> Edit it now: set institute.name, director, and your team."
} else {
    Write-Host "[setup] config.yml already exists - skipping copy."
}

Write-Host ""
Write-Host "[setup] Running agent frontmatter check..."
python tools/check_agents.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host ""
Write-Host "[setup] Running governance validate (CI ledger)..."
python governance/validate.py tools/ci_ledger.csv
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host ""
Write-Host "======================================================"
Write-Host "  Next steps"
Write-Host "======================================================"
Write-Host ""
Write-Host "  1. Edit config.yml  - set your lab name, director, and team."
Write-Host "  2. Open dashboard.html in a browser to see your institute org chart."
Write-Host "  3. Say a trigger phrase in Claude to begin:"
Write-Host ""
Write-Host "  Trigger phrases:"
Write-Host "    'new project: <name>'        - register a project folder"
Write-Host "    'read rfp <file/link>'       - start from an RFP (Gate G1)"
Write-Host "    'project approved'           - flip to mid-project mode"
Write-Host "    'run lab'                    - develop -> verify -> synthesize"
Write-Host "    'progress report'            - generate a progress report"
Write-Host ""
Write-Host "  Full guide: GETTING_STARTED.md"
Write-Host "======================================================"
Write-Host ""
