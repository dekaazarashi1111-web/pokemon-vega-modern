#!/usr/bin/env python3
"""Stage65を親にP03 bulk level/machine Stage66 checkpointを生成する。"""

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
from scripts.run_modernization_p03_stage66_mgba import (  # noqa: E402
    ModernizationP03Stage66MgbaError,
    validate_published_gate,
)
from tools.modernization_p03_stage66 import (  # noqa: E402
    ModernizationP03Stage66Error,
    build_stage66_image,
    fixed_input,
    read_config,
    sha256,
    stable_json,
)
from tools.release.bps import apply_bps, create_bps  # noqa: E402


DEFAULT_CONFIG = Path("config/modernization_p03_stage66.json")
TASK = "USER-MODERNIZATION-P03-STAGE66-BULK-LEARNSET-CHECKPOINT"
STAGE = 66


def build_outputs(config_path: Path = DEFAULT_CONFIG) -> dict[str, bytes]:
    built = build_stage66_image(ROOT, config_path)
    config = built.config
    output = built.rom
    inputs = config["inputs"]
    outputs = config["outputs"]

    parent = fixed_input(ROOT, inputs["parent_rom"], "Stage65 parent ROM")
    clean = fixed_input(
        ROOT,
        inputs["clean_rom"],
        "clean FireRed JPN Rev0 ROM",
        allow_symlink=True,
    )
    mgba = validate_published_gate(
        config_path, stage66_bytes=output, built=built,
    )
    mgba_path = ROOT / outputs["mgba_evidence"]
    mgba_raw = mgba_path.read_bytes()

    incremental = _sparse_bps(parent, output)
    clean_bps = create_bps(
        clean,
        output,
        metadata=(
            b"Clean FireRed JPN Rev0 to Stage66 Modernization P03 "
            b"Bulk Learnset Checkpoint"
        ),
    )
    if apply_bps(parent, incremental) != output:
        raise ModernizationP03Stage66Error(
            "Stage65→Stage66 incremental BPS round-trip不一致"
        )
    if apply_bps(clean, clean_bps) != output:
        raise ModernizationP03Stage66Error("clean→Stage66 direct BPS round-trip不一致")

    route_audit_raw = stable_json(built.route_audit)
    change_audit_raw = stable_json(built.change_audit)
    allocation_raw = stable_json(built.allocation)
    output_identity = {
        "path": outputs["rom"],
        "size": len(output),
        "sha256": sha256(output),
        "crc32": f"{zlib.crc32(output) & 0xFFFFFFFF:08X}",
    }
    route_audit_identity = {
        "path": outputs["route_audit"],
        "size": len(route_audit_raw),
        "sha256": sha256(route_audit_raw),
        "corrected_targets": built.route_audit["source_validation"][
            "corrected_target_count"
        ],
        "source_routes_validated": built.route_audit["source_validation"][
            "compiled_route_count"
        ],
        "routes_materialized": built.route_audit["materialization"][
            "materialized_routes"
        ],
    }
    change_audit_identity = {
        "path": outputs["change_audit"],
        "size": len(change_audit_raw),
        "sha256": sha256(change_audit_raw),
        "changed_bytes": built.change_audit["changed_byte_count"],
        "changed_spans": built.change_audit["changed_span_count"],
        "outside_declared_range_count": built.change_audit[
            "outside_declared_range_count"
        ],
    }
    allocation_identity = {
        "path": outputs["allocation"],
        "size": len(allocation_raw),
        "sha256": sha256(allocation_raw),
        "added_allocations": 1,
        "added_bytes": built.change_audit["output_tables"]["level_payload_size"],
        "remaining_allocatable_bytes": built.allocation["summaries"][
            "remaining_allocatable_bytes"
        ],
    }
    bps = {
        "incremental": {
            "path": outputs["incremental_bps"],
            "size": len(incremental),
            "sha256": sha256(incremental),
            "round_trip": True,
        },
        "clean": {
            "path": outputs["clean_bps"],
            "size": len(clean_bps),
            "sha256": sha256(clean_bps),
            "round_trip": True,
        },
    }
    mgba_identity = {
        "path": outputs["mgba_evidence"],
        "size": len(mgba_raw),
        "sha256": sha256(mgba_raw),
        "status": mgba["status"],
        "classification": mgba["classification"],
        "process_runs": mgba["execution"]["process_runs"],
        "representative_samples": len(mgba["runtime_result"]["samples"]),
    }
    acceptance = {
        "static_contract_gate": "PASS",
        "immutable_source_zip_gate": "PASS",
        "all_nine_consumer_input_validation_gate": "PASS",
        "parent_preimage_gate": "PASS",
        "allocation_gate": "PASS",
        "level_up_runtime_ready_bulk_gate": "PASS",
        "machine_existing_slot_bulk_gate": "PASS",
        "deferred_route_accounting_gate": "PASS",
        "incremental_bps_round_trip": "PASS",
        "clean_bps_round_trip": "PASS",
        "real_consumer_mgba_gate": "PASS",
        "independent_mgba_processes": 2,
        "full_p03_materialization_gate": "PARTIAL_NOT_COMPLETE",
        "scheduler_e2e": "NOT_RUN",
        "task_completion": "CHECKPOINT_NOT_P03_DONE",
    }
    scope = {
        "corrected_targets": 1300,
        "contract_routes_total": 118528,
        "level_up_routes_accounted": 18530,
        "level_up_routes_materialized": 18515,
        "level_up_move_1063_routes_deferred": 15,
        "machine_routes_accounted": 55380,
        "machine_existing_slot_routes_materialized": 29033,
        "machine_supply_required_routes_deferred": 26347,
        "routes_materialized_by_this_checkpoint": 47548,
        "routes_not_materialized_by_this_checkpoint": 70980,
        "representative_runtime_species": [10, 858, 1620, 649],
        "consumers_exercised_in_mgba": ["level_up", "machine"],
        "all_p03_routes_implemented": False,
        "move_1063_implemented": False,
        "species_ids_changed": False,
        "move_ids_changed": False,
        "save_layout_changed": False,
        "existing_party_box_save_rewritten": False,
        "active_play_baseline_changed": False,
        "historical_outputs_overwritten": False,
        "review_only_branches_applied": False,
    }
    remaining = {
        "status": "REQUIRED_BEFORE_P03_DONE",
        "routes_not_materialized_by_this_checkpoint": 70980,
        "level_up_move_1063": {
            "routes": 15,
            "status": "BLOCKING_RUNTIME_DEPENDENCY_NOT_IMPLEMENTED",
        },
        "machine_supply_required": {
            "routes": 26347,
            "status": "REQUIRES_CATALOG_OR_ALTERNATE_SUPPLY_IMPLEMENTATION",
        },
        "consumer_routes_not_in_stage66_scope": {
            "evolution": 341,
            "reminder": 298,
            "tutor": 1113,
            "egg": 2572,
            "shared_egg": 5041,
            "pre_evolution_carry": 35183,
            "form_change": 70,
        },
        "move_1063_all_consumers": {
            "routes": 159,
            "status": "BLOCKING_RUNTIME_DEPENDENCY_NOT_IMPLEMENTED",
        },
        "full_scheduler_and_save_reload": "NOT_RUN",
        "note_ja": (
            "このStage66は全level-up入力を監査しruntime-ready 18,515経路と、"
            "既存slotへ解決できるmachine 29,033経路を接続したbulk checkpoint。"
            "供給不足・別consumer・Move 1063を残すためP03完了ではない。"
        ),
    }
    input_audit = dict(built.input_audit)
    input_audit["clean_rom"] = {
        "path": inputs["clean_rom"]["path"],
        "size": len(clean),
        "sha256": sha256(clean),
    }
    input_audit["mgba_runtime_gate"] = mgba_identity
    checkpoint = {
        "schema_version": 1,
        "task": TASK,
        "stage": STAGE,
        "status": "CHECKPOINT",
        "done": False,
        "checkpoint_marker": "CHECKPOINT_NOT_P03_DONE",
        "input": input_audit,
        "output": output_identity,
        "allocation": allocation_identity,
        "route_audit": route_audit_identity,
        "change_audit": change_audit_identity,
        "bps": bps,
        "runtime_gate": mgba_identity,
        "acceptance": acceptance,
        "scope": scope,
        "remaining_work": remaining,
        "producer_boundary": {
            "generator": "tools/modernization_p03_stage66.py",
            "builder": "scripts/build_modernization_p03_stage66.py",
            "parent_stage": 65,
            "clean_rom_cumulative_generation": True,
            "incremental_parent_generation": True,
            "level_consumer_root_repointed": False,
            "corrected_target_pointer_entries_repointed": 1300,
            "machine_catalog_changed": False,
            "corrected_target_compatibility_rows_replaced": 1300,
            "non_adopted_species_rows_preserved": 321,
        },
    }
    metadata = {
        "schema_version": 1,
        "task": TASK,
        "stage": STAGE,
        "status": "CHECKPOINT",
        "done": False,
        "checkpoint_marker": "CHECKPOINT_NOT_P03_DONE",
        "input": input_audit,
        "output": output_identity,
        "allocation": allocation_identity,
        "route_audit": route_audit_identity,
        "change_audit": change_audit_identity,
        "bps": bps,
        "acceptance": acceptance,
        "scope": scope,
        "remaining_work": remaining,
    }
    return {
        outputs["rom"]: output,
        outputs["metadata"]: stable_json(metadata),
        outputs["allocation"]: allocation_raw,
        outputs["incremental_bps"]: incremental,
        outputs["clean_bps"]: clean_bps,
        outputs["route_audit"]: route_audit_raw,
        outputs["change_audit"]: change_audit_raw,
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
        relative
        for relative, raw in outputs.items()
        if not (ROOT / relative).is_file() or (ROOT / relative).read_bytes() != raw
    ]
    if drift:
        raise ModernizationP03Stage66Error(
            "Stage66 generated artifact drift: " + ", ".join(drift)
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
        OSError,
        KeyError,
        TypeError,
        ValueError,
        struct.error,
        ModernizationP03Stage66Error,
        ModernizationP03Stage66MgbaError,
    ) as error:
        print(f"P03 Stage66 {args.mode} failed: {error}", file=sys.stderr)
        return 1
    print(
        "P03 Stage66 %s: %s sha256=%s crc32=%s changed=%d "
        "routes=%d/118528 runtime_gate=%s completion=%s"
        % (
            args.mode,
            metadata["status"],
            metadata["output"]["sha256"],
            metadata["output"]["crc32"],
            metadata["change_audit"]["changed_bytes"],
            metadata["scope"]["routes_materialized_by_this_checkpoint"],
            metadata["acceptance"]["real_consumer_mgba_gate"],
            metadata["checkpoint_marker"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
