#!/usr/bin/env python3
"""stage 24へ無料の共通技管理「わざメモリー」を決定的に結合する。"""

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
from scripts.fast_stage_reuse import (  # noqa: E402
    generated_input_may_follow_stage,
    trusted_stage_sha,
    trusted_t06_fingerprint,
)


TASK = "USER-20260814-MOVE-MEMORY"
ROM_SIZE = 32 * 1024 * 1024
CLEAN_ROM = Path("inputs/private/FireRed_JPN_Rev0_clean.gba")
CLEAN_ROM_SHA256 = "1e4af44b0c75cc8649bfb8649dc4ae5850bf5358bd6b9cd0bf779c99f9db1486"
CONFIG = Path("config/move_memory.json")
STAGE24 = Path("build/stages/24_battle_ui.gba")
STAGE24_META = Path("build/stages/24_battle_ui.json")
STAGE24_ALLOCATION = Path("build/stages/24_allocation.json")
STAGE25 = Path("build/stages/25_move_memory.gba")
STAGE25_META = Path("build/stages/25_move_memory.json")
STAGE25_ALLOCATION = Path("build/stages/25_allocation.json")
RUNTIME_BIN = Path("generated/runtime/move_memory.bin")
RUNTIME_SYMBOLS = Path("generated/runtime/move_memory_symbols.json")
MGBA_FIXTURE = Path("build/stages/25_mgba_move_memory.json")
REPORT = Path("reports/generated/move_memory.md")
RUNNER = Path("tools/mgba_move_memory_smoke.c")
EMBEDDED_RUNNER_SOURCES = (
    Path("tools/mgba_battle_core_smoke.c"),
    Path("tools/mgba_ai_fixture_runner.c"),
)
ALLOCATION_NAME = "move_memory_runtime"
PAYLOAD_HEADER_SIZE = 64

EXPECTED_STAGE24_SHA256 = "dc0fdd490eceb087ccfe6d14685f22bb39b2dad46808d78f9269b542c0012130"
EXPECTED_CFRU_COMMIT = "e24a16fe39e27ae162faf5b78596d1f3df18489d"
EXPECTED_CFRU_TREE = "f4424af017abd01afe2d2deb833fb67275f03804"
EXPECTED_T06_FINGERPRINT = "9215826454ee6023888d2f53d33b662d21a340af868c92637aae2c5c191c5717"


def _expected_stage24(root: Path) -> str:
    return trusted_stage_sha(
        root, STAGE24, STAGE24_META, "USER-20260814-BATTLE-UI",
        EXPECTED_STAGE24_SHA256,
    )


def _expected_t06_fingerprint(root: Path) -> str:
    return trusted_t06_fingerprint(
        root, Path("build/stages/06_battle_core.json"),
        EXPECTED_T06_FINGERPRINT,
    )

ITEM_DATA = 0x0904D108
ITEM_DATA_STRIDE = 40
ITEM_GRAPHICS = 0x09056D20
ITEM_GRAPHICS_STRIDE = 8
ITEM_ID = 347
ECOLOGY_RADAR_ITEM_ID = 348
ITEM_TEMPLATE_ID = 364
ITEM_ICON_SOURCE_ID = 366
MODE_RAM = 0x0203EC00
MAX_CANDIDATES = 40
PARTY_SIZE = 6

SPECIAL_CHOOSE_RELEARNER_MON = 0x00DB
SPECIAL_TEACH_RELEARNER_MOVE = 0x00E0
SPECIAL_CHOOSE_PARTY_MON = 0x009F
SPECIAL_IS_SELECTED_MON_EGG = 0x0148
SPECIAL_SELECT_DELETER_MOVE = 0x00DC
SPECIAL_BUFFER_DELETER = 0x00DE
SPECIAL_COUNT_SELECTED_MOVES = 0x00DF

REQUIRED_SYMBOLS = {
    "VegaMoveMemory_FieldUse",
    "VegaMoveMemory_CheckContext",
    "VegaMoveMemory_OpenModeMenu",
    "VegaMoveMemory_SetNormalMode",
    "VegaMoveMemory_SetEggMode",
    "VegaMoveMemory_ResetMode",
    "VegaMoveMemory_GetMoveRelearnerMoves",
    "VegaMoveMemory_CheckEggEntry",
    "VegaMoveMemory_CheckEggSlot",
    "VegaMoveMemory_SelectedMonHasEmptySlot",
    "VegaMoveMemory_SelectedMoveHasPpUps",
    "VegaMoveMemory_SelectedMoveCanForget",
    "VegaMoveMemory_DeleteSelectedMove",
    "VegaMoveMemory_ContextAllowedFromState",
    "VegaMoveMemory_EvaluateEggPolicy",
    "VegaMoveMemory_CanForgetMove",
    "VegaMoveMemory_ItemScriptPointer",
}

UPSTREAM_SYMBOLS = {
    "GetAllEggMoves": 0x090EB970,
    "GetMoveRelearnerMoves": 0x091141D4,
    "GetNumberOfRelearnableMoves": 0x0911430C,
    "SetMonMoveSlot": 0x09114698,
    "RemoveMonPPBonus": 0x08040755,
    "ShiftMoveSlot": 0x080C0C79,
    "RandomizeMove": 0x09114334,
}

TEXTS = {
    "text_item_description": "いつでも わざを おもいだしたり\nわすれさせたり できる そうち。",
    "text_badge_reward": "わざメモリーと せいたいレーダーを\nてにいれた！",
    "text_npc_grant": "わざメモリーを もっていなかったので\nひとつ おわたしします",
    "text_ecology_grant": "せいたいレーダーも おわたしします",
    "text_remember_intro": "わざを おもいだします",
    "text_forget_intro": "わざを わすれさせます",
    "text_choose_mon": "どの ポケモンに つかいますか？",
    "text_choose_forget_mon": "わすれさせる ポケモンを えらんでください",
    "text_no_moves": "おもいだせる わざが ありません",
    "text_egg_rejected": "タマゴは えらべません",
    "text_egg_locked": "タマゴわざは まだ つかえません",
    "text_need_herb": "ものまねハーブが ひつようです",
    "text_need_empty": "あきの わざわくが ひつようです",
    "text_last_move": "さいごの ひとつは わすれられません",
    "text_pp_up_warning": "ポイントアップの こうかが なくなります。\nよろしいですか？",
    "text_forget_confirm": "この わざを わすれさせますか？",
    "text_forgot": "わざを わすれさせました",
    "text_form_rejected": "その わざは いまの すがたでは\nわすれられません",
    "text_context_rejected": "つかうことが できません",
}


class MoveMemoryError(ValueError):
    """入力hash、ROM ABI、受入条件の違反。"""


