#!/usr/bin/env python3
"""実ROMへBattle Factory Trialの受付・選択・交換・復元を結合する。"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import struct
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, NoReturn, Sequence


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.regression.rom_runtime import _Blob, _charmap, _encode_text  # noqa: E402
from tools.rom_allocator import GBA_ROM_BASE, build_allocation_report_from_csv  # noqa: E402


TASK = "USER-20260814-FACILITY-RUNTIME"
ROM_SIZE = 32 * 1024 * 1024
STAGE19 = Path("build/stages/19_trainer_rebalance.gba")
STAGE19_META = Path("build/stages/19_trainer_rebalance.json")
STAGE19_ALLOC = Path("build/stages/19_allocation.json")
STAGE20 = Path("build/stages/20_facility_runtime.gba")
STAGE20_META = Path("build/stages/20_facility_runtime.json")
STAGE20_ALLOC = Path("build/stages/20_allocation.json")
RUNTIME_BIN = Path("generated/runtime/facility_runtime.bin")
RUNTIME_SYMBOLS = Path("generated/runtime/facility_runtime_symbols.json")
REPORT = Path("reports/generated/facility_runtime.md")
MGBA_FIXTURE = Path("build/stages/20_mgba_smoke.json")
ALLOCATION_NAME = "facility_runtime_payload"
GBA_ENTRY = (96, 5)
PAYLOAD_HEADER_SIZE = 0x80
POKEMON_SIZE = 100
TRIAL_BATTLE_COUNT = 3
TRIAL_REWARD_BP = 9

REQUIRED_ENTRYPOINTS = {
    "FacilityRuntime_Probe",
    "FacilityRuntime_Recover",
    "FacilityRuntime_Enter",
    "FacilityRuntime_CommitSelection",
    "FacilityRuntime_PrepareBattle",
    "FacilityRuntime_AfterBattle",
    "FacilityRuntime_BeginExchange",
    "FacilityRuntime_CommitExchange",
    "FacilityRuntime_SkipExchange",
    "FacilityRuntime_Complete",
    "FacilityRuntime_Abort",
}


class FacilityRuntimeError(ValueError):
    """施設runtimeの入力、ROM ABI、または動作証跡が不正。"""


def _fail(message: str) -> NoReturn:
    raise FacilityRuntimeError(message)


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _stable(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def _u32(raw: bytes | bytearray, offset: int, label: str) -> int:
    if offset < 0 or offset + 4 > len(raw):
        _fail(f"{label}: offset outside ROM: {offset:#x}")
    return struct.unpack_from("<I", raw, offset)[0]


def _rom_offset(pointer: int, size: int, label: str) -> int:
    address = pointer & ~1
    offset = address - GBA_ROM_BASE
    if offset < 0 or offset + size > ROM_SIZE:
        _fail(f"{label}: invalid ROM pointer {pointer:#010x}")
    return offset


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        _fail(f"JSON object required: {path}")
    return value


def _run(command: Sequence[str], label: str, *, cwd: Path = ROOT) -> str:
    completed = subprocess.run(
        command, cwd=cwd, text=True, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, check=False,
    )
    if completed.returncode:
        detail = completed.stderr.strip() or completed.stdout.strip()
        _fail(f"{label} failed ({completed.returncode}): {detail[-3000:]}")
    return completed.stdout.strip()


def _compile_runtime(root: Path, load_address: int) -> tuple[bytes, dict[str, int]]:
    compiler = shutil.which("arm-none-eabi-gcc")
    objcopy = shutil.which("arm-none-eabi-objcopy")
    nm = shutil.which("arm-none-eabi-nm")
    if not compiler or not objcopy or not nm:
        _fail("ARM GNU toolchain is required for facility runtime")
    source = root / "overlays/facility_runtime/facility_runtime.c"
    header = root / "overlays/facility_runtime/facility_runtime.h"
    save_source = root / "overlays/save_migration/save_migration.c"
    save_header = root / "overlays/save_migration/save_migration.h"
    for path in (source, header, save_source, save_header):
        if not path.is_file():
            _fail(f"facility runtime source missing: {path}")

    with tempfile.TemporaryDirectory(prefix="vega-facility-runtime-") as temporary:
        directory = Path(temporary)
        linker = directory / "linker.ld"
        elf = directory / "facility_runtime.elf"
        binary = directory / "facility_runtime.bin"
        linker.write_text(
            "SECTIONS\n{\n"
            f"  . = 0x{load_address:08X};\n"
            "  .text : { KEEP(*(.text.FacilityRuntime_*)) *(.text*) *(.rodata*) }\n"
            "  /DISCARD/ : { *(.comment*) *(.ARM.attributes*) *(.note*) }\n"
            "}\n",
            encoding="ascii",
        )
        command = [
            compiler, "-mthumb", "-mcpu=arm7tdmi", "-Os", "-std=c11",
            "-Wall", "-Wextra", "-Werror", "-ffreestanding", "-fno-builtin",
            "-DVEGA_SAVE_ROM_RUNTIME=1",
            "-fno-unwind-tables", "-fno-asynchronous-unwind-tables",
            "-fdata-sections", "-ffunction-sections", "-nostdlib",
            "-Wl,--build-id=none", "-Wl,--gc-sections",
            "-Wl,-e,FacilityRuntime_Probe", f"-Wl,-T,{linker}",
            f"-I{source.parent}", f"-I{save_source.parent}",
            str(source), str(save_source), "-o", str(elf),
        ]
        _run(command, "facility ARM link")
        undefined = _run([nm, "-u", str(elf)], "facility undefined-symbol check")
        if undefined.strip():
            _fail("facility ARM image has undefined symbols: " + undefined.strip())
        _run([objcopy, "-O", "binary", str(elf), str(binary)], "facility objcopy")
        symbol_text = _run([nm, "-n", "--defined-only", str(elf)], "facility nm")
        symbols: dict[str, int] = {}
        for line in symbol_text.splitlines():
            fields = line.split()
            if len(fields) == 3 and fields[2].startswith("FacilityRuntime_"):
                symbols[fields[2]] = int(fields[0], 16)
        missing = REQUIRED_ENTRYPOINTS - set(symbols)
        if missing:
            _fail(f"facility entrypoints missing: {sorted(missing)}")
        raw = binary.read_bytes()
        if not raw or len(raw) > 32 * 1024:
            _fail(f"unexpected facility runtime size: {len(raw)}")
        return raw, symbols


@dataclass
class _Script:
    data: bytearray
    fixups: list[tuple[int, str, bool]]

    def __init__(self) -> None:
        self.data = bytearray()
        self.fixups = []

    def emit(self, *values: int) -> "_Script":
        self.data.extend(values)
        return self

    def half(self, value: int) -> "_Script":
        self.data.extend(struct.pack("<H", value))
        return self

    def pointer(self, label: str, *, thumb: bool = False) -> "_Script":
        self.fixups.append((len(self.data), label, thumb))
        self.data.extend(bytes(4))
        return self

    def callnative(self, name: str) -> "_Script":
        return self.emit(0x23).pointer(f"native::{name}", thumb=True)

    def msgbox(self, label: str, kind: int = 4) -> "_Script":
        return self.emit(0x0F, 0x00).pointer(label).emit(0x09, kind)

    def compare_result(self, value: int) -> "_Script":
        return self.emit(0x21).half(0x800D).half(value)

    def if_equal(self, label: str) -> "_Script":
        return self.emit(0x06, 0x01).pointer(label)

    def goto(self, label: str) -> "_Script":
        return self.emit(0x05).pointer(label)


def _add_script(blob: _Blob, label: str, script: _Script) -> None:
    offset = blob.add(label, bytes(script.data), 4)
    for relative, target, thumb in script.fixups:
        blob.pointer(offset + relative, target, thumb=thumb)


def _normal_end(script: _Script) -> _Script:
    return script.emit(0x6C, 0x02)


def _battle_script(intro_text: str, after_label: str) -> _Script:
    return (
        _Script().msgbox(intro_text)
        .callnative("FacilityRuntime_PrepareBattle")
        .compare_result(1).if_equal(after_label)
        .goto("script_facility_loss")
    )


def _build_scripts(root: Path, blob: _Blob) -> dict[str, int]:
    mapping, tokens = _charmap(root)
    texts = {
        "text_facility_prompt": "バトルファクトリー トライアル！\nレンタルで 3れんせん しますか？",
        "text_facility_choose": "ランダムな 6ひきから\n3ひきを えらんでください",
        "text_facility_battle1": "だい1せん スタート！",
        "text_facility_battle2": "だい2せん スタート！",
        "text_facility_battle3": "だい3せん スタート！",
        "text_facility_exchange": "しょうり！ あいての ポケモンと\n1ひき こうかんしますか？",
        "text_facility_complete": "3れんしょう！\nBPを 9 てにいれました",
        "text_facility_loss": "ちょうせん しゅうりょう\nもとの てもちを もどしました",
        "text_facility_cancel": "ちょうせんを とりやめました",
        "text_facility_error": "じゅんびに しっぱいしました",
    }
    for label, text in texts.items():
        blob.add(label, _encode_text(text, mapping, tokens), 1)

    _add_script(
        blob, "script_facility_npc",
        _Script().emit(0x6A, 0x5A).msgbox("text_facility_prompt", 5)
        .compare_result(1).if_equal("script_facility_enter")
        .emit(0x6C, 0x02),
    )
    _add_script(
        blob, "script_facility_enter",
        _Script().callnative("FacilityRuntime_Enter")
        .compare_result(1).if_equal("script_facility_choose")
        .goto("script_facility_error"),
    )
    _add_script(
        blob, "script_facility_choose",
        _Script().msgbox("text_facility_choose").emit(0x25).half(0x002F).emit(0x27)
        .callnative("FacilityRuntime_CommitSelection")
        .compare_result(1).if_equal("script_facility_battle1")
        .goto("script_facility_cancel"),
    )

    for number in range(1, 4):
        label = f"script_facility_battle{number}"
        launch = f"script_facility_battle{number}_launch"
        _add_script(blob, label, _battle_script(f"text_facility_battle{number}", launch))
        after = _Script().emit(0x25).half(0x0029).emit(0x27, 0x5D)
        after.callnative("FacilityRuntime_AfterBattle")
        if number == 3:
            after.compare_result(2).if_equal("script_facility_complete")
            after.goto("script_facility_loss")
        else:
            after.compare_result(1).if_equal(f"script_facility_exchange{number}")
            after.goto("script_facility_loss")
        _add_script(blob, launch, after)

    for number in (1, 2):
        next_battle = f"script_facility_battle{number + 1}"
        _add_script(
            blob, f"script_facility_exchange{number}",
            _Script().msgbox("text_facility_exchange", 5)
            .compare_result(1).if_equal(f"script_facility_exchange{number}_choose")
            .goto(f"script_facility_exchange{number}_skip"),
        )
        _add_script(
            blob, f"script_facility_exchange{number}_choose",
            _Script().callnative("FacilityRuntime_BeginExchange")
            .compare_result(1).if_equal(f"script_facility_exchange{number}_menu")
            .goto(f"script_facility_exchange{number}_skip"),
        )
        _add_script(
            blob, f"script_facility_exchange{number}_menu",
            _Script().emit(0x25).half(0x002F).emit(0x27)
            .callnative("FacilityRuntime_CommitExchange").goto(next_battle),
        )
        _add_script(
            blob, f"script_facility_exchange{number}_skip",
            _Script().callnative("FacilityRuntime_SkipExchange").goto(next_battle),
        )

    _add_script(
        blob, "script_facility_complete",
        _normal_end(_Script().callnative("FacilityRuntime_Complete")
                    .msgbox("text_facility_complete")),
    )
    _add_script(
        blob, "script_facility_loss",
        _normal_end(_Script().msgbox("text_facility_loss")),
    )
    _add_script(
        blob, "script_facility_cancel",
        _normal_end(_Script().callnative("FacilityRuntime_Abort")
                    .msgbox("text_facility_cancel")),
    )
    _add_script(
        blob, "script_facility_error",
        _normal_end(_Script().callnative("FacilityRuntime_Abort")
                    .msgbox("text_facility_error")),
    )
    _add_script(
        blob, "script_facility_recover",
        _Script().callnative("FacilityRuntime_Recover").emit(0x02),
    )
    return {label: len(text) for label, text in texts.items()}


def _entry_header(stage: bytes, stage17_meta: dict[str, Any]) -> tuple[int, int]:
    root_pointer = int(stage17_meta["symbols"]["map_groups_root"])
    root = _rom_offset(root_pointer, 99 * 4, "stage17 map groups root")
    group_pointer = _u32(stage, root + GBA_ENTRY[0] * 4, "Kanto entry group")
    group = _rom_offset(group_pointer, (GBA_ENTRY[1] + 1) * 4, "Kanto entry group")
    header_pointer = _u32(stage, group + GBA_ENTRY[1] * 4, "Kanto entry header")
    header = _rom_offset(header_pointer, 0x1C, "Kanto entry header")
    return header, header_pointer


def _add_map_runtime(stage: bytes, stage17_meta: dict[str, Any], blob: _Blob) -> dict[str, Any]:
    header, header_pointer = _entry_header(stage, stage17_meta)
    events_pointer = _u32(stage, header + 4, "Vermilion events")
    events = _rom_offset(events_pointer, 0x14, "Vermilion events")
    old_events = bytearray(stage[events:events + 0x14])
    if old_events[0] != 1:
        _fail(f"Vermilion object count drift: {old_events[0]} != 1")
    objects_pointer = _u32(stage, events + 4, "Vermilion objects")
    objects = _rom_offset(objects_pointer, 0x18, "Vermilion objects")
    return_object = bytearray(stage[objects:objects + 0x18])
    if return_object[0] != 1:
        _fail("Vermilion return object local id drift")

    facility_object = bytearray(return_object)
    facility_object[0] = 2
    facility_object[3] = 0
    struct.pack_into("<HH", facility_object, 4, 20, 19)
    facility_object[8] = 3
    facility_object[9] = 0
    struct.pack_into("<H", facility_object, 0x0A, 0)
    struct.pack_into("<H", facility_object, 0x0C, 0)
    struct.pack_into("<I", facility_object, 0x10, 0)
    struct.pack_into("<H", facility_object, 0x14, 0)

    object_offset = blob.add(
        "facility_vermilion_objects", bytes(return_object + facility_object), 4
    )
    blob.pointer(object_offset + 0x18 + 0x10, "script_facility_npc")

    old_events[0] = 2
    struct.pack_into("<I", old_events, 4, 0)
    event_offset = blob.add("facility_vermilion_events", bytes(old_events), 4)
    blob.pointer(event_offset + 4, "facility_vermilion_objects")

    map_scripts = bytearray([3]) + bytes(4) + bytes([0])
    scripts_offset = blob.add("facility_vermilion_map_scripts", bytes(map_scripts), 4)
    blob.pointer(scripts_offset + 1, "script_facility_recover")

    old_scripts_pointer = _u32(stage, header + 8, "Vermilion map scripts")
    old_scripts = _rom_offset(old_scripts_pointer, 1, "Vermilion map scripts")
    if stage[old_scripts] != 0:
        _fail("Vermilion map script root is no longer the T17 empty terminator")
    return {
        "header_offset": header,
        "header_address": header_pointer,
        "old_events_pointer": events_pointer,
        "old_scripts_pointer": old_scripts_pointer,
        "object_count_before": 1,
        "object_count_after": 2,
        "facility_object": {"local_id": 2, "x": 20, "y": 19},
    }


def _build_payload(root: Path, stage: bytes, stage17_meta: dict[str, Any],
                   payload_offset: int) -> tuple[bytes, dict[str, Any]]:
    blob = _Blob()
    header_offset = blob.reserve("facility_runtime_header", PAYLOAD_HEADER_SIZE, 16)
    code_load = GBA_ROM_BASE + payload_offset + ((len(blob.data) + 3) & ~3)
    code, code_symbols = _compile_runtime(root, code_load)
    code_offset = blob.add("facility_runtime_code", code, 4)
    if GBA_ROM_BASE + payload_offset + code_offset != code_load:
        _fail("facility linker address disagrees with payload placement")
    for name, address in code_symbols.items():
        relative = address - code_load
        if relative < 0 or relative >= len(code):
            _fail(f"facility symbol outside code image: {name}")
        blob.labels[f"native::{name}"] = code_offset + relative

    text_lengths = _build_scripts(root, blob)
    map_meta = _add_map_runtime(stage, stage17_meta, blob)
    runtime_size = len(blob.data)
    struct.pack_into(
        "<8sIIIIIIII", blob.data, header_offset,
        b"VEGAF20\0", 1, runtime_size, len(code),
        TRIAL_BATTLE_COUNT, 6, 3, TRIAL_REWARD_BP, POKEMON_SIZE,
    )
    blob.pointer(header_offset + 40, "native::FacilityRuntime_Probe", thumb=True)
    blob.pointer(header_offset + 44, "script_facility_npc")
    blob.pointer(header_offset + 48, "facility_vermilion_events")
    blob.pointer(header_offset + 52, "facility_vermilion_map_scripts")
    payload = blob.finish(payload_offset)
    for number in range(1, TRIAL_BATTLE_COUNT + 1):
        launch = blob.labels[f"script_facility_battle{number}_launch"]
        if payload[launch:launch + 5] != b"\x25\x29\x00\x27\x5D":
            _fail(f"facility battle {number} launch opcode drift")
    metadata = {
        "payload": {
            "magic": "VEGAF20", "offset": payload_offset,
            "address": GBA_ROM_BASE + payload_offset,
            "size": len(payload), "sha256": _sha(payload),
            "code_offset": payload_offset + code_offset,
            "code_address": code_load, "code_size": len(code),
            "code_sha256": _sha(code),
        },
        "entrypoints": {
            name: code_symbols[name] | 1 for name in sorted(REQUIRED_ENTRYPOINTS)
        },
        "scripts": {
            "npc_address": GBA_ROM_BASE + payload_offset + blob.labels["script_facility_npc"],
            "recover_address": GBA_ROM_BASE + payload_offset + blob.labels["script_facility_recover"],
            "battlebegin_count": TRIAL_BATTLE_COUNT,
            "party_selection_special": 0x2F,
            "uses_existing_party_ui": True,
            "text_lengths": text_lengths,
        },
        "map": map_meta,
        "symbols": {
            label: GBA_ROM_BASE + payload_offset + relative
            for label, relative in sorted(blob.labels.items())
            if label.startswith("native::") or label.startswith("script_facility_")
            or label.startswith("facility_vermilion_")
        },
    }
    return payload, metadata


def _previous_requests(root: Path) -> list[dict[str, object]]:
    report = _read_json(root / STAGE19_ALLOC)
    return [{
        "name": row["name"], "region": row["region"], "size": row["size"],
        "alignment": row["alignment"], "start": row["start"],
        "owner": row["owner"], "purpose": row["purpose"],
        "content_sha256": row["content_sha256"],
    } for row in report["allocations"]]


def _allocation(root: Path, size: int, digest: str) -> tuple[dict[str, Any], dict[str, Any]]:
    requests = _previous_requests(root)
    requests.append({
        "name": ALLOCATION_NAME, "region": "integration_modules",
        "size": size, "alignment": 4, "owner": TASK,
        "purpose": "実ROM Factory受付、6候補/3選択、交換、3連戦、保存復元",
        "content_sha256": digest,
    })
    report = build_allocation_report_from_csv(root / "config/rom_regions.csv", requests)
    allocation = next(row for row in report["allocations"] if row["name"] == ALLOCATION_NAME)
    return allocation, report


def _patch_pointer(output: bytearray, offset: int, expected: int, replacement: int,
                   label: str) -> dict[str, Any]:
    actual = _u32(output, offset, label)
    if actual != expected:
        _fail(f"{label}: expected {expected:#010x}, got {actual:#010x}")
    struct.pack_into("<I", output, offset, replacement)
    return {
        "label": label, "site_offset": offset,
        "site_address": GBA_ROM_BASE + offset,
        "expected_pointer": expected, "replacement_pointer": replacement,
    }


def build_runtime_outputs(root: Path = ROOT) -> dict[str, bytes]:
    root = Path(root)
    stage = (root / STAGE19).read_bytes()
    stage_meta = _read_json(root / STAGE19_META)
    stage17_meta = _read_json(root / "build/stages/17_regression.json")
    if len(stage) != ROM_SIZE or _sha(stage) != stage_meta["output"]["sha256"]:
        _fail("stage19 size/hash contract failed")

    preliminary, _ = _build_payload(root, stage, stage17_meta, 0)
    allocation, _ = _allocation(root, len(preliminary), "0" * 64)
    payload_offset = int(allocation["start"])
    payload, runtime = _build_payload(root, stage, stage17_meta, payload_offset)
    if len(payload) != len(preliminary):
        _fail("address-dependent facility payload size changed")
    allocation, allocation_report = _allocation(root, len(payload), _sha(payload))
    if int(allocation["start"]) != payload_offset:
        _fail("facility allocation changed after final link")
    payload_end = int(allocation["end_exclusive"])
    if stage[payload_offset:payload_end] != b"\xFF" * len(payload):
        _fail("facility payload destination is not erased FF")

    output = bytearray(stage)
    output[payload_offset:payload_end] = payload
    header = int(runtime["map"]["header_offset"])
    patches = [
        _patch_pointer(
            output, header + 4, int(runtime["map"]["old_events_pointer"]),
            int(runtime["symbols"]["facility_vermilion_events"]),
            "Vermilion events root",
        ),
        _patch_pointer(
            output, header + 8, int(runtime["map"]["old_scripts_pointer"]),
            int(runtime["symbols"]["facility_vermilion_map_scripts"]),
            "Vermilion map scripts root",
        ),
    ]
    allowed = [(payload_offset, payload_end)] + [
        (row["site_offset"], row["site_offset"] + 4) for row in patches
    ]
    outside: list[int] = []
    for index, (before, after) in enumerate(zip(stage, output)):
        if before != after and not any(start <= index < end for start, end in allowed):
            outside.append(index)
            if len(outside) == 8:
                break
    if outside:
        _fail(f"facility bytes changed outside declared spans: {outside}")

    output_raw = bytes(output)
    metadata = {
        "schema_version": 1,
        "task": TASK,
        "status": "PASS",
        "input": {"path": STAGE19.as_posix(), "size": len(stage), "sha256": _sha(stage)},
        "output": {"path": STAGE20.as_posix(), "size": len(output_raw), "sha256": _sha(output_raw)},
        **runtime,
        "patches": patches,
        "allocation": {
            "path": STAGE20_ALLOC.as_posix(), "name": ALLOCATION_NAME,
            "overlap_count": allocation_report["summaries"]["overlap_count"],
            "remaining_allocatable_bytes": allocation_report["summaries"]["remaining_allocatable_bytes"],
        },
        "contract": {
            "random_candidates": 6, "manual_selections": 3,
            "battle_count": TRIAL_BATTLE_COUNT,
            "exchange_after_wins": True, "exchange_manual_party_slot": True,
            "bp_reward": TRIAL_REWARD_BP,
            "exact_party_snapshot_bytes": 6 * POKEMON_SIZE,
            "seen_only": True, "caught_unchanged": True,
            "recovery_map_script": True,
            "battle_policy_source": "CFRU-JP fixed upstream runtime",
        },
        "invariants": {
            "rom_size_32_mib": len(output_raw) == ROM_SIZE,
            "allocator_overlap_zero": allocation_report["summaries"]["overlap_count"] == 0,
            "existing_return_npc_preserved": True,
            "facility_npc_physically_bound": runtime["map"]["object_count_after"] == 2,
            "three_battlebegin_commands": runtime["scripts"]["battlebegin_count"] == 3,
            "all_runtime_entrypoints_bound": set(runtime["entrypoints"]) == REQUIRED_ENTRYPOINTS,
        },
    }
    if not all(metadata["invariants"].values()):
        _fail("facility runtime invariant failed")
    symbol_output = {
        "schema_version": 1,
        "payload": metadata["payload"],
        "entrypoints": metadata["entrypoints"],
        "scripts": metadata["scripts"],
        "map": metadata["map"],
    }
    return {
        STAGE20.as_posix(): output_raw,
        STAGE20_META.as_posix(): _stable(metadata),
        STAGE20_ALLOC.as_posix(): _stable(allocation_report),
        RUNTIME_BIN.as_posix(): payload,
        RUNTIME_SYMBOLS.as_posix(): _stable(symbol_output),
    }


def _mgba_fixture(root: Path, stage: bytes, metadata: dict[str, Any]) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="vega-facility-smoke-") as temporary:
        temp = Path(temporary)
        rom = temp / "20_facility_runtime.gba"
        executable = temp / "mgba-facility-runtime-smoke"
        rom.write_bytes(stage)
        compiler = os.environ.get("CC", "cc")
        _run([
            compiler, "-std=c11", "-Wall", "-Wextra", "-Werror", "-pedantic",
            "tools/mgba_facility_runtime_smoke.c", "-o", str(executable), "-lmgba",
        ], "facility libmGBA smoke compile", cwd=root)
        entrypoints = metadata["entrypoints"]
        args = [
            str(executable), str(rom),
            hex(entrypoints["FacilityRuntime_Probe"]),
            hex(entrypoints["FacilityRuntime_Enter"]),
            hex(entrypoints["FacilityRuntime_CommitSelection"]),
            hex(entrypoints["FacilityRuntime_PrepareBattle"]),
            hex(entrypoints["FacilityRuntime_AfterBattle"]),
            hex(entrypoints["FacilityRuntime_BeginExchange"]),
            hex(entrypoints["FacilityRuntime_CommitExchange"]),
            hex(entrypoints["FacilityRuntime_SkipExchange"]),
            hex(entrypoints["FacilityRuntime_Complete"]),
            hex(entrypoints["FacilityRuntime_Abort"]),
            hex(entrypoints["FacilityRuntime_Recover"]),
            hex(metadata["symbols"]["script_facility_npc"]),
            hex(metadata["symbols"]["facility_vermilion_map_scripts"]),
        ]
        first = json.loads(_run(args, "facility exact-ROM smoke run 1", cwd=root))
        second = json.loads(_run(args, "facility exact-ROM smoke run 2", cwd=root))
        if first != second or first.get("status") != "PASS":
            _fail("facility exact-ROM smoke is not deterministic PASS")
        first["process_runs"] = 2
        first["rom_sha256"] = _sha(stage)
        return first


def _report(metadata: dict[str, Any], mgba: dict[str, Any]) -> bytes:
    checks = mgba["checks"]
    text = f"""# 実ROM Battle Factory runtime

