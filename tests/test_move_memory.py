"""無料の共通技管理を結合したstage 25の限定回帰。"""

from __future__ import annotations

import csv
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_move_memory import (  # noqa: E402
    ECOLOGY_RADAR_ITEM_ID,
    ITEM_ID,
    MAX_CANDIDATES,
    MODE_RAM,
    STAGE25,
    STAGE25_META,
    _build_stage,
)


class MoveMemoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.metadata = json.loads(
            (ROOT / STAGE25_META).read_text(encoding="utf-8")
        )
        cls.fixture = json.loads(
            (ROOT / "build/stages/25_mgba_move_memory.json").read_text(
                encoding="utf-8"
            )
        )

    def test_stage_build_is_deterministic_and_declared_only(self) -> None:
        first, first_meta = _build_stage(ROOT)
        second, second_meta = _build_stage(ROOT)
        self.assertEqual(first, second)
        self.assertEqual(first_meta, second_meta)
        self.assertEqual(first[STAGE25.as_posix()], (ROOT / STAGE25).read_bytes())
        self.assertEqual(first_meta["status"], "PASS")
        self.assertEqual(len(first_meta["patches"]), 6)
        self.assertTrue(all(first_meta["invariants"].values()))
        self.assertEqual(first_meta["allocation"]["overlap_count"], 0)
        self.assertTrue(first_meta["release_patch_round_trip"]["exact"])

    def test_item_npcs_and_badge_share_the_free_core(self) -> None:
        metadata = self.metadata
        self.assertEqual(metadata["item"]["id"], ITEM_ID)
        self.assertEqual(metadata["item"]["name"], "わざメモリー")
        self.assertEqual(metadata["item"]["pocket"], "KEY_ITEMS")
        scripts = metadata["runtime"]["payload"]["script_contract"]["scripts"]
        operations = [
            operation
            for script in scripts.values()
            for operation in script["operations"]
        ]
        self.assertFalse(any(value.startswith("removeitem:") for value in operations))
        self.assertIn("additem:347:1", scripts["script_badge1_reward"]["operations"])
        self.assertIn(
            f"additem:{ECOLOGY_RADAR_ITEM_ID}:1",
            scripts["script_badge1_reward"]["operations"],
        )
        self.assertEqual(
            metadata["companion_item"],
            {
                "id": ECOLOGY_RADAR_ITEM_ID,
                "name": "せいたいレーダー",
                "grant": "badge1_reward_and_shiou_recovery",
                "runtime_owner": "T17_TOHOKU_ECOLOGY",
            },
        )
        self.assertIn(
            "goto:script_shiou_ecology_check",
            scripts["script_shiou_grant"]["operations"],
        )
        self.assertIn(
            "goto:script_shiou_context",
            scripts["script_shiou_ecology_grant"]["operations"],
        )
        self.assertIn(
            "branch:1:script_remember_entry",
            scripts["script_shiou_context"]["operations"],
        )
        self.assertIn(
            "branch:1:script_forget_entry",
            scripts["script_karasuba_npc"]["operations"],
        )
        self.assertEqual(
            scripts["script_finish"]["operations"],
            ["callnative:VegaMoveMemory_ResetMode", "release_end"],
        )
        self.assertTrue(metadata["acceptance"]["item_and_npcs_share_core"])
        self.assertTrue(metadata["acceptance"]["no_mushroom_or_item_consumption"])

    def test_normal_and_egg_candidate_boundaries_pass_on_exact_rom(self) -> None:
        fixture = self.fixture
        self.assertEqual(fixture["status"], "PASS")
        self.assertEqual(fixture["process_runs"], 2)
        self.assertEqual(fixture["warnings_errors"], 0)
        self.assertTrue(fixture["normal"]["level_zero_one_included"])
        self.assertTrue(fixture["normal"]["future_level_rejected"])
        self.assertTrue(fixture["normal"]["known_and_duplicate_filtered"])
        self.assertEqual(fixture["normal"]["candidate_cap"], MAX_CANDIDATES)
        self.assertTrue(fixture["egg"]["direct_owner_match"])
        self.assertTrue(fixture["egg"]["mode_reset"])
        self.assertEqual(fixture["egg"]["policy_matrix_cases"], 5)

    def test_forget_uses_cfru_slot_path_and_preserves_form_rules(self) -> None:
        forget = self.fixture["forget"]
        self.assertTrue(forget["last_move_script_guard"])
        self.assertTrue(forget["pp_up_warning_script_guard"])
        self.assertTrue(forget["hm_allowed"])
        self.assertTrue(forget["form_only_rejected"])
        self.assertTrue(forget["secret_sword_form_link_allowed"])
        self.assertTrue(forget["set_mon_move_slot_native_path"])
        source = (ROOT / "overlays/move_memory/move_memory.c").read_text(
            encoding="utf-8"
        )
        self.assertIn("FN_SET_MON_MOVE_SLOT(mon, MOVE_NONE", source)
        self.assertIn("FN_REMOVE_MON_PP_BONUS(mon", source)
        self.assertIn("FN_SHIFT_MOVE_SLOT(mon", source)
        self.assertNotIn("mon->moves", source)
        operations = self.metadata["runtime"]["payload"]["script_contract"][
            "scripts"
        ]["script_forget_delete"]["operations"]
        self.assertIn("callnative:VegaMoveMemory_DeleteSelectedMove", operations)
        self.assertNotIn("special:0x0DD", operations)

    def test_manifest_ids_and_volatile_ram_are_pinned(self) -> None:
        with (ROOT / "manifests/move_ids.csv").open(
            encoding="utf-8-sig", newline=""
        ) as stream:
            rows = {row["cfru_symbol"]: int(row["id"]) for row in csv.DictReader(stream)}
        expected = {
            "MOVE_SECRETSWORD": 619,
            "MOVE_BEHEMOTHBLADE": 768,
            "MOVE_BEHEMOTHBASH": 769,
        }
        self.assertEqual({name: rows[name] for name in expected}, expected)
        self.assertEqual(self.metadata["source_audit"]["manifest_move_ids"], expected)
        ram = self.metadata["ram_audit"]
        self.assertEqual(ram["address"], MODE_RAM)
        self.assertEqual(ram["persistence"], "VOLATILE")
        self.assertFalse(ram["flash_serialized"])

    def test_context_physical_patches_and_runner_are_clean(self) -> None:
        self.assertTrue(self.fixture["context"]["matrix_pass"])
        self.assertTrue(self.fixture["physical_patches"]["all_match"])
        self.assertTrue(all(self.metadata["acceptance"].values()))
        runner = (ROOT / "tools/mgba_move_memory_smoke.c").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("fopen(", runner)
        self.assertIn("MM_SPECIES_KELDEO_RESOLUTE", runner)
        self.assertIn("set_mon_move_slot_native_path", runner)


if __name__ == "__main__":
    unittest.main()
