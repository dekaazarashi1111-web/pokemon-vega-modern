#!/usr/bin/env python3
"""Stage62へP01のID意味訂正を決定的に適用し、Stage63候補を生成する。"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import struct
import sys
import tempfile
import zlib
from pathlib import Path
from typing import Any, Mapping, NoReturn, Sequence


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_trainer_v5_stage32 import _sparse_bps  # noqa: E402
from tools.release.bps import apply_bps, create_bps  # noqa: E402


TASK = "USER-MODERNIZATION-P01"
STAGE = 63
ROM_SIZE = 32 * 1024 * 1024
CLEAN_ROM_SIZE = 16 * 1024 * 1024
SPECIES_COUNT = 1621
NO_INDEX = 0xFFFF
DEFAULT_CONFIG = Path("config/modernization_p01_runtime.json")
SPECIES_MANIFEST = Path("manifests/species_ids.csv")
ACTIVE_BASELINE = Path("config/active_play_baseline.json")
SAVE_LAYOUT = Path("config/save_layout.csv")

TARGET_CLASSES = {
    "REQUIRED_BASE": 1,
    "REQUIRED_VEGA_ORIGINAL": 2,
    "REQUIRED_ENABLING_FORM": 3,
    "OPTIONAL_FORM": 4,
    "BATTLE_ONLY_EXCLUDED": 5,
    "BATTLE_ONLY_EXCLUDED_COPY": 5,
    "UNOBTAINABLE_EVENT_FORM_EXCLUDED": 6,
}


class ModernizationP01BuildError(RuntimeError):
    """P01の入力identity、意味解決、ROM配置、または再現性の違反。"""


def _fail(message: str) -> NoReturn:
    raise ModernizationP01BuildError(message)


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _stable(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        _fail(f"JSON root is not an object: {path}")
    return value


def _rows(path: Path) -> list[dict[str, str]]:
    with (ROOT / path).open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def _identity(contract: Mapping[str, Any], label: str) -> bytes:
    path = ROOT / str(contract["path"])
    raw = path.read_bytes()
    if "size" in contract and len(raw) != int(contract["size"]):
        _fail(f"{label} size differs: {len(raw)}")
    if _sha(raw) != str(contract["sha256"]):
        _fail(f"{label} SHA-256 differs")
    return raw


def _load_config(path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    config = _read_json(path)
    if (config.get("schema_version"), config.get("task"), config.get("stage")) != (1, TASK, STAGE):
        _fail("P01 runtime config schema/task/stage differs")
    inputs_path = Path(str(config["inputs"]["modernization_inputs"]))
    inputs = _read_json(inputs_path)
    if (inputs.get("schema_version"), inputs.get("task")) != (1, TASK):
        _fail("modernization input ledger schema/task differs")
    identity_raw = _identity(config["inputs"]["identity_contract"], "P01 identity contract")
    identity = json.loads(identity_raw)
    summary = identity.get("target_normalization", {}).get("summary", {})
    expected_summary = {
        "changed_keys": ["SPECIES_KEY_EGG", "SPECIES_KEY_CATERPIE"],
        "input_apply_true": 1299,
        "normalized_apply_true": 1300,
        "normalized_rows": SPECIES_COUNT,
        "protected_input_false_rows": 321,
        "source_rows": SPECIES_COUNT,
        "unauthorized_false_to_true": 0,
    }
    if identity.get("status") != "PASS" or summary != expected_summary:
        _fail("P01 identity contract semantics differ")
    if identity.get("restoration_review_audit", {}).get("automatically_adopted_rows") != 0:
        _fail("review-only restoration candidates were unexpectedly adopted")
    return config, inputs


def _verify_tracked_sources(inputs: Mapping[str, Any]) -> dict[str, str]:
    observed: dict[str, str] = {}
    for label, pair in inputs["tracked_identity_sources"].items():
        if not isinstance(pair, list) or len(pair) != 2:
            _fail(f"tracked identity source contract differs: {label}")
        path = ROOT / str(pair[0])
        digest = _sha(path.read_bytes())
        if digest != str(pair[1]):
            _fail(f"tracked identity source SHA-256 differs: {label}")
        observed[str(pair[0])] = digest
    return observed


def _verify_archives(inputs: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for label, contract in inputs["archives"].items():
        raw = _identity(contract, f"{label} archive")
        result[label] = {
            "path": contract["path"],
            "size": len(raw),
            "sha256": _sha(raw),
            "role": contract["role"],
        }
    return result


def _unique_by(rows: Sequence[Mapping[str, str]], field: str, label: str) -> dict[str, Mapping[str, str]]:
    result: dict[str, Mapping[str, str]] = {}
    duplicates: list[str] = []
    for row in rows:
        key = str(row[field])
        if key in result:
            duplicates.append(key)
        result[key] = row
    if duplicates:
        _fail(f"{label} duplicate {field}: {sorted(set(duplicates))[:8]}")
    return result


def _parse_vendor_collection_c(raw: bytes) -> bytes:
    text = raw.decode("ascii")
    values = [
        tuple(int(value) for value in match)
        for match in re.findall(
            r"\{(\d+)u,\s*(\d+)u,\s*(\d+)u,\s*(\d+)u,\s*(\d+)u,\s*(\d+)u\}",
            text,
        )
    ]
    if len(values) != SPECIES_COUNT:
        _fail(f"vendor collection C row count differs: {len(values)}")
    return b"".join(struct.pack("<HHBBBB", *row) for row in values)


def _derive_collection_table(config: Mapping[str, Any]) -> tuple[bytes, dict[str, Any]]:
    species_rows = _rows(SPECIES_MANIFEST)
    registry_path = Path(str(config["inputs"]["vendor_registry"]["path"]))
    ledger_path = Path(str(config["inputs"]["vendor_ledger"]["path"]))
    registry_rows = _rows(registry_path)
    ledger_rows = _rows(ledger_path)
    if len(species_rows) != SPECIES_COUNT or len(registry_rows) != SPECIES_COUNT:
        _fail(f"Species row count differs: manifest={len(species_rows)} registry={len(registry_rows)}")

    species_by_key = _unique_by(species_rows, "species_key", "Species manifest")
    species_by_id = _unique_by(species_rows, "id", "Species manifest")
    registry_by_key = _unique_by(registry_rows, "species_key", "acquisition registry")
    _unique_by(registry_rows, "canonical_id", "acquisition registry")
    if set(map(str, range(SPECIES_COUNT))) != set(species_by_id):
        _fail("Species manifest ID space is not contiguous 0..1620")
    if set(species_by_key) != set(registry_by_key):
        missing = sorted(set(species_by_key) - set(registry_by_key))[:8]
        extra = sorted(set(registry_by_key) - set(species_by_key))[:8]
        _fail(f"acquisition registry key set differs: missing={missing} extra={extra}")

    ledger_by_key = _unique_by(ledger_rows, "species_key", "collection ledger")
    ledger_indices: set[int] = set()
    for key, row in ledger_by_key.items():
        if key not in species_by_key:
            _fail(f"collection ledger Species key unresolved: {key}")
        index = int(row["ledger_bit_index"])
        if index in ledger_indices:
            _fail(f"collection ledger duplicate bit index: {index}")
        ledger_indices.add(index)
    if ledger_indices != set(range(len(ledger_rows))):
        _fail("collection ledger bit indices are not contiguous")

    resolved: list[tuple[int, int, int, int, int, int] | None] = [None] * SPECIES_COUNT
    mismatches: list[dict[str, Any]] = []
    for row in registry_rows:
        key = row["species_key"]
        source_id = int(row["canonical_id"])
        resolved_id = int(species_by_key[key]["id"])
        ledger_index = int(ledger_by_key[key]["ledger_bit_index"]) if key in ledger_by_key else NO_INDEX
        completion = int(row["completion_weight"])
        route_required = 1 if row["route_required"] == "yes" else 0
        target_class = TARGET_CLASSES.get(row["target_status"], 0)
        if resolved[resolved_id] is not None:
            _fail(f"resolved Species ID collision: {resolved_id}")
        resolved[resolved_id] = (
            resolved_id, ledger_index, completion, route_required, target_class, 0,
        )
        if source_id != resolved_id:
            mismatches.append({
                "species_key": key,
                "source_id": source_id,
                "resolved_id": resolved_id,
                "ledger_bit_index": ledger_index,
                "completion_weight": completion,
                "route_required": route_required,
                "target_class": target_class,
            })
    if any(row is None for row in resolved):
        _fail("resolved collection table has missing IDs")

    expected_mismatches = sorted(
        config["runtime_table"]["corrections"], key=lambda row: row["species_key"],
    )
    if sorted(mismatches, key=lambda row: row["species_key"]) != expected_mismatches:
        _fail(f"unexpected Species ID mismatch set: {mismatches}")
    table = b"".join(struct.pack("<HHBBBB", *row) for row in resolved if row is not None)
    if _sha(table) != config["runtime_table"]["corrected_sha256"]:
        _fail("corrected acquisition collection table SHA-256 differs")
    completion_count = sum(row[2] for row in resolved if row is not None)
    if completion_count != 1206 or len(ledger_rows) != 1216:
        _fail(f"collection/save count changed: completion={completion_count} ledger={len(ledger_rows)}")
    return table, {
        "species_count": SPECIES_COUNT,
        "ledger_bit_count": len(ledger_rows),
        "completion_target_count": completion_count,
        "mismatch_count": len(mismatches),
        "mismatches": mismatches,
        "save_layout_unchanged": True,
    }


def _changed_spans(before: bytes, after: bytes) -> list[dict[str, int]]:
    if len(before) != len(after):
        _fail("change audit size differs")
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


def _markdown(audit: Mapping[str, Any]) -> bytes:
    output = audit["output"]
    rows = audit["collection_runtime"]["corrections"]
    lines = [
        "# USER-MODERNIZATION-P01 ROM ID意味修復", "",
        "## 結果", "",
        f"- Stage63候補: `{output['sha256']}` / CRC32 `{output['crc32']}`",
        f"- 変更byte: {audit['change_audit']['changed_byte_count']}（宣言外 {audit['change_audit']['outside_declared_span_count']}）",
        "- 既存Species ID、collection ledger bit、save layout、allocationは変更していない。", "",
        "## 訂正", "",
    ]
    for row in rows:
        lines.append(
            f"- `{row['species_key']}`: 資料ID {row['source_id']} → 現行ID {row['resolved_id']}、ledger `{row['ledger_bit_index']}`"
        )
    lines += [
        "", "## 境界", "",
        "- Stage61由来の取得資料は履歴として不変。現行manifestのspecies_keyから生成時に再解決する。",
        "- 原作復元候補の能力・種族値・タイプ・進化と、技習得全表はこの工程ではROMへ適用しない。",
        "- active play baselineの切替と実プレイsaveの更新は行わない。",
    ]
    return ("\n".join(lines) + "\n").encode("utf-8")


def _build_outputs(config_path: Path, *, verify_archives: bool = True) -> dict[str, bytes]:
    config, inputs = _load_config(config_path)
    tracked = _verify_tracked_sources(inputs)
    archives = _verify_archives(inputs) if verify_archives else {}
    active_raw = (ROOT / ACTIVE_BASELINE).read_bytes()
    if _sha(active_raw) != inputs["active_parent"]["identity_source_sha256"]:
        _fail("active play baseline identity changed")
    active = json.loads(active_raw)
    parent_contract = inputs["active_parent"]["rom"]
    if active.get("stage") != 62 or active.get("rom") != parent_contract:
        _fail("active play baseline no longer selects the configured Stage62 parent")
    parent = _identity(parent_contract, "Stage62 parent ROM")
    parent_meta_raw = _identity(inputs["active_parent"]["metadata"], "Stage62 metadata")
    parent_meta = json.loads(parent_meta_raw)
    if parent_meta.get("output", {}).get("sha256") != _sha(parent):
        _fail("Stage62 metadata does not bind the parent ROM")
    allocation_raw = _identity(inputs["active_parent"]["allocation"], "inherited allocation")
    allocation = json.loads(allocation_raw)
    if allocation.get("summaries", {}).get("overlap_count") != 0:
        _fail("inherited allocation contains overlap")
    clean = _identity(inputs["clean_rom"], "clean FireRed JPN Rev0")
    if len(parent) != ROM_SIZE or len(clean) != CLEAN_ROM_SIZE:
        _fail("parent/clean ROM size differs")
    save_layout_raw = (ROOT / SAVE_LAYOUT).read_bytes()

    vendor_c = _identity(config["inputs"]["vendor_collection_c"], "vendor collection C")
    old_table = _parse_vendor_collection_c(vendor_c)
    table_config = config["runtime_table"]
    if _sha(old_table) != table_config["old_sha256"]:
        _fail("vendor collection table SHA-256 differs")
    corrected_table, table_evidence = _derive_collection_table(config)
    offset = int(table_config["rom_offset"])
    if offset + len(old_table) > len(parent):
        _fail("collection runtime table range is outside ROM")
    if parent[offset:offset + len(old_table)] != old_table or parent.count(old_table) != 1:
        _fail("Stage62 collection runtime table identity/location differs")

    output = bytearray(parent)
    output[offset:offset + len(corrected_table)] = corrected_table
    output_raw = bytes(output)
    spans = _changed_spans(parent, output_raw)
    allowed = {
        (offset + int(row["resolved_id"]) * 8, offset + (int(row["resolved_id"]) + 1) * 8)
        for row in table_config["corrections"]
    }
    outside = [span for span in spans if not any(
        start <= span["start"] and span["end_exclusive"] <= end for start, end in allowed
    )]
    if outside:
        _fail(f"P01 changed bytes outside corrected collection rows: {outside[:4]}")
    changed_bytes = sum(span["size"] for span in spans)
    if changed_bytes != 10:
        _fail(f"P01 changed byte count differs: {changed_bytes}")
    if output_raw.count(corrected_table) != 1 or old_table in output_raw:
        _fail("corrected/legacy collection table occurrence differs")

    incremental = _sparse_bps(parent, output_raw)
    direct = create_bps(
        clean, output_raw,
        metadata=b"Clean FireRed JPN Rev0 to Stage63 Modernization P01 Identity Repair",
    )
    if apply_bps(parent, incremental) != output_raw:
        _fail("Stage62 incremental BPS round-trip differs")
    if apply_bps(clean, direct) != output_raw:
        _fail("clean direct BPS round-trip differs")

    output_identity = {
        "path": config["outputs"]["rom"],
        "size": len(output_raw),
        "sha256": _sha(output_raw),
        "crc32": f"{zlib.crc32(output_raw) & 0xFFFFFFFF:08X}",
    }
    correction_rows = []
    for row in table_config["corrections"]:
        resolved_id = int(row["resolved_id"])
        before = old_table[resolved_id * 8:(resolved_id + 1) * 8]
        after = corrected_table[resolved_id * 8:(resolved_id + 1) * 8]
        correction_rows.append({
            **row,
            "rom_offset": offset + resolved_id * 8,
            "gba_address": f"0x{0x08000000 + offset + resolved_id * 8:08X}",
            "before_hex": before.hex(),
            "after_hex": after.hex(),
        })
    audit = {
        "schema_version": 1,
        "task": TASK,
        "stage": STAGE,
        "status": "PASS",
        "input": {
            "source_commit": inputs["source"]["start_commit"],
            "parent": parent_contract,
            "parent_metadata_sha256": _sha(parent_meta_raw),
            "allocation_sha256": _sha(allocation_raw),
            "archives": archives,
            "tracked_identity_sources": tracked,
            "identity_contract": config["inputs"]["identity_contract"],
        },
        "output": output_identity,
        "root_cause": (
            "取得資料のcanonical_idをstable species_keyとの意味照合なしで配列indexへ使用し、"
            "Caterpieと内部Eggの旧ID割当を現行manifestへ持ち込んだ"
        ),
        "collection_runtime": {
            **table_evidence,
            "table_offset": offset,
            "table_size": len(corrected_table),
            "legacy_sha256": _sha(old_table),
            "corrected_sha256": _sha(corrected_table),
            "corrections": correction_rows,
            "legacy_table_remaining": False,
        },
        "change_audit": {
            "changed_byte_count": changed_bytes,
            "changed_span_count": len(spans),
            "declared_row_count": len(allowed),
            "outside_declared_span_count": len(outside),
            "spans": spans,
        },
        "save_and_allocation": {
            "save_layout_path": str(SAVE_LAYOUT),
            "save_layout_sha256": _sha(save_layout_raw),
            "collection_ledger_bit_count": table_evidence["ledger_bit_count"],
            "collection_ledger_mapping_changed": False,
            "save_layout_changed": False,
            "allocation_changed": False,
            "allocator_overlap_count": allocation["summaries"]["overlap_count"],
            "remaining_allocatable_bytes": allocation["summaries"]["remaining_allocatable_bytes"],
        },
        "bps": {
            "incremental": {
                "path": config["outputs"]["incremental_bps"],
                "size": len(incremental),
                "sha256": _sha(incremental),
                "round_trip": True,
            },
            "clean": {
                "path": config["outputs"]["clean_bps"],
                "size": len(direct),
                "sha256": _sha(direct),
                "round_trip": True,
            },
        },
        "scope": {
            "p01_only": True,
            "learnsets_applied": False,
            "restoration_candidates_applied": False,
            "active_play_baseline_changed": False,
            "save_changed": False,
        },
    }
    metadata = {
        "schema_version": 1,
        "task": TASK,
        "stage": STAGE,
        "status": "PASS",
        "input": audit["input"],
        "output": output_identity,
        "collection_runtime": audit["collection_runtime"],
        "change_audit": audit["change_audit"],
        "save_and_allocation": audit["save_and_allocation"],
        "bps": audit["bps"],
        "scope": audit["scope"],
    }
    return {
        config["outputs"]["rom"]: output_raw,
        config["outputs"]["metadata"]: _stable(metadata),
        config["outputs"]["incremental_bps"]: incremental,
        config["outputs"]["clean_bps"]: direct,
        config["outputs"]["audit"]: _stable(audit),
        config["outputs"]["report"]: _markdown(audit),
    }


def _write_outputs(outputs: Mapping[str, bytes]) -> None:
    for relative, raw in outputs.items():
        path = ROOT / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=f".{path.name}.", delete=False) as stream:
            stream.write(raw)
            temporary = Path(stream.name)
        os.replace(temporary, path)


def _check_outputs(outputs: Mapping[str, bytes]) -> None:
    drift = [
        relative for relative, raw in outputs.items()
        if not (ROOT / relative).is_file() or (ROOT / relative).read_bytes() != raw
    ]
    if drift:
        _fail("P01 generated artifact drift: " + ", ".join(drift))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("build", "check"))
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument(
        "--skip-archive-rehash", action="store_true",
        help="focused反復専用。最終gateでは使用しない",
    )
    args = parser.parse_args()
    try:
        verify_archives = not args.skip_archive_rehash
        first = _build_outputs(args.config, verify_archives=verify_archives)
        second = _build_outputs(args.config, verify_archives=verify_archives)
        if first != second:
            _fail("P01 build is not byte deterministic")
        config, _ = _load_config(args.config)
        if args.mode == "build":
            _write_outputs(first)
        else:
            _check_outputs(first)
        metadata = json.loads(first[config["outputs"]["metadata"]])
    except (OSError, ValueError, KeyError, TypeError, struct.error, json.JSONDecodeError,
            ModernizationP01BuildError) as error:
        print(f"P01 modernization {args.mode} failed: {error}", file=sys.stderr)
        return 1
    print(
        "P01 modernization %s: %s sha256=%s crc32=%s changed=%d artifacts=%d"
        % (
            args.mode,
            metadata["status"],
            metadata["output"]["sha256"],
            metadata["output"]["crc32"],
            metadata["change_audit"]["changed_byte_count"],
            len(first),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
