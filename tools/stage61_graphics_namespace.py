"""Stage61 Kanto object-graphics namespace planning.

The imported Kanto maps keep FireRed's numeric ``graphics_id`` values, while
Vega/Stage60 has legitimately repurposed a part of the underlying graphics
assets.  Numeric equality is therefore not proof of visual identity.  This
module inventories every live object in the 253 imported physical maps,
compares the complete clean/Stage60 graphics closure, and clones only the
closures whose semantics differ.

The implementation deliberately treats pointers as a graph.  A source address
is emitted once, all aliases point at the same emitted node, and every internal
pointer is fixed up only after the final load address is known.  Missing or
out-of-ROM pointers, table drift, allocation collisions, and unresolved fixups
are hard failures.
"""

from __future__ import annotations

import hashlib
import json
import re
import struct
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


class GraphicsNamespaceError(RuntimeError):
    """A graphics namespace cannot be proved safe from the pinned inputs."""


GBA_BASE = 0x08000000
GBA_ROM_END = 0x0A000000
MAP_GROUPS_POINTER_SITE = 0x00054B0C
OBJECT_EVENT_SIZE = 0x18
OBJECT_GRAPHICS_INFO_SIZE = 0x24
OBJECT_GRAPHICS_TABLE = 0x08363E38
OBJECT_GRAPHICS_COUNT = 152
# The stock accessor, CFRU's 16-bit graphics resolver, and that resolver's
# namespace-bank zero entry are three independent live consumers.  Updating
# only the stock accessor leaves CFRU paths reading the old 152-entry table.
OBJECT_GRAPHICS_POINTER_SITES = (
    0x0805EBB4,
    0x090DF0B0,
    0x09163828,
)
OBJECT_GRAPHICS_STATIC_LIMIT_SITE = 0x0805EBA0
OBJECT_GRAPHICS_STATIC_LIMIT_PREIMAGE = bytes.fromhex("9729")  # cmp r1, #151
OBJECT_GRAPHICS_STATIC_LIMIT_REPLACEMENT = bytes.fromhex("ef29")  # cmp r1, #239
OBJECT_PALETTE_TABLE = 0x083691E0
OBJECT_PALETTE_ENTRY_COUNT = 18
OBJECT_PALETTE_SENTINEL = 0x11FF
OBJECT_PALETTE_POINTER_SITES = (
    0x0805ED98,
    0x0805EE30,
    0x0805EE88,
)

# 152..238 are the only static IDs unused by the stock FireRed table and below
# both the Stage61 Snorlax reservation (239) and the engine's dynamic IDs
# (240..255).  The allocator never silently crosses either boundary.
CLONE_GRAPHICS_ID_START = 152
CLONE_GRAPHICS_ID_END = 238
RESERVED_GRAPHICS_IDS = frozenset({239})
DYNAMIC_GRAPHICS_ID_START = 240

# Sprite palette tags are identifiers rather than table indexes.  A private
# high range prevents a cloned Kanto palette from changing the palette used by
# an existing Tohoku object with the same FireRed-era tag.
CLONE_PALETTE_TAG_START = 0x7000
CLONE_PALETTE_TAG_END = 0x70FF

CLEAN_ROM_SHA256 = "1e4af44b0c75cc8649bfb8649dc4ae5850bf5358bd6b9cd0bf779c99f9db1486"
STAGE60_ROM_SHA256 = "3f9983eb099c2ca7205c14047460c8b2ed73a6180bd2a131a09c74af9d359ff1"
# Canonical importer schema v3 preserves the source object/coord producer
# fields instead of silently zeroing them.  The graphics plan below still
# validates every selected object closure and fixed remap; pin the complete
# regenerated 253-map surface so a later schema/content change fails closed.
CANONICAL_IMPORTER_SHA256 = "85d13607a3f8b2822fac67af4a3cb3c3ec751e663491084bbdbfa9496c1c68d7"
CANONICAL_MAPS_SHA256 = "972234ebbc9a4c405508b113c690fe7874bc767070b099875c7cf4b06c133ef0"
EVENT_OBJECT_CONSTANTS_SHA256 = "5f552a754182788f21ee00fe9460d5dbc73303239cc06743fbed96c93b6e6947"

# The animation pointer tables are not all referenced by ObjectEventGraphicsInfo
# (for example AcroBike).  Consequently, "next referenced pointer" cannot be
# used to infer their sizes.  These exact counts come from the pinned clean
# Japanese binary/source pair and are validated command-by-command below.
ANIMATION_TABLE_COUNTS: Mapping[int, int] = {
    0x0836739C: 1,   # Inanimate
    0x083673A0: 20,  # QuintyPlump (unreferenced by the 152 stock infos)
    0x083673F0: 21,  # Standard
    0x08367444: 21,  # HoOh
    0x08367498: 24,  # Unknown
    0x083674F8: 29,  # RedGreenNormal
    0x0836756C: 40,  # AcroBike
    0x0836760C: 24,  # RedGreenSurf
    0x0836766C: 21,  # Nurse
    0x083676C0: 1,   # FieldMove
    0x083676C4: 1,   # VSSeeker
    0x083676C8: 1,   # VSSeekerBike
    0x083676CC: 5,   # BerryTree (unreferenced)
    0x083676E0: 2,   # RockSmashRock
    0x083676E8: 2,   # CutTree
    0x083676F0: 12,  # Fish
}

IMAGE_TABLE_END = 0x083669D8
AFFINE_TABLE_COUNTS: Mapping[int, int] = {0x081F11F0: 1}


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _stable(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True,
                       separators=(",", ":")) + "\n").encode()


def _align(value: int, alignment: int) -> int:
    if alignment <= 0 or alignment & (alignment - 1):
        raise GraphicsNamespaceError(f"alignment must be a power of two: {alignment}")
    return (value + alignment - 1) & ~(alignment - 1)


def _rom_offset(raw: bytes, pointer: int, size: int, what: str) -> int:
    offset = pointer - GBA_BASE
    if pointer < GBA_BASE or offset < 0 or size < 0 or offset + size > len(raw):
        raise GraphicsNamespaceError(
            f"{what}: ROM pointer outside image: {pointer:#010x} size={size:#x}"
        )
    return offset


def _read(raw: bytes, pointer: int, size: int, what: str) -> bytes:
    offset = _rom_offset(raw, pointer, size, what)
    return raw[offset:offset + size]


def _u32_at(raw: bytes, offset: int, what: str) -> int:
    if offset < 0 or offset + 4 > len(raw):
        raise GraphicsNamespaceError(f"{what}: truncated u32 at {offset:#x}")
    return struct.unpack_from("<I", raw, offset)[0]


def _u32_ptr(raw: bytes, pointer: int, what: str) -> int:
    return struct.unpack("<I", _read(raw, pointer, 4, what))[0]


def _is_rom_pointer(raw: bytes, pointer: int, size: int = 1) -> bool:
    offset = pointer - GBA_BASE
    return pointer >= GBA_BASE and offset >= 0 and offset + size <= len(raw)


def _file_sha(path: Path, expected: str, what: str) -> bytes:
    if not path.is_file():
        raise GraphicsNamespaceError(f"{what} is missing: {path}")
    raw = path.read_bytes()
    actual = _sha(raw)
    if actual != expected:
        raise GraphicsNamespaceError(
            f"{what} SHA-256 differs: {actual} != {expected}"
        )
    return raw


def _literal_offsets(raw: bytes, value: int) -> tuple[int, ...]:
    needle = struct.pack("<I", value)
    result: list[int] = []
    cursor = 0
    while True:
        offset = raw.find(needle, cursor)
        if offset < 0:
            return tuple(result)
        result.append(offset)
        cursor = offset + 1


