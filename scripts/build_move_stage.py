#!/usr/bin/env python3
"""T04: Vega技ID固定modelとstage 04 ROMを決定的に生成・検査する。"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import struct
import sys
import tempfile
from pathlib import Path
from typing import Any, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_move_port import (  # noqa: E402
    MovePortError,
    build_move_model,
    render_artifacts,
    validate_move_model,
)
from scripts.build_project import (  # noqa: E402
    HarnessBuildError,
    _read_json_object,
    _run,
    _tool_environment,
    _verify_smoke_toolchain,
    check_harness,
)
from scripts.common import sha256_file, stable_digest, write_json  # noqa: E402
from tools.rom_allocator import (  # noqa: E402
    GBA_ROM_BASE,
    ROM_SIZE,
    build_allocation_report_from_csv,
)


SCHEMA_VERSION = 1
TASK_ID = "T04"
STAGE_ROM = Path("build/stages/04_moves.gba")
STAGE_METADATA = Path("build/stages/04_moves.json")
ALLOCATION_REPORT = Path("build/stages/04_allocation.json")
REPORT = Path("reports/generated/move_port.md")
CONFIG = Path("config/move_port.json")
STAGE03_ROM = Path("build/stages/03_harness.gba")
STAGE03_METADATA = Path("build/stages/03_harness.json")
ADAPTER_METADATA = Path("build/modules/vega_adapter/metadata.json")
EXPECTED_ARTIFACT_KEYS = frozenset(
    {
        "generated/engine/moves/move_port.json",
        "generated/engine/moves/moves_merged.h",
        "generated/engine/moves/battle_moves.c",
        "generated/engine/moves/move_names.c",
        "generated/engine/moves/move_descriptions.c",
        "generated/engine/moves/move_effect_map.c",
        "generated/engine/moves/move_animation_map.c",
        "generated/engine/moves/move_effect_adapters.c",
        "generated/engine/moves/vega_bridge.bin",
        "generated/engine/moves/layout.json",
        "manifests/move_ids.csv",
    }
)
FINGERPRINT_FILES = (
    "Makefile",
    "config/move_port.json",
    "config/rom_regions.csv",
    "infra/toolchain_manifest.json",
    "scripts/build_move_stage.py",
    "scripts/build_move_port.py",
    "scripts/build_project.py",
    "tools/rom_allocator.py",
    "tools/engine/extract_vega_moves.py",
    "tools/engine/cfru_move_inventory.py",
    "tools/mgba_move_smoke.c",
    "tools/mgba_ai_fixture_runner.c",
    "design/imported/VEGA_CFRU_DPE_技調整設計_V3/SHA256SUMS.txt",
    "design/imported/VEGA_CFRU_DPE_技調整設計_V3/data/技効果現代化マスター.csv",
    "design/imported/VEGA_CFRU_DPE_技調整設計_V3/data/ベガ独自技再調整マスター.csv",
)
TABLE_ORDER = ("names", "battle", "descriptions", "animations", "effects")


class MoveStageError(RuntimeError):
    """T04 stage、成果物、smokeのいずれかが固定契約に違反した。"""


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_json(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode(
        "utf-8"
    )


def _read_config(root: Path) -> dict[str, Any]:
    config = _read_json_object(root / CONFIG, "move port config")
    if config.get("schema_version") != SCHEMA_VERSION or config.get("task") != TASK_ID:
        raise MoveStageError("move port config schema/task mismatch")
    return config


def _generated(root: Path, config: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, bytes]]:
    model = build_move_model(root, config)
    validate_move_model(model)
    rendered = render_artifacts(model)
    if set(rendered) != EXPECTED_ARTIFACT_KEYS:
        missing = sorted(EXPECTED_ARTIFACT_KEYS - set(rendered))
        extra = sorted(set(rendered) - EXPECTED_ARTIFACT_KEYS)
        raise MoveStageError(f"generated artifact set mismatch: missing={missing}, extra={extra}")
    artifacts: dict[str, bytes] = {}
    for logical, payload in rendered.items():
        if Path(logical).is_absolute() or ".." in Path(logical).parts:
            raise MoveStageError(f"generated artifact path is unsafe: {logical}")
        if not isinstance(payload, bytes) or not payload:
            raise MoveStageError(f"generated artifact is empty/non-bytes: {logical}")
        artifacts[logical] = payload
    return model, artifacts


def _table_layout(config: Mapping[str, Any], bridge_size: int) -> dict[str, dict[str, int]]:
    cursor = 0
    layout: dict[str, dict[str, int]] = {}
    tables = config["vega"]["tables"]
    for name in TABLE_ORDER:
        table = tables[name]
        size = int(table["count"]) * int(table["stride"])
        layout[name] = {
            "offset": cursor,
            "size": size,
            "count": int(table["count"]),
            "stride": int(table["stride"]),
        }
        cursor += size
    if cursor != bridge_size or cursor != int(config["bridge"]["expected_size"]):
        raise MoveStageError(
            f"Vega bridge size mismatch: layout={cursor}, artifact={bridge_size}, "
            f"config={config['bridge']['expected_size']}"
        )
    return layout


def discover_table_repoints(
    rom: bytes,
    config: Mapping[str, Any],
    *,
    bridge_start: int,
    bridge_size: int,
) -> tuple[list[dict[str, Any]], dict[str, dict[str, int]]]:
    """Vega-owned 16 MiBのaligned pointer wordを全件列挙する。"""

    if len(rom) != ROM_SIZE:
        raise MoveStageError("stage 03 ROM must be exactly 32 MiB")
    vega_size = int(config["vega"]["rom_size"])
    if vega_size != 0x01000000 or bridge_start & 3:
        raise MoveStageError("Vega/bridge layout contract mismatch")
    layout = _table_layout(config, bridge_size)
    rows: list[dict[str, Any]] = []
    seen_sites: set[int] = set()
    for name in TABLE_ORDER:
        contract = config["vega"]["tables"][name]
        old_pointer = int(str(contract["address"]), 0)
        new_pointer = GBA_ROM_BASE + bridge_start + layout[name]["offset"]
        needle = struct.pack("<I", old_pointer)
        sites = [
            offset
            for offset in range(0, vega_size - 3, 4)
            if rom[offset : offset + 4] == needle
        ]
        expected_count = int(contract["reference_count"])
        if len(sites) != expected_count:
            raise MoveStageError(
                f"{name} repoint count mismatch: expected {expected_count}, got {len(sites)}"
            )
        for offset in sites:
            if offset in seen_sites:
                raise MoveStageError(f"duplicate repoint site: 0x{offset:08X}")
            seen_sites.add(offset)
            rows.append(
                {
                    "table": name,
                    "rom_offset": offset,
                    "gba_address": GBA_ROM_BASE + offset,
                    "old_pointer": old_pointer,
                    "new_pointer": new_pointer,
                    "size": 4,
                }
            )
    rows.sort(key=lambda row: int(row["rom_offset"]))
    expected_total = sum(
        int(config["vega"]["tables"][name]["reference_count"])
        for name in TABLE_ORDER
    )
    if len(rows) != expected_total or expected_total != 178:
        raise MoveStageError(f"total repoint count mismatch: {len(rows)} / {expected_total}")
    return rows, layout


def build_stage_bytes(
    stage03: bytes, bridge: bytes, config: Mapping[str, Any]
) -> tuple[bytes, list[dict[str, Any]], dict[str, dict[str, int]]]:
    """bridgeを挿入し、Vegaの全aligned table referenceを更新する。"""

    start = int(str(config["bridge"]["start"]), 0)
    end = start + len(bridge)
    if not 0 <= start < end <= len(stage03):
        raise MoveStageError("move bridge allocation is outside ROM")
    if stage03[start:end] != b"\xFF" * len(bridge):
        raise MoveStageError("move bridge destination is not erased 0xFF")
    repoints, layout = discover_table_repoints(
        stage03, config, bridge_start=start, bridge_size=len(bridge)
    )
    output = bytearray(stage03)
    output[start:end] = bridge
    for row in repoints:
        offset = int(row["rom_offset"])
        old = struct.pack("<I", int(row["old_pointer"]))
        if output[offset : offset + 4] != old:
            raise MoveStageError(f"repoint expected bytes changed: 0x{offset:08X}")
        output[offset : offset + 4] = struct.pack("<I", int(row["new_pointer"]))
    return bytes(output), repoints, layout


def _allocation(
    root: Path, bridge: bytes, config: Mapping[str, Any]
) -> dict[str, Any]:
    adapter = _read_json_object(root / ADAPTER_METADATA, "T03 adapter metadata")
    adapter_request = adapter.get("allocator_request")
    if not isinstance(adapter_request, Mapping):
        raise MoveStageError("T03 adapter allocator request is missing")
    move_request = {
        "name": "move_table_bridge",
        "region": str(config["bridge"]["region"]),
        "start": int(str(config["bridge"]["start"]), 0),
        "size": len(bridge),
        "alignment": int(config["bridge"]["alignment"]),
        "owner": TASK_ID,
        "purpose": "Vega move tables with V3 adjustments and canonical repoints",
        "content_sha256": _sha256_bytes(bridge),
    }
    report = build_allocation_report_from_csv(
        root / "config/rom_regions.csv", [dict(adapter_request), move_request]
    )
    if report["summaries"]["overlap_count"] != 0 or len(report["allocations"]) != 2:
        raise MoveStageError("T03/T04 allocation contract failed")
    move_row = next(
        (row for row in report["allocations"] if row["name"] == "move_table_bridge"),
        None,
    )
    if (
        move_row is None
        or move_row["start"] != move_request["start"]
        or move_row["size"] != len(bridge)
        or move_row["content_sha256"] != _sha256_bytes(bridge)
    ):
        raise MoveStageError("move allocation/content cross-link failed")
    return report


def _validate_smoke(payload: object, expected_sha256: str) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise MoveStageError("move smoke is not an object")
    if (
        payload.get("schema_version") != 1
        or payload.get("status") != "PASS"
        or payload.get("fixture") != "synthetic_rooted_early_wild_battle"
        or payload.get("battle_kind") != "WILD"
        or payload.get("rom_sha256") != expected_sha256
        or payload.get("fixed_rtc_unix") != 946684800
        or payload.get("boot_trace_segments") != 233
        or payload.get("progress_frames") != 300
        or payload.get("warnings_errors") != 0
        or payload.get("artifacts_written") != []
        or payload.get("core_alive_after_progression") is not True
        or payload.get("active_move_ids_stable") is not True
    ):
        raise MoveStageError("move smoke envelope failed")
    if payload.get("provenance") != {
        "field_base": "natural_T03_233_segment_trace",
        "rooted_species": {"player": 4, "enemy": 10, "level": 5},
        "direct_rom_calls": {
            "CreateMon": "0x0803D1C1",
            "BattleSetup_StartWildBattle": "0x0807EE2D",
        },
    } or payload.get("move_id_contract") != {
        "zero_slot_allowed": True,
        "nonzero_min": 1,
        "nonzero_max": 511,
    }:
        raise MoveStageError("move smoke provenance/ID contract failed")
    expected_moves = {33, 43, 45, 64, 116}
    observed: set[int] = set()
    for phase in ("before", "after"):
        snapshot = payload.get(phase)
        if (
            not isinstance(snapshot, Mapping)
            or snapshot.get("wild_battle_active") is not True
            or int(snapshot.get("battle_type_flags", -1)) & 0x8
            or snapshot.get("active_battlers") != 2
            or snapshot.get("absent_flags") != 0
        ):
            raise MoveStageError(f"move smoke {phase} battle contract failed")
        battlers = snapshot.get("battlers")
        if not isinstance(battlers, list) or len(battlers) != 2:
            raise MoveStageError(f"move smoke {phase} battlers are incomplete")
        pc = snapshot.get("pc")
        digest = snapshot.get("ewram_iwram_fnv1a64")
        if (
            not isinstance(pc, int)
            or not (
                0x02000000 <= pc < 0x02040000
                or 0x03000000 <= pc < 0x03008000
                or 0x08000000 <= pc < 0x0A000000
            )
            or not isinstance(digest, str)
            or len(digest) != 16
            or any(character not in "0123456789abcdef" for character in digest)
        ):
            raise MoveStageError(f"move smoke {phase} execution evidence is invalid")
        for battler in battlers:
            if not isinstance(battler, Mapping) or int(battler.get("hp", 0)) <= 0:
                raise MoveStageError(f"move smoke {phase} battler is invalid")
            moves = battler.get("moves")
            pp = battler.get("pp")
            if not isinstance(moves, list) or not isinstance(pp, list) or len(moves) != 4 or len(pp) != 4:
                raise MoveStageError(f"move smoke {phase} move slots are invalid")
            if not any(int(move) for move in moves):
                raise MoveStageError(f"move smoke {phase} has no usable move")
            for move, remaining in zip(moves, pp, strict=True):
                move_id = int(move)
                if move_id:
                    if not 1 <= move_id <= 511 or int(remaining) <= 0:
                        raise MoveStageError(f"move smoke {phase} move ID/PP is invalid")
                    observed.add(move_id)
    before_battlers = payload["before"]["battlers"]
    after_battlers = payload["after"]["battlers"]
    if observed != expected_moves:
        raise MoveStageError("move smoke early move identity mismatch")
    for before, after in zip(before_battlers, after_battlers, strict=True):
        if before["species"] != after["species"] or before["moves"] != after["moves"]:
            raise MoveStageError("move smoke active move identity changed")
    execution = payload.get("move_execution")
    if execution != {
        "input": "A_x6_slot0",
        "player_pp_spent": True,
        "hp_changed": True,
    }:
        raise MoveStageError("move smoke did not execute the fixed battle turn")
    if after_battlers[0]["pp"][0] != before_battlers[0]["pp"][0] - 1:
        raise MoveStageError("move smoke player slot-0 PP delta is not exactly one")
    if after_battlers[1]["hp"] >= before_battlers[1]["hp"]:
        raise MoveStageError("move smoke fixed player move did not lower enemy HP")
    if payload["before"]["ewram_iwram_fnv1a64"] == payload["after"]["ewram_iwram_fnv1a64"]:
        raise MoveStageError("move smoke did not observe runtime progression")
    return payload


def _compile_and_run_smoke(
    root: Path, work: Path, reference: Path, candidate: Path
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    manifest = _read_json_object(root / "infra/toolchain_manifest.json", "toolchain manifest")
    toolchain = _verify_smoke_toolchain(manifest)
    compiler = str(manifest["tools"]["host_cc"]["path"])
    runner = work / "mgba_move_smoke"
    _run(
        [
            compiler,
            "-std=c11",
            "-O2",
            "-Wall",
            "-Wextra",
            "-Werror",
            str(root / "tools/mgba_move_smoke.c"),
            "-o",
            str(runner),
            "-lmgba",
        ],
        cwd=root,
        timeout=60,
        require_empty_stderr=True,
    )
    runner.chmod(0o700)

    def run_one(path: Path) -> dict[str, Any]:
        digest = sha256_file(path)
        completed = _run(
            [str(runner), str(path), digest, "300"],
            cwd=work,
            timeout=60,
            require_empty_stderr=True,
        )
        try:
            payload = json.loads(completed.stdout.decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError) as error:
            raise MoveStageError("move smoke stdout is not one JSON document") from error
        return _validate_smoke(payload, digest)

    reference_result = run_one(reference)
    candidate_result = run_one(candidate)
    def comparable(payload: Mapping[str, Any]) -> dict[str, Any]:
        value = json.loads(json.dumps(payload))
        value.pop("rom_sha256", None)
        for phase in ("before", "after"):
            value[phase].pop("ewram_iwram_fnv1a64", None)
            value[phase].pop("pc", None)
        for battler in value["after"]["battlers"]:
            battler.pop("hp", None)
        return value

    comparable_reference = comparable(reference_result)
    comparable_candidate = comparable(candidate_result)
    if comparable_reference != comparable_candidate:
        raise MoveStageError("reference/candidate move smoke observations differ")
    toolchain["runner"] = {
        "source_sha256": sha256_file(root / "tools/mgba_move_smoke.c"),
        "included_source_sha256": sha256_file(root / "tools/mgba_ai_fixture_runner.c"),
        "binary_sha256": sha256_file(runner),
        "compiler_flags": ["-std=c11", "-O2", "-Wall", "-Wextra", "-Werror"],
    }
    return reference_result, candidate_result, toolchain


def _fingerprint_inputs(
    root: Path, stage03_sha256: str, config: Mapping[str, Any]
) -> dict[str, Any]:
    files: dict[str, str] = {}
    for logical in FINGERPRINT_FILES:
        path = root / logical
        if path.is_symlink() or not path.is_file():
            raise MoveStageError(f"fingerprint input is missing/non-regular: {logical}")
        files[logical] = sha256_file(path)
    return {
        "schema_version": SCHEMA_VERSION,
        "task": TASK_ID,
        "stage03_sha256": stage03_sha256,
        "vega_reference_sha256": str(config["vega"]["rom_sha256"]),
        "files": files,
        "repeat_count": 2,
    }


def _artifact_records(artifacts: Mapping[str, bytes]) -> dict[str, dict[str, Any]]:
    return {
        logical: {"size": len(payload), "sha256": _sha256_bytes(payload)}
        for logical, payload in sorted(artifacts.items())
    }


def _compile_runner_identity(root: Path) -> dict[str, Any]:
    """現在の固定toolchainでrunnerを再構築し、そのidentityだけを返す。"""

    manifest = _read_json_object(root / "infra/toolchain_manifest.json", "toolchain manifest")
    toolchain = _verify_smoke_toolchain(manifest)
    compiler = str(manifest["tools"]["host_cc"]["path"])
    build_root = root / "build"
    build_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".t04-runner-check-", dir=build_root) as raw:
        runner = Path(raw) / "mgba_move_smoke"
        _run(
            [
                compiler,
                "-std=c11",
                "-O2",
                "-Wall",
                "-Wextra",
                "-Werror",
                str(root / "tools/mgba_move_smoke.c"),
                "-o",
                str(runner),
                "-lmgba",
            ],
            cwd=root,
            timeout=60,
            require_empty_stderr=True,
        )
        binary_sha256 = sha256_file(runner)
    toolchain["runner"] = {
        "source_sha256": sha256_file(root / "tools/mgba_move_smoke.c"),
        "included_source_sha256": sha256_file(root / "tools/mgba_ai_fixture_runner.c"),
        "binary_sha256": binary_sha256,
        "compiler_flags": ["-std=c11", "-O2", "-Wall", "-Wextra", "-Werror"],
    }
    return toolchain


def _artifacts_written(artifacts: Mapping[str, bytes]) -> list[str]:
    return [
        STAGE_ROM.as_posix(),
        STAGE_METADATA.as_posix(),
        ALLOCATION_REPORT.as_posix(),
        REPORT.as_posix(),
        *sorted(artifacts),
    ]


def _render_report(metadata: Mapping[str, Any]) -> str:
    summaries = metadata["model_summaries"]
    repoints = metadata["repoints"]
    allocation = next(
        row
        for row in metadata["allocation"]["allocations"]
        if row["name"] == "move_table_bridge"
    )
    smoke = metadata["smoke"]["candidate"]
    counts = repoints["counts_by_table"]
    return f"""# T04 Vega Move ID port

