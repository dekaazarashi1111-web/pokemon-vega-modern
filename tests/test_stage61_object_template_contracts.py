from __future__ import annotations

import hashlib
import json
import struct
import unittest
from copy import deepcopy
from types import SimpleNamespace

from tools.stage61_object_template_contracts import (
    MAP_GROUPS_POINTER_SITE,
    ROM_BASE,
    Stage61ObjectTemplateContractError,
    attach_stage61_object_template_contracts,
    build_stage61_object_template_contracts,
    decode_object_template,
    read_object_template,
    validate_stage61_object_template_contract_document,
    validate_stage61_object_template_contracts,
)


def _record(
    *, local_id: int, graphics_id: int, x: int, y: int,
    script: int, flag: int = 0, kind: int = 0,
    elevation: int = 3, movement: int = 2, movement_range: int = 0x21,
    trainer_type: int = 0, sight_range: int = 0,
) -> bytes:
    raw = bytearray(24)
    raw[0] = local_id
    raw[1] = graphics_id
    raw[2] = kind
    raw[3] = 0xAB
    struct.pack_into("<hh", raw, 4, x, y)
    raw[8] = elevation
    raw[9] = movement
    raw[10] = movement_range
    raw[11] = 0xCD
    struct.pack_into("<HHIH", raw, 12, trainer_type, sight_range, script, flag)
    raw[22:24] = b"\xEE\xFF"
    return bytes(raw)


def _reseal(document: dict) -> None:
    document.pop("contract_sha256", None)
    raw = (
        json.dumps(
            document, ensure_ascii=False, sort_keys=True,
            separators=(",", ":"),
        ) + "\n"
    ).encode("utf-8")
    document["contract_sha256"] = hashlib.sha256(raw).hexdigest()