def _audit_table_consumers(stage60: bytes) -> None:
    graphics_offsets = _literal_offsets(stage60, OBJECT_GRAPHICS_TABLE)
    expected_graphics = tuple(site - GBA_BASE for site in OBJECT_GRAPHICS_POINTER_SITES)
    if graphics_offsets != expected_graphics:
        raise GraphicsNamespaceError(
            f"object graphics table consumer inventory differs: "
            f"{[hex(value) for value in graphics_offsets]}"
        )
    palette_offsets = _literal_offsets(stage60, OBJECT_PALETTE_TABLE)
    expected_palette = tuple(site - GBA_BASE for site in OBJECT_PALETTE_POINTER_SITES)
    if palette_offsets != expected_palette:
        raise GraphicsNamespaceError(
            f"object palette table consumer inventory differs: "
            f"{[hex(value) for value in palette_offsets]}"
        )
    limit_offset = OBJECT_GRAPHICS_STATIC_LIMIT_SITE - GBA_BASE
    if stage60[limit_offset:limit_offset + 2] != OBJECT_GRAPHICS_STATIC_LIMIT_PREIMAGE:
        raise GraphicsNamespaceError("stock graphics accessor limit preimage differs")

    # CFRU's resolver at 0x090DF004 first indexes a table of namespace-bank
    # pointers (bank zero lives at 0x09163828), then uses the direct stock
    # pointer literal as its fallback.  These opcode preimages prove that the
    # two expanded-ROM occurrences above are live consumers, not data matches.
    consumer_preimages = {
        0x010DF03E: bytes.fromhex("194a9b009b58"),
        0x010DF06C: bytes.fromhex("104b9c46a40064442068"),
        0x010DF07A: bytes.fromhex("0d4b186c"),
        0x010DF09A: bytes.fromhex("054bd4e7"),
    }
    for offset, expected in consumer_preimages.items():
        if stage60[offset:offset + len(expected)] != expected:
            raise GraphicsNamespaceError(
                f"CFRU graphics resolver consumer differs at {GBA_BASE + offset:#010x}"
            )
    if _u32_at(stage60, 0x010DF0A4, "CFRU graphics bank table pointer") \
            != 0x09163828:
        raise GraphicsNamespaceError("CFRU graphics bank-zero indirection differs")


def _component(raw: bytes) -> dict[str, object]:
    return {"size": len(raw), "sha256": _sha(raw), "hex": raw.hex()}


def _alias_rows(pointers: Sequence[int], payloads: Sequence[bytes]) -> list[dict[str, object]]:
    aliases: dict[int, int] = {}
    result: list[dict[str, object]] = []
    for pointer, raw in zip(pointers, payloads):
        if pointer not in aliases:
            aliases[pointer] = len(aliases)
        result.append({"alias": aliases[pointer], **_component(raw)})
    return result


@dataclass(frozen=True)
class ClosureSignature:
    graphics_id: int
    sha256: str
    components: Mapping[str, object]


@dataclass(frozen=True)
class PayloadFixup:
    offset: int
    target_key: str
    target_delta: int = 0


@dataclass(frozen=True)
class PayloadNode:
    key: str
    raw: bytes
    alignment: int
    source_address: int | None
    roles: tuple[str, ...]
    fixups: tuple[PayloadFixup, ...] = ()


@dataclass(frozen=True)
class PointerPatch:
    name: str
    offset: int
    expected: bytes
    replacement: bytes


@dataclass(frozen=True)
class MaterializedGraphicsNamespace:
    payload: bytes
    load_address: int
    node_offsets: Mapping[str, int]
    node_addresses: Mapping[str, int]
    graphics_info_addresses: Mapping[int, int]
    palette_table_address: int
    palette_pointer_patches: tuple[PointerPatch, ...]
    palette_tag_remap: Mapping[int, int]
    sha256: str
    fixup_count: int


@dataclass(frozen=True)
class RelocatableGraphicsPayload:
    nodes: tuple[PayloadNode, ...]
    graphics_info_nodes: Mapping[int, str]
    palette_table_node: str
    palette_tag_remap: Mapping[int, int]
    source_closure_sha256: str

    def materialize(self, load_address: int) -> MaterializedGraphicsNamespace:
        if load_address & 3:
            raise GraphicsNamespaceError(
                f"graphics payload load address is not word-aligned: {load_address:#010x}"
            )
        offsets: dict[str, int] = {}
        cursor = 0
        keys: set[str] = set()
        for node in self.nodes:
            if node.key in keys:
                raise GraphicsNamespaceError(f"duplicate payload node: {node.key}")
            keys.add(node.key)
            cursor = _align(cursor, node.alignment)
            offsets[node.key] = cursor
            cursor += len(node.raw)
        if load_address < GBA_BASE or load_address + cursor > GBA_ROM_END:
            raise GraphicsNamespaceError(
                f"materialized graphics payload outside 32 MiB ROM: "
                f"{load_address:#010x}+{cursor:#x}"
            )
        addresses = {key: load_address + offset for key, offset in offsets.items()}
        node_by_key = {node.key: node for node in self.nodes}
        result = bytearray(cursor)
        fixup_count = 0
        for node in self.nodes:
            start = offsets[node.key]
            result[start:start + len(node.raw)] = node.raw
            occupied: set[int] = set()
            for fixup in node.fixups:
                if fixup.offset < 0 or fixup.offset + 4 > len(node.raw):
                    raise GraphicsNamespaceError(
                        f"{node.key}: fixup outside node at {fixup.offset:#x}"
                    )
                if any(index in occupied for index in range(fixup.offset, fixup.offset + 4)):
                    raise GraphicsNamespaceError(
                        f"{node.key}: overlapping fixup at {fixup.offset:#x}"
                    )
                occupied.update(range(fixup.offset, fixup.offset + 4))
                if fixup.target_key not in addresses:
                    raise GraphicsNamespaceError(
                        f"{node.key}: unresolved payload target {fixup.target_key}"
                    )
                target_node = node_by_key[fixup.target_key]
                if not 0 <= fixup.target_delta < len(target_node.raw):
                    raise GraphicsNamespaceError(
                        f"{node.key}: target delta outside {fixup.target_key}: "
                        f"{fixup.target_delta:#x}"
                    )
                target = addresses[fixup.target_key] + fixup.target_delta
                if not load_address <= target < load_address + cursor:
                    raise GraphicsNamespaceError(
                        f"{node.key}: internal target outside payload: {target:#010x}"
                    )
                struct.pack_into("<I", result, start + fixup.offset, target)
                fixup_count += 1
        palette_address = addresses.get(self.palette_table_node)
        if palette_address is None:
            raise GraphicsNamespaceError("palette table node was not materialized")
        graphics_info_addresses = {
            source_id: addresses[key]
            for source_id, key in self.graphics_info_nodes.items()
        }
        pointer_raw = struct.pack("<I", palette_address)
        old_pointer_raw = struct.pack("<I", OBJECT_PALETTE_TABLE)
        palette_patches = tuple(
            PointerPatch(
                name=f"object_palette_table_pointer::{site:#010x}",
                offset=site - GBA_BASE,
                expected=old_pointer_raw,
                replacement=pointer_raw,
            )
            for site in OBJECT_PALETTE_POINTER_SITES
        )
        payload = bytes(result)
        return MaterializedGraphicsNamespace(
            payload=payload,
            load_address=load_address,
            node_offsets=dict(offsets),
            node_addresses=dict(addresses),
            graphics_info_addresses=graphics_info_addresses,
            palette_table_address=palette_address,
            palette_pointer_patches=palette_patches,
            palette_tag_remap=dict(self.palette_tag_remap),
            sha256=_sha(payload),
            fixup_count=fixup_count,
        )


