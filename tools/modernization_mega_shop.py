#!/usr/bin/env python3
"""Stage67へ45種のMega Stone実体・独立BP shopを決定的に結合する。"""

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
from typing import Any, Mapping, NoReturn, Sequence


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.regression.rom_runtime import _Blob, _charmap, _encode_text  # noqa: E402
from tools.release.bps import apply_bps, create_bps  # noqa: E402
from tools.rom_allocator import GBA_ROM_BASE, build_allocation_report_from_csv  # noqa: E402


TASK = "USER-MODERNIZATION-MEGA-STONE-BP-SHOP"
CONFIG = Path("config/modernization_mega_shop.json")
ROM_SIZE = 32 * 1024 * 1024
PAYLOAD_HEADER_SIZE = 0x100
ALLOCATION_NAME = "modernization_mega_shop_stage68_payload"
MAP_GROUPS_POINTER_SITE = 0x00054B0C
ITEM_SANITIZER_REPLACEMENT = bytes.fromhex(
    "0004000cff2106318900884200d3002071467047c046c046"
)

REQUIRED_ENTRYPOINTS = {
    "MegaShop_Probe",
    "MegaShop_EnsureSave",
    "MegaShop_GetBalance",
    "MegaShop_IsUnlocked",
    "MegaShop_IsClaimed",
    "MegaShop_PurchaseByIndex",
    "MegaShop_PurchaseSelected",
    "MegaShop_Open",
    "MegaShop_PostMenu",
}
REQUIRED_LINKED_SYMBOLS = REQUIRED_ENTRYPOINTS | {"VegaSaveFinalize"}

TEXTS = {
    "text_mega_shop_success": "こうにゅうしました！",
    "text_mega_shop_locked": "メガリングが ひつようです",
    "text_mega_shop_claimed": "こうにゅうずみです",
    "text_mega_shop_all_claimed": "すべて こうにゅうずみです",
    "text_mega_shop_persist": "セーブに しっぱいしました",
    "text_mega_shop_insufficient": "BPが たりません",
    "text_mega_shop_full": "もちものが いっぱいです",
    "text_mega_shop_error": "こうにゅうできませんでした",
}


class MegaShopBuildError(ValueError):
    """入力、ID、asset、ROM ABI、配置contractの違反。"""


def _fail(message: str) -> NoReturn:
    raise MegaShopBuildError(message)


def _sha(raw: bytes | bytearray) -> str:
    return hashlib.sha256(raw).hexdigest()


def _stable(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        _fail(f"JSONを読めません: {path}: {error}")
    if not isinstance(value, dict):
        _fail(f"JSON rootがobjectではありません: {path}")
    return value


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def _integer(value: object, label: str) -> int:
    if isinstance(value, bool):
        _fail(f"{label}が整数ではありません")
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value, 0)
        except ValueError:
            pass
    _fail(f"{label}が整数ではありません: {value!r}")


def _run(command: Sequence[str], label: str, *, cwd: Path = ROOT) -> str:
    completed = subprocess.run(
        list(command), cwd=cwd, text=True, capture_output=True, check=False,
    )
    if completed.returncode:
        detail = (completed.stderr or completed.stdout).strip()
        _fail(f"{label}失敗 ({completed.returncode}): {detail}")
    return completed.stdout.strip()


def _u16(raw: bytes | bytearray, offset: int, label: str) -> int:
    if offset < 0 or offset + 2 > len(raw):
        _fail(f"{label}: ROM範囲外 offset=0x{offset:X}")
    return struct.unpack_from("<H", raw, offset)[0]


def _u32(raw: bytes | bytearray, offset: int, label: str) -> int:
    if offset < 0 or offset + 4 > len(raw):
        _fail(f"{label}: ROM範囲外 offset=0x{offset:X}")
    return struct.unpack_from("<I", raw, offset)[0]


def _rom_offset(address: int, size: int, label: str) -> int:
    address &= ~1
    offset = address - GBA_ROM_BASE
    if offset < 0 or offset + size > ROM_SIZE:
        _fail(f"{label}: ROM address範囲外 0x{address:08X}+{size}")
    return offset


def _input_file(root: Path, spec: Mapping[str, Any], label: str) -> tuple[Path, bytes]:
    path = root / str(spec.get("path", ""))
    if not path.is_file():
        _fail(f"{label}がありません: {path}")
    raw = path.read_bytes()
    if "size" in spec and len(raw) != _integer(spec["size"], f"{label}.size"):
        _fail(f"{label} size不一致: {len(raw)}")
    expected = spec.get("sha256")
    if expected is not None and _sha(raw) != expected:
        _fail(f"{label} SHA-256不一致: {_sha(raw)}")
    return path, raw


def _all_offsets(raw: bytes | bytearray, needle: bytes) -> list[int]:
    result: list[int] = []
    cursor = 0
    while True:
        cursor = raw.find(needle, cursor)
        if cursor < 0:
            return result
        result.append(cursor)
        cursor += 1


def _c_bytes(name: str, raw: bytes, *, suffix: str = "") -> str:
    lines = []
    for start in range(0, len(raw), 12):
        lines.append("    " + ", ".join(
            f"0x{value:02X}u" for value in raw[start:start + 12]
        ) + ",")
    declarator = suffix or "[]"
    return f"static const u8 {name}{declarator} = {{\n" + "\n".join(lines) + "\n};\n"


def _fixed_name(text: str, mapping: Mapping[str, int], tokens: Sequence[str]) -> bytes:
    encoded = _encode_text(text, mapping, tokens)
    if not encoded or encoded[-1] != 0xFF or len(encoded) > 10:
        _fail(f"Item名が9-byte glyph境界を超えます: {text} ({len(encoded)})")
    return encoded + bytes([0xFF]) * (10 - len(encoded))


def _stone_display_name(item_key: str, base_name: str) -> str:
    suffix = ""
    for candidate in ("_X", "_Y", "_Z"):
        if item_key.endswith(candidate):
            suffix = candidate[-1]
            break
    return f"{base_name}ナイト{suffix}"


def _load_contract(root: Path) -> tuple[
    dict[str, Any], bytes, dict[str, Any], dict[str, Any], dict[str, Any],
    dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]
]:
    config = _read_json(root / CONFIG)
    if config.get("schema_version") != 1 or config.get("task") != TASK:
        _fail("Mega shop config schema/task不一致")
    inputs = config.get("inputs")
    if not isinstance(inputs, dict):
        _fail("inputs contractがobjectではありません")
    _, stage = _input_file(root, inputs["rom"], "Stage67 ROM")
    if len(stage) != ROM_SIZE:
        _fail("Stage67 ROMが32 MiBではありません")
    _, metadata_raw = _input_file(root, inputs["metadata"], "Stage67 metadata")
    _, allocation_raw = _input_file(root, inputs["allocation"], "Stage67 allocation")
    _, allowlist_raw = _input_file(
        root, inputs["pointer_site_allowlist"], "pointer site allowlist",
    )
    _, bounds_raw = _input_file(
        root, inputs["item_bound_allowlist"], "item bound allowlist",
    )
    metadata = json.loads(metadata_raw)
    allocation = json.loads(allocation_raw)
    allowlist = json.loads(allowlist_raw)
    bounds = json.loads(bounds_raw)
    _, candidate_raw = _input_file(root, inputs["candidate_manifest"], "P04 candidate")
    _, asset_raw = _input_file(root, inputs["asset_manifest"], "P04 asset")
    _, capacity_raw = _input_file(root, inputs["capacity_manifest"], "P04 capacity")
    candidate = json.loads(candidate_raw)
    asset = json.loads(asset_raw)
    capacity = json.loads(capacity_raw)
    if allocation.get("summaries", {}).get("overlap_count") != 0:
        _fail("Stage67 allocation overlap contract不一致")
    if metadata.get("output", {}).get("sha256") != _sha(stage):
        _fail("Stage67 metadata output hash不一致")
    if (allowlist.get("schema_version") != 1 or allowlist.get("task") != TASK
            or allowlist.get("stage") != 68):
        _fail("pointer site allowlist schema/task/stage不一致")
    parent = allowlist.get("parent_rom", {})
    if parent.get("size") != len(stage) or parent.get("sha256") != _sha(stage):
        _fail("pointer site allowlistのStage67 pin不一致")
    if (bounds.get("schema_version") != 1 or bounds.get("task") != TASK
            or bounds.get("stage") != 68
            or bounds.get("parent_rom_sha256") != _sha(stage)):
        _fail("item bound allowlist schema/task/stage/ROM pin不一致")
    return (config, stage, metadata, allocation, candidate, asset, capacity,
            allowlist, bounds)


