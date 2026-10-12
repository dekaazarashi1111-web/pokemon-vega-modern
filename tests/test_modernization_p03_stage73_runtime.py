from __future__ import annotations

import struct
import unittest
from pathlib import Path

from tools.modernization_p03_stage73_runtime import (
    DEFAULT_CONFIG,
    EXACT_EGG_SPECIES,
    PROVISIONAL_LOAD_ADDRESS,
    ModernizationP03Stage73RuntimeError,
    _veneer,
    build_capacity_audit,
    build_exact_egg_payload,
    build_runtime_tables,
    build_stage73_image,
    compile_payload,
    compile_route_model,
    plan_rotom_move_transition,
    read_config,
    require_pinned_parent,
    sha256,
    verify_existing_light_ball_owner,
)


ROOT = Path(__file__).resolve().parents[1]


class ModernizationP03Stage73RuntimeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = read_config(ROOT, DEFAULT_CONFIG)
        cls.model = compile_route_model(ROOT, cls.config)
        cls.blobs, cls.table_audit = build_runtime_tables(cls.model)

    def test_parent_identity_gate_matches_config_state(self) -> None:
        if self.config["status"] == "STAGE72_IDENTITY_PINNED":
            require_pinned_parent(self.config)
            return
        with self.assertRaisesRegex(
            ModernizationP03Stage73RuntimeError,
            "Stage72 identity未確定",
        ):
            require_pinned_parent(self.config)
        with self.assertRaisesRegex(
            ModernizationP03Stage73RuntimeError,
            "Stage72 identity未確定",
        ):
            build_stage73_image(ROOT, DEFAULT_CONFIG)

    def test_five_group_accounting_and_exclusions(self) -> None:
        audit = self.model.route_audit
        self.assertEqual(audit["source_route_count"], 118528)
        self.assertEqual(audit["selection_boundary"]["five_group_selected_count"], 40570)
        self.assertEqual(audit["selection_boundary"]["side_change_global_excluded_count"], 159)
        self.assertEqual(audit["selection_boundary"]["side_change_five_group_excluded_count"], 72)
        self.assertEqual(audit["browt_pombon_gecqua_source_routes"], 0)
        self.assertEqual(audit["browt_pombon_gecqua_materialized"], 0)
        self.assertEqual(audit["prohibited_coercions_materialized"], 0)
        self.assertEqual(audit["accounting"]["consumer_boundary_accounted_routes"], 40570)
        self.assertEqual(audit["accounting"]["new_runtime_materialized_routes"], 5363)
        self.assertEqual(audit["accounting"]["existing_owner_accounted_routes"], 35207)
        self.assertEqual(
            audit["accounting"]["new_runtime_materialized_breakdown"],
            {
                "conditional_exact_egg": 40,
                "shared_egg": 5023,
                "reminder": 295,
                "rotom_form_change": 5,
            },
        )
        evidence = audit["conditional_breeding_existing_owner_evidence"]
        self.assertEqual(evidence["canonical_species"], 24)
        self.assertEqual(evidence["light_ball_item"], 202)
        self.assertEqual(evidence["volt_tackle_move"], 344)
        self.assertEqual(evidence["runtime_owner"], "PARENT_BUILD_EGG_MOVESET")
        self.assertEqual(
            evidence["instruction_evidence"]["volt_tackle_build"]["immediate"],
            172,
        )
        self.assertEqual(
            evidence["instruction_evidence"]["volt_tackle_build"]["result"],
            344,
        )
        self.assertEqual(audit["remaining_full_p03_routes"]["total"], 26648)

    def test_indexed_tables_have_exact_consumer_counts(self) -> None:
        self.assertEqual(self.table_audit["Shared"]["move_rows"], 5023)
        self.assertEqual(self.table_audit["Reminder"]["move_rows"], 295)
        self.assertEqual(self.table_audit["ExactEgg"]["move_rows"], 40)
        self.assertEqual(self.table_audit["Shared"]["max_rows_per_species"], 15)
        self.assertEqual(self.table_audit["Reminder"]["max_rows_per_species"], 17)
        self.assertEqual(self.table_audit["ExactEgg"]["species_with_rows"], 7)
        self.assertEqual(set(self.model.exact_egg_rows), EXACT_EGG_SPECIES)
        for name in ("Shared", "Reminder", "ExactEgg"):
            raw = self.blobs[f"Stage73_{name}Index"]
            offsets = struct.unpack(f"<{len(raw) // 2}H", raw)
            self.assertEqual(len(offsets), 1622)
            self.assertEqual(offsets[0], 0)
            self.assertEqual(offsets[-1], self.table_audit[name]["move_rows"])
            self.assertEqual(tuple(sorted(offsets)), offsets)

    def test_arm_payload_compiles_and_exports_consumer_abi(self) -> None:
        compiled = compile_payload(ROOT, PROVISIONAL_LOAD_ADDRESS, self.blobs)
        self.assertEqual(compiled.symbols["Stage73_RuntimeProbe"], PROVISIONAL_LOAD_ADDRESS)
        for symbol in (
            "Stage73_GetAllEggMoves",
            "Stage73_GetMoveRelearnerMoves",
            "Stage73_CollectionApplySelectedForm",
            "Stage73_OriginalGetAllEggMoves",
            "Stage73_OriginalCollectionApplySelectedForm",
        ):
            self.assertIn(symbol, compiled.symbols)
            self.assertEqual(compiled.symbols[symbol] & 1, 0)
        self.assertNotIn("Stage73_BuildEggMoveset", compiled.symbols)
        self.assertNotIn("Stage73_OriginalBuildEggMoveset", compiled.symbols)
        self.assertLess(len(compiled.code), 0x10000)

    def test_all_parent_hook_preimages_match_stage72_bytes(self) -> None:
        parent_row = self.config["parent_identity"]["rom"]
        parent_path = ROOT / parent_row["path"]
        if not parent_path.is_file():
            self.skipTest("Stage72 parent ROM is unavailable")
        parent = parent_path.read_bytes()
        self.assertEqual(len(parent), parent_row["size"])
        if self.config["status"] == "STAGE72_IDENTITY_PINNED":
            self.assertEqual(sha256(parent), parent_row["sha256"])
        for hook in self.config["parent_abi"]["hooks"]:
            offset = int(hook["address"], 0) - 0x08000000
            width = hook["width"]
            self.assertEqual(
                parent[offset:offset + width].hex(),
                hook["parent_hex"],
                hook["name"],
            )

    def test_existing_light_ball_owner_uses_pichu_24_item_202_move_344(self) -> None:
        parent_row = self.config["parent_identity"]["rom"]
        parent_path = ROOT / parent_row["path"]
        if not parent_path.is_file():
            self.skipTest("Stage72 parent ROM is unavailable")
        parent = parent_path.read_bytes()
        evidence = verify_existing_light_ball_owner(parent)
        self.assertEqual(evidence["canonical_species"], 24)
        self.assertEqual(evidence["light_ball_item"], 202)
        self.assertEqual(evidence["volt_tackle_move"], 344)
        # egg->species is loaded, saved at sp+24, and compared with canonical 24.
        self.assertEqual(parent[0x10EA946:0x10EA948].hex(), "048c")
        self.assertEqual(parent[0x10EA94E:0x10EA950].hex(), "0694")
        self.assertEqual(parent[0x10EAA74:0x10EAA7A].hex(), "069b182b46d0")
        # Both parent paths compare held item ID 202.
        self.assertEqual(parent[0x10EAB14:0x10EAB18].hex(), "ca2807d0")
        self.assertEqual(parent[0x10EAB24:0x10EAB28].hex(), "ca28a8d1")
        # Thumb movs #172 then lsl #1 constructs project Move ID 344.
        self.assertEqual(parent[0x10EAB28:0x10EAB30].hex(), "ac21124b05984900")
        self.assertEqual(172 << 1, 344)

    def test_exact_egg_replacement_and_capacity_are_lossless(self) -> None:
        parent_path = ROOT / self.config["parent_identity"]["rom"]["path"]
        if not parent_path.is_file():
            self.skipTest("Stage72 exact parent ROM is unavailable")
        parent = parent_path.read_bytes()
        exact = build_exact_egg_payload(parent, self.model, self.config)
        self.assertEqual(exact.audit["replaced_route_count"], 40)
        self.assertEqual(exact.audit["replaced_species"], sorted(EXACT_EGG_SPECIES))
        self.assertEqual(exact.audit["unaffected_records_preserved"], 1392)
        capacity = build_capacity_audit(parent, self.model, exact.rows)
        self.assertEqual(capacity["normal_relearner"]["max_union_count"], 28)
        self.assertEqual(capacity["normal_relearner"]["capacity_drop_count"], 0)
        self.assertEqual(capacity["mirror_herb_shared_egg"]["max_union_count"], 19)
        self.assertEqual(capacity["mirror_herb_shared_egg"]["capacity_drop_count"], 0)

    def test_rotom_never_silently_overwrites_a_full_moveset(self) -> None:
        self.assertEqual(
            plan_rotom_move_transition(742, 894, (1, 2, 3, 4)),
            ("EFFECTLESS_FULL", (1, 2, 3, 4)),
        )
        self.assertEqual(
            plan_rotom_move_transition(742, 895, (1, 0, 3, 4)),
            ("APPLY_FORM", (1, 56, 3, 4)),
        )
        self.assertEqual(
            plan_rotom_move_transition(742, 898, (1, 315, 3, 4)),
            ("APPLY_FORM", (1, 401, 3, 4)),
        )
        self.assertEqual(
            plan_rotom_move_transition(898, 898, (1, 401, 3, 4)),
            ("RETURN_BASE", (1, 3, 4, 0)),
        )

    def test_thumb_veneer_shapes_are_fixed(self) -> None:
        self.assertEqual(_veneer(8, 0x09501234).hex(), "004b184735125009")
        self.assertEqual(_veneer(12, 0x09501234).hex(), "9c46014b1847c04635125009")


if __name__ == "__main__":
    unittest.main()