@dataclass(frozen=True)
class ObjectRecordPlan:
    map_key: str
    group: int
    map_number: int
    object_index: int
    local_id: int
    record_offset: int
    record_preimage: bytes
    source_graphics_id: int
    runtime_graphics_id: int
    action: str

    @property
    def patch(self) -> PointerPatch | None:
        if self.action != "REMAP_CLEAN_CLOSURE":
            return None
        return PointerPatch(
            name=(f"kanto_object_graphics::{self.group:03d}/"
                  f"{self.map_number:03d}/{self.object_index:03d}"),
            offset=self.record_offset + 1,
            expected=bytes((self.source_graphics_id,)),
            replacement=bytes((self.runtime_graphics_id,)),
        )


@dataclass(frozen=True)
class GraphicsNamespacePlan:
    clean_rom_sha256: str
    stage60_rom_sha256: str
    canonical_importer_sha256: str
    canonical_maps_sha256: str
    map_count: int
    object_records: tuple[ObjectRecordPlan, ...]
    used_graphics_ids: tuple[int, ...]
    mismatched_graphics_ids: tuple[int, ...]
    closure_signatures_clean: Mapping[int, ClosureSignature]
    closure_signatures_stage60: Mapping[int, ClosureSignature]
    graphics_id_remap: Mapping[int, int]
    payload: RelocatableGraphicsPayload
    stage60_graphics_pointers: tuple[int, ...]
    stage60_rom: bytes = field(repr=False, compare=False)

    @property
    def object_patches(self) -> tuple[PointerPatch, ...]:
        return tuple(
            patch for row in self.object_records
            if (patch := row.patch) is not None
        )

    @property
    def remapped_object_count(self) -> int:
        return len(self.object_patches)

    def materialize(self, load_address: int) -> MaterializedGraphicsNamespace:
        return self.payload.materialize(load_address)

    def apply_object_patches(self, rom: bytes) -> bytes:
        if _sha(rom) != self.stage60_rom_sha256:
            raise GraphicsNamespaceError("object patches require the exact Stage60 ROM")
        output = bytearray(rom)
        for row in self.object_records:
            if output[row.record_offset:row.record_offset + OBJECT_EVENT_SIZE] \
                    != row.record_preimage:
                raise GraphicsNamespaceError(
                    f"{row.map_key} object {row.object_index}: record preimage differs"
                )
            patch = row.patch
            if patch is not None:
                output[patch.offset:patch.offset + 1] = patch.replacement
        return bytes(output)

    def build_extended_graphics_table(
        self,
        materialized: MaterializedGraphicsNamespace,
        *,
        reserved_graphics_pointers: Mapping[int, int],
        entry_count: int = 240,
        fallback_graphics_id: int = 16,
    ) -> bytes:
        if entry_count != DYNAMIC_GRAPHICS_ID_START:
            raise GraphicsNamespaceError(
                f"extended static table must stop before dynamic ID 240: {entry_count}"
            )
        if not 0 <= fallback_graphics_id < OBJECT_GRAPHICS_COUNT:
            raise GraphicsNamespaceError("fallback graphics ID is outside the stock table")
        missing = RESERVED_GRAPHICS_IDS - set(reserved_graphics_pointers)
        extra = set(reserved_graphics_pointers) - RESERVED_GRAPHICS_IDS
        if missing or extra:
            raise GraphicsNamespaceError(
                f"reserved graphics pointers differ: missing={sorted(missing)} "
                f"extra={sorted(extra)}"
            )
        fallback = self.stage60_graphics_pointers[fallback_graphics_id]
        entries = [
            self.stage60_graphics_pointers[index]
            if index < OBJECT_GRAPHICS_COUNT else fallback
            for index in range(entry_count)
        ]
        runtime_ids = tuple(self.graphics_id_remap.values())
        if len(set(runtime_ids)) != len(runtime_ids):
            raise GraphicsNamespaceError("graphics clone remap is not injective")
        if any(
            not CLONE_GRAPHICS_ID_START <= runtime_id <= CLONE_GRAPHICS_ID_END
            for runtime_id in runtime_ids
        ):
            raise GraphicsNamespaceError(
                "graphics clone remap escaped the proven-free static range"
            )
        if materialized.palette_tag_remap != self.payload.palette_tag_remap:
            raise GraphicsNamespaceError(
                "materialized payload belongs to a different graphics plan"
            )
        for source_id, runtime_id in self.graphics_id_remap.items():
            address = materialized.graphics_info_addresses.get(source_id)
            if address is None:
                raise GraphicsNamespaceError(
                    f"materialized info is missing for graphics ID {source_id}"
                )
            info_key = self.payload.graphics_info_nodes.get(source_id)
            if info_key is None \
                    or materialized.node_addresses.get(info_key) != address:
                raise GraphicsNamespaceError(
                    f"materialized info alias differs for graphics ID {source_id}"
                )
            if not materialized.load_address <= address \
                    or address + OBJECT_GRAPHICS_INFO_SIZE \
                    > materialized.load_address + len(materialized.payload) \
                    or address & 3:
                raise GraphicsNamespaceError(
                    f"materialized info address is invalid for graphics ID {source_id}"
                )
            if entries[runtime_id] != fallback:
                raise GraphicsNamespaceError(
                    f"graphics table collision at runtime ID {runtime_id}"
                )
            entries[runtime_id] = address
        for runtime_id, pointer in reserved_graphics_pointers.items():
            if not isinstance(pointer, int) \
                    or not GBA_BASE <= pointer \
                    or pointer + OBJECT_GRAPHICS_INFO_SIZE > GBA_ROM_END \
                    or pointer & 3:
                raise GraphicsNamespaceError(
                    f"reserved graphics pointer is invalid: {runtime_id}={pointer!r}"
                )
            if runtime_id in self.graphics_id_remap.values():
                raise GraphicsNamespaceError(
                    f"reserved graphics ID collides with clone: {runtime_id}"
                )
            entries[runtime_id] = pointer
        return struct.pack(f"<{entry_count}I", *entries)

    def graphics_table_pointer_patches(
        self, table_address: int,
    ) -> tuple[PointerPatch, ...]:
        """Return all three proven live references to the graphics table."""
        if not isinstance(table_address, int) \
                or not GBA_BASE <= table_address \
                or table_address + DYNAMIC_GRAPHICS_ID_START * 4 > GBA_ROM_END \
                or table_address & 3:
            raise GraphicsNamespaceError(
                f"graphics table address is invalid: {table_address!r}"
            )
        expected = struct.pack("<I", OBJECT_GRAPHICS_TABLE)
        replacement = struct.pack("<I", table_address)
        return tuple(
            PointerPatch(
                name=f"object_graphics_table_pointer::{site:#010x}",
                offset=site - GBA_BASE,
                expected=expected,
                replacement=replacement,
            )
            for site in OBJECT_GRAPHICS_POINTER_SITES
        )

    def graphics_static_limit_patch(self) -> PointerPatch:
        """Allow the stock u8 accessor to index cloned IDs through ID 239."""
        return PointerPatch(
            name="object_graphics_static_id_limit::0x0805EBA0",
            offset=OBJECT_GRAPHICS_STATIC_LIMIT_SITE - GBA_BASE,
            expected=OBJECT_GRAPHICS_STATIC_LIMIT_PREIMAGE,
            replacement=OBJECT_GRAPHICS_STATIC_LIMIT_REPLACEMENT,
        )

    def graphics_table_installation_patches(
        self, table_address: int,
    ) -> tuple[PointerPatch, ...]:
        """Return the complete table-pointer and stock-bound patch set."""
        return (*self.graphics_table_pointer_patches(table_address),
                self.graphics_static_limit_patch())

    def audit_dict(self) -> dict[str, object]:
        action_counts: dict[str, int] = {}
        for row in self.object_records:
            action_counts[row.action] = action_counts.get(row.action, 0) + 1
        return {
            "schema_version": 1,
            "inputs": {
                "clean_rom_sha256": self.clean_rom_sha256,
                "stage60_rom_sha256": self.stage60_rom_sha256,
                "canonical_importer_sha256": self.canonical_importer_sha256,
                "canonical_maps_sha256": self.canonical_maps_sha256,
            },
            "map_count": self.map_count,
            "object_count": len(self.object_records),
            "used_graphics_ids": list(self.used_graphics_ids),
            "mismatched_graphics_ids": list(self.mismatched_graphics_ids),
            "graphics_id_remap": {
                str(key): value for key, value in sorted(self.graphics_id_remap.items())
            },
            "action_counts": action_counts,
            "source_closure_sha256": self.payload.source_closure_sha256,
            "palette_tag_remap": {
                f"0x{key:04X}": f"0x{value:04X}"
                for key, value in sorted(self.payload.palette_tag_remap.items())
            },
            "object_records": [
                {
                    "map_key": row.map_key,
                    "group": row.group,
                    "map": row.map_number,
                    "object_index": row.object_index,
                    "local_id": row.local_id,
                    "record_offset": row.record_offset,
                    "record_preimage": row.record_preimage.hex(),
                    "source_graphics_id": row.source_graphics_id,
                    "runtime_graphics_id": row.runtime_graphics_id,
                    "action": row.action,
                }
                for row in self.object_records
            ],
        }


