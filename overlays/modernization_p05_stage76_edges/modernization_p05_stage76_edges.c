#include "modernization_p05_stage76_edges.h"

/*
 * Stage76 intentionally has no dependency on CFRU headers.  These constants
 * are the byte-exact ABI of the pinned CFRU-JP image inherited through
 * Stage75.  Ability values are u16 (the new project abilities exceed 255).
 */
#define STAGE76_G_BATTLE_MONS ((volatile Stage76U8 *)0x02023B44u)
#define STAGE76_G_BATTLERS_COUNT (*(volatile Stage76U8 *)0x02023B2Cu)
#define STAGE76_G_BANK_ATTACKER (*(volatile Stage76U8 *)0x02023CCBu)
#define STAGE76_G_BATTLE_SCRIPT (*(volatile Stage76U8 **)0x02023CD4u)
#define STAGE76_G_BATTLE_TYPE_FLAGS (*(volatile Stage76U32 *)0x02022AACu)
#define STAGE76_G_PROTECT_STRUCTS ((volatile Stage76U8 *)0x02023DECu)
#define STAGE76_G_BATTLE_WEATHER (*(volatile Stage76U16 *)0x02023E7Cu)
#define STAGE76_G_BATTLE_SCRIPTING ((volatile Stage76U8 *)0x02023F24u)
#define STAGE76_G_HIT_MARKER (*(volatile Stage76U32 *)0x02023D30u)
#define STAGE76_G_BATTLE_MOVES ((const volatile Stage76U8 *)0x090421F4u)
#define STAGE76_G_BATTLE_STRUCT \
    (*(volatile Stage76U8 * volatile *)0x02023F48u)
#define STAGE76_G_CHOSEN_MOVES_BY_BANKS \
    ((const volatile Stage76U16 *)0x02023D24u)

enum {
    STAGE76_BATTLER_CAPACITY = 4,
    STAGE76_BATTLE_MON_STRIDE = 0x58,
    STAGE76_BATTLE_MON_MOVES_OFFSET = 0x0C,
    STAGE76_BATTLE_MON_HP_OFFSET = 0x28,
    STAGE76_BATTLE_MON_ABILITY_OFFSET = 0x38,
    STAGE76_BATTLE_MON_STATUS2_OFFSET = 0x50,
    STAGE76_BATTLE_MOVE_STRIDE = 12,
    STAGE76_BATTLE_MOVE_EFFECT_OFFSET = 0,
    STAGE76_BATTLE_MOVE_POWER_OFFSET = 1,
    STAGE76_BATTLE_MOVE_FLAGS_OFFSET = 8,
    STAGE76_BATTLE_MOVE_SPLIT_OFFSET = 10,
    STAGE76_AI_SCRIPT_ATK_PARTNER_ABILITY_OFFSET = 0x40,
    STAGE76_AI_SCRIPT_FOE1_OFFSET = 0x44,
    STAGE76_AI_SCRIPT_PARTNER_MOVE_OFFSET = 0x46,
    STAGE76_DAMAGE_CALC_ATK_ABILITY_OFFSET = 0x10,
    STAGE76_BATTLE_STRUCT_MOVE_TARGET_OFFSET = 0x0C,
    STAGE76_BATTLE_STRUCT_MON_TO_SWITCH_OFFSET = 0x5C,
    STAGE76_PARTY_SIZE_SENTINEL = 6,
    STAGE76_PROTECT_STRUCT_STRIDE = 16,
    STAGE76_BATTLE_SCRIPTING_BANK_OFFSET = 0x17,
    STAGE76_ABILITY_CLOUD_NINE = 13,
    STAGE76_ABILITY_MARVEL_SCALE = 63,
    STAGE76_ABILITY_GUTS = 62,
    STAGE76_ABILITY_AIR_LOCK = 77,
    STAGE76_ABILITY_QUICK_FEET = 95,
    STAGE76_ABILITY_FLARE_BOOST = 138,
    STAGE76_ABILITY_NONE = 0,
    STAGE76_ABILITY_MEGA_SOL = 315,
    STAGE76_ABILITY_PIERCING_DRILL = 316,
    STAGE76_ABILITY_SPICY_SPRAY = 317,
    STAGE76_ITEM_EFFECT_CURE_BURN = 5,
    STAGE76_ITEM_EFFECT_CURE_STATUS = 9,
    STAGE76_ITEM_EFFECT_FLAME_ORB = 76,
    STAGE76_ITEM_EFFECT_UTILITY_UMBRELLA = 136,
    STAGE76_ITEM_EFFECT_ABILITY_SHIELD = 147,
    STAGE76_MOVE_FACADE = 263,
    STAGE76_MOVE_MIND_BLOWN = 732,
    STAGE76_MOVE_STEEL_BEAM = 783,
    STAGE76_MOVE_CHLOROBLAST = 821,
    STAGE76_MOVE_PROTECT = 182,
    STAGE76_MOVE_DETECT = 197,
    STAGE76_MOVE_KINGS_SHIELD = 599,
    STAGE76_MOVE_SPIKY_SHIELD = 638,
    STAGE76_MOVE_BANEFUL_BUNKER = 651,
    STAGE76_MOVE_OBSTRUCT = 779,
    STAGE76_MOVE_MAX_GUARD = 891,
    STAGE76_MOVE_SILK_TRAP = 1033,
    STAGE76_MOVE_BURNING_BULWARK = 1052,
    STAGE76_EFFECT_EXPLOSION = 7,
    STAGE76_EFFECT_OHKO = 38,
    STAGE76_EFFECT_PRESENT = 122,
    STAGE76_EFFECT_FUTURE_SIGHT = 148,
    STAGE76_EFFECT_SEMI_INVULNERABLE = 155,
    STAGE76_EFFECT_MEMENTO_FAMILY = 168,
    STAGE76_EFFECT_HEAL_TARGET = 233,
    STAGE76_SPLIT_PHYSICAL = 0,
    STAGE76_SPLIT_SPECIAL = 1,
    STAGE76_SPLIT_STATUS = 2,
    STAGE76_MOVE_TARGET_SELECTED = 0,
    STAGE76_MOVE_TARGET_USER_OR_PARTNER = 2,
    STAGE76_MOVE_TARGET_RANDOM = 4,
    STAGE76_MOVE_TARGET_ALL = 0x20,
    STAGE76_MOVE_FLAG_PROTECT_AFFECTED = 0x02,
    STAGE76_MOVE_RESULT_NO_EFFECT = 0x29,
    STAGE76_BATTLE_TYPE_DOUBLE = 0x0001,
    STAGE76_STATUS2_MULTIPLETURNS = 0x00001000,
    STAGE76_HITMARKER_NO_ATTACKSTRING = 0x00000200,
    STAGE76_WEATHER_SUN_ANY = (1 << 5) | (1 << 6) | (1 << 11),
    STAGE76_SPICY_SCORE_BONUS = 3,
    STAGE76_PROTECT_INDIVIDUAL_MASK =
        (1u << 0) | (1u << 22) | (1u << 23) | (1u << 24)
        | (1u << 25) | (1u << 26) | (1u << 27)
};

