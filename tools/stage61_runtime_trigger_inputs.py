"""Stage61全event ownerの実field入力経路をfinal ROMから生成する。

このmoduleはscript rootを直接呼ぶためのfixtureを生成しない。Object/BG/Coordは
final event recordとfinal collisionを読み、Mapは実在するstock map-load経路、
Commonは実在する非Common ownerから到達可能なcallstd bytecodeへ結び付ける。
``owner_paths`` は :func:`tools.stage61_interaction_oracle.
_validated_runtime_trigger_path` のexact schemaだけを持つ。runnerに必要な歩行方向は
path自体へ持たせ、追加provenanceだけを ``owner_path_evidence`` に分離する。

Productionでは6417 ownerのうちruntime必須5416件だけを ``owner_paths`` へ入れ、
残り1001件は ``structural_nontrigger_owner_ids`` へ一対一で列挙する。NULL root
1000件と参照のないstandard-script index 7はそれぞれROM-boundな
``structural_nontrigger_evidence`` を持つ。入力が未完な
場合、既定の ``require_complete=True`` はartifactを返さずfail closedする。
調査時だけFalseにすると、生成できたpathと全unresolvedを同じschemaで確認できる。
"""

from __future__ import annotations

import hashlib
import json
import struct
from collections import Counter, defaultdict, deque
from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Iterable, Mapping, NoReturn, Sequence


ROM_BASE = 0x08000000
MAP_GROUPS_POINTER_SITE = 0x54B0C

EXPECTED_OWNER_COUNT = 6417
EXPECTED_RUNTIME_REQUIRED_COUNT = 5416
EXPECTED_STRUCTURAL_NONTRIGGER_COUNT = 1001
EXPECTED_OWNER_KIND_COUNTS = {
    "OBJECT": 3112, "BG": 1436, "COORD": 1231,
    "MAP": 628, "COMMON": 10,
}
EXPECTED_RUNTIME_KIND_COUNTS = {
    "OBJECT": 3108, "BG": 1023, "COORD": 648,
    "MAP": 628, "COMMON": 9,
}
EXPECTED_STRUCTURAL_KIND_COUNTS = {
    "OBJECT": 4, "BG": 413, "COORD": 583, "COMMON": 1,
}
EXPECTED_MAP_SEED_KIND_COUNTS = {
    "stock_warp": 590,
    "stock_connection": 0,
    "engine_teleport": 38,
}
_MAP_SEED_KINDS = tuple(EXPECTED_MAP_SEED_KIND_COUNTS)

# Inventoryのruntime_rootはROM tableに非NULL rootが存在するという構造事実。
# 実行scopeを分類する前は未参照のCOMMON 7も含む。
_EXPECTED_INVENTORY_RUNTIME_ROOT_COUNT = 5417
_EXPECTED_INVENTORY_NULL_ROOT_COUNT = 1000
_EXPECTED_INVENTORY_RUNTIME_KIND_COUNTS = {
    "OBJECT": 3108, "BG": 1023, "COORD": 648,
    "MAP": 628, "COMMON": 10,
}
_EXPECTED_INVENTORY_NULL_KIND_COUNTS = {
    "OBJECT": 4, "BG": 413, "COORD": 583,
}

STANDARD_SCRIPT_TABLE = 0x08163758
STANDARD_SCRIPT_COUNT = 10
UNREFERENCED_STANDARD_OWNER_ID = "COMMON:STANDARD:007"

_CARDINAL_DELTAS = {
    "UP": (0, -1), "DOWN": (0, 1),
    "LEFT": (-1, 0), "RIGHT": (1, 0),
}
_OPPOSITE = {
    "UP": "DOWN", "DOWN": "UP", "LEFT": "RIGHT", "RIGHT": "LEFT",
}
_FACE_STANCE_DELTA = {
    # Playerがこの方向を向いた時、event tileから見たstance位置。
    "UP": (0, 1), "DOWN": (0, -1),
    "RIGHT": (-1, 0), "LEFT": (1, 0),
}
_BG_REQUIRED_DIRECTION = {1: "UP", 2: "DOWN", 3: "RIGHT", 4: "LEFT"}
_FACE_DIRECTION_ORDER = ("UP", "LEFT", "RIGHT", "DOWN")
_WARP_BEHAVIORS = frozenset(range(0x60, 0x70)) | {0x71}
_MAP_STOCK_WARP_TAGS = frozenset({1, 2, 3, 4})
_MAP_FIELD_RETURN_TAGS = frozenset({5, 7})


class Stage61RuntimeTriggerInputsError(RuntimeError):
    """Runtime trigger producerのprovenance/geometry不整合。"""


def _fail(message: str) -> NoReturn:
    raise Stage61RuntimeTriggerInputsError(message)


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _stable(value: Any) -> bytes:
    return (
        json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        ) + "\n"
    ).encode("utf-8")


def _self_hash_without(document: Mapping[str, Any], field: str) -> str:
    """Hash a JSON-compatible document with one self-hash field omitted."""

    return _sha(_stable({
        key: value for key, value in document.items() if key != field
    }))


def _address(value: Any, label: str) -> int:
    if isinstance(value, str):
        try:
            value = int(value, 0)
        except ValueError:
            _fail(f"{label}: address文字列不正")
    if isinstance(value, bool) or not isinstance(value, int):
        _fail(f"{label}: address型不正")
    return value


def _offset(rom: bytes, address: Any, size: int, label: str) -> int:
    value = _address(address, label)
    offset = value - ROM_BASE
    if size < 0 or offset < 0 or offset + size > len(rom):
        _fail(f"{label}: ROM範囲外: 0x{value:08X}+{size}")
    return offset


def _read(rom: bytes, address: Any, size: int, label: str) -> bytes:
    at = _offset(rom, address, size, label)
    return rom[at:at + size]


def _u16(raw: bytes, offset: int = 0) -> int:
    return struct.unpack_from("<H", raw, offset)[0]


def _u32(raw: bytes, offset: int = 0) -> int:
    return struct.unpack_from("<I", raw, offset)[0]


def _u32_at(rom: bytes, offset: int, label: str) -> int:
    if offset < 0 or offset + 4 > len(rom):
        _fail(f"{label}: u32 ROM offset範囲外")
    return struct.unpack_from("<I", rom, offset)[0]


def _point(value: Any, label: str) -> tuple[int, int]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)) \
            or len(value) != 2 or any(
                isinstance(item, bool) or not isinstance(item, int)
                for item in value
            ):
        _fail(f"{label}: point不正")
    return int(value[0]), int(value[1])


def _point_dict(point: tuple[int, int]) -> dict[str, int]:
    return {"x": point[0], "y": point[1]}


def _parse_physical_map(value: Any, label: str) -> tuple[int, int]:
    if not isinstance(value, str):
        _fail(f"{label}: physical_map不正")
    fields = value.split("/")
    if len(fields) != 2 or any(not field.isdigit() for field in fields):
        _fail(f"{label}: physical_map書式不正")
    group, number = map(int, fields)
    if not 0 <= group <= 0xFF or not 0 <= number <= 0xFF:
        _fail(f"{label}: physical_map範囲外")
    return group, number


@dataclass(frozen=True)
class _Geometry:
    width: int
    height: int
    blocks: tuple[int, ...]
    behaviors: tuple[int, ...]
    layout_address: int
    blockdata_address: int

    def in_bounds(self, point: tuple[int, int]) -> bool:
        x, y = point
        return 0 <= x < self.width and 0 <= y < self.height

    def collision_zero(self, point: tuple[int, int]) -> bool:
        if not self.in_bounds(point):
            return False
        x, y = point
        return ((self.blocks[y * self.width + x] >> 10) & 3) == 0

    def collision(self, point: tuple[int, int]) -> int:
        if not self.in_bounds(point):
            return -1
        x, y = point
        return (self.blocks[y * self.width + x] >> 10) & 3

    def elevation(self, point: tuple[int, int]) -> int:
        if not self.in_bounds(point):
            return -1
        x, y = point
        return (self.blocks[y * self.width + x] >> 12) & 0xF

    def behavior(self, point: tuple[int, int]) -> int:
        if not self.in_bounds(point):
            return -1
        x, y = point
        return self.behaviors[y * self.width + x]


@dataclass(frozen=True)
class _Warp:
    group: int
    map: int
    index: int
    address: int
    x: int
    y: int
    elevation: int
    destination_warp: int
    destination_map: int
    destination_group: int
    raw: bytes


@dataclass(frozen=True)
class _MapState:
    group: int
    map: int
    header_address: int
    event_header_address: int | None
    geometry: _Geometry
    objects: tuple[bytes, ...]
    warps: tuple[_Warp, ...]
    coords: tuple[bytes, ...]
    backgrounds: tuple[bytes, ...]
    runtime_object_positions: tuple[
        tuple[int, tuple[int, int]], ...
    ] = ()

    @property
    def object_tiles(self) -> frozenset[tuple[int, int]]:
        # Some permanent map-script actors deliberately move away from their
        # dormant object-template coordinate.  The placement audit is the
        # final runtime source of truth for those object indices; retaining
        # both coordinates here creates a blocker which does not exist in the
        # loaded field and invalidates otherwise real walk paths.
        by_index = {
            index: struct.unpack_from("<hh", raw, 4)
            for index, raw in enumerate(self.objects)
        }
        by_index.update(dict(self.runtime_object_positions))
        return frozenset(by_index.values())

    @property
    def warp_tiles(self) -> frozenset[tuple[int, int]]:
        return frozenset((row.x, row.y) for row in self.warps)

    @property
    def coord_tiles(self) -> frozenset[tuple[int, int]]:
        return frozenset(
            struct.unpack_from("<HH", raw, 0) for raw in self.coords
        )

    @property
    def reserved_tiles(self) -> frozenset[tuple[int, int]]:
        result = {(row.x, row.y) for row in self.warps}
        result.update(struct.unpack_from("<HH", raw, 0) for raw in self.coords)
        result.update(
            struct.unpack_from("<HH", raw, 0) for raw in self.backgrounds
        )
        return frozenset(result)


@dataclass(frozen=True)
class _WarpMapState:
    """Warp scan view which never depends on dormant COORD/BG arrays.

    A malformed non-WARP pointer on an otherwise unrelated map must not abort
    the scan for every destination map.  OBJECT is decoded independently only
    to reject occupied predecessor tiles; when that array is malformed the
    source map remains readable but is not eligible as a physical predecessor.
    """

    group: int
    map: int
    geometry: _Geometry
    warps: tuple[_Warp, ...]
    object_tiles: frozenset[tuple[int, int]]
    object_array_usable: bool
    object_array_diagnostic: str | None

    @property
    def warp_tiles(self) -> frozenset[tuple[int, int]]:
        return frozenset((row.x, row.y) for row in self.warps)


