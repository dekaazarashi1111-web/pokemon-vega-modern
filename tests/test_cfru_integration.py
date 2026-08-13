import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import textwrap
import unittest


ROOT = Path(__file__).resolve().parents[1]
INCLUDE_DIR = ROOT / "overlays" / "cfru"
RUNTIME_C = INCLUDE_DIR / "runtime.c"
INTEGRATION_C = INCLUDE_DIR / "integration.c"


HARNESS = r'''
#include "integration.h"

#define CHECK(condition) do { if (!(condition)) return __LINE__; } while (0)

static cfru_u8 sBattlersCount;
static cfru_u8 sControllerInitCalls;
static cfru_u8 sControllerInitValue;

static void fake_init_controllers(void)
{
    ++sControllerInitCalls;
    sBattlersCount = sControllerInitValue;
}

static int test_begin_ai_mechanic(void)
{
    const CfruIntegrationState *state;
    CHECK(!cfru_integration_battle_begin(2, CFRU_AI_FULL_SMART));
    CHECK(cfru_integration_battle_begin(CFRU_AI_BASIC, CFRU_AI_FULL_SMART));
    state = cfru_integration_state();
    CHECK(state == &gCfruBattlePolicy);
    CHECK(state->battle_active);
    CHECK(state->mechanic.active);
    CHECK(state->mechanic.battle_mode == CFRU_MECHANIC_STANDARD);
    CHECK(!state->controllers_init_attempted);
    CHECK(!state->controllers_ready);
    CHECK(state->observed_battlers_count == 0);
    CHECK(cfru_integration_ai_profile(CFRU_SIDE_PLAYER) == 1);
    CHECK(cfru_integration_ai_profile(CFRU_SIDE_OPPONENT) == 5);
    CHECK(cfru_integration_set_ai_profile(CFRU_SIDE_OPPONENT, CFRU_AI_SEMI_SMART));
    CHECK(cfru_integration_ai_profile(CFRU_SIDE_OPPONENT) == 3);
    CHECK(!cfru_integration_set_ai_profile(2, CFRU_AI_BASIC));

    CHECK(cfru_integration_select_mechanic(CFRU_MECHANIC_MEGA, 9));
    CHECK(!cfru_integration_select_mechanic(CFRU_MECHANIC_Z_MOVE, 9));
    CHECK(cfru_integration_mechanic_mode(CFRU_SIDE_PLAYER) == CFRU_MECHANIC_MEGA);
    CHECK(cfru_integration_mechanic_can_use(CFRU_SIDE_PLAYER, CFRU_MECHANIC_MEGA));
    CHECK(cfru_integration_mechanic_try_use(CFRU_SIDE_PLAYER, CFRU_MECHANIC_MEGA));
    CHECK(!cfru_integration_mechanic_try_use(CFRU_SIDE_PLAYER, CFRU_MECHANIC_MEGA));
    CHECK(cfru_integration_mechanic_try_use(CFRU_SIDE_OPPONENT, CFRU_MECHANIC_MEGA));
    CHECK(!cfru_integration_mechanic_is_forced(CFRU_SIDE_OPPONENT));
    CHECK(cfru_integration_battle_end(CFRU_EXIT_WON));
    CHECK(!state->battle_active && !state->mechanic.active);
    CHECK(!state->mechanic.used[0] && !state->mechanic.used[1]);
    CHECK(state->ai_profile[0] == 0 && state->ai_profile[1] == 0);
    return 0;
}

static int test_battle_controller_init_link(void)
{
    const CfruIntegrationState *state = cfru_integration_state();
    CHECK(cfru_integration_expected_battlers(CFRU_BATTLE_LAYOUT_SINGLE) == 2);
    CHECK(cfru_integration_expected_battlers(CFRU_BATTLE_LAYOUT_DOUBLE) == 4);
    CHECK(cfru_integration_expected_battlers(CFRU_BATTLE_LAYOUT_RAID_TRIPLE) == 3);
    CHECK(cfru_integration_expected_battlers(CFRU_BATTLE_LAYOUT_COUNT) == 0);
    CHECK(!cfru_integration_init_battle_controllers(
        fake_init_controllers, &sBattlersCount, CFRU_BATTLE_LAYOUT_SINGLE));

    sBattlersCount = 0;
    sControllerInitCalls = 0;
    sControllerInitValue = 2;
    CHECK(cfru_integration_battle_begin(CFRU_AI_BASIC, CFRU_AI_FULL_SMART));
    CHECK(sBattlersCount == 0);
    CHECK(cfru_integration_init_battle_controllers(
        fake_init_controllers, &sBattlersCount, CFRU_BATTLE_LAYOUT_SINGLE));
    CHECK(sControllerInitCalls == 1 && sBattlersCount == 2);
    CHECK(state->controllers_ready);
    CHECK(state->expected_battlers_count == 2);
    CHECK(state->observed_battlers_count == 2);
    CHECK(!cfru_integration_init_battle_controllers(
        fake_init_controllers, &sBattlersCount, CFRU_BATTLE_LAYOUT_SINGLE));
    CHECK(sControllerInitCalls == 1);
    CHECK(cfru_integration_battle_end(CFRU_EXIT_WON));
    CHECK(!state->controllers_ready);

    sBattlersCount = 0;
    sControllerInitCalls = 0;
    sControllerInitValue = 2;
    CHECK(cfru_integration_battle_begin(CFRU_AI_BASIC, CFRU_AI_FULL_SMART));
    CHECK(!cfru_integration_init_battle_controllers(
        fake_init_controllers, &sBattlersCount, CFRU_BATTLE_LAYOUT_DOUBLE));
    CHECK(sControllerInitCalls == 1);
    CHECK(!state->controllers_ready);
    CHECK(state->controllers_init_attempted);
    CHECK(state->expected_battlers_count == 4);
    CHECK(state->observed_battlers_count == 2);
    CHECK(!cfru_integration_init_battle_controllers(
        fake_init_controllers, &sBattlersCount, CFRU_BATTLE_LAYOUT_DOUBLE));
    CHECK(sControllerInitCalls == 1);
    CHECK(cfru_integration_battle_end(CFRU_EXIT_ERROR));

    sBattlersCount = 0;
    sControllerInitCalls = 0;
    sControllerInitValue = 3;
    CHECK(cfru_integration_battle_begin(CFRU_AI_BASIC, CFRU_AI_FULL_SMART));
    CHECK(!cfru_integration_init_battle_controllers(
        fake_init_controllers, &sBattlersCount, CFRU_BATTLE_LAYOUT_RAID_TRIPLE));
    CHECK(sControllerInitCalls == 0);
    CHECK(cfru_integration_raid_begin(1, 0, 1, 1, 100, 100, 5, 1));
    CHECK(cfru_integration_init_battle_controllers(
        fake_init_controllers, &sBattlersCount, CFRU_BATTLE_LAYOUT_RAID_TRIPLE));
    CHECK(sControllerInitCalls == 1 && sBattlersCount == 3);
    CHECK(cfru_integration_battle_end(CFRU_EXIT_ABORTED));
    return 0;
}

static int test_facility(void)
{
    cfru_u8 format;
    cfru_u8 rule;
    cfru_u8 effect;
    CHECK(cfru_integration_battle_begin(CFRU_AI_BASIC, CFRU_AI_FULL_SMART));
    for (format = 0; format < CFRU_FACILITY_FORMAT_COUNT; ++format)
    {
        for (rule = 0; rule < CFRU_FACILITY_RULE_COUNT; ++rule)
        {
            CHECK(cfru_integration_facility_begin(
                (CfruFacilityFormat)format, (CfruFacilityRule)rule));
            CHECK(!cfru_integration_facility_begin(
                (CfruFacilityFormat)format, (CfruFacilityRule)rule));
            for (effect = 0; effect < CFRU_PERSISTENT_EFFECT_COUNT; ++effect)
                CHECK(!cfru_integration_persistent_effect_allowed(
                    (CfruPersistentEffect)effect));
            CHECK(cfru_integration_facility_end());
            CHECK(cfru_integration_persistent_effect_allowed(CFRU_PERSIST_EXP));
        }
    }
    CHECK(cfru_integration_battle_end(CFRU_EXIT_FORFEIT));
    CHECK(!cfru_integration_state()->facility.active);
    return 0;
}

static int test_forwarders(void)
{
    static const cfru_u32 growth[] = {0, 0, 100, 300, 600};
    CfruStatInputs inputs = {
        1, 6, 2, {1, 2, 3, 4, 5, 6}, (cfru_u8)(1u << 3), 1
    };
    CfruCandyTarget target = {1, 0};
    CfruCandyResult candy;
    CfruTrainerMon base = {
        1, 2, {3, 4, 5, 6}, 7, 8, 0,
        {9, 10, 11, 12, 13, 14}, {0, 0, 0, 0, 0, 0}
    };
    CfruTrainerMon output = {0};
    CfruTrainerBuildPatch patch = {0};

    CHECK(cfru_integration_stat_inputs_are_valid(&inputs));
    CHECK(cfru_integration_effective_nature(&inputs) == 6);
    CHECK(cfru_integration_effective_iv(&inputs, 3) == 31);
    CHECK(cfru_integration_ability_slot(&inputs) == 2);
    CHECK(cfru_integration_receives_battle_exp(&inputs, 0));
    candy = cfru_integration_apply_exp_candy(&target, 350, 4, growth, 5);
    CHECK(candy.status == CFRU_CANDY_APPLIED && candy.consumed);
    CHECK(target.level == 3 && target.experience == 350);

    patch.present_fields = CFRU_TRAINER_FIELD_LEVEL | CFRU_TRAINER_FIELD_ITEM;
    patch.level = 50;
    patch.item = 998;
    patch.move_mask = 1;
    patch.moves[0] = 1062;
    CHECK(cfru_integration_trainer_build_apply(&output, &base, &patch));
    CHECK(output.level == 50 && output.item == 998 && output.moves[0] == 1062);
    CHECK(output.nature == base.nature && output.iv[5] == base.iv[5]);
    return 0;
}

static int test_mirage_all_exits(void)
{
    cfru_u8 exit_path;
    for (exit_path = 0; exit_path < CFRU_EXIT_COUNT; ++exit_path)
    {
        cfru_u16 item0 = 41;
        cfru_u16 item1 = 42;
        CHECK(cfru_integration_battle_begin(CFRU_AI_BASIC, CFRU_AI_FULL_SMART));
        CHECK(cfru_integration_mirage_begin(0, &item0, 900));
        CHECK(cfru_integration_mirage_begin(1, &item1, 901));
        CHECK(cfru_integration_mirage_current(0) == 900);
        CHECK(cfru_integration_mirage_set_battle_value(0, 0));
        item0 = 777;
        item1 = 778;
        if ((exit_path & 1u) == 0)
        {
            CHECK(cfru_integration_mirage_end(
                0, (CfruBattleExit)exit_path));
            CHECK(item0 == 41);
            CHECK(!cfru_integration_state()->mirage_items[0].active);
        }
        CHECK(cfru_integration_battle_end((CfruBattleExit)exit_path));
        CHECK(item0 == 41 && item1 == 42);
        CHECK(!cfru_integration_state()->mirage_items[0].active);
        CHECK(!cfru_integration_state()->mirage_items[1].active);
        CHECK(cfru_integration_state()->mirage_persistent_items[0] == (cfru_u16 *)0);
    }
    return 0;
}

static int test_raid(void)
{
    const CfruIntegrationState *state;
    CHECK(cfru_integration_battle_begin(CFRU_AI_BASIC, CFRU_AI_FULL_SMART));
    CHECK(!cfru_integration_select_mechanic(CFRU_MECHANIC_RAID_HIGH_DIFFICULTY, 1));
    CHECK(cfru_integration_raid_begin(
        CFRU_SIDE_OPPONENT, 0, (cfru_u8)((1u << 1) | (1u << 2)),
        2, 500, 500, 4, 1));
    state = cfru_integration_state();
    CHECK(state->raid.active && state->mechanic_mode_locked);
    CHECK(cfru_integration_mechanic_mode(CFRU_SIDE_PLAYER) == CFRU_MECHANIC_STANDARD);
    CHECK(cfru_integration_mechanic_mode(CFRU_SIDE_OPPONENT) == CFRU_MECHANIC_DYNAMAX);
    CHECK(cfru_integration_mechanic_is_forced(CFRU_SIDE_OPPONENT));
    CHECK(!cfru_integration_mechanic_is_forced(CFRU_SIDE_PLAYER));
    CHECK(cfru_integration_mechanic_try_use(CFRU_SIDE_OPPONENT, CFRU_MECHANIC_DYNAMAX));
    CHECK(!cfru_integration_mechanic_try_use(CFRU_SIDE_OPPONENT, CFRU_MECHANIC_DYNAMAX));
    CHECK(cfru_integration_raid_partner_is_active(1));
    CHECK(cfru_integration_raid_shields_remaining() == 2);
    CHECK(cfru_integration_raid_break_shield());
    CHECK(cfru_integration_raid_advance_turn());
    CHECK(cfru_integration_raid_set_boss_hp(0));
    CHECK(cfru_integration_raid_try_capture());
    CHECK(cfru_integration_raid_end(CFRU_RAID_END_CAPTURED));
    CHECK(!state->raid.active && !state->mechanic.active);
    CHECK(state->last_raid_end_reason == CFRU_RAID_END_CAPTURED);
    CHECK(state->last_raid_captured);
    CHECK(cfru_integration_battle_end(CFRU_EXIT_CAPTURED));
    CHECK(!state->battle_active && !state->raid.active && !state->mechanic.active);

    CHECK(cfru_integration_battle_begin(CFRU_AI_BASIC, CFRU_AI_FULL_SMART));
    CHECK(cfru_integration_raid_begin(1, 0, 0, 0, 1, 1, 1, 0));
    CHECK(cfru_integration_raid_advance_turn());
    CHECK(state->raid.end_reason == CFRU_RAID_END_TURN_LIMIT);
    CHECK(cfru_integration_raid_end(CFRU_RAID_END_TURN_LIMIT));
    CHECK(!state->raid.active);
    CHECK(cfru_integration_battle_end(CFRU_EXIT_LOST));
    return 0;
}

static int test_pending_raid_partner_mask(void)
{
    CfruPendingBattleCommand command;

    cfru_integration_pending_clear();
    CHECK(cfru_integration_pending_configure_raid(
        0, 0x2Au, 5, 4, CFRU_TRUE));
    CHECK(cfru_integration_pending_copy(&command));
    CHECK(command.raid_partner_mask == 0x2Au);
    cfru_integration_pending_clear();
    CHECK(cfru_integration_pending_restore(&command));
    cfru_integration_pending_clear();

    CHECK(!cfru_integration_pending_configure_raid(
        0, 0x0Fu, 5, 4, CFRU_TRUE));
    CHECK(!cfru_integration_pending_configure_raid(
        0, 0x80u, 5, 4, CFRU_TRUE));
    command.raid_partner_mask = 0x0Fu;
    CHECK(!cfru_integration_pending_restore(&command));
    command.raid_partner_mask = 0x80u;
    CHECK(!cfru_integration_pending_restore(&command));
    return 0;
}

static int test_begin_recovers_stale_battle(void)
{
    cfru_u16 item = 77;
    CHECK(cfru_integration_battle_begin(CFRU_AI_BASIC, CFRU_AI_BASIC));
    CHECK(cfru_integration_facility_begin(CFRU_FACILITY_SINGLE_3V3, CFRU_FACILITY_OU));
    CHECK(cfru_integration_mirage_begin(0, &item, 800));
    item = 999;
    CHECK(cfru_integration_battle_begin(CFRU_AI_SEMI_SMART, CFRU_AI_FULL_SMART));
    CHECK(item == 77);
    CHECK(!cfru_integration_state()->facility.active);
    CHECK(!cfru_integration_state()->mirage_items[0].active);
    CHECK(cfru_integration_state()->mechanic.battle_mode == CFRU_MECHANIC_STANDARD);
    CHECK(cfru_integration_ai_profile(CFRU_SIDE_PLAYER) == CFRU_AI_SEMI_SMART);
    CHECK(cfru_integration_battle_end(CFRU_EXIT_ABORTED));
    return 0;
}

static int test_pending_shadow_phase_lifecycle(void)
{
    CfruPendingBattleCommand command;

    cfru_integration_pending_clear();
    CHECK(cfru_integration_pending_configure(
        CFRU_AI_SEMI_SMART, CFRU_MECHANIC_MEGA));
    CHECK(cfru_integration_pending_take(&command));
    CHECK(cfru_integration_pending_mark_transferred());
    CHECK(cfru_integration_pending_is_transferred());
    CHECK(!cfru_integration_pending_configure(
        CFRU_AI_BASIC, CFRU_MECHANIC_STANDARD));
    CHECK(cfru_integration_pending_restore(&command));
    CHECK(cfru_integration_battle_begin(CFRU_AI_BASIC, command.ai_profile));
    CHECK(cfru_integration_pending_battle_is_active());
    CHECK(!cfru_integration_pending_configure(
        CFRU_AI_BASIC, CFRU_MECHANIC_STANDARD));
    CHECK(cfru_integration_battle_end(CFRU_EXIT_WON));
    CHECK(!cfru_integration_pending_battle_is_active());
    return 0;
}

int main(void)
{
    int result;
    result = test_begin_ai_mechanic(); if (result) return result;
    result = test_battle_controller_init_link(); if (result) return result;
    result = test_facility(); if (result) return result;
    result = test_forwarders(); if (result) return result;
    result = test_mirage_all_exits(); if (result) return result;
    result = test_raid(); if (result) return result;
    result = test_pending_raid_partner_mask(); if (result) return result;
    result = test_begin_recovers_stale_battle(); if (result) return result;
    result = test_pending_shadow_phase_lifecycle(); if (result) return result;
    return 0;
}
'''


class CfruIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.cc = os.environ.get("CC", "cc")
        if shutil.which(self.cc) is None:
            self.skipTest(f"C compiler not found: {self.cc}")

    def compile(self, output: Path, *extra: str) -> None:
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
                str(INTEGRATION_C),
                *extra,
                "-o",
                str(output),
            ],
            check=True,
            cwd=ROOT,
        )

    def test_all_exported_wrappers_and_cleanup(self):
        with tempfile.TemporaryDirectory(prefix="cfru-integration-") as temp_dir:
            harness = Path(temp_dir) / "integration_harness.c"
            executable = Path(temp_dir) / "integration_harness"
            harness.write_text(textwrap.dedent(HARNESS), encoding="utf-8")
            self.compile(executable, str(harness))
            subprocess.run([str(executable)], check=True, cwd=ROOT)

    def test_no_libc_or_upstream_undefined_symbols(self):
        with tempfile.TemporaryDirectory(prefix="cfru-integration-") as temp_dir:
            combined = Path(temp_dir) / "combined.o"
            runtime_obj = Path(temp_dir) / "runtime.o"
            integration_obj = Path(temp_dir) / "integration.o"
            common = [
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
            ]
            subprocess.run(common + [str(RUNTIME_C), "-o", str(runtime_obj)], check=True, cwd=ROOT)
            subprocess.run(common + [str(INTEGRATION_C), "-o", str(integration_obj)], check=True, cwd=ROOT)
            subprocess.run(
                [self.cc, "-nostdlib", "-r", str(runtime_obj), str(integration_obj), "-o", str(combined)],
                check=True,
                cwd=ROOT,
            )
            nm = shutil.which("nm")
            if nm is not None:
                result = subprocess.run(
                    [nm, "-u", str(combined)],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(result.stdout.strip(), "")


if __name__ == "__main__":
    unittest.main()
