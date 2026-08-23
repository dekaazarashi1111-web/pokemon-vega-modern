#!/usr/bin/env python3
"""Stage 28へFactory TrialのACTIVE反復報酬2件を実ROM接続する。"""

from __future__ import annotations

import argparse
import json
import os
import struct
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any, NoReturn, Sequence


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(ROOT))

from scripts import build_factory_reward_runtime as stage28_builder  # noqa: E402
from tools.release.bps import apply_bps  # noqa: E402
from tools.rom_allocator import GBA_ROM_BASE, build_allocation_report_from_csv  # noqa: E402


TASK = "USER-20260818-FACTORY-REPEAT-REWARD-RUNTIME"
ROM_SIZE = 32 * 1024 * 1024
INPUT_ROM = Path("build/stages/28_factory_reward_runtime.gba")
INPUT_META = Path("build/stages/28_factory_reward_runtime.json")
INPUT_ALLOC = Path("build/stages/28_allocation.json")
INPUT_CATALOG = Path("generated/runtime/factory_reward_catalog.json")
BP_SHOP_META = Path("build/stages/27_bp_shop_runtime.json")
BASE_ROM = Path("build/final/vega-modern-kanto-v1.4.0.gba")
OUTPUT_ROM = Path("build/stages/29_factory_repeat_reward_runtime.gba")
OUTPUT_META = Path("build/stages/29_factory_repeat_reward_runtime.json")
OUTPUT_ALLOC = Path("build/stages/29_allocation.json")
RUNTIME_BIN = Path("generated/runtime/factory_repeat_reward_runtime.bin")
RUNTIME_SYMBOLS = Path("generated/runtime/factory_repeat_reward_runtime_symbols.json")
CATALOG_HEADER = Path("generated/runtime/factory_repeat_reward_catalog_generated.h")
CATALOG_JSON = Path("generated/runtime/factory_repeat_reward_catalog.json")
MGBA_FIXTURE = Path("build/stages/29_mgba_factory_repeat_reward_smoke.json")
REPORT = Path("reports/generated/factory_repeat_reward_runtime.md")
PATCH_INCREMENTAL = Path(
    "build/patches/factory-reward-stage28-to-factory-repeat-reward-stage29.bps"
)
PATCH_CUMULATIVE = Path(
    "build/patches/vega-modern-kanto-v1.4.0-to-factory-repeat-reward-stage29.bps"
)
RUNNER = Path("tools/mgba_factory_repeat_reward_smoke.c")

EXPECTED_INPUT_SHA256 = "5e3f34737489824bf13968ee3809957565cf05cd4b530ef68b16f24e1b9770b9"
EXPECTED_BASE_SHA256 = "30f19ee3ebab856379393a572bfde33c2ccfdac7351e73ff3a7f3e231f3f553e"
PAYLOAD_HEADER_SIZE = 0x80
ALLOCATION_NAME = "factory_repeat_reward_runtime_payload"
RANDOM_ADDRESS = 0x0804448D
MANIFEST_KEYS = (
    "FACILITY_REWARD_KEY_TRIAL_REPEAT_BP1",
    "FACILITY_REWARD_KEY_TRIAL_REPEAT_BP2",
)
EXPECTED_ROWS = {
    "FACILITY_REWARD_KEY_TRIAL_REPEAT_BP1": {
        "amount": 1,
        "item_key": "ITEM_KEY_ORAN_BERRY",
        "quantity": 1,
    },
    "FACILITY_REWARD_KEY_TRIAL_REPEAT_BP2": {
        "amount": 2,
        "item_key": "ITEM_KEY_ULTRA_BALL",
        "quantity": 1,
    },
}
REQUIRED_ENTRYPOINTS = {
    "FactoryRepeatRewardRuntime_Probe",
    "FactoryRepeatRewardRuntime_Complete",
}


class FactoryRepeatRewardBuildError(ValueError):
    """入力、manifest、ROM ABI、配置、または受入条件の違反。"""


def _fail(message: str) -> NoReturn:
    raise FactoryRepeatRewardBuildError(message)


def _sha(raw: bytes | bytearray) -> str:
    return stage28_builder._sha(raw)


def _stable(value: object) -> bytes:
    return stage28_builder._stable(value)


def _rows(path: Path) -> list[dict[str, str]]:
    return stage28_builder._rows(path)


def _read_json(path: Path) -> dict[str, Any]:
    return stage28_builder._read_json(path)


def _run(command: Sequence[str], label: str, *, cwd: Path = ROOT) -> str:
    return stage28_builder._run(command, label, cwd=cwd)


