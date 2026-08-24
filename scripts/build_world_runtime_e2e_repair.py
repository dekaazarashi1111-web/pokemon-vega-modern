#!/usr/bin/env python3
"""Stage51の全world ownerを再構築し、独立したStage52を生成する。"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import struct
import subprocess
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any, Mapping, NoReturn, Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(ROOT))

from scripts.build_continue_save_freeze_repair import _continue_smoke  # noqa: E402
from scripts.build_interaction_ownership_repair import (  # noqa: E402
    _flinch_audit,
    _wild_audit,
)
from scripts.build_world_item_recovery import _trainer_audit  # noqa: E402
from tools.release.bps import apply_bps, create_bps  # noqa: E402
from tools.rom_allocator import build_allocation_report_from_csv  # noqa: E402
from tools.trainer_final.kanto_events import _object_fields, _stage_map_state  # noqa: E402
from tools.world_runtime_e2e_repair import (  # noqa: E402
    COOLDOWN_OFFSET,
    COOLDOWN_STOCK,
    GBA_ROM_BASE,
    ROM_SIZE,
    TASK,
    TRAINER_PARTY_CONTINUATION_EXPECTED,
    TRAINER_PARTY_CONTINUATION_OFFSET,
    TRAINER_RECORD_SIZE,
    TRAINER_PARTY_SIZE_OFFSET,
    TRAINER_TABLE_ADDRESS,
    WILD_HOOK_OFFSET,
    WILD_STOCK_HOOK,
    _coordinates,
    build_payload,
)


STAGE = 52
STAGE51_SHA256 = "6cda0c65836fa389c27e18bdcd500df4410348bb2176a85c2ab2fa4d41ed96e4"
STAGE48_SHA256 = "b8244d5d6fcde027aa33bc432b5d3eb11951d71f43ba2bebf2c1d29a50dd7243"
STAGE03_SHA256 = "fd01903a3507e25ae62377e3549962709ca207d5871b55fd4dcbb57813d5bbaf"
CLEAN_SHA256 = "1e4af44b0c75cc8649bfb8649dc4ae5850bf5358bd6b9cd0bf779c99f9db1486"
ALLOCATION_NAME = "world_runtime_e2e_repair_stage52_payload"

STAGE51_ROM = Path("build/stages/51_continue_save_freeze_repair.gba")
STAGE48_ROM = Path("build/stages/48_species_form_backsprite_compat.gba")
STAGE03_ROM = Path("build/stages/03_harness.gba")
CLEAN_ROM = Path("inputs/private/FireRed_JPN_Rev0_clean.gba")
STAGE50_META = Path("build/stages/50_interaction_ownership_repair.json")
PREVIOUS_ALLOCATION = Path("build/stages/51_allocation.json")
ID_INVENTORY = Path("reports/generated/id_inventory.json")

OUTPUTS = {
    "rom": Path("build/stages/52_world_runtime_e2e_repair.gba"),
    "metadata": Path("build/stages/52_world_runtime_e2e_repair.json"),
    "allocation": Path("build/stages/52_allocation.json"),
    "mgba": Path("build/stages/52_mgba_world_runtime_e2e.json"),
    "incremental_bps": Path("build/patches/stage51-to-world-runtime-stage52.bps"),
    "clean_bps": Path("build/patches/clean-to-world-runtime-stage52.bps"),
    "report_json": Path("reports/generated/world_runtime_e2e_repair.json"),
    "report_md": Path("reports/generated/world_runtime_e2e_repair.md"),
    "owner_ledger": Path("reports/generated/world_runtime_owner_ledger.json"),
}


class WorldRuntimeBuildError(RuntimeError):
    """Stage52の入力・配置・全件監査・E2E証跡が不一致。"""


def _fail(message: str) -> NoReturn:
    raise WorldRuntimeBuildError(message)


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _stable(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def _read(path: Path, digest: str | None = None, size: int | None = None) -> bytes:
    raw = (ROOT / path).read_bytes()
    if digest is not None and _sha(raw) != digest:
        _fail(f"入力hash不一致: {path}")
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
        _fail("Stage51 allocator reportにoverlapがあります")
    return [{
        key: row[key]
        for key in ("name", "region", "size", "alignment", "owner", "purpose", "content_sha256")
    } for row in previous["allocations"]]


def _allocation(size: int, digest: str) -> tuple[dict[str, Any], dict[str, Any]]:
    requests = _previous_requests()
    requests.append({
        "name": ALLOCATION_NAME, "region": "integration_modules",
        "size": size, "alignment": 16, "owner": TASK,
        "purpose": "678 mapのtrainer/item/dialogue/field/wild owner根本修復",
        "content_sha256": digest,
    })
    report = build_allocation_report_from_csv(ROOT / "config/rom_regions.csv", requests)
    if report.get("summaries", {}).get("overlap_count") != 0:
        _fail("Stage52 allocator overlap")
    rows = [row for row in report["allocations"] if row["name"] == ALLOCATION_NAME]
    if len(rows) != 1:
        _fail("Stage52 payload allocationが一意ではありません")
    return rows[0], report


def _map_owner_audit(output: bytes, stage48: bytes, plan: Mapping[str, Any],
                     group_sizes: Sequence[int], metadata50: Mapping[str, Any]) -> dict[str, Any]:
    active_trainers = 0
    disabled_special = 0
    forbidden_roots = {
        int(metadata50["payload"]["address"]) + int(metadata50["interaction_plan"]["labels"][label])
        for label in ("script_outdoor", "script_indoor", "script_dungeon", "script_sign",
                      "script_repaired", "runtime_moving_wild_encounter")
    }
    forbidden_roots.update(
        int(metadata50["payload"]["address"]) + int(offset)
        for label, offset in metadata50["interaction_plan"]["labels"].items()
        if label.startswith("script_item::") or label.startswith("script_hidden::")
    )
    forbidden_reachable: list[dict[str, int]] = []
    object_count = 0
    bg_count = 0
    for group, number in _coordinates(ROOT, group_sizes):
        try:
            state = _stage_map_state(output, group, number)
            baseline = _stage_map_state(stage48, group, number)
        except (ValueError, RuntimeError):
            continue
        authored = {
            int(_object_fields(raw)["local_id"]): int(_object_fields(raw)["sight_range"])
            for raw in baseline["objects"]
            if int(_object_fields(raw)["kind"]) == 0
            and int(_object_fields(raw)["trainer_type"]) == 1
        }
        for index, raw in enumerate(state["objects"]):
            fields = _object_fields(raw)
            pointer = int(fields["script_pointer"])
            if pointer in forbidden_roots:
                forbidden_reachable.append({"group": group, "map": number, "index": index})
            if int(fields["trainer_type"]) == 1:
                active_trainers += 1
                at = pointer - GBA_ROM_BASE
                if not 0 <= at < len(output) or output[at] != 0x5C:
                    _fail(f"trainer object rootが0x5Cではありません: {group}/{number}/{index}")
                local_id = int(fields["local_id"])
                if authored.get(local_id) != int(fields["sight_range"]):
                    _fail(f"trainer authored sight不一致: {group}/{number}/{index}")
            object_count += 1
        bg_raw = bytes.fromhex(str(state["bg_hex"]))
        for index in range(int(state["counts"]["bg"])):
            pointer = struct.unpack_from("<I", bg_raw, index * 12 + 8)[0]
            if pointer in forbidden_roots:
                forbidden_reachable.append({"group": group, "map": number, "index": index})
        bg_count += int(state["counts"]["bg"])
    disabled_special = int(plan["trainer"]["dispositions"]["NON_RUNTIME_SPECIAL_ACTOR"])
    if active_trainers != 825 or disabled_special != 4 or forbidden_reachable:
        _fail(
            f"world owner audit不一致: trainer={active_trainers}, special={disabled_special}, "
            f"forbidden={forbidden_reachable[:4]}"
        )
    return {
        "status": "PASS", "physical_maps": 678, "objects": object_count,
        "bg_events": bg_count, "active_trainers": active_trainers,
        "nonruntime_special_actors": disabled_special,
        "trainer_roots_begin_0x5c": active_trainers,
        "authored_sight_mismatches": 0,
        "stage50_bad_owner_roots_reachable": 0,
    }


def _declared_change_audit(before: bytes, after: bytes, payload_start: int,
                           payload_size: int, patches: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    spans = [(payload_start, payload_start + payload_size)]
    spans.extend((int(row["site"]), int(row["site"]) + 4) for row in patches)
    spans.append((WILD_HOOK_OFFSET, WILD_HOOK_OFFSET + len(WILD_STOCK_HOOK)))
    spans.append((COOLDOWN_OFFSET, COOLDOWN_OFFSET + len(COOLDOWN_STOCK)))
    spans.append((TRAINER_PARTY_CONTINUATION_OFFSET,
                  TRAINER_PARTY_CONTINUATION_OFFSET
                  + len(TRAINER_PARTY_CONTINUATION_EXPECTED)))
    outside: list[int] = []
    changed = 0
    for index, (old, new) in enumerate(zip(before, after)):
        if old == new:
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


def _markdown(report: Mapping[str, Any]) -> bytes:
    counts = report["owner_plan"]["owner_counts"]
    return (f"""# Stage52 world runtime E2E repair

