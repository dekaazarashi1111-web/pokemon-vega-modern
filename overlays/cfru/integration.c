#include "integration.h"

CfruIntegrationState gCfruBattlePolicy;
CfruPendingBattleShadow gCfruPendingBattleShadow;

static void __attribute__((noinline)) cfru_pending_command_reset(
    CfruPendingBattleCommand *pending
)
{
    pending->active = CFRU_FALSE;
    pending->facility_active = CFRU_FALSE;
    pending->ai_profile = 0;
    pending->mechanic_mode = CFRU_MECHANIC_STANDARD;
    pending->facility_format = 0;
    pending->facility_rule = 0;
    pending->mirage_mask = 0;
    pending->raid_active = CFRU_FALSE;
    pending->raid_boss_party_index = 0;
    pending->raid_partner_mask = 0;
    pending->raid_shield_count = 0;
    pending->raid_turn_limit = 0;
    pending->raid_capture_allowed = CFRU_FALSE;
    pending->reserved = 0;
    pending->facility_state[0] = 0;
    pending->facility_state[1] = 0;
    pending->facility_state[2] = 0;
    pending->facility_state[3] = 0;
    pending->facility_state[4] = 0;
    pending->facility_state[5] = 0;
    pending->facility_state[6] = 0;
    pending->facility_state[7] = 0;
    pending->facility_state[8] = 0;
    pending->facility_state[9] = 0;
    pending->facility_state[10] = 0;
    pending->mirage_virtual_items[0] = 0;
    pending->mirage_virtual_items[1] = 0;
    pending->mirage_virtual_items[2] = 0;
    pending->mirage_virtual_items[3] = 0;
    pending->mirage_virtual_items[4] = 0;
    pending->mirage_virtual_items[5] = 0;
}

static void __attribute__((noinline)) cfru_pending_command_copy(
    CfruPendingBattleCommand *output,
    const CfruPendingBattleCommand *input
)
{
    output->active = input->active;
    output->facility_active = input->facility_active;
    output->ai_profile = input->ai_profile;
    output->mechanic_mode = input->mechanic_mode;
    output->facility_format = input->facility_format;
    output->facility_rule = input->facility_rule;
    output->mirage_mask = input->mirage_mask;
    output->raid_active = input->raid_active;
    output->raid_boss_party_index = input->raid_boss_party_index;
    output->raid_partner_mask = input->raid_partner_mask;
    output->raid_shield_count = input->raid_shield_count;
    output->raid_turn_limit = input->raid_turn_limit;
    output->raid_capture_allowed = input->raid_capture_allowed;
    output->reserved = input->reserved;
    output->facility_state[0] = input->facility_state[0];
    output->facility_state[1] = input->facility_state[1];
    output->facility_state[2] = input->facility_state[2];
    output->facility_state[3] = input->facility_state[3];
    output->facility_state[4] = input->facility_state[4];
    output->facility_state[5] = input->facility_state[5];
    output->facility_state[6] = input->facility_state[6];
    output->facility_state[7] = input->facility_state[7];
    output->facility_state[8] = input->facility_state[8];
    output->facility_state[9] = input->facility_state[9];
    output->facility_state[10] = input->facility_state[10];
    output->mirage_virtual_items[0] = input->mirage_virtual_items[0];
    output->mirage_virtual_items[1] = input->mirage_virtual_items[1];
    output->mirage_virtual_items[2] = input->mirage_virtual_items[2];
    output->mirage_virtual_items[3] = input->mirage_virtual_items[3];
    output->mirage_virtual_items[4] = input->mirage_virtual_items[4];
    output->mirage_virtual_items[5] = input->mirage_virtual_items[5];
}

static void cfru_integration_pending_reset(void)
{
    cfru_pending_command_reset(&gCfruBattlePolicy.pending);
}

static void cfru_integration_pending_shadow_invalidate(void)
{
    gCfruPendingBattleShadow.magic = 0;
}

static CfruPendingBattleCommand *cfru_integration_pending_shadow(void)
{
    if (gCfruPendingBattleShadow.magic != CFRU_PENDING_BATTLE_MAGIC)
    {
        cfru_integration_pending_shadow_invalidate();
        cfru_pending_command_reset(&gCfruPendingBattleShadow.command);
        gCfruPendingBattleShadow.magic = CFRU_PENDING_BATTLE_MAGIC;
    }
    return &gCfruPendingBattleShadow.command;
}

static cfru_u8 cfru_integration_side_is_valid(cfru_u8 side)
{
    return (cfru_u8)(side < CFRU_SIDE_COUNT);
}

static cfru_u8 cfru_integration_exit_is_valid(cfru_u8 exit_path)
{
    return (cfru_u8)(exit_path < CFRU_EXIT_COUNT);
}

