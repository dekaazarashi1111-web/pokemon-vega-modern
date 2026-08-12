#!/usr/bin/env python3
"""Deterministic, ROM-rooted Vega inventory used by the T02 exact audit.

The scanner deliberately has no byte-pattern search.  Every ROM read descends
from a documented pointer/table root and every event-script edge descends from
a map event or a map-script table.  This makes the result reproducible and,
more importantly, prevents text/graphics/party data from being mistaken for
event bytecode.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
import sys
from collections import defaultdict, deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


ROM_BASE = 0x08000000
MAP_GROUPS_POINTER_SITE = 0x08054B0C
SPECIES_NAMES_POINTER_SITE = 0x08000144
MOVE_NAMES_POINTER_SITE = 0x08000148
ITEM_TABLE_POINTER_SITE = 0x080001C8
MOVE_DATA_POINTER_SITE = 0x080001CC

MAP_HEADER_SIZE = 0x1C
MAP_LAYOUT_SIZE = 0x1C
MAP_EVENTS_SIZE = 0x14
OBJECT_EVENT_SIZE = 0x18
WARP_EVENT_SIZE = 0x08
COORD_EVENT_SIZE = 0x10
BG_EVENT_SIZE = 0x0C
MAP_CONNECTION_SIZE = 0x0C
WILD_HEADER_SIZE = 0x14
WILD_INFO_SIZE = 0x08
WILD_SLOT_SIZE = 0x04
TRAINER_RECORD_SIZE = 0x20
TRAINER_MONEY_POINTER_SITE = 0x080251B8
HIDDEN_ITEM_FLAG_START = 0x03E8
MAP_DYNAMIC = (0x7F, 0x7F)
MAP_UNDEFINED = (0xFF, 0xFF)
VARS_START = 0x4000
VARS_END = 0x40FF
SPECIAL_VARS_START = 0x8000
SPECIAL_VARS_END = 0x8014


class InventoryError(ValueError):
    """An input violates a fixed ABI, pointer, or provenance invariant."""


def _hex(value: int) -> str:
    return f"0x{value:08X}"


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _parse_int(value: Any, name: str) -> int:
    if isinstance(value, bool):
        raise InventoryError(f"{name} must be an integer, not bool")
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value, 0)
        except ValueError as exc:
            raise InventoryError(f"{name} is not an integer: {value!r}") from exc
    raise InventoryError(f"{name} is not an integer: {value!r}")


def _policy_get(mapping: Mapping[str, Any], path: Sequence[str]) -> Any:
    value: Any = mapping
    for key in path:
        if not isinstance(value, Mapping) or key not in value:
            raise InventoryError(f"policy is missing {'.'.join(path)}")
        value = value[key]
    return value


def validate_map_id(group: int, map_num: int, *, allow_dynamic: bool = False) -> str:
    """Validate the signed-byte map ABI and classify reserved pairs.

    Physical/imported map IDs must be below 0x7F.  The exact 0x7F/0x7F pair is
    accepted only by callers which explicitly handle MAP_DYNAMIC.  0xFF/0xFF
    is the separate MAP_UNDEFINED sentinel and is never a physical map ID.
    """

    if not 0 <= group <= 0xFF or not 0 <= map_num <= 0xFF:
        raise InventoryError(f"map id out of byte range: ({group}, {map_num})")
    if (group, map_num) == MAP_DYNAMIC:
        if allow_dynamic:
            return "MAP_DYNAMIC"
        raise InventoryError("MAP_DYNAMIC (0x7F/0x7F) is not a physical map id")
    if (group, map_num) == MAP_UNDEFINED:
        raise InventoryError("MAP_UNDEFINED (0xFF/0xFF) is not a physical map id")
    if group >= 0x7F or map_num >= 0x7F:
        raise InventoryError(
            f"map id aliases signed/reserved space: ({group:#04x}, {map_num:#04x})"
        )
    return "PHYSICAL"


def classify_map_reference(group: int, map_num: int) -> str:
    if (group, map_num) == MAP_DYNAMIC:
        return "MAP_DYNAMIC"
    if (group, map_num) == MAP_UNDEFINED:
        return "MAP_UNDEFINED"
    try:
        return validate_map_id(group, map_num)
    except InventoryError:
        return "INVALID_RESERVED"


def is_script_var(value: int) -> bool:
    """Match the ranges for which FireRed's VarGet dereferences an ID."""

    return VARS_START <= value <= VARS_END or SPECIAL_VARS_START <= value <= SPECIAL_VARS_END


@dataclass(frozen=True)
class RomImage:
    label: str
    data: bytes
    logical_path: str = ""

    @classmethod
    def from_path(
        cls, label: str, path: Path, expected: Mapping[str, Any] | None = None
    ) -> "RomImage":
        try:
            data = path.read_bytes()
        except OSError as exc:
            raise InventoryError(f"cannot read {label} ROM: {path}") from exc
        if expected:
            if "size" in expected and len(data) != _parse_int(expected["size"], f"{label}.size"):
                raise InventoryError(
                    f"{label} ROM size mismatch: {len(data)} != {expected['size']}"
                )
            digest = _sha256(data)
            if "sha256" in expected and digest.lower() != str(expected["sha256"]).lower():
                raise InventoryError(f"{label} ROM sha256 mismatch: {digest}")
        return cls(label=label, data=data, logical_path=str(expected.get("path", "")) if expected else "")

    @property
    def end(self) -> int:
        return ROM_BASE + len(self.data)

    @property
    def sha256(self) -> str:
        return _sha256(self.data)

    def contains(self, address: int, size: int = 1, alignment: int = 1) -> bool:
        if size < 0 or alignment <= 0:
            return False
        return (
            address >= ROM_BASE
            and address + size <= self.end
            and address % alignment == 0
        )

    def require(self, address: int, size: int = 1, *, alignment: int = 1, what: str = "read") -> int:
        if not self.contains(address, size, alignment):
            raise InventoryError(
                f"{self.label}: invalid {what} {_hex(address)}+{size} "
                f"(ROM {_hex(ROM_BASE)}..{_hex(self.end)}, alignment {alignment})"
            )
        return address - ROM_BASE

    def raw(self, address: int, size: int, *, alignment: int = 1, what: str = "read") -> bytes:
        offset = self.require(address, size, alignment=alignment, what=what)
        return self.data[offset : offset + size]

    def u8(self, address: int, *, what: str = "u8") -> int:
        return self.raw(address, 1, what=what)[0]

    def u16(self, address: int, *, what: str = "u16") -> int:
        return struct.unpack("<H", self.raw(address, 2, what=what))[0]

    def s16(self, address: int, *, what: str = "s16") -> int:
        return struct.unpack("<h", self.raw(address, 2, what=what))[0]

    def u32(self, address: int, *, what: str = "u32") -> int:
        return struct.unpack("<I", self.raw(address, 4, what=what))[0]

    def s32(self, address: int, *, what: str = "s32") -> int:
        return struct.unpack("<i", self.raw(address, 4, what=what))[0]

    def require_pointer(
        self,
        value: int,
        *,
        size: int = 1,
        alignment: int = 1,
        nullable: bool = False,
        what: str = "pointer",
    ) -> int:
        if value == 0 and nullable:
            return value
        self.require(value, size, alignment=alignment, what=what)
        return value


@dataclass(frozen=True)
class ScriptRoot:
    address: int
    label: str
    kind: str


# Total command sizes, including the opcode.  This is the FireRed event ABI
# from asm/macros/event.inc.  0x5C (trainerbattle) is variable and handled
# separately.  Unknown commands terminate that rooted path rather than causing
# speculative resynchronisation.
_COMMAND_LENGTHS_LIST = [
    1, 1, 1, 1, 5, 5, 6, 6, 2, 2, 3, 3, 1, 1, 2, 6,
    3, 6, 6, 6, 3, 9, 5, 5, 5, 5, 5, 3, 3, 6, 6, 6,
    9, 5, 5, 5, 5, 3, 5, 1, 3, 3, 3, 3, 5, 1, 1, 3,
    1, 3, 1, 4, 3, 1, 3, 2, 2, 9, 9, 9, 3, 9, 9, 9,
    9, 9, 5, 1, 5, 5, 5, 5, 3, 5, 5, 3, 3, 3, 3, 7,
    9, 3, 5, 3, 5, 3, 5, 7, 5, 5, 1, 4, 0, 1, 1, 1,
    3, 3, 3, 7, 3, 4, 1, 5, 1, 1, 1, 1, 1, 1, 3, 5,
    6, 6, 1, 5, 5, 6, 1, 2, 5, 15, 3, 5, 3, 4, 2, 4,
    4, 4, 4, 4, 4, 6, 5, 5, 5, 3, 4, 1, 1, 1, 1, 3,
    6, 6, 6, 4, 3, 4, 3, 2, 3, 3, 2, 5, 3, 4, 3, 3,
    1, 5, 9, 1, 3, 1, 2, 3, 6, 5, 9, 3, 5, 5, 1, 5,
    5, 8, 1, 3, 3, 3, 6, 1, 5, 5, 5, 6, 6, 5, 5, 6,
    3, 3, 3, 2, 9, 1, 4, 2, 5, 1, 1, 1, 6, 3, 3, 1,
    3, 9, 4, 5, 6,
]
COMMAND_LENGTHS = {opcode: length for opcode, length in enumerate(_COMMAND_LENGTHS_LIST)}

