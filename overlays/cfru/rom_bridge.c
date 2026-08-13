#include "rom_bridge.h"

#include "../include/new/dynamax.h"
#include "../include/new/form_change.h"
#include "../include/new/frontier.h"
#include "../include/new/mega.h"
#include "../include/new/multi.h"
#include "../include/new/terastal.h"
#include "../include/random.h"

static bool8 VegaEnsurePendingPolicyStorage(void)
{
    return (bool8)(
        !cfru_integration_pending_is_transferred()
        && !cfru_integration_pending_battle_is_active());
}

_Static_assert(B_SIDE_PLAYER == CFRU_SIDE_PLAYER,
               "CFRU player side must match policy ABI");
_Static_assert(B_SIDE_OPPONENT == CFRU_SIDE_OPPONENT,
               "CFRU opponent side must match policy ABI");
_Static_assert(PARTY_SIZE == CFRU_PARTY_SIZE,
               "CFRU party size must match policy ABI");
_Static_assert(AI_SCRIPT_CHECK_BAD_MOVE == CFRU_AI_BASIC,
               "AI_BASIC must be CFRU bad-move bit");
_Static_assert((AI_SCRIPT_CHECK_BAD_MOVE | AI_SCRIPT_SEMI_SMART)
                   == CFRU_AI_SEMI_SMART,
               "AI_SEMI_SMART must be CFRU basic+semi bits");
_Static_assert((AI_SCRIPT_CHECK_BAD_MOVE | AI_SCRIPT_CHECK_GOOD_MOVE)
                   == CFRU_AI_FULL_SMART,
               "AI_FULL_SMART must be CFRU basic+good bits");

static bool8 VegaBattlePolicyBattlerSide(u8 battler, cfru_u8 *side)
{
    u8 upstream_side;

    if (side == (cfru_u8 *)0 || battler >= gBattlersCount)
        return FALSE;

    upstream_side = SIDE(battler);
    if (upstream_side != B_SIDE_PLAYER && upstream_side != B_SIDE_OPPONENT)
        return FALSE;

    *side = (cfru_u8)upstream_side;
    return TRUE;
}

static bool8 VegaBattlePolicyCanMechanic(
    u8 battler,
    bool8 upstream_allowed,
    CfruMechanicMode mode
)
{
    cfru_u8 side;

    if (!upstream_allowed || !VegaBattlePolicyBattlerSide(battler, &side))
        return FALSE;

    return (bool8)cfru_integration_mechanic_can_use(side, mode);
}

static bool8 VegaBattlePolicyMarkMechanic(
    u8 battler,
    CfruMechanicMode mode
)
{
    cfru_u8 side;

    if (!VegaBattlePolicyBattlerSide(battler, &side))
        return FALSE;

    return (bool8)cfru_integration_mechanic_try_use(side, mode);
}

u8 VegaNormalizeTrainerAIProfile(u32 trainer_ai_flags)
{
    if (trainer_ai_flags & AI_SCRIPT_CHECK_GOOD_MOVE)
        return CFRU_AI_FULL_SMART;
    if (trainer_ai_flags & AI_SCRIPT_SEMI_SMART)
        return CFRU_AI_SEMI_SMART;
    return CFRU_AI_BASIC;
}

bool8 VegaConfigureNextBattlePolicy(u8 ai_profile, CfruMechanicMode mode)
{
    if (!cfru_ai_profile_is_valid(ai_profile)
        || mode > CFRU_MECHANIC_TERASTAL
        || !VegaEnsurePendingPolicyStorage())
        return FALSE;
    return (bool8)cfru_integration_pending_configure(ai_profile, mode);
}

bool8 VegaConfigureNextFacility(
    CfruFacilityFormat format,
    CfruFacilityRule rule,
    CfruMechanicMode mode
)
{
    if ((u8)format >= CFRU_FACILITY_FORMAT_COUNT
        || (u8)rule >= CFRU_FACILITY_RULE_COUNT
        || mode > CFRU_MECHANIC_TERASTAL
        || !VegaEnsurePendingPolicyStorage())
        return FALSE;
    if (!cfru_integration_pending_configure_facility(format, rule, mode))
        return FALSE;

    cfru_integration_pending_facility_set(8, 0);
    cfru_integration_pending_facility_set(9, 1);
    cfru_integration_pending_facility_set(10, 0);
    return VegaBattlePolicyPrepareFacilityBattle();
}