- Status: `PASS`
- Fingerprint: `{metadata['fingerprint']}`
- Stage 04 ROM SHA-256: `{metadata['output']['sha256']}`
- Vega ID固定: `0..511`（512件）
- CFRU追加: `512..1062`（551件）
- 統合技数: `{summaries['move_count']}`

## Mapping

- exact NFKC共有: `{summaries['exact_match_count']}` Vega rows / `{summaries['exact_match_identity_count']}` CFRU identities
- V3独自技: `{summaries['v3_exclusive_count']}`件を自動同名一致より優先
- V3現代化: `{summaries['v3_modern_count']}`件
- Vega ID 470: `くらいつく` → **ソウルバイト** (`MOVE_KEY_SOUL_BITE`)
- Vega ID 509: `ねらいうち` → **ダークスナイプ** (`MOVE_KEY_DARK_SNIPE`)
- CFRU公式 `MOVE_JAWLOCK` / `MOVE_SNIPESHOT` は別のappend IDとして保持
- 曖昧・未解決・重複ID: `0`

## Generated tables and ROM repoints

- bridge: file offset `{allocation['start']:#010x}..{allocation['end_exclusive']:#010x}` / GBA `{allocation['gba_start']:#010x}`
- bridge size: `{allocation['size']}` bytes、allocator overlap `0`
- aligned pointer repoints: `{repoints['total']}` (`names {counts['names']}`, `battle {counts['battle']}`, `descriptions {counts['descriptions']}`, `animations {counts['animations']}`, `effects {counts['effects']}`)
- 連続2生成: model/artifacts/ROM/allocation byte-identical
- stage 03とbridge/repoint宣言span外のbyte差分: `0`

