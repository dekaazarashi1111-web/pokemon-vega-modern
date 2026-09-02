#!/usr/bin/env python3
"""Stage 26へFactory BPショップのmanifest catalogと物理NPCを統合する。"""

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
from dataclasses import dataclass
from pathlib import Path
from typing import Any, NoReturn, Sequence


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.regression.rom_runtime import _Blob, _charmap, _encode_text  # noqa: E402
from tools.release.bps import apply_bps, create_bps  # noqa: E402
from tools.rom_allocator import GBA_ROM_BASE, build_allocation_report_from_csv  # noqa: E402


TASK = "USER-20260817-BP-SHOP-RUNTIME"
ROM_SIZE = 32 * 1024 * 1024
INPUT_ROM = Path("build/stages/26_acquisition_events.gba")
INPUT_META = Path("build/stages/26_acquisition_events.json")
INPUT_ALLOC = Path("build/stages/26_allocation.json")
STAGE17_META = Path("build/stages/17_regression.json")
OUTPUT_ROM = Path("build/stages/27_bp_shop_runtime.gba")
OUTPUT_META = Path("build/stages/27_bp_shop_runtime.json")
OUTPUT_ALLOC = Path("build/stages/27_allocation.json")
RUNTIME_BIN = Path("generated/runtime/bp_shop_runtime.bin")
RUNTIME_SYMBOLS = Path("generated/runtime/bp_shop_runtime_symbols.json")
CATALOG_HEADER = Path("generated/runtime/bp_shop_catalog_generated.h")
CATALOG_JSON = Path("generated/runtime/bp_shop_catalog.json")
MGBA_FIXTURE = Path("build/stages/27_mgba_bp_shop_smoke.json")
REPORT = Path("reports/generated/bp_shop_runtime.md")
PATCH = Path("build/patches/vega-modern-kanto-v1.4.0-to-bp-shop-stage27.bps")
RUNNER = Path("tools/mgba_bp_shop_smoke.c")

EXPECTED_INPUT_SHA256 = "5a4d1b68c619be291f35a201ada97d6a7921ff89d4d48cc3b3396f04195db2ea"
MAP_GROUPS_POINTER_SITE = 0x00054B0C
GBA_ENTRY = (96, 5)
PAYLOAD_HEADER_SIZE = 0x80
ALLOCATION_NAME = "bp_shop_runtime_payload"
CATALOG_COUNT = 18
VOLATILE_RAM_START = 0x0203ED40
VOLATILE_RAM_END = 0x0203EDC0

REQUIRED_ENTRYPOINTS = {
    "BpShop_Probe",
    "BpShop_EnsureSave",
    "BpShop_GetBalance",
    "BpShop_IsItemUnlocked",
    "BpShop_PurchaseByIndex",
    "BpShop_PurchaseSelected",
    "BpShop_Open",
    "BpShop_PostMenu",
}
REQUIRED_LINKED_SYMBOLS = REQUIRED_ENTRYPOINTS | {"VegaSaveFinalize"}

UNLOCK_ENUM = {
    "VEGA_DH_CLEAR": "BP_UNLOCK_DH_CLEAR",
    "KANTO_EARLY_ACCESS": "BP_UNLOCK_KANTO_EARLY_ACCESS",
    "VEGA_BADGE_1": "BP_UNLOCK_BADGE_1",
    "KANTO_DAYCARE_QUEST": "BP_UNLOCK_KANTO_DAYCARE_QUEST",
    "VEGA_BADGE_5": "BP_UNLOCK_BADGE_5",
    "VEGA_BADGE_6": "BP_UNLOCK_BADGE_6",
    "COMPETITIVE_SUPPLY_UNLOCKED": "BP_UNLOCK_COMPETITIVE_SUPPLY",
    "VEGA_BADGE_7": "BP_UNLOCK_BADGE_7",
    "VEGA_BADGE_8": "BP_UNLOCK_BADGE_8",
    "KANTO_LEAGUE_CLEAR": "BP_UNLOCK_KANTO_LEAGUE_CLEAR",
    "UB_PARADOX_UNLOCKED": "BP_UNLOCK_UB_PARADOX",
}

UNLOCK_RUNTIME_SIGNAL = {
    "VEGA_DH_CLEAR": "Flag 0x114B",
    "KANTO_EARLY_ACCESS": "kanto_travel_unlocked || Hall of Fame || (flags 0x0824 && 0x114B)",
    "VEGA_BADGE_1": "Flag 0x0820",
    "KANTO_DAYCARE_QUEST": "Kanto access && kanto_visited",
    "VEGA_BADGE_5": "Flag 0x0824",
    "VEGA_BADGE_6": "Flag 0x0825",
    "COMPETITIVE_SUPPLY_UNLOCKED": "Hall of Fame && popcount(kanto_certifications) >= 4",
    "VEGA_BADGE_7": "Flag 0x0826",
    "VEGA_BADGE_8": "Flag 0x0827",
    "KANTO_LEAGUE_CLEAR": "league_ii_cleared",
    "UB_PARADOX_UNLOCKED": "league_ii_cleared",
}

TEXTS = {
    "text_bp_shop_success": "こうにゅうしました！",
    "text_bp_shop_locked": "まだ こうにゅうできません",
    "text_bp_shop_persist": "セーブに しっぱいしました",
    "text_bp_shop_insufficient": "BPが たりません",
    "text_bp_shop_full": "もちものが いっぱいです",
    "text_bp_shop_error": "こうにゅうできませんでした",
}


