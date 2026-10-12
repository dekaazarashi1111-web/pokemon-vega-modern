#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="$(cd -- "${SCRIPT_DIR}/.." && pwd)"

cd "${WORKSPACE_DIR}"
export PYTHONDONTWRITEBYTECODE=1
exec python3 tools/modernization_p05_stage78_eelevate_switch_ai.py "$@"