V3の全独自技提案70件をoperation列へ構造化し、compile済みadapter interface/dispatchを単一manifestから生成した。各adapterはVega effect pointerの来歴、数値、対象、優先度、追加効果を保持する。CFRU battle coreへのruntime bindingは依存タスクT06で有効化する。

## Early-game runtime smoke

- fixture: `{smoke['fixture']}`（自然T03 field状態からVega `CreateMon` / `BattleSetup_StartWildBattle`を直接使用）
- battle kind: `{smoke['battle_kind']}`、active battlers `{smoke['before']['active_battlers']}`
- observed frozen move IDs: `33, 43, 45, 64, 116`
- fixed progression: `{smoke['progress_frames']}` frames
- fixed input `A×6` でslot 0を実行し、双方でplayer PPがexact `-1`、enemy HPが低下
- reference Vega / candidate stage: species・move ID・PP deltaのsemantic projection一致、warning/error `0`

これは序盤で実使用される技IDの未定義・freeze回帰を検出するsynthetic wild fixtureであり、自然trainer戦を測定したという主張はしない。
"""


def _atomic_write(path: Path, payload: bytes, mode: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        temporary.chmod(mode)
        os.replace(temporary, path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def _publish(
    root: Path,
    stage: bytes,
    artifacts: Mapping[str, bytes],
    metadata: Mapping[str, Any],
    report: str,
) -> None:
    _atomic_write(root / STAGE_ROM, stage, 0o600)
    for logical, payload in sorted(artifacts.items()):
        _atomic_write(root / logical, payload, 0o644)
    write_json(root / ALLOCATION_REPORT, metadata["allocation"])
    write_json(root / STAGE_METADATA, metadata)
    _atomic_write(root / REPORT, report.encode("utf-8"), 0o644)


def _summary_counts(model: Mapping[str, Any]) -> Mapping[str, Any]:
    summaries = model.get("summary")
    if not isinstance(summaries, Mapping):
        raise MoveStageError("move model summaries are missing")
    result = dict(summaries)
    moves = model.get("moves")
    if not isinstance(moves, list):
        raise MoveStageError("move model rows are missing")
    result["exact_match_count"] = sum(
        row.get("classification") in {"VEGA_CFRU_CANONICAL", "VEGA_COMPAT_DUPLICATE"}
        for row in moves[:512]
    )
    result["exact_match_identity_count"] = int(result["mapped_cfru_count"])
    return result


def build_moves(root: Path) -> dict[str, Any]:
    config = _read_config(root)
    try:
        check_harness(root, root / "config/project.toml")
    except HarnessBuildError as error:
        raise MoveStageError(f"T03 harness input is stale: {error}") from error
    stage03_path = root / STAGE03_ROM
    stage03 = stage03_path.read_bytes()
    stage03_sha = _sha256_bytes(stage03)
    stage03_metadata = _read_json_object(root / STAGE03_METADATA, "T03 metadata")
    if stage03_metadata.get("outputs", {}).get("rom", {}).get("sha256") != stage03_sha:
        raise MoveStageError("T03 ROM/metadata cross-link failed")
    vega_path = root / str(config["vega"]["rom_path"])
    if (
        vega_path.is_symlink()
        or not vega_path.is_file()
        or vega_path.stat().st_size != int(config["vega"]["rom_size"])
        or sha256_file(vega_path) != str(config["vega"]["rom_sha256"])
    ):
        raise MoveStageError("fixed Vega reference identity mismatch")

    first_model, first_artifacts = _generated(root, config)
    second_model, second_artifacts = _generated(root, config)
    if first_model != second_model or first_artifacts != second_artifacts:
        raise MoveStageError("two consecutive move model/artifact generations differ")
    bridge = first_artifacts["generated/engine/moves/vega_bridge.bin"]
    stage_first, repoints, table_layout = build_stage_bytes(stage03, bridge, config)
    stage_second, repoints_second, table_layout_second = build_stage_bytes(stage03, bridge, config)
    if (
        stage_first != stage_second
        or repoints != repoints_second
        or table_layout != table_layout_second
    ):
        raise MoveStageError("two consecutive move ROM builds differ")
    allocation = _allocation(root, bridge, config)
    allocation_second = _allocation(root, bridge, config)
    if allocation != allocation_second:
        raise MoveStageError("two consecutive allocation reports differ")
    fingerprint_inputs = _fingerprint_inputs(root, stage03_sha, config)
    fingerprint = stable_digest(fingerprint_inputs)
    build_root = root / "build"
    build_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".t04-moves-", dir=build_root) as raw:
        work = Path(raw)
        candidate = work / "04_moves.gba"
        candidate.write_bytes(stage_first)
        candidate.chmod(0o600)
        reference_result, candidate_result, toolchain = _compile_and_run_smoke(
            root, work, vega_path, candidate
        )

    counts_by_table = {
        name: sum(1 for row in repoints if row["table"] == name) for name in TABLE_ORDER
    }
    metadata: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": "PASS",
        "task": TASK_ID,
        "fingerprint": fingerprint,
        "fingerprint_inputs": fingerprint_inputs,
        "input": {
            "stage03": {"size": len(stage03), "sha256": stage03_sha},
            "vega_reference": {
                "size": vega_path.stat().st_size,
                "sha256": sha256_file(vega_path),
            },
        },
        "output": {"size": len(stage_first), "sha256": _sha256_bytes(stage_first)},
        "model_summaries": dict(_summary_counts(first_model)),
        "generated_artifacts": _artifact_records(first_artifacts),
        "table_layout": table_layout,
        "repoints": {
            "total": len(repoints),
            "counts_by_table": counts_by_table,
            "rows": repoints,
        },
        "allocation": allocation,
        "repeatability": {
            "runs": 2,
            "model_identical": True,
            "artifacts_identical": True,
            "rom_identical": True,
            "allocation_identical": True,
        },
        "layout": {
            "rom_size": len(stage_first),
            "bridge_start": int(str(config["bridge"]["start"]), 0),
            "bridge_end_exclusive": int(str(config["bridge"]["start"]), 0) + len(bridge),
            "bridge_size": len(bridge),
            "repoint_count": len(repoints),
            "declared_write_span_count": len(repoints) + 1,
            "changed_outside_declared_writes": 0,
        },
        "smoke": {"reference": reference_result, "candidate": candidate_result},
        "toolchain": toolchain,
        "artifacts_written": _artifacts_written(first_artifacts),
    }
    report = _render_report(metadata)
    _publish(root, stage_first, first_artifacts, metadata, report)
    return metadata


def check_moves(root: Path) -> dict[str, Any]:
    config = _read_config(root)
    try:
        check_harness(root, root / "config/project.toml")
    except HarnessBuildError as error:
        raise MoveStageError(f"T03 harness input is stale: {error}") from error
    metadata = _read_json_object(root / STAGE_METADATA, "T04 stage metadata")
    if (
        metadata.get("schema_version") != 1
        or metadata.get("status") != "PASS"
        or metadata.get("task") != TASK_ID
    ):
        raise MoveStageError("published T04 metadata is not PASS schema 1")
    stage03 = (root / STAGE03_ROM).read_bytes()
    stage03_sha = _sha256_bytes(stage03)
    current_inputs = _fingerprint_inputs(root, stage03_sha, config)
    if metadata.get("fingerprint_inputs") != current_inputs:
        raise MoveStageError("published T04 fingerprint inputs are stale")
    if metadata.get("fingerprint") != stable_digest(current_inputs):
        raise MoveStageError("published T04 fingerprint is stale")
    vega_path = root / str(config["vega"]["rom_path"])
    expected_input = {
        "stage03": {"size": len(stage03), "sha256": stage03_sha},
        "vega_reference": {
            "size": vega_path.stat().st_size,
            "sha256": sha256_file(vega_path),
        },
    }
    if metadata.get("input") != expected_input:
        raise MoveStageError("published T04 input identity is stale")
    model, artifacts = _generated(root, config)
    expected_records = _artifact_records(artifacts)
    if metadata.get("generated_artifacts") != expected_records:
        raise MoveStageError("published generated artifact records are stale")
    for logical, payload in sorted(artifacts.items()):
        path = root / logical
        if path.is_symlink() or not path.is_file() or path.read_bytes() != payload:
            raise MoveStageError(f"published generated artifact is stale: {logical}")
    bridge = artifacts["generated/engine/moves/vega_bridge.bin"]
    expected_stage, repoints, table_layout = build_stage_bytes(stage03, bridge, config)
    stage_path = root / STAGE_ROM
    if stage_path.is_symlink() or not stage_path.is_file():
        raise MoveStageError("published T04 ROM is missing/non-regular")
    published_stage = stage_path.read_bytes()
    if published_stage != expected_stage:
        raise MoveStageError("published T04 ROM differs from deterministic reconstruction")
    if metadata.get("output") != {
        "size": len(expected_stage),
        "sha256": _sha256_bytes(expected_stage),
    }:
        raise MoveStageError("published T04 output identity is stale")
    allocation = _allocation(root, bridge, config)
    if metadata.get("allocation") != allocation:
        raise MoveStageError("published T04 allocation is stale")
    if _read_json_object(root / ALLOCATION_REPORT, "T04 allocation file") != allocation:
        raise MoveStageError("published T04 allocation file is stale")
    counts_by_table = {
        name: sum(1 for row in repoints if row["table"] == name) for name in TABLE_ORDER
    }
    if metadata.get("repoints") != {
        "total": len(repoints),
        "counts_by_table": counts_by_table,
        "rows": repoints,
    }:
        raise MoveStageError("published T04 repoint metadata is stale")
    if metadata.get("table_layout") != table_layout:
        raise MoveStageError("published T04 table layout is stale")
    if metadata.get("model_summaries") != dict(_summary_counts(model)):
        raise MoveStageError("published T04 model summaries are stale")
    expected_repeatability = {
        "runs": 2,
        "model_identical": True,
        "artifacts_identical": True,
        "rom_identical": True,
        "allocation_identical": True,
    }
    if metadata.get("repeatability") != expected_repeatability:
        raise MoveStageError("published T04 repeatability contract is stale")
    expected_layout = {
        "rom_size": len(expected_stage),
        "bridge_start": int(str(config["bridge"]["start"]), 0),
        "bridge_end_exclusive": int(str(config["bridge"]["start"]), 0) + len(bridge),
        "bridge_size": len(bridge),
        "repoint_count": len(repoints),
        "declared_write_span_count": len(repoints) + 1,
        "changed_outside_declared_writes": 0,
    }
    if metadata.get("layout") != expected_layout:
        raise MoveStageError("published T04 ROM layout contract is stale")
    if metadata.get("artifacts_written") != _artifacts_written(artifacts):
        raise MoveStageError("published T04 artifact list is stale")
    saved_toolchain = metadata.get("toolchain")
    if not isinstance(saved_toolchain, Mapping):
        raise MoveStageError("published T04 toolchain provenance is missing")
    if saved_toolchain != _compile_runner_identity(root):
        raise MoveStageError("published T04 toolchain/runner provenance is stale")
    smoke = metadata.get("smoke")
    if not isinstance(smoke, Mapping):
        raise MoveStageError("published T04 smoke is missing")
    reference_sha = str(config["vega"]["rom_sha256"])
    _validate_smoke(smoke.get("reference"), reference_sha)
    _validate_smoke(smoke.get("candidate"), _sha256_bytes(expected_stage))
    def comparable(payload: Mapping[str, Any]) -> dict[str, Any]:
        value = json.loads(json.dumps(payload))
        value.pop("rom_sha256", None)
        for phase in ("before", "after"):
            value[phase].pop("ewram_iwram_fnv1a64", None)
            value[phase].pop("pc", None)
        for battler in value["after"]["battlers"]:
            battler.pop("hp", None)
        return value

    left = comparable(smoke["reference"])
    right = comparable(smoke["candidate"])
    if left != right:
        raise MoveStageError("published smoke reference/candidate observations differ")
    expected_report = _render_report(metadata)
    report_path = root / REPORT
    if not report_path.is_file() or report_path.read_text(encoding="utf-8") != expected_report:
        raise MoveStageError("published T04 report is stale")
    return {
        "status": "PASS",
        "fingerprint": metadata["fingerprint"],
        "rom_sha256": metadata["output"]["sha256"],
        "move_count": metadata["model_summaries"]["move_count"],
        "repoint_count": len(repoints),
        "smoke_status": smoke["candidate"]["status"],
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("build", "check"))
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "build":
            result = build_moves(ROOT)
            summary = {
                "status": result["status"],
                "fingerprint": result["fingerprint"],
                "rom_sha256": result["output"]["sha256"],
                "move_count": result["model_summaries"]["move_count"],
                "repoint_count": result["repoints"]["total"],
                "smoke_status": result["smoke"]["candidate"]["status"],
            }
        else:
            summary = check_moves(ROOT)
    except (
        MoveStageError,
        MovePortError,
        HarnessBuildError,
        OSError,
        ValueError,
        KeyError,
        TypeError,
    ) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
