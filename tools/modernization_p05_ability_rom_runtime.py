#!/usr/bin/env python3
"""Stage72 Ability 312..317 CFRU-JP thin-hook image builder core."""

from __future__ import annotations

import hashlib
import json
import shutil
import struct
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, NoReturn, Sequence

from tools.regression.rom_runtime import _charmap, _encode_text
from tools.rom_allocator import GBA_ROM_BASE, build_allocation_report_from_csv


SCHEMA_VERSION = 1
TASK = "USER-MODERNIZATION-P05-ABILITY-ROM-RUNTIME-STAGE72"
STAGE = 72
ROM_SIZE = 32 * 1024 * 1024
ABILITY_FIRST = 312
ABILITY_COUNT = 6
DEFAULT_CONFIG = Path("config/modernization_p05_ability_rom_runtime.json")
PROVISIONAL_LOAD_ADDRESS = 0x09500000


class ModernizationP05AbilityRomRuntimeError(ValueError):
    """Stage72 identity、ABI、preimage、allocation、allowlist違反。"""


def _fail(message: str) -> NoReturn:
    raise ModernizationP05AbilityRomRuntimeError(message)


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def stable_json(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def _integer(value: Any, label: str) -> int:
    if isinstance(value, bool):
        _fail(f"{label}がboolです")
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value, 0)
        except ValueError:
            pass
    _fail(f"{label}が整数ではありません: {value!r}")


def _offset(address: int, width: int, label: str) -> int:
    result = address - GBA_ROM_BASE
    if width < 0 or not 0 <= result <= ROM_SIZE - width:
        _fail(f"{label}がROM範囲外です: 0x{address:08X}+{width}")
    return result


def _fixed_raw(root: Path, contract: Mapping[str, Any], label: str) -> bytes:
    relative = contract.get("path")
    expected = contract.get("sha256")
    if not isinstance(relative, str) or not isinstance(expected, str) or len(expected) != 64:
        _fail(f"{label} contractが不正です")
    path = root / relative
    if path.is_symlink() or not path.is_file():
        _fail(f"{label}が通常fileではありません: {path}")
    raw = path.read_bytes()
    if contract.get("size") is not None and len(raw) != _integer(contract["size"], f"{label}.size"):
        _fail(f"{label} size不一致")
    if sha256(raw) != expected:
        _fail(f"{label} SHA-256不一致: {sha256(raw)} != {expected}")
    return raw


