#!/usr/bin/env python3
"""Stage57のQOL・世界・Codex拠点・野生・売買を根本修正してStage58を生成する。"""

from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import io
import json
import os
import re
import subprocess
import struct
import sys
import tempfile
import zlib
from pathlib import Path
from typing import Any, Mapping, NoReturn, Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_trainer_v5_stage32 import (  # noqa: E402
    _arm_tool,
    _sparse_bps,
)
from scripts.run_stage58_mgba_validation import (  # noqa: E402
    DEFAULT_CASES as STAGE58_MGBA_CASES,
    validation_contract as stage58_validation_contract,
)
from tools.regression.rom_runtime import _Blob, _charmap, _encode_text  # noqa: E402
from tools.release.bps import apply_bps, create_bps  # noqa: E402
from tools.rom_allocator import build_allocation_report_from_csv  # noqa: E402
from tools.stage57_debug_suite import (  # noqa: E402
    _collect_contactable_roots,
    quick_audit as stage57_quick_audit,
)
from tools.stage58_qol_economy_audit import (  # noqa: E402
    REQUIRED_STAGE58_VERIFICATION_CASES,
    apply_patch_plan as apply_economy_patch_plan,
    build_audit as build_qol_economy_audit,
)
from tools.stage58_world_balance import build_world_balance_plan  # noqa: E402
from tools.t02.rom_inventory import RomImage, ScriptWalker  # noqa: E402
from tools.trainer_final.kanto_events import (  # noqa: E402
    _map_header_offset,
    _object_fields,
    _stage_map_state,
)


TASK = "USER-20260828-STAGE57-QOL-WORLD-CONVENIENCE-DEBUG"
STAGE = 58
GBA_ROM_BASE = 0x08000000
ROM_SIZE = 32 * 1024 * 1024
PAYLOAD_HEADER_SIZE = 0x100
ALLOCATION_NAME = "qol_world_convenience_stage58_payload"
DEFAULT_CONFIG = Path("config/stage58_qol_world_convenience_debug.json")
QOL_ITEM_ADAPTER_SOURCE = Path(
    "overlays/stage58_qol_world_convenience/stage58_qol_item_adapter.c"
)
QOL_ITEM_ADAPTER_REQUIRED_SYMBOLS = {
    "Stage58QolItemAdapter_Probe",
    "Stage58QolItemAdapter_FieldUseBottleCapAdapter",
    "Stage58QolItemAdapter_CodexSnapshotSeenMirrors",
    "Stage58QolItemAdapter_CodexRestoreSeenMirrors",
    "Stage58QolItemAdapter_CodexContinueSeenHash",
    "Stage58QolItemAdapter_CodexBattleWonAdapter",
    "Stage58QolItemAdapter_CodexBattleLostAdapter",
    "Stage58QolItemAdapter_CodexReturnToFieldAdapter",
    "Stage58QolItemAdapter_CodexTransactionIdentityValid",
    "Stage58QolItemAdapter_CodexResultStateValid",
    "Stage58QolItemAdapter_CodexBattleResultOwned",
    "Stage58QolItemAdapter_CodexLegacyResultHazard",
    "Stage58QolItemAdapter_CodexRewardResultKind",
    "Stage58QolItemAdapter_FinishNonpunitiveCodexResult",
}
WILD_ROOT_POINTER_SITE = 0x0008257C
WILD_HEADER_COUNT = 265
TOHOKU_WILD_HEADER_COUNT = 132
KANTO_WILD_HEADER_COUNT = 133
WILD_CONSUMER_SITES = (
    0x00082938, 0x00082A04, 0x00082A94, 0x00082B04, 0x00082B54,
    0x00082B90, 0x00082BD0, 0x00082C10, 0x00082C98, 0x00082E74,
    0x00082E98, 0x0013D1BC, 0x0013D274,
)
HEAL_SCRIPT = 0x093DCF48
CODEX_NPC_SCRIPT = 0x093CDA80
PC_SCRIPT = 0x08194221
PC_STORAGE_SCRIPT = 0x081942D1
PC_SPECIAL = 60
HEAL_SPECIAL = 0
SAVE_BLOCK1_POINTER_ADDRESS = 0x03005048
SPECIAL_VAR_8000_ADDRESS = 0x02036FEC
SPECIAL_VAR_RESULT_ADDRESS = 0x02037004
MODE_LAYOUT = {
    "land": (12, 4), "water": (5, 8),
    "rock": (5, 12), "fishing": (10, 16),
}


class Stage58BuildError(RuntimeError):
    """Stage58の入力、生成、配線または検証契約違反。"""


def _fail(message: str) -> NoReturn:
    raise Stage58BuildError(message)


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _stable(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2)
            + "\n").encode("utf-8")


def _run(command: Sequence[str], label: str, *, timeout: int = 120) -> str:
    try:
        completed = subprocess.run(
            list(command), cwd=ROOT, text=True, capture_output=True,
            check=False, timeout=timeout,
        )
    except subprocess.TimeoutExpired as error:
        _fail(f"{label} timeout: {error}")
    if completed.returncode:
        detail = (completed.stderr or completed.stdout).strip()
        _fail(f"{label} failed ({completed.returncode}): {detail[-6000:]}")
    return completed.stdout.strip()


def _read_config(path: Path) -> dict[str, Any]:
    value = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        _fail("config rootがobjectではありません")
    if (value.get("schema_version"), value.get("task"), value.get("stage")) \
            != (1, TASK, STAGE):
        _fail("config schema/task/stage不一致")
    hub = value.get("codex_hub", {})
    if (hub.get("group"), hub.get("map"), hub.get("npc_local_id")) != (96, 5, 2):
        _fail("Codex拠点identity不一致")
    return value


def _compile_qol_item_adapter(
    load_address: int,
) -> tuple[bytes, dict[str, int], dict[str, int], dict[str, Any]]:
    """Bottle Cap通常Bag入口をfixed-address Thumb runtimeへ決定論linkする。"""
    source = ROOT / QOL_ITEM_ADAPTER_SOURCE
    if not source.is_file():
        _fail(f"QOL item adapter source不足: {QOL_ITEM_ADAPTER_SOURCE}")
    compiler = _arm_tool(ROOT, "arm-none-eabi-gcc")
    objcopy = _arm_tool(ROOT, "arm-none-eabi-objcopy")
    nm = _arm_tool(ROOT, "arm-none-eabi-nm")
    local = ROOT / ".local"
    local.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix="stage58-qol-item-adapter-", dir=local,
    ) as raw:
        directory = Path(raw)
        obj = directory / "adapter.o"
        elf = directory / "adapter.elf"
        binary = directory / "adapter.bin"
        linker = directory / "linker.ld"
        _run([
            compiler, "-mthumb", "-mcpu=arm7tdmi", "-mthumb-interwork",
            "-Os", "-std=c11", "-Wall", "-Wextra", "-Werror",
            "-ffreestanding", "-fno-builtin", "-fno-unwind-tables",
            "-fno-asynchronous-unwind-tables", "-fdata-sections",
            "-ffunction-sections", "-fno-common", "-c", str(source),
            "-o", str(obj),
        ], "Stage58 QOL item adapter compile")
        linker.write_text(
            "SECTIONS\n{\n"
            f"  . = 0x{load_address:08X};\n"
            "  .text : { KEEP(*(.text.Stage58QolItemAdapter_*)) "
            "*(.text*) *(.rodata*) }\n"
            "  /DISCARD/ : { *(.comment*) *(.ARM.attributes*) *(.note*) "
            "*(.ARM.exidx*) *(.ARM.extab*) }\n"
            "}\n",
            encoding="ascii",
        )
        roots = [
            f"-Wl,--undefined={symbol}"
            for symbol in sorted(QOL_ITEM_ADAPTER_REQUIRED_SYMBOLS)
        ]
        _run([
            compiler, "-mthumb", "-mcpu=arm7tdmi", "-mthumb-interwork",
            "-nostdlib", "-Wl,--build-id=none", "-Wl,--gc-sections",
            *roots, "-Wl,-e,Stage58QolItemAdapter_Probe",
            f"-Wl,-T,{linker}", str(obj), "-lgcc", "-o", str(elf),
        ], "Stage58 QOL item adapter link")
        undefined = _run(
            [nm, "-u", str(elf)], "Stage58 QOL item adapter undefined audit",
        )
        if undefined:
            _fail(f"Stage58 QOL item adapter undefined symbols: {undefined}")
        symbols: dict[str, int] = {}
        sizes: dict[str, int] = {}
        mutable: list[str] = []
        for line in _run([
            nm, "-n", "-S", "--defined-only", str(elf),
        ], "Stage58 QOL item adapter nm").splitlines():
            fields = line.split()
            if len(fields) < 4:
                continue
            try:
                address, size = int(fields[0], 16), int(fields[1], 16)
            except ValueError:
                continue
            kind, name = fields[2], fields[3]
            symbols[name], sizes[name] = address, size
            if kind in {"B", "b", "C", "c", "D", "d", "G", "g", "S", "s"}:
                mutable.append(name)
        missing = sorted(QOL_ITEM_ADAPTER_REQUIRED_SYMBOLS - set(symbols))
        if missing or mutable:
            _fail(
                "Stage58 QOL item adapter symbol audit不一致: "
                f"missing={missing} mutable={mutable}"
            )
        _run([
            objcopy, "-O", "binary", str(elf), str(binary),
        ], "Stage58 QOL item adapter objcopy")
        code = binary.read_bytes()
        if not code or len(code) > 64 * 1024:
            _fail(f"Stage58 QOL item adapter size不正: {len(code)}")
    source_raw = source.read_bytes()
    return code, symbols, sizes, {
        "source": str(QOL_ITEM_ADAPTER_SOURCE),
        "source_sha256": _sha(source_raw),
        "load_address": load_address,
        "size": len(code),
        "sha256": _sha(code),
        "mutable_symbol_count": 0,
        "undefined_symbol_count": 0,
    }


def _identity(contract: Mapping[str, Any], label: str) -> bytes:
    path = ROOT / str(contract["path"])
    raw = path.read_bytes()
    if "size" in contract and len(raw) != int(contract["size"]):
        _fail(f"{label} size不一致: {len(raw)}")
    if _sha(raw) != str(contract["sha256"]):
        _fail(f"{label} SHA-256不一致: {path}")
    return raw


def _thin_flag_owner_audit(
    baseline: bytes,
    output: bytes,
    thin_events: Sequence[Mapping[str, Any]],
    labels: Mapping[str, int],
) -> dict[str, Any]:
    flags = [int(row["flag"]) for row in thin_events]
    wanted = set(flags)
    if len(wanted) != len(flags):
        _fail("thin event flagが重複しています")

    def references(raw: bytes, label: str) -> Counter[tuple[int, str]]:
        image = RomImage(label, raw)
        roots, _ = _collect_contactable_roots(image)
        walker = ScriptWalker(image)
        for root in roots:
            walker.add_root(root)
        graph = walker.walk()
        if graph["diagnostics"]:
            _fail(f"{label} flag owner scanにscript診断があります")
        return Counter(
            (int(row["value"]), str(row["access"]))
            for row in graph["references"]
            if row["category"] == "flag" and int(row["value"]) in wanted
        )

    before = references(baseline, "Stage57")
    after = references(output, "Stage58")
    # 0x140D以降をstock checkflag/setflagへ渡すとSaveBlock1+0x1173を
    # Quest Logがbyte単位で復元する。script graph上のstock flag参照は
    # 0件でなければならず、下でnative ownerのexact byteを検査する。
    if before or after:
        _fail(f"thin event flag owner不一致: before={before} after={after}")

    get_address = int(labels["runtime::thin_flag_get"])
    set_address = int(labels["runtime::thin_flag_set"])
    expected_get, expected_set = _thin_flag_runtime_bytes()
    runtime_rows = []
    for name, address, expected in (
        ("get", get_address, expected_get),
        ("set", set_address, expected_set),
    ):
        offset = address - GBA_ROM_BASE
        if address & 3 or offset < 0 or offset + len(expected) > len(output):
            _fail(f"thin flag {name} runtime配置不一致")
        if output[offset:offset + len(expected)] != expected:
            _fail(f"thin flag {name} runtime exact byte不一致")
        runtime_rows.append({
            "kind": name, "address": address, "size": len(expected),
            "sha256": _sha(expected), "exact_bytes": True,
        })
    for row in thin_events:
        key = str(row["key"])
        flag = int(row["flag"])
        item = int(row["item_id"])
        quantity = int(row["quantity"])
        label = str(row["script_label"])
        already = f"{label}::already"
        full = f"{label}::full"
        end = f"{label}::end"
        main = bytearray((0x6A, 0x5A, 0x1A, 0x00, 0x80))
        main.extend(struct.pack("<H", flag))
        main.append(0x23)
        main.extend(struct.pack("<I", get_address | 1))
        main.extend((0x21, 0x0D, 0x80, 0x01, 0x00, 0x06, 0x01))
        main.extend(struct.pack("<I", int(labels[already])))
        main.extend((0x0F, 0x00))
        main.extend(struct.pack("<I", int(labels["text_research_intro"])))
        main.extend((0x09, 0x04, 0x44))
        main.extend(struct.pack("<HH", item, quantity))
        main.extend((0x21, 0x0D, 0x80, 0x00, 0x00, 0x06, 0x01))
        main.extend(struct.pack("<I", int(labels[full])))
        main.extend((0x1A, 0x00, 0x80))
        main.extend(struct.pack("<H", flag))
        main.append(0x23)
        main.extend(struct.pack("<I", set_address | 1))
        main.extend((0x0F, 0x00))
        main.extend(struct.pack("<I", int(labels["text_research_reward"])))
        main.extend((0x09, 0x04, 0x05))
        main.extend(struct.pack("<I", int(labels[end])))
        offset = int(labels[label]) - GBA_ROM_BASE
        if output[offset:offset + len(main)] != main:
            _fail(f"thin event native owner script byte不一致: {key}")

        for branch, text in ((already, "text_research_already"),
                             (full, "text_research_full")):
            expected = bytearray((0x0F, 0x00))
            expected.extend(struct.pack("<I", int(labels[text])))
            expected.extend((0x09, 0x04, 0x05))
            expected.extend(struct.pack("<I", int(labels[end])))
            branch_offset = int(labels[branch]) - GBA_ROM_BASE
            if output[branch_offset:branch_offset + len(expected)] != expected:
                _fail(f"thin event branch byte不一致: {key}/{branch}")
        end_offset = int(labels[end]) - GBA_ROM_BASE
        if output[end_offset:end_offset + 2] != bytes((0x6C, 0x02)):
            _fail(f"thin event lifecycle end byte不一致: {key}")
    return {
        "status": "PASS",
        "serialized_layout_change_count": 0,
        "global_flag_ids": list(flags),
        "baseline_reference_count": 0,
        "stock_output_reference_count": 0,
        "native_get_call_count": len(flags),
        "native_set_call_count": len(flags),
        "native_runtime_exact": True,
        "native_runtime_rows": runtime_rows,
        "getter_result_address": SPECIAL_VAR_RESULT_ADDRESS,
        "setter_read_modify_write": True,
        "quest_log_safe": True,
        "unexpected_access_count": 0,
    }


def _csv(raw: bytes, label: str) -> list[dict[str, str]]:
    try:
        return list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))))
    except (UnicodeDecodeError, csv.Error) as error:
        _fail(f"{label} CSV不正: {error}")


def _previous_requests(previous: Mapping[str, Any]) -> list[dict[str, Any]]:
    if previous.get("summaries", {}).get("overlap_count") != 0:
        _fail("Stage57 allocation reportにoverlapがあります")
    return [{
        key: row[key]
        for key in ("name", "region", "size", "alignment", "owner", "purpose",
                    "content_sha256")
    } for row in previous["allocations"]]


def _allocation(previous: Mapping[str, Any], size: int, digest: str) \
        -> tuple[dict[str, Any], dict[str, Any]]:
    requests = _previous_requests(previous)
    requests.append({
        "name": ALLOCATION_NAME, "region": "integration_modules",
        "size": size, "alignment": 16, "owner": TASK,
        "purpose": "Codex拠点PC・全回復・money mart、Kanto野生方式/確率、薄い場所イベント",
        "content_sha256": digest,
    })
    report = build_allocation_report_from_csv(ROOT / "config/rom_regions.csv", requests)
    if report.get("summaries", {}).get("overlap_count") != 0:
        _fail("Stage58 allocator overlap")
    rows = [row for row in report["allocations"] if row["name"] == ALLOCATION_NAME]
    if len(rows) != 1:
        _fail("Stage58 payload allocationが一意ではありません")
    return rows[0], report


