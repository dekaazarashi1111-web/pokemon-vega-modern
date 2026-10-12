/* Host-only adapter for the production gift function; never linked into ROM. */
#include <assert.h>
#include <stdint.h>
#include "../overlays/ring_npc/ring_npc.h"

unsigned ring_test_unlocked, ring_test_owned, ring_test_space, ring_test_add_ok;
unsigned ring_test_add_calls, ring_test_flag_calls, ring_test_has_calls, ring_test_space_calls;
volatile uint16_t VegaRingHostResult;
uint8_t VegaRingHostFlagGet(uint16_t flag)
{
    assert(flag == VEGA_RING_FINAL_LEAGUE_FLAG);
    ++ring_test_flag_calls;
    return (uint8_t)ring_test_unlocked;
}
uint8_t VegaRingHostHasItem(uint16_t item, uint16_t count)
{
    assert(item == 580u && count == 1u);
    ++ring_test_has_calls;
    return (uint8_t)(ring_test_owned != 0u);
}
uint8_t VegaRingHostHasSpace(uint16_t item, uint16_t count)
{
    assert(item == 580u && count == 1u);
    ++ring_test_space_calls;
    return (uint8_t)ring_test_space;
}
uint8_t VegaRingHostAddItem(uint16_t item, uint16_t count)
{
    assert(item == 580u && count == 1u);
    ++ring_test_add_calls;
    if (ring_test_add_ok) ++ring_test_owned;
    return (uint8_t)ring_test_add_ok;
}
void ring_test_reset(unsigned gate, unsigned quantity, unsigned capacity, unsigned ok)
{
    ring_test_unlocked=gate; ring_test_owned=quantity;
    ring_test_space=capacity; ring_test_add_ok=ok;
    ring_test_add_calls=ring_test_flag_calls=ring_test_has_calls=ring_test_space_calls=0u;
    VegaRingHostResult=0xFFFFu;
}