class _FinalRomMaps:
    """final ROMだけからlayout/event/foreign WarpEventを復元するcache。"""

    def __init__(
        self,
        rom: bytes,
        coordinates: Iterable[tuple[int, int]],
        runtime_object_positions: Mapping[
            tuple[int, int], Mapping[int, tuple[int, int]]
        ],
    ):
        self.rom = rom
        self.coordinates = tuple(sorted(set(coordinates)))
        self.runtime_object_positions = {
            key: dict(rows) for key, rows in runtime_object_positions.items()
        }
        self._states: dict[tuple[int, int], _MapState] = {}
        self._warp_states: dict[tuple[int, int], _WarpMapState] = {}
        self.stock_scan_diagnostics: dict[tuple[int, int], dict[str, Any]] = {}

    def _map_header(self, group: int, number: int) -> tuple[int, int]:
        root_pointer = _u32_at(
            self.rom, MAP_GROUPS_POINTER_SITE, "gMapGroups pointer",
        )
        root = _offset(
            self.rom, root_pointer, (group + 1) * 4, "gMapGroups",
        )
        group_pointer = _u32_at(
            self.rom, root + group * 4, f"map group {group}",
        )
        group_at = _offset(
            self.rom, group_pointer, (number + 1) * 4,
            f"map group {group} table",
        )
        header_pointer = _u32_at(
            self.rom, group_at + number * 4, f"map header {group}/{number}",
        )
        return header_pointer, _offset(
            self.rom, header_pointer, 0x1C, f"map header {group}/{number}",
        )

    def _geometry(self, header: int, label: str) -> _Geometry:
        layout_address = _u32_at(self.rom, header, f"{label} layout pointer")
        layout = _offset(self.rom, layout_address, 0x18, f"{label} layout")
        width = _u32_at(self.rom, layout, f"{label} width")
        height = _u32_at(self.rom, layout + 4, f"{label} height")
        if not 0 < width <= 1024 or not 0 < height <= 1024 \
                or width * height > 0x100000:
            _fail(f"{label}: map dimensions不正:{width}x{height}")
        block_pointer = _u32_at(self.rom, layout + 12, f"{label} blocks")
        block_at = _offset(
            self.rom, block_pointer, width * height * 2, f"{label} blocks",
        )
        blocks = struct.unpack_from(
            f"<{width * height}H", self.rom, block_at,
        )
        attribute_offsets: list[int] = []
        for name, site in (("primary", layout + 16), ("secondary", layout + 20)):
            tileset_pointer = _u32_at(
                self.rom, site, f"{label} {name} tileset pointer",
            )
            tileset = _offset(
                self.rom, tileset_pointer, 0x18, f"{label} {name} tileset",
            )
            attribute_pointer = _u32_at(
                self.rom, tileset + 20, f"{label} {name} attributes pointer",
            )
            # Either table can be selected by a 10-bit metatile ID.  The
            # source builder pins 640 entries for both, so use the same bound.
            attribute_offsets.append(_offset(
                self.rom, attribute_pointer, 640 * 4,
                f"{label} {name} attributes",
            ))
        behaviors = []
        for block in blocks:
            metatile = block & 0x3FF
            table = attribute_offsets[0] if metatile < 640 \
                else attribute_offsets[1]
            index = metatile if metatile < 640 else metatile - 640
            behaviors.append(
                _u32_at(self.rom, table + index * 4, f"{label} behavior")
                & 0x1FF
            )
        return _Geometry(
            width, height, tuple(blocks), tuple(behaviors), layout_address,
            block_pointer,
        )

    def state(self, group: int, number: int) -> _MapState:
        key = (group, number)
        cached = self._states.get(key)
        if cached is not None:
            return cached
        header_address, header = self._map_header(group, number)
        label = f"map {group:03d}/{number:03d}"
        geometry = self._geometry(header, label)
        event_pointer = _u32_at(self.rom, header + 4, f"{label} event pointer")
        if event_pointer in (0, 0xFFFFFFFF):
            state = _MapState(
                group, number, header_address, None, geometry,
                (), (), (), (),
            )
            self._states[key] = state
            return state
        event = _offset(self.rom, event_pointer, 0x14, f"{label} event header")
        object_count, warp_count, coord_count, bg_count = self.rom[event:event + 4]
        pointers = struct.unpack_from("<IIII", self.rom, event + 4)

        def array(pointer: int, count: int, size: int, name: str) -> tuple[bytes, ...]:
            if count == 0:
                return ()
            at = _offset(
                self.rom, pointer, count * size, f"{label} {name} array",
            )
            return tuple(
                self.rom[at + index * size:at + (index + 1) * size]
                for index in range(count)
            )

        objects = array(pointers[0], object_count, 0x18, "OBJECT")
        warp_raw = array(pointers[1], warp_count, 8, "WARP")
        coords = array(pointers[2], coord_count, 0x10, "COORD")
        backgrounds = array(pointers[3], bg_count, 0x0C, "BG")
        warps = tuple(
            _Warp(
                group=group, map=number, index=index,
                address=pointers[1] + index * 8,
                x=struct.unpack_from("<h", raw, 0)[0],
                y=struct.unpack_from("<h", raw, 2)[0],
                elevation=raw[4], destination_warp=raw[5],
                destination_map=raw[6], destination_group=raw[7], raw=raw,
            )
            for index, raw in enumerate(warp_raw)
        )
        state = _MapState(
            group, number, header_address, event_pointer, geometry,
            objects, warps, coords, backgrounds,
            tuple(sorted(
                self.runtime_object_positions.get(key, {}).items()
            )),
        )
        self._states[key] = state
        return state

    def warp_state(self, group: int, number: int) -> _WarpMapState:
        """Decode WARP independently and keep non-WARP failures local."""

        key = (group, number)
        cached = self._warp_states.get(key)
        if cached is not None:
            return cached
        _header_address, header = self._map_header(group, number)
        label = f"map {group:03d}/{number:03d}"
        geometry = self._geometry(header, label)
        event_pointer = _u32_at(self.rom, header + 4, f"{label} event pointer")
        if event_pointer in (0, 0xFFFFFFFF):
            result = _WarpMapState(
                group, number, geometry, (), frozenset(), True, None,
            )
            self._warp_states[key] = result
            return result
        event = _offset(self.rom, event_pointer, 0x14, f"{label} event header")
        object_count, warp_count = self.rom[event:event + 2]
        object_pointer, warp_pointer = struct.unpack_from("<II", self.rom, event + 4)

        if warp_count:
            warp_at = _offset(
                self.rom, warp_pointer, warp_count * 8, f"{label} WARP array",
            )
            warp_raw = tuple(
                self.rom[warp_at + index * 8:warp_at + (index + 1) * 8]
                for index in range(warp_count)
            )
        else:
            warp_raw = ()
        warps = tuple(
            _Warp(
                group=group, map=number, index=index,
                address=warp_pointer + index * 8,
                x=struct.unpack_from("<h", raw, 0)[0],
                y=struct.unpack_from("<h", raw, 2)[0],
                elevation=raw[4], destination_warp=raw[5],
                destination_map=raw[6], destination_group=raw[7], raw=raw,
            )
            for index, raw in enumerate(warp_raw)
        )

        object_positions: dict[int, tuple[int, int]] = {}
        object_usable = True
        object_diagnostic: str | None = None
        if object_count:
            try:
                object_at = _offset(
                    self.rom, object_pointer, object_count * 0x18,
                    f"{label} OBJECT array",
                )
                object_positions.update({
                    index: struct.unpack_from(
                        "<hh", self.rom, object_at + index * 0x18 + 4,
                    )
                    for index in range(object_count)
                })
            except Stage61RuntimeTriggerInputsError as exc:
                object_usable = False
                object_diagnostic = str(exc)
        runtime_positions = self.runtime_object_positions.get(key, {})
        object_positions.update(runtime_positions)
        # A malformed raw array is acceptable only when the final placement
        # audit accounts for every runtime object slot declared by the header.
        if not object_usable and len(runtime_positions) >= object_count:
            object_usable = True
        result = _WarpMapState(
            group, number, geometry, warps,
            frozenset(object_positions.values()), object_usable,
            object_diagnostic,
        )
        self._warp_states[key] = result
        return result

    def stock_warps_into(
        self, destination: tuple[int, int], *, rom_sha256: str,
    ) -> list[tuple[dict[str, Any], dict[str, Any]]]:
        """Return exact foreign warp plus physical predecessor evidence."""

        target = self.warp_state(*destination)
        diagnostic: dict[str, Any] = {
            "destination": list(destination),
            "foreign_warp_reference_count": 0,
            "usable_stock_warp_count": 0,
            "invalid_source_warp_view_count": 0,
            "unusable_reason_counts": {},
        }
        reason_counts: Counter[str] = Counter()
        candidates: list[tuple[tuple[Any, ...], dict[str, Any], dict[str, Any]]] = []
        for source_key in self.coordinates:
            try:
                source = self.warp_state(*source_key)
            except Stage61RuntimeTriggerInputsError:
                # Invalid WARP/layout data invalidates this source only.  It
                # must never make all 628 destination owners fail together.
                diagnostic["invalid_source_warp_view_count"] += 1
                continue
            for warp in source.warps:
                if (warp.destination_group, warp.destination_map) != destination:
                    continue
                diagnostic["foreign_warp_reference_count"] += 1
                if not source.object_array_usable:
                    # We cannot prove the physical predecessor object-free.
                    # Continue scanning other exact foreign WarpEvents.
                    reason_counts["SOURCE_OBJECT_OCCUPANCY_UNPROVEN"] += 1
                    continue
                trigger = (warp.x, warp.y)
                if not source.geometry.in_bounds(trigger):
                    reason_counts["TRIGGER_OUT_OF_BOUNDS"] += 1
                    continue
                behavior = source.geometry.behavior(trigger)
                if behavior == 0x69:
                    predecessor_rows = [((warp.x, warp.y + 1), "UP")]
                    trigger_usable = True
                elif behavior in _WARP_BEHAVIORS \
                        and source.geometry.collision_zero(trigger):
                    predecessor_rows = []
                    for direction in _FACE_DIRECTION_ORDER:
                        dx, dy = _FACE_STANCE_DELTA[direction]
                        predecessor_rows.append(((warp.x + dx, warp.y + dy), direction))
                    trigger_usable = True
                else:
                    predecessor_rows = []
                    trigger_usable = False
                if not trigger_usable:
                    reason_counts[
                        "TRIGGER_BEHAVIOR_OR_COLLISION_NOT_STOCK_STEP"
                    ] += 1
                    continue
                predecessor_rows = [
                    (point, direction) for point, direction in predecessor_rows
                    if source.geometry.collision_zero(point)
                    and point not in source.object_tiles
                    and point not in source.warp_tiles - {trigger}
                ]
                if not predecessor_rows:
                    reason_counts["NO_FREE_CARDINAL_PREDECESSOR"] += 1
                    continue
                if warp.destination_warp < len(target.warps):
                    arrival = (
                        target.warps[warp.destination_warp].x,
                        target.warps[warp.destination_warp].y,
                    )
                    arrival_basis = "EXACT_DESTINATION_WARP_EVENT"
                else:
                    arrival = (
                        target.geometry.width // 2,
                        target.geometry.height // 2,
                    )
                    arrival_basis = "ENGINE_INVALID_WARP_ID_MAP_CENTER_FALLBACK"
                if not target.geometry.in_bounds(arrival):
                    reason_counts["ARRIVAL_OUT_OF_BOUNDS"] += 1
                    continue
                for predecessor, direction in predecessor_rows:
                    raw_sha = _sha(warp.raw)
                    path = {
                        "source": {
                            "group": warp.group, "map": warp.map,
                            "warp_id": warp.index,
                        },
                        "predecessor_tile": _point_dict(predecessor),
                        "trigger_tile": _point_dict(trigger),
                        "trigger_key": direction,
                        "destination": {
                            "group": destination[0], "map": destination[1],
                            "warp_id": warp.destination_warp,
                        },
                        "arrival_tile": _point_dict(arrival),
                        "connection_or_warp_record_address": warp.address,
                        "source_provenance": {
                            "kind": "FINAL_ROM_FOREIGN_WARP_EVENT_WITH_REAL_STEP",
                            "rom_sha256": rom_sha256,
                            "record_address": f"0x{warp.address:08X}",
                            "record_raw_sha256": raw_sha,
                            "record_raw_hex": warp.raw.hex(),
                            "source_trigger_behavior": behavior,
                            "arrival_basis": arrival_basis,
                            "array_decode_scope": "WARP_INDEPENDENT_OBJECT_FOR_PREDECESSOR_ONLY",
                            "dormant_coord_bg_arrays_not_decoded": True,
                        },
                    }
                    evidence = {
                        "kind": "STOCK_WARP_PHYSICAL_PREDECESSOR",
                        "source_map": [warp.group, warp.map],
                        "source_warp_id": warp.index,
                        "predecessor_tile": list(predecessor),
                        "trigger_tile": list(trigger),
                        "trigger_key": direction,
                        "source_trigger_collision_zero": (
                            source.geometry.collision_zero(trigger)
                        ),
                        "source_trigger_behavior": behavior,
                        "predecessor_collision_zero": True,
                        "predecessor_object_free": True,
                        "predecessor_event_free": True,
                        "destination_map": list(destination),
                        "destination_warp_id": warp.destination_warp,
                        "arrival_tile": list(arrival),
                        "record_address": f"0x{warp.address:08X}",
                        "record_raw_sha256": raw_sha,
                        "array_decode_scope": "WARP_INDEPENDENT_OBJECT_FOR_PREDECESSOR_ONLY",
                    }
                    order = (
                        warp.group, warp.map, warp.index,
                        _FACE_DIRECTION_ORDER.index(direction),
                        predecessor[1], predecessor[0],
                    )
                    candidates.append((order, path, evidence))
        candidates.sort(key=lambda row: row[0])
        diagnostic["usable_stock_warp_count"] = len(candidates)
        diagnostic["unusable_reason_counts"] = dict(sorted(reason_counts.items()))
        self.stock_scan_diagnostics[destination] = diagnostic
        return [(path, evidence) for _order, path, evidence in candidates]


def _inventory_inputs(
    final_rom: bytes,
    event_owner_inventory: Mapping[str, Any],
    *,
    require_canonical_counts: bool,
) -> tuple[
    list[dict[str, Any]], dict[str, dict[str, Any]],
    list[tuple[int, int]], dict[tuple[int, int], Mapping[str, Any]],
]:
    rom_sha = _sha(final_rom)
    if not isinstance(event_owner_inventory, Mapping) \
            or event_owner_inventory.get("schema_version") != 1 \
            or event_owner_inventory.get("kind") != \
                "STAGE61_ALL_EVENT_OWNER_INVENTORY" \
            or event_owner_inventory.get("rom_sha256") != rom_sha:
        _fail("event owner inventory/final ROM provenance不一致")
    claimed_inventory_sha = event_owner_inventory.get("inventory_sha256")
    recomputed_inventory_sha = _self_hash_without(
        event_owner_inventory, "inventory_sha256",
    )
    if not isinstance(claimed_inventory_sha, str) \
            or len(claimed_inventory_sha) != 64 \
            or claimed_inventory_sha != recomputed_inventory_sha:
        _fail(
            "event owner inventory self-hash不一致:"
            f"claimed={claimed_inventory_sha} "
            f"recomputed={recomputed_inventory_sha}"
        )
    raw = event_owner_inventory.get("owners")
    if not isinstance(raw, list) \
            or event_owner_inventory.get("owner_count") != len(raw):
        _fail("event owner inventory owner count不一致")
    owners = [deepcopy(dict(row)) for row in raw if isinstance(row, Mapping)]
    if len(owners) != len(raw):
        _fail("event owner inventory owner row不正")
    owner_by_id = {str(row.get("owner_id")): row for row in owners}
    if len(owner_by_id) != len(owners) or "None" in owner_by_id:
        _fail("event owner inventory owner ID重複/不正")
    if any(row.get("owner_kind") not in {
        "OBJECT", "BG", "COORD", "MAP", "COMMON",
    } for row in owners):
        _fail("event owner inventory owner kind不正")
    surfaces = event_owner_inventory.get("surfaces")
    if not isinstance(surfaces, list):
        _fail("event owner inventory surfaces不正")
    surface_by_map: dict[tuple[int, int], Mapping[str, Any]] = {}
    for ordinal, surface in enumerate(surfaces):
        if not isinstance(surface, Mapping):
            _fail("event owner inventory surface row不正")
        key = _parse_physical_map(
            surface.get("physical_map"), f"surface[{ordinal}]",
        )
        if key in surface_by_map:
            _fail(f"event owner inventory surface重複:{key}")
        surface_by_map[key] = surface
    if any(
        row["owner_kind"] != "COMMON"
        and (int(row["group"]), int(row["map"])) not in surface_by_map
        for row in owners
    ):
        _fail("event owner inventory ownerのsurface欠落")
    coordinates = sorted(surface_by_map)
    if require_canonical_counts:
        owner_kind_counts = dict(sorted(Counter(
            str(row["owner_kind"]) for row in owners
        ).items()))
        if len(owners) != EXPECTED_OWNER_COUNT \
                or owner_kind_counts != EXPECTED_OWNER_KIND_COUNTS \
                or len(coordinates) != 678:
            _fail(
                "production owner/map cardinality不一致:"
                f"owners={len(owners)} kinds={owner_kind_counts} "
                f"maps={len(coordinates)}"
            )
    return owners, owner_by_id, coordinates, surface_by_map


def _runtime_sets(
    final_rom: bytes, owners: Sequence[Mapping[str, Any]],
    *, require_canonical_counts: bool,
) -> tuple[list[Mapping[str, Any]], list[Mapping[str, Any]]]:
    runtime: list[Mapping[str, Any]] = []
    structural: list[Mapping[str, Any]] = []
    for owner in owners:
        if owner.get("runtime_root") is True:
            root = _address(owner.get("root"), "runtime owner root")
            if int(owner.get("raw_root", -1)) != root:
                _fail(f"runtime owner raw/root不一致:{owner['owner_id']}")
            _offset(final_rom, root, 1, f"runtime root {owner['owner_id']}")
            runtime.append(owner)
        elif owner.get("non_script_reason") == "HIDDEN_ITEM":
            if owner.get("owner_kind") != "BG" or owner.get("bg_kind") != 7 \
                    or owner.get("root") is not None:
                _fail(f"hidden item owner schema不正:{owner['owner_id']}")
            runtime.append(owner)
        else:
            if owner.get("non_script_reason") != "NULL_SCRIPT_POINTER" \
                    or int(owner.get("raw_root", -1)) != 0 \
                    or owner.get("root") is not None:
                _fail(f"structural nontrigger不明:{owner['owner_id']}")
            field = _address(
                owner.get("root_field_address"), "structural root field",
            )
            if _read(final_rom, field, 4, "structural NULL root") != b"\0" * 4:
                _fail(f"structural NULL root ROM不一致:{owner['owner_id']}")
            structural.append(owner)
    if require_canonical_counts:
        runtime_kinds = dict(sorted(Counter(
            str(row["owner_kind"]) for row in runtime
        ).items()))
        structural_kinds = dict(sorted(Counter(
            str(row["owner_kind"]) for row in structural
        ).items()))
        if len(runtime) != _EXPECTED_INVENTORY_RUNTIME_ROOT_COUNT \
                or len(structural) != _EXPECTED_INVENTORY_NULL_ROOT_COUNT \
                or runtime_kinds != _EXPECTED_INVENTORY_RUNTIME_KIND_COUNTS \
                or structural_kinds != _EXPECTED_INVENTORY_NULL_KIND_COUNTS:
            _fail(
                "production inventory-root/NULL cardinality不一致:"
                f"runtime={len(runtime)}/{runtime_kinds} "
                f"structural={len(structural)}/{structural_kinds}"
            )
    return runtime, structural