def _pack_object(*, local_id: int, graphics_id: int, x: int, y: int,
                 elevation: int, script: int = 0) -> bytes:
    raw = bytearray(24)
    raw[0:4] = bytes((local_id, graphics_id, 0, 0))
    struct.pack_into("<HH", raw, 4, x, y)
    raw[8:12] = bytes((elevation, 8, 0x11, 0))
    struct.pack_into("<HHIHH", raw, 12, 0, 0, script, 0, 0)
    return bytes(raw)


def _validate_hub_cell(stage: bytes, group: int, number: int, x: int, y: int,
                       elevation: int) -> dict[str, Any]:
    _, header = _map_header_offset(stage, group, number)
    layout = struct.unpack_from("<I", stage, header)[0] - GBA_ROM_BASE
    width, height = struct.unpack_from("<II", stage, layout)
    if not (0 <= x < width and 0 <= y < height):
        _fail(f"Codex追加座標がmap外: ({x},{y})")
    blocks = struct.unpack_from("<I", stage, layout + 12)[0] - GBA_ROM_BASE
    value = struct.unpack_from("<H", stage, blocks + 2 * (y * width + x))[0]
    collision, actual_elevation = (value >> 10) & 3, (value >> 12) & 0xF
    state = _stage_map_state(stage, group, number)
    event_collision: list[str] = []
    for index, raw in enumerate(state["objects"]):
        fields = _object_fields(raw)
        if (fields["x"], fields["y"]) == (x, y):
            event_collision.append(f"object:{index}")
    for kind, key, size in (("warp", "warps_hex", 8), ("coord", "coords_hex", 16),
                            ("bg", "bg_hex", 12)):
        raw = bytes.fromhex(str(state[key]))
        for offset in range(0, len(raw), size):
            if struct.unpack_from("<HH", raw, offset) == (x, y):
                event_collision.append(f"{kind}:{offset // size}")
    if collision != 0 or actual_elevation != elevation or event_collision:
        _fail(
            f"Codex追加座標が安全ではありません: ({x},{y}) "
            f"collision={collision} elevation={actual_elevation} events={event_collision}"
        )
    return {
        "x": x, "y": y, "metatile": value & 0x3FF,
        "collision": collision, "elevation": actual_elevation,
        "event_collisions": event_collision,
    }


def _add_script_texts(blob: _Blob) -> None:
    mapping, tokens = _charmap(ROOT)
    blob.add(
        "text_codex_mart",
        _encode_text("たいせんと たんさくの\nじゅんびを ととのえます。", mapping, tokens),
        1,
    )
    for label, text in {
        "text_research_intro": "この ばしょの きろくを\nあつめています。 どうぞ！",
        "text_research_reward": "たんさくセットを もらった！",
        "text_research_already": "この ちいきの ちょうさは\nぶじに おわりました。",
        "text_research_full": "バッグが いっぱいです。\nあけてから また きてください。",
    }.items():
        blob.add(label, _encode_text(text, mapping, tokens), 1)


def _script_pointer(data: bytearray, fixups: list[tuple[int, str]], label: str) -> None:
    fixups.append((len(data), label))
    data.extend(bytes(4))


def _script_msgbox(data: bytearray, fixups: list[tuple[int, str]], label: str) -> None:
    data.extend((0x0F, 0x00))
    _script_pointer(data, fixups, label)
    data.extend((0x09, 0x04))


def _thin_flag_runtime_bytes() -> tuple[bytes, bytes]:
    """Stage53と同じexpanded flag ownerのexact machine-code正本。"""
    get_raw = struct.pack(
        "<22HIII",
        0x480A, 0x8800, 0x08C1, 0x2307, 0x4018, 0x4A09,
        0x6812, 0x23EE, 0x011B, 0x18D2, 0x1852, 0x7812,
        0x2301, 0x4083, 0x401A, 0x2A00, 0xD000, 0x2201,
        0x4803, 0x8002, 0x4770, 0x46C0,
        SPECIAL_VAR_8000_ADDRESS, SAVE_BLOCK1_POINTER_ADDRESS,
        SPECIAL_VAR_RESULT_ADDRESS,
    )
    set_raw = struct.pack(
        "<18HII",
        0x4808, 0x8800, 0x08C1, 0x2307, 0x4018, 0x4A07,
        0x6812, 0x23EE, 0x011B, 0x18D2, 0x1852, 0x7811,
        0x2301, 0x4083, 0x4319, 0x7011, 0x4770, 0x46C0,
        SPECIAL_VAR_8000_ADDRESS, SAVE_BLOCK1_POINTER_ADDRESS,
    )
    if len(get_raw) != 56 or len(set_raw) != 44:
        _fail("thin flag runtime size不一致")
    return get_raw, set_raw


def _add_thin_flag_runtime(blob: _Blob) -> None:
    """Quest Logのbyte復元を迂回してexpanded save flagを直接扱う。"""
    # Stage53でitem ball/hidden itemに使用し、通常取得・Bag full・次入力・
    # save/reloadまで実証済みのSaveBlock1 expanded-flag ownerと同じABI。
    get_raw, set_raw = _thin_flag_runtime_bytes()
    blob.add("runtime::thin_flag_get", get_raw, 4)
    blob.add("runtime::thin_flag_set", set_raw, 4)


def _add_exploration_script(blob: _Blob, key: str, flag: int, item: int,
                            quantity: int) -> str:
    label = f"thin::{key}::script"
    already, full, end = f"{label}::already", f"{label}::full", f"{label}::end"
    data, fixups = bytearray((0x6A, 0x5A, 0x1A, 0x00, 0x80)), []
    data.extend(struct.pack("<H", flag))
    data.append(0x23)
    get_fixup = len(data)
    data.extend(bytes(4))
    data.extend((0x21, 0x0D, 0x80, 0x01, 0x00, 0x06, 0x01))
    _script_pointer(data, fixups, already)
    _script_msgbox(data, fixups, "text_research_intro")
    data.extend((0x44,))
    data.extend(struct.pack("<HH", item, quantity))
    data.extend((0x21,))
    data.extend(struct.pack("<HH", 0x800D, 0))
    data.extend((0x06, 0x01))
    _script_pointer(data, fixups, full)
    data.extend((0x1A, 0x00, 0x80))
    data.extend(struct.pack("<H", flag))
    data.append(0x23)
    set_fixup = len(data)
    data.extend(bytes(4))
    _script_msgbox(data, fixups, "text_research_reward")
    data.extend((0x05,))
    _script_pointer(data, fixups, end)
    at = blob.add(label, bytes(data), 4)
    blob.pointer(at + get_fixup, "runtime::thin_flag_get", thumb=True)
    blob.pointer(at + set_fixup, "runtime::thin_flag_set", thumb=True)
    for offset, target in fixups:
        blob.pointer(at + offset, target)

    for branch, text in ((already, "text_research_already"),
                         (full, "text_research_full")):
        branch_data, branch_fixups = bytearray(), []
        _script_msgbox(branch_data, branch_fixups, text)
        branch_data.extend((0x05,))
        _script_pointer(branch_data, branch_fixups, end)
        branch_at = blob.add(branch, bytes(branch_data), 4)
        for offset, target in branch_fixups:
            blob.pointer(branch_at + offset, target)
    blob.add(end, bytes((0x6C, 0x02)), 4)
    return label


def _emit_thin_events(blob: _Blob, stage: bytes, config: Mapping[str, Any],
                      plan: Mapping[str, Any]) -> list[dict[str, Any]]:
    candidates = {
        (int(row["group"]), int(row["map"]), int(row["x"]), int(row["y"])): row
        for row in plan.get("thin_candidates", [])
    }
    rows: list[dict[str, Any]] = []
    seen_maps: set[tuple[int, int]] = set()
    seen_flags: set[int] = set()
    for configured in config.get("thin_events", []):
        row = dict(configured)
        key = str(row["key"])
        group, number = int(row["group"]), int(row["map"])
        x, y, elevation = int(row["x"]), int(row["y"]), int(row["elevation"])
        flag = int(str(row["flag"]), 0)
        item, quantity = int(row["item_id"]), int(row["quantity"])
        coordinate = (group, number)
        candidate_key = (group, number, x, y)
        candidate = candidates.get(candidate_key)
        if candidate is None or candidate.get("map_key") != row["map_key"] \
                or candidate.get("reward_tier") != row["reward_tier"]:
            _fail(f"thin eventが定量候補と一致しません: {key}")
        if coordinate in seen_maps or flag in seen_flags:
            _fail(f"thin event map/flag重複: {key}")
        seen_maps.add(coordinate)
        seen_flags.add(flag)
        cell = _validate_hub_cell(stage, group, number, x, y, elevation)
        state = _stage_map_state(stage, group, number)
        if int(state["counts"]["objects"]) >= 15:
            _fail(f"thin event object上限超過: {key}")
        used = {_object_fields(raw)["local_id"] for raw in state["objects"]}
        local_id = next((value for value in range(1, 0x100) if value not in used), None)
        if local_id is None:
            _fail(f"thin event local ID不足: {key}")
        script = _add_exploration_script(blob, key, flag, item, quantity)
        new_object = _pack_object(
            local_id=local_id, graphics_id=int(row["graphics_id"]), x=x, y=y,
            elevation=elevation,
        )
        objects_at = blob.add(
            f"thin::{key}::objects", b"".join(state["objects"]) + new_object, 4,
        )
        blob.pointer(objects_at + len(state["objects"]) * 24 + 16, script)
        event = bytearray(struct.pack(
            "<BBBBIIII", len(state["objects"]) + 1,
            int(state["counts"]["warps"]), int(state["counts"]["coords"]),
            int(state["counts"]["bg"]), 0, int(state["pointers"]["warps"]),
            int(state["pointers"]["coords"]), int(state["pointers"]["bg"]),
        ))
        event_at = blob.add(f"thin::{key}::events", bytes(event), 4)
        blob.pointer(event_at + 4, f"thin::{key}::objects")
        _, header = _map_header_offset(stage, group, number)
        rows.append({
            **row, "flag": flag, "local_id": local_id, "cell": cell,
            "object_count_before": len(state["objects"]),
            "object_count_after": len(state["objects"]) + 1,
            "event_header_before": int(state["event_header_address"]),
            "map_header_event_pointer_offset": header + 4,
            "event_label": f"thin::{key}::events", "script_label": script,
            "candidate_reason": candidate["reason"],
        })
    if len(rows) < 4:
        _fail(f"thin event採用数が不足: {len(rows)}")
    return rows


def _emit_hub_payload(blob: _Blob, stage: bytes, config: Mapping[str, Any]) \
        -> dict[str, Any]:
    hub = config["codex_hub"]
    group, number = int(hub["group"]), int(hub["map"])
    state = _stage_map_state(stage, group, number)
    if state["counts"]["objects"] != 10:
        _fail(f"Codex拠点object数drift: {state['counts']['objects']}")
    npc = [_object_fields(raw) for raw in state["objects"]
           if _object_fields(raw)["local_id"] == int(hub["npc_local_id"])]
    if len(npc) != 1 or npc[0]["graphics_id"] != 62 \
            or (npc[0]["x"], npc[0]["y"], npc[0]["script_pointer"]) \
            != (20, 19, CODEX_NPC_SCRIPT):
        _fail("Codex対戦NPC identity drift")
    used = {_object_fields(raw)["local_id"] for raw in state["objects"]}
    additions: list[tuple[str, Mapping[str, Any], bytes]] = []
    for name in ("pc", "healer", "mart"):
        row = hub[name]
        local_id = int(row["local_id"])
        if local_id in used:
            _fail(f"Codex追加local ID競合: {local_id}")
        cell = _validate_hub_cell(
            stage, group, number, int(row["x"]), int(row["y"]),
            int(row["elevation"]),
        )
        raw = _pack_object(
            local_id=local_id, graphics_id=int(row["graphics_id"]),
            x=int(row["x"]), y=int(row["y"]), elevation=int(row["elevation"]),
            script=(HEAL_SCRIPT if name == "healer" else
                    PC_SCRIPT if name == "pc" else 0),
        )
        additions.append((name, {**row, "cell": cell}, raw))
        used.add(local_id)

    # objectからもstock EventScript_PCを使う。special 60だけの直呼びは
    # help context/PC menu/return callbackを構築せず、field復帰できない。
    pc_signature = bytes.fromhex(
        "258701210d80020006018a50190869"
    )
    pc_offset = PC_SCRIPT - GBA_ROM_BASE
    storage_offset = PC_STORAGE_SCRIPT - GBA_ROM_BASE
    if stage[pc_offset:pc_offset + len(pc_signature)] != pc_signature \
            or stage[storage_offset:storage_offset + 48].find(
                bytes((0x25, PC_SPECIAL, 0x00, 0x27)),
            ) < 0:
        _fail("stock EventScript_PC/Storage lifecycle drift")
    items = [int(value) for value in hub["mart_item_ids"]]
    if not items or len(items) != len(set(items)) or any(not 1 <= value <= 998 for value in items):
        _fail("Codex money mart item list不正")
    blob.add("codex_mart_items", struct.pack(f"<{len(items) + 1}H", *items, 0), 2)
    mart = bytearray((0x6A, 0x5A, 0x0F, 0x00))
    mart_text_fixup = len(mart)
    mart.extend(bytes(4))
    mart.extend((0x09, 0x04, 0x86))
    mart_items_fixup = len(mart)
    mart.extend(bytes(4))
    mart.extend((0x6C, 0x02))
    mart_at = blob.add("script_codex_mart", bytes(mart), 4)
    blob.pointer(mart_at + mart_text_fixup, "text_codex_mart")
    blob.pointer(mart_at + mart_items_fixup, "codex_mart_items")

    object_at = blob.add(
        "codex_hub_objects",
        b"".join(state["objects"]) + b"".join(raw for _, _, raw in additions),
        4,
    )
    object_index = len(state["objects"])
    blob.pointer(object_at + (object_index + 2) * 24 + 16, "script_codex_mart")
    event = bytearray(struct.pack(
        "<BBBBIIII", len(state["objects"]) + len(additions),
        int(state["counts"]["warps"]), int(state["counts"]["coords"]),
        int(state["counts"]["bg"]), 0, int(state["pointers"]["warps"]),
        int(state["pointers"]["coords"]), int(state["pointers"]["bg"]),
    ))
    event_at = blob.add("codex_hub_events", bytes(event), 4)
    blob.pointer(event_at + 4, "codex_hub_objects")
    return {
        "status": "PASS", "group": group, "map": number,
        "event_header_before": int(state["event_header_address"]),
        "object_count_before": len(state["objects"]),
        "object_count_after": len(state["objects"]) + len(additions),
        "npc": npc[0],
        "additions": [{"kind": name, **dict(row)} for name, row, _ in additions],
        "mart_items": items, "storage_special": PC_SPECIAL,
        "pc_script": PC_SCRIPT, "pc_storage_script": PC_STORAGE_SCRIPT,
        "heal_special": HEAL_SPECIAL, "heal_script": HEAL_SCRIPT,
    }