_COMMAND_NAMES = {
    0x02: "end",
    0x03: "return",
    0x04: "call",
    0x05: "goto",
    0x06: "goto_if",
    0x07: "call_if",
    0x16: "setvar",
    0x17: "addvar",
    0x18: "subvar",
    0x19: "copyvar",
    0x1A: "setorcopyvar",
    0x21: "compare_var_to_value",
    0x22: "compare_var_to_var",
    0x25: "special",
    0x26: "specialvar",
    0x29: "setflag",
    0x2A: "clearflag",
    0x2B: "checkflag",
    0x39: "warp",
    0x3A: "warpsilent",
    0x3B: "warpdoor",
    0x3C: "warphole",
    0x3D: "warpteleport",
    0x3E: "setwarp",
    0x3F: "setdynamicwarp",
    0x40: "setdivewarp",
    0x41: "setholewarp",
    0x44: "additem",
    0x45: "removeitem",
    0x46: "checkitemspace",
    0x47: "checkitem",
    0x48: "checkitemtype",
    0x49: "addpcitem",
    0x4A: "checkpcitem",
    0x5C: "trainerbattle",
    0x60: "checktrainerflag",
    0x61: "settrainerflag",
    0x62: "cleartrainerflag",
    0x75: "showmonpic",
    0x79: "givemon",
    0x7A: "giveegg",
    0x7B: "setmonmove",
    0x7C: "checkpartymove",
    0x7D: "bufferspeciesname",
    0x80: "bufferitemname",
    0x82: "buffermovename",
    0x9F: "setrespawn",
    0xA1: "playmoncry",
    0xB6: "setwildbattle",
    0xC4: "setescapewarp",
    0xD0: "setworldmapflag",
    0xD1: "warpspinenter",
    0xD4: "bufferitemnameplural",
}


def _trainerbattle_size(kind: int) -> int:
    sizes = {0: 14, 1: 18, 2: 18, 3: 10, 4: 18, 5: 14, 6: 22, 7: 18, 8: 22, 9: 14}
    if kind not in sizes:
        raise InventoryError(f"unknown trainerbattle type {kind}")
    return sizes[kind]


class ScriptWalker:
    """Decode the graph reachable from explicit event-script roots."""

    MAX_INSTRUCTIONS_PER_NODE = 4096

    def __init__(self, rom: RomImage):
        self.rom = rom
        self.roots: list[ScriptRoot] = []
        self.nodes: dict[int, dict[str, Any]] = {}
        self.diagnostics: list[dict[str, Any]] = []

    def add_root(self, root: ScriptRoot) -> None:
        self.rom.require_pointer(root.address, what=f"script root {root.label}")
        self.roots.append(root)

    def _reference(self, category: str, value: Any, access: str, at: int, opcode: int, **extra: Any) -> dict[str, Any]:
        result = {
            "category": category,
            "value": value,
            "access": access,
            "instruction_address": at,
            "opcode": opcode,
            "command": _COMMAND_NAMES.get(opcode, f"opcode_{opcode:02X}"),
        }
        result.update(extra)
        return result

    def _decode_refs(self, address: int, opcode: int, size: int) -> tuple[list[dict[str, Any]], list[int]]:
        r = self.rom
        refs: list[dict[str, Any]] = []
        edges: list[int] = []
        u16 = lambda off: r.u16(address + off, what="script operand")
        u32 = lambda off: r.u32(address + off, what="script operand")

        def var_get_reference(category: str, value: int, access: str) -> dict[str, Any]:
            # Commands backed by VarGet accept either a literal semantic ID or
            # a variable holding that ID.  Never count a VAR_* operand as an
            # item/species/move/heal ID; preserve its semantic use instead.
            if is_script_var(value):
                return self._reference(
                    "var",
                    value,
                    f"read_as_{category}",
                    address,
                    opcode,
                    semantic_category=category,
                )
            return self._reference(category, value, access, address, opcode)

        def optional_var_get_reference(category: str, value: int) -> None:
            if is_script_var(value):
                refs.append(var_get_reference(category, value, "read"))

        if opcode in (0x04, 0x05):
            edges.append(u32(1))
        elif opcode in (0x06, 0x07):
            edges.append(u32(2))
        elif opcode in (0x16, 0x17, 0x18):
            refs.append(self._reference("var", u16(1), "write", address, opcode, operand=u16(3)))
        elif opcode in (0x19, 0x1A):
            refs.append(self._reference("var", u16(1), "write", address, opcode, operand=u16(3)))
            if 0x4000 <= u16(3) <= 0x800F:
                refs.append(self._reference("var", u16(3), "read", address, opcode))
        elif opcode == 0x21:
            refs.append(self._reference("var", u16(1), "read", address, opcode, operand=u16(3)))
        elif opcode == 0x22:
            refs.extend(
                [
                    self._reference("var", u16(1), "read", address, opcode),
                    self._reference("var", u16(3), "read", address, opcode),
                ]
            )
        elif opcode == 0x25:
            refs.append(self._reference("special", u16(1), "call", address, opcode))
        elif opcode == 0x26:
            refs.append(self._reference("var", u16(1), "write", address, opcode))
            refs.append(self._reference("special", u16(3), "call", address, opcode))
        elif opcode in (0x29, 0x2A, 0x2B):
            access = {0x29: "set", 0x2A: "clear", 0x2B: "read"}[opcode]
            refs.append(self._reference("flag", u16(1), access, address, opcode))
        elif opcode in (0x39, 0x3A, 0x3B, 0x3D, 0x3E, 0x3F, 0x40, 0x41, 0xC4, 0xD1):
            group, map_num = r.u8(address + 1), r.u8(address + 2)
            refs.append(
                self._reference(
                    "map",
                    [group, map_num],
                    "warp",
                    address,
                    opcode,
                    map_id_class=classify_map_reference(group, map_num),
                )
            )
        elif opcode == 0x3C:
            group, map_num = r.u8(address + 1), r.u8(address + 2)
            refs.append(self._reference("map", [group, map_num], "warp", address, opcode, map_id_class=classify_map_reference(group, map_num)))
        elif opcode in (0x44, 0x45, 0x46, 0x47, 0x48, 0x49, 0x4A):
            refs.append(var_get_reference("item", u16(1), "use"))
            if opcode != 0x48:
                optional_var_get_reference("quantity", u16(3))
        elif opcode in (0x60, 0x61, 0x62):
            refs.append(self._reference("trainer", u16(1), "flag", address, opcode))
        elif opcode == 0x75:
            refs.append(var_get_reference("species", u16(1), "display"))
        elif opcode == 0x79:
            refs.append(var_get_reference("species", u16(1), "give"))
            refs.append(var_get_reference("item", u16(4), "held"))
        elif opcode == 0x7A:
            refs.append(var_get_reference("species", u16(1), "give_egg"))
        elif opcode == 0x7B:
            refs.append(self._reference("move", u16(3), "set", address, opcode))
        elif opcode == 0x7C:
            refs.append(self._reference("move", u16(1), "check", address, opcode))
        elif opcode == 0x7D:
            refs.append(var_get_reference("species", u16(2), "display"))
        elif opcode == 0x80:
            refs.append(var_get_reference("item", u16(2), "display"))
        elif opcode == 0x82:
            refs.append(var_get_reference("move", u16(2), "display"))
        elif opcode == 0x9F:
            refs.append(var_get_reference("heal_location", u16(1), "set_respawn"))
        elif opcode == 0xA1:
            refs.append(var_get_reference("species", u16(1), "cry"))
            optional_var_get_reference("cry_mode", u16(3))
        elif opcode == 0xB6:
            refs.append(self._reference("species", u16(1), "battle", address, opcode))
            refs.append(self._reference("item", u16(4), "held", address, opcode))
        elif opcode == 0xD4:
            refs.append(var_get_reference("item", u16(2), "display"))
            optional_var_get_reference("quantity", u16(4))
        elif opcode == 0xD0:
            refs.append(self._reference("fly_flag", u16(1), "set_world_map", address, opcode))

        if opcode == 0x5C:
            kind = r.u8(address + 1, what="trainerbattle type")
            trainer = u16(2)
            refs.append(self._reference("trainer", trainer, "battle", address, opcode, battle_type=kind))
            continuation_offset = {1: 14, 2: 14, 6: 18, 8: 18}.get(kind)
            if continuation_offset is not None:
                edges.append(u32(continuation_offset))
        return refs, edges

    def _decode_node(self, start: int) -> dict[str, Any]:
        self.rom.require_pointer(start, what="event bytecode")
        pc = start
        instructions: list[dict[str, Any]] = []
        references: list[dict[str, Any]] = []
        edges: list[int] = []
        reason = "terminal"
        for _ in range(self.MAX_INSTRUCTIONS_PER_NODE):
            try:
                opcode = self.rom.u8(pc, what="event opcode")
                if opcode == 0x5C:
                    size = _trainerbattle_size(self.rom.u8(pc + 1, what="trainerbattle type"))
                else:
                    size = COMMAND_LENGTHS.get(opcode, 0)
                    if size <= 0:
                        reason = "unknown_opcode"
                        self.diagnostics.append({"address": pc, "kind": reason, "opcode": opcode})
                        break
                self.rom.require(pc, size, what="event instruction")
                local_refs, local_edges = self._decode_refs(pc, opcode, size)
            except InventoryError as exc:
                reason = "invalid_instruction"
                self.diagnostics.append({"address": pc, "kind": reason, "detail": str(exc)})
                break
            instructions.append({"address": pc, "opcode": opcode, "size": size})
            references.extend(local_refs)
            for target in local_edges:
                if self.rom.contains(target):
                    edges.append(target)
                else:
                    self.diagnostics.append(
                        {"address": pc, "kind": "invalid_script_edge", "target": target}
                    )
            next_pc = pc + size
            if opcode in (0x02, 0x03, 0x05, 0x0C, 0x0D, 0x24, 0x5E, 0x5F, 0xB9):
                reason = _COMMAND_NAMES.get(opcode, f"opcode_{opcode:02X}")
                break
            pc = next_pc
        else:
            reason = "instruction_limit"
            self.diagnostics.append({"address": start, "kind": reason})
        return {
            "address": start,
            "end_reason": reason,
            "instruction_count": len(instructions),
            "edges": sorted(set(edges)),
            "references": references,
        }

    def walk(self) -> dict[str, Any]:
        pending = deque(sorted({root.address for root in self.roots}))
        while pending:
            address = pending.popleft()
            if address in self.nodes:
                continue
            node = self._decode_node(address)
            self.nodes[address] = node
            for target in node["edges"]:
                if target not in self.nodes:
                    pending.append(target)

        roots_by_node: dict[int, set[str]] = defaultdict(set)
        for root in sorted(self.roots, key=lambda item: (item.label, item.address, item.kind)):
            queue = deque([root.address])
            seen: set[int] = set()
            while queue:
                address = queue.popleft()
                if address in seen or address not in self.nodes:
                    continue
                seen.add(address)
                roots_by_node[address].add(root.label)
                queue.extend(self.nodes[address]["edges"])

        references: list[dict[str, Any]] = []
        nodes: list[dict[str, Any]] = []
        for address in sorted(self.nodes):
            node = self.nodes[address]
            roots = sorted(roots_by_node[address])
            nodes.append(
                {
                    "address": address,
                    "end_reason": node["end_reason"],
                    "instruction_count": node["instruction_count"],
                    "edges": node["edges"],
                    "roots": roots,
                }
            )
            for reference in node["references"]:
                references.append({**reference, "script_address": address, "roots": roots})
        references.sort(
            key=lambda item: (
                item["category"],
                json.dumps(item["value"], sort_keys=True),
                item["instruction_address"],
                item["access"],
            )
        )
        return {
            "root_count": len(self.roots),
            "unique_root_address_count": len({root.address for root in self.roots}),
            "visited_script_count": len(nodes),
            "nodes": nodes,
            "references": references,
            "diagnostics": sorted(self.diagnostics, key=lambda item: (item.get("address", 0), item["kind"])),
        }


