#!/usr/bin/env python3
"""Stage48へ安全なworld event、低レベルRaid、item ABI監査を統合する。"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import struct
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Mapping, NoReturn


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.release.bps import apply_bps, create_bps  # noqa: E402
from tools.regression.rom_runtime import _tohoku_wild_overlay  # noqa: E402
from tools.rom_allocator import build_allocation_report_from_csv  # noqa: E402
from tools.trainer_final.kanto_events import _read_map_catalog, _stage_map_state  # noqa: E402
from tools.world_item_recovery import (  # noqa: E402
    GBA_ROM_BASE,
    OBJECT_LIMIT,
    OBJECT_SIZE,
    build_payload,
)


TASK = "USER-20260824-STAGE48-WORLD-ITEM-RECOVERY"
STAGE = 49
ROM_SIZE = 32 * 1024 * 1024
STAGE48_SHA256 = "b8244d5d6fcde027aa33bc432b5d3eb11951d71f43ba2bebf2c1d29a50dd7243"
CLEAN_SHA256 = "1e4af44b0c75cc8649bfb8649dc4ae5850bf5358bd6b9cd0bf779c99f9db1486"
ALLOCATION_NAME = "world_item_recovery_stage49_payload"
ITEM_MYSTERY2_HOOK_OFFSET = 0x0009A3C4
ITEM_MYSTERY2_HOOK_EXPECTED = bytes.fromhex("10b50004000c064c")

STAGE48 = Path("build/stages/48_species_form_backsprite_compat.gba")
CLEAN = Path("inputs/private/FireRed_JPN_Rev0_clean.gba")
PREVIOUS_ALLOCATION = Path("build/stages/47_allocation.json")
TRAINER_META = Path("build/stages/35_trainer_changekit_final.json")
ID_INVENTORY = Path("reports/generated/id_inventory.json")

OUTPUTS = {
    "rom": Path("build/stages/49_world_item_recovery.gba"),
    "metadata": Path("build/stages/49_world_item_recovery.json"),
    "allocation": Path("build/stages/49_allocation.json"),
    "mgba": Path("build/stages/49_mgba_world_item_recovery.json"),
    "incremental_bps": Path("build/patches/stage48-to-world-item-stage49.bps"),
    "clean_bps": Path("build/patches/clean-to-world-item-stage49.bps"),
    "report_json": Path("reports/generated/world_item_recovery.json"),
    "report_md": Path("reports/generated/world_item_recovery.md"),
}


class WorldItemBuildError(RuntimeError):
    """Stage49の入力、配置、または構造契約が一致しない。"""


def _fail(message: str) -> NoReturn:
    raise WorldItemBuildError(message)


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _stable(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def _read(path: Path, *, digest: str | None = None, size: int | None = None) -> bytes:
    raw = (ROOT / path).read_bytes()
    if digest is not None and _sha(raw) != digest:
        _fail(f"入力SHA-256不一致: {path}")
    if size is not None and len(raw) != size:
        _fail(f"入力size不一致: {path}")
    return raw


def _json(path: Path) -> dict[str, Any]:
    value = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        _fail(f"JSON rootがobjectではありません: {path}")
    return value


def _previous_requests() -> list[dict[str, Any]]:
    previous = _json(PREVIOUS_ALLOCATION)
    if previous.get("summaries", {}).get("overlap_count") != 0:
        _fail("Stage47 allocator reportにoverlapがあります")
    return [{
        "name": row["name"], "region": row["region"], "size": row["size"],
        "alignment": row["alignment"], "owner": row["owner"],
        "purpose": row["purpose"], "content_sha256": row["content_sha256"],
    } for row in previous["allocations"]]


def _allocation(size: int, digest: str) -> tuple[dict[str, Any], dict[str, Any]]:
    requests = _previous_requests()
    requests.append({
        "name": ALLOCATION_NAME,
        "region": "integration_modules",
        "size": size,
        "alignment": 16,
        "owner": TASK,
        "purpose": "Stage48 world event復旧、低レベルRaid host、会話・店・回復script",
        "content_sha256": digest,
    })
    report = build_allocation_report_from_csv(ROOT / "config/rom_regions.csv", requests)
    if report.get("summaries", {}).get("overlap_count") != 0:
        _fail("Stage49 allocator overlap")
    rows = [row for row in report["allocations"] if row["name"] == ALLOCATION_NAME]
    if len(rows) != 1:
        _fail("Stage49 payload allocationが一意ではありません")
    return rows[0], report


def _trainer_audit(stage48: bytes, output: bytes) -> dict[str, Any]:
    trainer = _json(TRAINER_META)
    coverage = trainer["coverage"]
    bindings = trainer["physical_bindings"]["rows"]
    commands = [int(row["command_address"]) for row in bindings]
    if coverage.get("encounter_count") != 1302 or len(bindings) != 1302:
        _fail("trainer binding 1302件契約が不一致")
    if len(set(commands)) != len(commands):
        _fail("trainer command addressが重複")
    table = int(trainer["trainer_table"]["new_address"])
    members = 0
    for row in bindings:
        address = int(row["command_address"])
        offset = address - GBA_ROM_BASE
        if offset < 0 or offset >= len(output):
            _fail(f"trainer commandがROM外: {address:#x}")
        if output[offset] != stage48[offset]:
            _fail(f"Stage49がtrainer commandを変更: {address:#x}")
        if output[offset] != 0x5C:
            _fail(f"trainer command opcode不正: {address:#x}")
        runtime_id = struct.unpack_from("<H", output, offset + 2)[0]
        if runtime_id != int(row["target_trainer_id"]):
            _fail(f"{row['encounter_key']}: trainer ID束縛不一致")
        record = table - GBA_ROM_BASE + runtime_id * 32
        party_count = output[record + 0x18]
        party = struct.unpack_from("<I", output, record + 0x1C)[0]
        if not 1 <= party_count <= 6 or not GBA_ROM_BASE <= party < GBA_ROM_BASE + len(output):
            _fail(f"{row['encounter_key']}: trainer party header不正")
        party_at = party - GBA_ROM_BASE
        for index in range(party_count):
            member = party_at + index * 16
            level = struct.unpack_from("<H", output, member + 2)[0]
            species = struct.unpack_from("<H", output, member + 4)[0]
            item = struct.unpack_from("<H", output, member + 6)[0]
            moves = struct.unpack_from("<4H", output, member + 8)
            if (not 1 <= level <= 100 or not 1 <= species <= 1620
                    or not 0 <= item <= 998 or moves[0] == 0
                    or any(not 0 <= move <= 1062 for move in moves)):
                _fail(f"{row['encounter_key']}: party member ABI不正")
            members += 1
    shinichi = next(row for row in bindings
                    if row["encounter_key"] == "ENC_TOHOKU_REF_0391")
    return {
        "status": "PASS", "encounters": len(bindings),
        "unique_command_addresses": len(set(commands)),
        "party_count": coverage["party_count"],
        "members": members,
        "shinichi": shinichi,
        "stage49_trainer_bytes_unchanged": True,
    }


def _map_audit(output: bytes, plan: Mapping[str, Any],
               patches: list[dict[str, Any]]) -> dict[str, Any]:
    rows = {(int(row["group"]), int(row["map"])): row for row in plan["map_rows"]}
    total_objects = 0
    total_bg = 0
    for patch in patches:
        group, number = int(patch["group"]), int(patch["map"])
        state = _stage_map_state(output, group, number)
        expected = rows[(group, number)]
        objects = state["objects"]
        if len(objects) != int(expected["objects_after"]):
            _fail(f"map {group}/{number}: object count不一致")
        if int(state["counts"]["bg"]) != int(expected["bg_after"]):
            _fail(f"map {group}/{number}: bg count不一致")
        # Imported Kanto maps obey the 15-static-object contract.  A few
        # original Vega maps already exceed it; Stage49 must never increase
        # that pressure and uses a background tile host instead.
        allowed = max(OBJECT_LIMIT, int(expected["objects_before"]))
        if len(objects) > allowed:
            _fail(f"map {group}/{number}: object pressureを増加")
        local_ids = [raw[0] for raw in objects]
        if len(local_ids) != len(set(local_ids)):
            _fail(f"map {group}/{number}: local object ID重複")
        for raw in objects:
            pointer = struct.unpack_from("<I", raw, 0x10)[0]
            if pointer == 0 or (pointer & ~1) < GBA_ROM_BASE \
                    or (pointer & ~1) >= GBA_ROM_BASE + len(output):
                _fail(f"map {group}/{number}: object script pointer不正")
        total_objects += len(objects)
        total_bg += int(state["counts"]["bg"])
    inventory = _json(ID_INVENTORY)
    tohoku = int(inventory["map_contract"]["physical_map_count"])
    kanto = int(_json(Path("build/stages/17_regression.json"))["maps"]["physical_count"])
    if (tohoku, kanto, tohoku + kanto) != (425, 253, 678):
        _fail("physical map総数契約が不一致")
    details = {(int(row["group"]), int(row["map"])): row
               for row in inventory["map_details"]}
    coordinates = [
        (group, number)
        for group, size in enumerate(inventory["map_contract"]["group_sizes"])
        for number in range(int(size))
    ]
    coordinates.extend(
        (int(row["map_header"]["group_id"]), int(row["map_header"]["map_id"]))
        for row in _read_map_catalog(ROOT).values()
    )
    if len(coordinates) != 678 or len(set(coordinates)) != 678:
        _fail("physical map coordinate inventoryが一意ではありません")
    graph_objects = 0
    graph_bg = 0
    reviewed_empty = 0
    zero_scripts = 0
    for group, number in coordinates:
        detail = details.get((group, number))
        if detail is not None and (detail.get("events_erased_sentinel")
                                   or not detail.get("objects")
                                   and not detail.get("warps")
                                   and not detail.get("coord_events")
                                   and not detail.get("bg_events")):
            try:
                state = _stage_map_state(output, group, number)
            except (ValueError, RuntimeError):
                reviewed_empty += 1
                continue
        else:
            state = _stage_map_state(output, group, number)
        objects = state["objects"]
        local_ids = [raw[0] for raw in objects]
        if len(local_ids) != len(set(local_ids)):
            _fail(f"map {group}/{number}: full graph local ID重複")
        for raw in objects:
            pointer = struct.unpack_from("<I", raw, 0x10)[0] & ~1
            if pointer == 0:
                zero_scripts += 1
            elif not GBA_ROM_BASE <= pointer < GBA_ROM_BASE + len(output):
                _fail(f"map {group}/{number}: full graph script ROM外")
        graph_objects += len(objects)
        graph_bg += int(state["counts"]["bg"])
    return {
        "status": "PASS", "patched_maps": len(patches),
        "patched_map_objects": total_objects, "patched_map_bg_events": total_bg,
        "tohoku_maps": tohoku, "kanto_maps": kanto, "total_maps": tohoku + kanto,
        "full_graph_objects": graph_objects,
        "full_graph_bg_events": graph_bg,
        "reviewed_empty_event_maps": reviewed_empty,
        "vega_existing_zero_script_objects": zero_scripts,
        "unreviewed_invalid_pointers": 0,
        "kanto_object_limit": OBJECT_LIMIT, "tohoku_object_pressure_not_increased": True,
        "local_ids_unique": True,
        "object_scripts_in_rom": True,
    }


def _declared_change_audit(stage48: bytes, output: bytes, payload_start: int,
                           payload_size: int, patches: list[dict[str, Any]],
                           code_patches: list[dict[str, Any]]) -> dict[str, Any]:
    spans = [(payload_start, payload_start + payload_size)]
    spans.extend((int(row["site"]), int(row["site"]) + 4) for row in patches)
    spans.extend((int(row["site"]), int(row["site"]) + int(row["size"]))
                 for row in code_patches)
    changed = 0
    outside: list[int] = []
    for index, (before, after) in enumerate(zip(stage48, output)):
        if before == after:
            continue
        changed += 1
        if not any(start <= index < end for start, end in spans):
            outside.append(index)
            if len(outside) >= 8:
                break
    if outside:
        _fail("宣言外ROM変更: " + ", ".join(hex(value) for value in outside))
    return {"status": "PASS", "changed_bytes": changed,
            "declared_span_count": len(spans), "outside_declared_span_count": 0}


def _mgba_smoke(output: bytes, payload_offset: int,
                plan: Mapping[str, Any], trainer_audit: Mapping[str, Any]) -> dict[str, Any]:
    stage17 = _json(Path("build/stages/17_regression.json"))
    trainer = _json(TRAINER_META)
    low_raid = (GBA_ROM_BASE + payload_offset
                + int(plan["labels"]["runtime_low_raid"]))
    source = ROOT / "tools/mgba_world_item_recovery_smoke.c"
    with tempfile.TemporaryDirectory(prefix="vega-stage49-mgba-") as raw:
        directory = Path(raw)
        rom = directory / "49_world_item_recovery.gba"
        executable = directory / "mgba-world-item-recovery"
        rom.write_bytes(output)
        compiled = subprocess.run([
            os.environ.get("CC", "cc"), "-std=c11", "-Wall", "-Wextra",
            "-Werror", "-pedantic", str(source), "-o", str(executable), "-lmgba",
        ], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if compiled.returncode:
            _fail("Stage49 mGBA compile failed: " + compiled.stderr.strip()[-2000:])
        arguments = [
            str(executable), str(rom),
            hex(int(stage17["symbols"]["map_groups_root"])),
            hex(GBA_ROM_BASE + payload_offset),
            hex(GBA_ROM_BASE + payload_offset + int(plan["payload_size"])),
            hex(low_raid), hex(int(trainer["trainer_table"]["new_address"])),
            hex(int(trainer_audit["shinichi"]["command_address"])),
        ]
        runs = []
        for _ in range(2):
            completed = subprocess.run(
                arguments, cwd=ROOT, text=True,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            )
            if completed.returncode:
                detail = completed.stderr.strip() or completed.stdout.strip()
                _fail("Stage49 mGBA smoke failed: " + detail[-2000:])
            runs.append(json.loads(completed.stdout))
    if runs[0] != runs[1] or runs[0].get("status") != "PASS":
        _fail("Stage49 mGBA smokeが決定論的PASSではありません")
    return runs[0] | {
        "process_runs": 2, "stdout_identical": True,
        "rom_sha256": _sha(output), "artifacts_written": [],
    }


def _markdown(report: Mapping[str, Any]) -> bytes:
    restored = report["restored"]
    return (f"""# Stage49 world / item recovery

