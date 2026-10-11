#include "dex_save_bridge.h"
static uint8_t overlap(const void *a,size_t an,const void *b,size_t bn)
{
    uintptr_t x=(uintptr_t)a,y=(uintptr_t)b;
    if(a==NULL||b==NULL||an==0u||bn==0u)return 0u;
    return (uint8_t)(x<=y?y-x<an:x-y<bn);
}
static uint16_t r16(const uint8_t *p)
{return (uint16_t)((uint16_t)p[0]|((uint16_t)p[1]<<8));}
static uint32_t r32(const uint8_t *p)
{return (uint32_t)p[0]|((uint32_t)p[1]<<8)|((uint32_t)p[2]<<16)|((uint32_t)p[3]<<24);}
VegaDexRecordKind VegaDexClassifyRecord(const uint8_t *record,size_t size)
{
    size_t i;uint8_t zero=1u,erased=1u;
    if(record==NULL||size!=VEGA_DEX_OWNER_SIZE)return VEGA_DEX_RECORD_REJECT;
    for(i=0u;i<size;++i){if(record[i]!=0u)zero=0u;if(record[i]!=0xFFu)erased=0u;}
    if(zero)return VEGA_DEX_RECORD_LEGACY_ZERO;
    if(erased)return VEGA_DEX_RECORD_LEGACY_ERASED;
    return VegaDexValidate(record,size)==VEGA_DEX_OK?VEGA_DEX_RECORD_VALID:VEGA_DEX_RECORD_REJECT;
}
static VegaDexStatus sector_parent(const uint8_t *sector,size_t size,uint32_t counter,uint8_t verified)
{
    if(sector==NULL)return VEGA_DEX_INVALID_ARGUMENT;
    if(size!=VEGA_DEX_SECTOR_SIZE)return VEGA_DEX_BAD_SIZE;
    if(verified!=1u||r16(sector+0xFF4u)!=13u||r32(sector+0xFF8u)!=0x08012025u
       ||r32(sector+0xFFCu)!=counter)return VEGA_DEX_PARENT_NOT_VERIFIED;
    return VEGA_DEX_OK;
}
VegaDexStatus VegaDexCheckSector(const uint8_t *sector,size_t size,uint32_t counter,uint8_t verified)
{
    VegaDexStatus status=sector_parent(sector,size,counter,verified);
    VegaDexRecordKind kind;
    if(status!=VEGA_DEX_OK)return status;
    kind=VegaDexClassifyRecord(sector+VEGA_DEX_CHUNK13_OFFSET,VEGA_DEX_OWNER_SIZE);
    if(kind==VEGA_DEX_RECORD_REJECT)
        return VegaDexValidate(sector+VEGA_DEX_CHUNK13_OFFSET,VEGA_DEX_OWNER_SIZE);
    return VEGA_DEX_OK;
}
VegaDexStatus VegaDexInjectSector(uint8_t *sector,size_t size,const uint8_t *live,
    size_t live_size,uint32_t counter,uint8_t verified)
{
    size_t i;VegaDexStatus status=sector_parent(sector,size,counter,verified);
    if(status!=VEGA_DEX_OK)return status;
    if(overlap(sector,size,live,live_size))return VEGA_DEX_INVALID_ARGUMENT;
    status=VegaDexValidate(live,live_size);if(status!=VEGA_DEX_OK)return status;
    for(i=0u;i<VEGA_DEX_OWNER_SIZE;++i)sector[VEGA_DEX_CHUNK13_OFFSET+i]=live[i];
    return VEGA_DEX_OK;
}
VegaDexStatus VegaDexTailMatches(const uint8_t *sector,size_t size,const uint8_t *live,
    size_t live_size,uint32_t counter,uint8_t verified,uint8_t *matches)
{
    size_t i;VegaDexStatus status;
    if(matches==NULL||overlap(matches,1u,sector,size)||overlap(matches,1u,live,live_size))
        return VEGA_DEX_INVALID_ARGUMENT;
    status=VegaDexCheckSector(sector,size,counter,verified);if(status!=VEGA_DEX_OK)return status;
    status=VegaDexValidate(live,live_size);if(status!=VEGA_DEX_OK)return status;
    for(i=0u;i<VEGA_DEX_OWNER_SIZE;++i)if(sector[VEGA_DEX_CHUNK13_OFFSET+i]!=live[i]){*matches=0u;return VEGA_DEX_OK;}
    *matches=1u;return VEGA_DEX_OK;
}
VegaDexStatus VegaDexLoadSelected(uint8_t *live,size_t live_size,const uint8_t *sector,size_t sector_size,
    const uint8_t *save1,size_t save1_size,const uint8_t *save2,size_t save2_size,
    uint32_t counter,uint8_t verified)
{
    uint8_t legacy[VEGA_DEX_LEGACY_SIZE];size_t i;VegaDexStatus status;
    if(live==NULL||save1==NULL||save2==NULL)return VEGA_DEX_INVALID_ARGUMENT;
    if(live_size!=VEGA_DEX_OWNER_SIZE||save1_size!=VEGA_DEX_SAVE1_SIZE||save2_size!=VEGA_DEX_SAVE2_SIZE)return VEGA_DEX_BAD_SIZE;
    if(overlap(live,live_size,sector,sector_size)||overlap(live,live_size,save1,save1_size)||overlap(live,live_size,save2,save2_size))return VEGA_DEX_INVALID_ARGUMENT;
    status=VegaDexCheckSector(sector,sector_size,counter,verified);if(status!=VEGA_DEX_OK)return status;
    for(i=0u;i<52u;++i){legacy[i]=save1[0x5F8u+i];legacy[52u+i]=save1[0x3A18u+i];legacy[104u+i]=save2[0x5Cu+i];legacy[156u+i]=save2[0x28u+i];}
    return VegaDexLoad(live,live_size,sector+VEGA_DEX_CHUNK13_OFFSET,VEGA_DEX_OWNER_SIZE,legacy,sizeof(legacy),verified);
}
VegaDexStatus VegaDexInvalidateSession(uint8_t *live,size_t size)
{
    size_t i;if(live==NULL)return VEGA_DEX_INVALID_ARGUMENT;if(size!=VEGA_DEX_OWNER_SIZE)return VEGA_DEX_BAD_SIZE;
    for(i=0u;i<size;++i)live[i]=0u;
    return VEGA_DEX_OK;
}
