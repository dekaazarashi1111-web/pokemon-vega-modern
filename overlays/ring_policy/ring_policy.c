/* Re-evaluate Ring ownership at each ordinary battle, including cold Continue.
 * Granting the Ring never writes a NEXT command. An explicit pending command,
 * including Standard, takes precedence. Facility/raid/link/special battles do
 * not get a Ring fallback. Existing controller, stone, per-side usage and
 * mutually-exclusive mechanic gates are not replaced.
 */
#include "ring_policy.h"
#include "../cfru/integration.h"
#include <stddef.h>
#include <stdint.h>

_Static_assert(offsetof(CfruIntegrationState, pending) == 0, "pending must be first");
_Static_assert(offsetof(CfruPendingBattleCommand, active) == 0, "active ABI differs");
_Static_assert(offsetof(CfruIntegrationState, battle_active) == 48, "policy ABI differs");

#ifdef VEGA_RING_POLICY_HOST
extern uint8_t VegaRingPolicyHostPending(void);
extern uint32_t VegaRingPolicyHostFlags(void);
extern uint8_t VegaRingPolicyHostHasRing(void);
extern uint8_t VegaRingPolicyHostOriginal(void);
extern uint8_t VegaRingPolicyHostSelect(unsigned mode, unsigned side);
extern uint8_t VegaRingPolicyHostEnd(unsigned reason);
#define PENDING() VegaRingPolicyHostPending()
#define FLAGS() VegaRingPolicyHostFlags()
#define OWNED() VegaRingPolicyHostHasRing()
#define ORIGINAL() VegaRingPolicyHostOriginal()
#define SELECT(mode, side) VegaRingPolicyHostSelect(mode, side)
#define END(reason) VegaRingPolicyHostEnd(reason)
#else
#ifndef VEGA_RING_ORIGINAL_BEGIN
#error "candidate-bound original begin address is required"
#endif
#ifndef VEGA_RING_SELECT_MECHANIC
#error "candidate-bound select mechanic address is required"
#endif
#ifndef VEGA_RING_END_BATTLE
#error "candidate-bound battle end address is required"
#endif
#ifndef VEGA_RING_STATE_GETTER
#error "candidate-bound integration state getter is required"
#endif
/* All function addresses are decoded/validated by the bounded builder. */
#define PENDING() (((const CfruIntegrationState *(*)(void))(uintptr_t)VEGA_RING_STATE_GETTER)()->pending.active)
#define FLAGS() (*(volatile uint32_t *)(uintptr_t)0x02022AACu)
#define OWNED() (((uint8_t (*)(uint16_t, uint16_t))(uintptr_t)0x08099949u)(580u, 1u))
#define ORIGINAL() (((uint8_t (*)(void))(uintptr_t)VEGA_RING_ORIGINAL_BEGIN)())
#define SELECT(mode, side) (((uint8_t (*)(unsigned, unsigned))(uintptr_t)VEGA_RING_SELECT_MECHANIC)(mode, side))
#define END(reason) (((uint8_t (*)(unsigned))(uintptr_t)VEGA_RING_END_BATTLE)(reason))
#endif

uint8_t VegaRingPolicyEligible(uint32_t flags, uint8_t pending, uint8_t owned)
{
    return (uint8_t)(!pending && owned && !(flags & ~VEGA_RING_ORDINARY_FLAGS));
}

__attribute__((used, noinline, section(".text.VegaRingPolicyBegin")))
uint8_t VegaRingPolicyBegin(void)
{
    /* Original begin consumes pending. Capture intent beforehand, never after. */
    uint8_t pending = PENDING();
    uint32_t flags = FLAGS();
    uint8_t fallback = 0;
    if (!pending && !(flags & ~VEGA_RING_ORDINARY_FLAGS))
        fallback = VegaRingPolicyEligible(flags, pending, OWNED());
    uint8_t result = ORIGINAL();
    if (!result || !fallback)
        return result;
    if (!SELECT(CFRU_MECHANIC_MEGA, CFRU_SIDE_OPPONENT)) {
        (void)END(CFRU_EXIT_ERROR);
        return CFRU_FALSE;
    }
    return result;
}