def _catalog_outputs(
    root: Path,
    config: Mapping[str, Any],
    candidate: Mapping[str, Any],
    asset: Mapping[str, Any],
    capacity: Mapping[str, Any],
) -> tuple[list[dict[str, Any]], bytes, bytes]:
    catalog_config = config["catalog"]
    reservations = capacity.get("id_reservations", {}).get("item", {})
    rows = reservations.get("rows")
    if not isinstance(rows, list) or len(rows) != 45:
        _fail("P04 Item reservationが45行ではありません")
    if [row.get("id") for row in rows] != list(range(999, 1044)):
        _fail("P04 Item reservationが999..1043連続ではありません")
    if [row.get("item_key") for row in rows] != sorted(row.get("item_key") for row in rows):
        _fail("P04 Item reservationがstable key順ではありません")
    records = candidate.get("records")
    if not isinstance(records, list):
        _fail("P04 candidate records不一致")
    by_record = {row.get("record_key"): row for row in records}
    species_by_key = {
        row["species_key"]: row for row in _rows(root / config["inputs"]["species_manifest"])
    }
    stone_assets = asset.get("stone_assets")
    if not isinstance(stone_assets, list) or len(stone_assets) != 45:
        _fail("P04 stone assetが45行ではありません")
    asset_by_key = {row.get("mega_stone_key"): row for row in stone_assets}
    mapping, tokens = _charmap(root)
    price = _integer(catalog_config["price_bp"], "catalog.price_bp")
    flag_first = _integer(catalog_config["claim_flag_first"], "claim flag first")
    header: list[str] = [
        "#ifndef MODERNIZATION_MEGA_SHOP_CATALOG_GENERATED_H",
        "#define MODERNIZATION_MEGA_SHOP_CATALOG_GENERATED_H",
        "",
        "#define MEGA_SHOP_CATALOG_COUNT 45u",
        "",
    ]
    row_defs: list[str] = []
    entry_defs: list[str] = []
    catalog: list[dict[str, Any]] = []
    for index, reservation in enumerate(rows):
        item_key = str(reservation["item_key"])
        source = by_record.get(reservation.get("source_record_key"))
        if not isinstance(source, dict) or source.get("implementation_scope") != "ADOPT_CANDIDATE":
            _fail(f"Mega Stone source candidate不一致: {item_key}")
        species_key = source.get("source_species_key")
        species = species_by_key.get(species_key)
        if not species or not species.get("display_name"):
            _fail(f"Mega Stone base Species名を解決できません: {item_key}/{species_key}")
        display_name = _stone_display_name(item_key, species["display_name"])
        name_raw = _fixed_name(display_name, mapping, tokens)
        row_text = f"{display_name} {price}BP"
        row_raw = _encode_text(row_text, mapping, tokens)
        if len(row_raw) > 22:
            _fail(f"Mega shop menu rowが長すぎます: {row_text}")
        asset_row = asset_by_key.get(item_key)
        if not isinstance(asset_row, dict):
            _fail(f"Mega Stone assetを解決できません: {item_key}")
        icon = asset_row.get("png_asset", {}).get("gba_conversion", {})
        palette = asset_row.get("palette_asset", {}).get("gba_conversion", {})
        for role, record, expected_size in (("icon", icon, 288), ("palette", palette, 32)):
            path = root / config["inputs"]["asset_root"] / str(record.get("relative_path", ""))
            if not path.is_file():
                _fail(f"{item_key} {role} assetがありません: {path}")
            raw = path.read_bytes()
            if len(raw) != expected_size or len(raw) != record.get("size") or _sha(raw) != record.get("sha256"):
                _fail(f"{item_key} {role} assetのsize/hash不一致")
        claim_flag = flag_first + index
        row_symbol = f"gMegaShopRow{index:02d}"
        row_defs.append(_c_bytes(row_symbol, row_raw))
        entry_defs.append(
            "    {"
            f"{reservation['id']}u, {price}u, 0x{claim_flag:04X}u, 1u, 0u, {row_symbol}"
            "},"
        )
        catalog.append({
            "index": index,
            "item_id": reservation["id"],
            "item_key": item_key,
            "source_record_key": reservation["source_record_key"],
            "display_name": display_name,
            "display_name_hex": name_raw.hex(),
            "row_text": row_text,
            "row_text_hex": row_raw.hex(),
            "price_bp": price,
            "quantity": 1,
            "claim_flag": claim_flag,
            "claim_flag_hex": f"0x{claim_flag:04X}",
            "icon_relative_path": icon["relative_path"],
            "icon_sha256": icon["sha256"],
            "palette_relative_path": palette["relative_path"],
            "palette_sha256": palette["sha256"],
        })
    if catalog[-1]["claim_flag"] != _integer(catalog_config["claim_flag_last"], "claim flag last"):
        _fail("Mega Stone claim flag終端不一致")
    prefix = _encode_text("BP ", mapping, tokens)
    digits = _encode_text("0123456789", mapping, tokens)[:-1]
    if len(digits) != 10:
        _fail("数字font encoding不一致")
    header.extend(row_defs)
    header.append(_c_bytes("gMegaShopBalancePrefix", prefix))
    header.append(_c_bytes("gMegaShopDigitGlyphs", digits, suffix="[10]"))
    header.append(_c_bytes("gMegaShopTextNext", _encode_text("つぎ", mapping, tokens)))
    header.append(_c_bytes("gMegaShopTextCancel", _encode_text("やめる", mapping, tokens)))
    header.extend([
        "static const MegaShopCatalogEntry gMegaShopCatalog[MEGA_SHOP_CATALOG_COUNT] = {",
        *entry_defs,
        "};",
        "",
        "#endif /* MODERNIZATION_MEGA_SHOP_CATALOG_GENERATED_H */",
        "",
    ])
    header_raw = "\n".join(header).encode("ascii")
    catalog_doc = {
        "schema_version": 1,
        "task": TASK,
        "status": "ROM_MATERIALIZED",
        "currency": "BP",
        "unlock": {"item_key": "ITEM_KEY_MEGA_RING", "item_id": 580, "quantity": 1},
        "entry_count": 45,
        "page_size": 5,
        "page_count": 9,
        "claim_storage": {
            "kind": "EXPANDED_EVENT_FLAGS",
            "first": "0x14A0",
            "last": "0x14CC",
            "migration": "ZERO_DEFAULT_IN_EXISTING_EXPANDED_FLAGS_OWNER",
        },
        "entries": catalog,
        "header_sha256": _sha(header_raw),
    }
    return catalog, header_raw, _stable(catalog_doc)


