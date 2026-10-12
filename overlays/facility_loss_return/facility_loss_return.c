/* USER-20260913-BP-LOSS-RETURN: resume only the three bound Trial battle scripts.
 * No battle result/HP/party/ledger writes: the existing native AfterBattle owns
 * restoration. All other contexts still invoke the original WhiteOut callback.
 */
#include <stddef.h>
#include <stdint.h>
#include "../save_migration/save_migration.h"

uint8_t VegaFacilityLossReturnAllowed(uint8_t valid, uint8_t marker,
    uint8_t snapshot, uint8_t original_count, uint8_t outcome, uint32_t script)
{
    return (uint8_t)(valid == 1u && marker == VEGA_FACTORY_BATTLE_ACTIVE
        && snapshot == 1u && original_count >= 1u && original_count <= 6u
        && (outcome & 0x7Fu) == 2u
        && (script == 0x092CF669u || script == 0x092CF6A5u
            || script == 0x092CF6E1u));
}

#ifndef FACILITY_LOSS_RETURN_HOST_TEST
_Static_assert(offsetof(VegaModernSaveData, factory.marker) == 0x400u, "marker ABI");
_Static_assert(offsetof(VegaModernSaveData, factory.snapshot_valid) == 0x401u, "snapshot ABI");
_Static_assert(offsetof(VegaModernSaveData, factory.party_count) == 0x402u, "count ABI");

/* Bound to bffd's FacilityRuntime_AfterBattle BL at 092CE7BE and its source
 * ledger_valid(): VegaSaveValidate(ledger, 0x800) == VEGA_SAVE_OK.
 * The builder checks the exact parent, caller bytes, and unmodified allocation.
 */
#define LEDGER_VALID ((uint8_t (*)(void))(uintptr_t)0x092CEC29u)
#define WHITEOUT ((void (*)(void))(uintptr_t)0x08055F65u)
#define CONTINUE_SCRIPT ((void (*)(void))(uintptr_t)0x080561A1u)

__attribute__((section(".text.entry"), used))
void VegaFacilityLossReturn(void)
{
    const volatile VegaFactoryState *state = &gVegaModernSaveData->factory;
    uint32_t script = *(volatile uint32_t *)(uintptr_t)0x03000EB8u;
    uint8_t outcome = *(volatile uint8_t *)(uintptr_t)0x02023DEAu;
    if (VegaFacilityLossReturnAllowed(1u, state->marker, state->snapshot_valid,
            state->party_count, outcome, script) && LEDGER_VALID() == 1u) {
        CONTINUE_SCRIPT();
    } else {
        WHITEOUT();
    }
}
#endif
