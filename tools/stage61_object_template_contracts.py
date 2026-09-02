from __future__ import annotations

"""Stage61 ObjectEventTemplate の独立期待値を Stage60 から導出する。

このモジュールの build API は final ROM を受け取らない。期待値は Stage60 の
24-byte ObjectEventTemplate と、builder が既に持つ明示的な変換 plan だけを
順に合成する。final ROM は :func:`validate_stage61_object_template_contracts`
からのみ読み、期待値との比較対象として扱う。

変換順は次のとおりである。

1. Stage60 の完全な24-byte preimage
2. topology producer の exact object-array raw
3. missing-object materialization payload の exact record
4. graphics namespace の full-record preimage -> runtime graphics ID
5. object visibility の target flag
6. semantic root の relocated pointer
7. Archive / 明示 pre-placement patch
8. final interaction placement の exact 7 bytes (offset 4..10)
9. Snorlax の予約 graphics ID
10. Stage58 post-ledger owner の明示フィールド

padding byte 3/11 と reserved byte 22/23 も基底から保持するため、結果は一部
フィールドの自己照合ではなく、全24 bytesの独立oracleになる。
"""

import hashlib
import json
import re
import struct
from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Iterable, Mapping, NoReturn, Sequence


ROM_BASE = 0x08000000
ROM_LIMIT = 0x0A000000
MAP_GROUPS_POINTER_SITE = 0x00054B0C
OBJECT_TEMPLATE_SIZE = 24
EVENT_HEADER_SIZE = 20
SCHEMA_VERSION = 1

_OWNER_RE = re.compile(r"^OBJECT:(\d{3})/(\d{3}):(\d{3})$")


class Stage61ObjectTemplateContractError(RuntimeError):
    """ObjectEventTemplate の独立導出契約を証明できない。"""


class Stage60ObjectIndexMissingError(Stage61ObjectTemplateContractError):
    """明示materializationで追加可能な、Stage60 index欠落だけを表す。"""


def _fail(message: str) -> NoReturn:
    raise Stage61ObjectTemplateContractError(message)


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _stable(value: Any) -> bytes:
    return (
        json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        ) + "\n"
    ).encode("utf-8")


def _self_hash(document: Mapping[str, Any]) -> str:
    return _sha(_stable({
        key: value for key, value in document.items()
        if key != "contract_sha256"
    }))


def _value(row: Any, name: str, default: Any = None) -> Any:
    if isinstance(row, Mapping):
        return row.get(name, default)
    return getattr(row, name, default)


def _rows(value: Any, *, nested_keys: Sequence[str] = ()) -> list[Any]:
    if value is None:
        return []
    for key in nested_keys:
        nested = _value(value, key)
        if nested is not None:
            value = nested
            break
    if isinstance(value, Mapping):
        return list(value.values())
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return list(value)
    if isinstance(value, Iterable) and not isinstance(value, (str, bytes, bytearray)):
        return list(value)
    _fail("変換planはrow列またはmappingである必要があります")


def _integer(value: Any, label: str) -> int:
    if isinstance(value, bool):
        _fail(f"{label}: boolは整数として使用できません")
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value, 0)
        except ValueError:
            pass
    _fail(f"{label}: 整数が必要です: {value!r}")


def _bounded(value: Any, minimum: int, maximum: int, label: str) -> int:
    result = _integer(value, label)
    if not minimum <= result <= maximum:
        _fail(f"{label}: 範囲外です: {result}")
    return result


def _hex_bytes(value: Any, size: int | None, label: str) -> bytes:
    if isinstance(value, bytes):
        raw = value
    elif isinstance(value, bytearray):
        raw = bytes(value)
    elif isinstance(value, str):
        try:
            raw = bytes.fromhex(value)
        except ValueError:
            _fail(f"{label}: hex文字列が不正です")
    else:
        _fail(f"{label}: bytesまたはhex文字列が必要です")
    if size is not None and len(raw) != size:
        _fail(f"{label}: size不一致 {len(raw)} != {size}")
    return raw


def _canonical_template_hex(value: Any, label: str) -> bytes:
    """C/runner ABI用のexact 48-character uppercase HEXだけを受ける。"""

    if not isinstance(value, str) or re.fullmatch(r"[0-9A-F]{48}", value) is None:
        _fail(f"{label}: 48文字の大文字HEX canonical表現が必要です")
    return bytes.fromhex(value)


@dataclass(frozen=True, order=True)
class ObjectOwnerKey:
    group: int
    map_number: int
    object_index: int

    def __post_init__(self) -> None:
        if not all(0 <= value <= 0xFF for value in (
            self.group, self.map_number, self.object_index,
        )):
            _fail(f"object owner keyがu8範囲外です: {self}")

    @property
    def owner_id(self) -> str:
        return (
            f"OBJECT:{self.group:03d}/{self.map_number:03d}:"
            f"{self.object_index:03d}"
        )

    @classmethod
    def parse(cls, value: Any, label: str = "owner") -> "ObjectOwnerKey":
        if isinstance(value, ObjectOwnerKey):
            return value
        if isinstance(value, str):
            match = _OWNER_RE.fullmatch(value)
            if match is None:
                _fail(f"{label}: owner_id書式不正: {value!r}")
            return cls(*(int(part) for part in match.groups()))
        owner_id = _value(value, "owner_id", _value(value, "npc_id"))
        if owner_id is not None:
            parsed = cls.parse(owner_id, label)
            declared = (
                _value(value, "group", _value(value, "target_group")),
                _value(value, "map", _value(
                    value, "map_number", _value(value, "target_map"),
                )),
                _value(value, "object_index", _value(
                    value, "index", _value(value, "target_index"),
                )),
            )
            for expected, actual, field in zip(
                (parsed.group, parsed.map_number, parsed.object_index),
                declared, ("group", "map", "object_index"), strict=True,
            ):
                if actual is not None and _integer(actual, f"{label}.{field}") != expected:
                    _fail(f"{label}: owner_idと{field}が不一致です")
            return parsed
        group = _value(value, "group", _value(value, "target_group"))
        number = _value(
            value, "map_number", _value(value, "map", _value(value, "target_map")),
        )
        index = _value(
            value, "object_index", _value(value, "index", _value(value, "target_index")),
        )
        if None in (group, number, index):
            _fail(f"{label}: object owner identityが不足しています")
        return cls(
            _bounded(group, 0, 0xFF, f"{label}.group"),
            _bounded(number, 0, 0xFF, f"{label}.map"),
            _bounded(index, 0, 0xFF, f"{label}.object_index"),
        )


