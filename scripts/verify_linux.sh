#!/usr/bin/env bash
set -euo pipefail

# Minimal verify script for native Linux projects.
# Customize with your project's checks (pytest, npm test, make verify, etc).

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"

PY_BIN=python3
if ! command -v "$PY_BIN" >/dev/null 2>&1; then
  PY_BIN=python
fi

if [ -f ".venv/bin/activate" ]; then
  # Prefer project venv if present
  # shellcheck disable=SC1091
  source ".venv/bin/activate"
fi

# Lightweight bootstrap: install dev deps only when pytest is missing
if ! command -v pytest >/dev/null 2>&1 && [ -f "requirements-dev.txt" ]; then
  echo "[verify] pytest not found; installing requirements-dev.txt (one-time)"
  if [ ! -d ".venv" ]; then
    "$PY_BIN" -m venv .venv
    # shellcheck disable=SC1091
    source ".venv/bin/activate"
  fi
  "$PY_BIN" -m pip install --upgrade pip >/dev/null
  "$PY_BIN" -m pip install -r requirements-dev.txt
fi
echo "[verify] secrets scan"
"$PY_BIN" - <<'PY'
import pathlib
import re
import sys

root = pathlib.Path(".").resolve()
ignore = {".git", ".venv", ".venv_test", ".codex", ".local", "userfile", "vendor", "tests", "__pycache__", ".pytest_cache", "node_modules", "dist", "build", "generated", ".tox"}
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
PY

ran_check=0

if [ -f "Makefile" ]; then
  echo "[verify] running project gates"
  make validate guard test
  ran_check=1
fi

if [ $ran_check -eq 0 ] && command -v pytest >/dev/null 2>&1 && [ -d "tests" ]; then
  echo "[verify] running pytest -q"
  set +e
  pytest -q
  py_status=$?
  set -e
  if [ "$py_status" -eq 5 ]; then
    echo "[verify] pytest reported no tests collected; treating as pass"
  elif [ "$py_status" -ne 0 ]; then
    exit "$py_status"
  fi
  ran_check=1
fi

if command -v node >/dev/null 2>&1 && [ -f "package.json" ]; then
  echo "[verify] running npm check"
  npm run check
  ran_check=1
fi

if command -v dotnet >/dev/null 2>&1; then
  dotnet_target="$(find . -maxdepth 4 \( -name '*.sln' -o -name '*.csproj' \) -print -quit)"
  if [ -n "$dotnet_target" ]; then
    results_dir="$(mktemp -d -t dotnet-test-XXXXXX)"
    echo "[verify] running dotnet test (results: $results_dir)"
    set +e
    dotnet test --nologo --results-directory "$results_dir" --logger "trx;LogFileName=verify.trx"
    dotnet_status=$?
    set -e
    if [ "$dotnet_status" -ne 0 ]; then
      exit "$dotnet_status"
    fi
    ran_check=1
  fi
fi

if [ $ran_check -eq 0 ]; then
  echo "[verify] No project-specific checks configured."
  echo "[verify] Edit scripts/verify_linux.sh to add project-specific commands."
fi
