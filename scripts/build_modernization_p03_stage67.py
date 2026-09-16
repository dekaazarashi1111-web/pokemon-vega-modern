#!/usr/bin/env python3
"""Stage66+P02 overlayを親にP03 Stage67 consumer checkpointを生成する。"""

from __future__ import annotations

import argparse
import json
import os
import struct
import sys
import tempfile
import zlib
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_trainer_v5_stage32 import _sparse_bps  # noqa: E402
from scripts.run_modernization_p03_stage67_mgba import (  # noqa: E402
    ModernizationP03Stage67MgbaError,
    validate_published_gate,
)
from tools.modernization_p03_stage67 import (  # noqa: E402
    ModernizationP03Stage67Error,
    build_stage67_image,
    fixed_input,
    read_config,
    sha256,
    stable_json,
)
from tools.release.bps import apply_bps, create_bps  # noqa: E402


DEFAULT_CONFIG = Path("config/modernization_p03_stage67.json")
TASK = "USER-MODERNIZATION-P03-STAGE67-CONSUMER-CHECKPOINT"
STAGE = 67


def _identity(path: str, raw: bytes, **extra: Any) -> dict[str, Any]:
    return {"path": path, "size": len(raw), "sha256": sha256(raw), **extra}


def build_outputs(config_path: Path = DEFAULT_CONFIG) -> dict[str, bytes]:
    built = build_stage67_image(ROOT, config_path)
    config = built.config
    inputs = config["inputs"]
    outputs = config["outputs"]
    output = built.rom
    parent = built.parent
    clean = fixed_input(
        ROOT, inputs["clean_rom"], "clean FireRed JPN Rev0 ROM", allow_symlink=True,
    )
    gate = validate_published_gate(config_path, stage67_bytes=output, built=built)
    gate_raw = (ROOT / outputs["mgba_evidence"]).read_bytes()

    incremental = _sparse_bps(parent, output)
    clean_bps = create_bps(
        clean,
        output,
        metadata=(
            b"Clean FireRed JPN Rev0 to Stage67 cumulative P02 acceptance "
            b"and P03 consumer checkpoint"
        ),
    )
    if apply_bps(parent, incremental) != output:
        raise ModernizationP03Stage67Error(
            "P02 overlay parent→Stage67 incremental BPS round-trip不一致"
        )
    if apply_bps(clean, clean_bps) != output:
        raise ModernizationP03Stage67Error("clean→Stage67 direct BPS round-trip不一致")

    route_raw = stable_json(built.route_audit)
    change_raw = stable_json(built.change_audit)
    allocation_raw = stable_json(built.allocation)
    output_identity = _identity(
        outputs["rom"], output, crc32=f"{zlib.crc32(output) & 0xFFFFFFFF:08X}",
    )
    parent_identity = {
        "classification": "IN_MEMORY_P02_OVERLAY_PARENT_FOR_STAGE67",
        "base_stage": 66,
        "size": len(parent),
        "sha256": sha256(parent),
        "stage66_sha256": sha256(built.stage66),
        "p02_overlay_changed_bytes": 60,
    }
    route_identity = _identity(
        outputs["route_audit"], route_raw,
        source_routes=118528,
        selected_routes=118369,
        non_adopted_routes=159,
        new_materialized_routes=3603,
        cumulative_materialized_routes=51151,
        selected_deferred_routes=67218,
    )
    change_identity = _identity(
        outputs["change_audit"], change_raw,
        changed_bytes=built.change_audit["changed_byte_count"],
        changed_spans=built.change_audit["changed_span_count"],
        outside_declared_range_count=0,
        p02_overlay_bytes_preserved=True,
    )
    allocation_identity = _identity(
        outputs["allocation"], allocation_raw,
        inherited_allocations=69,
        added_allocations=2,
        added_bytes=sum(row["size"] for row in built.allocation["allocations"][-2:]),
        allocation_count=built.allocation["summaries"]["allocation_count"],
        overlap_count=built.allocation["summaries"]["overlap_count"],
        remaining_allocatable_bytes=built.allocation["summaries"][
            "remaining_allocatable_bytes"
        ],
    )
    bps = {
        "incremental": _identity(
            outputs["incremental_bps"], incremental,
            source_classification="IN_MEMORY_P02_OVERLAY_PARENT_FOR_STAGE67",
            source_sha256=sha256(parent), target_sha256=sha256(output), round_trip=True,
        ),
        "clean": _identity(
            outputs["clean_bps"], clean_bps,
            source_sha256=sha256(clean), target_sha256=sha256(output), round_trip=True,
        ),
    }
    counts = gate["runtime_result"]["counts"]
    gate_identity = _identity(
        outputs["mgba_evidence"], gate_raw,
        status=gate["status"], classification=gate["classification"],
        process_runs=gate["execution"]["process_runs"],
        evolution_routes=counts["evolution_routes"],
        tutor_positive_routes=counts["tutor_positive_routes"],
        egg_routes=counts["egg_routes"],
    )
    acceptance = {
        "static_contract_gate": "PASS",
        "all_nine_consumer_input_validation_gate": "PASS",
        "p02_overlay_parent_gate": "PASS",
        "parent_preimage_gate": "PASS",
        "allocation_first_fit_gate": "PASS",
        "allocation_overlap_gate": "PASS",
        "evolution_level_zero_consumer_gate": "PASS",
        "existing_slot_tutor_consumer_gate": "PASS",
        "normal_egg_dual_root_consumer_gate": "PASS",
        "pichu_special_breeding_separation_gate": "PASS",
        "deferred_route_accounting_gate": "PASS",
        "move_1063_non_adoption_gate": "PASS",
        "incremental_bps_round_trip": "PASS",
        "clean_bps_round_trip": "PASS",
        "real_consumer_mgba_gate": "PASS",
        "independent_mgba_processes": 2,
        "scheduler_breeding_save_e2e": "NOT_RUN",
        "full_p03_materialization_gate": "PARTIAL_NOT_COMPLETE",
        "task_completion": "CHECKPOINT_NOT_P03_DONE",
    }
    scope = {
        "corrected_targets": 1300,
        "source_routes": 118528,
        "selected_routes": 118369,
        "non_adopted_move_1063_routes": 159,
        "non_adopted_routes_count_as_remaining_runtime_work": False,
        "inherited_stage66_materialized_routes": 47548,
        "stage67_new_materialized_routes": 3603,
        "stage67_new_by_consumer": {"evolution": 341, "tutor": 740, "egg": 2522},
        "cumulative_materialized_routes": 51151,
        "selected_routes_deferred": 67218,
        "deferred_selected_by_consumer": {
            "reminder": 295, "machine": 26279, "tutor": 369, "egg": 41,
            "shared_egg": 5023, "pre_evolution_carry": 35141, "form_change": 70,
        },
        "all_p03_routes_implemented": False,
        "move_1063_implemented_or_replaced": False,
        "species_ids_changed": False,
        "move_ids_changed": False,
        "save_layout_changed": False,
        "existing_party_box_save_rewritten": False,
        "active_play_baseline_changed": False,
        "historical_outputs_overwritten": False,
    }
    remaining = {
        "status": "REQUIRED_BEFORE_P03_DONE",
        "selected_routes": 67218,
        "by_consumer": scope["deferred_selected_by_consumer"],
        "egg_reason_counts": {
            "special_breeding_light_ball": 1,
            "legacy_get_egg_species_alias_collision": 9,
            "incense_union_conflict": 31,
        },
        "move_1063": {
            "routes": 159,
            "status": "NON_ADOPTED_BY_USER_DECISION",
            "replacement": None,
            "counts_as_remaining_runtime_work": False,
        },
        "scheduler_breeding_save_reload_e2e": "NOT_RUN",
        "note_ja": (
            "Stage67は安全に実consumerへ接続できる進化341、既存slot教え技740、"
            "通常タマゴ2522経路を追加したcheckpoint。条件付き・供給不足・専用consumer"
            "未実装の67,218 selected経路と受入E2Eを残すためP03完了ではない。"
        ),
    }
    input_audit = dict(built.input_audit)
    input_audit["clean_rom"] = {
        "path": inputs["clean_rom"]["path"], "size": len(clean), "sha256": sha256(clean),
    }
    input_audit["runtime_gate"] = gate_identity
    common = {
        "schema_version": 1,
        "task": TASK,
        "stage": STAGE,
        "status": "CHECKPOINT",
        "done": False,
        "checkpoint_marker": "CHECKPOINT_NOT_P03_DONE",
        "input": input_audit,
        "parent": parent_identity,
        "output": output_identity,
        "allocation": allocation_identity,
        "route_audit": route_identity,
        "change_audit": change_identity,
        "bps": bps,
        "runtime_gate": gate_identity,
        "acceptance": acceptance,
        "scope": scope,
        "remaining_work": remaining,
    }
    checkpoint = {
        **common,
        "producer_boundary": {
            "generator": "tools/modernization_p03_stage67.py",
            "builder": "scripts/build_modernization_p03_stage67.py",
            "parent_stage": 66,
            "p02_overlay_applied_before_p03_consumer_patch": True,
            "clean_rom_cumulative_generation": True,
            "incremental_parent_generation": True,
            "level_pointer_entries_repointed": 330,
            "tutor_target_rows_replaced": 1300,
            "tutor_catalog_changed": False,
            "egg_primary_and_secondary_roots_repointed": True,
            "egg_scan_limit_updated": True,
            "non_adopted_species_rows_preserved": 321,
        },
    }
    metadata = dict(common)
    return {
        outputs["rom"]: output,
        outputs["metadata"]: stable_json(metadata),
        outputs["allocation"]: allocation_raw,
        outputs["incremental_bps"]: incremental,
        outputs["clean_bps"]: clean_bps,
        outputs["route_audit"]: route_raw,
        outputs["change_audit"]: change_raw,
        outputs["checkpoint"]: stable_json(checkpoint),
    }