enum {
    STAGE76_ORIGINAL_SOLAR_BEAM_SCRIPT = 0x090050C1u,
    STAGE76_SOLAR_BEAM_FIRST_TURN_SCRIPT = 0x09005110u,
    STAGE76_ORIGINAL_PREDICTED_ABILITY = 0x090B0970u,
    STAGE76_ORIGINAL_GET_MON_ABILITY = 0x090DA23Cu,
    STAGE76_IS_VALID_MOVE_PREDICTION = 0x090B0AFCu,
    STAGE76_STAGE72_ORIGINAL_PROTECTION = 0x095341B5u,
    STAGE76_GET_BASE_MOVE_TARGET = 0x090D5014u,
    STAGE76_CHECK_CONTACT = 0x090D4524u,
    STAGE76_IS_Z_MOVE = 0x090D6684u,
    STAGE76_IS_ANY_MAX_MOVE = 0x090F1CF4u,
    STAGE76_GET_BANK_ITEM_EFFECT = 0x090D3FECu,
    STAGE76_MOVE_BLOCKED_BY_SUBSTITUTE = 0x090D6268u,
    STAGE76_CAN_BE_BURNED = 0x090D745Cu,
    STAGE76_MOVE_KNOCKS_OUT_X_HITS = 0x090B39C4u,
    STAGE76_AI_SPECIAL_TYPE_CALC = 0x090E6278u,
    STAGE76_DOES_PROTECTION_MOVE_BLOCK_MOVE = 0x090BC4C0u,
    STAGE76_MOVE_WOULD_HIT_FIRST = 0x090AFF88u,
    STAGE76_IS_ABILITY_SUPPRESSED = 0x090D7BB0u,
    STAGE76_TRY_REPLACE_MOVE_WITH_Z_MOVE = 0x090B2E88u,
    STAGE76_GET_AI_CHOSEN_MOVE = 0x090B042Cu,
    STAGE76_GET_AI_ABILITY = 0x090B09C4u,
    STAGE76_IS_TARGET_ABILITY_IGNORED = 0x090BBB78u,
    STAGE76_IS_DYNAMAXED = 0x090F1894u
};

