#!/usr/bin/env python3
"""Stage64を親にP03キャタピー代表4経路のStage65 checkpointを生成する。"""

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
from scripts.run_modernization_p03_stage65_mgba import (  # noqa: E402
    ModernizationP03Stage65MgbaError,
    validate_published_gate,
)
from tools.modernization_p03_stage65 import (  # noqa: E402
    ModernizationP03Stage65Error,
    build_stage65_image,
    fixed_input,
    read_config,
    sha256,
    stable_json,
)
from tools.release.bps import apply_bps, create_bps  # noqa: E402


DEFAULT_CONFIG = Path("config/modernization_p03_stage65.json")
TASK = "USER-MODERNIZATION-P03-STAGE65-CATERPIE-SLICE"
STAGE = 65


def build_outputs(config_path: Path = DEFAULT_CONFIG) -> dict[str, bytes]:
    built = build_stage65_image(ROOT, config_path)
    config = built.config
    output = built.rom
    inputs = config["inputs"]
    outputs = config["outputs"]

    parent = fixed_input(ROOT, inputs["parent_rom"], "Stage64 parent ROM")
    clean = fixed_input(
        ROOT,
        inputs["clean_rom"],
        "clean FireRed JPN Rev0 ROM",
        allow_symlink=True,
    )
    mgba = validate_published_gate(config_path, stage65_bytes=output)
    mgba_path = ROOT / outputs["mgba_evidence"]
    mgba_raw = mgba_path.read_bytes()

    incremental = _sparse_bps(parent, output)
    clean_bps = create_bps(
        clean,
        output,
        metadata=(
            b"Clean FireRed JPN Rev0 to Stage65 Modernization P03 "
            b"Caterpie Representative Slice"
        ),
    )
    if apply_bps(parent, incremental) != output:
        raise ModernizationP03Stage65Error(
            "Stage64→Stage65 incremental BPS round-trip不一致"
        )
    if apply_bps(clean, clean_bps) != output:
        raise ModernizationP03Stage65Error("clean→Stage65 direct BPS round-trip不一致")

    output_identity = {
        "path": outputs["rom"],
        "size": len(output),
        "sha256": sha256(output),
        "crc32": f"{zlib.crc32(output) & 0xFFFFFFFF:08X}",
    }
    allocation_raw = stable_json(built.allocation)
    allocation_identity = {
        "path": outputs["allocation"],
        "size": len(allocation_raw),
        "sha256": sha256(allocation_raw),
        "added_allocations": 1,
        "added_bytes": built.audit["allocation"]["size"],
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
    }
    acceptance = {
        "static_contract_gate": "PASS",
        "manifest_identity_gate": "PASS",
        "parent_preimage_gate": "PASS",
        "allocation_gate": "PASS",
        "incremental_bps_round_trip": "PASS",
        "clean_bps_round_trip": "PASS",
        "real_consumer_mgba_gate": "PASS",
        "independent_mgba_processes": 2,
        "full_p03_materialization_gate": "NOT_RUN",
        "scheduler_e2e": "NOT_RUN",
        "task_completion": "CHECKPOINT_NOT_P03_DONE",
    }
    scope = {
        "representative_species": 1,
        "representative_species_key": "SPECIES_KEY_CATERPIE",
        "representative_species_id": 649,
        "contract_routes_total": 118528,
        "routes_materialized_by_this_checkpoint": 4,
        "routes_not_materialized_by_this_checkpoint": 118524,
        "consumers_exercised": ["level_up", "machine"],
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
        "routes_not_materialized_by_this_checkpoint": 118524,
        "consumer_families_not_exercised": [
            "egg",
            "evolution",
            "form_change",
            "pre_evolution_carry",
            "reminder",
            "shared_egg",
            "tutor",
        ],
        "level_and_machine_scope": "CATERPIE_ONLY_OTHER_TARGETS_REMAIN",
        "runtime_supply_required_rows": 26720,
        "move_1063": "BLOCKING_RUNTIME_DEPENDENCY_NOT_IMPLEMENTED",
        "full_scheduler_and_save_reload": "NOT_RUN",
        "note_ja": (
            "このStage65はCaterpie 4経路だけの実consumer縦切りであり、"
            "P03全118,528経路の実装完了を示さない。"
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
        "contract_gate": built.contract_audit,
        "output": output_identity,
        "allocation": allocation_identity,
        "change_audit": built.audit,
        "bps": bps,
        "runtime_gate": mgba_identity,
        "acceptance": acceptance,
        "scope": scope,
        "remaining_work": remaining,
        "producer_boundary": {
            "generator": "tools/modernization_p03_stage65.py",
            "builder": "scripts/build_modernization_p03_stage65.py",
            "parent_stage": 64,
            "clean_rom_cumulative_generation": True,
            "incremental_parent_generation": True,
            "level_consumer_root_repointed": False,
            "only_caterpie_pointer_entry_repointed": True,
            "tm_catalog_changed": False,
            "only_caterpie_compatibility_row_changed": True,
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
        "change_audit": built.audit,
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
        raise ModernizationP03Stage65Error(
            "Stage65 generated artifact drift: " + ", ".join(drift)
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
        ModernizationP03Stage65Error,
        ModernizationP03Stage65MgbaError,
    ) as error:
        print(f"P03 Stage65 {args.mode} failed: {error}", file=sys.stderr)
        return 1
    print(
        "P03 Stage65 %s: %s sha256=%s crc32=%s changed=%d routes=4/118528 "
        "runtime_gate=%s completion=%s"
        % (
            args.mode,
            metadata["status"],
            metadata["output"]["sha256"],
            metadata["output"]["crc32"],
            metadata["change_audit"]["changed_byte_count"],
            metadata["acceptance"]["real_consumer_mgba_gate"],
            metadata["checkpoint_marker"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