def _execution_index(
    final_rom: bytes,
    object_owners: Sequence[Mapping[str, Any]],
    npc_catalog: Mapping[str, Any],
    placement_audit: Mapping[str, Any],
) -> tuple[
    dict[str, Mapping[str, Any]],
    dict[tuple[int, int], dict[int, tuple[int, int]]],
]:
    if not isinstance(npc_catalog, Mapping) \
            or npc_catalog.get("status") != "PASS" \
            or not isinstance(npc_catalog.get("npcs"), list):
        _fail("final NPC catalog不正")
    npc_rows = {
        str(row.get("npc_id")): row for row in npc_catalog["npcs"]
        if isinstance(row, Mapping)
    }
    if len(npc_rows) != len(npc_catalog["npcs"]):
        _fail("final NPC catalog owner ID重複/不正")
    expected = {str(row["owner_id"]) for row in object_owners}
    if set(npc_rows) != expected:
        missing = sorted(expected - set(npc_rows))[:5]
        extra = sorted(set(npc_rows) - expected)[:5]
        _fail(f"final NPC catalog/runtime OBJECT集合不一致:{missing}/{extra}")
    if not isinstance(placement_audit, Mapping) \
            or placement_audit.get("status") != "PASS" \
            or placement_audit.get("rom_sha256") != _sha(final_rom) \
            or not isinstance(placement_audit.get("objects"), list):
        _fail("final placement audit/final ROM provenance不一致")
    placement = {
        str(row.get("npc_id")): row for row in placement_audit["objects"]
        if isinstance(row, Mapping)
    }
    if set(placement) != expected or len(placement) != len(
        placement_audit["objects"]
    ):
        _fail("final placement audit/runtime OBJECT集合不一致")
    result: dict[str, Mapping[str, Any]] = {}
    runtime_positions: dict[
        tuple[int, int], dict[int, tuple[int, int]]
    ] = defaultdict(dict)
    owner_by_id = {str(row["owner_id"]): row for row in object_owners}
    for owner_id in sorted(expected):
        owner = owner_by_id[owner_id]
        npc = npc_rows[owner_id]
        placed = placement[owner_id]
        execution = npc.get("interaction_execution")
        if not isinstance(execution, Mapping) \
                or execution != placed.get("interaction_execution"):
            _fail(f"final interaction_execution provenance不一致:{owner_id}")
        if npc.get("non_product_shadow_alias") \
                != placed.get("non_product_shadow_alias"):
            _fail(f"final non-product shadow alias provenance不一致:{owner_id}")
        group, number, object_index = (
            int(owner["group"]), int(owner["map"]), int(owner["index"]),
        )
        if any(int(placed.get(key, -1)) != expected_value for key, expected_value in (
            ("group", group), ("map", number), ("object_index", object_index),
        )):
            _fail(f"final placement owner identity不一致:{owner_id}")
        template = _point(
            placed.get("template_object"), f"{owner_id}.template_object",
        )
        runtime = _point(placed.get("object"), f"{owner_id}.object")
        raw = _read(
            final_rom, owner["record_address"], 0x18,
            f"{owner_id} placement template",
        )
        if struct.unpack_from("<hh", raw, 4) != template:
            _fail(f"final placement template/final ROM不一致:{owner_id}")
        basis = placed.get("interaction_object_basis")
        if not isinstance(basis, str) or not basis:
            _fail(f"final placement interaction_object_basis不正:{owner_id}")
        if basis == "FINAL_OBJECT_TEMPLATE" and runtime != template:
            _fail(f"final template-basis runtime位置不一致:{owner_id}")
        if object_index in runtime_positions[(group, number)]:
            _fail(f"final placement object index重複:{owner_id}")
        runtime_positions[(group, number)][object_index] = runtime
        merged = deepcopy(dict(npc))
        merged["_stage61_runtime_object"] = list(runtime)
        merged["_stage61_template_object"] = list(template)
        merged["_stage61_interaction_object_basis"] = basis
        result[owner_id] = merged
    return result, dict(runtime_positions)


def _walk(
    start: tuple[int, int], tokens: Sequence[str], geometry: _Geometry,
    unavailable: frozenset[tuple[int, int]], label: str,
) -> tuple[int, int]:
    cursor = start
    for token in tokens:
        if token not in _CARDINAL_DELTAS:
            _fail(f"{label}: walk token不正:{token}")
        dx, dy = _CARDINAL_DELTAS[token]
        cursor = cursor[0] + dx, cursor[1] + dy
        if not geometry.collision_zero(cursor) or cursor in unavailable:
            _fail(f"{label}: walkがcollision/event/objectへ進入:{cursor}")
    return cursor


def _object_path(
    final_rom: bytes,
    owner: Mapping[str, Any],
    npc: Mapping[str, Any],
    state: _MapState,
) -> tuple[dict[str, Any], dict[str, Any]]:
    owner_id = str(owner["owner_id"])
    raw = _read(final_rom, owner["record_address"], 0x18, f"{owner_id} record")
    local_id = raw[0]
    index = int(owner["index"])
    if int(npc.get("object_index", -1)) != index \
            or int(npc.get("local_id", -1)) != local_id \
            or int(npc.get("script_pointer", -1)) != int(owner["root"]):
        _fail(f"OBJECT catalog/final record identity不一致:{owner_id}")
    execution = npc["interaction_execution"]
    required_keys = {
        "trigger", "start", "walk_sequence", "stance", "action",
        "interaction_distance", "counter_tile", "actual_walk_required",
        "actual_walk_exception", "walk_path_basis",
        "direct_script_call_forbidden",
    }
    if set(execution) != required_keys \
            or execution.get("trigger") != \
                "TELEPORT_TO_WALK_START_REAL_WALK_TO_STANCE_FACE_AND_A" \
            or execution.get("direct_script_call_forbidden") is not True \
            or execution.get("action") not in _CARDINAL_DELTAS \
            or not isinstance(execution.get("walk_sequence"), list) \
            or not isinstance(execution.get("walk_path_basis"), str) \
            or not execution["walk_path_basis"].strip():
        _fail(f"OBJECT interaction_execution schema不正:{owner_id}")
    start = _point(execution["start"], f"{owner_id}.start")
    stance = _point(execution["stance"], f"{owner_id}.stance")
    # BG records are passive during walking; COORD and WARP records are not.
    unavailable = state.object_tiles | state.coord_tiles | state.warp_tiles
    if not state.geometry.in_bounds(start):
        _fail(f"OBJECT interaction start範囲外:{owner_id}:{start}")
    base_walk_valid = state.geometry.collision_zero(start) \
        and start not in unavailable
    try:
        walked_end = _walk(
            start, execution["walk_sequence"], state.geometry,
            unavailable, f"{owner_id}.walk_sequence",
        )
    except Stage61RuntimeTriggerInputsError:
        # Map scripts and flag states can replace collision after the stock
        # load.  Preserve the exact placement path as a runtime candidate,
        # but prove every token stays in bounds and make mGBA the final gate.
        base_walk_valid = False
        walked_end = start
        for token in execution["walk_sequence"]:
            if token not in _CARDINAL_DELTAS:
                _fail(f"{owner_id}.walk_sequence token不正:{token}")
            dx, dy = _CARDINAL_DELTAS[token]
            walked_end = walked_end[0] + dx, walked_end[1] + dy
            if not state.geometry.in_bounds(walked_end):
                _fail(f"OBJECT runtime walk候補が範囲外:{owner_id}:{walked_end}")
    if walked_end != stance:
        _fail(f"OBJECT interaction walk終点不一致:{owner_id}")
    actual = execution["actual_walk_required"]
    exception = execution["actual_walk_exception"]
    shadow = npc.get("non_product_shadow_alias")
    if shadow is not None and (
        not isinstance(shadow, Mapping)
        or set(shadow) != {
            "classification", "role", "source_owner_id",
            "canonical_owner_id",
        }
        or shadow.get("classification")
            != "CANONICAL_SHADOW_NON_PRODUCT_SOURCE"
        or shadow.get("role") not in {
            "NON_PRODUCT_SOURCE", "CANONICAL_PHYSICAL_OWNER",
        }
    ):
        _fail(f"OBJECT non-product shadow alias schema不正:{owner_id}")
    is_shadow_source = isinstance(shadow, Mapping) \
        and shadow.get("role") == "NON_PRODUCT_SOURCE"
    is_shadow_canonical = isinstance(shadow, Mapping) \
        and shadow.get("role") == "CANONICAL_PHYSICAL_OWNER"
    if is_shadow_source:
        expected_exception = {
            "classification": "CANONICAL_SHADOW_NON_PRODUCT_SOURCE",
            "canonical_owner_id": shadow["canonical_owner_id"],
            "canonical_walk_required": True,
            "source_teleport_face_a_required": True,
            "direct_script_call_forbidden": True,
        }
        if owner_id != shadow["source_owner_id"] \
                or actual is not False or execution["walk_sequence"] \
                or exception != expected_exception \
                or execution["start"] != execution["stance"] \
                or execution["walk_path_basis"] != (
                    "CANONICAL_SHADOW_NON_PRODUCT_SOURCE_DIAGNOSTIC_STANCE"
                ):
            _fail(f"OBJECT shadow source physical exception不一致:{owner_id}")
    elif actual is not True or not execution["walk_sequence"] \
            or exception is not None:
        _fail(f"OBJECT owner-specific actual walk evidence不一致:{owner_id}")
    if is_shadow_canonical and (
        owner_id != shadow["canonical_owner_id"]
        or execution["walk_path_basis"]
            != "CANONICAL_SHADOW_EXACT_STOCK_INCOMING_ARRIVAL_TO_STANCE"
    ):
        _fail(f"OBJECT shadow canonical walk根拠不一致:{owner_id}")
    template_point = struct.unpack_from("<hh", raw, 4)
    object_point = _point(
        npc["_stage61_runtime_object"], f"{owner_id}.runtime_object",
    )
    action = str(execution["action"])
    dx, dy = _CARDINAL_DELTAS[action]
    distance = int(execution["interaction_distance"])
    if distance not in (1, 2) \
            or (stance[0] + dx * distance, stance[1] + dy * distance) \
                != object_point:
        _fail(f"OBJECT stance/action/target geometry不一致:{owner_id}")
    if distance == 2:
        counter = stance[0] + dx, stance[1] + dy
        if _point(execution["counter_tile"], f"{owner_id}.counter") != counter \
                or state.geometry.behavior(counter) != 0x80:
            _fail(f"OBJECT counter ABI不一致:{owner_id}")
    elif execution["counter_tile"] is not None:
        _fail(f"OBJECT non-counterにcounter tileあり:{owner_id}")
    path = {
        "kind": "OBJECT_FACE_A", "group": int(owner["group"]),
        "map": int(owner["map"]), "local_id": local_id,
        "object_index": index, "root_pc": int(owner["root"]),
        "approach": (
            "TELEPORT_STANCE_FACE_A_CANONICAL_SHADOW_SOURCE"
            if is_shadow_source else "WALK_ADJACENT_FACE_A"
        ),
        "start_tile": _point_dict(start),
        "walk_sequence": list(execution["walk_sequence"]),
        "stance_tile": _point_dict(stance),
        "required_facing": action,
        "runtime_topology_probe_required": not base_walk_valid,
    }
    evidence = {
        "kind": "FINAL_NPC_CATALOG_INTERACTION_EXECUTION",
        "object_tile": list(object_point),
        "template_object_tile": list(template_point),
        "interaction_object_basis": npc[
            "_stage61_interaction_object_basis"
        ],
        "runtime_object_position_from_final_placement_audit": True,
        "start": list(start),
        "walk_sequence": list(execution["walk_sequence"]),
        "stance": list(stance), "action": action,
        "actual_walk_steps": len(execution["walk_sequence"]),
        "actual_walk_exception": deepcopy(exception),
        "non_product_shadow_alias": deepcopy(shadow),
        "walk_path_basis": str(execution["walk_path_basis"]),
        "map_level_real_walk_probe_required": False,
        "base_start_collision": state.geometry.collision(start),
        "base_static_walk_path": base_walk_valid,
        "runtime_topology_probe_required": (
            not base_walk_valid
        ),
        "runtime_topology_basis": (
            "LOADED_FIELD_AFTER_STOCK_MAP_LOAD_MAP_SCRIPTS_FLAGS_AND_SETMETATILE"
        ),
        "mgba_actual_field_interaction_required": True,
        "direct_script_call_forbidden": True,
    }
    return path, evidence


def _elevations_compatible(left: int, right: int) -> bool:
    """Match the field engine's wildcard elevation semantics.

    Event elevation 0 is wildcard.  Metatile elevations 0 and 15 are also
    transition/wildcard values and cannot be rejected by integer equality.
    The final arbiter remains an actual loaded-field mGBA step.
    """

    return left in {0, 15} or right in {0, 15} or left == right