def allocate_graphics_ids(
    source_ids: Iterable[int],
    *,
    allocation_start: int = CLONE_GRAPHICS_ID_START,
    allocation_end: int = CLONE_GRAPHICS_ID_END,
    reserved_ids: Iterable[int] = RESERVED_GRAPHICS_IDS,
    dynamic_start: int = DYNAMIC_GRAPHICS_ID_START,
) -> dict[int, int]:
    source = sorted(set(int(value) for value in source_ids))
    reserved = set(RESERVED_GRAPHICS_IDS) | {
        int(value) for value in reserved_ids
    }
    if any(not 0 <= value < OBJECT_GRAPHICS_COUNT for value in source):
        raise GraphicsNamespaceError(
            "graphics clone sources must be stock static IDs 0..151"
        )
    if any(not 0 <= value <= 0xFF for value in reserved):
        raise GraphicsNamespaceError("reserved graphics ID is outside u8")
    if dynamic_start != DYNAMIC_GRAPHICS_ID_START:
        raise GraphicsNamespaceError(
            f"dynamic graphics boundary is fixed at {DYNAMIC_GRAPHICS_ID_START}"
        )
    if not (
        CLONE_GRAPHICS_ID_START <= allocation_start <= allocation_end
        <= CLONE_GRAPHICS_ID_END
    ):
        raise GraphicsNamespaceError(
            f"graphics clone allocation must stay in the proven-free range "
            f"{CLONE_GRAPHICS_ID_START}..{CLONE_GRAPHICS_ID_END}"
        )
    candidates = [
        value for value in range(allocation_start, allocation_end + 1)
        if value not in reserved
    ]
    if len(source) > len(candidates):
        raise GraphicsNamespaceError(
            f"graphics clone IDs exhausted: need {len(source)}, have {len(candidates)}"
        )
    result = dict(zip(source, candidates))
    if set(result.values()) & reserved:
        raise GraphicsNamespaceError("graphics clone allocation overlaps a reserved ID")
    if any(value >= dynamic_start for value in result.values()):
        raise GraphicsNamespaceError("graphics clone allocation entered dynamic IDs")
    return result


def _palette_entries(raw: bytes) -> tuple[tuple[int, int, bytes], ...]:
    table = _read(
        raw, OBJECT_PALETTE_TABLE, (OBJECT_PALETTE_ENTRY_COUNT + 1) * 8,
        "object palette table",
    )
    result: list[tuple[int, int, bytes]] = []
    tags: set[int] = set()
    for index in range(OBJECT_PALETTE_ENTRY_COUNT):
        pointer, tag = struct.unpack_from("<IH", table, index * 8)
        if not pointer or tag in (0, OBJECT_PALETTE_SENTINEL):
            raise GraphicsNamespaceError(
                f"object palette entry {index} is unexpectedly empty/sentinel"
            )
        if tag in tags:
            raise GraphicsNamespaceError(f"duplicate object palette tag: {tag:#06x}")
        tags.add(tag)
        palette = _read(raw, pointer, 32, f"object palette {tag:#06x}")
        result.append((pointer, tag, palette))
    terminal_pointer, terminal_tag = struct.unpack_from(
        "<IH", table, OBJECT_PALETTE_ENTRY_COUNT * 8
    )
    if terminal_pointer or terminal_tag:
        raise GraphicsNamespaceError("object palette source terminator differs")
    return tuple(result)


def _animation_commands(raw: bytes, pointer: int, what: str) -> bytes:
    result = bytearray()
    for index in range(64):
        command = _read(raw, pointer + index * 4, 4, what)
        result.extend(command)
        command_type = struct.unpack_from("<h", command)[0]
        if command_type in (-1, -2):
            return bytes(result)
        if command_type < -3:
            raise GraphicsNamespaceError(
                f"{what}: unsupported animation command {command_type}"
            )
    raise GraphicsNamespaceError(f"{what}: animation does not terminate")


def _affine_commands(raw: bytes, pointer: int, what: str) -> bytes:
    result = bytearray()
    for index in range(32):
        command = _read(raw, pointer + index * 8, 8, what)
        result.extend(command)
        command_type = struct.unpack_from("<H", command)[0]
        if command_type in (0x7FFF, 0x7FFE):
            return bytes(result)
    raise GraphicsNamespaceError(f"{what}: affine animation does not terminate")


def _image_counts_from_clean(clean: bytes) -> dict[int, int]:
    starts: set[int] = set()
    for graphics_id in range(OBJECT_GRAPHICS_COUNT):
        info_pointer = _u32_ptr(
            clean, OBJECT_GRAPHICS_TABLE + graphics_id * 4,
            f"clean graphics table {graphics_id}",
        )
        info = _read(
            clean, info_pointer, OBJECT_GRAPHICS_INFO_SIZE,
            f"clean graphics info {graphics_id}",
        )
        image_pointer = struct.unpack_from("<I", info, 0x1C)[0]
        _rom_offset(clean, image_pointer, 8, f"clean image table {graphics_id}")
        starts.add(image_pointer)
    ordered = sorted(starts)
    if len(ordered) != 150 or ordered[0] != 0x08364128 \
            or ordered[-1] != 0x08366990:
        raise GraphicsNamespaceError(
            f"clean image table inventory differs: {len(ordered)} "
            f"{ordered[0]:#010x}..{ordered[-1]:#010x}"
        )
    result: dict[int, int] = {}
    for index, pointer in enumerate(ordered):
        end = ordered[index + 1] if index + 1 < len(ordered) else IMAGE_TABLE_END
        distance = end - pointer
        if distance <= 0 or distance % 8 or distance // 8 > 64:
            raise GraphicsNamespaceError(
                f"clean image table boundary differs at {pointer:#010x}: {distance:#x}"
            )
        count = distance // 8
        for frame in range(count):
            row = _read(clean, pointer + frame * 8, 8,
                        f"clean image row {pointer:#010x}/{frame}")
            data_pointer, size = struct.unpack_from("<IH", row)
            if size < 32 or size > 0x4000 or size % 32:
                raise GraphicsNamespaceError(
                    f"clean image size is invalid at {pointer:#010x}/{frame}: {size}"
                )
            _rom_offset(clean, data_pointer, size,
                        f"clean image data {pointer:#010x}/{frame}")
        result[pointer] = count
    return result


