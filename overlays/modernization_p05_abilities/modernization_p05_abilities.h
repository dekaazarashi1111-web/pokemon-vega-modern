#ifndef POKEMON_VEGA_MODERNIZATION_P05_ABILITIES_H
#define POKEMON_VEGA_MODERNIZATION_P05_ABILITIES_H

/*
 * P05 new-ability runtime checkpoint.
 *
 * This ABI is deliberately independent from both libc and an upstream engine
 * header.  The eventual Stage ROM adapter must translate its concrete battle
 * structures into these fixed-width values.  In particular, ability IDs are
 * u16: every ID in this slice is greater than 255.
 */
typedef unsigned char p05_u8;
typedef signed char p05_s8;
typedef unsigned short p05_u16;
typedef unsigned int p05_u32;

_Static_assert(sizeof(p05_u8) == 1, "p05_u8 must be 8-bit");
_Static_assert(sizeof(p05_s8) == 1, "p05_s8 must be 8-bit");
_Static_assert(sizeof(p05_u16) == 2, "p05_u16 must be 16-bit");
_Static_assert(sizeof(p05_u32) == 4, "p05_u32 must be 32-bit");

enum {
    P05_FALSE = 0,
    P05_TRUE = 1,
    P05_ABILITY_SLOT_COUNT = 3,
    P05_STAT_COUNT = 5,
    P05_MAX_STAT_STAGE = 6,
    P05_MAX_SPREAD_TARGETS = 4
};

/* Allocated by stable-key lexicographic order, not by upstream numeric ID. */
typedef enum P05AbilityId {
    P05_ABILITY_NONE = 0,
    P05_ABILITY_DRAGONIZE = 312,
    P05_ABILITY_EELEVATE = 313,
    P05_ABILITY_FIRE_MANE = 314,
    P05_ABILITY_MEGA_SOL = 315,
    P05_ABILITY_PIERCING_DRILL = 316,
    P05_ABILITY_SPICY_SPRAY = 317
} P05AbilityId;

_Static_assert(P05_ABILITY_DRAGONIZE > 255, "ability ABI must not narrow to u8");
_Static_assert(P05_ABILITY_SPICY_SPRAY <= 65535, "ability ABI must fit u16");

typedef enum P05Type {
    P05_TYPE_NORMAL = 0,
    P05_TYPE_FIGHTING = 1,
    P05_TYPE_FLYING = 2,
    P05_TYPE_POISON = 3,
    P05_TYPE_GROUND = 4,
    P05_TYPE_ROCK = 5,
    P05_TYPE_BUG = 6,
    P05_TYPE_GHOST = 7,
    P05_TYPE_STEEL = 8,
    P05_TYPE_MYSTERY = 9,
    P05_TYPE_FIRE = 10,
    P05_TYPE_WATER = 11,
    P05_TYPE_GRASS = 12,
    P05_TYPE_ELECTRIC = 13,
    P05_TYPE_PSYCHIC = 14,
    P05_TYPE_ICE = 15,
    P05_TYPE_DRAGON = 16,
    P05_TYPE_DARK = 17,
    /* 18..22 are real CFRU ABI holes/sentinels and must not be compacted. */
    P05_TYPE_RESERVED_18 = 18,
    P05_TYPE_ROOSTLESS = 19,
    P05_TYPE_BLANK = 20,
    P05_TYPE_RESERVED_21 = 21,
    P05_TYPE_RESERVED_22 = 22,
    P05_TYPE_FAIRY = 23,
    P05_TYPE_STELLAR = 24,
    P05_TYPE_COUNT = 25
} P05Type;

_Static_assert(P05_TYPE_FAIRY == 23, "project Fairy ABI must remain 23");
_Static_assert(P05_TYPE_STELLAR == 24, "project Stellar ABI must remain 24");

typedef enum P05MoveClass {
    P05_MOVE_STATUS = 0,
    P05_MOVE_PHYSICAL = 1,
    P05_MOVE_SPECIAL = 2
} P05MoveClass;

typedef enum P05ProtectKind {
    P05_PROTECT_NONE = 0,
    P05_PROTECT_SINGLE = 1,
    P05_PROTECT_SIDE = 2,
    P05_PROTECT_MAX_GUARD = 3
} P05ProtectKind;

typedef enum P05Weather {
    P05_WEATHER_NONE = 0,
    P05_WEATHER_SUN = 1,
    P05_WEATHER_RAIN = 2,
    P05_WEATHER_SAND = 4,
    P05_WEATHER_SNOW = 8
} P05Weather;

typedef enum P05Stat {
    /* Tie-breaking order is intentional and matches the pinned reference. */
    P05_STAT_ATTACK = 0,
    P05_STAT_DEFENSE = 1,
    P05_STAT_SP_ATTACK = 2,
    P05_STAT_SP_DEFENSE = 3,
    P05_STAT_SPEED = 4
} P05Stat;

typedef struct P05AbilityDefinition {
    p05_u16 id;
    const char *stable_key;
    const char *technical_name_en;
    const char *technical_description_en;
} P05AbilityDefinition;

const P05AbilityDefinition *p05_ability_definition(p05_u16 ability);
p05_u8 p05_ability_id_is_new(p05_u16 ability);
p05_u16 p05_effective_ability(p05_u16 ability, p05_u8 suppressed);

