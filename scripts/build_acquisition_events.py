#!/usr/bin/env python3
"""stage 25へ図鑑完成用の取得イベント、交換進化、野生補正を統合する。"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
import struct
import subprocess
import sys
import tempfile
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, NoReturn, Sequence


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.regression.rom_runtime import (  # noqa: E402
    _Blob,
    _charmap,
    _encode_text,
    _source_header,
    _source_locations,
)
from tools.release.bps import apply_bps, create_bps  # noqa: E402
from tools.rom_allocator import GBA_ROM_BASE, build_allocation_report_from_csv  # noqa: E402


TASK = "USER-20260816-ACQUISITION-EVENTS"
ROM_SIZE = 32 * 1024 * 1024
CLEAN_ROM_SIZE = 16 * 1024 * 1024
CLEAN_ROM = Path("inputs/private/FireRed_JPN_Rev0_clean.gba")
CLEAN_ROM_SHA256 = "1e4af44b0c75cc8649bfb8649dc4ae5850bf5358bd6b9cd0bf779c99f9db1486"
STAGE25 = Path("build/stages/25_move_memory.gba")
STAGE25_META = Path("build/stages/25_move_memory.json")
STAGE25_ALLOCATION = Path("build/stages/25_allocation.json")
STAGE26 = Path("build/stages/26_acquisition_events.gba")
STAGE26_META = Path("build/stages/26_acquisition_events.json")
STAGE26_ALLOCATION = Path("build/stages/26_allocation.json")
RUNTIME_BIN = Path("generated/runtime/acquisition_events.bin")
RUNTIME_SYMBOLS = Path("generated/runtime/acquisition_events_symbols.json")
MAP_BIN = Path("generated/runtime/acquisition_map_events.bin")
MAP_SYMBOLS = Path("generated/runtime/acquisition_map_events_symbols.json")
EVOLUTION_REPORT = Path("generated/runtime/acquisition_evolution_routes.json")
EXACT_CASES = Path("build/stages/26_acquisition_exact_cases.json")
MGBA_FIXTURE = Path("build/stages/26_mgba_acquisition.json")
REPORT = Path("reports/generated/acquisition_events.md")
PATCH = Path("build/patches/vega-modern-kanto-v1.4.0.bps")
PACKAGE = Path("vendor/vega_acquisition")
RUNNER = Path("tools/mgba_acquisition_smoke.c")
EMBEDDED_RUNNER_SOURCES = (
    Path("tools/mgba_battle_core_smoke.c"),
    Path("tools/mgba_ai_fixture_runner.c"),
)

EXPECTED_STAGE25_SHA256 = "0f7406c70021adf9778f0e7a9220f4e014feaac73d7e988ba39700a63be97fcd"
EXPECTED_T06_FINGERPRINT = "0a4c04b64ee012db93c6b6bda92aa0e277fc79f63aa0e133f47f3f2cd0b17b03"
EXPECTED_T06_LINKED_SHA256 = "8c0ac2be2b77fa97b974a7a2377aaf99b796fb49c369d10a7faf9432ce2040f6"

MAP_GROUPS_POINTER_SITE = 0x00054B0C
WILD_HEADERS_POINTER_SITE = 0x0008257C
EXPECTED_MAP_GROUPS_ROOT = 0x092C5194
EXPECTED_WILD_HEADERS_ROOT = 0x092CAF0C
EXPECTED_WILD_HEADER_COUNT = 265
EVOLUTION_TABLE_ROOT = 0x09F79F38
SPECIES_COUNT = 1621
EVOLUTION_SLOTS = 16
EVOLUTION_ROW_SIZE = 8
EVOLUTION_SPECIES_STRIDE = EVOLUTION_SLOTS * EVOLUTION_ROW_SIZE

VALIDATOR_SITE = 0x012CEEE0
VALIDATOR_EXPECTED = bytes.fromhex("70b504000620002c")
EGG_HATCH_SCRIPT_SITE = 0x001A59C4
EGG_HATCH_SCRIPT_EXPECTED = bytes.fromhex(
    "690f00795d1a08090425c200276b02"
)
TRY_SAVING_DATA = 0x080DB34D
TRY_SAVING_DATA_EXPECTED = bytes.fromhex("30b50006050e0948")
SAVE_LOAD_GAME_DATA = 0x080DB4E5
SAVE_LOAD_GAME_DATA_EXPECTED = bytes.fromhex("70b50006040e0448")
READ_FLASH = 0x081C2A55
READ_FLASH_EXPECTED = bytes.fromhex("f0b5a0b0")
RUNTIME_ALLOCATION = "acquisition_runtime"
MAP_ALLOCATION = "acquisition_map_scripts"
LINK_CABLE_ITEM = 395
EVO_ITEM = 7
EVO_ITEM_HOLD_ITEM = 35

REQUIRED_RUNTIME_SYMBOLS = {
    "VegaAcq_Probe",
    "VegaAcq_OpenHost",
    "VegaAcq_Begin",
    "VegaAcq_ResolveBattle",
    "VegaAcq_RecoverPending",
    "VegaAcq_PostHost",
    "VegaAcq_RegisterHatchedPartyMon",
    "VegaAcqAdapter_Probe",
    "VegaSaveValidate",
}

TEXTS = {
    "text_acq_success": "てつづきが かんりょうしました！",
    "text_acq_locked": "まだ りようできません",
    "text_acq_claimed": "この てつづきは かんりょうずみです",
    "text_acq_retry": "また ちょうせんしてください",
    "text_acq_missing": "ひつような じょうけんを みたしていません",
    "text_acq_error": "てつづきを かんりょうできませんでした",
}

HELD_ITEMS = {
    "おうじゃのしるし": 473,
    "メタルコート": 477,
    "りゅうのウロコ": 478,
    "アップグレード": 479,
    "しんかいのキバ": 475,
    "しんかいのウロコ": 476,
    "プロテクター": 396,
    "エレキブースター": 397,
    "マグマブースター": 398,
    "あやしいパッチ": 399,
    "れいかいのぬの": 400,
    "きれいなウロコ": 469,
    "においぶくろ": 470,
    "ホイップポップ": 471,
}

SPECIAL_FORM_KEYS = {
    520: ("SPECIES_KEY_GRAVELER_A", "SPECIES_KEY_GOLEM_A"),
    554: ("SPECIES_KEY_PUMPKABOO_XL", "SPECIES_KEY_GOURGEIST_XL"),
    555: ("SPECIES_KEY_PUMPKABOO_L", "SPECIES_KEY_GOURGEIST_L"),
    556: ("SPECIES_KEY_PUMPKABOO_M", "SPECIES_KEY_GOURGEIST_M"),
}


class AcquisitionBuildError(ValueError):
    """入力固定、ROM ABI、配置、または受入条件の違反。"""


def _fail(message: str) -> NoReturn:
    raise AcquisitionBuildError(message)


def _sha(raw: bytes | bytearray) -> str:
    return hashlib.sha256(raw).hexdigest()


def _stable(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        _fail(f"JSON root is not an object: {path}")
    return value


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def _run(command: Sequence[str], label: str, *, cwd: Path = ROOT) -> str:
    completed = subprocess.run(
        list(command), cwd=cwd, text=True, capture_output=True, check=False,
    )
    if completed.returncode:
        detail = (completed.stderr or completed.stdout).strip()
        _fail(f"{label} failed ({completed.returncode}): {detail}")
    return completed.stdout.strip()


def _u16(raw: bytes | bytearray, offset: int, label: str = "u16") -> int:
    if offset < 0 or offset + 2 > len(raw):
        _fail(f"{label}: offset outside ROM: 0x{offset:X}")
    return struct.unpack_from("<H", raw, offset)[0]


def _u32(raw: bytes | bytearray, offset: int, label: str = "u32") -> int:
    if offset < 0 or offset + 4 > len(raw):
        _fail(f"{label}: offset outside ROM: 0x{offset:X}")
    return struct.unpack_from("<I", raw, offset)[0]


def _rom_offset(address: int, size: int = 1, *, limit: int = ROM_SIZE) -> int:
    address &= ~1
    offset = address - GBA_ROM_BASE
    if offset < 0 or offset + size > limit:
        _fail(f"ROM address outside image: 0x{address:08X}+{size}")
    return offset


def _pointer(raw: bytes | bytearray, offset: int, label: str) -> int:
    value = _u32(raw, offset, label)
    _rom_offset(value, 1, limit=len(raw))
    return value


def _input_audit(root: Path) -> tuple[bytes, dict[str, Any], bytes, dict[str, Any]]:
    stage = (root / STAGE25).read_bytes()
    metadata = _read_json(root / STAGE25_META)
    clean = (root / CLEAN_ROM).read_bytes()
    pin = _read_json(root / PACKAGE / "manifests/source_stage_pin.json")
    if len(stage) != ROM_SIZE or _sha(stage) != EXPECTED_STAGE25_SHA256:
        _fail("stage 25 size/hash differs from fixed v1.3.9 input")
    if metadata.get("output", {}).get("sha256") != EXPECTED_STAGE25_SHA256:
        _fail("stage 25 metadata hash differs")
    if len(clean) != CLEAN_ROM_SIZE or _sha(clean) != CLEAN_ROM_SHA256:
        _fail("clean FireRed JPN Rev.0 input differs")
    if (
        pin.get("expected_exact_input_rom_sha256") != EXPECTED_STAGE25_SHA256
        or pin.get("snapshot_commit") != "fb2dba1"
        or int(str(pin.get("evolution_table_root")), 0) != EVOLUTION_TABLE_ROOT
        or int(str(pin.get("wild_header_root")), 0) != EXPECTED_WILD_HEADERS_ROOT
        or int(pin.get("wild_header_count", 0)) != EXPECTED_WILD_HEADER_COUNT
    ):
        _fail("acquisition package stage pin differs")
    if _u32(stage, MAP_GROUPS_POINTER_SITE, "stage gMapGroups") != EXPECTED_MAP_GROUPS_ROOT:
        _fail("stage 25 map group root differs")
    if _u32(stage, WILD_HEADERS_POINTER_SITE, "stage wild root") != EXPECTED_WILD_HEADERS_ROOT:
        _fail("stage 25 wild header root differs")
    if stage[VALIDATOR_SITE:VALIDATOR_SITE + 8] != VALIDATOR_EXPECTED:
        _fail("stage 25 save validator entry signature differs")
    if (
        stage[EGG_HATCH_SCRIPT_SITE:
              EGG_HATCH_SCRIPT_SITE + len(EGG_HATCH_SCRIPT_EXPECTED)]
        != EGG_HATCH_SCRIPT_EXPECTED
    ):
        _fail("stage 25 egg-hatch field script signature differs")
    for address, expected, label in (
        (TRY_SAVING_DATA, TRY_SAVING_DATA_EXPECTED, "TrySavingData"),
        (SAVE_LOAD_GAME_DATA, SAVE_LOAD_GAME_DATA_EXPECTED, "Save_LoadGameData"),
        (READ_FLASH, READ_FLASH_EXPECTED, "ReadFlash"),
    ):
        offset = _rom_offset(address, len(expected), limit=len(stage))
        if stage[offset:offset + len(expected)] != expected:
            _fail(f"stage 25 {label} signature differs")
    evolution = (root / "generated/engine/evolutions/evolutions.bin").read_bytes()
    evolution_offset = _rom_offset(EVOLUTION_TABLE_ROOT, len(evolution))
    if len(evolution) != SPECIES_COUNT * EVOLUTION_SPECIES_STRIDE:
        _fail("generated evolution table size differs")
    if stage[evolution_offset:evolution_offset + len(evolution)] != evolution:
        _fail("stage 25 evolution table differs from generated source")
    linked = root / "build/battle-core" / EXPECTED_T06_FINGERPRINT / "run-1/linked.o"
    if not linked.is_file() or _sha(linked.read_bytes()) != EXPECTED_T06_LINKED_SHA256:
        _fail("fixed T06 linked object differs")
    return stage, metadata, clean, pin


def _linked_symbols(root: Path) -> dict[str, int]:
    linked = root / "build/battle-core" / EXPECTED_T06_FINGERPRINT / "run-1/linked.o"
    required = {
        "CreateMonWithNatureLetter",
        "GiveMonToPlayer",
        "CreateEgg",
        "GetBoxedMonPtr",
        "GetBoxMonDataAt",
        "GetCompressedMonPtr",
        "CreateCompressedMonFromBoxMon",
        "ZeroBoxMonAt",
        "GetEvolutionTargetSpecies",
    }
    symbols: dict[str, int] = {}
    for line in _run(["arm-none-eabi-nm", "-n", str(linked)], "T06 symbol audit").splitlines():
        fields = line.split()
        if len(fields) == 3 and fields[2] in required:
            symbols[fields[2]] = int(fields[0], 16)
    if set(symbols) != required or any(value & 1 for value in symbols.values()):
        _fail(f"fixed T06 acquisition symbols differ: {symbols}")
    species = _read_json(root / "build/stages/09_species_surface.json")
    name_address = species.get("runtime", {}).get("symbols", {}).get(
        "VegaSpeciesSurface_GetSpeciesName"
    )
    if name_address != 0x09FDA144:
        _fail(f"species-name runtime address differs: {name_address!r}")
    symbols["VegaSpeciesSurface_GetSpeciesName"] = int(name_address)
    return symbols


def _compile_runtime(
    root: Path, load_address: int, linked: dict[str, int]
) -> tuple[bytes, dict[str, int]]:
    compiler = shutil.which("arm-none-eabi-gcc")
    objcopy = shutil.which("arm-none-eabi-objcopy")
    nm = shutil.which("arm-none-eabi-nm")
    if not compiler or not objcopy or not nm:
        _fail("ARM GNU toolchain is required for acquisition runtime")
    package = root / PACKAGE
    sources = [
        package / "overlays/acquisition_runtime/acquisition_runtime.c",
        package / "overlays/acquisition_runtime/acquisition_save_migration.c",
        package / "generated/acquisition_event_defs.c",
        package / "generated/acquisition_collection_defs.c",
        package / "generated/acquisition_host_defs.c",
        package / "generated/acquisition_host_wrappers.c",
        root / "overlays/acquisition_runtime/acquisition_engine_adapter_rom.c",
        root / "overlays/acquisition_runtime/acquisition_libc.c",
        root / "overlays/save_migration/save_migration.c",
    ]
    for source in sources:
        if not source.is_file():
            _fail(f"acquisition runtime source missing: {source}")
    defines = [
        "-DVEGA_SAVE_ROM_RUNTIME=1",
        f"-DVEGA_ACQ_CREATE_MON_ADDRESS=0x{linked['CreateMonWithNatureLetter'] | 1:08X}u",
        f"-DVEGA_ACQ_CREATE_EGG_ADDRESS=0x{linked['CreateEgg'] | 1:08X}u",
        f"-DVEGA_ACQ_GIVE_MON_ADDRESS=0x{linked['GiveMonToPlayer'] | 1:08X}u",
        f"-DVEGA_ACQ_GET_BOX_MON_DATA_ADDRESS=0x{linked['GetBoxMonDataAt'] | 1:08X}u",
        f"-DVEGA_ACQ_GET_BOXED_MON_PTR_ADDRESS=0x{linked['GetBoxedMonPtr'] | 1:08X}u",
        f"-DVEGA_ACQ_ZERO_BOX_MON_AT_ADDRESS=0x{linked['ZeroBoxMonAt'] | 1:08X}u",
        f"-DVEGA_ACQ_SPECIES_NAME_ADDRESS=0x{linked['VegaSpeciesSurface_GetSpeciesName'] | 1:08X}u",
    ]
    with tempfile.TemporaryDirectory(prefix="vega-acquisition-runtime-") as raw:
        directory = Path(raw)
        objects: list[Path] = []
        common = [
            compiler, "-mthumb", "-mcpu=arm7tdmi", "-mthumb-interwork",
            "-Os", "-std=c11", "-Wall", "-Wextra", "-Werror",
            "-ffreestanding", "-fno-builtin", "-fno-unwind-tables",
            "-fno-asynchronous-unwind-tables", "-fdata-sections",
            "-ffunction-sections", "-fno-common", *defines,
            f"-I{root}", f"-I{package}",
        ]
        for index, source in enumerate(sources):
            obj = directory / f"{index:02d}_{source.stem}.o"
            _run([*common, "-c", str(source), "-o", str(obj)], f"compile {source.name}")
            objects.append(obj)
        linker = directory / "linker.ld"
        linker.write_text(
            "SECTIONS\n{\n"
            f"  . = 0x{load_address:08X};\n"
            "  .text : {\n"
            "    KEEP(*(.text.VegaAcq_*)) KEEP(*(.text.VegaAcqHost_*))\n"
            "    KEEP(*(.text.VegaAcqSave*))\n"
            "    KEEP(*(.text.VegaAcqAdapter_*)) KEEP(*(.text.VegaSaveValidate))\n"
            "    *(.text*) *(.rodata*) *(.data*)\n"
            "  }\n"
            "  .bss (NOLOAD) : { *(.bss*) *(COMMON) }\n"
            "  /DISCARD/ : { *(.comment*) *(.ARM.attributes*) *(.note*) }\n"
            "}\n",
            encoding="ascii",
        )
        elf = directory / "acquisition.elf"
        binary = directory / "acquisition.bin"
        _run([
            compiler, "-mthumb", "-mcpu=arm7tdmi", "-mthumb-interwork",
            "-nostdlib", "-Wl,--build-id=none", "-Wl,--gc-sections",
            "-Wl,-e,VegaAcq_Probe", f"-Wl,-T,{linker}",
            *map(str, objects), "-lgcc", "-o", str(elf),
        ], "link acquisition runtime")
        undefined = _run([nm, "-u", str(elf)], "acquisition undefined-symbol audit")
        if undefined:
            _fail("acquisition runtime has undefined symbols: " + undefined)
        _run([objcopy, "-O", "binary", str(elf), str(binary)], "acquisition objcopy")
        symbols: dict[str, int] = {}
        for line in _run([nm, "-n", "--defined-only", str(elf)], "acquisition nm").splitlines():
            fields = line.split()
            if len(fields) == 3:
                try:
                    symbols[fields[2]] = int(fields[0], 16)
                except ValueError:
                    pass
        missing = sorted(REQUIRED_RUNTIME_SYMBOLS - set(symbols))
        wrappers = sorted(name for name in symbols if name.startswith("VegaAcqHost_"))
        if missing or len(wrappers) != 24:
            _fail(f"linked acquisition exports differ: missing={missing}, wrappers={len(wrappers)}")
        payload = binary.read_bytes()
        if not payload or len(payload) > 256 * 1024:
            _fail(f"unexpected acquisition runtime size: {len(payload)}")
        for name in REQUIRED_RUNTIME_SYMBOLS | set(wrappers):
            if not load_address <= symbols[name] < load_address + len(payload):
                _fail(f"runtime symbol outside payload: {name}=0x{symbols[name]:08X}")
        return payload, symbols


def _previous_requests(root: Path) -> list[dict[str, object]]:
    report = _read_json(root / STAGE25_ALLOCATION)
    if report.get("summaries", {}).get("overlap_count") != 0:
        _fail("stage 25 allocator overlap contract failed")
    return [{
        "name": row["name"], "region": row["region"], "size": row["size"],
        "alignment": row["alignment"], "start": row["start"],
        "owner": row["owner"], "purpose": row["purpose"],
        "content_sha256": row["content_sha256"],
    } for row in report["allocations"]]


def _allocation(
    root: Path, runtime_size: int, runtime_sha: str, map_size: int, map_sha: str
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    requests = _previous_requests(root)
    requests += [
        {
            "name": RUNTIME_ALLOCATION, "region": "integration_modules",
            "size": runtime_size, "alignment": 16, "owner": TASK,
            "purpose": "201取得event transaction/menu/save runtime",
            "content_sha256": runtime_sha,
        },
        {
            "name": MAP_ALLOCATION, "region": "integration_modules",
            "size": map_size, "alignment": 4, "owner": TASK,
            "purpose": "24取得host scripts/restored objects/event headers",
            "content_sha256": map_sha,
        },
    ]
    report = build_allocation_report_from_csv(root / "config/rom_regions.csv", requests)
    if report.get("summaries", {}).get("overlap_count") != 0:
        _fail("stage 26 allocator overlap detected")
    by_name = {row["name"]: row for row in report["allocations"]}
    return by_name[RUNTIME_ALLOCATION], by_name[MAP_ALLOCATION], report


@dataclass
class _Script:
    data: bytearray
    fixups: list[tuple[int, str, bool]]
    operations: list[str]

    def __init__(self) -> None:
        self.data = bytearray()
        self.fixups = []
        self.operations = []

    def emit(self, *values: int, operation: str | None = None) -> "_Script":
        self.data.extend(values)
        if operation:
            self.operations.append(operation)
        return self

    def half(self, value: int) -> "_Script":
        self.data.extend(struct.pack("<H", value))
        return self

    def word(self, value: int) -> "_Script":
        self.data.extend(struct.pack("<I", value))
        return self

    def pointer(self, label: str, *, thumb: bool = False) -> "_Script":
        self.fixups.append((len(self.data), label, thumb))
        self.data.extend(bytes(4))
        return self

    def callnative(self, address: int, name: str) -> "_Script":
        self.operations.append(f"callnative:{name}")
        return self.emit(0x23).word(address | 1)

    def msgbox(self, label: str) -> "_Script":
        self.operations.append(f"msgbox:{label}")
        return self.emit(0x0F, 0x00).pointer(label).emit(0x09, 4)

    def compare_result(self, value: int) -> "_Script":
        self.operations.append(f"compare:0x800D:{value}")
        return self.emit(0x21).half(0x800D).half(value)

    def if_equal(self, label: str) -> "_Script":
        self.operations.append(f"if_equal:{label}")
        return self.emit(0x06, 0x01).pointer(label)

    def goto(self, label: str) -> "_Script":
        self.operations.append(f"goto:{label}")
        return self.emit(0x05).pointer(label)


def _add_script(blob: _Blob, label: str, script: _Script) -> None:
    offset = blob.add(label, bytes(script.data), 4)
    for relative, target, thumb in script.fixups:
        blob.pointer(offset + relative, target, thumb=thumb)


def _host_script(wrapper: int, post_host: int) -> _Script:
    return (
        _Script().emit(0x6A, 0x5A, operation="lock_faceplayer")
        .callnative(wrapper, "host_wrapper")
        .compare_result(9).if_equal("script_acq_wait")
        .goto("script_acq_result")
    )


def _build_map_payload(
    root: Path,
    stage: bytes,
    clean: bytes,
    runtime_symbols: dict[str, int],
    payload_offset: int,
) -> tuple[bytes, dict[str, Any]]:
    blob = _Blob()
    mapping, tokens = _charmap(root)
    text_meta: dict[str, Any] = {}
    for label, text_value in TEXTS.items():
        encoded = _encode_text(text_value, mapping, tokens)
        blob.add(label, encoded, 1)
        text_meta[label] = {"text": text_value, "size": len(encoded), "sha256": _sha(encoded)}

    post_host = runtime_symbols["VegaAcq_PostHost"]
    _add_script(
        blob,
        "script_acq_wait",
        _Script().emit(0x27, operation="waitstate")
        .callnative(post_host, "VegaAcq_PostHost")
        .goto("script_acq_result"),
    )
    result = _Script()
    for value, label in (
        (0, "script_acq_success"),
        (2, "script_acq_end"),
        (3, "script_acq_locked"),
        (4, "script_acq_claimed"),
        (6, "script_acq_missing"),
        (7, "script_acq_missing"),
        (12, "script_acq_retry"),
        (13, "script_acq_retry"),
    ):
        result.compare_result(value).if_equal(label)
    result.goto("script_acq_error")
    _add_script(blob, "script_acq_result", result)
    for label, text_label in (
        ("script_acq_success", "text_acq_success"),
        ("script_acq_locked", "text_acq_locked"),
        ("script_acq_claimed", "text_acq_claimed"),
        ("script_acq_retry", "text_acq_retry"),
        ("script_acq_missing", "text_acq_missing"),
        ("script_acq_error", "text_acq_error"),
    ):
        _add_script(blob, label, _Script().msgbox(text_label).goto("script_acq_end"))
    _add_script(blob, "script_acq_end", _Script().emit(0x6C, 0x02, operation="release_end"))

    egg_hatch = (
        _Script()
        .emit(0x69, operation="lockall")
        .emit(0x0F, 0x00).word(0x081A5D79).emit(0x09, 0x04,
                                               operation="egg_hatch_message")
        .emit(0x25).half(0x00C2).emit(0x27, operation="egg_hatch_waitstate")
        .callnative(
            runtime_symbols["VegaAcq_RegisterHatchedPartyMon"],
            "VegaAcq_RegisterHatchedPartyMon",
        )
        .emit(0x6B, 0x02, operation="releaseall_end")
    )
    _add_script(blob, "script_acq_egg_hatch", egg_hatch)

    manifest = _read_json(root / PACKAGE / "generated/map_script_patch_manifest.json")
    hosts = manifest.get("hosts")
    if manifest.get("release_policy") != "READY_TO_SERIALIZE_OBJECT_REUSE_ONLY" or not isinstance(hosts, list):
        _fail("acquisition map patch manifest differs")
    if len(hosts) != 24:
        _fail(f"release host count differs: {len(hosts)}")
    map_rows = {row["map_key"]: row for row in _rows(root / "manifests/map_ids.csv")}
    source_locations, source_groups = _source_locations(root, clean)
    by_map: dict[tuple[int, int], list[dict[str, Any]]] = defaultdict(list)
    for host in hosts:
        by_map[(int(host["group_id"]), int(host["map_id"]))].append(host)

    host_meta: list[dict[str, Any]] = []
    map_meta: list[dict[str, Any]] = []
    for (group, map_id), map_hosts in sorted(by_map.items()):
        group_table = _pointer(
            stage,
            _rom_offset(EXPECTED_MAP_GROUPS_ROOT + group * 4),
            f"map group {group}",
        )
        map_header_address = _pointer(
            stage,
            _rom_offset(group_table + map_id * 4),
            f"map header {group}/{map_id}",
        )
        map_header_offset = _rom_offset(map_header_address, 0x1C)
        old_event_address = _pointer(stage, map_header_offset + 4, f"event header {group}/{map_id}")
        old_event_offset = _rom_offset(old_event_address, 0x14)
        old_event = bytearray(stage[old_event_offset:old_event_offset + 0x14])
        old_count = old_event[0]
        old_objects: list[bytearray] = []
        old_ids: set[int] = set()
        if old_count:
            old_objects_address = _pointer(stage, old_event_offset + 4, "existing object table")
            old_objects_offset = _rom_offset(old_objects_address, old_count * 0x18)
            for index in range(old_count):
                record = bytearray(stage[old_objects_offset + index * 0x18:old_objects_offset + (index + 1) * 0x18])
                local_id = record[0]
                if local_id == 0 or local_id in old_ids:
                    _fail(f"{group}/{map_id}: invalid existing local object id {local_id}")
                old_ids.add(local_id)
                old_objects.append(record)

        restored: list[tuple[dict[str, Any], bytearray, int]] = []
        used_ids = set(old_ids)
        for host in sorted(map_hosts, key=lambda row: (int(row["local_id"]), row["host_key"])):
            map_key = str(host["physical_map_key"])
            map_row = map_rows.get(map_key)
            if map_row is None or int(map_row["group_id"]) != group or int(map_row["map_id"]) != map_id:
                _fail(f"{host['host_key']}: map manifest binding differs")
            source_name = map_row["source_map"]
            _, source_header_offset = _source_header(
                clean, source_locations, source_groups, source_name,
            )
            source_event_address = _u32(clean, source_header_offset + 4, "clean event header")
            source_event_offset = _rom_offset(source_event_address, 0x14, limit=len(clean))
            source_count = clean[source_event_offset]
            if source_count != int(host["object_count"]):
                _fail(f"{host['host_key']}: clean object budget differs")
            source_objects_address = _u32(clean, source_event_offset + 4, "clean object table")
            source_objects_offset = _rom_offset(
                source_objects_address, source_count * 0x18, limit=len(clean),
            )
            requested_id = int(host["local_id"])
            matches = [
                source_objects_offset + index * 0x18
                for index in range(source_count)
                if clean[source_objects_offset + index * 0x18] == requested_id
            ]
            if len(matches) != 1:
                _fail(f"{host['host_key']}: clean source object is absent/ambiguous")
            record = bytearray(clean[matches[0]:matches[0] + 0x18])
            observed = (_u16(record, 4), _u16(record, 6), record[8])
            expected = (int(host["x"]), int(host["y"]), int(host["elevation"]))
            if observed != expected:
                _fail(f"{host['host_key']}: source coordinates differ {observed} != {expected}")
            assigned_id = requested_id
            if assigned_id in used_ids:
                assigned_id = next((value for value in range(1, 16) if value not in used_ids), 0)
            if assigned_id == 0:
                _fail(f"{host['host_key']}: no collision-free local id remains")
            used_ids.add(assigned_id)
            record[0] = assigned_id
            record[0x14:0x16] = b"\0\0"
            restored.append((host, record, assigned_id))

        final_count = len(old_objects) + len(restored)
        source_budget = max(int(host["object_count"]) for host in map_hosts)
        if final_count > source_budget or final_count > 15:
            _fail(f"{group}/{map_id}: restored object count {final_count} exceeds budget {source_budget}")

        all_objects = old_objects + [record for _, record, _ in restored]
        object_label = f"map_{group}_{map_id}_objects"
        object_raw = b"".join(bytes(record) for record in all_objects)
        object_relative = blob.add(object_label, object_raw, 4)
        for restored_index, (host, _, assigned_id) in enumerate(restored):
            record_index = len(old_objects) + restored_index
            script_label = f"host_script_{host['host_key']}"
            script = _host_script(runtime_symbols[str(host["wrapper_symbol"])], post_host)
            _add_script(blob, script_label, script)
            blob.pointer(object_relative + record_index * 0x18 + 0x10, script_label)
            host_meta.append({
                "host_key": host["host_key"],
                "physical_map_key": host["physical_map_key"],
                "group_id": group,
                "map_id": map_id,
                "requested_local_id": int(host["local_id"]),
                "local_id": assigned_id,
                "x": int(host["x"]),
                "y": int(host["y"]),
                "elevation": int(host["elevation"]),
                "source_object_budget": int(host["object_count"]),
                "wrapper_symbol": host["wrapper_symbol"],
                "wrapper_address": runtime_symbols[str(host["wrapper_symbol"])],
                "script_label": script_label,
                "script_size": len(script.data),
                "object_label": object_label,
                "object_record_relative": record_index * 0x18,
            })
        event_label = f"map_{group}_{map_id}_events"
        old_event[0] = final_count
        event_relative = blob.add(event_label, bytes(old_event), 4)
        blob.pointer(event_relative + 4, object_label)
        map_meta.append({
            "group_id": group,
            "map_id": map_id,
            "map_header_address": map_header_address,
            "map_event_pointer_patch_address": map_header_address + 4,
            "event_before_address": old_event_address,
            "event_label": event_label,
            "object_label": object_label,
            "object_count_before": old_count,
            "object_count_after": final_count,
            "source_object_budget": source_budget,
        })

    payload = blob.finish(payload_offset)
    base = GBA_ROM_BASE + payload_offset
    for row in host_meta:
        script_address = base + blob.labels[row.pop("script_label")]
        object_address = base + blob.labels[row["object_label"]] + int(row.pop("object_record_relative"))
        script_start = script_address - base
        script_size = int(row["script_size"])
        row.update({
            "object_record_address": object_address,
            "pointer_patch_address": object_address + 0x10,
            "script_after_address": script_address,
            "script_sha256": _sha(payload[script_start:script_start + script_size]),
        })
        row.pop("object_label")
    for row in map_meta:
        row["event_after_address"] = base + blob.labels[str(row.pop("event_label"))]
        row["object_table_address"] = base + blob.labels[str(row.pop("object_label"))]
    egg_script_address = base + blob.labels["script_acq_egg_hatch"]
    if len(host_meta) != 24 or len(map_meta) != 19:
        _fail(f"physical host/map counts differ: {len(host_meta)}/{len(map_meta)}")
    return payload, {
        "allocation_name": MAP_ALLOCATION,
        "address": base,
        "size": len(payload),
        "sha256": _sha(payload),
        "texts": text_meta,
        "patches": sorted(host_meta, key=lambda row: row["host_key"]),
        "maps": map_meta,
        "egg_hatch": {
            "original_script_address": GBA_ROM_BASE + EGG_HATCH_SCRIPT_SITE,
            "original_script_expected_hex": EGG_HATCH_SCRIPT_EXPECTED.hex(),
            "replacement_script_address": egg_script_address,
            "replacement_script_size": len(egg_hatch.data),
            "registration_hook_address": runtime_symbols[
                "VegaAcq_RegisterHatchedPartyMon"
            ],
            "operations": egg_hatch.operations,
            "script_sha256": _sha(
                payload[
                    egg_script_address - base:
                    egg_script_address - base + len(egg_hatch.data)
                ]
            ),
        },
        "restoration_policy": "T17で除去されたclean FireRed既存objectだけを復元し、script/flagを取得runtime向けに置換",
    }


def _patch_evolutions(root: Path, output: bytearray) -> dict[str, Any]:
    registry = {
        row["species_key"]: int(row["canonical_id"])
        for row in _rows(root / PACKAGE / "content/collectible_species_registry.csv")
    }
    catalog = _rows(root / PACKAGE / "content/trade_alternative_catalog_30.csv")
    if len(catalog) != 30:
        _fail(f"trade-alternative catalog count differs: {len(catalog)}")
    root_offset = _rom_offset(EVOLUTION_TABLE_ROOT, SPECIES_COUNT * EVOLUTION_SPECIES_STRIDE)
    routes: list[dict[str, Any]] = []
    mutation_spans: list[tuple[int, int]] = []
    for row in catalog:
        evolution_id = int(row["evolution_id"])
        from_key, to_key = SPECIAL_FORM_KEYS.get(
            evolution_id, (row["from_species_key"], row["to_species_key"]),
        )
        if from_key not in registry or to_key not in registry:
            _fail(f"trade route species key unresolved: {evolution_id}")
        source = registry[from_key]
        target = registry[to_key]
        requirement = row["required_held_item_or_partner"]
        held = HELD_ITEMS.get(requirement)
        expected = (
            (EVO_ITEM_HOLD_ITEM, LINK_CABLE_ITEM, target, held)
            if held is not None
            else (EVO_ITEM, LINK_CABLE_ITEM, target, 0)
        )
        slots = [
            struct.unpack_from("<HHHH", output, root_offset + source * EVOLUTION_SPECIES_STRIDE + slot * 8)
            for slot in range(EVOLUTION_SLOTS)
        ]
        existing = next((index for index, value in enumerate(slots) if value == expected), None)
        status = "EXISTING"
        before = expected
        if existing is None:
            replace = next(
                (index for index, value in enumerate(slots)
                 if value[0] == EVO_ITEM and value[2] == target),
                None,
            )
            if replace is None:
                replace = next((index for index, value in enumerate(slots) if value[0] == 0), None)
            if replace is None:
                _fail(f"evolution slots full for {from_key} ({source})")
            existing = replace
            before = slots[replace]
            address_offset = root_offset + source * EVOLUTION_SPECIES_STRIDE + replace * 8
            struct.pack_into("<HHHH", output, address_offset, *expected)
            mutation_spans.append((address_offset, address_offset + 8))
            status = "REPLACED" if before[0] else "ADDED"
        observed = struct.unpack_from(
            "<HHHH", output,
            root_offset + source * EVOLUTION_SPECIES_STRIDE + existing * 8,
        )
        if observed != expected:
            _fail(f"trade route verification failed: {evolution_id}")
        routes.append({
            "trade_alt_key": row["trade_alt_key"],
            "evolution_id": evolution_id,
            "from_species_key": from_key,
            "from_species_id": source,
            "to_species_key": to_key,
            "to_species_id": target,
            "slot": existing,
            "before": list(before),
            "after": list(expected),
            "status": status,
            "required_held_item": held,
        })
    if len({row["evolution_id"] for row in routes}) != 30:
        _fail("trade evolution ids are not unique")
    return {
        "status": "PASS",
        "table_root": EVOLUTION_TABLE_ROOT,
        "catalog_count": len(routes),
        "verified_route_count": len(routes),
        "mutation_count": sum(row["status"] != "EXISTING" for row in routes),
        "routes": routes,
        "mutation_spans": mutation_spans,
    }


def _wild_slots(raw: bytes | bytearray) -> list[dict[str, Any]]:
    kinds = {"LAND": (4, 12), "WATER": (8, 5), "ROCK_SMASH": (12, 5), "FISHING": (16, 10)}
    root = _rom_offset(EXPECTED_WILD_HEADERS_ROOT, (EXPECTED_WILD_HEADER_COUNT + 1) * 20)
    slots: list[dict[str, Any]] = []
    seen: set[tuple[int, int]] = set()
    for header_index in range(EXPECTED_WILD_HEADER_COUNT):
        header = root + header_index * 20
        group, map_id = raw[header], raw[header + 1]
        if (group, map_id) == (0xFF, 0xFF):
            _fail("wild header terminator appeared early")
        if (group, map_id) in seen and (group, map_id) != (0, 0):
            _fail(f"duplicate wild header map {group}/{map_id}")
        seen.add((group, map_id))
        for kind, (field, count) in kinds.items():
            info = _u32(raw, header + field, "wild info")
            if info == 0:
                continue
            info_offset = _rom_offset(info, 8)
            table = _u32(raw, info_offset + 4, "wild slots")
            table_offset = _rom_offset(table, count * 4)
            for slot in range(count):
                record = table_offset + slot * 4
                slots.append({
                    "map_group": group, "map_id": map_id,
                    "encounter_kind": kind, "slot_index": slot,
                    "species_id": _u16(raw, record + 2),
                    "species_offset": record + 2,
                })
    terminator = root + EXPECTED_WILD_HEADER_COUNT * 20
    if bytes(raw[terminator:terminator + 2]) != b"\xFF\xFF":
        _fail("wild header terminator/root differs")
    return slots


def _patch_wild(root: Path, output: bytearray) -> dict[str, Any]:
    internal = {
        int(row["canonical_id"])
        for row in _rows(root / PACKAGE / "content/internal_species_blocklist_25.csv")
    }
    rules = {
        (int(row["map_group"]), int(row["map_id"]), row["encounter_kind"], int(row["from_canonical_id"])): row
        for row in _rows(root / PACKAGE / "content/wild_source_corrections.csv")
    }
    before = [slot for slot in _wild_slots(output) if slot["species_id"] in internal]
    patches: list[dict[str, Any]] = []
    matches = {key: 0 for key in rules}
    for slot in before:
        key = (
            slot["map_group"], slot["map_id"], slot["encounter_kind"], slot["species_id"],
        )
        rule = rules.get(key)
        if rule is None:
            _fail(f"internal wild species lacks correction: {slot}")
        replacement = int(rule["to_canonical_id"])
        struct.pack_into("<H", output, slot["species_offset"], replacement)
        matches[key] += 1
        patches.append({
            "correction_key": rule["correction_key"],
            **slot,
            "from_canonical_id": slot["species_id"],
            "to_canonical_id": replacement,
            "address": GBA_ROM_BASE + slot["species_offset"],
        })
    if any(value == 0 for value in matches.values()):
        _fail("one or more wild corrections matched no exact slot")
    after = [slot for slot in _wild_slots(output) if slot["species_id"] in internal]
    if after:
        _fail(f"internal wild species remain: {after[:8]}")
    if len(patches) != 2:
        _fail(f"wild correction slot count differs: {len(patches)}")
    return {
        "status": "PASS", "header_root": EXPECTED_WILD_HEADERS_ROOT,
        "header_count": EXPECTED_WILD_HEADER_COUNT,
        "internal_slots_before": len(before), "internal_slots_after": len(after),
        "patches": patches,
    }


def _package_counts(root: Path) -> dict[str, Any]:
    completed = _run([
        sys.executable,
        str(root / PACKAGE / "scripts/validate_acquisition_content.py"),
        "--package", str(root / PACKAGE),
    ], "acquisition content validation")
    report = json.loads(completed)
    expected = {
        "status": "PASS", "events": 201, "release_hosts": 24,
        "exact_acceptance_cases": 2035, "reachable_required_or_enabling": 1216,
        "save_block_bytes": 240, "trade_edges": 30, "fossils": 16,
    }
    for key, value in expected.items():
        if report.get(key) != value:
            _fail(f"package validation {key} differs: {report.get(key)!r}")
    return report


def _ram_audit(root: Path) -> dict[str, Any]:
    rows = _rows(root / "config/ram_layout.csv")
    matches = [row for row in rows if row["owner"] == "USER_20260816_ACQUISITION_EVENTS"]
    if len(matches) != 1:
        _fail("acquisition volatile RAM reservation is not unique")
    row = matches[0]
    if (
        int(row["start"], 0) != 0x0203EC10
        or int(row["end_exclusive"], 0) != 0x0203ED30
        or row["persistence"] != "VOLATILE"
        or row["status"] != "LIVE"
    ):
        _fail("acquisition volatile RAM reservation differs")
    live = sorted(
        (int(item["start"], 0), int(item["end_exclusive"], 0), item["owner"])
        for item in rows
        if item["address_space"] == "EWRAM" and item["status"] == "LIVE"
    )
    overlap = [
        (left[2], right[2]) for left, right in zip(live, live[1:])
        if right[0] < left[1]
    ]
    if overlap:
        _fail(f"live EWRAM reservations overlap: {overlap}")
    return {
        "status": "PASS", "address": 0x0203EC10, "size": 288,
        "persistence": "VOLATILE", "flash_serialized": False,
        "layout_sha256": _sha((root / "config/ram_layout.csv").read_bytes()),
    }


def _exact_case_matrix(root: Path, output_sha: str) -> dict[str, Any]:
    cases = _rows(root / PACKAGE / "tests/exact_rom_acceptance_cases.csv")
    events = {
        row["event_key"]: row
        for row in _rows(root / PACKAGE / "content/acquisition_events.csv")
    }
    hosts = {
        row["host_key"]
        for row in _rows(root / PACKAGE / "content/acquisition_physical_hosts.csv")
        if row["status"] == "READY_TO_SERIALIZE"
    }
    scenarios = {
        "LOCKED", "CANCEL", "RESET_PREPARED", "SUCCESS", "REPEAT_AFTER_SUCCESS",
        "PARTY_FULL", "ALL_STORAGE_FULL", "SAVE_FAILURE", "DEFEAT", "ESCAPE",
        "RESET_CAPTURE", "HATCH", "INVALID_PARTY_SELECTION", "MISSING_INPUT",
        "REPEAT_SERVICE",
    }
    failed: list[str] = []
    seen: set[str] = set()
    for case in cases:
        key = case["case_key"]
        event = events.get(case["event_key"])
        if (
            key in seen
            or event is None
            or case["host_key"] not in hosts
            or case["scenario"] not in scenarios
            or event["battle_or_gift"] != case["mode"]
            or event["host_key"] != case["host_key"]
            or event["unlock_key"] != case["unlock_key"]
            or case["release_required"] != "yes"
        ):
            failed.append(key)
        seen.add(key)
    if len(cases) != 2035 or failed:
        _fail(f"exact acceptance matrix differs: count={len(cases)} failed={failed[:8]}")
    return {
        "schema_version": 1,
        "status": "PASS",
        "rom_sha256": output_sha,
        "case_count": len(cases),
        "case_key_sha256": _sha("\n".join(sorted(seen)).encode()),
        "validation_layer": "2,035-case static/native matrix + all 7 modes representative exact-ROM mGBA gate",
        "scenarios": sorted({case["scenario"] for case in cases}),
    }


def _tool_identity(root: Path) -> dict[str, str]:
    compiler = shutil.which(os.environ.get("CC", "cc"))
    if not compiler:
        _fail("C compiler missing for acquisition mGBA fixture")
    version = _run([compiler, "--version"], "C compiler version").splitlines()[0]
    pkg_config = shutil.which("pkg-config")
    libmgba = "linker:-lmgba"
    if pkg_config:
        probe = subprocess.run(
            [pkg_config, "--modversion", "mgba"], cwd=root, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False,
        )
        if probe.returncode == 0 and probe.stdout.strip():
            libmgba = probe.stdout.strip()
    return {"cc": compiler, "cc_version": version, "libmgba": libmgba}


def _mgba_selected(
    root: Path, runtime: dict[str, Any], map_runtime: dict[str, Any],
    evolution: dict[str, Any], wild: dict[str, Any],
) -> dict[str, int]:
    symbols = runtime["symbols"]
    linked = runtime["linked_abi"]
    host = map_runtime["patches"][0]
    map_row = next(
        row for row in map_runtime["maps"]
        if row["group_id"] == host["group_id"] and row["map_id"] == host["map_id"]
    )
    pure = next(row for row in evolution["routes"] if row["after"][0] == EVO_ITEM)
    held = next(
        row for row in evolution["routes"]
        if row["after"][0] == EVO_ITEM_HOLD_ITEM
    )
    wild_rows = wild["patches"]
    if len(wild_rows) != 2:
        _fail("representative acquisition wild fixtures differ")
    event_rows = _rows(root / PACKAGE / "content/acquisition_events.csv")
    registry = {
        row["species_key"]: int(row["canonical_id"])
        for row in _rows(
            root / PACKAGE / "content/collectible_species_registry.csv"
        )
    }
    egg_event = event_rows[30]
    if egg_event["battle_or_gift"] != "EGG":
        _fail("representative egg event index differs")
    return {
        "probe": symbols["VegaAcq_Probe"],
        "adapter_probe": symbols["VegaAcqAdapter_Probe"],
        "begin": symbols["VegaAcq_Begin"],
        "resolve": symbols["VegaAcq_ResolveBattle"],
        "recover": symbols["VegaAcq_RecoverPending"],
        "hatch_register": symbols["VegaAcq_RegisterHatchedPartyMon"],
        "is_registered": symbols["VegaAcqEngine_IsSpeciesRegistered"],
        "save_init": symbols["VegaSaveInitNew"],
        "save_finalize": symbols["VegaSaveFinalize"],
        "save_validate": symbols["VegaSaveValidate"],
        "inner_init": symbols["VegaAcqSaveInitialize"],
        "inner_finalize": symbols["VegaAcqSaveFinalize"],
        "inner_validate": symbols["VegaAcqSaveValidate"],
        "save_load": SAVE_LOAD_GAME_DATA,
        "get_boxed_mon_ptr": linked["GetBoxedMonPtr"],
        "get_box_mon_data": linked["GetBoxMonDataAt"],
        "get_compressed_mon_ptr": linked["GetCompressedMonPtr"],
        "create_compressed_mon": linked["CreateCompressedMonFromBoxMon"],
        "validator_site": GBA_ROM_BASE + VALIDATOR_SITE,
        "map_header": int(map_row["map_header_address"]),
        "event_header": int(map_row["event_after_address"]),
        "object_record": int(host["object_record_address"]),
        "host_script": int(host["script_after_address"]),
        "host_wrapper": int(host["wrapper_address"]),
        "egg_script_site": GBA_ROM_BASE + EGG_HATCH_SCRIPT_SITE,
        "egg_script_runtime": int(
            map_runtime["egg_hatch"]["replacement_script_address"]
        ),
        "egg_species": registry[egg_event["target_species_keys"]],
        "evo_pure": EVOLUTION_TABLE_ROOT
        + int(pure["from_species_id"]) * EVOLUTION_SPECIES_STRIDE
        + int(pure["slot"]) * EVOLUTION_ROW_SIZE,
        "evo_pure_target": int(pure["to_species_id"]),
        "evo_held": EVOLUTION_TABLE_ROOT
        + int(held["from_species_id"]) * EVOLUTION_SPECIES_STRIDE
        + int(held["slot"]) * EVOLUTION_ROW_SIZE,
        "evo_held_target": int(held["to_species_id"]),
        "evo_held_item": int(held["required_held_item"]),
        "wild_a": int(wild_rows[0]["address"]),
        "wild_b": int(wild_rows[1]["address"]),
    }


def _runner_cache_key(
    root: Path, rom_sha256: str, selected: dict[str, int],
) -> tuple[str, dict[str, Any]]:
    sources = (RUNNER, *EMBEDDED_RUNNER_SOURCES)
    provenance = {
        "schema_version": 1,
        "rom_sha256": rom_sha256,
        "sources": {
            path.as_posix(): _sha((root / path).read_bytes()) for path in sources
        },
        "toolchain": _tool_identity(root),
        "arguments": selected,
    }
    return _sha(_stable(provenance)), provenance


def _validate_mgba_fixture(value: dict[str, Any], rom_sha256: str) -> None:
    save = value.get("save", {})
    modes = value.get("modes", {})
    transactions = value.get("transactions", {})
    tables = value.get("rom_tables", {})
    if (
        value.get("status") != "PASS"
        or value.get("fixture") != "acquisition_runtime_v1"
        or value.get("rom_sha256") != rom_sha256
        or value.get("warnings_errors") != 0
        or not value.get("read_only_host")
        or not value.get("physical_host_chain")
        or not value.get("egg_hatch_hook")
        or value.get("artifacts_written") != []
        or not all(save.get(key) for key in (
            "legacy_zero_inner", "nested_crc_rejection",
            "migration_persisted", "save_sector_round_trip",
            "standard_party_round_trip",
        ))
        or not all(modes.get(key) for key in (
            "capture", "gift", "egg", "fossil", "evolution_support",
            "trade_emulator", "service", "egg_hatch_registration",
        ))
        or not all(transactions.get(key) for key in (
            "locked", "reset_retry", "success", "duplicate_guard",
            "repeatable_service", "party_full_routes_to_pc",
            "all_storage_full_rejected",
        ))
        or not tables.get("evolution_routes")
        or not tables.get("wild_corrections")
    ):
        _fail("acquisition exact-ROM mGBA fixture differs")


def _mgba_fixture(
    root: Path, rom: bytes, runtime: dict[str, Any],
    map_runtime: dict[str, Any], evolution: dict[str, Any], wild: dict[str, Any],
) -> dict[str, Any]:
    selected = _mgba_selected(root, runtime, map_runtime, evolution, wild)
    rom_sha256 = _sha(rom)
    key, provenance = _runner_cache_key(root, rom_sha256, selected)
    cache = root / MGBA_FIXTURE
    if cache.is_file():
        value = _read_json(cache)
        if value.get("cache", {}).get("key") == key:
            _validate_mgba_fixture(value, rom_sha256)
            return value
    with tempfile.TemporaryDirectory(prefix="vega-acquisition-mgba-") as raw:
        directory = Path(raw)
        rom_path = directory / STAGE26.name
        executable = directory / "mgba-acquisition-smoke"
        rom_path.write_bytes(rom)
        _run([
            os.environ.get("CC", "cc"), "-std=c11", "-O2", "-Wall",
            "-Wextra", "-Werror", str(root / RUNNER),
            "-o", str(executable), "-lmgba",
        ], "acquisition libmGBA runner compile", cwd=root)
        args = [str(executable), str(rom_path), rom_sha256]
        args.extend(f"{name}={address}" for name, address in selected.items())
        first = json.loads(_run(args, "acquisition exact-ROM run 1", cwd=root))
        second = json.loads(_run(args, "acquisition exact-ROM run 2", cwd=root))
        if first != second:
            _fail("acquisition exact-ROM fixture is not process deterministic")
        first["process_runs"] = 2
        first["cache"] = {"key": key, "provenance": provenance}
        _validate_mgba_fixture(first, rom_sha256)
        return first


def build_outputs(root: Path = ROOT) -> dict[str, bytes]:
    root = Path(root)
    stage, stage_meta, clean, pin = _input_audit(root)
    package_counts = _package_counts(root)
    linked = _linked_symbols(root)
    preliminary_runtime, preliminary_symbols = _compile_runtime(root, 0x09200000, linked)
    preliminary_map, _ = _build_map_payload(
        root, stage, clean, preliminary_symbols, 0,
    )
    runtime_allocation, map_allocation, _ = _allocation(
        root, len(preliminary_runtime), "0" * 64, len(preliminary_map), "0" * 64,
    )
    runtime_offset = int(runtime_allocation["start"])
    map_offset = int(map_allocation["start"])
    runtime, symbols = _compile_runtime(root, GBA_ROM_BASE + runtime_offset, linked)
    map_payload, map_runtime = _build_map_payload(
        root, stage, clean, symbols, map_offset,
    )
    if len(runtime) != len(preliminary_runtime) or len(map_payload) != len(preliminary_map):
        _fail("address-dependent acquisition payload size changed")
    runtime_allocation, map_allocation, allocation_report = _allocation(
        root, len(runtime), _sha(runtime), len(map_payload), _sha(map_payload),
    )
    if int(runtime_allocation["start"]) != runtime_offset or int(map_allocation["start"]) != map_offset:
        _fail("acquisition allocation moved after final link")
    if stage[runtime_offset:runtime_offset + len(runtime)] != b"\xFF" * len(runtime):
        _fail("acquisition runtime destination is not erased FF")
    if stage[map_offset:map_offset + len(map_payload)] != b"\xFF" * len(map_payload):
        _fail("acquisition map destination is not erased FF")

    output = bytearray(stage)
    output[runtime_offset:runtime_offset + len(runtime)] = runtime
    output[map_offset:map_offset + len(map_payload)] = map_payload
    allowed = [
        (runtime_offset, runtime_offset + len(runtime)),
        (map_offset, map_offset + len(map_payload)),
    ]
    map_pointer_patches: list[dict[str, Any]] = []
    for row in map_runtime["maps"]:
        site = _rom_offset(int(row["map_event_pointer_patch_address"]), 4)
        expected = int(row["event_before_address"])
        observed = _u32(output, site, "map event pointer before")
        if observed != expected:
            _fail(f"map event pointer drift at {row['group_id']}/{row['map_id']}")
        replacement = int(row["event_after_address"])
        struct.pack_into("<I", output, site, replacement)
        allowed.append((site, site + 4))
        map_pointer_patches.append({
            "label": f"acquisition event header {row['group_id']}/{row['map_id']}",
            "offset": site, "address": GBA_ROM_BASE + site,
            "expected_pointer": expected, "replacement_pointer": replacement,
        })

    egg_hatch_target = int(
        map_runtime["egg_hatch"]["replacement_script_address"]
    )
    egg_hatch_replacement = b"\x05" + struct.pack("<I", egg_hatch_target)
    if (
        output[EGG_HATCH_SCRIPT_SITE:
               EGG_HATCH_SCRIPT_SITE + len(EGG_HATCH_SCRIPT_EXPECTED)]
        != EGG_HATCH_SCRIPT_EXPECTED
    ):
        _fail("egg-hatch script signature changed during build")
    output[EGG_HATCH_SCRIPT_SITE:
           EGG_HATCH_SCRIPT_SITE + len(egg_hatch_replacement)] = (
        egg_hatch_replacement
    )
    allowed.append((
        EGG_HATCH_SCRIPT_SITE,
        EGG_HATCH_SCRIPT_SITE + len(egg_hatch_replacement),
    ))
    egg_hatch_patch = {
        **map_runtime["egg_hatch"],
        "site": GBA_ROM_BASE + EGG_HATCH_SCRIPT_SITE,
        "replacement_hex": egg_hatch_replacement.hex(),
    }

    validator_target = symbols["VegaSaveValidate"] | 1
    validator_replacement = b"\x00\x4B\x18\x47" + struct.pack("<I", validator_target)
    if output[VALIDATOR_SITE:VALIDATOR_SITE + 8] != VALIDATOR_EXPECTED:
        _fail("save validator trampoline signature changed during build")
    output[VALIDATOR_SITE:VALIDATOR_SITE + 8] = validator_replacement
    allowed.append((VALIDATOR_SITE, VALIDATOR_SITE + 8))

    evolution = _patch_evolutions(root, output)
    allowed += [tuple(span) for span in evolution.pop("mutation_spans")]
    wild = _patch_wild(root, output)
    allowed += [
        (_rom_offset(int(row["address"]), 2), _rom_offset(int(row["address"]), 2) + 2)
        for row in wild["patches"]
    ]

    outside: list[int] = []
    for index, (before, after) in enumerate(zip(stage, output)):
        if before != after and not any(start <= index < end for start, end in allowed):
            outside.append(index)
            if len(outside) == 8:
                break
    if outside:
        _fail(f"stage 26 changed bytes outside declared spans: {outside}")

    output_raw = bytes(output)
    output_sha = _sha(output_raw)
    patch = create_bps(clean, output_raw)
    if apply_bps(clean, patch) != output_raw:
        _fail("clean ROM to stage 26 BPS round-trip differs")
    exact = _exact_case_matrix(root, output_sha)
    runtime_meta = {
        "allocation_name": RUNTIME_ALLOCATION,
        "address": GBA_ROM_BASE + runtime_offset,
        "size": len(runtime),
        "payload_size": len(runtime),
        "payload_sha256": _sha(runtime),
        "symbols": {name: symbols[name] for name in sorted(symbols) if name.startswith("Vega")},
        "wrapper_symbol_count": sum(name.startswith("VegaAcqHost_") for name in symbols),
        "linked_abi": linked,
    }
    map_runtime.update({
        "allocation_address": GBA_ROM_BASE + map_offset,
        "allocation_size": len(map_payload),
        "allocation_used": len(map_payload),
    })
    ram = _ram_audit(root)
    fixture = _mgba_fixture(
        root, output_raw, runtime_meta, map_runtime, evolution, wild,
    )
    metadata = {
        "schema_version": 1,
        "task": TASK,
        "status": "PASS",
        "input": {"path": STAGE25.as_posix(), "size": len(stage), "sha256": _sha(stage)},
        "input_sha256": _sha(stage),
        "output": {"path": STAGE26.as_posix(), "size": len(output_raw), "sha256": output_sha},
        "output_sha256": output_sha,
        "runtime": runtime_meta,
        "map_scripts": map_runtime,
        "map_pointer_patches": map_pointer_patches,
        "egg_hatch_patch": egg_hatch_patch,
        "save_validator": {
            "site": GBA_ROM_BASE + VALIDATOR_SITE,
            "expected_hex": VALIDATOR_EXPECTED.hex(),
            "replacement_hex": validator_replacement.hex(),
            "target": validator_target,
            "nested_acquisition_bytes": 240,
            "alignment_prefix_bytes": 3,
            "remaining_reserved_bytes": 15,
        },
        "evolution_routes": {
            key: value for key, value in evolution.items() if key != "routes"
        },
        "wild_sanitization": wild,
        "package_validation": package_counts,
        "exact_case_matrix": exact,
        "exact_rom_fixture": {
            "path": MGBA_FIXTURE.as_posix(),
            "status": fixture["status"],
            "process_runs": fixture["process_runs"],
            "cache_key": fixture["cache"]["key"],
            "all_modes": all(fixture["modes"].values()),
            "save_sector_round_trip": fixture["save"]["save_sector_round_trip"],
            "all_storage_full_rejected": fixture["transactions"][
                "all_storage_full_rejected"
            ],
            "egg_hatch_registration": fixture["modes"][
                "egg_hatch_registration"
            ],
            "standard_party_round_trip": fixture["save"][
                "standard_party_round_trip"
            ],
        },
        "ram_audit": ram,
        "allocation": {
            "path": STAGE26_ALLOCATION.as_posix(),
            "overlap_count": allocation_report["summaries"]["overlap_count"],
            "remaining_allocatable_bytes": allocation_report["summaries"]["remaining_allocatable_bytes"],
        },
        "release_patch_round_trip": {
            "format": "BPS1", "exact": True,
            "source_sha256": _sha(clean), "target_sha256": output_sha,
            "patch_size": len(patch), "patch_sha256": _sha(patch),
        },
        "invariants": {
            "stage25_hash_pinned": True,
            "allocator_overlap_zero": True,
            "declared_changes_only": True,
            "rom_size_32_mib": True,
            "host_count_24": True,
            "event_count_201": True,
            "exact_case_count_2035": True,
            "trade_route_count_30": True,
            "internal_wild_species_zero": True,
            "release_patch_exact": True,
            "exact_rom_process_runs_2": fixture["process_runs"] == 2,
            "all_storage_full_no_mutation": fixture["transactions"][
                "all_storage_full_rejected"
            ],
            "egg_registers_on_hatch": fixture["modes"][
                "egg_hatch_registration"
            ],
            "party_pc_standard_save_durable": fixture["save"][
                "standard_party_round_trip"
            ],
        },
        "source_pin": pin,
        "upstream_metadata_task": stage_meta.get("task"),
    }
    symbol_doc = {
        "schema_version": 1,
        "allocation_name": RUNTIME_ALLOCATION,
        "base_address": GBA_ROM_BASE + runtime_offset,
        "payload_sha256": _sha(runtime),
        "symbols": {name: symbols[name] for name in sorted(symbols) if name.startswith("Vega")},
    }
    map_symbol_doc = {
        "schema_version": 1,
        "allocation_name": MAP_ALLOCATION,
        "base_address": GBA_ROM_BASE + map_offset,
        "payload_sha256": _sha(map_payload),
        "hosts": map_runtime["patches"],
        "maps": map_runtime["maps"],
        "egg_hatch": map_runtime["egg_hatch"],
    }
    evolution_doc = {
        "schema_version": 1,
        "task": TASK,
        **evolution,
        "stage_sha256": output_sha,
    }
    report = f"""# ポケモン取得方法・イベント統合レポート

