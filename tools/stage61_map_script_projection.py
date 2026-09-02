#!/usr/bin/env python3
"""Stage 61 Kanto map-script の地形だけを安全な project-owned IR へ投影する。

clean FireRed の map-script table を丸ごと移植すると、物語進行、trainer、link、
Hall of Fame、credits まで Stage 61 namespace に混入する。このモジュールは253件の
canonical Kanto mapをsource座標へ結び、非空table全95件を固定4分類へ分ける。
地形成立に必要な41件についても、DIRECT rootから ``setmetatile`` (0xA2) と
``setmaplayoutindex`` (0xA7) に至る条件だけを有限状態で全列挙する。生成IRには読み取り
条件と地形命令以外を含めず、未知命令、危険命令、資産不一致はmap単位でfail-closedに
する。

``materialize_projection`` は明示flag/var mappingを受け取り、source pointerを一切
含まないproject-owned map-script table/script byte列を返す。source conditional table
は意図的に一件も生成しない。
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import struct
import sys
from collections import Counter, defaultdict, deque
from copy import deepcopy
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.stage61_event_semantic_relocator import (  # noqa: E402
    OPCODE_NAMES,
    ROM_BASE,
    SemanticScriptGraph,
)
from tools.stage61_interaction_oracle import (  # noqa: E402
    _extract_map_owner_surface,
    _map_header_address,
)
from tools.t02.rom_inventory import COMMAND_LENGTHS  # noqa: E402


SCHEMA_VERSION = 1
TASK = "STAGE61_MAP_SCRIPT_PROJECTION"
MAP_GROUPS_POINTER_SITE = 0x00054B0C
MAP_LAYOUTS_POINTER_SITE = 0x00054A54
EXISTING_MAP_LAYOUT_COUNT = 383
PRIMARY_METATILE_COUNT = 0x280
MAX_ASSIGNMENTS = 4096
MAX_SCRIPT_STEPS = 8192
CLEAN_ROM_SIZE = 0x01000000
STAGE60_ROM_SIZE = 0x02000000
CLEAN_ROM_SHA256 = "1e4af44b0c75cc8649bfb8649dc4ae5850bf5358bd6b9cd0bf779c99f9db1486"

DEFAULT_CLEAN_PATH = Path("inputs/private/FireRed_JPN_Rev0_clean.gba")
DEFAULT_STAGE60_PATH = Path("build/stages/60_wild_species_root_repair.gba")
DEFAULT_CANONICAL_DIR = Path("generated/maps/kanto")
DEFAULT_MAP_GROUPS_PATH = Path("vendor/upstream/pokefirered/data/maps/map_groups.json")

# Classification is deliberately physical/canonical, never inferred from a source opcode.
# A source ROM drift therefore fails the topology assertions instead of silently moving a map.
GAMEPLAY_TOPOLOGY = frozenset(
    {(97, value) for value in (39, 40, 41, *range(48, 58), *range(59, 63), 86, 87)}
    | {(98, 40), (98, 72)}
)
SERVICE_GEOMETRY = frozenset(
    {(98, value) for value in (9, 16, 22, 29, 36, 55, 68, 78, 81, 89, 97, 105)}
)
STORY_GATED_GEOMETRY = frozenset(
    {(97, value) for value in (42, 45, 75, 76, 77, 78)}
    | {(98, 7), (98, 56)}
)
PROJECTABLE_MAPS = GAMEPLAY_TOPOLOGY | SERVICE_GEOMETRY
TOPOLOGY_MAPS = PROJECTABLE_MAPS | STORY_GATED_GEOMETRY

LEAGUE_ELITE_ADAPTERS: Mapping[tuple[int, int], Mapping[str, int]] = {
    (97, 75): {"scene_before": 0, "scene_after": 1, "completion_flag": 0x1408,
               "turn_root": 0x0816949B, "entry_root": 0x081694AA,
               "open_root": 0x08194AE2, "close_root": 0x08194B46,
               "movement_pointer": 0x08194B9D},
    (97, 76): {"scene_before": 1, "scene_after": 2, "completion_flag": 0x1409,
               "turn_root": 0x08169752, "entry_root": 0x08169761,
               "open_root": 0x08194AE2, "close_root": 0x08194B46,
               "movement_pointer": 0x08194B9D},
    (97, 77): {"scene_before": 2, "scene_after": 3, "completion_flag": 0x140A,
               "turn_root": 0x08169A4A, "entry_root": 0x08169A59,
               "open_root": 0x08194AE2, "close_root": 0x08194B46,
               "movement_pointer": 0x08194B9D},
    (97, 78): {"scene_before": 3, "scene_after": 4, "completion_flag": 0x140B,
               "turn_root": 0x08169D1B, "entry_root": 0x08169D2A,
               "open_root": 0x08194B33, "close_root": 0x08169D4B,
               "movement_pointer": 0x08169D94},
}
CHAMPION_ADAPTER = {
    "physical": (97, 79), "turn_root": 0x0816A187,
    "forbidden_story_root": 0x0816A196, "movement_pointer": 0x0816A327,
    "scene_before": 4, "scene_after": 5,
}
LEAGUE_MOVEMENT_PINS: Mapping[int, Mapping[str, Any]] = {
    0x08194B9D: {
        "raw_hex": "1111111111fe",
        "size": 6,
        "sha256": "2c8b00240a9731746b37c6cee323b825aa459db38c6d9dcca133ca0979bb4f76",
    },
    0x08169D94: {
        "raw_hex": "1111121212121212101010101010101212121212121212121212"
                   "1111111111111111fe",
        "size": 35,
        "sha256": "a9b09ff9b5dbec3bff689c1edab8444f2f68819411616e670ce3ecb90d92e090",
    },
    0x0816A327: {
        "raw_hex": "11111111111111111111fe",
        "size": 11,
        "sha256": "abfc16cd115ce706e877c4faed8db055afd3249e2836494dace308706176c40a",
    },
}
BLAINE_PROJECT_COMPLETION_BINDING: Mapping[str, Any] = {
    "physical_map": "098/072",
    "source_flag": 0x04B6,
    # Stage17's project progression table defines 0x1405 as the Saffron
    # prerequisite and 0x1406 as Blaine's completion flag.  The target battle
    # continuation below is the binary producer that proves the latter.
    "target_flag": 0x1406,
    "target_object_address": 0x09403C54,
    "target_object_raw_hex": (
        "0156000005000400030811000000000034b2360900000000"
    ),
    "target_root": 0x0936B234,
    "target_root_prefix_raw_hex": (
        "5a2b051406004cb236092b2c0806004cb2360905f4b336090f"
    ),
    "target_battle_root": 0x0936B3F4,
    "target_battle_prefix_raw_hex": "5c00f5020000ef463609524336",
    "target_continuation": 0x0936B255,
    "target_continuation_raw_hex": "290614",
}
TEMP_FLAG_0001_INSTRUCTIONS = (
    (0x08182E0A, "PROJECTION_READ", "2b0100"),
    (0x08182FC8, "FULL_CFG_READ", "2b0100"),
    (0x08182FFA, "FULL_CFG_SET", "290100"),
    (0x08183012, "FULL_CFG_CLEAR", "2a0100"),
)
SPECIAL_TABLE_ADDRESS = 0x08163068
VERMILION_TRANSITION_PHYSICAL = (98, 40)
VERMILION_TRANSITION_SOURCE_ROOT = 0x08182ED3
VERMILION_TRANSITION_INIT_ROOT = 0x08182ED9
VERMILION_TRANSITION_RETURN_ROOT = 0x08194D53
VERMILION_TRANSITION_SOURCE_ROOT_RAW = bytes.fromhex("04d92e180802")
VERMILION_TRANSITION_INIT_ROOT_RAW = bytes.fromhex(
    "2b64020601534d1908255b011900400480190140058003"
)
VERMILION_TRANSITION_CFG_SHA256 = (
    "3a3b260758e087232c06a24349b98661b336af6ab9911ccdd24d2b7c63f3b927"
)
VERMILION_TRASH_CAN_SPECIAL_ID = 0x015B
VERMILION_TRASH_CAN_SPECIAL_POINTER = 0x080CBFB9
VERMILION_TRASH_CAN_SPECIAL_SPAN_SIZE = 616
VERMILION_TRASH_CAN_SPECIAL_SPAN_SHA256 = (
    "7c95c370673857591d8547e4078a603e5d89155fbe8fa2290c8b8b5a1c9f5fdc"
)

CATEGORY_NAME = {
    "A": "GAMEPLAY_TOPOLOGY",
    "B": "SERVICE_GEOMETRY",
    "C": "STORY_GATED_GEOMETRY",
    "D": "SOURCE_STORY_NON_IMPORT",
}

# These are the only source commands understood by the finite-state extractor. Writes are
# evaluated solely to derive later read conditions; materialization never emits them.
ANALYSIS_OPCODE_ALLOWLIST = frozenset(
    {0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x16, 0x17, 0x18, 0x19,
     0x21, 0x29, 0x2A, 0x2B, 0xA2, 0xA7}
)
MATERIALIZED_OPCODE_ALLOWLIST = frozenset({0x02, 0x05, 0x06, 0x21, 0x2B, 0xA2, 0xA7})
# The Vermilion Gym transition adapter is not generic topology IR.  It is a
# separately pinned, project-owned state producer whose opcodes are audited at
# their own boundaries below.  Keeping the allowlists separate prevents this
# narrow exception from widening the generic projection surface.
MATERIALIZED_EXPLICIT_ADAPTER_OPCODE_ALLOWLIST = frozenset(
    {0x02, 0x06, 0x19, 0x25, 0x2B}
)
MATERIALIZED_ALL_OPCODE_ALLOWLIST = (
    MATERIALIZED_OPCODE_ALLOWLIST | MATERIALIZED_EXPLICIT_ADAPTER_OPCODE_ALLOWLIST
)
TOPOLOGY_OPCODES = frozenset({0xA2, 0xA7})
FORBIDDEN_FAMILIES: Mapping[str, frozenset[int]] = {
    "NATIVE": frozenset({0x23, 0x24}),
    "SPECIAL": frozenset({0x25, 0x26}),
    "WARP": frozenset({0x39, 0x3A, 0x3B, 0x3C, 0x3D, 0x3E, 0x3F, 0x40,
                        0x41, 0xC4, 0xD1}),
    "TRAINER": frozenset(range(0x5C, 0x63)),
    "MOVEMENT_OBJECT": frozenset({0x4F, 0x50, 0x51, 0x52, 0x53, 0x54,
                                   0x55, 0x56, 0x57, 0x58, 0x59, 0x5B,
                                   0x63, 0x64, 0x65, 0xA8, 0xA9, 0xAA,
                                   0xAB, 0xAC, 0xAD, 0xAE, 0xAF, 0xB0}),
    "LINK_MENU": frozenset({0x6E, 0x6F, 0x70, 0x71, 0x72, 0x73, 0x74,
                             0x86, 0x87, 0x88, 0x89, 0x8B, 0x8C, 0x8D,
                             0x8E, 0xB1, 0xB2}),
    "SAVE_CREDITS_HOF": frozenset({0x0D, 0x24, 0x25, 0x26, 0x34, 0xCF}),
}


class Stage61MapScriptProjectionError(RuntimeError):
    """A source/target/canonical invariant cannot be proven without guessing."""


def _fail(message: str) -> None:
    raise Stage61MapScriptProjectionError(message)


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _stable(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def _hex(value: int, width: int = 8) -> str:
    return f"0x{value:0{width}X}"


def _read(rom: bytes, address: int, size: int, label: str) -> bytes:
    offset = address - ROM_BASE
    if address < ROM_BASE or offset < 0 or size < 0 or offset + size > len(rom):
        _fail(f"{label} is outside ROM: {_hex(address)}+{size:#x}")
    return rom[offset:offset + size]


def _u16(raw: bytes, offset: int = 0) -> int:
    return struct.unpack_from("<H", raw, offset)[0]


def _u32(raw: bytes, offset: int = 0) -> int:
    return struct.unpack_from("<I", raw, offset)[0]


def _pointer(rom: bytes, address: int, label: str) -> int:
    value = _u32(_read(rom, address, 4, label))
    _read(rom, value, 1, f"{label} target")
    return value


def _physical_label(pair: tuple[int, int]) -> str:
    return f"{pair[0]:03d}/{pair[1]:03d}"


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        _fail(f"cannot read JSON {path}: {exc}")


def load_canonical_maps(
    canonical_dir: Path,
    map_groups_path: Path,
) -> list[dict[str, Any]]:
    """Load the exact 253 imported maps and bind their clean source coordinates."""

    groups = _load_json(map_groups_path)
    order = groups.get("group_order") if isinstance(groups, Mapping) else None
    if not isinstance(order, list):
        _fail("map_groups.json group_order is missing")
    coordinates: dict[str, tuple[int, int]] = {}
    for group, group_name in enumerate(order):
        names = groups.get(group_name)
        if not isinstance(names, list):
            _fail(f"map_groups.json group is invalid: {group_name}")
        for number, name in enumerate(names):
            if not isinstance(name, str) or name in coordinates:
                _fail(f"clean map name is invalid/duplicate: {name!r}")
            coordinates[name] = (group, number)

    rows: list[dict[str, Any]] = []
    for path in sorted(canonical_dir.glob("*.json")):
        if path.name == "index.json":
            continue
        value = _load_json(path)
        header = value.get("map_header", {}) if isinstance(value, Mapping) else {}
        if header.get("scope_decision") not in {"INCLUDE", "REBUILD"}:
            continue
        source_name = header.get("source_map")
        if source_name not in coordinates:
            _fail(f"{path}: canonical source map is unknown: {source_name!r}")
        group, number = header.get("group_id"), header.get("map_id")
        if isinstance(group, bool) or not isinstance(group, int) \
                or isinstance(number, bool) or not isinstance(number, int):
            _fail(f"{path}: canonical physical coordinate is invalid")
        source_group, source_map = coordinates[source_name]
        layout = value.get("layout")
        if not isinstance(layout, Mapping):
            _fail(f"{path}: canonical layout evidence is missing")
        rows.append({
            "physical": (group, number),
            "physical_map": _physical_label((group, number)),
            "map_key": str(header.get("map_key", "")),
            "source_name": source_name,
            "source": (source_group, source_map),
            "source_map": _physical_label((source_group, source_map)),
            "layout_name": str(header.get("layout", "")),
            "canonical_layout": {
                "width": layout.get("width"), "height": layout.get("height"),
                "blockdata_size": layout.get("blockdata_size"),
                "blockdata_sha256": layout.get("blockdata_sha256"),
                "border_size": layout.get("border_size"),
                "border_sha256": layout.get("border_sha256"),
                "raw_policy": layout.get("raw_policy"),
            },
            "canonical_path": path.as_posix(),
        })
    physical = [row["physical"] for row in rows]
    source = [row["source"] for row in rows]
    if len(rows) != 253 or len(set(physical)) != 253 or len(set(source)) != 253:
        _fail(
            "canonical Kanto cardinality mismatch: "
            f"rows={len(rows)} physical={len(set(physical))} source={len(set(source))}"
        )
    if any(not row["map_key"] or not row["layout_name"] for row in rows):
        _fail("canonical map_key/layout name is empty")
    return sorted(rows, key=lambda row: row["physical"])


def _source_surface(clean_rom: bytes, row: Mapping[str, Any]) -> dict[str, Any]:
    source_group, source_map = row["source"]
    return _extract_map_owner_surface(clean_rom, {
        "group": source_group,
        "map": source_map,
        "map_key": f"CLEAN_SOURCE::{row['source_name']}",
        "provenance": "IMPORTED_KANTO",
    })


def _target_surface(stage60_rom: bytes, row: Mapping[str, Any]) -> dict[str, Any]:
    group, number = row["physical"]
    return _extract_map_owner_surface(stage60_rom, {
        "group": group, "map": number, "map_key": row["map_key"],
        "provenance": "IMPORTED_KANTO",
    })


def _map_script_roots(surface: Mapping[str, Any]) -> list[int]:
    return sorted({
        int(owner["root"])
        for owner in surface.get("owners", [])
        if owner.get("owner_kind") == "MAP" and owner.get("runtime_root")
    })


def _direct_entries(surface: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [
        dict(entry) for entry in surface.get("map_script_structure", [])
        if "root" in entry
    ]


def _graph_for_root(rom: bytes, root: int) -> SemanticScriptGraph:
    graph = SemanticScriptGraph(rom)
    graph.walk([root])
    return graph


def _graph_evidence(graph: SemanticScriptGraph, root: int) -> dict[str, Any]:
    instructions = [
        instruction
        for _address, node in sorted(graph.nodes.items())
        for instruction in node.instructions
    ]
    counts = Counter(instruction.opcode for instruction in instructions)
    topology = [
        {
            "address": _hex(instruction.address),
            "opcode": _hex(instruction.opcode, 2),
            "name": OPCODE_NAMES.get(instruction.opcode, f"opcode_{instruction.opcode:02X}"),
            "raw_hex": instruction.raw.hex(),
        }
        for instruction in instructions if instruction.opcode in TOPOLOGY_OPCODES
    ]
    forbidden = defaultdict(list)
    for instruction in instructions:
        for family, opcodes in FORBIDDEN_FAMILIES.items():
            if instruction.opcode in opcodes:
                forbidden[family].append(_hex(instruction.address))
    return {
        "root": _hex(root),
        "node_count": len(graph.nodes),
        "instruction_count": len(instructions),
        "opcode_counts": {
            _hex(opcode, 2): {
                "name": OPCODE_NAMES.get(opcode, f"opcode_{opcode:02X}"),
                "count": count,
            }
            for opcode, count in sorted(counts.items())
        },
        "topology_actions": topology,
        "topology_action_count": len(topology),
        "forbidden_source_families": dict(sorted(forbidden.items())),
        "diagnostics": deepcopy(graph.diagnostics),
        "cfg_sha256": _sha(_stable([
            [instruction.address, instruction.raw.hex()] for instruction in instructions
        ])),
    }


def _table_evidence(clean_rom: bytes, surface: Mapping[str, Any]) -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    roots: dict[int, dict[str, Any]] = {}
    for entry in surface.get("map_script_structure", []):
        row = {
            "table_index": int(entry["table_index"]),
            "tag": int(entry["script_type"]),
            "entry_kind": "CONDITION" if "conditions" in entry else "DIRECT",
        }
        if "conditions" in entry:
            row["conditions"] = [{
                "condition_index": int(condition["condition_index"]),
                "variable": _hex(int(condition["variable"]), 4),
                "value": _hex(int(condition["value"]), 4),
                "root": _hex(int(condition["root"])),
            } for condition in entry["conditions"]]
            entry_roots = [int(condition["root"]) for condition in entry["conditions"]]
        else:
            root = int(entry["root"])
            row["root"] = _hex(root)
            entry_roots = [root]
        for root in entry_roots:
            if root not in roots:
                roots[root] = _graph_evidence(_graph_for_root(clean_rom, root), root)
        entries.append(row)
    return {
        "table_pointer": _hex(int(surface["map_script_table_pointer"])),
        "entries": entries,
        "entry_count": len(entries),
        "roots": [roots[root] for root in sorted(roots)],
        "unique_root_count": len(roots),
    }


def _classification(pair: tuple[int, int]) -> str:
    if pair in GAMEPLAY_TOPOLOGY:
        return "A"
    if pair in SERVICE_GEOMETRY:
        return "B"
    if pair in STORY_GATED_GEOMETRY:
        return "C"
    return "D"


def _reachable_topology(graph: SemanticScriptGraph) -> bool:
    return any(
        instruction.opcode in TOPOLOGY_OPCODES
        for node in graph.nodes.values() for instruction in node.instructions
    )


def _operand_ids(graph: SemanticScriptGraph) -> tuple[set[int], dict[int, set[int]]]:
    flags: set[int] = set()
    comparisons: dict[int, set[int]] = defaultdict(set)
    for node in graph.nodes.values():
        for instruction in node.instructions:
            raw = instruction.raw
            if instruction.opcode in (0x29, 0x2A, 0x2B):
                flags.add(_u16(raw, 1))
            elif instruction.opcode == 0x21:
                comparisons[_u16(raw, 1)].add(_u16(raw, 3))
    return flags, comparisons


def _var_categories(constants: Iterable[int]) -> list[dict[str, Any]]:
    points = sorted(set(constants))
    rows: list[dict[str, Any]] = []
    cursor = 0
    for point in points:
        if cursor < point:
            rows.append({"kind": "RANGE", "minimum": cursor, "maximum": point - 1,
                         "representative": cursor})
        rows.append({"kind": "EXACT", "value": point, "representative": point})
        cursor = point + 1
    if cursor <= 0xFFFF:
        rows.append({"kind": "RANGE", "minimum": cursor, "maximum": 0xFFFF,
                     "representative": cursor})
    return rows


def _condition_matches(condition: int, comparison: int | None) -> bool:
    if comparison is None:
        _fail("conditional command executed before compare/checkflag")
    predicates = {
        0: comparison < 0,
        1: comparison == 0,
        2: comparison > 0,
        3: comparison <= 0,
        4: comparison >= 0,
        5: comparison != 0,
    }
    if condition not in predicates:
        _fail(f"unknown script condition: {condition}")
    return predicates[condition]


def _action_from_raw(address: int, opcode: int, raw: bytes) -> dict[str, Any]:
    if opcode == 0xA2:
        return {
            "source_address": address, "opcode": opcode,
            "x": _u16(raw, 1), "y": _u16(raw, 3),
            "source_metatile": _u16(raw, 5), "collision": _u16(raw, 7),
            "raw_hex": raw.hex(),
        }
    if opcode == 0xA7:
        return {
            "source_address": address, "opcode": opcode,
            "source_layout": _u16(raw, 1), "raw_hex": raw.hex(),
        }
    _fail(f"not a topology opcode: {opcode:#x}")


def _execute_root(
    rom: bytes,
    root: int,
    flag_values: Mapping[int, bool],
    var_values: Mapping[int, int],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Concrete execution of the deliberately small, audited topology language."""

    flags = dict(flag_values)
    variables = dict(var_values)
    stack: list[int] = []
    pc = root
    comparison: int | None = None
    actions: list[dict[str, Any]] = []
    suppressed_writes: list[dict[str, Any]] = []
    for _step in range(MAX_SCRIPT_STEPS):
        opcode = _read(rom, pc, 1, "projection opcode")[0]
        size = int(COMMAND_LENGTHS.get(opcode, 0))
        if size <= 0:
            _fail(f"unknown opcode {_hex(opcode, 2)} at {_hex(pc)}")
        raw = _read(rom, pc, size, "projection instruction")
        if opcode not in ANALYSIS_OPCODE_ALLOWLIST:
            _fail(
                f"unsafe opcode in topology root {_hex(root)}: "
                f"{OPCODE_NAMES.get(opcode, _hex(opcode, 2))}@{_hex(pc)}"
            )
        next_pc = pc + size
        if opcode == 0x02:  # end
            break
        if opcode == 0x03:  # return
            if not stack:
                break
            pc = stack.pop()
            continue
        if opcode == 0x04:  # call
            stack.append(next_pc)
            pc = _u32(raw, 1)
            continue
        if opcode == 0x05:  # goto
            pc = _u32(raw, 1)
            continue
        if opcode in (0x06, 0x07):
            take = _condition_matches(raw[1], comparison)
            if take:
                if opcode == 0x07:
                    stack.append(next_pc)
                pc = _u32(raw, 2)
                continue
        elif opcode == 0x16:
            variable, value = _u16(raw, 1), _u16(raw, 3)
            variables[variable] = value
            suppressed_writes.append({"address": _hex(pc), "opcode": "0x16",
                                      "variable": _hex(variable, 4), "value": value})
        elif opcode == 0x17:
            variable, value = _u16(raw, 1), _u16(raw, 3)
            variables[variable] = (variables.get(variable, 0) + value) & 0xFFFF
            suppressed_writes.append({"address": _hex(pc), "opcode": "0x17",
                                      "variable": _hex(variable, 4), "value": value})
        elif opcode == 0x18:
            variable, value = _u16(raw, 1), _u16(raw, 3)
            variables[variable] = (variables.get(variable, 0) - value) & 0xFFFF
            suppressed_writes.append({"address": _hex(pc), "opcode": "0x18",
                                      "variable": _hex(variable, 4), "value": value})
        elif opcode == 0x19:
            target, source = _u16(raw, 1), _u16(raw, 3)
            variables[target] = variables.get(source, 0)
            suppressed_writes.append({"address": _hex(pc), "opcode": "0x19",
                                      "variable": _hex(target, 4),
                                      "source_variable": _hex(source, 4)})
        elif opcode == 0x21:
            left, right = variables.get(_u16(raw, 1), 0), _u16(raw, 3)
            comparison = -1 if left < right else 1 if left > right else 0
        elif opcode == 0x29:
            flag = _u16(raw, 1)
            flags[flag] = True
            suppressed_writes.append({"address": _hex(pc), "opcode": "0x29",
                                      "flag": _hex(flag, 4)})
        elif opcode == 0x2A:
            flag = _u16(raw, 1)
            flags[flag] = False
            suppressed_writes.append({"address": _hex(pc), "opcode": "0x2A",
                                      "flag": _hex(flag, 4)})
        elif opcode == 0x2B:
            # checkflag stores TRUE as the condition system's EQUAL state (0).
            comparison = 0 if flags.get(_u16(raw, 1), False) else -1
        elif opcode in TOPOLOGY_OPCODES:
            actions.append(_action_from_raw(pc, opcode, raw))
        pc = next_pc
    else:
        _fail(f"topology execution step limit exceeded: {_hex(root)}")
    return actions, suppressed_writes


