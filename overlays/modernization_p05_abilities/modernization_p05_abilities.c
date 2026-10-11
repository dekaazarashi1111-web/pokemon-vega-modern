#include "modernization_p05_abilities.h"

static const P05AbilityDefinition sP05AbilityDefinitions[] = {
    {
        P05_ABILITY_DRAGONIZE,
        "ABILITY_KEY_DRAGONIZE",
        "Dragonize",
        "Normal moves turn Dragon."
    },
    {
        P05_ABILITY_EELEVATE,
        "ABILITY_KEY_EELEVATE",
        "Eelevate",
        "Levitate and Beast Boost."
    },
    {
        P05_ABILITY_FIRE_MANE,
        "ABILITY_KEY_FIREMANE",
        "Fire Mane",
        "Ups Fire-type moves."
    },
    {
        P05_ABILITY_MEGA_SOL,
        "ABILITY_KEY_MEGASOL",
        "Mega Sol",
        "Acts like under sun."
    },
    {
        P05_ABILITY_PIERCING_DRILL,
        "ABILITY_KEY_PIERCINGDRILL",
        "Piercing Drill",
        "Contact evades protection."
    },
    {
        P05_ABILITY_SPICY_SPRAY,
        "ABILITY_KEY_SPICYSPRAY",
        "Spicy Spray",
        "Burns the foe when damaged."
    }
};

enum {
    P05_ABILITY_DEFINITION_COUNT =
        sizeof(sP05AbilityDefinitions) / sizeof(sP05AbilityDefinitions[0])
};

static p05_u8 p05_bool_is_valid(p05_u8 value)
{
    return (p05_u8)(value <= P05_TRUE);
}

static p05_u8 p05_move_query_is_valid(const P05MoveQuery *query)
{
    return (p05_u8)(query != (const P05MoveQuery *)0
        && query->base_type < P05_TYPE_COUNT
        && query->move_class <= P05_MOVE_SPECIAL
        && query->protect_kind <= P05_PROTECT_MAX_GUARD
        && p05_bool_is_valid(query->ability_suppressed)
        && p05_bool_is_valid(query->dynamic_type_locked)
        && p05_bool_is_valid(query->makes_contact)
        && p05_bool_is_valid(query->ignores_protect)
        && p05_bool_is_valid(query->is_ohko));
}

static p05_u16 p05_scale_damage(p05_u16 damage, p05_u16 numerator, p05_u16 denominator)
{
    p05_u32 scaled;

    if (damage == 0 || numerator == 0 || denominator == 0)
        return 0;
    scaled = ((p05_u32)damage * numerator) / denominator;
    if (scaled == 0)
        scaled = 1;
    if (scaled > 65535u)
        scaled = 65535u;
    return (p05_u16)scaled;
}

const P05AbilityDefinition *p05_ability_definition(p05_u16 ability)
{
    p05_u8 index;

    for (index = 0; index < P05_ABILITY_DEFINITION_COUNT; ++index)
    {
        if (sP05AbilityDefinitions[index].id == ability)
            return &sP05AbilityDefinitions[index];
    }
    return (const P05AbilityDefinition *)0;
}

p05_u8 p05_ability_id_is_new(p05_u16 ability)
{
    return (p05_u8)(p05_ability_definition(ability) !=
        (const P05AbilityDefinition *)0);
}

p05_u16 p05_effective_ability(p05_u16 ability, p05_u8 suppressed)
{
    if (!p05_bool_is_valid(suppressed) || suppressed)
        return P05_ABILITY_NONE;
    return ability;
}

p05_u8 p05_weather_for_user(
    p05_u16 ability,
    p05_u8 suppressed,
    p05_u8 field_weather
)
{
    if (p05_effective_ability(ability, suppressed) == P05_ABILITY_MEGA_SOL)
        return P05_WEATHER_SUN;
    return field_weather;
}

p05_u8 p05_weather_ball_type(
    p05_u16 ability,
    p05_u8 suppressed,
    p05_u8 field_weather,
    p05_u8 base_type
)
{
    p05_u8 weather = p05_weather_for_user(ability, suppressed, field_weather);

    if ((weather & P05_WEATHER_SUN) != 0)
        return P05_TYPE_FIRE;
    if ((weather & P05_WEATHER_RAIN) != 0)
        return P05_TYPE_WATER;
    if ((weather & P05_WEATHER_SAND) != 0)
        return P05_TYPE_ROCK;
    if ((weather & P05_WEATHER_SNOW) != 0)
        return P05_TYPE_ICE;
    return base_type;
}

