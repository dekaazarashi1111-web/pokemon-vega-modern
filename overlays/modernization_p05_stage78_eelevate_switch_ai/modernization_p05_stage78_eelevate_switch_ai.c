#include "modernization_p05_stage78_eelevate_switch_ai.h"

enum {
    STAGE78_ABILITY_NONE = 0,
    STAGE78_ABILITY_EARTH_EATER = 298,
    STAGE78_ABILITY_EELEVATE = 313,
    STAGE78_ABILITY_NEUTRALIZING_GAS = 257,
    STAGE78_TYPE_GROUND = 4,
    STAGE78_SPLIT_STATUS = 2,
    STAGE78_MOVE_NONE = 0,
    STAGE78_MOVE_MAX = 1062,
    STAGE78_MOVE_THOUSAND_ARROWS = 643,
    STAGE78_MOVE_PREDICTION_SWITCH = 0xFFFF,
    STAGE78_ITEM_EFFECT_ABILITY_SHIELD = 147
};

Stage78U16 Stage78_MapEelevateAbsorber(
    const Stage78EelevateQuery *query
)
{
    if (query == (const Stage78EelevateQuery *)0)
        return STAGE78_ABILITY_NONE;
    if (query->originalAbility != STAGE78_ABILITY_EELEVATE)
        return query->originalAbility;
    if (query->move == STAGE78_MOVE_NONE
        || query->move > STAGE78_MOVE_MAX
        || query->move == STAGE78_MOVE_THOUSAND_ARROWS
        || query->moveType != STAGE78_TYPE_GROUND
        || query->moveSplit == STAGE78_SPLIT_STATUS)
        return query->originalAbility;
    if (query->circusSuppressed
        || query->abilitySuppressed
        || query->grounded)
        return query->originalAbility;
    if (!query->abilityShield
        && (query->targetAbilityIgnored
            || query->neutralizingGasPresent))
        return query->originalAbility;
    return STAGE78_ABILITY_EARTH_EATER;
}

#ifndef STAGE78_HOST_TEST

#define STAGE78_G_BATTLE_MONS ((const volatile Stage78U8 *)0x02023B44u)
#define STAGE78_G_BATTLERS_COUNT (*(const volatile Stage78U8 *)0x02023B2Cu)
#define STAGE78_G_ABSENT_FLAGS (*(const volatile Stage78U8 *)0x02023CD0u)
#define STAGE78_G_BATTLE_TYPE_FLAGS (*(const volatile Stage78U32 *)0x02022AACu)
#define STAGE78_G_CIRCUS_FLAGS (*(const volatile Stage78U32 *)0x0203DFBCu)
#define STAGE78_G_BATTLE_MOVES ((const volatile Stage78U8 *)0x090421F4u)

enum {
    STAGE78_BATTLER_CAPACITY = 4,
    STAGE78_BATTLE_MON_STRIDE = 0x58,
    STAGE78_BATTLE_MON_HP_OFFSET = 0x28,
    STAGE78_BATTLE_MON_ABILITY_OFFSET = 0x38,
    STAGE78_BATTLE_MOVE_STRIDE = 12,
    STAGE78_BATTLE_MOVE_SPLIT_OFFSET = 10,
    STAGE78_BATTLE_TYPE_CIRCUS = 0x04000000u,
    STAGE78_CIRCUS_ABILITY_SUPPRESSION = 0x80000000u
};

typedef Stage78U8 (*Stage78FnU8Bank)(Stage78U8);
typedef Stage78U8 (*Stage78FnU8Mon)(void *);
typedef Stage78U8 (*Stage78FnItemBank)(Stage78U8);
typedef Stage78U8 (*Stage78FnItemMon)(void *);
typedef Stage78U8 (*Stage78FnMoveType)(Stage78U8, Stage78U16);
typedef Stage78U8 (*Stage78FnIgnored)(Stage78U16, Stage78U16, Stage78U16);
typedef Stage78U16 (*Stage78FnPrediction)(Stage78U8, Stage78U8);
typedef Stage78U16 (*Stage78FnAIAbility)(Stage78U8, Stage78U8, Stage78U16);
typedef void (*Stage78FnLoadBattlers)(
    Stage78U8 *, Stage78U8 *, Stage78U8 *, Stage78U8 *
);

#define STAGE78_FN(type, address) ((type)((Stage78U32)(address) | 1u))

static Stage78U16 Stage78_ReadU16(const volatile Stage78U8 *address)
{
    return *(const volatile Stage78U16 *)(const volatile void *)address;
}

static Stage78U8 Stage78_MoveSplit(Stage78U16 move)
{
    return STAGE78_G_BATTLE_MOVES[
        (Stage78U32)move * STAGE78_BATTLE_MOVE_STRIDE
        + STAGE78_BATTLE_MOVE_SPLIT_OFFSET
    ];
}

static Stage78U8 Stage78_CircusSuppressed(void)
{
    return (Stage78U8)(
        (STAGE78_G_BATTLE_TYPE_FLAGS & STAGE78_BATTLE_TYPE_CIRCUS) != 0
        && (STAGE78_G_CIRCUS_FLAGS
            & STAGE78_CIRCUS_ABILITY_SUPPRESSION) != 0
    );
}