def read_config(root: Path, relative: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    path = relative if relative.is_absolute() else root / relative
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        _fail(f"Stage72 configを読めません: {error}")
    if not isinstance(value, dict):
        _fail("Stage72 config rootがobjectではありません")
    if (value.get("schema_version"), value.get("task"), value.get("stage"), value.get("status")) != (
        SCHEMA_VERSION, TASK, STAGE, "STAGE71_IDENTITY_PINNED"
    ):
        _fail("Stage72 schema/task/stage/status不一致")
    abilities = value.get("abilities")
    if not isinstance(abilities, list) or [row.get("id") for row in abilities if isinstance(row, dict)] != list(range(312, 318)):
        _fail("Ability 312..317がstable昇順ではありません")
    if value.get("source_pins", {}).get("ability_storage") != "u16":
        _fail("Ability storageがu16ではありません")
    hooks = value.get("hooks")
    if not isinstance(hooks, list) or len(hooks) != 29:
        _fail("固定hook数が29ではありません")
    occupied: list[tuple[int, int, str]] = []
    for row in hooks:
        if not isinstance(row, dict):
            _fail("hook rowがobjectではありません")
        address = _integer(row.get("address"), "hook.address")
        width = _integer(row.get("width"), "hook.width")
        if width not in (8, 12) or len(bytes.fromhex(str(row.get("parent_hex")))) != width:
            _fail(f"hook width/preimage不一致: {row.get('name')}")
        start = _offset(address, width, f"hook {row.get('name')}")
        occupied.append((start, start + width, str(row.get("name"))))
    for left, right in zip(sorted(occupied), sorted(occupied)[1:]):
        if right[0] < left[1]:
            _fail(f"hook重複: {left[2]} / {right[2]}")
    return value


def _previous_requests(allocation: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows = allocation.get("allocations")
    if not isinstance(rows, list):
        _fail("Stage71 allocation rowsがありません")
    return [{
        "name": row["name"], "region": row["region"], "size": row["size"],
        "alignment": row["alignment"], "start": row["start"], "owner": row["owner"],
        "purpose": row["purpose"], "content_sha256": row["content_sha256"],
    } for row in rows]


def _allocate(
    root: Path,
    config: Mapping[str, Any],
    previous: Mapping[str, Any],
    size: int,
    digest: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    request = config["allocation"]
    requests = _previous_requests(previous)
    requests.append({
        "name": request["name"], "region": request["region"], "size": size,
        "alignment": request["alignment"], "owner": request["owner"],
        "purpose": request["purpose"], "content_sha256": digest,
    })
    report = build_allocation_report_from_csv(root / "config/rom_regions.csv", requests)
    if report["summaries"]["overlap_count"] != 0:
        _fail("allocator overlapを検出しました")
    matches = [row for row in report["allocations"] if row["name"] == request["name"]]
    if len(matches) != 1 or matches[0]["sequence"] != len(rows := previous["allocations"]):
        _fail("Stage72 allocationを末尾に一意解決できません")
    return matches[0], report


def _run(command: Sequence[str], root: Path, label: str) -> str:
    result = subprocess.run(command, cwd=root, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode:
        _fail(f"{label}失敗\n{result.stdout}\n{result.stderr}")
    return result.stdout


@dataclass(frozen=True)
class CompiledPayload:
    code: bytes
    symbols: dict[str, int]
    compiler: str


def compile_payload(root: Path, load_address: int) -> CompiledPayload:
    gcc = shutil.which("arm-none-eabi-gcc")
    objcopy = shutil.which("arm-none-eabi-objcopy")
    nm = shutil.which("arm-none-eabi-nm")
    if not gcc or not objcopy or not nm:
        _fail("arm-none-eabi gcc/objcopy/nmがPATHにありません")
    source_dir = root / "overlays/modernization_p05_ability_rom_runtime"
    c_source = source_dir / "modernization_p05_ability_rom_runtime.c"
    asm_source = source_dir / "modernization_p05_ability_rom_runtime_hooks.S"
    linker = source_dir / "modernization_p05_ability_rom_runtime.ld"
    common = ["-mthumb", "-mcpu=arm7tdmi", "-mthumb-interwork"]
    with tempfile.TemporaryDirectory(prefix="stage72-ability-") as temporary:
        work = Path(temporary)
        c_obj, asm_obj, elf, binary = (work / name for name in ("runtime.o", "hooks.o", "runtime.elf", "runtime.bin"))
        _run([gcc, *common, "-Os", "-std=c11", "-ffreestanding", "-fno-common", "-ffunction-sections", "-fdata-sections", "-Wall", "-Wextra", "-Werror", "-Wconversion", "-Wshadow", "-c", str(c_source), "-o", str(c_obj)], root, "Stage72 C compile")
        _run([gcc, *common, "-c", str(asm_source), "-o", str(asm_obj)], root, "Stage72 hook compile")
        _run([gcc, "-nostdlib", *common, f"-Wl,--defsym=STAGE72_LOAD_ADDRESS=0x{load_address:08X}", f"-Wl,-T,{linker}", str(c_obj), str(asm_obj), "-lgcc", "-o", str(elf)], root, "Stage72 link")
        _run([objcopy, "-O", "binary", str(elf), str(binary)], root, "Stage72 objcopy")
        symbol_text = _run([nm, "-n", str(elf)], root, "Stage72 nm")
        symbols: dict[str, int] = {}
        for line in symbol_text.splitlines():
            fields = line.split()
            if len(fields) == 3 and fields[0] and all(char in "0123456789abcdefABCDEF" for char in fields[0]):
                symbols[fields[2]] = int(fields[0], 16)
        code = binary.read_bytes()
    if not code or len(code) >= 0x10000:
        _fail(f"Stage72 payload code size不正: {len(code)}")
    return CompiledPayload(code=code, symbols=symbols, compiler=_run([gcc, "--version"], root, "gcc version").splitlines()[0])


def _description_blob(root: Path, abilities: Sequence[Mapping[str, Any]]) -> tuple[bytes, list[int]]:
    mapping, tokens = _charmap(root)
    blob = bytearray()
    offsets: list[int] = []
    for row in abilities:
        offsets.append(len(blob))
        encoded = _encode_text(str(row["description_ja"]), mapping, tokens)
        if not encoded or encoded[-1] != 0xFF:
            _fail(f"Ability {row['id']} description EOS不一致")
        blob.extend(encoded)
    return bytes(blob), offsets


def _veneer(width: int, target: int) -> bytes:
    target |= 1
    if width == 8:
        return struct.pack("<HHI", 0x4B00, 0x4718, target)
    if width == 12:
        return struct.pack("<HHHHI", 0x469C, 0x4B01, 0x4718, 0x46C0, target)
    _fail(f"未対応veneer width: {width}")


def _table_slice(parent: bytes, table: Mapping[str, Any], count: int) -> bytes:
    address = _integer(table["address"], "table.address")
    stride = _integer(table["stride"], "table.stride")
    start = _offset(address, count * stride, "ability table")
    return parent[start:start + count * stride]


@dataclass
class BuiltStage72:
    config: dict[str, Any]
    parent: bytes
    rom: bytes
    payload: bytes
    allocation: bytes
    symbols: dict[str, Any]
    metadata: dict[str, Any]
    checkpoint: dict[str, Any]
    surface_matrix: dict[str, Any]
    audit: dict[str, Any]


def build_stage72_image(root: Path, config_path: Path = DEFAULT_CONFIG) -> BuiltStage72:
    config = read_config(root, config_path)
    inputs = config["inputs"]
    parent = _fixed_raw(root, inputs["stage71_rom"], "Stage71 ROM")
    _fixed_raw(root, inputs["stage71_metadata"], "Stage71 metadata")
    previous_allocation_raw = _fixed_raw(root, inputs["stage71_allocation"], "Stage71 allocation")
    _fixed_raw(root, inputs["stage71_mapping"], "Stage71 mapping")
    _fixed_raw(root, inputs["stage71_checkpoint"], "Stage71 checkpoint")
    _fixed_raw(root, inputs["charmap"], "CFRU-JP charmap")
    previous_allocation = json.loads(previous_allocation_raw)
    abilities = config["abilities"]
    descriptions, description_offsets = _description_blob(root, abilities)

    provisional = compile_payload(root, PROVISIONAL_LOAD_ADDRESS)
    provisional_size = len(provisional.code) + len(descriptions)
    allocation, _ = _allocate(root, config, previous_allocation, provisional_size, "0" * 64)
    compiled = compile_payload(root, GBA_ROM_BASE + allocation["start"])
    if len(compiled.code) != len(provisional.code):
        _fail("link addressでcode sizeが変化しました")
    payload = compiled.code + descriptions
    allocation, allocation_report = _allocate(root, config, previous_allocation, len(payload), sha256(payload))
    if GBA_ROM_BASE + allocation["start"] != min(compiled.symbols.values()):
        # The first linked symbol is the fixed entry point at the load address.
        _fail("linked load addressとallocatorが一致しません")

    output = bytearray(parent)
    allowed = bytearray(ROM_SIZE)
    writes: list[dict[str, Any]] = []

    def patch(offset: int, raw: bytes, label: str, expected: bytes | None = None) -> None:
        if expected is not None and parent[offset:offset + len(raw)] != expected:
            _fail(f"{label} parent preimage不一致")
        if any(allowed[offset:offset + len(raw)]):
            _fail(f"{label} allowlist overlap")
        output[offset:offset + len(raw)] = raw
        allowed[offset:offset + len(raw)] = b"\x01" * len(raw)
        writes.append({"label": label, "start": offset, "end_exclusive": offset + len(raw), "size": len(raw), "parent_sha256": sha256(parent[offset:offset + len(raw)]), "output_sha256": sha256(raw)})

    payload_start = int(allocation["start"])
    patch(payload_start, payload, "stage72_payload", parent[payload_start:payload_start + len(payload)])
    hook_rows: list[dict[str, Any]] = []
    for row in config["hooks"]:
        name = str(row["name"])
        target_name = str(row["target"])
        if target_name not in compiled.symbols:
            _fail(f"hook target symbol欠落: {target_name}")
        address, width = _integer(row["address"], "hook.address"), _integer(row["width"], "hook.width")
        start = _offset(address, width, f"hook {name}")
        expected = bytes.fromhex(str(row["parent_hex"]))
        raw = _veneer(width, compiled.symbols[target_name])
        patch(start, raw, f"hook:{name}", expected)
        hook_rows.append({"name": name, "site": f"0x{address:08X}", "width": width, "target": target_name, "target_address": f"0x{(compiled.symbols[target_name] | 1):08X}", "preimage_sha256": sha256(expected), "veneer_hex": raw.hex(), "r3_preserved": width == 12})

    tables = config["ability_tables"]
    count = int(tables["count"])
    for key in ("names", "descriptions", "ratings", "mold_breaker_ignored"):
        raw = _table_slice(parent, tables[key], count)
        if sha256(raw) != tables[key]["parent_sha256"]:
            _fail(f"Ability {key} full 318-row table hash不一致")
    descriptions_table = tables["descriptions"]
    descriptions_start = _offset(_integer(descriptions_table["address"], "descriptions.address") + ABILITY_FIRST * 4, 24, "description rows")
    expected_desc = bytes.fromhex(descriptions_table["new_rows_parent_hex"])
    pointer_rows = b"".join(struct.pack("<I", GBA_ROM_BASE + payload_start + len(compiled.code) + relative) for relative in description_offsets)
    patch(descriptions_start, pointer_rows, "ability_description_pointers_312_317", expected_desc)
    ratings_start = _offset(_integer(tables["ratings"]["address"], "ratings.address") + ABILITY_FIRST, ABILITY_COUNT, "rating rows")
    patch(ratings_start, bytes(int(row["rating"]) & 0xFF for row in abilities), "ability_ratings_312_317", bytes.fromhex(tables["ratings"]["new_rows_parent_hex"]))
    mold_start = _offset(_integer(tables["mold_breaker_ignored"]["address"], "mold.address") + ABILITY_FIRST, ABILITY_COUNT, "mold rows")
    patch(mold_start, bytes(int(row["mold_breaker_ignored"]) for row in abilities), "ability_mold_breaker_ignored_312_317", bytes.fromhex(tables["mold_breaker_ignored"]["new_rows_parent_hex"]))

    binding = config["mega_binding"]
    base_stats = _integer(binding["base_stats_address"], "base_stats_address")
    binding_rows: list[dict[str, Any]] = []
    for row in abilities:
        values = []
        for field in binding["ability_offsets"]:
            start = _offset(base_stats + int(row["mega_species"]) * int(binding["stride"]) + int(field), 2, "mega ability binding")
            values.append(struct.unpack_from("<H", parent, start)[0])
        if values != [row["id"]] * 3:
            _fail(f"Mega species {row['mega_species']} ability binding不一致: {values}")
        binding_rows.append({"ability_id": row["id"], "mega_species": row["mega_species"], "ability_slots": values, "preserved_from_stage71": True})

    output_raw = bytes(output)
    outside = [index for index, (left, right) in enumerate(zip(parent, output_raw)) if left != right and not allowed[index]]
    if outside:
        _fail(f"allowlist外変更を検出: {outside[:8]}")
    changed = [index for index, (left, right) in enumerate(zip(parent, output_raw)) if left != right]
    unchanged_old_tables = {
        key: sha256(_table_slice(output_raw, tables[key], ABILITY_FIRST))
        for key in ("names", "descriptions", "ratings", "mold_breaker_ignored")
    }
    parent_old_tables = {
        key: sha256(_table_slice(parent, tables[key], ABILITY_FIRST))
        for key in unchanged_old_tables
    }
    if unchanged_old_tables != parent_old_tables:
        _fail("Ability 0..311 table prefixが変化しました")

    gaps = [
        "Mega SolのSolar Beam系charge省略時ability popupは、判定関数AttacksThisTurnがAI/utilityからも呼ばれるため副作用なしのまま（実効果は接続済み）",
        "Eelevateの専用AI吸収switch bonusはTypeCalc/CheckMonGrounding認識まで（追加score関数未接続）",
        "Piercing DrillのAI仮想Protectに対する1/4 damage予測は未接続（実戦の単体Protect貫通・1/4・side guard再評価は接続済み）",
        "Spicy Sprayを味方へ能動発火する専用doubles AI利得scoreは未接続（Future Sight元使用者不在時の誤火傷は除外済み）",
        "mGBA実戦闘は最終累積候補でrootが1回のみ実行予定",
    ]
    surface_matrix = {
        "schema_version": 1, "task": TASK, "stage": STAGE,
        "abilities": [
            {"id": 312, "key": "ABILITY_KEY_DRAGONIZE", "connected": ["live_type", "party_type", "damage", "ai_damage", "visual_power", "ion_deluge_overridden", "electrify_priority_retained", "inactive_tera_blast_type_and_power", "active_tera_blast_excluded", "max_move_type_excluded", "z_move_power_excluded", "suppression_by_live_ability"], "status": "STATIC_CONNECTED"},
            {"id": 313, "key": "ABILITY_KEY_EELEVATE", "connected": ["live_grounding", "noninvasive_grounding", "party_grounding", "live_typecalc", "ai_typecalc", "visual_typecalc", "visual_recorded_item_boundary", "damaging_ground_only", "ability_shield_preserves_immunity", "knockout_state29_yield_boundary", "knockout_boost", "future_sight_same_user_and_partner_bank_knockout_boost", "mold_breaker_flag"], "status": "STATIC_CONNECTED_AI_SWITCH_BONUS_GAP"},
            {"id": 314, "key": "ABILITY_KEY_FIREMANE", "connected": ["physical_damage", "special_damage", "ai_damage", "visual_power", "suppression_by_live_ability"], "status": "STATIC_CONNECTED"},
            {"id": 315, "key": "ABILITY_KEY_MEGASOL", "connected": ["fire_water_damage", "weather_ball_live_party", "solar_charge", "weather_heal", "weather_heal_popup_only_when_personal_sun_changes_result", "holder_utility_umbrella_does_not_cancel_personal_sun", "thunder_hurricane_accuracy", "sand_veil_snow_cloak_ignored_for_holder", "growth_plus_two", "partner_flower_gift_not_activated", "visual_power", "no_persistent_field_weather"], "status": "STATIC_CONNECTED_SOLAR_CHARGE_POPUP_GAP"},
            {"id": 316, "key": "ABILITY_KEY_PIERCINGDRILL", "connected": ["single_target_protect_bypass", "real_protected_quarter_damage", "shield_reaction_retained", "max_guard_block", "side_guard_rechecked_and_retained", "spread_moves_excluded", "ai_individual_protect_bypass_prediction", "ohko_no_quarter"], "status": "STATIC_CONNECTED_AI_QUARTER_PREDICTION_GAP"},
            {"id": 317, "key": "ABILITY_KEY_SPICYSPRAY", "connected": ["real_damage_only", "substitute_excluded", "holder_may_faint", "attacker_alive_present", "future_sight_original_user_resolution", "future_sight_off_field_no_trigger", "burn_eligibility", "noncontact"], "status": "STATIC_CONNECTED_FRIENDLY_AI_GAP"},
        ],
        "unconnected_surfaces": gaps,
        "release_candidate": False,
    }
    audit = {
        "schema_version": 1, "task": TASK, "stage": STAGE,
        "parent_sha256": sha256(parent), "output_sha256": sha256(output_raw),
        "payload": {"start": payload_start, "gba_start": f"0x{GBA_ROM_BASE + payload_start:08X}", "size": len(payload), "code_size": len(compiled.code), "description_size": len(descriptions), "sha256": sha256(payload)},
        "writes": writes, "hooks": hook_rows,
        "changed_byte_count": len(changed), "allowed_byte_count": sum(allowed), "outside_allowlist_count": 0,
        "changed_offsets_sha256": sha256(b"".join(struct.pack("<I", value) for value in changed)),
        "ability_0_311_prefixes_unchanged": True,
        "ability_prefix_sha256": unchanged_old_tables,
        "mega_bindings": binding_rows,
        "existing_rom_outside_allowlist_unchanged": True,
    }
    symbols = {
        "schema_version": 1, "load_address": f"0x{GBA_ROM_BASE + payload_start:08X}",
        "compiler": compiled.compiler,
        "symbols": {name: f"0x{(address | 1):08X}" for name, address in sorted(compiled.symbols.items()) if name.startswith("Stage72_")},
    }
    metadata = {
        "schema_version": 1, "task": TASK, "stage": STAGE,
        "status": "CHECKPOINT_STATIC_RUNTIME_CONNECTED_MGBA_AND_DOCUMENTED_AI_UI_EDGES_PENDING",
        "parent": {"path": inputs["stage71_rom"]["path"], "size": len(parent), "sha256": sha256(parent)},
        "output": {"path": config["outputs"]["rom"], "size": len(output_raw), "sha256": sha256(output_raw)},
        "allocation": allocation,
        "allocation_report_sha256": sha256(stable_json(allocation_report)),
        "hooks": hook_rows, "ability_rows": abilities, "mega_bindings": binding_rows,
        "validation": {"compile_link": "PASS", "hook_preimages": "PASS", "r3_preserving_12_byte_veneer": "PASS", "thumb_targets": "PASS", "ability_ids_u16": "PASS", "ability_0_311_unchanged": "PASS", "mega_bindings_312_317": "PASS", "allowlist_outside": 0, "mgba": "NOT_RUN_BY_STAGE72_OWNER"},
        "remaining_work": gaps, "release_candidate": False,
    }
    release_blockers = [
        "MGBA_RUNTIME_NOT_EXECUTED",
        "MEGA_SOL_SOLAR_CHARGE_POPUP_UNCONNECTED",
        "EELEVATE_AI_SWITCH_BONUS_UNCONNECTED",
        "PIERCING_DRILL_AI_QUARTER_PREDICTION_UNCONNECTED",
        "SPICY_SPRAY_FRIENDLY_FIRE_AI_SCORE_UNCONNECTED",
    ]
    metadata["release_blockers"] = release_blockers
    checkpoint = {
        "schema_version": 1, "task": TASK, "stage": STAGE,
        "status": metadata["status"], "parent_sha256": sha256(parent), "output_sha256": sha256(output_raw),
        "payload_sha256": sha256(payload), "allocation_sha256": sha256(stable_json(allocation_report)),
        "hook_count": len(hook_rows), "ability_ids": list(range(312, 318)),
        "static_tests_required": True, "builder_check_required": True,
        "mgba": "DEFERRED_TO_ROOT_FINAL_CUMULATIVE_ONCE",
        "release_blockers": release_blockers, "release_candidate": False,
    }
    return BuiltStage72(config=config, parent=parent, rom=output_raw, payload=payload,
                        allocation=stable_json(allocation_report), symbols=symbols,
                        metadata=metadata, checkpoint=checkpoint,
                        surface_matrix=surface_matrix, audit=audit)
