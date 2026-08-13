#ifndef POKEMON_VEGA_CFRU_INTEGRATION_H
#define POKEMON_VEGA_CFRU_INTEGRATION_H

#include "runtime.h"

/*
 * Stable bridge-facing state.  All ROM hooks call the wrappers below rather
 * than touching CFRU's fixed RAM addresses or runtime policy objects directly.
 */
typedef struct CfruPendingBattleCommand {
    cfru_u8 active;
    cfru_u8 facility_active;
    cfru_u8 ai_profile;
    cfru_u8 mechanic_mode;
    cfru_u8 facility_format;
    cfru_u8 facility_rule;
    cfru_u8 mirage_mask;
    cfru_u8 raid_active;
    cfru_u8 raid_boss_party_index;
    cfru_u8 raid_partner_mask;
    cfru_u8 raid_shield_count;
    cfru_u8 raid_turn_limit;
    cfru_u8 raid_capture_allowed;
    cfru_u8 reserved;
    cfru_u16 facility_state[11];
    cfru_u16 mirage_virtual_items[CFRU_PARTY_SIZE];
} CfruPendingBattleCommand;

enum {
    CFRU_PENDING_BATTLE_MAGIC = 0x54303650u,
    CFRU_PENDING_BATTLE_TRANSFER_MAGIC = 0x54303658u,
    CFRU_PENDING_BATTLE_ACTIVE_MAGIC = 0x54303641u
};

typedef struct CfruPendingBattleShadow {
    cfru_u32 magic;
    CfruPendingBattleCommand command;
} CfruPendingBattleShadow;

typedef struct CfruAiCacheBattlerSnapshot {
    cfru_u32 status1;
    cfru_u32 status2;
    cfru_u32 status3;
    cfru_u16 species;
    cfru_u16 attack;
    cfru_u16 defense;
    cfru_u16 speed;
    cfru_u16 sp_attack;
    cfru_u16 sp_defense;
    cfru_u16 hp;
    cfru_u16 max_hp;
    cfru_u16 ability;
    cfru_u16 item;
    cfru_u16 party_index;
    cfru_u16 moves[4];
    cfru_u8 pp[4];
    cfru_u8 type1;
    cfru_u8 type2;
    cfru_u8 type3;
    cfru_u8 stat_stages[7];
} CfruAiCacheBattlerSnapshot;

typedef struct CfruAiCachePartySnapshot {
    cfru_u32 status;
    cfru_u16 species;
    cfru_u16 item;
    cfru_u16 hp;
    cfru_u16 max_hp;
    cfru_u16 attack;
    cfru_u16 defense;
    cfru_u16 speed;
    cfru_u16 sp_attack;
    cfru_u16 sp_defense;
    cfru_u16 ability;
    cfru_u16 moves[4];
    cfru_u8 pp[4];
} CfruAiCachePartySnapshot;

typedef struct CfruAiCacheSnapshot {
    cfru_u8 valid;
    cfru_u8 battlers_count;
    cfru_u8 weather_duration;
    cfru_u8 terrain_type;
    cfru_u8 terrain_timer;
    cfru_u8 mud_sport_timer;
    cfru_u8 water_sport_timer;
    cfru_u8 gravity_timer;
    cfru_u8 trick_room_timer;
    cfru_u8 magic_room_timer;
    cfru_u8 wonder_room_timer;
    cfru_u8 fairy_lock_timer;
    cfru_u8 ion_deluge_timer;
    cfru_u8 reserved[3];
    cfru_u8 sea_of_fire_timers[CFRU_SIDE_COUNT];
    cfru_u8 swamp_timers[CFRU_SIDE_COUNT];
    cfru_u8 rainbow_timers[CFRU_SIDE_COUNT];
    cfru_u8 lucky_chant_timers[CFRU_SIDE_COUNT];
    cfru_u8 tailwind_timers[CFRU_SIDE_COUNT];
    cfru_u8 aurora_veil_timers[CFRU_SIDE_COUNT];
    cfru_u16 weather;
    cfru_u16 side_statuses[CFRU_SIDE_COUNT];
    cfru_u32 battle_type_flags;
    cfru_u8 side_timer_bytes[24];
    CfruAiCacheBattlerSnapshot battlers[4];
    CfruAiCachePartySnapshot player_party[CFRU_PARTY_SIZE];
    CfruAiCachePartySnapshot enemy_party[CFRU_PARTY_SIZE];
} CfruAiCacheSnapshot;