extern Stage76U32 Stage76_OriginalAICalcDmg(
    Stage76U8, Stage76U8, Stage76U16, void *
);
extern Stage76U8 Stage76_OriginalAIScriptPartner(
    Stage76U8, Stage76U8, Stage76U16, Stage76U8, void *
);
extern Stage76U8 Stage76_OriginalRangeMoveCanHurtPartner(
    Stage76U16, Stage76U8, Stage76U8
);
extern const Stage76U8 Stage76_BattleScriptMegaSolPopup[];

typedef Stage76U8 (*Stage76FnU8_1)(Stage76U8);
typedef Stage76U8 (*Stage76FnU8_3)(Stage76U8, Stage76U8, Stage76U8);
typedef Stage76U8 (*Stage76FnMoveBanks)(Stage76U16, Stage76U8, Stage76U8);
typedef Stage76U8 (*Stage76FnMovePredicate)(Stage76U16);
typedef Stage76U8 (*Stage76FnMoveHits)(Stage76U16, Stage76U8, Stage76U8, Stage76U8);
typedef Stage76U8 (*Stage76FnProtection)(Stage76U8, Stage76U8, Stage76U16, Stage76U16);
typedef Stage76U8 (*Stage76FnMoveTarget)(Stage76U16, Stage76U8);
typedef Stage76U16 (*Stage76FnPrediction)(Stage76U8, Stage76U8);
typedef Stage76U8 (*Stage76FnMoveOrder)(Stage76U16, Stage76U16, Stage76U16);
typedef Stage76U16 (*Stage76FnResolveMove)(Stage76U8, Stage76U8, Stage76U16);
typedef Stage76U8 (*Stage76FnTargetAbilityIgnored)(
    Stage76U16, Stage76U16, Stage76U16
);

#define STAGE76_FN(type, address) ((type)((Stage76U32)(address) | 1u))

static Stage76U16 Stage76_ReadU16(const volatile Stage76U8 *address)
{
    return *(const volatile Stage76U16 *)(const volatile void *)address;
}

static Stage76U32 Stage76_ReadU32(const volatile Stage76U8 *address)
{
    return *(const volatile Stage76U32 *)(const volatile void *)address;
}

static volatile Stage76U8 *Stage76_BattleMon(Stage76U8 bank)
{
    return STAGE76_G_BATTLE_MONS
        + (Stage76U32)bank * STAGE76_BATTLE_MON_STRIDE;
}

static Stage76U16 Stage76_BattleMonAbility(Stage76U8 bank)
{
    return Stage76_ReadU16(
        Stage76_BattleMon(bank) + STAGE76_BATTLE_MON_ABILITY_OFFSET
    );
}

static Stage76U8 Stage76_IsAbilitySuppressed(Stage76U8 bank)
{
    return STAGE76_FN(
        Stage76FnU8_1,
        STAGE76_IS_ABILITY_SUPPRESSED
    )(bank);
}

static Stage76U16 Stage76_EffectiveActiveAbility(Stage76U8 bank)
{
    if (Stage76_IsAbilitySuppressed(bank))
        return STAGE76_ABILITY_NONE;
    return Stage76_BattleMonAbility(bank);
}

static Stage76U16 Stage76_BattleMonHp(Stage76U8 bank)
{
    return Stage76_ReadU16(
        Stage76_BattleMon(bank) + STAGE76_BATTLE_MON_HP_OFFSET
    );
}

static const volatile Stage76U8 *Stage76_BattleMove(Stage76U16 move)
{
    return STAGE76_G_BATTLE_MOVES
        + (Stage76U32)move * STAGE76_BATTLE_MOVE_STRIDE;
}

static Stage76U8 Stage76_MoveSplit(Stage76U16 move)
{
    return Stage76_BattleMove(move)[STAGE76_BATTLE_MOVE_SPLIT_OFFSET];
}

static Stage76U8 Stage76_IsIndividualProtectMove(Stage76U16 move)
{
    switch (move)
    {
    case STAGE76_MOVE_PROTECT:
    case STAGE76_MOVE_DETECT:
    case STAGE76_MOVE_KINGS_SHIELD:
    case STAGE76_MOVE_SPIKY_SHIELD:
    case STAGE76_MOVE_BANEFUL_BUNKER:
    case STAGE76_MOVE_OBSTRUCT:
    case STAGE76_MOVE_SILK_TRAP:
    case STAGE76_MOVE_BURNING_BULWARK:
        return 1;
    default:
        return 0;
    }
}

static Stage76U8 Stage76_IsSingleTargetMove(
    Stage76U16 move,
    Stage76U8 bankAtk
)
{
    Stage76U8 target = STAGE76_FN(
        Stage76FnMoveTarget,
        STAGE76_GET_BASE_MOVE_TARGET
    )(move, bankAtk);

    return (Stage76U8)(target == STAGE76_MOVE_TARGET_SELECTED
        || target == STAGE76_MOVE_TARGET_RANDOM);
}

