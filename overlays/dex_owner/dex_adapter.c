#include "dex_adapter.h"
#include "dex_adapter_tables.h"
static uint8_t alias(const void *a,size_t an,const void *b,size_t bn)
{uintptr_t x=(uintptr_t)a,y=(uintptr_t)b;if(a==NULL||b==NULL||!an||!bn)return 0u;return (uint8_t)(x<=y?y-x<an:x-y<bn);}
static uint16_t species_owner(uint16_t sid)
{return sid<VEGA_DEX_SPECIES_SLOTS?sDexSpeciesOwner[sid]:0u;}
static void seal(uint8_t *live)
{uint32_t crc=VegaDexChecksum(live,VEGA_DEX_OWNER_SIZE);size_t i;for(i=0u;i<4u;++i)live[4u+i]=(uint8_t)(crc>>(i*8u));}
VegaDexStatus VegaDexSpeciesFlags(uint8_t *live,size_t size,uint16_t sid,uint8_t mode,uint8_t *value)
{return VegaDexAccess(live,size,species_owner(sid),mode,value);}
VegaDexStatus VegaDexOfficialFlags(uint8_t *live,size_t size,uint16_t national,uint8_t mode,uint8_t *value)
{return VegaDexAccess(live,size,national<=VEGA_DEX_OFFICIAL_COUNT?sDexOfficialOwner[national]:0u,mode,value);}
VegaDexStatus VegaDexOfficialRepresentative(uint16_t national,uint16_t *sid)
{
    if(sid==NULL)return VEGA_DEX_INVALID_ARGUMENT;
    if(national==0u||national>VEGA_DEX_OFFICIAL_COUNT)return VEGA_DEX_BAD_OWNER;
    *sid=sDexOfficialRepresentative[national];return VEGA_DEX_OK;
}
VegaDexStatus VegaDexOfficialCount(const uint8_t *live,size_t size,uint8_t mode,uint16_t *count)
{
    size_t i;uint16_t total=0u;VegaDexStatus status;
    if(count==NULL||alias(live,size,count,sizeof(*count)))return VEGA_DEX_INVALID_ARGUMENT;
    if(mode>VEGA_DEX_GET_CAUGHT)return VEGA_DEX_BAD_MODE;
    status=VegaDexValidate(live,size);if(status!=VEGA_DEX_OK)return status;
    for(i=0u;i<VEGA_DEX_BITMAP_SIZE;++i){uint8_t v=(uint8_t)(live[(mode==VEGA_DEX_GET_CAUGHT?VEGA_DEX_CAUGHT_OFFSET:VEGA_DEX_SEEN_OFFSET)+i]&sDexOfficialMask[i]);while(v){total+=(uint16_t)(v&1u);v>>=1;}}
    *count=total;return VEGA_DEX_OK;
}
VegaDexStatus VegaDexSnapshotSpecies(const uint8_t *live,size_t size,uint16_t sid,uint8_t *snap,size_t snap_size)
{
    uint16_t owner=species_owner(sid);size_t index;uint8_t bit;VegaDexStatus status;
    if(snap==NULL||alias(live,size,snap,snap_size))return VEGA_DEX_INVALID_ARGUMENT;
    if(snap_size!=VEGA_DEX_BIT_SNAPSHOT_SIZE)return VEGA_DEX_BAD_SIZE;
    if(owner==0u)return VEGA_DEX_BAD_OWNER;
    status=VegaDexValidate(live,size);if(status!=VEGA_DEX_OK)return status;
    index=(owner-1u)>>3;bit=(uint8_t)(1u<<((owner-1u)&7u));
    snap[0]=(uint8_t)owner;snap[1]=(uint8_t)(owner>>8);snap[2]=(uint8_t)(((live[VEGA_DEX_SEEN_OFFSET+index]&bit)?1u:0u)|((live[VEGA_DEX_CAUGHT_OFFSET+index]&bit)?2u:0u));snap[3]=0xD1u;
    return VEGA_DEX_OK;
}
VegaDexStatus VegaDexRestoreSpecies(uint8_t *live,size_t size,uint16_t sid,const uint8_t *snap,size_t snap_size)
{
    uint16_t owner=species_owner(sid);size_t index;uint8_t bit;VegaDexStatus status;
    if(snap==NULL||alias(live,size,snap,snap_size))return VEGA_DEX_INVALID_ARGUMENT;
    if(snap_size!=VEGA_DEX_BIT_SNAPSHOT_SIZE)return VEGA_DEX_BAD_SIZE;
    if(owner==0u||owner!=(uint16_t)((uint16_t)snap[0]|((uint16_t)snap[1]<<8)))return VEGA_DEX_BAD_OWNER;
    if(snap[3]!=0xD1u||snap[2]>3u||snap[2]==2u)return VEGA_DEX_BAD_FLAGS;
    status=VegaDexValidate(live,size);if(status!=VEGA_DEX_OK)return status;
    index=(owner-1u)>>3;bit=(uint8_t)(1u<<((owner-1u)&7u));
    live[VEGA_DEX_SEEN_OFFSET+index]=(uint8_t)((live[VEGA_DEX_SEEN_OFFSET+index]&~bit)|((snap[2]&1u)?bit:0u));
    live[VEGA_DEX_CAUGHT_OFFSET+index]=(uint8_t)((live[VEGA_DEX_CAUGHT_OFFSET+index]&~bit)|((snap[2]&2u)?bit:0u));seal(live);return VEGA_DEX_OK;
}
VegaDexStatus VegaDexSnapshotSeen(const uint8_t *live,size_t size,uint8_t *snap,size_t snap_size)
{
    size_t i;VegaDexStatus status;if(snap==NULL||alias(live,size,snap,snap_size))return VEGA_DEX_INVALID_ARGUMENT;
    if(snap_size!=VEGA_DEX_BITMAP_SIZE)return VEGA_DEX_BAD_SIZE;
    status=VegaDexValidate(live,size);if(status!=VEGA_DEX_OK)return status;
    for(i=0u;i<snap_size;++i){snap[i]=live[VEGA_DEX_SEEN_OFFSET+i];}
    return VEGA_DEX_OK;
}
VegaDexStatus VegaDexRestoreSeen(uint8_t *live,size_t size,const uint8_t *snap,size_t snap_size)
{
    size_t i;VegaDexStatus status;if(snap==NULL||alias(live,size,snap,snap_size))return VEGA_DEX_INVALID_ARGUMENT;
    if(snap_size!=VEGA_DEX_BITMAP_SIZE)return VEGA_DEX_BAD_SIZE;
    if(snap[snap_size-1u]&0xC0u)return VEGA_DEX_BAD_PADDING;
    status=VegaDexValidate(live,size);if(status!=VEGA_DEX_OK)return status;
    for(i=0u;i<snap_size;++i)if(live[VEGA_DEX_CAUGHT_OFFSET+i]&(uint8_t)~snap[i])return VEGA_DEX_CAUGHT_WITHOUT_SEEN;
    for(i=0u;i<snap_size;++i){live[VEGA_DEX_SEEN_OFFSET+i]=snap[i];}
    seal(live);return VEGA_DEX_OK;
}
