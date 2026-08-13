#include "runtime.h"

static cfru_u8 cfru_side_is_valid(cfru_u8 side)
{
    return (cfru_u8)(side < CFRU_SIDE_COUNT);
}

static cfru_u8 cfru_mechanic_mode_is_valid(cfru_u8 mode)
{
    return (cfru_u8)(mode < CFRU_MECHANIC_MODE_COUNT);
}

cfru_u8 cfru_ai_profile_is_valid(cfru_u8 profile)
{
    return (cfru_u8)(profile == CFRU_AI_BASIC
        || profile == CFRU_AI_SEMI_SMART
        || profile == CFRU_AI_FULL_SMART);
}

cfru_u8 cfru_ai_profile_bits(CfruAiProfile profile)
{
    if (!cfru_ai_profile_is_valid((cfru_u8)profile))
        return 0;
    return (cfru_u8)profile;
}

void cfru_mechanic_cleanup(CfruMechanicState *state)
{
    cfru_u8 side;

    if (state == (CfruMechanicState *)0)
        return;

    state->active = CFRU_FALSE;
    state->battle_mode = CFRU_MECHANIC_STANDARD;
    for (side = 0; side < CFRU_SIDE_COUNT; ++side)
    {
        state->effective_mode[side] = CFRU_MECHANIC_STANDARD;
        state->used[side] = CFRU_FALSE;
        state->forced[side] = CFRU_FALSE;
    }
}

cfru_u8 cfru_mechanic_begin(
    CfruMechanicState *state,
    CfruMechanicMode mode,
    cfru_u8 raid_boss_side
)
{
    cfru_u8 side;

    if (state == (CfruMechanicState *)0
        || !cfru_mechanic_mode_is_valid((cfru_u8)mode)
        || (mode == CFRU_MECHANIC_RAID_HIGH_DIFFICULTY
            && !cfru_side_is_valid(raid_boss_side)))
        return CFRU_FALSE;

    cfru_mechanic_cleanup(state);
    state->active = CFRU_TRUE;
    state->battle_mode = (cfru_u8)mode;

    if (mode == CFRU_MECHANIC_RAID_HIGH_DIFFICULTY)
    {
        state->effective_mode[raid_boss_side] = CFRU_MECHANIC_DYNAMAX;
        state->forced[raid_boss_side] = CFRU_TRUE;
    }
    else if (mode != CFRU_MECHANIC_STANDARD)
    {
        for (side = 0; side < CFRU_SIDE_COUNT; ++side)
            state->effective_mode[side] = (cfru_u8)mode;
    }

    return CFRU_TRUE;
}

cfru_u8 cfru_mechanic_can_use(
    const CfruMechanicState *state,
    cfru_u8 side,
    CfruMechanicMode requested_mode
)
{
    if (state == (const CfruMechanicState *)0
        || !state->active
        || !cfru_side_is_valid(side)
        || !cfru_mechanic_mode_is_valid((cfru_u8)requested_mode)
        || requested_mode == CFRU_MECHANIC_STANDARD
        || requested_mode == CFRU_MECHANIC_RAID_HIGH_DIFFICULTY)
        return CFRU_FALSE;

    return (cfru_u8)(!state->used[side]
        && state->effective_mode[side] == (cfru_u8)requested_mode);
}

cfru_u8 cfru_mechanic_try_use(
    CfruMechanicState *state,
    cfru_u8 side,
    CfruMechanicMode requested_mode
)
{
    if (!cfru_mechanic_can_use(state, side, requested_mode))
        return CFRU_FALSE;

    state->used[side] = CFRU_TRUE;
    return CFRU_TRUE;
}

cfru_u8 cfru_mechanic_is_forced(const CfruMechanicState *state, cfru_u8 side)
{
    if (state == (const CfruMechanicState *)0
        || !state->active
        || !cfru_side_is_valid(side))
        return CFRU_FALSE;
    return (cfru_u8)(state->forced[side] != 0);
}

