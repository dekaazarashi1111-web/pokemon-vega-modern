#ifndef VEGA_MODERNIZATION_P05_STAGE78_EELEVATE_SWITCH_AI_H
#define VEGA_MODERNIZATION_P05_STAGE78_EELEVATE_SWITCH_AI_H

typedef unsigned char Stage78U8;
typedef unsigned short Stage78U16;
typedef unsigned int Stage78U32;

_Static_assert(sizeof(Stage78U8) == 1, "Stage78U8 width");
_Static_assert(sizeof(Stage78U16) == 2, "Stage78U16 width");
_Static_assert(sizeof(Stage78U32) == 4, "Stage78U32 width");

/* Stable production ABI used by the cumulative mGBA runner. */
typedef struct Stage78EelevateQuery {
    Stage78U16 originalAbility;       /* +0 */
    Stage78U16 move;                  /* +2 */
    Stage78U8 moveType;               /* +4 */
    Stage78U8 moveSplit;              /* +5 */
    Stage78U8 grounded;               /* +6 */
    Stage78U8 targetAbilityIgnored;   /* +7 */
    Stage78U8 abilityShield;          /* +8 */
    Stage78U8 circusSuppressed;       /* +9 */
    Stage78U8 abilitySuppressed;      /* +10 */
    Stage78U8 neutralizingGasPresent; /* +11 */
} Stage78EelevateQuery;

_Static_assert(sizeof(Stage78EelevateQuery) == 12, "Stage78 query ABI");

Stage78U16 Stage78_MapEelevateAbsorber(
    const Stage78EelevateQuery *query
);

#ifndef STAGE78_HOST_TEST
Stage78U16 Stage78_ActiveAbsorberAbility(
    Stage78U16 originalAbility,
    Stage78U8 active,
    Stage78U8 originalFoe1
);
Stage78U16 Stage78_PartyAbsorberAbility(
    Stage78U16 originalAbility,
    void *mon
);
Stage78U8 Stage78_RuntimeProbe(void);
#endif

#endif