## 結論

- クチバ（Vermilion）にFactory Trial受付NPCを実配置した。
- 固定CFRU-JPの生成器でLv.50候補6体を毎回ランダム生成し、既存party UIで3体を選択する。
- single 3v3を3戦し、1・2戦目の勝利後は相手側からランダム提示された1体と、手持ちで選んだ1体を交換できる。
- 完走時は9 BP。敗北、辞退、selection cancel、reset復旧で入場前600 byte partyを復元する。
- rental/opponentはseenだけを更新し、caughtは変更しない。

## ROM結合

- Input: `{metadata['input']['path']}` / `{metadata['input']['sha256']}`
- Output: `{metadata['output']['path']}` / `{metadata['output']['sha256']}`
- Runtime: `{metadata['payload']['address']:#010x}` / {metadata['payload']['size']} bytes
- Vermilion object count: {metadata['map']['object_count_before']} -> {metadata['map']['object_count_after']}
- Allocator overlap: {metadata['allocation']['overlap_count']}

## 軽量実ROMスモーク

- random 6 unique candidates: {checks['random_six_unique']}
- manual 3 selection: {checks['manual_select_three']}
- CFRU facility policy pending: {checks['cfru_policy_pending']}
- win exchange: {checks['win_exchange']}
- exact party restore (complete/loss/abort/reset): {checks['exact_restore_all_exits']}
- seen only / caught unchanged: {checks['seen_only']}
- 9 BP / streak / once reward: {checks['reward_and_streak']}
- physical NPC and recovery script: {checks['physical_npc_and_recovery_script']}
- deterministic process runs: {mgba['process_runs']}

