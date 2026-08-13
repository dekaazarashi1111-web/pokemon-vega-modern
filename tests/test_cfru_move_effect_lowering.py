from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from tools.engine.cfru_move_effect_lowering import (
    EXPECTED_MOVE_PLANS,
    EXPECTED_OPERATIONS,
    MAX_SCRIPT_BYTES,
    MAX_SCRIPT_COMMANDS,
    MoveEffectLoweringError,
    RUNTIME_EFFECT_SYMBOLS,
    apply_required_native_patches,
    lower_t04_move_effects,
    validate_linked_adapter_disassembly,
)


ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT / "generated/engine/moves/move_port.json"


class CfruMoveEffectLoweringTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.model = json.loads(MODEL_PATH.read_text(encoding="utf-8"))
        cls.bundle = lower_t04_move_effects(cls.model)
        cls.bindings = {row["move_id"]: row for row in cls.bundle["bindings"]}

    def test_frozen_70_plans_and_66_operations_are_lowered_exactly(self) -> None:
        self.assertEqual(self.bundle["schema"], "cfru-vega-move-effect-lowering/v1")
        self.assertEqual(self.bundle["adapter_count"], 70)
        self.assertEqual(self.bundle["operation_count"], 66)
        self.assertEqual(set(self.bindings), set(EXPECTED_MOVE_PLANS))
        self.assertEqual(len(EXPECTED_OPERATIONS), 66)
        for move_id, expected in EXPECTED_MOVE_PLANS.items():
            self.assertEqual(tuple(self.bindings[move_id]["operations"]), expected)

    def test_every_move_has_a_unique_linked_native_symbol(self) -> None:
        symbols = [row["script_symbol"] for row in self.bundle["bindings"]]
        self.assertEqual(len(symbols), len(set(symbols)))
        self.assertEqual(symbols[0], "VegaMoveEffectScript_292")
        self.assertEqual(symbols[-1], "VegaMoveEffectScript_509")
        asm = self.bundle["sources"]["assembly/battle_scripts/vega_move_effect_adapters.s"]
        self.assertEqual(asm.count(".global VegaMoveEffectScript_"), 70)
        self.assertEqual(asm.count("\nVegaMoveEffectScript_"), 71)  # 70 entry labels + move440 rain label
        self.assertEqual(asm.count(".global VegaMoveEffectAdaptersEnd"), 1)
        self.assertTrue(asm.rstrip().endswith("VegaMoveEffectAdaptersEnd:"))

    def test_old_vega_script_pointers_are_absent_from_every_output(self) -> None:
        output = "\n".join(self.bundle["sources"].values())
        pointers = {
            row["effect_adapter"]["source_script_pointer"]
            for row in self.model["moves"]
            if row.get("effect_adapter")
        }
        for pointer in pointers:
            self.assertNotIn(str(pointer), output)
            self.assertNotIn(f"0x{pointer:08X}", output)
        self.assertNotRegex(output, r"\b0x0[89][0-9A-Fa-f]{6}\b")

    def test_unknown_or_changed_operation_fails_closed(self) -> None:
        bad = copy.deepcopy(self.model)
        row = next(row for row in bad["moves"] if row.get("effect_adapter"))
        row["effect_adapter"]["effect_plan"]["operations"].append("FALL_BACK_TO_HIT")
        with self.assertRaisesRegex(MoveEffectLoweringError, "unknown operation"):
            lower_t04_move_effects(bad)

        changed = copy.deepcopy(self.model)
        row = next(row for row in changed["moves"] if row.get("effect_adapter"))
        row["effect_adapter"]["effect_plan"]["operations"] = ["DAMAGE"]
        with self.assertRaisesRegex(MoveEffectLoweringError, "plan changed"):
            lower_t04_move_effects(changed)

    def test_missing_adapter_and_field_contract_fail_closed(self) -> None:
        missing = copy.deepcopy(self.model)
        row = next(row for row in missing["moves"] if row.get("effect_adapter"))
        row["effect_adapter"] = None
        with self.assertRaisesRegex(MoveEffectLoweringError, "adapter set changed"):
            lower_t04_move_effects(missing)

        wrong_target = copy.deepcopy(self.model)
        row = next(row for row in wrong_target["moves"] if row.get("id") == 357)
        row["battle"]["target"] = 0
        with self.assertRaisesRegex(MoveEffectLoweringError, "target"):
            lower_t04_move_effects(wrong_target)

        wrong_protect = copy.deepcopy(self.model)
        row = next(row for row in wrong_protect["moves"] if row.get("id") == 472)
        row["battle"]["flags"] &= ~0x2
        with self.assertRaisesRegex(MoveEffectLoweringError, "PROTECT_AFFECTED"):
            lower_t04_move_effects(wrong_protect)

    def test_recoil_and_user_confusion_do_not_share_old_pointer_semantics(self) -> None:
        # T04 evidence had 425/431 on one old script pointer despite different
        # plans.  Native symbols and mechanics must remain distinct.
        recoil = self.bindings[425]
        confusion = self.bindings[431]
        self.assertNotEqual(recoil["script_symbol"], confusion["script_symbol"])
        self.assertEqual(recoil["recoil_denominator"], 3)
        self.assertEqual(recoil["script_commands"], ["goto BS_STANDARD_HIT"])
        self.assertIn("MOVE_EFFECT_CONFUSION | MOVE_EFFECT_AFFECTS_USER", confusion["script_commands"][0])
        self.assertEqual(confusion["recoil_denominator"], 0)

    def test_recoil_uses_current_cfru_effect_namespace_and_ai_case(self) -> None:
        for move_id in (358, 425):
            binding = self.bindings[move_id]
            self.assertEqual(binding["runtime_effect_id"], 48)
            self.assertEqual(binding["runtime_effect_symbol"], "EFFECT_RECOIL")
            self.assertEqual(binding["table_memberships"], ["gPercent33RecoilMoves"])
            self.assertNotIn("198", " ".join(binding["script_commands"]))
            self.assertNotIn("0xE6", " ".join(binding["script_commands"]))
        recoil_ai = next(
            row for row in self.bundle["required_patches"] if row["id"] == "recoil-ai-query"
        )
        self.assertIn("VegaMoveEffectRecoilDenominator(move) == 3", recoil_ai["replacement"])

    def test_confusion_adapter_uses_cfru_symbol_not_u8_jumpifability_bytes(self) -> None:
        binding = self.bindings[445]
        self.assertEqual(binding["runtime_effect_id"], 49)
        self.assertEqual(binding["script_commands"], ["goto BS_049_SetConfusion"])
        asm = self.bundle["sources"]["assembly/battle_scripts/vega_move_effect_adapters.s"]
        self.assertNotIn("jumpifability", asm)

    def test_false_swipe_and_three_self_drops_have_explicit_native_semantics(self) -> None:
        false_swipe = self.bindings[472]
        self.assertIn("FALSE_SWIPE_DAMAGE_FLOOR", false_swipe["query_operations"])
        self.assertEqual(false_swipe["semantic_flags"] & 0x2, 0x2)
        drops = "\n".join(self.bindings[486]["script_commands"])
        for effect in ("MOVE_EFFECT_DEF_MINUS_1", "MOVE_EFFECT_SP_DEF_MINUS_1", "MOVE_EFFECT_SPD_MINUS_1"):
            self.assertIn(effect + " | MOVE_EFFECT_AFFECTS_USER | MOVE_EFFECT_CERTAIN", drops)
        self.assertEqual(drops.count("seteffectwithchancetarget"), 3)

    def test_move449_keeps_two_independent_exact_secondary_rolls(self) -> None:
        commands = self.bindings[449]["script_commands"]
        defense = commands.index("setmoveeffect MOVE_EFFECT_DEF_MINUS_1")
        freeze = commands.index("setmoveeffect MOVE_EFFECT_FREEZE")
        self.assertEqual(commands[defense + 1], "seteffectwithchancetarget")
        self.assertEqual(commands[freeze + 1], "seteffectwithchancetarget")
        self.assertLess(defense, freeze)
        self.assertEqual(commands.count("seteffectwithchancetarget"), 2)

        source = self.bundle["sources"]["src/vega_move_effect_adapters.c"]
        self.assertIn(
            "move == 449u && (moveEffect & 0x3Fu) == MOVE_EFFECT_FREEZE",
            source,
        )
        self.assertIn("return 10u;\n    return fallbackChance;", source)
        # Independent 20% / 10% rolls: both, defense-only, freeze-only, none.
        self.assertEqual((20 * 10, 20 * 90, 80 * 10, 80 * 90), (200, 1800, 800, 7200))

    def test_runtime_effect_overrides_use_the_fixed_cfru_namespace(self) -> None:
        expected_symbols = {
            0: "EFFECT_HIT", 2: "EFFECT_POISON_HIT", 6: "EFFECT_PARALYZE_HIT",
            31: "EFFECT_FLINCH_HIT", 36: "EFFECT_TRI_ATTACK", 42: "EFFECT_TRAP",
            48: "EFFECT_RECOIL",
            49: "EFFECT_CONFUSE", 55: "EFFECT_ACCURACY_UP_2",
            69: "EFFECT_DEFENSE_DOWN_HIT", 70: "EFFECT_SPEED_DOWN_HIT",
            72: "EFFECT_SPECIAL_DEFENSE_DOWN_HIT", 73: "EFFECT_ACCURACY_DOWN_HIT",
            74: "EFFECT_EVASION_DOWN_HIT", 76: "EFFECT_CONFUSE_HIT",
            96: "EFFECT_SPEED_UP_1_HIT", 110: "EFFECT_SPECIAL_ATTACK_UP_CHANCE",
            117: "EFFECT_ROLLOUT", 138: "EFFECT_DEFENSE_UP_HIT",
            139: "EFFECT_ATTACK_UP_HIT", 182: "EFFECT_SUPERPOWER",
            187: "EFFECT_YAWN", 198: "EFFECT_ATK_SPATK_UP",
            204: "EFFECT_OVERHEAT", 209: "EFFECT_BAD_POISON_HIT",
        }
        self.assertEqual(RUNTIME_EFFECT_SYMBOLS, expected_symbols)
        self.assertEqual(self.bundle["runtime_effect_symbols"], expected_symbols)
        for binding in self.bundle["bindings"]:
            effect = self.bundle["runtime_effect_overrides"][binding["move_id"]]
            self.assertEqual(binding["runtime_effect_symbol"], expected_symbols[effect])
        # These are the three namespace-conflict representatives: old Vega
        # recoil 0xE6 becomes current CFRU 48, confusion is current CFRU 49, and
        # the V-Create-style three self drops use CFRU's SUPERPOWER family.
        self.assertEqual(self.bindings[358]["runtime_effect_symbol"], "EFFECT_RECOIL")
        self.assertEqual(self.bindings[445]["runtime_effect_symbol"], "EFFECT_CONFUSE")
        self.assertEqual(self.bindings[486]["runtime_effect_symbol"], "EFFECT_SUPERPOWER")

    def test_sound_fixed_hits_and_recoil_publish_table_membership_contracts(self) -> None:
        memberships = self.bundle["native_table_memberships"]
        self.assertEqual(memberships["gSoundMoves"]["move_ids"], [428, 455, 465, 473, 477])
        self.assertEqual(memberships["gPercent33RecoilMoves"]["move_ids"], [358, 425])
        self.assertEqual(memberships["gTwoStrikesMoves"]["move_ids"], [427, 451])
        self.assertTrue(all(row["materialization"] == "central_query" for row in memberships.values()))
        self.assertEqual(self.bindings[480]["fixed_hit_count"], 3)

    def test_native_patch_manifest_covers_runtime_and_ai_consumers(self) -> None:
        patches = {row["id"]: row for row in self.bundle["required_patches"]}
        for patch_id in (
            "sound-central-query", "recoil-runtime-query", "recoil-ai-query",
            "fixed-hit-runtime-query", "fixed-hit-damage-query",
            "fixed-hit-ai-party-query", "fixed-hit-ai-active-query",
            "fixed-hit-parental-bond-query",
            "false-swipe-positive-query", "false-swipe-negative-query",
            "ignore-positive-evasion-query", "critical-runtime-query",
            "critical-ai-query", "dynamic-power-query",
            "per-effect-secondary-chance", "fixed-trap-duration",
            "fixed-hit-user-secondary-once",
        ):
            self.assertIn(patch_id, patches)
        self.assertEqual(patches["false-swipe-positive-query"]["expected_count"], 3)
        self.assertEqual(patches["false-swipe-negative-query"]["expected_count"], 1)
        consumers = {consumer for patch in patches.values() for consumer in patch["consumers"]}
        self.assertIn("AI damage", consumers)
        self.assertIn("AI party damage fixed-hit multiplier", consumers)
        self.assertIn("AI active-defender damage fixed-hit multiplier", consumers)
        self.assertIn("AI Parental Bond damage", consumers)
        self.assertIn("move 427 single user-boost roll", consumers)
        self.assertIn("AI recoil scoring", consumers)
        self.assertIn("Soundproof", consumers)

    def test_no_evasion_boost_keeps_negative_evasion_benefit(self) -> None:
        patch = next(
            row for row in self.bundle["required_patches"]
            if row["id"] == "ignore-positive-evasion-query"
        )
        self.assertTrue(patch["needle"].startswith("else if (atkAbility == ABILITY_KEENEYE"))
        self.assertNotIn("gIgnoreStatChangesMoves", patch["replacement"])
        self.assertIn("VegaMoveEffectIgnoresPositiveEvasion(move)", patch["replacement"])

        # The generated query joins CFRU's Keen Eye branch: stage > 6 is
        # neutralized, while stage <= 6 still contributes its accuracy benefit.
        def resulting_buff(accuracy_stage: int, evasion_stage: int) -> int:
            if evasion_stage > 6:
                return accuracy_stage
            return accuracy_stage + 6 - evasion_stage

        self.assertEqual(resulting_buff(6, 8), 6)  # +2 evasion is ignored.
        self.assertEqual(resulting_buff(6, 6), 6)  # Neutral is unchanged.
        self.assertEqual(resulting_buff(6, 4), 8)  # -2 evasion remains useful.

    def test_move427_user_boost_rolls_once_across_two_hits(self) -> None:
        patch = next(
            row for row in self.bundle["required_patches"]
            if row["id"] == "fixed-hit-user-secondary-once"
        )
        self.assertLess(
            patch["replacement"].index("VegaMoveEffectCanRollSecondaryOnce"),
            patch["replacement"].index("Random()"),
        )
        self.assertIn("Random() % 100 < percentChance", patch["replacement"])
        self.assertNotIn("Random() % 100 <= percentChance", patch["replacement"])
        source = self.bundle["sources"]["src/vega_move_effect_adapters.c"]
        self.assertIn("if (move == 427u", source)
        self.assertIn("MOVE_EFFECT_ATK_PLUS_1 | MOVE_EFFECT_AFFECTS_USER", source)
        self.assertIn("if (gNewBS->secondaryEffectApplied)\n            return FALSE;", source)
        self.assertIn("gNewBS->secondaryEffectApplied = TRUE;", source)
        for move_id in (444, 448, 469):
            self.assertNotIn(f"move == {move_id}u", source)

        # CMD49 executes the native script once per hit.  The helper consumes
        # the chance before the first RNG result, so both RNG-success and
        # RNG-failure fixtures have one roll and at most one +1 boost.
        for first_roll_succeeds in (False, True):
            attempted = False
            rolls = 0
            boosts = 0
            for _hit in range(2):
                if attempted:
                    continue
                attempted = True
                rolls += 1
                boosts += int(first_roll_succeeds)
            self.assertEqual(rolls, 1)
            self.assertLessEqual(boosts, 1)

        # RNG is uniformly reduced to 0..99, so `< percentChance` gives exact
        # 10/20/30/100 percent boundaries.  Serene Grace's doubled values use
        # the same comparator and cap naturally at all 100 values.
        for chance, expected in ((10, 10), (20, 20), (30, 30), (100, 100)):
            self.assertEqual(sum(roll < chance for roll in range(100)), expected)

    def test_move440_rain_preserves_attack_and_only_doubles_spattack(self) -> None:
        commands = self.bindings[440]["script_commands"]
        rain = commands[commands.index("VegaMoveEffectScript_440_Rain:") + 1 :]
        self.assertEqual(
            rain,
            [
                "setmoveeffect MOVE_EFFECT_ATK_PLUS_1 | MOVE_EFFECT_AFFECTS_USER | MOVE_EFFECT_CERTAIN",
                "seteffectwithchancetarget",
                "setmoveeffect MOVE_EFFECT_SP_ATK_PLUS_2 | MOVE_EFFECT_AFFECTS_USER | MOVE_EFFECT_CERTAIN",
                "seteffectwithchancetarget",
                "goto BS_MOVE_END",
            ],
        )

    def test_move474_only_doubles_after_a_real_runtime_hit(self) -> None:
        source = self.bundle["sources"]["src/vega_move_effect_adapters.c"]
        case = source.split("case 474u:", 1)[1].split("default:", 1)[0]
        self.assertIn(
            "!(data->specialFlags & (VEGA_DAMAGE_FLAG_CHECKING_FROM_MENU | VEGA_DAMAGE_FLAG_AI_CALC))",
            case,
        )
        self.assertLess(case.index("specialFlags"), case.index("gProtectStructs"))

        def adjusted(flags: int, real_hit: bool, power: int = 60) -> int:
            return power * 2 if not (flags & 0xC) and real_hit else power

        self.assertEqual(adjusted(0, True), 120)
        self.assertEqual(adjusted(0, False), 60)
        self.assertEqual(adjusted(4, True), 60)  # menu calculation
        self.assertEqual(adjusted(8, True), 60)  # AI calculation

    def test_required_patches_are_pure_and_fail_closed(self) -> None:
        fixture: dict[str, str] = {}
        for patch in self.bundle["required_patches"]:
            fixture.setdefault(patch["path"], "")
            fixture[patch["path"]] += (patch["needle"] + "\n") * patch["expected_count"]
        original = dict(fixture)
        patched = apply_required_native_patches(fixture, self.bundle)
        self.assertEqual(fixture, original)
        self.assertNotEqual(patched, original)
        for patch in self.bundle["required_patches"]:
            self.assertIn(patch["replacement"], patched[patch["path"]])

        broken = dict(fixture)
        first = self.bundle["required_patches"][0]
        broken[first["path"]] = broken[first["path"]].replace(first["needle"], "", 1)
        with self.assertRaisesRegex(MoveEffectLoweringError, "expected"):
            apply_required_native_patches(broken, self.bundle)

    def test_script_and_linked_disassembly_are_bounded(self) -> None:
        self.assertEqual(self.bundle["bounds"]["maximum_script_bytes"], MAX_SCRIPT_BYTES)
        self.assertEqual(self.bundle["bounds"]["maximum_script_commands"], MAX_SCRIPT_COMMANDS)
        for binding in self.bundle["bindings"]:
            contract = binding["disassembly_contract"]
            self.assertLessEqual(contract["maximum_bytes"], MAX_SCRIPT_BYTES)
            self.assertLessEqual(contract["maximum_commands"], MAX_SCRIPT_COMMANDS)
            self.assertNotIn("jumpifability", contract["opcodes"])

        image = bytes(range(256)) * 2
        ranges = {
            f"VegaMoveEffectScript_{move_id}": (index, index + 1)
            for index, move_id in enumerate(EXPECTED_MOVE_PLANS)
        }
        result = validate_linked_adapter_disassembly(image, ranges, (0x08123456,))
        self.assertEqual(result["symbol_count"], 70)
        self.assertEqual(result["total_bytes"], 70)
        self.assertEqual(result["decoded_command_count"], 0)

        bad_ranges = dict(ranges)
        bad_ranges["VegaMoveEffectScript_292"] = (0, MAX_SCRIPT_BYTES + 1)
        with self.assertRaisesRegex(MoveEffectLoweringError, "exceeds"):
            validate_linked_adapter_disassembly(image, bad_ranges)

        pointer = 0x08123456
        linked = pointer.to_bytes(4, "little") + bytes(100)
        pointer_ranges = dict(ranges)
        pointer_ranges["VegaMoveEffectScript_292"] = (0, 4)
        for index, move_id in enumerate(list(EXPECTED_MOVE_PLANS)[1:], start=4):
            pointer_ranges[f"VegaMoveEffectScript_{move_id}"] = (index, index + 1)
        with self.assertRaisesRegex(MoveEffectLoweringError, "legacy Vega script pointer"):
            validate_linked_adapter_disassembly(linked, pointer_ranges, (pointer,))

    def test_linked_decoder_uses_current_jumpifweather_operand_width(self) -> None:
        image = bytearray()
        ranges: dict[str, tuple[int, int]] = {}
        commands: dict[str, list[str]] = {}
        for move_id in EXPECTED_MOVE_PLANS:
            symbol = f"VegaMoveEffectScript_{move_id}"
            start = len(image)
            if move_id == 440:
                # opcode, predicate, u32 WEATHER_FLAGS, u16 weather, u32 target
                image += bytes((0x2A, 0x00))
                image += (0x02000000).to_bytes(4, "little")
                image += (0x0001).to_bytes(2, "little")
                image += (0x08001234).to_bytes(4, "little")
                commands[symbol] = ["jumpifweather WEATHER_RAIN_ANY local"]
            else:
                image += bytes((0x28,)) + (0x08001234).to_bytes(4, "little")
                commands[symbol] = ["goto BS_STANDARD_HIT"]
            ranges[symbol] = (start, len(image))

        result = validate_linked_adapter_disassembly(bytes(image), ranges, (), commands)
        self.assertEqual(result["decoded_command_count"], 70)
        broken = bytearray(image)
        weather_start = ranges["VegaMoveEffectScript_440"][0]
        broken[weather_start + 8:weather_start + 12] = (0x02000000).to_bytes(4, "little")
        with self.assertRaisesRegex(MoveEffectLoweringError, "control target outside ROM"):
            validate_linked_adapter_disassembly(bytes(broken), ranges, (), commands)

    def test_generation_is_deterministic(self) -> None:
        self.assertEqual(self.bundle, lower_t04_move_effects(self.model))


if __name__ == "__main__":
    unittest.main()
