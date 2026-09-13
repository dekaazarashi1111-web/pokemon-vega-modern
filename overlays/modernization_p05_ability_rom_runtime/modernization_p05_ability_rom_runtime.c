#include "modernization_p05_ability_rom_runtime.h"

/* Pinned CFRU-JP ROM ABI. */
#define STAGE72_G_BATTLE_MONS ((volatile Stage72U8 *)0x02023B44u)
#define STAGE72_G_BATTLERS_COUNT (*(volatile Stage72U8 *)0x02023B2Cu)
#define STAGE72_G_BATTLER_PARTY_INDEXES ((volatile Stage72U8 *)0x02023B2Eu)
#define STAGE72_G_BANK_ATTACKER (*(volatile Stage72U8 *)0x02023CCBu)
#define STAGE72_G_BANK_TARGET (*(volatile Stage72U8 *)0x02023CCCu)
#define STAGE72_G_ABSENT_FLAGS (*(volatile Stage72U8 *)0x02023CD0u)
#define STAGE72_G_BATTLE_SCRIPT (*(volatile Stage72U8 **)0x02023CD4u)
#define STAGE72_G_CURRENT_MOVE (*(volatile Stage72U16 *)0x02023CAAu)
#define STAGE72_G_BATTLE_MOVE_DAMAGE (*(volatile Stage72S32 *)0x02023CB0u)
#define STAGE72_G_BATTLE_TYPE_FLAGS (*(volatile Stage72U32 *)0x02022AACu)
#define STAGE72_G_BATTLE_COMMUNICATION ((volatile Stage72U8 *)0x02023DE2u)
#define STAGE72_G_PROTECT_STRUCTS ((volatile Stage72U8 *)0x02023DECu)
#define STAGE72_G_SPECIAL_STATUSES ((volatile Stage72U8 *)0x02023E2Cu)
#define STAGE72_G_BATTLE_WEATHER (*(volatile Stage72U16 *)0x02023E7Cu)
#define STAGE72_G_WISH_FUTURE_KNOCK ((volatile Stage72U8 *)0x02023E80u)
#define STAGE72_G_BATTLE_SCRIPTING ((volatile Stage72U8 *)0x02023F24u)
#define STAGE72_G_MOVE_RESULT_FLAGS (*(volatile Stage72U8 *)0x02023D2Cu)
#define STAGE72_G_HIT_MARKER (*(volatile Stage72U32 *)0x02023D30u)
#define STAGE72_G_LAST_USED_ABILITY (*(volatile Stage72U16 *)0x0203DFACu)
#define STAGE72_G_BATTLE_MOVES ((const volatile Stage72U8 *)0x090421F4u)
#define STAGE72_G_NEW_BS (*(volatile Stage72U8 **)0x0203DFB0u)

enum {
    STAGE72_BATTLE_SCRIPTING_ATK49_STATE_OFFSET = 0x14,
    STAGE72_BATTLE_SCRIPTING_BANK_OFFSET = 0x17,
    STAGE72_BATTLE_SCRIPTING_STAT_CHANGER_OFFSET = 0x1A,
    STAGE72_NEW_BS_RESULT_FLAGS_OFFSET = 0x20C,
    STAGE72_NEW_BS_MISS_STRING_OFFSET = 0x210,
    STAGE72_NEW_BS_ELECTRIFY_TIMERS_OFFSET = 0x38,
    STAGE72_WISH_FUTURE_PARTY_INDEX_OFFSET = 8,
    STAGE72_BATTLE_SCRIPT_OPCODE_MOVE_END = 0x49,
    /* Pinned cmd49.c enum: ATK49_SECOND_MOVE_EFFECT. */
    STAGE72_ATK49_SECOND_MOVE_EFFECT = 29,
    /* Pinned cmd49.c enum: ATK49_MAGICIAN_MOXIE_BATTLEBOND. */
    STAGE72_ATK49_KNOCKOUT_ABILITIES = 30,
    STAGE72_ATK49_FATIGUE = 31,
    STAGE72_ARG_IN_FUTURE_ATTACK = 3,
    STAGE72_ARG_ONLY_EMERGENCY_EXIT = 5,
    STAGE72_FLAG_CHECKING_FROM_MENU = 0x04,
    STAGE72_FLAG_AI_CALC = 0x08,
    STAGE72_MOVE_RESULT_MISSED_OR_IMMUNE = 0x09,
    STAGE72_PROTECT_INDIVIDUAL_MASK =
        (1u << 0) | (1u << 22) | (1u << 23) | (1u << 24)
        | (1u << 25) | (1u << 26) | (1u << 27),
    STAGE72_PROTECT_TOUCHED_MASK = 1u << 29,
    STAGE72_STAT_STAGE_MAX = 12,
    STAGE72_STAT_STAGE_BASE_OFFSET = 0x19,
    STAGE72_STAT_ATK = 1,
    STAGE72_STAT_DEF = 2,
    STAGE72_STAT_SPEED = 3,
    STAGE72_STAT_SPATK = 4,
    STAGE72_STAT_SPDEF = 5,
    STAGE72_MOVE_SHORE_UP = 680
};

/* call AbilityPopUp; pause 0x10; call AbilityPopUpRevert; return */
static const Stage72U8 sStage72MegaSolHealingPopupScript[]
    __attribute__((aligned(4))) = {
        0x41, 0x00, 0x12, 0x00, 0x09,
        0x39, 0x10, 0x00,
        0x41, 0x0F, 0x12, 0x00, 0x09,
        0x3C
    };

typedef Stage72U8 (*Stage72FnU8_1)(Stage72U8);
typedef Stage72U8 (*Stage72FnU8Void)(void);
typedef Stage72U8 (*Stage72FnCanBurn)(Stage72U8, Stage72U8, Stage72U8);
typedef Stage72U8 (*Stage72FnMoveBlockedBySubstitute)(Stage72U16, Stage72U8, Stage72U8);
typedef Stage72U8 (*Stage72FnIsTargetAbilityIgnored)(Stage72U16, Stage72U16, Stage72U16);
typedef Stage72U8 (*Stage72FnGetMoveType)(Stage72U8, Stage72U16);
typedef Stage72U8 (*Stage72FnPreAbilityType)(Stage72U16, Stage72U8, void *);
typedef Stage72U8 (*Stage72FnMovePredicate)(Stage72U16);
typedef Stage72U8 (*Stage72FnProtectedByMaxGuard)(Stage72U8, Stage72U16);
typedef Stage72U8 (*Stage72FnCheckContact)(Stage72U16, Stage72U8, Stage72U8);
typedef Stage72U32 (*Stage72FnGetMonData32)(void *, Stage72U8, void *);
typedef Stage72U8 (*Stage72FnHoldEffect)(Stage72U16);
typedef Stage72U8 (*Stage72FnMonItemEffect)(const void *);
typedef Stage72U8 (*Stage72FnMonPredicate)(const void *);
typedef Stage72U8 (*Stage72FnGetBaseMoveTarget)(Stage72U16, Stage72U8);
typedef Stage72U8 (*Stage72FnCheckMoveTable)(Stage72U16, const Stage72U16 *);
typedef Stage72U16 (*Stage72FnGetBaseMaxHp)(Stage72U8);
typedef Stage72U8 (*Stage72FnViableMonCount)(Stage72U8);
typedef void (*Stage72FnRecordAbility)(Stage72U8, Stage72U16);
typedef void (*Stage72FnVoid)(void);

#define STAGE72_FN(type, address) ((type)((Stage72U32)(address) | 1u))