def _decode_map_scripts(
    rom: RomImage,
    address: int,
    map_label: str,
) -> tuple[list[ScriptRoot], list[dict[str, Any]], list[dict[str, Any]]]:
    roots: list[ScriptRoot] = []
    refs: list[dict[str, Any]] = []
    rows: list[dict[str, Any]] = []
    if address == 0:
        return roots, refs, rows
    rom.require_pointer(address, what=f"{map_label} map-script table")
    cursor = address
    for table_index in range(64):
        script_type = rom.u8(cursor, what="map-script type")
        if script_type == 0:
            break
        if script_type not in range(1, 8):
            # A rooted pointer can still denote an unused/legacy blob.  Stop at
            # its first impossible table tag; never resynchronise through data.
            rows.append(
                {
                    "table_address": cursor,
                    "status": "INVALID_ROOTED_TABLE_TAG",
                    "invalid_type": script_type,
                }
            )
            break
        target = rom.u32(cursor + 1, what="map-script pointer")
        rom.require_pointer(target, what=f"{map_label} map-script target")
        row: dict[str, Any] = {"type": script_type, "pointer": target, "table_address": cursor}
        if script_type in (2, 4):
            conditions: list[dict[str, Any]] = []
            condition_cursor = target
            for condition_index in range(256):
                lhs = rom.u16(condition_cursor, what="map-script condition lhs")
                if lhs == 0:
                    break
                rhs = rom.u16(condition_cursor + 2, what="map-script condition rhs")
                script = rom.u32(condition_cursor + 4, what="map-script condition pointer")
                rom.require_pointer(script, what=f"{map_label} conditional map script")
                condition = {
                    "index": condition_index,
                    "lhs_var": lhs,
                    "rhs_var_or_value": rhs,
                    "script_address": script,
                }
                conditions.append(condition)
                refs.append(
                    {
                        "category": "var",
                        "value": lhs,
                        "access": "map_script_condition",
                        "instruction_address": condition_cursor,
                        "opcode": -1,
                        "command": "map_script_condition",
                        "script_address": script,
                        "roots": [map_label],
                        "operand": rhs,
                    }
                )
                if 0x4000 <= rhs <= 0x800F:
                    refs.append(
                        {
                            "category": "var",
                            "value": rhs,
                            "access": "map_script_condition_rhs",
                            "instruction_address": condition_cursor + 2,
                            "opcode": -1,
                            "command": "map_script_condition",
                            "script_address": script,
                            "roots": [map_label],
                        }
                    )
                roots.append(ScriptRoot(script, f"{map_label}:map_script:{script_type}:{condition_index}", "map_script_condition"))
                condition_cursor += 8
            else:
                raise InventoryError(f"{map_label}: unterminated conditional map-script table")
            row["conditions"] = conditions
        else:
            roots.append(ScriptRoot(target, f"{map_label}:map_script:{script_type}:{table_index}", "map_script"))
        rows.append(row)
        cursor += 5
    else:
        raise InventoryError(f"{map_label}: unterminated map-script table")
    return roots, refs, rows