static Stage78U8 Stage78_HasResidualNeutralizingGas(Stage78U8 outgoing)
{
    Stage78U8 bank;
    Stage78U8 count = STAGE78_G_BATTLERS_COUNT;

    if (count > STAGE78_BATTLER_CAPACITY)
        count = STAGE78_BATTLER_CAPACITY;
    for (bank = 0; bank < count; ++bank)
    {
        const volatile Stage78U8 *battleMon;

        if (bank == outgoing || (STAGE78_G_ABSENT_FLAGS & (1u << bank)))
            continue;
        battleMon = STAGE78_G_BATTLE_MONS
            + (Stage78U32)bank * STAGE78_BATTLE_MON_STRIDE;
        if (Stage78_ReadU16(battleMon + STAGE78_BATTLE_MON_HP_OFFSET) != 0
            && Stage78_ReadU16(
                battleMon + STAGE78_BATTLE_MON_ABILITY_OFFSET
            ) == STAGE78_ABILITY_NEUTRALIZING_GAS)
            return 1;
    }
    return 0;
}

static Stage78U8 Stage78_SelectThreat(
    Stage78U8 active,
    Stage78U8 *attacker,
    Stage78U16 *move
)
{
    Stage78U8 battlerIn1;
    Stage78U8 battlerIn2;
    Stage78U8 foe1;
    Stage78U8 foe2;
    Stage78U16 move1;
    Stage78U16 move2;

    STAGE78_FN(Stage78FnLoadBattlers, 0x0909D734u)(
        &battlerIn1, &battlerIn2, &foe1, &foe2
    );
    (void)battlerIn1;
    (void)battlerIn2;
    move1 = STAGE78_FN(Stage78FnPrediction, 0x090B0AFCu)(foe1, active);
    move2 = STAGE78_FN(Stage78FnPrediction, 0x090B0AFCu)(foe2, active);
    if (move1 != STAGE78_MOVE_NONE
        && move1 != STAGE78_MOVE_PREDICTION_SWITCH
        && move1 <= STAGE78_MOVE_MAX)
    {
        *attacker = foe1;
        *move = move1;
        return 1;
    }
    if (move2 != STAGE78_MOVE_NONE
        && move2 != STAGE78_MOVE_PREDICTION_SWITCH
        && move2 <= STAGE78_MOVE_MAX)
    {
        *attacker = foe2;
        *move = move2;
        return 1;
    }
    *attacker = foe1;
    *move = STAGE78_MOVE_NONE;
    return 0;
}

static Stage78U16 Stage78_BuildAndMap(
    Stage78U16 originalAbility,
    Stage78U8 active,
    void *mon,
    Stage78U8 partyCandidate
)
{
    Stage78EelevateQuery query;
    Stage78U8 attacker;
    Stage78U16 attackerAbility;

    query.originalAbility = originalAbility;
    query.move = STAGE78_MOVE_NONE;
    query.moveType = 0;
    query.moveSplit = STAGE78_SPLIT_STATUS;
    query.grounded = 0;
    query.targetAbilityIgnored = 0;
    query.abilityShield = 0;
    query.circusSuppressed = 0;
    query.abilitySuppressed = 0;
    query.neutralizingGasPresent = 0;
    if (originalAbility != STAGE78_ABILITY_EELEVATE)
        return originalAbility;
    if (!Stage78_SelectThreat(active, &attacker, &query.move))
        return originalAbility;
    query.moveType = STAGE78_FN(Stage78FnMoveType, 0x090E6234u)(
        attacker, query.move
    );
    query.moveSplit = Stage78_MoveSplit(query.move);
    query.circusSuppressed = Stage78_CircusSuppressed();
    if (partyCandidate)
    {
        query.grounded = STAGE78_FN(Stage78FnU8Mon, 0x090D43D4u)(mon);
        query.abilityShield = (Stage78U8)(
            STAGE78_FN(Stage78FnItemMon, 0x090D4048u)(mon)
            == STAGE78_ITEM_EFFECT_ABILITY_SHIELD
        );
    }
    else
    {
        query.abilitySuppressed = STAGE78_FN(
            Stage78FnU8Bank, 0x090D7BB0u
        )(active);
        query.grounded = STAGE78_FN(Stage78FnU8Bank, 0x090D4718u)(active);
        query.abilityShield = (Stage78U8)(
            STAGE78_FN(Stage78FnItemBank, 0x090D3FECu)(active)
            == STAGE78_ITEM_EFFECT_ABILITY_SHIELD
        );
    }
    query.neutralizingGasPresent = Stage78_HasResidualNeutralizingGas(active);
    attackerAbility = STAGE78_FN(Stage78FnAIAbility, 0x090B09C4u)(
        attacker, active, query.move
    );
    query.targetAbilityIgnored = STAGE78_FN(
        Stage78FnIgnored, 0x090BBB78u
    )(STAGE78_ABILITY_EELEVATE, attackerAbility, query.move);
    return Stage78_MapEelevateAbsorber(&query);
}

Stage78U16 Stage78_ActiveAbsorberAbility(
    Stage78U16 originalAbility,
    Stage78U8 active,
    Stage78U8 originalFoe1
)
{
    /* originalFoe1 is retained in the ABI to prove the original call tuple. */
    (void)originalFoe1;
    return Stage78_BuildAndMap(originalAbility, active, (void *)0, 0);
}

Stage78U16 Stage78_PartyAbsorberAbility(
    Stage78U16 originalAbility,
    void *mon
)
{
    Stage78U8 battlerIn1;
    Stage78U8 battlerIn2;
    Stage78U8 foe1;
    Stage78U8 foe2;

    STAGE78_FN(Stage78FnLoadBattlers, 0x0909D734u)(
        &battlerIn1, &battlerIn2, &foe1, &foe2
    );
    (void)battlerIn2;
    (void)foe1;
    (void)foe2;
    return Stage78_BuildAndMap(originalAbility, battlerIn1, mon, 1);
}

Stage78U8 Stage78_RuntimeProbe(void)
{
    return 78;
}

#endif