/* Original-entry trampolines are emitted by modernization_p05_ability_rom_runtime_hooks.S. */
extern Stage72U8 Stage72_OriginalAbilityBattleEffects(
    Stage72U8, Stage72U8, Stage72U16, Stage72U16, Stage72U16
);
extern Stage72U8 Stage72_OriginalDoesProtectionMoveBlockMove(
    Stage72U8, Stage72U8, Stage72U16, Stage72U16
);
extern Stage72U8 Stage72_OriginalProtectAffects(
    Stage72U16, Stage72U8, Stage72U8, Stage72U8
);
extern Stage72U8 Stage72_OriginalNonInvasiveCheckGrounding(
    Stage72U8, Stage72U16, Stage72U8, Stage72U8, Stage72U8
);
extern Stage72U8 Stage72_OriginalTypeCalc(
    Stage72U16, Stage72U8, Stage72U8, void *, Stage72U8
);
extern Stage72U8 Stage72_OriginalAITypeCalcPart(
    Stage72U16, Stage72U8, Stage72U8, void *
);
extern Stage72U16 Stage72_OriginalCalcVisualBasePower(
    Stage72U8, Stage72U8, Stage72U16, Stage72U8
);
extern Stage72U8 Stage72_OriginalGetMoveTypeSpecialPostAbility(
    Stage72U16, Stage72U16, Stage72U8
);
extern Stage72U8 Stage72_OriginalGetMoveTypeSpecialPreAbility(
    Stage72U16, Stage72U8, void *
);
extern Stage72U16 Stage72_OriginalAdjustBasePower(void *, Stage72U16);
extern Stage72S32 Stage72_OriginalCalculateBaseDamage(void *);
extern Stage72U8 Stage72_OriginalGetExceptionMoveType(Stage72U8, Stage72U16);
extern Stage72U8 Stage72_OriginalGetMonExceptionMoveType(void *, Stage72U16);
extern Stage72U8 Stage72_OriginalAttacksThisTurn(Stage72U8, Stage72U16);
extern Stage72U8 Stage72_OriginalCheckGrounding(Stage72U8);
extern Stage72U8 Stage72_OriginalCheckMonGrounding(void *);
extern Stage72U8 Stage72_OriginalCheckGroundingByDetails(
    Stage72U16, Stage72U16, Stage72U16
);
extern Stage72U8 Stage72_OriginalAISpecialTypeCalc(
    Stage72U16, Stage72U8, Stage72U8
);
extern Stage72U8 Stage72_OriginalVisualTypeCalcPart(
    Stage72U16, Stage72U8, Stage72U8
);
extern void Stage72_OriginalAtk06TypeCalc(void);
extern void Stage72_OriginalAtk4ATypeCalc2(void);
extern void Stage72_OriginalAtk49MoveEnd(void);
extern Stage72U8 Stage72_OriginalSetMoveEffect2(void);
extern void Stage72_OriginalRecoverBasedOnSunlight(void);
extern void Stage72_OriginalAtk01AccuracyCheck(void);
extern Stage72U32 Stage72_OriginalAccuracyCalc(
    Stage72U16, Stage72U8, Stage72U8
);
extern Stage72U32 Stage72_OriginalVisualAccuracyCalc(
    Stage72U16, Stage72U8, Stage72U8
);
extern Stage72U32 Stage72_OriginalVisualAccuracyCalcNoTarget(
    Stage72U16, Stage72U8
);
extern void Stage72_OriginalModifyGrowthInSun(void);

static Stage72U16 Stage72_ReadU16(const volatile Stage72U8 *address)
{
    return *(const volatile Stage72U16 *)(const volatile void *)address;
}

static Stage72U32 Stage72_ReadU32(const volatile Stage72U8 *address)
{
    return *(const volatile Stage72U32 *)(const volatile void *)address;
}

static void Stage72_WriteU32(volatile Stage72U8 *address, Stage72U32 value)
{
    *(volatile Stage72U32 *)(volatile void *)address = value;
}

static volatile Stage72U8 *Stage72_BattleMon(Stage72U8 bank)
{
    return STAGE72_G_BATTLE_MONS
        + (Stage72U32)bank * STAGE72_BATTLE_MON_STRIDE;
}

static Stage72U16 Stage72_BattleMonAbility(Stage72U8 bank)
{
    return Stage72_ReadU16(
        Stage72_BattleMon(bank) + STAGE72_BATTLE_MON_ABILITY_OFFSET
    );
}

static void Stage72_SetBattleMonAbility(Stage72U8 bank, Stage72U16 ability)
{
    *(volatile Stage72U16 *)(volatile void *)(Stage72_BattleMon(bank)
        + STAGE72_BATTLE_MON_ABILITY_OFFSET) = ability;
}

static Stage72U16 Stage72_BattleMonHp(Stage72U8 bank)
{
    return Stage72_ReadU16(Stage72_BattleMon(bank) + STAGE72_BATTLE_MON_HP_OFFSET);
}

static const volatile Stage72U8 *Stage72_BattleMove(Stage72U16 move)
{
    return STAGE72_G_BATTLE_MOVES + (Stage72U32)move * STAGE72_BATTLE_MOVE_STRIDE;
}

static Stage72U8 Stage72_MoveEffect(Stage72U16 move)
{
    return Stage72_BattleMove(move)[STAGE72_BATTLE_MOVE_EFFECT_OFFSET];
}

static Stage72U8 Stage72_MoveType(Stage72U16 move)
{
    return Stage72_BattleMove(move)[STAGE72_BATTLE_MOVE_TYPE_OFFSET];
}

static Stage72U8 Stage72_MoveSplit(Stage72U16 move)
{
    return Stage72_BattleMove(move)[STAGE72_BATTLE_MOVE_SPLIT_OFFSET];
}

static Stage72U8 Stage72_MoveProtectAffected(Stage72U16 move)
{
    return (Stage72U8)(Stage72_BattleMove(move)[STAGE72_BATTLE_MOVE_FLAGS_OFFSET]
        & STAGE72_MOVE_FLAG_PROTECT_AFFECTED);
}

static Stage72U8 Stage72_MoveTarget(Stage72U16 move, Stage72U8 bankAtk)
{
    return STAGE72_FN(Stage72FnGetBaseMoveTarget, 0x090D5014u)(move, bankAtk);
}

static Stage72U8 Stage72_IsSingleTargetMove(Stage72U16 move, Stage72U8 bankAtk)
{
    Stage72U8 target = Stage72_MoveTarget(move, bankAtk);

    return (Stage72U8)(target == STAGE72_MOVE_TARGET_SELECTED
        || target == STAGE72_MOVE_TARGET_RANDOM);
}

static Stage72U8 Stage72_BankItemEffect(Stage72U8 bank)
{
    if (bank >= STAGE72_G_BATTLERS_COUNT
        || bank >= STAGE72_BATTLER_CAPACITY)
        return 0;
    return STAGE72_FN(Stage72FnU8_1, 0x090D3FECu)(bank);
}

static Stage72U8 Stage72_RecordedItemEffect(Stage72U8 bank)
{
    if (bank >= STAGE72_G_BATTLERS_COUNT
        || bank >= STAGE72_BATTLER_CAPACITY)
        return 0;
    return STAGE72_FN(Stage72FnU8_1, 0x090D4098u)(bank);
}

static Stage72U8 Stage72_WeatherHasEffect(void)
{
    Stage72U8 bank;

    /* Exact pinned WeatherHasEffect semantics: only a living suppressor counts. */
    for (bank = 0; bank < STAGE72_G_BATTLERS_COUNT
        && bank < STAGE72_BATTLER_CAPACITY; ++bank)
    {
        Stage72U16 ability = Stage72_BattleMonAbility(bank);

        if ((ability == STAGE72_ABILITY_CLOUD_NINE
                || ability == STAGE72_ABILITY_AIR_LOCK)
            && Stage72_BattleMonHp(bank) != 0)
            return 0;
    }
    return 1;
}

static Stage72U16 Stage72_DamageU16(const void *data, Stage72U32 offset)
{
    return *(const Stage72U16 *)((const Stage72U8 *)data + offset);
}

static void Stage72_SetDamageU16(void *data, Stage72U32 offset, Stage72U16 value)
{
    *(Stage72U16 *)((Stage72U8 *)data + offset) = value;
}

static Stage72U8 Stage72_DamageU8(const void *data, Stage72U32 offset)
{
    return *((const Stage72U8 *)data + offset);
}

static void *Stage72_DamagePointer(const void *data, Stage72U32 offset)
{
    return *(void * const *)((const Stage72U8 *)data + offset);
}

static Stage72U16 Stage72_ScalePower(
    Stage72U16 power,
    Stage72U16 numerator,
    Stage72U16 denominator
)
{
    Stage72U32 scaled = ((Stage72U32)power * numerator) / denominator;

    if (scaled > 0xFFFFu)
        scaled = 0xFFFFu;
    return (Stage72U16)scaled;
}

static void Stage72_RecordAbility(Stage72U8 bank, Stage72U16 ability)
{
    STAGE72_FN(Stage72FnRecordAbility, 0x090D3FC0u)(bank, ability);
}

static Stage72U8 Stage72_GetMoveType(Stage72U8 bank, Stage72U16 move)
{
    return STAGE72_FN(Stage72FnGetMoveType, 0x090E6234u)(bank, move);
}

static Stage72U16 Stage72_GetMonAbility(const void *mon)
{
    /* The actual return ABI is u16 even though an obsolete header says u8. */
    typedef Stage72U16 (*Fn)(const void *);
    return STAGE72_FN(Fn, 0x090DA23Cu)(mon);
}

static Stage72U16 Stage72_DamageAttackerAbility(const void *damageCalc)
{
    Stage72U16 ability = Stage72_DamageU16(
        damageCalc,
        STAGE72_DAMAGE_ATK_ABILITY_OFFSET
    );
    void *mon = Stage72_DamagePointer(
        damageCalc,
        STAGE72_DAMAGE_MON_ATK_OFFSET
    );

    /* CalculateBaseDamage populates this field lazily on normal calls. */
    if (ability == STAGE72_ABILITY_NONE)
    {
        if (mon != (void *)0)
            ability = Stage72_GetMonAbility(mon);
        else
        {
            Stage72U8 bank = Stage72_DamageU8(
                damageCalc,
                STAGE72_DAMAGE_ATK_BANK_OFFSET
            );
            if (bank < STAGE72_G_BATTLERS_COUNT
                && bank < STAGE72_BATTLER_CAPACITY)
                ability = Stage72_BattleMonAbility(bank);
        }
    }
    return ability;
}

