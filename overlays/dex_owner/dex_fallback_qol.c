/* 選択済み片bank fallbackのidle QOLだけを非破壊復元する。
 * 戻り値255を1へ変換せず、既存の自動復旧Saveを新しく起動しない。 */
#include "dex_save_bridge.h"
#include "../save_migration/save_migration.h"
#ifndef DEX_FALLBACK_HOST
#include DEX_FALLBACK_ENTRIES
#define FALLBACK_STATUS (*(volatile uint16_t *)(uintptr_t)0x030053F0u)
#define FALLBACK_LIVE ((uint8_t *)(uintptr_t)VEGA_DEX_OWNER_RAM)
#define FALLBACK_LEDGER ((VegaModernSaveData *)(uintptr_t)VEGA_SAVE_EWRAM_ADDRESS)
#define FALLBACK_BUFFER ((uint8_t *)(uintptr_t)0x020399B0u)
#define FALLBACK_LOAD ((uint8_t (*)(uint8_t))(uintptr_t)FALLBACK_PREVIOUS_LOAD)
#define FALLBACK_VALIDATE ((VegaSaveStatus (*)(const VegaModernSaveData *,size_t))(uintptr_t)FALLBACK_SHIFTED_SAVE_VALIDATE)
#define FALLBACK_DEX_VALIDATE ((VegaDexStatus (*)(const uint8_t *,size_t))(uintptr_t)DEX_ENTRY_VegaDexValidate)
#define FALLBACK_INVALIDATE ((VegaDexStatus (*)(uint8_t *,size_t))(uintptr_t)DEX_ENTRY_VegaDexInvalidateSession)
#define FALLBACK_READ ((void (*)(uint16_t,uint32_t,void *,uint32_t))(uintptr_t)0x081C2A55u)
#endif

/* journalを実行する修復callerは成功1専用。未完transactionをfieldへ持ち出さない。 */
static uint8_t fallback_idle(const VegaModernSaveData *q)
{
    /* 全てledger先頭基準。0x800以降は同じsector31の別owner pendingのみ。 */
    static const uint16_t empty[][2] = {
        {0x01B,1},{0x120,20},{0x163,32},{0x400,4},{0x664,8},
        {0x694,46},{0x76B,16},{0x814,2},{0x828,8},{0x914,2},
        {0x952,1},{0xB18,8},{0xB24,1}
    };
    const uint8_t *p=(const uint8_t *)q;
    unsigned i,j;
    if (q->factory.reward_claim_bits & (1u<<18)) return 0;
    if (p[0x404]==0x46 && p[0x405]==0x48 && p[0x406]==0x53 && p[0x407]==0x54)
        return 0; /* Factory shiny FHST journal。 */
    for(i=0;i<sizeof(empty)/sizeof(empty[0]);i++)
        for(j=0;j<empty[i][1];j++)
            if(p[empty[i][0]+j]) return 0;
    return 1;
}
uint8_t VegaDexFallbackQolLoad(uint8_t type)
{
    uint8_t result = FALLBACK_LOAD(type);
    const VegaModernSaveData *q;
    unsigned i;
    if (type == 3u || result != 255u || FALLBACK_STATUS != 255u)
        return result;
    if (FALLBACK_DEX_VALIDATE(FALLBACK_LIVE,VEGA_DEX_OWNER_SIZE) != VEGA_DEX_OK)
        goto invalid;
    FALLBACK_READ(31u,0x64u,FALLBACK_BUFFER,0xF9Cu);
    q=(const VegaModernSaveData *)(const void *)FALLBACK_BUFFER;
    if (q->version != VEGA_SAVE_VERSION
        || FALLBACK_VALIDATE(q,VEGA_SAVE_LEDGER_SIZE) != VEGA_SAVE_OK
        || !fallback_idle(q))
        goto invalid;
    /* validな前session RAMを優先せず、検証したdurable全2048byteをpublish。 */
    for(i=0;i<VEGA_SAVE_LEDGER_SIZE;i++)
        ((uint8_t *)FALLBACK_LEDGER)[i]=((const uint8_t *)q)[i];
    return result;
invalid:
    (void)FALLBACK_INVALIDATE(FALLBACK_LIVE,VEGA_DEX_OWNER_SIZE);
    FALLBACK_STATUS=2u;
    return result;
}
