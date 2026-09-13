#ifndef VEGA_MODERNIZATION_P05_ABILITY_ROM_RUNTIME_H
#define VEGA_MODERNIZATION_P05_ABILITY_ROM_RUNTIME_H

/*
 * Stage72 is linked without the CFRU headers on purpose.  These fixed-width
 * declarations are the audited boundary to the pinned CFRU-JP binary.  In
 * particular, an Ability is always u16; the six Stage72 IDs do not fit in u8.
 */
typedef unsigned char Stage72U8;
typedef unsigned short Stage72U16;
typedef unsigned int Stage72U32;
typedef signed int Stage72S32;

_Static_assert(sizeof(Stage72U8) == 1, "Stage72U8 width");
_Static_assert(sizeof(Stage72U16) == 2, "Stage72U16 width");
_Static_assert(sizeof(Stage72U32) == 4, "Stage72U32 width");

enum Stage72Ability {
    STAGE72_ABILITY_NONE = 0,
    STAGE72_ABILITY_CLOUD_NINE = 13,
    STAGE72_ABILITY_LEVITATE = 26,
    STAGE72_ABILITY_AIR_LOCK = 77,
    STAGE72_ABILITY_FLOWER_GIFT = 122,
    /* Canonical project ID; the pinned CFRU binary compares against 225. */
    STAGE72_ABILITY_BEAST_BOOST = 225,
    STAGE72_ABILITY_DRAGONIZE = 312,
    STAGE72_ABILITY_EELEVATE = 313,
    STAGE72_ABILITY_FIRE_MANE = 314,
    STAGE72_ABILITY_MEGA_SOL = 315,
    STAGE72_ABILITY_PIERCING_DRILL = 316,
    STAGE72_ABILITY_SPICY_SPRAY = 317
};

enum Stage72Type {
    STAGE72_TYPE_NORMAL = 0,
    STAGE72_TYPE_GROUND = 4,
    STAGE72_TYPE_FIRE = 10,
    STAGE72_TYPE_ELECTRIC = 13,
    STAGE72_TYPE_DRAGON = 16
};

enum Stage72Move {
    STAGE72_MOVE_GROWTH = 74,
    STAGE72_MOVE_SOLAR_BEAM = 76,
    STAGE72_MOVE_PROTECT = 182,
    STAGE72_MOVE_WEATHER_BALL = 311,
    STAGE72_MOVE_KINGS_SHIELD = 599,
    STAGE72_MOVE_SPIKY_SHIELD = 638,
    STAGE72_MOVE_THOUSAND_ARROWS = 643,
    STAGE72_MOVE_BANEFUL_BUNKER = 651,
    STAGE72_MOVE_CRAFTY_SHIELD = 706,
    STAGE72_MOVE_MAT_BLOCK = 707,
    STAGE72_MOVE_QUICK_GUARD = 708,
    STAGE72_MOVE_WIDE_GUARD = 709,
    STAGE72_MOVE_OBSTRUCT = 779,
    STAGE72_MOVE_TERA_BLAST = 0x3C6,
    STAGE72_MOVE_SILK_TRAP = 1033,
    STAGE72_MOVE_BURNING_BULWARK = 1052
};

enum {
    STAGE72_BATTLER_CAPACITY = 4,
    STAGE72_BATTLE_MON_STRIDE = 0x58,
    STAGE72_BATTLE_MON_HP_OFFSET = 0x28,
    STAGE72_BATTLE_MON_ABILITY_OFFSET = 0x38,
    STAGE72_BATTLE_MOVE_STRIDE = 12,
    STAGE72_BATTLE_MOVE_EFFECT_OFFSET = 0,
    STAGE72_BATTLE_MOVE_TYPE_OFFSET = 2,
    STAGE72_BATTLE_MOVE_TARGET_OFFSET = 6,
    STAGE72_BATTLE_MOVE_FLAGS_OFFSET = 8,
    STAGE72_BATTLE_MOVE_SPLIT_OFFSET = 10,
    STAGE72_DAMAGE_ATK_BANK_OFFSET = 0,
    STAGE72_DAMAGE_DEF_BANK_OFFSET = 1,
    STAGE72_DAMAGE_MON_ATK_OFFSET = 4,
    STAGE72_DAMAGE_ATK_ABILITY_OFFSET = 0x10,
    STAGE72_DAMAGE_DEF_ABILITY_OFFSET = 0x12,
    STAGE72_DAMAGE_ATK_PARTNER_ABILITY_OFFSET = 0x14,
    STAGE72_DAMAGE_MOVE_OFFSET = 0x50,
    STAGE72_DAMAGE_MOVE_TYPE_OFFSET = 0x52,
    STAGE72_DAMAGE_MOVE_SPLIT_OFFSET = 0x53,
    STAGE72_DAMAGE_RESULT_FLAGS_OFFSET = 0x54,
    STAGE72_DAMAGE_BASE_POWER_OFFSET = 0x55,
    STAGE72_DAMAGE_SPECIAL_FLAGS_OFFSET = 0x5A,
    STAGE72_PROTECT_STRUCT_STRIDE = 16,
    STAGE72_SPECIAL_STATUS_STRIDE = 20,
    STAGE72_SPECIAL_STATUS_PHYSICAL_DAMAGE_OFFSET = 8,
    STAGE72_SPECIAL_STATUS_SPECIAL_DAMAGE_OFFSET = 12,
    STAGE72_MOVE_EFFECT_OHKO = 38,
    STAGE72_MOVE_EFFECT_SOLAR_BEAM = 151,
    STAGE72_SPLIT_STATUS = 2,
    STAGE72_MOVE_FLAG_PROTECT_AFFECTED = 0x02,
    STAGE72_ITEM_EFFECT_IRON_BALL = 98,
    STAGE72_ITEM_EFFECT_UTILITY_UMBRELLA = 136,
    STAGE72_ITEM_EFFECT_ABILITY_SHIELD = 147,
    STAGE72_WEATHER_SUN_TEMPORARY = 1 << 5,
    STAGE72_WEATHER_SUN_ANY = (1 << 5) | (1 << 6) | (1 << 11),
    STAGE72_WEATHER_AIR_CURRENT_PRIMAL = 1 << 13,
    STAGE72_MOVE_TARGET_SELECTED = 0,
    STAGE72_MOVE_TARGET_RANDOM = 4,
    STAGE72_MOVE_RESULT_NO_EFFECT = 0x29,
    STAGE72_HITMARKER_IGNORE_SAFEGUARD = 0x2000,
    STAGE72_MOVE_EFFECT_BURN = 0x03,
    STAGE72_MOVE_EFFECT_AFFECTS_USER = 0x40,
    STAGE72_ABILITY_EFFECT_CONTACT = 4,
    STAGE72_BATTLE_TYPE_SAFARI = 0x80,
    STAGE72_BATTLE_TYPE_OLD_MAN = 0x200
};