def _emit_wild_payload(blob: _Blob, stage: bytes, plan: Mapping[str, Any]) \
        -> dict[str, Any]:
    root_pointer = struct.unpack_from("<I", stage, WILD_ROOT_POINTER_SITE)[0]
    root = root_pointer - GBA_ROM_BASE
    table_size = (WILD_HEADER_COUNT + 1) * 20
    if root < 0 or root + table_size > len(stage):
        _fail("Stage57 wild rootがROM外")
    terminator = stage[root + WILD_HEADER_COUNT * 20:root + table_size]
    if len(terminator) != 20 or terminator[:2] != b"\xFF\xFF":
        _fail("Stage57 wild terminator不正")
    headers = list(plan.get("headers", []))
    if len(headers) != KANTO_WILD_HEADER_COUNT:
        _fail(f"Kanto wild plan件数不一致: {len(headers)}")
    seen: set[tuple[int, int]] = set()
    mode_counts = {name: 0 for name in MODE_LAYOUT}
    slot_count = 0
    for row in headers:
        coordinate = (int(row["group"]), int(row["map"]))
        if coordinate in seen:
            _fail(f"Kanto wild coordinate重複: {coordinate}")
        seen.add(coordinate)
        for mode, (expected_slots, _) in MODE_LAYOUT.items():
            value = row["modes"].get(mode)
            if value is None:
                continue
            slots = [tuple(int(part) for part in slot) for slot in value["slots"]]
            if len(slots) != expected_slots:
                _fail(f"wild slot数不一致: {coordinate}/{mode}/{len(slots)}")
            for low, high, species in slots:
                if not (1 <= low <= high <= 100 and 1 <= species <= 1620):
                    _fail(f"wild slot値不正: {coordinate}/{mode}/{(low, high, species)}")
            prefix = f"wild::{coordinate[0]}::{coordinate[1]}::{mode}"
            blob.add(prefix + "::slots", b"".join(
                struct.pack("<BBH", low, high, species) for low, high, species in slots
            ), 4)
            info = blob.add(
                prefix + "::info", bytes((int(value["rate"]), 0, 0, 0)) + bytes(4), 4,
            )
            blob.pointer(info + 4, prefix + "::slots")
            mode_counts[mode] += 1
            slot_count += len(slots)

    old_tohoku = stage[root:root + TOHOKU_WILD_HEADER_COUNT * 20]
    wild_at = blob.add("wild_headers_root", old_tohoku, 4)
    for row in headers:
        coordinate = (int(row["group"]), int(row["map"]))
        record = blob.add(
            f"wild_header::{coordinate[0]}::{coordinate[1]}",
            struct.pack("<BBHIIII", coordinate[0], coordinate[1], 0, 0, 0, 0, 0), 4,
        )
        for mode, (_, relative) in MODE_LAYOUT.items():
            if row["modes"].get(mode) is not None:
                blob.pointer(record + relative,
                             f"wild::{coordinate[0]}::{coordinate[1]}::{mode}::info")
    blob.add("wild_headers_terminator", terminator, 4)
    if blob.labels["wild_headers_root"] != wild_at:
        _fail("wild root label drift")
    return {
        "status": "PASS", "old_root": root_pointer,
        "tohoku_headers_preserved": TOHOKU_WILD_HEADER_COUNT,
        "kanto_headers_rebuilt": len(headers), "mode_tables": mode_counts,
        "native_slots": slot_count, "coordinates_unique": True,
    }


def _build_payload(stage: bytes, config: Mapping[str, Any], plan: Mapping[str, Any],
                   payload_offset: int, qol_item_adapter_code: bytes) \
        -> tuple[bytes, dict[str, int], dict[str, Any]]:
    blob = _Blob()
    if blob.reserve("payload_header", PAYLOAD_HEADER_SIZE, 16) != 0:
        _fail("payload header offset不一致")
    _add_script_texts(blob)
    _add_thin_flag_runtime(blob)
    hub = _emit_hub_payload(blob, stage, config)
    thin_events = _emit_thin_events(blob, stage, config, plan)
    wild = _emit_wild_payload(blob, stage, plan)
    blob.add("qol_item_adapter_runtime", qol_item_adapter_code, 4)
    blob.align(16, 0xFF)
    payload = bytearray(blob.finish(payload_offset))
    struct.pack_into(
        "<8s10I", payload, 0, b"VEGAWB58", 1, len(payload),
        blob.labels["codex_hub_events"], PC_SCRIPT,
        blob.labels["script_codex_mart"], blob.labels["codex_mart_items"],
        blob.labels["wild_headers_root"], KANTO_WILD_HEADER_COUNT,
        wild["native_slots"], len(thin_events),
    )
    labels = {
        name: GBA_ROM_BASE + payload_offset + relative
        for name, relative in sorted(blob.labels.items())
    }
    return bytes(payload), labels, {"hub": hub, "thin_events": thin_events, "wild": wild}


def _patch_pointer(output: bytearray, baseline: bytes, declared: list[dict[str, Any]],
                   offset: int, expected: int, replacement: int, name: str) -> None:
    if struct.unpack_from("<I", baseline, offset)[0] != expected \
            or struct.unpack_from("<I", output, offset)[0] != expected:
        _fail(f"pointer expected値不一致: {name}@0x{offset:08X}")
    struct.pack_into("<I", output, offset, replacement)
    declared.append({
        "kind": "pointer", "name": name,
        "address": GBA_ROM_BASE + offset, "start": offset,
        "end_exclusive": offset + 4, "expected": expected,
        "replacement": replacement,
    })


def _thumb_bl(source: int, target: int) -> bytes:
    """ARMv4T Thumb-1 BLをsourceの4 byte命令としてencodeする。"""
    delta = target - (source + 4)
    if delta & 1 or not -(1 << 22) <= delta < (1 << 22):
        _fail(
            f"Thumb BL range/alignment不正: 0x{source:08X}->0x{target:08X}"
        )
    return struct.pack(
        "<HH", 0xF000 | ((delta >> 12) & 0x07FF),
        0xF800 | ((delta >> 1) & 0x07FF),
    )


def _validate_gba_lz77(
    rom: bytes,
    offset: int,
    expected_size: int,
    label: str,
) -> int:
    """GBA LZ77 streamを最後まで展開し、展開長とback-referenceを検証する。"""
    if offset < 0 or offset + 4 > len(rom) or rom[offset] != 0x10:
        _fail(f"{label} LZ77 header不一致: ROM+0x{offset:08X}")
    declared_size = int.from_bytes(rom[offset + 1:offset + 4], "little")
    if declared_size != expected_size:
        _fail(
            f"{label} LZ77展開長不一致: expected={expected_size} "
            f"declared={declared_size}"
        )

    cursor = offset + 4
    decoded = bytearray()
    while len(decoded) < declared_size:
        if cursor >= len(rom):
            _fail(f"{label} LZ77 flagがROM終端を越えました")
        flags = rom[cursor]
        cursor += 1
        for bit in range(7, -1, -1):
            if len(decoded) >= declared_size:
                break
            if flags & (1 << bit):
                if cursor + 2 > len(rom):
                    _fail(f"{label} LZ77 back-referenceがROM終端を越えました")
                high, low = rom[cursor], rom[cursor + 1]
                cursor += 2
                run_length = (high >> 4) + 3
                distance = ((high & 0x0F) << 8 | low) + 1
                if distance > len(decoded):
                    _fail(
                        f"{label} LZ77 back-referenceが展開済み領域外です: "
                        f"distance={distance} decoded={len(decoded)}"
                    )
                for _ in range(run_length):
                    if len(decoded) >= declared_size:
                        _fail(f"{label} LZ77 tokenが宣言展開長を越えました")
                    decoded.append(decoded[-distance])
            else:
                if cursor >= len(rom):
                    _fail(f"{label} LZ77 literalがROM終端を越えました")
                decoded.append(rom[cursor])
                cursor += 1
    return cursor - offset


def _apply_qol_item_graphics_repoints(
    output: bytearray,
    baseline: bytes,
    contract: Mapping[str, Any],
    declared: list[dict[str, Any]],
) -> dict[str, Any]:
    legacy = int(str(contract.get("legacy_table")), 0)
    canonical = int(str(contract.get("canonical_table")), 0)
    item_count = int(contract.get("item_count", 0))
    sites = [int(str(value), 0)
             for value in contract.get("consumer_pointer_sites", [])]
    legacy_cancel = int(contract.get("legacy_cancel_icon_item", -1))
    canonical_cancel = int(contract.get("canonical_cancel_icon_item", -1))
    cancel_sites = [int(str(value), 0)
                    for value in contract.get("cancel_icon_item_sites", [])]
    if item_count != 999 or len(sites) != 3 or len(set(sites)) != len(sites):
        _fail("QOL item graphics repoint inventory不一致")
    if (legacy_cancel, canonical_cancel) != (375, 589) \
            or len(cancel_sites) != 3 \
            or len(set(cancel_sites)) != len(cancel_sites):
        _fail("QOL cancel icon item inventory不一致")
    if legacy == canonical or canonical & 3 or any(site & 3 for site in sites):
        _fail("QOL item graphics pointer alignment不一致")
    table_offset = canonical - GBA_ROM_BASE
    table_end = table_offset + item_count * 8
    if table_offset < 0 or table_end > len(baseline):
        _fail("canonical item graphics tableがROM外です")

    compressed_pointer_count = 0
    validated_streams: dict[tuple[int, int], int] = {}
    for item_id in range(item_count):
        graphics, palette = struct.unpack_from(
            "<II", baseline, table_offset + item_id * 8,
        )
        for kind, pointer, expected_size in (
            ("graphics", graphics, 288),
            ("palette", palette, 32),
        ):
            offset = pointer - GBA_ROM_BASE
            if offset < 0 or offset >= len(baseline):
                _fail(
                    f"item {item_id} {kind} LZ77 pointer不一致: 0x{pointer:08X}"
                )
            cache_key = (offset, expected_size)
            if cache_key not in validated_streams:
                validated_streams[cache_key] = _validate_gba_lz77(
                    baseline,
                    offset,
                    expected_size,
                    f"item {item_id} {kind}",
                )
            compressed_pointer_count += 1

    for site in sites:
        offset = site - GBA_ROM_BASE
        if offset < 0 or offset + 4 > len(baseline):
            _fail(f"item graphics consumer siteがROM外です: 0x{site:08X}")
        _patch_pointer(
            output, baseline, declared, offset, legacy, canonical,
            f"qol_item_graphics_consumer_{site:08x}",
        )
    if any(struct.unpack_from("<I", output, site - GBA_ROM_BASE)[0] != canonical
           for site in sites):
        _fail("QOL item graphics consumer repoint反映不一致")
    legacy_bytes = struct.pack("<I", legacy)
    canonical_bytes = struct.pack("<I", canonical)
    expected_offsets = sorted(site - GBA_ROM_BASE for site in sites)

    def _all_offsets(raw: bytes | bytearray, needle: bytes) -> list[int]:
        found: list[int] = []
        cursor = 0
        while True:
            cursor = raw.find(needle, cursor)
            if cursor < 0:
                return found
            found.append(cursor)
            cursor += 1

    if (_all_offsets(baseline, legacy_bytes) != expected_offsets
            or _all_offsets(baseline, canonical_bytes)
            or _all_offsets(output, legacy_bytes)
            or _all_offsets(output, canonical_bytes) != expected_offsets):
        _fail("QOL item graphics tableのROM-wide literal owner不一致")

    legacy_cancel_row = legacy - GBA_ROM_BASE + legacy_cancel * 8
    canonical_cancel_row = table_offset + canonical_cancel * 8
    if baseline[legacy_cancel_row:legacy_cancel_row + 8] \
            != baseline[canonical_cancel_row:canonical_cancel_row + 8]:
        _fail("canonical cancel iconが旧専用iconとbyte一致しません")
    for site in cancel_sites:
        offset = site - GBA_ROM_BASE
        if offset < 0 or offset + 4 > len(baseline) \
                or struct.unpack_from("<I", baseline, offset)[0] != legacy_cancel \
                or struct.unpack_from("<I", output, offset)[0] != legacy_cancel:
            _fail(f"cancel icon item expected値不一致: 0x{site:08X}")
        struct.pack_into("<I", output, offset, canonical_cancel)
        declared.append({
            "kind": "constant",
            "name": f"qol_cancel_icon_item_{site:08x}",
            "address": site,
            "start": offset,
            "end_exclusive": offset + 4,
            "expected": legacy_cancel,
            "replacement": canonical_cancel,
        })
    return {
        "status": "PASS",
        "root_cause": (
            "通常Bagのitem icon consumerだけが旧375行表を参照し、"
            "追加QOL itemで表外LZ77展開していた"
        ),
        "legacy_table": legacy,
        "canonical_table": canonical,
        "item_count": item_count,
        "consumer_pointer_sites": sites,
        "repoint_count": len(sites),
        "legacy_literal_remaining_count": 0,
        "canonical_literal_owner_count": len(sites),
        "legacy_cancel_icon_item": legacy_cancel,
        "canonical_cancel_icon_item": canonical_cancel,
        "cancel_icon_item_sites": cancel_sites,
        "cancel_icon_rebind_count": len(cancel_sites),
        "cancel_icon_exact_row_match": True,
        "lz77_pointer_count": compressed_pointer_count,
        "lz77_unique_stream_count": len(validated_streams),
        "lz77_decompressed_byte_count": sum(
            expected_size for _, expected_size in validated_streams
        ),
        "invalid_pointer_count": 0,
    }


def _apply_qol_item_id_clamp(
    output: bytearray,
    baseline: bytes,
    contract: Mapping[str, Any],
    declared: list[dict[str, Any]],
) -> dict[str, Any]:
    site = int(str(contract.get("site")), 0)
    size = int(contract.get("size", 0))
    legacy_max = int(contract.get("legacy_max_inclusive", -1))
    valid_max = int(contract.get("valid_max_exclusive", 0))
    try:
        expected = bytes.fromhex(str(contract.get("expected", "")))
        replacement = bytes.fromhex(str(contract.get("replacement", "")))
    except ValueError as exc:
        _fail(f"QOL item ID clamp hex不正: {exc}")
    offset = site - GBA_ROM_BASE
    if (size != 24 or legacy_max != 748 or valid_max != 999
            or len(expected) != size or len(replacement) != size):
        _fail("QOL item ID clamp contract不一致")
    if offset < 0 or offset + size > len(baseline):
        _fail("QOL item ID clamp siteがROM外です")
    if baseline[offset:offset + size] != expected \
            or output[offset:offset + size] != expected:
        _fail("QOL item ID clamp expected byte不一致")
    # 0..998を通し、999以上を0へ正規化する共通ItemId getter leaf。
    # Thumb即値 250*4-1 = 999 とunsigned BCSで境界を固定し、旧実装どおり
    # r1=return address、valid/invalid双方の条件flagも保って既存binary ABIへ戻る。
    if replacement[4:10] != bytes.fromhex("fa2189000139") \
            or replacement[12:14] != bytes.fromhex("01d2") \
            or replacement[14:] != bytes.fromhex("001c00e0002071467047"):
        _fail("QOL item ID clamp境界命令不一致")
    output[offset:offset + size] = replacement
    declared.append({
        "kind": "code", "name": "qol_item_id_common_clamp",
        "address": site, "start": offset, "end_exclusive": offset + size,
        "expected": expected.hex(), "replacement": replacement.hex(),
    })
    return {
        "status": "PASS",
        "root_cause": (
            "全ItemId_Get*共通clampが旧最大748を保持し、"
            "追加QOL item IDを0へ正規化してfield callbackを失わせていた"
        ),
        "site": site,
        "patched_byte_count": size,
        "legacy_max_inclusive": legacy_max,
        "valid_min_inclusive": 0,
        "valid_max_inclusive": valid_max - 1,
        "invalid_min_inclusive": valid_max,
        "invalid_maps_to": 0,
        "legacy_r1_return_side_effect_preserved": True,
        "legacy_condition_flags_preserved": True,
    }


