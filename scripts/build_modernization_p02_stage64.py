#!/usr/bin/env python3
"""Stage63へRayquaza進化parameterの2-byte修復を適用しStage64 checkpointを作る。"""

from __future__ import annotations

import argparse
import csv
import hashlib
import inspect
import json
import os
import struct
import sys
import tempfile
import zlib
from pathlib import Path
from typing import Any, Mapping, NoReturn


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_trainer_v5_stage32 import _sparse_bps  # noqa: E402
from scripts.build_species_surface import (  # noqa: E402
    EVOLUTION_PARAMETER_POLICY_MODERNIZATION_P02_V2,
    EVOLUTION_PARAMETER_POLICY_T09_LEGACY_V1,
    MEGA_VARIANT_WISH,
    merge_evolutions,
    remap_evolution_parameters,
)
from scripts.run_modernization_p02_mgba import (  # noqa: E402
    DEFAULT_CONFIG as P02_MGBA_CONFIG,
    ModernizationP02MgbaError,
    validate_published_gate,
)
from tools.release.bps import apply_bps, create_bps  # noqa: E402


TASK = "USER-MODERNIZATION-P02-RAYQUAZA"
STAGE = 64
ROM_BASE = 0x08000000
ROM_SIZE = 32 * 1024 * 1024
CLEAN_ROM_SIZE = 16 * 1024 * 1024
EVOLUTION_STRIDE = 128
EVOLUTION_ENTRY_SIZE = 8
DEFAULT_CONFIG = Path("config/modernization_p02_stage64.json")


class ModernizationP02Stage64Error(RuntimeError):
    """Stage64入力identity、patch preimage、または成果物契約の違反。"""