bool8 VegaBattlePolicyPrepareFacilityBattle(void)
{
    CfruPendingBattleCommand pending;
    CfruFacilityFormat format;
    u32 route_mask = BATTLE_TYPE_DOUBLE | BATTLE_TYPE_TWO_OPPONENTS
                   | BATTLE_TYPE_INGAME_PARTNER | BATTLE_TYPE_MULTI
                   | BATTLE_TYPE_LINK;

    if (!cfru_integration_pending_copy(&pending)
        || !pending.active
        || !pending.facility_active)
        return FALSE;
    format = (CfruFacilityFormat)pending.facility_format;
    if ((u8)format >= CFRU_FACILITY_FORMAT_COUNT)
        return FALSE;

    gBattleTypeFlags &= ~route_mask;
    gBattleTypeFlags |= BATTLE_TYPE_TRAINER | BATTLE_TYPE_FRONTIER;
    if (format == CFRU_FACILITY_DOUBLE_4V4)
        gBattleTypeFlags |= BATTLE_TYPE_DOUBLE;
    else if (format == CFRU_FACILITY_NPC_PARTNER_MULTI)
        gBattleTypeFlags |= BATTLE_TYPE_DOUBLE | BATTLE_TYPE_TWO_OPPONENTS
                          | BATTLE_TYPE_INGAME_PARTNER;
    /* These are CFRU dispatch IDs, never indexes into Vega's gTrainers. */
    gTrainerBattleOpponent_A = BATTLE_TOWER_TID;
    gTrainerBattleOpponent_B = BATTLE_TOWER_TID;
    gTrainerBattlePartner = format == CFRU_FACILITY_NPC_PARTNER_MULTI
        ? BATTLE_FACILITY_MULTI_TRAINER_TID : 0;
    return TRUE;
}

bool8 VegaConfigureNextMirageItem(u8 party_index, u16 virtual_item)
{
    if (!VegaEnsurePendingPolicyStorage())
        return FALSE;
    return (bool8)cfru_integration_pending_configure_mirage(
        (cfru_u8)party_index, (cfru_u16)virtual_item);
}

bool8 VegaConfigureNextRaid(
    u8 boss_party_index,
    u8 partner_mask,
    u8 shield_count,
    u8 turn_limit,
    u8 capture_allowed
)
{
    u32 route_mask = BATTLE_TYPE_TRAINER | BATTLE_TYPE_FRONTIER
                   | BATTLE_TYPE_TWO_OPPONENTS | BATTLE_TYPE_MULTI
                   | BATTLE_TYPE_LINK;

    if (!VegaEnsurePendingPolicyStorage()
        || !cfru_integration_pending_configure_raid(
            (cfru_u8)boss_party_index,
            (cfru_u8)partner_mask,
            (cfru_u8)shield_count,
            (cfru_u8)turn_limit,
            (cfru_u8)capture_allowed))
        return FALSE;

    gBattleTypeFlags &= ~route_mask;
    gBattleTypeFlags |= BATTLE_TYPE_DYNAMAX;
    if (partner_mask != 0)
        gBattleTypeFlags |= BATTLE_TYPE_DOUBLE | BATTLE_TYPE_INGAME_PARTNER;
    else
        gBattleTypeFlags &= ~(BATTLE_TYPE_DOUBLE | BATTLE_TYPE_INGAME_PARTNER);
    return TRUE;
}

bool8 VegaBattlePolicyIsRaid(void)
{
    CfruPendingBattleCommand pending;
    const CfruIntegrationState *policy;

    if (gBattleTypeFlags & BATTLE_TYPE_TRAINER)
        return FALSE;
    if (cfru_integration_pending_copy(&pending))
        return (bool8)(pending.active && pending.raid_active);
    if (gNewBS != (void *)0)
    {
        policy = cfru_integration_state();
        if (policy->battle_active)
            return (bool8)policy->raid.active;
        return (bool8)(policy->pending.active && policy->pending.raid_active);
    }
    return FALSE;
}

