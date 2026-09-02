#!/usr/bin/env python3
"""Stage61 MAP scriptの物理ライフサイクルをROMから構造decodeする。

このmoduleはevent executorや生成済みowner inventoryを信用しない。gMapGroupsから
MapHeader.mapScriptsを引き直し、outer tableとconditional tableのrecord identityを
固定する。実scriptの副作用合成はinteraction oracleが担当し、このmoduleはengineが
どのtagをどの順序で試すか、各条件tableでどのrowが最初に一致するかだけを所有する。
"""

from __future__ import annotations

from copy import deepcopy
import hashlib
import struct
from typing import Any, Mapping


ROM_BASE = 0x08000000
MAP_GROUPS_POINTER_SITE = 0x00054B0C
MAP_HEADER_SIZE = 0x1C
OUTER_RECORD_SIZE = 5
CONDITION_RECORD_SIZE = 8
MAX_OUTER_ROWS = 64
MAX_CONDITION_ROWS = 256
TEMP_VAR_START = 0x4000
TEMP_VAR_END = 0x400F
TEMP_FLAG_START = 0x0000
TEMP_FLAG_END = 0x001F
SYSTEM_FLAGS_CLEARED_ON_DESTINATION_LOAD = (
    0x0803,  # FLAG_SYS_WHITE_FLUTE_ACTIVE
    0x0804,  # FLAG_SYS_BLACK_FLUTE_ACTIVE
    0x0805,  # FLAG_SYS_USE_STRENGTH
    0x0807,  # FLAG_SYS_SPECIAL_WILD_BATTLE
    0x0842,  # FLAG_SYS_INFORMED_OF_LOCAL_WIRELESS_PLAYER
)
MAP_CONDITION_VAR_RANGES = (
    (0x4000, 0x40FF),
    (0x5000, 0x51FF),
)
MAP_CONDITION_IMMEDIATE_END = 0x3FFF

ATTEMPT_DISPATCH = "DISPATCH"
ATTEMPT_TAG_ABSENT = "TAG_ABSENT"
ATTEMPT_NO_CONDITION_MATCH = "NO_CONDITION_MATCH"

CONDITIONAL_TAGS = frozenset({2, 4})
VALID_TAGS = frozenset(range(1, 8))
VALID_PRODUCERS = frozenset({
    "STOCK_WARP", "ENGINE_TELEPORT", "CONNECTION",
})


class Stage61MapLifecycleError(RuntimeError):
    """MAP lifecycle構造が物理ROMと一致しない。"""


def _fail(message: str) -> None:
    raise Stage61MapLifecycleError(message)


def _offset(rom: bytes, address: int, size: int, label: str) -> int:
    if isinstance(address, bool) or not isinstance(address, int) \
            or isinstance(size, bool) or not isinstance(size, int) \
            or size < 0:
        _fail(f"{label} address/size型不正")
    offset = address - ROM_BASE if address >= ROM_BASE else address
    if offset < 0 or offset + size > len(rom):
        _fail(f"{label} ROM範囲外:0x{address:08X}+{size}")
    return offset


def _u16(rom: bytes, offset: int) -> int:
    if offset < 0 or offset + 2 > len(rom):
        _fail("u16 ROM範囲外")
    return struct.unpack_from("<H", rom, offset)[0]


def _u32(rom: bytes, offset: int) -> int:
    if offset < 0 or offset + 4 > len(rom):
        _fail("u32 ROM範囲外")
    return struct.unpack_from("<I", rom, offset)[0]


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _is_supported_condition_var(identifier: int) -> bool:
    return any(
        start <= identifier <= end
        for start, end in MAP_CONDITION_VAR_RANGES
    )


def map_header_address(rom: bytes, group: int, number: int) -> int:
    """gMapGroups ABIからphysical MapHeader pointerを解決する。"""

    if any(isinstance(value, bool) or not isinstance(value, int)
           or not 0 <= value <= 0xFF for value in (group, number)):
        _fail("map group/number不正")
    root_pointer = _u32(
        rom, _offset(rom, MAP_GROUPS_POINTER_SITE, 4, "gMapGroups literal"),
    )
    root = _offset(rom, root_pointer, (group + 1) * 4, "gMapGroups")
    group_pointer = _u32(rom, root + group * 4)
    group_rows = _offset(
        rom, group_pointer, (number + 1) * 4, f"map group {group}",
    )
    header_pointer = _u32(rom, group_rows + number * 4)
    _offset(rom, header_pointer, MAP_HEADER_SIZE, "MapHeader")
    return header_pointer


