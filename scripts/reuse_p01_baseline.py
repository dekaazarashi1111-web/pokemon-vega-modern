#!/usr/bin/env python3
"""P01: 同一baselineの成功証跡をsource差分・API・実ROMで照合。差異は再実行。"""
from __future__ import annotations
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts.build_p01_rom import identity

PIN_HEAD = "a89cd50f4a065a399553619456a4a17dc66de3a3"
PIN_RUN = 34172673504
REPO = "dekaazarashi1111-web/pokemon-vega-modern"
ROM = {"size": 33554432, "sha256": "d97a0d4a6cd6f8f77a1503a5ac6d473b0e94c4892e3d5a94098497ce35cb6e6f", "crc32": "73E4FB73"}
# baselineの実装・config・入力・既存依存は一つも許可しない。P01追加物と記録だけ。
NON_BASELINE_PATHS = frozenset({
    ".github/workflows/ci.yml", ".github/workflows/p01-record-checkpoint.yml",
    ".github/workflows/p01-target-validation.yml", ".github/workflows/p01-runtime-validation.yml",
    ".github/workflows/p01-candidate-validation.yml", ".github/workflows/p01-reference-validation.yml",
    "scripts/audit_p01_rom.py", "scripts/audit_p01_references.py", "scripts/build_p01_collection_table.py",
    "scripts/build_p01_rom.py", "scripts/run_p01_identity_mgba.py", "scripts/reuse_p01_baseline.py",
    "tools/mgba_p01_identity.c", "tests/test_p01_rom_audit.py", "tests/test_p01_rom_build.py",
    "tests/test_p01_collection_consumer.py", "tests/test_p01_references.py", "tests/test_p01_baseline_reuse.py",
    "config/modernization_rom_repair.json", "config/modernization_candidate.json", "config/modernization_inputs.json",
    "design/modernization_p01_audit.md", "design/modernization_p01_execution_evidence.json",
    "design/modernization_handoff.md", "design/modernization_p01_checkpoint.md",
    "design/run_log.md", "design/version_log.md", "design/tasks_next.md",
    "tasks/USER_MODERNIZATION_P01.md", "docs/MODERNIZATION_CURRENT_ID_INDEX_JA.md",
})


def eligible(paths: list[str]) -> bool:
    return set(paths) <= NON_BASELINE_PATHS


def valid_run(run: dict) -> bool:
    return (run.get("id") == PIN_RUN and run.get("head_sha") == PIN_HEAD
            and run.get("status") == "completed" and run.get("conclusion") == "success"
            and run.get("name") == "p01-runtime-validation" and run.get("event") == "pull_request")


def main() -> int:
    baseline = json.loads((ROOT / "config/active_play_baseline.json").read_text())
    raw = (ROOT / baseline["rom"]["path"]).read_bytes()
    reuse = False
    paths = []
    try:
        # commit差分だけを確認する。全repositoryの内容走査を新設しない。
        subprocess.run(["git", "fetch", "--no-tags", "--depth=1", "origin", PIN_HEAD], cwd=ROOT, check=True, capture_output=True)
        paths = subprocess.check_output(["git", "diff", "--name-only", "--no-renames", "-z", PIN_HEAD, "HEAD"], cwd=ROOT).decode().rstrip("\0").split("\0")
        paths = [path for path in paths if path]
        api = subprocess.check_output(["gh", "api", "repos/" + REPO + "/actions/runs/" + str(PIN_RUN)], cwd=ROOT)
        reuse = eligible(paths) and valid_run(json.loads(api)) and identity(raw) == ROM and baseline["stage"] == 62
    except (subprocess.SubprocessError, OSError, ValueError):
        reuse = False
    if not reuse:
        # 証跡不足や未知の差分ではskipしない。同じ既存mGBA gateを本当に実行する。
        return subprocess.run([sys.executable, "scripts/run_p01_baseline_gate.py", "stage62-mgba"], cwd=ROOT).returncode
    print(json.dumps({"status": "PASS", "verification": "VERIFIED_SAME_BASELINE_EVIDENCE_REUSE",
                      "evidence_run": PIN_RUN, "evidence_head": PIN_HEAD,
                      "current_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                      "rom": ROM, "baseline_implementation_changed": False,
                      "non_baseline_changed_paths": sorted(paths), "new_candidate_verified_by_this_gate": False}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