typedef struct CfruTeraTypeBackup {
    cfru_u8 active;
    cfru_u8 player[CFRU_PARTY_SIZE];
    cfru_u8 opponent[CFRU_PARTY_SIZE];
} CfruTeraTypeBackup;

typedef struct CfruIntegrationState {
    CfruPendingBattleCommand pending;
    cfru_u8 battle_active;
    cfru_u8 ai_profile[CFRU_SIDE_COUNT];
    cfru_u8 controllers_init_attempted;
    cfru_u8 controllers_ready;
    cfru_u8 expected_battlers_count;
    cfru_u8 observed_battlers_count;
    cfru_u8 mechanic_mode_locked;
    cfru_u8 last_raid_end_reason;
    cfru_u8 last_raid_captured;
    CfruAiCacheSnapshot ai_cache_snapshot;
    CfruTeraTypeBackup tera_type_backup;
    CfruMechanicState mechanic;
    CfruFacilityBoundary facility;
    cfru_u16 facility_state[11];
    CfruMirageItemState mirage_items[CFRU_PARTY_SIZE];
    cfru_u16 *mirage_persistent_items[CFRU_PARTY_SIZE];
    CfruRaidState raid;
} CfruIntegrationState;

typedef enum CfruBattleLayout {
    CFRU_BATTLE_LAYOUT_SINGLE = 0,
    CFRU_BATTLE_LAYOUT_DOUBLE = 1,
    CFRU_BATTLE_LAYOUT_RAID_TRIPLE = 2,
    CFRU_BATTLE_LAYOUT_COUNT = 3
} CfruBattleLayout;

typedef void (*CfruBattleControllerInit)(void);

extern CfruIntegrationState gCfruBattlePolicy;
extern CfruPendingBattleShadow gCfruPendingBattleShadow;

_Static_assert(sizeof(CfruPendingBattleCommand) == 48,
               "pending battle command ABI must remain 48 bytes");
_Static_assert(sizeof(CfruPendingBattleShadow) == 52,
               "pending battle shadow ABI must remain 52 bytes");

const CfruIntegrationState *cfru_integration_state(void);
CfruIntegrationState *cfru_integration_mutable_state(void);

cfru_u8 cfru_integration_pending_configure(
    cfru_u8 ai_profile,
    CfruMechanicMode mechanic_mode
);
cfru_u8 cfru_integration_pending_configure_facility(
    CfruFacilityFormat format,
    CfruFacilityRule rule,
    CfruMechanicMode mechanic_mode
);
cfru_u8 cfru_integration_pending_configure_mirage(
    cfru_u8 party_index,
    cfru_u16 virtual_item
);
cfru_u8 cfru_integration_pending_configure_raid(
    cfru_u8 boss_party_index,
    cfru_u8 partner_mask,
    cfru_u8 shield_count,
    cfru_u8 turn_limit,
    cfru_u8 capture_allowed
);
cfru_u8 cfru_integration_pending_restore(
    const CfruPendingBattleCommand *pending
);
cfru_u8 cfru_integration_pending_copy(CfruPendingBattleCommand *pending);
cfru_u8 cfru_integration_pending_take(CfruPendingBattleCommand *pending);
cfru_u8 cfru_integration_pending_mark_transferred(void);
cfru_u8 cfru_integration_pending_is_transferred(void);
cfru_u8 cfru_integration_pending_battle_is_active(void);
cfru_u8 cfru_integration_pending_is_active(void);
cfru_u8 cfru_integration_pending_facility_is_active(void);
cfru_u16 cfru_integration_pending_facility_get(cfru_u8 field);
void cfru_integration_pending_facility_set(cfru_u8 field, cfru_u16 value);
void cfru_integration_pending_clear(void);