static Stage72U8 Stage72_InactiveTeraBlast(const void *damageCalc)
{
    void *mon = Stage72_DamagePointer(
        damageCalc,
        STAGE72_DAMAGE_MON_ATK_OFFSET
    );

    if (mon != (void *)0)
        return (Stage72U8)!STAGE72_FN(
            Stage72FnMonPredicate,
            0x09130450u
        )(mon);
    {
        Stage72U8 bank = Stage72_DamageU8(
            damageCalc,
            STAGE72_DAMAGE_ATK_BANK_OFFSET
        );

        if (bank >= STAGE72_G_BATTLERS_COUNT
            || bank >= STAGE72_BATTLER_CAPACITY)
            return 0;
        return (Stage72U8)!STAGE72_FN(Stage72FnU8_1, 0x09130674u)(bank);
    }
}

typedef struct Stage72AbilityMap {
    Stage72U8 count;
    Stage72U16 before[STAGE72_BATTLER_CAPACITY];
    Stage72U16 mapped[STAGE72_BATTLER_CAPACITY];
} Stage72AbilityMap;

static void Stage72_MapAllAbilities(
    Stage72AbilityMap *map,
    Stage72U16 from,
    Stage72U16 to
)
{
    Stage72U8 bank;

    map->count = STAGE72_G_BATTLERS_COUNT;
    if (map->count > STAGE72_BATTLER_CAPACITY)
        map->count = 0;
    for (bank = 0; bank < STAGE72_BATTLER_CAPACITY; ++bank)
    {
        map->before[bank] = STAGE72_ABILITY_NONE;
        map->mapped[bank] = 0;
    }
    for (bank = 0; bank < map->count; ++bank)
    {
        map->before[bank] = Stage72_BattleMonAbility(bank);
        if (map->before[bank] == from)
        {
            Stage72_SetBattleMonAbility(bank, to);
            map->mapped[bank] = 1;
        }
    }
}

static void Stage72_RestoreAbilityMap(
    const Stage72AbilityMap *map,
    Stage72U16 temporary
)
{
    Stage72U8 bank;

    for (bank = 0; bank < map->count; ++bank)
    {
        if (map->mapped[bank] && Stage72_BattleMonAbility(bank) == temporary)
            Stage72_SetBattleMonAbility(bank, map->before[bank]);
    }
}

static Stage72U8 Stage72_IsIndividualProtectionActive(Stage72U8 bankDef)
{
    Stage72U32 fields;

    if (bankDef >= STAGE72_G_BATTLERS_COUNT
        || bankDef >= STAGE72_BATTLER_CAPACITY)
        return 0;
    fields = Stage72_ReadU32(STAGE72_G_PROTECT_STRUCTS
        + (Stage72U32)bankDef * STAGE72_PROTECT_STRUCT_STRIDE);
    return (Stage72U8)((fields & STAGE72_PROTECT_INDIVIDUAL_MASK) != 0);
}

static Stage72U16 Stage72_ActiveIndividualProtectMove(Stage72U8 bankDef)
{
    Stage72U32 fields;

    if (bankDef >= STAGE72_G_BATTLERS_COUNT
        || bankDef >= STAGE72_BATTLER_CAPACITY)
        return 0;
    fields = Stage72_ReadU32(STAGE72_G_PROTECT_STRUCTS
        + (Stage72U32)bankDef * STAGE72_PROTECT_STRUCT_STRIDE);
    if (fields & (1u << 0))
        return STAGE72_MOVE_PROTECT;
    if (fields & (1u << 22))
        return STAGE72_MOVE_OBSTRUCT;
    if (fields & (1u << 23))
        return STAGE72_MOVE_SILK_TRAP;
    if (fields & (1u << 24))
        return STAGE72_MOVE_KINGS_SHIELD;
    if (fields & (1u << 25))
        return STAGE72_MOVE_SPIKY_SHIELD;
    if (fields & (1u << 26))
        return STAGE72_MOVE_BANEFUL_BUNKER;
    if (fields & (1u << 27))
        return STAGE72_MOVE_BURNING_BULWARK;
    return 0;
}

static Stage72U8 Stage72_IsPiercingContact(
    Stage72U16 move,
    Stage72U8 bankAtk,
    Stage72U8 bankDef
)
{
    Stage72U16 protectMove;

    if (bankAtk >= STAGE72_G_BATTLERS_COUNT
        || bankDef >= STAGE72_G_BATTLERS_COUNT
        || Stage72_BattleMonAbility(bankAtk) != STAGE72_ABILITY_PIERCING_DRILL
        || !Stage72_IsSingleTargetMove(move, bankAtk)
        || !Stage72_MoveProtectAffected(move)
        || !STAGE72_FN(Stage72FnCheckContact, 0x090D4524u)(move, bankAtk, bankDef)
        || !Stage72_IsIndividualProtectionActive(bankDef)
        || STAGE72_FN(Stage72FnProtectedByMaxGuard, 0x090F2F5Cu)(bankDef, move))
        return 0;

    protectMove = Stage72_ActiveIndividualProtectMove(bankDef);
    if (protectMove == 0)
        return 0;
    /* This also excludes Phantom Force-style moves that already ignore Protect. */
    return Stage72_OriginalDoesProtectionMoveBlockMove(
        bankAtk,
        bankDef,
        move,
        protectMove
    );
}

static Stage72U8 Stage72_IsIndividualProtectMove(Stage72U16 move)
{
    switch (move)
    {
    case STAGE72_MOVE_PROTECT:
    case STAGE72_MOVE_KINGS_SHIELD:
    case STAGE72_MOVE_SPIKY_SHIELD:
    case STAGE72_MOVE_BANEFUL_BUNKER:
    case STAGE72_MOVE_OBSTRUCT:
    case STAGE72_MOVE_SILK_TRAP:
    case STAGE72_MOVE_BURNING_BULWARK:
        return 1;
    default:
        return 0;
    }
}

static Stage72U8 Stage72_BeginVirtualSunForBank(
    Stage72U8 bankAtk,
    Stage72U16 *savedWeather,
    Stage72AbilityMap *cloudNine,
    Stage72AbilityMap *airLock
)
{
    if (bankAtk >= STAGE72_G_BATTLERS_COUNT
        || bankAtk >= STAGE72_BATTLER_CAPACITY
        || Stage72_BattleMonAbility(bankAtk) != STAGE72_ABILITY_MEGA_SOL)
        return 0;

    *savedWeather = STAGE72_G_BATTLE_WEATHER;
    Stage72_MapAllAbilities(
        cloudNine,
        STAGE72_ABILITY_CLOUD_NINE,
        STAGE72_ABILITY_NONE
    );
    Stage72_MapAllAbilities(
        airLock,
        STAGE72_ABILITY_AIR_LOCK,
        STAGE72_ABILITY_NONE
    );
    STAGE72_G_BATTLE_WEATHER = STAGE72_WEATHER_SUN_TEMPORARY;
    return 1;
}

static Stage72U8 Stage72_BeginVirtualSun(
    const void *damageCalc,
    Stage72U16 *savedWeather,
    Stage72AbilityMap *cloudNine,
    Stage72AbilityMap *airLock
)
{
    if (Stage72_DamageAttackerAbility(damageCalc) != STAGE72_ABILITY_MEGA_SOL)
        return 0;
    *savedWeather = STAGE72_G_BATTLE_WEATHER;
    Stage72_MapAllAbilities(
        cloudNine,
        STAGE72_ABILITY_CLOUD_NINE,
        STAGE72_ABILITY_NONE
    );
    Stage72_MapAllAbilities(
        airLock,
        STAGE72_ABILITY_AIR_LOCK,
        STAGE72_ABILITY_NONE
    );
    STAGE72_G_BATTLE_WEATHER = STAGE72_WEATHER_SUN_TEMPORARY;
    return 1;
}

static void Stage72_EndVirtualSun(
    Stage72U16 weather,
    const Stage72AbilityMap *cloudNine,
    const Stage72AbilityMap *airLock
)
{
    STAGE72_G_BATTLE_WEATHER = weather;
    Stage72_RestoreAbilityMap(airLock, STAGE72_ABILITY_NONE);
    Stage72_RestoreAbilityMap(cloudNine, STAGE72_ABILITY_NONE);
}

void Stage72_Atk01AccuracyCheck(void)
{
    Stage72U16 savedWeather = 0;
    Stage72AbilityMap cloudNine;
    Stage72AbilityMap airLock;
    Stage72U8 virtualSun = Stage72_BeginVirtualSunForBank(
        STAGE72_G_BANK_ATTACKER,
        &savedWeather,
        &cloudNine,
        &airLock
    );

    Stage72_OriginalAtk01AccuracyCheck();
    if (virtualSun)
        Stage72_EndVirtualSun(savedWeather, &cloudNine, &airLock);
}

