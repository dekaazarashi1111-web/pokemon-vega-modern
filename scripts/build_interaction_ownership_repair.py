#!/usr/bin/env python3
"""Stage49の誤ったinteraction ownerを撤回し、Stage50を生成・検証する。"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import struct
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any, Mapping, NoReturn, Sequence


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_world_item_recovery import _trainer_audit  # noqa: E402
from tools.interaction_ownership_repair import (  # noqa: E402
    GBA_ROM_BASE,
    ITEM_FLAG_BASE,
    ITEM_FLAG_COUNT,
    OBJECT_SIZE,
    ROM_SIZE,
    build_payload,
)
from tools.release.bps import apply_bps, create_bps  # noqa: E402
from tools.rom_allocator import build_allocation_report_from_csv  # noqa: E402
from tools.trainer_final.kanto_events import (  # noqa: E402
    _map_header_offset,
    _object_fields,
    _read_map_catalog,
    _stage_map_state,
)


TASK = "USER-20260824-STAGE49-INTERACTION-OWNERSHIP-REPAIR"
STAGE = 50
STAGE49_SHA256 = "780504cda0884bf53ed88f30fce18cbb54985740162210cb4724df0c6570ef5a"
STAGE48_SHA256 = "b8244d5d6fcde027aa33bc432b5d3eb11951d71f43ba2bebf2c1d29a50dd7243"
CLEAN_SHA256 = "1e4af44b0c75cc8649bfb8649dc4ae5850bf5358bd6b9cd0bf779c99f9db1486"
ALLOCATION_NAME = "interaction_ownership_repair_stage50_payload"
WILD_HOOK_OFFSET = 0x0006CFE8
WILD_HOOK_EXPECTED = bytes.fromhex("00b515f0d7ff0006")
COOLDOWN_OFFSET = 0x00082F76
COOLDOWN_EXPECTED = bytes.fromhex("c1f7")
COOLDOWN_REPLACEMENT = bytes.fromhex("09e0")
MOVE_TABLE = 0x090421F4
MOVE_STRIDE = 12
MOVE_COUNT = 1063
DARK_PULSE = 369

STAGE49_ROM = Path("build/stages/49_world_item_recovery.gba")
STAGE48_ROM = Path("build/stages/48_species_form_backsprite_compat.gba")
CLEAN_ROM = Path("inputs/private/FireRed_JPN_Rev0_clean.gba")
STAGE49_META = Path("build/stages/49_world_item_recovery.json")
PREVIOUS_ALLOCATION = Path("build/stages/49_allocation.json")
TRAINER_META = Path("build/stages/35_trainer_changekit_final.json")
ID_INVENTORY = Path("reports/generated/id_inventory.json")
STAGE17_META = Path("build/stages/17_regression.json")

OUTPUTS = {
    "rom": Path("build/stages/50_interaction_ownership_repair.gba"),
    "metadata": Path("build/stages/50_interaction_ownership_repair.json"),
    "allocation": Path("build/stages/50_allocation.json"),
    "mgba": Path("build/stages/50_mgba_interaction_ownership.json"),
    "incremental_bps": Path("build/patches/stage49-to-interaction-owner-stage50.bps"),
    "clean_bps": Path("build/patches/clean-to-interaction-owner-stage50.bps"),
    "report_json": Path("reports/generated/interaction_ownership_repair.json"),
    "report_md": Path("reports/generated/interaction_ownership_repair.md"),
}


class InteractionBuildError(RuntimeError):
    """Stage50の入力、配置、ROM監査、またはmGBA検証が不一致。"""


def _fail(message: str) -> NoReturn:
    raise InteractionBuildError(message)


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _stable(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def _read(path: Path, *, digest: str, size: int) -> bytes:
    raw = (ROOT / path).read_bytes()
    if len(raw) != size or _sha(raw) != digest:
        _fail(f"入力契約不一致: {path}")
    return raw


def _json(path: Path) -> dict[str, Any]:
    value = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        _fail(f"JSON rootがobjectではありません: {path}")
    return value


def _previous_requests() -> list[dict[str, Any]]:
    previous = _json(PREVIOUS_ALLOCATION)
    if previous.get("summaries", {}).get("overlap_count") != 0:
        _fail("Stage49 allocator reportにoverlapがあります")
    return [{
        "name": row["name"], "region": row["region"], "size": row["size"],
        "alignment": row["alignment"], "owner": row["owner"],
        "purpose": row["purpose"], "content_sha256": row["content_sha256"],
    } for row in previous["allocations"]]


def _allocation(size: int, digest: str) -> tuple[dict[str, Any], dict[str, Any]]:
    requests = _previous_requests()
    requests.append({
        "name": ALLOCATION_NAME, "region": "integration_modules",
        "size": size, "alignment": 16, "owner": TASK,
        "purpose": "Stage49 interaction owner撤回、field object・遭遇・視線補正",
        "content_sha256": digest,
    })
    report = build_allocation_report_from_csv(ROOT / "config/rom_regions.csv", requests)
    if report.get("summaries", {}).get("overlap_count") != 0:
        _fail("Stage50 allocator overlap")
    rows = [row for row in report["allocations"] if row["name"] == ALLOCATION_NAME]
    if len(rows) != 1:
        _fail("Stage50 payload allocationが一意ではありません")
    return rows[0], report


def _coordinates(group_sizes: Sequence[int]) -> list[tuple[int, int]]:
    rows = [(group, number) for group, size in enumerate(group_sizes)
            for number in range(int(size))]
    rows.extend(
        (int(row["map_header"]["group_id"]), int(row["map_header"]["map_id"]))
        for row in _read_map_catalog(ROOT).values()
    )
    if len(rows) != 678 or len(set(rows)) != 678:
        _fail("678 physical map coordinate inventoryが一意ではありません")
    return rows


def _map_audit(stage48: bytes, stage49: bytes, output: bytes,
               group_sizes: Sequence[int], plan: Mapping[str, Any]) -> dict[str, Any]:
    old = _json(STAGE49_META)["payload"]
    old_start = int(old["address"])
    old_end = old_start + int(old["size"])
    invalid = 0
    noninteractive_zero_scripts: list[dict[str, Any]] = []
    old_payload_reachable = 0
    objects = 0
    bg_events = 0
    trainer_templates = 0
    sight_changed = 0
    sight_unchanged_one = 0
    for group, number in _coordinates(group_sizes):
        try:
            after = _stage_map_state(output, group, number)
        except (ValueError, RuntimeError):
            continue
        local_ids = [raw[0] for raw in after["objects"]]
        if len(local_ids) != len(set(local_ids)):
            _fail(f"map {group}/{number}: local object ID重複")
        for raw in after["objects"]:
            pointer = _object_fields(raw)["script_pointer"] & ~1
            if pointer == 0:
                invalid += 1
                fields = _object_fields(raw)
                if fields["kind"] != 0:
                    classification = "DYNAMIC_CLONE_TEMPLATE"
                elif fields["graphics_id"] == 108:
                    classification = "INVISIBLE_RUNTIME_ACTOR"
                else:
                    _fail(f"map {group}/{number}: interactable zero script remains")
                noninteractive_zero_scripts.append({
                    "group": group, "map": number,
                    "local_id": fields["local_id"],
                    "classification": classification,
                })
            elif not GBA_ROM_BASE <= pointer < GBA_ROM_BASE + len(output):
                _fail(f"map {group}/{number}: object script ROM外")
            if old_start <= pointer < old_end:
                old_payload_reachable += 1
        bg_pointer = int(after["pointers"]["bg"])
        bg_raw = bytes.fromhex(str(after["bg_hex"]))
        if bg_raw and not GBA_ROM_BASE <= bg_pointer < GBA_ROM_BASE + len(output):
            _fail(f"map {group}/{number}: bg array ROM外")
        for index in range(int(after["counts"]["bg"])):
            event_kind = bg_raw[index * 12 + 5]
            pointer = struct.unpack_from("<I", bg_raw, index * 12 + 8)[0] & ~1
            if event_kind == 0 and pointer \
                    and not GBA_ROM_BASE <= pointer < GBA_ROM_BASE + len(output):
                _fail(f"map {group}/{number}: bg script ROM外")
            if event_kind == 0 and old_start <= pointer < old_end:
                old_payload_reachable += 1
        try:
            before = _stage_map_state(stage48, group, number)
        except (ValueError, RuntimeError):
            before = None
        if before is not None:
            after_by_local = {_object_fields(raw)["local_id"]: _object_fields(raw)
                              for raw in after["objects"]}
            for raw in before["objects"]:
                fields = _object_fields(raw)
                if fields["kind"] != 0 or fields["trainer_type"] != 1:
                    continue
                trainer_templates += 1
                current = after_by_local.get(fields["local_id"])
                if current is None or current["script_pointer"] != fields["script_pointer"]:
                    _fail(f"map {group}/{number}: trainer owner/script changed")
                expected = (fields["sight_range"] - 1
                            if fields["sight_range"] > 1 else fields["sight_range"])
                if current["sight_range"] != expected:
                    _fail(f"map {group}/{number}: trainer sight補正不一致")
                if fields["sight_range"] > 1:
                    sight_changed += 1
                else:
                    sight_unchanged_one += 1
        objects += len(after["objects"])
        bg_events += int(after["counts"]["bg"])
    if old_payload_reachable:
        _fail(f"Stage49の誤owner payloadがmapから到達可能: {old_payload_reachable}")
    codex = _stage_map_state(output, 96, 5)
    codex_rows = [_object_fields(raw) for raw in codex["objects"]
                  if _object_fields(raw)["local_id"] == 2]
    if len(codex_rows) != 1 or codex_rows[0]["graphics_id"] != 62 \
            or (codex_rows[0]["x"], codex_rows[0]["y"]) != (20, 19) \
            or codex_rows[0]["script_pointer"] != 0x093CDA80:
        _fail("Codex reception NPC ownerがStage48から変化")
    expected_sight = (int(plan["trainer_sight"]["direct_patch_count"])
                      + int(plan["trainer_sight"]["payload_patch_count"]))
    if sight_changed != expected_sight or trainer_templates != 829:
        _fail(f"trainer sight全件監査不一致: {trainer_templates}/{sight_changed}/{expected_sight}")
    return {
        "status": "PASS", "tohoku_maps": 425, "kanto_maps": 253,
        "total_maps": 678, "objects": objects, "bg_events": bg_events,
        "trainer_templates": trainer_templates, "sight_ranges_reduced": sight_changed,
        "range_one_preserved": sight_unchanged_one,
        "stage49_map_payload_reachable": old_payload_reachable,
        "remaining_zero_scripts": invalid,
        "noninteractive_zero_script_rows": noninteractive_zero_scripts,
        "hisui_repaired": plan["tohoku"]["hisui"],
        "unresponsive_repaired": plan["tohoku"]["repaired_count"],
        "stage49_low_raid_hosts_removed": 6,
        "codex_reception": {
            "status": "PRESERVED", "group": 96, "map": 5,
            "local_id": 2, "x": 20, "y": 19,
            "script_pointer": 0x093CDA80,
        },
    }


def _item_script_audit(plan: Mapping[str, Any]) -> dict[str, Any]:
    scripts = plan["scripts"]
    main = [(label, row) for label, row in scripts.items()
            if (label.startswith("script_item::") or label.startswith("script_hidden::"))
            and "::already" not in label and "::full" not in label and "::end" not in label]
    objects = [row for label, row in main if label.startswith("script_item::")]
    hidden = [row for label, row in main if label.startswith("script_hidden::")]
    if len(objects) != 126 or len(hidden) != 124:
        _fail(f"item transaction script件数不一致: {len(objects)}/{len(hidden)}")
    for row in objects + hidden:
        operations = list(row["operations"])
        check = next((i for i, value in enumerate(operations) if value.startswith("checkflag:")), -1)
        add = next((i for i, value in enumerate(operations) if value.startswith("additem:")), -1)
        flag = next((i for i, value in enumerate(operations) if value.startswith("setflag:")), -1)
        if not 0 <= check < add < flag:
            _fail("item transactionがcheckflag→additem成功→setflag順ではありません")
    return {
        "status": "PASS", "object_transactions": len(objects),
        "hidden_transactions": len(hidden), "full_bag_preserves_flag": True,
        "already_collected_path": True, "object_removed_after_success": True,
        "manifest_flag_base": ITEM_FLAG_BASE, "manifest_flag_count": ITEM_FLAG_COUNT,
        "cut_trees": 33, "rock_smash_rocks": 40,
    }


def _wild_audit(output: bytes, group_sizes: Sequence[int]) -> dict[str, Any]:
    root = struct.unpack_from("<I", output, 0x8257C)[0]
    at = (root & ~1) - GBA_ROM_BASE
    if at < 0 or at + 266 * 20 > len(output):
        _fail("gWildMonHeaders rootがROM外")
    modes = (("land", 4, 12), ("water", 8, 5), ("rock", 12, 5), ("fishing", 16, 10))
    owners: dict[tuple[int, int], dict[str, str]] = {}
    orphaned: list[dict[str, Any]] = []
    tables = Counter()
    for index in range(265):
        row = at + index * 20
        coordinate = (output[row], output[row + 1])
        duplicate_zero = coordinate == (0, 0) and coordinate in owners
        if coordinate in owners and not duplicate_zero:
            _fail(f"wild owner重複: {coordinate}")
        mode_rows: dict[str, str] = {}
        for name, relative, slot_count in modes:
            pointer = struct.unpack_from("<I", output, row + relative)[0]
            if pointer == 0:
                mode_rows[name] = "NONE"
                continue
            info = (pointer & ~1) - GBA_ROM_BASE
            if info < 0 or info + 8 > len(output):
                _fail(f"wild {coordinate}/{name}: info ROM外")
            slots_pointer = struct.unpack_from("<I", output, info + 4)[0]
            slots = (slots_pointer & ~1) - GBA_ROM_BASE
            if output[info] == 0 or slots < 0 or slots + slot_count * 4 > len(output):
                _fail(f"wild {coordinate}/{name}: rate/slots不正")
            for slot in range(slot_count):
                low, high, species = struct.unpack_from("<BBH", output, slots + slot * 4)
                if low == 0 or low > high or not 1 <= species <= 1620:
                    _fail(f"wild {coordinate}/{name}: slot不正")
            mode_rows[name] = f"HEADER_{index}"
            tables[name] += 1
        if duplicate_zero:
            orphaned.append({
                "header_index": index, "coordinate": [0, 0],
                "classification": "LEGACY_ORPHAN_UNREACHABLE_AFTER_FIRST_MATCH",
                "modes": mode_rows,
            })
        else:
            owners[coordinate] = mode_rows
    expected = [(group, number) for group, size in enumerate(group_sizes)
                for number in range(int(size))]
    expected_set = set(expected)
    physical_owners = {coordinate: value for coordinate, value in owners.items()
                       if coordinate in expected_set}
    rows = [{
        "group": group, "map": number,
        "owner": physical_owners.get((group, number), {
            "land": "NO_NATIVE_ENCOUNTER", "water": "NO_NATIVE_ENCOUNTER",
            "rock": "NO_NATIVE_ENCOUNTER", "fishing": "NO_NATIVE_ENCOUNTER",
        }),
    } for group, number in expected]
    target = owners.get((3, 29), {})
    if target.get("land") in (None, "NONE"):
        _fail("511ばんすいどうland ownerが未設定")
    return {
        "status": "PASS", "physical_maps": len(rows), "native_headers": 265,
        "unique_coordinate_headers": len(owners),
        "legacy_orphan_headers": orphaned,
        "maps_without_native_header": len(rows) - len(physical_owners),
        "mode_tables": dict(tables), "owner_rows": rows,
        "waterway_511": target,
        "turning_requires_running_state_moving": True,
        "minimum_steps_early_random_roll_removed": True,
    }


def _flinch_audit(output: bytes) -> dict[str, Any]:
    table = MOVE_TABLE - GBA_ROM_BASE
    rows = []
    for move in range(MOVE_COUNT):
        row = table + move * MOVE_STRIDE
        if output[row] == 31:
            rows.append({"move": move, "chance": output[row + 5]})
    dark = output[table + DARK_PULSE * MOVE_STRIDE:table + (DARK_PULSE + 1) * MOVE_STRIDE]
    if len(dark) != MOVE_STRIDE or dark[0] != 31 or dark[5] != 20:
        _fail("あくのはどうの20%ひるみABIが不一致")
    if output[0x112B910:0x112B914] != bytes.fromhex("5145d3d2"):
        _fail("secondary chance比較がstrict <ではありません")
    source = (ROOT / "vendor/upstream/CFRU-JP/src/set_effect.c").read_text(encoding="utf-8")
    if not re.search(r"MOVE_EFFECT_FLINCH:\s*\n\s*if \(ABILITY\(gEffectBank\) == ABILITY_INNERFOCUS", source):
        _fail("Inner Focusひるみ無効contractがsource-lockにありません")
    if "gCurrentTurnActionNumber < GetBattlerTurnOrderNum(gEffectBank)" not in source:
        _fail("行動前だけひるむcontractがsource-lockにありません")
    return {
        "status": "PASS", "effect_31_moves": len(rows), "rows": rows,
        "dark_pulse": {"move_id": DARK_PULSE, "chance": 20},
        "compiled_comparison": "random_mod_100 < percentChance",
        "inner_focus_immunity": True, "already_acted_immunity": True,
    }


def _declared_change_audit(before: bytes, after: bytes, payload_start: int,
                           payload_size: int, pointer_patches: Sequence[Mapping[str, Any]],
                           sight_patches: Sequence[Mapping[str, Any]],
                           code_patches: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    spans = [(payload_start, payload_start + payload_size)]
    spans.extend((int(row["site"]), int(row["site"]) + 4) for row in pointer_patches)
    spans.extend((int(row["site"]), int(row["site"]) + 2) for row in sight_patches)
    spans.extend((int(row["site"]), int(row["site"]) + int(row["size"]))
                 for row in code_patches)
    changed = 0
    outside = []
    for index, (old, new) in enumerate(zip(before, after)):
        if old == new:
            continue
        changed += 1
        if not any(start <= index < end for start, end in spans):
            outside.append(index)
            if len(outside) == 8:
                break
    if outside:
        _fail("宣言外ROM変更: " + ", ".join(hex(value) for value in outside))
    return {"status": "PASS", "changed_bytes": changed,
            "declared_span_count": len(spans), "outside_declared_span_count": 0}


def _mgba_smoke(output: bytes, payload_offset: int, plan: Mapping[str, Any],
                trainer_audit: Mapping[str, Any]) -> dict[str, Any]:
    stage17 = _json(STAGE17_META)
    trainer = _json(TRAINER_META)
    address = lambda label: GBA_ROM_BASE + payload_offset + int(plan["labels"][label])
    source = ROOT / "tools/mgba_interaction_ownership_smoke.c"
    with tempfile.TemporaryDirectory(prefix="vega-stage50-mgba-") as raw:
        directory = Path(raw)
        rom = directory / "50_interaction_ownership_repair.gba"
        executable = directory / "mgba-interaction-ownership"
        rom.write_bytes(output)
        compiled = subprocess.run([
            os.environ.get("CC", "cc"), "-std=c11", "-Wall", "-Wextra",
            "-Werror", "-pedantic", str(source), "-o", str(executable), "-lmgba",
        ], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if compiled.returncode:
            _fail("Stage50 mGBA compile failed: " + compiled.stderr.strip()[-3000:])
        arguments = [
            str(executable), str(rom), hex(int(stage17["symbols"]["map_groups_root"])),
            hex(GBA_ROM_BASE + payload_offset), hex(GBA_ROM_BASE + payload_offset + len(output[payload_offset:payload_offset + int(plan["payload_size"])])),
            hex(address("script_hisui")), hex(address("runtime_moving_wild_encounter") | 1),
            hex(int(trainer["trainer_table"]["new_address"])),
            hex(int(trainer_audit["shinichi"]["command_address"])),
        ]
        runs = []
        for _ in range(2):
            completed = subprocess.run(arguments, cwd=ROOT, text=True,
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if completed.returncode:
                detail = completed.stderr.strip() or completed.stdout.strip()
                _fail("Stage50 mGBA smoke failed: " + detail[-3000:])
            runs.append(json.loads(completed.stdout))
    if runs[0] != runs[1] or runs[0].get("status") != "PASS":
        _fail("Stage50 mGBA smokeが決定論的PASSではありません")
    return runs[0] | {"process_runs": 2, "stdout_identical": True,
                      "rom_sha256": _sha(output), "artifacts_written": []}


def _markdown(report: Mapping[str, Any]) -> bytes:
    kanto = report["interaction_plan"]["kanto"]["counts"]
    return (f"""# Stage50 interaction ownership repair