def _u32(raw: bytes | bytearray, offset: int, label: str) -> int:
    return stage28_builder._u32(raw, offset, label)


def _rom_offset(address: int, size: int, label: str) -> int:
    return stage28_builder._rom_offset(address, size, label)


def _input_contract(
    root: Path,
) -> tuple[bytes, bytes, dict[str, Any], dict[str, Any], dict[str, Any]]:
    stage = (root / INPUT_ROM).read_bytes()
    base = (root / BASE_ROM).read_bytes()
    stage_meta = _read_json(root / INPUT_META)
    previous_alloc = _read_json(root / INPUT_ALLOC)
    stage28_catalog = _read_json(root / INPUT_CATALOG)
    if len(stage) != ROM_SIZE or _sha(stage) != EXPECTED_INPUT_SHA256:
        _fail("stage28 input size or hash differs")
    if len(base) != ROM_SIZE or _sha(base) != EXPECTED_BASE_SHA256:
        _fail("v1.4.0 base size or hash differs")
    if stage_meta.get("task") != "USER-20260818-FACTORY-REWARD-RUNTIME":
        _fail("stage28 metadata task differs")
    if stage_meta.get("output", {}).get("sha256") != EXPECTED_INPUT_SHA256:
        _fail("stage28 metadata output hash differs")
    if previous_alloc.get("summaries", {}).get("overlap_count") != 0:
        _fail("stage28 allocator overlap contract failed")
    old_complete = int(stage_meta.get("entrypoints", {}).get(
        "FactoryRewardRuntime_Complete", 0,
    ))
    script = int(stage_meta.get("completion_chain", {}).get("script", 0))
    script_offset = _rom_offset(script, 6, "Factory completion script")
    if stage[script_offset] != 0x23:
        _fail("Factory completion script no longer starts with callnative")
    if _u32(stage, script_offset + 1, "Stage28 completion pointer") != old_complete:
        _fail("Factory completion script no longer targets Stage28 wrapper")
    linked = stage_meta.get("linked_symbols", {})
    for name in ("VegaFactoryAddBattlePoints", "VegaSaveFinalize", "VegaSaveValidate"):
        address = int(linked.get(name, 0))
        if (address & 1) == 0 or not GBA_ROM_BASE <= (address & ~1) < GBA_ROM_BASE + ROM_SIZE:
            _fail(f"stage28 linked symbol contract differs: {name}=0x{address:08X}")
    if stage28_catalog.get("first_clear", {}).get("claim_mask") != 0x0E:
        _fail("stage28 first-clear claim mask differs")
    return stage, base, stage_meta, previous_alloc, stage28_catalog


def _catalog_outputs(
    root: Path, stage28_catalog: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], bytes, bytes]:
    if stage28_catalog is None:
        stage28_catalog = _read_json(root / INPUT_CATALOG)
    reward_rows = _rows(root / "manifests/facility_rewards.csv")
    selected = {
        row["facility_reward_key"]: row
        for row in reward_rows
        if row.get("facility_reward_key") in MANIFEST_KEYS
    }
    if set(selected) != set(MANIFEST_KEYS):
        _fail("Factory repeat reward manifest key set differs")
    item_rows = {row["item_key"]: row for row in _rows(root / "manifests/item_ids.csv")}
    required_mask = int(stage28_catalog.get("first_clear", {}).get("claim_mask", -1))
    if required_mask != 0x0E:
        _fail("Factory repeat required claim mask differs")

    rewards: list[dict[str, Any]] = []
    for key in MANIFEST_KEYS:
        row = selected[key]
        expected = EXPECTED_ROWS[key]
        if (
            row.get("status") != "ACTIVE"
            or row.get("trigger_kind") != "TRIAL_REPEAT"
            or int(row.get("streak") or "0", 0) != 0
            or row.get("currency_key") != "CURRENCY_KEY_BP"
            or int(row.get("amount") or "0", 0) != expected["amount"]
            or row.get("item_key") != expected["item_key"]
            or int(row.get("quantity") or "0", 0) != expected["quantity"]
            or row.get("unlock_key") != "KANTO_EARLY_ACCESS"
            or row.get("repeatability") != "REPEATABLE"
            or row.get("claim_key") != "NONE"
        ):
            _fail(f"Factory repeat reward semantics differ: {key}")
        try:
            item_id = int(item_rows[row["item_key"]]["id"], 0)
        except (KeyError, ValueError) as error:
            _fail(f"Factory repeat item binding differs: {key}: {error}")
        rewards.append({
            "facility_reward_key": key,
            "item_key": row["item_key"],
            "item_id": item_id,
            "quantity": int(row["quantity"], 0),
            "battle_points": int(row["amount"], 0),
            "unlock_key": row["unlock_key"],
            "repeatability": row["repeatability"],
        })

    item_ids = ", ".join(f"{row['item_id']}u" for row in rewards)
    quantities = ", ".join(f"{row['quantity']}u" for row in rewards)
    points = ", ".join(f"{row['battle_points']}u" for row in rewards)
    header = f"""#ifndef VEGA_FACTORY_REPEAT_REWARD_CATALOG_GENERATED_H
#define VEGA_FACTORY_REPEAT_REWARD_CATALOG_GENERATED_H

#include <stdint.h>

#define FACTORY_REPEAT_REWARD_COUNT {len(rewards)}u
#define FACTORY_REPEAT_REWARD_REQUIRED_CLAIM_MASK 0x{required_mask:02X}u

static const uint16_t gFactoryRepeatRewardItemIds[FACTORY_REPEAT_REWARD_COUNT] = {{
    {item_ids}
}};
static const uint16_t gFactoryRepeatRewardItemQuantities[FACTORY_REPEAT_REWARD_COUNT] = {{
    {quantities}
}};
static const uint16_t gFactoryRepeatRewardBattlePoints[FACTORY_REPEAT_REWARD_COUNT] = {{
    {points}
}};

#endif /* VEGA_FACTORY_REPEAT_REWARD_CATALOG_GENERATED_H */
""".encode("ascii")
    catalog = {
        "schema_version": 1,
        "task": TASK,
        "status": "PASS",
        "source": [
            "manifests/facility_rewards.csv",
            "manifests/item_ids.csv",
            INPUT_CATALOG.as_posix(),
        ],
        "selected_keys": list(MANIFEST_KEYS),
        "required_first_claim_mask": required_mask,
        "selection": "stock Random() modulo repeat reward count",
        "rewards": rewards,
        "header_sha256": _sha(header),
    }
    return catalog, header, _stable(catalog)


