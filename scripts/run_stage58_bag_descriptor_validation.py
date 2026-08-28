#!/usr/bin/env python3
"""Stage58の全5 Bag descriptorをexact ROM・独立2 processで検証する。"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Mapping, NoReturn, Sequence


ROOT = Path(__file__).resolve().parents[1]
TASK = "USER-20260828-STAGE57-QOL-WORLD-CONVENIENCE-DEBUG"
STAGE = 58
DEFAULT_ROM = ROOT / "build/stages/58_qol_world_convenience_debug.gba"
DEFAULT_METADATA = ROOT / "build/stages/58_qol_world_convenience_debug.json"
DEFAULT_SOURCE = ROOT / "tools/mgba_stage58_bag_descriptor_smoke.c"

PHASE1_KEYS = {
    "natural_field_descriptor_owner",
    "five_pocket_sentinels_seeded",
    "stock_normal_save_persistence_observed",
    "all_five_descriptors_exact_across_lifecycle",
    "all_five_encrypted_quantities_preserved",
    "post_save_irq_no_reset",
    "same_core_bag_reentry",
    "same_core_stock_saveblock_relocation_observed",
    "normal_start_menu_save_persisted",
}
RELOAD_KEYS = {
    "fresh_process_continue",
    "fresh_process_stock_saveblock_relocation_observed",
    "fresh_process_five_descriptors_exact",
    "fresh_process_five_sentinels_exact",
    "fresh_process_same_core_bag_reentry",
    "fresh_process_irq_no_reset",
}
SENTINEL_ITEMS = [19, 48, 2, 289, 133]
SENTINEL_QUANTITIES = [11, 1, 13, 2, 15]
POCKET_OFFSETS = [0x0310, 0x03B8, 0x0430, 0x0464, 0x054C]
POCKET_CAPACITIES = [42, 30, 13, 58, 43]
SAVE_BLOCK1_POINTER = 0x03005048
SAVE_BLOCK2_POINTER = 0x0300504C
BAG_POCKETS = 0x020397D8
SAVE2_ENCRYPTION_KEY_OFFSET = 0x0F20


class BagDescriptorValidationError(RuntimeError):
    """identity、metadata、compile、runtime evidenceのfail-closed違反。"""


def _fail(message: str) -> NoReturn:
    raise BagDescriptorValidationError(message)


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _number(value: Any, label: str) -> int:
    if isinstance(value, bool):
        _fail(f"{label} がboolです")
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value, 0)
        except ValueError:
            pass
    _fail(f"{label} が整数ではありません: {value!r}")


def _read_contract(rom: Path, metadata_path: Path) -> tuple[str, dict[str, Any]]:
    raw = rom.read_bytes()
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    digest = _sha(raw)
    if len(raw) != 32 * 1024 * 1024:
        _fail(f"Stage58 ROM size不一致: {len(raw)}")
    if (
        metadata.get("task") != TASK
        or metadata.get("stage") != STAGE
        or metadata.get("output", {}).get("sha256") != digest
    ):
        _fail("Stage58 ROM/metadata identity不一致")
    contract = metadata.get("saveblock_key_rotation_stock_contract")
    if not isinstance(contract, dict) or contract.get("status") != "PASS":
        _fail("stock Bag key-rotation contract不在")
    descriptors = contract.get("bag_pocket_descriptors")
    expected = [
        ("items", 0x0310, 42),
        ("key_items", 0x03B8, 30),
        ("poke_balls", 0x0430, 13),
        ("tm_case", 0x0464, 58),
        ("berry_pouch", 0x054C, 43),
    ]
    actual: list[tuple[str, int, int]] = []
    if not isinstance(descriptors, list) or len(descriptors) != 5:
        _fail("stock Bag descriptor 5件契約不一致")
    for index, row in enumerate(descriptors):
        if not isinstance(row, dict):
            _fail(f"Bag descriptor[{index}] 型不正")
        actual.append((
            str(row.get("name")),
            _number(row.get("save1_offset"), f"descriptor[{index}].offset"),
            _number(row.get("capacity"), f"descriptor[{index}].capacity"),
        ))
    if actual != expected:
        _fail(f"stock Bag descriptor ABI不一致: {actual!r}")
    if (
        contract.get("policy") != "preserve_stock_no_runtime_rebind"
        or contract.get("stock_callback_restore_preserved") is not True
        or contract.get("stock_apply_all_preserved") is not True
        or contract.get("stock_bag_child_preserved") is not True
        or _number(contract.get("additional_runtime_rebind_count"),
                   "additional_runtime_rebind_count") != 0
        or contract.get("host_rebind_after_field_return_forbidden") is not True
        or _number(contract.get("save_block1_pointer"),
                   "save_block1_pointer") != SAVE_BLOCK1_POINTER
        or _number(contract.get("save_block2_pointer"),
                   "save_block2_pointer") != SAVE_BLOCK2_POINTER
        or _number(contract.get("bag_pockets"),
                   "bag_pockets") != BAG_POCKETS
        or _number(contract.get("descriptor_stride"),
                   "descriptor_stride") != 8
        or _number(contract.get("descriptor_count"),
                   "descriptor_count") != 5
    ):
        _fail("stock Bag lifecycle意味契約不一致")
    enriched = dict(contract)
    enriched["encryption_key_offset"] = SAVE2_ENCRYPTION_KEY_OFFSET
    enriched["bag_pocket_descriptors"] = descriptors
    return digest, enriched


def _compile(executable: Path) -> None:
    compiler = shutil.which("cc")
    if compiler is None or not DEFAULT_SOURCE.is_file():
        _fail("C compilerまたはBag descriptor source不在")
    completed = subprocess.run(
        [
            compiler,
            "-std=c11",
            "-O2",
            "-Wall",
            "-Wextra",
            "-Werror",
            "-pedantic",
            str(DEFAULT_SOURCE),
            "-o",
            str(executable),
            "-lmgba",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=180,
        check=False,
    )
    if completed.returncode or completed.stdout or completed.stderr:
        _fail(
            "Bag descriptor runner strict compile失敗: "
            + (completed.stderr or completed.stdout or str(completed.returncode))[-6000:]
        )


def _runner_args(
    executable: Path,
    rom: Path,
    save: Path,
    digest: str,
    phase: str,
    contract: Mapping[str, Any],
    previous_save1: int = 0,
    previous_key: int = 0,
    field_callback: int = 0,
) -> list[str]:
    values = [
        _number(contract.get("move_save_blocks_reset_heap"), "move_save_blocks"),
        _number(contract.get("callback_restore_site"), "callback_restore_site"),
        _number(contract.get("apply_all_call_site"), "apply_all_call_site"),
        _number(contract.get("original_apply_new_encryption"), "apply_all"),
        _number(contract.get("bag_encryption_call_site"), "bag_encryption_call_site"),
        _number(contract.get("original_bag_encryption"), "bag_encryption"),
        _number(contract.get("set_bag_pockets_pointers"), "set_bag"),
        _number(contract.get("save_block1_pointer"), "save1_slot"),
        _number(contract.get("save_block2_pointer"), "save2_slot"),
        _number(contract.get("bag_pockets"), "bag_pockets"),
        _number(contract.get("encryption_key_offset"), "key_offset"),
        previous_save1,
        previous_key,
        field_callback,
    ]
    descriptors = contract["bag_pocket_descriptors"]
    for row in descriptors:
        values.extend([
            _number(row["save1_offset"], "descriptor offset"),
            _number(row["capacity"], "descriptor capacity"),
        ])
    return [
        str(executable), str(rom), str(save), digest, phase,
        *(hex(value) for value in values),
    ]


def _pointer_layout_exact(values: Any) -> bool:
    return (
        isinstance(values, list)
        and len(values) == 5
        and all(isinstance(pointer, int) for pointer in values)
        and [pointer - values[0] for pointer in values]
            == [offset - POCKET_OFFSETS[0] for offset in POCKET_OFFSETS]
    )


def _lifecycle_exact(row: Any, key_before: Any, key_after: Any) -> bool:
    if not isinstance(row, dict) or not isinstance(key_before, int) \
            or not isinstance(key_after, int):
        return False
    raw_before = row.get("raw_before")
    raw_after = row.get("raw_after")
    return (
        all(row.get(key) is True for key in (
            "stock_rom_call_graph_exact", "descriptor_before_exact",
            "descriptor_after_exact", "sentinel_before_exact",
            "sentinel_after_exact", "savedata_changed",
        ))
        and row.get("key_before") == key_before
        and row.get("key_after") == key_after
        and isinstance(raw_before, list)
        and isinstance(raw_after, list)
        and len(raw_before) == 5
        and len(raw_after) == 5
        and all(isinstance(raw, int) for raw in raw_before + raw_after)
        and [raw ^ (key_before & 0xFFFF) for raw in raw_before]
            == SENTINEL_QUANTITIES
        and [raw ^ (key_after & 0xFFFF) for raw in raw_after]
            == SENTINEL_QUANTITIES
        and _pointer_layout_exact(row.get("pointer_before"))
        and _pointer_layout_exact(row.get("pointer_after"))
        and row.get("capacity_before") == POCKET_CAPACITIES
        and row.get("capacity_after") == POCKET_CAPACITIES
    )


def _run(command: Sequence[str], phase: str) -> dict[str, Any]:
    completed = subprocess.run(
        list(command),
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=1800,
        check=False,
    )
    if completed.returncode or completed.stderr:
        _fail(
            f"Bag descriptor {phase} process失敗 exit={completed.returncode}: "
            + (completed.stderr or completed.stdout or str(completed.returncode))[-10000:]
        )
    try:
        document = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        _fail(f"Bag descriptor {phase} JSON不正: {error}")
    expected_keys = PHASE1_KEYS if phase == "phase1" else RELOAD_KEYS
    tests = document.get("tests")
    coverage = document.get("coverage")
    evidence = document.get("evidence")
    descriptors = evidence.get("descriptors", []) if isinstance(evidence, dict) else []
    sentinels = evidence.get("sentinels", []) if isinstance(evidence, dict) else []
    lifecycle = evidence.get("stock_lifecycle") if isinstance(evidence, dict) else None
    current_key = evidence.get("current_key") if isinstance(evidence, dict) else None
    if (
        document.get("phase") != phase
        or document.get("status") != "PASS"
        or document.get("warnings_errors") != 0
        or not isinstance(tests, dict)
        or set(tests) != expected_keys
        or not all(value is True for value in tests.values())
        or not isinstance(coverage, dict)
        or coverage.get("bag_pockets") != 5
        or coverage.get("descriptor_pointer_fields") != 5
        or coverage.get("descriptor_capacity_fields") != 5
        or coverage.get("process_contract") != 2
        or coverage.get("stock_save_lifecycles") != (1 if phase == "phase1" else 0)
        or coverage.get("same_core_bag_reentries") != 2
        or not isinstance(evidence, dict)
        or not isinstance(descriptors, list)
        or len(descriptors) != 5
        or [row.get("pocket") for row in descriptors] != list(range(1, 6))
        or not all(
            row.get("exact") is True
            and row.get("actual_pointer") == row.get("expected_pointer")
            and row.get("actual_capacity") == row.get("expected_capacity")
            for row in descriptors
        )
        or not isinstance(sentinels, list)
        or len(sentinels) != 5
        or [row.get("pocket") for row in sentinels] != list(range(1, 6))
        or [row.get("item") for row in sentinels] != SENTINEL_ITEMS
        or [row.get("quantity") for row in sentinels] != SENTINEL_QUANTITIES
        or not all(row.get("exact") is True for row in sentinels)
        or not all(isinstance(row.get("raw"), int) for row in sentinels)
        or not isinstance(current_key, int)
        or [row.get("raw") ^ (current_key & 0xFFFF) for row in sentinels]
            != SENTINEL_QUANTITIES
        or (phase == "phase1" and not isinstance(lifecycle, dict))
        or (phase == "reload" and lifecycle is not None)
    ):
        _fail(f"Bag descriptor {phase} evidence契約不一致: {document!r}")
    if phase == "phase1":
        if not _lifecycle_exact(
            lifecycle, evidence.get("normal_key_before"),
            evidence.get("normal_key_after"),
        ) or (
            evidence.get("current_save1") == lifecycle.get("save1_after")
            and current_key == evidence.get("normal_key_after")
        ):
            _fail(f"stock Bag lifecycle証跡不一致: {lifecycle!r}")
    return document


def run(rom: Path, metadata: Path, save: Path) -> dict[str, Any]:
    digest, contract = _read_contract(rom, metadata)
    with tempfile.TemporaryDirectory(prefix="stage58-bag-descriptor-") as raw:
        executable = Path(raw) / "mgba-stage58-bag-descriptor"
        _compile(executable)
        phase1 = _run(
            _runner_args(executable, rom, save, digest, "phase1", contract),
            "phase1",
        )
        phase1_evidence = phase1["evidence"]
        previous_save1 = _number(
            phase1_evidence.get("current_save1"), "phase1 current_save1",
        )
        previous_key = _number(
            phase1_evidence.get("current_key"), "phase1 current_key",
        )
        field_callback = _number(
            phase1_evidence.get("field_callback"), "phase1 field_callback",
        )
        reload = _run(
            _runner_args(
                executable, rom, save, digest, "reload", contract,
                previous_save1, previous_key, field_callback,
            ),
            "reload",
        )
        reload_evidence = reload["evidence"]
        if (
            reload_evidence.get("expected_previous_save1") != previous_save1
            or reload_evidence.get("expected_previous_key") != previous_key
            or reload_evidence.get("field_callback") != field_callback
            or (
                reload_evidence.get("fresh_entry_save1") == previous_save1
                and reload_evidence.get("fresh_entry_key") == previous_key
            )
        ):
            _fail("fresh process stock SaveBlock relocation証跡不一致")
    return {
        "schema_version": 1,
        "task": TASK,
        "stage": STAGE,
        "status": "PASS",
        "rom_sha256": digest,
        "process_runs": 2,
        "phase1": phase1,
        "reload": reload,
        "limitations": {
            "sentinel_setup_is_host_fixture": True,
            "host_rebind_performed": False,
            "stock_natural_descriptor_binding_observed": True,
            "stock_setbag_call_count_observed": False,
            "normal_start_menu_save": True,
            "fresh_process_reload": True,
            "physical_main_bag_tabs_only": True,
            "tm_case_berry_pouch_quantities_verified_encrypted": True,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", type=Path, default=DEFAULT_ROM)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA)
    parser.add_argument("--save", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    temp: tempfile.TemporaryDirectory[str] | None = None
    if args.save is None:
        temp = tempfile.TemporaryDirectory(prefix="stage58-bag-descriptor-save-")
        save = Path(temp.name) / "descriptor.sav"
    else:
        save = args.save.resolve()
        save.parent.mkdir(parents=True, exist_ok=True)
    try:
        result = run(args.rom.resolve(), args.metadata.resolve(), save)
    finally:
        if temp is not None:
            temp.cleanup()
    encoded = json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if args.output is None:
        sys.stdout.write(encoded)
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BagDescriptorValidationError as error:
        print(f"stage58 bag descriptor validation: {error}", file=sys.stderr)
        raise SystemExit(1)