def _fail(message: str) -> NoReturn:
    raise MoveMemoryError(message)


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _stable(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


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


def _address(value: object) -> int:
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    if isinstance(value, str):
        return int(value, 0)
    _fail(f"address is not an integer: {value!r}")


def _config(root: Path = ROOT) -> dict[str, Any]:
    path = root / CONFIG
    value = _read_json(path)
    if value.get("schema_version") != 1 or value.get("task") != TASK:
        _fail("move memory config schema/task differs")
    t06_fingerprint = _expected_t06_fingerprint(root)
    if generated_input_may_follow_stage(
        str(value["inputs"]["linked_object"]["path"])
    ):
        value["inputs"]["linked_object"]["path"] = (
            f"build/battle-core/{t06_fingerprint}/run-1/linked.o"
        )
    for row in value["inputs"].values():
        source = root / row["path"]
        if not source.is_file() or (
            not generated_input_may_follow_stage(str(row["path"]))
            and _sha(source.read_bytes()) != row["sha256"]
        ):
            _fail(f"move memory pinned input differs: {row['path']}")
    return value


def _rom_offset(address: int, size: int = 1) -> int:
    offset = address - GBA_ROM_BASE
    if offset < 0 or offset + size > ROM_SIZE:
        _fail(f"ROM address outside stage: 0x{address:08X}+{size}")
    return offset


def _rom_slice(rom: bytes, address: int, size: int) -> bytes:
    offset = _rom_offset(address, size)
    return rom[offset:offset + size]


def _source_audit(root: Path, config: dict[str, Any]) -> dict[str, Any]:
    source = root / config["source"]["path"]
    commit = _run(["git", "-C", str(source), "rev-parse", "HEAD"], "CFRU commit")
    tree = _run(["git", "-C", str(source), "rev-parse", "HEAD^{tree}"], "CFRU tree")
    if commit != EXPECTED_CFRU_COMMIT or tree != EXPECTED_CFRU_TREE:
        _fail("fixed CFRU source identity differs")
    linked = root / config["inputs"]["linked_object"]["path"]
    symbols: dict[str, int] = {}
    for line in _run(
        ["arm-none-eabi-nm", "-n", str(linked)], "CFRU linked symbol audit"
    ).splitlines():
        fields = line.split()
        if len(fields) == 3 and fields[2] in UPSTREAM_SYMBOLS:
            symbols[fields[2]] = int(fields[0], 16)
    if symbols != UPSTREAM_SYMBOLS:
        _fail(f"fixed CFRU move-management symbols differ: {symbols}")
    anchors = {
        "normal_level_boundary": (
            "src/learn_move.c", "if (lvlUpMove.level <= level)"
        ),
        "egg_move_owner": (
            "src/learn_move.c", "numMoves = GetAllEggMoves(mon, moves, TRUE);"
        ),
        "form_link": (
            "src/learn_move.c", "void SetMonMoveSlot(struct Pokemon* mon, u16 move, u8 slot)"
        ),
        "egg_buffer_bound": (
            "include/new/daycare.h", "#define EGG_MOVES_ARRAY_COUNT 50"
        ),
    }
    anchor_rows: dict[str, dict[str, str]] = {}
    for key, (relative, needle) in anchors.items():
        path = source / relative
        if needle not in path.read_text(encoding="utf-8"):
            _fail(f"CFRU source anchor missing: {key}")
        anchor_rows[key] = {
            "path": relative, "needle": needle, "sha256": _sha(path.read_bytes()),
        }
    species_surface = _read_json(root / config["inputs"]["species_surface_metadata"]["path"])
    learnsets = species_surface.get("learnsets", {})
    level_up = learnsets.get("level_up", {})
    if (
        learnsets.get("species_count") != 1621
        or level_up.get("format") != "U16_MOVE_U8_LEVEL"
        or level_up.get("stride") != 3
        or level_up.get("converted_vega_rows") != 412
        or level_up.get("translated_dpe_rows") != 1209
        or species_surface.get("repoints", {}).get("level_up", {}).get("site") != 0x0003E1E8
        or species_surface.get("repoints", {}).get("level_up_cfru_root", {}).get("site") != 0x0004346C
        or not species_surface.get("repoints", {}).get("level_up", {}).get(
            "legacy_root_preserved"
        )
        or len(species_surface.get("learn_move_hooks", [])) != 5
    ):
        _fail("T09 canonical level-up ABI contract differs")
    with (root / config["inputs"]["move_manifest"]["path"]).open(
        encoding="utf-8-sig", newline=""
    ) as stream:
        manifest_rows = list(csv.DictReader(stream))
    expected_move_ids = {
        "MOVE_SECRETSWORD": 619,
        "MOVE_BEHEMOTHBLADE": 768,
        "MOVE_BEHEMOTHBASH": 769,
    }
    manifest_move_ids = {
        row["cfru_symbol"]: int(row["id"])
        for row in manifest_rows if row["cfru_symbol"] in expected_move_ids
    }
    if (
        manifest_move_ids != expected_move_ids
        or config["policy"]["form_only_moves"] != [768, 769]
    ):
        _fail("fixed move-manifest IDs differ")
    return {
        "status": "PASS", "commit": commit, "tree": tree,
        "t06_fingerprint": _expected_t06_fingerprint(root),
        "linked_symbols": symbols, "anchors": anchor_rows,
        "manifest_move_ids": manifest_move_ids,
        "level_up_abi": {
            "root_pointer_site": 0x0804346C,
            "format": "U16_MOVE_U8_LEVEL",
            "stride": 3,
            "converted_vega_species": 412,
            "translated_dpe_species": 1209,
            "species_count": 1621,
        },
    }


def _ram_audit(root: Path) -> dict[str, Any]:
    path = root / "config/ram_layout.csv"
    with path.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    matches = [
        row for row in rows
        if row["owner"] == "USER_20260814_MOVE_MEMORY"
    ]
    if len(matches) != 1:
        _fail("move memory RAM reservation is not unique")
    row = matches[0]
    if (
        int(row["start"], 0) != MODE_RAM
        or int(row["end_exclusive"], 0) != MODE_RAM + 1
        or row["persistence"] != "VOLATILE"
        or row["status"] != "LIVE"
    ):
        _fail("move memory RAM reservation differs")
    live: list[tuple[int, int, str]] = []
    for item in rows:
        if item["address_space"] == "EWRAM" and item["status"] == "LIVE":
            live.append((int(item["start"], 0), int(item["end_exclusive"], 0), item["owner"]))
    live.sort()
    overlaps = [
        (left[2], right[2]) for left, right in zip(live, live[1:])
        if right[0] < left[1]
    ]
    if overlaps:
        _fail(f"live EWRAM reservation overlap: {overlaps}")
    return {
        "status": "PASS", "address": MODE_RAM, "size": 1,
        "persistence": "VOLATILE", "flash_serialized": False,
        "layout_sha256": _sha(path.read_bytes()),
    }


def _previous_requests(root: Path) -> list[dict[str, object]]:
    report = _read_json(root / STAGE24_ALLOCATION)
    if report.get("summaries", {}).get("overlap_count") != 0:
        _fail("stage24 allocator overlap contract failed")
    return [{
        "name": row["name"], "region": row["region"], "size": row["size"],
        "alignment": row["alignment"], "start": row["start"],
        "owner": row["owner"], "purpose": row["purpose"],
        "content_sha256": row["content_sha256"],
    } for row in report["allocations"]]


def _allocation(root: Path, size: int, digest: str) -> tuple[dict[str, Any], dict[str, Any]]:
    requests = _previous_requests(root)
    requests.append({
        "name": ALLOCATION_NAME,
        "region": "integration_modules",
        "size": size,
        "alignment": 16,
        "owner": TASK,
        "purpose": "item/NPC共通の技思い出し・技忘れ・タマゴ技管理core",
        "content_sha256": digest,
    })
    report = build_allocation_report_from_csv(root / "config/rom_regions.csv", requests)
    allocation = next(row for row in report["allocations"] if row["name"] == ALLOCATION_NAME)
    return allocation, report


def _compile_runtime(
    root: Path, load_address: int, linked_symbols: dict[str, int]
) -> tuple[bytes, dict[str, int]]:
    compiler = shutil.which("arm-none-eabi-gcc")
    objcopy = shutil.which("arm-none-eabi-objcopy")
    nm = shutil.which("arm-none-eabi-nm")
    if not compiler or not objcopy or not nm:
        _fail("ARM GNU toolchain is required for move memory runtime")
    source = root / "overlays/move_memory/move_memory.c"
    header = root / "overlays/move_memory/move_memory.h"
    if not source.is_file() or not header.is_file():
        _fail("move memory source/header is missing")
    with tempfile.TemporaryDirectory(prefix="vega-move-memory-") as raw:
        directory = Path(raw)
        linker = directory / "linker.ld"
        elf = directory / "move_memory.elf"
        binary = directory / "move_memory.bin"
        linker.write_text(
            "SECTIONS\n{\n"
            f"  . = 0x{load_address:08X};\n"
            "  .text : { KEEP(*(.text.VegaMoveMemory_*)) *(.text*) *(.rodata*) *(.data*) }\n"
            "  /DISCARD/ : { *(.comment*) *(.ARM.attributes*) *(.note*) }\n"
            "}\n",
            encoding="ascii",
        )
        _run([
            compiler, "-mthumb", "-mcpu=arm7tdmi", "-Os", "-std=c11",
            "-Wall", "-Wextra", "-Werror", "-ffreestanding", "-fno-builtin",
            "-DVEGA_MOVE_MEMORY_LINKED_ABI=1",
            f"-DVEGA_MOVE_MEMORY_GET_ALL_EGG_MOVES_ADDRESS=0x{linked_symbols['GetAllEggMoves'] | 1:08X}u",
            f"-DVEGA_MOVE_MEMORY_SET_MON_MOVE_SLOT_ADDRESS=0x{linked_symbols['SetMonMoveSlot'] | 1:08X}u",
            "-fno-unwind-tables", "-fno-asynchronous-unwind-tables",
            "-fdata-sections", "-ffunction-sections", "-nostdlib",
            "-Wl,--build-id=none", "-Wl,--gc-sections",
            "-Wl,-e,VegaMoveMemory_FieldUse", f"-Wl,-T,{linker}",
            f"-I{source.parent}", str(source), "-o", str(elf),
        ], "move memory ARM link", cwd=root)
        undefined = _run([nm, "-u", str(elf)], "move memory undefined-symbol check")
        if undefined:
            _fail("move memory image has undefined symbols: " + undefined)
        _run([objcopy, "-O", "binary", str(elf), str(binary)], "move memory objcopy")
        symbols: dict[str, int] = {}
        for line in _run([nm, "-n", "--defined-only", str(elf)], "move memory nm").splitlines():
            fields = line.split()
            if len(fields) == 3 and fields[2].startswith("VegaMoveMemory_"):
                symbols[fields[2]] = int(fields[0], 16)
        if set(symbols) != REQUIRED_SYMBOLS:
            _fail(f"move memory entrypoint set differs: {sorted(symbols)}")
        runtime = binary.read_bytes()
        if not runtime or len(runtime) > 8192:
            _fail(f"unexpected move memory runtime size: {len(runtime)}")
        return runtime, symbols


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

    def callnative(self, name: str) -> "_Script":
        self.operations.append(f"callnative:{name}")
        return self.emit(0x23).pointer(f"native::{name}", thumb=True)

    def msgbox(self, label: str, kind: int = 4) -> "_Script":
        self.operations.append(f"msgbox:{label}:{kind}")
        return self.emit(0x0F, 0x00).pointer(label).emit(0x09, kind)

    def compare(self, variable: int, value: int) -> "_Script":
        self.operations.append(f"compare:0x{variable:04X}:{value}")
        return self.emit(0x21).half(variable).half(value)

    def compare_result(self, value: int) -> "_Script":
        return self.compare(0x800D, value)

    def branch(self, condition: int, label: str) -> "_Script":
        self.operations.append(f"branch:{condition}:{label}")
        return self.emit(0x06, condition).pointer(label)

    def if_equal(self, label: str) -> "_Script":
        return self.branch(1, label)

    def if_at_least(self, label: str) -> "_Script":
        return self.branch(4, label)

    def goto(self, label: str) -> "_Script":
        self.operations.append(f"goto:{label}")
        return self.emit(0x05).pointer(label)

    def call(self, address: int) -> "_Script":
        self.operations.append(f"call:0x{address:08X}")
        return self.emit(0x04).word(address)

    def special(self, special: int) -> "_Script":
        self.operations.append(f"special:0x{special:03X}")
        return self.emit(0x25).half(special)

    def waitstate(self) -> "_Script":
        return self.emit(0x27, operation="waitstate")

    def checkflag(self, flag: int) -> "_Script":
        self.operations.append(f"checkflag:0x{flag:04X}")
        return self.emit(0x2B).half(flag)

    def checkitem(self, item: int, quantity: int = 1) -> "_Script":
        self.operations.append(f"checkitem:{item}:{quantity}")
        return self.emit(0x47).half(item).half(quantity)

    def additem(self, item: int, quantity: int = 1) -> "_Script":
        self.operations.append(f"additem:{item}:{quantity}")
        return self.emit(0x44).half(item).half(quantity)


def _add_script(blob: _Blob, label: str, script: _Script,
                audit: dict[str, Any]) -> None:
    offset = blob.add(label, bytes(script.data), 4)
    for relative, target, thumb in script.fixups:
        blob.pointer(offset + relative, target, thumb=thumb)
    audit[label] = {
        "offset": offset, "size": len(script.data), "operations": script.operations,
    }


def _finish_script() -> _Script:
    return _Script().callnative("VegaMoveMemory_ResetMode").emit(
        0x6C, 0x02, operation="release_end"
    )


def _build_scripts(root: Path, blob: _Blob) -> dict[str, Any]:
    mapping, tokens = _charmap(root)
    text_meta: dict[str, Any] = {}
    for label, text in TEXTS.items():
        encoded = _encode_text(text, mapping, tokens)
        blob.add(label, encoded, 1)
        text_meta[label] = {"text": text, "size": len(encoded), "sha256": _sha(encoded)}

    scripts: dict[str, Any] = {}

    _add_script(
        blob, "script_item_entry",
        _Script().emit(0x6A, operation="lock")
        .callnative("VegaMoveMemory_CheckContext")
        .compare_result(1).if_equal("script_mode_menu")
        .goto("script_context_rejected"), scripts,
    )
    _add_script(
        blob, "script_mode_menu",
        _Script().callnative("VegaMoveMemory_OpenModeMenu")
        .compare_result(3).if_equal("script_finish")
        .waitstate()
        .compare_result(0).if_equal("script_remember_entry")
        .compare_result(1).if_equal("script_forget_entry")
        .compare_result(2).if_equal("script_egg_entry")
        .goto("script_finish"), scripts,
    )
    _add_script(
        blob, "script_remember_entry",
        _Script().callnative("VegaMoveMemory_SetNormalMode")
        .msgbox("text_remember_intro").goto("script_remember_select"), scripts,
    )
    _add_script(
        blob, "script_remember_select",
        _Script().msgbox("text_choose_mon")
        .special(SPECIAL_CHOOSE_RELEARNER_MON).waitstate()
        .compare(0x8004, PARTY_SIZE).if_at_least("script_finish")
        .special(SPECIAL_IS_SELECTED_MON_EGG)
        .compare_result(1).if_equal("script_remember_egg_error")
        .compare(0x8005, 0).if_equal("script_remember_no_moves")
        .special(SPECIAL_TEACH_RELEARNER_MOVE).waitstate()
        .compare(0x8004, 0).if_equal("script_remember_select")
        .goto("script_finish"), scripts,
    )
    _add_script(
        blob, "script_remember_egg_error",
        _Script().msgbox("text_egg_rejected").goto("script_remember_select"), scripts,
    )
    _add_script(
        blob, "script_remember_no_moves",
        _Script().msgbox("text_no_moves").goto("script_remember_select"), scripts,
    )

    _add_script(
        blob, "script_egg_entry",
        _Script().callnative("VegaMoveMemory_CheckEggEntry")
        .compare_result(0).if_equal("script_egg_locked")
        .compare_result(2).if_equal("script_egg_need_herb")
        .callnative("VegaMoveMemory_SetEggMode")
        .goto("script_egg_select"), scripts,
    )
    _add_script(
        blob, "script_egg_select",
        _Script().msgbox("text_choose_mon")
        .special(SPECIAL_CHOOSE_RELEARNER_MON).waitstate()
        .compare(0x8004, PARTY_SIZE).if_at_least("script_finish")
        .special(SPECIAL_IS_SELECTED_MON_EGG)
        .compare_result(1).if_equal("script_egg_mon_error")
        .callnative("VegaMoveMemory_CheckEggSlot")
        .compare_result(0).if_equal("script_egg_locked")
        .compare_result(2).if_equal("script_egg_need_herb")
        .compare_result(3).if_equal("script_egg_need_empty")
        .compare(0x8005, 0).if_equal("script_egg_no_moves")
        .special(SPECIAL_TEACH_RELEARNER_MOVE).waitstate()
        .compare(0x8004, 0).if_equal("script_egg_select")
        .goto("script_finish"), scripts,
    )
    _add_script(
        blob, "script_egg_mon_error",
        _Script().msgbox("text_egg_rejected").goto("script_egg_select"), scripts,
    )
    _add_script(
        blob, "script_egg_no_moves",
        _Script().msgbox("text_no_moves").goto("script_egg_select"), scripts,
    )
    _add_script(
        blob, "script_egg_locked",
        _Script().msgbox("text_egg_locked").goto("script_finish"), scripts,
    )
    _add_script(
        blob, "script_egg_need_herb",
        _Script().msgbox("text_need_herb").goto("script_finish"), scripts,
    )
    _add_script(
        blob, "script_egg_need_empty",
        _Script().msgbox("text_need_empty").goto("script_egg_select"), scripts,
    )

    _add_script(
        blob, "script_forget_entry",
        _Script().callnative("VegaMoveMemory_SetNormalMode")
        .msgbox("text_forget_intro").goto("script_forget_select"), scripts,
    )
    _add_script(
        blob, "script_forget_select",
        _Script().msgbox("text_choose_forget_mon")
        .special(SPECIAL_CHOOSE_PARTY_MON).waitstate()
        .compare(0x8004, PARTY_SIZE).if_at_least("script_finish")
        .special(SPECIAL_IS_SELECTED_MON_EGG)
        .compare_result(1).if_equal("script_forget_egg_error")
        .special(SPECIAL_COUNT_SELECTED_MOVES)
        .compare_result(1).if_equal("script_forget_last_error")
        .emit(0x97, 1, operation="fade_out")
        .special(SPECIAL_SELECT_DELETER_MOVE)
        .emit(0x97, 0, operation="fade_in")
        .compare(0x8005, 4).if_at_least("script_forget_select")
        .callnative("VegaMoveMemory_SelectedMoveCanForget")
        .compare_result(0).if_equal("script_forget_form_error")
        .callnative("VegaMoveMemory_SelectedMoveHasPpUps")
        .compare_result(1).if_equal("script_forget_pp_warning")
        .goto("script_forget_confirm"), scripts,
    )
    _add_script(
        blob, "script_forget_pp_warning",
        _Script().msgbox("text_pp_up_warning", 5)
        .compare_result(1).if_equal("script_forget_confirm")
        .goto("script_finish"), scripts,
    )
    _add_script(
        blob, "script_forget_confirm",
        _Script().special(SPECIAL_BUFFER_DELETER)
        .msgbox("text_forget_confirm", 5)
        .compare_result(1).if_equal("script_forget_delete")
        .goto("script_finish"), scripts,
    )
    _add_script(
        blob, "script_forget_delete",
        _Script().callnative("VegaMoveMemory_DeleteSelectedMove")
        .emit(0x31, operation="play_fanfare").half(0x010E)
        .emit(0x32, operation="wait_fanfare")
        .msgbox("text_forgot").goto("script_finish"), scripts,
    )
    _add_script(
        blob, "script_forget_egg_error",
        _Script().msgbox("text_egg_rejected").goto("script_forget_select"), scripts,
    )
    _add_script(
        blob, "script_forget_last_error",
        _Script().msgbox("text_last_move").goto("script_forget_select"), scripts,
    )
    _add_script(
        blob, "script_forget_form_error",
        _Script().msgbox("text_form_rejected").goto("script_forget_select"), scripts,
    )

    _add_script(
        blob, "script_context_rejected",
        _Script().msgbox("text_context_rejected").goto("script_finish"), scripts,
    )
    _add_script(blob, "script_finish", _finish_script(), scripts)

    _add_script(
        blob, "script_shiou_npc",
        _Script().emit(0x6A, 0x5A, operation="lock_faceplayer")
        .checkflag(0x0820).compare_result(1).if_equal("script_shiou_item_check")
        .goto("script_shiou_context"), scripts,
    )
    _add_script(
        blob, "script_shiou_item_check",
        _Script().checkitem(ITEM_ID).compare_result(0).if_equal("script_shiou_grant")
        .goto("script_shiou_ecology_check"), scripts,
    )
    _add_script(
        blob, "script_shiou_grant",
        _Script().additem(ITEM_ID).msgbox("text_npc_grant")
        .goto("script_shiou_ecology_check"), scripts,
    )
    _add_script(
        blob, "script_shiou_ecology_check",
        _Script().checkitem(ECOLOGY_RADAR_ITEM_ID).compare_result(0)
        .if_equal("script_shiou_ecology_grant")
        .goto("script_shiou_context"), scripts,
    )
    _add_script(
        blob, "script_shiou_ecology_grant",
        _Script().additem(ECOLOGY_RADAR_ITEM_ID).msgbox("text_ecology_grant")
        .goto("script_shiou_context"), scripts,
    )
    _add_script(
        blob, "script_shiou_context",
        _Script().callnative("VegaMoveMemory_CheckContext")
        .compare_result(1).if_equal("script_remember_entry")
        .goto("script_context_rejected"), scripts,
    )
    _add_script(
        blob, "script_karasuba_npc",
        _Script().emit(0x6A, 0x5A, operation="lock_faceplayer")
        .callnative("VegaMoveMemory_CheckContext")
        .compare_result(1).if_equal("script_forget_entry")
        .goto("script_context_rejected"), scripts,
    )
    _add_script(
        blob, "script_badge1_reward",
        _Script().call(0x081943E4).additem(ITEM_ID)
        .additem(ECOLOGY_RADAR_ITEM_ID)
        .msgbox("text_badge_reward").emit(0x03, operation="return"), scripts,
    )

    required_ops = {
        "script_remember_select": {
            f"special:0x{SPECIAL_CHOOSE_RELEARNER_MON:03X}",
            f"special:0x{SPECIAL_TEACH_RELEARNER_MOVE:03X}",
            f"special:0x{SPECIAL_IS_SELECTED_MON_EGG:03X}",
        },
        "script_forget_select": {
            f"special:0x{SPECIAL_CHOOSE_PARTY_MON:03X}",
            f"special:0x{SPECIAL_COUNT_SELECTED_MOVES:03X}",
            f"special:0x{SPECIAL_SELECT_DELETER_MOVE:03X}",
            "callnative:VegaMoveMemory_SelectedMoveCanForget",
            "callnative:VegaMoveMemory_SelectedMoveHasPpUps",
        },
        "script_forget_delete": {"callnative:VegaMoveMemory_DeleteSelectedMove"},
        "script_egg_select": {
            "callnative:VegaMoveMemory_CheckEggSlot",
            f"special:0x{SPECIAL_TEACH_RELEARNER_MOVE:03X}",
        },
    }
    for label, expected in required_ops.items():
        observed = set(scripts[label]["operations"])
        if not expected <= observed:
            _fail(f"script operation contract differs: {label}")
    if any(
        operation.startswith("removeitem:")
        for row in scripts.values() for operation in row["operations"]
    ):
        _fail("move memory scripts must not consume mushrooms/items")
    return {"texts": text_meta, "scripts": scripts}


def _build_payload(
    root: Path, payload_offset: int, linked_symbols: dict[str, int]
) -> tuple[bytes, dict[str, Any], bytes, dict[str, int]]:
    blob = _Blob()
    header_offset = blob.reserve("move_memory_header", PAYLOAD_HEADER_SIZE, 16)
    code_load = GBA_ROM_BASE + payload_offset + ((len(blob.data) + 3) & ~3)
    code, symbols = _compile_runtime(root, code_load, linked_symbols)
    code_offset = blob.add("move_memory_code", code, 4)
    if GBA_ROM_BASE + payload_offset + code_offset != code_load:
        _fail("move memory linker address disagrees with payload placement")
    for name, address in symbols.items():
        relative = address - code_load
        if relative < 0 or relative >= len(code):
            _fail(f"move memory symbol outside code image: {name}")
        blob.labels[f"native::{name}"] = code_offset + relative

    script_meta = _build_scripts(root, blob)
    pointer_symbol = symbols["VegaMoveMemory_ItemScriptPointer"]
    blob.pointer(code_offset + pointer_symbol - code_load, "script_item_entry")

    total_size = len(blob.data)
    struct.pack_into(
        "<8sIIIIIII", blob.data, header_offset,
        b"VEGAM25\0", 1, total_size, len(code), ITEM_ID,
        MAX_CANDIDATES, MODE_RAM, 0,
    )
    blob.pointer(header_offset + 36, "native::VegaMoveMemory_FieldUse", thumb=True)
    blob.pointer(header_offset + 40, "native::VegaMoveMemory_GetMoveRelearnerMoves", thumb=True)
    blob.pointer(header_offset + 44, "script_item_entry")
    blob.pointer(header_offset + 48, "script_shiou_npc")
    blob.pointer(header_offset + 52, "script_karasuba_npc")
    blob.pointer(header_offset + 56, "script_badge1_reward")
    blob.pointer(header_offset + 60, "text_item_description")
    payload = blob.finish(payload_offset)
    meta = {
        "header": {
            "magic": "VEGAM25", "version": 1, "size": len(payload),
            "code_size": len(code), "item_id": ITEM_ID,
            "max_candidates": MAX_CANDIDATES, "mode_ram": MODE_RAM,
        },
        "labels": {
            label: GBA_ROM_BASE + payload_offset + offset
            for label, offset in sorted(blob.labels.items())
            if not label.startswith("native::")
        },
        "script_contract": script_meta,
    }
    return payload, meta, code, symbols


def _patch(output: bytearray, address: int, expected: bytes,
           replacement: bytes, label: str) -> dict[str, Any]:
    if len(expected) != len(replacement):
        _fail(f"{label}: patch size differs")
    offset = _rom_offset(address, len(expected))
    actual = bytes(output[offset:offset + len(expected)])
    if actual != expected:
        _fail(f"{label}: expected={expected.hex()} actual={actual.hex()}")
    output[offset:offset + len(replacement)] = replacement
    return {
        "label": label, "address": address, "offset": offset,
        "size": len(expected), "expected_hex": expected.hex(),
        "replacement_hex": replacement.hex(),
    }


def _fixed_item_name(root: Path, text: str) -> bytes:
    mapping, tokens = _charmap(root)
    encoded = _encode_text(text, mapping, tokens)
    if not encoded or encoded[-1] != 0xFF or len(encoded) > 10:
        _fail("move memory item name does not fit the 10-byte ABI")
    body = encoded[:-1]
    if len(body) > 9:
        _fail("move memory item name body is too long")
    return body + bytes([0xFF]) * (9 - len(body)) + b"\0"


def _build_item_row(root: Path, source: bytes, description: int,
                    field_callback: int) -> bytes:
    template_offset = _rom_offset(ITEM_DATA + ITEM_TEMPLATE_ID * ITEM_DATA_STRIDE, ITEM_DATA_STRIDE)
    row = bytearray(source[template_offset:template_offset + ITEM_DATA_STRIDE])
    row[0:10] = _fixed_item_name(root, "わざメモリー")
    struct.pack_into("<H", row, 10, ITEM_ID)
    struct.pack_into("<H", row, 12, 0)
    row[14] = 0
    row[15] = 0
    struct.pack_into("<I", row, 16, description)
    row[20:24] = bytes((1, 1, 2, 4))
    struct.pack_into("<I", row, 24, field_callback | 1)
    struct.pack_into("<III", row, 28, 0, 0, 0)
    return bytes(row)


def _hook_target(rom: bytes, address: int) -> int:
    stub = _rom_slice(rom, address, 8)
    if stub[:4] != b"\x00\x4b\x18\x47":
        _fail(f"Thumb r3 absolute hook shape differs: 0x{address:08X}")
    target = struct.unpack_from("<I", stub, 4)[0]
    if not target & 1:
        _fail(f"Thumb target is not odd: 0x{address:08X}")
    return target


def _build_stage(root: Path = ROOT) -> tuple[dict[str, bytes], dict[str, Any]]:
    config = _config(root)
    source_audit = _source_audit(root, config)
    ram_audit = _ram_audit(root)
    source = (root / STAGE24).read_bytes()
    expected_stage24 = _expected_stage24(root)
    if len(source) != ROM_SIZE or _sha(source) != expected_stage24:
        _fail("stage24 size/hash contract failed")
    stage24_meta = _read_json(root / STAGE24_META)
    if (
        stage24_meta.get("status") != "PASS"
        or stage24_meta.get("output", {}).get("sha256") != _sha(source)
    ):
        _fail("stage24 metadata contract failed")

    provisional, _ = _allocation(root, 16384, "0" * 64)
    payload_offset = int(provisional["start"])
    payload, payload_meta, code, symbols = _build_payload(
        root, payload_offset, source_audit["linked_symbols"]
    )
    allocation, allocation_report = _allocation(root, len(payload), _sha(payload))
    if int(allocation["start"]) != payload_offset:
        _fail("move memory allocation moved after final link")
    payload_end = int(allocation["end_exclusive"])
    if source[payload_offset:payload_end] != bytes([0xFF]) * len(payload):
        _fail("move memory allocation destination is not erased FF")

    output = bytearray(source)
    output[payload_offset:payload_end] = payload
    patches: list[dict[str, Any]] = []
    cfg_patches = config["patches"]

    item_cfg = config["item"]
    item_address = ITEM_DATA + ITEM_ID * ITEM_DATA_STRIDE
    description = payload_meta["labels"]["text_item_description"]
    item_row = _build_item_row(
        root, source, description, symbols["VegaMoveMemory_FieldUse"]
    )
    patches.append(_patch(
        output, item_address, bytes.fromhex(item_cfg["expected_row_hex"]),
        item_row, "unused item 347 -> わざメモリー",
    ))

    icon_address = ITEM_GRAPHICS + ITEM_ID * ITEM_GRAPHICS_STRIDE
    icon_source_address = ITEM_GRAPHICS + ITEM_ICON_SOURCE_ID * ITEM_GRAPHICS_STRIDE
    icon = _rom_slice(source, icon_source_address, ITEM_GRAPHICS_STRIDE)
    patches.append(_patch(
        output, icon_address, bytes.fromhex(item_cfg["expected_icon_hex"]),
        icon, "わざメモリー key-item icon",
    ))

    move_cfg = cfg_patches["move_relearner"]
    move_hook = _address(move_cfg["address"])
    move_target = symbols["VegaMoveMemory_GetMoveRelearnerMoves"] | 1
    patches.append(_patch(
        output, move_hook, bytes.fromhex(move_cfg["expected_hex"]),
        b"\x00\x4b\x18\x47" + struct.pack("<I", move_target),
        "CFRU GetMoveRelearnerMoves transient-mode adapter",
    ))

    pointer_contract = (
        ("shiou_npc", "script_shiou_npc"),
        ("karasuba_npc", "script_karasuba_npc"),
        ("badge1_reward_call", "script_badge1_reward"),
    )
    for key, label in pointer_contract:
        row = cfg_patches[key]
        patches.append(_patch(
            output, _address(row["address"]), bytes.fromhex(row["expected_hex"]),
            struct.pack("<I", payload_meta["labels"][label]),
            f"{key} -> shared move memory script",
        ))

    output_raw = bytes(output)
    allowed = set(range(payload_offset, payload_end))
    for row in patches:
        allowed.update(range(row["offset"], row["offset"] + row["size"]))
    changed = {
        index for index, pair in enumerate(zip(source, output_raw))
        if pair[0] != pair[1]
    }
    if not changed <= allowed:
        _fail("move memory build changed bytes outside declared sites")
    if _hook_target(output_raw, move_hook) != move_target:
        _fail("move relearner post-patch ownership chain differs")

    item_final = _rom_slice(output_raw, item_address, ITEM_DATA_STRIDE)
    if (
        struct.unpack_from("<H", item_final, 10)[0] != ITEM_ID
        or item_final[20:24] != bytes((1, 1, 2, 4))
        or struct.unpack_from("<I", item_final, 24)[0]
        != (symbols["VegaMoveMemory_FieldUse"] | 1)
        or struct.unpack_from("<I", item_final, 16)[0] != description
    ):
        _fail("move memory item row ABI differs")

    clean = (root / CLEAN_ROM).read_bytes()
    if len(clean) != 16 * 1024 * 1024 or _sha(clean) != CLEAN_ROM_SHA256:
        _fail("clean FireRed Japanese Rev.0 identity differs")
    release_patch = create_bps(
        clean, output_raw, metadata=f"{TASK}:{_sha(output_raw)}".encode("ascii")
    )
    if apply_bps(clean, release_patch) != output_raw:
        _fail("clean ROM to stage25 BPS round-trip differs")

    published_symbols = {
        name: address if name == "VegaMoveMemory_ItemScriptPointer" else address | 1
        for name, address in sorted(symbols.items())
    }
    symbol_payload = {
        "schema_version": 1, "task": TASK,
        "load_address": GBA_ROM_BASE + payload_offset,
        "symbols": published_symbols,
    }
    script_ops = payload_meta["script_contract"]["scripts"]
    acceptance = {
        "item_and_npcs_share_core": (
            payload_meta["labels"]["script_shiou_npc"]
            == struct.unpack("<I", _rom_slice(output_raw, 0x08382628, 4))[0]
            and payload_meta["labels"]["script_karasuba_npc"]
            == struct.unpack("<I", _rom_slice(output_raw, 0x0838047C, 4))[0]
        ),
        "no_mushroom_or_item_consumption": not any(
            operation.startswith("removeitem:")
            for row in script_ops.values() for operation in row["operations"]
        ),
        "normal_level_boundary_owned_by_adapter": _hook_target(output_raw, move_hook) == move_target,
        "egg_unlock_and_cost_policy_present": all(
            name in published_symbols for name in (
                "VegaMoveMemory_CheckEggEntry", "VegaMoveMemory_CheckEggSlot",
                "VegaMoveMemory_EvaluateEggPolicy",
            )
        ),
        "last_move_ppup_hm_form_guards_present": (
            f"special:0x{SPECIAL_COUNT_SELECTED_MOVES:03X}"
            in script_ops["script_forget_select"]["operations"]
            and "callnative:VegaMoveMemory_SelectedMoveHasPpUps"
            in script_ops["script_forget_select"]["operations"]
            and "callnative:VegaMoveMemory_SelectedMoveCanForget"
            in script_ops["script_forget_select"]["operations"]
            and "callnative:VegaMoveMemory_DeleteSelectedMove"
            in script_ops["script_forget_delete"]["operations"]
        ),
        "transient_mode_not_flash_serialized": not ram_audit["flash_serialized"],
        "context_rejection_present": (
            "callnative:VegaMoveMemory_CheckContext"
            in script_ops["script_item_entry"]["operations"]
        ),
    }
    if not all(acceptance.values()):
        _fail("move memory host acceptance failed")

    metadata: dict[str, Any] = {
        "schema_version": 1, "task": TASK, "status": "PASS",
        "input": {"path": STAGE24.as_posix(), "size": len(source), "sha256": _sha(source)},
        "output": {"path": STAGE25.as_posix(), "size": len(output_raw), "sha256": _sha(output_raw)},
        "source_audit": source_audit,
        "ram_audit": ram_audit,
        "runtime": {
            "allocation_name": ALLOCATION_NAME,
            "offset": payload_offset,
            "address": GBA_ROM_BASE + payload_offset,
            "size": len(payload), "sha256": _sha(payload),
            "code_size": len(code), "code_sha256": _sha(code),
            "symbols": published_symbols,
            "payload": payload_meta,
        },
        "item": {
            "id": ITEM_ID, "name": "わざメモリー", "address": item_address,
            "description_address": description,
            "field_callback": published_symbols["VegaMoveMemory_FieldUse"],
            "pocket": "KEY_ITEMS", "importance": 1, "registrable": True,
            "icon_source_item": ITEM_ICON_SOURCE_ID,
        },
        "companion_item": {
            "id": ECOLOGY_RADAR_ITEM_ID, "name": "せいたいレーダー",
            "grant": "badge1_reward_and_shiou_recovery",
            "runtime_owner": "T17_TOHOKU_ECOLOGY",
        },
        "npc_entries": {
            "shiou": {"map": "33:1", "object": 0, "script": payload_meta["labels"]["script_shiou_npc"]},
            "karasuba": {"map": "11:9", "object": 0, "script": payload_meta["labels"]["script_karasuba_npc"]},
        },
        "patches": patches,
        "allocation": {
            "path": STAGE25_ALLOCATION.as_posix(),
            "overlap_count": allocation_report["summaries"]["overlap_count"],
            "remaining_allocatable_bytes": allocation_report["summaries"]["remaining_allocatable_bytes"],
        },
        "release_patch_round_trip": {
            "format": "BPS1", "source_sha256": _sha(clean),
            "target_sha256": _sha(output_raw), "patch_sha256": _sha(release_patch),
            "patch_size": len(release_patch), "exact": True,
        },
        "acceptance": acceptance,
        "invariants": {
            "rom_size_32_mib": len(output_raw) == ROM_SIZE,
            "stage24_hash_pinned": _sha(source) == expected_stage24,
            "allocator_overlap_zero": allocation_report["summaries"]["overlap_count"] == 0,
            "declared_changes_only": changed <= allowed,
            "item_slot_was_exact_placeholder": bytes.fromhex(item_cfg["expected_row_hex"]) == _rom_slice(source, item_address, ITEM_DATA_STRIDE),
            "release_patch_exact": True,
        },
    }
    failed = [name for name, passed in metadata["invariants"].items() if not passed]
    if failed:
        _fail("move memory invariant failed: " + ", ".join(failed))
    return ({
        STAGE25.as_posix(): output_raw,
        STAGE25_ALLOCATION.as_posix(): _stable(allocation_report),
        RUNTIME_BIN.as_posix(): payload,
        RUNTIME_SYMBOLS.as_posix(): _stable(symbol_payload),
    }, metadata)


def _tool_identity(root: Path) -> dict[str, str]:
    cc = shutil.which(os.environ.get("CC", "cc"))
    if not cc:
        _fail("C compiler missing")
    version = _run([cc, "--version"], "C compiler version").splitlines()[0]
    pkg = shutil.which("pkg-config")
    mgba = "linker:-lmgba"
    if pkg:
        probe = subprocess.run(
            [pkg, "--modversion", "mgba"], text=True,
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False,
        )
        if probe.returncode == 0 and probe.stdout.strip():
            mgba = probe.stdout.strip()
    return {"cc": cc, "cc_version": version, "libmgba": mgba}


def _runner_cache_key(root: Path, rom_sha256: str, symbols: object) -> tuple[str, dict[str, Any]]:
    sources = (RUNNER, *EMBEDDED_RUNNER_SOURCES)
    payload = {
        "schema_version": 1, "rom_sha256": rom_sha256,
        "sources": {path.as_posix(): _sha((root / path).read_bytes()) for path in sources},
        "toolchain": _tool_identity(root), "symbols": symbols,
    }
    return _sha(_stable(payload)), payload


def _validate_fixture(value: dict[str, Any], rom_sha256: str) -> None:
    normal = value.get("normal", {})
    egg = value.get("egg", {})
    forget = value.get("forget", {})
    if (
        value.get("status") != "PASS"
        or value.get("fixture") != "move_memory_runtime_v1"
        or value.get("rom_sha256") != rom_sha256
        or value.get("warnings_errors") != 0
        or not value.get("read_only")
        or not normal.get("future_level_rejected")
        or not normal.get("level_zero_one_included")
        or not normal.get("known_and_duplicate_filtered")
        or normal.get("candidate_cap") != MAX_CANDIDATES
        or not egg.get("direct_owner_match")
        or not egg.get("mode_reset")
        or egg.get("policy_matrix_cases") != 5
        or not forget.get("last_move_script_guard")
        or not forget.get("pp_up_warning_script_guard")
        or not forget.get("hm_allowed")
        or not forget.get("form_only_rejected")
        or not forget.get("secret_sword_form_link_allowed")
        or not forget.get("set_mon_move_slot_native_path")
        or not value.get("context", {}).get("matrix_pass")
        or not value.get("physical_patches", {}).get("all_match")
    ):
        _fail("move memory exact-ROM fixture differs")


def _fixture(root: Path, rom: bytes, metadata: dict[str, Any]) -> dict[str, Any]:
    selected = {
        name: metadata["runtime"]["symbols"][name]
        for name in (
            "VegaMoveMemory_FieldUse", "VegaMoveMemory_GetMoveRelearnerMoves",
            "VegaMoveMemory_SetNormalMode", "VegaMoveMemory_SetEggMode",
            "VegaMoveMemory_ResetMode", "VegaMoveMemory_ContextAllowedFromState",
            "VegaMoveMemory_EvaluateEggPolicy", "VegaMoveMemory_CanForgetMove",
            "VegaMoveMemory_SelectedMonHasEmptySlot",
            "VegaMoveMemory_SelectedMoveHasPpUps",
            "VegaMoveMemory_SelectedMoveCanForget",
            "VegaMoveMemory_DeleteSelectedMove",
        )
    }
    selected["UpstreamGetMoveRelearnerMoves"] = metadata["source_audit"][
        "linked_symbols"
    ]["GetMoveRelearnerMoves"]
    selected["UpstreamGetAllEggMoves"] = (
        metadata["source_audit"]["linked_symbols"]["GetAllEggMoves"] | 1
    )
    labels = metadata["runtime"]["payload"]["labels"]
    for name in (
        "script_shiou_npc", "script_karasuba_npc", "script_badge1_reward",
        "script_forget_select", "script_forget_pp_warning",
        "script_forget_delete", "script_egg_select", "script_finish",
    ):
        selected[name] = labels[name]
    key, provenance = _runner_cache_key(root, _sha(rom), selected)
    cache = root / MGBA_FIXTURE
    if cache.is_file():
        value = _read_json(cache)
        if value.get("cache", {}).get("key") == key:
            _validate_fixture(value, _sha(rom))
            return value
    with tempfile.TemporaryDirectory(prefix="vega-move-memory-mgba-") as raw:
        directory = Path(raw)
        rom_path = directory / STAGE25.name
        executable = directory / "mgba-move-memory-smoke"
        rom_path.write_bytes(rom)
        _run([
            os.environ.get("CC", "cc"), "-std=c11", "-O2", "-Wall", "-Wextra",
            "-Werror", str(root / RUNNER), "-o", str(executable), "-lmgba",
        ], "move memory libmGBA runner compile", cwd=root)
        args = [str(executable), str(rom_path), _sha(rom)]
        args.extend(f"{name}={address}" for name, address in selected.items())
        first = json.loads(_run(args, "move memory exact-ROM run 1", cwd=root))
        second = json.loads(_run(args, "move memory exact-ROM run 2", cwd=root))
        if first != second:
            _fail("move memory exact-ROM fixture is not process deterministic")
        first["process_runs"] = 2
        first["cache"] = {"key": key, "provenance": provenance}
        _validate_fixture(first, _sha(rom))
        return first


def _report(metadata: dict[str, Any], fixture: dict[str, Any]) -> bytes:
    normal = fixture["normal"]
    egg = fixture["egg"]
    forget = fixture["forget"]
    text = f"""# わざメモリー実装結果

## 結論

- だいじなもの「わざメモリー」を未使用item 347へ登録し、1個目のバッジ報酬へ接続した。
- item、シオウの技教えマニア、カラスバの技忘れオヤジは同じstage 25 coreを呼ぶ。キノコやものまねハーブは消費しない。
- 一時modeは `0x{MODE_RAM:08X}` のvolatile 1 byteで、flash/save flagへ保存しない。

## exact-ROM結果

- 通常候補: Lv.0/1={normal['level_zero_one_included']} / 未来Lv拒否={normal['future_level_rejected']} / 既知・重複除外={normal['known_and_duplicate_filtered']} / 上限={normal['candidate_cap']}
- タマゴ技: CFRU owner一致={egg['direct_owner_match']} / mode reset={egg['mode_reset']} / policy matrix={egg['policy_matrix_cases']} cases
- 技忘れ: 最後の1技={forget['last_move_script_guard']} / PP Up警告={forget['pp_up_warning_script_guard']} / HM許可={forget['hm_allowed']} / 一時form拒否={forget['form_only_rejected']}
- context拒否: {fixture['context']['matrix_pass']} / physical patch: {fixture['physical_patches']['all_match']} / warnings-errors: {fixture['warnings_errors']}

## ROM境界

- Input: `{metadata['input']['sha256']}`
- Output: `{metadata['output']['sha256']}`
- Runtime: `0x{metadata['runtime']['address']:08X}` / {metadata['runtime']['size']} bytes / `{metadata['runtime']['sha256']}`
- allocator overlap: {metadata['allocation']['overlap_count']}
- clean FireRed Rev.0→stage 25 BPS exact: {metadata['release_patch_round_trip']['exact']}

検証済みstage 24を再利用し、全stage再構築は行っていない。
"""
    return text.encode("utf-8")


def collect_outputs(root: Path = ROOT) -> dict[str, bytes]:
    outputs, metadata = _build_stage(root)
    repeated, repeated_metadata = _build_stage(root)
    if outputs != repeated or metadata != repeated_metadata:
        _fail("move memory build is not byte deterministic")
    rom = outputs[STAGE25.as_posix()]
    fixture = _fixture(root, rom, metadata)
    metadata["exact_rom_fixture"] = {
        "path": MGBA_FIXTURE.as_posix(), "status": fixture["status"],
        "process_runs": fixture["process_runs"], "cache_key": fixture["cache"]["key"],
    }
    metadata["acceptance"].update({
        "normal_level_and_duplicate_matrix_pass": fixture["normal"]["future_level_rejected"]
        and fixture["normal"]["known_and_duplicate_filtered"],
        "egg_pre_post_hof_matrix_pass": fixture["egg"]["policy_matrix_cases"] == 5,
        "cancel_reset_pass": fixture["egg"]["mode_reset"],
        "hm_and_form_policy_pass": fixture["forget"]["hm_allowed"]
        and fixture["forget"]["form_only_rejected"],
    })
    if not all(metadata["acceptance"].values()):
        _fail("move memory final acceptance failed")
    outputs[STAGE25_META.as_posix()] = _stable(metadata)
    outputs[MGBA_FIXTURE.as_posix()] = _stable(fixture)
    outputs[REPORT.as_posix()] = _report(metadata, fixture)
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
                f"move memory build: PASS ({len(outputs)} artifacts; "
                f"ROM sha256={_sha(outputs[STAGE25.as_posix()])})"
            )
        else:
            drift = [
                relative for relative, raw in outputs.items()
                if not (ROOT / relative).is_file()
                or (ROOT / relative).read_bytes() != raw
            ]
            if drift:
                _fail("artifact drift: " + ", ".join(drift))
            print(
                f"move memory check: PASS ({len(outputs)} artifacts; "
                f"ROM sha256={_sha(outputs[STAGE25.as_posix()])})"
            )
        return 0
    except (
        MoveMemoryError, OSError, ValueError, KeyError, IndexError,
        StopIteration, subprocess.SubprocessError,
    ) as error:
        print(f"move memory: FAIL: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