static cfru_u8 cfru_integration_raid_partner_mask_is_valid(cfru_u8 mask)
{
    cfru_u8 index;
    cfru_u8 count = 0;
    const cfru_u8 party_mask = (cfru_u8)((1u << CFRU_PARTY_SIZE) - 1u);

    if ((mask & (cfru_u8)~party_mask) != 0)
        return CFRU_FALSE;
    for (index = 0; index < CFRU_PARTY_SIZE; ++index)
        count = (cfru_u8)(count + ((mask >> index) & 1u));
    return (cfru_u8)(count <= CFRU_RAID_MAX_PARTNERS);
}

static void cfru_integration_clear_mirage_slot(cfru_u8 party_index)
{
    gCfruBattlePolicy.mirage_items[party_index].active = CFRU_FALSE;
    gCfruBattlePolicy.mirage_items[party_index].original_item = 0;
    gCfruBattlePolicy.mirage_items[party_index].battle_item = 0;
    gCfruBattlePolicy.mirage_persistent_items[party_index] = (cfru_u16 *)0;
}

static void cfru_integration_clear_battle_state(void)
{
    cfru_u8 index;

    cfru_integration_pending_reset();
    gCfruBattlePolicy.battle_active = CFRU_FALSE;
    gCfruBattlePolicy.ai_profile[CFRU_SIDE_PLAYER] = 0;
    gCfruBattlePolicy.ai_profile[CFRU_SIDE_OPPONENT] = 0;
    gCfruBattlePolicy.controllers_init_attempted = CFRU_FALSE;
    gCfruBattlePolicy.controllers_ready = CFRU_FALSE;
    gCfruBattlePolicy.expected_battlers_count = 0;
    gCfruBattlePolicy.observed_battlers_count = 0;
    gCfruBattlePolicy.mechanic_mode_locked = CFRU_FALSE;
    gCfruBattlePolicy.last_raid_end_reason = CFRU_RAID_END_NONE;
    gCfruBattlePolicy.last_raid_captured = CFRU_FALSE;
    gCfruBattlePolicy.ai_cache_snapshot.valid = CFRU_FALSE;
    gCfruBattlePolicy.tera_type_backup.active = CFRU_FALSE;
    for (index = 0; index < CFRU_PARTY_SIZE; ++index)
    {
        gCfruBattlePolicy.tera_type_backup.player[index] = 0;
        gCfruBattlePolicy.tera_type_backup.opponent[index] = 0;
    }
    cfru_mechanic_cleanup(&gCfruBattlePolicy.mechanic);
    cfru_facility_end(&gCfruBattlePolicy.facility);
    for (index = 0; index < 11; ++index)
        gCfruBattlePolicy.facility_state[index] = 0;
    cfru_raid_cleanup(&gCfruBattlePolicy.raid);
    for (index = 0; index < CFRU_PARTY_SIZE; ++index)
        cfru_integration_clear_mirage_slot(index);
}

static void cfru_integration_record_raid_exit(CfruBattleExit exit_path)
{
    cfru_u8 reason = gCfruBattlePolicy.raid.end_reason;

    if (!gCfruBattlePolicy.raid.active)
        return;

    if (reason == CFRU_RAID_END_NONE)
    {
        switch (exit_path)
        {
            case CFRU_EXIT_WON:
                reason = CFRU_RAID_END_BOSS_DEFEATED;
                break;
            case CFRU_EXIT_LOST:
                reason = CFRU_RAID_END_PARTY_DEFEATED;
                break;
            case CFRU_EXIT_RAN:
            case CFRU_EXIT_FORFEIT:
                reason = CFRU_RAID_END_FLED;
                break;
            case CFRU_EXIT_CAPTURED:
                reason = CFRU_RAID_END_CAPTURED;
                break;
            case CFRU_EXIT_ABORTED:
            case CFRU_EXIT_ERROR:
            default:
                reason = CFRU_RAID_END_ABORTED;
                break;
        }
    }

    gCfruBattlePolicy.last_raid_end_reason = reason;
    gCfruBattlePolicy.last_raid_captured = (cfru_u8)(
        gCfruBattlePolicy.raid.captured || reason == CFRU_RAID_END_CAPTURED);
}

const CfruIntegrationState *cfru_integration_state(void)
{
    return &gCfruBattlePolicy;
}

CfruIntegrationState *cfru_integration_mutable_state(void)
{
    return &gCfruBattlePolicy;
}