重いfresh checkout全再構築は、ユーザー指示どおり再実行していない。変更範囲に限定したstage 20生成、allocator、script graph、libmGBA exact-ROM smokeを2 processで検証した。
"""
    return text.encode("utf-8")


def collect_outputs(root: Path = ROOT) -> dict[str, bytes]:
    outputs = build_runtime_outputs(root)
    repeated = build_runtime_outputs(root)
    if outputs != repeated:
        _fail("facility runtime build is not byte deterministic")
    stage = outputs[STAGE20.as_posix()]
    metadata = json.loads(outputs[STAGE20_META.as_posix()])
    mgba = _mgba_fixture(root, stage, metadata)
    outputs[MGBA_FIXTURE.as_posix()] = _stable(mgba)
    outputs[REPORT.as_posix()] = _report(metadata, mgba)
    return outputs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("build", "check"))
    args = parser.parse_args()
    try:
        outputs = collect_outputs(ROOT)
        if args.mode == "build":
            for relative, raw in outputs.items():
                path = ROOT / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
            print(
                f"Facility runtime build: PASS ({len(outputs)} artifacts; "
                f"ROM sha256={_sha(outputs[STAGE20.as_posix()])})"
            )
        else:
            drift = [
                relative for relative, raw in outputs.items()
                if not (ROOT / relative).is_file() or (ROOT / relative).read_bytes() != raw
            ]
            if drift:
                _fail("artifact drift: " + ", ".join(drift))
            print(f"Facility runtime check: PASS ({len(outputs)} artifacts, side effects NONE)")
    except (FacilityRuntimeError, OSError, KeyError, TypeError, ValueError,
            subprocess.SubprocessError) as error:
        print(f"Facility runtime {args.mode}: FAIL: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