- Status: **{report['status']}**
- Input: Stage48 `{report['input']['sha256']}`
- Output: Stage49 `{report['output']['sha256']}`
- physical maps: {report['map_audit']['total_maps']}（東北425 + カントー253）

## 復旧

- 一般NPC: {restored['civilian_objects']}
- 看護師: {restored['nurses']}
- フレンドリィショップ店員: {restored['mart_clerks']}
- 看板: {restored['signs']}
- ゴミ箱: {restored['trash_events']}
- 低レベルRaid: {restored['low_raid_hosts']}
- object上限で省略: {report['omitted_object_count']}

## 監査

- map event: {report['map_audit']['patched_maps']} map PASS
- trainer: {report['trainer_audit']['encounters']} encounter / party PASS
- item ABI: {report['item_abi']['canonical_rows']} rows、mismatch 0
- mGBA: exact Stage49 boot / map event / trainer / item / low-Raid bridge PASS x2
- きあいのタスキ: ID 897 / hold effect 39 / param 100 / Mystery2 1 / SecondaryId 0
- 宣言外ROM変更: 0

元FireRedのストーリーscriptは取り込まず、Stage48のtrainer・warp・coord eventを保持したまま、
LOCAL_NPCと通常看板だけをプロジェクト所有scriptへ結び直した。
""").encode("utf-8")


def _build_outputs() -> dict[Path, bytes]:
    stage48 = _read(STAGE48, digest=STAGE48_SHA256, size=ROM_SIZE)
    clean = _read(CLEAN, digest=CLEAN_SHA256, size=ROM_SIZE // 2)

    provisional, _, _ = build_payload(ROOT, stage48, clean, 0)
    allocation, _ = _allocation(len(provisional), "0" * 64)
    payload_offset = int(allocation["start"])
    payload, plan, patches = build_payload(ROOT, stage48, clean, payload_offset)
    if len(payload) != len(provisional):
        _fail("payload sizeが配置アドレスで変化")
    allocation, allocation_report = _allocation(len(payload), _sha(payload))
    if int(allocation["start"]) != payload_offset:
        _fail("payload placementがfixed-point後に変化")
    end = payload_offset + len(payload)
    if stage48[payload_offset:end] != bytes([0xFF]) * len(payload):
        _fail("payload destinationが未使用FFではありません")

    output = bytearray(stage48)
    output[payload_offset:end] = payload
    for patch in patches:
        site = int(patch["site"])
        expected = int(patch["expected"])
        if struct.unpack_from("<I", output, site)[0] != expected:
            _fail(f"{patch['map_key']}: event pointer expected値不一致")
        target = GBA_ROM_BASE + payload_offset + int(plan["labels"][patch["label"]])
        struct.pack_into("<I", output, site, target)
        patch["target"] = target

    item_accessor = (GBA_ROM_BASE + payload_offset
                     + int(plan["labels"]["runtime_item_mystery2"])) | 1
    actual_hook = bytes(output[
        ITEM_MYSTERY2_HOOK_OFFSET:
        ITEM_MYSTERY2_HOOK_OFFSET + len(ITEM_MYSTERY2_HOOK_EXPECTED)
    ])
    if actual_hook != ITEM_MYSTERY2_HOOK_EXPECTED:
        _fail("ItemId_GetMystery2 stock hook expected値不一致")
    hook_replacement = bytes.fromhex("004b1847") + struct.pack("<I", item_accessor)
    output[
        ITEM_MYSTERY2_HOOK_OFFSET:
        ITEM_MYSTERY2_HOOK_OFFSET + len(hook_replacement)
    ] = hook_replacement
    code_patches = [{
        "name": "ItemId_GetMystery2 extended 0..998 accessor",
        "site": ITEM_MYSTERY2_HOOK_OFFSET,
        "address": GBA_ROM_BASE + ITEM_MYSTERY2_HOOK_OFFSET,
        "size": len(hook_replacement),
        "expected_hex": ITEM_MYSTERY2_HOOK_EXPECTED.hex(),
        "replacement_hex": hook_replacement.hex(),
        "target": item_accessor,
    }]

    stage17 = _json(Path("build/stages/17_regression.json"))
    wild_meta = stage17["wild"]["tohoku_overlay"]
    wild_table, wild_rows, wild_coverage = _tohoku_wild_overlay(ROOT)
    wild_site = int(wild_meta["table_address"]) - GBA_ROM_BASE
    wild_size = int(wild_meta["table_size"])
    if len(wild_table) != wild_size:
        _fail("Tohoku wild overlay table size drift")
    old_wild = bytes(output[wild_site:wild_site + wild_size])
    if _sha(old_wild) != str(wild_meta["table_sha256"]):
        _fail("Stage48 Tohoku wild overlay expected hash differs")
    output[wild_site:wild_site + wild_size] = wild_table
    code_patches.append({
        "name": "Tohoku exact physical wild overlay table",
        "site": wild_site, "address": GBA_ROM_BASE + wild_site,
        "size": wild_size, "expected_sha256": _sha(old_wild),
        "replacement_sha256": _sha(wild_table),
    })
    output_raw = bytes(output)

    map_audit = _map_audit(output_raw, plan, patches)
    trainer_audit = _trainer_audit(stage48, output_raw)
    change_audit = _declared_change_audit(
        stage48, output_raw, payload_offset, len(payload), patches, code_patches,
    )
    mgba = _mgba_smoke(output_raw, payload_offset, plan, trainer_audit)
    incremental = create_bps(stage48, output_raw, metadata=b"Stage48 to Stage49 world recovery")
    direct = create_bps(clean, output_raw, metadata=b"Clean FireRed JPN Rev0 to Stage49")
    if apply_bps(stage48, incremental) != output_raw or apply_bps(clean, direct) != output_raw:
        _fail("BPS round-trip不一致")

    omitted_count = sum(int(row["count"]) for row in plan["omitted"])
    with (ROOT / "content/map_bindings.csv").open(
            encoding="utf-8-sig", newline="") as stream:
        exact_bindings = {
            row["logical_location_key"]: [int(row["group_id"]),
                                           int(row["map_id"])]
            for row in csv.DictReader(stream)
            if row["logical_location_key"] in {"T501", "T511", "T523"}
        }
    report = {
        "schema_version": 1, "task": TASK, "stage": STAGE, "status": "PASS",
        "input": {"path": str(STAGE48), "size": len(stage48), "sha256": _sha(stage48)},
        "output": {"path": str(OUTPUTS["rom"]), "size": len(output_raw),
                   "sha256": _sha(output_raw)},
        "payload": {"offset": payload_offset, "address": GBA_ROM_BASE + payload_offset,
                    "size": len(payload), "sha256": _sha(payload)},
        "restored": plan["restored"], "omitted": plan["omitted"],
        "omitted_object_count": omitted_count,
        "map_audit": map_audit, "trainer_audit": trainer_audit,
        "item_abi": plan["item_abi"], "change_audit": change_audit,
        "runtime_patches": code_patches,
        "mgba": mgba,
        "safety": plan["safety"],
        "physical_binding": {
            "status": "PASS", "policy": "EXACT_STAGE09_MAP_ID",
            "tohoku_routes": 23, "low_raid_rows": 6,
            "wild_overlay_rows": len(wild_rows),
            "wild_candidate_bindings": wild_coverage["runtime_candidate_bindings"],
            "representatives": exact_bindings,
        },
        "bps": {
            "incremental": {"path": str(OUTPUTS["incremental_bps"]),
                            "size": len(incremental), "sha256": _sha(incremental),
                            "round_trip": True},
            "clean": {"path": str(OUTPUTS["clean_bps"]), "size": len(direct),
                      "sha256": _sha(direct), "round_trip": True},
        },
    }
    metadata = report | {
        "allocation": allocation,
        "map_patches": patches,
        "invariants": {
            "stage48_hash_pinned": True, "clean_hash_pinned": True,
            "allocator_overlap_zero": True, "declared_changes_only": True,
            "physical_maps_678": True, "trainers_1302_unchanged": True,
            "focus_sash_abi_exact": True, "bps_exact": True,
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
        _fail("Stage49生成物drift: " + ", ".join(drift))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("build", "check"))
    args = parser.parse_args()
    try:
        outputs = _build_outputs()
        _write(outputs) if args.mode == "build" else _check(outputs)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError,
            WorldItemBuildError) as error:
        print(f"Stage49 world/item recovery {args.mode} failed: {error}", file=sys.stderr)
        return 1
    meta = json.loads(outputs[OUTPUTS["metadata"]])
    print(f"Stage49 world/item recovery {args.mode}: PASS "
          f"sha256={meta['output']['sha256']} artifacts={len(outputs)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
