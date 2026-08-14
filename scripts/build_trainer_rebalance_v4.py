#!/usr/bin/env python3
"""V4本編トレーナー設計をstage17の実Trainer ABIへ結合する。"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import struct
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Mapping, NoReturn, Sequence


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.rom_allocator import GBA_ROM_BASE, build_allocation_report_from_csv  # noqa: E402


TASK = "USER-20260814-TRAINER-V4"
ROM_SIZE = 32 * 1024 * 1024
CONFIG = Path("config/trainer_rebalance_v4.json")
STAGE17 = Path("build/stages/17_regression.gba")
STAGE17_META = Path("build/stages/17_regression.json")
STAGE17_ALLOC = Path("build/stages/17_allocation.json")
STAGE19 = Path("build/stages/19_trainer_rebalance.gba")
STAGE19_META = Path("build/stages/19_trainer_rebalance.json")
STAGE19_ALLOC = Path("build/stages/19_allocation.json")
NORMALIZED = Path("reports/generated/trainer_rebalance_v4.csv")
BINDINGS = Path("reports/generated/trainer_rebalance_v4_bindings.json")
REPORT = Path("reports/generated/trainer_rebalance_v4.md")
FIXTURE = Path("tests/fixtures/trainer_rebalance_v4.json")
ALLOCATION_NAME = "trainer_rebalance_v4_parties"
TRAINER_RECORD_SIZE = 0x20
EXISTING_TRAINER_COUNT = 743

EXPECTED_CONFIG_KEYS = {
    "schema_version", "task", "source", "ai_rank_to_cfru_flags", "ai_profiles",
    "species_aliases", "move_aliases", "item_aliases", "direct_bindings",
    "gym_trainer_bindings", "generic_roles", "preserved_roles", "live_fields",
    "catalog_only_fields",
}

CLASS_FAMILIES: dict[int, tuple[str, ...]] = {
    10: ("HEX",), 16: ("BLACKBELT",), 19: ("CAMPER",),
    21: ("PSYCHIC",), 28: ("VETERAN",), 29: ("YOUNGSTER",),
    31: ("FISHER",), 33: ("DRAGON",), 34: ("BIRD",),
    38: ("SWIMMER",), 39: ("PICNICKER",), 45: ("BREEDER",),
    46: ("RANGER",), 49: ("LASS",), 50: ("BUG",),
    51: ("HIKER",), 57: ("YOUNGSTER",), 58: ("BUG",),
    59: ("LASS",), 61: ("CAMPER",), 62: ("PICNICKER",),
    65: ("HIKER",), 69: ("FISHER",), 70: ("SWIMMER",),
    74: ("SWIMMER",), 75: ("PSYCHIC",), 79: ("BIRD",),
    80: ("BLACKBELT",), 82: ("SCIENTIST", "DH_SCI"),
    85: ("DH_",), 86: ("ACE",), 88: ("VETERAN",),
    91: ("HEX",), 101: ("BREEDER",), 102: ("RANGER",),
}
DOUBLE_CLASSES = {6, 26, 40, 52, 53, 54, 92, 93, 94, 95, 96}


class TrainerRebalanceError(ValueError):
    """V4入力、ID解決、またはROM ABI契約の違反。"""


def _fail(message: str) -> NoReturn:
    raise TrainerRebalanceError(message)


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _stable(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        _fail(f"JSON object required: {path}")
    return value


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def _normal(text: str) -> str:
    return unicodedata.normalize("NFKC", text).strip()


def _checked_source(root: Path, spec: Mapping[str, Any], label: str) -> Path:
    path = root / str(spec.get("path", ""))
    if not path.is_file() or path.is_symlink():
        _fail(f"{label}: tracked regular source is missing: {path}")
    raw = path.read_bytes()
    if _sha(raw) != spec.get("sha256"):
        _fail(f"{label}: source sha256 drift")
    return path


def _registry(root: Path, filename: str, key_field: str) -> tuple[
    dict[str, dict[str, str]], dict[str, list[dict[str, str]]]
]:
    rows = _read_rows(root / "manifests" / filename)
    by_key: dict[str, dict[str, str]] = {}
    by_name: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        key = row[key_field]
        if key in by_key:
            _fail(f"{filename}: duplicate key {key}")
        by_key[key] = row
        by_name[_normal(row["display_name"])].append(row)
    return by_key, dict(by_name)


def _candidate_rank(kind: str, row: Mapping[str, str]) -> tuple[int, int, int]:
    classification = row.get("classification", "")
    if kind == "species":
        classification_rank = {
            "VEGA_DPE_CANONICAL": 0,
            "DPE_SPECIES_APPEND": 1,
            "VEGA_ORIGINAL": 2,
            "DPE_FORM_APPEND": 3,
        }.get(classification, 9)
        official_rank = 0 if row.get("is_official") == "true" else 1
    else:
        classification_rank = 0 if "CANONICAL" in classification else 1
        official_rank = 0
    status_rank = 0 if row.get("status") == "FROZEN" else 1
    return classification_rank, official_rank, status_rank


def _resolve(
    value: str,
    *,
    kind: str,
    key_field: str,
    by_key: Mapping[str, Mapping[str, str]],
    by_name: Mapping[str, Sequence[Mapping[str, str]]],
    aliases: Mapping[str, str],
) -> tuple[Mapping[str, str], str]:
    normalized = _normal(value)
    alias_key = aliases.get(normalized)
    if alias_key:
        row = by_key.get(alias_key)
        if row is None:
            _fail(f"{kind}: alias target is absent: {value!r} -> {alias_key}")
        return row, "EXPLICIT_ALIAS"
    candidates = list(by_name.get(normalized, ()))
    if kind == "species":
        base = [row for row in candidates if not row.get("form_key")]
        if base:
            candidates = base
    if not candidates:
        _fail(f"{kind}: unresolved display name: {value!r}")
    ranked = sorted(candidates, key=lambda row: (_candidate_rank(kind, row), int(row["id"])))
    best_rank = _candidate_rank(kind, ranked[0])
    tied = [row for row in ranked if _candidate_rank(kind, row) == best_rank]
    if len(tied) != 1:
        _fail(
            f"{kind}: ambiguous display name {value!r}: "
            + ",".join(str(row[key_field]) for row in tied)
        )
    return ranked[0], "CANONICAL_BASE"


def _normalize_sources(
    root: Path, config: Mapping[str, Any]
) -> tuple[list[dict[str, Any]], dict[str, dict[str, str]], dict[str, Any]]:
    source = config["source"]
    party_path = _checked_source(root, source["parties"], "V4 parties")
    battle_path = _checked_source(root, source["battles"], "V4 battles")
    parties = _read_rows(party_path)
    battles = _read_rows(battle_path)
    if len(parties) != int(source["parties"]["rows"]):
        _fail("V4 party row count drift")
    if len(battles) != int(source["battles"]["rows"]):
        _fail("V4 battle row count drift")
    battle_by_id = {row["battle_id"]: row for row in battles}
    if len(battle_by_id) != len(battles):
        _fail("V4 battle_id is not unique")

    species_by_key, species_by_name = _registry(root, "species_ids.csv", "species_key")
    move_by_key, move_by_name = _registry(root, "move_ids.csv", "move_key")
    item_by_key, item_by_name = _registry(root, "item_ids.csv", "item_key")
    aliases = {
        "species": {_normal(k): v for k, v in config["species_aliases"].items()},
        "move": {_normal(k): v for k, v in config["move_aliases"].items()},
        "item": {_normal(k): v for k, v in config["item_aliases"].items()},
    }
    ai_map = {int(rank): int(flags) for rank, flags in config["ai_rank_to_cfru_flags"].items()}
    profiles = {int(flags): name for flags, name in config["ai_profiles"].items()}
    if ai_map != {1: 1, 2: 3, 3: 3, 4: 5, 5: 5}:
        _fail("V4 AI rank mapping must reuse CFRU flags 1/3/5 exactly")
    if profiles != {1: "AI_BASIC", 3: "AI_SEMI_SMART", 5: "AI_FULL_SMART"}:
        _fail("CFRU AI profile labels drift")

    normalized: list[dict[str, Any]] = []
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    resolution_counts: Counter[str] = Counter()
    for index, source_row in enumerate(parties, 2):
        battle_id = source_row["battle_id"]
        battle = battle_by_id.get(battle_id)
        if battle is None:
            _fail(f"parties.csv:{index}: unknown battle_id {battle_id}")
        for field in ("trainer_name", "location", "battle_format", "ai_rank"):
            if source_row[field] != battle[field]:
                _fail(f"{battle_id}: party/battle {field} mismatch")
        species, species_reason = _resolve(
            source_row["species"], kind="species", key_field="species_key",
            by_key=species_by_key, by_name=species_by_name,
            aliases=aliases["species"],
        )
        held, item_reason = _resolve(
            source_row["item"], kind="item", key_field="item_key",
            by_key=item_by_key, by_name=item_by_name, aliases=aliases["item"],
        )
        moves = []
        move_reasons = []
        for slot in range(1, 5):
            move, reason = _resolve(
                source_row[f"move{slot}"], kind="move", key_field="move_key",
                by_key=move_by_key, by_name=move_by_name, aliases=aliases["move"],
            )
            moves.append(move)
            move_reasons.append(reason)
        level = int(source_row["level"])
        iv_floor = int(source_row["iv_floor"])
        ai_rank = int(source_row["ai_rank"])
        if not 1 <= level <= 100 or not 0 <= iv_floor <= 31 or ai_rank not in ai_map:
            _fail(f"{battle_id}: level/IV/AI range violation")
        row: dict[str, Any] = {
            "battle_id": battle_id,
            "party_slot": int(source_row["party_slot"]),
            "species_source": source_row["species"],
            "species_key": species["species_key"],
            "species_id": int(species["id"]),
            "species_resolution": species_reason,
            "level": level,
            "item_source": source_row["item"],
            "item_key": held["item_key"],
            "item_id": int(held["id"]),
            "item_resolution": item_reason,
            "iv_floor": iv_floor,
            "ability": source_row["ability"],
            "nature": source_row["nature"],
            "ev_profile": source_row["ev_profile"],
            "ai_rank": ai_rank,
            "ai_flags": ai_map[ai_rank],
            "ai_profile": profiles[ai_map[ai_rank]],
        }
        for slot, move in enumerate(moves, 1):
            row[f"move{slot}_source"] = source_row[f"move{slot}"]
            row[f"move{slot}_key"] = move["move_key"]
            row[f"move{slot}_id"] = int(move["id"])
            row[f"move{slot}_resolution"] = move_reasons[slot - 1]
        normalized.append(row)
        grouped[battle_id].append(row)
        resolution_counts[f"species_{species_reason}"] += 1
        resolution_counts[f"item_{item_reason}"] += 1
        resolution_counts.update(f"move_{reason}" for reason in move_reasons)

    for battle_id, rows in grouped.items():
        rows.sort(key=lambda row: row["party_slot"])
        slots = [row["party_slot"] for row in rows]
        expected = list(range(1, len(rows) + 1))
        if slots != expected or len(rows) != int(battle_by_id[battle_id]["active_party_size"]):
            _fail(f"{battle_id}: party slots/active size mismatch")
        if len({row["ai_rank"] for row in rows}) != 1:
            _fail(f"{battle_id}: per-mon AI ranks differ")
    if set(grouped) != set(battle_by_id):
        _fail("V4 battle/party coverage is not exact")
    return normalized, battle_by_id, {
        "grouped": dict(grouped),
        "item_by_key": item_by_key,
        "item_by_name": item_by_name,
        "item_aliases": aliases["item"],
        "resolution_counts": dict(sorted(resolution_counts.items())),
    }


def _decode_names(root: Path) -> dict[int, str]:
    inverse: dict[int, str] = {}
    for line in (root / "vendor/upstream/CFRU-JP/charmap.tbl").read_text(
        encoding="utf-8-sig"
    ).splitlines():
        if len(line) < 3 or line[2] != "=":
            continue
        try:
            value = int(line[:2], 16)
        except ValueError:
            continue
        inverse.setdefault(value, line[3:])
    inventory = _read_json(root / "reports/generated/id_inventory.json")
    result: dict[int, str] = {}
    for row in inventory["trainer_details"]:
        raw = bytes.fromhex(row["name_hex"])
        result[int(row["trainer_id"])] = "".join(
            inverse.get(byte, f"<{byte:02X}>") for byte in raw if byte not in (0, 0xFF)
        )
    return result


def _trainer_inventory(root: Path) -> tuple[dict[int, dict[str, Any]], dict[int, str]]:
    inventory = _read_json(root / "reports/generated/id_inventory.json")
    details = {int(row["trainer_id"]): row for row in inventory["trainer_details"]}
    if set(details) != set(range(EXISTING_TRAINER_COUNT)):
        _fail("Vega trainer detail inventory must cover IDs 0..742")
    roles: dict[int, str] = {}
    for row in _read_rows(root / "reports/generated/vega_trainer_baseline.csv"):
        trainer_id = int(row["trainer_id"])
        roles[trainer_id] = row["role"]
    if set(roles) != set(details):
        _fail("Vega trainer role inventory differs from trainer details")
    return details, roles


def _average_level(detail: Mapping[str, Any]) -> float:
    levels = [int(row["level"]) for row in detail["party"]]
    return sum(levels) / len(levels) if levels else 0.0


def _generic_template(
    trainer_id: int,
    detail: Mapping[str, Any],
    battle_by_id: Mapping[str, Mapping[str, str]],
) -> str:
    candidates = [row for key, row in battle_by_id.items() if key.startswith("TPL_")]
    if not candidates:
        _fail("V4 generic templates are absent")
    current_average = _average_level(detail)
    current_size = len(detail["party"])
    trainer_class = int(detail["trainer_class"])
    families = CLASS_FAMILIES.get(trainer_class, ())
    current_double = bool(detail["double_battle"]) or trainer_class in DOUBLE_CLASSES

    def score(row: Mapping[str, str]) -> tuple[int, str]:
        source_average = float(row["average_level"])
        source_size = int(row["active_party_size"])
        source_double = row["battle_format"] == "ダブル"
        format_penalty = 0
        if current_double != source_double:
            format_penalty = 350 if current_double else 10000
        theme_penalty = 0
        if families and not any(fragment in row["battle_id"] for fragment in families):
            theme_penalty = 250
        distance = round(abs(current_average - source_average) * 100)
        size_penalty = abs(current_size - source_size) * 10
        tie = hashlib.sha256(f"{trainer_id}:{row['battle_id']}".encode()).hexdigest()
        return distance + size_penalty + format_penalty + theme_penalty, tie

    return min(candidates, key=score)["battle_id"]


def _build_bindings(
    root: Path,
    config: Mapping[str, Any],
    battle_by_id: Mapping[str, Mapping[str, str]],
) -> tuple[dict[int, dict[str, str]], dict[int, dict[str, Any]], dict[int, str]]:
    details, roles = _trainer_inventory(root)
    bindings: dict[int, dict[str, str]] = {}

    def bind(trainer_id: int, battle_id: str, kind: str) -> None:
        if trainer_id in bindings:
            _fail(f"trainer {trainer_id}: duplicate binding")
        if trainer_id <= 0 or trainer_id >= EXISTING_TRAINER_COUNT:
            _fail(f"trainer {trainer_id}: outside Vega main table")
        if battle_id not in battle_by_id:
            _fail(f"trainer {trainer_id}: unknown V4 battle {battle_id}")
        bindings[trainer_id] = {"battle_id": battle_id, "binding_type": kind}

    for trainer_id, battle_id in config["direct_bindings"].items():
        bind(int(trainer_id), str(battle_id), "DIRECT")
    for gym, trainer_ids in sorted(config["gym_trainer_bindings"].items(), key=lambda row: int(row[0])):
        templates = [f"G{int(gym)}_TRAINER_{letter}" for letter in "ABC"]
        for index, trainer_id in enumerate(trainer_ids):
            bind(int(trainer_id), templates[index % len(templates)], "GYM_EXISTING_NPC")

    generic_roles = set(config["generic_roles"])
    preserved_roles = set(config["preserved_roles"])
    if generic_roles & preserved_roles:
        _fail("generic and preserved trainer roles overlap")
    for trainer_id in sorted(details):
        if trainer_id in bindings or roles[trainer_id] not in generic_roles:
            continue
        if not details[trainer_id]["party"]:
            continue
        bind(
            trainer_id,
            _generic_template(trainer_id, details[trainer_id], battle_by_id),
            "GENERIC_LEVEL_CLASS_MATCH",
        )
    if any(
        roles[trainer_id] in preserved_roles
        and binding["binding_type"] == "GENERIC_LEVEL_CLASS_MATCH"
        for trainer_id, binding in bindings.items()
    ):
        _fail("preserved Mirage/Sphere row was selected for generic replacement")
    return bindings, details, roles


def _party_bytes(rows: Sequence[Mapping[str, Any]]) -> bytes:
    raw = bytearray()
    for row in rows:
        encoded_iv = min(255, int(row["iv_floor"]) * 8 + 7)
        values = (
            encoded_iv, int(row["level"]), int(row["species_id"]), int(row["item_id"]),
            *(int(row[f"move{slot}_id"]) for slot in range(1, 5)),
        )
        if any(not 0 <= value <= 0xFFFF for value in values):
            _fail(f"{row['battle_id']}: trainer party u16 overflow")
        raw += struct.pack("<8H", *values)
    return bytes(raw)


def _build_payload(
    bindings: Mapping[int, Mapping[str, str]], grouped: Mapping[str, Sequence[Mapping[str, Any]]]
) -> tuple[bytes, dict[str, int], dict[str, str]]:
    unique = sorted({row["battle_id"] for row in bindings.values()})
    payload = bytearray(struct.pack(
        "<8sIIIIII", b"VEGATR4\0", 1, len(bindings), len(unique), 610, 141, 0,
    ))
    offsets: dict[str, int] = {}
    digests: dict[str, str] = {}
    for battle_id in unique:
        while len(payload) % 4:
            payload.append(0)
        offsets[battle_id] = len(payload)
        party = _party_bytes(grouped[battle_id])
        payload.extend(party)
        digests[battle_id] = _sha(party)
    struct.pack_into("<I", payload, 28, len(payload))
    return bytes(payload), offsets, digests


def _allocation(
    root: Path, payload: bytes
) -> tuple[dict[str, Any], dict[str, Any]]:
    previous = _read_json(root / STAGE17_ALLOC)
    requests = [
        {
            "name": row["name"], "region": row["region"], "size": row["size"],
            "alignment": row["alignment"], "start": row["start"],
            "owner": row["owner"], "purpose": row["purpose"],
            "content_sha256": row["content_sha256"],
        }
        for row in previous["allocations"]
    ]
    requests.append({
        "name": ALLOCATION_NAME,
        "region": "integration_modules",
        "size": len(payload),
        "alignment": 4,
        "owner": TASK,
        "purpose": "V4 main-story trainer party rows",
        "content_sha256": _sha(payload),
    })
    report = build_allocation_report_from_csv(root / "config/rom_regions.csv", requests)
    allocation = next(row for row in report["allocations"] if row["name"] == ALLOCATION_NAME)
    return allocation, report


def _trainer_items(
    text: str,
    *,
    item_by_key: Mapping[str, Mapping[str, str]],
    item_by_name: Mapping[str, Sequence[Mapping[str, str]]],
    aliases: Mapping[str, str],
) -> list[int]:
    if text in {"", "なし"} or text.startswith("NPC"):
        return []
    result: list[int] = []
    for segment in text.split("／"):
        match = re.fullmatch(r"(.+?)×([1-4])", segment)
        if match is None:
            _fail(f"unrecognized trainer item expression: {text!r}")
        item, _ = _resolve(
            match.group(1), kind="item", key_field="item_key", by_key=item_by_key,
            by_name=item_by_name, aliases=aliases,
        )
        result.extend([int(item["id"])] * int(match.group(2)))
    if len(result) > 4:
        _fail(f"trainer item expression exceeds four ABI slots: {text!r}")
    return result


def _merged_spans(spans: Sequence[tuple[int, int]]) -> list[tuple[int, int]]:
    result: list[list[int]] = []
    for start, end in sorted(spans):
        if not result or start > result[-1][1]:
            result.append([start, end])
        else:
            result[-1][1] = max(result[-1][1], end)
    return [(start, end) for start, end in result]


def _changed_outside(before: bytes, after: bytes, spans: Sequence[tuple[int, int]]) -> list[int]:
    merged = _merged_spans(spans)
    outside: list[int] = []
    span_index = 0
    for offset, (left, right) in enumerate(zip(before, after, strict=True)):
        if left == right:
            continue
        while span_index < len(merged) and offset >= merged[span_index][1]:
            span_index += 1
        if span_index >= len(merged) or offset < merged[span_index][0]:
            outside.append(offset)
            if len(outside) == 8:
                break
    return outside


def _csv_bytes(rows: Sequence[Mapping[str, Any]]) -> bytes:
    fields = [
        "battle_id", "party_slot", "species_source", "species_key", "species_id",
        "species_resolution", "level", "item_source", "item_key", "item_id",
        "item_resolution", "move1_source", "move1_key", "move1_id",
        "move2_source", "move2_key", "move2_id", "move3_source", "move3_key",
        "move3_id", "move4_source", "move4_key", "move4_id", "iv_floor",
        "ability", "nature", "ev_profile", "ai_rank", "ai_profile", "ai_flags",
    ]
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({field: row[field] for field in fields})
    return stream.getvalue().encode("utf-8")


def _report(metadata: Mapping[str, Any]) -> bytes:
    counts = metadata["bindings"]["by_type"]
    live = "、".join(metadata["source"]["live_fields"])
    catalog = "、".join(metadata["source"]["catalog_only_fields"])
    text = f"""# V4 本編トレーナー ROM 結合報告