def _compile_runtime(
    root: Path, load_address: int, generated_header: bytes,
) -> tuple[bytes, dict[str, int], dict[str, Any]]:
    compiler = shutil.which("arm-none-eabi-gcc")
    objcopy = shutil.which("arm-none-eabi-objcopy")
    nm = shutil.which("arm-none-eabi-nm")
    if not compiler or not objcopy or not nm:
        _fail("ARM GNU toolchainが必要です")
    sources = [
        root / "overlays/modernization_mega_shop/modernization_mega_shop.c",
        root / "overlays/bp_shop_runtime/bp_shop_libc.c",
        root / "overlays/save_migration/save_migration.c",
    ]
    with tempfile.TemporaryDirectory(prefix="vega-modernization-mega-shop-") as temporary:
        directory = Path(temporary)
        (directory / "modernization_mega_shop_catalog_generated.h").write_bytes(generated_header)
        compile_flags = [
            "-mthumb", "-mcpu=arm7tdmi", "-mthumb-interwork",
            "-Os", "-std=c11", "-Wall", "-Wextra", "-Werror",
            "-ffreestanding", "-fno-builtin", "-fno-unwind-tables",
            "-fno-asynchronous-unwind-tables", "-fdata-sections",
            "-ffunction-sections", "-fno-common", "-DVEGA_SAVE_ROM_RUNTIME=1",
        ]
        common = [
            compiler, *compile_flags,
            f"-I{directory}", f"-I{root}",
            f"-I{root / 'overlays/modernization_mega_shop'}",
            f"-I{root / 'overlays/save_migration'}",
        ]
        objects: list[Path] = []
        for index, source in enumerate(sources):
            obj = directory / f"{index:02d}_{source.stem}.o"
            _run([*common, "-c", str(source), "-o", str(obj)], f"compile {source.name}")
            objects.append(obj)
        linker = directory / "linker.ld"
        linker_text = (
            "SECTIONS\n{\n"
            f"  . = 0x{load_address:08X};\n"
            "  .text : {\n"
            "    KEEP(*(.text.MegaShop_*))\n"
            "    *(.text*) *(.rodata*) *(.data*)\n"
            "  }\n"
            "  .bss (NOLOAD) : { *(.bss*) *(COMMON) }\n"
            "  /DISCARD/ : { *(.comment*) *(.ARM.attributes*) *(.note*) "
            "*(.ARM.exidx*) *(.ARM.extab*) }\n"
            "}\n"
        )
        linker.write_text(linker_text, encoding="ascii")
        elf = directory / "mega_shop.elf"
        binary = directory / "mega_shop.bin"
        link_flags = [
            "-mthumb", "-mcpu=arm7tdmi", "-mthumb-interwork",
            "-nostdlib", "-Wl,--build-id=none", "-Wl,--gc-sections",
            "-Wl,-e,MegaShop_Probe", f"-Wl,-T,{linker}",
        ]
        _run([compiler, *link_flags, *map(str, objects), "-lgcc", "-o", str(elf)],
             "link Mega shop runtime")
        undefined = _run([nm, "-u", str(elf)], "Mega shop undefined-symbol audit")
        if undefined:
            _fail("Mega shop runtimeにundefined symbolがあります: " + undefined)
        _run([objcopy, "-O", "binary", str(elf), str(binary)], "Mega shop objcopy")
        symbols: dict[str, int] = {}
        for line in _run([nm, "-n", "--defined-only", str(elf)], "Mega shop nm").splitlines():
            fields = line.split()
            if len(fields) == 3:
                try:
                    symbols[fields[2]] = int(fields[0], 16)
                except ValueError:
                    pass
        missing = sorted(REQUIRED_LINKED_SYMBOLS - set(symbols))
        if missing:
            _fail(f"Mega shop export不足: {missing}")
        payload = binary.read_bytes()
        if not payload or len(payload) > 96 * 1024:
            _fail(f"Mega shop runtime size不一致: {len(payload)}")
        executables = {}
        for role, executable in (("compiler", compiler), ("objcopy", objcopy), ("nm", nm)):
            resolved = Path(executable).resolve()
            executable_raw = resolved.read_bytes()
            version = _run([executable, "--version"], f"{role} version").splitlines()[0]
            executables[role] = {
                "path": executable,
                "resolved_path": str(resolved),
                "size": len(executable_raw),
                "sha256": _sha(executable_raw),
                "version": version,
            }
        provenance = {
            "executables": executables,
            "compile_flags": compile_flags,
            "include_roots": [
                "<temporary-generated-header-directory>",
                ".",
                "overlays/modernization_mega_shop",
                "overlays/save_migration",
            ],
            "link_flags": [flag if not flag.startswith("-Wl,-T,")
                           else "-Wl,-T,<generated-linker-script>"
                           for flag in link_flags],
            "link_libraries": ["libgcc"],
            "linker_script_sha256": _sha(linker_text.encode("ascii")),
            "load_address": load_address,
        }
        return payload, symbols, provenance


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
    texts: dict[str, Any] = {}
    for label, text in TEXTS.items():
        encoded = _encode_text(text, mapping, tokens)
        blob.add(label, encoded, 1)
        texts[label] = {"text": text, "size": len(encoded), "sha256": _sha(encoded)}
    _add_script(
        blob, "script_mega_shop_npc",
        _Script().emit(0x6A, 0x5A).callnative("MegaShop_Open")
        .compare_result(9).if_equal("script_mega_shop_wait")
        .goto("script_mega_shop_result"),
    )
    _add_script(
        blob, "script_mega_shop_wait",
        _Script().emit(0x27).callnative("MegaShop_PostMenu")
        .goto("script_mega_shop_result"),
    )
    result = _Script()
    for value, label in (
        (0, "script_mega_shop_success"),
        (2, "script_mega_shop_end"),
        (3, "script_mega_shop_locked"),
        (13, "script_mega_shop_persist"),
        (14, "script_mega_shop_insufficient"),
        (15, "script_mega_shop_full"),
        (17, "script_mega_shop_claimed"),
        (18, "script_mega_shop_all_claimed"),
    ):
        result.compare_result(value).if_equal(label)
    result.goto("script_mega_shop_error")
    _add_script(blob, "script_mega_shop_result", result)
    for label, text_label in (
        ("script_mega_shop_success", "text_mega_shop_success"),
        ("script_mega_shop_locked", "text_mega_shop_locked"),
        ("script_mega_shop_claimed", "text_mega_shop_claimed"),
        ("script_mega_shop_all_claimed", "text_mega_shop_all_claimed"),
        ("script_mega_shop_persist", "text_mega_shop_persist"),
        ("script_mega_shop_insufficient", "text_mega_shop_insufficient"),
        ("script_mega_shop_full", "text_mega_shop_full"),
        ("script_mega_shop_error", "text_mega_shop_error"),
    ):
        _add_script(blob, label, _Script().msgbox(text_label).goto("script_mega_shop_end"))
    _add_script(blob, "script_mega_shop_end", _Script().emit(0x6C, 0x02))
    return {"texts": texts, "busy_result": 9, "uses_waitstate": True}


def _lz77_literal(raw: bytes) -> bytes:
    if not raw or len(raw) >= 1 << 24:
        _fail("LZ77入力size不一致")
    output = bytearray((0x10, len(raw) & 0xFF, (len(raw) >> 8) & 0xFF, (len(raw) >> 16) & 0xFF))
    for start in range(0, len(raw), 8):
        output.append(0)
        output.extend(raw[start:start + 8])
    while len(output) & 3:
        output.append(0)
    return bytes(output)


