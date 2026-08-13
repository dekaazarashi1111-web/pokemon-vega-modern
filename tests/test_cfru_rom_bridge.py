import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import textwrap
import unittest


ROOT = Path(__file__).resolve().parents[1]
OVERLAY = ROOT / "overlays" / "cfru"


DEFINES_H = r'''
#ifndef TEST_CFRU_DEFINES_H
#define TEST_CFRU_DEFINES_H

typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
typedef signed int s32;
typedef u8 bool8;

#define FALSE 0
#define TRUE 1

struct Pokemon
{
    u16 species;
    u16 hp;
    u16 maxHP;
    u16 item;
    u8 teratype;
};

struct NewBattleStruct
{
    u8 storage[4096];
};

u16 VarGet(u16 variable);
void VarSet(u16 variable, u16 value);
void *Memset(void *destination, u8 pattern, u32 size);
void *Calloc(u32 size);
u32 GetMonData(struct Pokemon *mon, s32 field, u8 *dst);

#define NULL ((void *)0)
#define SPECIES_NONE 0
#define SPECIES_EGG 412
#define MON_DATA_SPECIES2 65

#endif
'''


DEFINES_BATTLE_H = r'''
#ifndef TEST_CFRU_DEFINES_BATTLE_H
#define TEST_CFRU_DEFINES_BATTLE_H

#include "defines.h"

#define PARTY_SIZE 6
#define B_SIDE_PLAYER 0
#define B_SIDE_OPPONENT 1

#define BATTLE_TYPE_INGAME_PARTNER 0x00400000u
#define BATTLE_TYPE_DYNAMAX 0x40000000u
#define BATTLE_TYPE_TRAINER 0x00000008u
#define BATTLE_TYPE_FRONTIER 0x00000400u
#define BATTLE_TYPE_DOUBLE 0x00000001u
#define BATTLE_TYPE_LINK 0x00000002u
#define BATTLE_TYPE_MULTI 0x00000040u
#define BATTLE_TYPE_TWO_OPPONENTS 0x00008000u

#define B_OUTCOME_WON 0x1
#define B_OUTCOME_LOST 0x2
#define B_OUTCOME_DREW 0x3
#define B_OUTCOME_RAN 0x4
#define B_OUTCOME_PLAYER_TELEPORTED 0x5
#define B_OUTCOME_MON_FLED 0x6
#define B_OUTCOME_CAUGHT 0x7
#define B_OUTCOME_NO_SAFARI_BALLS 0x8
#define B_OUTCOME_FORFEITED 0x9
#define B_OUTCOME_MON_TELEPORTED 0xA
#define B_OUTCOME_LINK_BATTLE_RAN 0x80

#define AI_SCRIPT_CHECK_BAD_MOVE (1u << 0)
#define AI_SCRIPT_SEMI_SMART (1u << 1)
#define AI_SCRIPT_CHECK_GOOD_MOVE (1u << 2)

extern u32 gBattleTypeFlags;
extern u8 gBattleOutcome;
extern u8 gBattlersCount;
extern struct Pokemon gPlayerParty[PARTY_SIZE];
extern struct Pokemon gEnemyParty[PARTY_SIZE];
struct Trainer { u32 aiFlags; };
extern struct Trainer gTrainers[4];
extern u16 gTrainerBattleOpponent_A;
extern struct NewBattleStruct *gNewBS;

u8 GetBattlerSide(u8 battler);
#define SIDE(battler) GetBattlerSide(battler)

#endif
'''


FRONTIER_H = r'''
#ifndef TEST_CFRU_FRONTIER_H
#define TEST_CFRU_FRONTIER_H

#define BATTLE_FACILITY_MULTI_TRAINER_TID 0x396
#define RAID_BATTLE_MULTI_TRAINER_TID 0x398
#define BATTLE_TOWER_TID 0x399

#endif
'''


MULTI_H = r'''
#ifndef TEST_CFRU_MULTI_H
#define TEST_CFRU_MULTI_H

extern u16 gTrainerBattleOpponent_B;
extern u16 gTrainerBattlePartner;

#endif
'''


DYNAMAX_H = r'''
#ifndef TEST_CFRU_DYNAMAX_H
#define TEST_CFRU_DYNAMAX_H

#include "../../src/defines.h"

bool8 IsRaidBattle(void);
bool8 IsCatchableRaidBattle(void);
void TryRevertGigantamax(struct Pokemon *mon);

#endif
'''


