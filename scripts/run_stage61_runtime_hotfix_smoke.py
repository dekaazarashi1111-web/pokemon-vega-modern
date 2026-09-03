#!/usr/bin/env python3
"""Stage61 runtime hotfixをfreshなlibmGBA processでfocused検証する。"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config/stage61_runtime_hotfix.json"
SOURCE = ROOT / "tools/mgba_stage61_runtime_hotfix_smoke.c"


class SmokeError(RuntimeError):
    pass


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _stable(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2)
            + "\n").encode("utf-8")


def _identity(root: Path, contract: dict[str, Any], label: str) -> bytes:
    path = root / contract["path"]
    raw = path.read_bytes()
    if len(raw) != int(contract["size"]) or _sha(raw) != contract["sha256"]:
        raise SmokeError(f"{label} identity differs")
    return raw


def _compile(executable: Path) -> None:
    compiler = shutil.which("cc")
    if compiler is None:
        raise SmokeError("C compiler is unavailable")
    completed = subprocess.run(
        [compiler, "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
         "-pedantic", str(SOURCE), "-o", str(executable), "-lmgba"],
        cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        timeout=180, check=False,
    )
    if completed.returncode or completed.stdout or completed.stderr:
        raise SmokeError(
            "mGBA runner compile failed: "
            + (completed.stderr or completed.stdout or str(completed.returncode))[-6000:])


def _run(executable: Path, rom: Path, save: Path, index: int) -> dict[str, Any]:
    completed = subprocess.run(
        [str(executable), str(rom), str(save)], cwd=ROOT, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=900, check=False,
    )
    if completed.returncode or completed.stderr:
        raise SmokeError(
            f"mGBA process {index} failed exit={completed.returncode}: "
            + (completed.stderr or completed.stdout)[-8000:])
    try:
        document = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        raise SmokeError(f"mGBA process {index} JSON invalid: {error}") from error
    if document.get("status") != "PASS" \
            or not document.get("tests") \
            or not all(document["tests"].values()) \
            or document.get("warnings_errors") != 0:
        raise SmokeError(f"mGBA process {index} acceptance differs: {document}")
    return document


def run(config_path: Path = CONFIG, process_runs: int = 2) -> dict[str, Any]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    metadata = json.loads((ROOT / config["outputs"]["metadata"]).read_text(encoding="utf-8"))
    rom_path = ROOT / config["outputs"]["rom"]
    rom = rom_path.read_bytes()
    digest = _sha(rom)
    if len(rom) != 32 * 1024 * 1024 \
            or metadata.get("output", {}).get("sha256") != digest \
            or metadata.get("status") != "PASS":
        raise SmokeError("Stage61 hotfix ROM/metadata identity differs")
    seed_contract = config["inputs"]["mgba_seed_save"]
    seed = _identity(ROOT, seed_contract, "mGBA seed save")
    if process_runs < 1 or process_runs > 4:
        raise SmokeError("process run count outside 1..4")

    with tempfile.TemporaryDirectory(prefix="stage61-hotfix-mgba-", dir=ROOT / ".local") as tmp:
        directory = Path(tmp)
        executable = directory / "runner"
        _compile(executable)
        documents: list[dict[str, Any]] = []
        for index in range(1, process_runs + 1):
            save = directory / f"run-{index}.sav"
            save.write_bytes(seed)
            documents.append(_run(executable, rom_path, save, index))
    if any(document != documents[0] for document in documents[1:]):
        raise SmokeError("independent mGBA process results differ")
    result = {
        "schema_version": 1,
        "task": config["task"],
        "status": "PASS",
        "rom": {"path": config["outputs"]["rom"], "size": len(rom),
                "sha256": digest},
        "seed_save": {"path": seed_contract["path"], "size": len(seed),
                      "sha256": _sha(seed), "mutated": False},
        "process_runs": process_runs,
        "identical_results": True,
        "result": documents[0],
        "physical_paths": {
            "move_memory": ["Bagから使用", "おもいだす選択", "party cancel", "field復帰",
                            "menu B cancel", "field復帰"],
            "ecology_radar": ["Bagから使用", "夜固定選択", "mode=2", "field復帰",
                              "menu B cancel", "field復帰"],
        },
    }
    output = ROOT / config["outputs"]["mgba"]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(_stable(result))
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=CONFIG)
    parser.add_argument("--process-runs", type=int, default=2)
    args = parser.parse_args()
    try:
        result = run(args.config, args.process_runs)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError,
            subprocess.SubprocessError, SmokeError) as error:
        print(f"Stage61 runtime hotfix mGBA: FAIL: {error}")
        return 1
    print(json.dumps({
        "status": result["status"], "sha256": result["rom"]["sha256"],
        "process_runs": result["process_runs"],
        "tests": len(result["result"]["tests"]),
    }, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