Stage72U32 Stage72_AccuracyCalc(
    Stage72U16 move,
    Stage72U8 bankAtk,
    Stage72U8 bankDef
)
{
    Stage72U16 savedWeather = 0;
    Stage72AbilityMap cloudNine;
    Stage72AbilityMap airLock;
    Stage72U8 virtualSun = Stage72_BeginVirtualSunForBank(
        bankAtk,
        &savedWeather,
        &cloudNine,
        &airLock
    );
    Stage72U32 accuracy = Stage72_OriginalAccuracyCalc(move, bankAtk, bankDef);

    if (virtualSun)
        Stage72_EndVirtualSun(savedWeather, &cloudNine, &airLock);
    return accuracy;
}

Stage72U32 Stage72_VisualAccuracyCalc(
    Stage72U16 move,
    Stage72U8 bankAtk,
    Stage72U8 bankDef
)
{
    Stage72U16 savedWeather = 0;
    Stage72AbilityMap cloudNine;
    Stage72AbilityMap airLock;
    Stage72U8 virtualSun = Stage72_BeginVirtualSunForBank(
        bankAtk,
        &savedWeather,
        &cloudNine,
        &airLock
    );
    Stage72U32 accuracy = Stage72_OriginalVisualAccuracyCalc(
        move,
        bankAtk,
        bankDef
    );

    if (virtualSun)
        Stage72_EndVirtualSun(savedWeather, &cloudNine, &airLock);
    return accuracy;
}

Stage72U32 Stage72_VisualAccuracyCalcNoTarget(
    Stage72U16 move,
    Stage72U8 bankAtk
)
{
    Stage72U16 savedWeather = 0;
    Stage72AbilityMap cloudNine;
    Stage72AbilityMap airLock;
    Stage72U8 virtualSun = Stage72_BeginVirtualSunForBank(
        bankAtk,
        &savedWeather,
        &cloudNine,
        &airLock
    );
    Stage72U32 accuracy = Stage72_OriginalVisualAccuracyCalcNoTarget(
        move,
        bankAtk
    );

    if (virtualSun)
        Stage72_EndVirtualSun(savedWeather, &cloudNine, &airLock);
    return accuracy;
}

void Stage72_ModifyGrowthInSun(void)
{
    Stage72U8 attacker = STAGE72_G_BANK_ATTACKER;

    if (STAGE72_G_CURRENT_MOVE == STAGE72_MOVE_GROWTH
        && attacker < STAGE72_G_BATTLERS_COUNT
        && attacker < STAGE72_BATTLER_CAPACITY
        && Stage72_BattleMonAbility(attacker) == STAGE72_ABILITY_MEGA_SOL)
    {
        STAGE72_G_BATTLE_SCRIPTING[
            STAGE72_BATTLE_SCRIPTING_STAT_CHANGER_OFFSET
        ] += 0x10u;
        Stage72_RecordAbility(attacker, STAGE72_ABILITY_MEGA_SOL);
        return;
    }
    Stage72_OriginalModifyGrowthInSun();
}

Stage72U8 Stage72_GetMoveTypeSpecialPreAbility(
    Stage72U16 move,
    Stage72U8 bankAtk,
    void *monAtk
)
{
    Stage72U8 resolved = Stage72_OriginalGetMoveTypeSpecialPreAbility(
        move,
        bankAtk,
        monAtk
    );

    if (monAtk == (void *)0
        && resolved == STAGE72_TYPE_ELECTRIC
        && Stage72_MoveType(move) == STAGE72_TYPE_NORMAL
        && bankAtk < STAGE72_G_BATTLERS_COUNT
        && bankAtk < STAGE72_BATTLER_CAPACITY
        && Stage72_BattleMonAbility(bankAtk) == STAGE72_ABILITY_DRAGONIZE
        && STAGE72_G_NEW_BS != (volatile Stage72U8 *)0
        && STAGE72_G_NEW_BS[
            STAGE72_NEW_BS_ELECTRIFY_TIMERS_OFFSET + bankAtk
        ] == 0
        && STAGE72_FN(Stage72FnU8Void, 0x090D77F4u)()
        && !STAGE72_FN(Stage72FnCheckMoveTable, 0x09130F38u)(
            move,
            (const Stage72U16 *)0x09040552u
        ))
        return 0xFFu;
    return resolved;
}

Stage72U8 Stage72_GetMoveTypeSpecialPostAbility(
    Stage72U16 move,
    Stage72U16 ability,
    Stage72U8 zMoveActive
)
{
    if ((!zMoveActive || Stage72_MoveSplit(move) == STAGE72_SPLIT_STATUS)
        && !STAGE72_FN(Stage72FnMovePredicate, 0x090F1CF4u)(move)
        && ability == STAGE72_ABILITY_DRAGONIZE
        && Stage72_MoveType(move) == STAGE72_TYPE_NORMAL)
        return STAGE72_TYPE_DRAGON;
    return Stage72_OriginalGetMoveTypeSpecialPostAbility(
        move,
        ability,
        zMoveActive
    );
}

Stage72U16 Stage72_AdjustBasePower(void *damageCalc, Stage72U16 power)
{
    Stage72U16 adjusted = Stage72_OriginalAdjustBasePower(damageCalc, power);
    Stage72U16 ability = Stage72_DamageU16(
        damageCalc,
        STAGE72_DAMAGE_ATK_ABILITY_OFFSET
    );
    Stage72U16 move = Stage72_DamageU16(damageCalc, STAGE72_DAMAGE_MOVE_OFFSET);
    Stage72U8 moveType = Stage72_DamageU8(
        damageCalc,
        STAGE72_DAMAGE_MOVE_TYPE_OFFSET
    );

    if (ability == STAGE72_ABILITY_DRAGONIZE
        && Stage72_MoveType(move) == STAGE72_TYPE_NORMAL
        && moveType == STAGE72_TYPE_DRAGON
        && !STAGE72_FN(Stage72FnMovePredicate, 0x090D6684u)(move)
        && !STAGE72_FN(Stage72FnMovePredicate, 0x090F1CF4u)(move)
        && (STAGE72_FN(Stage72FnPreAbilityType, 0x090E59D0u)(
                move,
                Stage72_DamageU8(damageCalc, STAGE72_DAMAGE_ATK_BANK_OFFSET),
                Stage72_DamagePointer(
                    damageCalc,
                    STAGE72_DAMAGE_MON_ATK_OFFSET
                )
            ) == 0xFFu
            || (move == STAGE72_MOVE_TERA_BLAST
                && Stage72_InactiveTeraBlast(damageCalc))))
    {
        adjusted = Stage72_ScalePower(adjusted, 6, 5);
    }
    else if (ability == STAGE72_ABILITY_FIRE_MANE
        && moveType == STAGE72_TYPE_FIRE)
    {
        adjusted = Stage72_ScalePower(adjusted, 3, 2);
    }
    return adjusted;
}

Stage72S32 Stage72_CalculateBaseDamage(void *damageCalc)
{
    Stage72U16 savedWeather = 0;
    Stage72AbilityMap cloudNine;
    Stage72AbilityMap airLock;
    Stage72AbilityMap flowerGift;
    Stage72U16 savedPartnerAbility = Stage72_DamageU16(
        damageCalc,
        STAGE72_DAMAGE_ATK_PARTNER_ABILITY_OFFSET
    );
    Stage72U8 virtualSun = Stage72_BeginVirtualSun(
        damageCalc,
        &savedWeather,
        &cloudNine,
        &airLock
    );

    /* Personal sun must not activate an ally's field-weather aura.  Flower
     * Gift is the only partner weather ability consumed by this pinned
     * CalculateBaseDamage implementation. */
    if (virtualSun)
    {
        Stage72_MapAllAbilities(
            &flowerGift,
            STAGE72_ABILITY_FLOWER_GIFT,
            STAGE72_ABILITY_NONE
        );
        if (savedPartnerAbility == STAGE72_ABILITY_FLOWER_GIFT)
            Stage72_SetDamageU16(
                damageCalc,
                STAGE72_DAMAGE_ATK_PARTNER_ABILITY_OFFSET,
                STAGE72_ABILITY_NONE
            );
    }
    Stage72S32 damage = Stage72_OriginalCalculateBaseDamage(damageCalc);
    Stage72U8 bankAtk = Stage72_DamageU8(
        damageCalc,
        STAGE72_DAMAGE_ATK_BANK_OFFSET
    );
    Stage72U8 bankDef = Stage72_DamageU8(
        damageCalc,
        STAGE72_DAMAGE_DEF_BANK_OFFSET
    );
    Stage72U16 move = Stage72_DamageU16(damageCalc, STAGE72_DAMAGE_MOVE_OFFSET);

    if (virtualSun)
    {
        if (savedPartnerAbility == STAGE72_ABILITY_FLOWER_GIFT)
            Stage72_SetDamageU16(
                damageCalc,
                STAGE72_DAMAGE_ATK_PARTNER_ABILITY_OFFSET,
                savedPartnerAbility
            );
        Stage72_RestoreAbilityMap(&flowerGift, STAGE72_ABILITY_NONE);
        Stage72_EndVirtualSun(savedWeather, &cloudNine, &airLock);
        if (!(Stage72_DamageU8(damageCalc, STAGE72_DAMAGE_SPECIAL_FLAGS_OFFSET)
            & (STAGE72_FLAG_CHECKING_FROM_MENU | STAGE72_FLAG_AI_CALC)))
            Stage72_RecordAbility(bankAtk, STAGE72_ABILITY_MEGA_SOL);
    }

    if (damage > 0
        && Stage72_DamageU16(damageCalc, STAGE72_DAMAGE_ATK_ABILITY_OFFSET)
            == STAGE72_ABILITY_PIERCING_DRILL
        && Stage72_MoveEffect(move) != STAGE72_MOVE_EFFECT_OHKO
        && !STAGE72_FN(Stage72FnMovePredicate, 0x090D6684u)(move)
        && !STAGE72_FN(Stage72FnMovePredicate, 0x090F1CF4u)(move)
        && Stage72_IsPiercingContact(move, bankAtk, bankDef))
    {
        damage /= 4;
        if (damage == 0)
            damage = 1;
        Stage72_RecordAbility(bankAtk, STAGE72_ABILITY_PIERCING_DRILL);
    }
    return damage;
}

