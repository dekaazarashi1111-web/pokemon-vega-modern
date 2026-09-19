#ifndef VEGA_RING_POLICY_H
#define VEGA_RING_POLICY_H
#include <stdint.h>
/* Only ordinary wild/trainer layouts; all other/unknown flags fail closed.
 * Pinned policy smoke owns these DOUBLE/TRAINER/TWO_OPPONENTS/PARTNER bits.
 */
#define VEGA_RING_ORDINARY_FLAGS 0x00600009u
uint8_t VegaRingPolicyEligible(uint32_t flags, uint8_t pending, uint8_t owned);
uint8_t VegaRingPolicyBegin(void);
#endif