def _write_outputs(outputs: Mapping[str, bytes]) -> None:
    for relative, raw in outputs.items():
        path = ROOT / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            dir=path.parent, prefix=f".{path.name}.", delete=False,
        ) as stream:
            stream.write(raw)
            temporary = Path(stream.name)
        os.replace(temporary, path)


def _check_outputs(outputs: Mapping[str, bytes]) -> None:
    drift = [
        relative for relative, raw in outputs.items()
        if not (ROOT / relative).is_file() or (ROOT / relative).read_bytes() != raw
    ]
    if drift:
        raise ModernizationP03Stage67Error(
            "Stage67 generated artifact drift: " + ", ".join(drift)
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("build", "check"))
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    args = parser.parse_args(argv)
    try:
        generated = build_outputs(args.config)
        config = read_config(ROOT, args.config)
        if args.mode == "build":
            _write_outputs(generated)
        else:
            _check_outputs(generated)
        metadata = json.loads(generated[config["outputs"]["metadata"]])
    except (
        OSError, KeyError, TypeError, ValueError, struct.error,
        ModernizationP03Stage67Error, ModernizationP03Stage67MgbaError,
    ) as error:
        print(f"P03 Stage67 {args.mode} failed: {error}", file=sys.stderr)
        return 1
    print(
        "P03 Stage67 %s: %s sha256=%s crc32=%s changed=%d new_routes=%d "
        "cumulative_routes=%d runtime_gate=%s completion=%s"
        % (
            args.mode, metadata["status"], metadata["output"]["sha256"],
            metadata["output"]["crc32"], metadata["change_audit"]["changed_bytes"],
            metadata["scope"]["stage67_new_materialized_routes"],
            metadata["scope"]["cumulative_materialized_routes"],
            metadata["acceptance"]["real_consumer_mgba_gate"],
            metadata["checkpoint_marker"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