typedef struct P05MoveQuery {
    p05_u16 ability;
    p05_u16 base_damage;
    p05_u8 ability_suppressed;
    p05_u8 base_type;
    p05_u8 move_class;
    /* Dynamic-type moves, active Tera Blast, Z/Max moves set this flag. */
    p05_u8 dynamic_type_locked;
    p05_u8 makes_contact;
    p05_u8 protect_kind;
    p05_u8 ignores_protect;
    p05_u8 is_ohko;
} P05MoveQuery;

typedef struct P05MoveResult {
    p05_u16 damage;
    p05_u8 resolved_type;
    p05_u8 ability_triggered;
    p05_u8 blocked;
    p05_u8 protection_bypassed;
    p05_u8 contact_protection_effects_apply;
    p05_u8 virtual_sun;
} P05MoveResult;

P05MoveResult p05_resolve_move(const P05MoveQuery *query);
p05_u8 p05_resolve_spread_move(
    const P05MoveQuery *query,
    const p05_u8 *protect_kinds,
    p05_u8 target_count,
    P05MoveResult *results
);
p05_u16 p05_ai_estimated_damage(const P05MoveQuery *query);
p05_u8 p05_ai_prefers_candidate(
    const P05MoveQuery *candidate,
    const P05MoveQuery *alternative
);

/* Mega Sol is personal virtual sun; it never mutates the field weather. */
p05_u8 p05_weather_for_user(
    p05_u16 ability,
    p05_u8 suppressed,
    p05_u8 field_weather
);
p05_u8 p05_weather_ball_type(
    p05_u16 ability,
    p05_u8 suppressed,
    p05_u8 field_weather,
    p05_u8 base_type
);
p05_u16 p05_weather_heal_amount(
    p05_u16 ability,
    p05_u8 suppressed,
    p05_u8 field_weather,
    p05_u16 max_hp
);
p05_u8 p05_solar_move_skips_charge(p05_u16 ability, p05_u8 suppressed);

typedef struct P05GroundQuery {
    p05_u16 defender_ability;
    p05_u8 ability_suppressed;
    p05_u8 attacker_has_mold_breaker;
    p05_u8 defender_has_ability_shield;
    p05_u8 move_type;
    p05_u8 move_class;
    p05_u8 attack_reached_target;
    p05_u8 iron_ball;
    p05_u8 gravity;
    p05_u8 rooted;
    p05_u8 smack_down;
} P05GroundQuery;

typedef struct P05GroundResult {
    p05_u8 immune;
    p05_u8 ability_triggered;
    p05_u8 ability_bypassed;
} P05GroundResult;

P05GroundResult p05_resolve_ground_immunity(const P05GroundQuery *query);
p05_u8 p05_ai_should_switch_into_ground(const P05GroundQuery *query);

typedef struct P05EelevateBoostQuery {
    p05_u16 ability;
    p05_u8 ability_suppressed;
    p05_u8 user_alive;
    p05_u8 battle_continues;
    p05_u8 knocked_out_count;
    p05_u16 raw_stats[P05_STAT_COUNT];
    p05_s8 stat_stages[P05_STAT_COUNT];
} P05EelevateBoostQuery;

typedef struct P05EelevateBoostResult {
    p05_u8 triggered;
    p05_u8 stat;
    p05_u8 stages_gained;
} P05EelevateBoostResult;

P05EelevateBoostResult p05_apply_eelevate_boost(P05EelevateBoostQuery *query);

typedef struct P05SpicySprayQuery {
    p05_u16 defender_ability;
    p05_u8 ability_suppressed;
    p05_u8 attacker_present;
    p05_u8 attacker_alive;
    /* True only when the ability holder, not its Substitute, took damage. */
    p05_u8 defender_took_damage;
    p05_u8 attacker_can_be_burned;
    p05_u8 attacker_already_burned;
} P05SpicySprayQuery;

typedef struct P05SpicySprayResult {
    p05_u8 triggered;
    p05_u8 burn_applied;
} P05SpicySprayResult;

P05SpicySprayResult p05_resolve_spicy_spray(const P05SpicySprayQuery *query);

typedef enum P05BurnBenefit {
    P05_BURN_BENEFIT_NONE = 0,
    P05_BURN_BENEFIT_GUTS_PHYSICAL = 1,
    P05_BURN_BENEFIT_MARVEL_SCALE = 2,
    P05_BURN_BENEFIT_QUICK_FEET = 3,
    P05_BURN_BENEFIT_FLARE_BOOST_SPECIAL = 4,
    P05_BURN_BENEFIT_FACADE = 5
} P05BurnBenefit;

typedef struct P05SpicySprayAiQuery {
    p05_u16 partner_ability;
    p05_u8 partner_ability_suppressed;
    p05_u8 partner_present;
    p05_u8 partner_staying_in;
    p05_u8 hits_to_knock_out_partner;
    p05_u8 self_sacrifice_move;
    p05_u8 half_max_hp_recoil_move;
    p05_u8 partner_substitute_protected;
    p05_u8 attacker_can_be_burned;
    p05_u8 attacker_has_flame_orb;
    p05_u8 attacker_has_usable_cure_berry;
    p05_u8 burn_benefit;
} P05SpicySprayAiQuery;

p05_u8 p05_ai_should_trigger_friendly_spicy_spray(
    const P05SpicySprayAiQuery *query
);

/* Save stores an ability-selection slot; the derived canonical ID remains u16. */
p05_u8 p05_resolve_saved_ability(
    const p05_u16 species_abilities[P05_ABILITY_SLOT_COUNT],
    p05_u8 stored_slot,
    p05_u16 *resolved_ability
);

#endif /* POKEMON_VEGA_MODERNIZATION_P05_ABILITIES_H */