cfru_u8 cfru_stat_inputs_are_valid(const CfruStatInputs *inputs)
{
    cfru_u8 index;

    if (inputs == (const CfruStatInputs *)0
        || inputs->stored_nature >= CFRU_NATURE_COUNT
        || (inputs->mint_nature != CFRU_NATURE_UNSET
            && inputs->mint_nature >= CFRU_NATURE_COUNT)
        || inputs->ability_slot >= CFRU_ABILITY_SLOT_COUNT
        || (inputs->hyper_trained_mask & (cfru_u8)~((1u << CFRU_STAT_COUNT) - 1u)) != 0
        || inputs->exp_share_enabled > CFRU_TRUE)
        return CFRU_FALSE;

    for (index = 0; index < CFRU_STAT_COUNT; ++index)
    {
        if (inputs->iv[index] > 31)
            return CFRU_FALSE;
    }
    return CFRU_TRUE;
}

cfru_u8 cfru_stat_effective_nature(const CfruStatInputs *inputs)
{
    if (!cfru_stat_inputs_are_valid(inputs))
        return CFRU_NATURE_UNSET;
    if (inputs->mint_nature != CFRU_NATURE_UNSET)
        return inputs->mint_nature;
    return inputs->stored_nature;
}

cfru_u8 cfru_stat_effective_iv(const CfruStatInputs *inputs, cfru_u8 stat_index)
{
    if (!cfru_stat_inputs_are_valid(inputs) || stat_index >= CFRU_STAT_COUNT)
        return 0;
    if ((inputs->hyper_trained_mask & (cfru_u8)(1u << stat_index)) != 0)
        return 31;
    return inputs->iv[stat_index];
}

cfru_u8 cfru_stat_ability_slot(const CfruStatInputs *inputs)
{
    if (!cfru_stat_inputs_are_valid(inputs))
        return 0;
    return inputs->ability_slot;
}

cfru_u8 cfru_stat_receives_battle_exp(const CfruStatInputs *inputs, cfru_u8 participated)
{
    if (!cfru_stat_inputs_are_valid(inputs) || participated > CFRU_TRUE)
        return CFRU_FALSE;
    return (cfru_u8)(participated || inputs->exp_share_enabled);
}

static CfruCandyResult cfru_candy_result(cfru_u8 status)
{
    CfruCandyResult result;
    result.status = status;
    result.consumed = CFRU_FALSE;
    result.levels_gained = 0;
    result.reached_cap = CFRU_FALSE;
    result.experience_gained = 0;
    return result;
}

CfruCandyResult cfru_apply_exp_candy(
    CfruCandyTarget *selected_target,
    cfru_u32 candy_experience,
    cfru_u8 max_level,
    const cfru_u32 *experience_for_level,
    cfru_u16 experience_table_count
)
{
    CfruCandyResult result = cfru_candy_result(CFRU_CANDY_INVALID);
    cfru_u8 level;
    cfru_u32 cap_experience;
    cfru_u32 available;
    cfru_u32 gained;
    cfru_u32 updated_experience;

    if (selected_target == (CfruCandyTarget *)0
        || experience_for_level == (const cfru_u32 *)0
        || max_level == 0
        || max_level > CFRU_MAX_LEVEL
        || experience_table_count <= max_level
        || selected_target->level == 0
        || selected_target->level > max_level)
        return result;

    for (level = 1; level < max_level; ++level)
    {
        if (experience_for_level[level + 1] < experience_for_level[level])
            return result;
    }

    if (selected_target->level == max_level)
        return cfru_candy_result(CFRU_CANDY_AT_CAP);
    if (candy_experience == 0)
        return cfru_candy_result(CFRU_CANDY_NO_EFFECT);

    cap_experience = experience_for_level[max_level];
    if (selected_target->experience >= cap_experience)
        return cfru_candy_result(CFRU_CANDY_AT_CAP);

    available = cap_experience - selected_target->experience;
    gained = candy_experience < available ? candy_experience : available;
    if (gained == 0)
        return cfru_candy_result(CFRU_CANDY_NO_EFFECT);

    updated_experience = selected_target->experience + gained;
    level = selected_target->level;
    while (level < max_level && updated_experience >= experience_for_level[level + 1])
        ++level;

    result.status = CFRU_CANDY_APPLIED;
    result.consumed = CFRU_TRUE;
    result.levels_gained = (cfru_u8)(level - selected_target->level);
    result.reached_cap = (cfru_u8)(updated_experience == cap_experience);
    result.experience_gained = gained;
    selected_target->level = level;
    selected_target->experience = updated_experience;
    return result;
}