def _closure_signature(
    raw: bytes,
    graphics_id: int,
    *,
    expected_image_count: int,
    expected_animation_count: int,
    expected_affine_count: int,
) -> ClosureSignature:
    if not 0 <= graphics_id < OBJECT_GRAPHICS_COUNT:
        raise GraphicsNamespaceError(f"static graphics ID outside table: {graphics_id}")
    info_pointer = _u32_ptr(
        raw, OBJECT_GRAPHICS_TABLE + graphics_id * 4,
        f"graphics table {graphics_id}",
    )
    info = _read(raw, info_pointer, OBJECT_GRAPHICS_INFO_SIZE,
                 f"graphics info {graphics_id}")
    oam_pointer, subsprite_pointer, animation_pointer, image_pointer, affine_pointer = \
        struct.unpack_from("<IIIII", info, 0x10)

    oam = _read(raw, oam_pointer, 8, f"OAM {graphics_id}")
    subsprite_table = _read(raw, subsprite_pointer, 6 * 8,
                            f"subsprite table {graphics_id}")
    subsprite_pointers: list[int] = []
    subsprite_payloads: list[bytes] = []
    subsprite_counts: list[int] = []
    for index in range(6):
        count = subsprite_table[index * 8]
        pointer = struct.unpack_from("<I", subsprite_table, index * 8 + 4)[0]
        subsprite_counts.append(count)
        if count:
            if not pointer:
                raise GraphicsNamespaceError(
                    f"subsprite {graphics_id}/{index}: nonzero count has null pointer"
                )
            subsprite_pointers.append(pointer)
            subsprite_payloads.append(_read(
                raw, pointer, count * 4, f"subsprite data {graphics_id}/{index}"
            ))
        elif pointer:
            raise GraphicsNamespaceError(
                f"subsprite {graphics_id}/{index}: zero count has non-null pointer"
            )

    animation_table = _read(
        raw, animation_pointer, expected_animation_count * 4,
        f"animation table {graphics_id}",
    )
    animation_pointers = list(struct.unpack(
        f"<{expected_animation_count}I", animation_table
    ))
    animation_payloads = [
        _animation_commands(raw, pointer, f"animation {graphics_id}/{index}")
        for index, pointer in enumerate(animation_pointers)
    ]

    image_table = _read(raw, image_pointer, expected_image_count * 8,
                        f"image table {graphics_id}")
    image_pointers: list[int] = []
    image_payloads: list[bytes] = []
    image_sizes: list[int] = []
    for index in range(expected_image_count):
        pointer, size = struct.unpack_from("<IH", image_table, index * 8)
        if not size:
            raise GraphicsNamespaceError(f"image {graphics_id}/{index}: zero size")
        image_pointers.append(pointer)
        image_sizes.append(size)
        image_payloads.append(_read(
            raw, pointer, size, f"image data {graphics_id}/{index}"
        ))

    affine_table = _read(raw, affine_pointer, expected_affine_count * 4,
                         f"affine table {graphics_id}")
    affine_pointers = list(struct.unpack(
        f"<{expected_affine_count}I", affine_table
    ))
    affine_payloads = [
        _affine_commands(raw, pointer, f"affine animation {graphics_id}/{index}")
        for index, pointer in enumerate(affine_pointers)
    ]

    palettes = {tag: (pointer, palette) for pointer, tag, palette in _palette_entries(raw)}
    palette_rows: list[dict[str, object]] = []
    palette_aliases: dict[int, int] = {}
    for role, tag in zip(("normal", "reflection"), struct.unpack_from("<HH", info, 2)):
        if tag == OBJECT_PALETTE_SENTINEL:
            palette_rows.append({"role": role, "tag": tag, "none": True})
            continue
        if tag not in palettes:
            raise GraphicsNamespaceError(
                f"graphics {graphics_id}: palette tag is unresolved: {tag:#06x}"
            )
        pointer, palette = palettes[tag]
        if pointer not in palette_aliases:
            palette_aliases[pointer] = len(palette_aliases)
        palette_rows.append({
            "role": role,
            "tag": tag,
            "alias": palette_aliases[pointer],
            **_component(palette),
        })

    components: dict[str, object] = {
        # Pointer fields are represented by their target closure below.  The
        # first 16 bytes are the complete scalar portion of the 0x24 struct.
        "info_scalars": _component(info[:0x10]),
        "oam": _component(oam),
        "subsprites": {
            "counts": subsprite_counts,
            "rows": _alias_rows(subsprite_pointers, subsprite_payloads),
        },
        "animations": _alias_rows(animation_pointers, animation_payloads),
        "images": {
            "sizes": image_sizes,
            "rows": _alias_rows(image_pointers, image_payloads),
        },
        "affine_animations": _alias_rows(affine_pointers, affine_payloads),
        "palettes": palette_rows,
    }
    signature = _sha(_stable(components))
    return ClosureSignature(graphics_id, signature, components)


def extract_graphics_closure_signature(
    rom: bytes,
    graphics_id: int,
    *,
    schema_rom: bytes | None = None,
) -> ClosureSignature:
    """Extract one closure, using clean table cardinalities as its schema.

    ``schema_rom`` is required when inspecting a modified ROM whose info
    pointers may no longer reference the original image/animation tables.
    """
    schema = schema_rom if schema_rom is not None else rom
    clean_image_counts = _image_counts_from_clean(schema)
    schema_info_pointer = _u32_ptr(
        schema, OBJECT_GRAPHICS_TABLE + graphics_id * 4,
        f"schema graphics table {graphics_id}",
    )
    schema_info = _read(
        schema, schema_info_pointer, OBJECT_GRAPHICS_INFO_SIZE,
        f"schema graphics info {graphics_id}",
    )
    animation_pointer = struct.unpack_from("<I", schema_info, 0x18)[0]
    image_pointer = struct.unpack_from("<I", schema_info, 0x1C)[0]
    affine_pointer = struct.unpack_from("<I", schema_info, 0x20)[0]
    if animation_pointer not in ANIMATION_TABLE_COUNTS:
        raise GraphicsNamespaceError(
            f"schema animation table is unknown: {animation_pointer:#010x}"
        )
    if image_pointer not in clean_image_counts:
        raise GraphicsNamespaceError(
            f"schema image table is unknown: {image_pointer:#010x}"
        )
    if affine_pointer not in AFFINE_TABLE_COUNTS:
        raise GraphicsNamespaceError(
            f"schema affine table is unknown: {affine_pointer:#010x}"
        )
    return _closure_signature(
        rom,
        graphics_id,
        expected_image_count=clean_image_counts[image_pointer],
        expected_animation_count=ANIMATION_TABLE_COUNTS[animation_pointer],
        expected_affine_count=AFFINE_TABLE_COUNTS[affine_pointer],
    )


