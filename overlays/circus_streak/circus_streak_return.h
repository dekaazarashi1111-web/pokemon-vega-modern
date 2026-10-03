#ifndef VEGA_CIRCUS_STREAK_RETURN_H
#define VEGA_CIRCUS_STREAK_RETURN_H
#include "circus_streak_loss.h"
/* 通常のフェード処理を再開するだけ。連勝・勝敗・party・scriptを変更しない。 */
static inline int CircusStreakReturnFadeAllowed(uint8_t armed, uint8_t circus,
    uint8_t marker, uint8_t snapshot, uint8_t count, uint8_t outcome,
    uint32_t script, uint32_t callback, uint8_t ready,
    uint8_t weather_waiter, uint8_t script_waiter)
{
    return CircusStreakLossAllowed(armed, circus, marker, snapshot, count, outcome, script)
        && callback == 0x08055E75u && ready == 0u
        && weather_waiter == 1u && script_waiter == 1u;
}
#endif