static void __attribute__((noinline)) cfru_trainer_mon_copy(
    CfruTrainerMon *output,
    const CfruTrainerMon *input
)
{
    output->species = input->species;
    output->item = input->item;
    output->level = input->level;
    output->nature = input->nature;
    output->ability_slot = input->ability_slot;
    output->moves[0] = input->moves[0];
    output->moves[1] = input->moves[1];
    output->moves[2] = input->moves[2];
    output->moves[3] = input->moves[3];

    /*
     * Keep these byte copies scalar.  The pinned ARM compiler otherwise
     * emits external memmove calls; the final mixed-ISA link resolves those
     * relocations as BLX encodings unsupported by the target ARM7TDMI.
     */
    output->iv[0] = input->iv[0];
    output->iv[1] = input->iv[1];
    output->iv[2] = input->iv[2];
    output->iv[3] = input->iv[3];
    output->iv[4] = input->iv[4];
    output->iv[5] = input->iv[5];
    output->ev[0] = input->ev[0];
    output->ev[1] = input->ev[1];
    output->ev[2] = input->ev[2];
    output->ev[3] = input->ev[3];
    output->ev[4] = input->ev[4];
    output->ev[5] = input->ev[5];
}

cfru_u8 cfru_trainer_build_apply(
    CfruTrainerMon *output,
    const CfruTrainerMon *base,
    const CfruTrainerBuildPatch *patch
)
{
    CfruTrainerMon candidate;
    cfru_u8 index;
    cfru_u16 ev_total = 0;
    const cfru_u8 stat_mask = (cfru_u8)((1u << CFRU_STAT_COUNT) - 1u);
    const cfru_u8 move_mask = (cfru_u8)((1u << CFRU_MOVE_SLOT_COUNT) - 1u);

    if (output == (CfruTrainerMon *)0
        || base == (const CfruTrainerMon *)0
        || patch == (const CfruTrainerBuildPatch *)0
        || (patch->present_fields & (cfru_u8)~CFRU_TRAINER_FIELD_MASK) != 0
        || (patch->iv_mask & (cfru_u8)~stat_mask) != 0
        || (patch->ev_mask & (cfru_u8)~stat_mask) != 0
        || (patch->move_mask & (cfru_u8)~move_mask) != 0)
        return CFRU_FALSE;

    cfru_trainer_mon_copy(&candidate, base);

    if ((patch->present_fields & CFRU_TRAINER_FIELD_LEVEL) != 0)
    {
        if (patch->level == 0 || patch->level > CFRU_MAX_LEVEL)
            return CFRU_FALSE;
        candidate.level = patch->level;
    }
    if ((patch->present_fields & CFRU_TRAINER_FIELD_NATURE) != 0)
    {
        if (patch->nature >= CFRU_NATURE_COUNT)
            return CFRU_FALSE;
        candidate.nature = patch->nature;
    }
    if ((patch->present_fields & CFRU_TRAINER_FIELD_ABILITY_SLOT) != 0)
    {
        if (patch->ability_slot >= CFRU_ABILITY_SLOT_COUNT)
            return CFRU_FALSE;
        candidate.ability_slot = patch->ability_slot;
    }
    if ((patch->present_fields & CFRU_TRAINER_FIELD_ITEM) != 0)
    {
        if (patch->item >= CFRU_ITEM_COUNT)
            return CFRU_FALSE;
        candidate.item = patch->item;
    }

    for (index = 0; index < CFRU_MOVE_SLOT_COUNT; ++index)
    {
        if ((patch->move_mask & (cfru_u8)(1u << index)) != 0)
        {
            if (patch->moves[index] >= CFRU_MOVE_COUNT)
                return CFRU_FALSE;
            candidate.moves[index] = patch->moves[index];
        }
    }
    for (index = 0; index < CFRU_STAT_COUNT; ++index)
    {
        if ((patch->iv_mask & (cfru_u8)(1u << index)) != 0)
        {
            if (patch->iv[index] > 31)
                return CFRU_FALSE;
            candidate.iv[index] = patch->iv[index];
        }
        if ((patch->ev_mask & (cfru_u8)(1u << index)) != 0)
        {
            if (patch->ev[index] > 252)
                return CFRU_FALSE;
            candidate.ev[index] = patch->ev[index];
        }
        ev_total = (cfru_u16)(ev_total + candidate.ev[index]);
    }
    if (ev_total > 510)
        return CFRU_FALSE;

    cfru_trainer_mon_copy(output, &candidate);
    return CFRU_TRUE;
}