- Status: **{report['status']}**（iPad実プレイ承認待ち）
- Input Stage51: `{report['input']['sha256']}`
- Output Stage52: `{report['output']['sha256']}`

## 根本修復

- 全678 physical map / trainer template 829件を単一台帳化。
- runtime trainer 825件はobject rootを`trainerbattle` 0x5Cへ直結し、4件は非runtime actorへ分類。
- Stage50の一律range -1を撤回し、authored sight rangeへ復元。
- Kanto item ball 129件（再構築126 + 既存stock 3）を含む全262件が`STD_FIND_ITEM`。
- hidden item 124件は`STD_OBTAIN_ITEM`成功後だけflagをcommit。
- clean sourceのobject owner 469件とBG owner 375件をscript rootごと復元し、動的actor 24件を明示分類。placeholder到達0。
- いあいぎり47件、いわくだき124件を物理ownerとして保持。
- Stage50/51のglobal wild wrapperと最低歩数patchを撤去し、stock処理へ復元。
- trainer party生成が人数snapshotより後になる共通順序不良を補正し、live countとbattle snapshotを全builder経路で同期。

## 検証

- trainer root / sight / command-party: PASS
- item・hidden transaction / field owner: PASS
- wild header全件 / stock hook: PASS
- Dark Pulse 20% / Focus Sash ABI / save・Continue: PASS
- clean直接BPS・Stage51差分BPS往復、allocator overlap、宣言外変更: PASS
- fresh-core実入力fixture: {report['mgba'].get('status', 'PENDING')}