def _entry_header(stage: bytes, group_id: int, map_id: int) -> tuple[int, int]:
    root_pointer = _u32(stage, MAP_GROUPS_POINTER_SITE, "gMapGroups root")
    root = _rom_offset(root_pointer, 99 * 4, "gMapGroups root")
    group_pointer = _u32(stage, root + group_id * 4, "Factory map group")
    group = _rom_offset(group_pointer, (map_id + 1) * 4, "Factory map group")
    header_pointer = _u32(stage, group + map_id * 4, "Factory map header")
    header = _rom_offset(header_pointer, 0x1C, "Factory map header")
    return header, header_pointer


def _add_map_runtime(stage: bytes, config: Mapping[str, Any], blob: _Blob) -> dict[str, Any]:
    map_config = config["map"]
    group_id = _integer(map_config["group"], "map group")
    map_id = _integer(map_config["map"], "map id")
    local_id = _integer(map_config["local_id"], "local id")
    clone_id = _integer(map_config["clone_local_id"], "clone local id")
    header, header_pointer = _entry_header(stage, group_id, map_id)
    events_pointer = _u32(stage, header + 4, "Factory events root")
    scripts_pointer = _u32(stage, header + 8, "Factory scripts root")
    events = _rom_offset(events_pointer, 0x14, "Factory events")
    old_events = bytearray(stage[events:events + 0x14])
    old_count = old_events[0]
    objects_pointer = _u32(stage, events + 4, "Factory object table")
    objects = _rom_offset(objects_pointer, old_count * 0x18, "Factory objects")
    old_objects = stage[objects:objects + old_count * 0x18]
    ids = [old_objects[index * 0x18] for index in range(old_count)]
    if ids != list(range(1, old_count + 1)) or local_id in ids or local_id != old_count + 1:
        _fail(f"Factory local ID連続性不一致: before={ids} requested={local_id}")
    matches = [old_objects[index * 0x18:(index + 1) * 0x18]
               for index in range(old_count) if ids[index] == clone_id]
    if len(matches) != 1:
        _fail("Factory clone NPCを一意に解決できません")
    shop = bytearray(matches[0])
    shop[0] = local_id
    struct.pack_into("<HH", shop, 4, _integer(map_config["x"], "map x"),
                     _integer(map_config["y"], "map y"))
    struct.pack_into("<I", shop, 0x10, 0)
    object_offset = blob.add("mega_shop_factory_objects", old_objects + bytes(shop), 4)
    blob.pointer(object_offset + old_count * 0x18 + 0x10, "script_mega_shop_npc")
    old_events[0] = old_count + 1
    struct.pack_into("<I", old_events, 4, 0)
    event_offset = blob.add("mega_shop_factory_events", bytes(old_events), 4)
    blob.pointer(event_offset + 4, "mega_shop_factory_objects")
    return {
        "group_id": group_id,
        "map_id": map_id,
        "header_offset": header,
        "header_address": header_pointer,
        "old_events_pointer": events_pointer,
        "old_scripts_pointer": scripts_pointer,
        "old_event_counts": list(stage[events:events + 4]),
        "old_objects_sha256": _sha(old_objects),
        "object_count_before": old_count,
        "object_count_after": old_count + 1,
        "shop_object": {
            "local_id": local_id,
            "graphics_id": shop[1],
            "movement_type": shop[9],
            "x": _integer(map_config["x"], "map x"),
            "y": _integer(map_config["y"], "map y"),
            "source_clone_local_id": clone_id,
        },
        "existing_objects_preserved": True,
        "map_scripts_preserved": True,
    }


def _add_item_assets_and_tables(
    root: Path,
    stage: bytes,
    config: Mapping[str, Any],
    catalog: Sequence[Mapping[str, Any]],
    blob: _Blob,
) -> dict[str, Any]:
    table_config = config["item_tables"]
    asset_root = root / config["inputs"]["asset_root"]
    mapping, tokens = _charmap(root)
    description = _encode_text("メガシンカを おこす ふしぎないし", mapping, tokens)
    blob.add("mega_shop_item_description", description, 1)
    stream_labels: dict[tuple[str, str], str] = {}

    def stream_label(kind: str, relative: str, expected_sha: str) -> str:
        key = (kind, expected_sha)
        if key in stream_labels:
            return stream_labels[key]
        raw = (asset_root / relative).read_bytes()
        if _sha(raw) != expected_sha:
            _fail(f"asset hashがcatalog生成後に変化しました: {relative}")
        label = f"mega_shop_{kind}_{len(stream_labels):03d}"
        blob.add(label, _lz77_literal(raw), 4)
        stream_labels[key] = label
        return label

    row_pointer_fixups: list[tuple[int, str]] = []
    table_meta: dict[str, Any] = {}
    template_id = _integer(table_config["template_item_id"], "template item")
    for table_key in ("item_data", "item_effect_pointer2", "item_fling", "item_graphics", "item_type_by_id"):
        spec = table_config[table_key]
        address = _integer(spec["address"], f"{table_key}.address")
        stride = _integer(spec["stride"], f"{table_key}.stride")
        old_count = _integer(spec["old_count"], f"{table_key}.old_count")
        new_count = _integer(spec["new_count"], f"{table_key}.new_count")
        old_offset = _rom_offset(address, old_count * stride, table_key)
        old_raw = stage[old_offset:old_offset + old_count * stride]
        if table_key == "item_data":
            template = old_raw[template_id * stride:(template_id + 1) * stride]
            appended = bytearray()
            for row in catalog:
                item = bytearray(template)
                item[:10] = bytes.fromhex(str(row["display_name_hex"]))
                struct.pack_into("<H", item, 10, _integer(row["item_id"], "item id"))
                struct.pack_into("<H", item, 12, 0)
                struct.pack_into("<I", item, 16, 0)
                appended.extend(item)
            table_raw = old_raw + bytes(appended)
        elif table_key == "item_graphics":
            table_raw = bytearray(old_raw + bytes(len(catalog) * stride))
        elif table_key == "item_type_by_id":
            table_raw = old_raw + b"".join(struct.pack("<H", 50) for _ in catalog)
        else:
            template = old_raw[template_id * stride:(template_id + 1) * stride]
            table_raw = old_raw + template * len(catalog)
        if len(table_raw) != new_count * stride:
            _fail(f"{table_key} new table size不一致")
        label = f"mega_shop_table_{table_key}"
        table_offset = blob.add(label, bytes(table_raw), 4)
        if table_key == "item_data":
            for index in range(len(catalog)):
                blob.pointer(table_offset + (old_count + index) * stride + 16,
                             "mega_shop_item_description")
        elif table_key == "item_graphics":
            for index, row in enumerate(catalog):
                icon_label = stream_label("icon_lz", str(row["icon_relative_path"]), str(row["icon_sha256"]))
                palette_label = stream_label("palette_lz", str(row["palette_relative_path"]), str(row["palette_sha256"]))
                blob.pointer(table_offset + (old_count + index) * stride, icon_label)
                blob.pointer(table_offset + (old_count + index) * stride + 4, palette_label)
        table_meta[table_key] = {
            "old_address": address,
            "old_count": old_count,
            "new_count": new_count,
            "stride": stride,
            "old_sha256": _sha(old_raw),
            "new_size": len(table_raw),
            "new_sha256_before_pointer_fixup": _sha(table_raw),
            "label": label,
        }
    return {
        "tables": table_meta,
        "description_size": len(description),
        "description_sha256": _sha(description),
        "unique_lz77_stream_count": len(stream_labels),
        "lz77_encoding": "GBA_LZ77_LITERAL_ONLY_DETERMINISTIC",
    }


