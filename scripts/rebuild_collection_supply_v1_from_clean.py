#!/usr/bin/env python3
"""clean FireRed日本版Rev.0からStage56を二経路で厳密再構築する。"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Mapping, NoReturn

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_collection_supply_v1 import _static_outputs  # noqa: E402
from tools.release.bps import apply_bps  # noqa: E402


TASK = "USER-20260827-COLLECTION-SUPPLY-V1-IMPLEMENTATION"
STAGE = 56
CONFIG = Path("config/collection_supply_v1.json")


class CollectionSupplyCleanRebuildError(RuntimeError):
    """clean、Stage55/56 BPSまたは最終証跡の契約違反。"""


def _fail(message: str) -> NoReturn:
    raise CollectionSupplyCleanRebuildError(message)


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _stable(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2)
            + "\n").encode("utf-8")


def _read(path: str | Path) -> bytes:
    try:
        return (ROOT / Path(path)).read_bytes()
    except OSError as error:
        _fail(f"必須成果物を読めません: {path}: {error}")


def _json(path: str | Path) -> dict[str, Any]:
    try:
        value = json.loads(_read(path))
    except json.JSONDecodeError as error:
        _fail(f"JSON不正: {path}: {error}")
    if not isinstance(value, dict):
        _fail(f"JSON root不一致: {path}")
    return value


def _identity(raw: bytes, contract: Mapping[str, Any], label: str) -> None:
    if "size" in contract and len(raw) != int(contract["size"]):
        _fail(f"{label} size不一致")
    if _sha(raw) != str(contract["sha256"]):
        _fail(f"{label} SHA-256不一致")


def _document() -> dict[str, Any]:
    config = _json(CONFIG)
    if config.get("task") != TASK or config.get("stage") != STAGE:
        _fail("Collection Supply config task/stage不一致")
    inputs = config["inputs"]
    outputs = config["outputs"]
    clean = _read(inputs["clean_rom"]["path"])
    stage55 = _read(inputs["stage55_rom"]["path"])
    stage56 = _read(outputs["rom"])
    _identity(clean, inputs["clean_rom"], "clean FireRed")
    _identity(stage55, inputs["stage55_rom"], "Stage55")

    metadata55 = _json(inputs["stage55_metadata"]["path"])
    clean55_contract = metadata55.get("bps", {}).get("clean")
    if not isinstance(clean55_contract, dict):
        _fail("Stage55 clean BPS契約がありません")
    clean55 = _read(clean55_contract["path"])
    _identity(clean55, clean55_contract, "clean→Stage55 BPS")
    rebuilt55 = apply_bps(clean, clean55)
    if rebuilt55 != stage55:
        _fail("clean→Stage55 BPS再構築不一致")

    incremental = _read(outputs["incremental_bps"])
    direct = _read(outputs["clean_bps"])
    chained56 = apply_bps(rebuilt55, incremental)
    direct56 = apply_bps(clean, direct)
    if chained56 != stage56 or direct56 != stage56:
        _fail("Stage55差分／clean直接BPSのStage56再構築不一致")

    static_first = _static_outputs(CONFIG)
    static_second = _static_outputs(CONFIG)
    if static_first != static_second:
        _fail("Stage56 source buildが非決定的です")
    if static_first[outputs["rom"]] != stage56:
        _fail("Stage56 source buildと公開ROMが不一致")
    if (static_first[outputs["incremental_bps"]] != incremental
            or static_first[outputs["clean_bps"]] != direct):
        _fail("Stage56 source buildと公開BPSが不一致")

    metadata = _json(outputs["metadata"])
    quick = _json(outputs["mgba_quick"])
    full = _json(outputs["mgba_full"])
    if (
        metadata.get("status") != "PASS"
        or metadata.get("output", {}).get("sha256") != _sha(stage56)
        or metadata.get("mgba", {}).get("status") != "PASS"
        or metadata.get("mgba", {}).get("process_count") != 2
        or metadata.get("world_input_e2e", {}).get("status") != "PASS"
        or metadata.get("world_input_e2e", {}).get("process_runs") != 2
        or quick.get("status") != "PASS"
        or full.get("status") != "PASS"
        or quick.get("rom_sha256") != full.get("rom_sha256")
        or quick.get("rom_sha256") != _sha(stage56)
        or quick.get("tests") != full.get("tests")
        or any(value is not True for value in quick.get("tests", {}).values())
    ):
        _fail("Stage56 final metadata/mGBA/world証跡不一致")

    return {
        "schema_version": 1,
        "task": TASK,
        "stage": STAGE,
        "status": "PASS",
        "output": {
            "path": outputs["rom"], "size": len(stage56),
            "sha256": _sha(stage56),
        },
        "routes": {
            "clean_to_stage55": {
                "patch": clean55_contract["path"],
                "patch_sha256": _sha(clean55), "exact": True,
            },
            "stage55_to_stage56": {
                "patch": outputs["incremental_bps"],
                "patch_sha256": _sha(incremental), "exact": True,
            },
            "clean_to_stage56": {
                "patch": outputs["clean_bps"],
                "patch_sha256": _sha(direct), "exact": True,
            },
            "source_build": {
                "builder": "scripts/build_collection_supply_v1.py",
                "two_runs_byte_identical": True,
                "rom_exact": True,
                "patches_exact": True,
            },
        },
        "acceptance": {
            "mgba_processes": 2,
            "mgba_quick_full_equal": True,
            "world_input_processes": 2,
            "world_input_fixtures": 22,
            "ipad_required": False,
        },
    }


def _write(path: Path, raw: bytes) -> None:
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as stream:
        stream.write(raw)
        temporary = Path(stream.name)
    os.replace(temporary, target)


def main() -> int:
    global CONFIG
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("build", "check"))
    parser.add_argument("--config", type=Path, default=CONFIG)
    args = parser.parse_args()
    CONFIG = args.config
    try:
        config = _json(CONFIG)
        output = Path(config["outputs"]["clean_rebuild"])
        raw = _stable(_document())
        if args.mode == "build":
            _write(output, raw)
        elif not (ROOT / output).is_file() or (ROOT / output).read_bytes() != raw:
            _fail(f"clean rebuild証跡drift: {output}")
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError,
            CollectionSupplyCleanRebuildError) as error:
        print(f"Collection Supply clean rebuild {args.mode} failed: {error}",
              file=sys.stderr)
        return 1
    document = json.loads(raw)
    print("Collection Supply clean rebuild %s: PASS sha256=%s"
          % (args.mode, document["output"]["sha256"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