bool8 VegaBattlePolicyRaidCaptureAllowed(void)
{
    CfruPendingBattleCommand pending;
    const CfruIntegrationState *policy;

    if (!VegaBattlePolicyIsRaid())
        return FALSE;
    if (cfru_integration_pending_copy(&pending))
        return (bool8)pending.raid_capture_allowed;
    if (gNewBS != (void *)0)
    {
        policy = cfru_integration_state();
        if (policy->battle_active)
            return (bool8)policy->raid.capture_allowed;
        return (bool8)(policy->pending.active
                       && policy->pending.raid_capture_allowed);
    }
    return FALSE;
}

bool8 VegaBattlePolicyRaidCaptureSucceeded(void)
{
    if (!VegaBattlePolicyIsRaid())
        return FALSE;
    return (bool8)cfru_integration_raid_try_capture();
}

bool8 VegaBattlePolicyRaidAdvanceTurnAndExpired(void)
{
    const CfruIntegrationState *policy;

    if (!VegaBattlePolicyIsRaid()
        || !cfru_integration_raid_advance_turn())
        return FALSE;
    policy = cfru_integration_state();
    return (bool8)(policy->raid.end_reason == CFRU_RAID_END_TURN_LIMIT);
}

static void VegaBattlePolicyPreparePartyTeraTypes(
    struct Pokemon *party,
    cfru_u8 backup[CFRU_PARTY_SIZE]
)
{
    u8 index;

    for (index = 0; index < PARTY_SIZE; ++index)
    {
        u16 species;

        backup[index] = party[index].teratype;
        species = GetMonData(&party[index], MON_DATA_SPECIES2, NULL);
        if (species > SPECIES_NONE && species < SPECIES_EGG)
            party[index].teratype = GetSpeciesTeraType(species);
    }
}

bool8 VegaBattlePolicyPrepareTeraTypes(void)
{
    CfruIntegrationState *policy;
    u32 saved_rng;

    if (gNewBS == NULL || !cfru_integration_state()->battle_active)
        return FALSE;
    policy = cfru_integration_mutable_state();
    if (policy->tera_type_backup.active)
        return TRUE;
    if (policy->mechanic.battle_mode != CFRU_MECHANIC_TERASTAL)
        return FALSE;

    saved_rng = gRngValue;
    VegaBattlePolicyPreparePartyTeraTypes(
        gPlayerParty, policy->tera_type_backup.player);
    VegaBattlePolicyPreparePartyTeraTypes(
        gEnemyParty, policy->tera_type_backup.opponent);
    gRngValue = saved_rng;
    policy->tera_type_backup.active = TRUE;
    return TRUE;
}

bool8 VegaBattlePolicyRestoreTeraTypes(void)
{
    CfruIntegrationState *policy;
    u8 index;

    if (gNewBS == NULL)
        return TRUE;
    policy = cfru_integration_mutable_state();
    if (!policy->tera_type_backup.active)
        return TRUE;
    for (index = 0; index < PARTY_SIZE; ++index)
    {
        gPlayerParty[index].teratype = policy->tera_type_backup.player[index];
        gEnemyParty[index].teratype = policy->tera_type_backup.opponent[index];
    }
    policy->tera_type_backup.active = FALSE;
    return TRUE;
}

void VegaBattlePolicyRestoreCapturedTeraType(struct Pokemon *mon)
{
    CfruIntegrationState *policy;
    u8 index;

    if (gNewBS == NULL || mon == NULL)
        return;
    policy = cfru_integration_mutable_state();
    if (!policy->tera_type_backup.active)
        return;
    for (index = 0; index < PARTY_SIZE; ++index)
    {
        if (mon == &gEnemyParty[index])
        {
            mon->teratype = policy->tera_type_backup.opponent[index];
            return;
        }
    }
}

u8 VegaGiveCaughtMonToPlayer(struct Pokemon *mon)
{
    typedef u8 (*VegaGiveMonToPlayerFn)(struct Pokemon *);

    /* Preserve CFRU's modern-form cleanup before crossing to Vega's
     * stock 100-byte party / 80-byte boxed-mon storage ABI. */
    TryFormRevert(mon);
    TryRevertMega(mon);
    TryRevertGigantamax(mon);
    TryRevertTerastalForm(mon);
    VegaBattlePolicyRestoreCapturedTeraType(mon);
    return ((VegaGiveMonToPlayerFn)(__UINTPTR_TYPE__)0x08040209u)(mon);
}

