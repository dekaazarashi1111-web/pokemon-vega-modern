#ifndef VEGA_CIRCUS_STREAK_LOSS_H
#define VEGA_CIRCUS_STREAK_LOSS_H
#include <stdint.h>
/* 既受入の複製script位置。判定のみ、勝敗/party/ledgerへ書き込まない。 */
static inline uint8_t CircusStreakLossAllowed(uint8_t armed, uint8_t ledger_valid,
    uint8_t marker, uint8_t snapshot, uint8_t count, uint8_t outcome, uint32_t script)
{
    return (uint8_t)(armed == 1u && ledger_valid == 1u && marker == 1u
        && snapshot == 1u && count >= 1u && count <= 6u
        && (outcome & 0x7Fu) == 2u
        && (script == 0x09FF4D16u || script == 0x09FF4D77u || script == 0x09FF4DD8u));
}
#endif