def _cube_expansion(
    cube: tuple[int | None, ...], dimensions: Sequence[Sequence[Any]],
) -> Iterable[tuple[int, ...]]:
    choices = [
        range(len(dimensions[index])) if value is None else (value,)
        for index, value in enumerate(cube)
    ]
    return itertools.product(*choices)


def _minimize_positive_points(
    positive: set[tuple[int, ...]], dimensions: Sequence[Sequence[Any]],
) -> list[tuple[int | None, ...]]:
    """Return deterministic exact cubes; a wildcard is admitted only if all points are true."""

    cubes: set[tuple[int | None, ...]] = set()
    for point in sorted(positive):
        cube: tuple[int | None, ...] = tuple(point)
        changed = True
        while changed:
            changed = False
            for index in range(len(cube)):
                if cube[index] is None:
                    continue
                candidate = cube[:index] + (None,) + cube[index + 1:]
                if all(tuple(item) in positive for item in _cube_expansion(candidate, dimensions)):
                    cube = candidate
                    changed = True
        cubes.add(cube)
    # Remove a cube covered by a more general cube.
    result = []
    for cube in sorted(cubes, key=lambda item: (sum(v is not None for v in item),
                                                tuple(-1 if v is None else v for v in item))):
        if any(all(left is None or left == right for left, right in zip(prior, cube))
               for prior in result):
            continue
        result.append(cube)
    covered = set(itertools.chain.from_iterable(
        _cube_expansion(cube, dimensions) for cube in result
    ))
    if covered != positive:
        _fail("guard minimizer did not preserve the complete truth set")
    return result