bool8 VegaBattlePolicyPrepareStorage(void)
{
    CfruPendingBattleCommand pending = {0};
    bool8 present;

    present = (bool8)cfru_integration_pending_take(&pending);
    if (!cfru_integration_pending_mark_transferred())
        return FALSE;
    gNewBS = Calloc(sizeof(struct NewBattleStruct));
    if (gNewBS == (void *)0)
    {
        cfru_integration_pending_clear();
        return FALSE;
    }

    if (!present)
        return TRUE;
    if (!cfru_integration_pending_restore(&pending))
    {
        cfru_integration_pending_clear();
        return FALSE;
    }
    return TRUE;
}

bool8 VegaBattlePolicyBegin(void)
{
    bool8 raid_ready;
    cfru_u8 opponent_profile;
    CfruMechanicMode mechanic_mode;
    cfru_u32 boss_hp;
    cfru_u32 boss_max_hp;
    const CfruIntegrationState *policy;
    CfruPendingBattleCommand pending;
    u16 facility_values[11];
    u8 facility_index;
    u8 party_index;
    CfruFacilityFormat facility_format;
    CfruFacilityRule facility_rule;
    bool8 facility_ready;

    /*
     * HandleNewBattleRamClearBeforeBattle has already allocated/cleared CFRU
     * battle RAM and added BATTLE_TYPE_DYNAMAX for a real Raid.  It has not
     * initialized controllers, so this function intentionally never reads
     * gBattlersCount.
     */
    policy = cfru_integration_state();
    pending = policy->pending;
    opponent_profile = CFRU_AI_BASIC;
    raid_ready = (bool8)(pending.active && pending.raid_active);
    for (facility_index = 0; facility_index < 11; ++facility_index)
        facility_values[facility_index] = pending.facility_state[facility_index];
    if (pending.active && cfru_ai_profile_is_valid(pending.ai_profile))
        opponent_profile = pending.ai_profile;
    mechanic_mode = CFRU_MECHANIC_STANDARD;
    if (pending.active && pending.mechanic_mode <= CFRU_MECHANIC_TERASTAL)
        mechanic_mode = (CfruMechanicMode)pending.mechanic_mode;
    facility_ready = (bool8)(
        pending.active && pending.facility_active);
    if ((gBattleTypeFlags & BATTLE_TYPE_TRAINER)
        && !(gBattleTypeFlags & BATTLE_TYPE_FRONTIER)
        && !facility_ready
        && !(pending.active && cfru_ai_profile_is_valid(pending.ai_profile)))
        opponent_profile = VegaNormalizeTrainerAIProfile(
            gTrainers[gTrainerBattleOpponent_A].aiFlags);
    facility_format = (CfruFacilityFormat)pending.facility_format;
    facility_rule = (CfruFacilityRule)pending.facility_rule;
    if (!cfru_integration_battle_begin(
            CFRU_AI_BASIC,
            raid_ready ? CFRU_AI_FULL_SMART : opponent_profile))
        return FALSE;

    if (facility_ready)
    {
        if (!cfru_integration_facility_begin(
                facility_format,
                facility_rule))
        {
            (void)cfru_integration_battle_end(CFRU_EXIT_ERROR);
            return FALSE;
        }
        for (facility_index = 0; facility_index < 11; ++facility_index)
            cfru_integration_facility_state_set(
                (cfru_u8)facility_index,
                (cfru_u16)facility_values[facility_index]);
        gBattleTypeFlags |= BATTLE_TYPE_FRONTIER;
    }

    for (party_index = 0; party_index < PARTY_SIZE; ++party_index)
    {
        if ((pending.mirage_mask & (1u << party_index))
            && !cfru_integration_mirage_begin(
                (cfru_u8)party_index,
                (cfru_u16 *)&gEnemyParty[party_index].item,
                pending.mirage_virtual_items[party_index]))
        {
            (void)cfru_integration_battle_end(CFRU_EXIT_ERROR);
            return FALSE;
        }
    }

    if (!raid_ready)
    {
        if (mechanic_mode != CFRU_MECHANIC_STANDARD
            && !cfru_integration_select_mechanic(
                mechanic_mode, CFRU_SIDE_OPPONENT))
        {
            (void)cfru_integration_battle_end(CFRU_EXIT_ERROR);
            return FALSE;
        }
        if (mechanic_mode == CFRU_MECHANIC_TERASTAL
            && !VegaBattlePolicyPrepareTeraTypes())
        {
            (void)cfru_integration_battle_end(CFRU_EXIT_ERROR);
            return FALSE;
        }
        return TRUE;
    }

    gBattleTypeFlags |= BATTLE_TYPE_DYNAMAX;
    if (pending.raid_partner_mask != 0)
        gBattleTypeFlags |= BATTLE_TYPE_DOUBLE | BATTLE_TYPE_INGAME_PARTNER;
    boss_hp = (cfru_u32)gEnemyParty[pending.raid_boss_party_index].hp;
    boss_max_hp = (cfru_u32)gEnemyParty[pending.raid_boss_party_index].maxHP;

    if (!cfru_integration_raid_begin(
            CFRU_SIDE_OPPONENT,
            pending.raid_boss_party_index,
            pending.raid_partner_mask,
            pending.raid_shield_count,
            boss_hp,
            boss_max_hp,
            pending.raid_turn_limit,
            pending.raid_capture_allowed))
    {
        (void)cfru_integration_battle_end(CFRU_EXIT_ERROR);
        return FALSE;
    }

    return TRUE;
}

