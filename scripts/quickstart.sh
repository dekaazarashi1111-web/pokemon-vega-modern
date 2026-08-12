#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if [[ ! -f config/project.toml ]]; then
  cp config/project.example.toml config/project.toml
fi

mkdir -p inputs/private inputs/reference inputs/source_archives
python3 scripts/bootstrap_project.py --config config/project.toml --auto --lock-inputs
python3 scripts/run_baseline_audit.py --config config/project.toml --target t00
python3 scripts/preflight.py --config config/project.toml
python3 scripts/validate_task_graph.py
python3 scripts/validate_manifests.py
python3 scripts/verify_imported_packages.py
python3 scripts/project_status.py --check
python3 scripts/guard_private_files.py
python3 scripts/taskctl.py next
