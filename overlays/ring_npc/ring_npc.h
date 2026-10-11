#ifndef VEGA_RING_NPC_H
#define VEGA_RING_NPC_H

#include <stdint.h>

/* The existing event-design state manifest owns this flag. Never set it here. */
#define VEGA_RING_FINAL_LEAGUE_FLAG 0x13FFu
#define VEGA_RING_ITEM 580u

enum VegaRingGiftResult {
    VEGA_RING_GIFT_OK = 1,
    VEGA_RING_GIFT_ALREADY_OWNED = 2,
    VEGA_RING_GIFT_LOCKED = 3,
    VEGA_RING_GIFT_NO_SPACE = 4,
    VEGA_RING_GIFT_FAILED = 5
};

uint32_t VegaRingNpcTryGive(void);
void VegaRingNpcInteract(void);

#endif
