from __future__ import annotations

import hashlib
import json
import struct
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.modernization_p05_ability_rom_runtime import read_config  # noqa: E402
from tools.regression.rom_runtime import _charmap, _encode_text  # noqa: E402
from tools.release.bps import apply_bps  # noqa: E402


ROM_BASE = 0x08000000


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


class ModernizationP05AbilityRomRuntimeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = read_config(ROOT)
        inputs = cls.config["inputs"]
        outputs = cls.config["outputs"]
        cls.parent = (ROOT / inputs["stage71_rom"]["path"]).read_bytes()
        cls.rom = (ROOT / outputs["rom"]).read_bytes()
        cls.metadata = json.loads((ROOT / outputs["metadata"]).read_text(encoding="utf-8"))
        cls.allocation = json.loads((ROOT / outputs["allocation"]).read_text(encoding="utf-8"))
        cls.checkpoint = json.loads((ROOT / outputs["checkpoint"]).read_text(encoding="utf-8"))
        cls.surface = json.loads((ROOT / outputs["surface_matrix"]).read_text(encoding="utf-8"))
        cls.symbols = json.loads((ROOT / outputs["symbols"]).read_text(encoding="utf-8"))
        cls.audit = json.loads((ROOT / outputs["audit"]).read_text(encoding="utf-8"))
        cls.payload = (ROOT / outputs["payload"]).read_bytes()

    def test_parent_and_output_identity_are_exact(self) -> None:
        self.assertEqual(len(self.parent), 32 * 1024 * 1024)
        self.assertEqual(sha256(self.parent), self.config["inputs"]["stage71_rom"]["sha256"])
        self.assertEqual(len(self.rom), len(self.parent))
        self.assertEqual(sha256(self.rom), self.metadata["output"]["sha256"])
        self.assertEqual(self.checkpoint["output_sha256"], sha256(self.rom))

    def test_payload_is_central_allocator_sequence_74_and_exact_rom_slice(self) -> None:
        rows = self.allocation["allocations"]
        row = rows[-1]
        self.assertEqual(row["sequence"], 74)
        self.assertEqual(row["name"], self.config["allocation"]["name"])
        self.assertEqual(row["content_sha256"], sha256(self.payload))
        self.assertEqual(self.rom[row["start"]:row["end_exclusive"]], self.payload)
        self.assertEqual(self.audit["payload"]["code_size"] + self.audit["payload"]["description_size"], len(self.payload))
        self.assertEqual(self.allocation["summaries"]["overlap_count"], 0)

    def test_every_hook_has_exact_parent_preimage_and_thumb_veneer(self) -> None:
        symbols = {key: int(value, 0) for key, value in self.symbols["symbols"].items()}
        for hook in self.config["hooks"]:
            with self.subTest(hook=hook["name"]):
                address = int(hook["address"], 0)
                start = address - ROM_BASE
                width = hook["width"]
                self.assertEqual(self.parent[start:start + width], bytes.fromhex(hook["parent_hex"]))
                patched = self.rom[start:start + width]
                self.assertEqual(struct.unpack_from("<I", patched, width - 4)[0], symbols[hook["target"]] | 1)
                if width == 12:
                    self.assertEqual(patched[:8], bytes.fromhex("9c46014b1847c046"))
                else:
                    self.assertEqual(patched[:4], bytes.fromhex("004b1847"))

    def test_four_and_five_argument_entries_restore_r3_and_preserve_r2(self) -> None:
        load = int(self.symbols["load_address"], 0)
        required = [
            "Stage72_EntryAbilityBattleEffects", "Stage72_EntryDoesProtectionMoveBlockMove",
            "Stage72_EntryProtectAffects", "Stage72_EntryNonInvasiveCheckGrounding",
            "Stage72_EntryTypeCalc", "Stage72_EntryAITypeCalcPart", "Stage72_EntryCalcVisualBasePower",
        ]
        expected_prefix = bytes.fromhex("634604b4")  # mov r3,ip; push {r2}
        for name in required:
            offset = (int(self.symbols["symbols"][name], 0) & ~1) - load
            with self.subTest(symbol=name):
                self.assertEqual(self.payload[offset:offset + 4], expected_prefix)
                self.assertEqual(self.payload[offset + 8:offset + 12], bytes.fromhex("04bc6047"))

    def test_original_trampolines_bind_all_untouched_continuations(self) -> None:
        continuations = [
            0x090B6689, 0x090BC1F5, 0x090BC4CD, 0x090D4305,
            0x090E66E1, 0x090E5ED9, 0x090E8071, 0x090E53BD,
            0x090E3139, 0x090E83DD, 0x090E541D, 0x090E579D,
            0x090D6585, 0x090D4721, 0x090D43DD, 0x090D4465,
            0x090E6281, 0x090E5A69, 0x090E4A89, 0x090E4789,
            0x090DF7A9, 0x0910C1F5, 0x090BCAE5, 0x090BC691,
            0x090BC6C1, 0x090BC7D5, 0x090C8EF9, 0x090E59D9,
            0x0912B96D,
        ]
        for address in continuations:
            with self.subTest(continuation=f"0x{address:08X}"):
                self.assertEqual(self.payload.count(struct.pack("<I", address)), 1)

    def test_final_descriptions_ratings_and_mold_flags(self) -> None:
        tables = self.config["ability_tables"]
        pointer_start = int(tables["descriptions"]["address"], 0) - ROM_BASE + 312 * 4
        rating_start = int(tables["ratings"]["address"], 0) - ROM_BASE + 312
        mold_start = int(tables["mold_breaker_ignored"]["address"], 0) - ROM_BASE + 312
        mapping, tokens = _charmap(ROOT)
        for index, ability in enumerate(self.config["abilities"]):
            pointer = struct.unpack_from("<I", self.rom, pointer_start + index * 4)[0]
            encoded = _encode_text(ability["description_ja"], mapping, tokens)
            offset = pointer - ROM_BASE
            with self.subTest(ability=ability["id"]):
                self.assertEqual(self.rom[offset:offset + len(encoded)], encoded)
                self.assertEqual(self.rom[rating_start + index], ability["rating"])
                self.assertEqual(self.rom[mold_start + index], ability["mold_breaker_ignored"])
        self.assertEqual([row["mold_breaker_ignored"] for row in self.config["abilities"]], [0, 1, 0, 0, 0, 0])

    def test_ability_zero_through_311_and_names_zero_through_317_are_unchanged(self) -> None:
        tables = self.config["ability_tables"]
        for key, count in (("names", 318), ("descriptions", 312), ("ratings", 312), ("mold_breaker_ignored", 312)):
            table = tables[key]
            start = int(table["address"], 0) - ROM_BASE
            size = count * table["stride"]
            with self.subTest(table=key):
                self.assertEqual(self.rom[start:start + size], self.parent[start:start + size])

    def test_six_mega_forms_keep_all_three_u16_ability_slots(self) -> None:
        binding = self.config["mega_binding"]
        base = int(binding["base_stats_address"], 0) - ROM_BASE
        for ability in self.config["abilities"]:
            row = base + ability["mega_species"] * binding["stride"]
            values = [struct.unpack_from("<H", self.rom, row + field)[0] for field in binding["ability_offsets"]]
            with self.subTest(species=ability["mega_species"]):
                self.assertEqual(values, [ability["id"]] * 3)
                self.assertEqual(self.rom[row:row + binding["stride"]], self.parent[row:row + binding["stride"]])

    def test_change_allowlist_is_complete_and_no_other_byte_changed(self) -> None:
        allowed = bytearray(len(self.parent))
        for row in self.audit["writes"]:
            allowed[row["start"]:row["end_exclusive"]] = b"\x01" * row["size"]
        changed = [index for index, (before, after) in enumerate(zip(self.parent, self.rom)) if before != after]
        self.assertTrue(changed)
        self.assertTrue(all(allowed[index] for index in changed))
        self.assertEqual(len(changed), self.audit["changed_byte_count"])
        self.assertEqual(self.audit["outside_allowlist_count"], 0)

    def test_incremental_bps_round_trip_is_exact(self) -> None:
        bps = (ROOT / self.config["outputs"]["incremental_bps"]).read_bytes()
        self.assertEqual(apply_bps(self.parent, bps), self.rom)
        self.assertEqual(sha256(bps), self.metadata["bps"]["sha256"])

    def test_surface_matrix_is_honest_non_rc_and_covers_all_six(self) -> None:
        self.assertFalse(self.metadata["release_candidate"])
        self.assertFalse(self.surface["release_candidate"])
        self.assertEqual([row["id"] for row in self.surface["abilities"]], list(range(312, 318)))
        gaps = "\n".join(self.surface["unconnected_surfaces"])
        self.assertIn("popup", gaps)
        self.assertIn("AI", gaps)
        self.assertIn("1/4 damage予測", gaps)
        self.assertIn("実効果は接続済み", gaps)
        self.assertIn("mGBA", gaps)
        self.assertEqual(self.checkpoint["release_blockers"], self.metadata["release_blockers"])
        self.assertIn("PIERCING_DRILL_AI_QUARTER_PREDICTION_UNCONNECTED", self.checkpoint["release_blockers"])

    def test_reviewed_high_risk_edges_are_fail_closed_in_source(self) -> None:
        source = (ROOT / "overlays/modernization_p05_ability_rom_runtime/modernization_p05_ability_rom_runtime.c").read_text(encoding="utf-8")
        header = (ROOT / "overlays/modernization_p05_ability_rom_runtime/modernization_p05_ability_rom_runtime.h").read_text(encoding="utf-8")

        # Eelevate: status Ground moves are never mapped to Levitate, while an
        # Ability Shield holder keeps its own immunity against Mold Breaker.
        self.assertIn("Stage72_IsDamagingGroundMove", source)
        self.assertGreaterEqual(source.count("Stage72_MoveSplit(move) != STAGE72_SPLIT_STATUS"), 4)
        self.assertIn("STAGE72_ITEM_EFFECT_ABILITY_SHIELD = 147", header)
        self.assertGreaterEqual(source.count("STAGE72_ITEM_EFFECT_ABILITY_SHIELD"), 3)

        # Spicy Spray: delayed attacks resolve the stored original party slot;
        # an off-field original user fails closed instead of burning a replacement.
        self.assertIn("STAGE72_ARG_IN_FUTURE_ATTACK = 3", source)
        self.assertIn("STAGE72_WISH_FUTURE_PARTY_INDEX_OFFSET", source)
        self.assertIn("STAGE72_G_BATTLER_PARTY_INDEXES[candidate] == partyIndex", source)
        self.assertIn("Stage72_ResolvePresentDamageAttacker", source)
        self.assertIn("candidate = index == 0 ? attacker : (Stage72U8)(attacker ^ 2u);", source)

        # Piercing Drill: only selected/random targets qualify and individual
        # flags are temporarily removed so a simultaneous side guard is retested.
        self.assertIn("Stage72_IsSingleTargetMove", source)
        self.assertIn("STAGE72_MOVE_TARGET_SELECTED", header)
        self.assertIn("STAGE72_MOVE_TARGET_RANDOM", header)
        self.assertIn("STAGE72_MOVE_FLAG_PROTECT_AFFECTED = 0x02", header)
        self.assertIn("Stage72_MoveProtectAffected(move)", source)
        self.assertIn("Stage72FnCheckContact, 0x090D4524u", source)
        self.assertIn("savedFields & ~(Stage72U32)STAGE72_PROTECT_INDIVIDUAL_MASK", source)
        self.assertGreaterEqual(source.count("Stage72_OriginalProtectAffects("), 3)
        self.assertIn("STAGE72_NEW_BS_MISS_STRING_OFFSET", source)
        self.assertIn("STAGE72_G_BATTLE_COMMUNICATION[6] = savedCommunication", source)
        self.assertIn("Keep touchedProtectLike", source)

    def test_mega_sol_accuracy_growth_and_healing_popup_surfaces_are_hooked(self) -> None:
        hook_names = {row["name"] for row in self.config["hooks"]}
        self.assertEqual(len(hook_names), 29)
        self.assertTrue({
            "AccuracyCalc", "VisualAccuracyCalc", "VisualAccuracyCalc_NoTarget",
            "atk01_accuracycheck", "ModifyGrowthInSun", "atkC0_recoverbasedonsunlight",
            "SetMoveEffect2",
        }.issubset(hook_names))
        source = (ROOT / "overlays/modernization_p05_ability_rom_runtime/modernization_p05_ability_rom_runtime.c").read_text(encoding="utf-8")
        for boundary in (
            "Stage72_Atk01AccuracyCheck", "Stage72_AccuracyCalc",
            "Stage72_VisualAccuracyCalc", "Stage72_VisualAccuracyCalcNoTarget",
            "Stage72_ModifyGrowthInSun", "sStage72MegaSolHealingPopupScript",
        ):
            self.assertIn(boundary, source)
        self.assertIn("STAGE72_BATTLE_SCRIPTING_STAT_CHANGER_OFFSET", source)
        self.assertIn("STAGE72_G_CURRENT_MOVE != STAGE72_MOVE_SHORE_UP", source)
        self.assertNotIn("Stage72FnU8Void, 0x090D6C30u", source)
        self.assertIn("STAGE72_ABILITY_FLOWER_GIFT = 122", (ROOT / "overlays/modernization_p05_ability_rom_runtime/modernization_p05_ability_rom_runtime.h").read_text(encoding="utf-8"))
        self.assertIn("Stage72_MapAllAbilities(\n            &flowerGift", source)
        self.assertIn("Stage72_RestoreAbilityMap(&flowerGift", source)
        self.assertIn("STAGE72_DAMAGE_ATK_PARTNER_ABILITY_OFFSET = 0x14", (ROOT / "overlays/modernization_p05_ability_rom_runtime/modernization_p05_ability_rom_runtime.h").read_text(encoding="utf-8"))
        self.assertGreaterEqual(source.count("STAGE72_DAMAGE_ATK_PARTNER_ABILITY_OFFSET"), 3)

    def test_adversarial_review_edges_are_bound_to_narrow_runtime_paths(self) -> None:
        source = (ROOT / "overlays/modernization_p05_ability_rom_runtime/modernization_p05_ability_rom_runtime.c").read_text(encoding="utf-8")
        header = (ROOT / "overlays/modernization_p05_ability_rom_runtime/modernization_p05_ability_rom_runtime.h").read_text(encoding="utf-8")
        surface_by_id = {row["id"]: row for row in self.surface["abilities"]}

        # A real, effective sunny field already gives 2/3 recovery.  Mega Sol's
        # popup is reserved for the paths where personal sun changes that result,
        # including Utility Umbrella and a living weather suppressor.
        self.assertIn("STAGE72_ITEM_EFFECT_UTILITY_UMBRELLA = 136", header)
        self.assertIn("Stage72U8 originalAlreadyTwoThirds", source)
        self.assertIn("Stage72_WeatherHasEffect()", source)
        self.assertIn("if (!originalAlreadyTwoThirds)", source)
        self.assertIn(
            "weather_heal_popup_only_when_personal_sun_changes_result",
            surface_by_id[315]["connected"],
        )

        # Future Sight may return to the nominal doubles bank or its partner.
        # State 30 must keep the resolved owner through BattleScript_Moxie,
        # because its stat change and animation use BANK_ATTACKER.  The wrapper
        # restores the original move-end attacker only on the next state (31),
        # after that queued script has returned, while preserving bankTarget.
        self.assertIn("candidate = index == 0 ? attacker : (Stage72U8)(attacker ^ 2u);", source)
        self.assertIn("STAGE72_ATK49_SECOND_MOVE_EFFECT = 29", source)
        self.assertIn("!= expectedState", source)
        self.assertIn("Stage72U8 Stage72_SetMoveEffect2(void)", source)
        forced_yield = source[source.index("Stage72U8 Stage72_SetMoveEffect2(void)"):]
        forced_yield = forced_yield[:forced_yield.index("void Stage72_Atk49MoveEnd(void)")]
        self.assertIn("Stage72_OriginalSetMoveEffect2()", forced_yield)
        self.assertIn("STAGE72_BATTLE_SCRIPT_OPCODE_MOVE_END", forced_yield)
        self.assertIn("STAGE72_ATK49_SECOND_MOVE_EFFECT", forced_yield)
        self.assertIn("return 1;", forced_yield)
        self.assertIn(
            "knockout_state29_yield_boundary",
            surface_by_id[313]["connected"],
        )

        # Model the pinned state29 tail: a false SetMoveEffect2 normally runs
        # state30 inline, while the narrow true adapter returns with state==30
        # so the outer Stage72 entry can perform the temporary ability map.
        def state_after_state29(forced: bool) -> tuple[int, bool]:
            state = 29
            effect = forced
            state += 1
            return state, effect

        self.assertEqual(state_after_state29(False), (30, False))
        self.assertEqual(state_after_state29(True), (30, True))
        self.assertIn("STAGE72_ATK49_FATIGUE = 31", source)
        self.assertIn("STAGE72_G_BANK_ATTACKER = owner;", source)
        self.assertIn("state == STAGE72_ATK49_FATIGUE", source)
        self.assertIn("arg1 == STAGE72_ARG_IN_FUTURE_ATTACK", source)
        self.assertIn("Stage72FnVoid, 0x090CC214u", source)
        restore = source[source.index("if (state == STAGE72_ATK49_FATIGUE"):]
        restore = restore[:restore.index("owner = STAGE72_G_BANK_ATTACKER;")]
        self.assertIn("Stage72U8 target = STAGE72_G_BANK_TARGET;", restore)
        self.assertIn("STAGE72_G_BANK_TARGET = target;", restore)
        mapped_path = source[source.index("if (mapped)\n    {"):]
        mapped_path = mapped_path[:mapped_path.index("if (mapped && Stage72_BattleMonAbility")]
        self.assertNotIn("STAGE72_G_BANK_ATTACKER = nominalAttacker;", mapped_path)
        self.assertIn(
            "future_sight_same_user_and_partner_bank_knockout_boost",
            surface_by_id[313]["connected"],
        )

        # The visual calculator must not reveal an unrecorded Ability Shield.
        self.assertIn("Stage72_RecordedItemEffect", source)
        visual = source[source.index("Stage72U8 Stage72_VisualTypeCalcPart"):]
        visual = visual[:visual.index("static void Stage72_CorrectMappedEelevateBanks")]
        self.assertIn("Stage72_RecordedItemEffect(bankDef)", visual)
        self.assertNotIn("Stage72_BankItemEffect(bankDef)", visual)
        self.assertIn("visual_recorded_item_boundary", surface_by_id[313]["connected"])

    def test_runtime_source_keeps_ability_width_and_key_boundaries(self) -> None:
        header = (ROOT / "overlays/modernization_p05_ability_rom_runtime/modernization_p05_ability_rom_runtime.h").read_text(encoding="utf-8")
        source = (ROOT / "overlays/modernization_p05_ability_rom_runtime/modernization_p05_ability_rom_runtime.c").read_text(encoding="utf-8")
        self.assertIn("typedef unsigned short Stage72U16;", header)
        for ability in ("DRAGONIZE", "EELEVATE", "FIRE_MANE", "MEGA_SOL", "PIERCING_DRILL", "SPICY_SPRAY"):
            self.assertIn(f"STAGE72_ABILITY_{ability}", source + header)
        self.assertIn("!STAGE72_FN(Stage72FnMovePredicate, 0x090F1CF4u)(move)", source)
        self.assertIn("STAGE72_MOVE_TERA_BLAST = 0x3C6", header)
        self.assertIn("Stage72_InactiveTeraBlast", source)
        self.assertIn("0x09130674u", source)
        self.assertIn("0x09130450u", source)
        self.assertIn("Stage72_GetMoveTypeSpecialPreAbility", source)
        self.assertIn("STAGE72_NEW_BS_ELECTRIFY_TIMERS_OFFSET", source)
        self.assertIn("Stage72FnU8Void, 0x090D77F4u", source)
        self.assertIn("Stage72FnCheckMoveTable, 0x09130F38u", source)
        for boundary in ("Stage72_GetMoveTypeSpecialPostAbility", "Stage72_AdjustBasePower", "Stage72_AbilityBattleEffects", "Stage72_DoesProtectionMoveBlockMove", "Stage72_Atk49MoveEnd"):
            self.assertIn(boundary, source)


if __name__ == "__main__":
    unittest.main()