cfru_u8 cfru_integration_pending_configure(
    cfru_u8 ai_profile,
    CfruMechanicMode mechanic_mode
)
{
    CfruPendingBattleCommand *pending;
    cfru_u8 mirage_mask;
    cfru_u16 mirage_item0;
    cfru_u16 mirage_item1;
    cfru_u16 mirage_item2;
    cfru_u16 mirage_item3;
    cfru_u16 mirage_item4;
    cfru_u16 mirage_item5;

    if (gCfruPendingBattleShadow.magic == CFRU_PENDING_BATTLE_TRANSFER_MAGIC
        || gCfruPendingBattleShadow.magic == CFRU_PENDING_BATTLE_ACTIVE_MAGIC
        || !cfru_ai_profile_is_valid(ai_profile)
        || mechanic_mode > CFRU_MECHANIC_TERASTAL)
        return CFRU_FALSE;

    pending = cfru_integration_pending_shadow();
    mirage_mask = pending->mirage_mask;
    mirage_item0 = pending->mirage_virtual_items[0];
    mirage_item1 = pending->mirage_virtual_items[1];
    mirage_item2 = pending->mirage_virtual_items[2];
    mirage_item3 = pending->mirage_virtual_items[3];
    mirage_item4 = pending->mirage_virtual_items[4];
    mirage_item5 = pending->mirage_virtual_items[5];
    cfru_integration_pending_shadow_invalidate();
    cfru_pending_command_reset(&gCfruPendingBattleShadow.command);
    pending = &gCfruPendingBattleShadow.command;
    pending->active = CFRU_TRUE;
    pending->ai_profile = ai_profile;
    pending->mechanic_mode = (cfru_u8)mechanic_mode;
    pending->mirage_mask = mirage_mask;
    pending->mirage_virtual_items[0] = mirage_item0;
    pending->mirage_virtual_items[1] = mirage_item1;
    pending->mirage_virtual_items[2] = mirage_item2;
    pending->mirage_virtual_items[3] = mirage_item3;
    pending->mirage_virtual_items[4] = mirage_item4;
    pending->mirage_virtual_items[5] = mirage_item5;
    gCfruPendingBattleShadow.magic = CFRU_PENDING_BATTLE_MAGIC;
    return CFRU_TRUE;
}

cfru_u8 cfru_integration_pending_configure_facility(
    CfruFacilityFormat format,
    CfruFacilityRule rule,
    CfruMechanicMode mechanic_mode
)
{
    CfruPendingBattleCommand *pending;
    static const cfru_u8 sTierByRule[CFRU_FACILITY_RULE_COUNT] = {
        0, 4, 6, 1, 2, 3, 7, 5
    };

    if ((cfru_u8)format >= CFRU_FACILITY_FORMAT_COUNT
        || (cfru_u8)rule >= CFRU_FACILITY_RULE_COUNT
        || !cfru_integration_pending_configure(
            CFRU_AI_FULL_SMART, mechanic_mode))
        return CFRU_FALSE;

    pending = cfru_integration_pending_shadow();
    cfru_integration_pending_shadow_invalidate();
    pending->facility_active = CFRU_TRUE;
    pending->facility_format = (cfru_u8)format;
    pending->facility_rule = (cfru_u8)rule;
    pending->facility_state[1] =
        format == CFRU_FACILITY_SINGLE_3V3 ? 3
        : format == CFRU_FACILITY_DOUBLE_4V4 ? 4
        : 2; /* Multi builds 2+2 on each side for an aggregate 4v4. */
    pending->facility_state[2] = 50;
    pending->facility_state[3] = (cfru_u16)(
        (cfru_u8)format + (rule == CFRU_FACILITY_RANDOM ? 4 : 0));
    pending->facility_state[4] = sTierByRule[(cfru_u8)rule];
    pending->facility_state[5] = 0xFFFF;
    pending->facility_state[6] = 0xFFFF;
    gCfruPendingBattleShadow.magic = CFRU_PENDING_BATTLE_MAGIC;
    return CFRU_TRUE;
}

cfru_u8 cfru_integration_pending_configure_mirage(
    cfru_u8 party_index,
    cfru_u16 virtual_item
)
{
    CfruPendingBattleCommand *pending;

    if (party_index >= CFRU_PARTY_SIZE
        || virtual_item >= CFRU_ITEM_COUNT)
        return CFRU_FALSE;

    if (!cfru_integration_pending_is_active()
        && !cfru_integration_pending_configure(
            CFRU_AI_BASIC, CFRU_MECHANIC_STANDARD))
        return CFRU_FALSE;

    pending = cfru_integration_pending_shadow();
    cfru_integration_pending_shadow_invalidate();
    pending->mirage_mask |= (cfru_u8)(1u << party_index);
    pending->mirage_virtual_items[party_index] = virtual_item;
    gCfruPendingBattleShadow.magic = CFRU_PENDING_BATTLE_MAGIC;
    return CFRU_TRUE;
}

