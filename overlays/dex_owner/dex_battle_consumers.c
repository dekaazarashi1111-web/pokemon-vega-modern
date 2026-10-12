/* SIDを失う前のbattle seenとCFRU公式count。旧鏡へ書き戻さない。 */
#include "dex_adapter.h"
#ifdef DEX_CONSUMER_HOST
extern uint8_t dex_consumer_live[VEGA_DEX_OWNER_SIZE];
#define LIVE dex_consumer_live
#define SPECIES VegaDexSpeciesFlags
#define COUNT VegaDexOfficialCount
#else
#include DEX_CONSUMER_ENTRIES
#define LIVE ((uint8_t *)(uintptr_t)VEGA_DEX_OWNER_RAM)
typedef VegaDexStatus (*SpeciesFn)(uint8_t *,size_t,uint16_t,uint8_t,uint8_t *);
typedef VegaDexStatus (*CountFn)(const uint8_t *,size_t,uint8_t,uint16_t *);
#define SPECIES ((SpeciesFn)(uintptr_t)DEX_ENTRY_VegaDexSpeciesFlags)
#define COUNT ((CountFn)(uintptr_t)DEX_ENTRY_VegaDexOfficialCount)
#endif
uint8_t VegaDexBattleSeenC(uint16_t species)
{
    uint8_t value=0u;
    if(SPECIES(LIVE,VEGA_DEX_OWNER_SIZE,species,VEGA_DEX_SET_SEEN,&value)!=VEGA_DEX_OK)return 0u;
    return value;
}
uint16_t VegaDexBattleOfficialCountC(uint8_t mode)
{
    uint16_t count=0u;
    if(COUNT(LIVE,VEGA_DEX_OWNER_SIZE,mode,&count)!=VEGA_DEX_OK)return 0u;
    return count;
}