class _NodeBuilder:
    def __init__(self, clean: bytes) -> None:
        self.clean = clean
        self.raw: dict[str, bytearray] = {}
        self.source: dict[str, int | None] = {}
        self.alignment: dict[str, int] = {}
        self.roles: dict[str, set[str]] = {}
        self.fixups: dict[str, dict[int, tuple[str, int]]] = {}
        self.by_address: dict[int, str] = {}

    def add_source(self, address: int, size: int, role: str,
                   alignment: int = 4) -> str:
        _rom_offset(self.clean, address, size, role)
        key = self.by_address.setdefault(address, f"source::{address:08X}")
        source_raw = _read(self.clean, address, size, role)
        if key in self.raw:
            current = bytes(self.raw[key])
            shared = min(len(current), len(source_raw))
            if current[:shared] != source_raw[:shared]:
                raise GraphicsNamespaceError(f"source alias bytes differ: {address:#010x}")
            if len(source_raw) > len(current):
                self.raw[key].extend(source_raw[len(current):])
        else:
            self.raw[key] = bytearray(source_raw)
            self.source[key] = address
            self.fixups[key] = {}
        self.alignment[key] = max(self.alignment.get(key, 1), alignment)
        self.roles.setdefault(key, set()).add(role)
        return key

    def add_synthetic(self, key: str, raw: bytes, role: str,
                      alignment: int = 4) -> str:
        if key in self.raw:
            raise GraphicsNamespaceError(f"duplicate synthetic node: {key}")
        self.raw[key] = bytearray(raw)
        self.source[key] = None
        self.alignment[key] = alignment
        self.roles[key] = {role}
        self.fixups[key] = {}
        return key

    def patch(self, key: str, offset: int, replacement: bytes) -> None:
        if key not in self.raw or offset < 0 or offset + len(replacement) > len(self.raw[key]):
            raise GraphicsNamespaceError(f"{key}: node patch outside bounds")
        self.raw[key][offset:offset + len(replacement)] = replacement

    def point(self, key: str, offset: int, target_key: str,
              target_delta: int = 0) -> None:
        if key not in self.raw or target_key not in self.raw:
            raise GraphicsNamespaceError(f"payload fixup references a missing node")
        previous = self.fixups[key].get(offset)
        value = (target_key, target_delta)
        if previous is not None and previous != value:
            raise GraphicsNamespaceError(f"{key}: conflicting fixup at {offset:#x}")
        self.fixups[key][offset] = value

    def freeze(self) -> tuple[PayloadNode, ...]:
        def order(key: str) -> tuple[int, int, str]:
            source = self.source[key]
            return (1 if source is None else 0, source or 0, key)
        result = []
        for key in sorted(self.raw, key=order):
            result.append(PayloadNode(
                key=key,
                raw=bytes(self.raw[key]),
                alignment=self.alignment[key],
                source_address=self.source[key],
                roles=tuple(sorted(self.roles[key])),
                fixups=tuple(
                    PayloadFixup(offset, target, delta)
                    for offset, (target, delta) in sorted(self.fixups[key].items())
                ),
            ))
        return tuple(result)


def _allocate_palette_tags(
    source_tags: Iterable[int], stage60: bytes, *,
    start: int, end: int, reserved: Iterable[int],
) -> dict[int, int]:
    source = sorted(set(source_tags) - {OBJECT_PALETTE_SENTINEL})
    reserved_set = {int(tag) for tag in reserved}
    if any(not 0 <= tag <= 0xFFFF for tag in set(source) | reserved_set):
        raise GraphicsNamespaceError("palette tag is outside u16")
    occupied = {tag for _, tag, _ in _palette_entries(stage60)} \
        | reserved_set | {0, OBJECT_PALETTE_SENTINEL}
    if not (
        CLONE_PALETTE_TAG_START <= start <= end <= CLONE_PALETTE_TAG_END
    ):
        raise GraphicsNamespaceError(
            f"palette clone allocation must stay in the private range "
            f"{CLONE_PALETTE_TAG_START:#06x}..{CLONE_PALETTE_TAG_END:#06x}"
        )
    candidates = [tag for tag in range(start, end + 1) if tag not in occupied]
    if len(source) > len(candidates):
        raise GraphicsNamespaceError(
            f"palette tags exhausted: need {len(source)}, have {len(candidates)}"
        )
    result = dict(zip(source, candidates))
    if set(result.values()) & occupied:
        raise GraphicsNamespaceError("palette tag allocation collision")
    return result


