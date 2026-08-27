from __future__ import annotations

import hashlib
import struct
import unittest

from scripts.build_stage57_comprehensive_debug_repair import _build_payload
from scripts.run_stage57_mgba_validation import _expand_profiles, _without_timing
from tools.stage57_debug_suite import (
    CONTROL_FLOW_REPAIRS,
    FACTORY_CURSOR_CALLSITE,
    MENU_CALLSITES,
    MENU_TILE_BASE,
    NPC_POINTER_REPAIRS,
    ROUTE_505_FORBIDDEN_SPECIES,
    ROUTE_505_RESEARCH_SPECIES,
    SPECIES_SET_CALLSITES,
    STORY_TRAINER_REPAIRS,
    STORY_TRAINER_SHARED_CLONE,
    STORY_TRAINER_SHARED_TARGET,
    canonical_qol_tables,
)


class Stage57DebugRepairTest(unittest.TestCase):
    def test_current_qol_binding_tables_are_exact(self) -> None:
        research, field_pc = canonical_qol_tables()
        self.assertEqual(len(research), 846 * 12)
        self.assertEqual(len(field_pc), 69 * 2)
        self.assertEqual(
            hashlib.sha256(research).hexdigest(),
            "4d3c49b581a5c4e38cce696dbf7a8197c597163186bfed58e82655bb62f06b8d",
        )
        self.assertEqual(
            hashlib.sha256(field_pc).hexdigest(),
            "e210ec1105a4f56b99a3952ca5b0599089aca1051bdd6ca67f0eb8f801c66782",
        )

    def test_route505_has_no_reported_cross_map_species(self) -> None:
        self.assertFalse(
            set(ROUTE_505_RESEARCH_SPECIES) & ROUTE_505_FORBIDDEN_SPECIES
        )
        self.assertEqual(len(ROUTE_505_RESEARCH_SPECIES), 12)

    def test_all_runtime_patch_sites_are_unique(self) -> None:
        addresses = [row[1] for row in MENU_CALLSITES]
        addresses += [row[1] for row in SPECIES_SET_CALLSITES]
        addresses += [row[1] for row in NPC_POINTER_REPAIRS]
        addresses += [row[1] for row in CONTROL_FLOW_REPAIRS]
        addresses.append(FACTORY_CURSOR_CALLSITE[1])
        self.assertEqual(len(addresses), len(set(addresses)))

    def test_payload_bg_fallback_is_bg_safe_and_finite(self) -> None:
        payload, script = _build_payload(b"\x00\x00\x00\x00", 0x100000)
        script_offset = script - 0x08000000 - 0x100000
        self.assertEqual(
            payload[script_offset:script_offset + 11],
            bytes((0x69, 0x0F, 0x00))
            + struct.pack("<I", 0x093DCE28)
            + bytes((0x09, 0x03, 0x6B, 0x02)),
        )

    def test_menu_content_base_does_not_alias_standard_frame(self) -> None:
        self.assertEqual(MENU_TILE_BASE, 0x38)
        self.assertFalse(0x200 <= MENU_TILE_BASE <= 0x21C)

    def test_story_trainer_repairs_are_unique_and_split_shared_target(self) -> None:
        self.assertEqual(len(STORY_TRAINER_REPAIRS), 26)
        self.assertEqual(
            len({row[0] for row in STORY_TRAINER_REPAIRS}),
            len(STORY_TRAINER_REPAIRS),
        )
        self.assertEqual(
            len({row[1] for row in STORY_TRAINER_REPAIRS}),
            len(STORY_TRAINER_REPAIRS),
        )
        self.assertIn(
            STORY_TRAINER_SHARED_TARGET,
            {row[1] for row in STORY_TRAINER_REPAIRS},
        )
        self.assertNotIn(
            STORY_TRAINER_SHARED_CLONE,
            {row[1] for row in STORY_TRAINER_REPAIRS},
        )

    def test_mgba_profiles_have_fast_and_full_domain_sets(self) -> None:
        quick, quick_name = _expand_profiles(["quick"])
        all_domains, all_name = _expand_profiles(["all"])
        self.assertEqual((quick, quick_name), ({"static", "story"}, "quick"))
        self.assertEqual(all_name, "all")
        self.assertEqual(
            all_domains,
            {"static", "story", "menu", "route505", "species",
             "collection", "world"},
        )
        self.assertEqual(
            _without_timing({"elapsed_seconds": 1, "nested": [
                {"elapsed_seconds": 2, "value": 3},
            ]}),
            {"nested": [{"value": 3}]},
        )


if __name__ == "__main__":
    unittest.main()