def _scan_maps(rom: RomImage, policy: Mapping[str, Any]) -> tuple[dict[str, Any], list[ScriptRoot], list[dict[str, Any]]]:
    groups_address = _parse_int(_policy_get(policy, ("maps", "groups_table_address")), "maps.groups_table_address")
    group_count = _parse_int(_policy_get(policy, ("maps", "expected_group_count")), "maps.expected_group_count")
    expected_maps = _parse_int(_policy_get(policy, ("maps", "expected_physical_map_count")), "maps.expected_physical_map_count")
    max_maps = _parse_int(_policy_get(policy, ("maps", "maximum_maps_per_group")), "maps.maximum_maps_per_group")
    rooted_address = rom.u32(MAP_GROUPS_POINTER_SITE, what="gMapGroups pointer site")
    if rooted_address != groups_address:
        raise InventoryError(
            f"gMapGroups root mismatch: pointer site has {_hex(rooted_address)}, policy has {_hex(groups_address)}"
        )
    rom.require_pointer(groups_address, size=group_count * 4, alignment=4, what="gMapGroups")
    group_ptrs = [rom.u32(groups_address + i * 4, what="map-group pointer") for i in range(group_count)]
    for i, pointer in enumerate(group_ptrs):
        rom.require_pointer(pointer, size=4, alignment=4, what=f"map group {i}")
    group_sizes: list[int] = []
    for i, pointer in enumerate(group_ptrs):
        end = group_ptrs[i + 1] if i + 1 < group_count else groups_address
        delta = end - pointer
        if delta <= 0 or delta % 4:
            raise InventoryError(f"map group {i} is not a contiguous pointer array")
        count = delta // 4
        if count > max_maps:
            raise InventoryError(f"map group {i} count {count} exceeds signed-ID limit {max_maps}")
        group_sizes.append(count)
    if sum(group_sizes) != expected_maps:
        raise InventoryError(f"physical map count {sum(group_sizes)} != {expected_maps}")

    rows: list[dict[str, Any]] = []
    details: list[dict[str, Any]] = []
    roots: list[ScriptRoot] = []
    structural_refs: list[dict[str, Any]] = []
    for group, count in enumerate(group_sizes):
        for map_num in range(count):
            validate_map_id(group, map_num)
            label = f"map:{group}:{map_num}"
            header = rom.u32(group_ptrs[group] + map_num * 4, what=f"{label} header pointer")
            rom.require_pointer(header, size=MAP_HEADER_SIZE, alignment=4, what=f"{label} header")
            layout = rom.u32(header, what=f"{label} layout")
            events = rom.u32(header + 4, what=f"{label} events")
            map_scripts = rom.u32(header + 8, what=f"{label} scripts")
            connections = rom.u32(header + 12, what=f"{label} connections")
            rom.require_pointer(layout, size=MAP_LAYOUT_SIZE, alignment=4, what=f"{label} layout")
            rom.require_pointer(events, size=MAP_EVENTS_SIZE, alignment=4, nullable=True, what=f"{label} events")
            rom.require_pointer(map_scripts, nullable=True, what=f"{label} scripts")
            rom.require_pointer(connections, size=8, alignment=4, nullable=True, what=f"{label} connections")

            width, height = rom.s32(layout), rom.s32(layout + 4)
            if not 0 < width <= 1024 or not 0 < height <= 1024:
                raise InventoryError(f"{label}: implausible layout {width}x{height}")
            for offset, name in ((8, "border"), (12, "map"), (16, "primary tileset"), (20, "secondary tileset")):
                rom.require_pointer(rom.u32(layout + offset), alignment=4 if offset >= 16 else 2, what=f"{label} {name}")

            counts = [0, 0, 0, 0]
            event_ptrs = [0, 0, 0, 0]
            objects: list[dict[str, Any]] = []
            warps: list[dict[str, Any]] = []
            coords: list[dict[str, Any]] = []
            bgs: list[dict[str, Any]] = []
            events_sentinel = bool(events and rom.raw(events, 4, what=f"{label} event counts") == b"\xFF" * 4)
            # Vega retains a few physical map headers whose event pointer lands
            # on an erased 0xFF record.  It is a rooted, explicit empty sentinel,
            # not four 255-entry arrays.
            if events and not events_sentinel:
                counts = list(rom.raw(events, 4, what=f"{label} event counts"))
                event_ptrs = [rom.u32(events + 4 + index * 4, what=f"{label} event list") for index in range(4)]
                sizes = [OBJECT_EVENT_SIZE, WARP_EVENT_SIZE, COORD_EVENT_SIZE, BG_EVENT_SIZE]
                for index, (amount, pointer, stride) in enumerate(zip(counts, event_ptrs, sizes)):
                    if amount:
                        rom.require_pointer(pointer, size=amount * stride, alignment=4, what=f"{label} event list {index}")
                    elif pointer:
                        rom.require_pointer(pointer, alignment=4, what=f"{label} empty event list {index}")
                for index in range(counts[0]):
                    at = event_ptrs[0] + index * OBJECT_EVENT_SIZE
                    script = rom.u32(at + 0x10, what="object script")
                    if script:
                        rom.require_pointer(script, what=f"{label} object {index} script")
                        roots.append(ScriptRoot(script, f"{label}:object:{index}", "object"))
                    flag = rom.u16(at + 0x14, what="object flag")
                    obj = {
                        "index": index,
                        "local_id": rom.u8(at),
                        "graphics_id": rom.u8(at + 1),
                        "kind": rom.u8(at + 2),
                        "x": rom.s16(at + 4),
                        "y": rom.s16(at + 6),
                        "script_address": script,
                        "flag": flag,
                    }
                    objects.append(obj)
                    if flag:
                        structural_refs.append({"category": "flag", "value": flag, "access": "object_visibility", "address": at + 0x14, "roots": [f"{label}:object:{index}"]})
                for index in range(counts[1]):
                    at = event_ptrs[1] + index * WARP_EVENT_SIZE
                    dest_group, dest_map = rom.u8(at + 7), rom.u8(at + 6)
                    warp = {
                        "index": index,
                        "x": rom.s16(at),
                        "y": rom.s16(at + 2),
                        "elevation": rom.u8(at + 4),
                        "warp_id": rom.u8(at + 5),
                        "destination_group": dest_group,
                        "destination_map": dest_map,
                        "destination_class": classify_map_reference(dest_group, dest_map),
                    }
                    warps.append(warp)
                    structural_refs.append({"category": "map", "value": [dest_group, dest_map], "access": "warp_event", "address": at, "roots": [label], "map_id_class": warp["destination_class"]})
                for index in range(counts[2]):
                    at = event_ptrs[2] + index * COORD_EVENT_SIZE
                    script = rom.u32(at + 0x0C, what="coord script")
                    if script:
                        rom.require_pointer(script, what=f"{label} coord {index} script")
                        roots.append(ScriptRoot(script, f"{label}:coord:{index}", "coord"))
                    trigger = rom.u16(at + 6)
                    coord = {"index": index, "x": rom.u16(at), "y": rom.u16(at + 2), "elevation": rom.u8(at + 4), "trigger_var": trigger, "trigger_value": rom.u16(at + 8), "script_address": script}
                    coords.append(coord)
                    if trigger:
                        structural_refs.append({"category": "var", "value": trigger, "access": "coord_trigger", "address": at + 6, "roots": [f"{label}:coord:{index}"]})
                for index in range(counts[3]):
                    at = event_ptrs[3] + index * BG_EVENT_SIZE
                    kind = rom.u8(at + 5)
                    raw = rom.u32(at + 8, what="bg event union")
                    bg: dict[str, Any] = {"index": index, "x": rom.u16(at), "y": rom.u16(at + 2), "elevation": rom.u8(at + 4), "kind": kind}
                    if kind == 7:
                        item = raw & 0xFFFF
                        flag_index = (raw >> 16) & 0xFF
                        flag = HIDDEN_ITEM_FLAG_START + flag_index
                        bg.update({"item": item, "hidden_item_flag_index": flag_index, "hidden_item_flag": flag, "quantity": (raw >> 24) & 0x7F, "underfoot": (raw >> 31) & 1})
                        structural_refs.extend([
                            {"category": "item", "value": item, "access": "hidden_item", "address": at + 8, "roots": [f"{label}:bg:{index}"]},
                            {"category": "flag", "value": flag, "access": "hidden_item", "address": at + 10, "roots": [f"{label}:bg:{index}"]},
                        ])
                    elif kind == 8:
                        # BG_EVENT_SECRET_BASE stores an integer in the union,
                        # not an event-script pointer.
                        bg["secret_base_id"] = raw
                    else:
                        rom.require_pointer(raw, nullable=True, what=f"{label} bg {index} script")
                        bg["script_address"] = raw
                        if raw:
                            roots.append(ScriptRoot(raw, f"{label}:bg:{index}", "bg"))
                    bgs.append(bg)

            connection_rows: list[dict[str, Any]] = []
            if connections:
                connection_count = rom.s32(connections, what="map connection count")
                if not 0 <= connection_count <= 64:
                    raise InventoryError(f"{label}: invalid connection count {connection_count}")
                connection_data = rom.u32(connections + 4, what="map connections pointer")
                if connection_count:
                    rom.require_pointer(connection_data, size=connection_count * MAP_CONNECTION_SIZE, alignment=4, what=f"{label} connections")
                for index in range(connection_count):
                    at = connection_data + index * MAP_CONNECTION_SIZE
                    dest_group, dest_map = rom.u8(at + 8), rom.u8(at + 9)
                    connection_rows.append({"index": index, "direction": rom.u8(at), "offset": rom.s32(at + 4), "destination_group": dest_group, "destination_map": dest_map, "destination_class": classify_map_reference(dest_group, dest_map)})
                    structural_refs.append({"category": "map", "value": [dest_group, dest_map], "access": "connection", "address": at, "roots": [label], "map_id_class": classify_map_reference(dest_group, dest_map)})

            script_roots, map_script_refs, map_script_rows = _decode_map_scripts(rom, map_scripts, label)
            roots.extend(script_roots)
            structural_refs.extend(map_script_refs)
            header_flags = rom.u8(header + 0x19)
            map_type = rom.u8(header + 0x17)
            row = {
                "group": group,
                "map": map_num,
                "header_address": header,
                "layout_id": rom.u16(header + 0x12),
                "map_section": rom.u8(header + 0x14),
                "music": rom.u16(header + 0x10),
                "events_address": events,
                "object_count": counts[0],
                "warp_count": counts[1],
                "coord_count": counts[2],
                "bg_count": counts[3],
                "map_scripts_address": map_scripts,
                "classification": "VEGA",
                "evidence": f"gMapGroups[{group}][{map_num}] at {_hex(group_ptrs[group] + map_num * 4)}",
            }
            rows.append(row)
            details.append({"group": group, "map": map_num, "layout_address": layout, "layout_width": width, "layout_height": height, "connections_address": connections, "events_erased_sentinel": events_sentinel, "map_type": map_type, "allow_escape": bool(header_flags & 1), "allow_running": bool(header_flags & 2), "objects": objects, "warps": warps, "coord_events": coords, "bg_events": bgs, "connections": connection_rows, "map_scripts": map_script_rows})

    early_policy = _policy_get(policy, ("maps", "early_port"))
    early_group = _parse_int(early_policy["group"], "early_port.group")
    early_map = _parse_int(early_policy["map"], "early_port.map")
    port_row = next(row for row in rows if row["group"] == early_group and row["map"] == early_map)
    port_detail = next(row for row in details if row["group"] == early_group and row["map"] == early_map)
    expected_header = _parse_int(early_policy["header_address"], "early_port.header_address")
    if port_row["header_address"] != expected_header or port_row["map_section"] != _parse_int(early_policy["map_section"], "early_port.map_section"):
        raise InventoryError("Aeshia early-port map identity does not match policy")
    expected_objects = _parse_int(early_policy["object_count"], "early_port.object_count")
    runtime_limit = _parse_int(early_policy["runtime_object_limit_including_player"], "early_port.runtime_object_limit")
    if port_row["object_count"] != expected_objects:
        raise InventoryError("Aeshia object count does not match policy")
    local_ids = [row["local_id"] for row in port_detail["objects"]]
    if len(local_ids) != len(set(local_ids)):
        raise InventoryError("Aeshia has duplicate object local IDs")
    expected_warp = early_policy["dh_entry_warp"]
    entry_index = _parse_int(expected_warp["index"], "dh_entry_warp.index")
    entry = port_detail["warps"][entry_index]
    for field in ("x", "y", "destination_group", "destination_map"):
        if entry[field] != _parse_int(expected_warp[field], f"dh_entry_warp.{field}"):
            raise InventoryError(f"Aeshia D/H entry warp mismatch: {field}")
    forbidden = [_parse_int(value, "forbidden_dummy_warp_indices") for value in early_policy["forbidden_dummy_warp_indices"]]
    dummy_rows = [port_detail["warps"][index] for index in forbidden]
    if any((row["destination_group"], row["destination_map"]) != (0, 0) for row in dummy_rows):
        raise InventoryError("Aeshia reserved dummy warp was repurposed")
    early_port = {
        "group": early_group,
        "map": early_map,
        "object_local_ids": local_ids,
        "static_object_count": expected_objects,
        "runtime_object_count_including_player": expected_objects + 1,
        "runtime_object_limit": runtime_limit,
        "free_runtime_object_slots": runtime_limit - expected_objects - 1,
        "new_static_object_allowed": runtime_limit - expected_objects - 1 > 0,
        "dh_entry_warp": entry,
        "reserved_dummy_warps": dummy_rows,
        "evidence": port_row["evidence"],
    }
    if early_port["new_static_object_allowed"] != bool(early_policy["new_static_object_allowed"]):
        raise InventoryError("Aeshia static-object capacity differs from policy")
    escape_maps = [[row["group"], row["map"]] for row in details if row["allow_escape"]]
    fly_map_types = [1, 2, 3, 6]
    fly_maps = [[row["group"], row["map"]] for row in details if row["map_type"] in fly_map_types]
    hidden_items = [
        {"group": row["group"], "map": row["map"], **bg}
        for row in details
        for bg in row["bg_events"]
        if bg["kind"] == 7
    ]
    travel_state = {
        "map_id_abi": {
            "storage_type": "signed int8",
            "physical_min": 0,
            "physical_max": 126,
            "dynamic_sentinel": [0x7F, 0x7F],
            "undefined_sentinel": [0xFF, 0xFF],
            "group_or_map_at_least_127_for_physical": "REJECT",
        },
        "save_warp_abi": {
            "owner": "Vega SaveBlock1",
            "record_size": 8,
            "fields": {"map_group_s8": 0, "map_num_s8": 1, "warp_id_s8": 2, "x_s16": 4, "y_s16": 6},
            "records": {
                "location": {"saveblock1_offset": 0x04, "purpose": "current map"},
                "continue_game_warp": {"saveblock1_offset": 0x0C, "purpose": "continue/load"},
                "dynamic_warp": {"saveblock1_offset": 0x14, "purpose": "MAP_DYNAMIC destination"},
                "last_heal_location": {"saveblock1_offset": 0x1C, "purpose": "whiteout, teleport, Fly origin state"},
                "escape_warp": {"saveblock1_offset": 0x24, "purpose": "Escape Rope/Dig destination"},
            },
            "evidence": "pokefirered include/global.h: WarpData and SaveBlock1 offsets 0x04..0x24",
        },
        "escape": {
            "map_header_field": "MapHeader+0x19 bit0 allowEscaping",
            "allowed_map_count": len(escape_maps),
            "allowed_maps": escape_maps,
            "save_owner": "SaveBlock1+0x24 escapeWarp",
            "script_command": "0xC4 setescapewarp",
        },
        "fly_and_heal": {
            "fly_allowed_map_types": fly_map_types,
            "fly_allowed_map_count": len(fly_maps),
            "fly_allowed_maps": fly_maps,
            "heal_save_owner": "SaveBlock1+0x1C lastHealLocation",
            "heal_record_fields": ["map_group_s8", "map_num_s8", "x_s16", "y_s16"],
            "fly_unlock_command": "0xD0 setworldmapflag",
            "respawn_command": "0x9F setrespawn",
            "evidence": "pokefirered overworld.c Overworld_MapTypeAllowsTeleportAndFly and heal_location.c",
        },
        "hidden_items": {
            "raw_width_bits": 32,
            "item_id_bits": 16,
            "flag_index_bits": 8,
            "quantity_bits": 7,
            "underfoot_bits": 1,
            "flag_base": HIDDEN_ITEM_FLAG_START,
            "row_count": len(hidden_items),
            "rows": hidden_items,
            "evidence": "pokefirered include/global.fieldmap.h BgEvent hiddenItem bit layout",
        },
    }
    return ({"groups_table_address": groups_address, "group_count": group_count, "physical_map_count": len(rows), "group_sizes": group_sizes, "rows": rows, "details": details, "early_port": early_port, "travel_state": travel_state}, roots, structural_refs)