def decode_object_template(raw: bytes) -> dict[str, Any]:
    """24-byte ABIをdecodeする。x/yは必ずsigned s16として扱う。"""

    raw = _hex_bytes(raw, OBJECT_TEMPLATE_SIZE, "ObjectEventTemplate")
    movement_range = raw[10]
    return {
        "local_id": raw[0],
        "graphics_id": raw[1],
        "kind": raw[2],
        "padding_3": raw[3],
        "x": struct.unpack_from("<h", raw, 4)[0],
        "y": struct.unpack_from("<h", raw, 6)[0],
        "elevation": raw[8],
        "movement_type": raw[9],
        "movement_range_x": movement_range & 0x0F,
        "movement_range_y": movement_range >> 4,
        "padding_11": raw[11],
        "trainer_type": struct.unpack_from("<H", raw, 12)[0],
        "sight_range": struct.unpack_from("<H", raw, 14)[0],
        "script_pointer": struct.unpack_from("<I", raw, 16)[0],
        "flag": struct.unpack_from("<H", raw, 20)[0],
        "reserved_22_23_hex": raw[22:24].hex(),
    }


def _rom_offset(rom: bytes, pointer: Any, size: int, label: str) -> int:
    address = _integer(pointer, label)
    offset = address - ROM_BASE
    if address < ROM_BASE or offset < 0 or size < 0 or offset + size > len(rom):
        _fail(f"{label}: ROM範囲外 0x{address:08X}+{size}")
    return offset


def _u32_at(rom: bytes, offset: int, label: str) -> int:
    if offset < 0 or offset + 4 > len(rom):
        _fail(f"{label}: u32 offset範囲外")
    return struct.unpack_from("<I", rom, offset)[0]


def read_object_template(
    rom: bytes, group: int, map_number: int, object_index: int,
) -> bytes:
    """ROMの現在のmap header pointerから1件のtemplateを読む。"""

    group = _bounded(group, 0, 0xFF, "group")
    map_number = _bounded(map_number, 0, 0xFF, "map")
    object_index = _bounded(object_index, 0, 0xFF, "object_index")
    if len(rom) < MAP_GROUPS_POINTER_SITE + 4:
        _fail("ROMがgMapGroups pointer siteより短いです")
    groups_pointer = _u32_at(rom, MAP_GROUPS_POINTER_SITE, "gMapGroups")
    groups = _rom_offset(rom, groups_pointer, (group + 1) * 4, "gMapGroups")
    group_pointer = _u32_at(rom, groups + group * 4, f"map group {group}")
    group_at = _rom_offset(
        rom, group_pointer, (map_number + 1) * 4, f"map group {group}",
    )
    header_pointer = _u32_at(
        rom, group_at + map_number * 4, f"map header {group}/{map_number}",
    )
    header = _rom_offset(rom, header_pointer, 0x1C, "map header")
    events_pointer = _u32_at(rom, header + 4, "map events")
    events = _rom_offset(rom, events_pointer, EVENT_HEADER_SIZE, "map events")
    count = rom[events]
    if object_index >= count:
        raise Stage60ObjectIndexMissingError(
            f"OBJECT:{group:03d}/{map_number:03d}:{object_index:03d}: "
            f"Stage60 object index範囲外 count={count}"
        )
    objects_pointer = _u32_at(rom, events + 4, "object array")
    objects = _rom_offset(
        rom, objects_pointer, count * OBJECT_TEMPLATE_SIZE, "object array",
    )
    start = objects + object_index * OBJECT_TEMPLATE_SIZE
    return rom[start:start + OBJECT_TEMPLATE_SIZE]


def _normalize_owner_rows(owner_rows: Iterable[Any]) -> dict[str, ObjectOwnerKey]:
    result: dict[str, ObjectOwnerKey] = {}
    for index, row in enumerate(owner_rows):
        key = ObjectOwnerKey.parse(row, f"owner_rows[{index}]")
        if key.owner_id in result:
            _fail(f"owner row重複: {key.owner_id}")
        result[key.owner_id] = key
    if not result:
        _fail("object owner集合が空です")
    return dict(sorted(result.items()))