def _fail(message: str) -> NoReturn:
    raise ModernizationP02Stage64Error(message)


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _stable(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads((ROOT / path).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        _fail(f"JSONを読めません: {path}: {error}")
    if not isinstance(value, dict):
        _fail(f"JSON rootがobjectではありません: {path}")
    return value


def _fixed(contract: Mapping[str, Any], label: str) -> bytes:
    path = ROOT / str(contract.get("path", ""))
    if not path.is_file():
        _fail(f"{label}がありません: {path}")
    raw = path.read_bytes()
    if "size" in contract and len(raw) != int(contract["size"]):
        _fail(f"{label} size不一致: {len(raw)} != {contract['size']}")
    if _sha(raw) != str(contract.get("sha256", "")):
        _fail(f"{label} SHA-256不一致")
    return raw


def _hex_int(value: Any, label: str) -> int:
    if not isinstance(value, str) or not value.startswith("0x"):
        _fail(f"{label}は0x付き16進数ではありません: {value!r}")
    try:
        result = int(value, 16)
    except ValueError:
        _fail(f"{label}が不正です: {value!r}")
    if result < 0:
        _fail(f"{label}が負数です")
    return result


def _manifest_by_key(contract: Mapping[str, Any], key_field: str, label: str) -> dict[str, dict[str, str]]:
    raw = _fixed(contract, label)
    try:
        rows = list(csv.DictReader(raw.decode("utf-8-sig").splitlines()))
    except UnicodeDecodeError as error:
        _fail(f"{label}がUTF-8 CSVではありません: {error}")
    result: dict[str, dict[str, str]] = {}
    ids: set[int] = set()
    for row in rows:
        key = row.get(key_field, "")
        entity_id = int(row.get("id", "-1"))
        if not key or key in result or entity_id in ids:
            _fail(f"{label} key/ID重複または欠落: key={key!r} id={entity_id}")
        result[key] = row
        ids.add(entity_id)
    if ids != set(range(len(rows))):
        _fail(f"{label} ID空間が0..N-1連続ではありません")
    return result


def _changed_spans(before: bytes, after: bytes) -> list[dict[str, int]]:
    if len(before) != len(after):
        _fail("before/after ROM sizeが一致しません")
    spans: list[dict[str, int]] = []
    index = 0
    while index < len(before):
        if before[index] == after[index]:
            index += 1
            continue
        start = index
        while index < len(before) and before[index] != after[index]:
            index += 1
        spans.append({"start": start, "end_exclusive": index, "size": index - start})
    return spans


def _root_policy_audit(patch: Mapping[str, Any]) -> dict[str, Any]:
    """root producerのversioned namespace policyを実行してpatch値を導出確認する。"""

    if int(patch["method_id"]) != 0xFE or int(patch["mega_variant"]) != MEGA_VARIANT_WISH:
        _fail("Stage64 patchがWish Mega ABIではありません")
    default_policy = inspect.signature(merge_evolutions).parameters["parameter_policy"].default
    if default_policy != EVOLUTION_PARAMETER_POLICY_T09_LEGACY_V1:
        _fail("merge_evolutionsの既定policyがhistorical byte互換ではありません")
    source_move_id = 559
    legacy = remap_evolution_parameters(
        0xFE,
        source_move_id,
        MEGA_VARIANT_WISH,
        {},
        {source_move_id: int(patch["after_move_id"])},
        {source_move_id: int(patch["before_move_id"])},
        policy=EVOLUTION_PARAMETER_POLICY_T09_LEGACY_V1,
    )
    modernization = remap_evolution_parameters(
        0xFE,
        source_move_id,
        MEGA_VARIANT_WISH,
        {},
        {source_move_id: int(patch["after_move_id"])},
        {source_move_id: int(patch["before_move_id"])},
        policy=EVOLUTION_PARAMETER_POLICY_MODERNIZATION_P02_V2,
    )
    if legacy != (int(patch["before_move_id"]), MEGA_VARIANT_WISH):
        _fail("historical policyがStage63 preimageを再現しません")
    if modernization != (int(patch["after_move_id"]), MEGA_VARIANT_WISH):
        _fail("modernization policyがDragon Ascent parameterを生成しません")
    return {
        "status": "PASS",
        "source_move_id": source_move_id,
        "historical_default_policy": EVOLUTION_PARAMETER_POLICY_T09_LEGACY_V1,
        "historical_default_output_preserved": True,
        "historical_resolved_parameter_id": legacy[0],
        "modernization_policy": EVOLUTION_PARAMETER_POLICY_MODERNIZATION_P02_V2,
        "modernization_resolved_parameter_id": modernization[0],
    }


def _validate_static_contract(
    raw: bytes,
    patch: Mapping[str, Any],
    policy_audit: Mapping[str, Any],
) -> dict[str, Any]:
    try:
        contract = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        _fail(f"P02 static contractがJSONではありません: {error}")
    if (
        contract.get("schema_version") != 1
        or contract.get("status") != "PASS"
        or contract.get("static_gate") != "PASS"
    ):
        _fail("P02 static contractがPASS schema 1ではありません")
    if not contract.get("deferred_runtime_acceptance", {}).get("must_not_be_reported_as_passed"):
        _fail("P02 static contractのruntime未検証境界がありません")
    table = contract.get("runtime_contract", {}).get("table", {})
    if _hex_int(patch["table_runtime_address"], "table_runtime_address") != int(table.get("runtime_address", -1)):
        _fail("configとP02 contractのevolution runtime addressが一致しません")
    if _hex_int(patch["table_rom_offset"], "table_rom_offset") != int(table.get("rom_file_offset", -1)):
        _fail("configとP02 contractのevolution ROM offsetが一致しません")
    findings = {
        row.get("finding_key"): row for row in contract.get("findings", {}).get("rows", [])
    }
    finding = findings.get(patch["patch_key"])
    if (
        finding is None
        or finding.get("classification")
        != "CONFIRMED_HISTORICAL_ARTIFACT_NAMESPACE_ERROR"
    ):
        _fail("Rayquazaの確認済みstatic findingがありません")
    if finding.get("row_key") != f"{patch['species_key']}#SLOT_{int(patch['slot']):02d}":
        _fail("Rayquaza findingのstable row keyがconfigと一致しません")
    if (
        finding.get("current", {}).get("parameter_key") != patch["before_move_key"]
        or int(finding.get("current", {}).get("parameter_id", -1)) != int(patch["before_move_id"])
        or finding.get("required", {}).get("parameter_key") != patch["after_move_key"]
        or int(finding.get("required", {}).get("parameter_id", -1)) != int(patch["after_move_id"])
    ):
        _fail("Rayquaza findingのbefore/after Move identityがconfigと一致しません")
    namespace = contract.get("runtime_contract", {}).get("producer", {}).get(
        "parameter_namespace_policy", {},
    )
    if (
        namespace.get("status") != "PASS"
        or not namespace.get("historical_default_output_preserved")
        or namespace.get("historical_default_policy")
        != policy_audit["historical_default_policy"]
        or namespace.get("modernization_policy") != policy_audit["modernization_policy"]
        or int(namespace.get("legacy_resolved_parameter_id", -1))
        != int(policy_audit["historical_resolved_parameter_id"])
        or int(namespace.get("modernization_resolved_parameter_id", -1))
        != int(policy_audit["modernization_resolved_parameter_id"])
    ):
        _fail("P02 static contractがroot namespace fixを保証していません")
    return contract


def _validate_config(config: Mapping[str, Any]) -> None:
    if (config.get("schema_version"), config.get("task"), config.get("stage")) != (1, TASK, STAGE):
        _fail("Stage64 config schema/task/stage不一致")
    acceptance = config.get("acceptance", {})
    if acceptance.get("mgba_runtime_gate") != "REQUIRED":
        _fail("Stage64 configがmGBA runtime gateを必須化していません")
    if acceptance.get("task_completion") != "CHECKPOINT_NOT_DONE":
        _fail("Stage64を誤ってDONE扱いするconfigです")


def apply_rayquaza_patch(parent: bytes, patch: Mapping[str, Any]) -> tuple[bytes, dict[str, Any]]:
    """宣言した1 entryのparameter 2 bytesだけをpreimage付きで置換する。"""

    policy_audit = _root_policy_audit(patch)
    if len(parent) != ROM_SIZE:
        _fail(f"Stage63 ROM size不一致: {len(parent)}")
    table_offset = _hex_int(patch["table_rom_offset"], "table_rom_offset")
    table_address = _hex_int(patch["table_runtime_address"], "table_runtime_address")
    species_id = int(patch["species_id"])
    slot = int(patch["slot"])
    if not (0 <= species_id < 1621 and 0 <= slot < 16):
        _fail("Species IDまたはslotが範囲外です")
    entry_offset = table_offset + species_id * EVOLUTION_STRIDE + slot * EVOLUTION_ENTRY_SIZE
    entry_address = table_address + species_id * EVOLUTION_STRIDE + slot * EVOLUTION_ENTRY_SIZE
    parameter_offset = _hex_int(patch["parameter_rom_offset"], "parameter_rom_offset")
    parameter_address = _hex_int(patch["parameter_runtime_address"], "parameter_runtime_address")
    if parameter_offset != entry_offset + 2 or parameter_address != entry_address + 2:
        _fail("parameter offset/addressがtable layout式と一致しません")
    if entry_address != ROM_BASE + entry_offset or parameter_address != ROM_BASE + parameter_offset:
        _fail("ROM offsetとGBA runtime addressの対応が不正です")

    expected = bytes.fromhex(str(patch["entry_before_hex"]))
    replacement = bytes.fromhex(str(patch["entry_after_hex"]))
    if len(expected) != EVOLUTION_ENTRY_SIZE or len(replacement) != EVOLUTION_ENTRY_SIZE:
        _fail("進化entry preimage/replacementが8 bytesではありません")
    expected_tuple = (
        int(patch["method_id"]), int(patch["before_move_id"]),
        int(patch["target_species_id"]), int(patch["mega_variant"]),
    )
    replacement_tuple = (
        int(patch["method_id"]), int(patch["after_move_id"]),
        int(patch["target_species_id"]), int(patch["mega_variant"]),
    )
    if struct.unpack("<HHHH", expected) != expected_tuple:
        _fail("entry_before_hexが意味tupleと一致しません")
    if struct.unpack("<HHHH", replacement) != replacement_tuple:
        _fail("entry_after_hexが意味tupleと一致しません")
    if parent[entry_offset:entry_offset + EVOLUTION_ENTRY_SIZE] != expected:
        actual = parent[entry_offset:entry_offset + EVOLUTION_ENTRY_SIZE].hex()
        _fail(f"Stage63 Rayquaza進化entry preimage不一致: {actual}")
    if expected[:2] != replacement[:2] or expected[4:] != replacement[4:]:
        _fail("parameter以外を変更するreplacementです")

    output = bytearray(parent)
    output[parameter_offset:parameter_offset + 2] = struct.pack("<H", int(patch["after_move_id"]))
    result = bytes(output)
    spans = _changed_spans(parent, result)
    if spans != [{"start": parameter_offset, "end_exclusive": parameter_offset + 2, "size": 2}]:
        _fail(f"Stage64変更spanが宣言した2 bytesだけではありません: {spans}")
    if result[entry_offset:entry_offset + EVOLUTION_ENTRY_SIZE] != replacement:
        _fail("Stage64 Rayquaza進化entry replacement不一致")
    return result, {
        "patch_key": patch["patch_key"],
        "species_key": patch["species_key"],
        "species_id": species_id,
        "slot": slot,
        "target_species_key": patch["target_species_key"],
        "target_species_id": int(patch["target_species_id"]),
        "method_id": int(patch["method_id"]),
        "mega_variant": int(patch["mega_variant"]),
        "entry_rom_offset": entry_offset,
        "entry_runtime_address": f"0x{entry_address:08X}",
        "parameter_rom_offset": parameter_offset,
        "parameter_runtime_address": f"0x{parameter_address:08X}",
        "before_move_key": patch["before_move_key"],
        "before_move_id": int(patch["before_move_id"]),
        "after_move_key": patch["after_move_key"],
        "after_move_id": int(patch["after_move_id"]),
        "before_hex": expected.hex(),
        "after_hex": replacement.hex(),
        "changed_bytes": 2,
        "changed_spans": spans,
        "parameter_policy": policy_audit,
    }


def build_outputs(config_path: Path = DEFAULT_CONFIG) -> dict[str, bytes]:
    config = _read_json(config_path)
    _validate_config(config)
    inputs = config["inputs"]
    patch = config["patch"]
    policy_audit = _root_policy_audit(patch)

    parent = _fixed(inputs["parent_rom"], "Stage63 parent ROM")
    parent_metadata_raw = _fixed(inputs["parent_metadata"], "Stage63 parent metadata")
    parent_metadata = json.loads(parent_metadata_raw)
    if (
        parent_metadata.get("stage") != 63
        or parent_metadata.get("status") != "PASS"
        or parent_metadata.get("output", {}).get("path") != inputs["parent_rom"]["path"]
        or parent_metadata.get("output", {}).get("sha256") != _sha(parent)
    ):
        _fail("Stage63 metadataがparent ROM identityを保証していません")
    if parent_metadata.get("scope", {}).get("active_play_baseline_changed"):
        _fail("Stage63がactive baselineを変更したという想定外metadataです")

    static_raw = _fixed(inputs["p02_static_contract"], "P02 static contract")
    static_contract = _validate_static_contract(static_raw, patch, policy_audit)
    species = _manifest_by_key(inputs["species_manifest"], "species_key", "Species manifest")
    moves = _manifest_by_key(inputs["move_manifest"], "move_key", "Move manifest")
    for key, expected_id in (
        (patch["species_key"], patch["species_id"]),
        (patch["target_species_key"], patch["target_species_id"]),
    ):
        if key not in species or int(species[key]["id"]) != int(expected_id):
            _fail(f"Species stable key/ID不一致: {key}")
    for key, expected_id in (
        (patch["before_move_key"], patch["before_move_id"]),
        (patch["after_move_key"], patch["after_move_id"]),
    ):
        if key not in moves or int(moves[key]["id"]) != int(expected_id):
            _fail(f"Move stable key/ID不一致: {key}")

    output, patch_audit = apply_rayquaza_patch(parent, patch)
    mgba_evidence = validate_published_gate(
        P02_MGBA_CONFIG,
        stage63_bytes=parent,
        stage64_bytes=output,
    )
    mgba_config = _read_json(P02_MGBA_CONFIG)
    mgba_evidence_path = Path(mgba_config["output"])
    mgba_evidence_raw = (ROOT / mgba_evidence_path).read_bytes()
    clean = _fixed(inputs["clean_rom"], "clean FireRed JPN Rev0 ROM")
    if len(clean) != CLEAN_ROM_SIZE:
        _fail(f"clean ROM size不一致: {len(clean)}")

    incremental = _sparse_bps(parent, output)
    clean_bps = create_bps(
        clean,
        output,
        metadata=b"Clean FireRed JPN Rev0 to Stage64 Modernization P02 Rayquaza Parameter Repair",
    )
    if apply_bps(parent, incremental) != output:
        _fail("Stage63→Stage64 incremental BPS round-trip不一致")
    if apply_bps(clean, clean_bps) != output:
        _fail("clean→Stage64 direct BPS round-trip不一致")

    outputs = config["outputs"]
    output_identity = {
        "path": outputs["rom"],
        "size": len(output),
        "sha256": _sha(output),
        "crc32": f"{zlib.crc32(output) & 0xFFFFFFFF:08X}",
    }
    bps = {
        "incremental": {
            "path": outputs["incremental_bps"],
            "size": len(incremental),
            "sha256": _sha(incremental),
            "round_trip": True,
        },
        "clean": {
            "path": outputs["clean_bps"],
            "size": len(clean_bps),
            "sha256": _sha(clean_bps),
            "round_trip": True,
        },
    }
    checkpoint = {
        "schema_version": 1,
        "task": TASK,
        "stage": STAGE,
        "status": "CHECKPOINT",
        "done": False,
        "input": {
            "parent_rom": {
                "path": inputs["parent_rom"]["path"],
                "size": len(parent),
                "sha256": _sha(parent),
            },
            "parent_metadata": {
                "path": inputs["parent_metadata"]["path"],
                "sha256": _sha(parent_metadata_raw),
            },
            "p02_static_contract": {
                "path": inputs["p02_static_contract"]["path"],
                "sha256": _sha(static_raw),
                "static_gate": static_contract["static_gate"],
            },
            "p02_mgba_runtime_gate": {
                "path": mgba_evidence_path.as_posix(),
                "size": len(mgba_evidence_raw),
                "sha256": _sha(mgba_evidence_raw),
                "status": mgba_evidence["status"],
                "process_runs": mgba_evidence["execution"]["process_runs"],
                "classification": mgba_evidence["classification"],
            },
        },
        "output": output_identity,
        "patch": patch_audit,
        "change_audit": {
            "changed_byte_count": 2,
            "changed_span_count": 1,
            "outside_declared_span_count": 0,
            "rom_size_changed": False,
        },
        "bps": bps,
        "producer_boundary": {
            "stage64_builder": "scripts/build_modernization_p02_stage64.py",
            "upstream_generator": static_contract["runtime_contract"]["producer"],
            "root_fix_applied": True,
            "historical_outputs_overwritten": False,
            "policy_verification": policy_audit,
            "note_ja": "build_species_surface.pyは履歴互換policyを既定値として保持し、modernization policyでWish MegaをMove namespaceへ修正した。Stage64はStage63を上書きせず決定的に2 bytesを修復する。",
        },
        "acceptance": {
            "static_patch_gate": "PASS",
            "incremental_bps_round_trip": "PASS",
            "clean_bps_round_trip": "PASS",
            "mgba_runtime_gate": "PASS",
            "ability_move_cancel_item_save_reload_gate": "NOT_RUN",
            "task_completion": "CHECKPOINT_NOT_DONE",
        },
        "scope": {
            "changed_evolution_rows": 1,
            "changed_parameter_bytes": 2,
            "other_evolution_rows_changed": 0,
            "species_ids_changed": False,
            "move_ids_changed": False,
            "save_layout_changed": False,
            "active_play_baseline_changed": False,
            "review_only_branches_applied": False,
        },
    }
    metadata = {
        "schema_version": 1,
        "task": TASK,
        "stage": STAGE,
        "status": "CHECKPOINT",
        "done": False,
        "input": checkpoint["input"],
        "output": output_identity,
        "patch": patch_audit,
        "change_audit": checkpoint["change_audit"],
        "bps": bps,
        "acceptance": checkpoint["acceptance"],
        "scope": checkpoint["scope"],
    }
    return {
        outputs["rom"]: output,
        outputs["metadata"]: _stable(metadata),
        outputs["incremental_bps"]: incremental,
        outputs["clean_bps"]: clean_bps,
        outputs["checkpoint"]: _stable(checkpoint),
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
        _fail("Stage64 generated artifact drift: " + ", ".join(drift))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("build", "check"))
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    args = parser.parse_args(argv)
    try:
        outputs = build_outputs(args.config)
        config = _read_json(args.config)
        if args.mode == "build":
            _write_outputs(outputs)
        else:
            _check_outputs(outputs)
        metadata = json.loads(outputs[config["outputs"]["metadata"]])
    except (
        OSError, ValueError, KeyError, TypeError, struct.error,
        ModernizationP02Stage64Error, ModernizationP02MgbaError,
    ) as error:
        print(f"P02 Stage64 {args.mode} failed: {error}", file=sys.stderr)
        return 1
    print(
        "P02 Stage64 %s: %s sha256=%s crc32=%s changed=%d runtime_gate=%s"
        % (
            args.mode,
            metadata["status"],
            metadata["output"]["sha256"],
            metadata["output"]["crc32"],
            metadata["change_audit"]["changed_byte_count"],
            metadata["acceptance"]["mgba_runtime_gate"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
