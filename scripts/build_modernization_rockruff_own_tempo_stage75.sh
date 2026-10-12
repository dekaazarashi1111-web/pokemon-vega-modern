#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
PYTHONDONTWRITEBYTECODE=1 python3 tools/modernization_rockruff_own_tempo_stage75.py "$@"