CfruBattleExit VegaBattlePolicyMapOutcome(u8 outcome)
{
    if (outcome & B_OUTCOME_LINK_BATTLE_RAN)
        return CFRU_EXIT_RAN;

    switch (outcome)
    {
        case B_OUTCOME_WON:
            return CFRU_EXIT_WON;
        case B_OUTCOME_LOST:
        case B_OUTCOME_DREW:
        case B_OUTCOME_NO_SAFARI_BALLS:
            return CFRU_EXIT_LOST;
        case B_OUTCOME_RAN:
        case B_OUTCOME_PLAYER_TELEPORTED:
        case B_OUTCOME_MON_FLED:
        case B_OUTCOME_MON_TELEPORTED:
            return CFRU_EXIT_RAN;
        case B_OUTCOME_FORFEITED:
            return CFRU_EXIT_FORFEIT;
        case B_OUTCOME_CAUGHT:
            return CFRU_EXIT_CAPTURED;
        default:
            return CFRU_EXIT_ERROR;
    }
}

bool8 VegaBattlePolicyEnd(void)
{
    bool8 ended;
    bool8 wasRaid = VegaBattlePolicyIsRaid();

    (void)VegaBattlePolicyRestoreTeraTypes();
    ended = (bool8)cfru_integration_battle_end(
        VegaBattlePolicyMapOutcome(gBattleOutcome));
    if (ended && wasRaid)
    {
        gBattleTypeFlags &= ~(BATTLE_TYPE_DYNAMAX
                            | BATTLE_TYPE_DOUBLE
                            | BATTLE_TYPE_INGAME_PARTNER);
    }
    return ended;
}

bool8 VegaFacilityStateIsActive(void)
{
    if (cfru_integration_pending_facility_is_active())
        return TRUE;
    if (gNewBS != (void *)0)
    {
        const CfruIntegrationState *policy = cfru_integration_state();
        if (policy->battle_active)
            return (bool8)policy->facility.active;
        if (cfru_integration_pending_is_transferred())
            return (bool8)(policy->pending.active
                           && policy->pending.facility_active);
    }
    return (bool8)cfru_integration_pending_facility_is_active();
}

u16 VegaFacilityStateGet(u16 field)
{
    if (field > 10u)
        return 0;
    if (cfru_integration_pending_facility_is_active())
        return (u16)cfru_integration_pending_facility_get((cfru_u8)field);
    if (gNewBS != (void *)0)
    {
        const CfruIntegrationState *policy = cfru_integration_state();
        if (policy->battle_active)
            return (u16)cfru_integration_facility_state_get((cfru_u8)field);
        if (cfru_integration_pending_is_transferred()
            && policy->pending.active
            && policy->pending.facility_active)
            return policy->pending.facility_state[field];
    }
    if (!VegaFacilityStateIsActive())
        return 0;
    return (u16)cfru_integration_pending_facility_get((cfru_u8)field);
}