p05_u16 p05_weather_heal_amount(
    p05_u16 ability,
    p05_u8 suppressed,
    p05_u8 field_weather,
    p05_u16 max_hp
)
{
    p05_u8 weather = p05_weather_for_user(ability, suppressed, field_weather);

    if ((weather & P05_WEATHER_SUN) != 0)
        return (p05_u16)(((p05_u32)max_hp * 2u) / 3u);
    if (weather != P05_WEATHER_NONE)
        return (p05_u16)(max_hp / 4u);
    return (p05_u16)(max_hp / 2u);
}

p05_u8 p05_solar_move_skips_charge(p05_u16 ability, p05_u8 suppressed)
{
    return (p05_u8)(p05_effective_ability(ability, suppressed)
        == P05_ABILITY_MEGA_SOL);
}

P05MoveResult p05_resolve_move(const P05MoveQuery *query)
{
    P05MoveResult result = {0, P05_TYPE_MYSTERY, P05_FALSE, P05_TRUE,
                            P05_FALSE, P05_FALSE, P05_FALSE};
    p05_u16 ability;

    if (!p05_move_query_is_valid(query))
        return result;

    result.damage = query->base_damage;
    result.resolved_type = query->base_type;
    result.blocked = P05_FALSE;
    ability = p05_effective_ability(query->ability, query->ability_suppressed);

    if (ability == P05_ABILITY_DRAGONIZE
        && query->base_type == P05_TYPE_NORMAL
        && !query->dynamic_type_locked)
    {
        result.resolved_type = P05_TYPE_DRAGON;
        result.damage = p05_scale_damage(result.damage, 6, 5);
        result.ability_triggered = P05_TRUE;
    }
    else if (ability == P05_ABILITY_FIRE_MANE
        && result.resolved_type == P05_TYPE_FIRE)
    {
        result.damage = p05_scale_damage(result.damage, 3, 2);
        result.ability_triggered = P05_TRUE;
    }
    else if (ability == P05_ABILITY_MEGA_SOL)
    {
        result.virtual_sun = P05_TRUE;
        result.ability_triggered = P05_TRUE;
        if (result.resolved_type == P05_TYPE_FIRE)
            result.damage = p05_scale_damage(result.damage, 3, 2);
        else if (result.resolved_type == P05_TYPE_WATER)
            result.damage = p05_scale_damage(result.damage, 1, 2);
    }

    if (query->protect_kind == P05_PROTECT_NONE || query->ignores_protect)
        return result;

    if (ability == P05_ABILITY_PIERCING_DRILL
        && query->makes_contact
        && query->protect_kind == P05_PROTECT_SINGLE)
    {
        result.ability_triggered = P05_TRUE;
        result.protection_bypassed = P05_TRUE;
        /* Pinned GEN_CHAMPIONS semantics retain the contact shield effect. */
        result.contact_protection_effects_apply = P05_TRUE;
        if (!query->is_ohko)
            result.damage = p05_scale_damage(result.damage, 1, 4);
        return result;
    }

    result.blocked = P05_TRUE;
    result.damage = 0;
    return result;
}

p05_u8 p05_resolve_spread_move(
    const P05MoveQuery *query,
    const p05_u8 *protect_kinds,
    p05_u8 target_count,
    P05MoveResult *results
)
{
    P05MoveQuery target_query;
    p05_u8 index;

    if (!p05_move_query_is_valid(query)
        || protect_kinds == (const p05_u8 *)0
        || results == (P05MoveResult *)0
        || target_count == 0
        || target_count > P05_MAX_SPREAD_TARGETS)
        return P05_FALSE;

    target_query = *query;
    for (index = 0; index < target_count; ++index)
    {
        if (protect_kinds[index] > P05_PROTECT_MAX_GUARD)
            return P05_FALSE;
        target_query.protect_kind = protect_kinds[index];
        results[index] = p05_resolve_move(&target_query);
    }
    return P05_TRUE;
}

p05_u16 p05_ai_estimated_damage(const P05MoveQuery *query)
{
    return p05_resolve_move(query).damage;
}

p05_u8 p05_ai_prefers_candidate(
    const P05MoveQuery *candidate,
    const P05MoveQuery *alternative
)
{
    if (!p05_move_query_is_valid(candidate) || !p05_move_query_is_valid(alternative))
        return P05_FALSE;
    return (p05_u8)(p05_ai_estimated_damage(candidate)
        > p05_ai_estimated_damage(alternative));
}

