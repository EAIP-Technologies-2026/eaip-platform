# =============================================================================
# EAIP — One-command developer bootstrap (Windows / PowerShell 5.1+ or 7+)
# -----------------------------------------------------------------------------
# Run from the repository root:
#     pwsh -File scripts/bootstrap.ps1
# Or under classic Windows PowerShell:
#     powershell -ExecutionPolicy Bypass -File scripts\bootstrap.ps1
# =============================================================================

#Requires -Version 5.1
[CmdletBinding()]
param(
    [string]$Python = "",
    [string]$Venv = ".venv"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Write-Step    { param($msg) Write-Host "-> $msg" -ForegroundColor Cyan }
function Write-Ok      { param($msg) Write-Host "OK $msg"  -ForegroundColor Green }
function Write-Warn    { param($msg) Write-Host "!  $msg"  -ForegroundColor Yellow }
function Stop-WithError {
    param($msg)
    Write-Host "x  $msg" -ForegroundColor Red
    exit 1
}

# ---- Locate Python ---------------------------------------------------------
if (-not $Python) {
    foreach ($cand in @("python3.13", "python3.12", "python3.11", "py -3.13", "py -3.12", "py -3.11", "python3", "python")) {
        try {
            $out = & cmd /c "$cand --version 2>nul"
            if ($LASTEXITCODE -eq 0 -and $out) { $Python = $cand; break }
        } catch { }
    }
}
if (-not $Python) {
    Stop-WithError "No Python 3.11+ found on PATH. Install from https://python.org and retry."
}

$verRaw = & cmd /c "$Python -c ""import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"""
$ver = $verRaw.Trim()
if ($ver -notin @("3.11", "3.12", "3.13")) {
    Stop-WithError "Python $ver is unsupported. EAIP requires 3.11, 3.12, or 3.13."
}
Write-Ok "Python $ver detected ($Python)"

# ---- Create venv -----------------------------------------------------------
if (-not (Test-Path $Venv)) {
    Write-Step "Creating virtualenv at $Venv"
    & cmd /c "$Python -m venv $Venv"
    if ($LASTEXITCODE -ne 0) { Stop-WithError "Failed to create virtualenv." }
} else {
    Write-Step "Reusing existing virtualenv at $Venv"
}

$venvPython = Join-Path $Venv "Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    $venvPython = Join-Path $Venv "bin/python"
}
if (-not (Test-Path $venvPython)) {
    Stop-WithError "Could not locate venv interpreter."
}

# ---- Install ---------------------------------------------------------------
Write-Step "Upgrading pip / wheel / setuptools"
& $venvPython -m pip install --quiet --upgrade pip wheel setuptools

Write-Step "Installing project (dev + test extras)"
& $venvPython -m pip install --quiet -e ".[dev,test]"

# ---- Pre-commit ------------------------------------------------------------
Write-Step "Installing pre-commit hooks"
try {
    & $venvPython -m pre_commit install --install-hooks  | Out-Null
    & $venvPython -m pre_commit install --hook-type commit-msg | Out-Null
    Write-Ok "Pre-commit hooks installed"
} catch {
    Write-Warn "Pre-commit hook install skipped: $($_.Exception.Message)"
}

Write-Ok "Bootstrap complete."
Write-Host ""
Write-Host "Next steps:"
Write-Host "  $Venv\Scripts\Activate.ps1"
Write-Host "  make help        # if you have make on PATH"
Write-Host "  python -m pytest tests -q"