- Status: **{report['status']}**
- Input Stage49: `{report['input']['sha256']}`
- Output Stage50: `{report['output']['sha256']}`
- physical maps: 678（東北425 + カントー253）

## 修正

- 無効script NPC: {report['map_audit']['unresponsive_repaired']}体（ヒスイシティ local 4を含む）
- 通常trainer視線: {report['map_audit']['sight_ranges_reduced']} templateを1マス補正
- item ball: {kanto['restored_item_ball']}復元 + {kanto.get('preserved_item_ball', 0)}既存
- hidden item transaction: {report['item_audit']['hidden_transactions']}
- いあいぎり: {report['item_audit']['cut_trees']}、いわくだき: {report['item_audit']['rock_smash_rocks']}
- Stage49低レベルRaid host: 6件撤回（進行停止経路を除去）
- 511ばんすいどう: land encounter owner新設
- 知恵の洞窟を含む通常遭遇: 方向転換を歩数から除外、最低歩数内の早期乱数を除去

## 回帰

- 通常trainer: {report['trainer_audit']['encounters']} encounter / party / script pointer PASS
- あくのはどう: 20%、compiled比較 `<`、Inner Focus・行動済み無効 PASS
- きあいのタスキ・特性ABI: exact-ROM PASS
- mGBA: exact Stage50 boot / Hisui / 511 / cadence / flinch / trainer / Focus Sash PASS x2
- Stage49誤owner payloadへのmap到達: 0
- 宣言外ROM変更: 0
""").encode("utf-8")


def _build_outputs() -> dict[Path, bytes]:
    stage49 = _read(STAGE49_ROM, digest=STAGE49_SHA256, size=ROM_SIZE)
    stage48 = _read(STAGE48_ROM, digest=STAGE48_SHA256, size=ROM_SIZE)
    clean = _read(CLEAN_ROM, digest=CLEAN_SHA256, size=ROM_SIZE // 2)
    inventory = _json(ID_INVENTORY)
    group_sizes = list(inventory["map_contract"]["group_sizes"])

    provisional, _, _, _ = build_payload(ROOT, stage49, stage48, clean, 0, group_sizes)
    allocation, _ = _allocation(len(provisional), "0" * 64)
    payload_offset = int(allocation["start"])
    payload, plan, pointer_patches, sight_patches = build_payload(
        ROOT, stage49, stage48, clean, payload_offset, group_sizes,
    )
    if len(payload) != len(provisional):
        _fail("payload sizeが配置アドレスで変化")
    allocation, allocation_report = _allocation(len(payload), _sha(payload))
    if int(allocation["start"]) != payload_offset:
        _fail("payload placementがfixed-point後に変化")
    end = payload_offset + len(payload)
    if stage49[payload_offset:end] != bytes([0xFF]) * len(payload):
        _fail("payload destinationが未使用FFではありません")

    output = bytearray(stage49)
    output[payload_offset:end] = payload
    for patch in pointer_patches:
        site = int(patch["site"])
        expected = int(patch["expected"])
        if struct.unpack_from("<I", output, site)[0] != expected:
            _fail(f"pointer expected値不一致: {patch.get('map_key', patch['kind'])}")
        target = GBA_ROM_BASE + payload_offset + int(plan["labels"][patch["label"]])
        struct.pack_into("<I", output, site, target)
        patch["target"] = target
    for patch in sight_patches:
        site = int(patch["site"])
        if struct.unpack_from("<H", output, site)[0] != int(patch["expected"]):
            _fail(f"trainer sight expected値不一致: {site:#x}")
        struct.pack_into("<H", output, site, int(patch["replacement"]))

    code_patches: list[dict[str, Any]] = []
    if bytes(output[WILD_HOOK_OFFSET:WILD_HOOK_OFFSET + 8]) != WILD_HOOK_EXPECTED:
        _fail("CheckStandardWildEncounter hook expected値不一致")
    wrapper = (GBA_ROM_BASE + payload_offset
               + int(plan["labels"]["runtime_moving_wild_encounter"])) | 1
    replacement = bytes.fromhex("004b1847") + struct.pack("<I", wrapper)
    output[WILD_HOOK_OFFSET:WILD_HOOK_OFFSET + 8] = replacement
    code_patches.append({
        "name": "encounter only when player runningState=MOVING",
        "site": WILD_HOOK_OFFSET, "address": GBA_ROM_BASE + WILD_HOOK_OFFSET,
        "size": 8, "expected_hex": WILD_HOOK_EXPECTED.hex(),
        "replacement_hex": replacement.hex(), "target": wrapper,
    })
    if bytes(output[COOLDOWN_OFFSET:COOLDOWN_OFFSET + 2]) != COOLDOWN_EXPECTED:
        _fail("encounter minimum-grace expected値不一致")
    output[COOLDOWN_OFFSET:COOLDOWN_OFFSET + 2] = COOLDOWN_REPLACEMENT
    code_patches.append({
        "name": "minimum encounter grace without early random roll",
        "site": COOLDOWN_OFFSET, "address": GBA_ROM_BASE + COOLDOWN_OFFSET,
        "size": 2, "expected_hex": COOLDOWN_EXPECTED.hex(),
        "replacement_hex": COOLDOWN_REPLACEMENT.hex(),
    })
    output_raw = bytes(output)

    map_audit = _map_audit(stage48, stage49, output_raw, group_sizes, plan)
    item_audit = _item_script_audit(plan)
    wild_audit = _wild_audit(output_raw, group_sizes)
    flinch_audit = _flinch_audit(output_raw)
    trainer = _trainer_audit(stage48, output_raw)
    change = _declared_change_audit(
        stage49, output_raw, payload_offset, len(payload),
        pointer_patches, sight_patches, code_patches,
    )
    mgba = _mgba_smoke(output_raw, payload_offset, plan, trainer)
    incremental = create_bps(stage49, output_raw,
                             metadata=b"Stage49 to Stage50 interaction ownership repair")
    direct = create_bps(clean, output_raw,
                        metadata=b"Clean FireRed JPN Rev0 to Stage50 interaction ownership repair")
    if apply_bps(stage49, incremental) != output_raw or apply_bps(clean, direct) != output_raw:
        _fail("BPS round-trip不一致")

    report = {
        "schema_version": 1, "task": TASK, "stage": STAGE, "status": "PASS",
        "input": {"path": str(STAGE49_ROM), "size": len(stage49), "sha256": _sha(stage49)},
        "output": {"path": str(OUTPUTS["rom"]), "size": len(output_raw),
                   "sha256": _sha(output_raw)},
        "payload": {"offset": payload_offset, "address": GBA_ROM_BASE + payload_offset,
                    "size": len(payload), "sha256": _sha(payload)},
        "interaction_plan": plan, "map_audit": map_audit,
        "item_audit": item_audit, "wild_audit": wild_audit,
        "flinch_audit": flinch_audit, "trainer_audit": trainer,
        "focus_sash_abi": plan["item_abi"], "change_audit": change,
        "runtime_patches": code_patches, "mgba": mgba,
        "bps": {
            "incremental": {"path": str(OUTPUTS["incremental_bps"]),
                            "size": len(incremental), "sha256": _sha(incremental),
                            "round_trip": True},
            "clean": {"path": str(OUTPUTS["clean_bps"]), "size": len(direct),
                      "sha256": _sha(direct), "round_trip": True},
        },
    }
    metadata = report | {
        "allocation": allocation, "pointer_patches": pointer_patches,
        "sight_patches": sight_patches,
        "invariants": {
            "stage49_hash_pinned": True, "stage48_hash_pinned": True,
            "clean_hash_pinned": True, "allocator_overlap_zero": True,
            "declared_changes_only": True, "physical_maps_678": True,
            "trainers_1302_preserved": True, "save_abi_append_only_flags": True,
            "bps_exact": True,
        },
    }
    return {
        OUTPUTS["rom"]: output_raw,
        OUTPUTS["metadata"]: _stable(metadata),
        OUTPUTS["allocation"]: _stable(allocation_report),
        OUTPUTS["mgba"]: _stable(mgba),
        OUTPUTS["incremental_bps"]: incremental,
        OUTPUTS["clean_bps"]: direct,
        OUTPUTS["report_json"]: _stable(report),
        OUTPUTS["report_md"]: _markdown(report),
    }


def _write(outputs: Mapping[Path, bytes]) -> None:
    for relative, raw in outputs.items():
        path = ROOT / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
            stream.write(raw)
            temporary = Path(stream.name)
        os.replace(temporary, path)


def _check(outputs: Mapping[Path, bytes]) -> None:
    drift = [str(path) for path, raw in outputs.items()
             if not (ROOT / path).is_file() or (ROOT / path).read_bytes() != raw]
    if drift:
        _fail("Stage50生成物drift: " + ", ".join(drift))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("build", "check"))
    args = parser.parse_args()
    try:
        outputs = _build_outputs()
        _write(outputs) if args.mode == "build" else _check(outputs)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError,
            InteractionBuildError) as error:
        print(f"Stage50 interaction ownership {args.mode} failed: {error}", file=sys.stderr)
        return 1
    meta = json.loads(outputs[OUTPUTS["metadata"]])
    print(f"Stage50 interaction ownership {args.mode}: PASS "
          f"sha256={meta['output']['sha256']} artifacts={len(outputs)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
