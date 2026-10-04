/* 通常loadの失敗を最初の復旧Saveより前に伝える。保存・再選択はしない。 */
#include "dex_owner.h"
#ifndef DEX_LIFECYCLE_HOST
#include DEX_LIFECYCLE_ENTRIES
#define DEX_LIFECYCLE_SAVE_STATUS (*(volatile uint16_t *)(uintptr_t)0x030053F0u)
#define DEX_LIFECYCLE_LIVE ((uint8_t *)(uintptr_t)VEGA_DEX_OWNER_RAM)
#define DEX_LIFECYCLE_QOL ((uint8_t (*)(uint8_t))(uintptr_t)0x09377695u)
#define DEX_LIFECYCLE_INVALIDATE ((VegaDexStatus (*)(uint8_t *,size_t))(uintptr_t)DEX_ENTRY_VegaDexInvalidateSession)
#define DEX_LIFECYCLE_VALIDATE ((VegaDexStatus (*)(const uint8_t *,size_t))(uintptr_t)DEX_ENTRY_VegaDexValidate)
#endif
uint8_t VegaDexPostQolLoad(uint8_t save_type)
{
    uint8_t status;
    /* 殿堂だけのloadはmain-bank sessionに触らない。 */
    if (save_type == 3u)
        return DEX_LIFECYCLE_QOL(save_type);
    /* 前sessionのvalid RAMが内側load失敗を隠さないよう先に失効する。 */
    (void)DEX_LIFECYCLE_INVALIDATE(DEX_LIFECYCLE_LIVE,VEGA_DEX_OWNER_SIZE);
    status = DEX_LIFECYCLE_QOL(save_type);
    if ((status == 1u || status == 255u) && DEX_LIFECYCLE_VALIDATE(
            DEX_LIFECYCLE_LIVE,VEGA_DEX_OWNER_SIZE) == VEGA_DEX_OK)
        return status;
    (void)DEX_LIFECYCLE_INVALIDATE(DEX_LIFECYCLE_LIVE,VEGA_DEX_OWNER_SIZE);
    /* 255は片bankからの正常fallbackも兼ねる。無効MDXだけContinueを遮断。
     * stock globalの255はContinueを残すため、失敗時はINVALID=2へ。
     * 既存エラー画面に委譲し、Flash消去や復旧Saveは一切しない。 */
    if (status == 1u || status == 255u)
        DEX_LIFECYCLE_SAVE_STATUS = 2u;
    return status == 1u ? 255u : status;
}
