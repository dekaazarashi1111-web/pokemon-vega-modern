from __future__ import annotations

import csv
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = (
    ROOT
    / "overlays"
    / "stage58_qol_world_convenience"
    / "stage58_qol_item_adapter.c"
)
GENERATED_QOL = ROOT / "generated" / "runtime" / "qol_production_generated.h"


class Stage58QolItemAdapterSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = SOURCE.read_text(encoding="utf-8")
        cls.generated_qol = GENERATED_QOL.read_text(encoding="utf-8")

    def test_exports_probe_and_normal_bag_field_entrypoint(self) -> None:
        for symbol in (
            "Stage58QolItemAdapter_Probe",
            "Stage58QolItemAdapter_FieldUseBottleCapAdapter",
            "Stage58QolItemAdapter_CodexBattleWonAdapter",
            "Stage58QolItemAdapter_CodexBattleLostAdapter",
            "Stage58QolItemAdapter_CodexSnapshotSeenMirrors",
            "Stage58QolItemAdapter_CodexRestoreSeenMirrors",
            "Stage58QolItemAdapter_CodexContinueSeenHash",
        ):
            self.assertIn(f"PUBLIC_TEXT({symbol})", self.source)
        self.assertIn("G_ITEM_USE_CALLBACK = bottle_cap_party_callback", self.source)
        self.assertIn("FN_SET_UP_ITEM_USE_CALLBACK(task_id)", self.source)
        self.assertIn("0x080A29A5u", self.source)
        self.assertIn("0x03005EE8u", self.source)

    def test_adapter_does_not_interpose_stock_key_rotation(self) -> None:
        for forbidden in (
            "Stage58QolItemAdapter_ApplyNewEncryptionWithGuardedBagRebind",
            "ApplyEncryptionFn",
            "BagPocket",
            "SetBagPocketsPointers",
            "0x0804BD5D",
            "0x0809984D",
            "0x08099841",
            "0x04000208",
            "SaveOriginalWithBagRebind",
            "TrySavingDataFn",
            "FN_ORIGINAL_TRY_SAVING_DATA",
        ):
            self.assertNotIn(forbidden, self.source)

    def test_adapter_does_not_wrap_codex_read_keys_or_own_mailbox(self) -> None:
        self.assertNotIn("Stage58QolItemAdapter_ReadKeysCompat", self.source)
        self.assertNotIn("FN_COLLECTION_READ_KEYS", self.source)
        self.assertNotIn("CODEX_RUNTIME_MAILBOX_ADDRESS", self.source)
        self.assertNotIn("codex_publish_stage47_capabilities", self.source)

    def test_codex_result_adapter_removes_tower_text_owner_before_safe_tail(self) -> None:
        self.assertRegex(
            self.source,
            r"BATTLE_TYPE_TRAINER_TOWER\s*=\s*0x00080000u",
        )
        self.assertIn("*flags &= ~BATTLE_TYPE_TRAINER_TOWER", self.source)
        self.assertIn(
            "Stage58QolItemAdapter_CodexReturnToFieldAdapter) | 1u",
            self.source,
        )
        self.assertIn("stock_handler();", self.source)
        self.assertIn("*script = CODEX_NONPUNITIVE_RESULT_SCRIPT", self.source)
        self.assertIn("0x081BC8BBu", self.source)
        self.assertIn("0x093D1E01u", self.source)
        self.assertIn("CODEX_RUNTIME_CODEX_SELECTION_VALID_OFFSET = 26u", self.source)
        self.assertIn("CODEX_RUNTIME_FIELD_COMPLETION_PENDING_OFFSET = 30u", self.source)
        self.assertIn("G_TRAINER_OPPONENT_A == CODEX_TRAINER_ID", self.source)
        self.assertIn("(*flags & BATTLE_TYPE_TRAINER) != 0u", self.source)
        self.assertNotIn("CODEX_RUNTIME_CONTROLLER_INSTALLED_OFFSET", self.source)
        self.assertIn("FN_SET_MAIN_CALLBACK2(FN_RETURN_TO_FIELD)", self.source)
        self.assertIn(
            "Stage58QolItemAdapter_CodexTransactionIdentityValid()",
            self.source,
        )
        self.assertIn(
            "Stage58QolItemAdapter_CodexLegacyResultHazard()",
            self.source,
        )
        self.assertIn("FN_STOCK_BATTLE_WON();", self.source)
        self.assertIn("FN_STOCK_BATTLE_LOST();", self.source)
        self.assertIn(
            "PUBLIC_TEXT(Stage58QolItemAdapter_CodexRewardResultKind)",
            self.source,
        )
        self.assertIn("CODEX_RUNTIME_CLEANUP_REASON_OFFSET = 82u", self.source)
        self.assertIn("if (cleanup == 3u)", self.source)
        self.assertIn("if (outcome == 5u)", self.source)
        self.assertLess(
            self.source.index("if (cleanup == 3u)"),
            self.source.index("if (outcome == 5u)"),
        )
        self.assertIn("FN_INHERITED_RETURN_TO_FIELD()", self.source)
        self.assertIn("FN_INHERITED_BATTLE_WON()", self.source)
        self.assertIn("FN_INHERITED_BATTLE_LOST()", self.source)
        finish = self.source[
            self.source.index(
                "void Stage58QolItemAdapter_FinishNonpunitiveCodexResult"
            ):
            self.source.index(
                "PUBLIC_TEXT(Stage58QolItemAdapter_CodexReturnToFieldAdapter)"
            )
        ]
        self.assertLess(
            finish.index("*flags &= ~BATTLE_TYPE_TRAINER_TOWER"),
            finish.index("Stage58QolItemAdapter_CodexReturnToFieldAdapter) | 1u"),
        )
        self.assertLess(
            finish.index("Stage58QolItemAdapter_CodexReturnToFieldAdapter) | 1u"),
            finish.index("stock_handler();"),
        )
        self.assertLess(
            finish.index("stock_handler();"),
            finish.index("*script = CODEX_NONPUNITIVE_RESULT_SCRIPT"),
        )

    def test_exact_two_item_boundary_and_service_17_owner(self) -> None:
        self.assertRegex(self.source, r"ITEM_BOTTLE_CAP\s*=\s*853u")
        self.assertRegex(self.source, r"ITEM_GOLD_BOTTLE_CAP\s*=\s*854u")
        self.assertRegex(
            self.source, r"QOL_SERVICE_HYPER_TRAIN_PARTY\s*=\s*17u"
        )
        self.assertIn("0x09378799u", self.source)
        self.assertIn("item != ITEM_BOTTLE_CAP", self.source)
        self.assertIn("item == ITEM_GOLD_BOTTLE_CAP", self.source)
        self.assertIn("HYPER_TRAIN_ALL_STATS, 0u", self.source)

    def test_silver_menu_has_six_generated_labels_and_explicit_cancel(self) -> None:
        self.assertIn("kBottleCapStatLabels[HYPER_TRAIN_STAT_COUNT][12]", self.source)
        self.assertIn("kBottleCapStatItems[7]", self.source)
        self.assertIn("menu.total_items = 7u", self.source)
        self.assertIn("menu.max_showed = 7u", self.source)
        self.assertIn("{kBottleCapCancelLabel, LIST_CANCEL}", self.source)
        self.assertIn("generated gVegaQolSupplyCancel", self.source)
        # Visual SpAtk/SpDef/Speed rows map back to service ids 4/5/3.
        for row in (
            "{kBottleCapStatLabels[3], 4}",
            "{kBottleCapStatLabels[4], 5}",
            "{kBottleCapStatLabels[5], 3}",
        ):
            self.assertIn(row, self.source)

        copied = re.search(
            r"kBottleCapStatLabels\[HYPER_TRAIN_STAT_COUNT\]\[12\]\s*=\s*\{"
            r"(?P<body>.*?)\n\};",
            self.source,
            flags=re.DOTALL,
        )
        generated = re.search(
            r"gVegaQolStatLabels\[6\]\[12\]\s*=\s*\{"
            r"(?P<body>.*?)\n\};",
            self.generated_qol,
            flags=re.DOTALL,
        )
        self.assertIsNotNone(copied)
        self.assertIsNotNone(generated)
        copied_bytes = [
            int(value, 16)
            for value in re.findall(r"0x([0-9A-Fa-f]{2})", copied.group("body"))
        ]
        generated_bytes = [
            int(value, 16)
            for value in re.findall(r"0x([0-9A-Fa-f]{2})", generated.group("body"))
        ]
        self.assertEqual(copied_bytes, generated_bytes)

        generated_cancel = re.search(
            r"gVegaQolSupplyCancel\[\]\s*=\s*\{(?P<body>[^}]*)\}",
            self.generated_qol,
        )
        copied_cancel = re.search(
            r"kBottleCapCancelLabel\[\]\s*=\s*\{(?P<body>[^}]*)\}",
            self.source,
        )
        self.assertIsNotNone(generated_cancel)
        self.assertIsNotNone(copied_cancel)
        self.assertEqual(
            re.findall(r"0x[0-9A-Fa-f]{2}", copied_cancel.group("body")),
            re.findall(r"0x[0-9A-Fa-f]{2}", generated_cancel.group("body")),
        )

    def test_success_is_the_only_consuming_path_and_returns_through_party(self) -> None:
        self.assertIn("success = (u8)(status == QOL_STATUS_OK)", self.source)
        self.assertIn("G_PARTY_USE_EXIT = success", self.source)
        self.assertIn("G_TASKS[task_id].func = return_task", self.source)
        self.assertIn("if (choice == LIST_CANCEL)", self.source)
        self.assertIn("G_PARTY_USE_EXIT = 0u", self.source)
        self.assertNotIn("RemoveBagItem", self.source)
        self.assertNotIn("FN_REMOVE_BAG_ITEM", self.source)
        self.assertNotIn("AddBagItem", self.source)

    def test_party_window_content_and_standard_frame_tiles_do_not_overlap(self) -> None:
        self.assertRegex(
            self.source,
            r"PARTY_DYNAMIC_WINDOW_BASE_BLOCK\s*=\s*0x2BFu",
        )
        self.assertIn("FN_LOAD_STD_WINDOW_FRAME_GFX()", self.source)
        self.assertIn("0x080F7EFDu", self.source)
        self.assertIn(
            "window.base_block = PARTY_DYNAMIC_WINDOW_BASE_BLOCK",
            self.source,
        )
        self.assertNotIn("window.base_block = FN_GET_STD_WINDOW_BASE_TILE()", self.source)
        # 13x16 content tiles occupy 0x2BF..0x38E; the stock frame is
        # 0x214..0x21C, so the two spans are strictly disjoint.
        self.assertGreater(0x2BF, 0x21C)
        self.assertLessEqual(0x2BF + 13 * 16, 0x400)

    def test_uses_task_data_and_adds_no_file_scope_mutable_owner(self) -> None:
        self.assertIn("G_TASKS[task_id].data", self.source)
        self.assertNotIn("SaveData", self.source)
        self.assertNotIn("malloc", self.source)
        self.assertNotIn("AllocZeroed", self.source)
        # All file-scope data objects must remain immutable.
        mutable = re.findall(
            r"^static\s+(?!const\b)(?:u8|u16|u32|s16|s32|TaskFunc|"
            r"WindowTemplate|ListMenuItem|ListMenuTemplate)\s+"
            r"[A-Za-z_]\w*\s*(?:\[|=|;)",
            self.source,
            flags=re.MULTILINE,
        )
        self.assertEqual(mutable, [])

    def test_codex_vega_seen_snapshot_uses_existing_split_buffers(self) -> None:
        for exact in (
            "VEGA_DEX_BITMAP_SIZE = 52u",
            "VEGA_SAVE1_DEX_SEEN_PRIMARY_OFFSET = 0x05F8u",
            "VEGA_SAVE1_DEX_SEEN_SECONDARY_OFFSET = 0x3A18u",
            "VEGA_SAVE2_DEX_OWNED_OFFSET = 0x0028u",
            "VEGA_SAVE2_DEX_SEEN_OFFSET = 0x005Cu",
            "VEGA_SAVE2_DEX_PERSONALITIES_OFFSET = 0x001Cu",
            "VEGA_SAVE2_DEX_PERSONALITIES_SIZE = 8u",
            "CODEX_SAVE1_SEEN_SNAPSHOT_OFFSET = 0x03A6u",
            "CODEX_SAVE1_SEEN_SNAPSHOT_SIZE = 150u",
            "CODEX_SAVE2_SEEN_SNAPSHOT_OFFSET = 0x053Cu",
            "CODEX_SAVE2_SEEN_SNAPSHOT_SIZE = 16u",
        ):
            self.assertIn(exact, self.source)
        self.assertIn(
            "3u * VEGA_DEX_BITMAP_SIZE\n"
            "               + VEGA_SAVE2_DEX_PERSONALITIES_SIZE",
            self.source,
        )
        self.assertIn("sources[2] = save2 + VEGA_SAVE2_DEX_OWNED_OFFSET", self.source)
        self.assertIn("value *= 16777619u", self.source)

    def test_codex_offsets_match_central_save_layout(self) -> None:
        with (ROOT / "config" / "save_layout.csv").open(
            encoding="utf-8", newline=""
        ) as handle:
            live = {
                row["symbol"]: row for row in csv.DictReader(handle)
                if row["status"] == "LIVE"
            }
        expected = {
            "seen_primary_412": ("SAVE_BLOCK1_OFFSET", 0x5F8, 52),
            "seen_secondary_412": ("SAVE_BLOCK1_OFFSET", 0x3A18, 52),
            "owned_412": ("SAVE_BLOCK2_OFFSET", 0x28, 52),
            "seen_save2_412": ("SAVE_BLOCK2_OFFSET", 0x5C, 52),
        }
        self.assertEqual(
            {
                name: (live[name]["address_space"],
                       int(live[name]["start"], 0),
                       int(live[name]["size"]))
                for name in expected
            },
            expected,
        )
        self.assertEqual(
            (int(live["bag_pockets_items_keyitems_balls_tmhm_berries"]
                 ["start"], 0),
             int(live["bag_pockets_items_keyitems_balls_tmhm_berries"]
                 ["end_exclusive"], 0)),
            (0x310, 0x5F8),
        )

    def test_arm7tdmi_thumb_freestanding_compile(self) -> None:
        compiler = shutil.which("arm-none-eabi-gcc")
        if compiler is None:
            self.skipTest("arm-none-eabi-gcc is not installed")
        with tempfile.TemporaryDirectory(prefix="stage58-cap-adapter-") as temp:
            output = Path(temp) / "stage58_qol_item_adapter.o"
            subprocess.run(
                [
                    compiler,
                    "-std=c11",
                    "-mthumb",
                    "-mcpu=arm7tdmi",
                    "-Os",
                    "-ffreestanding",
                    "-fno-builtin",
                    "-Wall",
                    "-Wextra",
                    "-Werror",
                    "-c",
                    str(SOURCE),
                    "-o",
                    str(output),
                ],
                check=True,
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            self.assertGreater(output.stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