def _walk_path_to(
    owner_id: str,
    geometry: _Geometry,
    target: tuple[int, int],
    unavailable: frozenset[tuple[int, int]],
    start_only_tiles: frozenset[tuple[int, int]] = frozenset(),
) -> dict[str, Any]:
    """Produce a deterministic teleport + real cardinal walk candidate.

    Prefer a two-or-more-step static BFS route.  When base blockdata cannot
    represent a route, retain an adjacent in-bounds candidate and explicitly
    require the loaded-field (map scripts/flags/setmetatile applied) runner to
    prove the actual step.  This is an input producer, not a static PASS for
    dynamic topology.
    """

    if not geometry.in_bounds(target):
        _fail(f"実field target範囲外:{owner_id}:{target}")
    base_target_elevation = geometry.elevation(target)
    paths: dict[tuple[int, int], list[str]] = {target: []}
    queue: deque[tuple[int, int]] = deque([target])
    if geometry.collision_zero(target) and target not in unavailable:
        while queue:
            current = queue.popleft()
            if len(paths[current]) >= 8:
                continue
            for token in _FACE_DIRECTION_ORDER:
                dx, dy = _CARDINAL_DELTAS[token]
                # Moving from neighbor with ``token`` reaches current.
                neighbor = current[0] - dx, current[1] - dy
                if neighbor in paths or neighbor in unavailable \
                        or not geometry.collision_zero(neighbor) \
                        or not _elevations_compatible(
                            geometry.elevation(neighbor),
                            geometry.elevation(current),
                        ):
                    continue
                paths[neighbor] = [token, *paths[current]]
                # Teleporting onto another COORD does not execute it.  It may
                # therefore be the first tile, but walking *through* it would
                # hit the wrong owner before the target.
                if neighbor not in start_only_tiles:
                    queue.append(neighbor)
    static_candidates = [
        (point, tokens) for point, tokens in paths.items() if tokens
    ]
    if static_candidates:
        # Prefer a non-trivial BFS route when one exists, then the shortest.
        point, tokens = min(
            static_candidates,
            key=lambda row: (
                len(row[1]) < 2, len(row[1]), row[0][1], row[0][0],
                tuple(_FACE_DIRECTION_ORDER.index(token) for token in row[1]),
            ),
        )
        runtime_probe = False
    else:
        dynamic_candidates: list[
            tuple[tuple[Any, ...], tuple[int, int], list[str]]
        ] = []
        for token in _FACE_DIRECTION_ORDER:
            dx, dy = _CARDINAL_DELTAS[token]
            neighbor = target[0] - dx, target[1] - dy
            if not geometry.in_bounds(neighbor) or neighbor in unavailable:
                continue
            score = (
                not geometry.collision_zero(neighbor),
                not _elevations_compatible(
                    geometry.elevation(neighbor), base_target_elevation,
                ),
                _FACE_DIRECTION_ORDER.index(token), neighbor[1], neighbor[0],
            )
            dynamic_candidates.append((score, neighbor, [token]))
        if not dynamic_candidates:
            _fail(f"実field cardinal predecessor候補なし:{owner_id}:{target}")
        _score, point, tokens = min(dynamic_candidates, key=lambda row: row[0])
        runtime_probe = True

    cursor = point
    predecessor = point
    for token in tokens:
        predecessor = cursor
        dx, dy = _CARDINAL_DELTAS[token]
        cursor = cursor[0] + dx, cursor[1] + dy
    if cursor != target:
        _fail(f"内部BFS walk終点不一致:{owner_id}:{cursor}:{target}")
    path_tiles = [point]
    cursor = point
    for token in tokens:
        dx, dy = _CARDINAL_DELTAS[token]
        cursor = cursor[0] + dx, cursor[1] + dy
        path_tiles.append(cursor)
    return {
        "start_tile": list(point),
        "walk_sequence": tokens,
        "walk_path_tiles": [list(row) for row in path_tiles],
        "predecessor_tile": list(predecessor),
        "target_tile": list(target),
        "trigger_key": tokens[-1],
        "actual_walk_steps": len(tokens),
        "base_target_collision": geometry.collision(target),
        "base_target_elevation": base_target_elevation,
        "base_predecessor_collision": geometry.collision(predecessor),
        "base_predecessor_elevation": geometry.elevation(predecessor),
        "base_static_bfs_path": not runtime_probe,
        "runtime_topology_probe_required": runtime_probe,
        "runtime_topology_basis": (
            "LOADED_FIELD_AFTER_STOCK_MAP_LOAD_MAP_SCRIPTS_FLAGS_AND_SETMETATILE"
        ),
        "mgba_actual_cardinal_first_hit_required": True,
        "teleport_does_not_satisfy_trigger": True,
    }


def _face_geometry(
    owner_id: str,
    state: _MapState,
    target: tuple[int, int],
    elevation: int,
    directions: Sequence[str],
) -> dict[str, Any]:
    unavailable = state.object_tiles | state.warp_tiles
    candidates: list[tuple[tuple[Any, ...], dict[str, Any]]] = []
    for direction in directions:
        dx, dy = _FACE_STANCE_DELTA[direction]
        stance = target[0] + dx, target[1] + dy
        try:
            walk = _walk_path_to(
                owner_id, state.geometry, stance, unavailable,
                state.coord_tiles,
            )
        except Stage61RuntimeTriggerInputsError:
            continue
        elevation_compatible = _elevations_compatible(
            elevation, state.geometry.elevation(stance),
        )
        if not elevation_compatible:
            walk["runtime_topology_probe_required"] = True
            walk["base_static_bfs_path"] = False
        walk.update({
            "target_tile": list(target), "stance_tile": list(stance),
            "required_facing": direction,
            "event_elevation": elevation,
            "event_elevation_base_compatible": elevation_compatible,
            "stance_object_free": stance not in state.object_tiles,
            "stance_step_trigger_free": (
                stance not in state.coord_tiles | state.warp_tiles
            ),
        })
        score = (
            walk["runtime_topology_probe_required"],
            len(walk["walk_sequence"]),
            _FACE_DIRECTION_ORDER.index(direction),
        )
        candidates.append((score, walk))
    if not candidates:
        _fail(f"実field face+A stance/BFS predecessorなし:{owner_id}:{target}")
    return min(candidates, key=lambda row: row[0])[1]


def _bg_path(
    final_rom: bytes, owner: Mapping[str, Any], state: _MapState,
) -> tuple[dict[str, Any], dict[str, Any]]:
    owner_id = str(owner["owner_id"])
    raw = _read(final_rom, owner["record_address"], 12, f"{owner_id} record")
    x, y, elevation, bg_kind = _u16(raw), _u16(raw, 2), raw[4], raw[5]
    if bg_kind not in {0, 1, 2, 3, 4}:
        _fail(f"script BG facing kind不正:{owner_id}:{bg_kind}")
    directions = (_BG_REQUIRED_DIRECTION[bg_kind],) if bg_kind else \
        _FACE_DIRECTION_ORDER
    evidence = _face_geometry(
        owner_id, state, (x, y), elevation, directions,
    )
    evidence["kind"] = "FINAL_BG_BFS_WALK_FACE_A"
    return {
        "kind": "BG_FACE_A", "group": int(owner["group"]),
        "map": int(owner["map"]), "x": x, "y": y,
        "elevation": elevation,
        "start_tile": _point_dict(tuple(evidence["start_tile"])),
        "walk_sequence": list(evidence["walk_sequence"]),
        "stance_tile": _point_dict(tuple(evidence["stance_tile"])),
        "required_facing": evidence["required_facing"],
        "root_pc": int(owner["root"]),
    }, evidence


def _step_geometry(
    owner_id: str, state: _MapState, target: tuple[int, int], elevation: int,
) -> dict[str, Any]:
    unavailable = state.object_tiles | state.warp_tiles
    result = _walk_path_to(
        owner_id, state.geometry, target, unavailable,
        state.coord_tiles - {target},
    )
    elevation_compatible = _elevations_compatible(
        elevation, state.geometry.elevation(target),
    )
    if not elevation_compatible:
        result["runtime_topology_probe_required"] = True
        result["base_static_bfs_path"] = False
    result.update({
        "event_elevation": elevation,
        "event_elevation_base_compatible": elevation_compatible,
        "predecessor_object_free": (
            tuple(result["predecessor_tile"]) not in state.object_tiles
        ),
        "predecessor_step_trigger_free": (
            tuple(result["predecessor_tile"])
            not in state.warp_tiles | (state.coord_tiles - {target})
        ),
    })
    return result


def _coord_path(
    final_rom: bytes, owner: Mapping[str, Any], state: _MapState,
) -> tuple[dict[str, Any], dict[str, Any]]:
    owner_id = str(owner["owner_id"])
    raw = _read(final_rom, owner["record_address"], 16, f"{owner_id} record")
    x, y, elevation = _u16(raw), _u16(raw, 2), raw[4]
    trigger_var = _u16(raw, 6)
    trigger_value = (_u16(raw, 8) & 0xFF) if trigger_var else 0
    evidence = _step_geometry(owner_id, state, (x, y), elevation)
    evidence["kind"] = "FINAL_COORD_ADJACENT_REAL_STEP"
    return {
        "kind": "COORD_STEP", "group": int(owner["group"]),
        "map": int(owner["map"]), "x": x, "y": y,
        "elevation": elevation, "trigger_var": trigger_var,
        "trigger_value": trigger_value,
        "start_tile": _point_dict(tuple(evidence["start_tile"])),
        "walk_sequence": list(evidence["walk_sequence"]),
        "trigger_key": evidence["trigger_key"],
        "root_pc": int(owner["root"]),
    }, evidence


def _map_script_tag(
    final_rom: bytes,
    owner: Mapping[str, Any],
    surface_by_map: Mapping[tuple[int, int], Mapping[str, Any]],
    maps: _FinalRomMaps,
) -> tuple[int, dict[str, Any]]:
    key = int(owner["group"]), int(owner["map"])
    surface = surface_by_map.get(key)
    if not isinstance(surface, Mapping) \
            or not isinstance(surface.get("map_script_structure"), list):
        _fail(f"MAP surface structure欠落:{owner['owner_id']}")
    index = owner.get("index")
    table_index = int(index[0]) if isinstance(index, list) else int(index)
    rows = [
        row for row in surface["map_script_structure"]
        if isinstance(row, Mapping) and int(row.get("table_index", -1)) == table_index
    ]
    if len(rows) != 1:
        _fail(f"MAP table index一意性不一致:{owner['owner_id']}")
    tag = int(rows[0].get("script_type", -1))
    if tag not in range(1, 8):
        _fail(f"MAP script tag不正:{owner['owner_id']}:{tag}")
    _header_address, header = maps._map_header(*key)
    table_pointer = _u32_at(
        final_rom, header + 8, f"MAP script table pointer:{owner['owner_id']}",
    )
    cursor = _offset(
        final_rom, table_pointer, 1, f"MAP script table:{owner['owner_id']}",
    )
    for current_index in range(table_index + 1):
        rom_tag = final_rom[cursor]
        if rom_tag == 0 or rom_tag not in range(1, 8):
            _fail(f"MAP script table index/tag ROM不正:{owner['owner_id']}")
        if current_index == table_index:
            break
        cursor = _offset(
            final_rom, ROM_BASE + cursor + 5, 1,
            f"MAP script table next row:{owner['owner_id']}",
        )
    if rom_tag != tag:
        _fail(f"MAP script tag inventory/ROM不一致:{owner['owner_id']}")
    target_pointer = _u32_at(
        final_rom, cursor + 1, f"MAP script target:{owner['owner_id']}",
    )
    record = _address(owner["record_address"], "MAP record")
    if owner.get("root_subkind") == "DIRECT":
        if record != ROM_BASE + cursor \
                or _read(final_rom, record, 1, "MAP direct tag")[0] != tag \
                or target_pointer != int(owner.get("root", -1)):
            _fail(f"MAP direct tag ROM不一致:{owner['owner_id']}")
    elif owner.get("root_subkind") == "CONDITION":
        conditions = rows[0].get("conditions")
        condition_index = int(index[1]) if isinstance(index, list) else -1
        matches = [
            row for row in conditions or []
            if isinstance(row, Mapping)
            and int(row.get("condition_index", -1)) == condition_index
        ]
        if len(matches) != 1 \
                or int(matches[0].get("record_address", -1)) != record:
            _fail(f"MAP condition structure/record不一致:{owner['owner_id']}")
        condition = _offset(
            final_rom, target_pointer, 2,
            f"MAP condition table:{owner['owner_id']}",
        )
        decoded: list[dict[str, Any]] = []
        for decoded_index in range(256):
            variable = _u16(final_rom, condition)
            if variable == 0:
                break
            raw = _read(
                final_rom, ROM_BASE + condition, 8,
                f"MAP condition row:{owner['owner_id']}:{decoded_index}",
            )
            decoded.append({
                "condition_index": decoded_index,
                "variable": variable,
                "value": _u16(raw, 2),
                "root": _u32_at(
                    final_rom, condition + 4,
                    f"MAP condition root:{owner['owner_id']}:{decoded_index}",
                ),
                "record_address": ROM_BASE + condition,
                "root_field_address": ROM_BASE + condition + 4,
            })
            if not (0x4000 <= decoded[-1]["variable"] <= 0x40FF
                    or 0x5000 <= decoded[-1]["variable"] <= 0x51FF) \
                    or not 0 <= decoded[-1]["value"] < 0x4000:
                _fail(
                    "MAP condition dynamic/unsupported operand:"
                    f"{owner['owner_id']}:{decoded_index}"
                )
            condition = _offset(
                final_rom, ROM_BASE + condition + 8, 2,
                f"MAP condition next row:{owner['owner_id']}",
            )
        else:
            _fail(f"MAP condition table未終端:{owner['owner_id']}")
        inventory_projection = [{
            key: int(row.get(key, -1))
            for key in (
                "condition_index", "variable", "value", "root",
                "record_address", "root_field_address",
            )
        } for row in conditions or [] if isinstance(row, Mapping)]
        if inventory_projection != decoded:
            _fail(f"MAP condition table inventory/ROM不一致:{owner['owner_id']}")
        structure = dict(rows[0])
        structure.update({
            "conditions": decoded,
            "condition_table_address": target_pointer,
            "condition_table_terminator_address": ROM_BASE + condition,
        })
        return tag, structure
    else:
        _fail(f"MAP root subkind不正:{owner['owner_id']}")
    return tag, dict(rows[0])