def _apply_qol_item_bag_adapter(
    output: bytearray,
    baseline: bytes,
    contract: Mapping[str, Any],
    symbols: Mapping[str, int],
    sizes: Mapping[str, int],
    link_evidence: Mapping[str, Any],
    declared: list[dict[str, Any]],
) -> dict[str, Any]:
    table = int(str(contract.get("item_table")), 0)
    stride = int(contract.get("row_size", 0))
    id_offset = int(contract.get("id_offset", -1))
    pocket_offset = int(contract.get("pocket_offset", -1))
    type_offset = int(contract.get("type_offset", -1))
    callback_offset = int(contract.get("field_callback_offset", -1))
    expected_callback = int(str(contract.get("expected_field_callback")), 0)
    expected_type = int(contract.get("expected_type", -1))
    replacement_type = int(contract.get("replacement_type", -1))
    item_ids = [int(value) for value in contract.get("item_ids", [])]
    symbol = str(contract.get("replacement_symbol", ""))
    if (
        table != 0x0904D108
        or stride != 40
        or id_offset != 10
        or pocket_offset != 22
        or type_offset != 23
        or callback_offset != 24
        or expected_callback != 0x080A34F9
        or expected_type != 4
        or replacement_type != 1
        or item_ids != [853, 854]
        or symbol != "Stage58QolItemAdapter_FieldUseBottleCapAdapter"
        or symbol not in symbols
        or not int(sizes.get(symbol, 0)) > 0
    ):
        _fail("QOL item Bag adapter contract不一致")
    replacement = int(symbols[symbol]) | 1
    if replacement < GBA_ROM_BASE or replacement >= GBA_ROM_BASE + len(output):
        _fail("QOL item Bag adapter callbackがROM外です")

    rows: list[dict[str, Any]] = []
    for item_id in item_ids:
        row_address = table + item_id * stride
        row_offset = row_address - GBA_ROM_BASE
        callback_site = row_offset + callback_offset
        if row_offset < 0 or row_offset + stride > len(baseline):
            _fail(f"QOL item Bag adapter rowがROM外です: {item_id}")
        if struct.unpack_from("<H", baseline, row_offset + id_offset)[0] != item_id:
            _fail(f"QOL item Bag adapter row ID不一致: {item_id}")
        pocket = baseline[row_offset + pocket_offset]
        item_type = baseline[row_offset + type_offset]
        if pocket != int(contract.get("expected_pocket", -1)) \
                or item_type != expected_type:
            _fail(
                f"QOL item Bag adapter pocket/type不一致: "
                f"item={item_id} pocket={pocket} type={item_type}"
            )
        baseline_callback = struct.unpack_from("<I", baseline, callback_site)[0]
        output_callback = struct.unpack_from("<I", output, callback_site)[0]
        if baseline_callback != expected_callback or output_callback != expected_callback:
            _fail(
                f"QOL item Bag adapter expected callback不一致: "
                f"item={item_id} baseline=0x{baseline_callback:08X} "
                f"output=0x{output_callback:08X}"
            )
        type_site = row_offset + type_offset
        if output[type_site] != expected_type:
            _fail(f"QOL item Bag adapter output type expected値不一致: {item_id}")
        output[type_site] = replacement_type
        struct.pack_into("<I", output, callback_site, replacement)
        declared.append({
            "kind": "byte",
            "name": f"qol_item_bag_party_type_{item_id}",
            "address": GBA_ROM_BASE + type_site,
            "start": type_site,
            "end_exclusive": type_site + 1,
            "expected": expected_type,
            "replacement": replacement_type,
        })
        declared.append({
            "kind": "pointer",
            "name": f"qol_item_bag_adapter_{item_id}",
            "address": GBA_ROM_BASE + callback_site,
            "start": callback_site,
            "end_exclusive": callback_site + 4,
            "expected": expected_callback,
            "replacement": replacement,
        })
        rows.append({
            "item_id": item_id,
            "row_address": row_address,
            "callback_site": GBA_ROM_BASE + callback_site,
            "expected_callback": expected_callback,
            "replacement_callback": replacement,
            "pocket": pocket,
            "expected_type": item_type,
            "replacement_type": replacement_type,
        })
    return {
        "status": "PASS",
        "root_cause": (
            "おうかん2種のfield callbackが汎用service表示へ留まり、かつ"
            "item type 4(Bag内継続)のため、通常BagのgItemUseCBを設定しても"
            "party選択exit callbackへ遷移できなかった"
        ),
        "item_ids": item_ids,
        "row_count": len(rows),
        "rows": rows,
        "replacement_symbol": symbol,
        "replacement_callback": replacement,
        "expected_type": expected_type,
        "replacement_type": replacement_type,
        "probe_symbol": "Stage58QolItemAdapter_Probe",
        "runtime": dict(link_evidence),
        "symbol_sizes": {
            key: int(sizes[key])
            for key in sorted(QOL_ITEM_ADAPTER_REQUIRED_SYMBOLS)
        },
        "service_owner": {
            "dispatch": 0x09378799,
            "service": 17,
            "adapter_direct_bag_mutation": False,
            "new_ram_or_save_owner": False,
        },
    }


def _validate_saveblock_key_rotation_stock_contract(
    output: bytearray,
    baseline: bytes,
    contract: Mapping[str, Any],
    symbols: Mapping[str, int],
    sizes: Mapping[str, int],
    previous_allocation: Mapping[str, Any],
    declared: list[dict[str, Any]],
) -> dict[str, Any]:
    """Stock save-ASLR/key-rotation chainに追加rebindがないことを固定する。"""
    del symbols, sizes, declared
    policy = str(contract.get("policy", ""))
    move_save = int(str(contract.get("move_save_blocks_reset_heap")), 0)
    apply_all_site = int(str(contract.get("apply_all_call_site")), 0)
    apply_all_expected = bytes.fromhex(
        str(contract.get("expected_stock_apply_all_call", ""))
    )
    callback_site = int(str(contract.get("callback_restore_site")), 0)
    callback_expected = bytes.fromhex(
        str(contract.get("expected_early_callback_restore", ""))
    )
    apply_all = int(str(contract.get("original_apply_new_encryption")), 0)
    bag_site = int(str(contract.get("bag_encryption_call_site")), 0)
    bag_expected = bytes.fromhex(
        str(contract.get("expected_bag_encryption_call", ""))
    )
    original_bag = int(str(contract.get("original_bag_encryption")), 0)
    set_bag = int(str(contract.get("set_bag_pockets_pointers")), 0)
    save1_pointer = int(str(contract.get("save_block1_pointer")), 0)
    save2_pointer = int(str(contract.get("save_block2_pointer")), 0)
    bag_pockets = int(str(contract.get("bag_pockets")), 0)
    descriptor_stride = int(contract.get("descriptor_stride", 0))
    descriptor_rows = contract.get("bag_pocket_descriptors", [])
    descriptors = [
        {
            "name": str(row.get("name", "")),
            "save1_offset": int(str(row.get("save1_offset")), 0),
            "capacity": int(row.get("capacity", 0)),
        }
        for row in descriptor_rows
        if isinstance(row, Mapping)
    ]
    veneer_contract = contract.get("veneer", {})
    veneer_address = int(str(veneer_contract.get("address")), 0)
    veneer_size = int(veneer_contract.get("size", 0))
    veneer_alignment = int(veneer_contract.get("alignment", 0))
    veneer_expected = bytes.fromhex(str(veneer_contract.get("expected", "")))
    veneer_reference_count = int(
        veneer_contract.get("reference_count_before", -1)
    )
    if (
        policy != "preserve_stock_no_runtime_rebind"
        or move_save != 0x0804B85D
        or apply_all_site != 0x0804B8FA
        or apply_all_expected != bytes.fromhex("00f02ffa")
        or callback_site != 0x0804B8DE
        or callback_expected != bytes.fromhex("019820610099e160")
        or apply_all != 0x0804BD5D
        or bag_site != 0x0804BD76
        or bag_expected != bytes.fromhex("4df063fd")
        or original_bag != 0x08099841
        or set_bag != 0x0809984D
        or save1_pointer != 0x03005048
        or save2_pointer != 0x0300504C
        or bag_pockets != 0x020397D8
        or descriptor_stride != 8
        or descriptors != [
            {"name": "items", "save1_offset": 0x0310, "capacity": 42},
            {"name": "key_items", "save1_offset": 0x03B8,
             "capacity": 30},
            {"name": "poke_balls", "save1_offset": 0x0430,
             "capacity": 13},
            {"name": "tm_case", "save1_offset": 0x0464,
             "capacity": 58},
            {"name": "berry_pouch", "save1_offset": 0x054C,
             "capacity": 43},
        ]
        or veneer_address != 0x0837BEAC
        or veneer_size != 8
        or veneer_alignment != 4
        or veneer_address % veneer_alignment != 0
        or veneer_expected != b"\xFF" * veneer_size
        or veneer_reference_count != 0
    ):
        _fail("SaveBlock key rotation stock contract不一致")
    if apply_all_expected != _thumb_bl(apply_all_site, apply_all & ~1):
        _fail("SaveBlock stock ApplyAll BL契約不一致")
    if bag_expected != _thumb_bl(bag_site, original_bag & ~1):
        _fail("SaveBlock stock Bag encryption BL契約不一致")
    ranges = (
        ("callback_restore", callback_site, callback_expected),
        ("apply_all", apply_all_site, apply_all_expected),
        ("bag_encryption", bag_site, bag_expected),
        ("unused_veneer", veneer_address, veneer_expected),
    )
    for label, address, expected in ranges:
        offset = address - GBA_ROM_BASE
        if offset < 0 or offset + len(expected) > len(baseline):
            _fail(f"SaveBlock {label} siteがROM外です")
        if baseline[offset:offset + len(expected)] != expected \
                or output[offset:offset + len(expected)] != expected:
            _fail(f"SaveBlock {label} stock byte不一致")
    pointer_references = baseline.count(struct.pack("<I", veneer_address))
    if pointer_references != veneer_reference_count:
        _fail("SaveBlock unused veneer既存pointer参照不一致")
    veneer_offset = veneer_address - GBA_ROM_BASE
    allocation_owners = [
        str(row["name"])
        for row in previous_allocation.get("allocations", [])
        if int(row["start"]) < veneer_offset + veneer_size
        and veneer_offset < int(row["end_exclusive"])
    ]
    if allocation_owners:
        _fail(
            "SaveBlock unused veneerが既存allocationと重複: "
            + ",".join(allocation_owners)
        )
    return {
        "status": "PASS",
        "root_cause": (
            "製品側の追加SetBagPocketsPointersはsave-ASLRのcycle境界を変え、"
            "wisdom_caveの自然Continueを次frameの全体resetへ落とした。QOL側の"
            "残件は検証runnerがfield復帰後にSetBagをhost直呼びしたことが原因で、"
            "直呼びを除くとBottle Cap通常Bagの9境界がstock経路で通る"
        ),
        "policy": policy,
        "move_save_blocks_reset_heap": move_save,
        "callback_restore_site": callback_site,
        "callback_restore_sha256": _sha(callback_expected),
        "apply_all_call_site": apply_all_site,
        "apply_all_call_sha256": _sha(apply_all_expected),
        "bag_encryption_call_site": bag_site,
        "bag_encryption_call_sha256": _sha(bag_expected),
        "set_bag_pockets_pointers": set_bag,
        "save_block1_pointer": save1_pointer,
        "save_block2_pointer": save2_pointer,
        "bag_pockets": bag_pockets,
        "descriptor_stride": descriptor_stride,
        "descriptor_count": len(descriptors),
        "bag_pocket_descriptors": descriptors,
        "original_apply_new_encryption": apply_all,
        "original_bag_encryption": original_bag,
        "stock_callback_restore_preserved": True,
        "stock_apply_all_preserved": True,
        "stock_bag_child_preserved": True,
        "additional_runtime_rebind_count": 0,
        "host_rebind_after_field_return_forbidden": True,
        "veneer": {
            "address": veneer_address,
            "size": veneer_size,
            "sha256": _sha(veneer_expected),
            "preexisting_pointer_reference_count": pointer_references,
            "prior_allocation_overlap_count": len(allocation_owners),
            "remains_unallocated": True,
        },
        "call_order": [
            "SetSaveBlocksPointersOwnsBagRebind",
            "RestoreSaveBlockCopies",
            "ApplyNewEncryptionKeyToAllEncryptedData",
            "StoreNewEncryptionKey",
        ],
        "all_stock_encrypted_fields_preserved": True,
        "new_ram_or_save_owner_count": 0,
    }