static Stage76U8 Stage76_IsDirectPartnerTargetMove(
    Stage76U16 move,
    Stage76U8 bankAtk
)
{
    Stage76U8 target = STAGE76_FN(
        Stage76FnMoveTarget,
        STAGE76_GET_BASE_MOVE_TARGET
    )(move, bankAtk);

    return (Stage76U8)(target == STAGE76_MOVE_TARGET_SELECTED
        || target == STAGE76_MOVE_TARGET_USER_OR_PARTNER);
}

static Stage76U8 Stage76_IsFriendlyFireSpreadMove(
    Stage76U16 move,
    Stage76U8 bankAtk
)
{
    return (Stage76U8)(STAGE76_FN(
        Stage76FnMoveTarget,
        STAGE76_GET_BASE_MOVE_TARGET
    )(move, bankAtk) & STAGE76_MOVE_TARGET_ALL);
}

static Stage76U8 Stage76_WeatherHasEffect(void)
{
    Stage76U8 bank;

    for (bank = 0; bank < STAGE76_G_BATTLERS_COUNT
        && bank < STAGE76_BATTLER_CAPACITY; ++bank)
    {
        Stage76U16 ability = Stage76_BattleMonAbility(bank);

        if ((ability == STAGE76_ABILITY_CLOUD_NINE
                || ability == STAGE76_ABILITY_AIR_LOCK)
            && Stage76_BattleMonHp(bank) != 0)
            return 0;
    }
    return 1;
}

static Stage76U8 Stage76_HasMove(Stage76U8 bank, Stage76U16 wanted)
{
    Stage76U8 slot;
    const volatile Stage76U8 *mon = Stage76_BattleMon(bank);

    for (slot = 0; slot < 4; ++slot)
    {
        if (Stage76_ReadU16(mon + STAGE76_BATTLE_MON_MOVES_OFFSET
                + (Stage76U32)slot * 2u) == wanted)
            return 1;
    }
    return 0;
}

static Stage76U8 Stage76_HasMoveSplit(Stage76U8 bank, Stage76U8 wanted)
{
    Stage76U8 slot;
    const volatile Stage76U8 *mon = Stage76_BattleMon(bank);

    for (slot = 0; slot < 4; ++slot)
    {
        Stage76U16 move = Stage76_ReadU16(
            mon + STAGE76_BATTLE_MON_MOVES_OFFSET
                + (Stage76U32)slot * 2u
        );

        if (move != 0 && Stage76_MoveSplit(move) == wanted)
            return 1;
    }
    return 0;
}

static Stage76U8 Stage76_HasBurnBenefit(
    Stage76U8 bank,
    Stage76U16 ability
)
{
    if (ability == STAGE76_ABILITY_MARVEL_SCALE
        || ability == STAGE76_ABILITY_QUICK_FEET)
        return 1;
    if (ability == STAGE76_ABILITY_GUTS
        && Stage76_HasMoveSplit(bank, STAGE76_SPLIT_PHYSICAL))
        return 1;
    if (ability == STAGE76_ABILITY_FLARE_BOOST
        && Stage76_HasMoveSplit(bank, STAGE76_SPLIT_SPECIAL))
        return 1;
    return Stage76_HasMove(bank, STAGE76_MOVE_FACADE);
}

static Stage76U8 Stage76_IsSelfSacrificingOrHalfRecoil(Stage76U16 move)
{
    Stage76U8 effect = Stage76_BattleMove(move)[
        STAGE76_BATTLE_MOVE_EFFECT_OFFSET
    ];

    return (Stage76U8)(effect == STAGE76_EFFECT_EXPLOSION
        || effect == STAGE76_EFFECT_MEMENTO_FAMILY
        || move == STAGE76_MOVE_MIND_BLOWN
        || move == STAGE76_MOVE_STEEL_BEAM
        || move == STAGE76_MOVE_CHLOROBLAST);
}

static Stage76U8 Stage76_PartnerStayingIn(Stage76U8 bankAtkPartner)
{
    const volatile Stage76U8 *battleStruct = STAGE76_G_BATTLE_STRUCT;

    return (Stage76U8)(battleStruct != (const volatile Stage76U8 *)0
        && battleStruct[STAGE76_BATTLE_STRUCT_MON_TO_SWITCH_OFFSET
            + bankAtkPartner] == STAGE76_PARTY_SIZE_SENTINEL);
}

