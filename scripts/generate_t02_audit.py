#!/usr/bin/env python3
"""固定ROM/source/T01成果からT02互換性監査を決定的に生成する。"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import sys
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from common import repo_root, sha256_file, write_json


ROOT = repo_root()
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.t02.rom_inventory import build_rom_inventory  # noqa: E402
from tools.t02.source_writes import (  # noqa: E402
    build_source_write_model,
    expand_cross_engine_overlap_template,
)
from tools.t02.state_inventory import (  # noqa: E402
    build_state_inventory,
    validate_state_inventory,
)


ADDRESS_FIELDS = (
    "write_id",
    "sequence",
    "engine",
    "profile",
    "source_file",
    "source_line",
    "kind",
    "symbol",
    "start",
    "end_exclusive",
    "size",
    "active_condition",
    "write_encoding",
    "write_value",
    "clean_value",
    "vega_value",
    "factory_value",
    "classification",
    "classification_evidence",
    "resolution",
    "evidence",
    "followup_task",
    "same_value_write",
    "overlaps",
    "code_context_start",
    "code_context_end_exclusive",
    "code_context_status",
    "code_context_clean_sha256",
    "code_context_vega_sha256",
    "code_context_factory_sha256",
)
RANGE_FIELDS = (
    "address_space",
    "start",
    "end_exclusive",
    "size",
    "owner",
    "key",
    "storage",
    "lifetime",
    "persistence",
    "active_condition",
    "source_ref",
    "overlaps",
    "classification",
    "resolution",
    "evidence_sha256",
)
MAP_FIELDS = (
    "group",
    "map",
    "header_address",
    "layout_id",
    "map_section",
    "music",
    "events_address",
    "object_count",
    "warp_count",
    "coord_count",
    "bg_count",
    "map_scripts_address",
    "classification",
    "evidence",
)
ENCOUNTER_FIELDS = (
    "group",
    "map",
    "header_address",
    "land_address",
    "water_address",
    "rock_address",
    "fishing_address",
    "classification",
    "evidence",
)
QOL_FIELDS = (
    "domain",
    "address_or_symbol",
    "status",
    "vega_expected_sha256",
    "classification",
    "evidence",
    "followup_task",
)
TRAINER_FIELDS = (
    "trainer_id",
    "role",
    "party_size",
    "species",
    "levels",
    "moves",
    "move_source",
    "abilities",
    "items",
    "ai_flags",
    "reward",
    "reward_basis",
    "rematch_branch",
    "classification_status",
    "unknown_fields",
    "followup_task",
    "evidence",
)


class AuditError(RuntimeError):
    pass


_RESOLUTIONS = {
    "VEGA": "PRESERVE_VEGA",
    "CFRU": "APPLY_CFRU_FIXED_WRITE",
    "PORT": "PORT_SEMANTICS_WITHOUT_BLIND_BYTE_COPY",
    "RELOCATE": "RELOCATE_TO_32_MIB_REGION",
    "SAME_TARGET": "KEEP_SHARED_IDENTICAL_TARGET",
    "UNKNOWN": "FOLLOW_UP_BEFORE_PORT",
}


def _digest_label(value: Any) -> str:
    if not isinstance(value, Mapping):
        raise AuditError("fixed-write byte observation must be a digest object")
    length = int(value.get("length", -1))
    digest = str(value.get("sha256", ""))
    if length < 0 or len(digest) != 64:
        raise AuditError("invalid fixed-write byte observation")
    return f"sha256:{digest};length:{length}"


def _normalise_source_writes(source: Mapping[str, Any]) -> list[dict[str, Any]]:
    raw_rows = source.get("writes")
    if not isinstance(raw_rows, list):
        raise AuditError("fixed-write model rows are missing")
    rows: list[dict[str, Any]] = []
    for raw in raw_rows:
        source_ref = raw.get("source", {})
        if not isinstance(source_ref, Mapping):
            raise AuditError("fixed-write source reference is invalid")
        start = int(raw["start"])
        end = int(raw["end"])
        classification = str(raw["classification_candidate"])
        context = raw.get("code_context") or {}
        if not isinstance(context, Mapping):
            raise AuditError("fixed-write code context is invalid")
        rows.append(
            {
                "write_id": str(raw["write_id"]),
                "sequence": int(raw["sequence"]),
                "engine": str(raw["engine"]),
                "profile": str(raw["profile"]),
                "source_file": str(source_ref.get("path", "")),
                "source_line": int(source_ref.get("line", 0)),
                "kind": str(raw["source_kind"]),
                "symbol": str(raw.get("intended_symbol", "")),
                "start": f"0x{start:08X}",
                "end_exclusive": f"0x{end:08X}",
                "size": end - start,
                "active_condition": str(raw.get("active_condition", "")),
                "write_encoding": "sha256+length",
                "write_value": _digest_label(raw["written"]),
                "clean_value": _digest_label(raw["clean"]),
                "vega_value": _digest_label(raw["vega"]),
                "factory_value": _digest_label(raw["factory"]),
                "classification": classification,
                "classification_evidence": str(raw.get("classification_evidence", "")),
                "resolution": _RESOLUTIONS.get(classification, ""),
                "evidence": list(raw.get("evidence", [])),
                "followup_task": raw.get("followup") or "",
                "same_value_write": bool(raw.get("same_value_write")),
                "overlaps": list(raw.get("overlaps", [])),
                "code_context_start": (
                    f"0x{int(context['start']):08X}" if context else ""
                ),
                "code_context_end_exclusive": (
                    f"0x{int(context['end']):08X}" if context else ""
                ),
                "code_context_status": str(
                    context.get("containing_function_status", "NOT_CODE")
                ),
                "code_context_clean_sha256": str(
                    context.get("clean", {}).get("sha256", "")
                ),
                "code_context_vega_sha256": str(
                    context.get("vega", {}).get("sha256", "")
                ),
                "code_context_factory_sha256": str(
                    context.get("factory", {}).get("sha256", "")
                ),
            }
        )
    return rows


def _qol_inventory_rows(
    policy: Mapping[str, Any],
    source: Mapping[str, Any],
    state: Mapping[str, Any],
) -> list[dict[str, Any]]:
    required = [str(value) for value in policy["qol_required_domains"]]
    patterns = policy.get("qol_write_symbol_patterns")
    if not isinstance(patterns, Mapping) or set(patterns) != set(required):
        raise AuditError("QOL fixed-write pattern contract is incomplete")
    state_rows = state.get("qol")
    if not isinstance(state_rows, list):
        raise AuditError("QOL state contracts are missing")
    by_domain = {str(row.get("domain")): row for row in state_rows}
    if set(by_domain) != set(required) or len(by_domain) != len(state_rows):
        raise AuditError("QOL state domains are incomplete or duplicated")

    output: list[dict[str, Any]] = []
    raw_writes = source.get("writes", [])
    for domain in required:
        try:
            expression = re.compile(str(patterns[domain]), re.IGNORECASE)
        except re.error as error:
            raise AuditError(f"invalid QOL pattern for {domain}: {error}") from error
        matched = [
            row
            for row in raw_writes
            if expression.fullmatch(str(row.get("intended_symbol", "")))
        ]
        if not matched:
            raise AuditError(f"QOL domain has no exact fixed-write observation: {domain}")
        unique: dict[tuple[Any, ...], list[Mapping[str, Any]]] = {}
        for row in matched:
            key = (
                int(row["start"]),
                int(row["end"]),
                str(row["intended_symbol"]),
                str(row["classification_candidate"]),
                str(row.get("vega", {}).get("sha256", "")),
            )
            unique.setdefault(key, []).append(row)
        for key, variants in sorted(unique.items()):
            row = variants[0]
            classification = str(row.get("classification_candidate", ""))
            digest = row.get("vega", {}).get("sha256")
            if classification == "UNKNOWN" or not re.fullmatch(
                r"[0-9a-f]{64}", str(digest)
            ):
                raise AuditError(f"QOL fixed write is unresolved: {row.get('write_id')}")
            source_refs = sorted(
                {
                    f"{variant['write_id']} {variant.get('source', {}).get('path', '')}:"
                    f"{variant.get('source', {}).get('line', 0)}"
                    for variant in variants
                }
            )
            output.append(
                {
                    "domain": domain,
                    "address_or_symbol": (
                        f"0x{int(row['start']):08X}:{row['intended_symbol']}"
                    ),
                    "status": "FIXED_WRITE_EXACT_VEGA_BYTES",
                    "vega_expected_sha256": str(digest),
                    "classification": classification,
                    "evidence": (
                        f"{'; '.join(source_refs)} span=0x{int(row['start']):08X}.."
                        f"0x{int(row['end']):08X}"
                    ),
                    "followup_task": by_domain[domain]["followup_task"],
                }
            )
        contract = dict(by_domain[domain])
        if contract.get("vega_expected_sha256") != "NOT_APPLICABLE_NON_ROM_CONTRACT":
            raise AuditError(f"QOL non-ROM contract marker mismatch: {domain}")
        if contract.get("classification") == "UNKNOWN":
            raise AuditError(f"QOL non-ROM contract is unresolved: {domain}")
        output.append(contract)
    return sorted(
        output,
        key=lambda row: (
            str(row["domain"]),
            str(row["status"]),
            str(row["address_or_symbol"]),
            str(row["evidence"]),
        ),
    )


def _atomic_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def _csv_value(value: Any) -> str | int:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (list, tuple, dict)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return value


def _write_csv(
    path: Path,
    fields: Sequence[str],
    rows: Iterable[Mapping[str, Any]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
            writer.writeheader()
            for row in rows:
                writer.writerow({field: _csv_value(row.get(field, "")) for field in fields})
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def _verify_path(path: Path, expected: Mapping[str, Any], label: str) -> None:
    if not path.is_file():
        raise AuditError(f"{label} is missing: {path}")
    size = path.stat().st_size
    if "size" in expected and size != int(expected["size"]):
        raise AuditError(f"{label} size mismatch: {size}")
    actual = sha256_file(path)
    if actual != str(expected["sha256"]):
        raise AuditError(f"{label} SHA-256 mismatch: {actual}")


def validate_policy(root: Path, policy: Mapping[str, Any]) -> None:
    if policy.get("schema_version") != 1 or policy.get("policy_id") != "T02_EXACT_AUDIT_V1":
        raise AuditError("unsupported T02 audit policy")
    lock = policy["source_lock"]
    lock_path = root / str(lock["path"])
    _verify_path(lock_path, {"sha256": lock["sha256"]}, "source lock")
    source_lock = json.loads(lock_path.read_text(encoding="utf-8"))
    actual_commits = {
        str(item["name"]): str(item["resolved_commit"])
        for item in source_lock.get("sources", [])
    }
    if actual_commits != dict(lock["commits"]):
        raise AuditError("source lock commit contract mismatch")
    for name, expected in policy["inputs"].items():
        _verify_path(root / str(expected["path"]), expected, f"{name} ROM")
    artifact = policy["t01_artifact"]
    result_path = root / str(artifact["result"])
    if result_path.is_symlink() or not result_path.is_file():
        raise AuditError("T01 result must be a regular non-symlink file")
    result = json.loads(result_path.read_text(encoding="utf-8"))
    if result.get("fingerprint") != artifact["fingerprint"]:
        raise AuditError("T01 fingerprint mismatch")
    observed = {
        f"{item['engine']}/{item['profile']}": item["output_sha256"]
        for item in result.get("builds", [])
        if int(item.get("run", 0)) == 1
    }
    if observed != dict(artifact["outputs"]):
        raise AuditError("T01 output hash contract mismatch")
    classifications = policy.get("classifications")
    if classifications != ["VEGA", "CFRU", "PORT", "RELOCATE", "SAME_TARGET", "UNKNOWN"]:
        raise AuditError("classification vocabulary mismatch")


def _validate_classifications(
    writes: Sequence[Mapping[str, Any]], policy: Mapping[str, Any]
) -> None:
    allowed = set(policy["classifications"])
    followups = set(policy["unknown_contract"]["allowed_followups"])
    identities: set[tuple[Any, ...]] = set()
    for row in writes:
        identity = (
            row.get("write_id"),
        )
        if identity in identities:
            raise AuditError(f"duplicate fixed-write identity: {identity}")
        identities.add(identity)
        classification = row.get("classification")
        if classification not in allowed:
            raise AuditError(f"unclassified fixed write: {identity}: {classification}")
        if not str(row.get("classification_evidence", "")).strip():
            raise AuditError(f"fixed write lacks classification evidence: {identity}")
        start = int(str(row["start"]), 0)
        end = int(str(row["end_exclusive"]), 0)
        if start >= end or int(row.get("size", 0)) != end - start:
            raise AuditError(f"invalid fixed-write interval: {identity}")
        if classification == "UNKNOWN":
            if not str(row.get("evidence", "")).strip():
                raise AuditError(f"UNKNOWN lacks evidence: {identity}")
            if row.get("followup_task") not in followups:
                raise AuditError(f"UNKNOWN lacks valid follow-up: {identity}")


def validate_models(
    policy: Mapping[str, Any],
    source: Mapping[str, Any],
    rom: Mapping[str, Any],
    state: Mapping[str, Any],
) -> None:
    for label, model in (("source", source), ("rom", rom), ("state", state)):
        if model.get("schema_version") != 1:
            raise AuditError(f"{label} model schema mismatch")
    writes = _normalise_source_writes(source)
    if not writes:
        raise AuditError("fixed-write model is empty")
    provenance = source.get("provenance", {})
    if provenance.get("t01_fingerprint") != policy["t01_artifact"]["fingerprint"]:
        raise AuditError("fixed-write model T01 identity mismatch")
    replay_outputs = {
        f"{row['engine']}/{row['profile']}": row["output_sha256"]
        for row in provenance.get("variant_replays", [])
    }
    if replay_outputs != dict(policy["t01_artifact"]["outputs"]):
        raise AuditError("fixed-write replay output identity mismatch")
    _validate_classifications(writes, policy)
    summary = source.get("summaries", {})
    if int(summary.get("write_count", -1)) != len(writes):
        raise AuditError("fixed-write summary count mismatch")
    raw_rows = source.get("writes", [])
    overlap_pairs = {
        tuple(sorted((str(row["write_id"]), str(other))))
        for row in raw_rows
        for other in row.get("overlaps", [])
    }
    source_policy = policy.get("source_writes", {})
    direct_overlaps = source_policy.get("allowed_overlaps", [])
    cross_overlaps = expand_cross_engine_overlap_template(
        source_policy.get("allowed_cross_engine_overlap_template")
    )
    expected_overlap_count = len(direct_overlaps) + len(cross_overlaps)
    if (
        len(overlap_pairs) != expected_overlap_count
        or len(overlap_pairs) != int(summary.get("overlap_pair_count", -1))
        or len(direct_overlaps) != int(summary.get("allowed_overlap_pair_count", -1))
        or len(cross_overlaps)
        != int(summary.get("allowed_cross_engine_overlap_pair_count", -1))
        or sum(bool(row.get("overlaps")) for row in raw_rows)
        != int(summary.get("overlap_row_count", -1))
    ):
        raise AuditError("fixed-write overlap graph mismatch")
    context_kinds = {"hook", "function_rewrite", "routine_pointer"}
    context_statuses = {
        "NO_VEGA_CHANGE_IN_BOUNDED_CONTEXT",
        "VEGA_CHANGED_IN_BOUNDED_CONTEXT",
        "NOT_A_CODE_CONTAINER_POINTER_TABLE",
    }
    raw_by_id = {str(row.get("write_id")): row for row in raw_rows}
    for row in raw_rows:
        context = row.get("code_context")
        if row.get("source_kind") in context_kinds:
            if not isinstance(context, Mapping) or context.get("raw_bytes_in_model") is not False:
                raise AuditError(f"fixed-write code context missing: {row.get('write_id')}")
            start = int(context.get("start", -1))
            end = int(context.get("end", -1))
            offset_start = int(context.get("rom_offset_start", -1))
            offset_end = int(context.get("rom_offset_end", -1))
            if (
                start >= end
                or offset_start >= offset_end
                or start != 0x08000000 + offset_start
                or end != 0x08000000 + offset_end
                or context.get("containing_function_status") not in context_statuses
            ):
                raise AuditError(f"fixed-write code context span/status mismatch: {row.get('write_id')}")
            for reference in ("clean", "vega", "factory"):
                digest = context.get(reference)
                if (
                    not isinstance(digest, Mapping)
                    or not re.fullmatch(r"[0-9a-f]{64}", str(digest.get("sha256", "")))
                    or int(digest.get("length", -1)) != offset_end - offset_start
                ):
                    raise AuditError(
                        f"fixed-write code context digest mismatch: {row.get('write_id')}/{reference}"
                    )
        elif context is not None:
            raise AuditError(f"unexpected fixed-write code context: {row.get('write_id')}")
    representatives = summary.get("representative_code_disassembly")
    if not isinstance(representatives, list) or len(representatives) != 4:
        raise AuditError("representative code disassembly mismatch")
    representative_ids: set[str] = set()
    for item in representatives:
        if not isinstance(item, Mapping):
            raise AuditError("representative code disassembly row is invalid")
        write_id = str(item.get("write_id", ""))
        raw = raw_by_id.get(write_id)
        context = raw.get("code_context") if isinstance(raw, Mapping) else None
        if (
            write_id in representative_ids
            or not isinstance(context, Mapping)
            or raw.get("source_kind") not in {"hook", "function_rewrite"}
            or int(item.get("context_start", -1)) != int(context.get("start", -2))
            or int(item.get("context_end", -1)) != int(context.get("end", -2))
            or item.get("raw_opcode_bytes_in_model") is not False
        ):
            raise AuditError(f"representative code disassembly identity mismatch: {write_id}")
        representative_ids.add(write_id)
        start = int(item["context_start"])
        end = int(item["context_end"])
        for reference in ("clean", "vega", "factory"):
            instructions = item.get(reference)
            if not isinstance(instructions, list) or not instructions:
                raise AuditError(
                    f"representative code disassembly is empty: {write_id}/{reference}"
                )
            previous = start - 1
            for instruction in instructions:
                if not isinstance(instruction, Mapping):
                    raise AuditError(
                        f"representative code instruction is invalid: {write_id}/{reference}"
                    )
                address = int(instruction.get("address", -1))
                text = str(instruction.get("instruction", "")).strip()
                if not (start <= address < end) or address <= previous or not text:
                    raise AuditError(
                        f"representative code instruction span mismatch: {write_id}/{reference}"
                    )
                previous = address
    validate_state_inventory(state, policy)
    map_model = rom.get("maps", {})
    encounter_model = rom.get("encounters", {})
    trainer_model = rom.get("trainers", {})
    maps = map_model.get("rows")
    encounters = encounter_model.get("rows")
    trainers = trainer_model.get("rows")
    if not isinstance(maps, list) or len(maps) != policy["maps"]["expected_physical_map_count"]:
        raise AuditError(f"Vega map count mismatch: {len(maps) if isinstance(maps, list) else 'invalid'}")
    if len({int(row["group"]) for row in maps}) != policy["maps"]["expected_group_count"]:
        raise AuditError("Vega map group count mismatch")
    if max(int(value) for value in map_model.get("group_sizes", [])) > int(
        policy["maps"]["maximum_maps_per_group"]
    ):
        raise AuditError("Vega map group exceeds the signed map-ID contract")
    early_port = map_model.get("early_port", {})
    if early_port.get("free_runtime_object_slots") != 0 or early_port.get(
        "new_static_object_allowed"
    ):
        raise AuditError("Aeshia port cannot accept another static object")
    if not isinstance(encounters, list) or len(encounters) != policy["encounters"]["expected_header_count"]:
        raise AuditError("Vega encounter count mismatch")
    if encounter_model.get("terminator") != [
        policy["encounters"]["terminator_group"],
        policy["encounters"]["terminator_map"],
    ]:
        raise AuditError("Vega encounter terminator mismatch")
    expected_trainer_count = int(policy["ids"]["vega_trainer_table"]["count"])
    if not isinstance(trainers, list) or len(trainers) != expected_trainer_count:
        raise AuditError("Vega trainer count mismatch")
    if not trainer_model.get("required_roles_validated"):
        raise AuditError("required Vega trainer roles are not classified")
    if int(trainer_model.get("role_counts", {}).get("gym_leader", 0)) != 8:
        raise AuditError("Vega trainer baseline does not contain exactly eight gym leaders")
    for row in trainers:
        if row.get("role") == "UNKNOWN" and (
            not row.get("evidence") or not row.get("followup_task")
        ):
            raise AuditError("UNKNOWN trainer row lacks evidence/follow-up")
        if row.get("reward") in {None, ""}:
            raise AuditError("Vega trainer row lacks a ROM-rooted reward baseline")
    unlock = rom.get("early_unlock", {})
    if unlock.get("required_flags") != policy["early_unlock"]["required_flags"]:
        raise AuditError("early travel unlock source mismatch")
    if unlock.get("operator") != "AND" or not unlock.get("validated"):
        raise AuditError("early travel unlock is not an exact two-source predicate")
    if set(unlock.get("referenced_flags", ())) & set(policy["early_unlock"]["forbidden_inferred_flags"]):
        raise AuditError("early travel uses a forbidden inferred flag")
    travel = map_model.get("travel_state", {})
    if travel.get("map_id_abi", {}).get("physical_max") != int(
        policy["maps"]["maximum_maps_per_group"]
    ):
        raise AuditError("signed map-ID ABI is not explicit")
    if travel.get("hidden_items", {}).get("flag_index_bits") != 8:
        raise AuditError("hidden-item flag width is not explicit")
    required_warps = {
        "location",
        "continue_game_warp",
        "dynamic_warp",
        "last_heal_location",
        "escape_warp",
    }
    if set(travel.get("save_warp_abi", {}).get("records", {})) != required_warps:
        raise AuditError("warp/heal/Fly/Escape save ownership is incomplete")
    combined_qol = _qol_inventory_rows(policy, source, state)
    observed_qol = {str(row.get("domain")) for row in combined_qol}
    missing_qol = set(policy["qol_required_domains"]) - observed_qol
    if missing_qol:
        raise AuditError(f"missing QOL domains: {sorted(missing_qol)}")


def _markdown_table(headers: Sequence[str], rows: Iterable[Sequence[Any]]) -> list[str]:
    output = [
        "|" + "|".join(headers) + "|",
        "|" + "|".join("---" for _ in headers) + "|",
    ]
    for values in rows:
        cells = [str(value).replace("|", "\\|").replace("\n", " ") for value in values]
        output.append("|" + "|".join(cells) + "|")
    return output


def _render_semantic_conflicts(
    policy: Mapping[str, Any], source: Mapping[str, Any]
) -> str:
    writes = _normalise_source_writes(source)
    counts = Counter(str(row["classification"]) for row in writes)
    conflicts = [
        row
        for row in writes
        if row["classification"] in {"VEGA", "PORT", "RELOCATE", "UNKNOWN"}
    ]
    overlap_pairs = sorted(
        {
            tuple(sorted((str(row["write_id"]), str(other))))
            for row in writes
            for other in row.get("overlaps", [])
        }
    )
    lines = [
        "# T02 fixed-write semantic conflicts",
        "",
        f"- T01 fingerprint: `{policy['t01_artifact']['fingerprint']}`",
        f"- fixed writes: {len(writes)}",
        "- classifications: "
        + ", ".join(f"{key}={counts.get(key, 0)}" for key in policy["classifications"]),
        "- `.org`やfunction rewriteは推測1 byteではなく、source-write modelの実emission spanを使用する。",
        "",
        "## 要統合・再配置site",
        "",
    ]
    lines.extend(
        _markdown_table(
            ("write_id", "kind", "symbol", "interval", "class", "reason", "follow-up"),
            (
                (
                    row["write_id"],
                    row["kind"],
                    row.get("symbol", ""),
                    f"{row['start']}..{row['end_exclusive']}",
                    row["classification"],
                    row["classification_evidence"],
                    row.get("followup_task", ""),
                )
                for row in conflicts
            ),
        )
    )
    lines.extend(("", f"## Fixed-write overlaps ({len(overlap_pairs)} pairs)", ""))
    lines.extend(
        _markdown_table(
            ("left write_id", "right write_id"), overlap_pairs
        )
    )
    disassembly = source.get("summaries", {}).get(
        "representative_code_disassembly", []
    )
    if not isinstance(disassembly, list) or len(disassembly) != 4:
        raise AuditError("representative bounded disassembly contract is incomplete")
    lines.extend(("", "## 代表code hookのbounded Thumb disassembly", ""))
    for item in disassembly:
        lines.extend(
            (
                f"### `{item['write_id']}`",
                "",
                f"- context: `0x{int(item['context_start']):08X}.."
                f"0x{int(item['context_end']):08X}`",
                f"- selection: {item['selection']}",
                "- clean:",
                "",
                "```text",
                *(
                    f"0x{int(row['address']):08X}  {row['instruction']}"
                    for row in item["clean"]
                ),
                "```",
                "- Vega:",
                "",
                "```text",
                *(
                    f"0x{int(row['address']):08X}  {row['instruction']}"
                    for row in item["vega"]
                ),
                "```",
                "- Factory:",
                "",
                "```text",
                *(
                    f"0x{int(row['address']):08X}  {row['instruction']}"
                    for row in item["factory"]
                ),
                "```",
                "",
            )
        )
    return "\n".join(lines) + "\n"


def _render_facility(state: Mapping[str, Any]) -> str:
    facilities = state["facilities"]
    currencies = state["currencies"]
    lines = [
        "# T02 Battle Factory / Mirage state audit",
        "",
        "FactoryとMirageはparty、record、reward、通貨、exit recoveryを共有しない。raw固定値は統合版symbolへ再配置する。",
        "",
    ]
    for name in ("factory", "mirage"):
        item = facilities[name]
        lines.extend((f"## {name}", "", f"- classification: `{item['classification']}`"))
        for key in (
            "state_fields",
            "transitions",
            "specials",
            "trainers",
            "maps",
            "music",
            "rewards",
            "records",
            "bounds",
            "fixture",
            "respawn_id",
            "policy",
            "party_transaction",
            "abnormal_exit_paths",
        ):
            lines.append(f"- {key}: `{json.dumps(item.get(key, []), ensure_ascii=False, sort_keys=True)}`")
        lines.append("")
    lines.extend(("## Currency", ""))
    for key, value in sorted(currencies.items()):
        lines.extend(
            (
                f"### {key}",
                "",
                f"- availability: `{value.get('availability', '')}`",
                f"- owner/storage: `{value.get('owner', '')}` / "
                f"`{value.get('storage', '')}`",
                f"- width/cap/enabled: `{value.get('width_bits', '')}` / "
                f"`{value.get('cap', '')}` / `{value.get('enabled', False)}`",
                f"- required_operations: `{json.dumps(value.get('required_operations', []), ensure_ascii=False)}`",
                f"- operations: `{json.dumps(value.get('operations', {}), ensure_ascii=False, sort_keys=True)}`",
                f"- earn_hooks: `{json.dumps(value.get('earn_hooks', []), ensure_ascii=False)}`",
                f"- spend_hooks: `{json.dumps(value.get('spend_hooks', []), ensure_ascii=False)}`",
                "",
            )
        )
    lines.extend(("", "## Coexistence assertions", ""))
    lines.extend(f"- {item}" for item in state.get("assertions", []))
    return "\n".join(lines) + "\n"


def _render_ai(policy: Mapping[str, Any], state: Mapping[str, Any]) -> str:
    ai = state["ai"]
    lines = [
        "# T02 Trainer AI hook/cache/RNG/knowledge audit",
        "",
        f"- active aliases: `{json.dumps(policy['ai']['aliases'], sort_keys=True)}`",
        f"- hook expected-byte assertions: {len(ai['hooks'])}",
        f"- cache/lifetime entries: {len(ai['cache_lifetimes'])}",
        f"- RNG domains: `{json.dumps(ai['rng_domains'], ensure_ascii=False)}`",
        f"- knowledge domains: `{json.dumps(ai['knowledge'], ensure_ascii=False, sort_keys=True)}`",
        f"- exact ABI: `{json.dumps(ai['abi'], ensure_ascii=False, sort_keys=True)}`",
        f"- inactive configs: `{json.dumps(ai['inactive_configs'], ensure_ascii=False, sort_keys=True)}`",
        f"- fixture: `{json.dumps(ai['fixture'], ensure_ascii=False, sort_keys=True)}`",
        "- global difficulty / level scaling configは暗黙に有効化しない。",
        "",
        "## Hooks",
        "",
    ]
    lines.extend(
        _markdown_table(
            ("address", "Vega expected", "owner", "resolution", "evidence"),
            (
                (
                    row["address"],
                    row["vega_expected"],
                    row["owner"],
                    row["resolution"],
                    row["evidence"],
                )
                for row in ai["hooks"]
            ),
        )
    )
    lines.extend(("", "## Cache lifetime / invalidation", ""))
    lines.extend(
        _markdown_table(
            ("key", "storage", "lifetime", "invalidation", "resolution", "evidence"),
            (
                (
                    row["key"],
                    row["storage"],
                    row["lifetime"],
                    json.dumps(row["invalidation"], ensure_ascii=False),
                    row["resolution"],
                    row["evidence"],
                )
                for row in ai["cache_lifetimes"]
            ),
        )
    )
    return "\n".join(lines) + "\n"


def _id_inventory(
    policy: Mapping[str, Any], rom: Mapping[str, Any], state: Mapping[str, Any]
) -> dict[str, Any]:
    map_contract = {
        key: value
        for key, value in rom["maps"].items()
        if key not in {"rows", "details"}
    }
    encounter_contract = {
        key: value
        for key, value in rom["encounters"].items()
        if key not in {"rows", "details"}
    }
    trainer_contract = {
        key: value
        for key, value in rom["trainers"].items()
        if key not in {"rows", "details"}
    }
    return {
        "schema_version": 1,
        "policy_id": policy["policy_id"],
        "source_lock_sha256": policy["source_lock"]["sha256"],
        "inputs": {
            name: {"size": value["size"], "sha256": value["sha256"]}
            for name, value in policy["inputs"].items()
        },
        "domains": state["id_domains"],
        "ranges": state.get("id_ranges", []),
        "cross_domain_aliases": state.get("cross_domain_aliases", []),
        "script_references": rom.get("script_references", {}).get("rows", []),
        "script_graph": rom.get("script_references", {}).get("graph", {}),
        "rom_provenance": rom.get("provenance", {}),
        "early_unlock": rom["early_unlock"],
        "map_contract": map_contract,
        "map_details": rom["maps"]["details"],
        "encounter_contract": encounter_contract,
        "encounter_details": rom["encounters"]["details"],
        "trainer_contract": trainer_contract,
        "trainer_details": rom["trainers"]["details"],
        "facilities": state["facilities"],
        "currencies": state["currencies"],
        "ai": state["ai"],
        "assertions": state.get("assertions", []),
        "summaries": {
            "domain_rows": len(state["id_domains"]),
            "script_references": len(rom.get("script_references", {}).get("rows", [])),
        },
    }


def generate(
    root: Path,
    policy_path: Path,
    output_dir: Path | None = None,
) -> dict[str, Any]:
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    validate_policy(root, policy)
    source = build_source_write_model(root, policy)
    rom = build_rom_inventory(root, policy)
    state = build_state_inventory(root, policy)
    validate_models(policy, source, rom, state)
    writes = _normalise_source_writes(source)

    generated = output_dir if output_dir is not None else root / "reports/generated"
    _write_csv(generated / "address_audit.csv", ADDRESS_FIELDS, writes)
    _atomic_text(generated / "semantic_conflicts.md", _render_semantic_conflicts(policy, source))
    _write_csv(generated / "ram_map.csv", RANGE_FIELDS, state["ram_ranges"])
    _write_csv(generated / "save_map.csv", RANGE_FIELDS, state["save_ranges"])
    write_json(generated / "id_inventory.json", _id_inventory(policy, rom, state))
    _write_csv(generated / "vega_map_inventory.csv", MAP_FIELDS, rom["maps"]["rows"])
    _write_csv(
        generated / "vega_encounter_inventory.csv",
        ENCOUNTER_FIELDS,
        rom["encounters"]["rows"],
    )
    combined_qol = _qol_inventory_rows(policy, source, state)
    _write_csv(generated / "qol_hook_inventory.csv", QOL_FIELDS, combined_qol)
    _atomic_text(generated / "facility_audit.md", _render_facility(state))
    _write_csv(
        generated / "vega_trainer_baseline.csv",
        TRAINER_FIELDS,
        rom["trainers"]["rows"],
    )
    _atomic_text(generated / "trainer_ai_audit.md", _render_ai(policy, state))

    output_hashes = {
        relative: sha256_file(generated / Path(relative).name)
        for relative in policy["outputs"]
    }
    return {
        "schema_version": 1,
        "status": "PASS",
        "policy_sha256": sha256_file(policy_path),
        "t01_fingerprint": policy["t01_artifact"]["fingerprint"],
        "counts": {
            "fixed_writes": len(writes),
            "ram_ranges": len(state["ram_ranges"]),
            "save_ranges": len(state["save_ranges"]),
            "id_rows": len(state["id_domains"]),
            "maps": len(rom["maps"]["rows"]),
            "encounters": len(rom["encounters"]["rows"]),
            "trainers": len(rom["trainers"]["rows"]),
            "script_references": len(
                rom.get("script_references", {}).get("rows", [])
            ),
            "qol_hooks": len(combined_qol),
        },
        "outputs": output_hashes,
    }


def parser() -> argparse.ArgumentParser:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument(
        "--policy",
        type=Path,
        default=Path("config/t02_audit_policy.json"),
    )
    return cli


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    root = repo_root()
    try:
        result = generate(root, root / args.policy)
    except (AuditError, OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print("RESULT=DONE TASK=T02 VERIFY=PASS COMMIT=-")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