FORM_CHANGE_H = r'''
#ifndef TEST_CFRU_FORM_CHANGE_H
#define TEST_CFRU_FORM_CHANGE_H

#include "../../src/defines.h"
bool8 TryFormRevert(struct Pokemon *mon);

#endif
'''


MEGA_H = r'''
#ifndef TEST_CFRU_MEGA_H
#define TEST_CFRU_MEGA_H

#include "../../src/defines.h"
void TryRevertMega(struct Pokemon *mon);

#endif
'''


TERASTAL_H = r'''
#ifndef TEST_CFRU_TERASTAL_H
#define TEST_CFRU_TERASTAL_H

#include "../../src/defines.h"
bool8 TryRevertTerastalForm(struct Pokemon *mon);
u8 GetSpeciesTeraType(u16 species);

#endif
'''


RANDOM_H = r'''
#ifndef TEST_CFRU_RANDOM_H
#define TEST_CFRU_RANDOM_H

#include "../src/defines.h"
extern u32 gRngValue;

#endif
'''


VARS_H = r'''
#ifndef TEST_CFRU_VARS_H
#define TEST_CFRU_VARS_H
#define VAR_TEMP_E 0x400E
#define VAR_TEMP_F 0x400F
#define VAR_TEMP_0 0x4000
#define VAR_TEMP_1 0x4001
#define VAR_TEMP_2 0x4002
#define VAR_TEMP_3 0x4003
#define VAR_TEMP_4 0x4004
#define VAR_TEMP_5 0x4005
#define VAR_TEMP_6 0x4006
#define VAR_TEMP_7 0x4007
#define VAR_TEMP_8 0x4008
#define VAR_TEMP_9 0x4009
#define VAR_TEMP_A 0x400A
#define VAR_TEMP_B 0x400B
#endif
'''


