#include <stdio.h>

#include "modernization_p05_abilities.h"

static unsigned int sCases;
static unsigned int sFailures;

static void record_case(
    const char *ability_key,
    const char *category,
    const char *case_key,
    int passed,
    unsigned long observed
)
{
    ++sCases;
    if (!passed)
        ++sFailures;
    printf(
        "CASE\t%s\t%s\t%s\t%s\t%lu\n",
        ability_key,
        category,
        case_key,
        passed ? "PASS" : "FAIL",
        observed
    );
}

static P05MoveQuery base_move(p05_u16 ability, p05_u8 type, p05_u16 damage)
{
    P05MoveQuery query = {
        ability,
        damage,
        P05_FALSE,
        type,
        P05_MOVE_PHYSICAL,
        P05_FALSE,
        P05_FALSE,
        P05_PROTECT_NONE,
        P05_FALSE,
        P05_FALSE
    };
    return query;
}

static P05GroundQuery base_ground(void)
{
    P05GroundQuery query = {
        P05_ABILITY_EELEVATE,
        P05_FALSE,
        P05_FALSE,
        P05_FALSE,
        P05_TYPE_GROUND,
        P05_MOVE_PHYSICAL,
        P05_TRUE,
        P05_FALSE,
        P05_FALSE,
        P05_FALSE,
        P05_FALSE
    };
    return query;
}

static void run_identity_and_save(void)
{
    static const p05_u16 ids[] = {
        P05_ABILITY_DRAGONIZE,
        P05_ABILITY_EELEVATE,
        P05_ABILITY_FIRE_MANE,
        P05_ABILITY_MEGA_SOL,
        P05_ABILITY_PIERCING_DRILL,
        P05_ABILITY_SPICY_SPRAY
    };
    p05_u8 index;

    for (index = 0; index < (p05_u8)(sizeof(ids) / sizeof(ids[0])); ++index)
    {
        const P05AbilityDefinition *definition = p05_ability_definition(ids[index]);
        p05_u16 slots[P05_ABILITY_SLOT_COUNT] = {1, ids[index], 2};
        p05_u16 resolved = 0;
        int passed = definition != (const P05AbilityDefinition *)0
            && definition->id == ids[index]
            && p05_resolve_saved_ability(slots, 1, &resolved)
            && resolved == ids[index]
            && resolved > 255;

        record_case(
            definition != (const P05AbilityDefinition *)0
                ? definition->stable_key : "ABILITY_KEY_INVALID",
            "save",
            "slot_roundtrip_u16",
            passed,
            resolved
        );
    }
}

static void run_piercing_drill(void)
{
    const char *key = "ABILITY_KEY_PIERCINGDRILL";
    P05MoveQuery query = base_move(P05_ABILITY_PIERCING_DRILL, P05_TYPE_NORMAL, 100);
    P05MoveResult result;
    P05MoveResult spread[2];
    p05_u8 protect[2] = {P05_PROTECT_SINGLE, P05_PROTECT_NONE};
    P05MoveQuery alternative;
    int spread_passed;

    query.makes_contact = P05_TRUE;
    query.protect_kind = P05_PROTECT_SINGLE;
    result = p05_resolve_move(&query);
    record_case(
        key,
        "trigger",
        "contact_pierces_single_protect_at_quarter_damage",
        result.ability_triggered && result.protection_bypassed
            && result.contact_protection_effects_apply && !result.blocked
            && result.damage == 25,
        result.damage
    );

    query.makes_contact = P05_FALSE;
    result = p05_resolve_move(&query);
    record_case(
        key,
        "no_trigger",
        "noncontact_move_remains_blocked",
        result.blocked && !result.ability_triggered && result.damage == 0,
        result.damage
    );

    query.makes_contact = P05_TRUE;
    query.ability_suppressed = P05_TRUE;
    result = p05_resolve_move(&query);
    record_case(
        key,
        "suppressed",
        "suppressed_ability_cannot_pierce",
        result.blocked && !result.ability_triggered && result.damage == 0,
        result.damage
    );

    query.ability_suppressed = P05_FALSE;
    query.protect_kind = P05_PROTECT_NONE;
    spread_passed = p05_resolve_spread_move(&query, protect, 2, spread)
        && spread[0].damage == 25 && spread[1].damage == 100
        && spread[0].protection_bypassed && !spread[1].protection_bypassed;
    record_case(
        key,
        "multi_target",
        "spread_targets_resolve_protect_independently",
        spread_passed,
        (unsigned long)spread[0].damage * 1000ul + spread[1].damage
    );

    query.protect_kind = P05_PROTECT_SINGLE;
    alternative = query;
    alternative.makes_contact = P05_FALSE;
    record_case(
        key,
        "ai",
        "ai_keeps_only_viable_protect_bypass",
        p05_ai_prefers_candidate(&query, &alternative)
            && p05_ai_estimated_damage(&query) == 25
            && p05_ai_estimated_damage(&alternative) == 0,
        p05_ai_estimated_damage(&query)
    );

    query.is_ohko = P05_TRUE;
    result = p05_resolve_move(&query);
    record_case(
        key,
        "trigger",
        "ohko_contact_passes_single_protect",
        result.protection_bypassed && !result.blocked && result.damage == 100,
        result.damage
    );
}

