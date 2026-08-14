/*
 * USER-20260815-BATTLE-UI-LOOP-AUDIT
 *
 * RunTurnActionsFunctionsへ入る直前に、Quick Draw通知indicatorと実際の
 * battler特性を照合する小さなThumb wrapper。Delta/VBA-M stateで観測した
 * 「アクタシの特性64にQuick Draw indicatorが残る」状態をfail closedにする。
 */

#include "first_battle_hotfix.h"

#include <stdint.h>

typedef uint8_t u8;
typedef uint16_t u16;
typedef uint32_t u32;

enum {
    MAX_BATTLERS = 4,
    BATTLE_MON_SIZE = 0x58,
    BATTLE_MON_ABILITY_OFFSET = 0x38,
    NEWBS_QUICK_DRAW_INDICATOR_OFFSET = 0x123,
    ABILITY_QUICK_DRAW = 260,
    EWRAM_START = 0x02000000,
    EWRAM_END_EXCLUSIVE = 0x02040000,
};

#define PTR(type, address) ((type)(uintptr_t)(address))
#define G_BATTLERS_COUNT PTR(volatile u8 *, 0x02023B2C)
#define G_BATTLE_MONS PTR(volatile u8 *, 0x02023B44)
#define G_NEW_BATTLE_STRUCT PTR(volatile u32 *, 0x0203DFB0)

#ifndef VEGA_FIRST_BATTLE_ORIGINAL_CONTINUE
#error "RunTurnActionsFunctions continuation must come from the T06 symbol contract"
#endif

#define VEGA_STRINGIFY_INNER(value) #value
#define VEGA_STRINGIFY(value) VEGA_STRINGIFY_INNER(value)

__attribute__((section(".text.VegaFirstBattle_ClearInvalidQuickDrawIndicators"),
               used, noinline))
void VegaFirstBattle_ClearInvalidQuickDrawIndicators(void)
{
    u32 state = *G_NEW_BATTLE_STRUCT;
    if (state < EWRAM_START
        || state > EWRAM_END_EXCLUSIVE
            - (NEWBS_QUICK_DRAW_INDICATOR_OFFSET + 1u))
        return;

    volatile u8 *indicator = PTR(
        volatile u8 *, state + NEWBS_QUICK_DRAW_INDICATOR_OFFSET);
    u8 value = *indicator;
    u8 count = *G_BATTLERS_COUNT;
    if (count > MAX_BATTLERS)
        count = MAX_BATTLERS;

    for (u8 bank = 0; bank < count; ++bank) {
        u8 bit = (u8)(1u << bank);
        volatile u16 *ability = PTR(
            volatile u16 *,
            (uintptr_t)G_BATTLE_MONS
                + (u32)bank * BATTLE_MON_SIZE
                + BATTLE_MON_ABILITY_OFFSET);
        if ((value & bit) && *ability != ABILITY_QUICK_DRAW)
            value &= (u8)~bit;
    }
    *indicator = value;
}

/*
 * Stage 21は先頭8 byteをabsolute jumpへ置換する。wrapper側でその4命令を
 * 再実行し、元関数+8へtail jumpするため、元関数のstack frameとreturn先は
 * 一切変わらない。
 */
__attribute__((section(".text.VegaFirstBattle_RunTurnActionsFunctions"),
               used, naked))
void VegaFirstBattle_RunTurnActionsFunctions(void)
{
    __asm__ volatile(
        "push {r4, lr}\n"
        "bl VegaFirstBattle_ClearInvalidQuickDrawIndicators\n"
        "pop {r4}\n"
        "pop {r0}\n"
        "mov lr, r0\n"
        "push {r4-r7, lr}\n"
        "mov r7, r10\n"
        "mov lr, r11\n"
        "mov r6, r9\n"
        "ldr r0, =" VEGA_STRINGIFY(VEGA_FIRST_BATTLE_ORIGINAL_CONTINUE) "\n"
        "bx r0\n"
    );
}