static Stage76U16 Stage76_GetResolvedPartnerMove(Stage76U8 bankAtkPartner)
{
    const volatile Stage76U8 *battleStruct = STAGE76_G_BATTLE_STRUCT;

    if (battleStruct == (const volatile Stage76U8 *)0
        || STAGE76_G_CHOSEN_MOVES_BY_BANKS[bankAtkPartner] == 0)
        return 0;
    return STAGE76_FN(
        Stage76FnPrediction,
        STAGE76_GET_AI_CHOSEN_MOVE
    )(bankAtkPartner, battleStruct[
        STAGE76_BATTLE_STRUCT_MOVE_TARGET_OFFSET + bankAtkPartner
    ]);
}

static Stage76U8 Stage76_PlannedPartnerMoveWillBeHit(
    Stage76U16 move,
    Stage76U8 bankAtk,
    Stage76U8 bankAtkPartner,
    Stage76U16 partnerMove
)
{
    if (partnerMove == 0)
        return 1;
    if (Stage76_IsPlannedMaxGuard(partnerMove))
        return 0;
    if (STAGE76_FN(
        Stage76FnProtection,
        STAGE76_DOES_PROTECTION_MOVE_BLOCK_MOVE
        )(
            bankAtk,
            bankAtkPartner,
            move,
            Stage76_NormalizePredictedProtectionMove(partnerMove)
        ))
        return 0;
    if (Stage76_BattleMove(partnerMove)[STAGE76_BATTLE_MOVE_EFFECT_OFFSET]
            == STAGE76_EFFECT_SEMI_INVULNERABLE
        && !STAGE76_FN(
            Stage76FnMoveOrder,
            STAGE76_MOVE_WOULD_HIT_FIRST
        )(move, bankAtk, bankAtkPartner))
        return 0;
    return 1;
}

