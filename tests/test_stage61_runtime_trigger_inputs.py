from __future__ import annotations

import hashlib
import json
import struct
import unittest
from copy import deepcopy
from pathlib import Path

from tools.stage61_interaction_oracle import (
    _map_condition_precedence_guards_from_rom,
    _validated_runtime_trigger_path,
)
from tools.stage61_runtime_trigger_inputs import (
    EXPECTED_MAP_SEED_KIND_COUNTS,
    Stage61RuntimeTriggerInputsError,
    _map_condition_precedence_guards,
    build_stage61_runtime_trigger_inputs,
    validate_stage61_runtime_trigger_inputs_map_seed_contract,
)


BASE = 0x08000000
ROOT = Path(__file__).resolve().parents[1]


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _stable(value) -> bytes:
    return (
        json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        ) + "\n"
    ).encode("utf-8")


class _Fixture:
    SOURCE_HEADER = 0x08056200
    TARGET_HEADER = 0x08056220
    SOURCE_LAYOUT = 0x08056300
    TARGET_LAYOUT = 0x08056320
    SOURCE_BLOCKS = 0x08056400
    TARGET_BLOCKS = 0x08056500
    PRIMARY_TILESET = 0x08056600
    SECONDARY_TILESET = 0x08056620
    PRIMARY_ATTRIBUTES = 0x08057000
    SECONDARY_ATTRIBUTES = 0x08057A00
    SOURCE_EVENTS = 0x08059000
    TARGET_EVENTS = 0x08059020
    SOURCE_WARPS = 0x08059100
    TARGET_OBJECTS = 0x08059200
    TARGET_WARPS = 0x08059220
    TARGET_COORDS = 0x08059240
    TARGET_BGS = 0x08059280
    TARGET_MAP_SCRIPTS = 0x08059300
    # Exact pinned gStdScripts table entry 7.
    COMMON_RECORD = 0x08163758 + 7 * 4
    OBJECT_ROOT = 0x08060000
    BG_ROOT = 0x08060010
    COORD_ROOT = 0x08060020
    MAP_ROOT = 0x08060030
    COMMON_ROOT = 0x08060040
    # Existing oracle deliberately pins the final JPN stock wrapper root.
    HIDDEN_ROOT = 0x0819410F
    CALLBACK = 0x08060080
    CALLBACK_INSTALL = 0x08060084
    CALLBACK_DISPATCH = 0x08060088

    def __init__(self) -> None:
        raw = bytearray(b"\xFF" * 0x1A0000)

        def at(address: int) -> int:
            return address - BASE

        def put(address: int, value: bytes) -> None:
            raw[at(address):at(address) + len(value)] = value

        # gMapGroups -> group 0 table -> two map headers.
        struct.pack_into("<I", raw, 0x54B0C, 0x08056000)
        struct.pack_into("<I", raw, at(0x08056000), 0x08056100)
        struct.pack_into(
            "<II", raw, at(0x08056100), self.SOURCE_HEADER,
            self.TARGET_HEADER,
        )
        # Both maps share tilesets but have independent final block arrays.
        for header, layout, events, scripts in (
            (self.SOURCE_HEADER, self.SOURCE_LAYOUT, self.SOURCE_EVENTS, 0),
            (
                self.TARGET_HEADER, self.TARGET_LAYOUT,
                self.TARGET_EVENTS, self.TARGET_MAP_SCRIPTS,
            ),
        ):
            struct.pack_into(
                "<III", raw, at(header), layout, events, scripts,
            )
        for layout, blocks in (
            (self.SOURCE_LAYOUT, self.SOURCE_BLOCKS),
            (self.TARGET_LAYOUT, self.TARGET_BLOCKS),
        ):
            struct.pack_into(
                "<IIIIII", raw, at(layout), 8, 8, 0, blocks,
                self.PRIMARY_TILESET, self.SECONDARY_TILESET,
            )
        source_blocks = [0] * 64
        source_blocks[2 + 2 * 8] = 1  # source WarpEventはbehavior 0x60。
        put(self.SOURCE_BLOCKS, struct.pack("<64H", *source_blocks))
        put(self.TARGET_BLOCKS, struct.pack("<64H", *([0] * 64)))
        struct.pack_into(
            "<I", raw, at(self.PRIMARY_TILESET) + 20,
            self.PRIMARY_ATTRIBUTES,
        )
        struct.pack_into(
            "<I", raw, at(self.SECONDARY_TILESET) + 20,
            self.SECONDARY_ATTRIBUTES,
        )
        put(self.PRIMARY_ATTRIBUTES, b"\0" * (640 * 4))
        put(self.SECONDARY_ATTRIBUTES, b"\0" * (640 * 4))
        struct.pack_into("<I", raw, at(self.PRIMARY_ATTRIBUTES) + 4, 0x60)

        # Source: one real WarpEvent at (2,2), walking UP from (2,3).
        put(
            self.SOURCE_EVENTS,
            bytes((0, 1, 0, 0))
            + struct.pack("<IIII", 0, self.SOURCE_WARPS, 0, 0),
        )
        put(
            self.SOURCE_WARPS,
            struct.pack("<hhBBBB", 2, 2, 0, 0, 1, 0),
        )

        # Target final objects/event arrays.
        put(
            self.TARGET_EVENTS,
            bytes((1, 1, 2, 2)) + struct.pack(
                "<IIII", self.TARGET_OBJECTS, self.TARGET_WARPS,
                self.TARGET_COORDS, self.TARGET_BGS,
            ),
        )
        object_raw = bytearray(0x18)
        object_raw[0] = 1
        struct.pack_into("<hh", object_raw, 4, 4, 4)
        object_raw[8] = 0
        struct.pack_into("<I", object_raw, 0x10, self.OBJECT_ROOT)
        put(self.TARGET_OBJECTS, object_raw)
        put(
            self.TARGET_WARPS,
            struct.pack("<hhBBBB", 1, 1, 0, 0, 0, 0),
        )
        coord = bytearray(0x10)
        struct.pack_into("<HH", coord, 0, 3, 3)
        coord[4] = 0
        struct.pack_into("<HH", coord, 6, 0x4001, 2)
        struct.pack_into("<I", coord, 12, self.COORD_ROOT)
        structural_coord = bytearray(0x10)
        struct.pack_into("<HH", structural_coord, 0, 1, 6)
        put(self.TARGET_COORDS, bytes(coord + structural_coord))
        bg = bytearray(0x0C)
        struct.pack_into("<HH", bg, 0, 6, 4)
        bg[4] = 0
        bg[5] = 0
        struct.pack_into("<I", bg, 8, self.BG_ROOT)
        hidden = bytearray(0x0C)
        struct.pack_into("<HH", hidden, 0, 2, 2)
        hidden[4] = 0
        hidden[5] = 7
        self.hidden_packed = 0x01020001
        struct.pack_into("<I", hidden, 8, self.hidden_packed)
        put(self.TARGET_BGS, bytes(bg + hidden))

        # Map transition root and bytecode roots.  OBJECT reaches callstd 7;
        # the COMMON owner must therefore use this actual caller PC.
        put(
            self.TARGET_MAP_SCRIPTS,
            bytes((3,)) + struct.pack("<I", self.MAP_ROOT) + b"\0",
        )
        put(self.OBJECT_ROOT, b"\x09\x07\x02")
        put(self.BG_ROOT, b"\x02")
        put(self.COORD_ROOT, b"\x02")
        put(self.MAP_ROOT, b"\x02")
        put(self.COMMON_ROOT, b"\x02")
        # special 150 SetHiddenItemFlag + special 350 CheckAddCoins.
        put(self.HIDDEN_ROOT, b"\x25\x96\x00\x25\x5E\x01\x02")
        put(self.CALLBACK, b"\x02\x02\x02\x02\x02\x02\x02\x02\x02")
        struct.pack_into("<I", raw, at(self.COMMON_RECORD), self.COMMON_ROOT)
        self.rom = bytes(raw)
        self._rebuild_documents()

    @staticmethod
    def _owner(
        owner_id: str, owner_kind: str, *, index, record: int,
        root_field: int, root: int | None, raw_root: int,
        **extra,
    ) -> dict:
        row = {
            "owner_id": owner_id, "owner_kind": owner_kind,
            "group": 0, "map": 1, "index": index,
            "record_address": record, "root_field_address": root_field,
            "physical_map_key": "TEST_TARGET",
            "physical_provenance": "VEGA_STOCK",
            "raw_root": raw_root, "root": root,
            "runtime_root": root is not None,
        }
        row.update(extra)
        return row

    def _rebuild_documents(self) -> None:
        sha = _sha(self.rom)
        owners = [
            self._owner(
                "OBJECT:000/001:000", "OBJECT", index=0,
                record=self.TARGET_OBJECTS,
                root_field=self.TARGET_OBJECTS + 0x10,
                root=self.OBJECT_ROOT, raw_root=self.OBJECT_ROOT,
            ),
            self._owner(
                "BG:000/001:000", "BG", index=0,
                record=self.TARGET_BGS, root_field=self.TARGET_BGS + 8,
                root=self.BG_ROOT, raw_root=self.BG_ROOT, bg_kind=0,
            ),
            self._owner(
                "BG:000/001:001", "BG", index=1,
                record=self.TARGET_BGS + 12,
                root_field=self.TARGET_BGS + 20,
                root=None, raw_root=self.hidden_packed, bg_kind=7,
                non_script_reason="HIDDEN_ITEM",
            ),
            self._owner(
                "COORD:000/001:000", "COORD", index=0,
                record=self.TARGET_COORDS,
                root_field=self.TARGET_COORDS + 12,
                root=self.COORD_ROOT, raw_root=self.COORD_ROOT,
            ),
            self._owner(
                "COORD:000/001:001", "COORD", index=1,
                record=self.TARGET_COORDS + 16,
                root_field=self.TARGET_COORDS + 28,
                root=None, raw_root=0,
                non_script_reason="NULL_SCRIPT_POINTER",
            ),
            self._owner(
                "MAP:000/001:000:DIRECT", "MAP", index=0,
                record=self.TARGET_MAP_SCRIPTS,
                root_field=self.TARGET_MAP_SCRIPTS + 1,
                root=self.MAP_ROOT, raw_root=self.MAP_ROOT,
                root_subkind="DIRECT",
            ),
            {
                "owner_id": "COMMON:STANDARD:007", "owner_kind": "COMMON",
                "root_subkind": "STANDARD_SCRIPT", "index": 7,
                "record_address": self.COMMON_RECORD,
                "root_field_address": self.COMMON_RECORD,
                "physical_map_key": None,
                "physical_provenance": "COMMON_ENGINE_TABLE",
                "raw_root": self.COMMON_ROOT, "root": self.COMMON_ROOT,
                "runtime_root": True,
            },
        ]
        target_ids = sorted(
            row["owner_id"] for row in owners if row["owner_kind"] != "COMMON"
        )
        self.inventory = {
            "schema_version": 1,
            "kind": "STAGE61_ALL_EVENT_OWNER_INVENTORY",
            "status": "PASS", "rom_sha256": sha,
            "owner_count": len(owners), "owners": owners,
            "surfaces": [
                {
                    "physical_map": "000/000",
                    "physical_map_key": "TEST_SOURCE",
                    "map_script_structure": [], "owner_ids": [],
                },
                {
                    "physical_map": "000/001",
                    "physical_map_key": "TEST_TARGET",
                    "map_script_structure": [{
                        "table_index": 0, "script_type": 3,
                        "root": self.MAP_ROOT, "conditions": [],
                    }],
                    "owner_ids": target_ids,
                },
            ],
            "findings": [],
        }
        self.inventory["inventory_sha256"] = _sha(_stable(self.inventory))
        execution = {
            "trigger": (
                "TELEPORT_TO_WALK_START_REAL_WALK_TO_STANCE_FACE_AND_A"
            ),
            "start": [4, 5], "walk_sequence": ["RIGHT", "LEFT"],
            "stance": [4, 5], "action": "UP", "interaction_distance": 1,
            "counter_tile": None, "actual_walk_required": True,
            "actual_walk_exception": None,
            "walk_path_basis": "FINAL_STANCE_CLOSED_ONE_TILE_CYCLE",
            "direct_script_call_forbidden": True,
        }
        self.npc_catalog = {
            "schema_version": 1, "status": "PASS", "script_object_count": 1,
            "npcs": [{
                "npc_id": "OBJECT:000/001:000", "group": 0, "map": 1,
                "object_index": 0, "local_id": 1,
                "script_pointer": self.OBJECT_ROOT,
                "interaction_execution": deepcopy(execution),
            }],
        }
        self.placement = {
            "schema_version": 2, "status": "PASS", "rom_sha256": sha,
            "objects": [{
                "npc_id": "OBJECT:000/001:000",
                "group": 0, "map": 1, "object_index": 0,
                "template_object": [4, 4], "object": [4, 4],
                "interaction_object_basis": "FINAL_OBJECT_TEMPLATE",
                "interaction_execution": deepcopy(execution),
            }],
        }
        self.hidden_consumers = {
            "schema_version": 1,
            "kind": "STAGE61_HIDDEN_ITEM_SCRIPT_CONSUMERS",
            "rom_sha256": sha,
            "by_entry": {
                "FACE_A": {
                    "consumer_script_root": self.HIDDEN_ROOT,
                    "symbol": "EventScript_HiddenItemScript",
                    "source_provenance": {
                        "kind": "FINAL_ROM_FIELD_ENGINE_SCRIPT_CONSUMER",
                        "rom_sha256": sha,
                        "symbol": "EventScript_HiddenItemScript",
                    },
                },
            },
        }
        self.callbacks = {
            "schema_version": 1,
            "kind": "STAGE61_MAP_FIELD_RETURN_CALLBACK_CONTRACTS",
            "rom_sha256": sha,
            "by_tag": {
                "5": {
                    "callback_address": self.CALLBACK,
                    "callback_install_instruction_pc": self.CALLBACK_INSTALL,
                    "callback_dispatch_instruction_pc": self.CALLBACK_DISPATCH,
                    "normal_trigger_tokens": ["START", "B"],
                    "source_provenance": {
                        "kind": "FINAL_ROM_NORMAL_FIELD_RETURN_CALLBACK",
                        "rom_sha256": sha, "tag": 5,
                    },
                },
            },
        }

    def rebuild_after_rom_change(self, raw: bytearray) -> None:
        self.rom = bytes(raw)
        self._rebuild_documents()

    def build(self, **kwargs):
        return build_stage61_runtime_trigger_inputs(
            self.rom, self.inventory, self.npc_catalog,
            placement_audit=self.placement,
            hidden_item_consumers=self.hidden_consumers,
            map_callback_contracts=self.callbacks,
            require_canonical_counts=False,
            **kwargs,
        )