/* Entry veneers that preserve an incoming r3 tail-branch to these functions. */
Stage72U8 Stage72_AbilityBattleEffects(
    Stage72U8 caseId,
    Stage72U8 bank,
    Stage72U16 ability,
    Stage72U16 special,
    Stage72U16 moveArg
);
Stage72U8 Stage72_DoesProtectionMoveBlockMove(
    Stage72U8 bankAtk,
    Stage72U8 bankDef,
    Stage72U16 attackMove,
    Stage72U16 protectMove
);
Stage72U8 Stage72_ProtectAffects(
    Stage72U16 move,
    Stage72U8 bankAtk,
    Stage72U8 bankDef,
    Stage72U8 set
);
Stage72U8 Stage72_NonInvasiveCheckGrounding(
    Stage72U8 bank,
    Stage72U16 ability,
    Stage72U8 type1,
    Stage72U8 type2,
    Stage72U8 type3
);
Stage72U8 Stage72_TypeCalc(
    Stage72U16 move,
    Stage72U8 bankAtk,
    Stage72U8 bankDef,
    void *monAtk,
    Stage72U8 checkParty
);
Stage72U8 Stage72_AITypeCalcPart(
    Stage72U16 move,
    Stage72U8 bankAtk,
    Stage72U8 bankDef,
    void *monDef
);
Stage72U16 Stage72_CalcVisualBasePower(
    Stage72U8 bankAtk,
    Stage72U8 bankDef,
    Stage72U16 move,
    Stage72U8 ignoreDef
);

Stage72U8 Stage72_GetMoveTypeSpecialPostAbility(
    Stage72U16 move,
    Stage72U16 ability,
    Stage72U8 zMoveActive
);
Stage72U8 Stage72_GetMoveTypeSpecialPreAbility(
    Stage72U16 move,
    Stage72U8 bankAtk,
    void *monAtk
);
Stage72U16 Stage72_AdjustBasePower(void *damageCalc, Stage72U16 power);
Stage72S32 Stage72_CalculateBaseDamage(void *damageCalc);
Stage72U8 Stage72_GetExceptionMoveType(Stage72U8 bankAtk, Stage72U16 move);
Stage72U8 Stage72_GetMonExceptionMoveType(void *mon, Stage72U16 move);
Stage72U8 Stage72_AttacksThisTurn(Stage72U8 bank, Stage72U16 move);
Stage72U8 Stage72_CheckGrounding(Stage72U8 bank);
Stage72U8 Stage72_CheckMonGrounding(void *mon);
Stage72U8 Stage72_CheckGroundingByDetails(
    Stage72U16 species,
    Stage72U16 item,
    Stage72U16 ability
);
Stage72U8 Stage72_AISpecialTypeCalc(
    Stage72U16 move,
    Stage72U8 bankAtk,
    Stage72U8 bankDef
);
Stage72U8 Stage72_VisualTypeCalcPart(
    Stage72U16 move,
    Stage72U8 bankAtk,
    Stage72U8 bankDef
);
void Stage72_Atk06TypeCalc(void);
void Stage72_Atk4ATypeCalc2(void);
void Stage72_Atk49MoveEnd(void);
Stage72U8 Stage72_SetMoveEffect2(void);
void Stage72_RecoverBasedOnSunlight(void);
void Stage72_Atk01AccuracyCheck(void);
Stage72U32 Stage72_AccuracyCalc(
    Stage72U16 move,
    Stage72U8 bankAtk,
    Stage72U8 bankDef
);
Stage72U32 Stage72_VisualAccuracyCalc(
    Stage72U16 move,
    Stage72U8 bankAtk,
    Stage72U8 bankDef
);
Stage72U32 Stage72_VisualAccuracyCalcNoTarget(
    Stage72U16 move,
    Stage72U8 bankAtk
);
void Stage72_ModifyGrowthInSun(void);

Stage72U32 Stage72_RuntimeProbe(void);

#endif