static Stage76U8 Stage76_ShouldRewardSpicySpray(
    Stage76U16 move,
    Stage76U8 bankAtk,
    Stage76U8 bankAtkPartner,
    Stage76U8 path,
    const void *data,
    Stage76U8 canonicalReach
)
{
    const volatile Stage76U8 *scriptData =
        (const volatile Stage76U8 *)data;
    Stage76U8 itemEffect;
    Stage76U8 isSpread;
    Stage76U16 attackerAbility;
    Stage76U16 partnerAbility;
    Stage76U16 partnerMove;
    Stage76U16 flags = 0;

    if (bankAtk >= STAGE76_G_BATTLERS_COUNT
        || bankAtkPartner >= STAGE76_G_BATTLERS_COUNT
        || bankAtk >= STAGE76_BATTLER_CAPACITY
        || bankAtkPartner >= STAGE76_BATTLER_CAPACITY)
        return 0;

    isSpread = Stage76_IsFriendlyFireSpreadMove(move, bankAtk);
    if (!Stage76_SpicyPathQualifies(path, isSpread, 1))
        return 0;
    if (path == STAGE76_SPICY_PATH_DIRECT)
    {
        if (!Stage76_IsDirectPartnerTargetMove(move, bankAtk)
            || !Stage76_DirectEffectCanDamagePartner(
                Stage76_BattleMove(move)[STAGE76_BATTLE_MOVE_EFFECT_OFFSET]
            )
            || scriptData == (const volatile Stage76U8 *)0)
            return 0;
        partnerAbility = Stage76_ReadU16(
            scriptData + STAGE76_AI_SCRIPT_ATK_PARTNER_ABILITY_OFFSET
        );
        attackerAbility = STAGE76_FN(
            Stage76FnResolveMove,
            STAGE76_GET_AI_ABILITY
        )(bankAtk, scriptData[STAGE76_AI_SCRIPT_FOE1_OFFSET], move);
        partnerMove = Stage76_ReadU16(
            scriptData + STAGE76_AI_SCRIPT_PARTNER_MOVE_OFFSET
        );
    }
    else
    {
        partnerAbility = Stage76_BattleMonAbility(bankAtkPartner);
        attackerAbility = STAGE76_FN(
            Stage76FnResolveMove,
            STAGE76_GET_AI_ABILITY
        )(bankAtk, (Stage76U8)(bankAtk ^ 1u), move);
        partnerMove = Stage76_GetResolvedPartnerMove(bankAtkPartner);
    }
    if (Stage76_IsAbilitySuppressed(bankAtkPartner))
        partnerAbility = STAGE76_ABILITY_NONE;
    if (Stage76_IsAbilitySuppressed(bankAtk))
        attackerAbility = STAGE76_ABILITY_NONE;
    if (partnerAbility != STAGE76_ABILITY_NONE
        && STAGE76_FN(
            Stage76FnTargetAbilityIgnored,
            STAGE76_IS_TARGET_ABILITY_IGNORED
        )(partnerAbility, attackerAbility, move)
        && STAGE76_FN(
            Stage76FnU8_1,
            STAGE76_GET_BANK_ITEM_EFFECT
        )(bankAtkPartner) != STAGE76_ITEM_EFFECT_ABILITY_SHIELD)
        partnerAbility = STAGE76_ABILITY_NONE;

    if (STAGE76_G_BATTLE_TYPE_FLAGS & STAGE76_BATTLE_TYPE_DOUBLE)
        flags |= STAGE76_SPICY_DOUBLE;
    if (bankAtk != bankAtkPartner)
        flags |= STAGE76_SPICY_DISTINCT_BANKS;
    if (Stage76_BattleMonHp(bankAtkPartner) != 0)
        flags |= STAGE76_SPICY_PARTNER_ALIVE;
    if (Stage76_PartnerStayingIn(bankAtkPartner))
        flags |= STAGE76_SPICY_PARTNER_STAYING;
    if (partnerAbility == STAGE76_ABILITY_SPICY_SPRAY)
        flags |= STAGE76_SPICY_PARTNER_ABILITY;
    if (Stage76_MoveSplit(move) != STAGE76_SPLIT_STATUS
        && Stage76_BattleMove(move)[STAGE76_BATTLE_MOVE_POWER_OFFSET] != 0
        && !(STAGE76_FN(
            Stage76FnMoveBanks,
            STAGE76_AI_SPECIAL_TYPE_CALC
        )(move, bankAtk, bankAtkPartner) & STAGE76_MOVE_RESULT_NO_EFFECT))
        flags |= STAGE76_SPICY_DAMAGING;
    if (!Stage76_IsSelfSacrificingOrHalfRecoil(move))
        flags |= STAGE76_SPICY_SAFE_MOVE;
    if (!STAGE76_FN(
            Stage76FnMoveBanks,
            STAGE76_MOVE_BLOCKED_BY_SUBSTITUTE
        )(move, bankAtk, bankAtkPartner))
        flags |= STAGE76_SPICY_NOT_SUB_BLOCKED;
    if (!STAGE76_FN(
            Stage76FnMoveHits,
            STAGE76_MOVE_KNOCKS_OUT_X_HITS
        )(move, bankAtk, bankAtkPartner, 1))
        flags |= STAGE76_SPICY_NOT_KO;
    if (STAGE76_FN(
            Stage76FnU8_3,
            STAGE76_CAN_BE_BURNED
        )(bankAtk, bankAtkPartner, 1))
        flags |= STAGE76_SPICY_CAN_BURN;
    if (Stage76_HasBurnBenefit(bankAtk, attackerAbility))
        flags |= STAGE76_SPICY_BURN_BENEFIT;

    itemEffect = STAGE76_FN(
        Stage76FnU8_1,
        STAGE76_GET_BANK_ITEM_EFFECT
    )(bankAtk);
    if (itemEffect != STAGE76_ITEM_EFFECT_FLAME_ORB
        && itemEffect != STAGE76_ITEM_EFFECT_CURE_BURN
        && itemEffect != STAGE76_ITEM_EFFECT_CURE_STATUS)
        flags |= STAGE76_SPICY_ITEM_OK;
    if (canonicalReach && Stage76_PlannedPartnerMoveWillBeHit(
            move, bankAtk, bankAtkPartner, partnerMove
        ))
        flags |= STAGE76_SPICY_REACHABLE;
    return Stage76_SpicyPolicyCore(flags);
}

Stage76U8 Stage76_MegaSolRoute(
    Stage76U16 ability,
    Stage76U8 alreadySecondTurn,
    Stage76U8 originalSunApplies
)
{
    if (ability != STAGE76_ABILITY_MEGA_SOL || alreadySecondTurn)
        return STAGE76_MEGA_ROUTE_ORIGINAL;
    if (originalSunApplies)
        return STAGE76_MEGA_ROUTE_FIRST_TURN;
    return STAGE76_MEGA_ROUTE_POPUP;
}

Stage76U32 Stage76_QuarterPredictedProtectDamage(
    Stage76U32 damage,
    Stage76U8 qualifies
)
{
    if (!qualifies || damage == 0)
        return damage;
    damage /= 4u;
    return damage == 0 ? 1u : damage;
}

Stage76U16 Stage76_NormalizePredictedProtectionMove(Stage76U16 move)
{
    if (move == STAGE76_MOVE_DETECT)
        return STAGE76_MOVE_PROTECT;
    return move;
}

Stage76U8 Stage76_IsPlannedMaxGuard(Stage76U16 move)
{
    return (Stage76U8)(move == STAGE76_MOVE_MAX_GUARD);
}