class _Fixture:
    GROUPS = 0x08010000
    GROUP0 = 0x08010100
    HEADERS = tuple(0x08010200 + index * 0x20 for index in range(5))
    EVENTS = tuple(0x08010400 + index * 0x20 for index in range(5))
    OBJECTS = tuple(0x08010600 + index * 0x40 for index in range(5))

    A = "OBJECT:000/000:000"
    T = "OBJECT:000/001:000"
    N = "OBJECT:000/002:000"
    S = "OBJECT:000/003:000"
    M = "OBJECT:000/004:000"

    def __init__(self) -> None:
        self.a = _record(
            local_id=1, graphics_id=5, x=-2, y=3,
            script=0x08101000, flag=0x10, trainer_type=1, sight_range=4,
        )
        self.t = _record(
            local_id=2, graphics_id=6, x=1, y=2,
            script=0x08102000,
        )
        self.n = _record(
            local_id=15, graphics_id=109, x=5, y=6,
            script=0x08103000,
        )
        self.s = _record(
            local_id=4, graphics_id=20, x=6, y=7,
            script=0x08104000,
        )
        self.topology = _record(
            local_id=2, graphics_id=61, x=-10, y=12,
            script=0x09310000, flag=0x18C5,
            movement=7, movement_range=0,
        )
        self.missing = _record(
            local_id=7, graphics_id=30, x=-12, y=-9,
            script=0x09350000, flag=0x18C6,
            movement=8, movement_range=0,
        )
        raw = bytearray(b"\xFF" * 0x60000)
        struct.pack_into("<I", raw, MAP_GROUPS_POINTER_SITE, self.GROUPS)
        struct.pack_into("<I", raw, self.GROUPS - ROM_BASE, self.GROUP0)
        struct.pack_into("<5I", raw, self.GROUP0 - ROM_BASE, *self.HEADERS)
        bases = (self.a, self.t, self.n, self.s, b"")
        for index, base in enumerate(bases):
            struct.pack_into(
                "<II", raw, self.HEADERS[index] - ROM_BASE,
                0, self.EVENTS[index],
            )
            event = self.EVENTS[index] - ROM_BASE
            raw[event:event + 4] = bytes((int(bool(base)), 0, 0, 0))
            struct.pack_into(
                "<IIII", raw, event + 4,
                self.OBJECTS[index] if base else 0, 0, 0, 0,
            )
            if base:
                start = self.OBJECTS[index] - ROM_BASE
                raw[start:start + 24] = base
        self.rom = bytes(raw)
        missing_prefix = b"MISSING!"
        self.missing_object = SimpleNamespace(
            payload_base=0x09000000,
            payload=missing_prefix + self.missing,
            object_array_address=0x09000000 + len(missing_prefix),
            requirement=SimpleNamespace(
                target_group=0, target_map=4, target_index=0,
                target_local_id=7,
            ),
        )
        self.owners = [
            {"npc_id": self.A, "group": 0, "map": 0, "object_index": 0,
             # These final-looking fields must not be consumed by the builder.
             "graphics_id": 0, "x": 30000, "script_pointer": 0},
            {"npc_id": self.T, "group": 0, "map": 1, "object_index": 0},
            {"npc_id": self.N, "group": 0, "map": 2, "object_index": 0},
            {"npc_id": self.S, "group": 0, "map": 3, "object_index": 0},
            {"npc_id": self.M, "group": 0, "map": 4, "object_index": 0},
        ]

    def kwargs(self) -> dict:
        after_archive = bytearray(self.a)
        struct.pack_into("<hh", after_archive, 4, -1, 4)
        placement_expected = bytes(after_archive[4:11])
        placement_replacement = struct.pack("<hhBBB", -5, 7, 4, 10, 0)
        return {
            "topology_rows": [{
                "map": "000/001", "count": 1,
                "raw_hex": self.topology.hex(),
                "sha256": hashlib.sha256(self.topology).hexdigest(),
            }],
            "missing_object": self.missing_object,
            "graphics_records": [
                SimpleNamespace(
                    group=0, map_number=0, object_index=0,
                    record_preimage=self.a, source_graphics_id=5,
                    runtime_graphics_id=155, action="REMAP_CLEAN_CLOSURE",
                ),
                # Product Snorlax sites suppress this ordinary clone overlay
                # and receive reserved ID 239 in the later explicit step.
                SimpleNamespace(
                    group=0, map_number=2, object_index=0,
                    record_preimage=self.n, source_graphics_id=109,
                    runtime_graphics_id=175, action="REMAP_CLEAN_CLOSURE",
                ),
            ],
            "visibility_rows": [{
                "owner_id": self.A,
                "target_flag_before": 0x10,
                # Generic plan value is retained for provenance, while the
                # applied product override must win when target_flag exists.
                "target_flag_after": 0x18C5,
                "target_flag": 0x1847,
                "mapping_basis": "FIXTURE_EXPLICIT",
            }],
            "semantic_root_plans": [SimpleNamespace(
                source_script_pointer=0x08101000,
                owners=({"event": "OBJECT", "owner_id": self.A},),
            )],
            "root_targets": {0x08101000: 0x09300000},
            "archive_placement_rows": [{
                "group": 0, "map": 0,
                "objects": [{"local_id": 1, "before": [-2, 3], "after": [-1, 4]}],
            }],
            "placement_repairs": [{
                "npc_id": self.A,
                "expected_hex": placement_expected.hex(),
                "replacement_hex": placement_replacement.hex(),
            }],
            "placement_mutable_owner_ids": [self.A],
            "snorlax_sites": [(0, 2, 15)],
            "supplemental_owners": [{
                "npc_id": self.S,
                "local_id": 4,
                "script_pointer": 0x08104001,
                "object": {
                    "graphics_id": 21, "kind": 0, "movement_type": 8,
                    "x": -7, "y": 8, "elevation": 3,
                    "trainer_type": 0, "sight_range": 0, "flag": 0,
                },
            }],
            "expected_owner_count": 5,
        }

    def build(self, **changes) -> dict:
        kwargs = self.kwargs()
        kwargs.update(changes)
        return build_stage61_object_template_contracts(
            self.rom, self.owners, **kwargs,
        )

    def final_rom(self, document: dict) -> bytes:
        raw = bytearray(self.rom)
        by_owner = {
            row["owner_id"]: bytes.fromhex(row["expected_template_raw_hex"])
            for row in document["owners"]
        }
        for index, owner_id in enumerate((self.A, self.T, self.N, self.S, self.M)):
            event = self.EVENTS[index] - ROM_BASE
            raw[event] = 1
            struct.pack_into("<I", raw, event + 4, self.OBJECTS[index])
            start = self.OBJECTS[index] - ROM_BASE
            raw[start:start + 24] = by_owner[owner_id]
        return bytes(raw)