P05GroundResult p05_resolve_ground_immunity(const P05GroundQuery *query)
{
    P05GroundResult result = {P05_FALSE, P05_FALSE, P05_FALSE};
    p05_u8 bypassed;
    p05_u16 ability;

    if (query == (const P05GroundQuery *)0)
        return result;

    bypassed = (p05_u8)(query->attacker_has_mold_breaker
        && !query->defender_has_ability_shield);
    ability = p05_effective_ability(
        query->defender_ability,
        (p05_u8)(query->ability_suppressed || bypassed)
    );
    result.ability_bypassed = (p05_u8)(bypassed
        && query->defender_ability == P05_ABILITY_EELEVATE);

    if (ability != P05_ABILITY_EELEVATE
        || query->move_type != P05_TYPE_GROUND
        || query->move_class == P05_MOVE_STATUS
        || !query->attack_reached_target
        || query->iron_ball
        || query->gravity
        || query->rooted
        || query->smack_down)
        return result;

    result.immune = P05_TRUE;
    result.ability_triggered = P05_TRUE;
    return result;
}

p05_u8 p05_ai_should_switch_into_ground(const P05GroundQuery *query)
{
    return p05_resolve_ground_immunity(query).immune;
}

P05EelevateBoostResult p05_apply_eelevate_boost(P05EelevateBoostQuery *query)
{
    P05EelevateBoostResult result = {P05_FALSE, P05_STAT_ATTACK, 0};
    p05_u8 index;
    p05_u8 highest = P05_STAT_ATTACK;
    p05_u8 available;
    p05_u8 gained;

    if (query == (P05EelevateBoostQuery *)0
        || p05_effective_ability(query->ability, query->ability_suppressed)
            != P05_ABILITY_EELEVATE
        || !query->user_alive
        || !query->battle_continues
        || query->knocked_out_count == 0)
        return result;

    for (index = 0; index < P05_STAT_COUNT; ++index)
    {
        if (query->stat_stages[index] < -P05_MAX_STAT_STAGE
            || query->stat_stages[index] > P05_MAX_STAT_STAGE)
            return result;
        if (query->raw_stats[index] > query->raw_stats[highest])
            highest = index;
    }

    if (query->stat_stages[highest] >= P05_MAX_STAT_STAGE)
        return result;
    available = (p05_u8)(P05_MAX_STAT_STAGE - query->stat_stages[highest]);
    gained = query->knocked_out_count < available
        ? query->knocked_out_count : available;
    query->stat_stages[highest] = (p05_s8)(query->stat_stages[highest] + gained);
    result.triggered = P05_TRUE;
    result.stat = highest;
    result.stages_gained = gained;
    return result;
}

P05SpicySprayResult p05_resolve_spicy_spray(const P05SpicySprayQuery *query)
{
    P05SpicySprayResult result = {P05_FALSE, P05_FALSE};

    if (query == (const P05SpicySprayQuery *)0
        || p05_effective_ability(query->defender_ability, query->ability_suppressed)
            != P05_ABILITY_SPICY_SPRAY
        || !query->attacker_present
        || !query->attacker_alive
        || !query->defender_took_damage
        || !query->attacker_can_be_burned
        || query->attacker_already_burned)
        return result;

    result.triggered = P05_TRUE;
    result.burn_applied = P05_TRUE;
    return result;
}

p05_u8 p05_ai_should_trigger_friendly_spicy_spray(
    const P05SpicySprayAiQuery *query
)
{
    if (query == (const P05SpicySprayAiQuery *)0
        || p05_effective_ability(
            query->partner_ability,
            query->partner_ability_suppressed
        ) != P05_ABILITY_SPICY_SPRAY
        || !query->partner_present
        || !query->partner_staying_in
        || query->hits_to_knock_out_partner == 0
        || query->self_sacrifice_move
        || query->half_max_hp_recoil_move
        || query->partner_substitute_protected
        || !query->attacker_can_be_burned
        || query->attacker_has_flame_orb
        || query->attacker_has_usable_cure_berry)
        return P05_FALSE;

    return (p05_u8)(query->burn_benefit >= P05_BURN_BENEFIT_GUTS_PHYSICAL
        && query->burn_benefit <= P05_BURN_BENEFIT_FACADE);
}

p05_u8 p05_resolve_saved_ability(
    const p05_u16 species_abilities[P05_ABILITY_SLOT_COUNT],
    p05_u8 stored_slot,
    p05_u16 *resolved_ability
)
{
    if (species_abilities == (const p05_u16 *)0
        || resolved_ability == (p05_u16 *)0
        || stored_slot >= P05_ABILITY_SLOT_COUNT)
        return P05_FALSE;
    *resolved_ability = species_abilities[stored_slot];
    return P05_TRUE;
}