Stage76U8 Stage76_DirectEffectCanDamagePartner(Stage76U8 effect)
{
    return (Stage76U8)(
        effect != STAGE76_EFFECT_PRESENT
        && effect != STAGE76_EFFECT_FUTURE_SIGHT
        && effect != STAGE76_EFFECT_HEAL_TARGET
    );
}

Stage76U8 Stage76_SpicyPolicyCore(Stage76U16 flags)
{
    return (Stage76U8)(flags == STAGE76_SPICY_ALL);
}

Stage76U8 Stage76_SpicyPathQualifies(
    Stage76U8 path,
    Stage76U8 isSpread,
    Stage76U8 commonPolicyQualifies
)
{
    if (!commonPolicyQualifies)
        return 0;
    if (path == STAGE76_SPICY_PATH_DIRECT)
        return (Stage76U8)!isSpread;
    if (path == STAGE76_SPICY_PATH_SPREAD)
        return (Stage76U8)!!isSpread;
    return 0;
}

Stage76U16 Stage76_SelectAIAttackerAbility(
    Stage76U16 activeAbility,
    Stage76U8 activeAbilitySuppressed,
    Stage76U8 hasDamageData,
    Stage76U16 damageDataAbility
)
{
    if (activeAbilitySuppressed)
        return STAGE76_ABILITY_NONE;
    if (hasDamageData)
        return damageDataAbility;
    return activeAbility;
}

void Stage76_DispatchMegaSolSolarBeam(void)
{
    Stage76U8 attacker = STAGE76_G_BANK_ATTACKER;
    Stage76U32 target = STAGE76_ORIGINAL_SOLAR_BEAM_SCRIPT;

    if (attacker < STAGE76_G_BATTLERS_COUNT
        && attacker < STAGE76_BATTLER_CAPACITY)
    {
        Stage76U8 originalSunApplies = (Stage76U8)(
            (STAGE76_G_BATTLE_WEATHER & STAGE76_WEATHER_SUN_ANY)
            && Stage76_WeatherHasEffect()
            && STAGE76_FN(
                Stage76FnU8_1,
                STAGE76_GET_BANK_ITEM_EFFECT
            )(attacker) != STAGE76_ITEM_EFFECT_UTILITY_UMBRELLA
        );
        Stage76U8 alreadySecondTurn = (Stage76U8)(
            (Stage76_ReadU32(Stage76_BattleMon(attacker)
                + STAGE76_BATTLE_MON_STATUS2_OFFSET)
                & STAGE76_STATUS2_MULTIPLETURNS)
            || (STAGE76_G_HIT_MARKER & STAGE76_HITMARKER_NO_ATTACKSTRING)
        );
        Stage76U8 route = Stage76_MegaSolRoute(
            Stage76_EffectiveActiveAbility(attacker),
            alreadySecondTurn,
            originalSunApplies
        );

        if (route == STAGE76_MEGA_ROUTE_FIRST_TURN)
            target = STAGE76_SOLAR_BEAM_FIRST_TURN_SCRIPT;
        else if (route == STAGE76_MEGA_ROUTE_POPUP)
        {
            STAGE76_G_BATTLE_SCRIPTING[
                STAGE76_BATTLE_SCRIPTING_BANK_OFFSET
            ] = attacker;
            target = (Stage76U32)Stage76_BattleScriptMegaSolPopup;
        }
    }

    /* CFRU atkF8_callasm advances by five bytes after this helper returns. */
    STAGE76_G_BATTLE_SCRIPT = (volatile Stage76U8 *)(target - 5u);
}