def _build_payload(
    clean: bytes,
    stage60: bytes,
    mismatch_ids: Sequence[int],
    clean_signatures: Mapping[int, ClosureSignature],
    *,
    palette_tag_start: int,
    palette_tag_end: int,
    reserved_palette_tags: Iterable[int],
) -> RelocatableGraphicsPayload:
    image_counts = _image_counts_from_clean(clean)
    clean_palettes = {tag: (pointer, palette)
                      for pointer, tag, palette in _palette_entries(clean)}
    source_palette_tags: set[int] = set()
    for graphics_id in mismatch_ids:
        info_pointer = _u32_ptr(
            clean, OBJECT_GRAPHICS_TABLE + graphics_id * 4,
            f"clean graphics table {graphics_id}",
        )
        info = _read(clean, info_pointer, OBJECT_GRAPHICS_INFO_SIZE,
                     f"clean graphics info {graphics_id}")
        source_palette_tags.update(
            tag for tag in struct.unpack_from("<HH", info, 2)
            if tag != OBJECT_PALETTE_SENTINEL
        )
    palette_remap = _allocate_palette_tags(
        source_palette_tags, stage60,
        start=palette_tag_start, end=palette_tag_end,
        reserved=reserved_palette_tags,
    )
    builder = _NodeBuilder(clean)
    info_nodes: dict[int, str] = {}

    for graphics_id in mismatch_ids:
        info_pointer = _u32_ptr(
            clean, OBJECT_GRAPHICS_TABLE + graphics_id * 4,
            f"clean graphics table {graphics_id}",
        )
        info = _read(clean, info_pointer, OBJECT_GRAPHICS_INFO_SIZE,
                     f"clean graphics info {graphics_id}")
        info_key = builder.add_source(
            info_pointer, OBJECT_GRAPHICS_INFO_SIZE,
            f"graphics_info::{graphics_id}",
        )
        info_nodes[graphics_id] = info_key
        for tag_offset in (2, 4):
            source_tag = struct.unpack_from("<H", info, tag_offset)[0]
            if source_tag != OBJECT_PALETTE_SENTINEL:
                builder.patch(
                    info_key, tag_offset,
                    struct.pack("<H", palette_remap[source_tag]),
                )
        oam_pointer, subsprite_pointer, animation_pointer, image_pointer, affine_pointer = \
            struct.unpack_from("<IIIII", info, 0x10)

        oam_key = builder.add_source(oam_pointer, 8, f"oam::{graphics_id}")
        builder.point(info_key, 0x10, oam_key)

        subsprite_key = builder.add_source(
            subsprite_pointer, 6 * 8, f"subsprite_table::{graphics_id}"
        )
        builder.point(info_key, 0x14, subsprite_key)
        subsprite_raw = _read(clean, subsprite_pointer, 6 * 8,
                              f"subsprite table {graphics_id}")
        for index in range(6):
            count = subsprite_raw[index * 8]
            pointer = struct.unpack_from("<I", subsprite_raw, index * 8 + 4)[0]
            if count:
                data_key = builder.add_source(
                    pointer, count * 4, f"subsprite_data::{graphics_id}/{index}"
                )
                builder.point(subsprite_key, index * 8 + 4, data_key)
            elif pointer:
                raise GraphicsNamespaceError(
                    f"subsprite {graphics_id}/{index}: zero count has pointer"
                )

        animation_count = ANIMATION_TABLE_COUNTS.get(animation_pointer)
        if animation_count is None:
            raise GraphicsNamespaceError(
                f"graphics {graphics_id}: unknown animation table {animation_pointer:#010x}"
            )
        animation_key = builder.add_source(
            animation_pointer, animation_count * 4,
            f"animation_table::{graphics_id}",
        )
        builder.point(info_key, 0x18, animation_key)
        for index in range(animation_count):
            pointer = _u32_ptr(
                clean, animation_pointer + index * 4,
                f"animation pointer {graphics_id}/{index}",
            )
            command_raw = _animation_commands(
                clean, pointer, f"animation {graphics_id}/{index}"
            )
            command_key = builder.add_source(
                pointer, len(command_raw), f"animation_commands::{graphics_id}/{index}"
            )
            builder.point(animation_key, index * 4, command_key)

        image_count = image_counts.get(image_pointer)
        if image_count is None:
            raise GraphicsNamespaceError(
                f"graphics {graphics_id}: unknown image table {image_pointer:#010x}"
            )
        image_key = builder.add_source(
            image_pointer, image_count * 8, f"image_table::{graphics_id}"
        )
        builder.point(info_key, 0x1C, image_key)
        for index in range(image_count):
            row = _read(clean, image_pointer + index * 8, 8,
                        f"image row {graphics_id}/{index}")
            pointer, size = struct.unpack_from("<IH", row)
            data_key = builder.add_source(
                pointer, size, f"image_data::{graphics_id}/{index}"
            )
            builder.point(image_key, index * 8, data_key)

        affine_count = AFFINE_TABLE_COUNTS.get(affine_pointer)
        if affine_count is None:
            raise GraphicsNamespaceError(
                f"graphics {graphics_id}: unknown affine table {affine_pointer:#010x}"
            )
        affine_key = builder.add_source(
            affine_pointer, affine_count * 4, f"affine_table::{graphics_id}"
        )
        builder.point(info_key, 0x20, affine_key)
        for index in range(affine_count):
            pointer = _u32_ptr(
                clean, affine_pointer + index * 4,
                f"affine pointer {graphics_id}/{index}",
            )
            command_raw = _affine_commands(
                clean, pointer, f"affine animation {graphics_id}/{index}"
            )
            command_key = builder.add_source(
                pointer, len(command_raw), f"affine_commands::{graphics_id}/{index}"
            )
            builder.point(affine_key, index * 4, command_key)

    # Preserve every existing Stage60 object palette entry, then append clean
    # Kanto palettes under private tags and an explicit 0x11FF terminator.
    palette_raw = bytearray()
    for pointer, tag, _ in _palette_entries(stage60):
        palette_raw.extend(struct.pack("<IHH", pointer, tag, 0))
    clone_palette_rows: list[tuple[int, int, int]] = []
    for source_tag, runtime_tag in sorted(palette_remap.items()):
        if source_tag not in clean_palettes:
            raise GraphicsNamespaceError(
                f"clean palette tag cannot be cloned: {source_tag:#06x}"
            )
        source_pointer, palette = clean_palettes[source_tag]
        row_offset = len(palette_raw)
        palette_raw.extend(struct.pack("<IHH", source_pointer, runtime_tag, 0))
        clone_palette_rows.append((row_offset, source_pointer, len(palette)))
    palette_raw.extend(struct.pack("<IHH", 0, OBJECT_PALETTE_SENTINEL, 0))
    palette_table_key = builder.add_synthetic(
        "synthetic::extended_object_palette_table", bytes(palette_raw),
        "extended_object_palette_table",
    )
    for row_offset, source_pointer, size in clone_palette_rows:
        palette_key = builder.add_source(
            source_pointer, size, f"object_palette::{source_pointer:#010x}"
        )
        builder.point(palette_table_key, row_offset, palette_key)

    nodes = builder.freeze()
    source_closure_hash = _sha(_stable({
        str(graphics_id): clean_signatures[graphics_id].sha256
        for graphics_id in mismatch_ids
    }))
    return RelocatableGraphicsPayload(
        nodes=nodes,
        graphics_info_nodes=dict(info_nodes),
        palette_table_node=palette_table_key,
        palette_tag_remap=dict(palette_remap),
        source_closure_sha256=source_closure_hash,
    )


def _canonical_digest(rows: Mapping[str, bytes]) -> str:
    digest = hashlib.sha256()
    names = sorted(
        name for name in rows
        if name.startswith("generated/maps/kanto/KANTO_") and name.endswith(".json")
    )
    for name in names:
        raw = rows[name]
        digest.update(Path(name).name.encode())
        digest.update(b"\0")
        digest.update(len(raw).to_bytes(8, "little"))
        digest.update(raw)
    return digest.hexdigest()


def _load_canonical(root: Path) -> list[dict[str, Any]]:
    importer_path = root / "tools/map_import/full_kanto_import.py"
    _file_sha(importer_path, CANONICAL_IMPORTER_SHA256, "canonical importer")
    constants_path = root / "vendor/upstream/pokefirered/include/constants/event_objects.h"
    _file_sha(constants_path, EVENT_OBJECT_CONSTANTS_SHA256,
              "event object constants")
    from tools.map_import.full_kanto_import import build_outputs

    outputs = build_outputs(root)
    digest = _canonical_digest(outputs)
    if digest != CANONICAL_MAPS_SHA256:
        raise GraphicsNamespaceError(
            f"canonical map aggregate differs: {digest} != {CANONICAL_MAPS_SHA256}"
        )
    rows: list[dict[str, Any]] = []
    for name, raw in outputs.items():
        if not name.startswith("generated/maps/kanto/KANTO_") \
                or not name.endswith(".json"):
            continue
        disk_path = root / name
        if not disk_path.is_file() or disk_path.read_bytes() != raw:
            raise GraphicsNamespaceError(f"canonical generated file differs: {name}")
        value = json.loads(raw)
        header = value.get("map_header", {})
        if header.get("scope_decision") in {"INCLUDE", "REBUILD"}:
            rows.append(value)
    rows.sort(key=lambda row: (
        int(row["map_header"]["group_id"]),
        int(row["map_header"]["map_id"]),
        str(row["map_header"]["map_key"]),
    ))
    coords = {
        (int(row["map_header"]["group_id"]), int(row["map_header"]["map_id"]))
        for row in rows
    }
    if len(rows) != 253 or len(coords) != 253:
        raise GraphicsNamespaceError(
            f"canonical Kanto map cardinality differs: {len(rows)}/{len(coords)}"
        )
    return rows


def _map_object_records(
    stage60: bytes, canonical: Sequence[Mapping[str, Any]],
) -> tuple[ObjectRecordPlan, ...]:
    root_pointer = _u32_at(stage60, MAP_GROUPS_POINTER_SITE, "gMapGroups pointer")
    root = _rom_offset(stage60, root_pointer, 99 * 4, "gMapGroups")
    rows: list[ObjectRecordPlan] = []
    for map_row in canonical:
        header = map_row["map_header"]
        group = int(header["group_id"])
        number = int(header["map_id"])
        group_pointer = _u32_at(stage60, root + group * 4, f"map group {group}")
        group_offset = _rom_offset(
            stage60, group_pointer, (number + 1) * 4, f"map group {group}"
        )
        header_pointer = _u32_at(
            stage60, group_offset + number * 4, f"map header {group}/{number}"
        )
        header_offset = _rom_offset(
            stage60, header_pointer, 0x1C, f"map header {group}/{number}"
        )
        events_pointer = _u32_at(
            stage60, header_offset + 4, f"events {group}/{number}"
        )
        events = _rom_offset(stage60, events_pointer, 0x14,
                             f"events {group}/{number}")
        count = stage60[events]
        if not count:
            continue
        objects_pointer = _u32_at(
            stage60, events + 4, f"object array {group}/{number}"
        )
        objects = _rom_offset(
            stage60, objects_pointer, count * OBJECT_EVENT_SIZE,
            f"object array {group}/{number}",
        )
        for index in range(count):
            offset = objects + index * OBJECT_EVENT_SIZE
            record = stage60[offset:offset + OBJECT_EVENT_SIZE]
            graphics_id = record[1]
            rows.append(ObjectRecordPlan(
                map_key=str(header["map_key"]),
                group=group,
                map_number=number,
                object_index=index,
                local_id=record[0],
                record_offset=offset,
                record_preimage=record,
                source_graphics_id=graphics_id,
                runtime_graphics_id=graphics_id,
                action="UNCLASSIFIED",
            ))
    if len(rows) != 1060:
        raise GraphicsNamespaceError(
            f"live imported Kanto object cardinality differs: {len(rows)} != 1060"
        )
    return tuple(rows)