def _scan_encounters(rom: RomImage, policy: Mapping[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    pointer_site = _parse_int(_policy_get(policy, ("encounters", "headers_pointer_address")), "encounters.headers_pointer_address")
    expected_address = _parse_int(_policy_get(policy, ("encounters", "headers_address")), "encounters.headers_address")
    expected_count = _parse_int(_policy_get(policy, ("encounters", "expected_header_count")), "encounters.expected_header_count")
    term_group = _parse_int(_policy_get(policy, ("encounters", "terminator_group")), "encounters.terminator_group")
    term_map = _parse_int(_policy_get(policy, ("encounters", "terminator_map")), "encounters.terminator_map")
    address = rom.u32(pointer_site, what="gWildMonHeaders pointer")
    if address != expected_address:
        raise InventoryError(f"gWildMonHeaders root mismatch: {_hex(address)} != {_hex(expected_address)}")
    rows: list[dict[str, Any]] = []
    details: list[dict[str, Any]] = []
    species_refs: list[dict[str, Any]] = []
    slot_counts = (12, 5, 5, 10)
    names = ("land", "water", "rock", "fishing")
    for index in range(expected_count + 1):
        at = address + index * WILD_HEADER_SIZE
        rom.require(at, WILD_HEADER_SIZE, what="wild header")
        group, map_num = rom.u8(at), rom.u8(at + 1)
        if (group, map_num) == (term_group, term_map):
            if index != expected_count:
                raise InventoryError(f"wild terminator appeared at {index}, expected {expected_count}")
            terminator_address = at
            break
        if index >= expected_count:
            raise InventoryError("gWildMonHeaders has no expected terminator")
        validate_map_id(group, map_num)
        pointers = [rom.u32(at + 4 + slot * 4, what="wild info pointer") for slot in range(4)]
        row = {
            "group": group,
            "map": map_num,
            "header_address": at,
            "land_address": pointers[0],
            "water_address": pointers[1],
            "rock_address": pointers[2],
            "fishing_address": pointers[3],
            "classification": "VEGA",
            "evidence": f"gWildMonHeaders[{index}] rooted at {_hex(pointer_site)}",
        }
        habitat: dict[str, Any] = {"group": group, "map": map_num, "tables": {}}
        for name, pointer, count in zip(names, pointers, slot_counts):
            if pointer == 0:
                habitat["tables"][name] = None
                continue
            rom.require_pointer(pointer, size=WILD_INFO_SIZE, alignment=4, what=f"wild {name} info")
            slots_pointer = rom.u32(pointer + 4, what=f"wild {name} slots")
            rom.require_pointer(slots_pointer, size=count * WILD_SLOT_SIZE, alignment=4, what=f"wild {name} slots")
            slots: list[dict[str, Any]] = []
            for slot_index in range(count):
                slot_at = slots_pointer + slot_index * WILD_SLOT_SIZE
                slot = {"index": slot_index, "minimum_level": rom.u8(slot_at), "maximum_level": rom.u8(slot_at + 1), "species": rom.u16(slot_at + 2)}
                if slot["minimum_level"] > slot["maximum_level"]:
                    raise InventoryError(f"wild level range inverted at {_hex(slot_at)}")
                slots.append(slot)
                species_refs.append({"category": "species", "value": slot["species"], "access": "wild_encounter", "address": slot_at + 2, "roots": [f"wild:{group}:{map_num}:{name}"]})
            habitat["tables"][name] = {"info_address": pointer, "encounter_rate": rom.u8(pointer), "slots_address": slots_pointer, "slots": slots}
        rows.append(row)
        details.append(habitat)
    else:
        raise InventoryError("wild terminator scan exceeded fixed bound")
    if len(rows) != expected_count:
        raise InventoryError(f"wild header count {len(rows)} != {expected_count}")
    return ({"headers_pointer_address": pointer_site, "headers_address": address, "header_count": len(rows), "terminator_address": terminator_address, "terminator": [term_group, term_map], "rows": rows, "details": details}, species_refs)


def _decode_trainer_party(rom: RomImage, pointer: int, party_size: int, flags: int) -> list[dict[str, Any]]:
    if party_size == 0:
        return []
    if party_size > 6:
        raise InventoryError(f"trainer party size {party_size} exceeds six")
    form = flags & 3
    stride = 16 if form & 1 else 8
    rom.require_pointer(pointer, size=party_size * stride, alignment=4, what="trainer party")
    party: list[dict[str, Any]] = []
    for index in range(party_size):
        at = pointer + index * stride
        mon: dict[str, Any] = {"index": index, "iv": rom.u16(at), "level": rom.u16(at + 2), "species": rom.u16(at + 4), "held_item": 0, "moves": []}
        if form == 1:
            mon["moves"] = [rom.u16(at + 6 + move * 2) for move in range(4)]
        elif form == 2:
            mon["held_item"] = rom.u16(at + 6)
        elif form == 3:
            mon["held_item"] = rom.u16(at + 6)
            mon["moves"] = [rom.u16(at + 8 + move * 2) for move in range(4)]
        if mon["level"] == 0 or mon["species"] == 0:
            raise InventoryError(f"invalid trainer mon at {_hex(at)}")
        party.append(mon)
    return party


def _script_ref_map_ids(ref: Mapping[str, Any]) -> set[tuple[int, int]]:
    result: set[tuple[int, int]] = set()
    for root in ref.get("roots", []):
        match = re.match(r"map:(\d+):(\d+):", str(root))
        if match:
            result.add((int(match.group(1)), int(match.group(2))))
    return result


def _scan_trainers(
    rom: RomImage,
    policy: Mapping[str, Any],
    script_refs: Sequence[Mapping[str, Any]],
    map_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    trainer_policy = _policy_get(policy, ("ids", "vega_trainer_table"))
    address = _parse_int(trainer_policy["address"], "vega_trainer_table.address")
    count = _parse_int(trainer_policy["count"], "vega_trainer_table.count")
    record_size = _parse_int(trainer_policy["record_size"], "vega_trainer_table.record_size")
    end = _parse_int(trainer_policy["end_exclusive"], "vega_trainer_table.end_exclusive")
    if record_size != TRAINER_RECORD_SIZE or address + count * record_size != end:
        raise InventoryError("trainer table policy does not match Japanese 0x20-byte ABI")
    rom.require_pointer(address, size=count * record_size, alignment=4, what="gTrainers")
    money_table_address = rom.u32(TRAINER_MONEY_POINTER_SITE, what="gTrainerMoneyTable pointer")
    rom.require_pointer(money_table_address, size=4, alignment=4, what="gTrainerMoneyTable")
    money_rates: dict[int, int] = {}
    money_rows: list[dict[str, int]] = []
    for money_index in range(256):
        money_at = money_table_address + money_index * 4
        trainer_class = rom.u8(money_at, what="trainer money class")
        rate = rom.u8(money_at + 1, what="trainer money rate")
        if trainer_class == 0xFF:
            money_terminator_address = money_at
            break
        if trainer_class in money_rates:
            raise InventoryError(f"duplicate trainer-money class {trainer_class}")
        money_rates[trainer_class] = rate
        money_rows.append({"trainer_class": trainer_class, "rate": rate, "address": money_at})
    else:
        raise InventoryError("unterminated gTrainerMoneyTable")
    fallback_money_rate = money_rows[0]["rate"]
    refs_by_trainer: dict[int, list[Mapping[str, Any]]] = defaultdict(list)
    for ref in script_refs:
        if ref.get("category") == "trainer" and isinstance(ref.get("value"), int):
            refs_by_trainer[int(ref["value"])].append(ref)
    map_sections = {
        (int(row["group"]), int(row["map"])): int(row["map_section"])
        for row in map_rows
    }
    mirage_policy = _policy_get(policy, ("facilities", "mirage"))
    mirage_map = (
        _parse_int(mirage_policy["group"], "facilities.mirage.group"),
        _parse_int(mirage_policy["map"], "facilities.mirage.map"),
    )
    rows: list[dict[str, Any]] = []
    details: list[dict[str, Any]] = []
    all_species: set[int] = set()
    all_moves: set[int] = set()
    all_items: set[int] = set()
    for trainer_id in range(count):
        at = address + trainer_id * record_size
        party_flags = rom.u8(at)
        if party_flags & ~3:
            raise InventoryError(f"trainer {trainer_id}: unknown party flags {party_flags:#x}")
        battle_items = [rom.u16(at + 0x0A + slot * 2) for slot in range(4)]
        ai_flags = rom.u32(at + 0x14)
        party_size = rom.u8(at + 0x18)
        party_pointer = rom.u32(at + 0x1C)
        party = _decode_trainer_party(rom, party_pointer, party_size, party_flags)
        levels = [mon["level"] for mon in party]
        species = [mon["species"] for mon in party]
        moves = [mon["moves"] for mon in party]
        items = [mon["held_item"] for mon in party]
        trainer_class = rom.u8(at + 1)
        money_rate = money_rates.get(trainer_class, fallback_money_rate)
        last_party_level = levels[-1] if levels else 0
        base_reward = (money_rate * 4) * last_party_level
        for mon in party:
            all_species.add(mon["species"])
            all_moves.update(move for move in mon["moves"] if move)
            if mon["held_item"]:
                all_items.add(mon["held_item"])
        all_items.update(item for item in battle_items if item)
        evidence_refs = sorted(refs_by_trainer.get(trainer_id, []), key=lambda ref: int(ref.get("instruction_address", 0)))
        battle_refs = [ref for ref in evidence_refs if ref.get("access") == "battle"]
        battle_map_ids = {map_id for ref in battle_refs for map_id in _script_ref_map_ids(ref)}
        battle_sections = {map_sections[map_id] for map_id in battle_map_ids if map_id in map_sections}
        battle_types = {int(ref["battle_type"]) for ref in battle_refs if isinstance(ref.get("battle_type"), int)}
        # These classifications are all ROM-rooted: trainer class/name/level,
        # trainerbattle type, and the map-section reached from each root.  The
        # semantic section IDs are fixed properties of the audited Vega image.
        if battle_refs and 0xB0 in battle_sections:
            role = "sphere_boss"
            role_basis = "trainerbattle root is a map with Vega map-section 0xB0 (Sphere Ruins)"
        elif battle_refs and mirage_map in battle_map_ids:
            role = "mirage"
            role_basis = f"trainerbattle root is Mirage map {mirage_map[0]}/{mirage_map[1]}"
        elif battle_refs and 0x89 in battle_sections and levels and max(levels) == 100:
            role = "league_upgraded"
            role_basis = "trainerbattle root is league map-section 0x89 and party is level 100"
        elif battle_refs and 0x89 in battle_sections:
            role = "league_initial"
            role_basis = "trainerbattle root is league map-section 0x89 and party is below level 100"
        elif battle_refs and rom.u8(at + 1) == 84 and levels and max(levels) < 80:
            role = "gym_leader"
            role_basis = "trainer class 84, rooted story battle, and pre-rematch level band"
        elif battle_refs and rom.u8(at + 1) == 89:
            role = "rival"
            role_basis = "trainer class 89 with dynamic rival-name bytes and rooted battle"
        elif battle_refs and rom.u8(at + 1) == 86:
            role = "dh_executive"
            role_basis = "trainer class 86/name identity with rooted D/H executive battle"
        elif battle_refs and battle_types & {5, 7}:
            role = "battle_searcher_rematch"
            role_basis = "rooted trainerbattle type 5/7 (rematch/rematch-double)"
        elif battle_refs:
            role = "general"
            role_basis = "rooted trainerbattle not in a boss/facility/rematch domain"
        else:
            role = "UNKNOWN"
            role_basis = "trainer table row has no reachable trainerbattle reference"
        evidence = f"gTrainers[{trainer_id}] at {_hex(at)}"
        if evidence_refs:
            evidence += "; script refs " + ",".join(_hex(int(ref["instruction_address"])) for ref in evidence_refs[:8])
        rematch = "UNKNOWN"
        rematch_types = sorted({int(ref.get("battle_type")) for ref in evidence_refs if ref.get("battle_type") in (5, 7)})
        if rematch_types:
            rematch = ",".join(f"trainerbattle_type_{value}" for value in rematch_types)
        evidence += f"; role={role}: {role_basis}"
        unknown_fields = ["abilities"]
        if rematch == "UNKNOWN":
            unknown_fields.append("rematch_branch")
        if not (party_flags & 1) and party_size:
            unknown_fields.append("moves_materialized_from_level_up_learnset")
        if role == "UNKNOWN":
            unknown_fields.append("role")
        rows.append({"trainer_id": trainer_id, "role": role, "party_size": party_size, "species": species, "levels": levels, "moves": moves, "items": items, "ai_flags": ai_flags, "reward": base_reward, "rematch_branch": rematch, "evidence": evidence, "abilities": ["UNKNOWN"] * party_size, "move_source": "custom" if party_flags & 1 else "level_up_default", "reward_basis": {"trainer_class": trainer_class, "rate": money_rate, "last_party_level": last_party_level, "formula": "(rate * 4) * last_party_level", "battle_money_multiplier_excluded": True, "ordinary_double_multiplier_excluded": True}, "unknown_fields": unknown_fields, "classification_status": "ROM_ROOTED" if role != "UNKNOWN" else "UNKNOWN", "followup_task": "T16" if unknown_fields else ""})
        details.append({"trainer_id": trainer_id, "record_address": at, "party_flags": party_flags, "trainer_class": trainer_class, "encounter_music_gender": rom.u8(at + 2), "trainer_pic": rom.u8(at + 3), "name_hex": rom.raw(at + 4, 6).hex(), "battle_items": battle_items, "double_battle": rom.u8(at + 0x12), "party_address": party_pointer, "party": party})
    if SPECIES_NAMES_POINTER_SITE and rom.u32(SPECIES_NAMES_POINTER_SITE) != end:
        raise InventoryError("trainer table does not end at the ROM-rooted species-name table")
    counted: defaultdict[str, int] = defaultdict(int)
    for row in rows:
        counted[str(row["role"])] += 1
    role_counts = dict(sorted(counted.items()))
    required_roles = ["general", "rival", "dh_executive", "gym_leader", "league_initial", "league_upgraded", "battle_searcher_rematch", "sphere_boss", "mirage"]
    missing_roles = [role for role in required_roles if role_counts.get(role, 0) == 0]
    if missing_roles:
        raise InventoryError(f"trainer role baseline has empty required categories: {missing_roles}")
    if role_counts.get("gym_leader") != 8:
        raise InventoryError(f"trainer role baseline must identify exactly 8 gym leaders, got {role_counts.get('gym_leader', 0)}")
    return {"table_address": address, "record_size": record_size, "count": count, "end_exclusive": end, "money_table": {"pointer_site": TRAINER_MONEY_POINTER_SITE, "address": money_table_address, "row_count": len(money_rows), "terminator_address": money_terminator_address, "fallback_rate": fallback_money_rate, "rows": money_rows}, "rows": rows, "details": details, "role_counts": role_counts, "required_roles": required_roles, "required_roles_validated": True, "referenced_ids": {"species": sorted(all_species), "moves": sorted(all_moves), "items": sorted(all_items)}}


def validate_early_unlock(
    policy: Mapping[str, Any],
    script_refs: Sequence[Mapping[str, Any]],
    graph_nodes: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    unlock = _policy_get(policy, ("early_unlock",))
    required = [_parse_int(value, "early_unlock.required_flags") for value in unlock["required_flags"]]
    forbidden = [_parse_int(value, "early_unlock.forbidden_inferred_flags") for value in unlock["forbidden_inferred_flags"]]
    if required != [0x0824, 0x114B]:
        raise InventoryError(f"early unlock must be exact 0x0824 && 0x114B, got {required}")
    if 0x0822 not in forbidden:
        raise InventoryError("early unlock must explicitly reject inferred flag 0x0822")
    specs = [
        ("shiou", unlock["shiou"], "battle_script_address", "completion_flag"),
        ("dh_building", unlock["dh_building"], "final_script_address", "completion_flag"),
    ]
    evidence_rows: list[dict[str, Any]] = []
    adjacency = {
        int(node["address"]): [int(target) for target in node.get("edges", [])]
        for node in graph_nodes
    }
    for label, spec, script_field, flag_field in specs:
        script_address = _parse_int(spec[script_field], f"{label}.{script_field}")
        flag = _parse_int(spec[flag_field], f"{label}.{flag_field}")
        reachable = {script_address}
        pending = [script_address]
        while pending:
            current = pending.pop()
            for target in adjacency.get(current, []):
                if target not in reachable:
                    reachable.add(target)
                    pending.append(target)
        matches = [ref for ref in script_refs if ref.get("category") == "flag" and ref.get("value") == flag and ref.get("access") == "set" and int(ref.get("script_address", -1)) in reachable]
        if not matches:
            raise InventoryError(f"{label}: completion flag {flag:#x} is not set by {_hex(script_address)}")
        evidence_rows.append({"source": label, "root_script_address": script_address, "flag": flag, "set_instruction_addresses": sorted(int(ref["instruction_address"]) for ref in matches), "setting_script_addresses": sorted({int(ref["script_address"]) for ref in matches}), "roots": sorted({root for ref in matches for root in ref.get("roots", [])})})
    if sorted(row["flag"] for row in evidence_rows) != sorted(required):
        raise InventoryError("early unlock evidence does not prove the exact required flag pair")
    return {"required_flags": required, "forbidden_inferred_flags": forbidden, "operator": "AND", "predicate": "FlagGet(0x0824) && FlagGet(0x114B)", "latch_policy": unlock["latch_policy"], "validated": True, "evidence": evidence_rows}


_QOL_PATTERNS: dict[str, tuple[tuple[str, ...], str]] = {
    "dash": (("src/overworld.c", "IsRunningDisabledByFlag"), "T03"),
    "bicycle": (("include/bike.h", "StartTransitionToFlipBikeState"), "T03"),
    "field_text_printer": (("src/em_mining.c", "AddTextPrinterParameterized2"), "T03"),
    "battle_text_printer": (("include/new/Vanilla_functions_battle.h", "BattlePutTextOnWindow"), "T06"),
    "experience_distribution": (("src/battle_script_commands.c", "GiveExp"), "T06"),
    "item_use": (("assembly/hooks/general_hooks.s", "ItemUseHook"), "T09"),
    "daycare_and_hatching": (("src/daycare.c", "DetermineEgg"), "T09"),
    "summary": (("assembly/hooks/general_hooks.s", "StorageSummaryScreen"), "T09"),
    "pc": (("src/pokemon_storage_system.c", "Storage"), "T09"),
    "move_relearner": (("include/move_reminder.h", "MoveRelearner"), "T04"),
    "tm_consumption": (("src/learn_move.c", "CanMonLearnTMHM"), "T04"),
    "dexnav": (("src/read_keys.c", "DexNav"), "T10"),
    "raid": (("src/raid_battles.c", "Raid"), "T10"),
    "settings_save": (("include/new_game.h", "SetDefaultOptions"), "T08"),
}


def _source_candidate(source_root: Path, relative_hint: str, needle: str) -> tuple[str, int, str] | None:
    hinted = source_root / relative_hint
    candidates: Iterable[Path]
    if hinted.is_file():
        candidates = (hinted,)
    else:
        candidates = sorted(path for path in source_root.rglob("*") if path.is_file() and path.suffix.lower() in {".c", ".h", ".s", ".inc"})
    for path in candidates:
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for line_number, line in enumerate(lines, 1):
            stripped = line.strip()
            if needle in line and stripped and not stripped.startswith(("//", "/*", "*", "@")):
                compact = re.sub(r"\s+", " ", stripped)
                return path.relative_to(source_root).as_posix(), line_number, compact[:240]
    return None


def _scan_qol_hooks(root: Path, policy: Mapping[str, Any], source_lock: Mapping[str, Any]) -> list[dict[str, Any]]:
    source_by_name = {entry.get("name"): entry for entry in source_lock.get("sources", []) if isinstance(entry, Mapping)}
    cfru = source_by_name.get("cfru")
    if not cfru or not cfru.get("path"):
        raise InventoryError("source-lock has no CFRU source path")
    source_root = root / str(cfru["path"])
    required = [str(value) for value in _policy_get(policy, ("qol_required_domains",))]
    rows: list[dict[str, Any]] = []
    for domain in required:
        hints = _QOL_PATTERNS.get(domain)
        candidate = _source_candidate(source_root, hints[0][0], hints[0][1]) if hints else None
        followup = hints[1] if hints else "T03"
        if candidate:
            path, line, source_line = candidate
            address = ""
            address_match = re.search(r"0x0?8[0-9A-Fa-f]{6,7}", source_line)
            if address_match:
                address = address_match.group(0).upper().replace("0X", "0x")
            identifiers = re.findall(r"\b[A-Za-z_][A-Za-z0-9_]*\b", source_line)
            matching_identifiers = [value for value in identifiers if hints[0][1].lower() in value.lower()]
            address_or_symbol = address or (matching_identifiers[0] if matching_identifiers else hints[0][1])
            rows.append({"domain": domain, "address_or_symbol": address_or_symbol, "status": "SOURCE_CANDIDATE", "vega_expected_sha256": "", "classification": "UNKNOWN", "evidence": f"CFRU-JP@{cfru.get('resolved_commit', cfru.get('configured_commit', ''))}:{path}:{line}: {source_line}", "followup_task": followup})
        else:
            rows.append({"domain": domain, "address_or_symbol": "", "status": "MISSING_SOURCE_CANDIDATE", "vega_expected_sha256": "", "classification": "UNKNOWN", "evidence": f"No rooted CFRU source match for domain {domain}", "followup_task": followup})
    return sorted(rows, key=lambda row: row["domain"])


def _source_lock_provenance(root: Path, policy: Mapping[str, Any]) -> tuple[dict[str, Any], Mapping[str, Any]]:
    lock_path_text = str(_policy_get(policy, ("source_lock", "path")))
    lock_path = root / lock_path_text
    try:
        lock_bytes = lock_path.read_bytes()
        source_lock = json.loads(lock_bytes)
    except (OSError, json.JSONDecodeError) as exc:
        raise InventoryError(f"cannot read source lock {lock_path_text}") from exc
    actual_hash = _sha256(lock_bytes)
    expected_hash = str(_policy_get(policy, ("source_lock", "sha256"))).lower()
    if actual_hash != expected_hash:
        raise InventoryError(f"source-lock sha256 mismatch: {actual_hash} != {expected_hash}")
    expected_commits = _policy_get(policy, ("source_lock", "commits"))
    sources = []
    for source in sorted(source_lock.get("sources", []), key=lambda entry: str(entry.get("name", ""))):
        name = str(source.get("name", ""))
        resolved = str(source.get("resolved_commit", source.get("actual_commit", "")))
        if name in expected_commits and resolved != str(expected_commits[name]):
            raise InventoryError(f"source commit mismatch for {name}: {resolved}")
        sources.append({"name": name, "path": str(source.get("path", "")), "commit": resolved, "repository": str(source.get("repository", ""))})
    return ({"path": lock_path_text, "sha256": actual_hash, "sources": sources}, source_lock)


def _rom_root_comparison(roms: Mapping[str, RomImage]) -> dict[str, dict[str, int]]:
    sites = {
        "gMapGroups": MAP_GROUPS_POINTER_SITE,
        "gWildMonHeaders": 0x0808257C,
        "species_names": SPECIES_NAMES_POINTER_SITE,
        "move_names": MOVE_NAMES_POINTER_SITE,
        "item_table": ITEM_TABLE_POINTER_SITE,
        "move_data": MOVE_DATA_POINTER_SITE,
    }
    result: dict[str, dict[str, int]] = {}
    for label, rom in sorted(roms.items()):
        roots: dict[str, int] = {}
        for name, site in sorted(sites.items()):
            pointer = rom.u32(site, what=f"{name} root")
            rom.require_pointer(pointer, alignment=4, what=f"{name} rooted data")
            roots[name] = pointer
        result[label] = roots
    return result


def build_rom_inventory(root: Path, policy: Mapping[str, Any]) -> dict[str, Any]:
    """Build the T02 JSON-compatible inventory from fixed repository inputs."""

    root = Path(root).resolve()
    source_provenance, source_lock = _source_lock_provenance(root, policy)
    input_policy = _policy_get(policy, ("inputs",))
    roms: dict[str, RomImage] = {}
    for label in ("clean", "vega", "factory"):
        expected = _policy_get(input_policy, (label,))
        roms[label] = RomImage.from_path(label, root / str(expected["path"]), expected)
    vega = roms["vega"]
    maps, roots, structural_refs = _scan_maps(vega, policy)
    encounters, wild_refs = _scan_encounters(vega, policy)
    walker = ScriptWalker(vega)
    for root_item in roots:
        walker.add_root(root_item)
    script_graph = walker.walk()
    script_refs = list(script_graph["references"])
    script_refs.extend(structural_refs)
    script_refs.extend(wild_refs)
    script_refs.sort(key=lambda item: (str(item["category"]), json.dumps(item["value"], sort_keys=True), int(item.get("instruction_address", item.get("address", 0))), str(item["access"])))
    maps["travel_state"]["escape"]["script_references"] = [ref for ref in script_graph["references"] if ref["category"] == "map" and ref.get("opcode") == 0xC4]
    maps["travel_state"]["fly_and_heal"]["respawn_references"] = [ref for ref in script_graph["references"] if ref["category"] == "heal_location"]
    maps["travel_state"]["fly_and_heal"]["fly_unlock_references"] = [ref for ref in script_graph["references"] if ref["category"] == "fly_flag"]
    early_unlock = validate_early_unlock(policy, script_graph["references"], script_graph["nodes"])
    trainers = _scan_trainers(vega, policy, script_graph["references"], maps["rows"])
    qol_hooks = _scan_qol_hooks(root, policy, source_lock)
    provenance = {
        "policy_id": str(policy.get("policy_id", "")),
        "source_lock": source_provenance,
        "roms": {label: {"path": rom.logical_path, "size": len(rom.data), "sha256": rom.sha256} for label, rom in sorted(roms.items())},
        "rom_pointer_roots": _rom_root_comparison(roms),
        "scan_contract": {"rom_byte_pattern_scan": False, "script_roots": ["map_scripts", "object_events", "coord_events", "bg_events"], "pointer_bounds_checked": True, "visited_graph": True, "timestamps": False, "private_raw_dump": False},
    }
    category_counts = defaultdict(int)
    for ref in script_refs:
        category_counts[str(ref["category"])] += 1
    summaries = {
        "map_group_count": maps["group_count"],
        "physical_map_count": maps["physical_map_count"],
        "wild_header_count": encounters["header_count"],
        "script_root_count": script_graph["root_count"],
        "visited_script_count": script_graph["visited_script_count"],
        "script_reference_counts": dict(sorted(category_counts.items())),
        "trainer_count": trainers["count"],
        "trainer_role_counts": trainers["role_counts"],
        "trainer_required_roles_validated": trainers["required_roles_validated"],
        "qol_domain_count": len(qol_hooks),
        "escape_allowed_map_count": maps["travel_state"]["escape"]["allowed_map_count"],
        "fly_allowed_map_count": maps["travel_state"]["fly_and_heal"]["fly_allowed_map_count"],
        "hidden_item_count": maps["travel_state"]["hidden_items"]["row_count"],
        "early_unlock_validated": early_unlock["validated"],
    }
    # Keep this exact key set: report renderers consume these eight sections.
    return {
        "schema_version": 1,
        "provenance": provenance,
        "maps": maps,
        "encounters": encounters,
        "script_references": {"graph": script_graph, "rows": script_refs},
        "early_unlock": early_unlock,
        "trainers": trainers,
        "qol_hooks": qol_hooks,
        "summaries": summaries,
    }


def _load_policy(path: Path) -> Mapping[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise InventoryError(f"cannot read policy: {path}") from exc
    if not isinstance(value, Mapping):
        raise InventoryError("policy root must be an object")
    return value


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build deterministic T02 ROM-rooted inventory JSON")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2], help="repository root")
    parser.add_argument("--policy", type=Path, default=Path("config/t02_audit_policy.json"), help="policy path, relative to --root")
    parser.add_argument("--pretty", action="store_true", help="pretty-print deterministic JSON")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    policy_path = args.policy if args.policy.is_absolute() else root / args.policy
    try:
        inventory = build_rom_inventory(root, _load_policy(policy_path))
    except InventoryError as exc:
        print(f"rom-inventory: {exc}", file=sys.stderr)
        return 2
    if args.pretty:
        json.dump(inventory, sys.stdout, ensure_ascii=False, sort_keys=True, indent=2)
    else:
        json.dump(inventory, sys.stdout, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