Stage72U16 Stage72_CalcVisualBasePower(
    Stage72U8 bankAtk,
    Stage72U8 bankDef,
    Stage72U16 move,
    Stage72U8 ignoreDef
)
{
    Stage72U16 savedWeather;
    Stage72AbilityMap cloudNine;
    Stage72AbilityMap airLock;

    if (bankAtk < STAGE72_G_BATTLERS_COUNT
        && Stage72_BattleMonAbility(bankAtk) == STAGE72_ABILITY_MEGA_SOL)
    {
        savedWeather = STAGE72_G_BATTLE_WEATHER;
        Stage72_MapAllAbilities(
            &cloudNine,
            STAGE72_ABILITY_CLOUD_NINE,
            STAGE72_ABILITY_NONE
        );
        Stage72_MapAllAbilities(
            &airLock,
            STAGE72_ABILITY_AIR_LOCK,
            STAGE72_ABILITY_NONE
        );
        STAGE72_G_BATTLE_WEATHER = STAGE72_WEATHER_SUN_TEMPORARY;
        {
            Stage72U16 power = Stage72_OriginalCalcVisualBasePower(
                bankAtk,
                bankDef,
                move,
                ignoreDef
            );
            Stage72_EndVirtualSun(savedWeather, &cloudNine, &airLock);
            return power;
        }
    }
    return Stage72_OriginalCalcVisualBasePower(bankAtk, bankDef, move, ignoreDef);
}

Stage72U8 Stage72_GetExceptionMoveType(Stage72U8 bankAtk, Stage72U16 move)
{
    if (move == STAGE72_MOVE_TERA_BLAST
        && bankAtk < STAGE72_G_BATTLERS_COUNT
        && bankAtk < STAGE72_BATTLER_CAPACITY
        && Stage72_BattleMonAbility(bankAtk) == STAGE72_ABILITY_DRAGONIZE
        && !STAGE72_FN(Stage72FnU8_1, 0x09130674u)(bankAtk))
        return STAGE72_TYPE_DRAGON;
    if (move == STAGE72_MOVE_WEATHER_BALL
        && bankAtk < STAGE72_G_BATTLERS_COUNT
        && Stage72_BattleMonAbility(bankAtk) == STAGE72_ABILITY_MEGA_SOL)
        return STAGE72_TYPE_FIRE;
    return Stage72_OriginalGetExceptionMoveType(bankAtk, move);
}

Stage72U8 Stage72_GetMonExceptionMoveType(void *mon, Stage72U16 move)
{
    if (move == STAGE72_MOVE_TERA_BLAST
        && Stage72_GetMonAbility(mon) == STAGE72_ABILITY_DRAGONIZE
        && !STAGE72_FN(Stage72FnMonPredicate, 0x09130450u)(mon))
        return STAGE72_TYPE_DRAGON;
    if (move == STAGE72_MOVE_WEATHER_BALL
        && Stage72_GetMonAbility(mon) == STAGE72_ABILITY_MEGA_SOL)
        return STAGE72_TYPE_FIRE;
    return Stage72_OriginalGetMonExceptionMoveType(mon, move);
}

Stage72U8 Stage72_AttacksThisTurn(Stage72U8 bank, Stage72U16 move)
{
    if (bank < STAGE72_G_BATTLERS_COUNT
        && Stage72_BattleMonAbility(bank) == STAGE72_ABILITY_MEGA_SOL
        && Stage72_MoveEffect(move) == STAGE72_MOVE_EFFECT_SOLAR_BEAM)
        return 2;
    return Stage72_OriginalAttacksThisTurn(bank, move);
}

Stage72U8 Stage72_CheckGrounding(Stage72U8 bank)
{
    Stage72U16 before;
    Stage72U8 grounded;

    if (bank >= STAGE72_G_BATTLERS_COUNT
        || bank >= STAGE72_BATTLER_CAPACITY)
        return Stage72_OriginalCheckGrounding(bank);
    before = Stage72_BattleMonAbility(bank);
    if (before != STAGE72_ABILITY_EELEVATE)
        return Stage72_OriginalCheckGrounding(bank);
    Stage72_SetBattleMonAbility(bank, STAGE72_ABILITY_LEVITATE);
    grounded = Stage72_OriginalCheckGrounding(bank);
    if (Stage72_BattleMonAbility(bank) == STAGE72_ABILITY_LEVITATE)
        Stage72_SetBattleMonAbility(bank, before);
    return grounded;
}

Stage72U8 Stage72_NonInvasiveCheckGrounding(
    Stage72U8 bank,
    Stage72U16 ability,
    Stage72U8 type1,
    Stage72U8 type2,
    Stage72U8 type3
)
{
    if (ability == STAGE72_ABILITY_EELEVATE)
        ability = STAGE72_ABILITY_LEVITATE;
    return Stage72_OriginalNonInvasiveCheckGrounding(
        bank,
        ability,
        type1,
        type2,
        type3
    );
}

Stage72U8 Stage72_CheckMonGrounding(void *mon)
{
    Stage72U16 ability = Stage72_GetMonAbility(mon);

    if (ability == STAGE72_ABILITY_EELEVATE)
    {
        Stage72U16 item;

        if (STAGE72_FN(Stage72FnU8Void, 0x090D77C8u)())
            return 1;
        item = (Stage72U16)STAGE72_FN(Stage72FnGetMonData32, 0x0803F355u)(
            mon,
            12,
            (void *)0
        );
        if (STAGE72_FN(Stage72FnHoldEffect, 0x0910FDD0u)(item)
            == STAGE72_ITEM_EFFECT_IRON_BALL)
            return 1;
        return 0;
    }
    return Stage72_OriginalCheckMonGrounding(mon);
}

Stage72U8 Stage72_CheckGroundingByDetails(
    Stage72U16 species,
    Stage72U16 item,
    Stage72U16 ability
)
{
    if (ability == STAGE72_ABILITY_EELEVATE)
        ability = STAGE72_ABILITY_LEVITATE;
    return Stage72_OriginalCheckGroundingByDetails(species, item, ability);
}

static Stage72U16 Stage72_MapDefenderToLevitate(Stage72U8 bankDef)
{
    Stage72U16 ability;

    if (bankDef >= STAGE72_G_BATTLERS_COUNT
        || bankDef >= STAGE72_BATTLER_CAPACITY)
        return STAGE72_ABILITY_NONE;
    ability = Stage72_BattleMonAbility(bankDef);
    if (ability == STAGE72_ABILITY_EELEVATE)
        Stage72_SetBattleMonAbility(bankDef, STAGE72_ABILITY_LEVITATE);
    return ability;
}

static Stage72U8 Stage72_IsDamagingGroundMove(
    Stage72U16 move,
    Stage72U8 bankAtk
)
{
    return (Stage72U8)(Stage72_MoveSplit(move) != STAGE72_SPLIT_STATUS
        && Stage72_GetMoveType(bankAtk, move) == STAGE72_TYPE_GROUND
        && move != STAGE72_MOVE_THOUSAND_ARROWS);
}

static Stage72U8 Stage72_ApplyShieldedEelevateImmunity(
    Stage72U16 move,
    Stage72U8 bankAtk,
    Stage72U8 bankDef,
    Stage72U16 originalAbility,
    Stage72U8 itemEffect,
    Stage72U8 flags
)
{
    if (originalAbility == STAGE72_ABILITY_EELEVATE
        && Stage72_IsDamagingGroundMove(move, bankAtk)
        && itemEffect == STAGE72_ITEM_EFFECT_ABILITY_SHIELD
        && !Stage72_CheckGrounding(bankDef))
        flags |= STAGE72_MOVE_RESULT_MISSED_OR_IMMUNE;
    return flags;
}