cfru_u8 cfru_integration_battle_begin(
    cfru_u8 player_ai_profile,
    cfru_u8 opponent_ai_profile
);
cfru_u8 cfru_integration_battle_end(CfruBattleExit exit_path);
cfru_u8 cfru_integration_ai_profile(cfru_u8 side);
cfru_u8 cfru_integration_set_ai_profile(cfru_u8 side, cfru_u8 profile);
cfru_u8 cfru_integration_expected_battlers(CfruBattleLayout layout);
cfru_u8 cfru_integration_init_battle_controllers(
    CfruBattleControllerInit upstream_init,
    cfru_u8 *battlers_count,
    CfruBattleLayout layout
);

cfru_u8 cfru_integration_select_mechanic(
    CfruMechanicMode mode,
    cfru_u8 raid_boss_side
);
cfru_u8 cfru_integration_mechanic_mode(cfru_u8 side);
cfru_u8 cfru_integration_mechanic_can_use(
    cfru_u8 side,
    CfruMechanicMode requested_mode
);
cfru_u8 cfru_integration_mechanic_try_use(
    cfru_u8 side,
    CfruMechanicMode requested_mode
);
cfru_u8 cfru_integration_mechanic_is_forced(cfru_u8 side);

cfru_u8 cfru_integration_facility_begin(
    CfruFacilityFormat format,
    CfruFacilityRule rule
);
cfru_u8 cfru_integration_facility_end(void);
cfru_u8 cfru_integration_persistent_effect_allowed(CfruPersistentEffect effect);
cfru_u16 cfru_integration_facility_state_get(cfru_u8 field);
void cfru_integration_facility_state_set(cfru_u8 field, cfru_u16 value);

cfru_u8 cfru_integration_stat_inputs_are_valid(const CfruStatInputs *inputs);
cfru_u8 cfru_integration_effective_nature(const CfruStatInputs *inputs);
cfru_u8 cfru_integration_effective_iv(
    const CfruStatInputs *inputs,
    cfru_u8 stat_index
);
cfru_u8 cfru_integration_ability_slot(const CfruStatInputs *inputs);
cfru_u8 cfru_integration_receives_battle_exp(
    const CfruStatInputs *inputs,
    cfru_u8 participated
);
CfruCandyResult cfru_integration_apply_exp_candy(
    CfruCandyTarget *selected_target,
    cfru_u32 candy_experience,
    cfru_u8 max_level,
    const cfru_u32 *experience_for_level,
    cfru_u16 experience_table_count
);
cfru_u8 cfru_integration_trainer_build_apply(
    CfruTrainerMon *output,
    const CfruTrainerMon *base,
    const CfruTrainerBuildPatch *patch
);

cfru_u8 cfru_integration_mirage_begin(
    cfru_u8 party_index,
    cfru_u16 *persistent_item,
    cfru_u16 virtual_item
);
cfru_u16 cfru_integration_mirage_current(cfru_u8 party_index);
cfru_u8 cfru_integration_mirage_set_battle_value(
    cfru_u8 party_index,
    cfru_u16 item
);
cfru_u8 cfru_integration_mirage_end(
    cfru_u8 party_index,
    CfruBattleExit exit_path
);

cfru_u8 cfru_integration_raid_begin(
    cfru_u8 boss_side,
    cfru_u8 boss_party_index,
    cfru_u8 partner_mask,
    cfru_u8 shield_count,
    cfru_u32 boss_hp,
    cfru_u32 boss_max_hp,
    cfru_u8 turn_limit,
    cfru_u8 capture_allowed
);
cfru_u8 cfru_integration_raid_partner_is_active(cfru_u8 party_index);
cfru_u8 cfru_integration_raid_shields_remaining(void);
cfru_u8 cfru_integration_raid_break_shield(void);
cfru_u8 cfru_integration_raid_set_boss_hp(cfru_u32 boss_hp);
cfru_u8 cfru_integration_raid_advance_turn(void);
cfru_u8 cfru_integration_raid_try_capture(void);
cfru_u8 cfru_integration_raid_end(CfruRaidEndReason reason);

#endif /* POKEMON_VEGA_CFRU_INTEGRATION_H */