def _apply_codex_save_layout_repair(
    output: bytearray,
    baseline: bytes,
    contract: Mapping[str, Any],
    symbols: Mapping[str, int],
    sizes: Mapping[str, int],
    declared: list[dict[str, Any]],
) -> dict[str, Any]:
    """Stage44のCFRU想定をVega実SaveBlockの図鑑4鏡へ差し替える。"""
    bitmap_size = int(contract.get("bitmap_size", -1))
    save1 = contract.get("save1", {})
    save2 = contract.get("save2", {})
    legacy = contract.get("legacy_misidentified", {})
    buffers = contract.get("snapshot_buffers", {})
    expected_layout = (
        bitmap_size == 52
        and int(str(save1.get("bag_items_offset")), 0) == 0x310
        and int(str(save1.get("seen_primary_offset")), 0) == 0x5F8
        and int(str(save1.get("seen_secondary_offset")), 0) == 0x3A18
        and int(str(save2.get("owned_offset")), 0) == 0x28
        and int(str(save2.get("seen_offset")), 0) == 0x5C
        and int(str(legacy.get("save1_offset")), 0) == 0x310
        and int(legacy.get("save1_size", -1)) == 150
        and int(str(legacy.get("save2_offset")), 0) == 0x18
        and int(legacy.get("save2_size", -1)) == 16
        and int(str(buffers.get("primary_address")), 0) == 0x0203FDA6
        and int(buffers.get("primary_size", -1)) == 150
        and int(str(buffers.get("spill_address")), 0) == 0x0203FF3C
        and int(buffers.get("spill_size", -1)) == 16
    )
    if not expected_layout:
        _fail("Codex Vega save layout contract不一致")
    storage_capacity = int(buffers["primary_size"]) + int(buffers["spill_size"])
    personality_size = int(save2.get("personality_size", -1))
    if (int(str(save2.get("header_offset")), 0) != 0x18
            or int(save2.get("header_size", -1)) != 16
            or int(str(save2.get("personality_offset")), 0) != 0x1C
            or personality_size != 8):
        _fail("Codex Save2 Pokedex header/personality contract不一致")
    storage_used = 3 * bitmap_size + personality_size
    if storage_used > storage_capacity:
        _fail("Codex seen mirror snapshot既存buffer容量不足")

    symbol_names = {
        "snapshot": "Stage58QolItemAdapter_CodexSnapshotSeenMirrors",
        "restore": "Stage58QolItemAdapter_CodexRestoreSeenMirrors",
        "hash": "Stage58QolItemAdapter_CodexContinueSeenHash",
    }
    configured_symbols = contract.get("symbols", {})
    if configured_symbols != symbol_names:
        _fail("Codex save layout adapter symbol契約不一致")
    for name in symbol_names.values():
        if name not in symbols or int(sizes.get(name, 0)) <= 0:
            _fail(f"Codex save layout adapter symbol不足: {name}")

    patches = contract.get("patches", {})
    patch_spec = (
        ("snapshot_save1", "snapshot", "snapshot_bl"),
        ("snapshot_save2_legacy", None, "legacy_nop"),
        ("restore_save1", "restore", "restore_bl"),
        ("restore_save2_legacy", None, "legacy_nop"),
        ("hash_save1", "hash", "hash_bl"),
        ("hash_save2_legacy", None, "legacy_skip"),
    )
    rows: list[dict[str, Any]] = []
    for key, symbol_key, strategy in patch_spec:
        row = patches.get(key, {})
        site = int(str(row.get("site")), 0)
        size = int(row.get("size", -1))
        try:
            expected = bytes.fromhex(str(row.get("expected", "")))
        except ValueError as exc:
            _fail(f"Codex save layout patch hex不正: {key}: {exc}")
        if size <= 0 or len(expected) != size:
            _fail(f"Codex save layout patch size不一致: {key}")
        offset = site - GBA_ROM_BASE
        if offset < 0 or offset + size > len(baseline):
            _fail(f"Codex save layout patch siteがROM外: {key}")
        if (baseline[offset:offset + size] != expected
                or output[offset:offset + size] != expected):
            _fail(f"Codex save layout expected byte不一致: {key}")
        if strategy == "snapshot_bl":
            target = int(symbols[symbol_names[str(symbol_key)]])
            replacement = (struct.pack("<H", 0x0020)
                           + _thumb_bl(site + 2, target)
                           + struct.pack("<3H", 0x46C0, 0x46C0, 0x46C0))
        elif strategy == "restore_bl":
            target = int(symbols[symbol_names[str(symbol_key)]])
            replacement = (struct.pack("<HH", 0x0007, 0x0028)
                           + _thumb_bl(site + 4, target)
                           + struct.pack("<5H", *([0x46C0] * 5)))
        elif strategy == "hash_bl":
            target = int(symbols[symbol_names[str(symbol_key)]])
            replacement = (struct.pack("<H", 0x0020)
                           + _thumb_bl(site + 2, target)
                           + struct.pack("<H", 0x0004)
                           + struct.pack("<7H", *([0x46C0] * 7)))
        elif strategy == "legacy_nop":
            target = None
            replacement = struct.pack(
                f"<{size // 2}H", *([0x46C0] * (size // 2))
            )
        elif strategy == "legacy_skip":
            target = None
            if size != 18:
                _fail("Codex legacy hash skip span size不一致")
            replacement = struct.pack("<H", 0xE007) + struct.pack(
                "<8H", *([0x46C0] * 8)
            )
        else:
            _fail(f"Codex save layout strategy不明: {strategy}")
        if len(replacement) != size:
            _fail(f"Codex save layout replacement size不一致: {key}")
        output[offset:offset + size] = replacement
        declared.append({
            "kind": "code", "name": f"codex_save_layout_{key}",
            "address": site, "start": offset,
            "end_exclusive": offset + size,
            "expected_sha256": _sha(expected),
            "replacement_sha256": _sha(replacement),
            "target": None if target is None else target | 1,
        })
        rows.append({
            "key": key, "strategy": strategy, "site": site, "size": size,
            "expected": expected.hex(), "replacement": replacement.hex(),
            "target": None if target is None else target | 1,
        })
    spans = sorted((int(row["site"]), int(row["site"]) + int(row["size"]))
                   for row in rows)
    if any(left[1] > right[0] for left, right in zip(spans, spans[1:])):
        _fail("Codex save layout repair patch span重複")
    return {
        "status": "PASS",
        "root_cause": (
            "Stage44 Codex runtimeがCFRU用SaveBlock配置をVegaへ流用し、"
            "SaveBlock1+0x310から150 byteのBag領域とSaveBlock2+0x18から"
            "16 byteを図鑑としてsnapshot/restore/hashしていた"
        ),
        "strategy": "PATCH_SIX_STAGE44_SITES_TO_VEGA_MIRROR_ADAPTERS",
        "bitmap_size": bitmap_size,
        "save1": dict(save1),
        "save2": dict(save2),
        "legacy_misidentified": dict(legacy),
        "snapshot_buffers": {
            **dict(buffers), "capacity": storage_capacity,
            "used": storage_used, "unused": storage_capacity - storage_used,
        },
        "snapshot_restore_mirrors": [
            "save1_seen_primary", "save1_seen_secondary", "save2_seen",
            "save2_unown_spinda_personalities",
        ],
        "hash_mirrors": [
            "save1_seen_primary", "save1_seen_secondary",
            "save2_owned", "save2_seen", "save2_pokedex_header",
        ],
        "owned_bitmap_hash_only_reason": (
            "Codex trainerbattleは捕獲不能でownedを変更しないため、"
            "改変検出には含めるがrestore対象にはしない"
        ),
        "personality_restore_reason": (
            "trainerbattle中の初見Unown/Spinda表示がSave2+0x1C..0x23を"
            "更新するため、seen bitmapと同じ取引snapshotへ8 byteを含める"
        ),
        "patches": rows,
        "patch_count": len(rows),
        "adapter_callsite_count": sum(row[1] is not None for row in patch_spec),
        "symbols": {
            key: int(symbols[value]) | 1 for key, value in symbol_names.items()
        },
        "symbol_sizes": {
            key: int(sizes[value]) for key, value in symbol_names.items()
        },
        "new_ram_or_save_owner_count": 0,
        "existing_public_state_offset_preserved": True,
        "bag_snapshot_restore_removed": True,
    }


def _apply_codex_mailbox_compat(
    output: bytearray,
    baseline: bytes,
    contract: Mapping[str, Any],
    declared: list[dict[str, Any]],
) -> dict[str, Any]:
    """Stage44初期化/検証のcapability定数をStage47公開値へ揃える。"""
    pointer_site = int(str(contract.get("read_keys_pointer_site")), 0)
    expected = int(str(contract.get("expected_delegate")), 0)
    initializer_site = int(str(
        contract.get("stage44_initializer_capability_literal_site")
    ), 0)
    validator_site = int(str(
        contract.get("stage44_validator_capability_literal_site")
    ), 0)
    embedded_config_site = int(str(
        contract.get("stage44_embedded_config_capability_site")
    ), 0)
    base_capabilities = int(str(contract.get("stage44_capabilities")), 0)
    public_capabilities = int(str(contract.get("stage47_capabilities")), 0)
    if (
        pointer_site != 0x080005EC
        or expected != 0x09405D65
        or initializer_site != 0x093C9CEC
        or validator_site != 0x093CA24C
        or embedded_config_site != 0x093C9B90
        or base_capabilities != 0x1FFF
        or public_capabilities != 0x7FFF
    ):
        _fail("Codex mailbox compatibility contract不一致")
    offset = pointer_site - GBA_ROM_BASE
    if offset < 0 or offset + 4 > len(baseline):
        _fail("Codex mailbox compatibility delegateがROM外です")
    if struct.unpack_from("<I", baseline, offset)[0] != expected \
            or struct.unpack_from("<I", output, offset)[0] != expected:
        _fail("Codex mailbox compatibility delegate expected値不一致")
    patches = []
    for name, site in (
        ("codex_mailbox_initializer_capability", initializer_site),
        ("codex_mailbox_validator_capability", validator_site),
    ):
        literal_offset = site - GBA_ROM_BASE
        if literal_offset < 0 or literal_offset + 4 > len(baseline):
            _fail(f"{name}がROM外です")
        before = struct.unpack_from("<I", baseline, literal_offset)[0]
        current = struct.unpack_from("<I", output, literal_offset)[0]
        if before != base_capabilities or current != base_capabilities:
            _fail(f"{name} expected値不一致")
        struct.pack_into("<I", output, literal_offset, public_capabilities)
        row = {
            "kind": "literal_u32",
            "name": name,
            "address": site,
            "start": literal_offset,
            "end_exclusive": literal_offset + 4,
            "expected": base_capabilities,
            "replacement": public_capabilities,
        }
        declared.append(row)
        patches.append(row)
    config_offset = embedded_config_site - GBA_ROM_BASE
    if struct.unpack_from("<I", baseline, config_offset)[0] \
            != base_capabilities \
            or struct.unpack_from("<I", output, config_offset)[0] \
            != base_capabilities:
        _fail("Codex embedded config capabilityの非変更guard不一致")
    return {
        "status": "PASS",
        "root_cause": (
            "Stage47が公開するcatalog/Box14拡張capability 0x7FFFを、"
            "Stage44 Pollが旧0x1FFFとの完全一致で破損と誤判定し、"
            "自然入力で送信済みrequestをmailbox再初期化により消去していた"
        ),
        "pointer_site": pointer_site,
        "expected_delegate": expected,
        "delegate_unchanged": True,
        "patched_literal_count": len(patches),
        "patched_literals": patches,
        "embedded_config_site": embedded_config_site,
        "embedded_config_unchanged": True,
        "stage44_capabilities": base_capabilities,
        "stage47_public_capabilities": public_capabilities,
        "compatibility_strategy": (
            "PATCH_STAGE44_INITIALIZER_AND_VALIDATOR_LITERALS_TO_0x7FFF"
        ),
        "external_capabilities_after_delegate": public_capabilities,
        "post_delegate_crc_and_sequence_republished": False,
        "request_owner_changed": False,
        "mailbox_owner_changed": False,
        "new_ram_or_save_owner_count": 0,
    }


def _apply_codex_result_compat(
    output: bytearray,
    baseline: bytes,
    contract: Mapping[str, Any],
    symbols: Mapping[str, int],
    sizes: Mapping[str, int],
    declared: list[dict[str, Any]],
) -> dict[str, Any]:
    """Codex結果だけをmoney/whiteoutなしの安全なbattle-script tailへ送る。"""
    table = int(str(contract.get("end_turn_function_table")), 0)
    win_expected = int(str(contract.get("inherited_win_adapter")), 0)
    loss_expected = int(str(contract.get("inherited_loss_adapter")), 0)
    draw_expected = int(str(contract.get("inherited_draw_adapter")), 0)
    inherited_return_adapter = int(str(
        contract.get("inherited_return_to_field_adapter")
    ), 0)
    result_script = int(str(contract.get("nonpunitive_result_script")), 0)
    if (
        table != 0x0820CAE8
        or win_expected != 0x093D203D
        or loss_expected != 0x093D2059
        or draw_expected != 0x093D2059
        or inherited_return_adapter != 0x093D1E01
        or result_script != 0x081BC8BB
    ):
        _fail("Codex result compatibility contract不一致")
    replacements = (
        ("win", table + 4, win_expected,
         int(symbols["Stage58QolItemAdapter_CodexBattleWonAdapter"]) | 1),
        ("loss", table + 8, loss_expected,
         int(symbols["Stage58QolItemAdapter_CodexBattleLostAdapter"]) | 1),
        ("draw", table + 12, draw_expected,
         int(symbols["Stage58QolItemAdapter_CodexBattleLostAdapter"]) | 1),
    )
    rows: list[dict[str, Any]] = []
    for kind, site, expected, replacement in replacements:
        offset = site - GBA_ROM_BASE
        _patch_pointer(
            output, baseline, declared, offset, expected, replacement,
            f"codex_nonpunitive_{kind}_adapter",
        )
        rows.append({
            "kind": kind, "site": site, "expected": expected,
            "replacement": replacement,
        })
    return {
        "status": "PASS",
        "root_cause": (
            "Stage45結果adapterがTrainer Tower bitをbattle script開始前に立て、"
            "通常Codex trainerで未初期化のTower名8 byteをEOSなしで展開し、"
            "gDisplayedStringBattleからbattle allocation pointerまで上書きした"
        ),
        "strategy": (
            "CODEX_TRANSACTION_WIN_LOSS_DRAW_CLEAR_TOWER_"
            "OVERRIDE_PICKUP_END2_CONTROLLER_INDEPENDENT_PARTIAL_FAIL_CLOSED"
        ),
        "end_turn_function_table": table,
        "rows": rows,
        "inherited_return_to_field_adapter": inherited_return_adapter,
        "return_to_field_adapter": int(
            symbols["Stage58QolItemAdapter_CodexReturnToFieldAdapter"]
        ) | 1,
        "nonpunitive_result_script": result_script,
        "adapter_symbol_sizes": {
            key: int(sizes[key]) for key in (
                "Stage58QolItemAdapter_CodexBattleWonAdapter",
                "Stage58QolItemAdapter_CodexBattleLostAdapter",
                "Stage58QolItemAdapter_CodexReturnToFieldAdapter",
            )
        },
        "owned_result_kinds": ["win", "loss", "draw"],
        "reward_result_taxonomy": {
            "win": 1, "loss": 2, "draw": 3, "forfeit": 4,
        },
        "controller_disconnect_safe": True,
        "result_guard": (
            "MAGIC_INVERSE_ACTIVE_BOTH_SELECTIONS_FIELD_COMPLETION_PENDING_"
            "TRAINER_OPPONENT_745"
        ),
        "return_guard": "MAGIC_INVERSE_ACTIVE",
        "partial_legacy_hazard_fail_closed": True,
        "partial_legacy_hazard_action": "STOCK_RESULT_WITHOUT_STAGE47_DELEGATE",
        "non_codex_delegates_preserved": True,
        "new_ram_or_save_owner_count": 0,
    }


def _apply_codex_reward_result_kind(
    output: bytearray,
    baseline: bytes,
    contract: Mapping[str, Any],
    symbols: Mapping[str, int],
    sizes: Mapping[str, int],
    declared: list[dict[str, Any]],
) -> dict[str, Any]:
    """Stage47 reward opener内のdraw/forfeit逆転を永続化前に正す。"""
    site = int(str(contract.get("mapping_patch_site")), 0)
    size = int(contract.get("mapping_patch_size", -1))
    expected = bytes.fromhex(str(contract.get("expected", "")))
    inherited = int(str(contract.get("inherited_after_battle_adapter")), 0)
    symbol = "Stage58QolItemAdapter_CodexRewardResultKind"
    target = int(symbols.get(symbol, -1))
    target_size = int(sizes.get(symbol, -1))
    if (
        site != 0x093D20B8
        or size != 24
        or len(expected) != size
        or inherited != 0x093D2075
        or target_size <= 0
    ):
        _fail("Codex reward result-kind contract不一致")
    offset = site - GBA_ROM_BASE
    if (
        baseline[offset:offset + size] != expected
        or output[offset:offset + size] != expected
    ):
        _fail("Codex reward result-kind inherited mapping byte不一致")
    replacement = _thumb_bl(site, target)
    # strb r0,[r5,#22] then nine ARMv4T NOPs.  The inherited function keeps
    # owner_finalize/persist_sector immediately after this replaced span.
    replacement += struct.pack("<H", 0x75A8) + b"\xC0\x46" * 9
    if len(replacement) != size:
        _fail("Codex reward result-kind replacement size不一致")
    output[offset:offset + size] = replacement
    declared.append({
        "kind": "code", "name": "codex_reward_result_kind_mapping",
        "address": site, "start": offset, "end_exclusive": offset + size,
        "expected_sha256": _sha(expected),
        "replacement_sha256": _sha(replacement),
        "target": target | 1,
    })
    return {
        "status": "PASS",
        "inherited_after_battle_adapter": inherited,
        "mapping_patch_site": site,
        "mapping_patch_size": size,
        "mapping_function": target | 1,
        "mapping_function_size": target_size,
        "expected_sha256": _sha(expected),
        "replacement_sha256": _sha(replacement),
        "taxonomy": {"win": 1, "loss": 2, "draw": 3, "forfeit": 4},
        "finalized_and_persisted_by_inherited_owner_after_mapping": True,
        "new_ram_or_save_owner_count": 0,
    }


def _validate_content_balance(
    config: Mapping[str, Any],
    item_by_id: Mapping[int, Mapping[str, str]],
) -> dict[str, Any]:
    rates = {str(key): int(value)
             for key, value in config.get("wild_rates", {}).items()}
    rate_policy = config.get("wild_rate_policy", {})
    if set(rates) != set(rate_policy):
        _fail("wild rate policy method集合不一致")
    rate_rows: list[dict[str, Any]] = []
    for method in sorted(rates):
        limits = rate_policy[method]
        minimum, maximum = int(limits["min"]), int(limits["max"])
        rate = rates[method]
        if minimum < 1 or maximum > 100 or minimum > rate or rate > maximum:
            _fail(f"wild rateが許容帯外です: {method}={rate} ({minimum}..{maximum})")
        rate_rows.append({
            "method": method, "rate": rate,
            "min": minimum, "max": maximum, "status": "PASS",
        })

    value_policy = config.get("thin_reward_value_policy", {})
    expected_tiers = {
        "EARLY_CONSUMABLE", "MID_EXPLORATION",
        "LATE_EXPLORATION", "POSTGAME_RARE",
    }
    if set(value_policy) != expected_tiers:
        _fail("thin reward value tier集合不一致")
    reward_rows: list[dict[str, Any]] = []
    for row in config.get("thin_events", []):
        item_id = int(row["item_id"])
        item = item_by_id[item_id]
        quantity = int(row["quantity"])
        unit_value = int(item["price"] or 0)
        total_value = unit_value * quantity
        tier = str(row["reward_tier"])
        limits = value_policy.get(tier, {})
        minimum, maximum = int(limits.get("min", -1)), int(limits.get("max", -1))
        if (item.get("importance") != "0" or minimum < 0
                or not minimum <= total_value <= maximum):
            _fail(
                f"thin reward valueがtier許容帯外です: {row.get('key')} "
                f"{tier}={total_value} ({minimum}..{maximum})"
            )
        reward_rows.append({
            "key": str(row["key"]), "tier": tier, "item_id": item_id,
            "item_name": str(item.get("display_name", "")),
            "quantity": quantity, "unit_value": unit_value,
            "total_value": total_value, "min": minimum, "max": maximum,
            "status": "PASS",
        })

    mart_ids = [int(value) for value in config["codex_hub"]["mart_item_ids"]]
    mart_rows = [item_by_id[value] for value in mart_ids]
    mart_prices = [int(row["price"] or 0) for row in mart_rows]
    pocket_counts = Counter(str(row["pocket"]) for row in mart_rows)
    if (len(mart_ids) != len(set(mart_ids)) or not mart_prices
            or min(mart_prices) > 600 or max(mart_prices) > 10000
            or any(row.get("importance") != "0" for row in mart_rows)
            or pocket_counts["POCKET_POKE_BALLS"] < 2
            or pocket_counts["POCKET_ITEMS"] < 5):
        _fail("Codex通常martの品揃えbalance contract不一致")
    return {
        "status": "PASS",
        "wild_rates": rate_rows,
        "thin_rewards": reward_rows,
        "mart": {
            "status": "PASS", "item_count": len(mart_ids),
            "duplicate_count": len(mart_ids) - len(set(mart_ids)),
            "price_min": min(mart_prices), "price_max": max(mart_prices),
            "pocket_counts": dict(sorted(pocket_counts.items())),
            "important_item_count": sum(
                row.get("importance") != "0" for row in mart_rows
            ),
        },
    }


def _change_audit(before: bytes, after: bytes,
                  declared: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    spans = sorted((int(row["start"]), int(row["end_exclusive"]), str(row["name"]))
                   for row in declared)
    overlap = [(left, right) for left, right in zip(spans, spans[1:])
               if left[1] > right[0]]
    if overlap:
        _fail(f"declared span overlap: {overlap[:2]}")
    changed = 0
    outside: list[int] = []
    cursor = 0
    for index, (old, new) in enumerate(zip(before, after, strict=True)):
        if old == new:
            continue
        changed += 1
        while cursor < len(spans) and index >= spans[cursor][1]:
            cursor += 1
        if cursor >= len(spans) or index < spans[cursor][0]:
            outside.append(index)
            if len(outside) >= 8:
                break
    if outside:
        _fail("宣言外ROM変更: " + ", ".join(hex(value) for value in outside))
    return {
        "status": "PASS", "changed_byte_count": changed,
        "declared_span_count": len(spans), "overlap_count": 0,
        "outside_declared_span_count": 0,
        "declared_spans": [
            {"start": start, "end_exclusive": end, "name": name}
            for start, end, name in spans
        ],
    }


def _apply_economy_patches(
    output: bytearray,
    baseline: bytes,
    report: Mapping[str, Any],
    declared: list[dict[str, Any]],
) -> dict[str, Any]:
    expected_output = apply_economy_patch_plan(baseline, report)
    rows = list(report["patch_plan"]["rows"])
    for row in rows:
        address = int(str(row["address"]), 0)
        start = address - GBA_ROM_BASE
        expected = bytes.fromhex(str(row["expected_hex"]))
        replacement = bytes.fromhex(str(row["replacement_hex"]))
        end = start + len(expected)
        if len(expected) != len(replacement) or baseline[start:end] != expected \
                or expected_output[start:end] != replacement \
                or output[start:end] != expected:
            _fail(f"economy patch expected/replacement不一致: {row['key']}")
        output[start:end] = replacement
        declared.append({
            "kind": "economy_patch", "name": str(row["key"]),
            "priority": str(row["priority"]), "address": address,
            "start": start, "end_exclusive": end,
            "expected_hex": expected.hex(),
            "replacement_hex": replacement.hex(),
        })
    changed = sum(
        sum(left != right for left, right in zip(
            bytes.fromhex(str(row["expected_hex"])),
            bytes.fromhex(str(row["replacement_hex"])), strict=True,
        ))
        for row in rows
    )
    categories = {
        "collection_qol_owner_rows": sum(
            str(row["key"]).startswith("COLLECTION_QOL_OWNER_") for row in rows
        ),
        "collection_research_price_rows": sum(
            str(row["key"]).startswith("COLLECTION_RESEARCH_PRICE_")
            for row in rows
        ),
        "honey_arbitrage_rows": sum(
            row["key"] == "COLLECTION_HONEY_MONEY_ARBITRAGE" for row in rows
        ),
        "low_raid_unlock_rows": sum(
            row["key"] == "LOW_RAID_EXP_CANDY_XS_UNLOCK" for row in rows
        ),
        "ability_patch_reacquisition_rows": sum(
            row["key"] == "QOL_ABILITY_PATCH_REACQUISITION" for row in rows
        ),
    }
    if categories != {
        "collection_qol_owner_rows": 47,
        "collection_research_price_rows": 71,
        "honey_arbitrage_rows": 1,
        "low_raid_unlock_rows": 1,
        "ability_patch_reacquisition_rows": 1,
    }:
        _fail(f"Stage58 economy patch category drift: {categories}")
    return {
        "status": "PASS", "patch_count": len(rows),
        "p0_patch_count": sum(row["priority"] == "P0" for row in rows),
        "p1_patch_count": sum(row["priority"] == "P1" for row in rows),
        "changed_byte_count": changed,
        "categories": categories,
    }


def _economy_post_contract(report: Mapping[str, Any]) -> dict[str, Any]:
    plan = report["patch_plan"]
    economy = report["economy"]
    raid = report["raid_rewards"]
    if plan["pending_count"] != 0 or plan["applied_count"] != plan["count"]:
        _fail("Stage58 economy patchが全件APPLIEDではありません")
    required = (
        economy["money_buy_sell_arbitrage_count"] == 0,
        economy["collection_qol_bp_duplicate_count"] == 0,
        economy["collection_research_money_per_point_ceiling"] <= 125,
        economy["collection_research_daily_money_conversion_max"] <= 14500,
        raid["pre_unlock_leak_count"] == 0,
    )
    if not all(required):
        _fail("Stage58 economy post-contractに残件があります")
    return {
        "status": "PASS",
        "patch_count": int(plan["count"]),
        "money_arbitrage_count": 0,
        "qol_bp_duplicate_owner_count": 0,
        "research_money_per_point_ceiling":
            economy["collection_research_money_per_point_ceiling"],
        "research_daily_money_conversion_max":
            economy["collection_research_daily_money_conversion_max"],
        "raid_pre_unlock_leak_count": 0,
        "effect_item_count": int(report["qol_effect_items"]["count"]),
        "effect_runtime_baseline_status": report["status"],
    }


def _mgba_evidence(path: Path, rom_sha256: str) -> dict[str, Any]:
    if not path.is_file():
        return {"status": "PENDING", "path": str(path.relative_to(ROOT)),
                "process_runs": 0}
    raw = path.read_bytes()
    document = json.loads(raw)
    if (document.get("schema_version"), document.get("task"), document.get("stage"),
            document.get("status"), document.get("rom_sha256")) \
            != (1, TASK, STAGE, "PASS", rom_sha256):
        _fail("Stage58 mGBA evidence identity/status不一致")
    expected_contract = stage58_validation_contract(ROOT / STAGE58_MGBA_CASES)
    if document.get("validation_contract") != expected_contract:
        _fail("Stage58 mGBA evidenceのcases/runner検証契約hash不一致")
    expected_domains = {
        "static", "story", "menu", "route505", "species",
        "collection", "world", "qol_items", "economy", "convenience",
    }
    domains = document.get("domains")
    if not isinstance(domains, dict) or set(domains) != expected_domains \
            or set(document.get("selected_domains", [])) != expected_domains \
            or document.get("profile") != "all" \
            or document.get("full_coverage") is not True \
            or document.get("collection_mode") != "full" \
            or document.get("domain_count") != 10 \
            or document.get("inherited_domain_count") != 7:
        _fail("Stage58 mGBA full domain inventory不一致")
    if domains.get("collection", {}).get("mode") != "full":
        _fail("Stage58 Collection mGBA evidenceがfullではありません")
    if document.get("warnings") != 0 \
            or document.get("dynamic_process_runs") != 22:
        _fail("Stage58 mGBA coverage不足")
    for name, domain in domains.items():
        expected_runs = 4 if name in {"qol_items", "economy", "convenience"} else 2
        if domain.get("status") != "PASS" \
                or domain.get("identical_results") is not True \
                or domain.get("process_runs") != expected_runs:
            _fail(f"Stage58 mGBA domain反復契約不一致: {name}")

    for name in ("qol_items", "economy", "convenience"):
        result = domains[name].get("result")
        if not isinstance(result, dict) or set(result) != {"phase1", "reload"}:
            _fail(f"Stage58 mGBA two-phase証跡不一致: {name}")
        for phase in ("phase1", "reload"):
            phase_result = result[phase]
            if (phase_result.get("schema_version"), phase_result.get("task"),
                    phase_result.get("stage"), phase_result.get("phase"),
                    phase_result.get("status"),
                    phase_result.get("rom_sha256")) \
                    != (1, TASK, STAGE, phase, "PASS", rom_sha256) \
                    or not phase_result.get("tests") \
                    or not all(phase_result["tests"].values()):
                _fail(f"Stage58 mGBA phase identity/test不一致: {name}/{phase}")

    item_domain = domains["qol_items"]
    item_phase = item_domain["result"]["phase1"]
    item_reload = item_domain["result"]["reload"]
    if item_domain.get("effect_item_count") != 36 \
            or item_phase.get("coverage", {}).get("effect_items") != 36 \
            or any(int(item_phase.get("counts", {}).get(key, -1)) != 36
                   for key in ("cancelled", "successful", "effectless")) \
            or any(int(item_reload.get("counts", {}).get(key, -1)) != 36
                   for key in ("reload_records", "reload_bags")):
        _fail("Stage58 QOL item 36品効果/永続化coverage不足")

    economy_phase = domains["economy"]["result"]["phase1"]
    economy_reload = domains["economy"]["result"]["reload"]
    if (domains["economy"].get("transaction_cases"),
            domains["economy"].get("economy_test_cases")) != (5, 14):
        _fail("Stage58 economy transaction/test case count不一致")
    required_economy = {
        "normal_menu_cancel_no_mutation", "bag_full_no_debit",
        "insufficient_no_mutation", "cross_store_fault_rollback",
        "limited_repeatable_reopen",
        "currency_owner_api_integration_boundary",
        "low_raid_xs_unlock_runtime",
        "collection_qol_owner_47_runtime",
        "honey_buy_sell_no_profit_runtime",
        "research_rate_71_runtime",
        "normal_trainer_victory_prize_honey_normal_save_phase1",
        "factory_prepare_real_battles_bp_patch_normal_save_phase1",
    }
    if set(economy_phase["tests"]) != required_economy \
            or set(economy_reload["tests"]) \
                != {"fresh_process_trainer_prize_honey_reload",
                    "fresh_process_factory_reward_ability_patch_reload"} \
            or (economy_phase.get("ability_patch", {}).get("catalog_index"),
                economy_phase.get("ability_patch", {}).get("item_id"),
                economy_phase.get("ability_patch", {}).get("price_bp"),
                economy_phase.get("ability_patch", {}).get("bag_capacity"),
                economy_phase.get("ability_patch", {}).get(
                    "bag_capacity_observed_phase1"),
                economy_reload.get("ability_patch", {}).get(
                    "bag_capacity_observed_phase1")) \
                != (35, 943, 64, 999, 999, 0):
        _fail("Stage58 economy transaction coverage不足")
    phase1_economy_boundaries = {
        "normal_trainer_victory_to_prize_honey_normal_save": True,
        "factory_prepare_to_real_battle_to_bp_reward": True,
        "factory_reward_to_patch_normal_save": True,
        "fresh_process_earned_purchases_reload": False,
        "factory_physical_npc_and_selection_ui": False,
        "factory_unmodified_battle_fixture": False,
        "low_raid_field_battle": False,
        "honey_sell_ui": False,
        "synthetic_currency_owner_api_is_actual_earn": False,
    }
    reload_economy_boundaries = {
        **phase1_economy_boundaries,
        "normal_trainer_victory_to_prize_honey_normal_save": False,
        "factory_prepare_to_real_battle_to_bp_reward": False,
        "factory_reward_to_patch_normal_save": False,
        "fresh_process_earned_purchases_reload": True,
    }
    if economy_phase.get("e2e_boundaries") != phase1_economy_boundaries \
            or economy_reload.get("e2e_boundaries") \
                != reload_economy_boundaries \
            or economy_phase.get("completion_claim") \
                != "ACTUAL_TRAINER_AND_FACTORY_EARN_PURCHASE_NORMAL_SAVE" \
            or economy_reload.get("completion_claim") \
                != "ACTUAL_TRAINER_AND_FACTORY_EARN_PURCHASE_NORMAL_SAVE_FRESH_PROCESS_RELOAD":
        _fail("Stage58 economy実獲得証明境界不一致")
    trainer_evidence = economy_phase.get("trainer_evidence", {})
    factory_evidence = economy_phase.get("factory_evidence", {})
    reload_evidence = economy_reload.get("reload_evidence", {})
    phase_counts = economy_phase.get("evidence_counts", {})
    reload_counts = economy_reload.get("evidence_counts", {})
    if (trainer_evidence.get("observed_in_phase1"),
            trainer_evidence.get("trainer_id"),
            trainer_evidence.get("script"),
            trainer_evidence.get("money_before"),
            trainer_evidence.get("money_after"),
            trainer_evidence.get("prize_delta"),
            trainer_evidence.get("money_after_honey"),
            trainer_evidence.get("outcome"),
            trainer_evidence.get("enemy_fainted"),
            trainer_evidence.get("runtime_cleaned")) \
            != (True, 89, "0x09376713", 3000, 3128, 128, 2228,
                1, True, True) \
            or (factory_evidence.get("observed_in_phase1"),
                factory_evidence.get("outcomes"),
                factory_evidence.get("payload_starts"),
                factory_evidence.get("bp_before"),
                factory_evidence.get("bp_after_reward"),
                factory_evidence.get("bp_delta"),
                factory_evidence.get("bp_after_purchase"),
                factory_evidence.get("purchase_raw_result"),
                factory_evidence.get("purchase_special_result")) \
            != (True, [1, 1, 1], 3, 55, 64, 9, 0, 0, 0) \
            or (reload_evidence.get("observed_in_fresh_process"),
                reload_evidence.get("money"), reload_evidence.get("honey"),
                reload_evidence.get("bp"),
                reload_evidence.get("ability_patch")) \
            != (True, 2228, 1, 0, 1) \
            or (phase_counts.get("phase1_transaction_boundaries_contract"),
                phase_counts.get("transaction_boundaries_observed_this_phase"),
                phase_counts.get("collection_owner_rows"),
                phase_counts.get("research_reprice_rows")) != (5, 5, 47, 71) \
            or reload_counts.get(
                "transaction_boundaries_observed_this_phase") != 0:
        _fail("Stage58 economy実賞金/Factory BP/再読込coverage不足")
    save_hashes: list[int] = []
    for owner, evidence in (
        ("trainer", trainer_evidence), ("factory", factory_evidence),
    ):
        encoded_hash = evidence.get("normal_save_hash")
        if not isinstance(encoded_hash, str) \
                or re.fullmatch(r"0x[0-9a-f]{16}", encoded_hash) is None:
            _fail(f"Stage58 economy {owner} normal save hash形式不正")
        try:
            save_hash = int(encoded_hash, 16)
        except (KeyError, TypeError, ValueError):
            _fail(f"Stage58 economy {owner} normal save hash証跡不正")
        if save_hash == 0:
            _fail(f"Stage58 economy {owner} normal save hashがゼロです")
        save_hashes.append(save_hash)
    if len(set(save_hashes)) != 2:
        _fail("Stage58 economy trainer/Factory normal save hashが未遷移です")
    routes = economy_phase.get("test_routes", {})
    if routes.get("normal_trainer_fixture_scope") \
            != "AUTHORED_TRAINER89_SCRIPT_COPY_AND_ENEMY_HP1_NO_OUTCOME_OR_PRIZE_WRITE" \
            or routes.get("factory_fixture_scope") \
            != "HOST_SELECTED_ORDER_HP_MAXHP_SPEED_MOVE_PP_ACTION_AND_MOVE_CURSORS_NO_OUTCOME_OR_REWARD_WRITE":
        _fail("Stage58 economy deterministic fixture scope証跡不一致")

    convenience_phase = domains["convenience"]["result"]["phase1"]
    convenience_reload = domains["convenience"]["result"]["reload"]
    required_convenience_phase = {
        "hub_exact_graph", "thin_events_exact_graph", "wild_exact_slots",
        "codex_result_win_loss_draw_table_exact",
        "kanto_wild_runtime_land_rate_species_level_field_return",
        "kanto_wild_runtime_water_rate_species_level_field_return",
        "kanto_wild_runtime_rock_rate_species_level_field_return",
        "kanto_wild_runtime_fishing_rate_species_level_field_return",
        "kanto_wild_fishing_old_good_super_rng_boundaries",
        "thin_events_initial_pickup", "thin_events_repeat_no_duplicate",
        "thin_events_blockdata_walkable_non_event_adjacent",
        "thin_events_bag_full_retry_all_6",
        "thin_events_native_flag_neighbor_bits_stable",
        "thin_events_quest_log_normal_save_recorded",
        "thin_events_quest_log_reload_next_input_flag_stable",
        "thin_events_quantities_preserved_across_normal_saves",
        "pc_object_storage_callback_field_return",
        "pc_normal_ui_deposit",
        "healer_object_hp_pp_status", "healer_zero_party_field_return",
        "healer_egg_hp_pp_status", "healer_fainted_hp_pp_status",
        "healer_normal_hp_pp_status",
        "mart_object_open_navigate_cancel_unchanged", "mart_money_purchase",
        "mart_bag_full_no_charge", "mart_normal_ui_sell_ball",
        "mart_normal_ui_sell_item",
        "codex_npc_normal_a_battle_start_finish_field_return",
        "codex_reward_closed_open_closed",
        "codex_transaction_request_owned",
        "codex_natural_readkeys_all_11_requests",
        "codex_forfeit_result_kind_4",
        "codex_disconnect_cpu_controller_uninstalled",
        "codex_disconnect_cpu_win_result_kind_1",
        "codex_cpu_win_thin_quantities_preserved",
        "codex_forfeit_thin_quantities_preserved",
        "codex_cpu_win_save_layout_restored",
        "codex_forfeit_save_layout_restored",
        "codex_disconnect_cpu_normal_input_field_reward_return",
        "codex_external_capabilities_7fff_preserved",
        "codex_request_window_not_cleared",
        "thin_codex_owner_hash_unchanged",
        "hub_codex_boundaries_valid", "save_after_normal_ui_mutation",
    }
    required_convenience_reload = {
        "hub_exact_graph", "thin_events_exact_graph", "wild_exact_slots",
        "codex_result_win_loss_draw_table_exact",
        "pc_normal_ui_deposit_persisted", "mart_money_purchase_persisted",
        "mart_normal_ui_sales_persisted",
        "codex_post_battle_closed_reset_boundary",
        "codex_external_mailbox_volatile_reset",
        "thin_events_pickups_persisted", "reload_box",
        "reload_party_healed", "reload_field_codex_boundaries",
    }
    phase_coverage = convenience_phase.get("coverage", {})
    reload_coverage = convenience_reload.get("coverage", {})
    if set(convenience_phase["tests"]) != required_convenience_phase \
            or set(convenience_reload["tests"]) \
                != required_convenience_reload \
            or phase_coverage.get("thin_events") != 6 \
            or phase_coverage.get("thin_retry") != 6 \
            or phase_coverage.get("wild_modes") != 4 \
            or phase_coverage.get("wild_runtime_modes") != 4 \
            or phase_coverage.get("fishing_tiers") != 3 \
            or phase_coverage.get("fishing_rng_samples") != 300 \
            or phase_coverage.get("codex_battle_paths") != 2 \
            or phase_coverage.get("codex_result_routes_exact") != 3 \
            or reload_coverage.get("thin_events") != 6 \
            or reload_coverage.get("thin_retry") != 6 \
            or reload_coverage.get("wild_modes") != 4 \
            or reload_coverage.get("codex_result_routes_exact") != 3:
        _fail("Stage58 Codex convenience runtime coverage不足")
    cpu_battle = convenience_phase.get("evidence", {}).get("cpu_battle", {})
    if (
        int(cpu_battle.get("outcome", -1)) != 1
        or int(cpu_battle.get("result_kind", -1)) != 1
    ):
        _fail("Stage58 Codex CPU勝利/result-kind証跡不足")
    save_layout = convenience_phase.get("evidence", {}).get(
        "codex_save_layout", {}
    )
    for owner in ("seen", "personality", "owned"):
        try:
            before = int(str(save_layout[f"{owner}_before"]), 16)
            after_cpu = int(str(save_layout[f"{owner}_after_cpu"]), 16)
            after_forfeit = int(
                str(save_layout[f"{owner}_after_forfeit"]), 16
            )
        except (KeyError, TypeError, ValueError):
            _fail(f"Stage58 Codex {owner} hash証跡不正")
        if before == 0 or (before, after_cpu, after_forfeit) \
                != (before, before, before):
            _fail(f"Stage58 Codex {owner} restore証跡不一致")
    return {
        "status": "PASS", "path": str(path.relative_to(ROOT)), "sha256": _sha(raw),
        "process_runs": int(document["dynamic_process_runs"]),
        "domain_count": 10, "domains": domains, "warnings": 0,
    }


def _verification_resolution(economy_report: Mapping[str, Any],
                             mgba: Mapping[str, Any]) -> dict[str, Any]:
    required = economy_report.get("required_stage58_verification_cases")
    expected_ids = [str(row["id"]) for row in REQUIRED_STAGE58_VERIFICATION_CASES]
    if not isinstance(required, list) \
            or [str(row.get("id")) for row in required] != expected_ids:
        _fail("Stage58 economy必須case ID inventory不一致")
    if mgba.get("status") != "PASS":
        return {
            "status": "PENDING",
            "required_case_count": len(expected_ids),
            "passed_case_count": 0,
            "effect_execution_proven_count": 13,
            "effect_execution_unproven_count": 23,
            "effect_then_fresh_core_reload_proven_count": 0,
            "effect_then_fresh_core_reload_unproven_count": 36,
            "cases": [{"id": case_id, "status": "PENDING"}
                      for case_id in expected_ids],
        }

    domains = mgba["domains"]
    rows: list[dict[str, Any]] = []
    for spec in REQUIRED_STAGE58_VERIFICATION_CASES:
        domain_name = str(spec["domain"])
        domain = domains.get(domain_name, {}).get("result", {})
        locations: list[str] = []
        for test in spec["tests"]:
            matches = [
                phase for phase in ("phase1", "reload")
                if domain.get(phase, {}).get("tests", {}).get(test) is True
            ]
            if len(matches) != 1:
                _fail(f"Stage58必須case証跡不足: {spec['id']}/{test}/{matches}")
            locations.append(f"{domain_name}.{matches[0]}.{test}")
        rows.append({
            "id": str(spec["id"]), "status": "PASS",
            "evidence": locations,
        })
    return {
        "status": "PASS",
        "required_case_count": len(rows),
        "passed_case_count": len(rows),
        "effect_execution_proven_count": 36,
        "effect_execution_unproven_count": 0,
        "effect_then_fresh_core_reload_proven_count": 36,
        "effect_then_fresh_core_reload_unproven_count": 0,
        "cases": rows,
    }


def _markdown(audit: Mapping[str, Any]) -> bytes:
    hub = audit["world"]["hub"]
    wild = audit["world"]["wild"]
    balance = audit["world_balance"]["audit"]
    aggregate_modes = audit["world_balance"]["balance_metrics"]["aggregate"]["modes"]
    progression = audit["world_balance"]["progression_contract"]
    content_balance = audit["content_balance"]
    economy = audit["qol_economy"]
    verification = economy["verification_resolution"]

    def _mode_delta(mode: str) -> str:
        metric = aggregate_modes[mode]
        before = metric["before"]
        after = metric["after"]
        before_levels = f"Lv{before['level_min']}-{before['level_max']}" \
            if before["level_min"] is not None else "Lvなし"
        after_levels = f"Lv{after['level_min']}-{after['level_max']}" \
            if after["level_min"] is not None else "Lvなし"
        return (
            f"- {mode}: table {before['enabled_table_count']}→{after['enabled_table_count']} / "
            f"rate合計 {before['rate_sum']}→{after['rate_sum']} / "
            f"slot {before['slot_count']}→{after['slot_count']} / "
            f"diversity {before['diversity']}→{after['diversity']} / "
            f"{before_levels}→{after_levels}"
        )

    lines = [
        "# Stage58 QOL・世界・利便性・野生バランス報告", "",
        f"- Status: {audit['status']}",
        f"- ROM SHA-256: `{audit['output']['sha256']}`",
        f"- 変更byte数: {audit['change_audit']['changed_byte_count']}", "",
        "## Codex対戦拠点", "",
        "- 受付local 2 / (20,19) / script ownerを保持",
        "- 左隣(19,19): 標準PC端末（正規PC menu→Storage special 60）",
        "- 右隣(21,19): HP・PP・状態異常の全回復看護師",
        "- (23,19): 通常money売買。BP店(22,19)と通貨を混同しない",
        f"- object: {hub['object_count_before']} → {hub['object_count_after']}（上限内）",
        "- Codex勝敗: 未初期化Trainer Tower名を読む旧結果経路を除去し、"
        "win/loss/drawをcontroller切断後も非懲罰tail→field→rewardへ復帰",
        "- 報酬結果ABI: win=1 / loss=2 / draw=3 / forfeit=4。"
        "Stage47のdraw/forfeit逆転をowner CRC・sector31永続化前に修正", "",
        "## 薄い場所の探索イベント", "",
        f"- 定量候補: {audit['world_balance']['audit']['thin_candidate_count']}件",
        f"- 採用: {len(audit['world']['thin_events'])}件（すべて一回限り・bag full時flag保持）",
        "- 採用map: " + ", ".join(
            f"{row['group']}/{row['map']}" for row in audit["world"]["thin_events"]
        ), "",
        f"- reward価値帯: {len(content_balance['thin_rewards'])}件すべてPASS",
        f"- 通常mart: {content_balance['mart']['item_count']}品 / "
        f"{content_balance['mart']['price_min']}～{content_balance['mart']['price_max']}円 / "
        "重要品0", "",
        "## Kanto野生根本修正", "",
        f"- rebuilt headers: {wild['kanto_headers_rebuilt']}（Tohoku {wild['tohoku_headers_preserved']}保持）",
        f"- native mode tables: {json.dumps(wild['mode_tables'], ensure_ascii=False, sort_keys=True)}",
        f"- native slots: {wild['native_slots']}",
        _mode_delta("land"),
        _mode_delta("water"),
        _mode_delta("fishing"),
        _mode_delta("rock"),
        f"- method不適合slot: {balance['method_misplacement_count']}",
        "- weight=0/event/egg/fossil native混入: " + str(sum(
            int(balance[key]) for key in (
                "zero_weight_native_inclusion_count",
                "event_native_inclusion_count", "egg_native_inclusion_count",
                "fossil_native_inclusion_count",
            )
        )),
        "- progression_requirementは監査metadataのみ（serializer/runtime gateへは非適用）",
        f"- runtime map-access owner: {progression['runtime_map_access_owner_physical_count']}/133 "
        f"({progression['runtime_map_access_owner_coverage_status']}); "
        f"metadataより遅い安全側の物理map差分 "
        f"{progression['metadata_runtime_owner_mismatch_count']}件を診断記録 / "
        f"早期露出 {progression['premature_exposure_count']}件", "",
        "## QOL・shop・経済", "",
        f"- exact patch: {economy['patch_application']['patch_count']}件"
        f"（P0 {economy['patch_application']['p0_patch_count']} / "
        f"P1 {economy['patch_application']['p1_patch_count']}）",
        "- patch内訳: Collection QOL owner 47 / Research価格 71 / "
        "Honey・Raid解禁・Ability Patch再取得 各1",
        "- 通常Bag item icon: 旧375行表を参照した3 consumerを999行canonical表へrepoint",
        "- Bag/PC/Berry Pouchの終了icon: 旧専用row 375とbyte同一のcanonical row 589へ3か所を再束縛",
        f"- item icon LZ77 pointer: {audit['qol_item_graphics']['lz77_pointer_count']}件検査 / "
        f"不正 {audit['qol_item_graphics']['invalid_pointer_count']}",
        f"- QOL item ID共通clamp: 0..{audit['qol_item_id_clamp']['valid_max_inclusive']}を保持 / "
        f"{audit['qol_item_id_clamp']['invalid_min_inclusive']}以上は0へ正規化",
        "- おうかん／きんのおうかん: 通常Bagのparty選択adapterから既存service 17へ接続。"
        "item typeもBag内継続4→party対象1へ修正。"
        "取消・無効時は無消費、adapter側に新規RAM/save ownerなし",
        "- SaveBlock移動: security key再暗号化の直前にBag pocket参照を"
        "現SaveBlockへ再束縛。Codex戦を含むmap/battle初期化後も、"
        "薄い場所の報酬数量をfresh-core reloadまで保持",
        "- Codex save復元: 誤ったSaveBlock1+0x310/150 byte（Bag）を廃止し、"
        "Vega実図鑑seen 3鏡各52 byteとUnown/Spinda personality 8 byteを"
        "既存166-byte transaction bufferへ164 byteで格納。owned/headerもhash監視",
        "- Codex mailbox: ReadKeys delegateは変更せず、Stage44の初期化／"
        "検証literalだけをStage47公開capability 0x7FFFへ統一。"
        "自然ReadKeysでrequestを消去せず、追加CRC／RAM ownerなし",
        "- QOL BP重複owner: 47 → 0",
        "- money無限利益cycle: 1 → 0",
        "- 研究通貨換金上限: 1187.5円/RP → 125円/RP",
        "- 116 RP/day最大換金: 134750円 → 14500円",
        "- 解禁前Raid EXP Candy XS漏出: 1 → 0", "",
        "## 実ROMの必須動的証跡", "",
        f"- stable case: {verification['passed_case_count']}/"
        f"{verification['required_case_count']} ({verification['status']})",
        f"- QOL効果実行: {verification['effect_execution_proven_count']}/36、"
        f"未証明 {verification['effect_execution_unproven_count']}",
        f"- 効果後fresh-core reload: "
        f"{verification['effect_then_fresh_core_reload_proven_count']}/36、"
        f"未証明 {verification['effect_then_fresh_core_reload_unproven_count']}", "",
        "## 検証", "",
        f"- Stage57継承quick audit: {audit['inherited_debug']['status']}",
        f"- declared外変更 / overlap: {audit['change_audit']['outside_declared_span_count']} / {audit['change_audit']['overlap_count']}",
        f"- incremental / clean BPS: {audit['bps']['incremental']['round_trip']} / {audit['bps']['clean']['round_trip']}",
        f"- mGBA: {audit['mgba']['status']}",
    ]
    return ("\n".join(lines) + "\n").encode("utf-8")


def _build_static(config_path: Path) -> dict[str, bytes]:
    config = _read_config(config_path)
    inputs = config["inputs"]
    stage57 = _identity(inputs["stage57_rom"], "Stage57 ROM")
    metadata57_raw = _identity(inputs["stage57_metadata"], "Stage57 metadata")
    metadata57 = json.loads(metadata57_raw)
    previous = json.loads(_identity(inputs["stage57_allocation"], "Stage57 allocation"))
    stage17 = json.loads(_identity(inputs["stage17_metadata"], "Stage17 metadata"))
    encounter_raw = _identity(inputs["kanto_encounters"], "Kanto encounters")
    species_raw = _identity(inputs["species_ids"], "Species IDs")
    item_raw = _identity(inputs["item_ids"], "Item IDs")
    flags_raw = _identity(inputs["flags"], "Flags")
    clean = _identity(inputs["clean_rom"], "clean FireRed JPN Rev0")
    if len(stage57) != ROM_SIZE or len(clean) != ROM_SIZE // 2:
        _fail("Stage57/clean ROM size不一致")
    if metadata57.get("output", {}).get("sha256") != _sha(stage57):
        _fail("Stage57 metadata output identity不一致")
    encounter_rows = _csv(encounter_raw, "Kanto encounters")
    species_rows = _csv(species_raw, "Species IDs")
    species_by_key = {row["species_key"]: int(row["id"]) for row in species_rows}
    if len(species_by_key) != len(species_rows):
        _fail("Species key重複")
    # identity pin兼、martの価格/重要品検証で利用する。
    item_rows = _csv(item_raw, "Item IDs")
    item_by_id = {int(row["id"]): row for row in item_rows}
    mart_ids = [int(value) for value in config["codex_hub"]["mart_item_ids"]]
    if any(value not in item_by_id or not int(item_by_id[value]["price"] or 0) > 0
           for value in mart_ids):
        _fail("Codex martに通常価格のないitemがあります")
    flag_rows = _csv(flags_raw, "Flags")
    flags_by_id = {int(row["id"], 0): row for row in flag_rows}
    if len(flags_by_id) != len(flag_rows):
        _fail("Flag ID重複")
    for row in config.get("thin_events", []):
        flag = int(str(row["flag"]), 0)
        item = int(row["item_id"])
        if (flag not in flags_by_id
                or flags_by_id[flag].get("owner") != TASK
                or item not in item_by_id or int(item_by_id[item]["price"] or 0) <= 0
                or int(row["quantity"]) <= 0):
            _fail(f"thin event flag/item正本不一致: {row.get('key')}")
    content_balance = _validate_content_balance(config, item_by_id)

    economy_before = build_qol_economy_audit(ROOT)
    if (economy_before.get("status") != "REPAIR_REQUIRED"
            or economy_before.get("patch_plan", {}).get("count") != 121
            or economy_before.get("patch_plan", {}).get("pending_count") != 121):
        _fail("Stage57 QOL/economy監査の修正前contract不一致")

    plan = build_world_balance_plan(
        ROOT, stage57, stage17, encounter_rows, species_by_key, config["wild_rates"],
    )
    provisional_code, _, _, _ = _compile_qol_item_adapter(0x09E00000)
    provisional, provisional_labels, _ = _build_payload(
        stage57, config, plan, 0, provisional_code,
    )
    adapter_relative = (
        provisional_labels["qol_item_adapter_runtime"] - GBA_ROM_BASE
    )
    allocation, _ = _allocation(previous, len(provisional), "0" * 64)
    payload_offset = int(allocation["start"])
    adapter_load_address = GBA_ROM_BASE + payload_offset + adapter_relative
    adapter_code, adapter_symbols, adapter_sizes, adapter_link = \
        _compile_qol_item_adapter(adapter_load_address)
    if len(adapter_code) != len(provisional_code):
        _fail("QOL item adapterは配置addressによりcode sizeが変化しました")
    payload, labels, world = _build_payload(
        stage57, config, plan, payload_offset, adapter_code,
    )
    if labels["qol_item_adapter_runtime"] != adapter_load_address:
        _fail("QOL item adapter payload label drift")
    collisions = set(labels) & set(adapter_symbols)
    if collisions:
        _fail(f"QOL item adapter symbol label重複: {sorted(collisions)}")
    labels.update({key: int(value) for key, value in adapter_symbols.items()})
    if len(payload) != len(provisional):
        _fail("配置addressによりpayload sizeが変化")
    allocation, allocation_report = _allocation(previous, len(payload), _sha(payload))
    if int(allocation["start"]) != payload_offset:
        _fail("payload hash確定後にallocationが移動")
    payload_end = payload_offset + len(payload)
    if stage57[payload_offset:payload_end] != b"\xFF" * len(payload):
        _fail("Stage58 payload destinationがerased FFではありません")

    output = bytearray(stage57)
    output[payload_offset:payload_end] = payload
    declared: list[dict[str, Any]] = [{
        "kind": "payload", "name": ALLOCATION_NAME,
        "address": GBA_ROM_BASE + payload_offset, "start": payload_offset,
        "end_exclusive": payload_end,
    }]
    economy_application = _apply_economy_patches(
        output, stage57, economy_before, declared,
    )
    item_graphics = _apply_qol_item_graphics_repoints(
        output, stage57, config.get("qol_item_graphics", {}), declared,
    )
    item_id_clamp = _apply_qol_item_id_clamp(
        output, stage57, config.get("qol_item_id_clamp", {}), declared,
    )
    item_bag_adapter = _apply_qol_item_bag_adapter(
        output, stage57, config.get("qol_item_bag_adapter", {}),
        adapter_symbols, adapter_sizes, adapter_link, declared,
    )
    saveblock_key_rotation_stock_contract = \
        _validate_saveblock_key_rotation_stock_contract(
        output, stage57,
        config.get("saveblock_key_rotation_stock_contract", {}),
        adapter_symbols, adapter_sizes, previous, declared,
    )
    codex_save_layout_repair = _apply_codex_save_layout_repair(
        output, stage57, config.get("codex_save_layout_repair", {}),
        adapter_symbols, adapter_sizes, declared,
    )
    codex_mailbox_compat = _apply_codex_mailbox_compat(
        output, stage57, config.get("codex_mailbox_compat", {}), declared,
    )
    codex_result_compat = _apply_codex_result_compat(
        output, stage57, config.get("codex_result_compat", {}),
        adapter_symbols, adapter_sizes, declared,
    )
    codex_reward_result_kind = _apply_codex_reward_result_kind(
        output, stage57, config.get("codex_reward_result_kind", {}),
        adapter_symbols, adapter_sizes, declared,
    )
    _, hub_header = _map_header_offset(stage57, 96, 5)
    old_event = struct.unpack_from("<I", stage57, hub_header + 4)[0]
    _patch_pointer(
        output, stage57, declared, hub_header + 4, old_event,
        labels["codex_hub_events"], "codex_hub_event_header",
    )
    for row in world["thin_events"]:
        offset = int(row["map_header_event_pointer_offset"])
        expected = struct.unpack_from("<I", stage57, offset)[0]
        _patch_pointer(
            output, stage57, declared, offset, expected,
            labels[str(row["event_label"])], f"thin_event_{row['key']}",
        )
    old_wild_root = struct.unpack_from("<I", stage57, WILD_ROOT_POINTER_SITE)[0]
    new_wild_root = labels["wild_headers_root"]
    for site in (WILD_ROOT_POINTER_SITE, *WILD_CONSUMER_SITES):
        _patch_pointer(
            output, stage57, declared, site, old_wild_root, new_wild_root,
            "wild_root" if site == WILD_ROOT_POINTER_SITE else f"wild_consumer_{site:06x}",
        )
    output_raw = bytes(output)
    thin_flag_owner = _thin_flag_owner_audit(
        stage57, output_raw, world["thin_events"], labels,
    )
    economy_after = build_qol_economy_audit(
        ROOT, require_stage57_identity=False, rom_bytes=output_raw,
        hyper_service_item_callback=int(item_bag_adapter["replacement_callback"]),
    )
    economy_post = _economy_post_contract(economy_after)
    change = _change_audit(stage57, output_raw, declared)
    inherited = stage57_quick_audit(output_raw, metadata=None)
    inherited.pop("elapsed_seconds", None)
    output_identity = {
        "path": config["outputs"]["rom"], "size": len(output_raw),
        "sha256": _sha(output_raw),
        "crc32": f"{zlib.crc32(output_raw) & 0xFFFFFFFF:08X}",
    }
    mgba = _mgba_evidence(ROOT / config["outputs"]["mgba"], output_identity["sha256"])
    verification_resolution = _verification_resolution(economy_after, mgba)
    status = "PASS" if verification_resolution["status"] == "PASS" \
        else "PASS_STATIC_MGBA_PENDING"

    incremental = _sparse_bps(stage57, output_raw)
    direct = create_bps(
        clean, output_raw,
        metadata=b"Clean FireRed JPN Rev0 to Stage58 QOL World Convenience Debug",
    )
    if apply_bps(stage57, incremental) != output_raw or apply_bps(clean, direct) != output_raw:
        _fail("Stage58 BPS round-trip不一致")
    bps = {
        "incremental": {
            "path": config["outputs"]["incremental_bps"], "size": len(incremental),
            "sha256": _sha(incremental), "round_trip": True,
        },
        "clean": {
            "path": config["outputs"]["clean_bps"], "size": len(direct),
            "sha256": _sha(direct), "round_trip": True,
        },
    }
    runtime = {
        "payload": {"offset": payload_offset, "address": GBA_ROM_BASE + payload_offset,
                    "size": len(payload), "sha256": _sha(payload)},
        "labels": labels,
        "qol_item_adapter": {
            **adapter_link,
            "symbols": {
                key: int(adapter_symbols[key])
                for key in sorted(QOL_ITEM_ADAPTER_REQUIRED_SYMBOLS)
            },
            "symbol_sizes": {
                key: int(adapter_sizes[key])
                for key in sorted(QOL_ITEM_ADAPTER_REQUIRED_SYMBOLS)
            },
        },
    }
    metadata = {
        "schema_version": 1, "task": TASK, "stage": STAGE, "status": status,
        "input": {"stage57": {"path": inputs["stage57_rom"]["path"],
                               "size": len(stage57), "sha256": _sha(stage57)},
                  "clean": {"path": inputs["clean_rom"]["path"],
                            "size": len(clean), "sha256": _sha(clean)}},
        "output": output_identity, "runtime": runtime, "allocation": allocation,
        "world": world, "world_balance": plan, "change_audit": change,
        "content_balance": content_balance,
        "qol_item_graphics": item_graphics,
        "qol_item_id_clamp": item_id_clamp,
        "qol_item_bag_adapter": item_bag_adapter,
        "saveblock_key_rotation_stock_contract":
            saveblock_key_rotation_stock_contract,
        "codex_save_layout_repair": codex_save_layout_repair,
        "codex_mailbox_compat": codex_mailbox_compat,
        "codex_result_compat": codex_result_compat,
        "codex_reward_result_kind": codex_reward_result_kind,
        "qol_economy": {
            "status": "PASS"
                if verification_resolution["status"] == "PASS"
                else "PASS_PATCHED_RUNTIME_PROOF_PENDING",
            "patch_status": "PASS",
            "runtime_status": verification_resolution["status"],
            "verification_resolution": verification_resolution,
            "patch_application": economy_application,
            "before": {
                "money_arbitrage_count":
                    economy_before["economy"]["money_buy_sell_arbitrage_count"],
                "qol_bp_duplicate_owner_count":
                    economy_before["economy"]["collection_qol_bp_duplicate_count"],
                "research_money_per_point_ceiling":
                    economy_before["economy"]["collection_research_money_per_point_ceiling"],
                "research_daily_money_conversion_max":
                    economy_before["economy"]["collection_research_daily_money_conversion_max"],
                "raid_pre_unlock_leak_count":
                    economy_before["raid_rewards"]["pre_unlock_leak_count"],
            },
            "after": economy_post,
            "audit_path": config["outputs"]["economy_audit"],
        },
        "overlap_audit": {
            "status": "PASS",
            "rom": int(change["outside_declared_span_count"])
                + int(change["overlap_count"]),
            "ram": 0,
            "save": int(thin_flag_owner["baseline_reference_count"])
                + int(thin_flag_owner["unexpected_access_count"]),
            "map": int(plan["audit"]
                       ["thin_candidate_collision_or_event_conflict_count"]),
            "hook": 0,
            "allocator_overlap": int(allocation_report["summaries"]["overlap_count"]),
            "evidence": {
                "rom": {
                    "declared_span_count": len(declared),
                    "changed_byte_count": int(change["changed_byte_count"]),
                    "outside_declared_span_count":
                        int(change["outside_declared_span_count"]),
                    "declared_span_overlap_count": int(change["overlap_count"]),
                },
                "ram": {
                    "new_runtime_ram_owner_count": 0,
                    "basis": (
                        "Stage58 adapterは既存party task dataのみ利用し、"
                        "event/data payloadにも新規mutable RAM/save ownerを持たない"
                    ),
                },
                "save": thin_flag_owner,
                "map": {
                    "event_header_repoint_count": 1 + len(world["thin_events"]),
                    "new_object_count": 3 + len(world["thin_events"]),
                    "collision_or_event_conflict_count": int(
                        plan["audit"]
                        ["thin_candidate_collision_or_event_conflict_count"]
                    ),
                },
                "hook": {
                    "new_executable_hook_count": 5,
                    "qol_item_adapter_callback_repoint_count":
                        int(item_bag_adapter["row_count"]),
                    "saveblock_key_rotation_additional_rebind_count": 0,
                    "saveblock_key_rotation_veneer_count": 0,
                    "codex_save_layout_patch_count":
                        int(codex_save_layout_repair["patch_count"]),
                    "codex_save_layout_adapter_callsite_count":
                        int(codex_save_layout_repair["adapter_callsite_count"]),
                    "codex_mailbox_capability_literal_patch_count":
                        int(codex_mailbox_compat["patched_literal_count"]),
                    "codex_result_adapter_pointer_repoint_count":
                        len(codex_result_compat["rows"]),
                    "wild_root_expected_pointer_repoint_count":
                        1 + len(WILD_CONSUMER_SITES),
                    "item_graphics_expected_pointer_repoint_count":
                        int(item_graphics["repoint_count"]),
                    "expected_byte_guarded": True,
                },
                "allocator": {
                    "overlap_count": int(
                        allocation_report["summaries"]["overlap_count"]
                    ),
                },
            },
        },
        "inherited_debug": inherited, "mgba": mgba, "bps": bps,
    }
    # no-encounter、land、fishing、land+rockの4代表。waterは自然Surf
    # runtimeで別途検証する。Stage58で唯一のrock table (97/82)を静的
    # representativeから落とさず、合計4 mode tableをexact byte照合する。
    representative_coordinates = {(96, 0), (96, 12), (97, 4), (97, 82)}
    representatives = [row for row in plan["headers"]
                       if (int(row["group"]), int(row["map"])) in representative_coordinates]
    if len(representatives) != len(representative_coordinates):
        _fail("wild representative coverage不一致")
    hub = world["hub"]
    additions = {row["kind"]: row for row in hub["additions"]}
    cases = {
        "schema_version": 1, "task": TASK, "stage": STAGE,
        "rom_sha256": output_identity["sha256"],
        "map_groups_root": struct.unpack_from("<I", output_raw, 0x00054B0C)[0],
        "wild_headers_root": new_wild_root,
        "codex_hub": {
            "group": 96, "map": 5, "object_count": hub["object_count_after"],
            "npc": {"local_id": 2, "graphics_id": 62, "x": 20, "y": 19,
                    "script": CODEX_NPC_SCRIPT},
            "pc": {**{key: additions["pc"][key] for key in
                      ("local_id", "graphics_id", "x", "y")},
                   "script": PC_SCRIPT, "entry_special": 0x187,
                   "storage_script": PC_STORAGE_SCRIPT,
                   "special": PC_SPECIAL},
            "healer": {**{key: additions["healer"][key] for key in
                          ("local_id", "graphics_id", "x", "y")},
                       "script": HEAL_SCRIPT, "special": HEAL_SPECIAL},
            "mart": {**{key: additions["mart"][key] for key in
                        ("local_id", "graphics_id", "x", "y")},
                     "script": labels["script_codex_mart"],
                     "items": hub["mart_items"]},
        },
        "wild_representatives": representatives,
        "thin_events": [{
            key: row[key] for key in (
                "key", "group", "map", "local_id", "x", "y", "flag",
                "item_id", "quantity", "object_count_before", "object_count_after",
            )
        } for row in world["thin_events"]],
        "qol": {
            "effect_runner": "mgba_stage58_qol_item_effects_smoke",
            "effect_item_count": 36,
            "normal_bag_ui_family_paths_required": True,
            "cancel_effect_ineligible_reload_required": True,
            "item_graphics": item_graphics,
            "item_bag_adapter": item_bag_adapter,
            "saveblock_key_rotation_stock_contract":
                saveblock_key_rotation_stock_contract,
            "codex_save_layout_repair": codex_save_layout_repair,
        },
        "codex_mailbox_compat": codex_mailbox_compat,
        "codex_result_compat": codex_result_compat,
    }
    audit = {**metadata, "root_causes": {
        "kanto_wild": "Stage17がmethod/weight/event専用区分を無視して全4方式へ循環配置",
        "codex_setup": "対戦受付とBP店にBox・全回復・通常money売買が隣接していなかった",
        "qol_coverage": "購入成功smokeだけでは道具効果/cancel/fault/save reloadを証明しない",
        "qol_bag_icon_table": "通常Bagの3 consumerが追加item未対応の旧画像表を参照していた",
        "qol_bottle_cap_bag_entry": (
            "おうかん2種が通常Bagのparty callbackを設定せず、"
            "既存service 17へ到達できなかった"
        ),
        "saveblock_bag_key_rotation":
            saveblock_key_rotation_stock_contract["root_cause"],
        "codex_vega_save_layout": codex_save_layout_repair["root_cause"],
        "codex_natural_request_loss": codex_mailbox_compat["root_cause"],
        "codex_result_string_overflow": codex_result_compat["root_cause"],
    }}
    outputs = config["outputs"]
    economy_audit = {
        "schema_version": 1, "task": TASK, "stage": STAGE,
        "status": "PASS_PATCHED_RUNTIME_PROOF_PENDING"
            if verification_resolution["status"] != "PASS" else "PASS",
        "rom_sha256": output_identity["sha256"],
        "before": economy_before,
        "after": economy_after,
        "patch_application": economy_application,
        "runtime_evidence": mgba,
        "verification_resolution": verification_resolution,
    }
    return {
        outputs["rom"]: output_raw,
        outputs["metadata"]: _stable(metadata),
        outputs["allocation"]: _stable(allocation_report),
        outputs["incremental_bps"]: incremental,
        outputs["clean_bps"]: direct,
        outputs["payload"]: payload,
        outputs["symbols"]: _stable({
            "schema_version": 1, "task": TASK, "stage": STAGE,
            "runtime": runtime, "wild_consumer_sites": list(WILD_CONSUMER_SITES),
        }),
        outputs["cases"]: _stable(cases),
        outputs["economy_audit"]: _stable(economy_audit),
        outputs["audit"]: _stable(audit),
        outputs["report"]: _markdown(audit),
    }


def _write_outputs(outputs: Mapping[str, bytes]) -> None:
    for relative, raw in outputs.items():
        path = ROOT / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
            stream.write(raw)
            temporary = Path(stream.name)
        os.replace(temporary, path)


def _check_outputs(outputs: Mapping[str, bytes]) -> None:
    drift = [relative for relative, raw in outputs.items()
             if not (ROOT / relative).is_file() or (ROOT / relative).read_bytes() != raw]
    if drift:
        _fail("Stage58生成物drift: " + ", ".join(drift))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("build", "check"))
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument(
        "--require-mgba", action="store_true",
        help="full 10-domain mGBA証跡を必須にし、PENDINGを拒否する",
    )
    args = parser.parse_args()
    try:
        first, second = _build_static(args.config), _build_static(args.config)
        if first != second:
            _fail("Stage58 buildがbyte deterministicではありません")
        config = _read_config(args.config)
        metadata = json.loads(first[config["outputs"]["metadata"]])
        if args.require_mgba and metadata.get("status") != "PASS":
            _fail("Stage58 full mGBA証跡が未確定です")
        if args.mode == "build":
            _write_outputs(first)
        else:
            _check_outputs(first)
    except (OSError, ValueError, KeyError, TypeError, struct.error,
            json.JSONDecodeError, Stage58BuildError) as error:
        print(f"Stage58 QOL/world convenience {args.mode} failed: {error}", file=sys.stderr)
        return 1
    print(
        "Stage58 QOL/world convenience %s: %s sha256=%s crc32=%s artifacts=%d"
        % (args.mode, metadata["status"], metadata["output"]["sha256"],
           metadata["output"]["crc32"], len(first))
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
