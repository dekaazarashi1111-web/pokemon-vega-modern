/* USER-20260918-RING-NPC
 * A normal Bag transaction; no NEXT-policy write, save-format change or
 * independent claimed bit. Ownership is the duplicate guard and survives the
 * game's ordinary Save/Continue path. A failed give can always be retried.
 */
#include "ring_npc.h"
#include <stdint.h>

#ifdef VEGA_RING_NPC_HOST
extern uint8_t VegaRingHostFlagGet(uint16_t flag);
extern uint8_t VegaRingHostHasItem(uint16_t item, uint16_t count);
extern uint8_t VegaRingHostHasSpace(uint16_t item, uint16_t count);
extern uint8_t VegaRingHostAddItem(uint16_t item, uint16_t count);
extern volatile uint16_t VegaRingHostResult;
#define FLAG_GET VegaRingHostFlagGet
#define HAS_ITEM VegaRingHostHasItem
#define HAS_SPACE VegaRingHostHasSpace
#define ADD_ITEM VegaRingHostAddItem
#define SCRIPT_RESULT VegaRingHostResult
#else
typedef uint8_t (*FlagGetFn)(uint16_t);
typedef uint8_t (*BagFn)(uint16_t, uint16_t);
/* Fixed BPRJ01 adapter addresses already used by the existing field owners. */
#define FLAG_GET ((FlagGetFn)(uintptr_t)0x0806DEC5u)
#define HAS_ITEM ((BagFn)(uintptr_t)0x08099949u)
#define HAS_SPACE ((BagFn)(uintptr_t)0x08099A09u)
#define ADD_ITEM ((BagFn)(uintptr_t)0x08099A8Du)
#define SCRIPT_RESULT (*(volatile uint16_t *)(uintptr_t)0x02037004u)
#endif

uint32_t VegaRingNpcTryGive(void)
{
    if (!FLAG_GET(VEGA_RING_FINAL_LEAGUE_FLAG))
        return VEGA_RING_GIFT_LOCKED;
    if (HAS_ITEM(VEGA_RING_ITEM, 1u))
        return VEGA_RING_GIFT_ALREADY_OWNED;
    if (!HAS_SPACE(VEGA_RING_ITEM, 1u))
        return VEGA_RING_GIFT_NO_SPACE;
    if (!ADD_ITEM(VEGA_RING_ITEM, 1u))
        return VEGA_RING_GIFT_FAILED;
    return VEGA_RING_GIFT_OK;
}

__attribute__((used, noinline, section(".text.VegaRingNpcInteract")))
void VegaRingNpcInteract(void)
{
    SCRIPT_RESULT = (uint16_t)VegaRingNpcTryGive();
}