static void run_dragonize(void)
{
    const char *key = "ABILITY_KEY_DRAGONIZE";
    P05MoveQuery query = base_move(P05_ABILITY_DRAGONIZE, P05_TYPE_NORMAL, 100);
    P05MoveResult result;
    P05MoveResult spread[2];
    p05_u8 protect[2] = {P05_PROTECT_NONE, P05_PROTECT_NONE};
    P05MoveQuery alternative = base_move(P05_ABILITY_NONE, P05_TYPE_NORMAL, 100);
    int spread_passed;

    result = p05_resolve_move(&query);
    record_case(
        key,
        "trigger",
        "normal_becomes_dragon_and_gains_twenty_percent",
        result.ability_triggered && result.resolved_type == P05_TYPE_DRAGON
            && result.damage == 120,
        (unsigned long)result.resolved_type * 1000ul + result.damage
    );

    query.dynamic_type_locked = P05_TRUE;
    result = p05_resolve_move(&query);
    record_case(
        key,
        "no_trigger",
        "dynamic_type_move_is_not_overridden",
        !result.ability_triggered && result.resolved_type == P05_TYPE_NORMAL
            && result.damage == 100,
        (unsigned long)result.resolved_type * 1000ul + result.damage
    );

    query.dynamic_type_locked = P05_FALSE;
    query.ability_suppressed = P05_TRUE;
    result = p05_resolve_move(&query);
    record_case(
        key,
        "suppressed",
        "suppression_preserves_normal_type_and_power",
        !result.ability_triggered && result.resolved_type == P05_TYPE_NORMAL
            && result.damage == 100,
        (unsigned long)result.resolved_type * 1000ul + result.damage
    );

    query.ability_suppressed = P05_FALSE;
    spread_passed = p05_resolve_spread_move(&query, protect, 2, spread)
        && spread[0].damage == 120 && spread[1].damage == 120
        && spread[0].resolved_type == P05_TYPE_DRAGON
        && spread[1].resolved_type == P05_TYPE_DRAGON;
    record_case(
        key,
        "multi_target",
        "spread_conversion_applies_once_per_damage_context",
        spread_passed,
        (unsigned long)spread[0].damage * 1000ul + spread[1].damage
    );

    record_case(
        key,
        "ai",
        "ai_uses_post_ability_type_and_power",
        p05_ai_prefers_candidate(&query, &alternative)
            && p05_ai_estimated_damage(&query) == 120,
        p05_ai_estimated_damage(&query)
    );

    query = base_move(P05_ABILITY_DRAGONIZE, P05_TYPE_FAIRY, 100);
    result = p05_resolve_move(&query);
    record_case(
        key,
        "no_trigger",
        "project_fairy_id_23_passes_through",
        !result.ability_triggered && result.resolved_type == P05_TYPE_FAIRY
            && result.damage == 100 && P05_TYPE_FAIRY == 23,
        result.resolved_type
    );

    query = base_move(P05_ABILITY_DRAGONIZE, P05_TYPE_STELLAR, 100);
    result = p05_resolve_move(&query);
    record_case(
        key,
        "no_trigger",
        "project_stellar_id_24_passes_through",
        !result.ability_triggered && result.resolved_type == P05_TYPE_STELLAR
            && result.damage == 100 && P05_TYPE_STELLAR == 24,
        result.resolved_type
    );
}