cfru_u8 cfru_integration_pending_configure_raid(
    cfru_u8 boss_party_index,
    cfru_u8 partner_mask,
    cfru_u8 shield_count,
    cfru_u8 turn_limit,
    cfru_u8 capture_allowed
)
{
    CfruPendingBattleCommand *pending;
    cfru_u8 mirage_mask;
    cfru_u16 mirage_item0;
    cfru_u16 mirage_item1;
    cfru_u16 mirage_item2;
    cfru_u16 mirage_item3;
    cfru_u16 mirage_item4;
    cfru_u16 mirage_item5;

    if (gCfruPendingBattleShadow.magic == CFRU_PENDING_BATTLE_TRANSFER_MAGIC
        || gCfruPendingBattleShadow.magic == CFRU_PENDING_BATTLE_ACTIVE_MAGIC
        || boss_party_index >= CFRU_PARTY_SIZE
        || !cfru_integration_raid_partner_mask_is_valid(partner_mask)
        || shield_count > CFRU_RAID_MAX_SHIELDS
        || turn_limit == 0
        || capture_allowed > CFRU_TRUE)
        return CFRU_FALSE;

    pending = cfru_integration_pending_shadow();
    mirage_mask = pending->mirage_mask;
    mirage_item0 = pending->mirage_virtual_items[0];
    mirage_item1 = pending->mirage_virtual_items[1];
    mirage_item2 = pending->mirage_virtual_items[2];
    mirage_item3 = pending->mirage_virtual_items[3];
    mirage_item4 = pending->mirage_virtual_items[4];
    mirage_item5 = pending->mirage_virtual_items[5];
    cfru_integration_pending_shadow_invalidate();
    cfru_pending_command_reset(&gCfruPendingBattleShadow.command);
    pending = &gCfruPendingBattleShadow.command;
    pending->active = CFRU_TRUE;
    pending->ai_profile = CFRU_AI_FULL_SMART;
    pending->mechanic_mode = CFRU_MECHANIC_RAID_HIGH_DIFFICULTY;
    pending->mirage_mask = mirage_mask;
    pending->mirage_virtual_items[0] = mirage_item0;
    pending->mirage_virtual_items[1] = mirage_item1;
    pending->mirage_virtual_items[2] = mirage_item2;
    pending->mirage_virtual_items[3] = mirage_item3;
    pending->mirage_virtual_items[4] = mirage_item4;
    pending->mirage_virtual_items[5] = mirage_item5;
    pending->raid_active = CFRU_TRUE;
    pending->raid_boss_party_index = boss_party_index;
    pending->raid_partner_mask = partner_mask;
    pending->raid_shield_count = shield_count;
    pending->raid_turn_limit = turn_limit;
    pending->raid_capture_allowed = capture_allowed;
    gCfruPendingBattleShadow.magic = CFRU_PENDING_BATTLE_MAGIC;
    return CFRU_TRUE;
}

cfru_u8 cfru_integration_pending_restore(
    const CfruPendingBattleCommand *pending
)
{
    cfru_u8 index;

    if (pending == (const CfruPendingBattleCommand *)0
        || gCfruBattlePolicy.battle_active
        || pending->reserved != 0
        || (pending->mirage_mask & (cfru_u8)~((1u << CFRU_PARTY_SIZE) - 1u)))
        return CFRU_FALSE;

    if (!pending->active)
    {
        cfru_integration_pending_reset();
        return CFRU_TRUE;
    }
    if (!cfru_ai_profile_is_valid(pending->ai_profile)
        || pending->facility_active > CFRU_TRUE
        || pending->raid_active > CFRU_TRUE
        || (pending->facility_active && pending->raid_active)
        || (pending->raid_active
            ? pending->mechanic_mode != CFRU_MECHANIC_RAID_HIGH_DIFFICULTY
            : pending->mechanic_mode > CFRU_MECHANIC_TERASTAL))
        return CFRU_FALSE;
    if (pending->facility_active
        && (pending->facility_format >= CFRU_FACILITY_FORMAT_COUNT
            || pending->facility_rule >= CFRU_FACILITY_RULE_COUNT))
        return CFRU_FALSE;
    if (pending->raid_active
        && (pending->raid_boss_party_index >= CFRU_PARTY_SIZE
            || !cfru_integration_raid_partner_mask_is_valid(
                pending->raid_partner_mask)
            || pending->raid_shield_count > CFRU_RAID_MAX_SHIELDS
            || pending->raid_turn_limit == 0
            || pending->raid_capture_allowed > CFRU_TRUE))
        return CFRU_FALSE;
    for (index = 0; index < CFRU_PARTY_SIZE; ++index)
    {
        if ((pending->mirage_mask & (1u << index))
            && pending->mirage_virtual_items[index] >= CFRU_ITEM_COUNT)
            return CFRU_FALSE;
    }

    cfru_pending_command_copy(&gCfruBattlePolicy.pending, pending);
    return CFRU_TRUE;
}

cfru_u8 cfru_integration_pending_copy(CfruPendingBattleCommand *pending)
{
    if (pending == (CfruPendingBattleCommand *)0)
        return CFRU_FALSE;
    cfru_pending_command_reset(pending);
    if (gCfruPendingBattleShadow.magic != CFRU_PENDING_BATTLE_MAGIC)
        return CFRU_FALSE;
    cfru_pending_command_copy(pending, &gCfruPendingBattleShadow.command);
    return CFRU_TRUE;
}

cfru_u8 cfru_integration_pending_take(CfruPendingBattleCommand *pending)
{
    cfru_u8 present = cfru_integration_pending_copy(pending);

    cfru_integration_pending_shadow_invalidate();
    return present;
}