def _decode_conditions(
    rom: bytes,
    *,
    group: int,
    number: int,
    outer_index: int,
    tag: int,
    table_pointer: int,
) -> list[dict[str, Any]]:
    cursor = _offset(
        rom, table_pointer, 2,
        f"conditional table {group:03d}/{number:03d}/{outer_index}",
    )
    rows: list[dict[str, Any]] = []
    for condition_index in range(MAX_CONDITION_ROWS):
        variable = _u16(rom, cursor)
        if variable == 0:
            return rows
        raw = bytes(rom[_offset(
            rom, ROM_BASE + cursor, CONDITION_RECORD_SIZE,
            "conditional record",
        ):cursor + CONDITION_RECORD_SIZE])
        value = _u16(rom, cursor + 2)
        if not _is_supported_condition_var(variable):
            _fail(
                "conditional LHS VAR契約違反:"
                f"{group:03d}/{number:03d}/{outer_index}/"
                f"{condition_index}:0x{variable:04X}"
            )
        # Engineは両operandへVarGetを適用する。Stage61のMAP condition
        # contractはRHSを0x0000..0x3FFFの即値に限定しているため、変数IDを
        # literalとして誤評価せずdecode時点でfail closedする。
        if not 0 <= value <= MAP_CONDITION_IMMEDIATE_END:
            _fail(
                "conditional RHS即値契約違反:"
                f"{group:03d}/{number:03d}/{outer_index}/"
                f"{condition_index}:0x{value:04X}"
            )
        root_pc = _u32(rom, cursor + 4)
        _offset(rom, root_pc, 1, "conditional root")
        record_address = ROM_BASE + cursor
        rows.append({
            "condition_index": condition_index,
            "tag": tag,
            "record_address": record_address,
            "root_field_address": record_address + 4,
            "record_raw_hex": raw.hex(),
            "record_raw_sha256": _sha256(raw),
            "variable": variable,
            "value": value,
            "root_pc": root_pc,
            "owner_id": (
                f"MAP:{group:03d}/{number:03d}:"
                f"{outer_index:03d}:{condition_index:03d}"
            ),
        })
        cursor += CONDITION_RECORD_SIZE
    _fail(
        "conditional table未終端:"
        f"{group:03d}/{number:03d}/{outer_index}"
    )


def decode_map_lifecycle_topology(
    rom: bytes, group: int, number: int,
) -> dict[str, Any]:
    """1 mapの全outer/condition recordをdecodeし、tag重複を拒否する。"""

    header_pointer = map_header_address(rom, group, number)
    header = _offset(rom, header_pointer, MAP_HEADER_SIZE, "MapHeader")
    table_pointer = _u32(rom, header + 8)
    map_id = f"{group:03d}/{number:03d}"
    if table_pointer in (0, 0xFFFFFFFF):
        return {
            "schema_version": 1,
            "kind": "STAGE61_MAP_LIFECYCLE_TOPOLOGY",
            "map": {"group": group, "map": number},
            "map_id": map_id,
            "header_address": header_pointer,
            "table_pointer": None,
            "outer_rows": [],
            "by_tag": {},
            "rom_sha256": _sha256(rom),
        }

    cursor = _offset(rom, table_pointer, 1, "MapScripts outer table")
    rows: list[dict[str, Any]] = []
    by_tag: dict[str, dict[str, Any]] = {}
    for outer_index in range(MAX_OUTER_ROWS):
        tag = rom[cursor]
        if tag == 0:
            return {
                "schema_version": 1,
                "kind": "STAGE61_MAP_LIFECYCLE_TOPOLOGY",
                "map": {"group": group, "map": number},
                "map_id": map_id,
                "header_address": header_pointer,
                "table_pointer": table_pointer,
                "outer_rows": rows,
                "by_tag": by_tag,
                "rom_sha256": _sha256(rom),
            }
        if tag not in VALID_TAGS:
            _fail(f"outer tag不正:{map_id}/{outer_index}:{tag}")
        if str(tag) in by_tag:
            _fail(f"outer tag重複:{map_id}:tag{tag}")
        raw = bytes(rom[cursor:cursor + OUTER_RECORD_SIZE])
        if len(raw) != OUTER_RECORD_SIZE:
            _fail(f"outer record範囲外:{map_id}/{outer_index}")
        pointer = _u32(rom, cursor + 1)
        record_address = ROM_BASE + cursor
        row: dict[str, Any] = {
            "outer_index": outer_index,
            "tag": tag,
            "record_address": record_address,
            "pointer_field_address": record_address + 1,
            "record_raw_hex": raw.hex(),
            "record_raw_sha256": _sha256(raw),
        }
        if tag in CONDITIONAL_TAGS:
            conditions = _decode_conditions(
                rom,
                group=group,
                number=number,
                outer_index=outer_index,
                tag=tag,
                table_pointer=pointer,
            )
            row.update({
                "dispatch_kind": "CONDITION_TABLE",
                "condition_table_pointer": pointer,
                "conditions": conditions,
            })
        else:
            _offset(rom, pointer, 1, "direct map root")
            row.update({
                "dispatch_kind": "DIRECT",
                "root_pc": pointer,
                "root_field_address": record_address + 1,
                "owner_id": (
                    f"MAP:{map_id}:{outer_index:03d}:DIRECT"
                ),
            })
        rows.append(row)
        by_tag[str(tag)] = deepcopy(row)
        cursor = _offset(
            rom, ROM_BASE + cursor + OUTER_RECORD_SIZE, 1,
            "next MapScripts outer record",
        )
    _fail(f"outer table未終端:{map_id}")


