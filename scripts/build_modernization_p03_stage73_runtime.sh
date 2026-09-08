#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
workspace_root="$(cd -- "${script_dir}/.." && pwd)"
action="${1:-build}"
if [[ $# -gt 0 ]]; then
  shift
fi

cd "${workspace_root}"
exec python3 tools/modernization_p03_stage73_runtime.py \
  "${action}" --config config/modernization_p03_stage73_runtime.json "$@"