class Stage61RuntimeTriggerInputsTests(unittest.TestCase):
    def test_map_condition_precedence_guards_are_rom_ordered_and_exact(self) -> None:
        raw = bytearray(b"\xFF" * 0x60000)
        records = []
        rows = [
            (0x4000, 0, 0x08000500),
            (0x4079, 0, 0x08000510),
            (0x4079, 2, 0x08000520),
            (0x400D, 16, 0x08000530),
            (0x400D, 17, 0x08000540),
        ]
        for index, (variable, value, root) in enumerate(rows):
            address = BASE + 0x400 + index * 8
            record = struct.pack("<HHI", variable, value, root)
            raw[address - BASE:address - BASE + 8] = record
            records.append({
                "condition_index": index,
                "variable": variable, "value": value, "root": root,
                "record_address": address,
                "root_field_address": address + 4,
            })
        owner = {
            "owner_id": "MAP:000/000:000:004", "owner_kind": "MAP",
            "root_subkind": "CONDITION", "group": 0, "map": 0,
            "index": [0, 4], "record_address": BASE + 0x420,
            "root": 0x08000540,
        }
        guards = _map_condition_precedence_guards(
            bytes(raw), owner, {"conditions": records},
        )
        self.assertEqual([
            (guard["variable"], guard["required_value"],
             guard["forbidden_values"])
            for guard in guards
        ], [
            (0x4000, 1, [0]),
            (0x4079, 1, [0, 2]),
        ])
        self.assertEqual([
            source["condition_index"] for source in guards[1][
                "source_conditions"
            ]
        ], [1, 2])
        duplicate = deepcopy(records)
        duplicate[3] = {**duplicate[3], "value": 17}
        raw[BASE + 0x418 - BASE:BASE + 0x420 - BASE] = struct.pack(
            "<HHI", 0x400D, 17, 0x08000530,
        )
        with self.assertRaisesRegex(
            Stage61RuntimeTriggerInputsError, "同一先行条件",
        ):
            _map_condition_precedence_guards(
                bytes(raw), owner, {"conditions": duplicate},
            )

    def test_oracle_independently_decodes_condition_table_chain(self) -> None:
        raw = bytearray(b"\xFF" * 0x60000)
        struct.pack_into("<I", raw, 0x54B0C, BASE + 0x100)
        struct.pack_into("<I", raw, 0x100, BASE + 0x110)
        struct.pack_into("<I", raw, 0x110, BASE + 0x200)
        struct.pack_into("<I", raw, 0x208, BASE + 0x300)
        raw[0x300] = 2
        struct.pack_into("<I", raw, 0x301, BASE + 0x400)
        raw[0x305] = 0
        condition_rows = [
            (0x4079, 0, 0x08000500),
            (0x4079, 2, 0x08000510),
            (0x406F, 8, 0x08000520),
        ]
        for index, row in enumerate(condition_rows):
            struct.pack_into("<HHI", raw, 0x400 + index * 8, *row)
        struct.pack_into("<H", raw, 0x418, 0)
        owner = {
            "owner_id": "MAP:000/000:000:002", "owner_kind": "MAP",
            "root_subkind": "CONDITION", "group": 0, "map": 0,
            "index": [0, 2], "record_address": BASE + 0x410,
            "root": 0x08000520,
        }
        tag, target, guards = _map_condition_precedence_guards_from_rom(
            bytes(raw), owner,
        )
        self.assertEqual(tag, 2)
        self.assertEqual(
            (target["variable"], target["value"]), (0x406F, 8),
        )
        self.assertEqual([
            (guard["variable"], guard["required_value"],
             guard["forbidden_values"])
            for guard in guards
        ], [(0x4079, 1, [0, 2])])

    def test_all_runtime_kinds_use_existing_validator_and_exact_partition(self) -> None:
        fixture = _Fixture()
        document = fixture.build()
        self.assertEqual(document["status"], "PASS")
        self.assertEqual(document["counts"], {
            "event_owner_count": 7,
            "runtime_required_owner_count": 6,
            "generated_owner_path_count": 6,
            "structural_nontrigger_owner_count": 1,
            "runtime_owner_kind_counts": {
                "BG": 2, "COMMON": 1, "COORD": 1,
                "MAP": 1, "OBJECT": 1,
            },
            "structural_nontrigger_owner_kind_counts": {"COORD": 1},
            "map_seed_kind_counts": {
                "stock_warp": 1,
                "stock_connection": 0,
                "engine_teleport": 0,
            },
            "unresolved_count": 0,
            "non_product_shadow_source_count": 0,
            "canonical_shadow_physical_owner_count": 0,
        })
        self.assertEqual(
            set(document["owner_paths"]),
            set(document["runtime_required_owner_ids"]),
        )
        self.assertEqual(
            document["structural_nontrigger_owner_ids"],
            ["COORD:000/001:001"],
        )
        owners = {row["owner_id"]: row for row in fixture.inventory["owners"]}
        for owner_id, path in document["owner_paths"].items():
            normalized = _validated_runtime_trigger_path(
                fixture.rom, owners[owner_id], path,
            )
            self.assertEqual(normalized["kind"], path["kind"])
        self.assertTrue(all(document["assertions"].values()))
        self.assertEqual(document["policies"]["direct_script_calls"], 0)
        self.assertEqual(document["policies"]["direct_callback_calls"], 0)
        provenance = document["input_provenance"]
        self.assertEqual(
            provenance["event_owner_inventory_claimed_self_sha256"],
            provenance["event_owner_inventory_recomputed_self_sha256"],
        )
        self.assertEqual(
            provenance["event_owner_inventory_full_document_sha256"],
            _sha(_stable(fixture.inventory)),
        )

    def test_production_artifact_has_exact_rom_derived_map_seed_counts(
        self,
    ) -> None:
        config_path = ROOT / "config/stage61_display_npc_event_audit.json"
        config = json.loads(config_path.read_text(encoding="utf-8"))
        artifact_path = ROOT / config["outputs"]["runtime_trigger_inputs"]
        if not artifact_path.is_file():
            self.skipTest("production runtime-trigger artifactはbuild後に検証")
        document = json.loads(artifact_path.read_text(encoding="utf-8"))
        rom_path = ROOT / config["outputs"]["rom"]
        self.assertTrue(rom_path.is_file())
        self.assertEqual(document["rom_sha256"], _sha(rom_path.read_bytes()))
        self.assertEqual(
            validate_stage61_runtime_trigger_inputs_map_seed_contract(document),
            EXPECTED_MAP_SEED_KIND_COUNTS,
        )
        self.assertEqual(
            document["counts"]["map_seed_kind_counts"],
            {"stock_warp": 590, "stock_connection": 0, "engine_teleport": 38},
        )

    def test_persisted_map_seed_count_drift_is_rejected(self) -> None:
        document = _Fixture().build()
        document["counts"]["map_seed_kind_counts"]["stock_warp"] += 1
        document["document_sha256"] = _sha(_stable({
            key: value for key, value in document.items()
            if key != "document_sha256"
        }))
        with self.assertRaisesRegex(
            Stage61RuntimeTriggerInputsError,
            "MAP seed kind claimed/recount不一致",
        ):
            validate_stage61_runtime_trigger_inputs_map_seed_contract(
                document, require_canonical_counts=False,
            )

    def test_engine_teleport_rejects_nonzero_usable_foreign_stock_warp(
        self,
    ) -> None:
        fixture = _Fixture()
        raw = bytearray(fixture.rom)
        raw[fixture.SOURCE_EVENTS - BASE + 1] = 0
        fixture.rebuild_after_rom_change(raw)
        document = fixture.build()
        path = document["owner_paths"]["MAP:000/001:000:DIRECT"]
        scan = path["engine_teleport"]["source_provenance"][
            "foreign_stock_warp_scan"
        ]
        self.assertEqual(scan["usable_stock_warp_count"], 0)
        scan["usable_stock_warp_count"] = 1
        document["document_sha256"] = _sha(_stable({
            key: value for key, value in document.items()
            if key != "document_sha256"
        }))
        with self.assertRaisesRegex(
            Stage61RuntimeTriggerInputsError,
            "ENGINE teleport selected despite usable foreign stock warp",
        ):
            validate_stage61_runtime_trigger_inputs_map_seed_contract(
                document, require_canonical_counts=False,
            )

    def test_object_bg_coord_hidden_have_real_geometry_evidence(self) -> None:
        document = _Fixture().build()
        evidence = document["owner_path_evidence"]
        obj = evidence["OBJECT:000/001:000"]
        self.assertEqual(obj["walk_sequence"], ["RIGHT", "LEFT"])
        self.assertEqual(obj["actual_walk_steps"], 2)
        bg = evidence["BG:000/001:000"]
        self.assertEqual(bg["kind"], "FINAL_BG_BFS_WALK_FACE_A")
        self.assertGreaterEqual(bg["actual_walk_steps"], 1)
        self.assertEqual(bg["walk_path_tiles"][-1], bg["stance_tile"])
        coord = evidence["COORD:000/001:000"]
        self.assertEqual(coord["kind"], "FINAL_COORD_ADJACENT_REAL_STEP")
        self.assertGreaterEqual(coord["actual_walk_steps"], 1)
        self.assertEqual(coord["walk_path_tiles"][-1], coord["target_tile"])
        hidden = evidence["BG:000/001:001"]
        self.assertEqual(hidden["consumer_symbol"], "EventScript_HiddenItemScript")
        self.assertTrue(hidden["available_success_special_150"])
        self.assertTrue(hidden["coin_branch_special_350"])

    def test_coord_path_is_self_contained_non_up_multi_step(self) -> None:
        fixture = _Fixture()
        raw = bytearray(fixture.rom)
        # Leave only the west corridor into (3,3).  The exact runtime path
        # must not fall back to an implicit one-step UP in a consumer.
        for x, y in ((3, 2), (3, 4), (4, 3), (2, 2), (2, 4)):
            block_at = fixture.TARGET_BLOCKS - BASE + (x + y * 8) * 2
            struct.pack_into("<H", raw, block_at, 1 << 10)
        fixture.rebuild_after_rom_change(raw)
        document = fixture.build()
        path = document["owner_paths"]["COORD:000/001:000"]
        self.assertEqual(path["start_tile"], {"x": 1, "y": 3})
        self.assertEqual(path["walk_sequence"], ["RIGHT", "RIGHT"])
        self.assertEqual(path["trigger_key"], "RIGHT")
        owner = next(
            row for row in fixture.inventory["owners"]
            if row["owner_id"] == "COORD:000/001:000"
        )
        self.assertEqual(
            _validated_runtime_trigger_path(fixture.rom, owner, path), path,
        )

    def test_object_uses_runtime_placement_not_raw_template_occupancy(self) -> None:
        fixture = _Fixture()
        execution = {
            "trigger": (
                "TELEPORT_TO_WALK_START_REAL_WALK_TO_STANCE_FACE_AND_A"
            ),
            "start": [4, 5], "walk_sequence": ["UP"],
            "stance": [4, 4], "action": "RIGHT",
            "interaction_distance": 1, "counter_tile": None,
            "actual_walk_required": True, "actual_walk_exception": None,
            "walk_path_basis": "EXACT_STOCK_INCOMING_ARRIVAL_TO_OWNER_STANCE",
            "direct_script_call_forbidden": True,
        }
        fixture.npc_catalog["npcs"][0]["interaction_execution"] = deepcopy(
            execution
        )
        placed = fixture.placement["objects"][0]
        placed["object"] = [5, 4]
        placed["interaction_object_basis"] = (
            "MAP_SCRIPT_EXACT_PERMANENT_RUNTIME_POSITION"
        )
        placed["interaction_execution"] = deepcopy(execution)
        document = fixture.build()
        path = document["owner_paths"]["OBJECT:000/001:000"]
        self.assertEqual(path["start_tile"], {"x": 4, "y": 5})
        self.assertEqual(path["walk_sequence"], ["UP"])
        self.assertEqual(path["stance_tile"], {"x": 4, "y": 4})
        self.assertEqual(path["required_facing"], "RIGHT")
        self.assertFalse(path["runtime_topology_probe_required"])
        evidence = document["owner_path_evidence"]["OBJECT:000/001:000"]
        self.assertEqual(evidence["template_object_tile"], [4, 4])
        self.assertEqual(evidence["object_tile"], [5, 4])
        self.assertEqual(
            evidence["interaction_object_basis"],
            "MAP_SCRIPT_EXACT_PERMANENT_RUNTIME_POSITION",
        )

    def test_map_uses_exact_foreign_warp_record_and_actual_step(self) -> None:
        fixture = _Fixture()
        document = fixture.build()
        path = document["owner_paths"]["MAP:000/001:000:DIRECT"]
        self.assertEqual(
            path["entry"],
            "STOCK_WARP_OR_CONNECTION_OR_ENGINE_TELEPORT_OR_RESUME_CALLBACK",
        )
        self.assertEqual(path["map_script_tag"], 3)
        warp = path["stock_warp"]
        self.assertEqual(warp["source"], {"group": 0, "map": 0, "warp_id": 0})
        self.assertEqual(warp["predecessor_tile"], {"x": 2, "y": 3})
        self.assertEqual(warp["trigger_tile"], {"x": 2, "y": 2})
        self.assertEqual(warp["trigger_key"], "UP")
        self.assertEqual(warp["destination"], {"group": 0, "map": 1, "warp_id": 0})
        self.assertEqual(warp["arrival_tile"], {"x": 1, "y": 1})
        self.assertEqual(
            warp["connection_or_warp_record_address"], fixture.SOURCE_WARPS,
        )
        self.assertEqual(
            warp["source_provenance"]["record_raw_sha256"],
            _sha(fixture.rom[
                fixture.SOURCE_WARPS - BASE:fixture.SOURCE_WARPS - BASE + 8
            ]),
        )

    def test_map_warp_scan_ignores_unrelated_invalid_object_array(self) -> None:
        fixture = _Fixture()
        raw = bytearray(fixture.rom)
        header = 0x08056240
        layout = 0x08056340
        blocks = 0x08058600
        events = 0x08059060
        struct.pack_into("<I", raw, 0x08056108 - BASE, header)
        struct.pack_into("<III", raw, header - BASE, layout, events, 0)
        struct.pack_into(
            "<IIIIII", raw, layout - BASE, 8, 8, 0, blocks,
            fixture.PRIMARY_TILESET, fixture.SECONDARY_TILESET,
        )
        raw[blocks - BASE:blocks - BASE + 128] = b"\0" * 128
        raw[events - BASE:events - BASE + 20] = (
            bytes((1, 0, 0, 0))
            + struct.pack("<IIII", 0xFFFFFFFF, 0, 0, 0)
        )
        fixture.rebuild_after_rom_change(raw)
        fixture.inventory["surfaces"].append({
            "physical_map": "000/002",
            "physical_map_key": "DORMANT_INVALID_OBJECT_ARRAY",
            "map_script_structure": [], "owner_ids": [],
        })
        fixture.inventory["inventory_sha256"] = _sha(_stable({
            key: value for key, value in fixture.inventory.items()
            if key != "inventory_sha256"
        }))
        document = fixture.build()
        path = document["owner_paths"]["MAP:000/001:000:DIRECT"]
        self.assertIn("stock_warp", path)
        self.assertEqual(
            path["stock_warp"]["connection_or_warp_record_address"],
            fixture.SOURCE_WARPS,
        )

    def test_map_uses_stock_connection_before_engine_teleport(self) -> None:
        fixture = _Fixture()
        raw = bytearray(fixture.rom)
        raw[fixture.SOURCE_EVENTS - BASE + 1] = 0
        record = 0x08059500
        record_raw = struct.pack("<IiBBBB", 4, 0, 0, 1, 0, 0)
        raw[record - BASE:record - BASE + len(record_raw)] = record_raw
        fixture.rebuild_after_rom_change(raw)
        fixture.placement["maps"] = [{
            "group": 0, "map": 1,
            "entry": {"connections": [{
                "index": 0, "direction": 4,
                "source": [0, 0], "target": [0, 1],
                "row_address": record, "row_raw_hex": record_raw.hex(),
                "seed_basis": "FINAL_ROM_STOCK_CONNECTION",
                "engine_source": {"kind": "MAP_CONNECTION"},
                "coordinate_evidence": [{
                    "source_boundary_tile": [7, 3],
                    "arrival_tile": [0, 3],
                    "source_collision_zero": True,
                    "target_collision_zero": True,
                }],
            }]},
        }]
        document = fixture.build()
        path = document["owner_paths"]["MAP:000/001:000:DIRECT"]
        self.assertNotIn("stock_warp", path)
        self.assertNotIn("engine_teleport", path)
        connection = path["stock_connection"]
        self.assertEqual(
            connection["kind"], "STOCK_CONNECTION_BOUNDARY_STEP",
        )
        self.assertEqual(connection["source"], {"group": 0, "map": 0})
        self.assertEqual(connection["predecessor_tile"], {"x": 7, "y": 3})
        self.assertEqual(connection["trigger_tile"], {"x": 8, "y": 3})
        self.assertEqual(connection["trigger_key"], "RIGHT")
        self.assertEqual(connection["arrival_tile"], {"x": 0, "y": 3})
        self.assertEqual(connection["connection_or_warp_record_address"], record)

    def test_map_resume_is_stock_warp_then_start_b_not_direct_callback(self) -> None:
        fixture = _Fixture()
        raw = bytearray(fixture.rom)
        raw[fixture.TARGET_MAP_SCRIPTS - BASE] = 5
        fixture.rebuild_after_rom_change(raw)
        fixture.inventory["surfaces"][1]["map_script_structure"][0][
            "script_type"
        ] = 5
        fixture.inventory["inventory_sha256"] = _sha(_stable({
            key: value for key, value in fixture.inventory.items()
            if key != "inventory_sha256"
        }))
        document = fixture.build()
        path = document["owner_paths"]["MAP:000/001:000:DIRECT"]
        self.assertNotIn("stock_warp", path)
        resume = path["resume_callback"]
        self.assertEqual(resume["normal_trigger_tokens"], ["START", "B"])
        predecessor = resume["actual_predecessor_consumer"]
        self.assertEqual(predecessor["kind"], "STOCK_WARP_THEN_FIELD_RETURN")
        self.assertEqual(
            predecessor["field_return"]["kind"], "START_MENU_OPEN_CLOSE",
        )
        evidence = document["owner_path_evidence"][
            "MAP:000/001:000:DIRECT"
        ]
        self.assertTrue(evidence["direct_callback_call_forbidden"])
        self.assertEqual(evidence["field_return_tokens"], ["START", "B"])

    def test_map_resume_uses_engine_teleport_when_no_stock_entry_exists(
        self,
    ) -> None:
        fixture = _Fixture()
        raw = bytearray(fixture.rom)
        raw[fixture.SOURCE_EVENTS - BASE + 1] = 0
        raw[fixture.TARGET_MAP_SCRIPTS - BASE] = 5
        fixture.rebuild_after_rom_change(raw)
        fixture.inventory["surfaces"][1]["map_script_structure"][0][
            "script_type"
        ] = 5
        fixture.inventory["inventory_sha256"] = _sha(_stable({
            key: value for key, value in fixture.inventory.items()
            if key != "inventory_sha256"
        }))
        document = fixture.build()
        path = document["owner_paths"]["MAP:000/001:000:DIRECT"]
        resume = path["resume_callback"]
        predecessor = resume["actual_predecessor_consumer"]
        self.assertEqual(
            predecessor["kind"], "ENGINE_TELEPORT_THEN_FIELD_RETURN",
        )
        teleport = predecessor["engine_teleport"]
        self.assertEqual(
            teleport["kind"], "ENGINE_PLAYER_TELEPORT_MAP_LOAD",
        )
        self.assertEqual(teleport["destination"], {"group": 0, "map": 1})
        self.assertEqual(teleport["engine_entry"], "BOOTSTRAP_KANTO_WARP")
        provenance = teleport["source_provenance"]
        self.assertTrue(provenance["first_root_hit_map_identity_required"])
        self.assertTrue(
            provenance[
                "settled_map_identity_not_substituted_for_first_root_hit"
            ]
        )
        self.assertEqual(provenance["usable_stock_connection_count"], 0)
        self.assertEqual(
            predecessor["field_return"]["normal_trigger_tokens"],
            ["START", "B"],
        )

    def test_common_binds_live_caller_pc_separately_from_common_root(self) -> None:
        fixture = _Fixture()
        document = fixture.build()
        path = document["owner_paths"]["COMMON:STANDARD:007"]
        self.assertEqual(path["root_pc"], fixture.COMMON_ROOT)
        self.assertEqual(path["caller_instruction_pc"], fixture.OBJECT_ROOT)
        self.assertEqual(path["caller_owner_id"], "OBJECT:000/001:000")
        evidence = document["owner_path_evidence"]["COMMON:STANDARD:007"]
        self.assertEqual(evidence["common_root_pc"], "0x08060040")
        self.assertEqual(evidence["caller_instruction_pc"], "0x08060000")
        self.assertTrue(
            evidence["common_root_and_caller_pc_are_distinct_evidence"]
        )

    def test_missing_common_live_caller_is_unresolved_and_complete_fails(self) -> None:
        fixture = _Fixture()
        raw = bytearray(fixture.rom)
        common_6_record = 0x08163758 + 6 * 4
        struct.pack_into(
            "<I", raw, common_6_record - BASE, fixture.COMMON_ROOT,
        )
        fixture.rebuild_after_rom_change(raw)
        common = next(
            row for row in fixture.inventory["owners"]
            if row["owner_kind"] == "COMMON"
        )
        common["owner_id"] = "COMMON:STANDARD:006"
        common["index"] = 6
        common["record_address"] = common_6_record
        common["root_field_address"] = common_6_record
        fixture.inventory["inventory_sha256"] = _sha(_stable({
            key: value for key, value in fixture.inventory.items()
            if key != "inventory_sha256"
        }))
        diagnostic = fixture.build(require_complete=False)
        self.assertEqual(diagnostic["status"], "UNRESOLVED")
        self.assertEqual(
            diagnostic["unresolved"], [{
                "owner_id": "COMMON:STANDARD:006",
                "kind": "COMMON_LIVE_CALLER_BYTECODE_REQUIRED",
                "standard_index": 6,
            }],
        )
        with self.assertRaisesRegex(
            Stage61RuntimeTriggerInputsError,
            "RUNTIME_TRIGGER_INPUTS_UNRESOLVED",
        ):
            fixture.build()

    def test_unreferenced_common_7_is_structural_with_full_cfg_abi_evidence(
        self,
    ) -> None:
        fixture = _Fixture()
        raw = bytearray(fixture.rom)
        raw[fixture.OBJECT_ROOT - BASE] = 0x02
        fixture.rebuild_after_rom_change(raw)
        document = fixture.build()
        owner_id = "COMMON:STANDARD:007"
        self.assertEqual(document["status"], "PASS")
        self.assertNotIn(owner_id, document["owner_paths"])
        self.assertIn(owner_id, document["structural_nontrigger_owner_ids"])
        evidence = document["structural_nontrigger_evidence"][owner_id]
        self.assertEqual(
            evidence["kind"], "UNREFERENCED_STANDARD_SCRIPT_TABLE_ENTRY",
        )
        self.assertEqual(evidence["standard_index"], 7)
        self.assertEqual(evidence["record_address"], fixture.COMMON_RECORD)
        self.assertEqual(evidence["root_pc"], fixture.COMMON_ROOT)
        self.assertEqual(evidence["live_caller_instruction_pc_count"], 0)
        self.assertTrue(evidence["exact_table_abi_bound"])
        self.assertTrue(
            evidence["noncommon_cfg_closure"]["cfg_diagnostics_zero"]
        )
        self.assertEqual(
            set(document["structural_nontrigger_evidence"]),
            set(document["structural_nontrigger_owner_ids"]),
        )

    def test_collision_bearing_coord_requires_loaded_field_runtime_probe(self) -> None:
        fixture = _Fixture()
        raw = bytearray(fixture.rom)
        block_at = fixture.TARGET_BLOCKS - BASE + (3 + 3 * 8) * 2
        struct.pack_into("<H", raw, block_at, 1 << 10)
        fixture.rebuild_after_rom_change(raw)
        document = fixture.build()
        evidence = document["owner_path_evidence"]["COORD:000/001:000"]
        self.assertEqual(evidence["base_target_collision"], 1)
        self.assertTrue(evidence["runtime_topology_probe_required"])
        self.assertTrue(evidence["mgba_actual_cardinal_first_hit_required"])
        self.assertTrue(evidence["teleport_does_not_satisfy_trigger"])

    def test_inventory_rom_sha_and_structural_null_are_fail_closed(self) -> None:
        fixture = _Fixture()
        stale = deepcopy(fixture.inventory)
        stale["producer_revision"] = "SELF_HASH_MUST_BE_RECOMPUTED"
        with self.assertRaisesRegex(
            Stage61RuntimeTriggerInputsError, "inventory self-hash不一致",
        ):
            build_stage61_runtime_trigger_inputs(
                fixture.rom, stale, fixture.npc_catalog,
                placement_audit=fixture.placement,
                hidden_item_consumers=fixture.hidden_consumers,
                map_callback_contracts=fixture.callbacks,
                require_canonical_counts=False,
            )
        regenerated = deepcopy(stale)
        regenerated["inventory_sha256"] = _sha(_stable({
            key: value for key, value in regenerated.items()
            if key != "inventory_sha256"
        }))
        document = build_stage61_runtime_trigger_inputs(
            fixture.rom, regenerated, fixture.npc_catalog,
            placement_audit=fixture.placement,
            hidden_item_consumers=fixture.hidden_consumers,
            map_callback_contracts=fixture.callbacks,
            require_canonical_counts=False,
        )
        self.assertEqual(document["status"], "PASS")
        self.assertEqual(
            document["input_provenance"][
                "event_owner_inventory_recomputed_self_sha256"
            ], regenerated["inventory_sha256"],
        )
        bad_sha = deepcopy(fixture.inventory)
        bad_sha["rom_sha256"] = "0" * 64
        with self.assertRaisesRegex(
            Stage61RuntimeTriggerInputsError, "provenance不一致",
        ):
            build_stage61_runtime_trigger_inputs(
                fixture.rom, bad_sha, fixture.npc_catalog,
                placement_audit=fixture.placement,
                hidden_item_consumers=fixture.hidden_consumers,
                map_callback_contracts=fixture.callbacks,
                require_canonical_counts=False,
            )
        raw = bytearray(fixture.rom)
        struct.pack_into("<I", raw, fixture.TARGET_COORDS - BASE + 28, 1)
        fixture.rebuild_after_rom_change(raw)
        # rebuild_documents correctly reads the new final ROM identity, but
        # the structural owner still promises NULL and must be rejected.
        with self.assertRaisesRegex(
            Stage61RuntimeTriggerInputsError, "structural NULL root ROM不一致",
        ):
            fixture.build()


if __name__ == "__main__":
    unittest.main()
