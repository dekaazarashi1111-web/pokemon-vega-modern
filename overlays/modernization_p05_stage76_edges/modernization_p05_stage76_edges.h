#ifndef MODERNIZATION_P05_STAGE76_EDGES_H
#define MODERNIZATION_P05_STAGE76_EDGES_H

typedef unsigned char Stage76U8;
typedef unsigned short Stage76U16;
typedef unsigned int Stage76U32;

_Static_assert(sizeof(Stage76U8) == 1, "Stage76U8 width");
_Static_assert(sizeof(Stage76U16) == 2, "Stage76U16 width");
_Static_assert(sizeof(Stage76U32) == 4, "Stage76U32 width");

enum Stage76MegaSolRoute {
    STAGE76_MEGA_ROUTE_ORIGINAL = 0,
    STAGE76_MEGA_ROUTE_FIRST_TURN = 1,
    STAGE76_MEGA_ROUTE_POPUP = 2
};

enum Stage76SpicyPolicyFlag {
    STAGE76_SPICY_DOUBLE = 1 << 0,
    STAGE76_SPICY_DISTINCT_BANKS = 1 << 1,
    STAGE76_SPICY_PARTNER_ALIVE = 1 << 2,
    STAGE76_SPICY_PARTNER_STAYING = 1 << 3,
    STAGE76_SPICY_PARTNER_ABILITY = 1 << 4,
    STAGE76_SPICY_DAMAGING = 1 << 5,
    STAGE76_SPICY_SAFE_MOVE = 1 << 6,
    STAGE76_SPICY_NOT_SUB_BLOCKED = 1 << 7,
    STAGE76_SPICY_NOT_KO = 1 << 8,
    STAGE76_SPICY_CAN_BURN = 1 << 9,
    STAGE76_SPICY_BURN_BENEFIT = 1 << 10,
    STAGE76_SPICY_ITEM_OK = 1 << 11,
    STAGE76_SPICY_REACHABLE = 1 << 12,
    STAGE76_SPICY_ALL = (1 << 13) - 1
};

enum Stage76SpicyPath {
    STAGE76_SPICY_PATH_DIRECT = 0,
    STAGE76_SPICY_PATH_SPREAD = 1
};

Stage76U8 Stage76_MegaSolRoute(
    Stage76U16 ability,
    Stage76U8 alreadySecondTurn,
    Stage76U8 originalSunApplies
);
Stage76U32 Stage76_QuarterPredictedProtectDamage(
    Stage76U32 damage,
    Stage76U8 qualifies
);
Stage76U16 Stage76_NormalizePredictedProtectionMove(Stage76U16 move);
Stage76U8 Stage76_IsPlannedMaxGuard(Stage76U16 move);
Stage76U8 Stage76_DirectEffectCanDamagePartner(Stage76U8 effect);
Stage76U8 Stage76_SpicyPolicyCore(Stage76U16 flags);
Stage76U8 Stage76_SpicyPathQualifies(
    Stage76U8 path,
    Stage76U8 isSpread,
    Stage76U8 commonPolicyQualifies
);
Stage76U16 Stage76_SelectAIAttackerAbility(
    Stage76U16 activeAbility,
    Stage76U8 activeAbilitySuppressed,
    Stage76U8 hasDamageData,
    Stage76U16 damageDataAbility
);

Stage76U32 Stage76_AICalcDmg(
    Stage76U8 bankAtk,
    Stage76U8 bankDef,
    Stage76U16 move,
    void *damageData
);
Stage76U8 Stage76_AIScriptPartner(
    Stage76U8 bankAtk,
    Stage76U8 bankAtkPartner,
    Stage76U16 originalMove,
    Stage76U8 originalViability,
    void *data
);
Stage76U8 Stage76_RangeMoveCanHurtPartner(
    Stage76U16 move,
    Stage76U8 bankAtk,
    Stage76U8 bankAtkPartner
);
void Stage76_DispatchMegaSolSolarBeam(void);
Stage76U32 Stage76_RuntimeProbe(Stage76U32 query);

#endif