- Status: PASS
- Source archive SHA-256: `{metadata['source']['archive_sha256']}`
- 設計入力: {metadata['source']['battle_count']}戦 / {metadata['source']['party_row_count']}体
- 実Trainer ID変更: {metadata['bindings']['trainer_count']}件
- 直接対応: {counts.get('DIRECT', 0)}件
- 既存ジムNPC対応: {counts.get('GYM_EXISTING_NPC', 0)}件
- 一般・バトルサーチャー決定的対応: {counts.get('GENERIC_LEVEL_CLASS_MATCH', 0)}件
- 共有party blob: {metadata['payload']['unique_party_count']}編成 / {metadata['payload']['size']} bytes
- AI変換: rank 1→AI_BASIC、2–3→AI_SEMI_SMART、4–5→AI_FULL_SMART
- ROMへ反映: {live}
- 設計台帳のみ（現行Trainer ABI非対応）: {catalog}
- 保護: Mirageおよび未指定Sphere trainerは変更なし
- Allocator overlap: {metadata['allocation']['overlap_count']}
- Output SHA-256: `{metadata['output']['sha256']}`
"""
    return text.encode("utf-8")


def build_outputs(root: Path = ROOT) -> dict[str, bytes]:
    root = Path(root)
    config = _read_json(root / CONFIG)
    if set(config) != EXPECTED_CONFIG_KEYS or config.get("schema_version") != 1:
        _fail("trainer_rebalance_v4 config schema drift")
    if config.get("task") != TASK:
        _fail("trainer_rebalance_v4 task id drift")

    normalized, battle_by_id, models = _normalize_sources(root, config)
    grouped: dict[str, list[dict[str, Any]]] = models["grouped"]
    bindings, details, roles = _build_bindings(root, config, battle_by_id)
    names = _decode_names(root)
    payload, party_offsets, party_digests = _build_payload(bindings, grouped)
    allocation, allocation_report = _allocation(root, payload)

    stage = (root / STAGE17).read_bytes()
    stage_meta = _read_json(root / STAGE17_META)
    if len(stage) != ROM_SIZE or _sha(stage) != stage_meta.get("output", {}).get("sha256"):
        _fail("stage17 identity drift")
    trainer = stage_meta.get("trainers", {})
    if (
        trainer.get("existing_count") != EXISTING_TRAINER_COUNT
        or trainer.get("record_size") != TRAINER_RECORD_SIZE
    ):
        _fail("stage17 trainer ABI drift")
    table_offset = int(trainer["address"]) - GBA_ROM_BASE
    if table_offset < 0 or table_offset + EXISTING_TRAINER_COUNT * TRAINER_RECORD_SIZE > len(stage):
        _fail("stage17 trainer table pointer is outside ROM")

    payload_start = int(allocation["start"])
    payload_end = int(allocation["end_exclusive"])
    if stage[payload_start:payload_end] != b"\xFF" * len(payload):
        _fail("V4 party allocation destination is not erased FF")
    output = bytearray(stage)
    output[payload_start:payload_end] = payload
    spans: list[tuple[int, int]] = [(payload_start, payload_end)]
    binding_rows: list[dict[str, Any]] = []
    for trainer_id in sorted(bindings):
        binding = bindings[trainer_id]
        battle_id = binding["battle_id"]
        battle = battle_by_id[battle_id]
        rows = grouped[battle_id]
        record_offset = table_offset + trainer_id * TRAINER_RECORD_SIZE
        original = bytes(output[record_offset:record_offset + TRAINER_RECORD_SIZE])
        if len(original) != TRAINER_RECORD_SIZE:
            _fail(f"trainer {trainer_id}: truncated record")
        record = bytearray(original)
        record[0] = 3
        items = _trainer_items(
            battle["trainer_items"], item_by_key=models["item_by_key"],
            item_by_name=models["item_by_name"], aliases=models["item_aliases"],
        )
        struct.pack_into("<4H", record, 0x0A, *(items + [0] * (4 - len(items))))
        ai_rank = int(battle["ai_rank"])
        ai_flags = int(config["ai_rank_to_cfru_flags"][str(ai_rank)])
        struct.pack_into("<I", record, 0x14, ai_flags)
        record[0x18] = len(rows)
        party_pointer = GBA_ROM_BASE + payload_start + party_offsets[battle_id]
        struct.pack_into("<I", record, 0x1C, party_pointer)
        output[record_offset:record_offset + TRAINER_RECORD_SIZE] = record
        spans.append((record_offset, record_offset + TRAINER_RECORD_SIZE))
        binding_rows.append({
            "trainer_id": trainer_id,
            "trainer_name": names[trainer_id],
            "original_role": roles[trainer_id],
            "binding_type": binding["binding_type"],
            "battle_id": battle_id,
            "source_category": battle["category"],
            "source_location": battle["location"],
            "original_average_level": round(_average_level(details[trainer_id]), 2),
            "new_average_level": round(sum(row["level"] for row in rows) / len(rows), 2),
            "party_size": len(rows),
            "party_pointer": party_pointer,
            "party_sha256": party_digests[battle_id],
            "ai_rank": ai_rank,
            "ai_flags": ai_flags,
            "ai_profile": config["ai_profiles"][str(ai_flags)],
            "trainer_items": items,
            "double_battle_preserved": int(record[0x12]) == int(original[0x12]),
            "original_record_sha256": _sha(original),
            "replacement_record_sha256": _sha(bytes(record)),
        })

    output_raw = bytes(output)
    outside = _changed_outside(stage, output_raw, spans)
    if outside:
        _fail(f"bytes changed outside declared V4 spans: {outside}")
    by_type = dict(sorted(Counter(row["binding_type"] for row in binding_rows).items()))
    bound_battles = sorted({row["battle_id"] for row in binding_rows})
    catalog_only = sorted(set(battle_by_id) - set(bound_battles))
    preserved_ids = sorted(
        trainer_id for trainer_id, role in roles.items()
        if role in set(config["preserved_roles"]) and trainer_id not in bindings
    )
    metadata: dict[str, Any] = {
        "schema_version": 1,
        "task": TASK,
        "status": "PASS",
        "input": {"path": STAGE17.as_posix(), "size": len(stage), "sha256": _sha(stage)},
        "output": {"path": STAGE19.as_posix(), "size": len(output_raw), "sha256": _sha(output_raw)},
        "source": {
            "archive_name": config["source"]["archive_name"],
            "archive_sha256": config["source"]["archive_sha256"],
            "extracted_tree_sha256": config["source"]["extracted_tree_sha256"],
            "battle_count": len(battle_by_id),
            "party_row_count": len(normalized),
            "live_fields": config["live_fields"],
            "catalog_only_fields": config["catalog_only_fields"],
        },
        "resolution": {
            "counts": models["resolution_counts"],
            "all_species_moves_items_resolved": True,
            "normalized_manifest": NORMALIZED.as_posix(),
            "normalized_manifest_sha256": _sha(_csv_bytes(normalized)),
        },
        "ai": {
            "source": "CFRU-JP fixed trainer AI flags",
            "source_commit": "e24a16fe39e27ae162faf5b78596d1f3df18489d",
            "rank_to_flags": config["ai_rank_to_cfru_flags"],
            "profiles": config["ai_profiles"],
            "custom_ai_added": False,
        },
        "trainer_table": {
            "address": int(trainer["address"]),
            "record_size": TRAINER_RECORD_SIZE,
            "existing_count": EXISTING_TRAINER_COUNT,
            "repointed": False,
            "records_modified_in_place": len(bindings),
        },
        "payload": {
            "magic": "VEGATR4",
            "offset": payload_start,
            "address": GBA_ROM_BASE + payload_start,
            "size": len(payload),
            "sha256": _sha(payload),
            "unique_party_count": len(party_offsets),
        },
        "bindings": {
            "trainer_count": len(binding_rows),
            "by_type": by_type,
            "bound_battle_count": len(bound_battles),
            "catalog_only_battle_count": len(catalog_only),
            "catalog_only_battles": catalog_only,
            "preserved_role_ids": preserved_ids,
            "rows": binding_rows,
        },
        "allocation": {
            "path": STAGE19_ALLOC.as_posix(),
            "name": ALLOCATION_NAME,
            "overlap_count": allocation_report["summaries"]["overlap_count"],
            "remaining_allocatable_bytes": allocation_report["summaries"]["remaining_allocatable_bytes"],
        },
        "invariants": {
            "rom_size_32_mib": len(output_raw) == ROM_SIZE,
            "source_141_battles_610_rows": len(battle_by_id) == 141 and len(normalized) == 610,
            "all_species_moves_items_resolved": True,
            "all_modified_records_point_to_v4_payload": all(
                GBA_ROM_BASE + payload_start <= row["party_pointer"] < GBA_ROM_BASE + payload_end
                for row in binding_rows
            ),
            "cfru_ai_flags_only": {row["ai_flags"] for row in binding_rows} <= {1, 3, 5},
            "double_battle_flags_preserved": all(row["double_battle_preserved"] for row in binding_rows),
            "mirage_and_unselected_sphere_preserved": len(preserved_ids) > 0,
            "stage17_unchanged_outside_payload_and_records": True,
            "allocator_overlap_zero": allocation_report["summaries"]["overlap_count"] == 0,
        },
    }
    if not all(metadata["invariants"].values()):
        _fail("V4 build invariant failed")
    fixture = {
        "schema_version": 1,
        "task": TASK,
        "status": "PASS",
        "source": {"battles": 141, "party_rows": 610},
        "bindings": {"trainers": len(binding_rows), "by_type": by_type},
        "ai_flags": sorted({row["ai_flags"] for row in binding_rows}),
        "representative": {
            str(trainer_id): next(
                {
                    "battle_id": row["battle_id"], "party_size": row["party_size"],
                    "ai_flags": row["ai_flags"], "party_pointer": row["party_pointer"],
                }
                for row in binding_rows if row["trainer_id"] == trainer_id
            )
            for trainer_id in (326, 414, 438, 704, 735)
        },
        "output_sha256": _sha(output_raw),
    }
    return {
        STAGE19.as_posix(): output_raw,
        STAGE19_META.as_posix(): _stable(metadata),
        STAGE19_ALLOC.as_posix(): _stable(allocation_report),
        NORMALIZED.as_posix(): _csv_bytes(normalized),
        BINDINGS.as_posix(): _stable(metadata["bindings"]),
        REPORT.as_posix(): _report(metadata),
        FIXTURE.as_posix(): _stable(fixture),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("build", "check"))
    args = parser.parse_args()
    try:
        outputs = build_outputs(ROOT)
        if args.mode == "build":
            for relative, raw in outputs.items():
                path = ROOT / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
            print(
                f"Trainer V4 build: PASS ({len(outputs)} artifacts; "
                f"ROM sha256={_sha(outputs[STAGE19.as_posix()])})"
            )
        else:
            drift = [
                relative for relative, raw in outputs.items()
                if not (ROOT / relative).is_file() or (ROOT / relative).read_bytes() != raw
            ]
            if drift:
                _fail("artifact drift: " + ", ".join(drift))
            print(f"Trainer V4 check: PASS ({len(outputs)} artifacts, side effects NONE)")
    except (TrainerRebalanceError, OSError, KeyError, TypeError, ValueError) as error:
        print(f"Trainer V4 {args.mode}: FAIL: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