def _copy_variable_state(values: Mapping[int, int]) -> dict[int, int]:
    if not isinstance(values, Mapping):
        _fail("VAR state schema不正")
    result: dict[int, int] = {}
    for key, value in values.items():
        if isinstance(key, bool) or not isinstance(key, int) \
                or isinstance(value, bool) or not isinstance(value, int) \
                or not 0 <= key <= 0xFFFF or not 0 <= value <= 0xFFFF:
            _fail("VAR state不正")
        result[key] = value
    return result


def _copy_flag_state(values: Mapping[int, bool]) -> dict[int, bool]:
    if not isinstance(values, Mapping):
        _fail("FLAG state schema不正")
    result: dict[int, bool] = {}
    for key, value in values.items():
        if isinstance(key, bool) or not isinstance(key, int) \
                or not isinstance(value, bool) \
                or not 0 <= key <= 0xFFFF:
            _fail("FLAG state不正")
        result[key] = value
    return result


def apply_destination_engine_clear(
    variables: Mapping[int, int], flags: Mapping[int, bool],
) -> dict[str, Any]:
    """ClearTempFieldEventDataをpureな明示engine transformとして返す。

    入力mappingは変更しない。``variables`` / ``flags`` は適用後state、write列は
    interaction oracleがscript effectと混同せずordered lifecycle evidenceへ
    取り込むための完全なengine write集合である。
    """

    next_variables = _copy_variable_state(variables)
    next_flags = _copy_flag_state(flags)
    variable_writes = [
        {"id": identifier, "value": 0}
        for identifier in range(TEMP_VAR_START, TEMP_VAR_END + 1)
    ]
    temporary_flag_writes = [
        {"id": identifier, "value": False}
        for identifier in range(TEMP_FLAG_START, TEMP_FLAG_END + 1)
    ]
    system_flag_writes = [
        {"id": identifier, "value": False}
        for identifier in SYSTEM_FLAGS_CLEARED_ON_DESTINATION_LOAD
    ]
    for row in variable_writes:
        next_variables[row["id"]] = row["value"]
    for row in (*temporary_flag_writes, *system_flag_writes):
        next_flags[row["id"]] = row["value"]
    return {
        "schema_version": 1,
        "kind": "STAGE61_MAP_ENGINE_TRANSFORM",
        "operation": "CLEAR_TEMP_FIELD_EVENT_DATA",
        "phase": "DESTINATION_TEMP_CLEAR",
        "variable_writes": variable_writes,
        "temporary_flag_writes": temporary_flag_writes,
        "system_flag_writes": system_flag_writes,
        "variables": next_variables,
        "flags": next_flags,
    }


def clear_destination_temp_vars(
    values: Mapping[int, int],
) -> dict[int, int]:
    """旧API互換: destination load後のVAR stateだけを返す。"""

    result = _copy_variable_state(values)
    for identifier in range(TEMP_VAR_START, TEMP_VAR_END + 1):
        result[identifier] = 0
    return result


def select_first_condition(
    outer_row: Mapping[str, Any], values: Mapping[int, int],
) -> dict[str, Any] | None:
    """現在stateでROM順の最初に一致するconditional rowだけを返す。"""

    state = _copy_variable_state(values)
    if outer_row.get("dispatch_kind") != "CONDITION_TABLE" \
            or not isinstance(outer_row.get("conditions"), list):
        _fail("conditional outer row不正")
    for row in outer_row["conditions"]:
        if not isinstance(row, Mapping):
            _fail("conditional row schema不正")
        variable = row.get("variable")
        value = row.get("value")
        if isinstance(variable, bool) or not isinstance(variable, int) \
                or isinstance(value, bool) or not isinstance(value, int):
            _fail("conditional operand不正")
        if not _is_supported_condition_var(variable):
            _fail(f"conditional LHS VAR契約違反:0x{variable:04X}")
        if not 0 <= value <= MAP_CONDITION_IMMEDIATE_END:
            _fail(f"conditional RHS即値契約違反:0x{value:04X}")
        if variable not in state:
            _fail(f"conditional LHS state不足:0x{variable:04X}")
        # VarGet(value)はStage61 contract上、value < 0x4000なのでvalue自身。
        if state[variable] == value:
            return deepcopy(dict(row))
    return None


