from __future__ import annotations

import copy
import struct
import unittest
from pathlib import Path

from scripts.build_stage61_display_npc_event_audit import (
    STAGE61_KANTO_LEAGUE_SCENE_VAR,
    STAGE61_LEAGUE_BATTLE_COMPLETION_BINDINGS,
    _Blob,
    _league_completion_runtime_repair_row,
    _materialize_project_league_map_scripts,
)
from tools.stage61_map_script_projection import (
    build_projection_plan,
    load_canonical_maps,
)


ROOT = Path(__file__).resolve().parents[1]


class Stage61LeagueMaterializationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.clean = (ROOT / "inputs/private/FireRed_JPN_Rev0_clean.gba").read_bytes()
        cls.stage60 = (ROOT / "build/stages/60_wild_species_root_repair.gba").read_bytes()
        canonical = load_canonical_maps(
            ROOT / "generated/maps/kanto",
            ROOT / "vendor/upstream/pokefirered/data/maps/map_groups.json",
        )
        cls.plan = build_projection_plan(
            cls.clean, cls.stage60, canonical, require_ready=True
        )

    def _materialize(self, contract=None, stage60=None):
        blob = _Blob()
        blob.add("prefix", b"stage61", 1)
        return _materialize_project_league_map_scripts(
            blob,
            self.clean,
            self.stage60 if stage60 is None else stage60,
            contract or self.plan["league_explicit_adapter_contract"],
            0x09E00000,
        )

    def test_completion_open_is_the_final_on_load_decision_for_every_scene(self) -> None:
        result = self._materialize()
        self.assertEqual(result["status"], "PASS")
        self.assertTrue(all(result["assertions"].values()))
        self.assertEqual(len(result["maps"]), 5)
        self.assertGreater(result["payload_size"], 0)
        self.assertEqual(len(result["payload_sha256"]), 64)

        for room in result["maps"][:4]:
            self.assertEqual(
                room["on_load_resolution_order"],
                ["SCENE_AFTER_CLOSE", "COMPLETION_OPEN_FINAL_PRIORITY"],
            )
            matrix = room["on_load_state_matrix"]
            self.assertEqual(len(matrix), 12)
            self.assertTrue(all(
                row["result"] == "OPEN" for row in matrix if row["completion"]
            ))
            scene_after = room["project_scene_transition"][1]
            unfinished = {
                row["scene"]: row["result"]
                for row in matrix if not row["completion"]
            }
            self.assertEqual(unfinished[scene_after], "CLOSED")
            self.assertTrue(all(
                result == "UNCHANGED"
                for scene, result in unfinished.items() if scene != scene_after
            ))

            raw = bytes.fromhex(room["on_load_raw_hex"])
            self.assertEqual(
                raw[:5],
                struct.pack(
                    "<BHH", 0x21, STAGE61_KANTO_LEAGUE_SCENE_VAR, scene_after
                ),
            )
            # call_if close precedes checkflag/call_if open, so completion wins.
            self.assertEqual(raw[5:7], b"\x07\x01")
            self.assertEqual(raw[11], 0x2B)
            self.assertEqual(raw[14:16], b"\x07\x01")
            self.assertEqual(raw[-1], 0x02)

    def test_scene_lifecycle_is_persistent_high_water_not_an_implicit_reset(self) -> None:
        result = self._materialize()
        lifecycle = result["scene_lifecycle"]
        self.assertEqual(lifecycle["initial_value"], 0)
        self.assertEqual(lifecycle["reset_writer"], "NONE_BY_DESIGN")
        self.assertEqual(
            lifecycle["mid_room_save_reload"],
            "PRESERVE_TO_AVOID_REPLAYING_ENTRY_MOVEMENT",
        )
        self.assertEqual(
            [row["project_scene_transition"] for row in result["maps"]],
            [[0, 1], [1, 2], [2, 3], [3, 4], [4, 5]],
        )

    def test_battle_completion_sets_flag_then_opens_and_redraws_same_room(self) -> None:
        result = self._materialize()
        patches = result["completion_patches"]
        self.assertEqual(len(patches), 4)
        self.assertEqual(
            {(row["group"], row["map"]) for row in patches},
            {(97, number) for number in range(75, 79)},
        )
        patch_by_map = {row["physical_map"]: row for row in patches}
        for room in result["maps"][:4]:
            patch = patch_by_map[room["physical_map"]]
            raw = bytes.fromhex(room["battle_completion_adapter_raw_hex"])
            completion_flag = int(room["completion_flag"], 0)
            self.assertEqual(raw[:3], b"\x29" + struct.pack("<H", completion_flag))
            self.assertEqual(raw[3], 0x04)
            self.assertEqual(
                struct.unpack_from("<I", raw, 4)[0],
                int(patch["open_draw_pointer"], 0),
            )
            self.assertEqual(raw[-1], 0x02)
            self.assertEqual(
                room["post_battle_resolution_order"],
                [
                    "SET_COMPLETION_FLAG",
                    "OPEN_EXIT_GEOMETRY_AND_DRAW_CURRENT_MAP",
                    "END",
                ],
            )
            source = room["battle_completion_source"]
            pointer_site = int(source["proxy_goto_pointer_site"], 0)
            binding = STAGE61_LEAGUE_BATTLE_COMPLETION_BINDINGS[
                (room["group"], room["map"])
            ]
            self.assertEqual(pointer_site, binding["proxy_goto_pointer_site"])
            self.assertEqual(
                self.stage60[pointer_site - 0x08000001:pointer_site - 0x08000000 + 4],
                b"\x05" + struct.pack("<I", binding["completion_root"]),
            )

        champion = result["maps"][-1]
        self.assertEqual(champion["physical_map"], "097/079")
        self.assertFalse(
            result["champion_completion_negative_control"]["geometry_redraw"]
        )
        self.assertNotIn("battle_completion_adapter_pointer", champion)
        self.assertTrue(all(row["map"] != 79 for row in patches))

    def test_completion_proxy_opcode_or_unique_reference_drift_fails_closed(self) -> None:
        opcode_drift = bytearray(self.stage60)
        site = STAGE61_LEAGUE_BATTLE_COMPLETION_BINDINGS[(97, 75)][
            "proxy_goto_pointer_site"
        ]
        opcode_drift[site - 0x08000001] = 0x04
        with self.assertRaisesRegex(RuntimeError, "proxy post-battle goto drift"):
            self._materialize(stage60=bytes(opcode_drift))

        duplicate = bytearray(self.stage60)
        root = STAGE61_LEAGUE_BATTLE_COMPLETION_BINDINGS[(97, 75)][
            "completion_root"
        ]
        duplicate[-4:] = struct.pack("<I", root)
        with self.assertRaisesRegex(RuntimeError, "reference非一意"):
            self._materialize(stage60=bytes(duplicate))

    def test_completion_operand_repairs_bind_enclosing_instruction_provenance(
        self,
    ) -> None:
        result = self._materialize()
        repairs = [
            _league_completion_runtime_repair_row(patch)
            for patch in result["completion_patches"]
        ]
        self.assertEqual(len(repairs), 4)
        self.assertEqual(
            {row["physical_map"] for row in repairs},
            {f"097/{number:03d}" for number in range(75, 79)},
        )
        for patch, repair in zip(
            result["completion_patches"], repairs, strict=True,
        ):
            pointer_site = 0x08000000 + int(patch["offset"])
            instruction = int(repair["instruction_address"])
            self.assertEqual(repair["address"], pointer_site)
            self.assertEqual(instruction, pointer_site - 1)
            self.assertLess(repair["address"], instruction + 5)
            self.assertLess(instruction, repair["address"] + 4)
            self.assertEqual(
                bytes.fromhex(repair["expected_hex"]), patch["expected"],
            )
            self.assertEqual(
                bytes.fromhex(repair["replacement_hex"]),
                patch["replacement"],
            )

        broken = copy.deepcopy(result["completion_patches"][0])
        broken["proxy_goto_opcode_address"] = (
            f"0x{int(broken['proxy_goto_opcode_address'], 0) + 1:08X}"
        )
        with self.assertRaisesRegex(RuntimeError, "preimage/interval"):
            _league_completion_runtime_repair_row(broken)

    def test_movement_or_lifecycle_drift_fails_closed(self) -> None:
        contract = copy.deepcopy(self.plan["league_explicit_adapter_contract"])
        contract["elite_rooms"][0]["entry_movement_payloads"][0]["raw_hex"] = "11fe"
        with self.assertRaisesRegex(RuntimeError, "movement provenance"):
            self._materialize(contract)

        contract = copy.deepcopy(self.plan["league_explicit_adapter_contract"])
        contract["policy"]["scene_lifecycle"]["reset_writer"] = "UNREVIEWED_RESET"
        with self.assertRaisesRegex(RuntimeError, "scene lifecycle"):
            self._materialize(contract)


if __name__ == "__main__":
    unittest.main()