static void Stage72_RestoreDefender(
    Stage72U8 bankDef,
    Stage72U16 ability
)
{
    if (ability == STAGE72_ABILITY_EELEVATE
        && Stage72_BattleMonAbility(bankDef) == STAGE72_ABILITY_LEVITATE)
        Stage72_SetBattleMonAbility(bankDef, ability);
}

static void Stage72_CorrectEelevateRecord(
    Stage72U16 move,
    Stage72U8 bankAtk,
    Stage72U8 bankDef,
    Stage72U8 flags,
    Stage72U16 originalAbility
)
{
    if (originalAbility == STAGE72_ABILITY_EELEVATE
        && Stage72_MoveSplit(move) != STAGE72_SPLIT_STATUS
        && Stage72_GetMoveType(bankAtk, move) == STAGE72_TYPE_GROUND
        && move != STAGE72_MOVE_THOUSAND_ARROWS
        && (flags & STAGE72_MOVE_RESULT_MISSED_OR_IMMUNE)
            == STAGE72_MOVE_RESULT_MISSED_OR_IMMUNE)
    {
        STAGE72_G_LAST_USED_ABILITY = STAGE72_ABILITY_EELEVATE;
        Stage72_RecordAbility(bankDef, STAGE72_ABILITY_EELEVATE);
    }
}

Stage72U8 Stage72_TypeCalc(
    Stage72U16 move,
    Stage72U8 bankAtk,
    Stage72U8 bankDef,
    void *monAtk,
    Stage72U8 checkParty
)
{
    Stage72U16 ability = STAGE72_ABILITY_NONE;
    if (Stage72_MoveSplit(move) != STAGE72_SPLIT_STATUS)
        ability = Stage72_MapDefenderToLevitate(bankDef);
    Stage72U8 flags = Stage72_OriginalTypeCalc(
        move,
        bankAtk,
        bankDef,
        monAtk,
        checkParty
    );

    Stage72_RestoreDefender(bankDef, ability);
    flags = Stage72_ApplyShieldedEelevateImmunity(
        move,
        bankAtk,
        bankDef,
        ability,
        Stage72_BankItemEffect(bankDef),
        flags
    );
    Stage72_CorrectEelevateRecord(move, bankAtk, bankDef, flags, ability);
    return flags;
}

Stage72U8 Stage72_AITypeCalcPart(
    Stage72U16 move,
    Stage72U8 bankAtk,
    Stage72U8 bankDef,
    void *monDef
)
{
    Stage72U8 flags = Stage72_OriginalAITypeCalcPart(
        move,
        bankAtk,
        bankDef,
        monDef
    );
    Stage72U16 ability = Stage72_GetMonAbility(monDef);

    if (ability == STAGE72_ABILITY_EELEVATE
        && Stage72_GetMoveType(bankAtk, move) == STAGE72_TYPE_GROUND
        && Stage72_MoveSplit(move) != STAGE72_SPLIT_STATUS
        && move != STAGE72_MOVE_THOUSAND_ARROWS
        && !Stage72_CheckMonGrounding(monDef)
        && (STAGE72_FN(Stage72FnMonItemEffect, 0x090D4048u)(monDef)
                == STAGE72_ITEM_EFFECT_ABILITY_SHIELD
            || !STAGE72_FN(Stage72FnIsTargetAbilityIgnored, 0x090BBB78u)(
                ability,
                Stage72_BattleMonAbility(bankAtk),
                move
            )))
        flags |= STAGE72_MOVE_RESULT_MISSED_OR_IMMUNE;
    return flags;
}

Stage72U8 Stage72_AISpecialTypeCalc(
    Stage72U16 move,
    Stage72U8 bankAtk,
    Stage72U8 bankDef
)
{
    Stage72U16 ability = STAGE72_ABILITY_NONE;
    if (Stage72_MoveSplit(move) != STAGE72_SPLIT_STATUS)
        ability = Stage72_MapDefenderToLevitate(bankDef);
    Stage72U8 flags = Stage72_OriginalAISpecialTypeCalc(move, bankAtk, bankDef);

    Stage72_RestoreDefender(bankDef, ability);
    flags = Stage72_ApplyShieldedEelevateImmunity(
        move,
        bankAtk,
        bankDef,
        ability,
        Stage72_BankItemEffect(bankDef),
        flags
    );
    return flags;
}

Stage72U8 Stage72_VisualTypeCalcPart(
    Stage72U16 move,
    Stage72U8 bankAtk,
    Stage72U8 bankDef
)
{
    typedef Stage72U16 (*GetRecorded)(Stage72U8);
    Stage72U16 recorded = STAGE72_FN(GetRecorded, 0x090D3E18u)(bankDef);
    Stage72U8 flags;

    if (recorded == STAGE72_ABILITY_EELEVATE
        && Stage72_MoveSplit(move) != STAGE72_SPLIT_STATUS)
        Stage72_RecordAbility(bankDef, STAGE72_ABILITY_LEVITATE);
    flags = Stage72_OriginalVisualTypeCalcPart(move, bankAtk, bankDef);
    if (recorded == STAGE72_ABILITY_EELEVATE
        && Stage72_MoveSplit(move) != STAGE72_SPLIT_STATUS)
        Stage72_RecordAbility(bankDef, recorded);
    flags = Stage72_ApplyShieldedEelevateImmunity(
        move,
        bankAtk,
        bankDef,
        recorded,
        Stage72_RecordedItemEffect(bankDef),
        flags
    );
    return flags;
}

static void Stage72_CorrectMappedEelevateBanks(
    const Stage72AbilityMap *map,
    Stage72U16 move,
    Stage72U8 bankAtk
)
{
    Stage72U8 bank;
    Stage72U8 corrected = 0;

    if (!Stage72_IsDamagingGroundMove(move, bankAtk))
        return;
    for (bank = 0; bank < map->count; ++bank)
    {
        if (map->mapped[bank] && !Stage72_CheckGrounding(bank))
        {
            if (Stage72_BankItemEffect(bank)
                == STAGE72_ITEM_EFFECT_ABILITY_SHIELD)
            {
                if (STAGE72_G_NEW_BS != (volatile Stage72U8 *)0)
                    STAGE72_G_NEW_BS[
                        STAGE72_NEW_BS_RESULT_FLAGS_OFFSET + bank
                    ] |= STAGE72_MOVE_RESULT_MISSED_OR_IMMUNE;
                if (bank == STAGE72_G_BANK_TARGET)
                    STAGE72_G_MOVE_RESULT_FLAGS |=
                        STAGE72_MOVE_RESULT_MISSED_OR_IMMUNE;
            }
            Stage72_RecordAbility(bank, STAGE72_ABILITY_EELEVATE);
            corrected = 1;
        }
    }
    if (corrected && STAGE72_G_LAST_USED_ABILITY == STAGE72_ABILITY_LEVITATE)
        STAGE72_G_LAST_USED_ABILITY = STAGE72_ABILITY_EELEVATE;
}

static Stage72U8 Stage72_ResolvePresentDamageAttacker(
    Stage72U8 holder,
    Stage72U8 *resolved
)
{
    Stage72U8 attacker = STAGE72_G_BANK_ATTACKER;

    if (resolved == (Stage72U8 *)0
        || holder >= STAGE72_G_BATTLERS_COUNT
        || holder >= STAGE72_BATTLER_CAPACITY
        || attacker >= STAGE72_G_BATTLERS_COUNT
        || attacker >= STAGE72_BATTLER_CAPACITY)
        return 0;

    if (STAGE72_G_BATTLE_SCRIPT != (volatile Stage72U8 *)0
        && STAGE72_G_BATTLE_SCRIPT[1] == STAGE72_ARG_IN_FUTURE_ATTACK)
    {
        Stage72U32 partyIndex = Stage72_ReadU32(
            STAGE72_G_WISH_FUTURE_KNOCK
            + STAGE72_WISH_FUTURE_PARTY_INDEX_OFFSET
            + (Stage72U32)holder * 4u
        );
        Stage72U8 candidate;
        Stage72U8 index;

        /* Doubles has exactly the nominal bank and its same-side partner. */
        for (index = 0; index < 2; ++index)
        {
            candidate = index == 0 ? attacker : (Stage72U8)(attacker ^ 2u);
            if (candidate < STAGE72_G_BATTLERS_COUNT
                && candidate < STAGE72_BATTLER_CAPACITY
                && !(STAGE72_G_ABSENT_FLAGS & (1u << candidate))
                && Stage72_BattleMonHp(candidate) != 0
                && STAGE72_G_BATTLER_PARTY_INDEXES[candidate] == partyIndex)
            {
                *resolved = candidate;
                return 1;
            }
        }
        return 0;
    }

    if (STAGE72_G_ABSENT_FLAGS & (1u << attacker)
        || Stage72_BattleMonHp(attacker) == 0)
        return 0;
    *resolved = attacker;
    return 1;
}