cfru_u8 cfru_integration_pending_mark_transferred(void)
{
    if (gCfruPendingBattleShadow.magic != 0)
        return CFRU_FALSE;
    gCfruPendingBattleShadow.magic = CFRU_PENDING_BATTLE_TRANSFER_MAGIC;
    return CFRU_TRUE;
}

cfru_u8 cfru_integration_pending_is_transferred(void)
{
    return (cfru_u8)(
        gCfruPendingBattleShadow.magic == CFRU_PENDING_BATTLE_TRANSFER_MAGIC);
}

cfru_u8 cfru_integration_pending_battle_is_active(void)
{
    return (cfru_u8)(
        gCfruPendingBattleShadow.magic == CFRU_PENDING_BATTLE_ACTIVE_MAGIC);
}

cfru_u8 cfru_integration_pending_is_active(void)
{
    return (cfru_u8)(
        gCfruPendingBattleShadow.magic == CFRU_PENDING_BATTLE_MAGIC
        && gCfruPendingBattleShadow.command.active);
}

cfru_u8 cfru_integration_pending_facility_is_active(void)
{
    return (cfru_u8)(
        cfru_integration_pending_is_active()
        && gCfruPendingBattleShadow.command.facility_active);
}

cfru_u16 cfru_integration_pending_facility_get(cfru_u8 field)
{
    if (!cfru_integration_pending_facility_is_active() || field >= 11)
        return 0;
    return gCfruPendingBattleShadow.command.facility_state[field];
}

void cfru_integration_pending_facility_set(cfru_u8 field, cfru_u16 value)
{
    if (cfru_integration_pending_facility_is_active() && field < 11)
    {
        cfru_integration_pending_shadow_invalidate();
        gCfruPendingBattleShadow.command.facility_state[field] = value;
        gCfruPendingBattleShadow.magic = CFRU_PENDING_BATTLE_MAGIC;
    }
}

void cfru_integration_pending_clear(void)
{
    cfru_integration_pending_shadow_invalidate();
}

cfru_u8 cfru_integration_battle_begin(
    cfru_u8 player_ai_profile,
    cfru_u8 opponent_ai_profile
)
{
    if (!cfru_ai_profile_is_valid(player_ai_profile)
        || !cfru_ai_profile_is_valid(opponent_ai_profile))
        return CFRU_FALSE;

    if (gCfruBattlePolicy.battle_active)
    {
        if (!cfru_integration_battle_end(CFRU_EXIT_ERROR))
            return CFRU_FALSE;
    }
    cfru_integration_clear_battle_state();

    if (!cfru_mechanic_begin(
        &gCfruBattlePolicy.mechanic,
        CFRU_MECHANIC_STANDARD,
        CFRU_SIDE_OPPONENT))
        return CFRU_FALSE;

    gCfruBattlePolicy.battle_active = CFRU_TRUE;
    gCfruBattlePolicy.ai_profile[CFRU_SIDE_PLAYER] = player_ai_profile;
    gCfruBattlePolicy.ai_profile[CFRU_SIDE_OPPONENT] = opponent_ai_profile;
    gCfruPendingBattleShadow.magic = CFRU_PENDING_BATTLE_ACTIVE_MAGIC;
    return CFRU_TRUE;
}

cfru_u8 cfru_integration_battle_end(CfruBattleExit exit_path)
{
    cfru_u8 index;

    if (!gCfruBattlePolicy.battle_active
        || !cfru_integration_exit_is_valid((cfru_u8)exit_path))
        return CFRU_FALSE;

    for (index = 0; index < CFRU_PARTY_SIZE; ++index)
    {
        if (gCfruBattlePolicy.mirage_items[index].active)
        {
            if (!cfru_integration_mirage_end(index, exit_path))
                return CFRU_FALSE;
        }
    }

    cfru_integration_record_raid_exit(exit_path);
    cfru_raid_cleanup(&gCfruBattlePolicy.raid);
    cfru_facility_end(&gCfruBattlePolicy.facility);
    cfru_mechanic_cleanup(&gCfruBattlePolicy.mechanic);
    gCfruBattlePolicy.mechanic_mode_locked = CFRU_FALSE;
    gCfruBattlePolicy.controllers_init_attempted = CFRU_FALSE;
    gCfruBattlePolicy.controllers_ready = CFRU_FALSE;
    gCfruBattlePolicy.expected_battlers_count = 0;
    gCfruBattlePolicy.observed_battlers_count = 0;
    gCfruBattlePolicy.ai_profile[CFRU_SIDE_PLAYER] = 0;
    gCfruBattlePolicy.ai_profile[CFRU_SIDE_OPPONENT] = 0;
    gCfruBattlePolicy.battle_active = CFRU_FALSE;
    cfru_integration_pending_shadow_invalidate();
    return CFRU_TRUE;
}

