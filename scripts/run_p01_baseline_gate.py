#!/usr/bin/env python3
"""P01 baseline gateの限定結果。private例外本文・ROM/save・生ログは出力しない。"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import zlib

ROOT = Path(__file__).resolve().parents[1]
COMMANDS = {
    "stage62-check": ["scripts/build_stage62_npc_placement_integrity_repair.py", "check", "--runs", "2"],
    "stage62-mgba": ["scripts/build_stage62_npc_placement_integrity_repair.py", "mgba", "--runs", "2"],
}


def identity(path: Path) -> dict:
    data = path.read_bytes()
    return {"size": len(data), "sha256": hashlib.sha256(data).hexdigest(), "crc32": f"{zlib.crc32(data) & 0xffffffff:08X}"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("suite", choices=tuple(COMMANDS))
    args = parser.parse_args()
    baseline = json.loads((ROOT / "config/active_play_baseline.json").read_text())
    candidate = json.loads((ROOT / "config/modernization_candidate.json").read_text())
    expected = {key: baseline["rom"][key] for key in ("size", "sha256", "crc32")}
    if baseline["stage"] != 62 or any(candidate["parent"][key] != value for key, value in expected.items()):
        raise SystemExit("P01_PARENT_IDENTITY_MISMATCH")
    path = ROOT / baseline["rom"]["path"]
    before = identity(path)
    if before != expected:
        raise SystemExit("P01_BASELINE_ROM_IDENTITY_MISMATCH")
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    result = {"schema_version": 1, "task": "USER-MODERNIZATION-P01", "suite": args.suite,
              "head": head, "baseline_rom": before, "new_candidate_validated": False}
    with tempfile.TemporaryFile() as log:
        process = subprocess.run([sys.executable, *COMMANDS[args.suite]], cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, timeout=1200)
        result["exit_code"] = process.returncode
        result["status"] = "PASS" if process.returncode == 0 else "FAIL"
        if process.returncode:
            log.seek(0)
            text = log.read().decode("utf-8", errors="replace")
            result["exception_types"] = sorted(set(re.findall(r"^([A-Za-z_][A-Za-z0-9_]*(?:Error|Exception)):", text, re.MULTILINE)))
            frames = []
            for name, lineno in re.findall(r'File "([^"]+\.py)", line ([0-9]+)', text):
                try:
                    relative = Path(name).resolve().relative_to(ROOT).as_posix()
                    tracked = subprocess.check_output(["git", "ls-files", "--", relative], cwd=ROOT, text=True).strip()
                    if tracked == relative and re.fullmatch(r"(?:scripts|tools)/[A-Za-z0-9_./-]+\.py", relative):
                        frame = {"path": relative, "line": int(lineno)}
                        if frame not in frames:
                            frames.append(frame)
                except (ValueError, OSError, subprocess.SubprocessError):
                    pass
            result["tracked_frames"] = frames[-12:]
    after = identity(path)
    result["baseline_unchanged"] = before == after
    if not result["baseline_unchanged"]:
        result["status"] = "FAIL"
    output = ROOT / "generated/modernization"
    output.mkdir(parents=True, exist_ok=True)
    (output / (args.suite + "_result.json")).write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