def _expand_topology_rows(rows: Iterable[Any]) -> dict[str, bytes]:
    records: dict[str, bytes] = {}
    for row_index, row in enumerate(rows):
        map_value = _value(row, "map")
        if not isinstance(map_value, str) or not re.fullmatch(r"\d{1,3}/\d{1,3}", map_value):
            _fail(f"topology_rows[{row_index}].map書式不正")
        group, number = (int(part) for part in map_value.split("/"))
        _bounded(group, 0, 0xFF, "topology group")
        _bounded(number, 0, 0xFF, "topology map")
        raw = _hex_bytes(_value(row, "raw_hex"), None, "topology raw")
        if not raw or len(raw) % OBJECT_TEMPLATE_SIZE:
            _fail(f"topology_rows[{row_index}] object array size不正")
        count = _value(row, "count")
        if count is not None and _integer(count, "topology count") != len(raw) // 24:
            _fail(f"topology_rows[{row_index}] count不一致")
        digest = _value(row, "sha256")
        if digest is not None and digest != _sha(raw):
            _fail(f"topology_rows[{row_index}] SHA-256不一致")
        for index in range(len(raw) // 24):
            owner_id = ObjectOwnerKey(group, number, index).owner_id
            if owner_id in records:
                _fail(f"topology exact record重複: {owner_id}")
            records[owner_id] = raw[index * 24:(index + 1) * 24]
    return records


def _missing_materialization_record(value: Any) -> tuple[str, bytes] | None:
    if value is None:
        return None
    requirement = _value(value, "requirement", value)
    key = ObjectOwnerKey(
        _bounded(_value(requirement, "target_group"), 0, 0xFF,
                 "missing target_group"),
        _bounded(_value(requirement, "target_map"), 0, 0xFF,
                 "missing target_map"),
        _bounded(_value(requirement, "target_index"), 0, 0xFF,
                 "missing target_index"),
    )
    direct = _value(value, "record_hex")
    if direct is not None:
        record = _hex_bytes(direct, 24, "missing record")
    else:
        payload_value = _value(value, "payload", _value(value, "payload_raw_hex"))
        payload = _hex_bytes(payload_value, None, "missing payload")
        payload_base = _integer(_value(value, "payload_base"), "missing payload_base")
        object_array = _integer(
            _value(value, "object_array_address"), "missing object_array_address",
        )
        start = object_array - payload_base + key.object_index * 24
        if start < 0 or start + 24 > len(payload):
            _fail("missing object recordがpayload範囲外です")
        record = payload[start:start + 24]
        digest = _value(value, "payload_sha256")
        if digest is not None and digest != _sha(payload):
            _fail("missing payload SHA-256不一致")
    target_local = _value(requirement, "target_local_id")
    if target_local is not None and record[0] != _integer(
        target_local, "missing target_local_id",
    ):
        _fail("missing object local ID不一致")
    return key.owner_id, record


def _set_u16(raw: bytearray, offset: int, value: Any, label: str) -> None:
    struct.pack_into("<H", raw, offset, _bounded(value, 0, 0xFFFF, label))


def _set_s16(raw: bytearray, offset: int, value: Any, label: str) -> None:
    number = _bounded(value, -0x8000, 0x7FFF, label)
    struct.pack_into("<h", raw, offset, number)


def _set_u32(raw: bytearray, offset: int, value: Any, label: str) -> None:
    struct.pack_into("<I", raw, offset, _bounded(value, 0, 0xFFFFFFFF, label))


def _append_step(
    provenance: dict[str, list[dict[str, Any]]], owner_id: str,
    kind: str, before: bytes, after: bytes, **details: Any,
) -> None:
    provenance[owner_id].append({
        "ordinal": len(provenance[owner_id]),
        "kind": kind,
        "changed": before != after,
        "before_sha256": _sha(before),
        "after_sha256": _sha(after),
        **details,
    })


def _resolve_owner_by_local(
    row: Any, records: Mapping[str, bytearray], label: str,
) -> str:
    direct = _value(row, "owner_id", _value(row, "npc_id"))
    if direct is not None:
        return ObjectOwnerKey.parse(direct, label).owner_id
    group = _value(row, "group", _value(row, "target_group"))
    number = _value(row, "map", _value(
        row, "map_number", _value(row, "target_map"),
    ))
    index = _value(row, "object_index", _value(
        row, "index", _value(row, "target_index"),
    ))
    if None not in (group, number, index):
        return ObjectOwnerKey(
            _bounded(group, 0, 0xFF, f"{label}.group"),
            _bounded(number, 0, 0xFF, f"{label}.map"),
            _bounded(index, 0, 0xFF, f"{label}.index"),
        ).owner_id
    local_id = _value(row, "local_id")
    if None in (group, number, local_id):
        _fail(f"{label}: owner identityまたはgroup/map/local_idが必要です")
    target_group = _bounded(group, 0, 0xFF, f"{label}.group")
    target_map = _bounded(number, 0, 0xFF, f"{label}.map")
    target_local = _bounded(local_id, 0, 0xFF, f"{label}.local_id")
    candidates = [
        owner_id for owner_id, raw in records.items()
        if (key := ObjectOwnerKey.parse(owner_id)).group == target_group
        and key.map_number == target_map and raw[0] == target_local
    ]
    if len(candidates) != 1:
        _fail(f"{label}: local ID ownerが一意ではありません: {candidates}")
    return candidates[0]


def _require_known(owner_id: str, records: Mapping[str, Any], label: str) -> None:
    if owner_id not in records:
        _fail(f"{label}: 未知のobject ownerです: {owner_id}")


def _apply_exact_patch_rows(
    rows: Iterable[Any], records: dict[str, bytearray],
    provenance: dict[str, list[dict[str, Any]]], *,
    kind: str, default_offset: int | None = None,
    exact_size: int | None = None,
) -> int:
    seen: set[tuple[str, int, int]] = set()
    count = 0
    for index, row in enumerate(rows):
        label = f"{kind}[{index}]"
        owner_id = _resolve_owner_by_local(row, records, label)
        _require_known(owner_id, records, label)
        expected = _hex_bytes(_value(row, "expected_hex"), exact_size, f"{label}.expected")
        replacement = _hex_bytes(
            _value(row, "replacement_hex"), exact_size, f"{label}.replacement",
        )
        if len(expected) != len(replacement):
            _fail(f"{label}: patch length不一致")
        offset_value = _value(row, "record_offset", _value(row, "template_offset"))
        offset = default_offset if offset_value is None else _integer(offset_value, label)
        if offset is None or offset < 0 or offset + len(expected) > 24:
            _fail(f"{label}: template内offset範囲外")
        identity = (owner_id, offset, len(expected))
        if identity in seen:
            _fail(f"{label}: exact patch重複: {identity}")
        seen.add(identity)
        current = records[owner_id]
        actual = bytes(current[offset:offset + len(expected)])
        # Placement reports include every jointly reserved owner.  A row with
        # patch_applied=false is an observation that no write was necessary;
        # in that case replacement_hex (the already-current bytes), not the
        # dormant Stage60 patch preimage, must match this derivation stage.
        patch_applied = _value(row, "patch_applied")
        required_current = replacement if patch_applied is False else expected
        if actual != required_current:
            _fail(
                f"{label}: preimage mismatch {owner_id}+{offset}: "
                f"{actual.hex()} != {required_current.hex()}"
            )
        before = bytes(current)
        current[offset:offset + len(replacement)] = replacement
        _append_step(
            provenance, owner_id, kind, before, bytes(current),
            template_offset=offset, expected_hex=expected.hex(),
            replacement_hex=replacement.hex(), patch_applied=patch_applied,
        )
        count += 1
    return count


def _apply_archive_rows(
    rows: Iterable[Any], records: dict[str, bytearray],
    provenance: dict[str, list[dict[str, Any]]],
) -> int:
    count = 0
    seen: set[str] = set()
    for map_index, map_row in enumerate(rows):
        group = _bounded(_value(map_row, "group"), 0, 0xFF, "archive group")
        number = _bounded(_value(map_row, "map"), 0, 0xFF, "archive map")
        objects = _rows(_value(map_row, "objects"))
        for object_index, row in enumerate(objects):
            label = f"archive_placement_rows[{map_index}].objects[{object_index}]"
            merged = {
                "group": group, "map": number,
                "local_id": _value(row, "local_id"),
            }
            owner_id = _resolve_owner_by_local(merged, records, label)
            _require_known(owner_id, records, label)
            if owner_id in seen:
                _fail(f"{label}: Archive owner重複: {owner_id}")
            seen.add(owner_id)
            before_point = _value(row, "before")
            after_point = _value(row, "after")
            if not all(
                isinstance(point, Sequence)
                and not isinstance(point, (str, bytes)) and len(point) == 2
                for point in (before_point, after_point)
            ):
                _fail(f"{label}: before/after point不正")
            expected = struct.pack(
                "<hh", *(
                    _bounded(value, -0x8000, 0x7FFF, f"{label}.before")
                    for value in before_point
                ),
            )
            replacement = struct.pack(
                "<hh", *(
                    _bounded(value, -0x8000, 0x7FFF, f"{label}.after")
                    for value in after_point
                ),
            )
            current = records[owner_id]
            if bytes(current[4:8]) != expected:
                _fail(f"{label}: Stage60 Archive座標preimage mismatch")
            prior = bytes(current)
            current[4:8] = replacement
            _append_step(
                provenance, owner_id, "ARCHIVE_POSITION", prior, bytes(current),
                template_offset=4, expected_hex=expected.hex(),
                replacement_hex=replacement.hex(),
            )
            count += 1
    return count


def _overlay_supplemental_fields(raw: bytearray, fields: Mapping[str, Any], label: str) -> None:
    known = {
        "local_id", "graphics_id", "kind", "padding_3", "x", "y",
        "elevation", "movement_type", "movement_range_x", "movement_range_y",
        "padding_11", "trainer_type", "sight_range", "script_pointer", "flag",
        "reserved_22_23_hex",
    }
    unknown = set(fields) - known
    if unknown:
        _fail(f"{label}: 未知のsupplemental field: {sorted(unknown)}")
    byte_fields = {
        "local_id": 0, "graphics_id": 1, "kind": 2, "padding_3": 3,
        "elevation": 8, "movement_type": 9, "padding_11": 11,
    }
    for name, offset in byte_fields.items():
        if name in fields:
            raw[offset] = _bounded(fields[name], 0, 0xFF, f"{label}.{name}")
    if "x" in fields:
        _set_s16(raw, 4, fields["x"], f"{label}.x")
    if "y" in fields:
        _set_s16(raw, 6, fields["y"], f"{label}.y")
    range_x = fields.get("movement_range_x")
    range_y = fields.get("movement_range_y")
    if range_x is not None or range_y is not None:
        x = raw[10] & 0x0F if range_x is None else _bounded(
            range_x, 0, 0x0F, f"{label}.movement_range_x",
        )
        y = raw[10] >> 4 if range_y is None else _bounded(
            range_y, 0, 0x0F, f"{label}.movement_range_y",
        )
        raw[10] = x | (y << 4)
    for name, offset in (("trainer_type", 12), ("sight_range", 14), ("flag", 20)):
        if name in fields:
            _set_u16(raw, offset, fields[name], f"{label}.{name}")
    if "script_pointer" in fields:
        _set_u32(raw, 16, fields["script_pointer"], f"{label}.script_pointer")
    if "reserved_22_23_hex" in fields:
        raw[22:24] = _hex_bytes(
            fields["reserved_22_23_hex"], 2, f"{label}.reserved_22_23_hex",
        )


def build_stage61_object_template_contracts(
    stage60_rom: bytes,
    owner_rows: Iterable[Any],
    *,
    topology_rows: Iterable[Any] = (),
    missing_object: Any = None,
    graphics_records: Iterable[Any] = (),
    visibility_rows: Iterable[Any] = (),
    semantic_root_plans: Iterable[Any] = (),
    root_targets: Mapping[Any, Any] | None = None,
    archive_placement_rows: Iterable[Any] = (),
    pre_placement_patches: Iterable[Any] = (),
    placement_repairs: Iterable[Any] = (),
    snorlax_sites: Iterable[Any] = (),
    supplemental_owners: Iterable[Any] | Mapping[Any, Any] = (),
    expected_owner_count: int | None = None,
    source_stage: int = 60,
) -> dict[str, Any]:
    """全object ownerの最終24-byte期待値をfinal ROM非依存で構築する。

    ``owner_rows`` から使う値は owner identity (group/map/index) だけである。
    final catalog由来のgraphics/座標/script等を期待値へ混入させない。
    ``pre_placement_patches`` はArchive以外の独立exact patch用で、各rowに
    ``record_offset``, ``expected_hex``, ``replacement_hex`` を要求する。
    """

    if not isinstance(stage60_rom, bytes) or not stage60_rom:
        _fail("Stage60 ROM bytesが必要です")
    owners = _normalize_owner_rows(owner_rows)
    if expected_owner_count is not None and len(owners) != expected_owner_count:
        _fail(f"owner count不一致: {len(owners)} != {expected_owner_count}")
    topology = _expand_topology_rows(_rows(
        topology_rows, nested_keys=("object_rows", "objects"),
    ))
    missing = _missing_materialization_record(missing_object)
    explicit_bases = dict(topology)
    if missing is not None:
        if missing[0] in explicit_bases:
            _fail(f"topology/missing base owner衝突: {missing[0]}")
        explicit_bases[missing[0]] = missing[1]
        if missing[0] not in owners:
            _fail(f"missing objectが未知のownerです: {missing[0]}")

    stage60_preimages: dict[str, bytes | None] = {}
    records: dict[str, bytearray] = {}
    provenance: dict[str, list[dict[str, Any]]] = {owner_id: [] for owner_id in owners}
    for owner_id, key in owners.items():
        try:
            stage60 = read_object_template(
                stage60_rom, key.group, key.map_number, key.object_index,
            )
        except Stage60ObjectIndexMissingError:
            if owner_id not in explicit_bases:
                raise
            stage60 = None
        stage60_preimages[owner_id] = stage60
        if stage60 is not None:
            records[owner_id] = bytearray(stage60)
            _append_step(
                provenance, owner_id, "STAGE60_PREIMAGE", stage60, stage60,
                source_stage=source_stage, raw_hex=stage60.hex(),
            )
        if owner_id in topology:
            before = bytes(records.get(owner_id, bytearray(topology[owner_id])))
            records[owner_id] = bytearray(topology[owner_id])
            _append_step(
                provenance, owner_id, "TOPOLOGY_EXACT_RAW", before,
                bytes(records[owner_id]), raw_hex=topology[owner_id].hex(),
            )
        if missing is not None and owner_id == missing[0]:
            before = bytes(records.get(owner_id, bytearray(missing[1])))
            records[owner_id] = bytearray(missing[1])
            _append_step(
                provenance, owner_id, "MISSING_OBJECT_PAYLOAD", before,
                bytes(records[owner_id]), raw_hex=missing[1].hex(),
            )
        if owner_id not in records:
            _fail(f"owner base templateを解決できません: {owner_id}")

    # The product builder deliberately suppresses the ordinary graphics clone
    # patch at the two Snorlax records, then installs reserved ID 239.  Resolve
    # those identities before applying graphics_records so this exception is
    # explicit and cannot depend on the post-graphics local lookup.
    normalized_snorlax_rows: list[tuple[str, Any]] = []
    seen_snorlax: set[str] = set()
    for index, source_row in enumerate(_rows(snorlax_sites)):
        row = source_row
        if isinstance(row, Sequence) and not isinstance(row, (str, bytes, bytearray)):
            if len(row) != 3:
                _fail(f"snorlax_sites[{index}]はgroup/map/local_idの3要素です")
            row = {"group": row[0], "map": row[1], "local_id": row[2]}
        label = f"snorlax_sites[{index}]"
        owner_id = _resolve_owner_by_local(row, records, label)
        _require_known(owner_id, records, label)
        if owner_id in seen_snorlax:
            _fail(f"Snorlax owner重複: {owner_id}")
        seen_snorlax.add(owner_id)
        normalized_snorlax_rows.append((owner_id, row))

    graphics_count = 0
    ignored_graphics_count = 0
    seen_graphics: set[str] = set()
    for index, row in enumerate(_rows(graphics_records, nested_keys=("object_records",))):
        key = ObjectOwnerKey(
            _bounded(_value(row, "group"), 0, 0xFF, "graphics group"),
            _bounded(_value(row, "map_number", _value(row, "map")), 0, 0xFF,
                     "graphics map"),
            _bounded(_value(row, "object_index"), 0, 0xFF, "graphics index"),
        )
        owner_id = key.owner_id
        if owner_id not in owners:
            ignored_graphics_count += 1
            continue
        if owner_id in seen_graphics:
            _fail(f"graphics owner重複: {owner_id}")
        seen_graphics.add(owner_id)
        preimage = _hex_bytes(
            _value(row, "record_preimage"), 24,
            f"graphics_records[{index}].record_preimage",
        )
        stage60 = stage60_preimages[owner_id]
        if stage60 is None or stage60 != preimage:
            actual = "NONE" if stage60 is None else stage60.hex()
            _fail(f"graphics full-record preimage mismatch: {owner_id}: {actual}")
        source = _bounded(_value(row, "source_graphics_id"), 0, 0xFF,
                          "source_graphics_id")
        target = _bounded(_value(row, "runtime_graphics_id"), 0, 0xFF,
                          "runtime_graphics_id")
        if preimage[1] != source:
            _fail(f"graphics source ID/preimage不一致: {owner_id}")
        action = str(_value(row, "action", ""))
        if action == "REMAP_CLEAN_CLOSURE" and source == target:
            _fail(f"graphics remap targetがsourceと同一です: {owner_id}")
        if action not in {
            "REMAP_CLEAN_CLOSURE", "KEEP_IDENTICAL_CLOSURE",
            "PRESERVE_DYNAMIC_GRAPHICS_ID",
        }:
            _fail(f"graphics action不正: {owner_id}: {action!r}")
        current = records[owner_id]
        if current[1] not in {source, target}:
            _fail(f"graphics current IDがsource/target外です: {owner_id}")
        before = bytes(current)
        if owner_id in seen_snorlax:
            # Keep the exact Stage60 source ID until the later reserved-ID
            # transform.  A pre-materialized clone here would hide a builder
            # ordering bug, so only source is accepted.
            if current[1] != source:
                _fail(f"Snorlax graphics clone suppression preimage不一致: {owner_id}")
            step_kind = "GRAPHICS_NAMESPACE_SUPPRESSED_BY_SNORLAX_RESERVATION"
        else:
            current[1] = target
            step_kind = "GRAPHICS_NAMESPACE"
        _append_step(
            provenance, owner_id, step_kind, before, bytes(current),
            action=action, source_graphics_id=source,
            runtime_graphics_id=target, record_preimage_sha256=_sha(preimage),
        )
        graphics_count += 1

    visibility_count = 0
    seen_visibility: set[str] = set()
    for index, row in enumerate(_rows(visibility_rows, nested_keys=("owner_rows", "owners"))):
        owner_id = ObjectOwnerKey.parse(row, f"visibility_rows[{index}]").owner_id
        _require_known(owner_id, records, f"visibility_rows[{index}]")
        if owner_id in seen_visibility:
            _fail(f"visibility owner重複: {owner_id}")
        seen_visibility.add(owner_id)
        before_flag = _bounded(_value(row, "target_flag_before"), 0, 0xFFFF,
                               "target_flag_before")
        # ``target_flag_after`` is the generic namespace-plan target.  The
        # builder's applied-owner row additionally carries ``target_flag`` for
        # explicit product overrides (notably the two Snorlax story flags),
        # which is the actual later transform and therefore has precedence.
        after_value = _value(row, "target_flag", _value(row, "target_flag_after"))
        if after_value is None:
            _fail(f"visibility target transform不足: {owner_id}")
        after_flag = _bounded(after_value, 0, 0xFFFF, "target_flag_after")
        stage60 = stage60_preimages[owner_id]
        if stage60 is not None and struct.unpack_from("<H", stage60, 20)[0] != before_flag:
            _fail(f"visibility Stage60 preimage mismatch: {owner_id}")
        current = records[owner_id]
        current_flag = struct.unpack_from("<H", current, 20)[0]
        if current_flag not in {before_flag, after_flag}:
            _fail(f"visibility current flagがbefore/after外です: {owner_id}")
        before = bytes(current)
        struct.pack_into("<H", current, 20, after_flag)
        _append_step(
            provenance, owner_id, "VISIBILITY_NAMESPACE", before, bytes(current),
            target_flag_before=before_flag, target_flag_after=after_flag,
            generic_target_flag_after=_value(row, "target_flag_after"),
            mapping_basis=_value(row, "mapping_basis"),
        )
        visibility_count += 1

    normalized_targets = {
        _integer(source, "root_targets source"):
            _integer(target, "root_targets target")
        for source, target in (root_targets or {}).items()
    }
    semantic_count = 0
    seen_semantic: set[str] = set()
    for root_index, root in enumerate(_rows(semantic_root_plans, nested_keys=("root_plans",))):
        source_root = _integer(
            _value(root, "source_script_pointer"),
            f"semantic_root_plans[{root_index}].source_script_pointer",
        )
        object_owners = [
            owner for owner in _rows(_value(root, "owners"))
            if str(_value(owner, "event", _value(owner, "owner_kind", ""))) == "OBJECT"
        ]
        if object_owners and source_root not in normalized_targets:
            _fail(f"semantic root transform不足: 0x{source_root:08X}")
        target = normalized_targets.get(source_root)
        for owner_index, owner in enumerate(object_owners):
            label = f"semantic_root_plans[{root_index}].owners[{owner_index}]"
            owner_id = ObjectOwnerKey.parse(owner, label).owner_id
            _require_known(owner_id, records, label)
            if owner_id in seen_semantic:
                _fail(f"semantic owner重複: {owner_id}")
            seen_semantic.add(owner_id)
            assert target is not None
            if not ROM_BASE <= target < ROM_LIMIT:
                _fail(f"semantic target ROM pointer範囲外: {owner_id}")
            current = records[owner_id]
            current_pointer = struct.unpack_from("<I", current, 16)[0]
            stage60 = stage60_preimages[owner_id]
            stage60_pointer = (
                None if stage60 is None else struct.unpack_from("<I", stage60, 16)[0]
            )
            allowed = {source_root, target}
            if stage60_pointer is not None:
                allowed.add(stage60_pointer)
            if current_pointer not in allowed:
                _fail(f"semantic current pointerがsource/preimage/target外です: {owner_id}")
            before = bytes(current)
            struct.pack_into("<I", current, 16, target)
            _append_step(
                provenance, owner_id, "SEMANTIC_ROOT_RELOCATION", before,
                bytes(current), source_script_pointer=f"0x{source_root:08X}",
                target_script_pointer=f"0x{target:08X}",
                stage60_script_pointer=(
                    None if stage60_pointer is None
                    else f"0x{stage60_pointer:08X}"
                ),
            )
            semantic_count += 1

    archive_count = _apply_archive_rows(
        _rows(archive_placement_rows), records, provenance,
    )
    preplacement_count = _apply_exact_patch_rows(
        _rows(pre_placement_patches), records, provenance,
        kind="PRE_PLACEMENT_EXACT_PATCH",
    )
    placement_count = _apply_exact_patch_rows(
        _rows(placement_repairs, nested_keys=("repairs",)), records, provenance,
        kind="FINAL_INTERACTION_PLACEMENT", default_offset=4, exact_size=7,
    )

    snorlax_count = 0
    for index, (owner_id, row) in enumerate(normalized_snorlax_rows):
        label = f"snorlax_sites[{index}]"
        source = _bounded(_value(row, "source_graphics_id", 109), 0, 0xFF,
                          f"{label}.source_graphics_id")
        target = _bounded(_value(row, "runtime_graphics_id", 239), 0, 0xFF,
                          f"{label}.runtime_graphics_id")
        current = records[owner_id]
        if current[1] not in {source, target}:
            _fail(f"{label}: graphics preimage mismatch: {current[1]} not {source}/{target}")
        before = bytes(current)
        current[1] = target
        _append_step(
            provenance, owner_id, "SNORLAX_RESERVED_GRAPHICS", before,
            bytes(current), source_graphics_id=source,
            runtime_graphics_id=target,
        )
        snorlax_count += 1

    supplemental_count = 0
    seen_supplemental: set[str] = set()
    for index, row in enumerate(_rows(supplemental_owners, nested_keys=("owners",))):
        label = f"supplemental_owners[{index}]"
        owner_id = ObjectOwnerKey.parse(row, label).owner_id
        _require_known(owner_id, records, label)
        if owner_id in seen_supplemental:
            _fail(f"supplemental owner重複: {owner_id}")
        seen_supplemental.add(owner_id)
        object_fields = _value(row, "object")
        if not isinstance(object_fields, Mapping):
            _fail(f"{label}.object field mapping不足")
        fields = dict(object_fields)
        for name in ("local_id", "script_pointer"):
            value = _value(row, name)
            if value is not None:
                fields[name] = value
        before = bytes(records[owner_id])
        _overlay_supplemental_fields(records[owner_id], fields, label)
        _append_step(
            provenance, owner_id, "SUPPLEMENTAL_EXPLICIT_FIELDS", before,
            bytes(records[owner_id]), fields=deepcopy(fields),
            manifest_sha256=_value(row, "manifest_sha256"),
        )
        supplemental_count += 1

    result_rows: list[dict[str, Any]] = []
    for owner_id, key in owners.items():
        expected = bytes(records[owner_id])
        if len(expected) != 24:
            _fail(f"final template size drift: {owner_id}")
        steps = provenance[owner_id]
        if not steps:
            _fail(f"template provenanceが空です: {owner_id}")
        if [step["ordinal"] for step in steps] != list(range(len(steps))):
            _fail(f"template provenance ordinal不正: {owner_id}")
        result_rows.append({
            "owner_id": owner_id,
            "group": key.group,
            "map": key.map_number,
            "object_index": key.object_index,
            "stage60_preimage_raw_hex": (
                None if stage60_preimages[owner_id] is None
                else stage60_preimages[owner_id].hex()
            ),
            "stage60_preimage_sha256": (
                None if stage60_preimages[owner_id] is None
                else _sha(stage60_preimages[owner_id])
            ),
            "expected_template_raw_hex": expected.hex().upper(),
            "expected_template_sha256": _sha(expected),
            "expected_fields": decode_object_template(expected),
            "provenance": steps,
        })

    transform_counts = {
        "topology_exact_owner_count": sum(owner_id in topology for owner_id in owners),
        "missing_object_owner_count": int(missing is not None),
        "graphics_owner_count": graphics_count,
        "graphics_nonruntime_owner_ignored_count": ignored_graphics_count,
        "visibility_owner_count": visibility_count,
        "semantic_owner_count": semantic_count,
        "archive_position_owner_count": archive_count,
        "pre_placement_exact_patch_count": preplacement_count,
        "final_interaction_placement_owner_count": placement_count,
        "snorlax_owner_count": snorlax_count,
        "supplemental_owner_count": supplemental_count,
    }
    document: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "contract_kind": "STAGE61_INDEPENDENT_OBJECT_EVENT_TEMPLATE_24_BYTE_ORACLE",
        "status": "PASS",
        "source_stage": source_stage,
        "source_rom_sha256": _sha(stage60_rom),
        "expectation_source_policy": (
            "STAGE60_PREIMAGE_PLUS_EXPLICIT_TRANSFORM_PLANS_ONLY_"
            "FINAL_ROM_FORBIDDEN_DURING_BUILD"
        ),
        "owner_count": len(result_rows),
        "transform_counts": transform_counts,
        "assertions": {
            "owner_identity_unique": len(result_rows) == len(owners),
            "every_owner_has_exact_24_bytes": all(
                len(bytes.fromhex(row["expected_template_raw_hex"])) == 24
                for row in result_rows
            ),
            "every_expected_sha256_matches": all(
                _sha(bytes.fromhex(row["expected_template_raw_hex"]))
                    == row["expected_template_sha256"]
                for row in result_rows
            ),
            "signed_xy_decoder_used": all(
                row["expected_fields"]["x"]
                    == struct.unpack_from(
                        "<h", bytes.fromhex(row["expected_template_raw_hex"]), 4,
                    )[0]
                and row["expected_fields"]["y"]
                    == struct.unpack_from(
                        "<h", bytes.fromhex(row["expected_template_raw_hex"]), 6,
                    )[0]
                for row in result_rows
            ),
            "final_rom_not_an_expectation_input": True,
        },
        "owners": result_rows,
    }
    document["contract_sha256"] = _self_hash(document)
    validate_stage61_object_template_contract_document(document)
    return document