def _build_payload(
    root: Path,
    stage: bytes,
    config: Mapping[str, Any],
    catalog: Sequence[Mapping[str, Any]],
    generated_header: bytes,
    payload_offset: int,
) -> tuple[bytes, dict[str, Any]]:
    blob = _Blob()
    header_offset = blob.reserve("mega_shop_payload_header", PAYLOAD_HEADER_SIZE, 16)
    code_load = GBA_ROM_BASE + payload_offset + ((len(blob.data) + 3) & ~3)
    code, code_symbols, toolchain = _compile_runtime(
        root, code_load, generated_header,
    )
    code_offset = blob.add("mega_shop_runtime_code", code, 4)
    if GBA_ROM_BASE + payload_offset + code_offset != code_load:
        _fail("Mega shop linker/payload address不一致")
    for name, address in code_symbols.items():
        relative = address - code_load
        if 0 <= relative < len(code):
            blob.labels[f"native::{name}"] = code_offset + relative
    script_meta = _build_scripts(root, blob)
    map_meta = _add_map_runtime(stage, config, blob)
    item_meta = _add_item_assets_and_tables(root, stage, config, catalog, blob)
    runtime_size = len(blob.data)
    struct.pack_into(
        "<8sIIIIIIIIIII", blob.data, header_offset,
        b"VEGAMS68", 1, runtime_size, len(code), 45, 999, 1044,
        0x14A0, 0x14CC, 580, map_meta["object_count_after"], 0,
    )
    for offset, label, thumb in (
        (52, "native::MegaShop_Probe", True),
        (56, "native::MegaShop_Open", True),
        (60, "native::MegaShop_PurchaseByIndex", True),
        (64, "script_mega_shop_npc", False),
        (68, "mega_shop_factory_events", False),
        (72, "mega_shop_table_item_data", False),
        (76, "mega_shop_table_item_graphics", False),
        (80, "mega_shop_table_item_effect_pointer2", False),
        (84, "mega_shop_table_item_fling", False),
        (88, "mega_shop_table_item_type_by_id", False),
    ):
        blob.pointer(header_offset + offset, label, thumb=thumb)
    payload = blob.finish(payload_offset)
    base = GBA_ROM_BASE + payload_offset
    labels = {label: base + relative for label, relative in sorted(blob.labels.items())}
    map_meta.update({
        "events_after_address": labels["mega_shop_factory_events"],
        "objects_after_address": labels["mega_shop_factory_objects"],
        "shop_script_address": labels["script_mega_shop_npc"],
    })
    for key, record in item_meta["tables"].items():
        record["new_address"] = labels[record.pop("label")]
        offset = record["new_address"] - GBA_ROM_BASE - payload_offset
        record["new_sha256"] = _sha(payload[offset:offset + record["new_size"]])
    return payload, {
        "payload": {
            "magic": "VEGAMS68",
            "offset": payload_offset,
            "address": base,
            "size": len(payload),
            "sha256": _sha(payload),
            "code_offset": payload_offset + code_offset,
            "code_address": code_load,
            "code_size": len(code),
            "code_sha256": _sha(code),
        },
        "entrypoints": {name: code_symbols[name] | 1 for name in sorted(REQUIRED_ENTRYPOINTS)},
        "linked_symbols": {name: code_symbols[name] | 1 for name in sorted(REQUIRED_LINKED_SYMBOLS)},
        "toolchain": toolchain,
        "scripts": {**script_meta, "npc_address": labels["script_mega_shop_npc"]},
        "map": map_meta,
        "item_materialization": item_meta,
        "labels": labels,
    }


def _previous_requests(allocation: Mapping[str, Any]) -> list[dict[str, object]]:
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


def _allocation(root: Path, previous: Mapping[str, Any], size: int, digest: str) -> tuple[dict[str, Any], dict[str, Any]]:
    requests = _previous_requests(previous)
    requests.append({
        "name": ALLOCATION_NAME,
        "region": "integration_modules",
        "size": size,
        "alignment": 16,
        "owner": TASK,
        "purpose": "45 Mega Stone item tables/assets, BP shop runtime, and Factory NPC",
        "content_sha256": digest,
    })
    report = build_allocation_report_from_csv(root / "config/rom_regions.csv", requests)
    if report.get("summaries", {}).get("overlap_count") != 0:
        _fail("Stage68 allocator overlapを検出しました")
    matches = [row for row in report["allocations"] if row["name"] == ALLOCATION_NAME]
    if len(matches) != 1:
        _fail("Stage68 allocationを一意に解決できません")
    return matches[0], report


def _apply_pointer_repoints(
    output: bytearray,
    stage: bytes,
    capacity: Mapping[str, Any],
    allowlist: Mapping[str, Any],
    runtime: Mapping[str, Any],
) -> list[dict[str, Any]]:
    literal_inventory = capacity["consumer_audit"]["stage65_exact_literal_candidates"]
    if allowlist.get("policy") != "PATCH_ONLY_EXPLICIT_SEMANTIC_OWNER_SITES_WITH_EXACT_CONTEXT":
        _fail("pointer site allowlist policy不一致")
    groups = allowlist.get("tables")
    if not isinstance(groups, list):
        _fail("pointer site allowlist tablesがarrayではありません")
    allow_by_key = {row.get("table_key"): row for row in groups}
    if len(allow_by_key) != len(groups):
        _fail("pointer site allowlist table keyが重複しています")
    patches: list[dict[str, Any]] = []
    for key, table in runtime["item_materialization"]["tables"].items():
        old = _integer(table["old_address"], f"{key}.old_address")
        new = _integer(table["new_address"], f"{key}.new_address")
        inventory = literal_inventory[key]
        expected_sites = inventory["site_offsets"]
        observed = _all_offsets(stage, struct.pack("<I", old))
        if observed != expected_sites:
            _fail(f"{key} literal site集合がP04監査から変化しました")
        group = allow_by_key.get(key)
        if not isinstance(group, dict):
            _fail(f"{key} pointer site allowlistがありません")
        rows = group.get("sites")
        if not isinstance(rows, list):
            _fail(f"{key} pointer site allowlist rows不一致")
        allowed_sites = [_integer(row.get("site_offset"), f"{key}.site_offset")
                         for row in rows]
        if (allowed_sites != expected_sites
                or group.get("site_count") != len(expected_sites)
                or _integer(group.get("old_address"), f"{key}.old_address") != old
                or group.get("capacity_site_set_sha256") != inventory["site_set_sha256"]):
            _fail(f"{key} semantic allowlistがP04 site inventoryと一致しません")
        owners: list[str] = []
        for row, site in zip(rows, allowed_sites):
            owner = row.get("semantic_owner")
            evidence = row.get("semantic_evidence")
            if not isinstance(owner, str) or not owner or owner == "UNCLASSIFIED" \
                    or not isinstance(evidence, str) or not evidence:
                _fail(f"{key} site 0x{site:X}のsemantic owner/evidence不足")
            context_offset = _integer(row.get("context_offset"), f"{key}.context_offset")
            pointer_in_context = _integer(
                row.get("pointer_offset_in_context"), f"{key}.pointer_offset",
            )
            expected_context = bytes.fromhex(str(row.get("expected_context_hex", "")))
            if (context_offset + pointer_in_context != site
                    or len(expected_context) != allowlist.get("context_bytes")
                    or _sha(expected_context) != row.get("expected_context_sha256")
                    or stage[context_offset:context_offset + len(expected_context)] != expected_context
                    or struct.unpack_from("<I", expected_context, pointer_in_context)[0] != old):
                _fail(f"{key} site 0x{site:X}のexpected context不一致")
            struct.pack_into("<I", output, site, new)
            owners.append(owner)
        patches.append({
            "table_key": key,
            "old_address": old,
            "new_address": new,
            "site_count": len(allowed_sites),
            "site_offsets": allowed_sites,
            "site_set_sha256": _sha(b"".join(struct.pack("<I", value) for value in allowed_sites)),
            "semantic_owner_count": len(set(owners)),
            "semantic_owners": sorted(set(owners)),
            "policy": allowlist["policy"],
            "all_literal_matches_allowlisted": observed == allowed_sites,
            "all_contexts_exact": True,
        })
    if set(allow_by_key) != set(runtime["item_materialization"]["tables"]):
        _fail("pointer site allowlistに過不足tableがあります")
    return patches