cfru_u8 cfru_facility_begin(
    CfruFacilityBoundary *state,
    CfruFacilityFormat format,
    CfruFacilityRule rule
)
{
    if (state == (CfruFacilityBoundary *)0
        || (cfru_u8)format >= CFRU_FACILITY_FORMAT_COUNT
        || (cfru_u8)rule >= CFRU_FACILITY_RULE_COUNT)
        return CFRU_FALSE;
    state->active = CFRU_TRUE;
    state->format = (cfru_u8)format;
    state->rule = (cfru_u8)rule;
    return CFRU_TRUE;
}

cfru_u8 cfru_facility_allows_persistent_effect(
    const CfruFacilityBoundary *state,
    CfruPersistentEffect effect
)
{
    if (state == (const CfruFacilityBoundary *)0
        || (cfru_u8)effect >= CFRU_PERSISTENT_EFFECT_COUNT)
        return CFRU_FALSE;
    return (cfru_u8)(!state->active);
}

void cfru_facility_end(CfruFacilityBoundary *state)
{
    if (state == (CfruFacilityBoundary *)0)
        return;
    state->active = CFRU_FALSE;
    state->format = CFRU_FACILITY_SINGLE_3V3;
    state->rule = CFRU_FACILITY_RANDOM;
}

cfru_u8 cfru_mirage_item_begin(
    CfruMirageItemState *state,
    cfru_u16 persistent_item,
    cfru_u16 virtual_item
)
{
    if (state == (CfruMirageItemState *)0
        || state->active
        || persistent_item >= CFRU_ITEM_COUNT
        || virtual_item >= CFRU_ITEM_COUNT)
        return CFRU_FALSE;
    state->active = CFRU_TRUE;
    state->original_item = persistent_item;
    state->battle_item = virtual_item;
    return CFRU_TRUE;
}

cfru_u16 cfru_mirage_item_current(const CfruMirageItemState *state)
{
    if (state == (const CfruMirageItemState *)0)
        return 0;
    if (state->active)
        return state->battle_item;
    return state->original_item;
}

cfru_u8 cfru_mirage_item_set_battle_value(CfruMirageItemState *state, cfru_u16 item)
{
    if (state == (CfruMirageItemState *)0 || !state->active || item >= CFRU_ITEM_COUNT)
        return CFRU_FALSE;
    state->battle_item = item;
    return CFRU_TRUE;
}

cfru_u8 cfru_mirage_item_finish(
    CfruMirageItemState *state,
    CfruBattleExit exit_path,
    cfru_u16 *persistent_item
)
{
    cfru_u16 original_item;

    if (state == (CfruMirageItemState *)0
        || persistent_item == (cfru_u16 *)0
        || !state->active
        || (cfru_u8)exit_path >= CFRU_EXIT_COUNT)
        return CFRU_FALSE;

    original_item = state->original_item;
    *persistent_item = original_item;
    state->active = CFRU_FALSE;
    state->original_item = original_item;
    state->battle_item = original_item;
    return CFRU_TRUE;
}

static cfru_u8 cfru_count_bits(cfru_u8 value)
{
    cfru_u8 count = 0;
    while (value != 0)
    {
        count = (cfru_u8)(count + (value & 1u));
        value = (cfru_u8)(value >> 1);
    }
    return count;
}