cfru_u8 cfru_integration_ai_profile(cfru_u8 side)
{
    if (!gCfruBattlePolicy.battle_active || !cfru_integration_side_is_valid(side))
        return 0;
    return gCfruBattlePolicy.ai_profile[side];
}

cfru_u8 cfru_integration_set_ai_profile(cfru_u8 side, cfru_u8 profile)
{
    if (!gCfruBattlePolicy.battle_active
        || !cfru_integration_side_is_valid(side)
        || !cfru_ai_profile_is_valid(profile))
        return CFRU_FALSE;
    gCfruBattlePolicy.ai_profile[side] = profile;
    return CFRU_TRUE;
}

cfru_u8 cfru_integration_expected_battlers(CfruBattleLayout layout)
{
    switch (layout)
    {
        case CFRU_BATTLE_LAYOUT_SINGLE:
            return 2;
        case CFRU_BATTLE_LAYOUT_DOUBLE:
            return 4;
        case CFRU_BATTLE_LAYOUT_RAID_TRIPLE:
            return 3;
        case CFRU_BATTLE_LAYOUT_COUNT:
        default:
            return 0;
    }
}

cfru_u8 cfru_integration_init_battle_controllers(
    CfruBattleControllerInit upstream_init,
    cfru_u8 *battlers_count,
    CfruBattleLayout layout
)
{
    cfru_u8 expected = cfru_integration_expected_battlers(layout);

    if (!gCfruBattlePolicy.battle_active
        || gCfruBattlePolicy.controllers_init_attempted
        || upstream_init == (CfruBattleControllerInit)0
        || battlers_count == (cfru_u8 *)0
        || expected == 0
        || (layout == CFRU_BATTLE_LAYOUT_RAID_TRIPLE
            && !gCfruBattlePolicy.raid.active))
        return CFRU_FALSE;

    /*
     * The original controller initializer owns controller functions, battler
     * positions and gBattlersCount.  Policy initialization must not replace
     * that work; it calls the original first and validates its postcondition.
     */
    gCfruBattlePolicy.controllers_init_attempted = CFRU_TRUE;
    upstream_init();
    gCfruBattlePolicy.expected_battlers_count = expected;
    gCfruBattlePolicy.observed_battlers_count = *battlers_count;
    gCfruBattlePolicy.controllers_ready = (cfru_u8)(*battlers_count == expected);
    return gCfruBattlePolicy.controllers_ready;
}

cfru_u8 cfru_integration_select_mechanic(
    CfruMechanicMode mode,
    cfru_u8 raid_boss_side
)
{
    CfruMechanicState candidate;

    if (!gCfruBattlePolicy.battle_active
        || gCfruBattlePolicy.mechanic_mode_locked
        || mode == CFRU_MECHANIC_RAID_HIGH_DIFFICULTY)
        return CFRU_FALSE;

    if (!cfru_mechanic_begin(&candidate, mode, raid_boss_side))
        return CFRU_FALSE;

    gCfruBattlePolicy.mechanic = candidate;
    gCfruBattlePolicy.mechanic_mode_locked = CFRU_TRUE;
    return CFRU_TRUE;
}

cfru_u8 cfru_integration_mechanic_mode(cfru_u8 side)
{
    if (!gCfruBattlePolicy.battle_active
        || !cfru_integration_side_is_valid(side)
        || !gCfruBattlePolicy.mechanic.active)
        return CFRU_MECHANIC_STANDARD;
    return gCfruBattlePolicy.mechanic.effective_mode[side];
}

cfru_u8 cfru_integration_mechanic_can_use(
    cfru_u8 side,
    CfruMechanicMode requested_mode
)
{
    if (!gCfruBattlePolicy.battle_active)
        return CFRU_FALSE;
    return cfru_mechanic_can_use(
        &gCfruBattlePolicy.mechanic,
        side,
        requested_mode);
}

cfru_u8 cfru_integration_mechanic_try_use(
    cfru_u8 side,
    CfruMechanicMode requested_mode
)
{
    if (!gCfruBattlePolicy.battle_active)
        return CFRU_FALSE;
    return cfru_mechanic_try_use(
        &gCfruBattlePolicy.mechanic,
        side,
        requested_mode);
}

cfru_u8 cfru_integration_mechanic_is_forced(cfru_u8 side)
{
    if (!gCfruBattlePolicy.battle_active)
        return CFRU_FALSE;
    return cfru_mechanic_is_forced(&gCfruBattlePolicy.mechanic, side);
}