def _guard_from_cube(
    cube: tuple[int | None, ...],
    dimension_meta: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    predicates: list[dict[str, Any]] = []
    for selected, meta in zip(cube, dimension_meta):
        if selected is None:
            continue
        if meta["kind"] == "FLAG":
            predicates.append({
                "kind": "FLAG_SET" if selected else "FLAG_CLEAR",
                "source_flag": _hex(int(meta["id"]), 4),
            })
            continue
        category = meta["categories"][selected]
        variable = _hex(int(meta["id"]), 4)
        if category["kind"] == "EXACT":
            predicates.append({"kind": "VAR_EQ", "source_var": variable,
                               "value": int(category["value"])})
        else:
            minimum, maximum = int(category["minimum"]), int(category["maximum"])
            if minimum:
                predicates.append({"kind": "VAR_GE", "source_var": variable,
                                   "value": minimum})
            if maximum < 0xFFFF:
                predicates.append({"kind": "VAR_LE", "source_var": variable,
                                   "value": maximum})
    return predicates


def _extract_root_projection(clean_rom: bytes, root: int) -> dict[str, Any]:
    graph = _graph_for_root(clean_rom, root)
    evidence = _graph_evidence(graph, root)
    opcodes = {
        instruction.opcode
        for node in graph.nodes.values() for instruction in node.instructions
    }
    unsafe = sorted(opcodes - ANALYSIS_OPCODE_ALLOWLIST)
    if graph.diagnostics or unsafe:
        return {
            "status": "BLOCKED_UNSAFE_TOPOLOGY_ROOT",
            "root": _hex(root), "evidence": evidence,
            "block_reasons": [
                *(["CFG_DIAGNOSTIC_PRESENT"] if graph.diagnostics else []),
                *[f"UNSUPPORTED_OPCODE:{_hex(opcode, 2)}:{OPCODE_NAMES.get(opcode, 'unknown')}"
                  for opcode in unsafe],
            ],
        }
    flags, comparisons = _operand_ids(graph)
    dimension_meta: list[dict[str, Any]] = [
        {"kind": "FLAG", "id": flag, "values": [False, True]}
        for flag in sorted(flags)
    ]
    for variable in sorted(comparisons):
        categories = _var_categories(comparisons[variable])
        dimension_meta.append({
            "kind": "VAR", "id": variable, "categories": categories,
            "values": [category["representative"] for category in categories],
        })
    dimensions: list[list[Any]] = [list(meta["values"]) for meta in dimension_meta]
    assignment_count = 1
    for dimension in dimensions:
        assignment_count *= len(dimension)
    if assignment_count > MAX_ASSIGNMENTS:
        return {
            "status": "BLOCKED_STATE_SPACE_LIMIT", "root": _hex(root),
            "evidence": evidence, "assignment_count": assignment_count,
            "block_reasons": [f"STATE_SPACE_EXCEEDS_{MAX_ASSIGNMENTS}"],
        }

    action_templates: dict[tuple[Any, ...], dict[str, Any]] = {}
    positive: dict[tuple[Any, ...], set[tuple[int, ...]]] = defaultdict(set)
    suppressed: dict[bytes, dict[str, Any]] = {}
    all_points = list(itertools.product(*(range(len(row)) for row in dimensions))) \
        if dimensions else [tuple()]
    truth_rows: list[list[Any]] = []
    for point in all_points:
        flag_values: dict[int, bool] = {}
        var_values: dict[int, int] = {}
        for selected, meta in zip(point, dimension_meta):
            if meta["kind"] == "FLAG":
                flag_values[int(meta["id"])] = bool(meta["values"][selected])
            else:
                var_values[int(meta["id"])] = int(meta["values"][selected])
        actions, writes = _execute_root(clean_rom, root, flag_values, var_values)
        action_keys: list[tuple[Any, ...]] = []
        for action in actions:
            key = (
                action["source_address"], action["opcode"], action.get("x"),
                action.get("y"), action.get("source_metatile"),
                action.get("collision"), action.get("source_layout"),
            )
            action_templates[key] = action
            positive[key].add(tuple(point))
            action_keys.append(key)
        for write in writes:
            suppressed[_stable(write)] = write
        truth_rows.append([list(point), [list(key) for key in action_keys]])

    actions_report: list[dict[str, Any]] = []
    required_flags: set[int] = set()
    required_vars: set[int] = set()
    for key in sorted(action_templates):
        cubes = _minimize_positive_points(positive[key], dimensions)
        alternatives = [_guard_from_cube(cube, dimension_meta) for cube in cubes]
        for guard in alternatives:
            for predicate in guard:
                if predicate["kind"].startswith("FLAG_"):
                    required_flags.add(int(predicate["source_flag"], 0))
                else:
                    required_vars.add(int(predicate["source_var"], 0))
        action = dict(action_templates[key])
        action.update({
            "source_address": _hex(int(action["source_address"])),
            "opcode": _hex(int(action["opcode"]), 2),
            "name": OPCODE_NAMES.get(
                int(action["opcode"]),
                "setmaplayoutindex" if int(action["opcode"]) == 0xA7
                else f"opcode_{int(action['opcode']):02X}",
            ),
            "guard_alternatives": alternatives,
            "positive_assignment_count": len(positive[key]),
        })
        actions_report.append(action)
    return {
        "status": "EXTRACTED", "root": _hex(root), "evidence": evidence,
        "equivalence_assignment_count": assignment_count,
        "input_dimensions": [{
            "kind": meta["kind"], "source_id": _hex(int(meta["id"]), 4),
            **({"values": [False, True]} if meta["kind"] == "FLAG" else
               {"categories": meta["categories"]}),
        } for meta in dimension_meta],
        "actions": actions_report,
        "action_count": len(actions_report),
        "requirements": {
            "flags": [_hex(value, 4) for value in sorted(required_flags)],
            "vars": [_hex(value, 4) for value in sorted(required_vars)],
        },
        "suppressed_source_writes": sorted(suppressed.values(), key=lambda row: _stable(row)),
        "truth_table_sha256": _sha(_stable(truth_rows)),
        "block_reasons": [],
    }


def _layout_raw(rom: bytes, group: int, number: int) -> tuple[int, bytes]:
    header = _map_header_address(rom, group, number)
    layout = _pointer(rom, header, "map layout")
    return layout, _read(rom, layout, 0x1C, "map layout struct")


def _layout_content(rom: bytes, layout_pointer: int) -> dict[str, Any]:
    raw = _read(rom, layout_pointer, 0x1C, "layout content")
    width, height = struct.unpack_from("<II", raw, 0)
    border_pointer, block_pointer = struct.unpack_from("<II", raw, 8)
    primary, secondary = struct.unpack_from("<II", raw, 0x10)
    border_width, border_height = raw[0x18], raw[0x19]
    if not width or not height or width * height > 65536 \
            or not border_width or not border_height:
        _fail(f"invalid layout geometry at {_hex(layout_pointer)}")
    block = _read(rom, block_pointer, width * height * 2, "layout blockdata")
    border = _read(rom, border_pointer, border_width * border_height * 2,
                   "layout border")
    return {
        "pointer": layout_pointer, "width": width, "height": height,
        "border_width": border_width, "border_height": border_height,
        "block": block, "border": border,
        "primary_tileset": primary, "secondary_tileset": secondary,
    }


def _metatile_signature(rom: bytes, layout: Mapping[str, Any], metatile: int) -> str:
    if not 0 <= metatile <= 0x3FF:
        _fail(f"metatile ID outside 10-bit map ABI: {metatile:#x}")
    if metatile < PRIMARY_METATILE_COUNT:
        tileset, local = int(layout["primary_tileset"]), metatile
    else:
        tileset, local = int(layout["secondary_tileset"]), metatile - PRIMARY_METATILE_COUNT
    header = _read(rom, tileset, 0x18, "tileset header")
    metatiles_pointer, attributes_pointer = _u32(header, 0x0C), _u32(header, 0x14)
    semantic = (
        header[:4]
        + _read(rom, metatiles_pointer + local * 16, 16, "metatile definition")
        + _read(rom, attributes_pointer + local * 4, 4, "metatile attribute")
    )
    return _sha(semantic)


def _layout_signature(rom: bytes, layout_pointer: int) -> dict[str, Any]:
    layout = _layout_content(rom, layout_pointer)
    used = sorted({_u16(layout["block"], index) & 0x03FF
                   for index in range(0, len(layout["block"]), 2)}
                  | {_u16(layout["border"], index) & 0x03FF
                     for index in range(0, len(layout["border"]), 2)})
    semantic = {
        "width": layout["width"], "height": layout["height"],
        "border_width": layout["border_width"],
        "border_height": layout["border_height"],
        "block_sha256": _sha(layout["block"]),
        "border_sha256": _sha(layout["border"]),
        "metatiles": [[value, _metatile_signature(rom, layout, value)] for value in used],
    }
    return {**semantic, "semantic_sha256": _sha(_stable(semantic))}


def _current_layout_evidence(
    clean_rom: bytes, stage60_rom: bytes, row: Mapping[str, Any],
) -> dict[str, Any]:
    source_layout_pointer, _ = _layout_raw(clean_rom, *row["source"])
    target_layout_pointer, _ = _layout_raw(stage60_rom, *row["physical"])
    source = _layout_content(clean_rom, source_layout_pointer)
    target = _layout_content(stage60_rom, target_layout_pointer)
    canonical = row["canonical_layout"]
    source_block_sha, target_block_sha = _sha(source["block"]), _sha(target["block"])
    source_border_sha, target_border_sha = _sha(source["border"]), _sha(target["border"])
    exact = (
        source["width"] == target["width"] == canonical["width"]
        and source["height"] == target["height"] == canonical["height"]
        and source_block_sha == target_block_sha == canonical["blockdata_sha256"]
        and len(source["block"]) == len(target["block"]) == canonical["blockdata_size"]
        and source_border_sha == target_border_sha == canonical["border_sha256"]
        and len(source["border"]) == len(target["border"]) == canonical["border_size"]
        and canonical["raw_policy"] == "CLEAN_MATCH"
    )
    return {
        "source_layout_pointer": _hex(source_layout_pointer),
        "target_layout_pointer": _hex(target_layout_pointer),
        "dimensions": [source["width"], source["height"]],
        "source_block_sha256": source_block_sha,
        "target_block_sha256": target_block_sha,
        "canonical_block_sha256": canonical["blockdata_sha256"],
        "source_border_sha256": source_border_sha,
        "target_border_sha256": target_border_sha,
        "canonical_border_sha256": canonical["border_sha256"],
        "exact": exact,
    }


def _layout_id_pointer(rom: bytes, layout_id: int) -> int:
    if not 1 <= layout_id <= 0xFFFF:
        _fail(f"invalid layout ID: {layout_id}")
    root = _pointer(rom, ROM_BASE + MAP_LAYOUTS_POINTER_SITE, "gMapLayouts root")
    return _pointer(rom, root + (layout_id - 1) * 4, "gMapLayouts entry")


def _resolve_target_layout(
    clean_rom: bytes,
    stage60_rom: bytes,
    row: Mapping[str, Any],
    source_layout_id: int,
    target_layout_count: int,
    clone_layout_id: int | None,
) -> dict[str, Any]:
    source_pointer = _layout_id_pointer(clean_rom, source_layout_id)
    source = _layout_signature(clean_rom, source_pointer)
    hits: list[dict[str, Any]] = []
    # Basic block/border checks discard nearly all rows before metatile signatures are built.
    for target_id in range(1, target_layout_count + 1):
        try:
            target_pointer = _layout_id_pointer(stage60_rom, target_id)
            target_content = _layout_content(stage60_rom, target_pointer)
        except Stage61MapScriptProjectionError:
            continue
        if (
            target_content["width"] != source["width"]
            or target_content["height"] != source["height"]
            or _sha(target_content["block"]) != source["block_sha256"]
            or _sha(target_content["border"]) != source["border_sha256"]
        ):
            continue
        target = _layout_signature(stage60_rom, target_pointer)
        if target["semantic_sha256"] == source["semantic_sha256"]:
            hits.append({"target_layout_id": target_id,
                         "target_layout_pointer": _hex(target_pointer)})
    result: dict[str, Any] = {
        "source_layout_id": source_layout_id,
        "source_layout_pointer": _hex(source_pointer),
        "source_semantic_sha256": source["semantic_sha256"],
        "target_layout_count": target_layout_count,
        "exact_target_candidates": hits,
        "resolved_target_layout_id": hits[0]["target_layout_id"] if len(hits) == 1 else None,
        "resolution_kind": "EXISTING_EXACT" if len(hits) == 1 else "UNRESOLVED",
        "exact": len(hits) == 1,
    }
    if hits or clone_layout_id is None:
        return result

    source_content = _layout_content(clean_rom, source_pointer)
    target_pointer, _target_raw = _layout_raw(stage60_rom, *row["physical"])
    target_content = _layout_content(stage60_rom, target_pointer)
    used = sorted(
        {_u16(source_content["block"], index) & 0x03FF
         for index in range(0, len(source_content["block"]), 2)}
        | {_u16(source_content["border"], index) & 0x03FF
           for index in range(0, len(source_content["border"]), 2)}
    )
    metatile_rows = []
    for metatile in used:
        source_signature = _metatile_signature(clean_rom, source_content, metatile)
        target_signature = _metatile_signature(stage60_rom, target_content, metatile)
        metatile_rows.append({
            "metatile": metatile,
            "source_signature_sha256": source_signature,
            "target_signature_sha256": target_signature,
            "exact": source_signature == target_signature,
        })
    source_raw = _read(clean_rom, source_pointer, 0x1C, "source alternate layout")
    clone_exact = (
        len(hits) == 0
        and source_content["width"] == target_content["width"]
        and source_content["height"] == target_content["height"]
        and all(item["exact"] for item in metatile_rows)
        and clone_layout_id == target_layout_count + source_layout_id - 0x115
    )
    clone = {
        "new_layout_id": clone_layout_id,
        "width": source_content["width"], "height": source_content["height"],
        "border_width": source_content["border_width"],
        "border_height": source_content["border_height"],
        "border_raw_hex": source_content["border"].hex(),
        "border_sha256": _sha(source_content["border"]),
        "blockdata_raw_hex": source_content["block"].hex(),
        "blockdata_sha256": _sha(source_content["block"]),
        "target_primary_tileset_pointer": _hex(int(target_content["primary_tileset"])),
        "target_secondary_tileset_pointer": _hex(int(target_content["secondary_tileset"])),
        "layout_tail_raw_hex": source_raw[0x18:0x1C].hex(),
        "used_metatile_count": len(used),
        "metatile_bindings": metatile_rows,
        "all_used_metatiles_target_exact": all(item["exact"] for item in metatile_rows),
        "source_pointer_reused": False,
        "exact": clone_exact,
    }
    result.update({
        "resolved_target_layout_id": clone_layout_id if clone_exact else None,
        "resolution_kind": "PROJECT_LAYOUT_CLONE" if clone_exact else "UNRESOLVED",
        "clone": clone,
        "exact": clone_exact,
    })
    return result


def _bind_projection_assets(
    clean_rom: bytes,
    stage60_rom: bytes,
    row: Mapping[str, Any],
    root_projections: list[dict[str, Any]],
    target_layout_count: int,
    layout_clone_ids: Mapping[int, int],
) -> tuple[dict[str, Any], list[str]]:
    layout_evidence = _current_layout_evidence(clean_rom, stage60_rom, row)
    failures: list[str] = []
    if not layout_evidence["exact"]:
        failures.append("CURRENT_LAYOUT_NOT_CLEAN_EXACT")
    source_layout_pointer, _ = _layout_raw(clean_rom, *row["source"])
    target_layout_pointer, _ = _layout_raw(stage60_rom, *row["physical"])
    source_layout = _layout_content(clean_rom, source_layout_pointer)
    target_layout = _layout_content(stage60_rom, target_layout_pointer)
    metatiles: dict[int, dict[str, Any]] = {}
    layouts: dict[int, dict[str, Any]] = {}
    for projection in root_projections:
        for action in projection.get("actions", []):
            if action["opcode"] == "0xA2":
                metatile = int(action["source_metatile"])
                if metatile not in metatiles:
                    source_signature = _metatile_signature(clean_rom, source_layout, metatile)
                    target_signature = _metatile_signature(stage60_rom, target_layout, metatile)
                    metatiles[metatile] = {
                        "source_metatile": metatile,
                        "resolved_target_metatile": metatile
                        if source_signature == target_signature else None,
                        "source_signature_sha256": source_signature,
                        "target_signature_sha256": target_signature,
                        "identity_exact": source_signature == target_signature,
                    }
                    if source_signature != target_signature:
                        failures.append(f"METATILE_SEMANTICS_DIFFER:{metatile:#x}")
            elif action["opcode"] == "0xA7":
                layout_id = int(action["source_layout"])
                if layout_id not in layouts:
                    layouts[layout_id] = _resolve_target_layout(
                        clean_rom, stage60_rom, row, layout_id, target_layout_count,
                        layout_clone_ids.get(layout_id),
                    )
                    if not layouts[layout_id]["exact"]:
                        failures.append(f"LAYOUT_MAPPING_NOT_UNIQUE:{layout_id:#x}")
    return {
        "current_layout": layout_evidence,
        "metatile_mappings": [metatiles[value] for value in sorted(metatiles)],
        "layout_mappings": [layouts[value] for value in sorted(layouts)],
    }, sorted(set(failures))


def _projection_for_map(
    clean_rom: bytes,
    stage60_rom: bytes,
    row: Mapping[str, Any],
    surface: Mapping[str, Any],
    target_surface: Mapping[str, Any],
    target_layout_count: int,
    layout_clone_ids: Mapping[int, int],
) -> dict[str, Any]:
    category = _classification(row["physical"])
    topology_entries: list[tuple[dict[str, Any], SemanticScriptGraph]] = []
    excluded_direct: list[dict[str, Any]] = []
    for entry in _direct_entries(surface):
        graph = _graph_for_root(clean_rom, int(entry["root"]))
        evidence = _graph_evidence(graph, int(entry["root"]))
        if _reachable_topology(graph):
            topology_entries.append((entry, graph))
        else:
            excluded_direct.append({
                "table_index": int(entry["table_index"]),
                "tag": int(entry["script_type"]),
                "root": _hex(int(entry["root"])),
                "reason": "DIRECT_ROOT_HAS_NO_TOPOLOGY_ACTION",
                "evidence": evidence,
            })
    excluded_conditions = [{
        "table_index": int(entry["table_index"]),
        "tag": int(entry["script_type"]),
        "condition_count": len(entry.get("conditions", [])),
        "reason": "SOURCE_CONDITIONAL_TABLE_IS_NEVER_PROJECTED",
    } for entry in surface.get("map_script_structure", []) if "conditions" in entry]
    base = {
        "physical_map": row["physical_map"], "group": row["physical"][0],
        "map": row["physical"][1], "map_key": row["map_key"],
        "source_map": row["source_map"], "source_name": row["source_name"],
        "category": category, "category_name": CATEGORY_NAME[category],
        "topology_direct_root_count": len(topology_entries),
        "excluded_direct_roots": excluded_direct,
        "excluded_condition_tables": excluded_conditions,
        "source_full_roots_imported": False,
        "source_conditional_tables_imported": False,
        "target_map_header_pointer": _hex(int(target_surface["header_pointer"])),
        "target_map_script_field_address": _hex(int(target_surface["header_pointer"]) + 8),
        "target_map_script_expected_pointer": _hex(
            int(target_surface["map_script_table_pointer"])
        ),
        "target_map_script_structure_empty": not bool(
            target_surface.get("map_script_structure")
        ),
    }
    if category == "D":
        return {**base, "status": "NOT_IMPORTED_SOURCE_STORY",
                "root_projections": [], "block_reasons": []}
    if category == "C":
        return {
            **base, "status": "BLOCKED_STORY_BINDING_REQUIRED",
            "root_projections": [],
            "block_reasons": [
                "STORY_GATED_GEOMETRY_REQUIRES_PROJECT_OWNED_EXPLICIT_BINDING",
                "SOURCE_STORY_STATE_MUST_NOT_BE_INFERRED_OR_IMPORTED",
            ],
            "topology_source_roots": [
                {"table_index": int(entry["table_index"]),
                 "tag": int(entry["script_type"]),
                 "root": _hex(int(entry["root"])),
                 "evidence": _graph_evidence(graph, int(entry["root"]))}
                for entry, graph in topology_entries
            ],
        }
    if _map_script_roots(target_surface):
        return {
            **base, "status": "BLOCKED_TARGET_TABLE_OCCUPIED",
            "root_projections": [],
            "block_reasons": ["TARGET_MAP_SCRIPT_TABLE_ALREADY_HAS_RUNTIME_ROOTS"],
        }
    root_projections: list[dict[str, Any]] = []
    for entry, _graph in topology_entries:
        projection = _extract_root_projection(clean_rom, int(entry["root"]))
        projection.update({
            "source_table_index": int(entry["table_index"]),
            "script_type": int(entry["script_type"]),
        })
        root_projections.append(projection)
    failures = [
        reason
        for projection in root_projections
        for reason in projection.get("block_reasons", [])
    ]
    if not root_projections:
        failures.append("NO_DIRECT_TOPOLOGY_ROOT")
    assets, asset_failures = _bind_projection_assets(
        clean_rom, stage60_rom, row, root_projections, target_layout_count,
        layout_clone_ids,
    )
    failures.extend(asset_failures)
    requirements = {
        "flags": sorted({value for projection in root_projections
                         for value in projection.get("requirements", {}).get("flags", [])}),
        "vars": sorted({value for projection in root_projections
                        for value in projection.get("requirements", {}).get("vars", [])}),
    }
    action_count = sum(projection.get("action_count", 0) for projection in root_projections)
    if action_count == 0:
        failures.append("NO_EXTRACTED_TOPOLOGY_ACTION")
    return {
        **base,
        "status": "EXTRACTABLE" if not failures else "BLOCKED_FAIL_CLOSED",
        "root_projections": root_projections,
        "projection_action_count": action_count,
        "requirements": requirements,
        "asset_bindings": assets,
        "block_reasons": sorted(set(failures)),
    }


def _target_table_evidence(
    stage60_rom: bytes, rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    result = []
    for row in rows:
        surface = _target_surface(stage60_rom, row)
        structure = surface.get("map_script_structure", [])
        if not structure:
            continue
        result.append({
            "physical_map": row["physical_map"], "map_key": row["map_key"],
            "table_pointer": _hex(int(surface["map_script_table_pointer"])),
            "tags": [int(entry["script_type"]) for entry in structure],
            "roots": [_hex(value) for value in _map_script_roots(surface)],
        })
    return result


def _movement_evidence(clean_rom: bytes, pointer: int) -> dict[str, Any]:
    raw = bytearray()
    for index in range(512):
        value = _read(clean_rom, pointer + index, 1, "League movement")[0]
        raw.append(value)
        if value == 0xFE:
            break
    else:
        _fail(f"League movement has no terminator: {_hex(pointer)}")
    evidence = {
        "pointer": _hex(pointer), "raw_hex": bytes(raw).hex(),
        "size": len(raw), "sha256": _sha(bytes(raw)),
    }
    pin = LEAGUE_MOVEMENT_PINS.get(pointer)
    if pin is not None:
        evidence["pinned"] = dict(pin)
        evidence["pin_exact"] = all(evidence[key] == value for key, value in pin.items())
    return evidence


def _league_entry_geometry_evidence(
    clean_rom: bytes,
    source_by_pair: Mapping[tuple[int, int], tuple[Mapping[str, Any], Mapping[str, Any]]],
) -> list[dict[str, Any]]:
    """Pin the five League entry consumers without treating them as generic projection.

    The four Elite rooms are category C and Champion remains category D. Their tag 2/4
    consumers are nevertheless required by collision-bearing entrances, so the builder must
    replace them with an explicit project-owned adapter. This report gives the exact source
    evidence but never emits the story-bearing roots.
    """

    expected = {
        (97, 75): {"turn": (4, 0x4001, 0), "entry": (2, 0x4068, 0)},
        (97, 76): {"turn": (4, 0x4001, 0), "entry": (2, 0x4068, 1)},
        (97, 77): {"turn": (4, 0x4001, 0), "entry": (2, 0x4068, 2)},
        (97, 78): {"turn": (4, 0x4001, 0), "entry": (2, 0x4068, 3)},
        (97, 79): {"turn": (4, 0x4001, 0), "entry": (2, 0x4001, 0)},
    }
    result: list[dict[str, Any]] = []
    for pair, contract in expected.items():
        if pair not in source_by_pair:
            _fail(f"League entry source table is missing: {pair}")
        row, surface = source_by_pair[pair]
        roles: dict[str, dict[str, Any]] = {}
        for role, (tag, variable, value) in contract.items():
            matches = []
            for entry in surface["map_script_structure"]:
                if int(entry["script_type"]) != tag or "conditions" not in entry:
                    continue
                for condition in entry["conditions"]:
                    if int(condition["variable"]) == variable \
                            and int(condition["value"]) == value:
                        matches.append((entry, condition))
            if len(matches) != 1:
                _fail(f"League {pair} {role} conditional owner is not unique")
            entry, condition = matches[0]
            root = int(condition["root"])
            graph = _graph_for_root(clean_rom, root)
            instructions = [
                instruction for _address, node in sorted(graph.nodes.items())
                for instruction in node.instructions
            ]
            movements = []
            for instruction in instructions:
                if instruction.opcode == 0x4F:
                    movements.append(_movement_evidence(
                        clean_rom, _u32(instruction.raw, 3),
                    ))
            roles[role] = {
                "table_index": int(entry["table_index"]), "tag": tag,
                "condition_variable": _hex(variable, 4),
                "condition_value": _hex(value, 4), "root": _hex(root),
                "root_evidence": _graph_evidence(graph, root),
                "turnobject_player_raw": [
                    instruction.raw.hex() for instruction in instructions
                    if instruction.opcode == 0x5B
                ],
                "movement_payloads": movements,
                "setmetatile_raw": [
                    instruction.raw.hex() for instruction in instructions
                    if instruction.opcode == 0xA2
                ],
            }
        turn = roles["turn"]
        entry = roles["entry"]
        if turn["turnobject_player_raw"] != ["5bff0002"]:
            _fail(f"League {pair} player-facing instruction drifted")
        result.append({
            "physical_map": _physical_label(pair), "map_key": row["map_key"],
            "source_name": row["source_name"],
            "classification": _classification(pair),
            "status": "EXPLICIT_PROJECT_ADAPTER_REQUIRED",
            "turn_on_entry": turn,
            "entry_transition": entry,
            "automatic_projection": False,
            "requirements": [
                "PROJECT_OWNED_LOCAL_ENTRY_STATE",
                "PROJECT_OWNED_PLAYER_FACING_OR_MOVEMENT",
                "PROJECT_OWNED_COLLISION_DOOR_UPDATE" if pair != (97, 79)
                else "PROJECT_OWNED_CHAMPION_ENTRY_MOVEMENT",
                "ON_LOAD_AND_ON_RESUME_GEOMETRY_WHERE_APPLICABLE",
            ],
            "forbidden_in_adapter": [
                "SOURCE_VAR_MAP_SCENE", "SOURCE_STORY_FLAGS", "TRAINER",
                "SPECIAL", "LINK", "CREDITS", "HALL_OF_FAME", "WARP", "SAVE",
            ],
        })
    return result


def _a2_only_root(clean_rom: bytes, root: int) -> dict[str, Any]:
    graph = _graph_for_root(clean_rom, root)
    instructions = [
        instruction for _address, node in sorted(graph.nodes.items())
        for instruction in node.instructions
    ]
    opcodes = [instruction.opcode for instruction in instructions]
    exact = bool(opcodes) and set(opcodes) <= {0x03, 0xA2} and 0xA2 in opcodes \
        and not graph.diagnostics
    return {
        "root": _hex(root), "status": "A2_ONLY" if exact else "BLOCKED",
        "raw_actions": [instruction.raw.hex() for instruction in instructions
                        if instruction.opcode == 0xA2],
        "opcode_sequence": [_hex(opcode, 2) for opcode in opcodes],
        "evidence": _graph_evidence(graph, root), "exact": exact,
    }


def build_league_explicit_adapter_contract(
    clean_rom: bytes,
    league_entry_geometry: Sequence[Mapping[str, Any]],
    target_nonempty_tables: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Return the bounded exception contract consumed by the Stage61 builder.

    This is not an exemption from the projection denylist. Source roots are provenance only;
    emitted scripts must be rebuilt from the listed movement/A2 bytes and project state.
    """

    by_pair = {
        (int(row["physical_map"].split("/")[0]),
         int(row["physical_map"].split("/")[1])): row
        for row in league_entry_geometry
    }
    elite: list[dict[str, Any]] = []
    exact = True
    for pair, spec in LEAGUE_ELITE_ADAPTERS.items():
        row = by_pair.get(pair)
        if row is None:
            _fail(f"League explicit adapter evidence missing: {pair}")
        turn, entry = row["turn_on_entry"], row["entry_transition"]
        roots_exact = (
            int(turn["root"], 0) == spec["turn_root"]
            and int(entry["root"], 0) == spec["entry_root"]
        )
        movement_exact = (
            len(entry["movement_payloads"]) == 1
            and int(entry["movement_payloads"][0]["pointer"], 0)
                == spec["movement_pointer"]
            and entry["movement_payloads"][0].get("pin_exact") is True
        )
        open_geometry = _a2_only_root(clean_rom, spec["open_root"])
        close_geometry = _a2_only_root(clean_rom, spec["close_root"])
        exact &= (
            roots_exact and movement_exact
            and open_geometry["exact"] and close_geometry["exact"]
        )
        elite.append({
            "physical_map": _physical_label(pair), "map_key": row["map_key"],
            "status": "READY_FOR_EXPLICIT_BUILDER" if roots_exact and movement_exact
                      and open_geometry["exact"] and close_geometry["exact"]
                      else "BLOCKED",
            "table_contract": {
                "tag_1_on_load": {
                    "completion_flag": _hex(spec["completion_flag"], 4),
                    "when_complete": "APPLY_EXIT_OPEN_A2",
                    "when_scene_is_current": "APPLY_ENTRY_CLOSE_A2",
                },
                "tag_2_entry": {
                    "condition": {
                        "project_scene_var": "NON_IDENTITY_BINDING_REQUIRED",
                        "equals": spec["scene_before"],
                    },
                    "operations": [
                        "PROJECT_OWNED_ENTRY_MOVEMENT",
                        "APPLY_ENTRY_CLOSE_A2",
                        f"SET_PROJECT_SCENE_VAR_{spec['scene_after']}",
                    ],
                },
                "tag_4_turn": {
                    "condition_var": "TEMP_1", "condition_value": 0,
                    "source_root": _hex(spec["turn_root"]),
                    "semantic_rebuild": "TURN_PLAYER_DIRECTION_2",
                },
                "tag_5_battle_resume": {
                    "condition_flag": _hex(spec["completion_flag"], 4),
                    "operations": ["APPLY_EXIT_OPEN_A2", "DRAW_WHOLE_MAP_VIEW"],
                    "source_story_root_imported": False,
                },
            },
            "source_cfg_bounds": {
                "turn_root": _hex(spec["turn_root"]),
                "entry_reference_root": _hex(spec["entry_root"]),
                "entry_reference_root_materialized_verbatim": False,
            },
            "entry_movement_payloads": deepcopy(entry["movement_payloads"]),
            "entry_movement_pin_exact": movement_exact,
            "exit_open_geometry": open_geometry,
            "entry_close_geometry": close_geometry,
            "source_var_0x4068_imported": False,
            "source_story_flags_imported": False,
        })

    champion_row = by_pair.get(CHAMPION_ADAPTER["physical"])
    if champion_row is None:
        _fail("Champion explicit adapter evidence missing")
    champion_turn = champion_row["turn_on_entry"]
    champion_entry = champion_row["entry_transition"]
    champion_movement = _movement_evidence(
        clean_rom, CHAMPION_ADAPTER["movement_pointer"],
    )
    champion_exact = (
        int(champion_turn["root"], 0) == CHAMPION_ADAPTER["turn_root"]
        and int(champion_entry["root"], 0) == CHAMPION_ADAPTER["forbidden_story_root"]
        and champion_movement.get("pin_exact") is True
    )
    exact &= champion_exact
    champion = {
        "physical_map": "097/079", "map_key": champion_row["map_key"],
        "status": "READY_FOR_EXPLICIT_BUILDER" if champion_exact else "BLOCKED",
        "tag_4_turn": {
            "condition_var": "TEMP_1", "condition_value": 0,
            "source_root": _hex(CHAMPION_ADAPTER["turn_root"]),
            "semantic_rebuild": "TURN_PLAYER_DIRECTION_2",
        },
        "tag_2_entry": {
            "condition": {
                "project_scene_var": "NON_IDENTITY_BINDING_REQUIRED",
                "equals": CHAMPION_ADAPTER["scene_before"],
            },
            "movement": champion_movement,
            "movement_semantics": "WALK_UP_10",
            "set_project_scene_var": CHAMPION_ADAPTER["scene_after"],
        },
        "forbidden_source_story_root": _hex(CHAMPION_ADAPTER["forbidden_story_root"]),
        "forbidden_source_story_root_imported": False,
    }
    hof = [row for row in target_nonempty_tables if row["physical_map"] == "097/080"]
    hof_exact = len(hof) == 1 and hof[0]["tags"] == [3]
    exact &= hof_exact
    contract = {
        "schema_version": 1,
        "status": "READY" if exact else "BLOCKED",
        "policy": {
            "source_var_0x4068": "NEVER_IDENTITY_MAP",
            "project_scene_var": "DEDICATED_PERSISTENT_VAR_REQUIRED",
            "scene_sequence": [0, 1, 2, 3, 4, 5],
            "source_story_roots": "PROVENANCE_ONLY_NOT_VERBATIM_PAYLOAD",
            "safe_payload": "PROJECT_OWNED_MOVEMENT_AND_A2_ONLY",
            "scene_lifecycle": {
                "initial_value": 0,
                "advance": "MONOTONIC_HIGH_WATER_MARK_ON_PHYSICAL_ROOM_ENTRY",
                "mid_room_save_reload": "PRESERVE_TO_AVOID_REPLAYING_ENTRY_MOVEMENT",
                "blackout_retry": "PRESERVE_DEFEATED_ROOM_PROGRESS",
                "completed_revisit": "KEEP_5_AND_LEAVE_COMPLETION_DOORS_OPEN",
                "rematch_geometry": "COMPLETED_OPEN_NO_FORCED_ENTRY_REPLAY",
                "reset_writer": "NONE_BY_DESIGN",
            },
        },
        "elite_rooms": elite,
        "champion_room": champion,
        "hall_of_fame": {
            "physical_map": "097/080", "policy": "PRESERVE_EXISTING_PROJECT_TAG_3_ONLY",
            "target_evidence": deepcopy(hof[0]) if hof else None,
            "exact": hof_exact,
        },
        "assertions": {
            "elite_4_exact": len(elite) == 4 and all(
                row["status"] == "READY_FOR_EXPLICIT_BUILDER" for row in elite
            ),
            "all_movement_payloads_pinned_exact": (
                all(row["entry_movement_pin_exact"] for row in elite)
                and champion_movement.get("pin_exact") is True
            ),
            "champion_walk_up_10_exact": champion_exact,
            "source_scene_var_requires_nonidentity_mapping": True,
            "source_story_roots_not_materialized": all(
                not row["source_cfg_bounds"]["entry_reference_root_materialized_verbatim"]
                for row in elite
            ) and not champion["forbidden_source_story_root_imported"],
            "hof_existing_tag_3_preserved": hof_exact,
            "scene_lifecycle_is_explicit_high_water_policy": True,
        },
    }
    contract["contract_sha256"] = _sha(_stable(contract))
    return contract


def _build_blaine_project_completion_binding(
    stage60_rom: bytes,
    flag_consumers: Mapping[str, Sequence[str]],
) -> dict[str, Any]:
    """Pin the project battle producer before binding source topology state."""

    spec = BLAINE_PROJECT_COMPLETION_BINDING
    evidence_fields = (
        ("target_object_address", "target_object_raw_hex"),
        ("target_root", "target_root_prefix_raw_hex"),
        ("target_battle_root", "target_battle_prefix_raw_hex"),
        ("target_continuation", "target_continuation_raw_hex"),
    )
    evidence: list[dict[str, Any]] = []
    exact = True
    for address_key, raw_key in evidence_fields:
        expected = bytes.fromhex(str(spec[raw_key]))
        address = int(spec[address_key])
        actual = _read(stage60_rom, address, len(expected), f"Blaine {address_key}")
        row_exact = actual == expected
        exact &= row_exact
        evidence.append({
            "role": address_key,
            "address": _hex(address),
            "expected_raw_hex": expected.hex(),
            "actual_raw_hex": actual.hex(),
            "sha256": _sha(actual),
            "exact": row_exact,
        })
    source = int(spec["source_flag"])
    consumers = sorted(set(flag_consumers.get(_hex(source, 4), [])))
    consumer_exact = consumers == [str(spec["physical_map"])]
    exact &= consumer_exact
    return {
        "status": "READY" if exact else "BLOCKED",
        "physical_map": spec["physical_map"],
        "source_flag": _hex(source, 4),
        "target_project_flag": _hex(int(spec["target_flag"]), 4),
        "binding": "PROJECT_BLAINE_COMPLETION_FLAG",
        "source_consumers": consumers,
        "evidence": evidence,
        "assertions": {
            "source_consumer_unique_to_cinnabar_gym": consumer_exact,
            "target_object_and_battle_flow_exact": all(
                row["exact"] for row in evidence
            ),
            "continuation_sets_project_completion_0x1406": (
                evidence[-1]["actual_raw_hex"] == "290614"
            ),
        },
    }


def _vermilion_adjacent_switch_pairs() -> list[list[int]]:
    """Return every directed orthogonal pair in the stock 5x3 can grid."""

    pairs: list[list[int]] = []
    for first in range(1, 16):
        row, column = divmod(first - 1, 5)
        for d_row, d_column in ((-1, 0), (0, -1), (0, 1), (1, 0)):
            other_row, other_column = row + d_row, column + d_column
            if 0 <= other_row < 3 and 0 <= other_column < 5:
                pairs.append([first, other_row * 5 + other_column + 1])
    return sorted(pairs)


def _build_vermilion_transition_adapter_contract(
    clean_rom: bytes,
    stage60_rom: bytes,
    projections: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Pin the omitted tag-3 trash-can state producer without importing story CFG.

    Generic projection intentionally retains topology commands only.  Vermilion
    Gym is the one A/B map whose excluded OnTransition root creates volatile
    switch IDs consumed by the already-relocated trash-can scripts.  This
    contract proves the exact stock root and native special, then authorizes a
    minimal project-owned rebuild rather than copying either source pointer.
    """

    physical = _physical_label(VERMILION_TRANSITION_PHYSICAL)
    rows = [row for row in projections if row.get("physical_map") == physical]
    if len(rows) != 1:
        _fail(f"Vermilion transition projection row is not unique: {len(rows)}")
    row = rows[0]
    excluded = [
        item for item in row.get("excluded_direct_roots", [])
        if int(str(item.get("root", "0")), 0) == VERMILION_TRANSITION_SOURCE_ROOT
    ]
    excluded_exact = (
        len(excluded) == 1
        and int(excluded[0].get("table_index", -1)) == 1
        and int(excluded[0].get("tag", -1)) == 3
        and excluded[0].get("reason") == "DIRECT_ROOT_HAS_NO_TOPOLOGY_ACTION"
        and excluded[0].get("evidence", {}).get("cfg_sha256")
            == VERMILION_TRANSITION_CFG_SHA256
        and excluded[0].get("evidence", {}).get("instruction_count") == 9
    )

    source_root_raw = _read(
        clean_rom, VERMILION_TRANSITION_SOURCE_ROOT,
        len(VERMILION_TRANSITION_SOURCE_ROOT_RAW),
        "Vermilion OnTransition source root",
    )
    init_root_raw = _read(
        clean_rom, VERMILION_TRANSITION_INIT_ROOT,
        len(VERMILION_TRANSITION_INIT_ROOT_RAW),
        "Vermilion trash-can init root",
    )
    return_raw = _read(
        clean_rom, VERMILION_TRANSITION_RETURN_ROOT, 1,
        "Vermilion source EventScript_Return",
    )
    special_entry_address = (
        SPECIAL_TABLE_ADDRESS + VERMILION_TRASH_CAN_SPECIAL_ID * 4
    )
    clean_special_entry = _read(
        clean_rom, special_entry_address, 4,
        "clean SetVermilionTrashCans special table entry",
    )
    stage60_special_entry = _read(
        stage60_rom, special_entry_address, 4,
        "Stage60 SetVermilionTrashCans special table entry",
    )
    clean_special_pointer = _u32(clean_special_entry)
    stage60_special_pointer = _u32(stage60_special_entry)
    special_target = VERMILION_TRASH_CAN_SPECIAL_POINTER & ~1
    clean_special_span = _read(
        clean_rom, special_target, VERMILION_TRASH_CAN_SPECIAL_SPAN_SIZE,
        "clean SetVermilionTrashCans span",
    )
    stage60_special_span = _read(
        stage60_rom, special_target, VERMILION_TRASH_CAN_SPECIAL_SPAN_SIZE,
        "Stage60 SetVermilionTrashCans span",
    )
    allowed_pairs = _vermilion_adjacent_switch_pairs()
    assertions = {
        "physical_and_source_identity_exact": (
            row.get("source_map") == "009/006"
            and row.get("source_name") == "VermilionCity_Gym"
            and row.get("status") == "EXTRACTABLE"
        ),
        "excluded_tag_3_root_exact": excluded_exact,
        "source_wrapper_and_init_bytes_exact": (
            source_root_raw == VERMILION_TRANSITION_SOURCE_ROOT_RAW
            and init_root_raw == VERMILION_TRANSITION_INIT_ROOT_RAW
            and return_raw == b"\x03"
        ),
        "special_015b_table_identity_exact": (
            clean_special_pointer == VERMILION_TRASH_CAN_SPECIAL_POINTER
            and stage60_special_pointer == VERMILION_TRASH_CAN_SPECIAL_POINTER
            and clean_special_entry == stage60_special_entry
        ),
        "special_015b_full_span_identity_exact": (
            clean_special_span == stage60_special_span
            and _sha(clean_special_span)
                == VERMILION_TRASH_CAN_SPECIAL_SPAN_SHA256
        ),
        "switch_pair_domain_is_complete_5x3_orthogonal": (
            len(allowed_pairs) == 44
            and len({tuple(pair) for pair in allowed_pairs}) == 44
            and all(
                1 <= first <= 15 and 1 <= second <= 15
                and first != second
                and (
                    abs(first - second) == 5
                    or (
                        abs(first - second) == 1
                        and (first - 1) // 5 == (second - 1) // 5
                    )
                )
                for first, second in allowed_pairs
            )
        ),
    }
    contract = {
        "schema_version": 1,
        "status": "READY" if all(assertions.values()) else "BLOCKED",
        "physical_map": physical,
        "map_key": row.get("map_key"),
        "source_map": row.get("source_map"),
        "source_name": row.get("source_name"),
        "source_table_index": 1,
        "script_type": 3,
        "source_wrapper_root": _hex(VERMILION_TRANSITION_SOURCE_ROOT),
        "source_init_root": _hex(VERMILION_TRANSITION_INIT_ROOT),
        "source_return_root": _hex(VERMILION_TRANSITION_RETURN_ROOT),
        "source_wrapper_raw_hex": source_root_raw.hex(),
        "source_init_raw_hex": init_root_raw.hex(),
        "source_cfg_sha256": VERMILION_TRANSITION_CFG_SHA256,
        "completion_source_flag": "0x0264",
        "selection_special": {
            "id": _hex(VERMILION_TRASH_CAN_SPECIAL_ID, 4),
            "table_entry_address": _hex(special_entry_address),
            "table_entry_raw_hex": clean_special_entry.hex(),
            "target_pointer": _hex(clean_special_pointer),
            "span_size": VERMILION_TRASH_CAN_SPECIAL_SPAN_SIZE,
            "span_sha256": _sha(clean_special_span),
            "symbol": "SetVermilionTrashCans",
        },
        "special_output_vars": ["0x8004", "0x8005"],
        "volatile_target_vars": ["0x4000", "0x4001"],
        "allowed_directed_switch_pairs": allowed_pairs,
        "semantic_rebuild": [
            "IF_PROJECT_COMPLETION_FLAG_SET_END",
            "CALL_PINNED_SPECIAL_015B",
            "COPY_0x8004_TO_VAR_TEMP_0",
            "COPY_0x8005_TO_VAR_TEMP_1",
            "END",
        ],
        "source_wrapper_materialized_verbatim": False,
        "source_init_root_materialized_verbatim": False,
        "source_pointer_literals_permitted": False,
        "assertions": assertions,
    }
    contract["contract_sha256"] = _sha(_stable(contract))
    return contract


def build_projection_plan(
    clean_rom: bytes,
    stage60_rom: bytes,
    canonical_maps: Sequence[Mapping[str, Any]],
    *,
    require_ready: bool = True,
) -> dict[str, Any]:
    """Build the exact 95-map classification and safe 41-map projection plan."""

    if not isinstance(clean_rom, bytes) or not isinstance(stage60_rom, bytes):
        _fail("clean_rom and stage60_rom must be immutable bytes")
    clean_digest = _sha(clean_rom)
    if len(clean_rom) != CLEAN_ROM_SIZE or clean_digest != CLEAN_ROM_SHA256:
        _fail(
            "clean FireRed JPN Rev.0 identity mismatch: "
            f"size={len(clean_rom)} sha256={clean_digest}"
        )
    if len(stage60_rom) != STAGE60_ROM_SIZE:
        _fail(f"Stage60 ROM size mismatch: {len(stage60_rom)}")
    rows = [dict(row) for row in canonical_maps]
    if len(rows) != 253 or len({tuple(row["physical"]) for row in rows}) != 253:
        _fail("canonical input must contain exactly 253 unique physical maps")
    source_rows: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for row in rows:
        surface = _source_surface(clean_rom, row)
        if surface.get("findings"):
            _fail(f"clean source surface findings at {row['physical_map']}: {surface['findings']}")
        if surface.get("map_script_structure"):
            source_rows.append((row, surface))
    nonempty_pairs = {tuple(row["physical"]) for row, _surface in source_rows}
    if len(source_rows) != 95:
        _fail(f"clean nonempty map-script table count drifted: {len(source_rows)} != 95")
    missing_fixed = TOPOLOGY_MAPS - nonempty_pairs
    if missing_fixed:
        _fail(f"fixed topology maps lost source tables: {sorted(missing_fixed)}")

    classification_rows: list[dict[str, Any]] = []
    actual_topology: set[tuple[int, int]] = set()
    table_entry_count = 0
    root_fields = 0
    unique_roots: set[int] = set()
    tag_counts: Counter[int] = Counter()
    for row, surface in source_rows:
        table = _table_evidence(clean_rom, surface)
        topology_count = sum(
            int(root["topology_action_count"]) for root in table["roots"]
        )
        if topology_count:
            actual_topology.add(tuple(row["physical"]))
        table_entry_count += table["entry_count"]
        for entry in surface["map_script_structure"]:
            tag_counts[int(entry["script_type"])] += 1
            if "conditions" in entry:
                root_fields += len(entry["conditions"])
                unique_roots.update(int(item["root"]) for item in entry["conditions"])
            else:
                root_fields += 1
                unique_roots.add(int(entry["root"]))
        category = _classification(tuple(row["physical"]))
        classification_rows.append({
            "physical_map": row["physical_map"], "group": row["physical"][0],
            "map": row["physical"][1], "map_key": row["map_key"],
            "source_map": row["source_map"], "source_name": row["source_name"],
            "category": category, "category_name": CATEGORY_NAME[category],
            "topology_action_count": topology_count,
            "table": table,
        })
    if actual_topology != TOPOLOGY_MAPS:
        _fail(
            "topology opcode map set drifted: "
            f"missing={sorted(TOPOLOGY_MAPS-actual_topology)} "
            f"extra={sorted(actual_topology-TOPOLOGY_MAPS)}"
        )
    category_counts = Counter(row["category"] for row in classification_rows)
    expected_counts = Counter({"A": 21, "B": 12, "C": 8, "D": 54})
    if category_counts != expected_counts:
        _fail(f"classification cardinality drifted: {category_counts} != {expected_counts}")

    target_nonempty = _target_table_evidence(stage60_rom, rows)
    target_pairs = {(row["physical_map"], tuple(row["tags"])) for row in target_nonempty}
    expected_target = {("096/005", (3,)), ("097/080", (3,))}
    if target_pairs != expected_target:
        _fail(f"Stage60 target map-script surface drifted: {sorted(target_pairs)}")

    canonical_layout_count = len({row["layout_name"] for row in rows})
    target_layout_count = EXISTING_MAP_LAYOUT_COUNT + canonical_layout_count
    layout_clone_ids = {
        0x116: target_layout_count + 1,
        0x117: target_layout_count + 2,
    }
    projections: list[dict[str, Any]] = []
    source_by_pair = {tuple(row["physical"]): (row, surface)
                      for row, surface in source_rows}
    for pair in sorted(nonempty_pairs):
        row, surface = source_by_pair[pair]
        target_surface = _target_surface(stage60_rom, row)
        projections.append(_projection_for_map(
            clean_rom, stage60_rom, row, surface, target_surface,
            target_layout_count, layout_clone_ids,
        ))

    league_entry_geometry = _league_entry_geometry_evidence(
        clean_rom, source_by_pair,
    )
    league_adapter_contract = build_league_explicit_adapter_contract(
        clean_rom, league_entry_geometry, target_nonempty,
    )
    vermilion_transition_adapter_contract = (
        _build_vermilion_transition_adapter_contract(
            clean_rom, stage60_rom, projections,
        )
    )

    projectable = [row for row in projections if row["category"] in {"A", "B"}]
    story_blocked = [row for row in projections if row["category"] == "C"]
    layout_clones_by_id: dict[int, dict[str, Any]] = {}
    for row in projectable:
        for binding in row.get("asset_bindings", {}).get("layout_mappings", []):
            if binding.get("resolution_kind") != "PROJECT_LAYOUT_CLONE":
                continue
            clone = deepcopy(binding["clone"])
            clone.update({
                "source_layout_id": int(binding["source_layout_id"]),
                "source_layout_pointer": binding["source_layout_pointer"],
                "physical_map": row["physical_map"], "map_key": row["map_key"],
            })
            new_id = int(clone["new_layout_id"])
            prior = layout_clones_by_id.setdefault(new_id, clone)
            if prior != clone:
                _fail(f"layout clone ID collision: {new_id}")
    target_layout_root = _pointer(
        stage60_rom, ROM_BASE + MAP_LAYOUTS_POINTER_SITE, "Stage60 gMapLayouts root",
    )
    existing_layout_table = _read(
        stage60_rom, target_layout_root, target_layout_count * 4,
        "Stage60 gMapLayouts table",
    )
    layout_extension = {
        "status": "READY" if len(layout_clones_by_id) == 2
                  and all(row["exact"] for row in layout_clones_by_id.values())
                  else "BLOCKED",
        "pointer_site": _hex(ROM_BASE + MAP_LAYOUTS_POINTER_SITE),
        "expected_root_pointer": _hex(target_layout_root),
        "existing_count": target_layout_count,
        "expanded_count": target_layout_count + len(layout_clones_by_id),
        "existing_table_raw_hex": existing_layout_table.hex(),
        "existing_table_sha256": _sha(existing_layout_table),
        "clones": [layout_clones_by_id[value] for value in sorted(layout_clones_by_id)],
        "source_layout_pointer_reused": False,
    }
    projection_opcode_set = sorted({
        action["opcode"]
        for row in projectable for projection in row.get("root_projections", [])
        for action in projection.get("actions", [])
    })
    flag_consumers: dict[str, list[str]] = defaultdict(list)
    var_consumers: dict[str, list[str]] = defaultdict(list)
    for row in projectable:
        for value in row.get("requirements", {}).get("flags", []):
            flag_consumers[value].append(row["physical_map"])
        for value in row.get("requirements", {}).get("vars", []):
            var_consumers[value].append(row["physical_map"])
    temp_flag_instructions = []
    for address, role, expected_raw in TEMP_FLAG_0001_INSTRUCTIONS:
        opcode = _read(clean_rom, address, 1, "TEMP_FLAG_0001 opcode")[0]
        size = int(COMMAND_LENGTHS.get(opcode, 0))
        raw = _read(clean_rom, address, size, "TEMP_FLAG_0001 instruction")
        temp_flag_instructions.append({
            "address": _hex(address), "role": role, "raw_hex": raw.hex(),
            "expected_raw_hex": expected_raw, "exact": raw.hex() == expected_raw,
        })
    temp_flag_0001_abi = {
        "source_id": "0x0001", "namespace": "TEMP_FLAG",
        "lifetime": "MAP_TRANSITION_CLEARED_ENGINE_VOLATILE_STATE",
        "mapping_policy": "EXPLICIT_IDENTITY_REQUIRED",
        "projection_consumers": ["098/040"],
        "full_cfg_producer_consumer_instructions": temp_flag_instructions,
        "producer_consumer_identity_exact": (
            flag_consumers.get("0x0001") == ["098/040"]
            and all(row["exact"] for row in temp_flag_instructions)
        ),
    }
    state_requirements = {
        "mapping_policy": "EXPLICIT_NAMESPACE_DEPENDENT",
        "flags": [{
            "source_id": value, "consumers": sorted(set(consumers)),
            "namespace": "TEMP_FLAG" if 0 < int(value, 0) <= 0x1F
                         else "PERSISTENT_FLAG",
            "mapping_policy": "IDENTITY_REQUIRED"
            if 0 < int(value, 0) <= 0x1F else "NON_IDENTITY_REQUIRED",
        }
                  for value, consumers in sorted(flag_consumers.items())],
        "vars": [{
            "source_id": value, "consumers": sorted(set(consumers)),
            "namespace": "PERSISTENT_VAR",
            "mapping_policy": "NON_IDENTITY_REQUIRED",
        }
                 for value, consumers in sorted(var_consumers.items())],
        "source_writes_materialized": False,
        "temp_flag_0001_abi": temp_flag_0001_abi,
    }
    blaine_completion_binding = _build_blaine_project_completion_binding(
        stage60_rom, flag_consumers,
    )
    # Keep this in the plan so the materializer can replace only the unique
    # Cinnabar projection consumer.  Full-CFG uses of source 0x04B6 retain
    # their independently allocated namespace.
    explicit_project_state_bindings = {
        "flags": [{
            "source_id": blaine_completion_binding["source_flag"],
            "target_id": blaine_completion_binding["target_project_flag"],
            "physical_map": blaine_completion_binding["physical_map"],
            "binding": blaine_completion_binding["binding"],
        }],
        "vars": [],
    }
    assertions = {
        "canonical_253_exact": len(rows) == 253,
        "source_nonempty_95_exact": len(source_rows) == 95,
        "source_table_entries_184_exact": table_entry_count == 184,
        "source_root_fields_346_exact": root_fields == 346,
        "source_unique_roots_139_exact": len(unique_roots) == 139,
        "source_tag_counts_exact": tag_counts == Counter({1: 40, 2: 29, 3: 70, 4: 23, 5: 22}),
        "classification_A21_B12_C8_D54_exact": category_counts == expected_counts,
        "topology_41_exact": actual_topology == TOPOLOGY_MAPS,
        "target_nonempty_tables_exact": target_pairs == expected_target,
        "target_tables_do_not_overlap_projection": not any(
            row["physical_map"] in {_physical_label(pair) for pair in PROJECTABLE_MAPS}
            for row in target_nonempty
        ),
        "all_A_B_extractable": len(projectable) == 33
            and all(row["status"] == "EXTRACTABLE" for row in projectable),
        "seafoam_layout_clones_563_to_565_exact": (
            layout_extension["status"] == "READY"
            and layout_extension["existing_count"] == 563
            and layout_extension["expanded_count"] == 565
            and [row["new_layout_id"] for row in layout_extension["clones"]]
                == [564, 565]
            and [row["source_layout_id"] for row in layout_extension["clones"]]
                == [0x116, 0x117]
        ),
        "all_C_fail_closed": len(story_blocked) == 8
            and all(row["status"] == "BLOCKED_STORY_BINDING_REQUIRED"
                    for row in story_blocked),
        "projection_IR_only_topology": set(projection_opcode_set) <= {"0xA2", "0xA7"},
        "source_full_roots_never_imported": all(
            not row["source_full_roots_imported"] for row in projections
        ),
        "source_condition_tables_never_imported": all(
            not row["source_conditional_tables_imported"] for row in projections
        ),
        "league_entry_consumers_5_exact": (
            len(league_entry_geometry) == 5
            and {row["physical_map"] for row in league_entry_geometry}
                == {"097/075", "097/076", "097/077", "097/078", "097/079"}
            and all(row["status"] == "EXPLICIT_PROJECT_ADAPTER_REQUIRED"
                    and not row["automatic_projection"]
                    for row in league_entry_geometry)
        ),
        "league_explicit_adapter_contract_ready": (
            league_adapter_contract["status"] == "READY"
            and all(league_adapter_contract["assertions"].values())
        ),
        "vermilion_transition_adapter_contract_ready": (
            vermilion_transition_adapter_contract["status"] == "READY"
            and all(
                vermilion_transition_adapter_contract["assertions"].values()
            )
        ),
        "temp_flag_0001_identity_exact": temp_flag_0001_abi[
            "producer_consumer_identity_exact"
        ],
        "blaine_project_completion_binding_ready": (
            blaine_completion_binding["status"] == "READY"
            and all(blaine_completion_binding["assertions"].values())
        ),
    }
    ready = all(assertions.values())
    report = {
        "schema_version": SCHEMA_VERSION, "task": TASK,
        "status": "READY" if ready else "BLOCKED",
        "input": {
            "clean_size": len(clean_rom), "clean_sha256": _sha(clean_rom),
            "stage60_size": len(stage60_rom), "stage60_sha256": _sha(stage60_rom),
            "canonical_map_count": len(rows),
            "canonical_identity_sha256": _sha(_stable([{
                key: value for key, value in row.items() if key != "canonical_path"
            } for row in rows])),
        },
        "policy": {
            "source_story_import": "FORBIDDEN",
            "projection_source_roots": "DIRECT_TOPOLOGY_ONLY",
            "source_condition_tables": "EXCLUDED",
            "source_writes": "ANALYSIS_ONLY_SUPPRESSED",
            "materialized_opcodes": [_hex(value, 2)
                                     for value in sorted(MATERIALIZED_OPCODE_ALLOWLIST)],
            "explicit_adapter_opcodes": [
                _hex(value, 2)
                for value in sorted(
                    MATERIALIZED_EXPLICIT_ADAPTER_OPCODE_ALLOWLIST
                )
            ],
            "explicit_adapters": {
                "098/040_tag_3": (
                    "PINNED_PROJECT_OWNED_VOLATILE_STATE_PRODUCER"
                ),
            },
            "forbidden_families": {
                key: [_hex(value, 2) for value in sorted(values)]
                for key, values in FORBIDDEN_FAMILIES.items()
            },
        },
        "summary": {
            "classification_counts": dict(sorted(category_counts.items())),
            "source_table_entry_count": table_entry_count,
            "source_root_field_count": root_fields,
            "source_unique_root_count": len(unique_roots),
            "source_tag_counts": {str(key): value for key, value in sorted(tag_counts.items())},
            "topology_map_count": len(actual_topology),
            "extractable_map_count": sum(row["status"] == "EXTRACTABLE" for row in projections),
            "story_blocked_map_count": len(story_blocked),
            "target_nonempty_table_count": len(target_nonempty),
        },
        "classification": classification_rows,
        "projections": projections,
        "league_entry_geometry": league_entry_geometry,
        "league_explicit_adapter_contract": league_adapter_contract,
        "vermilion_transition_adapter_contract": (
            vermilion_transition_adapter_contract
        ),
        "layout_extension": layout_extension,
        "state_requirements": state_requirements,
        "explicit_project_state_bindings": explicit_project_state_bindings,
        "blaine_project_completion_binding": blaine_completion_binding,
        "target_nonempty_tables": target_nonempty,
        "assertions": assertions,
    }
    report["plan_sha256"] = _sha(_stable(report))
    if require_ready and not ready:
        failed = [key for key, value in assertions.items() if not value]
        _fail(f"projection plan is not READY: {failed}")
    return report


def build_projection_plan_from_paths(
    root: Path,
    *,
    clean_path: Path | None = None,
    stage60_path: Path | None = None,
    canonical_dir: Path | None = None,
    map_groups_path: Path | None = None,
    require_ready: bool = True,
) -> dict[str, Any]:
    clean = clean_path or root / DEFAULT_CLEAN_PATH
    stage60 = stage60_path or root / DEFAULT_STAGE60_PATH
    canonical = canonical_dir or root / DEFAULT_CANONICAL_DIR
    groups = map_groups_path or root / DEFAULT_MAP_GROUPS_PATH
    try:
        clean_rom, stage60_rom = clean.read_bytes(), stage60.read_bytes()
    except OSError as exc:
        _fail(f"cannot read projection ROM input: {exc}")
    rows = load_canonical_maps(canonical, groups)
    return build_projection_plan(
        clean_rom, stage60_rom, rows, require_ready=require_ready,
    )


def _normalize_id_mapping(mapping: Mapping[Any, Any], label: str) -> dict[int, int]:
    result: dict[int, int] = {}
    for raw_key, raw_value in mapping.items():
        try:
            key = int(raw_key, 0) if isinstance(raw_key, str) else int(raw_key)
            value = int(raw_value, 0) if isinstance(raw_value, str) else int(raw_value)
        except (TypeError, ValueError) as exc:
            _fail(f"{label} mapping is not numeric: {raw_key!r}->{raw_value!r}")
        if isinstance(raw_key, bool) or isinstance(raw_value, bool) \
                or not 0 <= key <= 0xFFFF or not 0 <= value <= 0xFFFF:
            _fail(f"{label} mapping outside u16: {raw_key!r}->{raw_value!r}")
        if key in result and result[key] != value:
            _fail(f"{label} mapping duplicate source ID: {key:#x}")
        result[key] = value
    return result


def _mapped(mapping: Mapping[int, int], source_hex: str, label: str) -> int:
    source = int(source_hex, 0)
    if source not in mapping:
        _fail(f"materialization is missing {label} mapping for {source_hex}")
    return mapping[source]


def _emit_guard_predicate(
    output: bytearray,
    predicate: Mapping[str, Any],
    failure_label: str,
    fixups: list[tuple[int, str]],
    flag_mapping: Mapping[int, int],
    var_mapping: Mapping[int, int],
) -> None:
    kind = predicate["kind"]
    if kind in {"FLAG_SET", "FLAG_CLEAR"}:
        flag = _mapped(flag_mapping, str(predicate["source_flag"]), "flag")
        output += struct.pack("<BH", 0x2B, flag)
        # checkflag TRUE is condition EQUAL(1), FALSE is condition LESS(0).
        failure_condition = 0 if kind == "FLAG_SET" else 1
    else:
        variable = _mapped(var_mapping, str(predicate["source_var"]), "var")
        output += struct.pack("<BHH", 0x21, variable, int(predicate["value"]))
        failure_condition = {"VAR_EQ": 5, "VAR_GE": 0, "VAR_LE": 2}.get(kind, -1)
        if failure_condition < 0:
            _fail(f"unsupported materialized predicate: {kind}")
    output += bytes((0x06, failure_condition))
    fixups.append((len(output), failure_label))
    output += b"\x00\x00\x00\x00"


def _compile_root_script(
    root_projection: Mapping[str, Any],
    script_base: int,
    flag_mapping: Mapping[int, int],
    var_mapping: Mapping[int, int],
    metatile_mapping: Mapping[int, int],
    layout_mapping: Mapping[int, int],
) -> bytes:
    output = bytearray()
    labels: dict[str, int] = {}
    fixups: list[tuple[int, str]] = []
    actions = root_projection.get("actions", [])
    for action_index, action in enumerate(actions):
        next_action = f"action_{action_index + 1}"
        alternatives = action.get("guard_alternatives", [])
        if not alternatives:
            _fail("projection action has no guard alternative")
        for alternative_index, guard in enumerate(alternatives):
            alternative_next = f"action_{action_index}_alt_{alternative_index + 1}"
            failure = alternative_next if alternative_index + 1 < len(alternatives) else next_action
            for predicate in guard:
                _emit_guard_predicate(
                    output, predicate, failure, fixups, flag_mapping, var_mapping,
                )
            opcode = int(action["opcode"], 0)
            if opcode == 0xA2:
                source = int(action["source_metatile"])
                if source not in metatile_mapping:
                    _fail(f"materialization is missing metatile mapping for {source:#x}")
                output += struct.pack(
                    "<BHHHH", 0xA2, int(action["x"]), int(action["y"]),
                    metatile_mapping[source], int(action["collision"]),
                )
            elif opcode == 0xA7:
                source = int(action["source_layout"])
                if source not in layout_mapping:
                    _fail(f"materialization is missing layout mapping for {source:#x}")
                output += struct.pack("<BH", 0xA7, layout_mapping[source])
            else:
                _fail(f"non-topology action reached materializer: {opcode:#x}")
            if alternative_index + 1 < len(alternatives):
                output += b"\x05"
                fixups.append((len(output), next_action))
                output += b"\x00\x00\x00\x00"
            labels[alternative_next] = len(output)
        labels[next_action] = len(output)
    output += b"\x02"
    for offset, label in fixups:
        if label not in labels:
            _fail(f"internal materialization label is missing: {label}")
        pointer = script_base + labels[label]
        if not ROM_BASE <= pointer < 0x0A000000:
            _fail(f"materialized branch pointer outside 32MiB ROM: {_hex(pointer)}")
        struct.pack_into("<I", output, offset, pointer)
    return bytes(output)


def _compile_vermilion_transition_adapter(
    contract: Mapping[str, Any],
    script_base: int,
    flag_mapping: Mapping[int, int],
) -> bytes:
    """Emit the bounded tag-3 producer authorized by the pinned contract."""

    unsigned = dict(contract)
    claimed_hash = unsigned.pop("contract_sha256", None)
    if claimed_hash != _sha(_stable(unsigned)):
        _fail("Vermilion transition adapter contract hash mismatch")
    if contract.get("status") != "READY" \
            or not all(contract.get("assertions", {}).values()):
        _fail("Vermilion transition adapter contract is not READY")
    expected = {
        "physical_map": "098/040",
        "source_table_index": 1,
        "script_type": 3,
        "source_wrapper_root": _hex(VERMILION_TRANSITION_SOURCE_ROOT),
        "source_init_root": _hex(VERMILION_TRANSITION_INIT_ROOT),
        "completion_source_flag": "0x0264",
        "special_output_vars": ["0x8004", "0x8005"],
        "volatile_target_vars": ["0x4000", "0x4001"],
        "source_wrapper_materialized_verbatim": False,
        "source_init_root_materialized_verbatim": False,
        "source_pointer_literals_permitted": False,
    }
    if any(contract.get(key) != value for key, value in expected.items()):
        _fail("Vermilion transition adapter semantic contract drift")
    special = contract.get("selection_special")
    if not isinstance(special, Mapping) or (
        special.get("id"), special.get("target_pointer"),
        special.get("span_size"), special.get("span_sha256"),
    ) != (
        _hex(VERMILION_TRASH_CAN_SPECIAL_ID, 4),
        _hex(VERMILION_TRASH_CAN_SPECIAL_POINTER),
        VERMILION_TRASH_CAN_SPECIAL_SPAN_SIZE,
        VERMILION_TRASH_CAN_SPECIAL_SPAN_SHA256,
    ):
        _fail("Vermilion transition special identity drift")
    allowed_pairs = contract.get("allowed_directed_switch_pairs")
    if allowed_pairs != _vermilion_adjacent_switch_pairs():
        _fail("Vermilion transition switch-pair domain drift")

    source_flag = int(str(contract["completion_source_flag"]), 0)
    target_flag = flag_mapping.get(source_flag)
    if target_flag is None or not 0 <= target_flag <= 0xFFFF:
        _fail("Vermilion transition completion flag mapping is missing")
    if not ROM_BASE <= script_base < 0x0A000000:
        _fail("Vermilion transition adapter base is outside 32MiB ROM")

    output = bytearray(struct.pack("<BH", 0x2B, target_flag))
    output += bytes((0x06, 0x01)) + b"\x00\x00\x00\x00"
    output += struct.pack("<BH", 0x25, VERMILION_TRASH_CAN_SPECIAL_ID)
    output += struct.pack("<BHH", 0x19, 0x4000, 0x8004)
    output += struct.pack("<BHH", 0x19, 0x4001, 0x8005)
    end_offset = len(output)
    output += b"\x02"
    struct.pack_into("<I", output, 5, script_base + end_offset)
    if len(output) != 23 or end_offset != 22:
        _fail("Vermilion transition adapter byte geometry drift")
    return bytes(output)


def materialize_projection(
    plan: Mapping[str, Any],
    *,
    payload_base: int,
    flag_mapping: Mapping[Any, Any],
    var_mapping: Mapping[Any, Any],
    delegated_maps: Iterable[tuple[int, int]] = (),
) -> dict[str, Any]:
    """Materialize A/B IR into standalone tables/scripts using explicit state bindings."""

    if plan.get("status") != "READY" or not all(plan.get("assertions", {}).values()):
        _fail("only a complete READY projection plan can be materialized")
    if not ROM_BASE <= payload_base < 0x0A000000 or payload_base & 3:
        _fail("payload_base must be 4-byte aligned inside the 32MiB ROM address space")
    flags = _normalize_id_mapping(flag_mapping, "flag")
    variables = _normalize_id_mapping(var_mapping, "var")
    explicit_flag_bindings: dict[int, int] = {}
    for row in plan.get("explicit_project_state_bindings", {}).get("flags", []):
        source = int(str(row["source_id"]), 0)
        target = int(str(row["target_id"]), 0)
        prior = explicit_flag_bindings.setdefault(source, target)
        if prior != target:
            _fail(f"explicit project flag binding collision: {source:#06x}")
    missing_explicit_sources = set(explicit_flag_bindings) - set(flags)
    if missing_explicit_sources:
        _fail(
            "state mapping incomplete: explicit project flag binding source missing: "
            f"{sorted(missing_explicit_sources)}"
        )
    flags.update(explicit_flag_bindings)
    all_maps = [row for row in plan["projections"] if row["status"] == "EXTRACTABLE"]
    if len(all_maps) != int(plan["summary"]["extractable_map_count"]):
        _fail("materializer input does not match the plan's extractable map count")
    delegated = set(delegated_maps)
    available = {(int(row["group"]), int(row["map"])) for row in all_maps}
    unknown_delegated = delegated - available
    if unknown_delegated:
        _fail(
            "delegated map is not an extractable projection: "
            f"{sorted(unknown_delegated)}"
        )
    vermilion_contract = plan.get("vermilion_transition_adapter_contract")
    if not isinstance(vermilion_contract, Mapping):
        _fail("Vermilion transition adapter contract is missing")
    vermilion_pair = VERMILION_TRANSITION_PHYSICAL
    if vermilion_pair not in available:
        _fail("Vermilion transition adapter target is not extractable")
    if vermilion_pair in delegated:
        _fail("required Vermilion transition adapter may not be delegated")
    maps = [
        row for row in all_maps
        if (int(row["group"]), int(row["map"])) not in delegated
    ]
    required_flags = {
        int(row["source_id"], 0) for row in plan["state_requirements"]["flags"]
    }
    required_vars = {
        int(row["source_id"], 0) for row in plan["state_requirements"]["vars"]
    }
    missing_flags, missing_vars = required_flags - set(flags), required_vars - set(variables)
    if missing_flags or missing_vars:
        _fail(
            "materialization state mapping incomplete: "
            f"flags={[hex(value) for value in sorted(missing_flags)]} "
            f"vars={[hex(value) for value in sorted(missing_vars)]}"
        )
    temp_flags = {value for value in required_flags if 0 < value <= 0x1F}
    persistent_flags = required_flags - temp_flags
    nonidentity_temp_flags = {value for value in temp_flags if flags[value] != value}
    identity_flags = {value for value in persistent_flags if flags[value] == value}
    identity_vars = {value for value in required_vars if variables[value] == value}
    if nonidentity_temp_flags:
        _fail(
            "temporary flag ABI requires identity mapping: "
            f"flags={[hex(value) for value in sorted(nonidentity_temp_flags)]}"
        )
    if identity_flags or identity_vars:
        _fail(
            "persistent source state IDs require non-identity mapping: "
            f"flags={[hex(value) for value in sorted(identity_flags)]} "
            f"vars={[hex(value) for value in sorted(identity_vars)]}"
        )
    if len({flags[value] for value in required_flags}) != len(required_flags) \
            or len({variables[value] for value in required_vars}) != len(required_vars):
        _fail("projection state mapping must be injective within each namespace")

    extension = plan.get("layout_extension")
    if not isinstance(extension, Mapping) or extension.get("status") != "READY":
        _fail("READY layout extension contract is required")
    existing_count = int(extension["existing_count"])
    expanded_count = int(extension["expanded_count"])
    existing_table = bytes.fromhex(str(extension["existing_table_raw_hex"]))
    clones = list(extension.get("clones", []))
    if len(existing_table) != existing_count * 4 \
            or _sha(existing_table) != extension["existing_table_sha256"] \
            or expanded_count != existing_count + len(clones):
        _fail("layout extension table geometry/hash mismatch")

    # First allocate the expanded global layout table, cloned assets, then map tables/scripts.
    layout_table_offset = 0
    cursor = expanded_count * 4
    cursor = (cursor + 3) & ~3
    clone_allocations: list[dict[str, Any]] = []
    for clone_index, clone in enumerate(sorted(clones, key=lambda row: row["new_layout_id"])):
        expected_id = existing_count + clone_index + 1
        if int(clone["new_layout_id"]) != expected_id or not clone.get("exact"):
            _fail("layout clone IDs must be contiguous exact additions")
        border = bytes.fromhex(str(clone["border_raw_hex"]))
        block = bytes.fromhex(str(clone["blockdata_raw_hex"]))
        tail = bytes.fromhex(str(clone["layout_tail_raw_hex"]))
        if _sha(border) != clone["border_sha256"] \
                or _sha(block) != clone["blockdata_sha256"] or len(tail) != 4:
            _fail(f"layout clone raw/hash mismatch: {expected_id}")
        border_offset = cursor
        cursor += len(border)
        cursor = (cursor + 3) & ~3
        block_offset = cursor
        cursor += len(block)
        cursor = (cursor + 3) & ~3
        layout_offset = cursor
        cursor += 0x1C
        cursor = (cursor + 3) & ~3
        clone_allocations.append({
            "clone": clone, "border": border, "block": block, "tail": tail,
            "border_offset": border_offset, "block_offset": block_offset,
            "layout_offset": layout_offset,
        })

    allocations: list[dict[str, Any]] = []
    for row in maps:
        roots = sorted(row["root_projections"], key=lambda item: item["source_table_index"])
        pair = (int(row["group"]), int(row["map"]))
        adapter_contracts = (
            [vermilion_contract] if pair == vermilion_pair else []
        )
        table_order = [
            (int(root["source_table_index"]), "TOPOLOGY_IR")
            for root in roots
        ] + [
            (int(adapter["source_table_index"]), "VERMILION_TRANSITION_ADAPTER")
            for adapter in adapter_contracts
        ]
        if table_order != sorted(table_order) \
                or len({index for index, _role in table_order}) != len(table_order):
            _fail(f"materialized map-script table order collision: {row['physical_map']}")
        table_offset = cursor
        cursor += len(table_order) * 5 + 1
        cursor = (cursor + 3) & ~3
        root_allocations = []
        meta = {
            int(item["source_metatile"]): int(item["resolved_target_metatile"])
            for item in row["asset_bindings"]["metatile_mappings"]
        }
        layouts = {
            int(item["source_layout_id"]): int(item["resolved_target_layout_id"])
            for item in row["asset_bindings"]["layout_mappings"]
        }
        for root in roots:
            trial = _compile_root_script(root, payload_base, flags, variables, meta, layouts)
            root_allocations.append({"root": root, "offset": cursor, "size": len(trial)})
            cursor += len(trial)
            cursor = (cursor + 3) & ~3
        adapter_allocations = []
        for adapter in adapter_contracts:
            trial = _compile_vermilion_transition_adapter(
                adapter, payload_base + cursor, flags,
            )
            adapter_allocations.append({
                "contract": adapter, "offset": cursor, "size": len(trial),
            })
            cursor += len(trial)
            cursor = (cursor + 3) & ~3
        allocations.append({
            "row": row, "table_offset": table_offset, "roots": root_allocations,
            "adapters": adapter_allocations,
            "metatile_mapping": meta, "layout_mapping": layouts,
        })
    if payload_base + cursor > 0x0A000000:
        _fail("materialized projection payload exceeds the 32MiB ROM")
    blob = bytearray(cursor)
    blob[layout_table_offset:layout_table_offset + len(existing_table)] = existing_table
    clone_reports: list[dict[str, Any]] = []
    for allocation in clone_allocations:
        clone = allocation["clone"]
        border_pointer = payload_base + allocation["border_offset"]
        block_pointer = payload_base + allocation["block_offset"]
        layout_pointer = payload_base + allocation["layout_offset"]
        primary = int(str(clone["target_primary_tileset_pointer"]), 0)
        secondary = int(str(clone["target_secondary_tileset_pointer"]), 0)
        layout_raw = (
            struct.pack("<IIIIII", int(clone["width"]), int(clone["height"]),
                        border_pointer, block_pointer, primary, secondary)
            + allocation["tail"]
        )
        if len(layout_raw) != 0x1C:
            _fail("cloned layout struct size mismatch")
        blob[allocation["border_offset"]:allocation["border_offset"]
             + len(allocation["border"])] = allocation["border"]
        blob[allocation["block_offset"]:allocation["block_offset"]
             + len(allocation["block"])] = allocation["block"]
        blob[allocation["layout_offset"]:allocation["layout_offset"] + 0x1C] = layout_raw
        table_entry_offset = (int(clone["new_layout_id"]) - 1) * 4
        struct.pack_into("<I", blob, layout_table_offset + table_entry_offset, layout_pointer)
        clone_reports.append({
            "source_layout_id": int(clone["source_layout_id"]),
            "new_layout_id": int(clone["new_layout_id"]),
            "physical_map": clone["physical_map"],
            "border_pointer": _hex(border_pointer),
            "blockdata_pointer": _hex(block_pointer),
            "layout_pointer": _hex(layout_pointer),
            "layout_raw_hex": layout_raw.hex(), "layout_sha256": _sha(layout_raw),
            "target_primary_tileset_pointer": _hex(primary),
            "target_secondary_tileset_pointer": _hex(secondary),
            "all_used_metatiles_target_exact": clone["all_used_metatiles_target_exact"],
        })
    records: list[dict[str, Any]] = []
    all_script_bytes: list[tuple[bytes, str]] = []
    for allocation in allocations:
        row = allocation["row"]
        table_pointer = payload_base + allocation["table_offset"]
        table = bytearray()
        script_reports = []
        for root_allocation in allocation["roots"]:
            root = root_allocation["root"]
            script_pointer = payload_base + root_allocation["offset"]
            raw = _compile_root_script(
                root, script_pointer, flags, variables,
                allocation["metatile_mapping"], allocation["layout_mapping"],
            )
            if len(raw) != root_allocation["size"]:
                _fail("materialized script size changed between allocation passes")
            blob[root_allocation["offset"]:root_allocation["offset"] + len(raw)] = raw
            all_script_bytes.append((raw, "TOPOLOGY_IR"))
            table += struct.pack("<BI", int(root["script_type"]), script_pointer)
            script_reports.append({
                "source_root": root["root"], "script_type": int(root["script_type"]),
                "pointer": _hex(script_pointer), "size": len(raw),
                "raw_hex": raw.hex(), "sha256": _sha(raw),
                "materialization_role": "TOPOLOGY_IR",
                "source_root_materialized_verbatim": False,
            })
        for adapter_allocation in allocation["adapters"]:
            adapter = adapter_allocation["contract"]
            script_pointer = payload_base + adapter_allocation["offset"]
            raw = _compile_vermilion_transition_adapter(
                adapter, script_pointer, flags,
            )
            if len(raw) != adapter_allocation["size"]:
                _fail("Vermilion adapter size changed between allocation passes")
            blob[adapter_allocation["offset"]:adapter_allocation["offset"]
                 + len(raw)] = raw
            all_script_bytes.append((raw, "VERMILION_TRANSITION_ADAPTER"))
            table += struct.pack("<BI", int(adapter["script_type"]), script_pointer)
            script_reports.append({
                "source_root": adapter["source_wrapper_root"],
                "source_init_root": adapter["source_init_root"],
                "script_type": int(adapter["script_type"]),
                "pointer": _hex(script_pointer), "size": len(raw),
                "raw_hex": raw.hex(), "sha256": _sha(raw),
                "materialization_role": "VERMILION_TRANSITION_ADAPTER",
                "contract_sha256": adapter["contract_sha256"],
                "completion_source_flag": adapter["completion_source_flag"],
                "completion_target_flag": _hex(
                    flags[int(str(adapter["completion_source_flag"]), 0)], 4,
                ),
                "selection_special_id": adapter["selection_special"]["id"],
                "allowed_directed_switch_pair_count": len(
                    adapter["allowed_directed_switch_pairs"]
                ),
                "source_root_materialized_verbatim": False,
                "source_pointer_literals_permitted": False,
            })
        table += b"\x00"
        blob[allocation["table_offset"]:allocation["table_offset"] + len(table)] = table
        records.append({
            "physical_map": row["physical_map"], "group": int(row["group"]),
            "map": int(row["map"]), "map_key": row["map_key"],
            "table_pointer": _hex(table_pointer), "table_size": len(table),
            "table_raw_hex": table.hex(), "scripts": script_reports,
            "condition_tables": [],
            "source_full_roots_imported": False,
            "source_condition_tables_imported": False,
            "map_script_pointer_patch": {
                "address": row["target_map_script_field_address"],
                "expected_pointer": row["target_map_script_expected_pointer"],
                "replacement_pointer": _hex(table_pointer),
                "expected_table_structure_empty": row[
                    "target_map_script_structure_empty"
                ],
            },
        })
    # Decode every emitted instruction boundary and reject any unexpected opcode. Branch pointers
    # are project-owned payload addresses by construction; source pointers are never copied.
    emitted_opcodes: Counter[int] = Counter()
    emitted_opcode_roles: dict[str, Counter[int]] = defaultdict(Counter)
    for raw, role in all_script_bytes:
        allowlist = (
            MATERIALIZED_OPCODE_ALLOWLIST
            if role == "TOPOLOGY_IR"
            else MATERIALIZED_EXPLICIT_ADAPTER_OPCODE_ALLOWLIST
            if role == "VERMILION_TRANSITION_ADAPTER"
            else frozenset()
        )
        pc = 0
        while pc < len(raw):
            opcode = raw[pc]
            if opcode not in allowlist:
                _fail(
                    f"materializer emitted forbidden opcode for {role}: {opcode:#x}"
                )
            emitted_opcodes[opcode] += 1
            emitted_opcode_roles[role][opcode] += 1
            size = int(COMMAND_LENGTHS[opcode])
            pc += size
            if opcode == 0x02:
                if pc != len(raw):
                    _fail("materialized script contains bytes after end")
                break
        if pc != len(raw):
            _fail("materialized script boundary mismatch")
    source_roots = {
        int(root["root"], 0)
        for row in maps for root in row["root_projections"]
    }
    source_roots.update({
        VERMILION_TRANSITION_SOURCE_ROOT,
        VERMILION_TRANSITION_INIT_ROOT,
        VERMILION_TRANSITION_RETURN_ROOT,
    })
    joined_script_bytes = b"".join(raw for raw, _role in all_script_bytes)
    source_pointer_literals = [
        _hex(pointer) for pointer in sorted(source_roots)
        if struct.pack("<I", pointer) in joined_script_bytes
    ]
    if source_pointer_literals:
        _fail(f"source root pointer leaked into materialized payload: {source_pointer_literals}")
    result = {
        "schema_version": 1, "status": "READY",
        "plan_sha256": plan["plan_sha256"], "payload_base": _hex(payload_base),
        "payload_size": len(blob), "payload_raw_hex": bytes(blob).hex(),
        "payload_sha256": _sha(bytes(blob)), "maps": records,
        "delegated_maps": [
            _physical_label(pair) for pair in sorted(delegated)
        ],
        "state_bindings": {
            "flags": [{
                "source_id": _hex(source, 4), "target_id": _hex(flags[source], 4),
                "namespace": "TEMP_FLAG" if source in temp_flags else "PERSISTENT_FLAG",
                "mapping": (
                    "EXPLICIT_PROJECT_STATE_BINDING"
                    if source in explicit_flag_bindings
                    else "IDENTITY" if source == flags[source] else "NON_IDENTITY"
                ),
            } for source in sorted(required_flags)],
            "vars": [{
                "source_id": _hex(source, 4), "target_id": _hex(variables[source], 4),
                "namespace": "PERSISTENT_VAR", "mapping": "NON_IDENTITY",
            } for source in sorted(required_vars)],
        },
        "layout_installation": {
            "pointer_patch": {
                "address": extension["pointer_site"],
                "expected_pointer": extension["expected_root_pointer"],
                "replacement_pointer": _hex(payload_base + layout_table_offset),
            },
            "table_pointer": _hex(payload_base + layout_table_offset),
            "existing_count": existing_count, "expanded_count": expanded_count,
            "table_size": expanded_count * 4,
            "table_raw_hex": bytes(blob[:expanded_count * 4]).hex(),
            "table_sha256": _sha(bytes(blob[:expanded_count * 4])),
            "clones": clone_reports,
        },
        "condition_table_count": 0,
        "emitted_opcode_counts": {
            _hex(opcode, 2): count for opcode, count in sorted(emitted_opcodes.items())
        },
        "emitted_opcode_counts_by_role": {
            role: {
                _hex(opcode, 2): count
                for opcode, count in sorted(counts.items())
            }
            for role, counts in sorted(emitted_opcode_roles.items())
        },
        "explicit_adapters": [
            {
                "physical_map": row["physical_map"],
                **{
                    key: value for key, value in script.items()
                    if key not in {"raw_hex"}
                },
            }
            for row in records for script in row["scripts"]
            if script["materialization_role"]
                == "VERMILION_TRANSITION_ADAPTER"
        ],
        "source_pointer_literals": source_pointer_literals,
        "assertions": {
            "all_nondelegated_extractable_maps_materialized": (
                len(records) + len(delegated)
                == int(plan["summary"]["extractable_map_count"])
                and {row["physical_map"] for row in records}.isdisjoint(
                    {_physical_label(pair) for pair in delegated}
                )
            ),
            "condition_tables_empty": all(not row["condition_tables"] for row in records),
            "only_role_scoped_safe_opcodes_emitted": (
                set(emitted_opcode_roles.get("TOPOLOGY_IR", {}))
                    <= MATERIALIZED_OPCODE_ALLOWLIST
                and set(emitted_opcode_roles.get(
                    "VERMILION_TRANSITION_ADAPTER", {}
                )) <= MATERIALIZED_EXPLICIT_ADAPTER_OPCODE_ALLOWLIST
                and set(emitted_opcodes) <= MATERIALIZED_ALL_OPCODE_ALLOWLIST
            ),
            "vermilion_transition_adapter_materialized_once": (
                sum(
                    script["materialization_role"]
                        == "VERMILION_TRANSITION_ADAPTER"
                    for row in records for script in row["scripts"]
                ) == 1
                and any(
                    row["physical_map"] == "098/040"
                    and [script["script_type"] for script in row["scripts"]]
                        == [1, 3]
                    for row in records
                )
            ),
            "no_source_root_pointer_literal": not source_pointer_literals,
            "layout_table_563_to_565_materialized": existing_count == 563
                and expanded_count == 565 and len(clone_reports) == 2,
            "layout_clones_use_target_tilesets": all(
                row["all_used_metatiles_target_exact"] for row in clone_reports
            ),
            "all_map_script_patches_replace_structurally_empty_tables": all(
                row["map_script_pointer_patch"]["expected_table_structure_empty"]
                and row["map_script_pointer_patch"]["expected_pointer"]
                    != row["map_script_pointer_patch"]["replacement_pointer"]
                for row in records
            ),
            "temp_flags_identity_persistent_state_nonidentity": (
                all(flags[value] == value for value in temp_flags)
                and all(flags[value] != value for value in persistent_flags)
                and all(variables[value] != value for value in required_vars)
            ),
        },
    }
    if not all(result["assertions"].values()):
        _fail("materialized projection assertion failed: " + ",".join(
            key for key, value in result["assertions"].items() if not value
        ))
    result["materialization_sha256"] = _sha(_stable(result))
    return result


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--clean", type=Path)
    parser.add_argument("--stage60", type=Path)
    parser.add_argument("--canonical-dir", type=Path)
    parser.add_argument("--map-groups", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--require-ready", action="store_true")
    args = parser.parse_args(argv)
    try:
        report = build_projection_plan_from_paths(
            args.root,
            clean_path=args.clean,
            stage60_path=args.stage60,
            canonical_dir=args.canonical_dir,
            map_groups_path=args.map_groups,
            require_ready=args.require_ready,
        )
        if args.output:
            _write_json(args.output, report)
        print(json.dumps({
            "status": report["status"], "plan_sha256": report["plan_sha256"],
            **report["summary"],
        }, ensure_ascii=False, sort_keys=True))
        return 0 if report["status"] == "READY" else 1
    except Stage61MapScriptProjectionError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
