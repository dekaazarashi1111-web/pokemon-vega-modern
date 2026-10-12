#!/usr/bin/env python3
"""Stage75: Own Tempo Rockruffを内部条件フォームとして実ROMへ追加する。"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import zlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.modernization_p03_stage73_runtime import compile_route_model
from tools.modernization_p03_stage74_supply import compile_supply_routes
from tools.modernization_p04_species_runtime import SPECIES_TABLE_KEYS
from tools.release.bps import apply_bps, create_bps
from tools.rom_allocator import GBA_ROM_BASE, build_allocation_report_from_csv


TASK = "USER-MODERNIZATION-ROCKRUFF-OWN-TEMPO-STAGE75"
STAGE = 75
ROM_SIZE = 32 * 1024 * 1024
CONFIG_PATH = Path("config/modernization_rockruff_own_tempo_stage75.json")
PROVISIONAL_LOAD_ADDRESS = 0x0954B030
OLD_SPECIES_COUNT = 1670
NEW_SPECIES_COUNT = 1671
NORMAL_ROCKRUFF = 1142
LYCANROC_DUSK = 1263
OWN_TEMPO_ROCKRUFF = 1670
OWN_TEMPO_ABILITY = 20
EVOLUTION_STRIDE = 128
EVOLUTION_ROW = struct.pack("<HHHH", 28, 25, LYCANROC_DUSK, 0x1114)
EGG_MOVES = (37, 283, 745, 541)
EXPECTED_ROCKRUFF_ROUTE_SET_SHA256 = "791ce4be04329952b52bb4b9d16e8ba12ab0cfd079b236e66976ad8a375cd0d8"
EXPECTED_TOUCHED_ALLOCATION_SEQUENCES = (25, 27, 33, 34, 44, 48, 61, 62, 66)
EXPECTED_EXISTING_CARRY_MOVES = (
    14, 156, 157, 164, 182, 201, 203, 214, 269, 270, 334,
    405, 407, 495, 520, 545, 550, 675, 688, 1037, 1040,
)
EXPECTED_ARCHIVE_CARRY_MOVES = (
    34, 36, 38, 46, 91, 184, 189, 204, 242, 263, 283,
    304, 317, 384, 395, 422, 424,
)


class Stage75Error(RuntimeError):
    """Stage75の固定入力・ABI・生成結果が一致しない。"""


EXPECTED_HOOKS = (
    {
        "name": "GetEggSpecies", "address": "0x08044F34", "width": 8,
        "parent_hex": "f0b5474680b40004", "target": "Stage75_GetEggSpecies",
        "continuation_thumb": "0x08044F3D",
    },
    {
        "name": "GetEggMoves", "address": "0x080451EC", "width": 8,
        "parent_hex": "f0b5474680b48846", "target": "Stage75_GetEggMoves",
        "continuation_thumb": "0x080451F5",
    },
    {
        "name": "TryGenerateWildMon", "address": "0x080826D8", "width": 8,
        "parent_hex": "004b1847bd414109", "target": "Stage75_TryGenerateWildMonAdapter",
    },
    {
        "name": "GetMoveRelearnerMoves", "address": "0x091141D4", "width": 8,
        "parent_hex": "004b1847a9a05309", "target": "Stage75_GetMoveRelearnerMoves",
    },
    {
        "name": "BuildLearnableMoveset", "address": "0x091143B8", "width": 8,
        "parent_hex": "004b184715a15309", "target": "Stage75_BuildLearnableMoveset",
    },
)
EXPECTED_ITEM_SCRIPT_POINTER = {
    "address": "0x092D05B4", "parent_hex": "34a65309", "target": "Stage75_ItemScript",
}
EXPECTED_STAGE73_ABI = {
    "Stage73_SharedIndex": "0x09534C9E",
    "Stage73_SharedMoves": "0x0953594A",
    "Stage73_ReminderIndex": "0x09538088",
    "Stage73_ReminderMoves": "0x09538D34",
}
EXPECTED_STAGE74_ABI = {
    "Stage74_MachineIndex": "0x0953A89A",
    "Stage74_MachineMoves": "0x0953B546",
    "Stage74_TutorIndex": "0x09548294",
    "Stage74_TutorMoves": "0x09548F40",
    "Stage74_PreservationIndex": "0x09549222",
    "Stage74_PreservationMoves": "0x09549ECE",
    "Stage74_GetMoveRelearnerMoves": "0x0953A0A9",
    "Stage74_BuildLearnableMoveset": "0x0953A115",
    "Stage74_PrepareMachinePages": "0x0953A1D5",
    "Stage74_CommitMachinePage": "0x0953A1FD",
    "Stage74_SelectedMachinePageHasMoves": "0x0953A23D",
    "Stage74_OpenArchiveModeMenu": "0x0953A299",
    "Stage74_OpenMachinePageMenu": "0x0953A2B1",
    "Stage74_TextChooseMon": "0x0953A83C",
    "Stage74_TextNoMoves": "0x0953A850",
    "Stage74_TextEggRejected": "0x0953A864",
    "Stage74_TextArchiveLocked": "0x0953A870",
    "Stage74_TextPageNoMoves": "0x0953A888",
}
EXPECTED_ENGINE_ABI = {
    "GetMonData": {"address": "0x0803F355", "parent_hex": "10b5041c0b1c181c"},
    "SetMonData": {"address": "0x0803FA71", "parent_hex": "10b5031c0c1c201c"},
    "CalculateMonStats": {"address": "0x0803DBE9", "parent_hex": "004908479d930d09"},
    "TryGenerateWildMonParent": {"address": "0x094141BD", "parent_hex": "10b5064b00f00ef8"},
}
EXPECTED_EXISTING_SCRIPTS = {
    "CheckContext": {"address": "0x092CFFB0", "parent_hex": "93200a4b70b50001"},
    "ContextReject": {"address": "0x092D09F8", "parent_hex": "0f0041072d090904"},
    "NormalRemember": {"address": "0x092D07A0", "parent_hex": "2321012d090f0049"},
    "Forget": {"address": "0x092D08FC", "parent_hex": "2321012d090f0055"},
    "Egg": {"address": "0x092D0818", "parent_hex": "2399022d09210d80"},
}


def _fail(message: str) -> None:
    raise Stage75Error(message)


def _require(condition: bool, message: str) -> None:
    if not condition:
        _fail(message)


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _stable_json(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def _integer(value: Any, label: str) -> int:
    if isinstance(value, bool):
        _fail(f"{label}が整数ではありません")
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value, 0)
        except ValueError as exc:
            raise Stage75Error(f"{label}を整数化できません: {value}") from exc
    _fail(f"{label}が整数ではありません")
    raise AssertionError


def _read_json(raw: bytes, label: str) -> Any:
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise Stage75Error(f"{label} JSON不正: {exc}") from exc


def _validate_config(config: Mapping[str, Any]) -> None:
    _require(config.get("task") == TASK and config.get("stage") == STAGE, "Stage75 config identity不一致")
    identity = config.get("identity", {})
    _require(
        identity.get("reference_id") == "scarletviolet:0744.01"
        and identity.get("classification") == "INTERNAL_CONDITIONAL_FORM"
        and identity.get("species_id") == OWN_TEMPO_ROCKRUFF
        and identity.get("normal_species_id") == NORMAL_ROCKRUFF
        and identity.get("dusk_species_id") == LYCANROC_DUSK
        and identity.get("national_dex") == 744
        and identity.get("ability_id") == OWN_TEMPO_ABILITY
        and identity.get("ability_slots") == [20, 20, 20]
        and identity.get("collection_class") == 4
        and identity.get("collection_weight") == 0
        and identity.get("save_layout_changed") is False,
        "Stage75 identity contract不一致",
    )
    _require(config.get("evolution") == {
        "normal_removed_slot": 2,
        "own_tempo_slot": 0,
        "row_u16": [28, 25, LYCANROC_DUSK, 0x1114],
    }, "Stage75 evolution contract不一致")
    p03 = config.get("p03", {})
    _require(
        p03.get("owner_clone_species") == NORMAL_ROCKRUFF
        and p03.get("egg_moves") == list(EGG_MOVES)
        and p03.get("selected_owner_route_counts") == {
            "level_up": 14, "machine": 38, "egg": 4, "shared_egg": 4, "total": 60,
        }
        and p03.get("withheld_carry_paths") == 38
        and p03.get("carry_resolution_counts") == {
            "reference_existing_slot": 21, "reference_stage74_archive": 17,
        }
        and p03.get("route_accounting_delta") == 0
        and p03.get("build_learnable_capacity_u16") == 429,
        "Stage75 P03 contract不一致",
    )
    _require(config.get("breeding") == {
        "get_egg_species_intercepts": [LYCANROC_DUSK, OWN_TEMPO_ROCKRUFF],
        "get_egg_species_result": OWN_TEMPO_ROCKRUFF,
        "all_other_species": "EXACT_PARENT_TRAMPOLINE",
        "get_egg_moves_1670": list(EGG_MOVES),
    }, "Stage75 breeding contract不一致")
    wild = config.get("wild_acquisition", {})
    _require(
        wild.get("policy") == "POST_GENERATION_PERSONALITY_MIXED_LOW_3_BITS_ZERO"
        and wild.get("probability_numerator") == 1
        and wild.get("probability_denominator") == 8
        and wild.get("additional_rng_calls") == 0
        and wild.get("mix") == "x=pid^(pid>>16);x*=0x9E3779B1;x^=x>>16"
        and wild.get("normal_rockruff_retained") is True
        and wild.get("delegate_thumb") == "0x094141BD",
        "Stage75 wild acquisition contract不一致",
    )
    _require(config.get("exclusions") == {
        "side_change_project_move_id": 1063,
        "side_change_materialized": 0,
        "browt_pombon_gecqua_materialized": 0,
        "prohibited_coercions_materialized": 0,
        "full_p03_done": False,
    }, "Stage75 exclusion contract不一致")
    abi = config.get("parent_abi", {})
    _require(tuple(abi.get("hooks", ())) == EXPECTED_HOOKS, "Stage75 exact hook集合不一致")
    _require(abi.get("item_script_pointer") == EXPECTED_ITEM_SCRIPT_POINTER, "Stage75 ItemScript pointer contract不一致")
    runtime_abi = config.get("runtime_abi", {})
    _require(runtime_abi.get("stage73_symbols") == EXPECTED_STAGE73_ABI, "Stage73 ABI config不一致")
    _require(runtime_abi.get("stage74_symbols") == EXPECTED_STAGE74_ABI, "Stage74 ABI config不一致")
    _require(runtime_abi.get("engine_thumb") == EXPECTED_ENGINE_ABI, "engine ABI config不一致")
    _require(runtime_abi.get("existing_scripts") == EXPECTED_EXISTING_SCRIPTS, "existing script ABI config不一致")


def _validate_runtime_abi(
    root: Path,
    parent: bytes,
    stage73_symbols: Mapping[str, Any],
    stage74_symbols: Mapping[str, Any],
) -> None:
    for expected, source, label in (
        (EXPECTED_STAGE73_ABI, stage73_symbols, "Stage73"),
        (EXPECTED_STAGE74_ABI, stage74_symbols, "Stage74"),
    ):
        rows = source.get("symbols", {})
        for name, address_text in expected.items():
            address = int(address_text, 0)
            row = rows.get(name, {})
            field = "thumb_address" if address & 1 else "address"
            _require(row.get(field) == address_text, f"{label} symbol ABI drift: {name}")
    for group, label in (
        (EXPECTED_ENGINE_ABI, "engine"),
        (EXPECTED_EXISTING_SCRIPTS, "existing script"),
    ):
        for name, spec in group.items():
            address = int(spec["address"], 0) & ~1
            expected = bytes.fromhex(spec["parent_hex"])
            _require(_slice(parent, address, len(expected), name) == expected, f"{label} preimage drift: {name}")
    source_dir = root / "overlays/modernization_rockruff_own_tempo_stage75"
    source_text = "\n".join(
        (source_dir / name).read_text(encoding="utf-8")
        for name in (
            "modernization_rockruff_own_tempo_stage75.c",
            "modernization_rockruff_own_tempo_stage75_scripts.S",
        )
    )
    literal_addresses = {int(value, 16) for value in re.findall(r"0x([0-9A-Fa-f]+)", source_text)}
    required_addresses = {
        int(value, 0) for value in (*EXPECTED_STAGE73_ABI.values(), *EXPECTED_STAGE74_ABI.values())
    } | {
        int(spec["address"], 0)
        for spec in (*EXPECTED_ENGINE_ABI.values(), *EXPECTED_EXISTING_SCRIPTS.values())
    }
    _require(required_addresses <= literal_addresses, "Stage75 overlay hardcoded ABI literal不足")


def _pinned(root: Path, spec: Mapping[str, Any], label: str) -> bytes:
    path = root / str(spec["path"])
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise Stage75Error(f"{label}を読めません: {path}: {exc}") from exc
    _require(_sha(raw) == str(spec["sha256"]), f"{label} SHA-256不一致")
    if "size" in spec:
        _require(len(raw) == int(spec["size"]), f"{label} size不一致")
    return raw


def _all_offsets(raw: bytes, needle: bytes) -> list[int]:
    result: list[int] = []
    cursor = 0
    while True:
        cursor = raw.find(needle, cursor)
        if cursor < 0:
            return result
        result.append(cursor)
        cursor += 1


def _slice(rom: bytes, address: int, size: int, label: str) -> bytes:
    offset = address - GBA_ROM_BASE
    _require(0 <= offset <= len(rom) - size, f"{label} ROM範囲外")
    return rom[offset:offset + size]


def _context(rom: bytes, site: int, width: int = 4) -> dict[str, Any]:
    start = max(0, min(site - 8, len(rom) - 20))
    raw = rom[start:start + 20]
    return {
        "site_offset": site,
        "site_address": f"0x{GBA_ROM_BASE + site:08X}",
        "parent_context_start": start,
        "site_offset_in_context": site - start,
        "parent_context_hex": raw.hex(),
        "parent_context_sha256": _sha(raw),
        "width": width,
    }


def _set_sha(values: Sequence[str]) -> str:
    return _sha("\n".join(sorted(values)).encode("utf-8"))


def _run(command: Sequence[str], root: Path, label: str) -> str:
    result = subprocess.run(
        list(command), cwd=root, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    if result.returncode:
        _fail(f"{label}失敗\n{result.stdout}\n{result.stderr}")
    return result.stdout


def _previous_requests(
    allocation: Mapping[str, Any], overrides: Mapping[int, str] | None = None,
) -> list[dict[str, Any]]:
    rows = allocation.get("allocations")
    _require(isinstance(rows, list) and len(rows) == 78, "Stage74 allocation count不一致")
    _require([row.get("sequence") for row in rows] == list(range(78)), "Stage74 allocation sequence不連続")
    overrides = overrides or {}
    requests: list[dict[str, Any]] = []
    for row in rows:
        sequence = int(row["sequence"])
        request = {
            "name": row["name"], "region": row["region"],
            "size": row["size"], "alignment": row["alignment"],
            "owner": row["owner"], "purpose": row["purpose"],
            "content_sha256": overrides.get(sequence, row["content_sha256"]),
        }
        if row.get("placement") == "EXPLICIT":
            request["start"] = row["start"]
        else:
            _require(row.get("placement") == "FIRST_FIT", f"allocation placement不正: {sequence}")
        requests.append(request)
    return requests


def _allocate(
    root: Path,
    config: Mapping[str, Any],
    previous: Mapping[str, Any],
    size: int,
    digest: str,
    overrides: Mapping[int, str] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    requests = _previous_requests(previous, overrides)
    declaration = config["allocation"]
    requests.append({
        "name": declaration["name"], "region": declaration["region"],
        "size": size, "alignment": int(declaration["alignment"]),
        "owner": declaration["owner"], "purpose": declaration["purpose"],
        "content_sha256": digest,
    })
    report = build_allocation_report_from_csv(
        root / str(config["inputs"]["rom_regions"]["path"]), requests
    )
    _require(report.get("summaries", {}).get("overlap_count") == 0, "Stage75 allocator overlap")
    rows = report.get("allocations", [])
    _require(len(rows) == 79 and rows[-1].get("sequence") == 78, "Stage75 allocation sequence不一致")
    row = rows[-1]
    _require(
        row.get("name") == declaration["name"]
        and row.get("placement") == "FIRST_FIT",
        "Stage75 FIRST_FIT allocation不一致",
    )
    return row, report


def _table_rows(
    parent: bytes,
    p04: Mapping[str, Any],
) -> tuple[dict[str, bytes], dict[str, dict[str, Any]]]:
    blobs: dict[str, bytes] = {}
    metadata: dict[str, dict[str, Any]] = {}
    for key in SPECIES_TABLE_KEYS:
        source = p04["tables"][key]
        stride = int(source["stride"])
        old_count = int(source["new_count"])
        expected_old_count = OLD_SPECIES_COUNT - 1 if key == "species_national_dex_runtime" else OLD_SPECIES_COUNT
        new_count = NEW_SPECIES_COUNT - 1 if key == "species_national_dex_runtime" else NEW_SPECIES_COUNT
        _require(old_count == expected_old_count, f"{key}: Stage70 count不一致")
        old_address = int(source["new_address"])
        old_size = old_count * stride
        old_raw = _slice(parent, old_address, old_size, key)
        rows = bytearray(old_raw)
        donor_index = NORMAL_ROCKRUFF - 1 if key == "species_national_dex_runtime" else NORMAL_ROCKRUFF
        donor = old_raw[donor_index * stride:(donor_index + 1) * stride]
        _require(len(donor) == stride, f"{key}: donor row不足")
        if key == "evolution":
            normal = NORMAL_ROCKRUFF * stride
            _require(stride == EVOLUTION_STRIDE, "evolution stride不一致")
            _require(rows[normal + 16:normal + 24] == EVOLUTION_ROW, "1142 Dusk evolution row preimage不一致")
            rows[normal + 16:normal + 24] = bytes(8)
            appended = bytearray(stride)
            appended[:8] = EVOLUTION_ROW
            rows.extend(appended)
        elif key in ("species_front", "species_back"):
            appended = bytearray(donor)
            _require(struct.unpack_from("<H", appended, 4)[0] == 2048, f"{key}: donor sprite size不一致")
            struct.pack_into("<H", appended, 6, OWN_TEMPO_ROCKRUFF)
            rows.extend(appended)
        elif key == "species_palette":
            appended = bytearray(donor)
            struct.pack_into("<H", appended, 4, OWN_TEMPO_ROCKRUFF)
            rows.extend(appended)
        elif key == "species_shiny_palette":
            appended = bytearray(donor)
            struct.pack_into("<H", appended, 4, OWN_TEMPO_ROCKRUFF + 1621)
            rows.extend(appended)
        elif key == "species_base_stats":
            appended = bytearray(donor)
            for offset in (22, 26, 28):
                struct.pack_into("<H", appended, offset, OWN_TEMPO_ABILITY)
            rows.extend(appended)
        elif key == "acquisition_collection_defs":
            rows.extend(struct.pack("<HHBBBB", OWN_TEMPO_ROCKRUFF, 0xFFFF, 0, 0, 4, 0))
        else:
            rows.extend(donor)
        _require(len(rows) == new_count * stride, f"{key}: Stage75 table size不一致")
        label = f"Stage75_Table_{key}"
        blobs[label] = bytes(rows)
        sites = [int(value) for value in source["pointer_consumers"]["site_offsets"]]
        _require(sites == sorted(sites) and len(sites) == int(source["pointer_consumers"]["count"]), f"{key}: consumer pin不一致")
        metadata[key] = {
            "label": label,
            "old_address": old_address,
            "old_file_offset": old_address - GBA_ROM_BASE,
            "old_count": old_count,
            "new_count": new_count,
            "stride": stride,
            "old_size": old_size,
            "new_size": len(rows),
            "old_sha256": _sha(old_raw),
            "new_unlinked_sha256": _sha(bytes(rows)),
            "pointer_sites": sites,
            "pointer_site_set_sha256": _sha(_stable_json(sites)),
        }
    blobs["Stage75_OwnTempoEggMoves"] = struct.pack("<4H", *EGG_MOVES)
    return blobs, metadata


@dataclass(frozen=True)
class CompiledPayload:
    code: bytes
    symbols: dict[str, int]
    symbol_types: dict[str, str]
    compiler: str


def _compile_payload(root: Path, load_address: int, blobs: Mapping[str, bytes]) -> CompiledPayload:
    gcc = shutil.which("arm-none-eabi-gcc")
    objcopy = shutil.which("arm-none-eabi-objcopy")
    nm = shutil.which("arm-none-eabi-nm")
    _require(bool(gcc and objcopy and nm), "arm-none-eabi toolchainがPATHにありません")
    source_dir = root / "overlays/modernization_rockruff_own_tempo_stage75"
    c_source = source_dir / "modernization_rockruff_own_tempo_stage75.c"
    scripts_source = source_dir / "modernization_rockruff_own_tempo_stage75_scripts.S"
    linker = source_dir / "modernization_rockruff_own_tempo_stage75.ld"
    for path in (c_source, scripts_source, linker):
        _require(path.is_file() and not path.is_symlink(), f"Stage75 overlay欠落: {path}")
    common = ["-mthumb", "-mcpu=arm7tdmi", "-mthumb-interwork"]
    with tempfile.TemporaryDirectory(prefix="stage75-rockruff-") as temporary:
        work = Path(temporary)
        table_asm = work / "tables.S"
        lines = [
            ".syntax unified", ".cpu arm7tdmi", ".thumb",
            '.section .rodata.Stage75GeneratedTables,"a",%progbits', ".balign 4",
        ]
        for index, (name, raw) in enumerate(blobs.items()):
            blob_path = work / f"blob-{index}.bin"
            blob_path.write_bytes(raw)
            lines.extend([
                ".balign 4", f".global {name}", f".type {name}, %object", f"{name}:",
                f'.incbin "{blob_path}"', f".size {name}, .-{name}",
            ])
        lines.append('.section .note.GNU-stack,"",%progbits')
        table_asm.write_text("\n".join(lines) + "\n", encoding="utf-8")
        c_obj, scripts_obj, tables_obj = work / "runtime.o", work / "scripts.o", work / "tables.o"
        elf, binary = work / "runtime.elf", work / "runtime.bin"
        _run([
            str(gcc), *common, "-Os", "-std=c11", "-ffreestanding", "-fno-common",
            "-ffunction-sections", "-fdata-sections", "-Wall", "-Wextra", "-Werror",
            "-Wconversion", "-Wshadow", "-c", str(c_source), "-o", str(c_obj),
        ], root, "Stage75 C compile")
        _run([str(gcc), *common, "-c", str(scripts_source), "-o", str(scripts_obj)], root, "Stage75 script compile")
        _run([str(gcc), *common, "-c", str(table_asm), "-o", str(tables_obj)], root, "Stage75 table compile")
        _run([
            str(gcc), "-nostdlib", *common,
            f"-Wl,--defsym=STAGE75_LOAD_ADDRESS=0x{load_address:08X}",
            f"-Wl,-T,{linker}", str(c_obj), str(scripts_obj), str(tables_obj),
            "-lgcc", "-o", str(elf),
        ], root, "Stage75 link")
        _run([str(objcopy), "-O", "binary", str(elf), str(binary)], root, "Stage75 objcopy")
        symbols: dict[str, int] = {}
        symbol_types: dict[str, str] = {}
        for line in _run([str(nm), "-n", str(elf)], root, "Stage75 nm").splitlines():
            fields = line.split()
            if len(fields) == 3 and re.fullmatch(r"[0-9a-fA-F]+", fields[0]):
                symbols[fields[2]] = int(fields[0], 16)
                symbol_types[fields[2]] = fields[1]
        code = binary.read_bytes()
    required = {
        "Stage75_RuntimeProbe", "Stage75_GetEggSpecies", "Stage75_GetEggMoves",
        "Stage75_OriginalGetEggSpecies", "Stage75_OriginalGetEggMoves",
        "Stage75_TryGenerateWildMonAdapter", "Stage75_GetMoveRelearnerMoves",
        "Stage75_BuildLearnableMoveset", "Stage75_PrepareMachinePages",
        "Stage75_SelectedMachinePageHasMoves", "Stage75_ItemScript",
        "Stage75_FinishScript", *blobs,
    }
    _require(not (required - set(symbols)), f"Stage75 symbols不足: {sorted(required - set(symbols))}")
    _require(symbols["Stage75_RuntimeProbe"] == load_address, "Stage75 entry/load address不一致")
    _require(560000 < len(code) < 700000, f"Stage75 payload size不正: {len(code)}")
    return CompiledPayload(
        code=code, symbols=symbols, symbol_types=symbol_types,
        compiler=_run([str(gcc), "--version"], root, "gcc version").splitlines()[0],
    )


def _veneer(target: int) -> bytes:
    return struct.pack("<HHI", 0x4B00, 0x4718, target | 1)


def _changed_spans(before: bytes, after: bytes) -> list[dict[str, int]]:
    spans: list[dict[str, int]] = []
    start: int | None = None
    for offset, (left, right) in enumerate(zip(before, after, strict=True)):
        if left != right and start is None:
            start = offset
        elif left == right and start is not None:
            spans.append({"start": start, "end_exclusive": offset, "size": offset - start})
            start = None
    if start is not None:
        spans.append({"start": start, "end_exclusive": len(before), "size": len(before) - start})
    return spans


def _egg_species_host(species: int) -> int | None:
    if species in (LYCANROC_DUSK, OWN_TEMPO_ROCKRUFF):
        return OWN_TEMPO_ROCKRUFF
    return None


def _dusk_evolution_host(species: int, level: int, hour: int) -> int | None:
    method, required_level, target, time_range = struct.unpack("<HHHH", EVOLUTION_ROW)
    start_hour = time_range >> 8
    end_hour = time_range & 0xFF
    if (
        species == OWN_TEMPO_ROCKRUFF
        and method == 28
        and level >= required_level
        and start_hour <= hour < end_hour
    ):
        return target
    return None


def _wild_species_host(result: int, species: int, personality: int) -> int:
    if not result or species != NORMAL_ROCKRUFF:
        return species
    mixed = (personality ^ (personality >> 16)) & 0xFFFFFFFF
    mixed = mixed * 0x9E3779B1 & 0xFFFFFFFF
    mixed ^= mixed >> 16
    return OWN_TEMPO_ROCKRUFF if mixed & 7 == 0 else NORMAL_ROCKRUFF


def _accounting_chain(
    parent_metadata: Mapping[str, Any],
    stage74_audit: Mapping[str, Any],
) -> dict[str, int]:
    parent = parent_metadata.get("accounting", {})
    selected = int(parent.get("cumulative_accounted_routes", -1))
    materialized = int(parent.get("cumulative_runtime_materialized_routes", -1))
    direct = int(parent.get("stage74_direct_supply_materialized_routes", -1))
    _require(
        selected == 118369
        and materialized == 83162
        and direct == 26648
        and int(parent.get("selected_direct_supply_routes_remaining", -1)) == 0,
        "Stage74 accounting chain不一致",
    )
    preservation = (
        stage74_audit.get("build_learnable_preservation", {})
        .get("capacity", {})
        .get("preservation_only", {})
    )
    _require(
        int(preservation.get("selected_route_count_checked", -1)) == selected
        and int(preservation.get("route_accounting_added", -1)) == 0
        and int(preservation.get("ui_supply_routes_added", -1)) == 0,
        "Stage74 preservation accounting chain不一致",
    )
    _require(
        int(stage74_audit.get("direct_supply", {}).get("route_count", -1)) == direct,
        "Stage74 direct supply accounting chain不一致",
    )
    return {
        "selected_routes_before": selected,
        "selected_routes_after": selected,
        "materialized_routes_before": materialized,
        "materialized_routes_after": materialized,
        "route_accounting_delta": 0,
    }


def _p03_audit(
    root: Path,
    stage73_config: Mapping[str, Any],
    stage74_config: Mapping[str, Any],
    stage74_audit: Mapping[str, Any],
    compiled_index: Mapping[str, Any],
    accounting: Mapping[str, int],
) -> dict[str, Any]:
    model73 = compile_route_model(root, stage73_config)
    model74 = compile_supply_routes(root, stage74_config)
    exclusions = stage74_audit.get("exclusions", {})
    _require(
        exclusions.get("side_change_project_move_id") == 1063
        and exclusions.get("side_change_materialized") == 0
        and exclusions.get("browt_pombon_gecqua_materialized") == 0
        and exclusions.get("prohibited_coercions_materialized") == 0
        and stage74_audit.get("full_p03_done") is False,
        "Stage74 exclusion boundary不一致",
    )
    _require(model73.direct_egg_rows.get(NORMAL_ROCKRUFF) == EGG_MOVES, "Rockruff direct egg row不一致")
    _require(model73.shared_rows.get(NORMAL_ROCKRUFF) == EGG_MOVES, "Rockruff shared egg row不一致")
    _require(model73.reminder_rows.get(NORMAL_ROCKRUFF, ()) == (), "Rockruff reminder row不一致")
    machine = model74.machine_rows.get(NORMAL_ROCKRUFF, ())
    tutor = model74.tutor_rows.get(NORMAL_ROCKRUFF, ())
    _require(len(machine) == 17 and not tutor, "Rockruff Stage74 archive row不一致")
    fallback = model74.route_audit["upstream_carry_form_dependency"]["target_direct_equivalent_fallbacks"]
    _require(len(fallback) == 38, "Own Tempo carry fallback count不一致")
    _require(all(
        row.get("consumer") == "pre_evolution_carry"
        and row.get("family") == "machine"
        and row.get("missing_reference") == "scarletviolet:0744.01"
        and int(row.get("target_species", -1)) == LYCANROC_DUSK
        and row.get("fallback") in ("TARGET_EXISTING_SLOT", "TARGET_STAGE74_ARCHIVE")
        for row in fallback
    ), "Own Tempo carry fallback semantic不一致")
    existing = sorted(int(row["move"]) for row in fallback if row["fallback"] == "TARGET_EXISTING_SLOT")
    archive = sorted(int(row["move"]) for row in fallback if row["fallback"] == "TARGET_STAGE74_ARCHIVE")
    _require(
        tuple(existing) == EXPECTED_EXISTING_CARRY_MOVES
        and tuple(archive) == EXPECTED_ARCHIVE_CARRY_MOVES
        and tuple(archive) == tuple(sorted(machine)),
        "Own Tempo carry 21/17 exact partition不一致",
    )
    records = [row for row in compiled_index["records"] if row.get("reference_id") == "scarletviolet:0744.00"]
    _require(
        len(records) == 1
        and records[0]["route_count"] == 60
        and records[0]["selected_route_count"] == 60
        and records[0]["route_id_set_sha256"] == EXPECTED_ROCKRUFF_ROUTE_SET_SHA256
        and records[0]["selected_route_id_set_sha256"] == EXPECTED_ROCKRUFF_ROUTE_SET_SHA256
        and records[0]["selected_consumer_counts"] == {
            "egg": 4, "level_up": 14, "machine": 38, "shared_egg": 4,
        },
        "Rockruff source owner 60-route exact contract不一致",
    )
    _require(stage74_audit["upstream_carry_form_dependency"]["reference_owner_missing_paths"] == 38, "Stage74 withheld boundary不一致")
    moves = existing + archive
    return {
        "schema_version": 1,
        "task": TASK,
        "stage": STAGE,
        "status": "PASS_OWN_TEMPO_OWNER_RESOLVED",
        "identity_mapping": {"reference_id": "scarletviolet:0744.01", "species_id": OWN_TEMPO_ROCKRUFF},
        "source_route_clone": {
            "source_reference_id": "scarletviolet:0744.00",
            "target_reference_id": "scarletviolet:0744.01",
            "route_count": 60,
            "route_id_set_sha256": EXPECTED_ROCKRUFF_ROUTE_SET_SHA256,
            "policy": "EXACT_LEARNSET_CLONE_WITH_DISTINCT_INTERNAL_SPECIES_OWNER",
        },
        "owner_clone": {
            "donor_species": NORMAL_ROCKRUFF,
            "route_counts": {"level_up": 14, "machine": 38, "egg": 4, "shared_egg": 4, "total": 60},
            "egg_moves": list(EGG_MOVES), "shared_egg_moves": list(EGG_MOVES),
            "stage74_archive_moves": list(machine), "tutor_moves": [],
        },
        "pre_evolution_carry": {
            "target_species": LYCANROC_DUSK,
            "reference_owner": OWN_TEMPO_ROCKRUFF,
            "path_count": 38,
            "missing_owner_path_count": 0,
            "resolution_counts": {"reference_existing_slot": 21, "reference_stage74_archive": 17},
            "existing_slot_moves": existing,
            "stage74_archive_moves": archive,
            "move_set_sha256": _set_sha([str(move) for move in moves]),
            "direct_conversion": "FORBIDDEN",
        },
        "accounting": {
            **accounting,
            "owner_identity_support_routes": 60,
            "reason": "38 carry routes were already accounted on target 1263; Stage75 resolves their owner identity without duplicating routes",
        },
        "exclusions": {
            "side_change_project_move_id": 1063,
            "side_change_materialized": 0,
            "browt_pombon_gecqua_materialized": 0,
            "prohibited_coercions_materialized": 0,
            "full_p03_done": False,
        },
    }


def build_artifacts(root: Path) -> dict[str, bytes]:
    root = root.resolve()
    config_raw = (root / CONFIG_PATH).read_bytes()
    config = _read_json(config_raw, "Stage75 config")
    _validate_config(config)
    inputs = config["inputs"]
    parent = _pinned(root, inputs["rom"], "Stage74 ROM")
    _require(len(parent) == ROM_SIZE, "Stage74 ROM size不一致")
    parent_metadata_raw = _pinned(root, inputs["metadata"], "Stage74 metadata")
    parent_metadata = _read_json(parent_metadata_raw, "Stage74 metadata")
    _require(parent_metadata.get("stage") == 74 and parent_metadata.get("output", {}).get("sha256") == _sha(parent), "Stage74 metadata→ROM不一致")
    previous_raw = _pinned(root, inputs["allocation"], "Stage74 allocation")
    previous = _read_json(previous_raw, "Stage74 allocation")
    p04 = _read_json(_pinned(root, inputs["p04_contract"], "P04 contract"), "P04 contract")
    p04_config = _read_json(_pinned(root, inputs["p04_config"], "P04 config"), "P04 config")
    index = _read_json(_pinned(root, inputs["p03_index"], "P03 index"), "P03 index")
    stage73_config = _read_json(_pinned(root, inputs["stage73_config"], "Stage73 config"), "Stage73 config")
    stage74_config = _read_json(_pinned(root, inputs["stage74_config"], "Stage74 config"), "Stage74 config")
    stage74_route = _read_json(_pinned(root, inputs["stage74_route_audit"], "Stage74 route audit"), "Stage74 route audit")
    stage73_symbols = _read_json(_pinned(root, inputs["stage73_symbols"], "Stage73 symbols"), "Stage73 symbols")
    stage74_symbols = _read_json(_pinned(root, inputs["stage74_symbols"], "Stage74 symbols"), "Stage74 symbols")
    _pinned(root, inputs["rom_regions"], "ROM regions")
    ability_raw = _pinned(root, inputs["ability_manifest"], "Ability manifest")
    ability_rows = list(csv.DictReader(ability_raw.decode("utf-8-sig").splitlines()))
    own_rows = [row for row in ability_rows if int(row["id"]) == OWN_TEMPO_ABILITY]
    _require(len(own_rows) == 1 and own_rows[0]["ability_key"] == "ABILITY_KEY_OWNTEMPO", "Own Tempo Ability ID不一致")
    _validate_runtime_abi(root, parent, stage73_symbols, stage74_symbols)

    accounting = _accounting_chain(parent_metadata, stage74_route)
    route_audit = _p03_audit(
        root, stage73_config, stage74_config, stage74_route, index, accounting
    )
    blobs, table_plan = _table_rows(parent, p04)
    provisional = _compile_payload(root, PROVISIONAL_LOAD_ADDRESS, blobs)
    allocation, _ = _allocate(root, config, previous, len(provisional.code), "0" * 64)
    load_address = GBA_ROM_BASE + int(allocation["start"])
    _require(load_address == PROVISIONAL_LOAD_ADDRESS, f"Stage75 expected FIRST_FIT drift: 0x{load_address:08X}")
    compiled = _compile_payload(root, load_address, blobs)
    _require(len(compiled.code) == len(provisional.code), "Stage75 link addressでsize変化")
    payload = compiled.code

    output = bytearray(parent)
    allowed = bytearray(ROM_SIZE)
    writes: list[dict[str, Any]] = []

    def patch(offset: int, raw: bytes, label: str, expected: bytes) -> None:
        _require(0 <= offset <= ROM_SIZE - len(raw), f"{label}: patch範囲外")
        _require(parent[offset:offset + len(raw)] == expected, f"{label}: parent preimage不一致")
        _require(not any(allowed[offset:offset + len(raw)]), f"{label}: allowlist overlap")
        output[offset:offset + len(raw)] = raw
        allowed[offset:offset + len(raw)] = b"\x01" * len(raw)
        writes.append({
            "label": label, "start": offset, "end_exclusive": offset + len(raw),
            "size": len(raw), "parent_sha256": _sha(expected), "output_sha256": _sha(raw),
        })

    payload_start = int(allocation["start"])
    _require(parent[payload_start:payload_start + len(payload)] == b"\xFF" * len(payload), "Stage75 allocation preimage非FF")
    patch(payload_start, payload, "stage75_payload", b"\xFF" * len(payload))

    tables_meta: dict[str, Any] = {}
    for key in SPECIES_TABLE_KEYS:
        plan = table_plan[key]
        label = str(plan["label"])
        new_address = compiled.symbols[label]
        sites = list(plan["pointer_sites"])
        observed = _all_offsets(parent, struct.pack("<I", int(plan["old_address"])))
        _require(observed == sites, f"{key}: Stage74 pointer consumer集合drift")
        pointer_rows = []
        for site in sites:
            old = struct.pack("<I", int(plan["old_address"]))
            patch(site, struct.pack("<I", new_address), f"table_pointer:{key}", old)
            pointer_rows.append(_context(parent, site))
        new_offset = new_address - GBA_ROM_BASE
        new_raw = bytes(output[new_offset:new_offset + int(plan["new_size"])])
        _require(_sha(new_raw) == plan["new_unlinked_sha256"], f"{key}: linked table bytes不一致")
        tables_meta[key] = {
            **{field: value for field, value in plan.items() if field not in {"label", "pointer_sites", "new_unlinked_sha256"}},
            "label": label, "new_address": new_address, "new_file_offset": new_offset,
            "new_sha256": _sha(new_raw), "pointer_consumer_count": len(sites),
            "pointer_consumers": pointer_rows,
        }

    count_rows = []
    for spec in p04_config["count_consumers"]["sites"]:
        site, width = int(spec["site"]), int(spec["width"])
        old = int(spec["new"])
        new = NEW_SPECIES_COUNT if old == OLD_SPECIES_COUNT else OWN_TEMPO_ROCKRUFF
        _require(old in (OLD_SPECIES_COUNT, OLD_SPECIES_COUNT - 1), "Species count current literal不正")
        patch(site, new.to_bytes(width, "little"), f"species_count:{spec['owner']}", old.to_bytes(width, "little"))
        count_rows.append({**_context(parent, site, width), "owner": spec["owner"], "old": old, "new": new})
    _require(len(count_rows) == 19, f"Species count consumer total不一致: {len(count_rows)}")

    hook_rows = []
    for hook in config["parent_abi"]["hooks"]:
        address = _integer(hook["address"], "hook address")
        offset = address - GBA_ROM_BASE
        expected = bytes.fromhex(str(hook["parent_hex"]))
        _require(int(hook["width"]) == 8, "Stage75 hook width不一致")
        target = compiled.symbols[str(hook["target"])]
        veneer = _veneer(target)
        patch(offset, veneer, f"hook:{hook['name']}", expected)
        hook_rows.append({
            "name": hook["name"], "site": f"0x{address:08X}", "parent_hex": expected.hex(),
            "target": hook["target"], "target_thumb": f"0x{target | 1:08X}", "veneer_hex": veneer.hex(),
            **({"continuation_thumb": hook["continuation_thumb"]} if "continuation_thumb" in hook else {}),
        })
    item = config["parent_abi"]["item_script_pointer"]
    item_address = _integer(item["address"], "item script pointer")
    item_offset = item_address - GBA_ROM_BASE
    item_target = compiled.symbols[str(item["target"])]
    _require(item_target % 4 == 0, "Stage75 ItemScript alignment不一致")
    patch(item_offset, struct.pack("<I", item_target), "move_memory_item_script_pointer", bytes.fromhex(str(item["parent_hex"])))

    result = bytes(output)
    _require(not any(
        left != right and not allowed[index]
        for index, (left, right) in enumerate(zip(parent, result, strict=True))
    ), "Stage75 allowlist外変更")

    normal_evo = tables_meta["evolution"]["new_file_offset"] + NORMAL_ROCKRUFF * EVOLUTION_STRIDE
    own_evo = tables_meta["evolution"]["new_file_offset"] + OWN_TEMPO_ROCKRUFF * EVOLUTION_STRIDE
    _require(result[normal_evo + 16:normal_evo + 24] == bytes(8), "1142 Dusk row未除去")
    _require(result[own_evo:own_evo + 8] == EVOLUTION_ROW and result[own_evo + 8:own_evo + EVOLUTION_STRIDE] == bytes(EVOLUTION_STRIDE - 8), "1670 evolution row不一致")
    base = tables_meta["species_base_stats"]["new_file_offset"] + OWN_TEMPO_ROCKRUFF * 32
    own_base = result[base:base + 32]
    _require([struct.unpack_from("<H", own_base, value)[0] for value in (22, 26, 28)] == [20, 20, 20], "1670 Own Tempo 3-slot不一致")
    for key in ("species_national_dex", "species_national_dex_runtime"):
        row = tables_meta[key]
        index_value = OWN_TEMPO_ROCKRUFF - 1 if key.endswith("runtime") else OWN_TEMPO_ROCKRUFF
        value = struct.unpack_from("<H", result, row["new_file_offset"] + index_value * 2)[0]
        _require(value == 744, f"{key}: 1670 NatDex不一致")
    for key in ("species_front", "species_back"):
        old = tables_meta[key]["new_file_offset"] + NORMAL_ROCKRUFF * 8
        new = tables_meta[key]["new_file_offset"] + OWN_TEMPO_ROCKRUFF * 8
        _require(result[new:new + 4] == result[old:old + 4], f"{key}: 1142 pointer非共有")
        _require(struct.unpack_from("<HH", result, new + 4) == (2048, OWN_TEMPO_ROCKRUFF), f"{key}: size/tag不一致")
    for key, tag in (("species_palette", OWN_TEMPO_ROCKRUFF), ("species_shiny_palette", OWN_TEMPO_ROCKRUFF + 1621)):
        old = tables_meta[key]["new_file_offset"] + NORMAL_ROCKRUFF * 8
        new = tables_meta[key]["new_file_offset"] + OWN_TEMPO_ROCKRUFF * 8
        _require(result[new:new + 4] == result[old:old + 4], f"{key}: 1142 pointer非共有")
        _require(struct.unpack_from("<HH", result, new + 4) == (tag, 0), f"{key}: tag/pad不一致")
    collection = tables_meta["acquisition_collection_defs"]["new_file_offset"] + OWN_TEMPO_ROCKRUFF * 8
    _require(
        result[collection:collection + 8]
        == struct.pack("<HHBBBB", OWN_TEMPO_ROCKRUFF, 0xFFFF, 0, 0, 4, 0),
        "1670 collection internal-form row不一致",
    )
    egg_results = {str(species): _egg_species_host(species) for species in (1142, 1143, 1227, 1263, 1670)}
    _require(egg_results == {"1142": None, "1143": None, "1227": None, "1263": 1670, "1670": 1670}, f"Rockruff breeding intercept不一致: {egg_results}")

    tmhm_row = tables_meta["species_tmhm"]["new_file_offset"] + OWN_TEMPO_ROCKRUFF * 16
    legacy_machine_count = sum(byte.bit_count() for byte in result[tmhm_row:tmhm_row + 16])
    machine_count = len(route_audit["owner_clone"]["stage74_archive_moves"])
    preservation_index_offset = 0x09549222 - GBA_ROM_BASE
    preservation_begin = struct.unpack_from("<H", parent, preservation_index_offset + NORMAL_ROCKRUFF * 2)[0]
    preservation_end = struct.unpack_from("<H", parent, preservation_index_offset + (NORMAL_ROCKRUFF + 1) * 2)[0]
    own_structural_upper = 40 + 4 + legacy_machine_count + machine_count + (preservation_end - preservation_begin)
    _require(own_structural_upper <= int(config["p03"]["build_learnable_capacity_u16"]), "1670 BuildLearnable capacity overflow")

    changed_offsets = [index for index, (left, right) in enumerate(zip(parent, result, strict=True)) if left != right]
    touched_sequences: dict[int, dict[str, Any]] = {}
    for row in previous["allocations"]:
        start, end = int(row["start"]), int(row["end_exclusive"])
        if any(allowed[start:end]):
            touched_sequences[int(row["sequence"])] = {
                "sequence": int(row["sequence"]), "name": row["name"],
                "parent_declared_sha256": row["content_sha256"],
                "parent_effective_sha256": _sha(parent[start:end]),
                "output_effective_sha256": _sha(result[start:end]),
            }
    overrides = {sequence: row["output_effective_sha256"] for sequence, row in touched_sequences.items()}
    _require(
        tuple(sorted(touched_sequences)) == EXPECTED_TOUCHED_ALLOCATION_SEQUENCES,
        f"inherited allocation mutation集合不一致: {sorted(touched_sequences)}",
    )
    final_allocation, allocation_report = _allocate(root, config, previous, len(payload), _sha(payload), overrides)
    _require(final_allocation["start"] == payload_start, "Stage75 final allocation drift")
    layout_keys = ("sequence", "name", "region", "alignment", "start", "end_exclusive", "size", "owner", "purpose", "placement")
    for before, after in zip(previous["allocations"], allocation_report["allocations"][:78], strict=True):
        _require(all(before.get(key) == after.get(key) for key in layout_keys), f"inherited allocation layout drift: {before['sequence']}")
        expected_hash = overrides.get(int(before["sequence"]), before["content_sha256"])
        _require(after["content_sha256"] == expected_hash, f"inherited allocation hash更新不一致: {before['sequence']}")

    table_pointer_total = sum(row["pointer_consumer_count"] for row in tables_meta.values())
    _require(table_pointer_total == 310, f"24 table pointer consumer total不一致: {table_pointer_total}")
    symbols = {
        "schema_version": 1, "task": TASK, "stage": STAGE,
        "load_address": f"0x{load_address:08X}", "payload_size": len(payload),
        "symbols": {
            name: {
                "address": f"0x{address:08X}",
                **({"thumb_address": f"0x{address | 1:08X}"}
                   if compiled.symbol_types.get(name, "").lower() == "t" else {}),
            }
            for name, address in sorted(compiled.symbols.items()) if name.startswith("Stage75_")
        },
    }
    mutations = [touched_sequences[key] for key in sorted(touched_sequences)]
    audit = {
        "schema_version": 1, "task": TASK, "stage": STAGE, "status": "PASS",
        "parent_sha256": _sha(parent), "output_sha256": _sha(result),
        "output_crc32": f"{zlib.crc32(result) & 0xFFFFFFFF:08X}",
        "payload": {"start": payload_start, "address": f"0x{load_address:08X}", "size": len(payload), "sha256": _sha(payload)},
        "hooks": hook_rows,
        "item_script_pointer": {"site": f"0x{item_address:08X}", "target": f"0x{item_target:08X}"},
        "table_pointer_consumer_count": table_pointer_total,
        "species_count_consumer_count": len(count_rows),
        "allocation_mutations": mutations,
        "changed_byte_count": len(changed_offsets),
        "changed_offsets_sha256": _sha(b"".join(value.to_bytes(4, "little") for value in changed_offsets)),
        "changed_spans": _changed_spans(parent, result),
        "outside_allowlist_count": 0,
        "breeding": {
            "get_egg_species_intercepts": [LYCANROC_DUSK, OWN_TEMPO_ROCKRUFF],
            "get_egg_species_result": OWN_TEMPO_ROCKRUFF,
            "all_other_species": "EXACT_PARENT_TRAMPOLINE",
            "get_egg_moves_1670": list(EGG_MOVES), "rockruff_family_results": egg_results,
        },
        "wild": {**config["wild_acquisition"], "source_species": NORMAL_ROCKRUFF, "target_species": OWN_TEMPO_ROCKRUFF},
        "build_learnable": {
            "caller_capacity_u16": int(config["p03"]["build_learnable_capacity_u16"]),
            "own_tempo_structural_upper_bound": own_structural_upper,
            "legacy_machine_rows": legacy_machine_count,
            "archive_machine_rows": machine_count,
            "preservation_rows": preservation_end - preservation_begin,
        },
        "checks": {
            "all_24_species_tables_relocated": "PASS", "all_310_pointer_consumers_repointed": "PASS",
            "all_19_species_count_consumers_updated": "PASS", "ability_slots_20_20_20": "PASS",
            "normal_dusk_edge_removed": "PASS", "own_dusk_edge_added": "PASS",
            "natdex_744_both_tables": "PASS", "save_layout_unchanged": "PASS",
            "collection_row_internal_form_no_weight": "PASS",
            "all_22_stage73_stage74_runtime_abi_pins": "PASS",
            "engine_and_existing_script_preimages": "PASS",
            "p03_owner_resolved_without_accounting_delta": "PASS", "bps_roundtrip": "PASS",
        },
    }
    metadata = {
        "schema_version": 1, "task": TASK, "stage": STAGE,
        "status": "CHECKPOINT_OWN_TEMPO_ROCKRUFF_RUNTIME_CONNECTED",
        "parent": {"path": inputs["rom"]["path"], "sha256": _sha(parent), "size": len(parent)},
        "output": {"path": config["outputs"]["rom"], "sha256": _sha(result), "size": len(result), "crc32": audit["output_crc32"]},
        "allocation": final_allocation, "allocation_mutations": mutations,
        "payload": audit["payload"], "tables": tables_meta,
        "count_consumers": count_rows, "hooks": hook_rows,
        "identity": config["identity"], "route_audit": route_audit,
        "full_p03_done": False,
        "release_candidate": False,
        "remaining_work": ["STAGE75_FOCUSED_MGBA", "FINAL_CUMULATIVE_MGBA", "OTHER_P02_P05_PENDING_EDGES"],
        "source_evidence": {
            "config_sha256": _sha(config_raw), "parent_metadata_sha256": _sha(parent_metadata_raw),
            "parent_allocation_sha256": _sha(previous_raw), "compiler": compiled.compiler,
        },
    }
    contract = {
        "schema_version": 1, "task": TASK, "stage": STAGE,
        "status": "STAGE75_OWN_TEMPO_INTERNAL_FORM_CONTRACT",
        "identity": config["identity"],
        "table_contract": {
            "old_species_count": OLD_SPECIES_COUNT, "new_species_count": NEW_SPECIES_COUNT,
            "relocated_species_tables": list(SPECIES_TABLE_KEYS),
            "pointer_consumers": table_pointer_total, "count_consumers": len(count_rows),
            "ability_slots": [20, 20, 20], "national_dex": 744,
        },
        "evolution_correction": {
            "normal_species": NORMAL_ROCKRUFF, "removed_slot": 2,
            "own_tempo_species": OWN_TEMPO_ROCKRUFF, "added_slot": 0,
            "row_hex": EVOLUTION_ROW.hex(),
        },
        "acquisition": audit["wild"], "breeding": audit["breeding"],
        "p03": route_audit,
        "exclusions": route_audit["exclusions"],
        "save": {
            "layout_changed": False, "migration_required": False,
            "existing_1142_preserved": True, "existing_1263_preserved": True,
            "new_species_field_width": "existing_u16",
        },
    }
    bps = create_bps(parent, result, metadata=b"Stage74 to Stage75 Own Tempo Rockruff internal form")
    _require(apply_bps(parent, bps) == result, "Stage74→75 BPS roundtrip不一致")
    outputs = config["outputs"]
    metadata_raw = _stable_json(metadata)
    allocation_raw = _stable_json(allocation_report)
    symbols_raw = _stable_json(symbols)
    audit_raw = _stable_json(audit)
    route_raw = _stable_json(route_audit)
    contract_raw = _stable_json(contract)
    checkpoint = {
        "schema_version": 1, "task": TASK, "stage": STAGE,
        "status": "ROM_MATERIALIZED_CHECKPOINT",
        "parent": {
            "path": inputs["rom"]["path"], "size": len(parent), "sha256": _sha(parent),
        },
        "output": {
            "path": outputs["rom"], "size": len(result), "sha256": _sha(result),
            "crc32": audit["output_crc32"],
        },
        "metadata": {
            "path": outputs["metadata"], "size": len(metadata_raw), "sha256": _sha(metadata_raw),
        },
        "allocation": {
            "path": outputs["allocation"], "size": len(allocation_raw), "sha256": _sha(allocation_raw),
            "new_sequence": 78, "inherited_layout_changes": 0,
            "mutated_content_hash_sequences": list(EXPECTED_TOUCHED_ALLOCATION_SEQUENCES),
        },
        "bps": {
            "path": outputs["incremental_bps"], "size": len(bps), "sha256": _sha(bps),
            "source_sha256": _sha(parent), "target_sha256": _sha(result), "round_trip": True,
        },
        "payload": {
            "path": outputs["payload"], "size": len(payload), "sha256": _sha(payload),
            "address": f"0x{load_address:08X}", "allocation_sequence": 78,
        },
        "symbols": {
            "path": outputs["symbols"], "size": len(symbols_raw), "sha256": _sha(symbols_raw),
        },
        "runtime_audit": {
            "path": outputs["audit"], "size": len(audit_raw), "sha256": _sha(audit_raw),
        },
        "route_audit": {
            "path": outputs["route_audit"], "size": len(route_raw), "sha256": _sha(route_raw),
        },
        "contract": {
            "path": outputs["contract"], "size": len(contract_raw), "sha256": _sha(contract_raw),
        },
        "identity": config["identity"],
        "species_count": NEW_SPECIES_COUNT,
        "p03": {
            "missing_owner_paths": 0,
            "accounting": route_audit["accounting"],
            "exclusions": route_audit["exclusions"],
            "full_p03_done": False,
        },
        "save": contract["save"],
        "done": False,
        "release_candidate": False,
        "mgba": "DEFERRED_TO_ROOT_FINAL_CUMULATIVE_ONCE",
        "checks": audit["checks"],
        "pending": metadata["remaining_work"],
    }
    checkpoint_raw = _stable_json(checkpoint)
    return {
        outputs["rom"]: result,
        outputs["metadata"]: metadata_raw,
        outputs["allocation"]: allocation_raw,
        outputs["incremental_bps"]: bps,
        outputs["payload"]: payload,
        outputs["symbols"]: symbols_raw,
        outputs["audit"]: audit_raw,
        outputs["route_audit"]: route_raw,
        outputs["contract"]: contract_raw,
        outputs["checkpoint"]: checkpoint_raw,
    }


def _atomic_write(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def materialize(root: Path, *, check: bool = False) -> dict[str, Any]:
    artifacts = build_artifacts(root)
    differences: list[str] = []
    for relative, raw in artifacts.items():
        path = root / relative
        if check:
            if not path.is_file() or path.read_bytes() != raw:
                differences.append(relative)
        else:
            _atomic_write(path, raw)
    if differences:
        _fail("生成物が再現結果と不一致です: " + ", ".join(differences))
    config = _read_json((root / CONFIG_PATH).read_bytes(), "Stage75 config")
    metadata = _read_json(artifacts[config["outputs"]["metadata"]], "Stage75 metadata")
    return {
        "status": "PASS", "mode": "CHECK" if check else "WRITE",
        "output_sha256": metadata["output"]["sha256"],
        "output_crc32": metadata["output"]["crc32"],
        "payload_size": metadata["payload"]["size"],
        "species_count": metadata["identity"]["species_id"] + 1,
        "p03_missing_owner_paths": metadata["route_audit"]["pre_evolution_carry"]["missing_owner_path_count"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = materialize(args.root, check=args.check)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    print("RESULT=DONE TASK=USER-MODERNIZATION-ROCKRUFF-OWN-TEMPO-STAGE75 VERIFY=PASS COMMIT=-")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["CONFIG_PATH", "Stage75Error", "build_artifacts", "materialize"]
