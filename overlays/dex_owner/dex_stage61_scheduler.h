/* Private generated Stage61 copy includes this scheduler boundary.
 * Entry addresses are emitted from the accepted placement EXPORTS manifest. */
#include "dex_save_bridge.h"
#define DEX_LIVE ((volatile u8 *)(uintptr_t)VEGA_DEX_OWNER_RAM)
typedef VegaDexStatus (*DexValidateFn)(const uint8_t *,size_t);
typedef VegaDexStatus (*DexCheckFn)(const uint8_t *,size_t,uint32_t,uint8_t);
typedef VegaDexStatus (*DexLoadFn)(uint8_t *,size_t,const uint8_t *,size_t,
    const uint8_t *,size_t,const uint8_t *,size_t,uint32_t,uint8_t);
typedef VegaDexStatus (*DexInvalidateFn)(uint8_t *,size_t);
static u8 stage61_dex_live_valid(void)
{
    return ((DexValidateFn)(uintptr_t)DEX_ENTRY_VegaDexValidate)(
        (const uint8_t *)DEX_LIVE,VEGA_DEX_OWNER_SIZE)==VEGA_DEX_OK;
}
static u8 stage61_dex_check(const volatile u8 *section,u32 counter)
{
    return ((DexCheckFn)(uintptr_t)DEX_ENTRY_VegaDexCheckSector)(
        (const uint8_t *)section,VEGA_DEX_SECTOR_SIZE,counter,1u)==VEGA_DEX_OK;
}
static void stage61_dex_invalidate(void)
{
    (void)((DexInvalidateFn)(uintptr_t)DEX_ENTRY_VegaDexInvalidateSession)(
        (uint8_t *)DEX_LIVE,VEGA_DEX_OWNER_SIZE);
}
static u8 stage61_dex_load(const volatile u8 *section,const volatile u8 *save1,
    const volatile u8 *save2,u32 counter)
{
    return ((DexLoadFn)(uintptr_t)DEX_ENTRY_VegaDexLoadSelected)(
        (uint8_t *)DEX_LIVE,VEGA_DEX_OWNER_SIZE,(const uint8_t *)section,
        VEGA_DEX_SECTOR_SIZE,(const uint8_t *)save1,VEGA_DEX_SAVE1_SIZE,
        (const uint8_t *)save2,VEGA_DEX_SAVE2_SIZE,counter,1u)==VEGA_DEX_OK;
}
/* Shared body programmer keeps signature-last semantics and reduces duplicate
 * loops without borrowing any adjacent owner. Callers retain erase, commit,
 * damaged-sector selection and exact readback responsibilities. */
static __attribute__((noinline)) u8 stage61_dex_program_body(
    ProgramFlashByteFn program_byte,u16 sector,const volatile u8 *section)
{
    u32 index;
    for(index=0u;index<STAGE61_SAVE_SECTION_SIZE;++index) {
        if(index==STAGE61_SAVE_SIGNATURE_OFFSET)continue;
        if(program_byte(sector,index,section[index])!=0u)return 0u;
    }
    return 1u;
}

static __attribute__((noinline)) u8 stage61_dex_fail_live(void);
