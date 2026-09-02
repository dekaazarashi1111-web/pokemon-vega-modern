from __future__ import annotations

import hashlib
import struct
import unittest
from pathlib import Path

from tools.stage61_topology_producer_state import (
    FLAG_MAPPING,
    MAP_PREIMAGES,
    SOURCE_SCRIPT_PINS,
    STRENGTH_SOURCE_ROOT,
    VAR_MAPPING,
    Stage61TopologyProducerError,
    build_stage61_topology_producer_contract,
    materialize_stage61_topology_producer_state,
)


ROOT = Path(__file__).resolve().parents[1]
CLEAN = ROOT / "inputs/private/FireRed_JPN_Rev0_clean.gba"
STAGE60 = ROOT / "build/stages/60_wild_species_root_repair.gba"
PAYLOAD_BASE = 0x09D00000
STRENGTH_TARGET = 0x09C00000


def _records(raw: bytes) -> list[bytes]:
    return [raw[offset:offset + 24] for offset in range(0, len(raw), 24)]


class Stage61TopologyProducerStateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.clean = CLEAN.read_bytes()
        cls.stage60 = STAGE60.read_bytes()
        cls.contract = build_stage61_topology_producer_contract(
            cls.clean, cls.stage60,
        )
        cls.materialized = materialize_stage61_topology_producer_state(
            cls.contract,
            cls.clean,
            cls.stage60,
            PAYLOAD_BASE,
            root_targets={STRENGTH_SOURCE_ROOT: STRENGTH_TARGET},
        )
        cls.objects = {
            row["map"]: _records(bytes.fromhex(str(row["raw_hex"])))
            for row in cls.materialized.object_rows
        }

    def _node(self, name: str, size: int) -> bytes:
        address = self.materialized.node_addresses[name]
        offset = address - self.materialized.payload_base
        return self.materialized.payload[offset:offset + size]

    def test_contract_pins_all_source_target_surfaces_and_state_owners(self) -> None:
        self.assertTrue(all(self.contract.assertions.values()))
        self.assertEqual(len(self.contract.source_evidence), 10)
        self.assertEqual(len(self.contract.target_evidence), 10)
        self.assertEqual(len(self.contract.script_evidence), 8)
        self.assertEqual(
            {row["name"] for row in self.contract.source_evidence},
            set(MAP_PREIMAGES),
        )
        owner_ids = {
            (row["namespace"], int(str(row["source_id"]), 0),
             int(str(row["target_id"]), 0))
            for row in self.contract.owner_rows
        }
        self.assertEqual(owner_ids, {
            *(("FLAG", source, target)
              for source, target in FLAG_MAPPING.items()),
            *(("VAR", source, target)
              for source, target in VAR_MAPPING.items()),
        })
        self.assertEqual(len(owner_ids), 23)
        self.assertTrue(all(row["producer_owners"] for row in self.contract.owner_rows))
        self.assertTrue(all(row["consumer_owners"] for row in self.contract.owner_rows))
        self.assertFalse(any(
            int(str(row["source_id"]), 0) in {0x0082, 0x02BE}
            for row in self.contract.owner_rows
        ))

    def test_source_script_raw_size_and_sha_are_independently_pinned(self) -> None:
        for name, (address, raw_hex, digest) in SOURCE_SCRIPT_PINS.items():
            raw = bytes.fromhex(raw_hex)
            self.assertEqual(hashlib.sha256(raw).hexdigest(), digest, name)
            offset = address - 0x08000000
            self.assertEqual(self.clean[offset:offset + len(raw)], raw, name)
        self.assertEqual(
            bytes.fromhex(SOURCE_SCRIPT_PINS["ROUTE20_RESET"][1])[:6],
            bytes.fromhex("031a86170800"),
        )
        self.assertEqual(
            bytes.fromhex(SOURCE_SCRIPT_PINS["ROUTE23_RESET"][1])[:6],
            bytes.fromhex("036391170800"),
        )

    def test_any_clean_target_or_script_mutation_is_rejected_fail_closed(self) -> None:
        cases = []
        clean_object = bytearray(self.clean)
        clean_object[0x08375E14 - 0x08000000] ^= 1
        cases.append((bytes(clean_object), self.stage60))
        clean_script = bytearray(self.clean)
        clean_script[0x0816B047 - 0x08000000] ^= 1
        cases.append((bytes(clean_script), self.stage60))
        target_event = bytearray(self.stage60)
        target_event[0x09401138 - 0x08000000] ^= 1
        cases.append((self.clean, bytes(target_event)))
        for clean, target in cases:
            with self.subTest(clean=clean is not self.clean, target=target is not self.stage60):
                with self.assertRaisesRegex(
                    Stage61TopologyProducerError, "identity mismatch"
                ):
                    build_stage61_topology_producer_contract(clean, target)

    def test_payload_and_structural_patch_surface_are_exact(self) -> None:
        result = self.materialized
        self.assertTrue(all(result.verification_assertions.values()))
        self.assertEqual(result.source_pointer_literals, ())
        self.assertEqual([row["count"] for row in result.object_rows],
                         [3, 4, 3, 6, 4, 11, 11])
        self.assertEqual([row["count"] for row in result.coord_rows], [3, 1, 2, 1])
        self.assertEqual([row["map"] for row in result.map_script_rows],
                         ["097/086", "097/087", "096/031", "096/035"])
        self.assertEqual(len(result.patches), 26)
        self.assertEqual(
            {row.role for row in result.patches if row.role.endswith("MAP_SCRIPT_POINTER")},
            {
                "SEAFOAM_B3F_MAP_SCRIPT_POINTER",
                "SEAFOAM_B4F_MAP_SCRIPT_POINTER",
                "ROUTE20_MAP_SCRIPT_POINTER",
                "ROUTE23_MAP_SCRIPT_POINTER",
            },
        )
        self.assertEqual(hashlib.sha256(result.payload).hexdigest(),
                         result.to_report()["payload_sha256"])
        self.assertEqual(result.to_report()["payload_raw_hex"], result.payload.hex())

    def test_boulder_visibility_and_fall_reveal_fields_use_project_namespace(self) -> None:
        expected = {
            ("097/083", 2): (FLAG_MAPPING[0x42], FLAG_MAPPING[0x40]),
            ("097/083", 3): (FLAG_MAPPING[0x43], FLAG_MAPPING[0x41]),
            ("097/084", 3): (FLAG_MAPPING[0x44], FLAG_MAPPING[0x42]),
            ("097/084", 4): (FLAG_MAPPING[0x45], FLAG_MAPPING[0x43]),
            ("097/085", 2): (FLAG_MAPPING[0x46], FLAG_MAPPING[0x44]),
            ("097/085", 3): (FLAG_MAPPING[0x47], FLAG_MAPPING[0x45]),
            ("097/086", 1): (0, FLAG_MAPPING[0x46]),
            ("097/086", 2): (0, FLAG_MAPPING[0x47]),
            ("097/086", 3): (0, FLAG_MAPPING[0x4B]),
            ("097/086", 4): (0, FLAG_MAPPING[0x49]),
            ("097/086", 5): (FLAG_MAPPING[0x4D], FLAG_MAPPING[0x4A]),
            ("097/086", 6): (FLAG_MAPPING[0x4C], FLAG_MAPPING[0x48]),
            ("097/087", 1): (0, FLAG_MAPPING[0x4C]),
            ("097/087", 4): (0, FLAG_MAPPING[0x4D]),
            ("097/040", 10): (0, FLAG_MAPPING[0x58]),
            ("097/041", 11): (FLAG_MAPPING[0x58], FLAG_MAPPING[0x59]),
        }
        actual = {}
        for map_name, records in self.objects.items():
            for record in records:
                if record[1] != 0x61:
                    continue
                actual[(map_name, record[0])] = (
                    struct.unpack_from("<H", record, 12)[0],
                    struct.unpack_from("<H", record, 20)[0],
                )
                script = struct.unpack_from("<I", record, 16)[0]
                self.assertIn(
                    script,
                    {STRENGTH_TARGET, 0x0938E388, 0x093EE8AC},
                )
        for key, value in expected.items():
            self.assertEqual(actual[key], value, key)

    def test_b3_b4_merge_preserves_every_live_target_host(self) -> None:
        target_b3 = _records(bytes.fromhex(
            str(MAP_PREIMAGES["SEAFOAM_B3F"]["target_objects_hex"])
        ))
        target_b4 = _records(bytes.fromhex(
            str(MAP_PREIMAGES["SEAFOAM_B4F"]["target_objects_hex"])
        ))
        output_b3 = self.objects["097/086"]
        output_b4 = self.objects["097/087"]

        # Coordinate/graphics/local identity and the target service roots survive the merge.
        for index in range(4):
            self.assertEqual(output_b3[index][:12], target_b3[index][:12])
            self.assertEqual(output_b4[index][:12], target_b4[index][:12])
        self.assertEqual(struct.unpack_from("<I", output_b3[0], 16)[0], 0x093EE8AC)
        self.assertEqual(struct.unpack_from("<I", output_b3[1], 16)[0], 0x093EE8AC)
        self.assertEqual(struct.unpack_from("<I", output_b4[0], 16)[0], 0x0938E388)
        self.assertEqual(struct.unpack_from("<I", output_b4[3], 16)[0], 0x093EE8AC)

        # HOST_ALOLA_LIGHT remains connected to its project bridge and native transaction.
        root = struct.unpack_from("<I", output_b4[0], 16)[0]
        root_offset = root - 0x08000000
        self.assertEqual(
            self.stage60[root_offset:root_offset + 16],
            bytes.fromhex("6a5a1601800000160080390023198138"),
        )
        bridge_offset = 0x092DBF60 - 0x08000000
        self.assertEqual(
            self.stage60[bridge_offset:bridge_offset + 7],
            bytes.fromhex("6a5a2361102d09"),
        )

        # Only topology-owned visibility fields are overridden on shared records.
        self.assertEqual(struct.unpack_from("<H", output_b3[0], 20)[0],
                         FLAG_MAPPING[0x46])
        self.assertEqual(struct.unpack_from("<H", output_b3[1], 20)[0],
                         FLAG_MAPPING[0x47])
        self.assertEqual(struct.unpack_from("<H", output_b4[0], 20)[0],
                         FLAG_MAPPING[0x4C])
        self.assertEqual(struct.unpack_from("<H", output_b4[3], 20)[0],
                         FLAG_MAPPING[0x4D])
        self.assertEqual(output_b4[1], target_b4[1])
        self.assertEqual(output_b4[2], target_b4[2])

        # The only missing B3 source boulders are appended at unused local5/6.
        self.assertEqual([record[0] for record in output_b3], [1, 2, 3, 4, 5, 6])
        self.assertEqual(len({record[0] for record in output_b3}), 6)
        self.assertEqual(len({record[0] for record in output_b4}), 4)

    def test_b3_b4_tables_condition_structs_and_physical_warp_are_project_owned(self) -> None:
        b3_table = self._node("b3_table", 11)
        self.assertEqual((b3_table[0], b3_table[5], b3_table[10]), (3, 2, 0))
        self.assertEqual(struct.unpack_from("<I", b3_table, 1)[0],
                         self.materialized.node_addresses["b3_transition"])
        self.assertEqual(struct.unpack_from("<I", b3_table, 6)[0],
                         self.materialized.node_addresses["b3_condition"])
        b3_condition = self._node("b3_condition", 10)
        self.assertEqual(struct.unpack_from("<HHI", b3_condition), (
            0x4001, 1, self.materialized.node_addresses["b3_fall"],
        ))
        self.assertEqual(b3_condition[-2:], b"\x00\x00")

        b4_table = self._node("b4_table", 21)
        self.assertEqual([b4_table[offset] for offset in (0, 5, 10, 15, 20)],
                         [3, 1, 4, 2, 0])
        self.assertNotIn(5, [b4_table[offset] for offset in (0, 5, 10, 15)])
        b4_frame = self._node("b4_frame_condition", 18)
        first = struct.unpack_from("<HHI", b4_frame, 0)
        second = struct.unpack_from("<HHI", b4_frame, 8)
        self.assertEqual(first[:2], (VAR_MAPPING[0x4063], 1))
        self.assertEqual(second[:2], (0x4001, 1))
        self.assertEqual(b4_frame[-2:], b"\x00\x00")

        b3_fall = self._node("b3_fall", 78)
        self.assertIn(bytes((0x39, 97, 87, 0xFF, 27, 0, 21, 0)), b3_fall)
        self.assertNotIn(struct.pack("<I", 0x0816B10B), self.materialized.payload)
        self.assertNotIn(struct.pack("<I", 0x0816B119), self.materialized.payload)

    def test_route_reset_writers_and_victory_coord_scripts_have_mapped_operands(self) -> None:
        route20 = self._node("route20_transition", 19)
        self.assertEqual(route20.count(0x2B), 2)
        self.assertIn(struct.pack("<H", FLAG_MAPPING[0x02D2]), route20)
        self.assertIn(struct.pack("<H", FLAG_MAPPING[0x02D3]), route20)
        b3_reset = self._node("route20_b3", 25)
        for source in range(0x40, 0x48):
            self.assertIn(struct.pack("<H", FLAG_MAPPING[source]), b3_reset)
        b4_reset = self._node("route20_b4", 19)
        for source in range(0x48, 0x4E):
            self.assertIn(struct.pack("<H", FLAG_MAPPING[source]), b4_reset)
        route23 = self._node("route23_transition", 27)
        self.assertIn(struct.pack("<H", FLAG_MAPPING[0x58]), route23)
        self.assertIn(struct.pack("<H", FLAG_MAPPING[0x59]), route23)
        for source in range(0x4064, 0x4068):
            self.assertIn(struct.pack("<H", VAR_MAPPING[source]), route23)

        expected_coords = {
            "097/087": [(26, 19, 1, VAR_MAPPING[0x4063], 0),
                         (27, 19, 1, VAR_MAPPING[0x4063], 0),
                         (28, 19, 1, VAR_MAPPING[0x4063], 0)],
            "097/039": [(20, 16, 3, VAR_MAPPING[0x4064], 99)],
            "097/040": [(2, 19, 3, VAR_MAPPING[0x4065], 99),
                         (14, 19, 3, VAR_MAPPING[0x4066], 99)],
            "097/041": [(7, 7, 3, VAR_MAPPING[0x4067], 99)],
        }
        for row in self.materialized.coord_rows:
            raw = bytes.fromhex(str(row["raw_hex"]))
            actual = []
            for offset in range(0, len(raw), 16):
                x, y, elevation, variable, value, pointer = struct.unpack_from(
                    "<HHBxHH2xI", raw, offset,
                )
                actual.append((x, y, elevation, variable, value))
                self.assertGreaterEqual(pointer, PAYLOAD_BASE)
                self.assertLess(pointer, PAYLOAD_BASE + len(self.materialized.payload))
            self.assertEqual(actual, expected_coords[row["map"]])
        for name in ("victory1_switch", "victory2a_switch",
                     "victory2b_switch", "victory3_switch"):
            raw = self._node(name, 56)
            self.assertIn(struct.pack("<H", 0x0307), raw)
            self.assertIn(struct.pack("<H", 0x0317), raw)

    def test_old_object_record_and_field_sites_rebase_exactly(self) -> None:
        result = self.materialized
        self.assertEqual(len(result.record_address_mapping), 33)
        for old, new in result.record_address_mapping.items():
            self.assertEqual(result.rebase_object_address(old), new)
            self.assertEqual(result.rebase_object_address(old + 1), new + 1)
            self.assertEqual(result.rebase_object_address(old + 16), new + 16)
            self.assertEqual(result.rebase_object_address(old + 23), new + 23)
        self.assertIsNone(result.rebase_object_address(0x08000000))
        self.assertIsNone(result.rebase_object_address(
            max(result.record_address_mapping) + 24,
        ))

    def test_structural_patches_apply_cleanly_in_memory(self) -> None:
        image = bytearray(self.stage60)
        for patch in self.materialized.patches:
            offset = patch.address - 0x08000000
            self.assertEqual(bytes(image[offset:offset + len(patch.expected)]),
                             patch.expected)
            image[offset:offset + len(patch.replacement)] = patch.replacement
        for patch in self.materialized.patches:
            offset = patch.address - 0x08000000
            self.assertEqual(bytes(image[offset:offset + len(patch.replacement)]),
                             patch.replacement)

    def test_unrelocated_or_extra_root_mapping_and_bad_payload_base_are_rejected(self) -> None:
        bad_roots = (
            {STRENGTH_SOURCE_ROOT: STRENGTH_SOURCE_ROOT},
            {STRENGTH_SOURCE_ROOT: STRENGTH_TARGET, 0x0816B295: 0x09C00100},
            {},
        )
        for roots in bad_roots:
            with self.subTest(roots=roots):
                with self.assertRaises(Stage61TopologyProducerError):
                    materialize_stage61_topology_producer_state(
                        self.contract, self.clean, self.stage60, PAYLOAD_BASE,
                        root_targets=roots,
                    )
        for base in (0x08FFFFFC, 0x09D00001, 0x0A000000):
            with self.subTest(base=base):
                with self.assertRaises(Stage61TopologyProducerError):
                    materialize_stage61_topology_producer_state(
                        self.contract, self.clean, self.stage60, base,
                        root_targets={STRENGTH_SOURCE_ROOT: STRENGTH_TARGET},
                    )

    def test_materialization_is_deterministic(self) -> None:
        again = materialize_stage61_topology_producer_state(
            self.contract,
            self.clean,
            self.stage60,
            PAYLOAD_BASE,
            root_targets={STRENGTH_SOURCE_ROOT: STRENGTH_TARGET},
        )
        self.assertEqual(again.payload, self.materialized.payload)
        self.assertEqual(again.patches, self.materialized.patches)
        self.assertEqual(again.record_address_mapping,
                         self.materialized.record_address_mapping)
        self.assertEqual(again.materialization_sha256,
                         self.materialized.materialization_sha256)


if __name__ == "__main__":
    unittest.main()
