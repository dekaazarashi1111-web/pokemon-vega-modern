#include <assert.h>
#include <stdint.h>
#include "../overlays/cfru/integration.h"
unsigned ring_policy_pending, ring_policy_flags, ring_policy_owned, ring_policy_ok, ring_policy_select_ok;
unsigned ring_policy_original_calls, ring_policy_select_calls, ring_policy_end_calls, ring_policy_bag_calls;
unsigned ring_policy_sequence;
uint8_t VegaRingPolicyHostPending(void) { assert(ring_policy_sequence==0u);ring_policy_sequence=1u;return (uint8_t)ring_policy_pending; }
uint32_t VegaRingPolicyHostFlags(void) { assert(ring_policy_sequence==1u);ring_policy_sequence=2u;return ring_policy_flags; }
uint8_t VegaRingPolicyHostHasRing(void) { assert(ring_policy_sequence==2u);++ring_policy_bag_calls;return (uint8_t)ring_policy_owned; }
uint8_t VegaRingPolicyHostOriginal(void) {
 assert(ring_policy_sequence==2u);ring_policy_sequence=3u;
 ++ring_policy_original_calls;ring_policy_pending=0u;return (uint8_t)ring_policy_ok;
}
uint8_t VegaRingPolicyHostSelect(unsigned mode,unsigned side) {
 assert(ring_policy_sequence==3u && mode==CFRU_MECHANIC_MEGA && side==CFRU_SIDE_OPPONENT);
 ring_policy_sequence=4u;++ring_policy_select_calls;return (uint8_t)ring_policy_select_ok;
}
uint8_t VegaRingPolicyHostEnd(unsigned reason) {
 assert(ring_policy_sequence==4u && reason==CFRU_EXIT_ERROR);++ring_policy_end_calls;return 1u;
}
void ring_policy_reset(unsigned flags,unsigned pending,unsigned owned,unsigned original,unsigned selection) {
 ring_policy_flags=flags;ring_policy_pending=pending;ring_policy_owned=owned;
 ring_policy_ok=original;ring_policy_select_ok=selection;
 ring_policy_original_calls=ring_policy_select_calls=ring_policy_end_calls=ring_policy_bag_calls=ring_policy_sequence=0u;
}
