/* 交換後のTrial継続だけ、battle初期化によるplayer再抽選を抑止する。
 * 通常戦・初戦・無効ledger・別scriptは既存predicateをそのまま返す。
 * party/HP/戦闘結果/ledgerへの書込みは行わない。 */
#include <stdint.h>

uint8_t VegaFacilityKeepExchangedParty(uint8_t valid, uint8_t marker,
    uint8_t snapshot, uint8_t original_count, uint8_t live_count,
    uint8_t pending, uint32_t script)
{
    return (uint8_t)(valid == 1u && marker == 2u && snapshot == 1u
        && original_count >= 1u && original_count <= 6u && live_count == 3u
        && ((pending == 1u && script == 0x092CF6A5u)
            || (pending == 2u && script == 0x092CF6E1u)));
}

#ifndef FACILITY_PARTY_RETENTION_HOST_TEST
#include <stddef.h>
#include "../save_migration/save_migration.h"
_Static_assert(VEGA_FACTORY_BATTLE_ACTIVE == 2u, "marker ABI");
_Static_assert(offsetof(VegaModernSaveData, factory.marker) == 0x400u, "marker ABI");
_Static_assert(offsetof(VegaModernSaveData, factory.snapshot_valid) == 0x401u, "snapshot ABI");
_Static_assert(offsetof(VegaModernSaveData, factory.party_count) == 0x402u, "count ABI");
#ifndef VEGA_ORIGINAL_RANDOM_PREDICATE
#error "固定candidateのcallsite/ABI照合で決定する"
#endif
#define RANDOM_PREDICATE ((uint8_t (*)(void))(uintptr_t)VEGA_ORIGINAL_RANDOM_PREDICATE)
#define LEDGER_VALID ((uint8_t (*)(void))(uintptr_t)0x092CEC29u)
__attribute__((section(".text.entry"), used))
uint8_t VegaFacilityRandomPlayerParty(void)
{
    uint8_t original = RANDOM_PREDICATE();
    const volatile VegaFactoryState *state = &gVegaModernSaveData->factory;
    uint32_t script = *(volatile uint32_t *)(uintptr_t)0x03000EB8u;
    uint8_t live_count = *(volatile uint8_t *)(uintptr_t)0x02023F89u;
    if (original && VegaFacilityKeepExchangedParty(1u, state->marker,
            state->snapshot_valid, state->party_count, live_count,
            state->reward_pending, script) && LEDGER_VALID() == 1u)
        return 0u;
    return original;
}
#endif