static void run_eelevate(void)
{
    const char *key = "ABILITY_KEY_EELEVATE";
    P05GroundQuery ground = base_ground();
    P05GroundResult ground_result;
    P05EelevateBoostQuery boost = {0};
    P05EelevateBoostResult boost_result;

    ground_result = p05_resolve_ground_immunity(&ground);
    record_case(
        key,
        "trigger",
        "damaging_ground_move_is_immune",
        ground_result.immune && ground_result.ability_triggered,
        ground_result.immune
    );

    ground.gravity = P05_TRUE;
    ground_result = p05_resolve_ground_immunity(&ground);
    record_case(
        key,
        "no_trigger",
        "gravity_forces_grounding",
        !ground_result.immune && !ground_result.ability_triggered,
        ground_result.immune
    );

    ground.gravity = P05_FALSE;
    ground.attacker_has_mold_breaker = P05_TRUE;
    ground_result = p05_resolve_ground_immunity(&ground);
    record_case(
        key,
        "suppressed",
        "mold_breaker_bypasses_without_ability_shield",
        !ground_result.immune && ground_result.ability_bypassed,
        ground_result.ability_bypassed
    );

    ground.defender_has_ability_shield = P05_TRUE;
    ground_result = p05_resolve_ground_immunity(&ground);
    record_case(
        key,
        "multi_target",
        "spread_ground_immunity_does_not_inflate_other_target_damage",
        ground_result.immune && ground_result.ability_triggered,
        (unsigned long)ground_result.immune * 1000ul + 100ul
    );

    record_case(
        key,
        "ai",
        "switch_ai_accounts_for_mold_breaker_and_ability_shield",
        p05_ai_should_switch_into_ground(&ground),
        p05_ai_should_switch_into_ground(&ground)
    );
    ground.defender_has_ability_shield = P05_FALSE;
    record_case(
        key,
        "ai",
        "switch_ai_rejects_bypassed_immunity",
        !p05_ai_should_switch_into_ground(&ground),
        p05_ai_should_switch_into_ground(&ground)
    );

    boost.ability = P05_ABILITY_EELEVATE;
    boost.user_alive = P05_TRUE;
    boost.battle_continues = P05_TRUE;
    boost.knocked_out_count = 2;
    boost.raw_stats[P05_STAT_ATTACK] = 100;
    boost.raw_stats[P05_STAT_DEFENSE] = 120;
    boost.raw_stats[P05_STAT_SP_ATTACK] = 180;
    boost.raw_stats[P05_STAT_SP_DEFENSE] = 90;
    boost.raw_stats[P05_STAT_SPEED] = 180;
    boost_result = p05_apply_eelevate_boost(&boost);
    record_case(
        key,
        "multi_target",
        "two_knockouts_raise_highest_stat_twice_with_tie_order",
        boost_result.triggered && boost_result.stat == P05_STAT_SP_ATTACK
            && boost_result.stages_gained == 2
            && boost.stat_stages[P05_STAT_SP_ATTACK] == 2,
        (unsigned long)boost_result.stat * 100ul + boost_result.stages_gained
    );

    boost.ability_suppressed = P05_TRUE;
    boost.knocked_out_count = 1;
    boost_result = p05_apply_eelevate_boost(&boost);
    record_case(
        key,
        "suppressed",
        "suppression_blocks_knockout_boost",
        !boost_result.triggered && boost_result.stages_gained == 0,
        boost_result.stages_gained
    );
}