def _patch_sanitizer(output: bytearray, stage: bytes, config: Mapping[str, Any]) -> dict[str, Any]:
    spec = config["item_sanitizer"]
    address = _integer(spec["address"], "item sanitizer address")
    offset = _rom_offset(address, len(ITEM_SANITIZER_REPLACEMENT), "item sanitizer")
    expected = bytes.fromhex(str(spec["expected_hex"]))
    if len(expected) != len(ITEM_SANITIZER_REPLACEMENT) or stage[offset:offset + len(expected)] != expected:
        _fail("item sanitizer expected bytes不一致")
    output[offset:offset + len(expected)] = ITEM_SANITIZER_REPLACEMENT
    return {
        "site_address": address,
        "site_offset": offset,
        "expected_hex": expected.hex(),
        "replacement_hex": ITEM_SANITIZER_REPLACEMENT.hex(),
        "valid_max_exclusive_before": 999,
        "valid_max_exclusive_after": 1044,
        "thumb_disposition": "u16 normalize; compare against (255+6)<<2; invalid->ITEM_NONE",
    }


def _patch_cfru_item_bounds(
    output: bytearray,
    stage: bytes,
    bounds: Mapping[str, Any],
) -> dict[str, Any]:
    if bounds.get("policy") != "PATCH_ONLY_CFRU_ITEM_C_SEMANTIC_MAX_INCLUSIVE_LITERALS":
        _fail("CFRU item bound allowlist policy不一致")
    old_max = _integer(bounds.get("old_max_inclusive"), "old item max")
    new_max = _integer(bounds.get("new_max_inclusive"), "new item max")
    first_rejected = _integer(bounds.get("first_rejected"), "first rejected item")
    rows = bounds.get("sites")
    if (old_max, new_max, first_rejected) != (998, 1043, 1044) \
            or not isinstance(rows, list) or bounds.get("site_count") != 12 \
            or len(rows) != 12:
        _fail("CFRU item bound 998->1043 contract不一致")
    sites = [_integer(row.get("site_offset"), "item bound site") for row in rows]
    if sites != sorted(set(sites)):
        _fail("CFRU item bound siteが一意昇順ではありません")
    cluster_start = 0x0110F000
    cluster_end = 0x01120000
    observed_cluster = [
        site for site in _all_offsets(stage, struct.pack("<I", old_max))
        if cluster_start <= site < cluster_end
    ]
    if observed_cluster != sites:
        _fail(
            "CFRU item.c clusterの998 literalとsemantic allowlistが一致しません: "
            f"observed={observed_cluster} allowed={sites}"
        )
    owners: list[str] = []
    for row, site in zip(rows, sites):
        owner = row.get("semantic_owner")
        evidence = row.get("semantic_evidence")
        context_offset = _integer(row.get("context_offset"), "item bound context")
        literal_offset = _integer(
            row.get("literal_offset_in_context"), "item bound literal offset",
        )
        context = bytes.fromhex(str(row.get("expected_context_hex", "")))
        if (not isinstance(owner, str) or not owner.startswith("CFRU_")
                or not isinstance(evidence, str) or not evidence
                or context_offset + literal_offset != site
                or len(context) != 20
                or _sha(context) != row.get("expected_context_sha256")
                or stage[context_offset:context_offset + len(context)] != context
                or struct.unpack_from("<I", context, literal_offset)[0] != old_max):
            _fail(f"CFRU item bound site 0x{site:X}のsemantic/context不一致")
        struct.pack_into("<I", output, site, new_max)
        owners.append(owner)
    if any(struct.unpack_from("<I", output, site)[0] != new_max for site in sites):
        _fail("CFRU item bound patch反映不一致")
    return {
        "old_max_inclusive": old_max,
        "new_max_inclusive": new_max,
        "first_rejected": first_rejected,
        "site_count": len(sites),
        "site_offsets": sites,
        "semantic_owners": owners,
        "all_item_c_cluster_998_literals_allowlisted": True,
        "all_contexts_exact": True,
        "explicit_exclusions": bounds.get("explicit_exclusions"),
    }


def _flag_namespace_audit(root: Path, config: Mapping[str, Any]) -> dict[str, Any]:
    rows = _rows(root / config["inputs"]["flags_manifest"])
    used: dict[int, dict[str, str]] = {}
    for row in rows:
        try:
            flag = int(row["id"], 0)
        except (KeyError, ValueError):
            continue
        used[flag] = row
    first = _integer(config["catalog"]["claim_flag_first"], "claim flag first")
    last = _integer(config["catalog"]["claim_flag_last"], "claim flag last")
    collisions = {
        f"0x{flag:04X}": used[flag].get("flag_key", "")
        for flag in range(first, last + 1)
        if flag in used
    }
    if collisions:
        _fail(f"Mega shop claim flag衝突: {collisions}")
    predecessor = max((flag for flag in used if flag < first), default=-1)
    if predecessor != 0x149D:
        _fail("claim範囲直前の既存flag終端が0x149Dではありません")
    if any(flag in used for flag in (0x149E, 0x149F)):
        _fail("0x149E/0x149Fの意図したgapが占有されています")
    if last >= 0x1500:
        _fail("Mega shop flagが次owner境界0x1500に到達しました")
    return {
        "status": "PASS_DEDICATED_STAGE68_ALLOCATION",
        "first": first,
        "last": last,
        "count": last - first + 1,
        "collision_count": 0,
        "global_manifest_rows_present": 0,
        "existing_predecessor": "0x149D",
        "intentional_gap": ["0x149E", "0x149F"],
        "next_owner_boundary": "0x1500",
        "storage": "CFRU expanded event flags, standard-save persisted, legacy zero default",
        "flags_manifest_mutated": False,
        "source_of_truth": "config/modernization_mega_shop.json + generated catalog",
    }


def _runtime_boundaries(config: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "codex": {
            "status": "EXPLICITLY_EXCLUDED_NOT_TRUNCATED",
            "reason": config["runtime_boundaries"]["codex"],
            "current_safe_max_item_id": 998,
            "new_item_ids_admitted": 0,
            "ten_bit_public_event_reached_by_new_items": False,
        },
        "mirage": {
            "status": "EXPLICITLY_EXCLUDED_NOT_TRUNCATED",
            "reason": config["runtime_boundaries"]["mirage"],
            "new_item_ids_admitted": 0,
            "ten_bit_probe_reached_by_new_items": False,
        },
        "item_obtained_bitmap": {
            "status": "UNCHANGED_BY_DESIGN",
            "reason": config["runtime_boundaries"]["item_obtained_bitmap"],
            "claim_owner": "expanded event flags 0x14A0..0x14CC",
        },
    }


def _file_binding(root: Path, relative: str) -> dict[str, Any]:
    path = root / relative
    if not path.is_file():
        _fail(f"source binding対象がありません: {relative}")
    raw = path.read_bytes()
    return {"path": relative, "size": len(raw), "sha256": _sha(raw)}