def validate_stage61_object_template_contract_document(
    document: Mapping[str, Any],
) -> None:
    """保存・受け渡し後のcontract自体をfail-closedで検証する。"""

    if not isinstance(document, Mapping) or document.get("schema_version") != SCHEMA_VERSION:
        _fail("object template contract schema不一致")
    if document.get("contract_kind") != (
        "STAGE61_INDEPENDENT_OBJECT_EVENT_TEMPLATE_24_BYTE_ORACLE"
    ) or document.get("status") != "PASS":
        _fail("object template contract kind/status不一致")
    if document.get("expectation_source_policy") != (
        "STAGE60_PREIMAGE_PLUS_EXPLICIT_TRANSFORM_PLANS_ONLY_"
        "FINAL_ROM_FORBIDDEN_DURING_BUILD"
    ):
        _fail("object template expectation source policy不一致")
    if document.get("contract_sha256") != _self_hash(document):
        _fail("object template contract self hash不一致")
    rows = document.get("owners")
    if not isinstance(rows, list) or len(rows) != document.get("owner_count") or not rows:
        _fail("object template owner cardinality不一致")
    seen: set[str] = set()
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            _fail(f"owners[{index}] schema不正")
        key = ObjectOwnerKey.parse(row, f"owners[{index}]")
        if key.owner_id in seen:
            _fail(f"contract owner重複: {key.owner_id}")
        seen.add(key.owner_id)
        raw = _canonical_template_hex(
            row.get("expected_template_raw_hex"), "expected template raw",
        )
        if row.get("expected_template_sha256") != _sha(raw):
            _fail(f"expected template SHA-256不一致: {key.owner_id}")
        if row.get("expected_fields") != decode_object_template(raw):
            _fail(f"expected template fields不一致: {key.owner_id}")
        steps = row.get("provenance")
        if not isinstance(steps, list) or not steps or [
            step.get("ordinal") for step in steps if isinstance(step, Mapping)
        ] != list(range(len(steps))):
            _fail(f"provenance ordinal不一致: {key.owner_id}")
    assertions = document.get("assertions")
    if not isinstance(assertions, Mapping) or not assertions or any(
        value is not True for value in assertions.values()
    ):
        _fail("object template contract assertion FAIL")