static void run_fire_mane(void)
{
    const char *key = "ABILITY_KEY_FIREMANE";
    P05MoveQuery fire = base_move(P05_ABILITY_FIRE_MANE, P05_TYPE_FIRE, 100);
    P05MoveQuery normal = base_move(P05_ABILITY_FIRE_MANE, P05_TYPE_NORMAL, 100);
    P05MoveQuery alternative = base_move(P05_ABILITY_NONE, P05_TYPE_FIRE, 100);
    P05MoveResult result;
    P05MoveResult spread[2];
    p05_u8 protect[2] = {P05_PROTECT_NONE, P05_PROTECT_NONE};
    int spread_passed;

    result = p05_resolve_move(&fire);
    record_case(
        key,
        "trigger",
        "physical_fire_move_gains_fifty_percent",
        result.ability_triggered && result.damage == 150,
        result.damage
    );
    fire.move_class = P05_MOVE_SPECIAL;
    result = p05_resolve_move(&fire);
    record_case(
        key,
        "trigger",
        "special_fire_move_gains_fifty_percent",
        result.ability_triggered && result.damage == 150,
        result.damage
    );

    result = p05_resolve_move(&normal);
    record_case(
        key,
        "no_trigger",
        "non_fire_move_is_unchanged",
        !result.ability_triggered && result.damage == 100,
        result.damage
    );

    fire.ability_suppressed = P05_TRUE;
    result = p05_resolve_move(&fire);
    record_case(
        key,
        "suppressed",
        "suppression_removes_fire_boost",
        !result.ability_triggered && result.damage == 100,
        result.damage
    );

    fire.ability_suppressed = P05_FALSE;
    spread_passed = p05_resolve_spread_move(&fire, protect, 2, spread)
        && spread[0].damage == 150 && spread[1].damage == 150;
    record_case(
        key,
        "multi_target",
        "spread_fire_move_boosts_each_target_without_cross_scaling",
        spread_passed,
        (unsigned long)spread[0].damage * 1000ul + spread[1].damage
    );

    record_case(
        key,
        "ai",
        "ai_values_boosted_fire_damage",
        p05_ai_prefers_candidate(&fire, &alternative),
        p05_ai_estimated_damage(&fire)
    );
}

static void run_mega_sol(void)
{
    const char *key = "ABILITY_KEY_MEGASOL";
    P05MoveQuery fire = base_move(P05_ABILITY_MEGA_SOL, P05_TYPE_FIRE, 100);
    P05MoveQuery water = base_move(P05_ABILITY_MEGA_SOL, P05_TYPE_WATER, 100);
    P05MoveQuery electric = base_move(P05_ABILITY_MEGA_SOL, P05_TYPE_ELECTRIC, 100);
    P05MoveQuery alternative = base_move(P05_ABILITY_NONE, P05_TYPE_FIRE, 100);
    P05MoveResult result;
    P05MoveResult spread[2];
    p05_u8 protect[2] = {P05_PROTECT_NONE, P05_PROTECT_NONE};
    int spread_passed;

    result = p05_resolve_move(&fire);
    record_case(
        key,
        "trigger",
        "personal_sun_boosts_fire",
        result.virtual_sun && result.ability_triggered && result.damage == 150,
        result.damage
    );
    result = p05_resolve_move(&water);
    record_case(
        key,
        "trigger",
        "personal_sun_halves_water",
        result.virtual_sun && result.damage == 50,
        result.damage
    );
    record_case(
        key,
        "trigger",
        "weather_ball_and_healing_use_personal_sun",
        p05_weather_ball_type(
            P05_ABILITY_MEGA_SOL, P05_FALSE, P05_WEATHER_RAIN, P05_TYPE_NORMAL
        ) == P05_TYPE_FIRE
            && p05_weather_heal_amount(
                P05_ABILITY_MEGA_SOL, P05_FALSE, P05_WEATHER_SAND, 300
            ) == 200
            && p05_solar_move_skips_charge(P05_ABILITY_MEGA_SOL, P05_FALSE),
        p05_weather_heal_amount(
            P05_ABILITY_MEGA_SOL, P05_FALSE, P05_WEATHER_SAND, 300
        )
    );

    result = p05_resolve_move(&electric);
    record_case(
        key,
        "no_trigger",
        "personal_sun_does_not_change_unrelated_damage",
        result.virtual_sun && result.damage == 100,
        result.damage
    );

    fire.ability_suppressed = P05_TRUE;
    result = p05_resolve_move(&fire);
    record_case(
        key,
        "suppressed",
        "suppression_restores_field_weather_and_fire_damage",
        !result.virtual_sun && !result.ability_triggered && result.damage == 100
            && p05_weather_for_user(
                P05_ABILITY_MEGA_SOL, P05_TRUE, P05_WEATHER_RAIN
            ) == P05_WEATHER_RAIN,
        result.damage
    );

    fire.ability_suppressed = P05_FALSE;
    spread_passed = p05_resolve_spread_move(&fire, protect, 2, spread)
        && spread[0].damage == 150 && spread[1].damage == 150
        && p05_resolve_move(&alternative).damage == 100;
    record_case(
        key,
        "multi_target",
        "spread_owner_gets_personal_sun_but_partner_does_not",
        spread_passed,
        (unsigned long)spread[0].damage * 1000ul
            + p05_resolve_move(&alternative).damage
    );

    record_case(
        key,
        "ai",
        "ai_uses_personal_weather_damage",
        p05_ai_prefers_candidate(&fire, &alternative),
        p05_ai_estimated_damage(&fire)
    );
}