def _map_condition_precedence_guards(
    final_rom: bytes,
    owner: Mapping[str, Any],
    structure: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Derive the VAR values that make every earlier condition row false.

    ``MapHeaderCheckScriptTable`` is a first-match dispatcher.  Merely making
    the selected row true is therefore insufficient: an earlier row using a
    different VAR can consume the transition first.  Bind every guard to the
    ordered final-ROM records so the physical mGBA producer cannot silently
    substitute a convenient host-side state.
    """

    owner_id = str(owner["owner_id"])
    index = owner.get("index")
    if owner.get("root_subkind") != "CONDITION" \
            or not isinstance(index, list) or len(index) != 2:
        _fail(f"MAP condition precedence owner/index不正:{owner_id}")
    target_index = int(index[1])
    conditions = structure.get("conditions")
    if not isinstance(conditions, list) or not 0 <= target_index < len(conditions):
        _fail(f"MAP condition precedence table/index不正:{owner_id}")

    decoded: list[dict[str, Any]] = []
    for expected_index, source in enumerate(conditions):
        if not isinstance(source, Mapping) \
                or int(source.get("condition_index", -1)) != expected_index:
            _fail(f"MAP condition precedence row順序不正:{owner_id}")
        record_address = _address(
            source.get("record_address"), "MAP condition precedence record",
        )
        raw = _read(
            final_rom, record_address, 8,
            f"{owner_id} precedence condition {expected_index}",
        )
        variable, value, root = _u16(raw), _u16(raw, 2), _u32(raw, 4)
        if not (0x4000 <= variable <= 0x40FF
                or 0x5000 <= variable <= 0x51FF) \
                or not 0 <= value < 0x4000 \
                or variable != int(source.get("variable", -1)) \
                or value != int(source.get("value", -1)) \
                or root != int(source.get("root", -1)):
            _fail(f"MAP condition precedence row/ROM不一致:{owner_id}")
        decoded.append({
            "condition_index": expected_index,
            "record_address": record_address,
            "record_raw_hex": raw.hex(),
            "record_raw_sha256": _sha(raw),
            "variable": variable,
            "value": value,
            "root_pc": root,
        })

    target = decoded[target_index]
    if target["record_address"] != _address(
            owner.get("record_address"), "MAP target condition record",
    ) or target["root_pc"] != int(owner.get("root", -1)):
        _fail(f"MAP condition precedence target identity不一致:{owner_id}")

    grouped: dict[int, list[dict[str, Any]]] = {}
    for row in decoded[:target_index]:
        variable, value = int(row["variable"]), int(row["value"])
        if variable == int(target["variable"]):
            if value == int(target["value"]):
                _fail(
                    "MAP condition targetは同一先行条件により到達不能:"
                    f"{owner_id}:{target_index}"
                )
            # Installing the target equality already makes this row false.
            continue
        grouped.setdefault(variable, []).append(row)

    guards: list[dict[str, Any]] = []
    for variable in sorted(grouped):
        source_rows = grouped[variable]
        forbidden = sorted({int(row["value"]) for row in source_rows})
        required_value = next(
            (value for value in range(0x10000) if value not in forbidden),
            None,
        )
        if required_value is None:
            _fail(f"MAP condition precedence guard値を選べません:{owner_id}")
        guards.append({
            "variable": variable,
            "required_value": required_value,
            "forbidden_values": forbidden,
            "relation": "NOT_EQUAL_ALL_PRECEDING_VALUES",
            "source_conditions": deepcopy(source_rows),
        })
    return guards


def _callback_row(
    final_rom: bytes,
    map_callback_contracts: Mapping[str, Any] | None,
    tag: int,
) -> dict[str, Any]:
    rom_sha = _sha(final_rom)
    if not isinstance(map_callback_contracts, Mapping) \
            or map_callback_contracts.get("schema_version") != 1 \
            or map_callback_contracts.get("kind") != \
                "STAGE61_MAP_FIELD_RETURN_CALLBACK_CONTRACTS" \
            or map_callback_contracts.get("rom_sha256") != rom_sha \
            or not isinstance(map_callback_contracts.get("by_tag"), Mapping):
        _fail(f"MAP tag {tag} field-return callback contract欠落")
    source = map_callback_contracts["by_tag"].get(str(tag))
    if not isinstance(source, Mapping) or set(source) != {
        "callback_address", "callback_install_instruction_pc",
        "callback_dispatch_instruction_pc", "normal_trigger_tokens",
        "source_provenance",
    } or source.get("normal_trigger_tokens") != ["START", "B"] \
            or not isinstance(source.get("source_provenance"), Mapping) \
            or source["source_provenance"].get("rom_sha256") != rom_sha:
        _fail(f"MAP tag {tag} callback row schema/provenance不正")
    result = deepcopy(dict(source))
    for key in (
        "callback_address", "callback_install_instruction_pc",
        "callback_dispatch_instruction_pc",
    ):
        value = _address(result[key], f"MAP tag {tag} {key}")
        _offset(final_rom, value, 1, f"MAP tag {tag} {key}")
        result[key] = value
    return result


def _placement_map_entries(
    placement_audit: Mapping[str, Any],
) -> dict[tuple[int, int], Mapping[str, Any]]:
    raw = placement_audit.get("maps", [])
    if not isinstance(raw, list):
        _fail("final placement audit maps不正")
    result: dict[tuple[int, int], Mapping[str, Any]] = {}
    for ordinal, row in enumerate(raw):
        if not isinstance(row, Mapping):
            _fail(f"final placement map row不正:{ordinal}")
        try:
            key = int(row["group"]), int(row["map"])
        except (KeyError, TypeError, ValueError):
            _fail(f"final placement map identity不正:{ordinal}")
        if key in result:
            _fail(f"final placement map重複:{key}")
        entry = row.get("entry")
        if not isinstance(entry, Mapping):
            _fail(f"final placement map entry不正:{key}")
        result[key] = entry
    return result


def _stock_connection_candidates(
    final_rom: bytes,
    destination: tuple[int, int],
    entry_report: Mapping[str, Any] | None,
) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    if not isinstance(entry_report, Mapping):
        return []
    rows = entry_report.get("connections")
    if not isinstance(rows, list):
        _fail(f"placement connection rows不正:{destination}")
    candidates: list[
        tuple[tuple[Any, ...], dict[str, Any], dict[str, Any]]
    ] = []
    direction_by_code = {1: "UP", 2: "DOWN", 3: "LEFT", 4: "RIGHT"}
    for ordinal, row in enumerate(rows):
        if not isinstance(row, Mapping) or row.get("target") != list(destination):
            _fail(f"placement connection target不正:{destination}:{ordinal}")
        direction = direction_by_code.get(int(row.get("direction", -1)))
        source = _point(row.get("source"), f"connection source map {ordinal}")
        if direction is None or any(not 0 <= value <= 0xFF for value in source):
            continue
        record = _address(
            row.get("row_address"), f"connection record {destination}/{ordinal}",
        )
        raw = _read(final_rom, record, 12, "connection record")
        if raw.hex() != row.get("row_raw_hex"):
            _fail(f"connection final ROM raw不一致:{destination}:{ordinal}")
        coordinate_rows = row.get("coordinate_evidence")
        if not isinstance(coordinate_rows, list):
            _fail(f"connection coordinate evidence不正:{destination}:{ordinal}")
        for coordinate in coordinate_rows:
            if not isinstance(coordinate, Mapping) \
                    or coordinate.get("source_collision_zero") is not True \
                    or coordinate.get("target_collision_zero") is not True:
                continue
            predecessor = _point(
                coordinate.get("source_boundary_tile"),
                f"connection predecessor {destination}/{ordinal}",
            )
            arrival = _point(
                coordinate.get("arrival_tile"),
                f"connection arrival {destination}/{ordinal}",
            )
            dx, dy = _CARDINAL_DELTAS[direction]
            trigger = predecessor[0] + dx, predecessor[1] + dy
            if any(not 0 <= value <= 0xFFFF for value in trigger):
                continue
            provenance = {
                "kind": "FINAL_ROM_STOCK_CONNECTION_BOUNDARY_STEP",
                "rom_sha256": _sha(final_rom),
                "record_address": f"0x{record:08X}",
                "record_raw_hex": raw.hex(),
                "record_raw_sha256": _sha(raw),
                "placement_seed_basis": row.get("seed_basis"),
                "engine_source": deepcopy(row.get("engine_source")),
            }
            seed = {
                "kind": "STOCK_CONNECTION_BOUNDARY_STEP",
                "source": {"group": source[0], "map": source[1]},
                "predecessor_tile": _point_dict(predecessor),
                "trigger_tile": _point_dict(trigger),
                "trigger_key": direction,
                "destination": {
                    "group": destination[0], "map": destination[1],
                },
                "arrival_tile": _point_dict(arrival),
                "connection_or_warp_record_address": record,
                "source_provenance": provenance,
            }
            evidence = {
                "kind": "STOCK_CONNECTION_PHYSICAL_BOUNDARY_PREDECESSOR",
                "source_map": list(source),
                "predecessor_tile": list(predecessor),
                "trigger_tile": list(trigger),
                "trigger_key": direction,
                "destination_map": list(destination),
                "arrival_tile": list(arrival),
                "record_address": f"0x{record:08X}",
                "record_raw_sha256": _sha(raw),
            }
            order = (
                source[0], source[1], int(row.get("index", ordinal)),
                arrival[1], arrival[0],
            )
            candidates.append((order, seed, evidence))
    candidates.sort(key=lambda row: row[0])
    return [(seed, evidence) for _order, seed, evidence in candidates]


def _engine_teleport_seed(
    final_rom: bytes,
    destination: tuple[int, int],
    maps: _FinalRomMaps,
    entry_report: Mapping[str, Any] | None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    state = maps.warp_state(*destination)
    unavailable = state.object_tiles | state.warp_tiles
    center = state.geometry.width // 2, state.geometry.height // 2
    candidates = [
        (x, y)
        for y in range(state.geometry.height)
        for x in range(state.geometry.width)
        if state.geometry.collision_zero((x, y))
        and (x, y) not in unavailable
    ]
    if not candidates:
        _fail(f"ENGINE teleport final geometry safe startなし:{destination}")
    start = min(
        candidates,
        key=lambda point: (
            abs(point[0] - center[0]) + abs(point[1] - center[1]),
            point[1], point[0],
        ),
    )
    block_index = start[1] * state.geometry.width + start[0]
    block_address = state.geometry.blockdata_address + block_index * 2
    block_raw = _read(final_rom, block_address, 2, "teleport start block")
    scan = deepcopy(maps.stock_scan_diagnostics.get(destination, {}))
    connections = [] if not isinstance(entry_report, Mapping) else \
        entry_report.get("connections", [])
    if not isinstance(connections, list):
        _fail(f"ENGINE teleport connection evidence不正:{destination}")
    source_provenance = {
        "kind": "FINAL_ROM_GEOMETRY_BOUND_ENGINE_PLAYER_TELEPORT_MAP_LOAD",
        "rom_sha256": _sha(final_rom),
        "layout_address": f"0x{state.geometry.layout_address:08X}",
        "block_address": f"0x{block_address:08X}",
        "block_raw_hex": block_raw.hex(),
        "block_raw_sha256": _sha(block_raw),
        "base_collision": state.geometry.collision(start),
        "base_elevation": state.geometry.elevation(start),
        "foreign_stock_warp_scan": scan,
        "usable_stock_connection_count": len(
            _stock_connection_candidates(final_rom, destination, entry_report)
        ),
        "incoming_usable_zero_reason_bound": True,
        "first_root_hit_map_identity_required": True,
        "settled_map_identity_not_substituted_for_first_root_hit": True,
        "direct_root_call_forbidden": True,
        "direct_callback_call_forbidden": True,
    }
    seed = {
        "kind": "ENGINE_PLAYER_TELEPORT_MAP_LOAD",
        "destination": {
            "group": destination[0], "map": destination[1],
        },
        "start_tile": _point_dict(start),
        "engine_entry": "BOOTSTRAP_KANTO_WARP",
        "source_provenance": source_provenance,
    }
    evidence = {
        "kind": "FINAL_ROM_ENGINE_PLAYER_TELEPORT_MAP_LOAD",
        "destination_map": list(destination),
        "start_tile": list(start),
        "engine_entry": "BOOTSTRAP_KANTO_WARP",
        "base_collision_zero": True,
        "base_elevation": state.geometry.elevation(start),
        "foreign_stock_warp_scan": scan,
        "connection_reference_count": len(connections),
        "first_root_hit_map_identity_required": True,
        "direct_root_call_forbidden": True,
        "direct_callback_call_forbidden": True,
    }
    return seed, evidence


def _map_path(
    final_rom: bytes,
    owner: Mapping[str, Any],
    maps: _FinalRomMaps,
    surface_by_map: Mapping[tuple[int, int], Mapping[str, Any]],
    stock_warp_cache: dict[
        tuple[int, int], list[tuple[dict[str, Any], dict[str, Any]]]
    ],
    placement_map_entries: Mapping[tuple[int, int], Mapping[str, Any]],
    map_callback_contracts: Mapping[str, Any] | None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    owner_id = str(owner["owner_id"])
    destination = int(owner["group"]), int(owner["map"])
    tag, structure = _map_script_tag(final_rom, owner, surface_by_map, maps)
    # ``dict.setdefault`` evaluates its default eagerly.  With 628 MAP
    # owners that accidentally rescanned all 678 maps once per owner and let
    # one unrelated malformed array fan out to every MAP path.
    if destination not in stock_warp_cache:
        stock_warp_cache[destination] = maps.stock_warps_into(
            destination, rom_sha256=_sha(final_rom),
        )
    candidates = stock_warp_cache[destination]
    entry_report = placement_map_entries.get(destination)
    connection_candidates = _stock_connection_candidates(
        final_rom, destination, entry_report,
    )
    if candidates:
        seed_key = "stock_warp"
        seed, seed_evidence = deepcopy(candidates[0])
        predecessor_kind = "STOCK_WARP_THEN_FIELD_RETURN"
    elif connection_candidates:
        seed_key = "stock_connection"
        seed, seed_evidence = deepcopy(connection_candidates[0])
        predecessor_kind = "STOCK_CONNECTION_THEN_FIELD_RETURN"
    else:
        seed_key = "engine_teleport"
        seed, seed_evidence = _engine_teleport_seed(
            final_rom, destination, maps, entry_report,
        )
        predecessor_kind = "ENGINE_TELEPORT_THEN_FIELD_RETURN"
    path: dict[str, Any] = {
        "kind": "MAP_TRANSITION_LOAD", "group": destination[0],
        "map": destination[1], "root_subkind": owner["root_subkind"],
        "map_script_tag": tag,
        "entry": (
            "STOCK_WARP_OR_CONNECTION_OR_ENGINE_TELEPORT_OR_RESUME_CALLBACK"
        ),
        "root_pc": int(owner["root"]),
    }
    if owner["root_subkind"] == "CONDITION":
        raw = _read(final_rom, owner["record_address"], 8, f"{owner_id} condition")
        precedence_guards = _map_condition_precedence_guards(
            final_rom, owner, structure,
        )
        path.update({
            "left_operand": _u16(raw), "right_operand": _u16(raw, 2),
            "required_relation": "EQUAL",
            "precedence_guards": precedence_guards,
        })
    if tag in _MAP_STOCK_WARP_TAGS:
        path[seed_key] = seed
        evidence = {
            "kind": {
                "stock_warp": "FINAL_ROM_MAP_SCRIPT_ACTUAL_STOCK_WARP",
                "stock_connection": (
                    "FINAL_ROM_MAP_SCRIPT_ACTUAL_STOCK_CONNECTION"
                ),
                "engine_teleport": (
                    "FINAL_ROM_MAP_SCRIPT_ENGINE_PLAYER_TELEPORT_LOAD"
                ),
            }[seed_key],
            "map_script_tag": tag, "map_script_lifecycle": {
                1: "ON_LOAD", 2: "ON_FRAME_TABLE",
                3: "ON_TRANSITION", 4: "ON_WARP_INTO_MAP_TABLE",
            }[tag],
            "seed_kind": seed_key,
            "actual_predecessor": seed_evidence,
            "first_root_hit_map_identity_required": (
                seed_key == "engine_teleport"
            ),
            "direct_script_call_forbidden": True,
        }
    elif tag in _MAP_FIELD_RETURN_TAGS:
        callback = _callback_row(final_rom, map_callback_contracts, tag)
        path["resume_callback"] = {
            "callback_address": callback["callback_address"],
            "actual_predecessor_consumer": {
                "kind": predecessor_kind,
                seed_key: seed,
                "field_return": {
                    "kind": "START_MENU_OPEN_CLOSE",
                    "normal_trigger_tokens": ["START", "B"],
                    "callback_install_instruction_pc": callback[
                        "callback_install_instruction_pc"
                    ],
                    "callback_dispatch_instruction_pc": callback[
                        "callback_dispatch_instruction_pc"
                    ],
                    "expected_map": {
                        "group": destination[0], "map": destination[1],
                    },
                },
            },
            "normal_trigger_tokens": ["START", "B"],
            "source_provenance": deepcopy(callback["source_provenance"]),
        }
        evidence = {
            "kind": "FINAL_ROM_MAP_SCRIPT_ACTUAL_FIELD_RETURN",
            "map_script_tag": tag,
            "map_script_lifecycle": "ON_RESUME" if tag == 5
            else "ON_RETURN_TO_FIELD",
            "seed_kind": seed_key,
            "actual_predecessor": seed_evidence,
            "first_root_hit_map_identity_required": (
                seed_key == "engine_teleport"
            ),
            "field_return_tokens": ["START", "B"],
            "callback_address": f"0x{callback['callback_address']:08X}",
            "callback_install_instruction_pc": (
                f"0x{callback['callback_install_instruction_pc']:08X}"
            ),
            "callback_dispatch_instruction_pc": (
                f"0x{callback['callback_dispatch_instruction_pc']:08X}"
            ),
            "direct_callback_call_forbidden": True,
            "direct_script_call_forbidden": True,
        }
    else:
        _fail(f"MAP tag {tag}に実入力producer未定義:{owner_id}")
    if owner["root_subkind"] == "CONDITION":
        evidence.update({
            "first_matching_condition_owner_required": True,
            "precedence_guard_count": len(path["precedence_guards"]),
            "precedence_guards": deepcopy(path["precedence_guards"]),
        })
    return path, evidence


def _map_seed_kind_from_owner_path(
    path: Mapping[str, Any], owner_id: str,
) -> str:
    """Read one physical map-load seed from a normalized MAP owner path.

    Tags 1--4 keep the seed at the path root.  Tags 5/7 keep the same seed
    below the real field-return predecessor.  Counting these normalized
    ``owner_paths`` (rather than a placement/report label) binds the
    production cardinality to the exact transition input consumed by mGBA.
    """

    if not isinstance(path, Mapping) or path.get("kind") != "MAP_TRANSITION_LOAD":
        _fail(f"MAP seed owner path kind不正:{owner_id}")
    containers: list[Mapping[str, Any]] = [path]
    resume = path.get("resume_callback")
    if resume is not None:
        if not isinstance(resume, Mapping):
            _fail(f"MAP resume callback schema不正:{owner_id}")
        predecessor = resume.get("actual_predecessor_consumer")
        if not isinstance(predecessor, Mapping):
            _fail(f"MAP field-return predecessor欠落:{owner_id}")
        containers.append(predecessor)
    hits = [
        (kind, container[kind])
        for container in containers
        for kind in _MAP_SEED_KINDS
        if kind in container
    ]
    if len(hits) != 1:
        _fail(
            f"MAP owner physical seedはexactly-one必須:{owner_id}:"
            f"hits={[kind for kind, _seed in hits]}"
        )
    kind, seed = hits[0]
    if not isinstance(seed, Mapping):
        _fail(f"MAP owner seed schema不正:{owner_id}:{kind}")
    if kind == "engine_teleport":
        provenance = seed.get("source_provenance")
        scan = None if not isinstance(provenance, Mapping) else \
            provenance.get("foreign_stock_warp_scan")
        usable_warps = None if not isinstance(scan, Mapping) else \
            scan.get("usable_stock_warp_count")
        usable_connections = None if not isinstance(provenance, Mapping) else \
            provenance.get("usable_stock_connection_count")
        if isinstance(usable_warps, bool) or not isinstance(usable_warps, int) \
                or usable_warps != 0:
            _fail(
                "ENGINE teleport selected despite usable foreign stock warp:"
                f"{owner_id}:{usable_warps}"
            )
        if isinstance(usable_connections, bool) \
                or not isinstance(usable_connections, int) \
                or usable_connections != 0:
            _fail(
                "ENGINE teleport selected despite usable stock connection:"
                f"{owner_id}:{usable_connections}"
            )
    return kind


def _recount_map_seed_kinds(
    owner_paths: Mapping[str, Mapping[str, Any]],
    map_owner_ids: Iterable[str],
) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for owner_id in sorted(set(map_owner_ids)):
        path = owner_paths.get(owner_id)
        if path is None:
            continue
        counts[_map_seed_kind_from_owner_path(path, owner_id)] += 1
    return {kind: counts[kind] for kind in _MAP_SEED_KINDS}


def validate_stage61_runtime_trigger_inputs_map_seed_contract(
    document: Mapping[str, Any], *, require_canonical_counts: bool = True,
) -> dict[str, int]:
    """Fail closed when a persisted runtime-trigger artifact drifts.

    The validator deliberately recounts the physical seed from every MAP
    ``owner_paths`` row.  A caller cannot make a stale or edited claimed count
    pass merely by recomputing ``document_sha256``.
    """

    if not isinstance(document, Mapping) \
            or document.get("schema_version") != 1 \
            or document.get("kind") != "STAGE61_RUNTIME_TRIGGER_INPUTS" \
            or document.get("status") != "PASS":
        _fail("runtime trigger artifact schema/status不正")
    claimed_hash = document.get("document_sha256")
    recomputed_hash = _self_hash_without(document, "document_sha256")
    if not isinstance(claimed_hash, str) or len(claimed_hash) != 64 \
            or claimed_hash != recomputed_hash:
        _fail(
            "runtime trigger artifact self-hash不一致:"
            f"claimed={claimed_hash} recomputed={recomputed_hash}"
        )
    owner_paths = document.get("owner_paths")
    runtime_ids = document.get("runtime_required_owner_ids")
    counts = document.get("counts")
    assertions = document.get("assertions")
    if not isinstance(owner_paths, Mapping) \
            or not isinstance(runtime_ids, list) \
            or any(not isinstance(owner_id, str) for owner_id in runtime_ids) \
            or not isinstance(counts, Mapping) \
            or not isinstance(assertions, Mapping):
        _fail("runtime trigger artifact MAP count入力schema不正")
    map_owner_ids = {
        owner_id for owner_id in runtime_ids if owner_id.startswith("MAP:")
    }
    if not map_owner_ids <= set(owner_paths):
        _fail("runtime trigger artifact MAP owner path欠落")
    recounted = _recount_map_seed_kinds(owner_paths, map_owner_ids)
    claimed_counts = counts.get("map_seed_kind_counts")
    if claimed_counts != recounted:
        _fail(
            "MAP seed kind claimed/recount不一致:"
            f"claimed={claimed_counts} recounted={recounted}"
        )
    runtime_kind_counts = counts.get("runtime_owner_kind_counts")
    if not isinstance(runtime_kind_counts, Mapping) \
            or runtime_kind_counts.get("MAP") != len(map_owner_ids) \
            or sum(recounted.values()) != len(map_owner_ids):
        _fail(
            "MAP runtime owner/seed cardinality不一致:"
            f"owners={len(map_owner_ids)} seeds={sum(recounted.values())}"
        )
    if assertions.get("map_owner_paths_have_exactly_one_rom_seed_kind") \
            is not True \
            or assertions.get(
                "engine_teleport_requires_zero_usable_stock_entry"
            ) is not True \
            or assertions.get(
                "exact_production_map_seed_kind_counts_590_0_38"
            ) is not True:
        _fail("runtime trigger artifact MAP seed assertion不成立")
    if require_canonical_counts \
            and (len(map_owner_ids) != EXPECTED_RUNTIME_KIND_COUNTS["MAP"] \
                 or recounted != EXPECTED_MAP_SEED_KIND_COUNTS):
        _fail(
            "production MAP seed kind cardinality不一致:"
            f"owners={len(map_owner_ids)} counts={recounted}"
        )
    return recounted


def _hidden_consumers(
    final_rom: bytes,
    hidden_item_consumers: Mapping[str, Any],
) -> dict[str, dict[str, Any]]:
    rom_sha = _sha(final_rom)
    if not isinstance(hidden_item_consumers, Mapping) \
            or hidden_item_consumers.get("schema_version") != 1 \
            or hidden_item_consumers.get("kind") != \
                "STAGE61_HIDDEN_ITEM_SCRIPT_CONSUMERS" \
            or hidden_item_consumers.get("rom_sha256") != rom_sha \
            or not isinstance(hidden_item_consumers.get("by_entry"), Mapping):
        _fail("hidden item consumer provenance/schema不一致")
    result: dict[str, dict[str, Any]] = {}
    for entry, expected_symbol, required_specials in (
        ("FACE_A", "EventScript_HiddenItemScript", {150, 350}),
        ("ITEMFINDER_UNDERFOOT", "EventScript_ItemfinderDigUpUnderfootItem", {150}),
    ):
        raw = hidden_item_consumers["by_entry"].get(entry)
        if raw is None:
            continue
        if not isinstance(raw, Mapping) or set(raw) != {
            "consumer_script_root", "symbol", "source_provenance",
        } or raw.get("symbol") != expected_symbol \
                or not isinstance(raw.get("source_provenance"), Mapping) \
                or raw["source_provenance"].get("rom_sha256") != rom_sha:
            _fail(f"hidden item {entry} consumer row不正")
        root = _address(raw["consumer_script_root"], f"hidden {entry} root")
        _offset(final_rom, root, 1, f"hidden {entry} root")
        try:
            from tools.stage61_event_semantic_relocator import SemanticScriptGraph

            graph = SemanticScriptGraph(final_rom)
            graph.walk([root])
        except (ImportError, RuntimeError, ValueError) as exc:
            _fail(f"hidden {entry} CFG decode失敗:{exc}")
        if graph.diagnostics:
            _fail(f"hidden {entry} CFG diagnostics:{graph.diagnostics[0]}")
        specials: dict[int, list[int]] = defaultdict(list)
        for node_address in graph.distances(root):
            for instruction in graph.nodes[node_address].instructions:
                if instruction.opcode == 0x25:
                    special = _u16(instruction.raw, 1)
                elif instruction.opcode == 0x26:
                    special = _u16(instruction.raw, 3)
                else:
                    continue
                specials[special].append(instruction.address)
        if not required_specials <= set(specials):
            _fail(
                f"hidden {entry} SPECIAL consumer不足:"
                f"required={sorted(required_specials)} actual={sorted(specials)}"
            )
        result[entry] = {
            "consumer_script_root": root, "symbol": expected_symbol,
            "source_provenance": deepcopy(dict(raw["source_provenance"])),
            "reachable_special_instruction_addresses": {
                str(special): [f"0x{pc:08X}" for pc in sorted(addresses)]
                for special, addresses in sorted(specials.items())
                if special in required_specials
            },
        }
    return result


def _hidden_path(
    final_rom: bytes,
    owner: Mapping[str, Any],
    state: _MapState,
    consumers: Mapping[str, Mapping[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any]]:
    owner_id = str(owner["owner_id"])
    raw = _read(final_rom, owner["record_address"], 12, f"{owner_id} record")
    x, y, elevation = _u16(raw), _u16(raw, 2), raw[4]
    packed = int(owner["raw_root"])
    if _u32_at(final_rom, _offset(
        final_rom, owner["root_field_address"], 4, f"{owner_id} packed field",
    ), f"{owner_id} packed field") != packed:
        _fail(f"hidden packed record ROM不一致:{owner_id}")
    underfoot = bool((packed >> 31) & 1)
    entry = "ITEMFINDER_UNDERFOOT" if underfoot else "FACE_A"
    consumer = consumers.get(entry)
    if consumer is None:
        _fail(f"hidden item consumer root欠落:{owner_id}:{entry}")
    if underfoot:
        geometry = _step_geometry(owner_id, state, (x, y), elevation)
        geometry["kind"] = "FINAL_HIDDEN_ITEM_UNDERFOOT_REAL_STEP_ITEMFINDER"
    else:
        geometry = _face_geometry(
            owner_id, state, (x, y), elevation, _FACE_DIRECTION_ORDER,
        )
        geometry["kind"] = "FINAL_HIDDEN_ITEM_ADJACENT_FACE_A"
    item = packed & 0xFFFF
    quantity = 1 if underfoot else ((packed >> 24) & 0x7F)
    collection_flag = 0x3E8 + ((packed >> 16) & 0xFF)
    provenance = {
        **deepcopy(dict(consumer["source_provenance"])),
        "consumer_symbol": consumer["symbol"],
        "consumer_script_root": f"0x{consumer['consumer_script_root']:08X}",
        "reachable_special_instruction_addresses": deepcopy(
            consumer["reachable_special_instruction_addresses"]
        ),
        "field_entry": entry,
    }
    path = {
        "kind": "HIDDEN_ITEM", "group": int(owner["group"]),
        "map": int(owner["map"]), "x": x, "y": y,
        "elevation": elevation, "underfoot": underfoot, "entry": entry,
        "consumer_script_root": consumer["consumer_script_root"],
        "source_provenance": provenance,
    }
    path["start_tile"] = _point_dict(tuple(geometry["start_tile"]))
    path["walk_sequence"] = list(geometry["walk_sequence"])
    if underfoot:
        path["trigger_key"] = geometry["trigger_key"]
    else:
        path["stance_tile"] = _point_dict(tuple(geometry["stance_tile"]))
        path["required_facing"] = geometry["required_facing"]
    evidence = {
        **geometry,
        "item_id": item, "quantity": quantity,
        "collection_flag": collection_flag,
        "packed_record": f"0x{packed:08X}",
        "consumer_script_root": f"0x{consumer['consumer_script_root']:08X}",
        "consumer_symbol": consumer["symbol"],
        "available_success_special_150": True,
        "coin_branch_special_350": entry == "FACE_A",
        "direct_script_call_forbidden": True,
    }
    return path, evidence


def _validate_with_oracle(
    final_rom: bytes, owner: Mapping[str, Any], path: Mapping[str, Any],
) -> dict[str, Any]:
    try:
        from tools.stage61_interaction_oracle import (
            Stage61InteractionOracleError,
            _validated_runtime_trigger_path,
        )

        # The validator enriches hidden-item rows with decoded item/quantity/
        # flag fields for its internal executor.  Those enrichment keys are
        # intentionally *not* legal input keys on a second validation pass.
        # Keep the producer artifact in the exact input schema after proving
        # that the current path is accepted.
        _validated_runtime_trigger_path(final_rom, owner, path)
        return deepcopy(dict(path))
    except ImportError as exc:
        _fail(f"interaction oracle import失敗:{exc}")
    except Stage61InteractionOracleError as exc:
        _fail(f"既存runtime trigger validator拒否:{owner['owner_id']}:{exc}")


def _null_structural_evidence(
    final_rom: bytes,
    owners: Sequence[Mapping[str, Any]],
) -> dict[str, dict[str, Any]]:
    """全NULL ownerをexact final-ROM root fieldへ結び付ける。"""

    result: dict[str, dict[str, Any]] = {}
    for owner in owners:
        owner_id = str(owner["owner_id"])
        field = _address(
            owner.get("root_field_address"), f"{owner_id} NULL root field",
        )
        raw = _read(final_rom, field, 4, f"{owner_id} NULL root field")
        if raw != b"\0" * 4 \
                or owner.get("non_script_reason") != "NULL_SCRIPT_POINTER" \
                or owner.get("root") is not None \
                or int(owner.get("raw_root", -1)) != 0:
            _fail(f"structural NULL evidence不一致:{owner_id}")
        result[owner_id] = {
            "kind": "FINAL_ROM_NULL_SCRIPT_POINTER_RECORD",
            "owner_kind": str(owner["owner_kind"]),
            "record_address": _address(
                owner.get("record_address"), f"{owner_id} record",
            ),
            "root_field_address": field,
            "root_field_raw_hex": raw.hex(),
            "root_field_raw_sha256": _sha(raw),
            "non_script_reason": "NULL_SCRIPT_POINTER",
            "rom_sha256": _sha(final_rom),
            "runtime_trigger_required": False,
        }
    return result


def _standard_table_abi_evidence(
    final_rom: bytes, owner: Mapping[str, Any],
) -> dict[str, Any]:
    """COMMON ownerがpinned standard tableのexact entryであることを証明する。"""

    owner_id = str(owner["owner_id"])
    index = int(owner["index"])
    if not 0 <= index < STANDARD_SCRIPT_COUNT \
            or owner_id != f"COMMON:STANDARD:{index:03d}" \
            or owner.get("owner_kind") != "COMMON" \
            or owner.get("root_subkind") != "STANDARD_SCRIPT" \
            or owner.get("physical_provenance") != "COMMON_ENGINE_TABLE" \
            or owner.get("runtime_root") is not True:
        _fail(f"COMMON standard table owner ABI不一致:{owner_id}")
    expected_record = STANDARD_SCRIPT_TABLE + index * 4
    record = _address(owner.get("record_address"), f"{owner_id} record")
    root_field = _address(
        owner.get("root_field_address"), f"{owner_id} root field",
    )
    if record != expected_record or root_field != expected_record:
        _fail(f"COMMON standard table record ABI不一致:{owner_id}")
    raw = _read(final_rom, record, 4, f"{owner_id} table entry")
    pointer = struct.unpack_from("<I", raw)[0]
    root = _address(owner.get("root"), f"{owner_id} root")
    if pointer != root or int(owner.get("raw_root", -1)) != root:
        _fail(f"COMMON standard table pointer ABI不一致:{owner_id}")
    _offset(final_rom, root, 1, f"{owner_id} standard root")
    table_raw = _read(
        final_rom, STANDARD_SCRIPT_TABLE, STANDARD_SCRIPT_COUNT * 4,
        "standard script table ABI",
    )
    return {
        "standard_script_table_address": STANDARD_SCRIPT_TABLE,
        "standard_script_table_count": STANDARD_SCRIPT_COUNT,
        "standard_index": index,
        "record_address": record,
        "root_field_address": root_field,
        "table_entry_raw_hex": raw.hex(),
        "table_entry_raw_sha256": _sha(raw),
        "table_raw_sha256": _sha(table_raw),
        "root_pc": root,
        "record_address_matches_standard_index": True,
        "table_pointer_matches_inventory_root": True,
        "rom_sha256": _sha(final_rom),
    }


def _common_paths(
    final_rom: bytes,
    common_owners: Sequence[Mapping[str, Any]],
    noncommon_runtime_owners: Sequence[Mapping[str, Any]],
    owner_paths: Mapping[str, Mapping[str, Any]],
) -> tuple[
    dict[str, dict[str, Any]], dict[str, dict[str, Any]],
    list[dict[str, Any]], dict[str, dict[str, Any]],
]:
    try:
        from tools.stage61_event_semantic_relocator import SemanticScriptGraph

        graph = SemanticScriptGraph(final_rom)
        roots = sorted({
            int(owner["root"]) for owner in noncommon_runtime_owners
            if owner.get("runtime_root") is True
        })
        graph.walk(roots)
    except (ImportError, RuntimeError, ValueError) as exc:
        _fail(f"COMMON caller CFG decode失敗:{exc}")
    if graph.diagnostics:
        _fail(f"COMMON caller CFG diagnostics:{graph.diagnostics[0]}")
    table_abi = {
        str(owner["owner_id"]): _standard_table_abi_evidence(final_rom, owner)
        for owner in common_owners
    }
    closure_roots = [{
        "owner_id": str(owner["owner_id"]),
        "root_pc": int(owner["root"]),
    } for owner in sorted(
        noncommon_runtime_owners, key=lambda row: str(row["owner_id"]),
    ) if owner.get("runtime_root") is True]
    closure_instructions = [{
        "instruction_pc": instruction.address,
        "opcode": instruction.opcode,
        "raw_hex": instruction.raw.hex(),
    } for node in sorted(graph.nodes.values(), key=lambda row: row.address)
      for instruction in node.instructions]
    closure_provenance = {
        "kind": "FINAL_ROM_ALL_NONCOMMON_RUNTIME_ROOT_CFG_CLOSURE",
        "rom_sha256": _sha(final_rom),
        "noncommon_runtime_owner_count": len(closure_roots),
        "unique_noncommon_runtime_root_count": len(roots),
        "cfg_node_count": len(graph.nodes),
        "cfg_instruction_count": len(closure_instructions),
        "root_bindings_sha256": _sha(_stable(closure_roots)),
        "cfg_instructions_sha256": _sha(_stable(closure_instructions)),
        "semantic_standard_dispatch_opcodes": [0x08, 0x09, 0x0A, 0x0B],
        "conditional_standard_index_operand_offset": 2,
        "unconditional_standard_index_operand_offset": 1,
        "cfg_diagnostics_zero": True,
    }
    candidates: dict[int, list[tuple[Any, ...]]] = defaultdict(list)
    kind_priority = {"OBJECT": 0, "BG": 1, "COORD": 2, "MAP": 3}
    for owner in noncommon_runtime_owners:
        owner_id = str(owner["owner_id"])
        if owner.get("runtime_root") is not True:
            continue
        root = int(owner["root"])
        for node_address, distance in graph.distances(root).items():
            for instruction in graph.nodes[node_address].instructions:
                if instruction.opcode not in {0x08, 0x09, 0x0A, 0x0B}:
                    continue
                index = instruction.raw[1] if instruction.opcode in {0x08, 0x09} \
                    else instruction.raw[2]
                candidates[index].append((
                    distance, kind_priority[str(owner["owner_kind"])],
                    owner_id, instruction.address, owner,
                    owner_id in owner_paths,
                ))
    paths: dict[str, dict[str, Any]] = {}
    evidence: dict[str, dict[str, Any]] = {}
    unresolved: list[dict[str, Any]] = []
    structural: dict[str, dict[str, Any]] = {}
    for owner in sorted(common_owners, key=lambda row: str(row["owner_id"])):
        owner_id = str(owner["owner_id"])
        index = int(owner["index"])
        rows = sorted(candidates.get(index, []), key=lambda row: row[:4])
        if not rows:
            if owner_id == UNREFERENCED_STANDARD_OWNER_ID and index == 7:
                structural[owner_id] = {
                    "kind": "UNREFERENCED_STANDARD_SCRIPT_TABLE_ENTRY",
                    "structural_reason": (
                        "NO_LIVE_NONCOMMON_CALLER_IN_FINAL_ROM_CFG"
                    ),
                    **deepcopy(table_abi[owner_id]),
                    "noncommon_cfg_closure": deepcopy(closure_provenance),
                    "live_caller_instruction_pc_count": 0,
                    "live_caller_owner_path_count": 0,
                    "runtime_trigger_required": False,
                    "direct_common_root_call_forbidden": True,
                    "exact_table_abi_bound": True,
                }
                continue
            unresolved.append({
                "owner_id": owner_id,
                "kind": "COMMON_LIVE_CALLER_BYTECODE_REQUIRED",
                "standard_index": index,
            })
            continue
        triggerable_rows = [row for row in rows if row[5]]
        if not triggerable_rows:
            unresolved.append({
                "owner_id": owner_id,
                "kind": "COMMON_CALLER_OWNER_TRIGGER_PATH_REQUIRED",
                "standard_index": index,
                "live_caller_instruction_pc_count": len({
                    row[3] for row in rows
                }),
            })
            continue
        distance, _priority, caller_id, pc, caller, _triggerable = \
            triggerable_rows[0]
        caller_path = deepcopy(dict(owner_paths[caller_id]))
        path = {
            "kind": "COMMON_CALLER_TRIGGER", "standard_index": index,
            "caller_owner_id": caller_id,
            "caller_owner_kind": str(caller["owner_kind"]),
            "caller_instruction_pc": pc,
            "caller_trigger_path": caller_path,
            "root_pc": int(owner["root"]),
        }
        paths[owner_id] = _validate_with_oracle(final_rom, owner, path)
        evidence[owner_id] = {
            "kind": "LIVE_NONCOMMON_OWNER_CALLSTD_BYTECODE",
            "common_root_pc": f"0x{int(owner['root']):08X}",
            "standard_index": index,
            "caller_owner_id": caller_id,
            "caller_owner_kind": caller["owner_kind"],
            "caller_runtime_root": f"0x{int(caller['root']):08X}",
            "caller_instruction_pc": f"0x{pc:08X}",
            "caller_instruction_raw_hex": _read(
                final_rom, pc, 2 if final_rom[pc - ROM_BASE] in {0x08, 0x09}
                else 3, "COMMON caller instruction",
            ).hex(),
            "caller_cfg_distance": distance,
            "standard_table_abi": deepcopy(table_abi[owner_id]),
            "common_root_and_caller_pc_are_distinct_evidence": True,
            "direct_common_root_call_forbidden": True,
            "direct_script_call_forbidden": True,
        }
    return paths, evidence, unresolved, structural


def build_stage61_runtime_trigger_inputs(
    final_rom: bytes,
    event_owner_inventory: Mapping[str, Any],
    npc_catalog: Mapping[str, Any],
    *,
    placement_audit: Mapping[str, Any],
    hidden_item_consumers: Mapping[str, Any],
    map_callback_contracts: Mapping[str, Any] | None = None,
    require_canonical_counts: bool = True,
    require_complete: bool = True,
) -> dict[str, Any]:
    """Build ``STAGE61_RUNTIME_TRIGGER_INPUTS`` from the exact final ROM.

    Parameters required by the Stage61 builder:

    * ``final_rom`` / ``event_owner_inventory``: exact final physical records;
    * ``npc_catalog`` / ``placement_audit``: final OBJECT
      ``interaction_execution`` (both copies must be equal);
    * ``hidden_item_consumers``: final FACE_A/Itemfinder script roots with
      ROM-bound source provenance; their CFG must contain special 150 and the
      FACE_A coin branch must also contain special 350;
    * ``map_callback_contracts``: needed when MAP tag 5/7 exists.  It supplies
      final-ROM-bound callback/install/dispatch PCs, while this producer supplies and
      validates the actual preceding stock warp, stock connection, or engine
      player-teleport map load and the subsequent START/B field return.

    ``require_canonical_counts=False`` is for focused unit fixtures only.
    Production must leave it at the default so owner cardinalities cannot be
    silently learned from an incomplete inventory.
    """

    if not isinstance(final_rom, bytes) or not final_rom:
        _fail("final_romは非空bytes必須")
    owners, owner_by_id, coordinates, surface_by_map = _inventory_inputs(
        final_rom, event_owner_inventory,
        require_canonical_counts=require_canonical_counts,
    )
    inventory_runtime, null_structural = _runtime_sets(
        final_rom, owners,
        require_canonical_counts=require_canonical_counts,
    )
    inventory_runtime_ids = {
        str(row["owner_id"]) for row in inventory_runtime
    }
    null_structural_ids = {
        str(row["owner_id"]) for row in null_structural
    }
    if inventory_runtime_ids & null_structural_ids \
            or inventory_runtime_ids | null_structural_ids != set(owner_by_id):
        _fail("inventory-root/NULL owner partition不一致")
    object_owners = [
        row for row in inventory_runtime if row["owner_kind"] == "OBJECT"
    ]
    npc_by_id, runtime_object_positions = _execution_index(
        final_rom, object_owners, npc_catalog, placement_audit,
    )
    maps = _FinalRomMaps(
        final_rom, coordinates, runtime_object_positions,
    )
    placement_map_entries = _placement_map_entries(placement_audit)
    hidden_consumers = _hidden_consumers(final_rom, hidden_item_consumers)
    owner_paths: dict[str, dict[str, Any]] = {}
    owner_evidence: dict[str, dict[str, Any]] = {}
    unresolved: list[dict[str, Any]] = []
    stock_warp_cache: dict[
        tuple[int, int], list[tuple[dict[str, Any], dict[str, Any]]]
    ] = {}

    for owner in sorted(
        inventory_runtime, key=lambda row: str(row["owner_id"]),
    ):
        if owner["owner_kind"] == "COMMON":
            continue
        owner_id = str(owner["owner_id"])
        try:
            if owner.get("non_script_reason") == "HIDDEN_ITEM":
                state = maps.state(int(owner["group"]), int(owner["map"]))
                path, evidence = _hidden_path(
                    final_rom, owner, state, hidden_consumers,
                )
            elif owner["owner_kind"] == "OBJECT":
                state = maps.state(int(owner["group"]), int(owner["map"]))
                npc = npc_by_id[owner_id]
                path, evidence = _object_path(final_rom, owner, npc, state)
            elif owner["owner_kind"] == "BG":
                state = maps.state(int(owner["group"]), int(owner["map"]))
                path, evidence = _bg_path(final_rom, owner, state)
            elif owner["owner_kind"] == "COORD":
                state = maps.state(int(owner["group"]), int(owner["map"]))
                path, evidence = _coord_path(final_rom, owner, state)
            elif owner["owner_kind"] == "MAP":
                path, evidence = _map_path(
                    final_rom, owner, maps, surface_by_map,
                    stock_warp_cache, placement_map_entries,
                    map_callback_contracts,
                )
            else:
                _fail(f"非COMMON runtime owner kind不正:{owner_id}")
            validation_owner = owner
            if owner["owner_kind"] == "OBJECT":
                validation_owner = {
                    **owner,
                    "interaction_object": {
                        "x": int(npc["_stage61_runtime_object"][0]),
                        "y": int(npc["_stage61_runtime_object"][1]),
                    },
                    "interaction_object_basis": npc[
                        "_stage61_interaction_object_basis"
                    ],
                    "interaction_distance": int(
                        npc["interaction_execution"][
                            "interaction_distance"
                        ]
                    ),
                }
            owner_paths[owner_id] = _validate_with_oracle(
                final_rom, validation_owner, path,
            )
            owner_evidence[owner_id] = evidence
        except Stage61RuntimeTriggerInputsError as exc:
            unresolved.append({
                "owner_id": owner_id,
                "kind": str(exc).split(":", 1)[0],
                "detail": str(exc),
            })

    common_owners = [
        row for row in inventory_runtime if row["owner_kind"] == "COMMON"
    ]
    noncommon = [
        row for row in inventory_runtime if row["owner_kind"] != "COMMON"
    ]
    common_structural: dict[str, dict[str, Any]] = {}
    try:
        (
            common_paths, common_evidence, common_unresolved,
            common_structural,
        ) = _common_paths(final_rom, common_owners, noncommon, owner_paths)
        owner_paths.update(common_paths)
        owner_evidence.update(common_evidence)
        unresolved.extend(common_unresolved)
    except Stage61RuntimeTriggerInputsError as exc:
        unresolved.extend({
            "owner_id": str(owner["owner_id"]),
            "kind": "COMMON_CALLER_GRAPH_INVALID", "detail": str(exc),
        } for owner in common_owners)

    common_structural_ids = set(common_structural)
    common_by_id = {str(row["owner_id"]): row for row in common_owners}
    if not common_structural_ids <= set(common_by_id):
        _fail("COMMON structural owner集合不正")
    runtime = [
        row for row in inventory_runtime
        if str(row["owner_id"]) not in common_structural_ids
    ]
    structural = [*null_structural, *(
        common_by_id[owner_id] for owner_id in sorted(common_structural_ids)
    )]
    runtime_ids = {str(row["owner_id"]) for row in runtime}
    structural_ids = {str(row["owner_id"]) for row in structural}
    if runtime_ids & structural_ids \
            or runtime_ids | structural_ids != set(owner_by_id):
        _fail("execution runtime/structural owner partition不一致")
    structural_evidence = _null_structural_evidence(
        final_rom, null_structural,
    )
    structural_evidence.update(common_structural)
    if set(structural_evidence) != structural_ids:
        _fail("structural nontrigger evidence owner集合不一致")
    if require_canonical_counts:
        runtime_kinds = dict(sorted(Counter(
            str(row["owner_kind"]) for row in runtime
        ).items()))
        structural_kinds = dict(sorted(Counter(
            str(row["owner_kind"]) for row in structural
        ).items()))
        if len(runtime) != EXPECTED_RUNTIME_REQUIRED_COUNT \
                or len(structural) != EXPECTED_STRUCTURAL_NONTRIGGER_COUNT \
                or runtime_kinds != EXPECTED_RUNTIME_KIND_COUNTS \
                or structural_kinds != EXPECTED_STRUCTURAL_KIND_COUNTS \
                or common_structural_ids != {UNREFERENCED_STANDARD_OWNER_ID}:
            _fail(
                "production execution scope cardinality不一致:"
                f"runtime={len(runtime)}/{runtime_kinds} "
                f"structural={len(structural)}/{structural_kinds} "
                f"common_structural={sorted(common_structural_ids)}"
            )

    path_ids = set(owner_paths)
    missing = sorted(runtime_ids - path_ids)
    extra = sorted(path_ids - runtime_ids)
    if extra:
        _fail(f"runtime owner path余剰:{extra[:5]}")
    unresolved_ids = {str(row["owner_id"]) for row in unresolved}
    if set(missing) != unresolved_ids:
        _fail(
            "runtime missing/unresolved owner集合不一致:"
            f"missing={missing[:5]} unresolved={sorted(unresolved_ids)[:5]}"
        )
    direct_key_hits = [
        owner_id for owner_id, path in owner_paths.items()
        if any(key in path for key in (
            "direct_script_call", "script_entry_call", "direct_callback_call",
        ))
    ]
    if direct_key_hits:
        _fail(f"直接script/callback call key混入:{direct_key_hits[:5]}")
    map_runtime_ids = {
        str(row["owner_id"])
        for row in runtime if row["owner_kind"] == "MAP"
    }
    map_seed_kind_counts = _recount_map_seed_kinds(
        owner_paths, map_runtime_ids,
    )

    counts = {
        "event_owner_count": len(owners),
        "runtime_required_owner_count": len(runtime),
        "generated_owner_path_count": len(owner_paths),
        "structural_nontrigger_owner_count": len(structural),
        "runtime_owner_kind_counts": dict(sorted(Counter(
            str(row["owner_kind"]) for row in runtime
        ).items())),
        "structural_nontrigger_owner_kind_counts": dict(sorted(Counter(
            str(row["owner_kind"]) for row in structural
        ).items())),
        "map_seed_kind_counts": map_seed_kind_counts,
        "unresolved_count": len(unresolved),
        "non_product_shadow_source_count": sum(
            evidence.get("non_product_shadow_alias", {}).get("role")
                == "NON_PRODUCT_SOURCE"
            for evidence in owner_evidence.values()
            if isinstance(evidence.get("non_product_shadow_alias"), Mapping)
        ),
        "canonical_shadow_physical_owner_count": sum(
            evidence.get("non_product_shadow_alias", {}).get("role")
                == "CANONICAL_PHYSICAL_OWNER"
            for evidence in owner_evidence.values()
            if isinstance(evidence.get("non_product_shadow_alias"), Mapping)
        ),
    }
    assertions = {
        "exact_final_rom_inventory_provenance": (
            event_owner_inventory.get("rom_sha256") == _sha(final_rom)
            and event_owner_inventory.get("inventory_sha256")
                == _self_hash_without(
                    event_owner_inventory, "inventory_sha256",
                )
        ),
        "all_event_owners_partitioned_runtime_or_structural": (
            runtime_ids | structural_ids == set(owner_by_id)
            and not runtime_ids & structural_ids
        ),
        "owner_paths_equal_runtime_required_owner_set": path_ids == runtime_ids,
        "structural_nontriggers_listed_exactly_once": (
            len(structural_ids) == len(structural)
        ),
        "all_structural_nontriggers_have_exact_rom_evidence": (
            set(structural_evidence) == structural_ids
            and all(
                row.get("rom_sha256") == _sha(final_rom)
                for row in structural_evidence.values()
            )
        ),
        "unreferenced_common_7_has_zero_live_caller_closure": (
            UNREFERENCED_STANDARD_OWNER_ID not in structural_ids
            or (
                common_structural.get(
                    UNREFERENCED_STANDARD_OWNER_ID, {}
                ).get("live_caller_instruction_pc_count") == 0
                and common_structural.get(
                    UNREFERENCED_STANDARD_OWNER_ID, {}
                ).get("exact_table_abi_bound") is True
                and common_structural.get(
                    UNREFERENCED_STANDARD_OWNER_ID, {}
                ).get("noncommon_cfg_closure", {}).get(
                    "cfg_diagnostics_zero"
                ) is True
            )
        ),
        "all_paths_pass_existing_exact_schema_validator": (
            len(owner_paths) == len(path_ids)
        ),
        "object_paths_bound_to_final_interaction_execution": all(
            owner_evidence.get(str(row["owner_id"]), {}).get("kind")
                == "FINAL_NPC_CATALOG_INTERACTION_EXECUTION"
            and owner_paths.get(str(row["owner_id"]), {}).get("start_tile")
                == _point_dict(_point(
                    npc_by_id[str(row["owner_id"])]["interaction_execution"][
                        "start"
                    ], "OBJECT assertion start",
                ))
            and owner_paths.get(str(row["owner_id"]), {}).get(
                "walk_sequence"
            ) == npc_by_id[str(row["owner_id"])]["interaction_execution"][
                "walk_sequence"
            ]
            and owner_paths.get(str(row["owner_id"]), {}).get("stance_tile")
                == _point_dict(_point(
                    npc_by_id[str(row["owner_id"])]["interaction_execution"][
                        "stance"
                    ], "OBJECT assertion stance",
                ))
            and owner_paths.get(str(row["owner_id"]), {}).get(
                "required_facing"
            ) == npc_by_id[str(row["owner_id"])]["interaction_execution"][
                "action"
            ]
            for row in object_owners if str(row["owner_id"]) in owner_evidence
        ),
        "non_product_shadow_sources_bind_exact_walked_canonical_owners": all(
            isinstance(owner_evidence.get(source_id), Mapping)
            and owner_evidence[source_id].get(
                "actual_walk_exception", {}
            ).get("classification")
                == "CANONICAL_SHADOW_NON_PRODUCT_SOURCE"
            and owner_evidence[source_id].get("actual_walk_steps") == 0
            and isinstance(owner_evidence.get(str(alias["canonical_owner_id"])), Mapping)
            and owner_evidence[str(alias["canonical_owner_id"])].get(
                "actual_walk_steps", 0,
            ) > 0
            and owner_evidence[str(alias["canonical_owner_id"])].get(
                "non_product_shadow_alias", {},
            ).get("role") == "CANONICAL_PHYSICAL_OWNER"
            for source_id, alias in (
                (
                    owner_id,
                    evidence["non_product_shadow_alias"],
                )
                for owner_id, evidence in owner_evidence.items()
                if isinstance(evidence.get("non_product_shadow_alias"), Mapping)
                and evidence["non_product_shadow_alias"].get("role")
                    == "NON_PRODUCT_SOURCE"
            )
        ),
        "production_non_product_shadow_alias_cardinality_is_exact_two": (
            not require_canonical_counts
            or (
                counts["non_product_shadow_source_count"] == 2
                and counts["canonical_shadow_physical_owner_count"] == 2
            )
        ),
        "map_paths_have_actual_engine_map_load_predecessor": all(
            "actual_predecessor" in owner_evidence.get(
                str(row["owner_id"]), {}
            )
            for row in runtime if row["owner_kind"] == "MAP"
            and str(row["owner_id"]) in owner_evidence
        ),
        "map_owner_paths_have_exactly_one_rom_seed_kind": (
            map_runtime_ids <= path_ids
            and sum(map_seed_kind_counts.values()) == len(map_runtime_ids)
        ),
        "engine_teleport_requires_zero_usable_stock_entry": (
            map_runtime_ids <= path_ids
        ),
        "exact_production_map_seed_kind_counts_590_0_38": (
            not require_canonical_counts
            or (
                len(map_runtime_ids) == EXPECTED_RUNTIME_KIND_COUNTS["MAP"]
                and map_seed_kind_counts == EXPECTED_MAP_SEED_KIND_COUNTS
            )
        ),
        "common_paths_bind_distinct_root_and_live_caller_pc": all(
            owner_evidence.get(str(row["owner_id"]), {}).get(
                "common_root_and_caller_pc_are_distinct_evidence"
            ) is True
            for row in common_owners if str(row["owner_id"]) in owner_evidence
        ),
        "direct_script_and_callback_calls_zero": not direct_key_hits,
        "unresolved_zero": not unresolved,
    }
    output = {
        "schema_version": 1,
        "kind": "STAGE61_RUNTIME_TRIGGER_INPUTS",
        "status": "PASS" if not unresolved else "UNRESOLVED",
        "rom_sha256": _sha(final_rom),
        "event_owner_inventory_sha256": event_owner_inventory.get(
            "inventory_sha256"
        ),
        "input_provenance": {
            "event_owner_inventory_rom_sha256": event_owner_inventory.get(
                "rom_sha256"
            ),
            "event_owner_inventory_sha256": event_owner_inventory.get(
                "inventory_sha256"
            ),
            "event_owner_inventory_claimed_self_sha256": (
                event_owner_inventory.get("inventory_sha256")
            ),
            "event_owner_inventory_recomputed_self_sha256": (
                _self_hash_without(
                    event_owner_inventory, "inventory_sha256",
                )
            ),
            "event_owner_inventory_full_document_sha256": _sha(
                _stable(event_owner_inventory)
            ),
            "npc_catalog_sha256": _sha(_stable(npc_catalog)),
            "placement_audit_sha256": _sha(_stable(placement_audit)),
            "hidden_item_consumers_sha256": _sha(
                _stable(hidden_item_consumers)
            ),
            "map_callback_contracts_sha256": None
                if map_callback_contracts is None else
                _sha(_stable(map_callback_contracts)),
        },
        "owner_paths": {
            owner_id: owner_paths[owner_id] for owner_id in sorted(owner_paths)
        },
        "owner_path_evidence": {
            owner_id: owner_evidence[owner_id]
            for owner_id in sorted(owner_evidence)
        },
        "runtime_required_owner_ids": sorted(runtime_ids),
        "structural_nontrigger_owner_ids": sorted(structural_ids),
        "structural_nontrigger_evidence": {
            owner_id: structural_evidence[owner_id]
            for owner_id in sorted(structural_evidence)
        },
        "unresolved": sorted(
            unresolved,
            key=lambda row: (str(row["owner_id"]), str(row["kind"])),
        ),
        "counts": counts,
        "assertions": assertions,
        "policies": {
            "direct_script_calls": 0,
            "direct_callback_calls": 0,
            "object_entry": "FINAL_INTERACTION_EXECUTION_TELEPORT_WALK_FACE_A",
            "bg_entry": "FINAL_FIELD_BFS_WALK_FACE_A",
            "coord_entry": "FINAL_FIELD_BFS_REAL_STEP",
            "map_entry": (
                "STOCK_WARP_OR_STOCK_CONNECTION_OR_ENGINE_PLAYER_TELEPORT"
                "_MAP_LOAD_OPTIONALLY_START_B"
            ),
            "common_entry": "LIVE_NONCOMMON_OWNER_CALLSTD_BYTECODE",
            "common_7_structural_reason": (
                "NO_LIVE_NONCOMMON_CALLER_IN_FINAL_ROM_CFG"
            ),
            "hidden_entry": "FIELD_FACE_A_OR_ITEMFINDER_WITH_SPECIAL_SCAN",
            "coord_and_hidden_approach_direction_source": (
                "owner_paths.trigger_key_or_required_facing"
            ),
            "implicit_up_approach_for_coord_or_hidden_forbidden": True,
        },
    }
    output["document_sha256"] = _sha(_stable(output))
    if require_complete and unresolved:
        summary = Counter(str(row["kind"]) for row in unresolved)
        detail = ",".join(
            f"{key}={value}" for key, value in sorted(summary.items())
        )
        first = unresolved[0]
        _fail(
            "RUNTIME_TRIGGER_INPUTS_UNRESOLVED:"
            f"{len(unresolved)}:{detail}:first={first}"
        )
    if require_complete and not all(assertions.values()):
        _fail(f"runtime trigger inputs assertion不成立:{assertions}")
    if not unresolved:
        validate_stage61_runtime_trigger_inputs_map_seed_contract(
            output, require_canonical_counts=require_canonical_counts,
        )
    return output


__all__ = [
    "EXPECTED_OWNER_COUNT",
    "EXPECTED_MAP_SEED_KIND_COUNTS",
    "EXPECTED_RUNTIME_REQUIRED_COUNT",
    "EXPECTED_STRUCTURAL_NONTRIGGER_COUNT",
    "Stage61RuntimeTriggerInputsError",
    "build_stage61_runtime_trigger_inputs",
    "validate_stage61_runtime_trigger_inputs_map_seed_contract",
]
