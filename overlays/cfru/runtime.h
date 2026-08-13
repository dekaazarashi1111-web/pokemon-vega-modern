#ifndef POKEMON_VEGA_CFRU_RUNTIME_H
#define POKEMON_VEGA_CFRU_RUNTIME_H

/*
 * T06 battle-side policy ABI.
 *
 * This header deliberately has no dependency on libc or the upstream CFRU
 * headers.  The integration layer may translate these fixed-width values to
 * the concrete CFRU structures when the ROM hooks are installed.
 */
typedef unsigned char cfru_u8;
typedef unsigned short cfru_u16;
typedef unsigned int cfru_u32;

_Static_assert(sizeof(cfru_u8) == 1, "cfru_u8 must be 8-bit");
_Static_assert(sizeof(cfru_u16) == 2, "cfru_u16 must be 16-bit");
_Static_assert(sizeof(cfru_u32) == 4, "cfru_u32 must be 32-bit");

enum {
    CFRU_FALSE = 0,
    CFRU_TRUE = 1,
    CFRU_SIDE_PLAYER = 0,
    CFRU_SIDE_OPPONENT = 1,
    CFRU_SIDE_COUNT = 2,
    CFRU_STAT_COUNT = 6,
    CFRU_MOVE_SLOT_COUNT = 4,
    CFRU_PARTY_SIZE = 6,
    CFRU_NATURE_COUNT = 25,
    CFRU_ABILITY_SLOT_COUNT = 3,
    CFRU_ABILITY_COUNT = 312,
    CFRU_ITEM_COUNT = 999,
    CFRU_MOVE_COUNT = 1063,
    CFRU_MAX_LEVEL = 100,
    CFRU_NATURE_UNSET = 0xFF
};

typedef enum CfruAiProfile {
    CFRU_AI_BASIC = 1,
    CFRU_AI_SEMI_SMART = 3,
    CFRU_AI_FULL_SMART = 5
} CfruAiProfile;

cfru_u8 cfru_ai_profile_is_valid(cfru_u8 profile);
cfru_u8 cfru_ai_profile_bits(CfruAiProfile profile);

typedef enum CfruMechanicMode {
    CFRU_MECHANIC_STANDARD = 0,
    CFRU_MECHANIC_MEGA = 1,
    CFRU_MECHANIC_Z_MOVE = 2,
    CFRU_MECHANIC_DYNAMAX = 3,
    CFRU_MECHANIC_TERASTAL = 4,
    CFRU_MECHANIC_RAID_HIGH_DIFFICULTY = 5,
    CFRU_MECHANIC_MODE_COUNT = 6
} CfruMechanicMode;

typedef struct CfruMechanicState {
    cfru_u8 active;
    cfru_u8 battle_mode;
    cfru_u8 effective_mode[CFRU_SIDE_COUNT];
    cfru_u8 used[CFRU_SIDE_COUNT];
    cfru_u8 forced[CFRU_SIDE_COUNT];
} CfruMechanicState;

cfru_u8 cfru_mechanic_begin(
    CfruMechanicState *state,
    CfruMechanicMode mode,
    cfru_u8 raid_boss_side
);
cfru_u8 cfru_mechanic_can_use(
    const CfruMechanicState *state,
    cfru_u8 side,
    CfruMechanicMode requested_mode
);
cfru_u8 cfru_mechanic_try_use(
    CfruMechanicState *state,
    cfru_u8 side,
    CfruMechanicMode requested_mode
);
cfru_u8 cfru_mechanic_is_forced(const CfruMechanicState *state, cfru_u8 side);
void cfru_mechanic_cleanup(CfruMechanicState *state);

typedef struct CfruStatInputs {
    cfru_u8 stored_nature;
    cfru_u8 mint_nature;
    cfru_u8 ability_slot;
    cfru_u8 iv[CFRU_STAT_COUNT];
    cfru_u8 hyper_trained_mask;
    cfru_u8 exp_share_enabled;
} CfruStatInputs;