- Status: PASS
- Task: `{TASK}`
- Input: stage 25 `{_sha(stage)}`
- Output: stage 26 `{output_sha}`
- 取得イベント: 201件 / 物理ホスト: 24件（19マップ）
- 図鑑完成対象: 1,206種 + 必須フォーム10種
- exact受入ケース: 2,035件（定義・event/host/runtime binding PASS）
- mGBA exact-ROM: 7方式 / 孵化時登録 / 通常save再読込 / party→PC / 全収納満杯を独立2 processでPASS
- 単独ROM交換進化: 30経路（ROM table exact audit PASS）
- 化石復元: 16経路 + 採掘補助
- 内部互換Species野生残存: 0（2 slotをScytherへ補正）
- 取得save block: 240 byte（既存2,048 byte save ABI内、旧offset維持）
- allocator overlap: 0
- BPS clean round-trip: PASS

Kantoの対象NPCは新規物体を増設せず、T17で除去済みだったclean FireRed既存objectのうち
パッケージが指定した24件だけを復元しました。現在のKanto配置を保持し、各マップの元object
budgetおよびGen3の15-object上限以内であることをビルド時に検証します。
""".encode()
    return {
        STAGE26.as_posix(): output_raw,
        STAGE26_META.as_posix(): _stable(metadata),
        STAGE26_ALLOCATION.as_posix(): _stable(allocation_report),
        RUNTIME_BIN.as_posix(): runtime,
        RUNTIME_SYMBOLS.as_posix(): _stable(symbol_doc),
        MAP_BIN.as_posix(): map_payload,
        MAP_SYMBOLS.as_posix(): _stable(map_symbol_doc),
        EVOLUTION_REPORT.as_posix(): _stable(evolution_doc),
        EXACT_CASES.as_posix(): _stable(exact),
        MGBA_FIXTURE.as_posix(): _stable(fixture),
        REPORT.as_posix(): report,
        PATCH.as_posix(): patch,
    }


def _write_outputs(root: Path, outputs: dict[str, bytes]) -> None:
    for relative, raw in outputs.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
            stream.write(raw)
            temporary = Path(stream.name)
        os.replace(temporary, path)


def _check_outputs(root: Path, outputs: dict[str, bytes]) -> None:
    differences = [
        relative for relative, expected in outputs.items()
        if not (root / relative).is_file() or (root / relative).read_bytes() != expected
    ]
    if differences:
        _fail("acquisition generated outputs differ: " + ", ".join(differences))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("build", "check"))
    args = parser.parse_args()
    try:
        outputs = build_outputs(ROOT)
        if args.mode == "build":
            _write_outputs(ROOT, outputs)
        else:
            _check_outputs(ROOT, outputs)
    except (OSError, ValueError, KeyError, json.JSONDecodeError, AcquisitionBuildError) as error:
        print(f"acquisition event build failed: {error}", file=sys.stderr)
        return 1
    print(
        f"acquisition events {args.mode}: PASS "
        f"stage={_sha(outputs[STAGE26.as_posix()])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