def build_graphics_namespace_plan(
    root: Path,
    *,
    clone_graphics_id_start: int = CLONE_GRAPHICS_ID_START,
    clone_graphics_id_end: int = CLONE_GRAPHICS_ID_END,
    reserved_graphics_ids: Iterable[int] = RESERVED_GRAPHICS_IDS,
    palette_tag_start: int = CLONE_PALETTE_TAG_START,
    palette_tag_end: int = CLONE_PALETTE_TAG_END,
    reserved_palette_tags: Iterable[int] = (),
) -> GraphicsNamespacePlan:
    """Build the exact Stage60 -> Stage61 Kanto graphics namespace plan."""
    root = Path(root)
    clean = _file_sha(
        root / "inputs/private/FireRed_JPN_Rev0_clean.gba",
        CLEAN_ROM_SHA256,
        "clean FireRed Japanese Rev.0 ROM",
    )
    stage60 = _file_sha(
        root / "build/stages/60_wild_species_root_repair.gba",
        STAGE60_ROM_SHA256,
        "Stage60 ROM",
    )
    _audit_table_consumers(stage60)
    canonical = _load_canonical(root)
    preliminary = _map_object_records(stage60, canonical)
    used_ids = tuple(sorted({row.source_graphics_id for row in preliminary}))
    if len(used_ids) != 106:
        raise GraphicsNamespaceError(
            f"live Kanto graphics ID cardinality differs: {len(used_ids)} != 106"
        )
    unexpected_static = [
        value for value in used_ids
        if OBJECT_GRAPHICS_COUNT <= value < DYNAMIC_GRAPHICS_ID_START
    ]
    if unexpected_static:
        raise GraphicsNamespaceError(
            f"Stage60 already uses project static graphics IDs: {unexpected_static}"
        )

    clean_signatures: dict[int, ClosureSignature] = {}
    stage_signatures: dict[int, ClosureSignature] = {}
    mismatch: list[int] = []
    for graphics_id in used_ids:
        if graphics_id >= DYNAMIC_GRAPHICS_ID_START:
            continue
        clean_signature = extract_graphics_closure_signature(clean, graphics_id)
        clean_signatures[graphics_id] = clean_signature
        try:
            stage_signature = extract_graphics_closure_signature(
                stage60, graphics_id, schema_rom=clean
            )
        except GraphicsNamespaceError as exc:
            # An unresolved Stage60 target is itself a semantic mismatch.  Keep
            # the exact failure in a deterministic signature while the clean
            # closure remains the only source used for materialization.
            components = {"unresolved_stage60_closure": str(exc)}
            stage_signature = ClosureSignature(
                graphics_id=graphics_id,
                sha256=_sha(_stable(components)),
                components=components,
            )
        stage_signatures[graphics_id] = stage_signature
        if clean_signature.sha256 != stage_signature.sha256:
            mismatch.append(graphics_id)

    graphics_remap = allocate_graphics_ids(
        mismatch,
        allocation_start=clone_graphics_id_start,
        allocation_end=clone_graphics_id_end,
        reserved_ids=reserved_graphics_ids,
    )
    mismatch_set = set(mismatch)
    finalized: list[ObjectRecordPlan] = []
    for row in preliminary:
        if row.source_graphics_id in mismatch_set:
            action = "REMAP_CLEAN_CLOSURE"
            runtime_id = graphics_remap[row.source_graphics_id]
        elif row.source_graphics_id >= DYNAMIC_GRAPHICS_ID_START:
            action = "PRESERVE_DYNAMIC_GRAPHICS_ID"
            runtime_id = row.source_graphics_id
        else:
            action = "KEEP_IDENTICAL_CLOSURE"
            runtime_id = row.source_graphics_id
        finalized.append(ObjectRecordPlan(
            **{
                **row.__dict__,
                "runtime_graphics_id": runtime_id,
                "action": action,
            }
        ))
    if len(finalized) != 1060 or any(row.action == "UNCLASSIFIED" for row in finalized):
        raise GraphicsNamespaceError("not every live Kanto object was classified")

    payload = _build_payload(
        clean, stage60, mismatch, clean_signatures,
        palette_tag_start=palette_tag_start,
        palette_tag_end=palette_tag_end,
        reserved_palette_tags=reserved_palette_tags,
    )
    stage_pointers = struct.unpack(
        f"<{OBJECT_GRAPHICS_COUNT}I",
        _read(stage60, OBJECT_GRAPHICS_TABLE, OBJECT_GRAPHICS_COUNT * 4,
              "Stage60 graphics pointer table"),
    )
    return GraphicsNamespacePlan(
        clean_rom_sha256=_sha(clean),
        stage60_rom_sha256=_sha(stage60),
        canonical_importer_sha256=CANONICAL_IMPORTER_SHA256,
        canonical_maps_sha256=CANONICAL_MAPS_SHA256,
        map_count=len(canonical),
        object_records=tuple(finalized),
        used_graphics_ids=used_ids,
        mismatched_graphics_ids=tuple(mismatch),
        closure_signatures_clean=dict(clean_signatures),
        closure_signatures_stage60=dict(stage_signatures),
        graphics_id_remap=dict(graphics_remap),
        payload=payload,
        stage60_graphics_pointers=tuple(stage_pointers),
        stage60_rom=stage60,
    )


__all__ = [
    "AFFINE_TABLE_COUNTS",
    "CANONICAL_IMPORTER_SHA256",
    "CANONICAL_MAPS_SHA256",
    "CLEAN_ROM_SHA256",
    "CLONE_GRAPHICS_ID_END",
    "CLONE_GRAPHICS_ID_START",
    "CLONE_PALETTE_TAG_END",
    "CLONE_PALETTE_TAG_START",
    "ClosureSignature",
    "DYNAMIC_GRAPHICS_ID_START",
    "GBA_BASE",
    "GBA_ROM_END",
    "GraphicsNamespaceError",
    "GraphicsNamespacePlan",
    "MaterializedGraphicsNamespace",
    "OBJECT_EVENT_SIZE",
    "OBJECT_GRAPHICS_COUNT",
    "OBJECT_GRAPHICS_INFO_SIZE",
    "OBJECT_GRAPHICS_POINTER_SITES",
    "OBJECT_GRAPHICS_STATIC_LIMIT_SITE",
    "OBJECT_GRAPHICS_TABLE",
    "OBJECT_PALETTE_POINTER_SITES",
    "OBJECT_PALETTE_SENTINEL",
    "OBJECT_PALETTE_TABLE",
    "ObjectRecordPlan",
    "PayloadFixup",
    "PayloadNode",
    "PointerPatch",
    "RESERVED_GRAPHICS_IDS",
    "RelocatableGraphicsPayload",
    "STAGE60_ROM_SHA256",
    "allocate_graphics_ids",
    "build_graphics_namespace_plan",
    "extract_graphics_closure_signature",
]