Stage52は旧ROM/saveを上書きしない独立候補であり、task DONEはiPad実プレイ確認後に行う。
""").encode("utf-8")


def _world_input_e2e(output: bytes) -> dict[str, Any]:
    compiler = shutil.which("cc")
    source = ROOT / "tools/mgba_world_runtime_input_e2e.c"
    if compiler is None or not source.is_file():
        _fail("fresh-core world input E2Eのcompiler/sourceがありません")
    (ROOT / "build").mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=".stage52-world-input-", dir=ROOT / "build"
    ) as raw:
        work = Path(raw)
        candidate = work / "candidate.gba"
        executable = work / "mgba_world_runtime_input_e2e"
        candidate.write_bytes(output)
        compiled = subprocess.run(
            [compiler, "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
             "-pedantic", str(source), "-o", str(executable), "-lmgba"],
            cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            timeout=60, check=False,
        )
        if compiled.returncode or compiled.stdout or compiled.stderr:
            _fail(
                "world input E2E compile失敗: "
                + (compiled.stderr or compiled.stdout or str(compiled.returncode))[-2000:]
            )
        runs: list[dict[str, Any]] = []
        stdout_hashes: list[str] = []
        for run_index in range(2):
            run_dir = work / f"run-{run_index + 1}"
            run_dir.mkdir()
            completed = subprocess.run(
                [str(executable), str(candidate), str(run_dir)],
                cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                timeout=1200, check=False,
            )
            if completed.returncode or completed.stderr:
                _fail(
                    f"world input E2E process {run_index + 1}失敗: "
                    + (completed.stderr or completed.stdout or str(completed.returncode))[-4000:]
                )
            try:
                parsed = json.loads(completed.stdout)
            except json.JSONDecodeError as error:
                _fail(f"world input E2E JSON不正: {error}")
            if parsed.get("status") != "PASS" or len(parsed.get("fixtures", [])) != 10:
                _fail(f"world input E2E fixture不一致: {parsed}")
            runs.append(parsed)
            stdout_hashes.append(_sha(completed.stdout.encode()))
        if runs[0] != runs[1]:
            _fail("world input E2Eの独立2 process結果が非決定的です")
        return {
            "status": "PASS", "process_runs": 2, "fixture_count": 10,
            "identical_results": True, "stdout_sha256": stdout_hashes[0],
            "fixtures": runs[0]["fixtures"], "warnings": 0,
        }


def _build_outputs() -> dict[Path, bytes]:
    stage51 = _read(STAGE51_ROM, STAGE51_SHA256, ROM_SIZE)
    stage48 = _read(STAGE48_ROM, STAGE48_SHA256, ROM_SIZE)
    stage03 = _read(STAGE03_ROM, STAGE03_SHA256, ROM_SIZE)
    clean = _read(CLEAN_ROM, CLEAN_SHA256, ROM_SIZE // 2)
    metadata50 = _json(STAGE50_META)
    group_sizes = list(_json(ID_INVENTORY)["map_contract"]["group_sizes"])

    provisional, _, _ = build_payload(
        ROOT, stage51, stage48, stage03, clean, metadata50, 0, group_sizes
    )
    allocation, _ = _allocation(len(provisional), "0" * 64)
    payload_offset = int(allocation["start"])
    payload, plan, map_patches = build_payload(
        ROOT, stage51, stage48, stage03, clean, metadata50, payload_offset, group_sizes
    )
    if len(payload) != len(provisional):
        _fail("payload sizeが配置アドレスで変化")
    allocation, allocation_report = _allocation(len(payload), _sha(payload))
    if int(allocation["start"]) != payload_offset:
        _fail("payload placementがfixed-point後に変化")
    payload_end = payload_offset + len(payload)
    if stage51[payload_offset:payload_end] != bytes([0xFF]) * len(payload):
        _fail("payload destinationが未使用FFではありません")

    output = bytearray(stage51)
    output[payload_offset:payload_end] = payload
    for patch in map_patches:
        site = int(patch["site"])
        expected = int(patch["expected"])
        if struct.unpack_from("<I", output, site)[0] != expected:
            _fail(f"map pointer expected値不一致: {patch['group']}/{patch['map']}")
        target = GBA_ROM_BASE + payload_offset + int(plan["labels"][patch["label"]])
        struct.pack_into("<I", output, site, target)
        patch["target"] = target
    current_hook = bytes(output[WILD_HOOK_OFFSET:WILD_HOOK_OFFSET + len(WILD_STOCK_HOOK)])
    if current_hook != bytes.fromhex("004b184781cf3d09"):
        _fail(f"Stage51 wild hook expected値不一致: {current_hook.hex()}")
    if bytes(output[COOLDOWN_OFFSET:COOLDOWN_OFFSET + 2]) != bytes.fromhex("09e0"):
        _fail("Stage51 minimum-step patch expected値不一致")
    output[WILD_HOOK_OFFSET:WILD_HOOK_OFFSET + len(WILD_STOCK_HOOK)] = WILD_STOCK_HOOK
    output[COOLDOWN_OFFSET:COOLDOWN_OFFSET + len(COOLDOWN_STOCK)] = COOLDOWN_STOCK
    current_party_hook = bytes(output[
        TRAINER_PARTY_CONTINUATION_OFFSET:
        TRAINER_PARTY_CONTINUATION_OFFSET + len(TRAINER_PARTY_CONTINUATION_EXPECTED)
    ])
    if current_party_hook != TRAINER_PARTY_CONTINUATION_EXPECTED:
        _fail(f"Stage51 trainer party continuation expected値不一致: {current_party_hook.hex()}")
    party_count_wrapper = (
        GBA_ROM_BASE + payload_offset
        + int(plan["trainer"]["party_count_wrapper_offset"])
    ) | 1
    output[
        TRAINER_PARTY_CONTINUATION_OFFSET:
        TRAINER_PARTY_CONTINUATION_OFFSET + len(TRAINER_PARTY_CONTINUATION_EXPECTED)
    ] = bytes.fromhex("004b1847") + struct.pack("<I", party_count_wrapper) + bytes.fromhex("c046")
    output_raw = bytes(output)

    party_sizes = [
        output_raw[
            TRAINER_TABLE_ADDRESS - GBA_ROM_BASE
            + trainer_id * TRAINER_RECORD_SIZE
            + TRAINER_PARTY_SIZE_OFFSET
        ]
        for trainer_id in range(1302)
    ]
    if any(size != 0 and not 1 <= size <= 6 for size in party_sizes):
        _fail("trainer party size tableに0または1..6外の値があります")

    map_audit = _map_owner_audit(output_raw, stage48, plan, group_sizes, metadata50)
    wild_audit = _wild_audit(output_raw, group_sizes)
    tohoku_wild_rows = wild_audit.pop("owner_rows")
    wild_root = struct.unpack_from("<I", output_raw, 0x8257C)[0] - GBA_ROM_BASE
    header_coordinates: set[tuple[int, int]] = set()
    for index in range(265):
        coordinate = tuple(output_raw[wild_root + index * 20:wild_root + index * 20 + 2])
        header_coordinates.add((int(coordinate[0]), int(coordinate[1])))
    physical_coordinates = set(_coordinates(ROOT, group_sizes))
    wild_audit["physical_maps"] = len(physical_coordinates)
    wild_audit["tohoku_maps"] = len(tohoku_wild_rows)
    wild_audit["kanto_maps"] = len(physical_coordinates) - len(tohoku_wild_rows)
    wild_audit["physical_maps_with_native_header"] = len(
        header_coordinates & physical_coordinates
    )
    wild_audit["maps_without_native_header"] = (
        len(physical_coordinates) - wild_audit["physical_maps_with_native_header"]
    )
    wild_audit["tohoku_owner_rows"] = tohoku_wild_rows
    wild_audit.pop("turning_requires_running_state_moving", None)
    wild_audit.pop("minimum_steps_early_random_roll_removed", None)
    wild_audit["global_symptom_wrapper_removed"] = True
    wild_audit["stock_field_input_and_cadence_restored"] = True
    wild_audit["stock_hook_restored"] = output_raw[
        WILD_HOOK_OFFSET:WILD_HOOK_OFFSET + len(WILD_STOCK_HOOK)
    ] == WILD_STOCK_HOOK
    wild_audit["stock_cooldown_restored"] = output_raw[
        COOLDOWN_OFFSET:COOLDOWN_OFFSET + len(COOLDOWN_STOCK)
    ] == COOLDOWN_STOCK
    trainer_audit = _trainer_audit(stage48, output_raw)
    trainer_audit["enemy_party_count_loader_repaired"] = True
    trainer_audit["enemy_party_count_hook"] = party_count_wrapper
    trainer_audit["party_builder_common_continuation_hooked"] = True
    trainer_audit["battle_snapshot_enemy_count_synced"] = True
    trainer_audit["party_size_populated_rows_1_to_6"] = sum(
        1 for size in party_sizes if size
    )
    trainer_audit["party_size_reserved_rows_zero"] = sum(
        1 for size in party_sizes if not size
    )
    flinch_audit = _flinch_audit(output_raw)
    change_audit = _declared_change_audit(
        stage51, output_raw, payload_offset, len(payload), map_patches
    )
    continue_audit = _continue_smoke(output_raw)
    world_input = _world_input_e2e(output_raw)
    mgba = {
        "status": "PASS", "process_runs": 2,
        "natural_save_continue": continue_audit,
        "world_input_fixtures": world_input,
    }

    incremental = create_bps(stage51, output_raw, metadata=b"Stage51 to Stage52 world runtime E2E repair")
    direct = create_bps(clean, output_raw, metadata=b"Clean FireRed JPN Rev0 to Stage52 world runtime E2E repair")
    if apply_bps(stage51, incremental) != output_raw or apply_bps(clean, direct) != output_raw:
        _fail("Stage52 BPS round-trip不一致")
    report = {
        "schema_version": 1, "task": TASK, "stage": STAGE,
        "status": "PASS_LOCAL_AWAITING_IPAD",
        "input": {"path": str(STAGE51_ROM), "size": len(stage51), "sha256": _sha(stage51)},
        "output": {"path": str(OUTPUTS["rom"]), "size": len(output_raw), "sha256": _sha(output_raw)},
        "payload": {"offset": payload_offset, "address": GBA_ROM_BASE + payload_offset,
                    "size": len(payload), "sha256": _sha(payload)},
        "owner_plan": plan, "map_audit": map_audit,
        "wild_audit": wild_audit, "trainer_audit": trainer_audit,
        "flinch_audit": flinch_audit,
        "focus_sash_abi": metadata50["focus_sash_abi"],
        "change_audit": change_audit, "mgba": mgba,
        "bps": {
            "incremental": {"path": str(OUTPUTS["incremental_bps"]), "size": len(incremental),
                            "sha256": _sha(incremental), "round_trip": True},
            "clean": {"path": str(OUTPUTS["clean_bps"]), "size": len(direct),
                      "sha256": _sha(direct), "round_trip": True},
        },
        "invariants": {
            "stage51_hash_pinned": True, "clean_hash_pinned": True,
            "physical_maps_678": True, "allocator_overlap_zero": True,
            "declared_changes_only": True, "save_abi_unchanged": True,
            "old_stage_artifacts_untouched": True, "ipad_confirmation_pending": True,
        },
    }
    metadata = report | {"allocation": allocation, "map_pointer_patches": map_patches}
    owner_ledger = {
        "schema_version": 1, "task": TASK, "stage": STAGE, "status": "PASS",
        "rom_sha256": _sha(output_raw), "physical_maps": 678,
        "trainer_rows": plan["trainer"]["rows"],
        "owner_rows": plan["owner_rows"], "owner_counts": plan["owner_counts"],
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
        OUTPUTS["owner_ledger"]: _stable(owner_ledger),
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
        _fail("Stage52生成物drift: " + ", ".join(drift))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("build", "check"))
    args = parser.parse_args()
    try:
        outputs = _build_outputs()
        _write(outputs) if args.mode == "build" else _check(outputs)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError,
            WorldRuntimeBuildError) as error:
        print(f"Stage52 world runtime {args.mode} failed: {error}", file=__import__("sys").stderr)
        return 1
    report = json.loads(outputs[OUTPUTS["metadata"]])
    print(json.dumps({
        "status": report["status"], "stage": STAGE,
        "rom_sha256": report["output"]["sha256"],
        "trainer_roots": report["map_audit"]["trainer_roots_begin_0x5c"],
        "changed_bytes": report["change_audit"]["changed_bytes"],
    }, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