def validate_stage61_object_template_contracts(
    document: Mapping[str, Any],
    *,
    final_rom: bytes | None = None,
    observed_templates: Mapping[str, bytes | str] | None = None,
) -> dict[str, Any]:
    """独立期待値とobserved final templateをexact 24 bytesで比較する。

    ``final_rom`` と ``observed_templates`` は排他的である。前者を使う場合も
    expectation documentを先に自己検証し、その後にmap pointerから読む。
    """

    validate_stage61_object_template_contract_document(document)
    if (final_rom is None) == (observed_templates is None):
        _fail("final_romまたはobserved_templatesをexactly one指定してください")
    expected = {
        str(row["owner_id"]): bytes.fromhex(str(row["expected_template_raw_hex"]))
        for row in document["owners"]
    }
    if final_rom is not None:
        if not isinstance(final_rom, bytes) or not final_rom:
            _fail("final_rom bytesが不正です")
        observed = {
            owner_id: read_object_template(
                final_rom, key.group, key.map_number, key.object_index,
            )
            for owner_id in expected
            for key in (ObjectOwnerKey.parse(owner_id),)
        }
        observed_source = "FINAL_ROM_MAP_EVENT_POINTERS"
        observed_sha = _sha(final_rom)
    else:
        assert observed_templates is not None
        observed = {}
        for owner_id, raw in observed_templates.items():
            canonical_owner = ObjectOwnerKey.parse(
                owner_id, "observed owner",
            ).owner_id
            observed[canonical_owner] = (
                _canonical_template_hex(raw, f"observed {owner_id}")
                if isinstance(raw, str)
                else _hex_bytes(raw, 24, f"observed {owner_id}")
            )
        observed_source = "EXPLICIT_OBSERVED_TEMPLATE_MAPPING"
        observed_sha = _sha(_stable({
            owner_id: raw.hex() for owner_id, raw in sorted(observed.items())
        }))
    missing = sorted(set(expected) - set(observed))
    unknown = sorted(set(observed) - set(expected))
    if missing or unknown:
        _fail(f"observed owner集合不一致: missing={missing} unknown={unknown}")
    mismatches = [
        {
            "owner_id": owner_id,
            "expected_hex": expected[owner_id].hex(),
            "observed_hex": observed[owner_id].hex(),
            "differing_offsets": [
                index for index, (left, right) in enumerate(
                    zip(expected[owner_id], observed[owner_id], strict=True)
                ) if left != right
            ],
        }
        for owner_id in sorted(expected)
        if observed[owner_id] != expected[owner_id]
    ]
    if mismatches:
        first = mismatches[0]
        _fail(
            f"final ObjectEventTemplate mismatch: {first['owner_id']} "
            f"offsets={first['differing_offsets']}"
        )
    return {
        "schema_version": 1,
        "status": "PASS",
        "contract_sha256": document["contract_sha256"],
        "observed_source": observed_source,
        "observed_sha256": observed_sha,
        "owner_count": len(expected),
        "mismatch_count": 0,
        "exact_24_byte_match_all": True,
    }