Stage72U8 Stage72_AbilityBattleEffects(
    Stage72U8 caseId,
    Stage72U8 bank,
    Stage72U16 ability,
    Stage72U16 special,
    Stage72U16 moveArg
)
{
    Stage72U8 effect = Stage72_OriginalAbilityBattleEffects(
        caseId,
        bank,
        ability,
        special,
        moveArg
    );
    Stage72U8 attacker = STAGE72_G_BANK_ATTACKER;
    Stage72U16 move = moveArg ? moveArg : STAGE72_G_CURRENT_MOVE;

    if (effect
        || caseId != STAGE72_ABILITY_EFFECT_CONTACT
        || bank >= STAGE72_G_BATTLERS_COUNT
        || Stage72_BattleMonAbility(bank) != STAGE72_ABILITY_SPICY_SPRAY
        || STAGE72_G_LAST_USED_ABILITY != STAGE72_ABILITY_SPICY_SPRAY
        || STAGE72_G_BATTLE_TYPE_FLAGS
            & (STAGE72_BATTLE_TYPE_SAFARI | STAGE72_BATTLE_TYPE_OLD_MAN)
        || !Stage72_ResolvePresentDamageAttacker(bank, &attacker)
        || attacker == bank
        || STAGE72_G_MOVE_RESULT_FLAGS & STAGE72_MOVE_RESULT_NO_EFFECT
        || (!Stage72_ReadU32(STAGE72_G_SPECIAL_STATUSES
                + (Stage72U32)bank * STAGE72_SPECIAL_STATUS_STRIDE
                + STAGE72_SPECIAL_STATUS_PHYSICAL_DAMAGE_OFFSET)
            && !Stage72_ReadU32(STAGE72_G_SPECIAL_STATUSES
                + (Stage72U32)bank * STAGE72_SPECIAL_STATUS_STRIDE
                + STAGE72_SPECIAL_STATUS_SPECIAL_DAMAGE_OFFSET))
        || STAGE72_FN(Stage72FnMoveBlockedBySubstitute, 0x090D6268u)(
            move,
            attacker,
            bank
        )
        || !STAGE72_FN(Stage72FnCanBurn, 0x090D745Cu)(attacker, bank, 1))
        return effect;

    STAGE72_G_BATTLE_COMMUNICATION[3] =
        STAGE72_MOVE_EFFECT_AFFECTS_USER | STAGE72_MOVE_EFFECT_BURN;
    STAGE72_FN(Stage72FnVoid, 0x08016D55u)();
    STAGE72_G_BATTLE_SCRIPT = (volatile Stage72U8 *)0x0900070Bu;
    STAGE72_G_HIT_MARKER |= STAGE72_HITMARKER_IGNORE_SAFEGUARD;
    STAGE72_G_LAST_USED_ABILITY = STAGE72_ABILITY_SPICY_SPRAY;
    Stage72_RecordAbility(bank, STAGE72_ABILITY_SPICY_SPRAY);
    return 1;
}

Stage72U8 Stage72_ProtectAffects(
    Stage72U16 move,
    Stage72U8 bankAtk,
    Stage72U8 bankDef,
    Stage72U8 set
)
{
    Stage72U8 savedCommunication = STAGE72_G_BATTLE_COMMUNICATION[6];
    Stage72U8 savedMissString = 0;
    Stage72U8 canRestoreMissString = (Stage72U8)(
        STAGE72_G_NEW_BS != (volatile Stage72U8 *)0
        && bankDef < STAGE72_G_BATTLERS_COUNT
        && bankDef < STAGE72_BATTLER_CAPACITY
    );

    if (canRestoreMissString)
        savedMissString = STAGE72_G_NEW_BS[
            STAGE72_NEW_BS_MISS_STRING_OFFSET + bankDef
        ];
    Stage72U8 affected = Stage72_OriginalProtectAffects(
        move,
        bankAtk,
        bankDef,
        set
    );

    if (affected && Stage72_IsPiercingContact(move, bankAtk, bankDef))
    {
        volatile Stage72U8 *protect = STAGE72_G_PROTECT_STRUCTS
            + (Stage72U32)bankDef * STAGE72_PROTECT_STRUCT_STRIDE;
        Stage72U32 savedFields = Stage72_ReadU32(protect);
        Stage72U8 sideGuardAffected;

        Stage72_WriteU32(
            protect,
            savedFields & ~(Stage72U32)STAGE72_PROTECT_INDIVIDUAL_MASK
        );
        sideGuardAffected = Stage72_OriginalProtectAffects(
            move,
            bankAtk,
            bankDef,
            set
        );
        Stage72_WriteU32(protect, savedFields);
        if (sideGuardAffected)
            return affected;
        /* Keep touchedProtectLike for the shield's contact reaction, but the
         * bypassed individual shield must not leave a false miss message. */
        STAGE72_G_BATTLE_COMMUNICATION[6] = savedCommunication;
        if (canRestoreMissString)
            STAGE72_G_NEW_BS[
                STAGE72_NEW_BS_MISS_STRING_OFFSET + bankDef
            ] = savedMissString;
        STAGE72_G_LAST_USED_ABILITY = STAGE72_ABILITY_PIERCING_DRILL;
        Stage72_RecordAbility(bankAtk, STAGE72_ABILITY_PIERCING_DRILL);
        return 0;
    }
    return affected;
}

Stage72U8 Stage72_DoesProtectionMoveBlockMove(
    Stage72U8 bankAtk,
    Stage72U8 bankDef,
    Stage72U16 attackMove,
    Stage72U16 protectMove
)
{
    Stage72U8 blocked = Stage72_OriginalDoesProtectionMoveBlockMove(
        bankAtk,
        bankDef,
        attackMove,
        protectMove
    );

    if (blocked
        && Stage72_IsIndividualProtectMove(protectMove)
        && bankAtk < STAGE72_G_BATTLERS_COUNT
        && Stage72_BattleMonAbility(bankAtk) == STAGE72_ABILITY_PIERCING_DRILL
        && Stage72_IsSingleTargetMove(attackMove, bankAtk)
        && STAGE72_FN(Stage72FnCheckContact, 0x090D4524u)(
            attackMove,
            bankAtk,
            bankDef
        ))
        return 0;
    return blocked;
}

void Stage72_Atk06TypeCalc(void)
{
    Stage72AbilityMap map;
    Stage72U16 move = STAGE72_G_CURRENT_MOVE;
    Stage72U8 attacker = STAGE72_G_BANK_ATTACKER;

    if (Stage72_MoveSplit(move) == STAGE72_SPLIT_STATUS)
        map.count = 0;
    else
        Stage72_MapAllAbilities(
            &map,
            STAGE72_ABILITY_EELEVATE,
            STAGE72_ABILITY_LEVITATE
        );

    Stage72_OriginalAtk06TypeCalc();
    Stage72_RestoreAbilityMap(&map, STAGE72_ABILITY_LEVITATE);
    Stage72_CorrectMappedEelevateBanks(&map, move, attacker);
}

void Stage72_Atk4ATypeCalc2(void)
{
    Stage72U8 target = STAGE72_G_BANK_TARGET;
    Stage72U16 move = STAGE72_G_CURRENT_MOVE;
    Stage72U16 ability = STAGE72_ABILITY_NONE;

    if (Stage72_MoveSplit(move) != STAGE72_SPLIT_STATUS)
        ability = Stage72_MapDefenderToLevitate(target);

    Stage72_OriginalAtk4ATypeCalc2();
    Stage72_RestoreDefender(target, ability);
    STAGE72_G_MOVE_RESULT_FLAGS = Stage72_ApplyShieldedEelevateImmunity(
        move,
        STAGE72_G_BANK_ATTACKER,
        target,
        ability,
        Stage72_BankItemEffect(target),
        STAGE72_G_MOVE_RESULT_FLAGS
    );
    Stage72_CorrectEelevateRecord(
        move,
        STAGE72_G_BANK_ATTACKER,
        target,
        STAGE72_G_MOVE_RESULT_FLAGS,
        ability
    );
}

static Stage72U8 Stage72_HighestRawStatId(Stage72U8 bank)
{
    static const Stage72U8 statIds[5] = {
        STAGE72_STAT_ATK,
        STAGE72_STAT_DEF,
        STAGE72_STAT_SPATK,
        STAGE72_STAT_SPDEF,
        STAGE72_STAT_SPEED
    };
    static const Stage72U8 offsets[5] = {2, 4, 8, 10, 6};
    Stage72U16 values[5];
    Stage72U8 highest = 0;
    Stage72U8 index;
    volatile Stage72U8 *mon = Stage72_BattleMon(bank);

    for (index = 0; index < 5; ++index)
        values[index] = Stage72_ReadU16(mon + offsets[index]);
    if (STAGE72_FN(Stage72FnU8Void, 0x090D779Cu)())
    {
        Stage72U16 swap = values[1];
        values[1] = values[3];
        values[3] = swap;
    }
    for (index = 1; index < 5; ++index)
    {
        if (values[index] > values[highest])
            highest = index;
    }
    return statIds[highest];
}

