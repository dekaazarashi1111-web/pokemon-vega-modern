#!/usr/bin/env python3
"""工程7: 独自習得差分のlayer/precedence/conflict契約。

工程3の原作復元表とVega独自追加を混ぜず、提出済みの追加・削除だけを
key-firstで解決する。現時点では工程7向け配布表が提出されていないため、
両方向の採用差分は明示的に0件となる。
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping, NoReturn, Sequence

from tools.modernization_identity import CheckedArchive, ManifestIndex, load_manifests


SCHEMA_VERSION = 1
TASK = "USER-MODERNIZATION-P07"

LEARNSETS_ZIP = (
    "userfile/imports/modernization_p01/"
    "Pokemon_Vega_Stage61_技習得品質改善版_v1.3.0_20260905.zip"
)
RESTORATION_ZIP = (
    "userfile/imports/modernization_p01/"
    "Vega_Stage61_ID固定_原作復元監査資料.zip"
)
LEARNSETS_README = (
    "Pokemon_Vega_Stage61_Learnsets_v1_3_20260905/README_JA.md"
)
LEARNSETS_SCHEMA = (
    "Pokemon_Vega_Stage61_Learnsets_v1_3_20260905/SCHEMA_JA.md"
)
RESTORATION_README = "README_読んでください.txt"

EXPECTED_INPUTS = {
    "content/modernization/p03_learnset_contract.json":
        "4e421a5c6110ad5b4e2de399d354b058b566815aaf5aa30b8cc445cba38a6033",
    "content/modernization/p03_compiled_index.json":
        "a4258048c50df88ecbaf2525e04edaa6f2440da2a79d2f336ccb67e3a2362751",
    "content/modernization/p03_runtime_handoff.json":
        "2458a0b3299f318f4a08dc460df6db876ea4f5f2347e6f8c48541d9b8a9f0479",
    "content/modernization/p04_candidate_manifest.json":
        "64e9ffbc80a4344eef82726c191da25b008c6f7d87312c2bf8186c00a36c5644",
    "content/modernization/p05_battle_content_contract.json":
        "4107be2afbf74d25306da2b832430e007d46028e5fa3004f6eef3de15112cbf0",
    "content/modernization/p06_species_adjustment_contract.json":
        "1e26b64de260e30c266a0b7af02621bbd602d865436db793443b7428ae996405",
    "content/modernization/p06_review_projection.json":
        "04efc32cb54e2f0adf8cbb5d4de480c322188e709856d876198f57d27427f01f",
}
EXPECTED_MEMBER_HASHES = {
    LEARNSETS_README: "2a33bc7a2499c75134e8f7b543fff49b4dc3664dfb0838db3fe3c488afdbaeb3",
    LEARNSETS_SCHEMA: "7f873ab9aa3853d9d926d3d6fb8ea4b9fbc3e8396f3717d2cb301f6c8951ef80",
    RESTORATION_README: "49eef1f2fab8cae1183e91172e91ad845cd9ed8d5d2804ba150add09a0bbffb6",
}

NORMAL_TO_VEGA = "NORMAL_SPECIES_TO_VEGA_MOVE"
VEGA_TO_NORMAL = "VEGA_SPECIES_TO_NORMAL_MOVE"
DIRECTIONS = frozenset({NORMAL_TO_VEGA, VEGA_TO_NORMAL})

CONSUMER_BY_ROUTE = {
    ("direct", "level_up"): "level_up",
    ("direct", "evolution"): "evolution",
    ("direct", "reminder"): "reminder",
    ("direct", "tm"): "machine",
    ("direct", "tr"): "machine",
    ("direct", "tutor"): "tutor",
    ("direct", "egg"): "egg",
    ("direct", "special_breeding"): "egg",
    ("direct", "form_move"): "form_change",
    ("direct", "battle_transform"): "form_change",
    ("pre_evolution", "level_up"): "pre_evolution_carry",
    ("pre_evolution", "evolution"): "pre_evolution_carry",
    ("pre_evolution", "reminder"): "pre_evolution_carry",
    ("pre_evolution", "tm"): "pre_evolution_carry",
    ("pre_evolution", "tr"): "pre_evolution_carry",
    ("pre_evolution", "tutor"): "pre_evolution_carry",
    ("pre_evolution", "egg"): "pre_evolution_carry",
    ("shared_egg", "shared_egg"): "shared_egg",
    ("form_change", "level_up"): "form_change",
    ("form_change", "form_move"): "form_change",
    ("form_change", "battle_transform"): "form_change",
}

REQUIRED_ADDITION_FIELDS = frozenset(
    {
        "change_key",
        "direction",
        "target_species_key",
        "target_form_key",
        "move_key",
        "route_kind",
        "method",
        "level",
        "conditions",
        "availability",
        "intent_ja",
        "source_decision_ref",
        "p06_review_key",
        "existing_moveset_policy",
    }
)
REQUIRED_AVAILABILITY_FIELDS = frozenset(
    {"timing_ja", "restriction_ja", "relearn_policy"}
)
MACHINE_AVAILABILITY_FIELDS = frozenset(
    {"supply_key", "runtime_slot_key", "cost_policy", "unlock_key", "cancel_policy"}
)


class ModernizationP07Error(ValueError):
    """工程7の採用差分またはlayer契約違反。"""


def _fail(message: str) -> NoReturn:
    raise ModernizationP07Error(message)


def stable_json(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    ).encode("utf-8")


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _regular_file(path: Path, label: str) -> bytes:
    if path.is_symlink() or not path.is_file():
        _fail(f"{label}が通常ファイルではありません: {path}")
    return path.read_bytes()


def _load_json(
    root: Path, relative: str, expected_hash: str
) -> tuple[dict[str, Any], dict[str, Any]]:
    raw = _regular_file(root / relative, relative)
    digest = _sha256(raw)
    if digest != expected_hash:
        _fail(f"上流工程成果hashが不一致です: {relative}: {digest} != {expected_hash}")
    try:
        value = json.loads(raw.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        _fail(f"上流工程成果がUTF-8 JSONではありません: {relative}: {error}")
    if not isinstance(value, dict):
        _fail(f"上流工程成果のrootがobjectではありません: {relative}")
    return value, {"path": relative, "size": len(raw), "sha256": digest}


def _member_evidence(name: str, raw: bytes) -> dict[str, Any]:
    return {"path": name, "size": len(raw), "sha256": _sha256(raw)}


def _require_fields(row: Mapping[str, Any], fields: Iterable[str], label: str) -> None:
    missing = sorted(set(fields) - set(row))
    if missing:
        _fail(f"{label}の必須fieldがありません: {missing}")


def _nonempty(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        _fail(f"{label}が空または文字列ではありません")
    return value


def _canonical_species_domain(row: Mapping[str, str]) -> str:
    if row.get("classification") == "VEGA_ORIGINAL":
        return "VEGA_SPECIES"
    if row.get("is_official") == "true":
        return "NORMAL_SPECIES"
    return "INTERNAL_EXCLUDED"


def _canonical_move_domain(row: Mapping[str, str]) -> str:
    if row.get("classification") == "VEGA_EXCLUSIVE_V3":
        return "VEGA_MOVE"
    if row.get("move_key") != "MOVE_KEY_NONE" and row.get("classification") in {
        "VEGA_CFRU_CANONICAL", "CFRU_APPEND"
    }:
        return "NORMAL_MOVE"
    return "INTERNAL_OR_COMPATIBILITY_ONLY"


def _route_consumer(route_kind: Any, method: Any, label: str) -> str:
    pair = (route_kind, method)
    consumer = CONSUMER_BY_ROUTE.get(pair)
    if consumer is None:
        _fail(f"{label}のroute_kind/method組合せが未対応です: {pair}")
    return consumer


def validate_and_resolve_additions(
    rows: Sequence[Mapping[str, Any]],
    species: ManifestIndex,
    moves: ManifestIndex,
    *,
    p04_unallocated_species_keys: frozenset[str] = frozenset(),
    unavailable_move_keys: frozenset[str] = frozenset(),
    p06_ready: bool,
) -> list[dict[str, Any]]:
    """提出済み独自追加を解決する。空配列は有効な「採用差分0件」。"""

    resolved: list[dict[str, Any]] = []
    seen_change_keys: set[str] = set()
    seen_route_identity: dict[tuple[Any, ...], str] = {}
    for position, source in enumerate(rows):
        if not isinstance(source, Mapping):
            _fail(f"独自追加rowがobjectではありません: row={position}")
        label = f"独自追加row {position}"
        _require_fields(source, REQUIRED_ADDITION_FIELDS, label)
        unexpected_numeric = sorted(
            key for key in source
            if key in {"target_species_id", "move_id", "canonical_id", "project_move_id"}
        )
        if unexpected_numeric:
            _fail(f"{label}は数値IDを入力identityにできません: {unexpected_numeric}")
        change_key = _nonempty(source["change_key"], f"{label}:change_key")
        if re.fullmatch(r"P07_[A-Z0-9_]+", change_key) is None:
            _fail(f"{label}:change_keyが名前空間外です: {change_key}")
        if change_key in seen_change_keys:
            _fail(f"独自追加change_keyが重複しています: {change_key}")
        seen_change_keys.add(change_key)
        direction = source["direction"]
        if direction not in DIRECTIONS:
            _fail(f"{label}:directionが未対応です: {direction}")

        species_key = _nonempty(
            source["target_species_key"], f"{label}:target_species_key"
        )
        move_key = _nonempty(source["move_key"], f"{label}:move_key")
        if species_key in p04_unallocated_species_keys:
            _fail(f"{label}はP04未割当Speciesを参照しています: {species_key}")
        species_row = species.by_key.get(species_key)
        if species_row is None:
            _fail(f"{label}のSpecies keyがmanifestにありません: {species_key}")
        move_row = moves.by_key.get(move_key)
        if move_row is None:
            if move_key in unavailable_move_keys:
                _fail(f"{label}のMoveはruntime未実装です: {move_key}")
            _fail(f"{label}のMove keyがmanifestにありません: {move_key}")

        form_key = source["target_form_key"]
        if not isinstance(form_key, str) or form_key != species_row.get("form_key", ""):
            _fail(f"{label}のform keyがSpecies manifestと不一致です: {form_key!r}")
        species_domain = _canonical_species_domain(species_row)
        move_domain = _canonical_move_domain(move_row)
        expected_domains = {
            NORMAL_TO_VEGA: ("NORMAL_SPECIES", "VEGA_MOVE"),
            VEGA_TO_NORMAL: ("VEGA_SPECIES", "NORMAL_MOVE"),
        }[direction]
        if (species_domain, move_domain) != expected_domains:
            _fail(
                f"{label}の方向とSpecies/Move分類が不一致です: "
                f"{species_domain}/{move_domain}"
            )

        consumer = _route_consumer(source["route_kind"], source["method"], label)
        level = source["level"]
        conditions = source["conditions"]
        availability = source["availability"]
        if not isinstance(conditions, Mapping) or not isinstance(availability, Mapping):
            _fail(f"{label}のconditions/availabilityがobjectではありません")
        _require_fields(availability, REQUIRED_AVAILABILITY_FIELDS, f"{label}:availability")
        for field in REQUIRED_AVAILABILITY_FIELDS:
            _nonempty(availability[field], f"{label}:availability:{field}")
        if source["route_kind"] in {"pre_evolution", "form_change"}:
            # これはtargetの直習得levelではない。継承元levelやform条件を
            # conditions側で保持し、direct level-upへ平坦化しない。
            if level is not None:
                _fail(f"{label}の間接経路にtarget levelが設定されています")
        elif source["method"] == "level_up":
            if not isinstance(level, int) or isinstance(level, bool) or not 1 <= level <= 100:
                _fail(f"{label}のlevel_up levelが1..100ではありません")
        elif level is not None:
            _fail(f"{label}の非level_up経路にlevelが設定されています")

        if consumer in {"machine", "tutor"}:
            _require_fields(
                availability, MACHINE_AVAILABILITY_FIELDS, f"{label}:machine availability"
            )
            for field in MACHINE_AVAILABILITY_FIELDS:
                _nonempty(availability[field], f"{label}:availability:{field}")
        condition_identity: dict[str, Any] = {}
        if source["route_kind"] == "pre_evolution":
            donor_key = _nonempty(
                conditions.get("donor_species_key"), f"{label}:donor_species_key"
            )
            donor = species.by_key.get(donor_key)
            if donor is None:
                _fail(f"{label}:donor Species keyがmanifestにありません: {donor_key}")
            condition_identity = {
                "donor_species_key": donor_key,
                "donor_species_id": int(donor["id"]),
                "donor_form_key": donor.get("form_key", ""),
            }
            donor_level = conditions.get("donor_learning_level")
            if source["method"] == "level_up" and (
                not isinstance(donor_level, int)
                or isinstance(donor_level, bool)
                or not 1 <= donor_level <= 100
            ):
                _fail(f"{label}:donor_learning_levelが1..100ではありません")
        if source["route_kind"] == "shared_egg":
            _nonempty(conditions.get("shared_egg_source_key"), f"{label}:shared_egg_source_key")
        if consumer == "form_change":
            _nonempty(conditions.get("form_change_condition_ja"), f"{label}:form condition")

        _nonempty(source["intent_ja"], f"{label}:intent_ja")
        _nonempty(source["source_decision_ref"], f"{label}:source_decision_ref")
        _nonempty(source["p06_review_key"], f"{label}:p06_review_key")
        if source["existing_moveset_policy"] != "NEW_GENERATION_AND_LEARNING_ONLY":
            _fail(f"{label}が既存party/box/trainer技を一括変更しようとしています")
        if not p06_ready:
            _fail(f"{label}はP06 review完了前なので採用できません")

        identity = (species_key, form_key, move_key, consumer)
        previous = seen_route_identity.get(identity)
        if previous is not None:
            _fail(
                "同一対象/技/consumerの独自追加が競合しています: "
                f"{previous} / {change_key}"
            )
        seen_route_identity[identity] = change_key
        resolved.append(
            {
                **dict(source),
                "target_species_id": int(species_row["id"]),
                "move_id": int(move_row["id"]),
                "consumer": consumer,
                "species_domain": species_domain,
                "move_domain": move_domain,
                "condition_identity": condition_identity,
            }
        )
    return sorted(resolved, key=lambda row: row["change_key"])


def validate_and_resolve_deletions(
    rows: Sequence[Mapping[str, Any]],
    additions: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """明示削除だけを最上位layerへ解決し、暗黙の後勝ちを拒否する。"""

    addition_by_key = {str(row["change_key"]): row for row in additions}
    seen: set[str] = set()
    seen_targets: set[tuple[str, str]] = set()
    resolved: list[dict[str, Any]] = []
    required = {
        "deletion_key", "target_layer", "target_change_key", "p03_route_id",
        "reason_ja", "source_decision_ref",
    }
    for position, source in enumerate(rows):
        if not isinstance(source, Mapping):
            _fail(f"明示削除rowがobjectではありません: row={position}")
        label = f"明示削除row {position}"
        _require_fields(source, required, label)
        key = _nonempty(source["deletion_key"], f"{label}:deletion_key")
        if re.fullmatch(r"P07_DELETE_[A-Z0-9_]+", key) is None or key in seen:
            _fail(f"明示削除keyが不正または重複です: {key}")
        seen.add(key)
        target_layer = source["target_layer"]
        if target_layer == "P03_ORIGINAL_RESTORATION":
            if source["target_change_key"] is not None:
                _fail(f"{label}:P03削除にcustom change keyがあります")
            route_id = source["p03_route_id"]
            if not isinstance(route_id, str) or re.fullmatch(r"[0-9a-f]{24}", route_id) is None:
                _fail(f"{label}:P03 route IDが不正です")
            # compact P03成果はroute本文を持たないため、実採用にはstream照合が必要。
            verification = "P03_STREAM_ROUTE_RESOLUTION_REQUIRED"
        elif target_layer in {
            "P07_NORMAL_SPECIES_TO_VEGA_MOVE", "P07_VEGA_SPECIES_TO_NORMAL_MOVE"
        }:
            target = source["target_change_key"]
            if not isinstance(target, str) or target not in addition_by_key:
                _fail(f"{label}:削除対象custom additionがありません: {target!r}")
            expected_layer = (
                "P07_NORMAL_SPECIES_TO_VEGA_MOVE"
                if addition_by_key[target]["direction"] == NORMAL_TO_VEGA
                else "P07_VEGA_SPECIES_TO_NORMAL_MOVE"
            )
            if target_layer != expected_layer or source["p03_route_id"] is not None:
                _fail(f"{label}:削除対象layer/route identityが不一致です")
            verification = "TARGET_CUSTOM_CHANGE_RESOLVED"
        else:
            _fail(f"{label}:target_layerが未対応です: {target_layer}")
        target_identity = (
            str(target_layer),
            str(source["p03_route_id"] or source["target_change_key"]),
        )
        if target_identity in seen_targets:
            _fail(f"同じlower-layer routeを複数回削除しています: {target_identity}")
        seen_targets.add(target_identity)
        _nonempty(source["reason_ja"], f"{label}:reason_ja")
        _nonempty(source["source_decision_ref"], f"{label}:source_decision_ref")
        resolved.append({**dict(source), "verification": verification})
    return sorted(resolved, key=lambda row: row["deletion_key"])


def _validate_upstream_contracts(
    p03: Mapping[str, Any],
    p03_index: Mapping[str, Any],
    p03_runtime: Mapping[str, Any],
    p04: Mapping[str, Any],
    p05: Mapping[str, Any],
    manifests: Mapping[str, ManifestIndex],
) -> dict[str, Any]:
    if p03.get("task") != "USER-MODERNIZATION-P03" or p03.get("status") != "PASS":
        _fail("P03原作習得契約がPASSではありません")
    adoption = p03.get("corrected_adoption")
    if not isinstance(adoption, Mapping) or adoption.get("records") != 1300 \
            or adoption.get("routes") != 118_528:
        _fail("P03原作習得のrecord/route件数が固定値と不一致です")
    records = p03_index.get("records")
    if (
        p03_index.get("record_count") != 1300
        or p03_index.get("route_count") != 118_528
        or p03_index.get("selected_route_count") != 118_369
        or p03_index.get("excluded_route_count") != 159
        or not isinstance(records, list)
        or len(records) != 1300
    ):
        _fail("P03 compact indexが原作習得契約と不一致です")
    seen: set[str] = set()
    classifications: Counter[str] = Counter()
    for record in records:
        if not isinstance(record, Mapping):
            _fail("P03 compact recordがobjectではありません")
        key = str(record.get("species_key", ""))
        species = manifests["species"].by_key.get(key)
        if species is None or int(species["id"]) != record.get("canonical_id"):
            _fail(f"P03 compact recordがSpecies manifestと不一致です: {key}")
        if key in seen:
            _fail(f"P03 compact species keyが重複しています: {key}")
        seen.add(key)
        domain = _canonical_species_domain(species)
        if domain != "NORMAL_SPECIES":
            _fail(f"P03原作復元対象へVega/Internal Speciesが混入しています: {key}")
        classifications[species["classification"]] += 1

    runtime_selection = p03.get("runtime_selection")
    if not isinstance(runtime_selection, Mapping) \
            or runtime_selection.get("selected_routes") != 118_369 \
            or runtime_selection.get("excluded_routes") != 159:
        _fail("P03 runtime選択集合がSide Change除外後の固定値ではありません")
    side = p03_runtime.get("side_change_1063")
    if not isinstance(side, Mapping) \
            or side.get("status") != "NOT_ADOPTED_BY_USER_DECISION" \
            or side.get("source_route_count") != 159 \
            or side.get("adopted_route_count") != 0 \
            or side.get("excluded_route_count") != 159 \
            or side.get("decision", {}).get("replacement_move_key") is not None:
        _fail("P03 Side Change非採用・無置換判断が失われています")
    if p04.get("task") != "USER-MODERNIZATION-P04" or not isinstance(p04.get("records"), list):
        _fail("P04対象manifestが不正です")
    p04_records = p04["records"]
    learnset_fields = sum(
        field in row
        for row in p04_records if isinstance(row, Mapping)
        for field in ("learnsets", "learnset", "moves", "move_key", "distribution")
    )
    if learnset_fields:
        _fail("P04対象に未契約の習得配布fieldがあります")
    if p05.get("task") != "USER-MODERNIZATION-P05":
        _fail("P05技特性契約が不正です")
    move_content = p05.get("move_content")
    if not isinstance(move_content, Mapping):
        _fail("P05 move_contentがありません")
    if move_content.get("adopted_performance_adjustments") != [] \
            or move_content.get("p04_new_move_requests") != []:
        _fail("P05の確定差分集合が工程7想定から変化しました")
    new_moves = move_content.get("new_move_requirements")
    non_adopted = move_content.get("non_adopted_move_candidates")
    if new_moves != [] or not isinstance(non_adopted, list) \
            or len(non_adopted) != 1 \
            or non_adopted[0].get("move_key") != "MOVE_KEY_ALLYSWITCH" \
            or non_adopted[0].get("selection_status") \
            != "NOT_ADOPTED_BY_USER_DECISION" \
            or non_adopted[0].get("canonical_id") is not None:
        _fail("P05 Side Change非採用境界が工程7想定と不一致です")
    p04_unallocated = {
        str(row["proposed_species_key"])
        for row in p04_records
        if isinstance(row, Mapping) and row.get("implementation_scope") == "ADOPT_CANDIDATE"
    }
    return {
        "p03_species_classifications": dict(sorted(classifications.items())),
        "p03_vega_original_target_count": 0,
        "p03_original_restoration_records": 1300,
        "p03_original_restoration_source_routes": 118_528,
        "p03_original_restoration_routes": 118_369,
        "p04_candidate_records": sum(
            row.get("implementation_scope") == "ADOPT_CANDIDATE"
            for row in p04_records if isinstance(row, Mapping)
        ),
        "p04_learnset_distribution_fields": learnset_fields,
        "p04_unallocated_species_keys": sorted(p04_unallocated),
        "p05_adopted_performance_adjustments": 0,
        "p05_p04_new_move_requests": 0,
        "side_change_1063": {
            "move_key": "MOVE_KEY_ALLYSWITCH",
            "requested_project_id": 1063,
            "canonical_id": None,
            "p03_source_route_count": side["source_route_count"],
            "p03_adopted_route_count": 0,
            "p03_excluded_route_count": side["excluded_route_count"],
            "replacement_move_key": None,
            "status": "P03_NOT_ADOPTED_USER_DECISION_NOT_P07_CUSTOM",
        },
    }


def _p06_observation(
    contract: Mapping[str, Any],
    projection: Mapping[str, Any],
    artifacts: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """P06の空採用checkpointを固定し、完了済みとは解釈しない。"""

    if contract.get("task") != "USER-MODERNIZATION-P06" \
            or contract.get("status") != "CHECKPOINT_ADOPTED_DELTA_EMPTY":
        _fail("P06 Species調整checkpoint identityが不正です")
    adoption = contract.get("adoption")
    handoff = contract.get("handoff")
    partition = contract.get("review_partition")
    if not isinstance(adoption, Mapping) or not isinstance(handoff, Mapping) \
            or not isinstance(partition, Mapping):
        _fail("P06 checkpoint主要sectionがありません")
    if adoption.get("explicit_species_adjustment_spec_received") is not False \
            or adoption.get("adopted_delta_records") != [] \
            or adoption.get("adopted_delta_count") != 0 \
            or adoption.get("runtime_patch_authorized") is not False:
        _fail("P06 checkpointの採用差分0/runtime禁止境界が変化しました")
    if handoff.get("completion_state") != "CHECKPOINT_NOT_P06_DONE" \
            or handoff.get("p07_distribution_must_not_be_applied") is not True:
        _fail("P06未完了/P07配布禁止handoffが失われています")
    if projection.get("task") != "USER-MODERNIZATION-P06" \
            or projection.get("status") != "REVIEW_PROJECTION_ONLY_NOT_ADOPTED":
        _fail("P06 review projection identityが不正です")
    projection_partition = projection.get("partition")
    if not isinstance(projection_partition, Mapping) \
            or projection_partition.get("adopted_delta_count") != 0 \
            or projection_partition.get("vega_custom_submitted_delta_count") != 0:
        _fail("P06 review projectionへ未採用差分が混入しています")
    projection_identity = next(
        (row for row in artifacts if row.get("path") == partition.get("projection_path")),
        None,
    )
    if projection_identity is None \
            or projection_identity.get("sha256") != partition.get("projection_sha256"):
        _fail("P06 contractとreview projectionのhash接続が不一致です")
    return {
        "observed_artifacts": list(artifacts),
        "artifact_count": len(artifacts),
        "contract_status": contract["status"],
        "projection_status": projection["status"],
        "adopted_delta_count": 0,
        "runtime_patch_authorized": False,
        "status": "CHECKPOINT_NOT_P06_DONE_BLOCKING_RUNTIME_ADOPTION",
        "p06_ready_for_p07": False,
        "rule": "P06完了契約と採用review keyが接続されるまで非空P07差分をruntime採用しない",
    }


def build_p07_contract(root: Path) -> dict[str, Any]:
    root = root.resolve()
    manifests = load_manifests(root)
    documents: dict[str, dict[str, Any]] = {}
    identities: dict[str, dict[str, Any]] = {}
    for relative, expected_hash in EXPECTED_INPUTS.items():
        document, identity = _load_json(root, relative, expected_hash)
        documents[relative] = document
        identities[relative] = identity

    with CheckedArchive(root / LEARNSETS_ZIP, "learnsets") as archive:
        readme_name, readme_raw = archive.read(LEARNSETS_README)
        schema_name, schema_raw = archive.read(LEARNSETS_SCHEMA)
        learnsets_identity = archive.identity()
    with CheckedArchive(root / RESTORATION_ZIP, "restoration_audit") as archive:
        restoration_name, restoration_raw = archive.read(RESTORATION_README)
        restoration_identity = archive.identity()
    for name, raw in (
        (LEARNSETS_README, readme_raw),
        (LEARNSETS_SCHEMA, schema_raw),
        (RESTORATION_README, restoration_raw),
    ):
        if _sha256(raw) != EXPECTED_MEMBER_HASHES[name]:
            _fail(f"受領ZIP evidence member hashが不一致です: {name}")
    try:
        learnsets_readme = readme_raw.decode("utf-8-sig")
        learnsets_schema = schema_raw.decode("utf-8-sig")
        restoration_readme = restoration_raw.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        _fail(f"受領ZIP evidenceがUTF-8ではありません: {error}")
    required_evidence = (
        (
            "Vega独自181種は新しいバランスや習得技を創作せず、元資料をそのまま保持しています。",
            learnsets_readme,
        ),
        (
            "Vega独自181種と原作参照表のない内部枠は旧形式を保持します。",
            learnsets_schema,
        ),
        (
            "ベガ技の追加配布は別の明示的な差分で管理してください。",
            restoration_readme,
        ),
    )
    for snippet, text in required_evidence:
        if snippet not in text:
            _fail(f"受領資料の独自配布分離方針が見つかりません: {snippet}")

    upstream = _validate_upstream_contracts(
        documents["content/modernization/p03_learnset_contract.json"],
        documents["content/modernization/p03_compiled_index.json"],
        documents["content/modernization/p03_runtime_handoff.json"],
        documents["content/modernization/p04_candidate_manifest.json"],
        documents["content/modernization/p05_battle_content_contract.json"],
        manifests,
    )
    p06_paths = (
        "content/modernization/p06_species_adjustment_contract.json",
        "content/modernization/p06_review_projection.json",
    )
    p06 = _p06_observation(
        documents[p06_paths[0]],
        documents[p06_paths[1]],
        [identities[path] for path in p06_paths],
    )

    # 今回の入力には工程7向けの採用表がない。空配列を暗黙defaultではなく、
    # 上流資料の明示的な分離方針に基づく確定値としてvalidatorへ通す。
    submitted_additions: list[dict[str, Any]] = []
    submitted_deletions: list[dict[str, Any]] = []
    additions = validate_and_resolve_additions(
        submitted_additions,
        manifests["species"],
        manifests["moves"],
        p04_unallocated_species_keys=frozenset(upstream["p04_unallocated_species_keys"]),
        unavailable_move_keys=frozenset({"MOVE_KEY_ALLYSWITCH"}),
        p06_ready=False,
    )
    deletions = validate_and_resolve_deletions(submitted_deletions, additions)

    contract = {
        "schema_version": SCHEMA_VERSION,
        "task": TASK,
        "status": "CHECKPOINT_NO_ADOPTED_CROSS_DISTRIBUTION_RUNTIME_BLOCKED",
        "policy": {
            "selection": "EXPLICIT_ADOPTED_ROWS_ONLY",
            "missing_submission": "ZERO_DELTA_DO_NOT_INFER",
            "numeric_identity": "SPECIES_AND_MOVE_KEY_FIRST_MANIFEST_ID_ASSERTION_ONLY",
            "p03": "ORIGINAL_RESTORATION_LAYER_IMMUTABLE_NOT_UNIONED_WITH_CUSTOM",
            "p04": "CANDIDATE_IDENTITY_DOES_NOT_IMPLY_MOVE_DISTRIBUTION",
            "p05": "ONLY_RUNTIME_READY_ADOPTED_MOVE_MAY_ENTER_CUSTOM_LAYER",
            "p06": "REQUIRED_REVIEW_DEPENDENCY_BEFORE_NONEMPTY_RUNTIME_ADOPTION",
            "existing_party_box_trainer": "NEVER_BULK_REWRITE_FROM_LEARNSET_CHANGE",
            "conflicts": "FAIL_CLOSED_NO_SILENT_LAST_WRITER_WINS",
        },
        "inputs": {
            "upstream_contracts": {
                relative: identities[relative] for relative in sorted(identities)
            },
            "learnsets_archive": {
                **learnsets_identity,
                "path": LEARNSETS_ZIP,
                "evidence_members": [
                    _member_evidence(readme_name, readme_raw),
                    _member_evidence(schema_name, schema_raw),
                ],
            },
            "restoration_archive": {
                **restoration_identity,
                "path": RESTORATION_ZIP,
                "evidence_members": [_member_evidence(restoration_name, restoration_raw)],
            },
            "manifests": {
                name: {
                    "path": index.spec.relative_path,
                    "count": len(index.rows),
                    "sha256": index.sha256,
                }
                for name, index in sorted(manifests.items())
            },
            "p06": p06,
        },
        "source_evidence": {
            "learnsets_zip": [
                "VEGA_ORIGINAL_181_PRESERVED_WITHOUT_INVENTED_LEARNSETS",
                "APPLY_TARGETS_EXCLUDE_VEGA_ORIGINAL_AND_INTERNAL_ROWS",
            ],
            "restoration_zip": [
                "VEGA_MOVE_DISTRIBUTION_REQUIRES_SEPARATE_EXPLICIT_DELTA",
                "RESTORATION_REVIEW_JSON_DOES_NOT_BULK_CHANGE_LEARNSETS",
            ],
            "upstream_contract_audit": upstream,
        },
        "layer_model": {
            "precedence_low_to_high": [
                "BASE_EXISTING",
                "P03_ORIGINAL_RESTORATION",
                "P07_NORMAL_SPECIES_TO_VEGA_MOVE",
                "P07_VEGA_SPECIES_TO_NORMAL_MOVE",
                "P07_EXPLICIT_DELETION",
            ],
            "layers": {
                "BASE_EXISTING": {
                    "operation": "PRESERVE_UNLESS_HIGHER_LAYER_TARGETS_EXACT_IDENTITY",
                    "owner": "existing_runtime",
                },
                "P03_ORIGINAL_RESTORATION": {
                    "operation": "REPLACE_TARGET_LEARNSET_WITH_FIXED_REFERENCE",
                    "records": upstream["p03_original_restoration_records"],
                    "routes": upstream["p03_original_restoration_routes"],
                    "custom_distribution": False,
                },
                "P07_NORMAL_SPECIES_TO_VEGA_MOVE": {
                    "operation": "ADD_EXACT_ROUTE",
                    "records": [row for row in additions if row["direction"] == NORMAL_TO_VEGA],
                },
                "P07_VEGA_SPECIES_TO_NORMAL_MOVE": {
                    "operation": "ADD_EXACT_ROUTE",
                    "records": [row for row in additions if row["direction"] == VEGA_TO_NORMAL],
                },
                "P07_EXPLICIT_DELETION": {
                    "operation": "DELETE_EXACT_REFERENCED_ROUTE_ONLY",
                    "records": deletions,
                },
            },
            "conflict_rules": [
                "DUPLICATE_CHANGE_KEY_IS_ERROR",
                "SAME_SPECIES_FORM_MOVE_CONSUMER_MULTIPLE_ADDITIONS_IS_ERROR",
                "DIRECTION_MUST_MATCH_MANIFEST_SPECIES_AND_MOVE_DOMAINS",
                "FORM_KEY_MUST_MATCH_SPECIES_MANIFEST",
                "DELETE_MUST_REFERENCE_EXACT_LOWER_LAYER_IDENTITY",
                "P03_CARRY_SHARED_EGG_FORM_ROUTES_MUST_NOT_BECOME_DIRECT_ROUTES",
                "MACHINE_OR_TUTOR_REQUIRES_SUPPLY_SLOT_COST_UNLOCK_AND_CANCEL_POLICY",
            ],
        },
        "adopted_delta": {
            "normal_species_to_vega_move": [],
            "vega_species_to_normal_move": [],
            "explicit_deletions": [],
            "submission_status": "NO_P07_DISTRIBUTION_ROWS_SUBMITTED",
            "invented_rows": [],
        },
        "row_schema": {
            "required_fields": sorted(REQUIRED_ADDITION_FIELDS),
            "required_availability_fields": sorted(REQUIRED_AVAILABILITY_FIELDS),
            "machine_tutor_availability_fields": sorted(MACHINE_AVAILABILITY_FIELDS),
            "directions": sorted(DIRECTIONS),
            "route_to_consumer": [
                {"route_kind": pair[0], "method": pair[1], "consumer": consumer}
                for pair, consumer in sorted(CONSUMER_BY_ROUTE.items())
            ],
        },
        "preservation": {
            "pre_evolution_carry": "SEPARATE_CONSUMER_NEVER_TARGET_DIRECT_LEVEL",
            "shared_egg": "SEPARATE_FROM_DIRECT_EGG",
            "form_change": "CONDITION_REQUIRED_NOT_PERMANENT_ALL_FORM_LEARNSET",
            "mega": "BATTLE_ONLY_FORM_DOES_NOT_GAIN_PERMANENT_LEARNSET_WITHOUT_EXPLICIT_ROW",
            "wild_generation": "NEW_GENERATION_ONLY_FROM_LAYERED_SOURCE",
            "move_memory": "QUERY_SAME_LAYERED_SOURCE_WITH_ROUTE_CONDITIONS",
            "existing_party_box_save": "NO_FOUR_MOVE_REWRITE",
            "trainer_facility": "EXPLICIT_PARTIES_REMAIN_SEPARATE",
            "side_change_1063": (
                "NOT_ADOPTED_ALL_159_SOURCE_ROUTES_EXCLUDED_NO_REPLACEMENT"
            ),
        },
        "dependencies": [
            {
                "dependency": "P04_SPECIES_AND_FORM_ID_ALLOCATION",
                "status": "BLOCKED_52_CANDIDATES_UNALLOCATED",
                "impact": "未割当P04候補を工程7target keyとして採用しない",
            },
            {
                "dependency": "P06_SPECIES_BALANCE_REVIEW",
                "status": p06["status"],
                "impact": "強力な種族/特性/技組合せのreview keyが無い非空差分を採用しない",
            },
            {
                "dependency": "P03_MACHINE_TUTOR_SUPPLY",
                "status": "BLOCKED_26648_ADOPTED_ROUTE_ROWS_REQUIRE_SUPPLY",
                "impact": "compatibility bitだけで実装済みとしない",
            },
        ],
        "runtime_handoff": {
            "checkpoint_only": True,
            "rom_changed": False,
            "runtime_implemented": False,
            "required_when_rows_are_submitted": [
                "compile_each_direction_as_separate_layer",
                "resolve_all_keys_to_current_manifest_ids",
                "validate_p06_review_keys",
                "compile_route_specific_consumers_without_flattening",
                "connect_machine_tutor_ui_supply_cost_unlock_cancel",
                "use_same_source_for_generation_and_move_memory",
                "test_full_moveset_cancel_and_save_roundtrip",
                "prove_exact_added_and_deleted_route_sets",
            ],
        },
        "summary": {
            "normal_species_to_vega_move_adopted": 0,
            "vega_species_to_normal_move_adopted": 0,
            "explicit_deletions_adopted": 0,
            "p03_original_restoration_source_routes": 118_528,
            "p03_original_restoration_routes_preserved": 118_369,
            "p03_side_change_routes_excluded": 159,
            "p04_move_distribution_rows": 0,
            "p05_runtime_unready_move_dependencies": 0,
            "p06_ready": False,
            "runtime_implemented": False,
        },
    }
    validate_p07_contract(contract)
    return contract


def validate_p07_contract(contract: Mapping[str, Any]) -> None:
    if contract.get("schema_version") != SCHEMA_VERSION or contract.get("task") != TASK:
        _fail("P07 contract identityが不正です")
    if contract.get("status") != "CHECKPOINT_NO_ADOPTED_CROSS_DISTRIBUTION_RUNTIME_BLOCKED":
        _fail("P07 checkpointをruntime完了として誤表示しています")
    adopted = contract.get("adopted_delta")
    summary = contract.get("summary")
    layers = contract.get("layer_model", {}).get("layers")
    if not isinstance(adopted, Mapping) or not isinstance(summary, Mapping) \
            or not isinstance(layers, Mapping):
        _fail("P07 contract主要sectionがありません")
    for field in (
        "normal_species_to_vega_move", "vega_species_to_normal_move", "explicit_deletions"
    ):
        if adopted.get(field) != []:
            _fail(f"未提出のP07差分が採用されています: {field}")
    if adopted.get("invented_rows") != []:
        _fail("P07に創作rowがあります")
    if layers.get("P07_NORMAL_SPECIES_TO_VEGA_MOVE", {}).get("records") != [] \
            or layers.get("P07_VEGA_SPECIES_TO_NORMAL_MOVE", {}).get("records") != [] \
            or layers.get("P07_EXPLICIT_DELETION", {}).get("records") != []:
        _fail("P07空採用契約とlayer recordsが不一致です")
    if summary.get("normal_species_to_vega_move_adopted") != 0 \
            or summary.get("vega_species_to_normal_move_adopted") != 0 \
            or summary.get("explicit_deletions_adopted") != 0 \
            or summary.get("p03_original_restoration_source_routes") != 118_528 \
            or summary.get("p03_original_restoration_routes_preserved") != 118_369 \
            or summary.get("p03_side_change_routes_excluded") != 159 \
            or summary.get("p04_move_distribution_rows") != 0 \
            or summary.get("p05_runtime_unready_move_dependencies") != 0 \
            or summary.get("p06_ready") is not False \
            or summary.get("runtime_implemented") is not False:
        _fail("P07 summaryが採用差分0件と不一致です")
    p06 = contract.get("inputs", {}).get("p06")
    if not isinstance(p06, Mapping) \
            or p06.get("contract_status") != "CHECKPOINT_ADOPTED_DELTA_EMPTY" \
            or p06.get("projection_status") != "REVIEW_PROJECTION_ONLY_NOT_ADOPTED" \
            or p06.get("status") != "CHECKPOINT_NOT_P06_DONE_BLOCKING_RUNTIME_ADOPTION" \
            or p06.get("adopted_delta_count") != 0 \
            or p06.get("runtime_patch_authorized") is not False \
            or p06.get("p06_ready_for_p07") is not False:
        _fail("P07がP06未完了checkpoint境界を保持していません")
    handoff = contract.get("runtime_handoff")
    if not isinstance(handoff, Mapping) or handoff.get("checkpoint_only") is not True \
            or handoff.get("runtime_implemented") is not False \
            or handoff.get("rom_changed") is not False:
        _fail("P07 runtime未実装境界が不正です")
    dependency_statuses = {
        row.get("dependency"): row.get("status")
        for row in contract.get("dependencies", [])
        if isinstance(row, Mapping)
    }
    if dependency_statuses != {
        "P04_SPECIES_AND_FORM_ID_ALLOCATION":
            "BLOCKED_52_CANDIDATES_UNALLOCATED",
        "P06_SPECIES_BALANCE_REVIEW":
            "CHECKPOINT_NOT_P06_DONE_BLOCKING_RUNTIME_ADOPTION",
        "P03_MACHINE_TUTOR_SUPPLY":
            "BLOCKED_26648_ADOPTED_ROUTE_ROWS_REQUIRE_SUPPLY",
    }:
        _fail("P07 blocking dependency集合が不一致です")


__all__ = [
    "ModernizationP07Error",
    "NORMAL_TO_VEGA",
    "VEGA_TO_NORMAL",
    "build_p07_contract",
    "stable_json",
    "validate_and_resolve_additions",
    "validate_and_resolve_deletions",
    "validate_p07_contract",
]