def _compile_runtime(
    root: Path,
    load_address: int,
    generated_header: bytes,
    stage28_meta: dict[str, Any],
) -> tuple[bytes, dict[str, int]]:
    compiler = stage28_builder._arm_tool(root, "arm-none-eabi-gcc")
    objcopy = stage28_builder._arm_tool(root, "arm-none-eabi-objcopy")
    nm = stage28_builder._arm_tool(root, "arm-none-eabi-nm")
    source = root / "overlays/factory_repeat_reward_runtime/factory_repeat_reward_runtime.c"
    if not source.is_file():
        _fail(f"Factory repeat reward source missing: {source}")
    old_complete = int(stage28_meta["entrypoints"]["FactoryRewardRuntime_Complete"])
    linked = stage28_meta["linked_symbols"]
    with tempfile.TemporaryDirectory(prefix="vega-factory-repeat-reward-") as temporary:
        directory = Path(temporary)
        (directory / "factory_repeat_reward_catalog_generated.h").write_bytes(generated_header)
        common = [
            compiler, "-mthumb", "-mcpu=arm7tdmi", "-mthumb-interwork",
            "-Os", "-std=c11", "-Wall", "-Wextra", "-Werror",
            "-ffreestanding", "-fno-builtin", "-fno-unwind-tables",
            "-fno-asynchronous-unwind-tables", "-fdata-sections",
            "-ffunction-sections", "-fno-common",
            f"-DVEGA_FACTORY_REWARD_COMPLETE_ADDRESS=0x{old_complete:08X}u",
            f"-DVEGA_FACTORY_ADD_BP_ADDRESS=0x{int(linked['VegaFactoryAddBattlePoints']):08X}u",
            f"-DVEGA_SAVE_FINALIZE_ADDRESS=0x{int(linked['VegaSaveFinalize']):08X}u",
            f"-DVEGA_SAVE_VALIDATE_ADDRESS=0x{int(linked['VegaSaveValidate']):08X}u",
            f"-I{directory}", f"-I{root}",
            f"-I{root / 'overlays/factory_repeat_reward_runtime'}",
            f"-I{root / 'overlays/save_migration'}",
        ]
        obj = directory / "factory_repeat_reward_runtime.o"
        _run([*common, "-c", str(source), "-o", str(obj)], "compile Factory repeat reward")
        linker = directory / "linker.ld"
        linker.write_text(
            "SECTIONS\n{\n"
            f"  . = 0x{load_address:08X};\n"
            "  .text : {\n"
            "    KEEP(*(.text.FactoryRepeatRewardRuntime_*))\n"
            "    *(.text*) *(.rodata*) *(.data*)\n"
            "  }\n"
            "  .bss (NOLOAD) : { *(.bss*) *(COMMON) }\n"
            "  /DISCARD/ : { *(.comment*) *(.ARM.attributes*) *(.note*) "
            "*(.ARM.exidx*) *(.ARM.extab*) }\n"
            "}\n",
            encoding="ascii",
        )
        elf = directory / "factory_repeat_reward.elf"
        binary = directory / "factory_repeat_reward.bin"
        _run([
            compiler, "-mthumb", "-mcpu=arm7tdmi", "-mthumb-interwork",
            "-nostdlib", "-Wl,--build-id=none", "-Wl,--gc-sections",
            "-Wl,-e,FactoryRepeatRewardRuntime_Probe", f"-Wl,-T,{linker}",
            str(obj), "-lgcc", "-o", str(elf),
        ], "link Factory repeat reward")
        undefined = _run([nm, "-u", str(elf)], "Factory repeat reward undefined-symbol audit")
        if undefined:
            _fail("Factory repeat reward has undefined symbols: " + undefined)
        _run([objcopy, "-O", "binary", str(elf), str(binary)], "Factory repeat reward objcopy")
        symbols: dict[str, int] = {}
        for line in _run([nm, "-n", "--defined-only", str(elf)], "Factory repeat reward nm").splitlines():
            fields = line.split()
            if len(fields) == 3:
                try:
                    symbols[fields[2]] = int(fields[0], 16)
                except ValueError:
                    pass
        missing = sorted(REQUIRED_ENTRYPOINTS - set(symbols))
        if missing:
            _fail(f"Factory repeat reward exports differ: missing={missing}")
        code = binary.read_bytes()
        if not code or len(code) > 16 * 1024:
            _fail(f"unexpected Factory repeat reward size: {len(code)}")
        for name in REQUIRED_ENTRYPOINTS:
            address = symbols[name]
            if address & 1 or not load_address <= address < load_address + len(code):
                _fail(f"Factory repeat reward symbol outside/alignment: {name}=0x{address:08X}")
        return code, symbols