void cfru_raid_cleanup(CfruRaidState *state)
{
    if (state == (CfruRaidState *)0)
        return;
    state->active = CFRU_FALSE;
    state->boss_side = CFRU_SIDE_OPPONENT;
    state->boss_party_index = 0;
    state->partner_mask = 0;
    state->shield_total = 0;
    state->shield_broken = 0;
    state->capture_allowed = CFRU_FALSE;
    state->captured = CFRU_FALSE;
    state->end_reason = CFRU_RAID_END_NONE;
    state->turn_limit = 0;
    state->turns_elapsed = 0;
    state->boss_hp = 0;
    state->boss_max_hp = 0;
}

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
)
{
    const cfru_u8 party_mask = (cfru_u8)((1u << CFRU_PARTY_SIZE) - 1u);

    if (state == (CfruRaidState *)0
        || !cfru_side_is_valid(boss_side)
        || boss_party_index >= CFRU_PARTY_SIZE
        || (partner_mask & (cfru_u8)~party_mask) != 0
        || cfru_count_bits(partner_mask) > CFRU_RAID_MAX_PARTNERS
        || shield_count > CFRU_RAID_MAX_SHIELDS
        || boss_hp == 0
        || boss_max_hp == 0
        || boss_hp > boss_max_hp
        || turn_limit == 0
        || capture_allowed > CFRU_TRUE)
        return CFRU_FALSE;

    cfru_raid_cleanup(state);
    state->active = CFRU_TRUE;
    state->boss_side = boss_side;
    state->boss_party_index = boss_party_index;
    state->partner_mask = partner_mask;
    state->shield_total = shield_count;
    state->capture_allowed = capture_allowed;
    state->turn_limit = turn_limit;
    state->boss_hp = boss_hp;
    state->boss_max_hp = boss_max_hp;
    return CFRU_TRUE;
}

cfru_u8 cfru_raid_partner_is_active(const CfruRaidState *state, cfru_u8 party_index)
{
    if (state == (const CfruRaidState *)0
        || !state->active
        || party_index >= CFRU_PARTY_SIZE)
        return CFRU_FALSE;
    return (cfru_u8)((state->partner_mask & (cfru_u8)(1u << party_index)) != 0);
}

cfru_u8 cfru_raid_shields_remaining(const CfruRaidState *state)
{
    if (state == (const CfruRaidState *)0 || !state->active)
        return 0;
    return (cfru_u8)(state->shield_total - state->shield_broken);
}

cfru_u8 cfru_raid_break_shield(CfruRaidState *state)
{
    if (state == (CfruRaidState *)0
        || !state->active
        || state->end_reason != CFRU_RAID_END_NONE
        || state->shield_broken >= state->shield_total)
        return CFRU_FALSE;
    ++state->shield_broken;
    return CFRU_TRUE;
}

cfru_u8 cfru_raid_set_boss_hp(CfruRaidState *state, cfru_u32 boss_hp)
{
    if (state == (CfruRaidState *)0
        || !state->active
        || state->end_reason != CFRU_RAID_END_NONE
        || boss_hp > state->boss_max_hp)
        return CFRU_FALSE;
    state->boss_hp = boss_hp;
    if (boss_hp == 0)
        state->end_reason = CFRU_RAID_END_BOSS_DEFEATED;
    return CFRU_TRUE;
}

cfru_u8 cfru_raid_advance_turn(CfruRaidState *state)
{
    if (state == (CfruRaidState *)0
        || !state->active
        || state->end_reason != CFRU_RAID_END_NONE)
        return CFRU_FALSE;
    ++state->turns_elapsed;
    if (state->turns_elapsed >= state->turn_limit)
        state->end_reason = CFRU_RAID_END_TURN_LIMIT;
    return CFRU_TRUE;
}

cfru_u8 cfru_raid_finish(CfruRaidState *state, CfruRaidEndReason reason)
{
    if (state == (CfruRaidState *)0
        || !state->active
        || state->end_reason != CFRU_RAID_END_NONE
        || reason <= CFRU_RAID_END_NONE
        || reason >= CFRU_RAID_END_REASON_COUNT
        || reason == CFRU_RAID_END_CAPTURED)
        return CFRU_FALSE;
    state->end_reason = (cfru_u8)reason;
    return CFRU_TRUE;
}

cfru_u8 cfru_raid_try_capture(CfruRaidState *state)
{
    if (state == (CfruRaidState *)0
        || !state->active
        || !state->capture_allowed
        || state->captured
        || state->end_reason != CFRU_RAID_END_BOSS_DEFEATED)
        return CFRU_FALSE;
    state->captured = CFRU_TRUE;
    state->end_reason = CFRU_RAID_END_CAPTURED;
    return CFRU_TRUE;
}
