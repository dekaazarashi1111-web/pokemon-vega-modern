#!/usr/bin/env python3
"""Stage63の取得runtimeを後続map所有者から分離してmGBA検証する。"""

from __future__ import annotations

import hashlib
import json
import struct
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import build_acquisition_events as acquisition  # noqa: E402


CANDIDATE = Path("config/modernization_candidate.json")
RUNTIME_CONFIG = Path("config/modernization_p01_runtime.json")
ACQUISITION_METADATA = Path("build/stages/26_acquisition_events.json")
EVOLUTION_REPORT = Path("generated/runtime/acquisition_evolution_routes.json")


class ModernizationP01MgbaError(RuntimeError):
    """Stage63 identityまたはmGBA runtime検証の不一致。"""


def _json(path: Path) -> dict[str, Any]:
    value = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ModernizationP01MgbaError(f"JSON rootがobjectではありません: {path}")
    return value


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def run() -> dict[str, Any]:
    candidate = _json(CANDIDATE)["candidate"]
    runtime_config = _json(RUNTIME_CONFIG)
    rom = (ROOT / candidate["path"]).read_bytes()
    if len(rom) != candidate["size"] or _sha(rom) != candidate["sha256"]:
        raise ModernizationP01MgbaError("Stage63 candidate identityが不一致です")

    table = runtime_config["runtime_table"]
    offset = int(table["rom_offset"])
    row_size = int(table["row_size"])
    egg = struct.unpack_from("<HHBBBB", rom, offset + 412 * row_size)
    caterpie = struct.unpack_from("<HHBBBB", rom, offset + 649 * row_size)
    if egg != (412, 0xFFFF, 0, 0, 0, 0):
        raise ModernizationP01MgbaError(f"内部Egg runtime rowが不一致です: {egg}")
    if caterpie != (649, 386, 1, 1, 1, 0):
        raise ModernizationP01MgbaError(f"Caterpie runtime rowが不一致です: {caterpie}")

    metadata = _json(ACQUISITION_METADATA)
    evolution = _json(EVOLUTION_REPORT)
    identity = acquisition._load_species_identity_contract(ROOT)
    fixture = acquisition._mgba_fixture(
        ROOT,
        rom,
        metadata["runtime"],
        metadata["map_scripts"],
        evolution,
        metadata["wild_sanitization"],
        int(metadata["save_validator"]["site"]) - acquisition.GBA_ROM_BASE,
        identity,
        identity_only=True,
    )
    if fixture.get("physical_host_chain") is not False:
        raise ModernizationP01MgbaError("runtime-only gateが物理host検証を誤って主張しました")

    return {
        "schema_version": 1,
        "task": "USER-MODERNIZATION-P01",
        "status": "PASS",
        "rom_sha256": candidate["sha256"],
        "process_runs": fixture["process_runs"],
        "scope": {
            "acquisition_runtime": True,
            "collection_registration": True,
            "evolution_and_wild_tables": True,
            "stage26_physical_host_chain": False,
            "physical_host_skip_reason": (
                "Stage36以降がmap event chainを所有するため、Stage26の旧host物理addressは"
                "P01 runtime回帰の対象外。runtime関数・現存hook・表・saveを検証する"
            ),
        },
        "collection_rows": {
            "SPECIES_KEY_EGG": list(egg),
            "SPECIES_KEY_CATERPIE": list(caterpie),
        },
        "runtime_assertions": {
            "caterpie_registration_round_trip": fixture[
                "caterpie_registration_round_trip"
            ],
            "internal_egg_registration_excluded": fixture[
                "internal_egg_registration_excluded"
            ],
            "save_layout_preserved": fixture["save_layout_preserved"],
        },
        "warnings_errors": fixture["warnings_errors"],
        "artifacts_written": fixture["artifacts_written"],
    }


def main() -> int:
    try:
        report = run()
    except (OSError, ValueError, KeyError, acquisition.AcquisitionBuildError,
            ModernizationP01MgbaError) as error:
        print(f"Modernization P01 mGBA: FAIL: {error}", file=sys.stderr)
        return 1
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