def _build_payload(
    root: Path,
    generated_header: bytes,
    payload_offset: int,
    stage28_meta: dict[str, Any],
    catalog: dict[str, Any],
) -> tuple[bytes, dict[str, Any]]:
    code_address = GBA_ROM_BASE + payload_offset + PAYLOAD_HEADER_SIZE
    code, symbols = _compile_runtime(root, code_address, generated_header, stage28_meta)
    payload = bytearray(PAYLOAD_HEADER_SIZE + len(code))
    payload[PAYLOAD_HEADER_SIZE:] = code
    entrypoints = {name: symbols[name] | 1 for name in sorted(REQUIRED_ENTRYPOINTS)}
    old_complete = int(stage28_meta["entrypoints"]["FactoryRewardRuntime_Complete"])
    linked = stage28_meta["linked_symbols"]
    struct.pack_into(
        "<8sIIIIIIIIIII",
        payload,
        0,
        b"VEGARR29",
        1,
        len(payload),
        len(code),
        len(catalog["rewards"]),
        int(catalog["required_first_claim_mask"]),
        old_complete,
        entrypoints["FactoryRepeatRewardRuntime_Probe"],
        entrypoints["FactoryRepeatRewardRuntime_Complete"],
        RANDOM_ADDRESS,
        int(linked["VegaFactoryAddBattlePoints"]),
        0,
    )
    return bytes(payload), {
        "payload": {
            "magic": "VEGARR29",
            "offset": payload_offset,
            "address": GBA_ROM_BASE + payload_offset,
            "size": len(payload),
            "sha256": _sha(payload),
            "header_size": PAYLOAD_HEADER_SIZE,
            "code_offset": payload_offset + PAYLOAD_HEADER_SIZE,
            "code_address": code_address,
            "code_size": len(code),
            "code_sha256": _sha(code),
        },
        "entrypoints": entrypoints,
        "symbols": {
            f"native::{name}": symbols[name]
            for name in sorted(symbols)
            if code_address <= symbols[name] < code_address + len(code)
        },
    }