HARNESS = r'''
#include "rom_bridge.h"
#include "../include/constants/vars.h"

#define CHECK(condition) do { if (!(condition)) return __LINE__; } while (0)

u32 gBattleTypeFlags;
u8 gBattleOutcome;
u8 gBattlersCount;
struct Pokemon gEnemyParty[PARTY_SIZE];
struct Pokemon gPlayerParty[PARTY_SIZE];
struct Trainer gTrainers[4];
u16 gTrainerBattleOpponent_A;
u16 gTrainerBattleOpponent_B;
u16 gTrainerBattlePartner;
struct NewBattleStruct *gNewBS;
u32 gRngValue;
static struct NewBattleStruct sNewBattleStorage;

static bool8 sRaidBattle;
static bool8 sCatchableRaid;

u16 VarGet(u16 variable)
{
    (void)variable;
    return 0;
}

void VarSet(u16 variable, u16 value)
{
    (void)variable;
    (void)value;
}

void *Memset(void *destination, u8 pattern, u32 size)
{
    u8 *bytes = (u8 *)destination;
    u32 index;
    for (index = 0; index < size; ++index)
        bytes[index] = pattern;
    return destination;
}

void *Calloc(u32 size)
{
    if (size != sizeof(sNewBattleStorage))
        return (void *)0;
    Memset(&sNewBattleStorage, 0, sizeof(sNewBattleStorage));
    return &sNewBattleStorage;
}

u8 GetBattlerSide(u8 battler)
{
    return (u8)(battler & 1u);
}

bool8 IsRaidBattle(void)
{
    return sRaidBattle;
}

bool8 IsCatchableRaidBattle(void)
{
    return sCatchableRaid;
}

u32 GetMonData(struct Pokemon *mon, s32 field, u8 *dst)
{
    (void)field;
    (void)dst;
    return mon->species;
}

u8 GetSpeciesTeraType(u16 species)
{
    ++gRngValue;
    return (u8)(species % 25u);
}

bool8 TryFormRevert(struct Pokemon *mon)
{
    (void)mon;
    return FALSE;
}

void TryRevertMega(struct Pokemon *mon)
{
    (void)mon;
}

void TryRevertGigantamax(struct Pokemon *mon)
{
    (void)mon;
}

bool8 TryRevertTerastalForm(struct Pokemon *mon)
{
    (void)mon;
    return FALSE;
}

static void reset_upstream(void)
{
    gBattleTypeFlags = 0;
    gBattleOutcome = 0;
    gBattlersCount = 0;
    gEnemyParty[0].hp = 100;
    gEnemyParty[0].maxHP = 100;
    gEnemyParty[0].species = 10;
    gPlayerParty[0].item = 41;
    gPlayerParty[0].species = 4;
    gEnemyParty[0].item = 77;
    gRngValue = 0x12345678u;
    sRaidBattle = FALSE;
    sCatchableRaid = FALSE;
    cfru_integration_pending_clear();
    Memset(&sNewBattleStorage, 0, sizeof(sNewBattleStorage));
    gNewBS = &sNewBattleStorage;
    gTrainerBattleOpponent_A = 0;
    gTrainers[0].aiFlags = 0;
}

static int test_normal_begin_timing_and_ai(void)
{
    const CfruIntegrationState *state;

    reset_upstream();
    CHECK(VegaBattlePolicyBegin());
    state = cfru_integration_state();
    CHECK(state->battle_active);
    CHECK(state->mechanic.battle_mode == CFRU_MECHANIC_STANDARD);
    CHECK(!state->raid.active);

    /* RAM clear precedes controller setup: zero is expected here. */
    CHECK(gBattlersCount == 0);
    CHECK(VegaBattlePolicyResolveAIProfileBits(0, 0x55u) == 0x55u);

    /* InitBattleControllers later owns 2 for a normal single battle. */
    gBattlersCount = 2;
    CHECK(VegaBattlePolicyResolveAIProfileBits(0, 0) == AI_SCRIPT_CHECK_BAD_MOVE);
    CHECK(VegaBattlePolicyResolveAIProfileBits(1, 0) == AI_SCRIPT_CHECK_BAD_MOVE);
    CHECK(VegaBattlePolicyResolveAIProfileBits(0, 3) == 3);
    CHECK(VegaBattlePolicyResolveAIProfileBits(1, 7) == 7);
    CHECK(VegaBattlePolicyResolveAIProfileBits(1, 1u << 30) == (1u << 30));
    CHECK(VegaBattlePolicyResolveAIProfileBits(2, 0x55u) == 0x55u);
    CHECK(!VegaBattlePolicyCanMega(0, TRUE));
    CHECK(!VegaBattlePolicyCanZ(0, TRUE));
    CHECK(!VegaBattlePolicyCanDynamax(0, TRUE));
    CHECK(!VegaBattlePolicyCanTera(0, TRUE));

    gBattleOutcome = B_OUTCOME_WON;
    CHECK(VegaBattlePolicyEnd());
    CHECK(!state->battle_active && !state->mechanic.active);
    CHECK(VegaBattlePolicyResolveAIProfileBits(0, 0x55u) == 0x55u);
    CHECK(!VegaBattlePolicyEnd());
    return 0;
}

static int test_trainer_profile_and_pending_mechanic_adapter(void)
{
    const CfruIntegrationState *state;

    reset_upstream();
    gBattleTypeFlags = BATTLE_TYPE_TRAINER;
    gTrainers[0].aiFlags = 7;
    CHECK(VegaBattlePolicyBegin());
    state = cfru_integration_state();
    CHECK(state->ai_profile[CFRU_SIDE_OPPONENT] == CFRU_AI_FULL_SMART);
    gBattlersCount = 2;
    CHECK(VegaBattlePolicyResolveAIProfileBits(1, 7) == CFRU_AI_FULL_SMART);
    gBattleOutcome = B_OUTCOME_WON;
    CHECK(VegaBattlePolicyEnd());

    reset_upstream();
    gBattleTypeFlags = BATTLE_TYPE_TRAINER;
    gTrainers[0].aiFlags = 1;
    CHECK(VegaConfigureNextBattlePolicy(
        CFRU_AI_SEMI_SMART, CFRU_MECHANIC_MEGA));
    CHECK(VegaBattlePolicyPrepareStorage());
    CHECK(VegaBattlePolicyBegin());
    state = cfru_integration_state();
    CHECK(state->ai_profile[CFRU_SIDE_OPPONENT] == CFRU_AI_SEMI_SMART);
    CHECK(state->mechanic.battle_mode == CFRU_MECHANIC_MEGA);
    CHECK(!state->pending.active);
    gBattlersCount = 2;
    CHECK(VegaBattlePolicyCanMega(0, TRUE));
    CHECK(!VegaBattlePolicyCanZ(0, TRUE));
    gBattleOutcome = B_OUTCOME_WON;
    CHECK(VegaBattlePolicyEnd());

    CHECK(VegaNormalizeTrainerAIProfile(1) == CFRU_AI_BASIC);
    CHECK(VegaNormalizeTrainerAIProfile(3) == CFRU_AI_SEMI_SMART);
    CHECK(VegaNormalizeTrainerAIProfile(5) == CFRU_AI_FULL_SMART);
    CHECK(VegaNormalizeTrainerAIProfile(7) == CFRU_AI_FULL_SMART);
    return 0;
}

static int test_battle_local_tera_type_derivation_and_restore(void)
{
    const CfruIntegrationState *state;
    u32 rng_before;

    reset_upstream();
    gBattleTypeFlags = BATTLE_TYPE_TRAINER;
    gPlayerParty[0].teratype = 17;
    gEnemyParty[0].teratype = 19;
    rng_before = gRngValue;
    CHECK(VegaConfigureNextBattlePolicy(
        CFRU_AI_BASIC, CFRU_MECHANIC_TERASTAL));
    CHECK(VegaBattlePolicyPrepareStorage());
    CHECK(VegaBattlePolicyBegin());
    state = cfru_integration_state();
    CHECK(state->tera_type_backup.active);
    CHECK(state->tera_type_backup.player[0] == 17);
    CHECK(state->tera_type_backup.opponent[0] == 19);
    CHECK(gPlayerParty[0].teratype == 4);
    CHECK(gEnemyParty[0].teratype == 10);
    CHECK(gRngValue == rng_before);

    /* Capture restores only the selected opponent slot before storage copy. */
    gEnemyParty[0].teratype = 22;
    VegaBattlePolicyRestoreCapturedTeraType(&gEnemyParty[0]);
    CHECK(gEnemyParty[0].teratype == 19);
    CHECK(state->tera_type_backup.active);

    gBattleOutcome = B_OUTCOME_WON;
    CHECK(VegaBattlePolicyEnd());
    CHECK(gPlayerParty[0].teratype == 17);
    CHECK(gEnemyParty[0].teratype == 19);
    CHECK(!state->tera_type_backup.active);
    return 0;
}

typedef bool8 (*CanMechanic)(u8 battler, bool8 upstream_allowed);
typedef bool8 (*MarkMechanic)(u8 battler);

static int exercise_mechanic(
    CfruMechanicMode mode,
    CanMechanic can_use,
    MarkMechanic mark_used
)
{
    reset_upstream();
    CHECK(VegaBattlePolicyBegin());
    CHECK(cfru_integration_select_mechanic(mode, CFRU_SIDE_OPPONENT));
    gBattlersCount = 2;
    CHECK(!can_use(0, FALSE));
    CHECK(can_use(0, TRUE));
    CHECK(mark_used(0));
    CHECK(!can_use(0, TRUE));
    CHECK(!mark_used(0));
    CHECK(can_use(1, TRUE));
    CHECK(mark_used(1));
    CHECK(!can_use(2, TRUE));
    CHECK(!mark_used(2));
    gBattleOutcome = B_OUTCOME_WON;
    CHECK(VegaBattlePolicyEnd());
    return 0;
}

static int test_mechanic_side_gates(void)
{
    int result;

    result = exercise_mechanic(
        CFRU_MECHANIC_MEGA,
        VegaBattlePolicyCanMega,
        VegaBattlePolicyMarkMega);
    if (result)
        return result;
    result = exercise_mechanic(
        CFRU_MECHANIC_Z_MOVE,
        VegaBattlePolicyCanZ,
        VegaBattlePolicyMarkZ);
    if (result)
        return result;
    result = exercise_mechanic(
        CFRU_MECHANIC_DYNAMAX,
        VegaBattlePolicyCanDynamax,
        VegaBattlePolicyMarkDynamax);
    if (result)
        return result;
    return exercise_mechanic(
        CFRU_MECHANIC_TERASTAL,
        VegaBattlePolicyCanTera,
        VegaBattlePolicyMarkTera);
}

static int test_raid_begin_and_cleanup(void)
{
    const CfruIntegrationState *state;

    reset_upstream();
    sRaidBattle = TRUE;
    /* IsRaidBattle without the post-clear Dynamax flag is not a ready Raid. */
    CHECK(VegaBattlePolicyBegin());
    CHECK(!cfru_integration_state()->raid.active);
    CHECK(cfru_integration_state()->mechanic.battle_mode
          == CFRU_MECHANIC_STANDARD);
    gBattleOutcome = B_OUTCOME_RAN;
    CHECK(VegaBattlePolicyEnd());

    reset_upstream();
    sRaidBattle = TRUE;
    sCatchableRaid = TRUE;
    gEnemyParty[0].hp = 300;
    gEnemyParty[0].maxHP = 500;
    CHECK(VegaConfigureNextRaid(
        VEGA_RAID_BOSS_PARTY_INDEX,
        VEGA_RAID_FIRST_PARTNER_MASK,
        VEGA_RAID_INITIAL_SHIELDS,
        VEGA_RAID_DEFAULT_TURN_LIMIT,
        TRUE));
    CHECK(VegaBattlePolicyPrepareStorage());
    CHECK(VegaBattlePolicyBegin());
    state = cfru_integration_state();
    CHECK(state->raid.active);
    CHECK(state->raid.boss_side == CFRU_SIDE_OPPONENT);
    CHECK(state->raid.boss_party_index == VEGA_RAID_BOSS_PARTY_INDEX);
    CHECK(state->raid.partner_mask == VEGA_RAID_FIRST_PARTNER_MASK);
    CHECK(state->raid.shield_total == VEGA_RAID_INITIAL_SHIELDS);
    CHECK(state->raid.boss_hp == 300 && state->raid.boss_max_hp == 500);
    CHECK(state->raid.turn_limit == VEGA_RAID_DEFAULT_TURN_LIMIT);
    CHECK(state->raid.capture_allowed);
    CHECK(state->mechanic.battle_mode
          == CFRU_MECHANIC_RAID_HIGH_DIFFICULTY);
    CHECK(state->mechanic.effective_mode[CFRU_SIDE_PLAYER]
          == CFRU_MECHANIC_STANDARD);
    CHECK(state->mechanic.effective_mode[CFRU_SIDE_OPPONENT]
          == CFRU_MECHANIC_DYNAMAX);
    CHECK(state->mechanic.forced[CFRU_SIDE_OPPONENT]);

    /* Raid controller setup later owns the fixed three-battler count. */
    CHECK(gBattlersCount == 0);
    gBattlersCount = 3;
    CHECK(VegaBattlePolicyResolveAIProfileBits(1, 0)
          == (AI_SCRIPT_CHECK_BAD_MOVE | AI_SCRIPT_CHECK_GOOD_MOVE));
    CHECK(VegaBattlePolicyResolveAIProfileBits(1, 3) == 3);
    CHECK(VegaBattlePolicyCanDynamax(1, TRUE));
    CHECK(!VegaBattlePolicyCanDynamax(2, TRUE));
    CHECK(VegaBattlePolicyMarkDynamax(1));
    CHECK(!VegaBattlePolicyCanDynamax(1, TRUE));
    CHECK((gBattleTypeFlags & (BATTLE_TYPE_DYNAMAX
                              | BATTLE_TYPE_DOUBLE
                              | BATTLE_TYPE_INGAME_PARTNER))
          == (BATTLE_TYPE_DYNAMAX
              | BATTLE_TYPE_DOUBLE
              | BATTLE_TYPE_INGAME_PARTNER));
    gBattleOutcome = B_OUTCOME_CAUGHT;
    CHECK(VegaBattlePolicyEnd());
    CHECK((gBattleTypeFlags & (BATTLE_TYPE_DYNAMAX
                              | BATTLE_TYPE_DOUBLE
                              | BATTLE_TYPE_INGAME_PARTNER)) == 0);
    CHECK(!state->battle_active && !state->raid.active);
    CHECK(!state->mechanic.active);
    CHECK(state->last_raid_end_reason == CFRU_RAID_END_CAPTURED);
    CHECK(state->last_raid_captured);

    reset_upstream();
    sRaidBattle = TRUE;
    gEnemyParty[0].hp = 0;
    CHECK(VegaConfigureNextRaid(
        VEGA_RAID_BOSS_PARTY_INDEX,
        0,
        VEGA_RAID_INITIAL_SHIELDS,
        VEGA_RAID_DEFAULT_TURN_LIMIT,
        FALSE));
    CHECK(VegaBattlePolicyPrepareStorage());
    CHECK(!VegaBattlePolicyBegin());
    CHECK(!cfru_integration_state()->battle_active);
    CHECK(!cfru_integration_state()->raid.active);
    return 0;
}

static int test_outcome_mapping_and_all_state_cleanup(void)
{
    cfru_u16 persistent_item = 77;

    CHECK(VegaBattlePolicyMapOutcome(B_OUTCOME_WON) == CFRU_EXIT_WON);
    CHECK(VegaBattlePolicyMapOutcome(B_OUTCOME_LOST) == CFRU_EXIT_LOST);
    CHECK(VegaBattlePolicyMapOutcome(B_OUTCOME_DREW) == CFRU_EXIT_LOST);
    CHECK(VegaBattlePolicyMapOutcome(B_OUTCOME_NO_SAFARI_BALLS) == CFRU_EXIT_LOST);
    CHECK(VegaBattlePolicyMapOutcome(B_OUTCOME_RAN) == CFRU_EXIT_RAN);
    CHECK(VegaBattlePolicyMapOutcome(B_OUTCOME_PLAYER_TELEPORTED) == CFRU_EXIT_RAN);
    CHECK(VegaBattlePolicyMapOutcome(B_OUTCOME_MON_FLED) == CFRU_EXIT_RAN);
    CHECK(VegaBattlePolicyMapOutcome(B_OUTCOME_MON_TELEPORTED) == CFRU_EXIT_RAN);
    CHECK(VegaBattlePolicyMapOutcome(B_OUTCOME_FORFEITED) == CFRU_EXIT_FORFEIT);
    CHECK(VegaBattlePolicyMapOutcome(B_OUTCOME_CAUGHT) == CFRU_EXIT_CAPTURED);
    CHECK(VegaBattlePolicyMapOutcome(B_OUTCOME_LINK_BATTLE_RAN | B_OUTCOME_WON)
          == CFRU_EXIT_RAN);
    CHECK(VegaBattlePolicyMapOutcome(0) == CFRU_EXIT_ERROR);
    CHECK(VegaBattlePolicyMapOutcome(0x7Fu) == CFRU_EXIT_ERROR);

    reset_upstream();
    CHECK(VegaBattlePolicyBegin());
    CHECK(cfru_integration_facility_begin(
        CFRU_FACILITY_DOUBLE_4V4, CFRU_FACILITY_GS));
    CHECK(cfru_integration_mirage_begin(0, &persistent_item, 900));
    persistent_item = 999;
    gBattleOutcome = B_OUTCOME_FORFEITED;
    CHECK(VegaBattlePolicyEnd());
    CHECK(persistent_item == 77);
    CHECK(!cfru_integration_state()->battle_active);
    CHECK(!cfru_integration_state()->facility.active);
    CHECK(!cfru_integration_state()->mirage_items[0].active);
    CHECK(cfru_integration_state()->mirage_persistent_items[0]
          == (cfru_u16 *)0);
    return 0;
}

static int test_pending_mirage_virtualizes_only_opponent_item(void)
{
    reset_upstream();
    CHECK(VegaConfigureNextMirageItem(0, 900));
    CHECK(VegaBattlePolicyPrepareStorage());
    CHECK(VegaBattlePolicyBegin());
    CHECK(gPlayerParty[0].item == 41);
    CHECK(gEnemyParty[0].item == 900);
    CHECK(cfru_integration_mirage_current(0) == 900);
    gEnemyParty[0].item = 777;
    CHECK(cfru_integration_mirage_set_battle_value(0, 777));
    gBattleOutcome = B_OUTCOME_RAN;
    CHECK(VegaBattlePolicyEnd());
    CHECK(gPlayerParty[0].item == 41);
    CHECK(gEnemyParty[0].item == 77);
    return 0;
}

static int test_prebattle_shadow_pending_facility_command(void)
{
    const CfruIntegrationState *state;

    reset_upstream();
    gNewBS = (void *)0;
    CHECK(VegaConfigureNextFacility(
        CFRU_FACILITY_NPC_PARTNER_MULTI,
        CFRU_FACILITY_CAMOMONS,
        CFRU_MECHANIC_TERASTAL));
    state = cfru_integration_state();
    CHECK(gNewBS == (void *)0);
    CHECK(cfru_integration_pending_is_active());
    CHECK(cfru_integration_pending_facility_is_active());
    CHECK(VegaFacilityStateIsActive());
    CHECK(VegaFacilityStateGet(1) == 2);
    CHECK(VegaFacilityStateGet(2) == 50);
    VegaFacilityStateSet(8, 123);
    CHECK(VegaFacilityStateGet(8) == 123);

    /* Upstream RAM clear keeps only the allocator-owned one-shot command. */
    CHECK(VegaBattlePolicyPrepareStorage());
    CHECK(cfru_integration_pending_is_transferred());
    CHECK(cfru_integration_state()->pending.active);
    CHECK(VegaFacilityStateIsActive());
    CHECK(VegaFacilityStateGet(8) == 123);
    VegaFacilityStateSet(10, 456);
    CHECK(VegaFacilityStateGet(10) == 456);
    CHECK(VegaBattlePolicyBegin());
    state = cfru_integration_state();
    CHECK(!state->pending.active);
    CHECK(state->battle_active && state->facility.active);
    CHECK(state->facility.format == CFRU_FACILITY_NPC_PARTNER_MULTI);
    CHECK(state->facility.rule == CFRU_FACILITY_CAMOMONS);
    CHECK(cfru_integration_facility_state_get(8) == 123);
    CHECK(cfru_integration_facility_state_get(10) == 456);
    CHECK(state->mechanic.battle_mode == CFRU_MECHANIC_TERASTAL);
    CHECK((gBattleTypeFlags & BATTLE_TYPE_FRONTIER) != 0);
    gBattleOutcome = B_OUTCOME_WON;
    CHECK(VegaBattlePolicyEnd());
    CHECK(!state->battle_active && !state->facility.active);
    return 0;
}

static int test_stale_battle_pointer_does_not_hide_next_raid(void)
{
    reset_upstream();
    CHECK(VegaBattlePolicyBegin());
    gBattleOutcome = B_OUTCOME_WON;
    CHECK(VegaBattlePolicyEnd());
    CHECK(gNewBS != (void *)0);

    sRaidBattle = TRUE;
    sCatchableRaid = TRUE;
    CHECK(VegaConfigureNextRaid(0, 0, 2, 4, TRUE));
    CHECK(VegaBattlePolicyIsRaid());
    CHECK(VegaBattlePolicyRaidCaptureAllowed());
    CHECK(VegaBattlePolicyPrepareStorage());
    CHECK(VegaBattlePolicyIsRaid());
    CHECK(VegaBattlePolicyRaidCaptureAllowed());
    CHECK(VegaBattlePolicyBegin());
    CHECK(VegaBattlePolicyIsRaid());
    gBattleOutcome = B_OUTCOME_RAN;
    CHECK(VegaBattlePolicyEnd());
    return 0;
}

int main(void)
{
    int result;

    result = test_normal_begin_timing_and_ai();
    if (result)
        return result;
    result = test_mechanic_side_gates();
    if (result)
        return result;
    result = test_trainer_profile_and_pending_mechanic_adapter();
    if (result)
        return result;
    result = test_battle_local_tera_type_derivation_and_restore();
    if (result)
        return result;
    result = test_raid_begin_and_cleanup();
    if (result)
        return result;
    result = test_prebattle_shadow_pending_facility_command();
    if (result)
        return result;
    result = test_stale_battle_pointer_does_not_hide_next_raid();
    if (result)
        return result;
    result = test_pending_mirage_virtualizes_only_opponent_item();
    if (result)
        return result;
    return test_outcome_mapping_and_all_state_cleanup();
}
'''