cfru_u8 cfru_integration_facility_begin(
    CfruFacilityFormat format,
    CfruFacilityRule rule
)
{
    static const cfru_u8 sTierByRule[CFRU_FACILITY_RULE_COUNT] = {
        0, 4, 6, 1, 2, 3, 7, 5
    };
    cfru_u8 index;

    if (!gCfruBattlePolicy.battle_active || gCfruBattlePolicy.facility.active)
        return CFRU_FALSE;
    if (!cfru_facility_begin(&gCfruBattlePolicy.facility, format, rule))
        return CFRU_FALSE;
    for (index = 0; index < 11; ++index)
        gCfruBattlePolicy.facility_state[index] = 0;
    gCfruBattlePolicy.facility_state[1] =
        format == CFRU_FACILITY_SINGLE_3V3 ? 3 : 4;
    gCfruBattlePolicy.facility_state[2] = 50;
    gCfruBattlePolicy.facility_state[3] = (cfru_u16)(
        (cfru_u8)format + (rule == CFRU_FACILITY_RANDOM ? 4 : 0));
    gCfruBattlePolicy.facility_state[4] = sTierByRule[(cfru_u8)rule];
    gCfruBattlePolicy.facility_state[5] = 0xFFFF;
    gCfruBattlePolicy.facility_state[6] = 0xFFFF;
    return CFRU_TRUE;
}

cfru_u8 cfru_integration_facility_end(void)
{
    if (!gCfruBattlePolicy.battle_active || !gCfruBattlePolicy.facility.active)
        return CFRU_FALSE;
    cfru_facility_end(&gCfruBattlePolicy.facility);
    {
        cfru_u8 index;
        for (index = 0; index < 11; ++index)
            gCfruBattlePolicy.facility_state[index] = 0;
    }
    return CFRU_TRUE;
}

cfru_u8 cfru_integration_persistent_effect_allowed(CfruPersistentEffect effect)
{
    return cfru_facility_allows_persistent_effect(
        &gCfruBattlePolicy.facility,
        effect);
}

cfru_u16 cfru_integration_facility_state_get(cfru_u8 field)
{
    if (!gCfruBattlePolicy.facility.active || field >= 11)
        return 0;
    return gCfruBattlePolicy.facility_state[field];
}

void cfru_integration_facility_state_set(cfru_u8 field, cfru_u16 value)
{
    if (gCfruBattlePolicy.facility.active && field < 11)
        gCfruBattlePolicy.facility_state[field] = value;
}

cfru_u8 cfru_integration_stat_inputs_are_valid(const CfruStatInputs *inputs)
{
    return cfru_stat_inputs_are_valid(inputs);
}

cfru_u8 cfru_integration_effective_nature(const CfruStatInputs *inputs)
{
    return cfru_stat_effective_nature(inputs);
}

cfru_u8 cfru_integration_effective_iv(
    const CfruStatInputs *inputs,
    cfru_u8 stat_index
)
{
    return cfru_stat_effective_iv(inputs, stat_index);
}

cfru_u8 cfru_integration_ability_slot(const CfruStatInputs *inputs)
{
    return cfru_stat_ability_slot(inputs);
}

cfru_u8 cfru_integration_receives_battle_exp(
    const CfruStatInputs *inputs,
    cfru_u8 participated
)
{
    return cfru_stat_receives_battle_exp(inputs, participated);
}

CfruCandyResult cfru_integration_apply_exp_candy(
    CfruCandyTarget *selected_target,
    cfru_u32 candy_experience,
    cfru_u8 max_level,
    const cfru_u32 *experience_for_level,
    cfru_u16 experience_table_count
)
{
    return cfru_apply_exp_candy(
        selected_target,
        candy_experience,
        max_level,
        experience_for_level,
        experience_table_count);
}

cfru_u8 cfru_integration_trainer_build_apply(
    CfruTrainerMon *output,
    const CfruTrainerMon *base,
    const CfruTrainerBuildPatch *patch
)
{
    return cfru_trainer_build_apply(output, base, patch);
}

cfru_u8 cfru_integration_mirage_begin(
    cfru_u8 party_index,
    cfru_u16 *persistent_item,
    cfru_u16 virtual_item
)
{
    if (!gCfruBattlePolicy.battle_active
        || party_index >= CFRU_PARTY_SIZE
        || persistent_item == (cfru_u16 *)0
        || gCfruBattlePolicy.mirage_items[party_index].active)
        return CFRU_FALSE;

    if (!cfru_mirage_item_begin(
        &gCfruBattlePolicy.mirage_items[party_index],
        *persistent_item,
        virtual_item))
        return CFRU_FALSE;

    gCfruBattlePolicy.mirage_persistent_items[party_index] = persistent_item;
    *persistent_item = virtual_item;
    return CFRU_TRUE;
}

cfru_u16 cfru_integration_mirage_current(cfru_u8 party_index)
{
    if (party_index >= CFRU_PARTY_SIZE)
        return 0;
    return cfru_mirage_item_current(
        &gCfruBattlePolicy.mirage_items[party_index]);
}

cfru_u8 cfru_integration_mirage_set_battle_value(
    cfru_u8 party_index,
    cfru_u16 item
)
{
    if (!gCfruBattlePolicy.battle_active || party_index >= CFRU_PARTY_SIZE)
        return CFRU_FALSE;
    return cfru_mirage_item_set_battle_value(
        &gCfruBattlePolicy.mirage_items[party_index],
        item);
}

