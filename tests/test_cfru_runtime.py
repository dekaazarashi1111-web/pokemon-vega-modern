import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import textwrap
import unittest


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_C = ROOT / "overlays" / "cfru" / "runtime.c"
INCLUDE_DIR = ROOT / "overlays" / "cfru"
CONFIG = ROOT / "config" / "battle_core.json"


HARNESS = r'''
#include "runtime.h"

#define CHECK(condition) do { if (!(condition)) return __LINE__; } while (0)

static int test_ai(void)
{
    CHECK(cfru_ai_profile_is_valid(1));
    CHECK(cfru_ai_profile_is_valid(3));
    CHECK(cfru_ai_profile_is_valid(5));
    CHECK(!cfru_ai_profile_is_valid(0));
    CHECK(!cfru_ai_profile_is_valid(2));
    CHECK(!cfru_ai_profile_is_valid(7));
    CHECK(cfru_ai_profile_bits(CFRU_AI_BASIC) == 1);
    CHECK(cfru_ai_profile_bits(CFRU_AI_SEMI_SMART) == 3);
    CHECK(cfru_ai_profile_bits(CFRU_AI_FULL_SMART) == 5);
    return 0;
}

static int test_mechanics(void)
{
    CfruMechanicState state = {0};
    cfru_u8 side;
    cfru_u8 mode;

    CHECK(cfru_mechanic_begin(&state, CFRU_MECHANIC_STANDARD, 9));
    CHECK(!cfru_mechanic_can_use(&state, CFRU_SIDE_PLAYER, CFRU_MECHANIC_MEGA));
    cfru_mechanic_cleanup(&state);
    CHECK(!state.active);

    for (mode = CFRU_MECHANIC_MEGA; mode <= CFRU_MECHANIC_TERASTAL; ++mode)
    {
        CHECK(cfru_mechanic_begin(&state, (CfruMechanicMode)mode, 9));
        for (side = 0; side < CFRU_SIDE_COUNT; ++side)
        {
            CHECK(state.effective_mode[side] == mode);
            CHECK(!cfru_mechanic_is_forced(&state, side));
            CHECK(cfru_mechanic_try_use(&state, side, (CfruMechanicMode)mode));
            CHECK(!cfru_mechanic_try_use(&state, side, (CfruMechanicMode)mode));
        }
    }

    CHECK(cfru_mechanic_begin(
        &state, CFRU_MECHANIC_RAID_HIGH_DIFFICULTY, CFRU_SIDE_OPPONENT));
    CHECK(state.battle_mode == CFRU_MECHANIC_RAID_HIGH_DIFFICULTY);
    CHECK(state.effective_mode[CFRU_SIDE_PLAYER] == CFRU_MECHANIC_STANDARD);
    CHECK(state.effective_mode[CFRU_SIDE_OPPONENT] == CFRU_MECHANIC_DYNAMAX);
    CHECK(cfru_mechanic_is_forced(&state, CFRU_SIDE_OPPONENT));
    CHECK(!cfru_mechanic_is_forced(&state, CFRU_SIDE_PLAYER));
    CHECK(cfru_mechanic_try_use(
        &state, CFRU_SIDE_OPPONENT, CFRU_MECHANIC_DYNAMAX));
    CHECK(!cfru_mechanic_try_use(
        &state, CFRU_SIDE_PLAYER, CFRU_MECHANIC_DYNAMAX));
    cfru_mechanic_cleanup(&state);
    CHECK(!state.active && !state.used[0] && !state.used[1]);
    CHECK(!state.forced[0] && !state.forced[1]);
    CHECK(!cfru_mechanic_begin(
        &state, CFRU_MECHANIC_RAID_HIGH_DIFFICULTY, 2));
    return 0;
}

static int test_stats(void)
{
    CfruStatInputs inputs = {
        4, 12, 2, {0, 7, 15, 21, 30, 1}, (cfru_u8)((1u << 0) | (1u << 4)), 1
    };
    CHECK(cfru_stat_inputs_are_valid(&inputs));
    CHECK(cfru_stat_effective_nature(&inputs) == 12);
    CHECK(cfru_stat_effective_iv(&inputs, 0) == 31);
    CHECK(cfru_stat_effective_iv(&inputs, 1) == 7);
    CHECK(cfru_stat_effective_iv(&inputs, 4) == 31);
    CHECK(cfru_stat_ability_slot(&inputs) == 2);
    CHECK(cfru_stat_receives_battle_exp(&inputs, 0));
    inputs.mint_nature = CFRU_NATURE_UNSET;
    inputs.exp_share_enabled = 0;
    CHECK(cfru_stat_effective_nature(&inputs) == 4);
    CHECK(!cfru_stat_receives_battle_exp(&inputs, 0));
    CHECK(cfru_stat_receives_battle_exp(&inputs, 1));
    inputs.iv[2] = 32;
    CHECK(!cfru_stat_inputs_are_valid(&inputs));
    return 0;
}

static int test_candy(void)
{
    static const cfru_u32 growth[] = {0, 0, 100, 300, 600, 1000};
    CfruCandyTarget party[2] = {{1, 0}, {3, 333}};
    CfruCandyTarget before_other = party[1];
    CfruCandyResult result;

    result = cfru_apply_exp_candy(&party[0], 650, 5, growth, 6);
    CHECK(result.status == CFRU_CANDY_APPLIED);
    CHECK(result.consumed && result.levels_gained == 3);
    CHECK(result.experience_gained == 650 && !result.reached_cap);
    CHECK(party[0].level == 4 && party[0].experience == 650);
    CHECK(party[1].level == before_other.level);
    CHECK(party[1].experience == before_other.experience);

    result = cfru_apply_exp_candy(&party[0], 0xFFFFFFFFu, 5, growth, 6);
    CHECK(result.status == CFRU_CANDY_APPLIED && result.consumed);
    CHECK(result.experience_gained == 350 && result.reached_cap);
    CHECK(party[0].level == 5 && party[0].experience == 1000);

    result = cfru_apply_exp_candy(&party[0], 1, 5, growth, 6);
    CHECK(result.status == CFRU_CANDY_AT_CAP && !result.consumed);
    CHECK(party[0].level == 5 && party[0].experience == 1000);
    party[1].level = 3;
    result = cfru_apply_exp_candy(&party[1], 0, 5, growth, 6);
    CHECK(result.status == CFRU_CANDY_NO_EFFECT && !result.consumed);
    return 0;
}

static int test_trainer_build(void)
{
    CfruTrainerMon base = {
        25, 120, {10, 20, 30, 40}, 50, 4, 0,
        {1, 2, 3, 4, 5, 6}, {0, 0, 0, 0, 0, 0}
    };
    CfruTrainerMon output = {0};
    CfruTrainerBuildPatch patch = {0};

    patch.present_fields = CFRU_TRAINER_FIELD_NATURE
        | CFRU_TRAINER_FIELD_ABILITY_SLOT;
    patch.nature = 18;
    patch.ability_slot = 2;
    patch.iv_mask = (cfru_u8)(1u << 2);
    patch.iv[2] = 31;
    patch.ev_mask = (cfru_u8)((1u << 0) | (1u << 1));
    patch.ev[0] = 252;
    patch.ev[1] = 252;
    patch.move_mask = (cfru_u8)(1u << 3);
    patch.moves[3] = 1062;
    CHECK(cfru_trainer_build_apply(&output, &base, &patch));
    CHECK(output.species == base.species && output.item == base.item);
    CHECK(output.level == base.level && output.moves[0] == base.moves[0]);
    CHECK(output.nature == 18 && output.ability_slot == 2);
    CHECK(output.iv[2] == 31 && output.iv[3] == base.iv[3]);
    CHECK(output.ev[0] == 252 && output.ev[1] == 252);
    CHECK(output.moves[3] == 1062);

    patch.iv[2] = 32;
    CHECK(!cfru_trainer_build_apply(&output, &base, &patch));
    CHECK(output.nature == 18 && output.iv[2] == 31);
    return 0;
}

static int test_facility(void)
{
    CfruFacilityBoundary state = {0};
    cfru_u8 format;
    cfru_u8 rule;
    cfru_u8 effect;
    for (format = 0; format < CFRU_FACILITY_FORMAT_COUNT; ++format)
    {
        for (rule = 0; rule < CFRU_FACILITY_RULE_COUNT; ++rule)
        {
            CHECK(cfru_facility_begin(
                &state, (CfruFacilityFormat)format, (CfruFacilityRule)rule));
            for (effect = 0; effect < CFRU_PERSISTENT_EFFECT_COUNT; ++effect)
                CHECK(!cfru_facility_allows_persistent_effect(
                    &state, (CfruPersistentEffect)effect));
            cfru_facility_end(&state);
            CHECK(cfru_facility_allows_persistent_effect(&state, CFRU_PERSIST_EXP));
        }
    }
    CHECK(!cfru_facility_begin(
        &state, (CfruFacilityFormat)CFRU_FACILITY_FORMAT_COUNT, CFRU_FACILITY_RANDOM));
    return 0;
}

static int test_mirage(void)
{
    CfruMirageItemState state = {0};
    cfru_u8 exit_path;
    for (exit_path = 0; exit_path < CFRU_EXIT_COUNT; ++exit_path)
    {
        cfru_u16 persistent = 42;
        CHECK(cfru_mirage_item_begin(&state, persistent, 900));
        CHECK(cfru_mirage_item_current(&state) == 900);
        CHECK(cfru_mirage_item_set_battle_value(&state, 0));
        persistent = 777;
        CHECK(cfru_mirage_item_finish(
            &state, (CfruBattleExit)exit_path, &persistent));
        CHECK(persistent == 42);
        CHECK(!state.active && cfru_mirage_item_current(&state) == 42);
    }
    return 0;
}

static int test_raid(void)
{
    CfruRaidState state = {0};
    CHECK(cfru_raid_begin(
        &state, CFRU_SIDE_OPPONENT, 0, (cfru_u8)((1u << 1) | (1u << 3)),
        2, 500, 500, 3, 1));
    CHECK(cfru_raid_partner_is_active(&state, 1));
    CHECK(!cfru_raid_partner_is_active(&state, 2));
    CHECK(cfru_raid_shields_remaining(&state) == 2);
    CHECK(cfru_raid_break_shield(&state));
    CHECK(cfru_raid_break_shield(&state));
    CHECK(!cfru_raid_break_shield(&state));
    CHECK(cfru_raid_set_boss_hp(&state, 0));
    CHECK(state.end_reason == CFRU_RAID_END_BOSS_DEFEATED);
    CHECK(cfru_raid_try_capture(&state));
    CHECK(state.captured && state.end_reason == CFRU_RAID_END_CAPTURED);
    CHECK(!cfru_raid_try_capture(&state));
    cfru_raid_cleanup(&state);
    CHECK(!state.active && state.partner_mask == 0 && state.end_reason == 0);

    CHECK(cfru_raid_begin(&state, 1, 0, 0, 0, 1, 1, 2, 0));
    CHECK(cfru_raid_advance_turn(&state));
    CHECK(state.end_reason == CFRU_RAID_END_NONE);
    CHECK(cfru_raid_advance_turn(&state));
    CHECK(state.end_reason == CFRU_RAID_END_TURN_LIMIT);
    CHECK(!cfru_raid_try_capture(&state));
    CHECK(!cfru_raid_begin(&state, 1, 0, 0, 9, 1, 1, 2, 0));
    return 0;
}

int main(void)
{
    int result;
    result = test_ai(); if (result) return result;
    result = test_mechanics(); if (result) return result;
    result = test_stats(); if (result) return result;
    result = test_candy(); if (result) return result;
    result = test_trainer_build(); if (result) return result;
    result = test_facility(); if (result) return result;
    result = test_mirage(); if (result) return result;
    result = test_raid(); if (result) return result;
    return 0;
}
'''


class CfruRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.cc = os.environ.get("CC", "cc")
        if shutil.which(self.cc) is None:
            self.skipTest(f"C compiler not found: {self.cc}")

    def test_config_vocabulary_is_exact(self):
        data = json.loads(CONFIG.read_text(encoding="utf-8"))
        policies = data["policies"]
        self.assertEqual(
            policies["ai_profiles"],
            {"AI_BASIC": 1, "AI_SEMI_SMART": 3, "AI_FULL_SMART": 5},
        )
        self.assertEqual(
            policies["mechanic_modes"],
            ["STANDARD", "MEGA", "Z_MOVE", "DYNAMAX", "TERASTAL", "RAID_HIGH_DIFFICULTY"],
        )
        self.assertEqual(
            policies["facility_formats"],
            ["SINGLE_3V3", "DOUBLE_4V4", "NPC_PARTNER_MULTI"],
        )
        self.assertEqual(
            policies["facility_rules"],
            ["RANDOM", "LITTLE", "MONOTYPE", "UNRESTRICTED", "OU", "UBER", "CAMOMONS", "GS"],
        )

    def test_freestanding_object_has_no_undefined_runtime_symbols(self):
        with tempfile.TemporaryDirectory(prefix="cfru-runtime-") as temp_dir:
            obj = Path(temp_dir) / "runtime.o"
            subprocess.run(
                [
                    self.cc,
                    "-std=c11",
                    "-Wall",
                    "-Wextra",
                    "-Werror",
                    "-pedantic",
                    "-ffreestanding",
                    "-fno-builtin",
                    "-I",
                    str(INCLUDE_DIR),
                    "-c",
                    str(RUNTIME_C),
                    "-o",
                    str(obj),
                ],
                check=True,
                cwd=ROOT,
            )
            nm = shutil.which("nm")
            if nm is not None:
                result = subprocess.run(
                    [nm, "-u", str(obj)],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(result.stdout.strip(), "")

    def test_exact_runtime_contract(self):
        with tempfile.TemporaryDirectory(prefix="cfru-runtime-") as temp_dir:
            harness = Path(temp_dir) / "runtime_harness.c"
            executable = Path(temp_dir) / "runtime_harness"
            harness.write_text(textwrap.dedent(HARNESS), encoding="utf-8")
            subprocess.run(
                [
                    self.cc,
                    "-std=c11",
                    "-Wall",
                    "-Wextra",
                    "-Werror",
                    "-pedantic",
                    "-ffreestanding",
                    "-fno-builtin",
                    "-I",
                    str(INCLUDE_DIR),
                    str(RUNTIME_C),
                    str(harness),
                    "-o",
                    str(executable),
                ],
                check=True,
                cwd=ROOT,
            )
            subprocess.run([str(executable)], check=True, cwd=ROOT)


if __name__ == "__main__":
    unittest.main()