def _source_bindings(
    root: Path,
    config: Mapping[str, Any],
    catalog: Sequence[Mapping[str, Any]],
    generated_header: bytes,
    toolchain: Mapping[str, Any],
) -> dict[str, Any]:
    inputs = config["inputs"]
    paths = {
        str(CONFIG),
        str(inputs["rom"]["path"]),
        str(inputs["metadata"]["path"]),
        str(inputs["allocation"]["path"]),
        str(inputs["candidate_manifest"]["path"]),
        str(inputs["asset_manifest"]["path"]),
        str(inputs["capacity_manifest"]["path"]),
        str(inputs["species_manifest"]),
        str(inputs["flags_manifest"]),
        str(inputs["pointer_site_allowlist"]["path"]),
        str(inputs["item_bound_allowlist"]["path"]),
        "config/rom_regions.csv",
        "vendor/upstream/CFRU-JP/charmap.tbl",
        "overlays/modernization_mega_shop/modernization_mega_shop.c",
        "overlays/modernization_mega_shop/modernization_mega_shop.h",
        "overlays/modernization_mega_shop/modernization_mega_shop_host_harness.c",
        "overlays/modernization_mega_shop/README.md",
        "overlays/bp_shop_runtime/bp_shop_libc.c",
        "overlays/save_migration/save_migration.c",
        "overlays/save_migration/save_migration.h",
        "tools/modernization_mega_shop.py",
        "scripts/build_modernization_mega_shop.py",
        "tools/regression/rom_runtime.py",
        "tools/release/bps.py",
        "tools/rom_allocator.py",
        "tests/test_modernization_mega_shop.py",
    }
    files = [_file_binding(root, relative) for relative in sorted(paths)]
    asset_rows: list[dict[str, Any]] = []
    asset_root = root / str(inputs["asset_root"])
    for row in catalog:
        for role in ("icon", "palette"):
            relative = str(row[f"{role}_relative_path"])
            raw = (asset_root / relative).read_bytes()
            expected = str(row[f"{role}_sha256"])
            if _sha(raw) != expected:
                _fail(f"source binding asset hash不一致: {relative}")
            asset_rows.append({
                "role": role,
                "path": f"{inputs['asset_root']}/{relative}",
                "size": len(raw),
                "sha256": expected,
            })
    asset_inventory = _stable(asset_rows)
    return {
        "files": files,
        "file_count": len(files),
        "file_inventory_sha256": _sha(_stable(files)),
        "p04_asset_payload": {
            "file_count": len(asset_rows),
            "total_bytes": sum(row["size"] for row in asset_rows),
            "inventory_sha256": _sha(asset_inventory),
            "files": asset_rows,
        },
        "generated_catalog_header": {
            "size": len(generated_header),
            "sha256": _sha(generated_header),
        },
        "arm_toolchain": dict(toolchain),
    }


def _run_host_harness(root: Path, generated_header: bytes) -> dict[str, Any]:
    compiler = shutil.which("cc")
    if not compiler:
        _fail("Mega shop host harnessにC compilerが必要です")
    flags = ["-std=c11", "-O2", "-Wall", "-Wextra", "-Werror"]
    with tempfile.TemporaryDirectory(prefix="vega-mega-shop-host-") as temporary:
        directory = Path(temporary)
        (directory / "modernization_mega_shop_catalog_generated.h").write_bytes(
            generated_header,
        )
        executable = directory / "modernization_mega_shop_host"
        command = [
            compiler, *flags,
            f"-I{directory}", f"-I{root}",
            f"-I{root / 'overlays/modernization_mega_shop'}",
            f"-I{root / 'overlays/save_migration'}",
            str(root / "overlays/modernization_mega_shop/modernization_mega_shop_host_harness.c"),
            str(root / "overlays/save_migration/save_migration.c"),
            "-o", str(executable),
        ]
        _run(command, "compile Mega shop host harness", cwd=root)
        raw_result = _run([str(executable)], "run Mega shop host harness", cwd=root)
    try:
        result = json.loads(raw_result.splitlines()[-1])
    except (IndexError, json.JSONDecodeError) as error:
        _fail(f"Mega shop host harness output不一致: {error}: {raw_result!r}")
    if (result.get("status") != "PASS" or result.get("failures") != 0
            or result.get("catalog_entries") != 45
            or result.get("failure_injection_cases") != 2
            or _integer(result.get("assertions"), "host assertions") < 240):
        _fail(f"Mega shop host harness不合格: {result}")
    resolved = Path(compiler).resolve()
    compiler_raw = resolved.read_bytes()
    return {
        **result,
        "cases": [
            "45 catalog success paths",
            "locked and invalid pure preflight on empty save",
            "once rejection before and after fresh load",
            "insufficient BP and bag full pure on initialized save",
            "standard-save first-write failure compensation",
            "sector31 first-write failure compensation",
            "empty unlocked save initialization distinguished",
        ],
        "compiler": {
            "path": compiler,
            "resolved_path": str(resolved),
            "size": len(compiler_raw),
            "sha256": _sha(compiler_raw),
            "version": _run([compiler, "--version"], "host compiler version").splitlines()[0],
            "flags": flags,
        },
        "generated_header_sha256": _sha(generated_header),
    }


