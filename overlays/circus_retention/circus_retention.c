/* Circus複製scriptの実戦だけ選択個体を保持する。既存Factoryのpredicateは
 * 先に一度だけ呼び、非該当経路の返値をそのまま保存する。party/saveへの書込なし。 */
#include <stdint.h>
#ifndef CIRCUS_SCRIPT_FIRST
#error "実candidateのlaunch continuationをbuilderで固定する"
#endif
uint8_t VegaCircusKeepRental(uint8_t valid,uint8_t marker,uint8_t snapshot,
    uint8_t original_count,uint8_t live_count,uint8_t pending,uint32_t script,
    uint32_t magic,uint16_t number,uint32_t types)
{
    return (uint8_t)(valid==1u && marker==2u && snapshot==1u
        && original_count>=1u && original_count<=6u && live_count==3u
        && number==3u && (magic==0x54303650u || magic==0x54303641u)
        && (types&0x04000000u)!=0u
        && ((pending==0u && script==CIRCUS_SCRIPT_FIRST)
            || (pending==1u && script==CIRCUS_SCRIPT_SECOND)
            || (pending==2u && script==CIRCUS_SCRIPT_THIRD)));
}
#ifndef CIRCUS_RETENTION_HOST_TEST
#include <stddef.h>
#include "../save_migration/save_migration.h"
_Static_assert(offsetof(VegaModernSaveData,factory.marker)==0x400u,"marker ABI");
_Static_assert(offsetof(VegaModernSaveData,factory.snapshot_valid)==0x401u,"snapshot ABI");
_Static_assert(offsetof(VegaModernSaveData,factory.party_count)==0x402u,"original count ABI");
#ifndef CIRCUS_PREVIOUS_PREDICATE
#error "旧retention trampolineのThumb pointerをbuilderで検証する"
#endif
__attribute__((section(".text.entry"),used))
uint8_t VegaCircusRandomPlayerParty(void)
{
    uint8_t previous=((uint8_t (*)(void))(uintptr_t)CIRCUS_PREVIOUS_PREDICATE)();
    const volatile VegaFactoryState *state=&gVegaModernSaveData->factory;
    if(previous && VegaCircusKeepRental(1u,state->marker,state->snapshot_valid,
       state->party_count,*(volatile uint8_t *)(uintptr_t)0x02023F89u,state->reward_pending,
       *(volatile uint32_t *)(uintptr_t)0x03000EB8u,
       *(volatile uint32_t *)(uintptr_t)0x0203E040u,
       *(volatile uint16_t *)(uintptr_t)0x0203E052u,
       *(volatile uint32_t *)(uintptr_t)0x02022AACu)
       && ((uint8_t (*)(void))(uintptr_t)0x092CEC29u)()==1u)
        return 0u;
    return previous;
}
#endif