class Stage61ObjectTemplateContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = _Fixture()

    def test_builds_full_24_byte_independent_expectations(self) -> None:
        document = self.fixture.build()
        self.assertEqual(document["status"], "PASS")
        self.assertEqual(document["owner_count"], 5)
        self.assertTrue(all(document["assertions"].values()))
        self.assertEqual(
            document["expectation_source_policy"],
            "STAGE60_PREIMAGE_PLUS_EXPLICIT_TRANSFORM_PLANS_ONLY_"
            "FINAL_ROM_FORBIDDEN_DURING_BUILD",
        )
        rows = {row["owner_id"]: row for row in document["owners"]}

        a = bytes.fromhex(rows[self.fixture.A]["expected_template_raw_hex"])
        fields = decode_object_template(a)
        self.assertEqual(fields["graphics_id"], 155)
        self.assertEqual((fields["x"], fields["y"]), (-5, 7))
        self.assertEqual(fields["elevation"], 4)
        self.assertEqual(fields["movement_type"], 10)
        self.assertEqual((fields["movement_range_x"], fields["movement_range_y"]), (0, 0))
        self.assertEqual(fields["script_pointer"], 0x09300000)
        self.assertEqual(fields["flag"], 0x1847)
        # Full-record derivation preserves padding/reserved bytes too.
        self.assertEqual((a[3], a[11], a[22:24]), (0xAB, 0xCD, b"\xEE\xFF"))
        self.assertEqual(
            rows[self.fixture.T]["expected_template_raw_hex"],
            self.fixture.topology.hex().upper(),
        )
        self.assertEqual(
            rows[self.fixture.M]["expected_template_raw_hex"],
            self.fixture.missing.hex().upper(),
        )
        self.assertTrue(all(
            len(row["expected_template_raw_hex"]) == 48
            and row["expected_template_raw_hex"]
                == row["expected_template_raw_hex"].upper()
            for row in rows.values()
        ))
        self.assertIsNone(rows[self.fixture.M]["stage60_preimage_raw_hex"])
        self.assertEqual(rows[self.fixture.N]["expected_fields"]["graphics_id"], 239)
        self.assertEqual(
            (rows[self.fixture.S]["expected_fields"]["x"],
             rows[self.fixture.S]["expected_fields"]["y"]),
            (-7, 8),
        )
        self.assertEqual(rows[self.fixture.S]["expected_fields"]["script_pointer"], 0x08104001)
        self.assertEqual(
            [step["kind"] for step in rows[self.fixture.A]["provenance"]],
            [
                "STAGE60_PREIMAGE", "GRAPHICS_NAMESPACE",
                "VISIBILITY_NAMESPACE", "SEMANTIC_ROOT_RELOCATION",
                "ARCHIVE_POSITION", "FINAL_INTERACTION_PLACEMENT",
            ],
        )
        self.assertEqual(
            document["transform_counts"],
            {
                "topology_exact_owner_count": 1,
                "missing_object_owner_count": 1,
                "graphics_owner_count": 2,
                "graphics_nonruntime_owner_ignored_count": 0,
                "visibility_owner_count": 1,
                "semantic_owner_count": 1,
                "archive_position_owner_count": 1,
                "pre_placement_exact_patch_count": 0,
                "final_interaction_placement_owner_count": 1,
                "snorlax_owner_count": 1,
                "supplemental_owner_count": 1,
            },
        )
        self.assertEqual(
            [step["kind"] for step in rows[self.fixture.N]["provenance"]],
            [
                "STAGE60_PREIMAGE",
                "GRAPHICS_NAMESPACE_SUPPRESSED_BY_SNORLAX_RESERVATION",
                "SNORLAX_RESERVED_GRAPHICS",
            ],
        )

    def test_signed_coordinates_are_not_reinterpreted_as_unsigned(self) -> None:
        document = self.fixture.build()
        rows = {row["owner_id"]: row for row in document["owners"]}
        self.assertEqual(rows[self.fixture.M]["expected_fields"]["x"], -12)
        self.assertEqual(rows[self.fixture.M]["expected_fields"]["y"], -9)
        self.assertEqual(read_object_template(self.fixture.rom, 0, 0, 0), self.fixture.a)
        self.assertEqual(decode_object_template(self.fixture.a)["x"], -2)

    def test_final_rom_is_a_separate_observation_only_validation_input(self) -> None:
        document = self.fixture.build()
        report = validate_stage61_object_template_contracts(
            document, final_rom=self.fixture.final_rom(document),
        )
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["owner_count"], 5)
        self.assertEqual(report["mismatch_count"], 0)
        self.assertEqual(report["observed_source"], "FINAL_ROM_MAP_EVENT_POINTERS")

    def test_explicit_observed_mapping_passes_exact_owner_set(self) -> None:
        document = self.fixture.build()
        observed = {
            row["owner_id"]: row["expected_template_raw_hex"]
            for row in document["owners"]
        }
        report = validate_stage61_object_template_contracts(
            document, observed_templates=observed,
        )
        self.assertTrue(report["exact_24_byte_match_all"])

    def test_graphics_full_record_preimage_mismatch_is_rejected(self) -> None:
        bad = bytearray(self.fixture.a)
        bad[3] ^= 1
        rows = self.fixture.kwargs()["graphics_records"]
        rows[0] = SimpleNamespace(
            **{**rows[0].__dict__, "record_preimage": bytes(bad)}
        )
        with self.assertRaisesRegex(
            Stage61ObjectTemplateContractError, "full-record preimage mismatch",
        ):
            self.fixture.build(graphics_records=rows)

    def test_missing_semantic_transform_target_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            Stage61ObjectTemplateContractError, "semantic root transform不足",
        ):
            self.fixture.build(root_targets={})

    def test_visibility_missing_transform_is_rejected(self) -> None:
        rows = [{
            "owner_id": self.fixture.A,
            "target_flag_before": 0x10,
        }]
        with self.assertRaisesRegex(
            Stage61ObjectTemplateContractError, "visibility target transform不足",
        ):
            self.fixture.build(visibility_rows=rows)

    def test_placement_preimage_mismatch_is_rejected(self) -> None:
        repairs = deepcopy(self.fixture.kwargs()["placement_repairs"])
        repairs[0]["expected_hex"] = "00" * 7
        with self.assertRaisesRegex(
            Stage61ObjectTemplateContractError, "preimage mismatch",
        ):
            self.fixture.build(placement_repairs=repairs)

    def test_existing_owner_placement_change_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            Stage61ObjectTemplateContractError,
            "既存object ownerへの.*配置変更は禁止",
        ):
            self.fixture.build(placement_mutable_owner_ids=[])

    def test_unapplied_placement_row_binds_already_current_replacement(self) -> None:
        kwargs = self.fixture.kwargs()
        after_archive = bytearray(self.fixture.a)
        struct.pack_into("<hh", after_archive, 4, -1, 4)
        kwargs["placement_repairs"] = [{
            "npc_id": self.fixture.A,
            # This dormant baseline preimage is not applied after Archive.
            "expected_hex": self.fixture.a[4:11].hex(),
            "replacement_hex": bytes(after_archive[4:11]).hex(),
            "patch_applied": False,
        }]
        document = self.fixture.build(**kwargs)
        row = next(
            row for row in document["owners"]
            if row["owner_id"] == self.fixture.A
        )
        self.assertEqual((row["expected_fields"]["x"], row["expected_fields"]["y"]), (-1, 4))

    def test_unknown_transform_owner_is_rejected(self) -> None:
        repairs = deepcopy(self.fixture.kwargs()["placement_repairs"])
        repairs.append({
            "npc_id": "OBJECT:000/099:000",
            "expected_hex": "00" * 7,
            "replacement_hex": "00" * 7,
        })
        with self.assertRaisesRegex(
            Stage61ObjectTemplateContractError, "未知のobject owner",
        ):
            self.fixture.build(placement_repairs=repairs)

    def test_final_observed_mismatch_is_rejected_with_owner(self) -> None:
        document = self.fixture.build()
        observed = {
            row["owner_id"]: bytearray.fromhex(row["expected_template_raw_hex"])
            for row in document["owners"]
        }
        observed[self.fixture.T][9] ^= 1
        with self.assertRaisesRegex(
            Stage61ObjectTemplateContractError,
            r"final ObjectEventTemplate mismatch: OBJECT:000/001:000",
        ):
            validate_stage61_object_template_contracts(
                document,
                observed_templates={key: bytes(value) for key, value in observed.items()},
            )

    def test_unknown_or_missing_observed_owner_is_rejected(self) -> None:
        document = self.fixture.build()
        observed = {
            row["owner_id"]: row["expected_template_raw_hex"]
            for row in document["owners"]
            if row["owner_id"] != self.fixture.M
        }
        observed["OBJECT:000/099:000"] = "00" * 24
        with self.assertRaisesRegex(
            Stage61ObjectTemplateContractError, "observed owner集合不一致",
        ):
            validate_stage61_object_template_contracts(
                document, observed_templates=observed,
            )

    def test_contract_self_hash_and_expected_raw_are_fail_closed(self) -> None:
        document = self.fixture.build()
        tampered = deepcopy(document)
        tampered["owners"][0]["expected_template_raw_hex"] = "00" * 24
        with self.assertRaisesRegex(
            Stage61ObjectTemplateContractError, "self hash不一致",
        ):
            validate_stage61_object_template_contract_document(tampered)

    def test_lowercase_template_hex_is_not_canonical(self) -> None:
        document = self.fixture.build()
        tampered = deepcopy(document)
        row = next(
            row for row in tampered["owners"]
            if row["owner_id"] == self.fixture.A
        )
        row["expected_template_raw_hex"] = row[
            "expected_template_raw_hex"
        ].lower()
        _reseal(tampered)
        with self.assertRaisesRegex(
            Stage61ObjectTemplateContractError, "大文字HEX canonical",
        ):
            validate_stage61_object_template_contract_document(tampered)

        observed = {
            row["owner_id"]: row["expected_template_raw_hex"]
            for row in document["owners"]
        }
        observed[self.fixture.A] = observed[self.fixture.A].lower()
        with self.assertRaisesRegex(
            Stage61ObjectTemplateContractError, "大文字HEX canonical",
        ):
            validate_stage61_object_template_contracts(
                document, observed_templates=observed,
            )

    def test_attach_requires_exact_owner_set_and_does_not_replace_source_fields(self) -> None:
        document = self.fixture.build()
        attached = attach_stage61_object_template_contracts(
            self.fixture.owners, document,
        )
        by_owner = {row["npc_id"]: row for row in attached}
        self.assertEqual(by_owner[self.fixture.A]["graphics_id"], 0)
        self.assertEqual(by_owner[self.fixture.A]["expected_template_fields"]["graphics_id"], 155)
        self.assertEqual(
            by_owner[self.fixture.A]["expected_template_contract_sha256"],
            document["contract_sha256"],
        )
        with self.assertRaisesRegex(
            Stage61ObjectTemplateContractError, "attach対象owner不足",
        ):
            attach_stage61_object_template_contracts(
                self.fixture.owners[:-1], document,
            )


if __name__ == "__main__":
    unittest.main()