def build_outputs(root: Path = ROOT) -> dict[str, bytes]:
    root = Path(root)
    (config, stage, stage_meta, previous_alloc, candidate, asset, capacity,
     pointer_allowlist, item_bounds) = _load_contract(root)
    catalog, generated_header, catalog_json = _catalog_outputs(
        root, config, candidate, asset, capacity,
    )
    preliminary, _ = _build_payload(root, stage, config, catalog, generated_header, 0)
    allocation, _ = _allocation(root, previous_alloc, len(preliminary), "0" * 64)
    payload_offset = _integer(allocation["start"], "payload start")
    payload, runtime = _build_payload(
        root, stage, config, catalog, generated_header, payload_offset,
    )
    if len(payload) != len(preliminary):
        _fail("load addressによりpayload sizeが変化しました")
    allocation, allocation_report = _allocation(root, previous_alloc, len(payload), _sha(payload))
    if _integer(allocation["start"], "final payload start") != payload_offset:
        _fail("final payload allocationが変化しました")
    payload_end = _integer(allocation["end_exclusive"], "payload end")
    if stage[payload_offset:payload_end] != b"\xFF" * len(payload):
        _fail("Stage68 payload配置先がerased FFではありません")

    output = bytearray(stage)
    output[payload_offset:payload_end] = payload
    pointer_patches = _apply_pointer_repoints(
        output, stage, capacity, pointer_allowlist, runtime,
    )
    sanitizer = _patch_sanitizer(output, stage, config)
    cfru_item_bounds = _patch_cfru_item_bounds(output, stage, item_bounds)
    map_meta = runtime["map"]
    map_site = _integer(map_meta["header_offset"], "map header offset") + 4
    if _u32(stage, map_site, "Factory event root") != map_meta["old_events_pointer"]:
        _fail("Factory event root expected pointer不一致")
    struct.pack_into("<I", output, map_site, map_meta["events_after_address"])
    if _u32(output, map_site + 4, "Factory scripts root") != map_meta["old_scripts_pointer"]:
        _fail("Factory map scripts rootを変更しました")

    allowed = [(payload_offset, payload_end), (map_site, map_site + 4),
               (sanitizer["site_offset"], sanitizer["site_offset"] + len(ITEM_SANITIZER_REPLACEMENT))]
    for patch in pointer_patches:
        allowed.extend((site, site + 4) for site in patch["site_offsets"])
    allowed.extend((site, site + 4) for site in cfru_item_bounds["site_offsets"])
    outside = [index for index, (before, after) in enumerate(zip(stage, output))
               if before != after and not any(start <= index < end for start, end in allowed)]
    if outside:
        _fail(f"宣言span外を変更しました: {outside[:8]}")
    output_raw = bytes(output)
    patch_raw = create_bps(stage, output_raw)
    if apply_bps(stage, patch_raw) != output_raw:
        _fail("Stage67→68 BPS round-trip不一致")
    flags = _flag_namespace_audit(root, config)
    boundaries = _runtime_boundaries(config)
    host_harness = _run_host_harness(root, generated_header)
    source_bindings = _source_bindings(
        root, config, catalog, generated_header, runtime["toolchain"],
    )
    outputs = config["outputs"]
    metadata = {
        "schema_version": 1,
        "task": TASK,
        "stage": 68,
        "status": "PASS_HOST_STATIC_EXACT_ROM_PENDING",
        "parent": {"stage": 67, "task": stage_meta.get("task")},
        "input": {
            "path": config["inputs"]["rom"]["path"],
            "size": len(stage),
            "sha256": _sha(stage),
            "allocation_path": config["inputs"]["allocation"]["path"],
        },
        "source_bindings": source_bindings,
        "output": {"path": outputs["rom"], "size": len(output_raw), "sha256": _sha(output_raw)},
        **runtime,
        "catalog": {
            "path": outputs["catalog"],
            "entry_count": len(catalog),
            "item_ids": [row["item_id"] for row in catalog],
            "claim_flags": [row["claim_flag"] for row in catalog],
            "prices_bp": sorted({row["price_bp"] for row in catalog}),
            "page_size": 5,
            "page_count": 9,
            "key_stone_item_id": 580,
        },
        "pointer_repoints": pointer_patches,
        "item_sanitizer": sanitizer,
        "cfru_item_bounds": cfru_item_bounds,
        "flag_namespace": flags,
        "transaction": {
            "order": ["AddBagItem", "VegaFactorySpendBattlePoints", "FlagSet(claim)", "TrySavingData(0)", "TryWriteSector(31)"],
            "rollback": ["FlagClear(claim)", "restore exact BP", "VegaSaveFinalize", "RemoveBagItem", "best-effort standard save", "best-effort sector31"],
            "pure_preflight_results_even_on_empty_save": [3, 5, 17],
            "initialized_save_no_mutation_results": [3, 5, 14, 15, 17],
            "one_per_save_owner": "expanded event flags 0x14A0..0x14CC",
        },
        "runtime_boundaries": boundaries,
        "allocation": {
            "path": outputs["allocation"],
            "name": ALLOCATION_NAME,
            "overlap_count": allocation_report["summaries"]["overlap_count"],
            "remaining_allocatable_bytes": allocation_report["summaries"]["remaining_allocatable_bytes"],
        },
        "release_patch_round_trip": {
            "format": "BPS1",
            "source_sha256": _sha(stage),
            "target_sha256": _sha(output_raw),
            "size": len(patch_raw),
            "sha256": _sha(patch_raw),
            "exact": True,
        },
        "validation": {
            "exact_rom_runtime_smoke": "PENDING",
            "heavy_test_runs": 0,
            "static_and_host_checks": "PASS",
            "host_harness": host_harness,
        },
        "invariants": {
            "rom_size_32_mib": len(output_raw) == ROM_SIZE,
            "catalog_45": len(catalog) == 45,
            "item_ids_999_through_1043": [row["item_id"] for row in catalog] == list(range(999, 1044)),
            "claim_flags_45_unique": len({row["claim_flag"] for row in catalog}) == 45,
            "all_prices_16_bp": {row["price_bp"] for row in catalog} == {16},
            "five_rows_nine_pages": len(catalog) == 5 * 9,
            "mega_ring_gate_item_580": config["catalog"]["key_stone_item_id"] == 580,
            "item_tables_1044_rows": all(row["new_count"] == 1044 for row in runtime["item_materialization"]["tables"].values()),
            "all_old_table_literals_repointed": all(
                not _all_offsets(output_raw, struct.pack("<I", row["old_address"]))
                for row in runtime["item_materialization"]["tables"].values()
            ),
            "item_sanitizer_1044": sanitizer["valid_max_exclusive_after"] == 1044,
            "cfru_item_bounds_999_through_1043": (
                cfru_item_bounds["new_max_inclusive"] == 1043
                and cfru_item_bounds["first_rejected"] == 1044
                and cfru_item_bounds["site_count"] == 12
            ),
            "physical_npc_local14": map_meta["shop_object"]["local_id"] == 14,
            "existing_13_objects_preserved": map_meta["object_count_before"] == 13 and map_meta["existing_objects_preserved"],
            "allocator_overlap_zero": allocation_report["summaries"]["overlap_count"] == 0,
            "declared_spans_only": True,
            "bps_exact": True,
            "codex_narrow_id_boundary_explicit": boundaries["codex"]["new_item_ids_admitted"] == 0,
            "mirage_narrow_id_boundary_explicit": boundaries["mirage"]["new_item_ids_admitted"] == 0,
        },
    }
    if not all(metadata["invariants"].values()):
        failed = [key for key, value in metadata["invariants"].items() if not value]
        _fail(f"Stage68 invariant失敗: {failed}")
    symbols = {
        "schema_version": 1,
        "task": TASK,
        "payload": runtime["payload"],
        "entrypoints": runtime["entrypoints"],
        "linked_symbols": runtime["linked_symbols"],
        "scripts": runtime["scripts"],
        "map": runtime["map"],
        "item_tables": runtime["item_materialization"]["tables"],
    }
    checkpoint = {
        "schema_version": 1,
        "task": TASK,
        "stage": 68,
        "status": metadata["status"],
        "rom": metadata["output"],
        "catalog": metadata["catalog"],
        "payload": metadata["payload"],
        "table_repoint_counts": {row["table_key"]: row["site_count"] for row in pointer_patches},
        "cfru_item_bounds": cfru_item_bounds,
        "transaction": metadata["transaction"],
        "runtime_boundaries": boundaries,
        "validation": metadata["validation"],
        "source_bindings": source_bindings,
    }
    return {
        outputs["rom"]: output_raw,
        outputs["metadata"]: _stable(metadata),
        outputs["allocation"]: _stable(allocation_report),
        outputs["runtime_bin"]: payload,
        outputs["symbols"] if "symbols" in outputs else outputs["runtime_symbols"]: _stable(symbols),
        outputs["catalog_header"]: generated_header,
        outputs["catalog"]: catalog_json,
        outputs["checkpoint"]: _stable(checkpoint),
        outputs.get("patch", outputs.get("bps")): patch_raw,
    }


def _write_outputs(root: Path, outputs: Mapping[str, bytes]) -> None:
    for relative, raw in outputs.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
            stream.write(raw)
            temporary = Path(stream.name)
        os.replace(temporary, path)


def _check_outputs(root: Path, outputs: Mapping[str, bytes]) -> None:
    differences = [relative for relative, raw in outputs.items()
                   if not (root / relative).is_file() or (root / relative).read_bytes() != raw]
    if differences:
        _fail("Stage68生成物が不一致です: " + ", ".join(differences))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("build", "check"))
    args = parser.parse_args()
    try:
        outputs = build_outputs(ROOT)
        repeated = build_outputs(ROOT)
        if outputs != repeated:
            _fail("Stage68 buildがbyte deterministicではありません")
        if args.mode == "build":
            _write_outputs(ROOT, outputs)
        else:
            _check_outputs(ROOT, outputs)
    except (OSError, KeyError, TypeError, ValueError, MegaShopBuildError) as error:
        print(f"Modernization Mega shop {args.mode} failed: {error}", file=sys.stderr)
        return 1
    config = _read_json(ROOT / CONFIG)
    print(
        f"Modernization Mega shop {args.mode}: PASS "
        f"rom={_sha(outputs[config['outputs']['rom']])} outputs={len(outputs)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