class CfruRomBridgeTests(unittest.TestCase):
    def setUp(self):
        self.cc = os.environ.get("CC", "cc")
        if shutil.which(self.cc) is None:
            self.skipTest(f"C compiler not found: {self.cc}")

    def make_sandbox(self, root: Path) -> tuple[Path, Path]:
        src = root / "src"
        include_new = root / "include" / "new"
        src.mkdir(parents=True)
        include_new.mkdir(parents=True)
        constants = root / "include" / "constants"
        constants.mkdir(parents=True)
        for name in (
            "runtime.h",
            "runtime.c",
            "integration.h",
            "integration.c",
            "rom_bridge.h",
            "rom_bridge.c",
        ):
            shutil.copy2(OVERLAY / name, src / name)
        (src / "defines.h").write_text(
            textwrap.dedent(DEFINES_H), encoding="utf-8"
        )
        (src / "defines_battle.h").write_text(
            textwrap.dedent(DEFINES_BATTLE_H), encoding="utf-8"
        )
        (include_new / "dynamax.h").write_text(
            textwrap.dedent(DYNAMAX_H), encoding="utf-8"
        )
        (include_new / "form_change.h").write_text(
            textwrap.dedent(FORM_CHANGE_H), encoding="utf-8"
        )
        (include_new / "frontier.h").write_text(
            textwrap.dedent(FRONTIER_H), encoding="utf-8"
        )
        (include_new / "mega.h").write_text(
            textwrap.dedent(MEGA_H), encoding="utf-8"
        )
        (include_new / "multi.h").write_text(
            textwrap.dedent(MULTI_H), encoding="utf-8"
        )
        (include_new / "terastal.h").write_text(
            textwrap.dedent(TERASTAL_H), encoding="utf-8"
        )
        (root / "include" / "random.h").write_text(
            textwrap.dedent(RANDOM_H), encoding="utf-8"
        )
        (constants / "vars.h").write_text(
            textwrap.dedent(VARS_H), encoding="utf-8"
        )
        harness = src / "rom_bridge_harness.c"
        harness.write_text(textwrap.dedent(HARNESS), encoding="utf-8")
        return src, harness

    @staticmethod
    def common_flags(src: Path) -> list[str]:
        return [
            "-std=c11",
            "-Wall",
            "-Wextra",
            "-Werror",
            "-pedantic",
            "-ffreestanding",
            "-fno-builtin",
            "-I",
            str(src),
        ]

    def test_fixed_source_sandbox_runtime_contract(self):
        with tempfile.TemporaryDirectory(prefix="cfru-rom-bridge-") as temp_dir:
            root = Path(temp_dir)
            src, harness = self.make_sandbox(root)
            executable = root / "rom_bridge_harness"
            subprocess.run(
                [
                    self.cc,
                    *self.common_flags(src),
                    str(src / "runtime.c"),
                    str(src / "integration.c"),
                    str(src / "rom_bridge.c"),
                    str(harness),
                    "-o",
                    str(executable),
                ],
                check=True,
                cwd=root,
            )
            subprocess.run([str(executable)], check=True, cwd=root)

    def test_rom_object_references_real_integration_contract(self):
        nm = shutil.which("nm")
        if nm is None:
            self.skipTest("nm not found")

        with tempfile.TemporaryDirectory(prefix="cfru-rom-bridge-") as temp_dir:
            root = Path(temp_dir)
            src, _ = self.make_sandbox(root)
            bridge_object = root / "rom_bridge.o"
            subprocess.run(
                [
                    self.cc,
                    *self.common_flags(src),
                    "-c",
                    str(src / "rom_bridge.c"),
                    "-o",
                    str(bridge_object),
                ],
                check=True,
                cwd=root,
            )
            result = subprocess.run(
                [nm, "-u", str(bridge_object)],
                check=True,
                capture_output=True,
                text=True,
            )
            undefined = {line.split()[-1] for line in result.stdout.splitlines() if line.strip()}
            required = {
                "GetBattlerSide",
                "cfru_integration_ai_profile",
                "cfru_integration_battle_begin",
                "cfru_integration_battle_end",
                "cfru_integration_mechanic_can_use",
                "cfru_integration_mechanic_try_use",
                "cfru_integration_raid_begin",
                "cfru_integration_pending_configure_raid",
                "gBattleOutcome",
                "gBattleTypeFlags",
                "gBattlersCount",
                "gEnemyParty",
            }
            self.assertTrue(required <= undefined, sorted(undefined))
            self.assertFalse(
                undefined & {"malloc", "calloc", "free", "memcpy", "memset"},
                sorted(undefined),
            )

    def test_arm7tdmi_thumb_syntax_when_toolchain_is_available(self):
        arm_cc = shutil.which("arm-none-eabi-gcc")
        if arm_cc is None:
            self.skipTest("arm-none-eabi-gcc not found")

        with tempfile.TemporaryDirectory(prefix="cfru-rom-bridge-arm-") as temp_dir:
            root = Path(temp_dir)
            src, _ = self.make_sandbox(root)
            subprocess.run(
                [
                    arm_cc,
                    *self.common_flags(src),
                    "-mcpu=arm7tdmi",
                    "-mthumb",
                    "-mthumb-interwork",
                    "-c",
                    str(src / "rom_bridge.c"),
                    "-o",
                    str(root / "rom_bridge.arm.o"),
                ],
                check=True,
                cwd=root,
            )


if __name__ == "__main__":
    unittest.main()