cfru_u8 cfru_integration_mirage_end(
    cfru_u8 party_index,
    CfruBattleExit exit_path
)
{
    cfru_u16 *persistent_item;

    if (!gCfruBattlePolicy.battle_active
        || party_index >= CFRU_PARTY_SIZE
        || !cfru_integration_exit_is_valid((cfru_u8)exit_path))
        return CFRU_FALSE;

    persistent_item = gCfruBattlePolicy.mirage_persistent_items[party_index];
    if (persistent_item == (cfru_u16 *)0
        || !cfru_mirage_item_finish(
            &gCfruBattlePolicy.mirage_items[party_index],
            exit_path,
            persistent_item))
        return CFRU_FALSE;

    gCfruBattlePolicy.mirage_persistent_items[party_index] = (cfru_u16 *)0;
    return CFRU_TRUE;
}

cfru_u8 cfru_integration_raid_begin(
    cfru_u8 boss_side,
    cfru_u8 boss_party_index,
    cfru_u8 partner_mask,
    cfru_u8 shield_count,
    cfru_u32 boss_hp,
    cfru_u32 boss_max_hp,
    cfru_u8 turn_limit,
    cfru_u8 capture_allowed
)
{
    CfruRaidState raid_candidate = {0};
    CfruMechanicState mechanic_candidate;

    if (!gCfruBattlePolicy.battle_active
        || gCfruBattlePolicy.raid.active
        || gCfruBattlePolicy.mechanic_mode_locked)
        return CFRU_FALSE;

    if (!cfru_raid_begin(
        &raid_candidate,
        boss_side,
        boss_party_index,
        partner_mask,
        shield_count,
        boss_hp,
        boss_max_hp,
        turn_limit,
        capture_allowed))
        return CFRU_FALSE;

    if (!cfru_mechanic_begin(
        &mechanic_candidate,
        CFRU_MECHANIC_RAID_HIGH_DIFFICULTY,
        boss_side))
        return CFRU_FALSE;

    gCfruBattlePolicy.raid = raid_candidate;
    gCfruBattlePolicy.mechanic = mechanic_candidate;
    gCfruBattlePolicy.mechanic_mode_locked = CFRU_TRUE;
    gCfruBattlePolicy.last_raid_end_reason = CFRU_RAID_END_NONE;
    gCfruBattlePolicy.last_raid_captured = CFRU_FALSE;
    return CFRU_TRUE;
}

cfru_u8 cfru_integration_raid_partner_is_active(cfru_u8 party_index)
{
    return cfru_raid_partner_is_active(
        &gCfruBattlePolicy.raid,
        party_index);
}

cfru_u8 cfru_integration_raid_shields_remaining(void)
{
    return cfru_raid_shields_remaining(&gCfruBattlePolicy.raid);
}

cfru_u8 cfru_integration_raid_break_shield(void)
{
    return cfru_raid_break_shield(&gCfruBattlePolicy.raid);
}

cfru_u8 cfru_integration_raid_set_boss_hp(cfru_u32 boss_hp)
{
    return cfru_raid_set_boss_hp(&gCfruBattlePolicy.raid, boss_hp);
}

cfru_u8 cfru_integration_raid_advance_turn(void)
{
    return cfru_raid_advance_turn(&gCfruBattlePolicy.raid);
}

cfru_u8 cfru_integration_raid_try_capture(void)
{
    return cfru_raid_try_capture(&gCfruBattlePolicy.raid);
}

cfru_u8 cfru_integration_raid_end(CfruRaidEndReason reason)
{
    cfru_u8 current_reason;

    if (!gCfruBattlePolicy.battle_active
        || !gCfruBattlePolicy.raid.active
        || reason <= CFRU_RAID_END_NONE
        || reason >= CFRU_RAID_END_REASON_COUNT)
        return CFRU_FALSE;

    current_reason = gCfruBattlePolicy.raid.end_reason;
    if (reason == CFRU_RAID_END_CAPTURED)
    {
        if (!gCfruBattlePolicy.raid.captured
            && !cfru_raid_try_capture(&gCfruBattlePolicy.raid))
            return CFRU_FALSE;
    }
    else if (current_reason == CFRU_RAID_END_NONE)
    {
        if (!cfru_raid_finish(&gCfruBattlePolicy.raid, reason))
            return CFRU_FALSE;
    }
    else if (current_reason != (cfru_u8)reason)
        return CFRU_FALSE;

    gCfruBattlePolicy.last_raid_end_reason = gCfruBattlePolicy.raid.end_reason;
    gCfruBattlePolicy.last_raid_captured = gCfruBattlePolicy.raid.captured;
    cfru_raid_cleanup(&gCfruBattlePolicy.raid);
    cfru_mechanic_cleanup(&gCfruBattlePolicy.mechanic);
    return CFRU_TRUE;
}