Stage76U32 Stage76_AICalcDmg(
    Stage76U8 bankAtk,
    Stage76U8 bankDef,
    Stage76U16 move,
    void *damageData
)
{
    Stage76U32 damage = Stage76_OriginalAICalcDmg(
        bankAtk,
        bankDef,
        move,
        damageData
    );
    const volatile Stage76U8 *data =
        (const volatile Stage76U8 *)damageData;
    Stage76U16 attackerAbility;
    Stage76U16 predictedProtect;

    if (bankAtk >= STAGE76_G_BATTLERS_COUNT
        || bankDef >= STAGE76_G_BATTLERS_COUNT
        || bankAtk >= STAGE76_BATTLER_CAPACITY
        || bankDef >= STAGE76_BATTLER_CAPACITY)
        return damage;

    attackerAbility = Stage76_SelectAIAttackerAbility(
        Stage76_BattleMonAbility(bankAtk),
        Stage76_IsAbilitySuppressed(bankAtk),
        (Stage76U8)(data != (const volatile Stage76U8 *)0),
        data == (const volatile Stage76U8 *)0
            ? STAGE76_ABILITY_NONE
            : Stage76_ReadU16(data + STAGE76_DAMAGE_CALC_ATK_ABILITY_OFFSET)
    );

    if (damage == 0
        || attackerAbility != STAGE76_ABILITY_PIERCING_DRILL
        || Stage76_BattleMove(move)[STAGE76_BATTLE_MOVE_EFFECT_OFFSET]
            == STAGE76_EFFECT_OHKO
        || STAGE76_FN(
            Stage76FnMovePredicate,
            STAGE76_IS_Z_MOVE
        )(move)
        || STAGE76_FN(
            Stage76FnMovePredicate,
            STAGE76_IS_ANY_MAX_MOVE
        )(move)
        || Stage76_ReadU32(STAGE76_G_PROTECT_STRUCTS
            + (Stage76U32)bankDef * STAGE76_PROTECT_STRUCT_STRIDE)
            & STAGE76_PROTECT_INDIVIDUAL_MASK
        || !Stage76_IsSingleTargetMove(move, bankAtk)
        || !(Stage76_BattleMove(move)[STAGE76_BATTLE_MOVE_FLAGS_OFFSET]
            & STAGE76_MOVE_FLAG_PROTECT_AFFECTED)
        || !STAGE76_FN(
            Stage76FnMoveBanks,
            STAGE76_CHECK_CONTACT
        )(move, bankAtk, bankDef))
        return damage;

    predictedProtect = STAGE76_FN(
        Stage76FnPrediction,
        STAGE76_IS_VALID_MOVE_PREDICTION
    )(bankDef, bankAtk);
    if (STAGE76_G_CHOSEN_MOVES_BY_BANKS[bankDef] != 0)
        predictedProtect = STAGE76_FN(
            Stage76FnPrediction,
            STAGE76_GET_AI_CHOSEN_MOVE
        )(bankDef, bankAtk);
    else if (STAGE76_FN(Stage76FnU8_1, STAGE76_IS_DYNAMAXED)(bankDef))
        return damage;
    if (!Stage76_IsIndividualProtectMove(predictedProtect))
        return damage;

    predictedProtect = Stage76_NormalizePredictedProtectionMove(
        predictedProtect
    );
    if (!STAGE76_FN(
            Stage76FnProtection,
            STAGE76_STAGE72_ORIGINAL_PROTECTION
        )(bankAtk, bankDef, move, predictedProtect))
        return damage;

    return Stage76_QuarterPredictedProtectDamage(damage, 1);
}

Stage76U8 Stage76_AIScriptPartner(
    Stage76U8 bankAtk,
    Stage76U8 bankAtkPartner,
    Stage76U16 originalMove,
    Stage76U8 originalViability,
    void *data
)
{
    Stage76U8 viability = Stage76_OriginalAIScriptPartner(
        bankAtk,
        bankAtkPartner,
        originalMove,
        originalViability,
        data
    );
    Stage76U16 resolvedMove = STAGE76_FN(
        Stage76FnResolveMove,
        STAGE76_TRY_REPLACE_MOVE_WITH_Z_MOVE
    )(bankAtk, bankAtkPartner, originalMove);

    if (Stage76_ShouldRewardSpicySpray(
            resolvedMove,
            bankAtk,
            bankAtkPartner,
            STAGE76_SPICY_PATH_DIRECT,
            data,
            Stage76_OriginalRangeMoveCanHurtPartner(
                resolvedMove, bankAtk, bankAtkPartner
            )
        ))
    {
        if (viability > (Stage76U8)(255 - STAGE76_SPICY_SCORE_BONUS))
            viability = 255;
        else
            viability = (Stage76U8)(viability + STAGE76_SPICY_SCORE_BONUS);
    }
    return viability;
}

Stage76U8 Stage76_RangeMoveCanHurtPartner(
    Stage76U16 move,
    Stage76U8 bankAtk,
    Stage76U8 bankAtkPartner
)
{
    Stage76U8 hurts = Stage76_OriginalRangeMoveCanHurtPartner(
        move,
        bankAtk,
        bankAtkPartner
    );

    if (hurts && Stage76_ShouldRewardSpicySpray(
            move,
            bankAtk,
            bankAtkPartner,
            STAGE76_SPICY_PATH_SPREAD,
            (const void *)0,
            hurts
        ))
        return 0;
    return hurts;
}

Stage76U32 Stage76_RuntimeProbe(Stage76U32 query)
{
    switch (query)
    {
    case 0:
        return 0x53543736u; /* "ST76" */
    case 1:
        return 0x00000007u; /* Mega, Piercing, Spicy */
    case 2:
        return 1u; /* One dedicated switch-AI edge remains pending. */
    default:
        return 0;
    }
}
