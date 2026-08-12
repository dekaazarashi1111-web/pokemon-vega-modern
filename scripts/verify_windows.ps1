#!/usr/bin/env pwsh
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Minimal verify script for Windows projects.
# Replace the commands below with your project's real checks (pytest, npm test, make verify, etc).

$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $root

# Prefer project virtualenv if available
$venvActivate = Join-Path $root ".venv\\Scripts\\Activate.ps1"
if (Test-Path $venvActivate) {
    . $venvActivate
}

# Lightweight bootstrap: install dev deps only when pytest is missing
if (-not (Get-Command pytest -ErrorAction SilentlyContinue) -and (Test-Path (Join-Path $root "requirements-dev.txt"))) {
    Write-Host "[verify] pytest not found; installing requirements-dev.txt (one-time)"
    $venvDir = Join-Path $root ".venv"
    if (-not (Test-Path $venvDir)) {
        python -m venv $venvDir
        if (Test-Path $venvActivate) { . $venvActivate }
    }
    python -m pip install --upgrade pip *> $null
    python -m pip install -r (Join-Path $root "requirements-dev.txt")
}

Write-Host "[verify] secrets scan"
$secretScan = @'
import pathlib
import re
import sys

root = pathlib.Path(".").resolve()
ignore = {".git", ".venv", ".venv_test", ".codex", "tests", "__pycache__", ".pytest_cache", "node_modules", "dist", "build", ".tox"}
patterns = [
    re.compile(r"(?i)(bearer\s+)([A-Za-z0-9._-]{8,})"),
    re.compile(r"(?i)(token=)([A-Za-z0-9._-]{8,})"),
    re.compile(r"(?i)(api[_-]?key\s*[=:]\s*)([A-Za-z0-9._-]{12,})"),
    re.compile(r"(?i)(access[_-]?token\s*[=:]\s*)([A-Za-z0-9._-]{12,})"),
    re.compile(r"(?i)(aws_secret_access_key\s*[=:]\s*)([A-Za-z0-9/+=]{16,})"),
    re.compile(r"(?i)(aws_access_key_id\s*[=:]\s*)([A-Z0-9]{16,})"),
    re.compile(r"(sk-[A-Za-z0-9]{16,})"),
    re.compile(r"(ghp_[A-Za-z0-9]{20,})"),
    re.compile(r"(xox[baprs]-[A-Za-z0-9-]{10,})"),
]

hits = []
for path in root.rglob("*"):
    if path.is_dir():
        continue
    if any(part in ignore for part in path.parts):
        continue
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        continue
    for lineno, line in enumerate(text.splitlines(), 1):
        for pat in patterns:
            if pat.search(line):
                hits.append((path, lineno))
                break

if hits:
    print("[verify] secrets scan FAILED")
    for path, lineno in hits[:5]:
        print(f"{path}:{lineno} [REDACTED]")
    sys.exit(1)

print("[verify] secrets scan ok")
'@
$secretScan | python -
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

$ranCheck = $false

if ((Get-Command pytest -ErrorAction SilentlyContinue) -and (Test-Path (Join-Path $root "tests"))) {
    Write-Host "[verify] running pytest -q"
    python -m pytest -q
    $pyExit = $LASTEXITCODE
    if ($pyExit -eq 5) {
        Write-Host "[verify] pytest reported no tests collected; treating as pass"
    } elseif ($pyExit -ne 0) {
        exit $pyExit
    }
    $ranCheck = $true
}

if (Get-Command dotnet -ErrorAction SilentlyContinue) {
    $dotnetTarget = Get-ChildItem -Path $root -Recurse -Include *.sln,*.csproj -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($dotnetTarget) {
        $results = Join-Path ([System.IO.Path]::GetTempPath()) ("dotnet-test-" + [System.IO.Path]::GetRandomFileName())
        New-Item -ItemType Directory -Path $results -Force | Out-Null
        Write-Host "[verify] running dotnet test (results: $results)"
        dotnet test --nologo --results-directory $results --logger "trx;LogFileName=verify.trx"
        if ($LASTEXITCODE -ne 0) {
            exit $LASTEXITCODE
        }
        $ranCheck = $true
    }
}

if (-not $ranCheck) {
    Write-Host "[verify] No project-specific checks configured."
    Write-Host "[verify] Edit scripts\\verify_windows.ps1 to add your project's verify commands."
}
