from __future__ import annotations

import json
import struct
import unittest
from pathlib import Path

from tools.interaction_ownership_repair import (
    GBA_ROM_BASE,
    WILD_HEADERS_POINTER_SITE,
    build_payload,
)
from tools.trainer_final.kanto_events import _object_fields, _stage_map_state


ROOT = Path(__file__).resolve().parents[1]


class InteractionOwnershipRepairTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.stage49 = (ROOT / "build/stages/49_world_item_recovery.gba").read_bytes()
        cls.stage48 = (ROOT / "build/stages/48_species_form_backsprite_compat.gba").read_bytes()
        cls.clean = (ROOT / "inputs/private/FireRed_JPN_Rev0_clean.gba").read_bytes()
        inventory = json.loads((ROOT / "reports/generated/id_inventory.json").read_text())
        cls.group_sizes = inventory["map_contract"]["group_sizes"]
        cls.payload, cls.plan, cls.pointer_patches, cls.sight_patches = build_payload(
            ROOT, cls.stage49, cls.stage48, cls.clean, 0, cls.group_sizes,
        )
        cls.output = (ROOT / "build/stages/50_interaction_ownership_repair.gba").read_bytes()

    def test_field_objects_have_distinct_owners(self) -> None:
        counts = self.plan["kanto"]["counts"]
        self.assertEqual(counts["restored_item_ball"] + counts["preserved_item_ball"], 129)
        self.assertEqual(counts["restored_cut_tree"] + counts.get("preserved_cut_tree", 0), 33)
        self.assertEqual(counts["restored_rock_smash"] + counts.get("preserved_rock_smash", 0), 40)
        self.assertEqual(counts["restored_hidden_item"], 124)
        self.assertNotIn("カントーへ", json.dumps(self.plan, ensure_ascii=False))

    def test_item_transaction_sets_flag_only_after_success(self) -> None:
        scripts = self.plan["scripts"]
        rows = [row for label, row in scripts.items()
                if (label.startswith("script_item::") or label.startswith("script_hidden::"))
                and "::" in label and not any(label.endswith(suffix)
                    for suffix in ("::already", "::full", "::end"))]
        self.assertEqual(len(rows), 250)
        for row in rows:
            operations = row["operations"]
            check = next(index for index, value in enumerate(operations)
                         if value.startswith("checkflag:"))
            add = next(index for index, value in enumerate(operations)
                       if value.startswith("additem:"))
            flag = next(index for index, value in enumerate(operations)
                        if value.startswith("setflag:"))
            self.assertLess(check, add)
            self.assertLess(add, flag)

    def test_all_interactable_zero_scripts_repaired(self) -> None:
        self.assertEqual(self.plan["tohoku"]["repaired_count"], 86)
        self.assertEqual(self.plan["tohoku"]["hisui"]["local_id"], 4)
        for group, size in enumerate(self.group_sizes):
            for number in range(size):
                try:
                    state = _stage_map_state(self.output, group, number)
                except (ValueError, RuntimeError):
                    continue
                for raw in state["objects"]:
                    fields = _object_fields(raw)
                    if fields["script_pointer"] == 0:
                        self.assertTrue(fields["kind"] != 0 or fields["graphics_id"] == 108)

    def test_codex_reception_is_preserved(self) -> None:
        state = _stage_map_state(self.output, 96, 5)
        rows = [_object_fields(raw) for raw in state["objects"]
                if _object_fields(raw)["local_id"] == 2]
        self.assertEqual(len(rows), 1)
        self.assertEqual((rows[0]["x"], rows[0]["y"]), (20, 19))
        self.assertEqual(rows[0]["script_pointer"], 0x093CDA80)

    def test_encounter_runtime_and_511_land_owner(self) -> None:
        self.assertEqual(self.output[0x82F76:0x82F78], bytes.fromhex("09e0"))
        hook_target = struct.unpack_from("<I", self.output, 0x6CFEC)[0]
        self.assertEqual(hook_target & 1, 1)
        wrapper = (hook_target & ~1) - GBA_ROM_BASE
        self.assertEqual(
            self.output[wrapper:wrapper + 20],
            bytes.fromhex("10b504498978022902d1034b984710bd002010bd"),
        )
        root = struct.unpack_from("<I", self.output, WILD_HEADERS_POINTER_SITE)[0]
        root -= GBA_ROM_BASE
        target = [root + index * 20 for index in range(265)
                  if self.output[root + index * 20:root + index * 20 + 2] == bytes((3, 29))]
        self.assertEqual(len(target), 1)
        land = struct.unpack_from("<I", self.output, target[0] + 4)[0]
        self.assertNotEqual(land, 0)

    def test_flinch_and_focus_sash_regressions(self) -> None:
        dark_pulse = 0x10421F4 + 369 * 12
        self.assertEqual(self.output[dark_pulse], 31)
        self.assertEqual(self.output[dark_pulse + 5], 20)
        self.assertEqual(self.output[0x112B910:0x112B914], bytes.fromhex("5145d3d2"))
        sash = 0x104D108 + 897 * 40
        self.assertEqual(struct.unpack_from("<H", self.output, sash + 10)[0], 897)
        self.assertEqual(tuple(self.output[sash + offset] for offset in (14, 15, 21, 36)),
                         (39, 100, 1, 0))


if __name__ == "__main__":
    unittest.main()