def _allocation(
    root: Path,
    previous: dict[str, Any],
    size: int,
    digest: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    requests = stage28_builder._previous_requests(previous)
    requests.append({
        "name": ALLOCATION_NAME,
        "region": "integration_modules",
        "size": size,
        "alignment": 16,
        "owner": TASK,
        "purpose": "Factory Trial repeat item/BP reward wrapper",
        "content_sha256": digest,
    })
    report = build_allocation_report_from_csv(root / "config/rom_regions.csv", requests)
    if report.get("summaries", {}).get("overlap_count") != 0:
        _fail("stage29 allocator overlap detected")
    matches = [row for row in report["allocations"] if row["name"] == ALLOCATION_NAME]
    if len(matches) != 1:
        _fail("Factory repeat reward allocation is not unique")
    return matches[0], report


def build_runtime_outputs(root: Path = ROOT) -> dict[str, bytes]:
    root = Path(root)
    stage, base, stage28_meta, previous_alloc, stage28_catalog = _input_contract(root)
    catalog, generated_header, catalog_json = _catalog_outputs(root, stage28_catalog)
    script_address = int(stage28_meta["completion_chain"]["script"])
    script_offset = _rom_offset(script_address, 6, "Factory completion script")
    old_complete = int(stage28_meta["entrypoints"]["FactoryRewardRuntime_Complete"])

    preliminary, _ = _build_payload(root, generated_header, 0, stage28_meta, catalog)
    allocation, _ = _allocation(root, previous_alloc, len(preliminary), "0" * 64)
    payload_offset = int(allocation["start"])
    payload, runtime = _build_payload(
        root, generated_header, payload_offset, stage28_meta, catalog,
    )
    if len(payload) != len(preliminary):
        _fail("address-dependent Factory repeat reward payload size changed")
    allocation, allocation_report = _allocation(
        root, previous_alloc, len(payload), _sha(payload),
    )
    if int(allocation["start"]) != payload_offset:
        _fail("Factory repeat reward allocation changed after final link")
    payload_end = int(allocation["end_exclusive"])
    if stage[payload_offset:payload_end] != b"\xFF" * len(payload):
        _fail("Factory repeat reward destination is not erased FF")

    output = bytearray(stage)
    output[payload_offset:payload_end] = payload
    pointer_site = script_offset + 1
    expected = _u32(output, pointer_site, "Stage28 Factory reward pointer")
    if expected != old_complete:
        _fail(f"Stage28 Factory reward pointer differs: 0x{expected:08X}")
    replacement = int(runtime["entrypoints"]["FactoryRepeatRewardRuntime_Complete"])
    struct.pack_into("<I", output, pointer_site, replacement)
    patch = {
        "label": "Factory Trial completion Stage29 repeat reward wrapper",
        "script_address": script_address,
        "script_offset": script_offset,
        "site_address": GBA_ROM_BASE + pointer_site,
        "site_offset": pointer_site,
        "opcode": 0x23,
        "expected_pointer": old_complete,
        "replacement_pointer": replacement,
    }

    allowed = [(payload_offset, payload_end), (pointer_site, pointer_site + 4)]
    changed = [index for index, (before, after) in enumerate(zip(stage, output)) if before != after]
    outside = [
        index for index in changed
        if not any(start <= index < end for start, end in allowed)
    ]
    if outside:
        _fail(f"stage29 changed bytes outside declared spans: {outside[:8]}")
    output_raw = bytes(output)
    incremental = stage28_builder._sparse_bps(stage, output_raw)
    cumulative = stage28_builder._sparse_bps(base, output_raw)
    if apply_bps(stage, incremental) != output_raw:
        _fail("stage28 to stage29 BPS round-trip differs")
    if apply_bps(base, cumulative) != output_raw:
        _fail("v1.4.0 to stage29 cumulative BPS round-trip differs")

    ram = stage28_builder._ram_audit(root)
    metadata: dict[str, Any] = {
        "schema_version": 1,
        "task": TASK,
        "status": "PASS",
        "input": {
            "path": INPUT_ROM.as_posix(),
            "size": len(stage),
            "sha256": _sha(stage),
            "upstream_task": stage28_meta.get("task"),
        },
        "base_release": {
            "path": BASE_ROM.as_posix(),
            "size": len(base),
            "sha256": _sha(base),
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
            "selected_row_count": len(catalog["rewards"]),
            "required_first_claim_mask": catalog["required_first_claim_mask"],
            "selection": catalog["selection"],
            "rewards": catalog["rewards"],
        },
        "patches": [patch],
        "completion_chain": {
            "script": script_address,
            "stage20_complete": int(stage28_meta["completion_chain"]["old_complete"]),
            "stage28_complete": old_complete,
            "stage29_complete": replacement,
            "order": [
                "capture Stage28 first-clear claim eligibility",
                "FactoryRewardRuntime_Complete",
                "on result 9 and pre-existing first claims: apply one TRIAL_REPEAT row",
            ],
            "base_result_preserved": 9,
            "stage28_ownership": [
                "party restore", "current/best streak", "base 9 BP",
                "first-clear rewards", "streak credits", "sector31 persistence",
            ],
        },
        "transaction": {
            "order": [
                "select one row with stock Random()",
                "snapshot exact post-Stage28 ledger",
                "AddBagItem selected item x1",
                "increment Factory transaction_id",
                "VegaFactoryAddBattlePoints selected +1/+2",
                "TrySavingData(0)",
                "TryWriteSector(31)",
            ],
            "first_clear_behavior": "not eligible because first-clear claim mask was incomplete before Stage28 completion",
            "bag_full_behavior": "Stage28 completion remains committed; repeat item/BP are skipped together",
            "compensation": "save failure restores exact post-Stage28 ledger snapshot, removes selected item, and best-effort rewrites both stores",
            "rollback_storage": "gVegaSaveRollbackData (sequential reuse after Stage28 returns)",
        },
        "random_binding": {
            "function": "Random",
            "address": RANDOM_ADDRESS,
            "state_address": 0x03005040,
            "selection_count": len(catalog["rewards"]),
        },
        "ram_audit": ram,
        "allocation": {
            "path": OUTPUT_ALLOC.as_posix(),
            "name": ALLOCATION_NAME,
            "overlap_count": allocation_report["summaries"]["overlap_count"],
            "remaining_allocatable_bytes": allocation_report["summaries"]["remaining_allocatable_bytes"],
        },
        "release_patches": {
            "incremental": {
                "path": PATCH_INCREMENTAL.as_posix(),
                "source_sha256": _sha(stage),
                "target_sha256": _sha(output_raw),
                "size": len(incremental),
                "sha256": _sha(incremental),
                "exact": True,
            },
            "cumulative": {
                "path": PATCH_CUMULATIVE.as_posix(),
                "source_sha256": _sha(base),
                "target_sha256": _sha(output_raw),
                "size": len(cumulative),
                "sha256": _sha(cumulative),
                "exact": True,
            },
        },
        "change_audit": {
            "changed_byte_count": len(changed),
            "declared_spans": [
                {"start": payload_offset, "end_exclusive": payload_end, "kind": "payload"},
                {"start": pointer_site, "end_exclusive": pointer_site + 4, "kind": "callnative pointer"},
            ],
            "outside_declared_span_count": 0,
        },
        "invariants": {
            "input_stage28_hash_pinned": _sha(stage) == EXPECTED_INPUT_SHA256,
            "base_v1_4_0_hash_pinned": _sha(base) == EXPECTED_BASE_SHA256,
            "rom_size_32_mib": len(output_raw) == ROM_SIZE,
            "manifest_selected_rows_2": len(catalog["rewards"]) == 2,
            "repeat_rewards_1_and_2_bp": [row["battle_points"] for row in catalog["rewards"]] == [1, 2],
            "repeat_items_oran_ultra": [row["item_id"] for row in catalog["rewards"]] == [432, 2],
            "first_claim_mask_0x0e": catalog["required_first_claim_mask"] == 0x0E,
            "completion_wrapper_physically_bound": _u32(output_raw, pointer_site, "Stage29 wrapper pointer") == replacement,
            "stage28_complete_called_first": True,
            "allocator_overlap_zero": allocation_report["summaries"]["overlap_count"] == 0,
            "ram_overlap_zero": ram["overlap_count"] == 0,
            "declared_changes_only": not outside,
            "incremental_bps_exact": True,
            "cumulative_bps_exact": True,
        },
    }
    if not all(metadata["invariants"].values()):
        _fail("Factory repeat reward runtime invariant failed")
    symbols_doc = {
        "schema_version": 1,
        "task": TASK,
        "payload": runtime["payload"],
        "entrypoints": runtime["entrypoints"],
        "symbols": runtime["symbols"],
        "completion_chain": metadata["completion_chain"],
        "random_binding": metadata["random_binding"],
    }
    return {
        OUTPUT_ROM.as_posix(): output_raw,
        OUTPUT_META.as_posix(): _stable(metadata),
        OUTPUT_ALLOC.as_posix(): _stable(allocation_report),
        RUNTIME_BIN.as_posix(): payload,
        RUNTIME_SYMBOLS.as_posix(): _stable(symbols_doc),
        CATALOG_HEADER.as_posix(): generated_header,
        CATALOG_JSON.as_posix(): catalog_json,
        PATCH_INCREMENTAL.as_posix(): incremental,
        PATCH_CUMULATIVE.as_posix(): cumulative,
    }


def _mgba_fixture(root: Path, stage: bytes, metadata: dict[str, Any]) -> dict[str, Any]:
    runner = root / RUNNER
    if not runner.is_file():
        _fail(f"Factory repeat reward mGBA runner missing: {runner}")
    with tempfile.TemporaryDirectory(prefix="vega-factory-repeat-reward-smoke-") as temporary:
        temp = Path(temporary)
        executable = temp / "mgba-factory-repeat-reward-smoke"
        _run([
            stage28_builder._host_cc(root), "-std=c11", "-Wall", "-Wextra", "-Werror",
            str(RUNNER), "-o", str(executable), "-lmgba",
        ], "Factory repeat reward libmGBA smoke compile", cwd=root)
        entry = metadata["entrypoints"]
        stage28_meta = _read_json(root / INPUT_META)
        ensure = _read_json(root / BP_SHOP_META)["entrypoints"]["BpShop_EnsureSave"]
        common_args = [
            hex(entry["FactoryRepeatRewardRuntime_Probe"]),
            hex(entry["FactoryRepeatRewardRuntime_Complete"]),
            hex(stage28_meta["linked_symbols"]["VegaSaveFinalize"]),
            hex(ensure),
            hex(metadata["completion_chain"]["script"]),
            hex(metadata["completion_chain"]["stage28_complete"]),
        ]
        processes: list[tuple[subprocess.Popen[str], Path, Path]] = []
        for index in (1, 2):
            rom = temp / f"29_factory_repeat_reward_run{index}.gba"
            save = temp / f"29_factory_repeat_reward_run{index}.sav"
            rom.write_bytes(stage)
            process = subprocess.Popen(
                [str(executable), str(rom), str(save), *common_args],
                cwd=root, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            )
            processes.append((process, rom, save))
            if index == 1:
                # Avoid making both isolated cores enter flash I/O on the same
                # host scheduler tick while retaining a sub-30-second gate.
                time.sleep(1.0)
        payloads: list[str] = []
        for index, (process, _rom, _save) in enumerate(processes, start=1):
            try:
                stdout, stderr = process.communicate(timeout=90)
            except subprocess.TimeoutExpired as error:
                for pending, _, _ in processes:
                    if pending.poll() is None:
                        pending.kill()
                for pending, _, _ in processes:
                    pending.communicate()
                detail = ((error.stderr or error.stdout) or "").strip()
                _fail(f"Factory repeat reward exact-ROM run {index} timed out: {detail}")
            if process.returncode:
                for pending, _, _ in processes:
                    if pending.poll() is None:
                        pending.kill()
                for pending, _, _ in processes:
                    if pending is not process:
                        pending.communicate()
                detail = (stderr or stdout).strip()
                _fail(
                    f"Factory repeat reward exact-ROM run {index} failed "
                    f"({process.returncode}): {detail}"
                )
            payloads.append(stdout.strip())
        first, second = (json.loads(payload) for payload in payloads)
        if first != second or first.get("status") != "PASS":
            _fail("Factory repeat reward exact-ROM smoke is not deterministic PASS")
        first["process_runs"] = 2
        first["rom_sha256"] = _sha(stage)
        return first


def _report(metadata: dict[str, Any], mgba: dict[str, Any]) -> bytes:
    checks = mgba["checks"]
    rewards = metadata["catalog"]["rewards"]
    text = f"""# Factory Trial repeat reward runtime / Stage 29

## 結論

- Stage 28の`FactoryRewardRuntime_Complete`を先に呼ぶwrapperを、Factory Trial完了scriptへ物理接続した。
- 初回報酬claimが呼出前から完了している成功完走だけを反復対象にしたため、初回報酬と反復報酬は混在しない。
- ACTIVE `TRIAL_REPEAT` 2行をstock `Random()`で抽選し、`{rewards[0]['item_key']}`×1＋{rewards[0]['battle_points']} BP、`{rewards[1]['item_key']}`×1＋{rewards[1]['battle_points']} BPを接続した。
- itemと追加BPは同一補償transactionで、bag満杯時もStage 28の基本9 BP、party復元、連勝・creditを取り消さない。

## ROM結合

- Input: `{metadata['input']['path']}` / `{metadata['input']['sha256']}`
- Output: `{metadata['output']['path']}` / `{metadata['output']['sha256']}`
- Payload: `{metadata['payload']['address']:#010x}` / {metadata['payload']['size']} bytes
- Completion script: `{metadata['completion_chain']['script']:#010x}`
- Stage 28 complete: `{metadata['completion_chain']['stage28_complete']:#010x}`
- Stage 29 complete: `{metadata['completion_chain']['stage29_complete']:#010x}`
- Allocator overlap: {metadata['allocation']['overlap_count']}
- Declared span外変更: {metadata['change_audit']['outside_declared_span_count']}
- Incremental/cumulative BPS exact: {metadata['release_patches']['incremental']['exact']} / {metadata['release_patches']['cumulative']['exact']}

## focused exact-ROM smoke

- completion callnative binding: {checks['completion_wrapper_binding']}
- ABI probe / save initialization: {checks['probe_and_save_init']}
- first clear excludes repeat reward: {checks['first_clear_excludes_repeat']}
- +1 BP / Oran branch: {checks['repeat_oran_branch']}
- +2 BP / Ultra Ball branch: {checks['repeat_ultra_branch']}
- streak credit coexistence: {checks['streak_credit_coexistence']}
- bag-full keeps Stage 28 base completion: {checks['bag_full_base_preserved']}
- normal save item reload: {checks['normal_save_item_reload']}
- sector31 ledger match: {checks['sector31_ledger_match']}
- exact party restore: {checks['exact_party_restore']}
- deterministic process runs: {mgba['process_runs']}

ユーザー指示どおりfresh全監査は再実行せず、Stage 29 builder、manifest binding、allocator、変更span、BPS往復、libmGBA exact-ROM smokeに限定して検証した。
"""
    return text.encode("utf-8")


def _validate_mgba_result(mgba: dict[str, Any], stage: bytes) -> None:
    expected_checks = {
        "completion_wrapper_binding",
        "probe_and_save_init",
        "first_clear_excludes_repeat",
        "repeat_oran_branch",
        "repeat_ultra_branch",
        "streak_credit_coexistence",
        "bag_full_base_preserved",
        "normal_save_item_reload",
        "sector31_ledger_match",
        "exact_party_restore",
    }
    expected_metrics = {
        "first_clear_bp": 112,
        "oran_repeat_bp": 122,
        "ultra_repeat_bp": 133,
        "streak_repeat_bp": 143,
        "bag_full_base_bp": 209,
    }
    checks = mgba.get("checks")
    if (
        mgba.get("schema_version") != 1
        or mgba.get("status") != "PASS"
        or mgba.get("process_runs") != 2
        or mgba.get("rom_sha256") != _sha(stage)
        or not isinstance(checks, dict)
        or set(checks) != expected_checks
        or not all(checks.values())
        or any(mgba.get(key) != value for key, value in expected_metrics.items())
        or mgba.get("artifacts_written") != []
    ):
        _fail("Factory repeat reward exact-ROM fixture contract differs")


def collect_outputs(
    root: Path = ROOT, *, run_exact: bool = True,
) -> dict[str, bytes]:
    outputs = build_runtime_outputs(root)
    repeated = build_runtime_outputs(root)
    if outputs != repeated:
        _fail("Factory repeat reward runtime build is not byte deterministic")
    stage = outputs[OUTPUT_ROM.as_posix()]
    metadata = json.loads(outputs[OUTPUT_META.as_posix()])
    if run_exact:
        mgba = _mgba_fixture(root, stage, metadata)
    else:
        fixture_path = Path(root) / MGBA_FIXTURE
        if not fixture_path.is_file():
            _fail("Factory repeat reward exact-ROM fixture is missing; run build first")
        mgba = _read_json(fixture_path)
    _validate_mgba_result(mgba, stage)
    metadata["exact_rom_fixture"] = {
        "path": MGBA_FIXTURE.as_posix(),
        "status": mgba["status"],
        "process_runs": mgba["process_runs"],
        "all_checks": all(mgba["checks"].values()),
    }
    metadata["invariants"]["exact_rom_process_runs_2"] = mgba["process_runs"] == 2
    metadata["invariants"]["exact_rom_all_checks"] = all(mgba["checks"].values())
    if not all(metadata["invariants"].values()):
        _fail("Factory repeat reward exact-ROM invariant failed")
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
        _fail("Factory repeat reward generated outputs differ: " + ", ".join(differences))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("build", "check"))
    args = parser.parse_args()
    try:
        outputs = collect_outputs(ROOT, run_exact=args.mode == "build")
        if args.mode == "build":
            _write_outputs(ROOT, outputs)
        else:
            _check_outputs(ROOT, outputs)
    except (OSError, ValueError, KeyError, json.JSONDecodeError, FactoryRepeatRewardBuildError) as error:
        print(f"Factory repeat reward runtime build failed: {error}", file=__import__("sys").stderr)
        return 1
    print(
        f"Factory repeat reward runtime {args.mode}: PASS "
        f"stage={_sha(outputs[OUTPUT_ROM.as_posix()])} artifacts={len(outputs)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