class BpShopBuildError(ValueError):
    """入力、manifest、ROM ABI、配置、または受入条件の違反。"""


def _fail(message: str) -> NoReturn:
    raise BpShopBuildError(message)


def _sha(raw: bytes | bytearray) -> str:
    return hashlib.sha256(raw).hexdigest()


def _stable(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        _fail(f"JSON root is not an object: {path}")
    return value


def _run(command: Sequence[str], label: str, *, cwd: Path = ROOT) -> str:
    completed = subprocess.run(
        list(command), cwd=cwd, text=True, capture_output=True, check=False,
    )
    if completed.returncode:
        detail = (completed.stderr or completed.stdout).strip()
        _fail(f"{label} failed ({completed.returncode}): {detail}")
    return completed.stdout.strip()


def _u16(raw: bytes | bytearray, offset: int, label: str) -> int:
    if offset < 0 or offset + 2 > len(raw):
        _fail(f"{label}: offset outside ROM: 0x{offset:X}")
    return struct.unpack_from("<H", raw, offset)[0]


def _u32(raw: bytes | bytearray, offset: int, label: str) -> int:
    if offset < 0 or offset + 4 > len(raw):
        _fail(f"{label}: offset outside ROM: 0x{offset:X}")
    return struct.unpack_from("<I", raw, offset)[0]


def _rom_offset(address: int, size: int, label: str, *, limit: int = ROM_SIZE) -> int:
    address &= ~1
    offset = address - GBA_ROM_BASE
    if offset < 0 or offset + size > limit:
        _fail(f"{label}: ROM address outside image: 0x{address:08X}+{size}")
    return offset


def _input_contract(root: Path) -> tuple[bytes, dict[str, Any], dict[str, Any], dict[str, Any]]:
    stage = (root / INPUT_ROM).read_bytes()
    stage_meta = _read_json(root / INPUT_META)
    allocation = _read_json(root / INPUT_ALLOC)
    stage17 = _read_json(root / STAGE17_META)
    if len(stage) != ROM_SIZE or _sha(stage) != EXPECTED_INPUT_SHA256:
        _fail("v1.4.0 final/stage26 input size or hash differs")
    if stage_meta.get("output", {}).get("sha256") != EXPECTED_INPUT_SHA256:
        _fail("stage26 metadata output hash differs from v1.4.0 final input")
    if allocation.get("summaries", {}).get("overlap_count") != 0:
        _fail("stage26 allocator overlap contract failed")
    map_root = int(stage17.get("symbols", {}).get("map_groups_root", 0))
    if _u32(stage, MAP_GROUPS_POINTER_SITE, "gMapGroups site") != map_root:
        _fail("stage26 map group root differs from stage17 symbol")
    return stage, stage_meta, allocation, stage17


def _c_bytes(name: str, raw: bytes, *, suffix: str = "") -> str:
    lines: list[str] = []
    for start in range(0, len(raw), 12):
        chunk = raw[start:start + 12]
        lines.append("    " + ", ".join(f"0x{value:02X}u" for value in chunk) + ",")
    body = "\n".join(lines)
    declarator = suffix or "[]"
    return f"static const u8 {name}{declarator} = {{\n{body}\n}};\n"


def _catalog_outputs(root: Path) -> tuple[list[dict[str, Any]], bytes, bytes]:
    rewards = [
        row for row in _rows(root / "manifests/qol_rewards.csv")
        if row.get("source_kind") == "BP_SHOP" and row.get("status") == "ACTIVE"
    ]
    if len(rewards) != CATALOG_COUNT:
        _fail(f"ACTIVE BP_SHOP catalog count differs: {len(rewards)}")
    item_rows = {
        row["item_key"]: row for row in _rows(root / "manifests/item_ids.csv")
    }
    mapping, tokens = _charmap(root)
    catalog: list[dict[str, Any]] = []
    seen_items: set[int] = set()
    header: list[str] = [
        "#ifndef VEGA_BP_SHOP_CATALOG_GENERATED_H",
        "#define VEGA_BP_SHOP_CATALOG_GENERATED_H",
        "",
        f"#define BP_SHOP_CATALOG_COUNT {CATALOG_COUNT}u",
        "",
    ]
    rows_c: list[str] = []
    entries_c: list[str] = []
    for index, reward in enumerate(rewards):
        item_key = reward.get("item_key", "")
        item = item_rows.get(item_key)
        if item is None:
            _fail(f"BP shop item_key is unresolved: {item_key}")
        if (
            reward.get("currency_key") != "CURRENCY_KEY_BP"
            or reward.get("quantity") != "1"
            or reward.get("repeatability") not in {"REPEATABLE", "LIMITED_REPEATABLE"}
            or reward.get("claim_key") != "NONE"
        ):
            _fail(f"BP shop reward contract differs: {reward.get('reward_key')}")
        unlock_key = reward.get("unlock_key", "")
        if unlock_key not in UNLOCK_ENUM:
            _fail(f"BP shop unlock is not physically mapped: {unlock_key}")
        item_id = int(item["id"])
        price = int(reward["price"])
        quantity = int(reward["quantity"])
        if not 1 <= item_id <= 999 or item_id in seen_items:
            _fail(f"BP shop item id is invalid/duplicate: {item_id}")
        if item.get("pocket") != "POCKET_ITEMS" or price <= 0 or price > 9999:
            _fail(f"BP shop item pocket/price differs: {item_key}")
        seen_items.add(item_id)
        display_name = item["display_name"]
        row_text = f"{display_name} {price}BP"
        encoded = _encode_text(row_text, mapping, tokens)
        if len(encoded) > 22:
            _fail(f"BP shop menu row is too wide ({len(encoded) - 1}): {row_text}")
        row_symbol = f"gBpShopRow{index:02d}"
        rows_c.append(_c_bytes(row_symbol, encoded))
        entries_c.append(
            "    {"
            f"{item_id}u, {price}u, {UNLOCK_ENUM[unlock_key]}, {quantity}u, "
            f"{row_symbol}" "},"
        )
        catalog.append({
            "index": index,
            "reward_key": reward["reward_key"],
            "item_key": item_key,
            "item_id": item_id,
            "display_name": display_name,
            "quantity": quantity,
            "price_bp": price,
            "unlock_key": unlock_key,
            "runtime_unlock_signal": UNLOCK_RUNTIME_SIGNAL[unlock_key],
            "repeatability": reward["repeatability"],
            "row_text": row_text,
            "row_text_hex": encoded.hex(),
        })
    prefix = _encode_text("BP ", mapping, tokens)
    digits = _encode_text("0123456789", mapping, tokens)[:-1]
    if len(digits) != 10:
        _fail("game font digit encoding differs")
    next_text = _encode_text("つぎ", mapping, tokens)
    cancel_text = _encode_text("やめる", mapping, tokens)
    header.extend(rows_c)
    header.append(_c_bytes("gBpShopBalancePrefix", prefix))
    header.append(_c_bytes("gBpShopDigitGlyphs", digits, suffix="[10]"))
    header.append(_c_bytes("gBpShopTextNext", next_text))
    header.append(_c_bytes("gBpShopTextCancel", cancel_text))
    header.extend([
        "static const BpShopCatalogEntry gBpShopCatalog[BP_SHOP_CATALOG_COUNT] = {",
        *entries_c,
        "};",
        "",
        "#endif /* VEGA_BP_SHOP_CATALOG_GENERATED_H */",
        "",
    ])
    header_raw = "\n".join(header).encode("ascii")
    document = {
        "schema_version": 1,
        "task": TASK,
        "status": "PASS",
        "source": ["manifests/qol_rewards.csv", "manifests/item_ids.csv"],
        "currency": "BP",
        "entry_count": len(catalog),
        "entries": catalog,
        "unlock_derivations": {
            "KANTO_DAYCARE_QUEST": "v1 save ABIに専用quest bitがないため、Kanto access後のkanto_visitedを単調な物理完了signalとして使用",
            "COMPETITIVE_SUPPLY_UNLOCKED": "Hall of FameかつKanto認定4件以上",
            "KANTO_LEAGUE_CLEAR": "現行save ABIのlate-league完了signalであるleague_ii_cleared",
            "UB_PARADOX_UNLOCKED": "manifest上Kanto League clear直下のためleague_ii_clearedを共有",
        },
        "header_sha256": _sha(header_raw),
    }
    return catalog, header_raw, _stable(document)


def _compile_runtime(root: Path, load_address: int, generated_header: bytes) -> tuple[bytes, dict[str, int]]:
    compiler = shutil.which("arm-none-eabi-gcc")
    objcopy = shutil.which("arm-none-eabi-objcopy")
    nm = shutil.which("arm-none-eabi-nm")
    if not compiler or not objcopy or not nm:
        _fail("ARM GNU toolchain is required for BP shop runtime")
    sources = [
        root / "overlays/bp_shop_runtime/bp_shop_runtime.c",
        root / "overlays/bp_shop_runtime/bp_shop_libc.c",
        root / "overlays/save_migration/save_migration.c",
    ]
    for source in sources:
        if not source.is_file():
            _fail(f"BP shop runtime source missing: {source}")
    with tempfile.TemporaryDirectory(prefix="vega-bp-shop-runtime-") as temporary:
        directory = Path(temporary)
        (directory / "bp_shop_catalog_generated.h").write_bytes(generated_header)
        common = [
            compiler, "-mthumb", "-mcpu=arm7tdmi", "-mthumb-interwork",
            "-Os", "-std=c11", "-Wall", "-Wextra", "-Werror",
            "-ffreestanding", "-fno-builtin", "-fno-unwind-tables",
            "-fno-asynchronous-unwind-tables", "-fdata-sections",
            "-ffunction-sections", "-fno-common", "-DVEGA_SAVE_ROM_RUNTIME=1",
            f"-I{directory}", f"-I{root}",
            f"-I{root / 'overlays/bp_shop_runtime'}",
            f"-I{root / 'overlays/save_migration'}",
        ]
        objects: list[Path] = []
        for index, source in enumerate(sources):
            obj = directory / f"{index:02d}_{source.stem}.o"
            _run([*common, "-c", str(source), "-o", str(obj)], f"compile {source.name}")
            objects.append(obj)
        linker = directory / "linker.ld"
        linker.write_text(
            "SECTIONS\n{\n"
            f"  . = 0x{load_address:08X};\n"
            "  .text : {\n"
            "    KEEP(*(.text.BpShop_*))\n"
            "    *(.text*) *(.rodata*) *(.data*)\n"
            "  }\n"
            "  .bss (NOLOAD) : { *(.bss*) *(COMMON) }\n"
            "  /DISCARD/ : { *(.comment*) *(.ARM.attributes*) *(.note*) "
            "*(.ARM.exidx*) *(.ARM.extab*) }\n"
            "}\n",
            encoding="ascii",
        )
        elf = directory / "bp_shop.elf"
        binary = directory / "bp_shop.bin"
        _run([
            compiler, "-mthumb", "-mcpu=arm7tdmi", "-mthumb-interwork",
            "-nostdlib", "-Wl,--build-id=none", "-Wl,--gc-sections",
            "-Wl,-e,BpShop_Probe", f"-Wl,-T,{linker}",
            *map(str, objects), "-lgcc", "-o", str(elf),
        ], "link BP shop runtime")
        undefined = _run([nm, "-u", str(elf)], "BP shop undefined-symbol audit")
        if undefined:
            _fail("BP shop runtime has undefined symbols: " + undefined)
        _run([objcopy, "-O", "binary", str(elf), str(binary)], "BP shop objcopy")
        symbols: dict[str, int] = {}
        for line in _run([nm, "-n", "--defined-only", str(elf)], "BP shop nm").splitlines():
            fields = line.split()
            if len(fields) == 3:
                try:
                    symbols[fields[2]] = int(fields[0], 16)
                except ValueError:
                    pass
        missing = sorted(REQUIRED_LINKED_SYMBOLS - set(symbols))
        if missing:
            _fail(f"BP shop linked exports differ: missing={missing}")
        payload = binary.read_bytes()
        if not payload or len(payload) > 64 * 1024:
            _fail(f"unexpected BP shop runtime size: {len(payload)}")
        for name in REQUIRED_LINKED_SYMBOLS:
            address = symbols[name]
            if address & 1 or not load_address <= address < load_address + len(payload):
                _fail(f"BP shop symbol outside/alignment: {name}=0x{address:08X}")
        return payload, symbols


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

    def msgbox(self, label: str) -> "_Script":
        return self.emit(0x0F, 0x00).pointer(label).emit(0x09, 4)

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


def _build_scripts(root: Path, blob: _Blob) -> dict[str, Any]:
    mapping, tokens = _charmap(root)
    text_meta: dict[str, Any] = {}
    for label, text in TEXTS.items():
        encoded = _encode_text(text, mapping, tokens)
        blob.add(label, encoded, 1)
        text_meta[label] = {"text": text, "size": len(encoded), "sha256": _sha(encoded)}
    _add_script(
        blob, "script_bp_shop_npc",
        _Script().emit(0x6A, 0x5A).callnative("BpShop_Open")
        .compare_result(9).if_equal("script_bp_shop_wait")
        .goto("script_bp_shop_result"),
    )
    _add_script(
        blob, "script_bp_shop_wait",
        _Script().emit(0x27).callnative("BpShop_PostMenu")
        .goto("script_bp_shop_result"),
    )
    result = _Script()
    for value, label in (
        (0, "script_bp_shop_success"),
        (2, "script_bp_shop_end"),
        (3, "script_bp_shop_locked"),
        (13, "script_bp_shop_persist"),
        (14, "script_bp_shop_insufficient"),
        (15, "script_bp_shop_full"),
    ):
        result.compare_result(value).if_equal(label)
    result.goto("script_bp_shop_error")
    _add_script(blob, "script_bp_shop_result", result)
    for label, text_label in (
        ("script_bp_shop_success", "text_bp_shop_success"),
        ("script_bp_shop_locked", "text_bp_shop_locked"),
        ("script_bp_shop_persist", "text_bp_shop_persist"),
        ("script_bp_shop_insufficient", "text_bp_shop_insufficient"),
        ("script_bp_shop_full", "text_bp_shop_full"),
        ("script_bp_shop_error", "text_bp_shop_error"),
    ):
        _add_script(blob, label, _Script().msgbox(text_label).goto("script_bp_shop_end"))
    _add_script(blob, "script_bp_shop_end", _Script().emit(0x6C, 0x02))
    return {
        "texts": text_meta,
        "result_branches": [0, 2, 3, 13, 14, 15],
        "busy_result": 9,
        "uses_waitstate": True,
    }


def _entry_header(stage: bytes, stage17: dict[str, Any]) -> tuple[int, int]:
    root_pointer = int(stage17["symbols"]["map_groups_root"])
    root = _rom_offset(root_pointer, 99 * 4, "stage17 map groups root")
    group_pointer = _u32(stage, root + GBA_ENTRY[0] * 4, "Factory map group")
    group = _rom_offset(group_pointer, (GBA_ENTRY[1] + 1) * 4, "Factory map group")
    header_pointer = _u32(stage, group + GBA_ENTRY[1] * 4, "Factory map header")
    header = _rom_offset(header_pointer, 0x1C, "Factory map header")
    return header, header_pointer


def _add_map_runtime(stage: bytes, stage17: dict[str, Any], blob: _Blob) -> dict[str, Any]:
    header, header_pointer = _entry_header(stage, stage17)
    events_pointer = _u32(stage, header + 4, "Factory events root")
    scripts_pointer = _u32(stage, header + 8, "Factory map scripts root")
    events = _rom_offset(events_pointer, 0x14, "Factory events")
    old_events = bytearray(stage[events:events + 0x14])
    old_count = old_events[0]
    if old_count != 2 or old_events[1:4] != bytes((10, 0, 0)):
        _fail(f"Factory event counts drift: {list(old_events[:4])}")
    objects_pointer = _u32(stage, events + 4, "Factory object table")
    objects = _rom_offset(objects_pointer, old_count * 0x18, "Factory objects")
    old_objects = stage[objects:objects + old_count * 0x18]
    first = old_objects[:0x18]
    trial = old_objects[0x18:0x30]
    if (
        first[0] != 1 or struct.unpack_from("<HH", first, 4) != (24, 33)
        or trial[0] != 2 or struct.unpack_from("<HH", trial, 4) != (20, 19)
    ):
        _fail("Factory existing object identity/coordinates drift")
    if any(old_objects[index * 0x18] == 3 for index in range(old_count)):
        _fail("Factory local_id 3 is already occupied")
    shop = bytearray(trial)
    shop[0] = 3
    struct.pack_into("<HH", shop, 4, 22, 19)
    struct.pack_into("<I", shop, 0x10, 0)
    object_offset = blob.add("bp_shop_factory_objects", old_objects + bytes(shop), 4)
    blob.pointer(object_offset + old_count * 0x18 + 0x10, "script_bp_shop_npc")
    old_events[0] = old_count + 1
    struct.pack_into("<I", old_events, 4, 0)
    event_offset = blob.add("bp_shop_factory_events", bytes(old_events), 4)
    blob.pointer(event_offset + 4, "bp_shop_factory_objects")
    return {
        "group_id": GBA_ENTRY[0],
        "map_id": GBA_ENTRY[1],
        "header_offset": header,
        "header_address": header_pointer,
        "old_events_pointer": events_pointer,
        "old_scripts_pointer": scripts_pointer,
        "old_event_header_hex": stage[events:events + 0x14].hex(),
        "old_objects_sha256": _sha(old_objects),
        "object_count_before": old_count,
        "object_count_after": old_count + 1,
        "existing_objects_preserved": True,
        "map_scripts_preserved": True,
        "shop_object": {
            "local_id": 3,
            "graphics_id": shop[1],
            # ObjectEventTemplate byte 3 is compiler padding.  The live
            # movement type follows elevation at byte 9.
            "movement_type": shop[9],
            "x": 22,
            "y": 19,
            "source_clone_local_id": 2,
        },
    }


def _build_payload(
    root: Path,
    stage: bytes,
    stage17: dict[str, Any],
    generated_header: bytes,
    payload_offset: int,
) -> tuple[bytes, dict[str, Any]]:
    blob = _Blob()
    header_offset = blob.reserve("bp_shop_payload_header", PAYLOAD_HEADER_SIZE, 16)
    code_load = GBA_ROM_BASE + payload_offset + ((len(blob.data) + 3) & ~3)
    code, code_symbols = _compile_runtime(root, code_load, generated_header)
    code_offset = blob.add("bp_shop_runtime_code", code, 4)
    if GBA_ROM_BASE + payload_offset + code_offset != code_load:
        _fail("BP shop linker address disagrees with payload placement")
    for name, address in code_symbols.items():
        relative = address - code_load
        if 0 <= relative < len(code):
            blob.labels[f"native::{name}"] = code_offset + relative
    script_meta = _build_scripts(root, blob)
    map_meta = _add_map_runtime(stage, stage17, blob)
    runtime_size = len(blob.data)
    struct.pack_into(
        "<8sIIIIIIII", blob.data, header_offset,
        b"VEGABP27", 1, runtime_size, len(code), CATALOG_COUNT,
        GBA_ENTRY[0], GBA_ENTRY[1], map_meta["object_count_after"], 0,
    )
    blob.pointer(header_offset + 40, "native::BpShop_Probe", thumb=True)
    blob.pointer(header_offset + 44, "native::BpShop_Open", thumb=True)
    blob.pointer(header_offset + 48, "native::BpShop_PurchaseByIndex", thumb=True)
    blob.pointer(header_offset + 52, "script_bp_shop_npc")
    blob.pointer(header_offset + 56, "bp_shop_factory_events")
    payload = blob.finish(payload_offset)
    base = GBA_ROM_BASE + payload_offset
    symbols = {
        label: base + relative
        for label, relative in sorted(blob.labels.items())
        if label.startswith("native::")
        or label.startswith("script_bp_shop_")
        or label.startswith("bp_shop_factory_")
    }
    map_meta.update({
        "events_after_address": symbols["bp_shop_factory_events"],
        "objects_after_address": symbols["bp_shop_factory_objects"],
        "shop_script_address": symbols["script_bp_shop_npc"],
    })
    return payload, {
        "payload": {
            "magic": "VEGABP27",
            "offset": payload_offset,
            "address": base,
            "size": len(payload),
            "sha256": _sha(payload),
            "code_offset": payload_offset + code_offset,
            "code_address": code_load,
            "code_size": len(code),
            "code_sha256": _sha(code),
        },
        "entrypoints": {
            name: code_symbols[name] | 1 for name in sorted(REQUIRED_ENTRYPOINTS)
        },
        "linked_symbols": {
            name: code_symbols[name] | (1 if name != "VegaSaveFinalize" else 1)
            for name in sorted(REQUIRED_LINKED_SYMBOLS)
        },
        "scripts": {
            **script_meta,
            "npc_address": symbols["script_bp_shop_npc"],
            "wait_address": symbols["script_bp_shop_wait"],
            "result_address": symbols["script_bp_shop_result"],
        },
        "map": map_meta,
        "symbols": symbols,
    }


def _previous_requests(allocation: dict[str, Any]) -> list[dict[str, object]]:
    return [{
        "name": row["name"],
        "region": row["region"],
        "size": row["size"],
        "alignment": row["alignment"],
        "start": row["start"],
        "owner": row["owner"],
        "purpose": row["purpose"],
        "content_sha256": row["content_sha256"],
    } for row in allocation["allocations"]]


def _allocation(
    root: Path, previous: dict[str, Any], size: int, digest: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    requests = _previous_requests(previous)
    requests.append({
        "name": ALLOCATION_NAME,
        "region": "integration_modules",
        "size": size,
        "alignment": 16,
        "owner": TASK,
        "purpose": "Factory BP catalog/menu/purchase/save runtime and physical shop NPC",
        "content_sha256": digest,
    })
    report = build_allocation_report_from_csv(root / "config/rom_regions.csv", requests)
    if report.get("summaries", {}).get("overlap_count") != 0:
        _fail("stage27 allocator overlap detected")
    matches = [row for row in report["allocations"] if row["name"] == ALLOCATION_NAME]
    if len(matches) != 1:
        _fail("BP shop allocation is not unique")
    return matches[0], report


def _ram_audit(root: Path) -> dict[str, Any]:
    path = root / "config/ram_layout.csv"
    rows = _rows(path)
    matches = [row for row in rows if row["owner"] == "USER_20260817_BP_SHOP_RUNTIME"]
    if len(matches) != 1:
        _fail("BP shop volatile RAM reservation is not unique")
    row = matches[0]
    if (
        int(row["start"], 0) != VOLATILE_RAM_START
        or int(row["end_exclusive"], 0) != VOLATILE_RAM_END
        or int(row["size"], 0) != VOLATILE_RAM_END - VOLATILE_RAM_START
        or row["persistence"] != "VOLATILE"
        or row["status"] != "LIVE"
    ):
        _fail("BP shop volatile RAM reservation differs")
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
        "status": "PASS",
        "address": VOLATILE_RAM_START,
        "end_exclusive": VOLATILE_RAM_END,
        "size": VOLATILE_RAM_END - VOLATILE_RAM_START,
        "persistence": "VOLATILE",
        "flash_serialized": False,
        "overlap_count": 0,
        "layout_sha256": _sha(path.read_bytes()),
    }


def _patch_pointer(
    output: bytearray, offset: int, expected: int, replacement: int, label: str,
) -> dict[str, Any]:
    actual = _u32(output, offset, label)
    if actual != expected:
        _fail(f"{label}: expected {expected:#010x}, got {actual:#010x}")
    struct.pack_into("<I", output, offset, replacement)
    return {
        "label": label,
        "site_offset": offset,
        "site_address": GBA_ROM_BASE + offset,
        "expected_pointer": expected,
        "replacement_pointer": replacement,
    }


def build_runtime_outputs(root: Path = ROOT) -> dict[str, bytes]:
    root = Path(root)
    stage, stage_meta, previous_alloc, stage17 = _input_contract(root)
    catalog, generated_header, catalog_json = _catalog_outputs(root)
    preliminary, _ = _build_payload(root, stage, stage17, generated_header, 0)
    allocation, _ = _allocation(root, previous_alloc, len(preliminary), "0" * 64)
    payload_offset = int(allocation["start"])
    payload, runtime = _build_payload(root, stage, stage17, generated_header, payload_offset)
    if len(payload) != len(preliminary):
        _fail("address-dependent BP shop payload size changed")
    allocation, allocation_report = _allocation(
        root, previous_alloc, len(payload), _sha(payload),
    )
    if int(allocation["start"]) != payload_offset:
        _fail("BP shop allocation changed after final link")
    payload_end = int(allocation["end_exclusive"])
    if stage[payload_offset:payload_end] != b"\xFF" * len(payload):
        _fail("BP shop payload destination is not erased FF")

    output = bytearray(stage)
    output[payload_offset:payload_end] = payload
    map_meta = runtime["map"]
    patch = _patch_pointer(
        output,
        int(map_meta["header_offset"]) + 4,
        int(map_meta["old_events_pointer"]),
        int(map_meta["events_after_address"]),
        "Factory events root",
    )
    if _u32(output, int(map_meta["header_offset"]) + 8, "Factory map scripts") != int(map_meta["old_scripts_pointer"]):
        _fail("Factory map scripts pointer changed")
    allowed = [
        (payload_offset, payload_end),
        (patch["site_offset"], patch["site_offset"] + 4),
    ]
    outside: list[int] = []
    for index, (before, after) in enumerate(zip(stage, output)):
        if before != after and not any(start <= index < end for start, end in allowed):
            outside.append(index)
            if len(outside) == 8:
                break
    if outside:
        _fail(f"stage27 changed bytes outside declared spans: {outside}")
    output_raw = bytes(output)
    release_patch = create_bps(stage, output_raw)
    if apply_bps(stage, release_patch) != output_raw:
        _fail("stage26 to stage27 BPS round-trip differs")
    ram = _ram_audit(root)
    metadata = {
        "schema_version": 1,
        "task": TASK,
        "status": "PASS",
        "input": {
            "path": INPUT_ROM.as_posix(),
            "size": len(stage),
            "sha256": _sha(stage),
            "upstream_task": stage_meta.get("task"),
        },
        "output": {
            "path": OUTPUT_ROM.as_posix(),
            "size": len(output_raw),
            "sha256": _sha(output_raw),
        },
        **runtime,
        "catalog": {
            "path": CATALOG_JSON.as_posix(),
            "header_path": CATALOG_HEADER.as_posix(),
            "entry_count": len(catalog),
            "item_ids": [row["item_id"] for row in catalog],
            "prices_bp": [row["price_bp"] for row in catalog],
            "source": "ACTIVE BP_SHOP rows in manifests/qol_rewards.csv joined to manifests/item_ids.csv",
        },
        "patches": [patch],
        "transaction": {
            "order": ["AddBagItem", "VegaFactorySpendBattlePoints", "TrySavingData(0)", "TryWriteSector(31)"],
            "preflight_no_mutation_results": [3, 14, 15],
            "compensation": "standard-save or sector31 failure restores BP, removes item, and rewrites both stores where possible",
            "balance_storage": "VegaModernSaveData.factory.battle_points",
            "save_sector": 31,
        },
        "ram_audit": ram,
        "allocation": {
            "path": OUTPUT_ALLOC.as_posix(),
            "name": ALLOCATION_NAME,
            "overlap_count": allocation_report["summaries"]["overlap_count"],
            "remaining_allocatable_bytes": allocation_report["summaries"]["remaining_allocatable_bytes"],
        },
        "release_patch_round_trip": {
            "format": "BPS1",
            "source_sha256": _sha(stage),
            "target_sha256": _sha(output_raw),
            "patch_size": len(release_patch),
            "patch_sha256": _sha(release_patch),
            "exact": True,
        },
        "invariants": {
            "input_v1_4_0_hash_pinned": True,
            "rom_size_32_mib": len(output_raw) == ROM_SIZE,
            "catalog_count_18": len(catalog) == CATALOG_COUNT,
            "catalog_item_ids_unique": len({row["item_id"] for row in catalog}) == CATALOG_COUNT,
            "allocator_overlap_zero": allocation_report["summaries"]["overlap_count"] == 0,
            "declared_changes_only": True,
            "factory_object_count_2_to_3": map_meta["object_count_before"] == 2 and map_meta["object_count_after"] == 3,
            "existing_factory_objects_preserved": map_meta["existing_objects_preserved"],
            "factory_map_scripts_preserved": map_meta["map_scripts_preserved"],
            "shop_npc_physically_bound": map_meta["shop_object"]["local_id"] == 3,
            "release_patch_exact": True,
            "ram_overlap_zero": ram["overlap_count"] == 0,
        },
    }
    if not all(metadata["invariants"].values()):
        _fail("BP shop runtime invariant failed")
    symbols_doc = {
        "schema_version": 1,
        "task": TASK,
        "payload": runtime["payload"],
        "entrypoints": runtime["entrypoints"],
        "linked_symbols": runtime["linked_symbols"],
        "scripts": runtime["scripts"],
        "map": runtime["map"],
        "symbols": runtime["symbols"],
    }
    return {
        OUTPUT_ROM.as_posix(): output_raw,
        OUTPUT_META.as_posix(): _stable(metadata),
        OUTPUT_ALLOC.as_posix(): _stable(allocation_report),
        RUNTIME_BIN.as_posix(): payload,
        RUNTIME_SYMBOLS.as_posix(): _stable(symbols_doc),
        CATALOG_HEADER.as_posix(): generated_header,
        CATALOG_JSON.as_posix(): catalog_json,
        PATCH.as_posix(): release_patch,
    }


def _mgba_fixture(root: Path, stage: bytes, metadata: dict[str, Any]) -> dict[str, Any]:
    runner = root / RUNNER
    if not runner.is_file():
        _fail(f"BP shop mGBA runner missing: {runner}")
    with tempfile.TemporaryDirectory(prefix="vega-bp-shop-smoke-") as temporary:
        temp = Path(temporary)
        rom_run1 = temp / "27_bp_shop_runtime_run1.gba"
        rom_run2 = temp / "27_bp_shop_runtime_run2.gba"
        save_run1 = temp / "27_bp_shop_runtime_run1.sav"
        save_run2 = temp / "27_bp_shop_runtime_run2.sav"
        executable = temp / "mgba-bp-shop-smoke"
        rom_run1.write_bytes(stage)
        rom_run2.write_bytes(stage)
        compiler = os.environ.get("CC", "cc")
        _run([
            compiler, "-std=c11", "-Wall", "-Wextra", "-Werror",
            str(RUNNER), "-o", str(executable), "-lmgba",
        ], "BP shop libmGBA smoke compile", cwd=root)
        entry = metadata["entrypoints"]
        linked = metadata["linked_symbols"]
        common_args = [
            hex(entry["BpShop_Probe"]),
            hex(entry["BpShop_EnsureSave"]),
            hex(entry["BpShop_GetBalance"]),
            hex(entry["BpShop_IsItemUnlocked"]),
            hex(entry["BpShop_PurchaseByIndex"]),
            hex(linked["VegaSaveFinalize"]),
            hex(metadata["scripts"]["npc_address"]),
            hex(metadata["map"]["events_after_address"]),
            hex(metadata["map"]["old_scripts_pointer"]),
        ]
        commands = [
            [str(executable), str(rom_run1), str(save_run1), *common_args],
            [str(executable), str(rom_run2), str(save_run2), *common_args],
        ]
        processes = [
            subprocess.Popen(
                command, cwd=root, text=True, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            for command in commands
        ]
        payloads: list[str] = []
        for index, process in enumerate(processes, start=1):
            try:
                stdout, stderr = process.communicate(timeout=90)
            except subprocess.TimeoutExpired as error:
                for pending in processes:
                    if pending.poll() is None:
                        pending.kill()
                for pending in processes:
                    pending.communicate()
                detail = ((error.stderr or error.stdout) or "").strip()
                _fail(
                    f"BP shop exact-ROM smoke run {index} timed out: {detail}"
                )
            if process.returncode:
                for pending in processes:
                    if pending.poll() is None:
                        pending.kill()
                for pending in processes:
                    if pending is not process:
                        pending.communicate()
                detail = (stderr or stdout).strip()
                _fail(
                    f"BP shop exact-ROM smoke run {index} failed "
                    f"({process.returncode}): {detail}"
                )
            payloads.append(stdout.strip())
        first, second = (json.loads(payload) for payload in payloads)
        if first != second or first.get("status") != "PASS":
            _fail("BP shop exact-ROM smoke is not deterministic PASS")
        first["process_runs"] = 2
        first["rom_sha256"] = _sha(stage)
        return first


def _report(metadata: dict[str, Any], mgba: dict[str, Any]) -> bytes:
    checks = mgba["checks"]
    text = f"""# Factory BPショップ実ROM統合

## 結論

- クチバFactory（map 96/5）へBPショップNPC local_id 3を実配置した。
- `manifests/qol_rewards.csv` のACTIVE `BP_SHOP` 18件を、`item_ids.csv` の実item IDへ結合した。
- Trial runtimeと同じ `VegaModernSaveData.factory.battle_points` を残高正本に使用する。
- 購入はitem追加、BP減算、通常save、sector 31の順で確定し、保存失敗時は補償rollbackする。
- 残高不足、未解禁、bag満杯は購入前に無変更で返す。

## ROM結合

- Input: `{metadata['input']['path']}` / `{metadata['input']['sha256']}`
- Output: `{metadata['output']['path']}` / `{metadata['output']['sha256']}`
- Payload: `{metadata['payload']['address']:#010x}` / {metadata['payload']['size']} bytes
- Factory object count: {metadata['map']['object_count_before']} -> {metadata['map']['object_count_after']}
- 既存Factory Trial NPCとmap scripts: byte-preserved
- Catalog: {metadata['catalog']['entry_count']} items
- Allocator overlap: {metadata['allocation']['overlap_count']}
- BPS exact round-trip: {metadata['release_patch_round_trip']['exact']}

## focused exact-ROM smoke

- physical NPC/event graph: {checks['physical_npc_event_graph']}
- ABI probe / save initialization: {checks['probe_and_save_init']}
- unlock mapping: {checks['unlock_mapping']}
- successful purchase and BP debit: {checks['successful_purchase']}
- sector 31 reload durability: {checks['sector31_reload']}
- insufficient BP no mutation: {checks['insufficient_no_mutation']}
- bag-full no mutation: {checks['bag_full_no_mutation']}
- locked no mutation: {checks['locked_no_mutation']}
- deterministic process runs: {mgba['process_runs']}

解禁signalのうち専用bitがないものは、現行v1 save ABIで既に永続化される単調signalへ明示的に写像した。Kanto保育所はKanto access後の`kanto_visited`、対戦用品はHall of FameかつKanto認定4件、Kantoリーグ/UB・Paradoxは`league_ii_cleared`を使用する。

ユーザー指示どおりfresh全監査は再実行せず、このstage 27 builder、allocator、catalog binding、変更span、BPS round-trip、libmGBA exact-ROM smokeを対象限定で検証した。
"""
    return text.encode("utf-8")


def collect_outputs(root: Path = ROOT) -> dict[str, bytes]:
    outputs = build_runtime_outputs(root)
    repeated = build_runtime_outputs(root)
    if outputs != repeated:
        _fail("BP shop runtime build is not byte deterministic")
    stage = outputs[OUTPUT_ROM.as_posix()]
    metadata = json.loads(outputs[OUTPUT_META.as_posix()])
    mgba = _mgba_fixture(root, stage, metadata)
    metadata["exact_rom_fixture"] = {
        "path": MGBA_FIXTURE.as_posix(),
        "status": mgba["status"],
        "process_runs": mgba["process_runs"],
        "all_checks": all(mgba["checks"].values()),
    }
    metadata["invariants"]["exact_rom_process_runs_2"] = mgba["process_runs"] == 2
    metadata["invariants"]["exact_rom_all_checks"] = all(mgba["checks"].values())
    if not all(metadata["invariants"].values()):
        _fail("BP shop exact-ROM invariant failed")
    outputs[OUTPUT_META.as_posix()] = _stable(metadata)
    outputs[MGBA_FIXTURE.as_posix()] = _stable(mgba)
    outputs[REPORT.as_posix()] = _report(metadata, mgba)
    return outputs


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
        _fail("BP shop generated outputs differ: " + ", ".join(differences))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("build", "check"))
    args = parser.parse_args()
    try:
        outputs = collect_outputs(ROOT)
        if args.mode == "build":
            _write_outputs(ROOT, outputs)
        else:
            _check_outputs(ROOT, outputs)
    except (OSError, ValueError, KeyError, json.JSONDecodeError, BpShopBuildError) as error:
        print(f"BP shop runtime build failed: {error}", file=sys.stderr)
        return 1
    print(
        f"BP shop runtime {args.mode}: PASS "
        f"stage={_sha(outputs[OUTPUT_ROM.as_posix()])} artifacts={len(outputs)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