cfru_u8 cfru_stat_inputs_are_valid(const CfruStatInputs *inputs);
cfru_u8 cfru_stat_effective_nature(const CfruStatInputs *inputs);
cfru_u8 cfru_stat_effective_iv(const CfruStatInputs *inputs, cfru_u8 stat_index);
cfru_u8 cfru_stat_ability_slot(const CfruStatInputs *inputs);
cfru_u8 cfru_stat_receives_battle_exp(const CfruStatInputs *inputs, cfru_u8 participated);

typedef struct CfruCandyTarget {
    cfru_u8 level;
    cfru_u32 experience;
} CfruCandyTarget;

typedef enum CfruCandyStatus {
    CFRU_CANDY_INVALID = 0,
    CFRU_CANDY_APPLIED = 1,
    CFRU_CANDY_NO_EFFECT = 2,
    CFRU_CANDY_AT_CAP = 3
} CfruCandyStatus;

typedef struct CfruCandyResult {
    cfru_u8 status;
    cfru_u8 consumed;
    cfru_u8 levels_gained;
    cfru_u8 reached_cap;
    cfru_u32 experience_gained;
} CfruCandyResult;

CfruCandyResult cfru_apply_exp_candy(
    CfruCandyTarget *selected_target,
    cfru_u32 candy_experience,
    cfru_u8 max_level,
    const cfru_u32 *experience_for_level,
    cfru_u16 experience_table_count
);

typedef struct CfruTrainerMon {
    cfru_u16 species;
    cfru_u16 item;
    cfru_u16 moves[CFRU_MOVE_SLOT_COUNT];
    cfru_u8 level;
    cfru_u8 nature;
    cfru_u8 ability_slot;
    cfru_u8 iv[CFRU_STAT_COUNT];
    cfru_u8 ev[CFRU_STAT_COUNT];
} CfruTrainerMon;

enum {
    CFRU_TRAINER_FIELD_LEVEL = 1u << 0,
    CFRU_TRAINER_FIELD_NATURE = 1u << 1,
    CFRU_TRAINER_FIELD_ABILITY_SLOT = 1u << 2,
    CFRU_TRAINER_FIELD_ITEM = 1u << 3,
    CFRU_TRAINER_FIELD_MASK = (1u << 4) - 1u
};

typedef struct CfruTrainerBuildPatch {
    cfru_u8 present_fields;
    cfru_u8 iv_mask;
    cfru_u8 ev_mask;
    cfru_u8 move_mask;
    cfru_u8 level;
    cfru_u8 nature;
    cfru_u8 ability_slot;
    cfru_u16 item;
    cfru_u16 moves[CFRU_MOVE_SLOT_COUNT];
    cfru_u8 iv[CFRU_STAT_COUNT];
    cfru_u8 ev[CFRU_STAT_COUNT];
} CfruTrainerBuildPatch;

cfru_u8 cfru_trainer_build_apply(
    CfruTrainerMon *output,
    const CfruTrainerMon *base,
    const CfruTrainerBuildPatch *patch
);

typedef enum CfruFacilityFormat {
    CFRU_FACILITY_SINGLE_3V3 = 0,
    CFRU_FACILITY_DOUBLE_4V4 = 1,
    CFRU_FACILITY_NPC_PARTNER_MULTI = 2,
    CFRU_FACILITY_FORMAT_COUNT = 3
} CfruFacilityFormat;

typedef enum CfruFacilityRule {
    CFRU_FACILITY_RANDOM = 0,
    CFRU_FACILITY_LITTLE = 1,
    CFRU_FACILITY_MONOTYPE = 2,
    CFRU_FACILITY_UNRESTRICTED = 3,
    CFRU_FACILITY_OU = 4,
    CFRU_FACILITY_UBER = 5,
    CFRU_FACILITY_CAMOMONS = 6,
    CFRU_FACILITY_GS = 7,
    CFRU_FACILITY_RULE_COUNT = 8
} CfruFacilityRule;

typedef enum CfruPersistentEffect {
    CFRU_PERSIST_EXP = 0,
    CFRU_PERSIST_EV = 1,
    CFRU_PERSIST_FRIENDSHIP = 2,
    CFRU_PERSIST_HATCH_STEPS = 3,
    CFRU_PERSIST_CAPTURE = 4,
    CFRU_PERSIST_MONEY = 5,
    CFRU_PERSIST_ITEM_CHANGE = 6,
    CFRU_PERSISTENT_EFFECT_COUNT = 7
} CfruPersistentEffect;