def lifecycle_attempts(
    producer_kind: str, *, include_field_return: bool,
) -> list[dict[str, Any]]:
    """固定上流engine順をtag attempt列として返す。

    tag2はinitial loadの最後に1回だけ記録する。以後の反復はscript副作用を知る
    interaction oracleがquiescentまで追加する。
    """

    if producer_kind not in VALID_PRODUCERS:
        _fail(f"MAP producer kind不正:{producer_kind}")
    attempts: list[dict[str, Any]] = [{
        "phase": "DESTINATION_TEMP_CLEAR", "tag": None,
    }]
    for phase, tag in (
        ("INITIAL_TRANSITION", 3),
        ("INITIAL_LOAD", 1),
        ("INITIAL_RESUME", 5),
    ):
        attempts.append({"phase": phase, "tag": tag})
    if producer_kind != "CONNECTION":
        attempts.append({"phase": "INITIAL_WARP_INTO", "tag": 4})
    attempts.append({"phase": "PRE_FIELD_INPUT_ON_FRAME", "tag": 2})
    if include_field_return:
        attempts.extend((
            {"phase": "FIELD_RETURN_RESUME", "tag": 5},
            {"phase": "FIELD_RETURN_RETURN_TO_FIELD", "tag": 7},
        ))
    for ordinal, row in enumerate(attempts):
        row["attempt_ordinal"] = ordinal
    return attempts


def resolve_attempt_result(
    topology: Mapping[str, Any], tag: int, values: Mapping[int, int],
) -> dict[str, Any]:
    """attemptを解決し、未dispatch理由も含むexact resultを返す。"""

    if isinstance(tag, bool) or not isinstance(tag, int) or tag not in VALID_TAGS:
        _fail(f"MAP lifecycle tag不正:{tag!r}")

    by_tag = topology.get("by_tag")
    if not isinstance(by_tag, Mapping):
        _fail("MAP topology by_tag不正")
    outer = by_tag.get(str(tag))
    if outer is None:
        return {"tag": tag, "result": ATTEMPT_TAG_ABSENT}
    if not isinstance(outer, Mapping):
        _fail("MAP topology outer row不正")
    if outer.get("dispatch_kind") == "DIRECT":
        return {
            "tag": tag,
            "result": ATTEMPT_DISPATCH,
            "outer_index": outer["outer_index"],
            "outer_record_address": outer["record_address"],
            "selected_condition_index": None,
            "selected_condition_record_address": None,
            "root_field_address": outer["root_field_address"],
            "root_pc": outer["root_pc"],
            "owner_id": outer["owner_id"],
        }
    if outer.get("dispatch_kind") != "CONDITION_TABLE":
        _fail("MAP topology dispatch kind不正")
    selected = select_first_condition(outer, values)
    if selected is None:
        return {
            "tag": tag,
            "result": ATTEMPT_NO_CONDITION_MATCH,
            "outer_index": outer["outer_index"],
            "outer_record_address": outer["record_address"],
        }
    return {
        "tag": tag,
        "result": ATTEMPT_DISPATCH,
        "outer_index": outer["outer_index"],
        "outer_record_address": outer["record_address"],
        "selected_condition_index": selected["condition_index"],
        "selected_condition_record_address": selected["record_address"],
        "root_field_address": selected["root_field_address"],
        "root_pc": selected["root_pc"],
        "owner_id": selected["owner_id"],
    }


def resolve_attempt(
    topology: Mapping[str, Any], tag: int, values: Mapping[int, int],
) -> dict[str, Any] | None:
    """旧API互換: exact dispatch、または未dispatch時にNoneを返す。"""

    result = resolve_attempt_result(topology, tag, values)
    if result["result"] != ATTEMPT_DISPATCH:
        return None
    dispatch = deepcopy(result)
    del dispatch["result"]
    return dispatch


__all__ = [
    "ATTEMPT_DISPATCH",
    "ATTEMPT_NO_CONDITION_MATCH",
    "ATTEMPT_TAG_ABSENT",
    "Stage61MapLifecycleError",
    "SYSTEM_FLAGS_CLEARED_ON_DESTINATION_LOAD",
    "apply_destination_engine_clear",
    "clear_destination_temp_vars",
    "decode_map_lifecycle_topology",
    "lifecycle_attempts",
    "map_header_address",
    "resolve_attempt",
    "resolve_attempt_result",
    "select_first_condition",
]