def attach_stage61_object_template_contracts(
    owner_rows: Iterable[Mapping[str, Any]],
    document: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """catalog rowsへ期待raw/hash/fieldsだけをexact owner identityで付与する。"""

    validate_stage61_object_template_contract_document(document)
    expected = {str(row["owner_id"]): row for row in document["owners"]}
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, source in enumerate(owner_rows):
        owner_id = ObjectOwnerKey.parse(source, f"owner_rows[{index}]").owner_id
        if owner_id not in expected:
            _fail(f"attach対象が未知のownerです: {owner_id}")
        if owner_id in seen:
            _fail(f"attach対象owner重複: {owner_id}")
        seen.add(owner_id)
        contract = expected[owner_id]
        result.append({
            **deepcopy(dict(source)),
            "expected_template_raw_hex": contract["expected_template_raw_hex"],
            "expected_template_sha256": contract["expected_template_sha256"],
            "expected_template_fields": deepcopy(contract["expected_fields"]),
            "expected_template_contract_sha256": document["contract_sha256"],
        })
    missing = sorted(set(expected) - seen)
    if missing:
        _fail(f"attach対象owner不足: {missing}")
    return result


__all__ = [
    "EVENT_HEADER_SIZE",
    "MAP_GROUPS_POINTER_SITE",
    "OBJECT_TEMPLATE_SIZE",
    "ObjectOwnerKey",
    "ROM_BASE",
    "SCHEMA_VERSION",
    "Stage60ObjectIndexMissingError",
    "Stage61ObjectTemplateContractError",
    "attach_stage61_object_template_contracts",
    "build_stage61_object_template_contracts",
    "decode_object_template",
    "read_object_template",
    "validate_stage61_object_template_contract_document",
    "validate_stage61_object_template_contracts",
]