typedef struct CfruFacilityBoundary {
    cfru_u8 active;
    cfru_u8 format;
    cfru_u8 rule;
} CfruFacilityBoundary;

cfru_u8 cfru_facility_begin(
    CfruFacilityBoundary *state,
    CfruFacilityFormat format,
    CfruFacilityRule rule
);
cfru_u8 cfru_facility_allows_persistent_effect(
    const CfruFacilityBoundary *state,
    CfruPersistentEffect effect
);
void cfru_facility_end(CfruFacilityBoundary *state);

typedef enum CfruBattleExit {
    CFRU_EXIT_WON = 0,
    CFRU_EXIT_LOST = 1,
    CFRU_EXIT_RAN = 2,
    CFRU_EXIT_FORFEIT = 3,
    CFRU_EXIT_CAPTURED = 4,
    CFRU_EXIT_ABORTED = 5,
    CFRU_EXIT_ERROR = 6,
    CFRU_EXIT_COUNT = 7
} CfruBattleExit;

typedef struct CfruMirageItemState {
    cfru_u8 active;
    cfru_u16 original_item;
    cfru_u16 battle_item;
} CfruMirageItemState;

cfru_u8 cfru_mirage_item_begin(
    CfruMirageItemState *state,
    cfru_u16 persistent_item,
    cfru_u16 virtual_item
);
cfru_u16 cfru_mirage_item_current(const CfruMirageItemState *state);
cfru_u8 cfru_mirage_item_set_battle_value(CfruMirageItemState *state, cfru_u16 item);
cfru_u8 cfru_mirage_item_finish(
    CfruMirageItemState *state,
    CfruBattleExit exit_path,
    cfru_u16 *persistent_item
);

enum {
    /* Fixed CFRU UI owns exactly five shield sprite slots. */
    CFRU_RAID_MAX_SHIELDS = 5,
    CFRU_RAID_MAX_PARTNERS = 3
};

typedef enum CfruRaidEndReason {
    CFRU_RAID_END_NONE = 0,
    CFRU_RAID_END_BOSS_DEFEATED = 1,
    CFRU_RAID_END_TURN_LIMIT = 2,
    CFRU_RAID_END_PARTY_DEFEATED = 3,
    CFRU_RAID_END_FLED = 4,
    CFRU_RAID_END_CAPTURED = 5,
    CFRU_RAID_END_ABORTED = 6,
    CFRU_RAID_END_REASON_COUNT = 7
} CfruRaidEndReason;

typedef struct CfruRaidState {
    cfru_u8 active;
    cfru_u8 boss_side;
    cfru_u8 boss_party_index;
    cfru_u8 partner_mask;
    cfru_u8 shield_total;
    cfru_u8 shield_broken;
    cfru_u8 capture_allowed;
    cfru_u8 captured;
    cfru_u8 end_reason;
    cfru_u8 turn_limit;
    cfru_u8 turns_elapsed;
    cfru_u32 boss_hp;
    cfru_u32 boss_max_hp;
} CfruRaidState;

cfru_u8 cfru_raid_begin(
    CfruRaidState *state,
    cfru_u8 boss_side,
    cfru_u8 boss_party_index,
    cfru_u8 partner_mask,
    cfru_u8 shield_count,
    cfru_u32 boss_hp,
    cfru_u32 boss_max_hp,
    cfru_u8 turn_limit,
    cfru_u8 capture_allowed
);
cfru_u8 cfru_raid_partner_is_active(const CfruRaidState *state, cfru_u8 party_index);
cfru_u8 cfru_raid_shields_remaining(const CfruRaidState *state);
cfru_u8 cfru_raid_break_shield(CfruRaidState *state);
cfru_u8 cfru_raid_set_boss_hp(CfruRaidState *state, cfru_u32 boss_hp);
cfru_u8 cfru_raid_advance_turn(CfruRaidState *state);
cfru_u8 cfru_raid_finish(CfruRaidState *state, CfruRaidEndReason reason);
cfru_u8 cfru_raid_try_capture(CfruRaidState *state);
void cfru_raid_cleanup(CfruRaidState *state);

#endif /* POKEMON_VEGA_CFRU_RUNTIME_H */