static Stage72U8 Stage72_ShouldMapEelevateForKnockout(
    Stage72U8 *ownerOut,
    Stage72U8 expectedState
)
{
    Stage72U8 attacker = STAGE72_G_BANK_ATTACKER;
    Stage72U8 owner = attacker;
    Stage72U8 target = STAGE72_G_BANK_TARGET;
    Stage72U8 arg1;
    Stage72U8 stat;
    const volatile Stage72U8 *status;

    if (ownerOut == (Stage72U8 *)0
        || attacker >= STAGE72_G_BATTLERS_COUNT
        || attacker >= STAGE72_BATTLER_CAPACITY
        || target >= STAGE72_G_BATTLERS_COUNT
        || target >= STAGE72_BATTLER_CAPACITY
        || STAGE72_G_BATTLE_SCRIPT == (volatile Stage72U8 *)0
        || STAGE72_G_BATTLE_SCRIPTING[STAGE72_BATTLE_SCRIPTING_ATK49_STATE_OFFSET]
            != expectedState)
        return 0;
    arg1 = STAGE72_G_BATTLE_SCRIPT[1];
    if (arg1 == STAGE72_ARG_ONLY_EMERGENCY_EXIT
        || !Stage72_ResolvePresentDamageAttacker(target, &owner)
        || Stage72_BattleMonAbility(owner) != STAGE72_ABILITY_EELEVATE
        || Stage72_BattleMonHp(target) != 0
        || STAGE72_G_MOVE_RESULT_FLAGS & STAGE72_MOVE_RESULT_NO_EFFECT)
        return 0;
    status = STAGE72_G_SPECIAL_STATUSES
        + (Stage72U32)target * STAGE72_SPECIAL_STATUS_STRIDE;
    if (!Stage72_ReadU32(status + STAGE72_SPECIAL_STATUS_PHYSICAL_DAMAGE_OFFSET)
        && !Stage72_ReadU32(status + STAGE72_SPECIAL_STATUS_SPECIAL_DAMAGE_OFFSET))
        return 0;
    if (!STAGE72_FN(Stage72FnViableMonCount, 0x090D44FCu)(owner ^ 1u))
        return 0;
    stat = Stage72_HighestRawStatId(owner);
    if (Stage72_BattleMon(owner)[
        STAGE72_STAT_STAGE_BASE_OFFSET + stat - 1
    ] >= STAGE72_STAT_STAGE_MAX)
        return 0;
    *ownerOut = owner;
    return 1;
}

Stage72U8 Stage72_SetMoveEffect2(void)
{
    Stage72U8 effect = Stage72_OriginalSetMoveEffect2();
    Stage72U8 owner = STAGE72_G_BANK_ATTACKER;

    /* Pinned atk49_moveend normally falls straight from state 29 into state
     * 30 inside one do-while call when SetMoveEffect2 returns false.  Yield the
     * command for exactly an eligible Eelevate KO so the entry adapter gets a
     * state-30 boundary on the next interpreter tick.  No script/global is
     * changed here; the original command increments state to 30 immediately
     * after it observes this true return. */
    if (!effect
        && STAGE72_G_BATTLE_SCRIPT != (volatile Stage72U8 *)0
        && STAGE72_G_BATTLE_SCRIPT[0]
            == STAGE72_BATTLE_SCRIPT_OPCODE_MOVE_END
        && Stage72_ShouldMapEelevateForKnockout(
            &owner,
            STAGE72_ATK49_SECOND_MOVE_EFFECT
        ))
        return 1;
    return effect;
}

void Stage72_Atk49MoveEnd(void)
{
    Stage72U8 state = STAGE72_G_BATTLE_SCRIPTING[
        STAGE72_BATTLE_SCRIPTING_ATK49_STATE_OFFSET
    ];
    Stage72U8 arg1 = STAGE72_G_BATTLE_SCRIPT == (volatile Stage72U8 *)0
        ? 0
        : STAGE72_G_BATTLE_SCRIPT[1];
    Stage72U8 owner;
    Stage72U8 mapped;

    /* State 30 leaves the real Future Sight owner in gBankAttacker while the
     * queued Moxie script executes: statbuffchange and playanimation both use
     * BANK_ATTACKER.  The next atk49 entry is state 31, after that script has
     * returned, so only then restore the pinned move-end attacker backup.  Do
     * not restore gBankTarget: it still identifies the fainted damage holder. */
    if (state == STAGE72_ATK49_FATIGUE
        && arg1 == STAGE72_ARG_IN_FUTURE_ATTACK)
    {
        Stage72U8 target = STAGE72_G_BANK_TARGET;

        STAGE72_FN(Stage72FnVoid, 0x090CC214u)();
        STAGE72_G_BANK_TARGET = target;
    }

    owner = STAGE72_G_BANK_ATTACKER;
    mapped = Stage72_ShouldMapEelevateForKnockout(
        &owner,
        STAGE72_ATK49_KNOCKOUT_ABILITIES
    );

    if (mapped)
    {
        Stage72_SetBattleMonAbility(owner, STAGE72_ABILITY_BEAST_BOOST);
        /* Exact state-30 adapter.  Keep this bank through BattleScript_Moxie;
         * the state-31 prelude above restores it after the script completes. */
        STAGE72_G_BANK_ATTACKER = owner;
    }
    Stage72_OriginalAtk49MoveEnd();
    if (mapped && Stage72_BattleMonAbility(owner) == STAGE72_ABILITY_BEAST_BOOST)
        Stage72_SetBattleMonAbility(owner, STAGE72_ABILITY_EELEVATE);
    if (mapped && STAGE72_G_LAST_USED_ABILITY == STAGE72_ABILITY_BEAST_BOOST)
        STAGE72_G_LAST_USED_ABILITY = STAGE72_ABILITY_EELEVATE;
    if (mapped)
        Stage72_RecordAbility(owner, STAGE72_ABILITY_EELEVATE);
}

void Stage72_RecoverBasedOnSunlight(void)
{
    Stage72U8 attacker = STAGE72_G_BANK_ATTACKER;

    if (attacker < STAGE72_G_BATTLERS_COUNT
        && Stage72_BattleMonAbility(attacker) == STAGE72_ABILITY_MEGA_SOL
        && STAGE72_G_CURRENT_MOVE != STAGE72_MOVE_SHORE_UP)
    {
        Stage72U16 maximum = STAGE72_FN(
            Stage72FnGetBaseMaxHp,
            0x090D4218u
        )(attacker);

        STAGE72_G_BANK_TARGET = attacker;
        if (Stage72_BattleMonHp(attacker) < maximum)
        {
            Stage72S32 amount = (Stage72S32)(((Stage72U32)maximum * 2u) / 3u);
            Stage72U8 originalAlreadyTwoThirds = (Stage72U8)(
                STAGE72_G_BATTLE_WEATHER != 0
                && !(STAGE72_G_BATTLE_WEATHER
                    & STAGE72_WEATHER_AIR_CURRENT_PRIMAL)
                && Stage72_WeatherHasEffect()
                && (STAGE72_G_BATTLE_WEATHER & STAGE72_WEATHER_SUN_ANY)
                && Stage72_BankItemEffect(attacker)
                    != STAGE72_ITEM_EFFECT_UTILITY_UMBRELLA
            );

            if (amount < 1)
                amount = 1;
            STAGE72_G_BATTLE_MOVE_DAMAGE = -amount;
            STAGE72_G_BATTLE_SCRIPT += 5;
            if (!originalAlreadyTwoThirds)
            {
                STAGE72_G_BATTLE_SCRIPTING[
                    STAGE72_BATTLE_SCRIPTING_BANK_OFFSET
                ] = attacker;
                STAGE72_G_LAST_USED_ABILITY = STAGE72_ABILITY_MEGA_SOL;
                Stage72_RecordAbility(attacker, STAGE72_ABILITY_MEGA_SOL);
                STAGE72_FN(Stage72FnVoid, 0x08016D55u)();
                STAGE72_G_BATTLE_SCRIPT =
                    (volatile Stage72U8 *)sStage72MegaSolHealingPopupScript;
            }
        }
        else
        {
            const volatile Stage72U8 *script = STAGE72_G_BATTLE_SCRIPT;
            Stage72U32 target = Stage72_ReadU32(script + 1);
            STAGE72_G_BATTLE_SCRIPT = (volatile Stage72U8 *)(Stage72U32)target;
        }
        return;
    }
    Stage72_OriginalRecoverBasedOnSunlight();
}

Stage72U32 Stage72_RuntimeProbe(void)
{
    return ((Stage72U32)STAGE72_ABILITY_DRAGONIZE << 16)
        | STAGE72_ABILITY_SPICY_SPRAY;
}