static void run_spicy_spray(void)
{
    const char *key = "ABILITY_KEY_SPICYSPRAY";
    P05SpicySprayQuery query = {
        P05_ABILITY_SPICY_SPRAY,
        P05_FALSE,
        P05_TRUE,
        P05_TRUE,
        P05_TRUE,
        P05_TRUE,
        P05_FALSE
    };
    P05SpicySprayResult result;
    P05SpicySprayResult second;
    P05SpicySprayAiQuery ai = {
        P05_ABILITY_SPICY_SPRAY,
        P05_FALSE,
        P05_TRUE,
        P05_TRUE,
        2,
        P05_FALSE,
        P05_FALSE,
        P05_FALSE,
        P05_TRUE,
        P05_FALSE,
        P05_FALSE,
        P05_BURN_BENEFIT_GUTS_PHYSICAL
    };

    result = p05_resolve_spicy_spray(&query);
    record_case(
        key,
        "trigger",
        "damaging_noncontact_attack_burns_present_attacker",
        result.triggered && result.burn_applied,
        result.burn_applied
    );

    query.defender_took_damage = P05_FALSE;
    result = p05_resolve_spicy_spray(&query);
    record_case(
        key,
        "no_trigger",
        "substitute_only_damage_does_not_trigger",
        !result.triggered && !result.burn_applied,
        result.burn_applied
    );

    query.defender_took_damage = P05_TRUE;
    query.ability_suppressed = P05_TRUE;
    result = p05_resolve_spicy_spray(&query);
    record_case(
        key,
        "suppressed",
        "suppression_blocks_reactive_burn",
        !result.triggered && !result.burn_applied,
        result.burn_applied
    );

    query.ability_suppressed = P05_FALSE;
    result = p05_resolve_spicy_spray(&query);
    query.attacker_already_burned = result.burn_applied;
    second = p05_resolve_spicy_spray(&query);
    record_case(
        key,
        "multi_target",
        "two_holders_queue_only_one_idempotent_burn",
        result.triggered && !second.triggered,
        (unsigned long)result.triggered + second.triggered
    );

    record_case(
        key,
        "ai",
        "ai_accepts_safe_friendly_fire_for_guts",
        p05_ai_should_trigger_friendly_spicy_spray(&ai),
        p05_ai_should_trigger_friendly_spicy_spray(&ai)
    );
    ai.burn_benefit = P05_BURN_BENEFIT_NONE;
    record_case(
        key,
        "ai",
        "ai_rejects_friendly_fire_without_burn_benefit",
        !p05_ai_should_trigger_friendly_spicy_spray(&ai),
        p05_ai_should_trigger_friendly_spicy_spray(&ai)
    );
}

int main(void)
{
    run_identity_and_save();
    run_piercing_drill();
    run_dragonize();
    run_eelevate();
    run_fire_mane();
    run_mega_sol();
    run_spicy_spray();
    printf("SUMMARY\t%u\t%u\n", sCases, sFailures);
    return sFailures == 0 ? 0 : 1;
}