void VegaFacilityStateSet(u16 field, u16 value)
{
    if (field > 10u)
        return;
    if (cfru_integration_pending_facility_is_active())
        cfru_integration_pending_facility_set((cfru_u8)field,
                                              (cfru_u16)value);
    else if (gNewBS != (void *)0 && cfru_integration_state()->battle_active)
        cfru_integration_facility_state_set((cfru_u8)field, (cfru_u16)value);
    else if (gNewBS != (void *)0
             && cfru_integration_pending_is_transferred()
             && cfru_integration_state()->pending.active
             && cfru_integration_state()->pending.facility_active)
        cfru_integration_mutable_state()->pending.facility_state[field] =
            (cfru_u16)value;
    else if (VegaFacilityStateIsActive())
        cfru_integration_pending_facility_set((cfru_u8)field, (cfru_u16)value);
}

u16 VegaFacilitySecondOpponent(void)
{
    return VegaFacilityStateIsActive() ? BATTLE_TOWER_TID : 0;
}

u16 VegaFacilityFirstOpponent(void)
{
    return VegaFacilityStateIsActive() ? BATTLE_TOWER_TID : 0;
}

u16 VegaFacilityPartner(void)
{
    if (VegaFacilityStateIsActive())
        return BATTLE_FACILITY_MULTI_TRAINER_TID;
    if (VegaBattlePolicyIsRaid())
        return RAID_BATTLE_MULTI_TRAINER_TID;
    return 0;
}

u32 VegaBattlePolicyResolveAIProfileBits(u8 battler, u32 fallback)
{
    cfru_u8 side;
    cfru_u8 profile;

    if (!VegaBattlePolicyBattlerSide(battler, &side))
        return fallback;

    /* Safari/roaming/tutorial/facility-owned high bits remain authoritative. */
    if (fallback & ~7u)
        return fallback;

    profile = cfru_integration_ai_profile(side);
    if (profile != CFRU_AI_BASIC
        && profile != CFRU_AI_SEMI_SMART
        && profile != CFRU_AI_FULL_SMART)
        return fallback;

    if ((gBattleTypeFlags & BATTLE_TYPE_TRAINER) || fallback == 0)
        return (u32)profile;
    return fallback;
}

bool8 VegaBattlePolicyCanMega(u8 battler, bool8 upstream_allowed)
{
    return VegaBattlePolicyCanMechanic(
        battler, upstream_allowed, CFRU_MECHANIC_MEGA);
}

bool8 VegaBattlePolicyMarkMega(u8 battler)
{
    return VegaBattlePolicyMarkMechanic(battler, CFRU_MECHANIC_MEGA);
}

bool8 VegaBattlePolicyCanZ(u8 battler, bool8 upstream_allowed)
{
    return VegaBattlePolicyCanMechanic(
        battler, upstream_allowed, CFRU_MECHANIC_Z_MOVE);
}

bool8 VegaBattlePolicyMarkZ(u8 battler)
{
    return VegaBattlePolicyMarkMechanic(battler, CFRU_MECHANIC_Z_MOVE);
}

bool8 VegaBattlePolicyCanDynamax(u8 battler, bool8 upstream_allowed)
{
    return VegaBattlePolicyCanMechanic(
        battler, upstream_allowed, CFRU_MECHANIC_DYNAMAX);
}

bool8 VegaBattlePolicyMarkDynamax(u8 battler)
{
    return VegaBattlePolicyMarkMechanic(battler, CFRU_MECHANIC_DYNAMAX);
}

bool8 VegaBattlePolicyCanTera(u8 battler, bool8 upstream_allowed)
{
    return VegaBattlePolicyCanMechanic(
        battler, upstream_allowed, CFRU_MECHANIC_TERASTAL);
}

bool8 VegaBattlePolicyMarkTera(u8 battler)
{
    return VegaBattlePolicyMarkMechanic(battler, CFRU_MECHANIC_TERASTAL);
}
