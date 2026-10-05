#include "hof_heap.h"

#define HH_EWRAM_FIRST 0x02000000u
#define HH_EWRAM_END 0x02040000u
#define HH_SCRATCH_FIRST 0x02020004u
#define HH_SCRATCH_END 0x02020010u

static uint16_t rd16(const volatile uint8_t *p)
{ return (uint16_t)((uint16_t)p[0]|(uint16_t)p[1]<<8); }
static uint32_t rd32(const volatile uint8_t *p)
{ return (uint32_t)p[0]|(uint32_t)p[1]<<8|(uint32_t)p[2]<<16|(uint32_t)p[3]<<24; }
static void clear(HH_Plan *p)
{
 p->block=0;p->raw=0;p->arena=0;p->payload=0;p->allocated=0;
 p->split_block=0;p->split_payload=0;p->largest_free=0;p->free_bytes=0;p->blocks=0;
}
static void copy(HH_Plan *to,const HH_Plan *from)
{
 to->block=from->block;to->raw=from->raw;to->arena=from->arena;
 to->payload=from->payload;to->allocated=from->allocated;
 to->split_block=from->split_block;to->split_payload=from->split_payload;
 to->largest_free=from->largest_free;to->free_bytes=from->free_bytes;to->blocks=from->blocks;
}

/* 数値GBA addressとhost写像pointerを混同しない。span加算を使わず検査。 */
static int separate(const volatile uint8_t *heap,uint32_t size,const HH_Plan *out)
{
 uintptr_t a=(uintptr_t)heap,b=(uintptr_t)out;
 return a<=b?b-a>=size:a-b>=sizeof(*out);
}
static int walk(const volatile uint8_t *heap,uint32_t root,uint32_t size,
                 uint32_t owned,int ownership,HH_Plan *out)
{
 HH_Plan plan;uint32_t off=0,previous=root;unsigned previous_free=0;
 if(!heap||!out||!separate(heap,size,out))return HH_ERR_ARGUMENT;
 clear(out);clear(&plan);
 if(root<HH_EWRAM_FIRST||root>=HH_EWRAM_END||(root&3u)||
    size<HH_HEADER_BYTES||(size&3u)||size>HH_EWRAM_END-root)
  return HH_ERR_GEOMETRY;
 if(root<HH_SCRATCH_END&&root+size>HH_SCRATCH_FIRST)return HH_ERR_GEOMETRY;
 if(ownership&&((owned&3u)||owned<root+HH_HEADER_BYTES||
                owned>root+size-HH_ROUNDED_BYTES))return HH_ERR_OWNERSHIP;
 for(;;){
  const volatile uint8_t *h=heap+off;
  uint32_t block=root+off,payload,next,end;uint16_t used;
  /* nextの採用前に常に残りheader長を確定。循環/任意pointerは追跡しない。 */
  if(size-off<HH_HEADER_BYTES)return HH_ERR_CHAIN;
  used=rd16(h);payload=rd32(h+4);next=rd32(h+12);
  if(used>1u||rd16(h+2)!=HH_MAGIC||rd32(h+8)!=previous||
     (payload&3u)||payload>size-off-HH_HEADER_BYTES||(!used&&previous_free))
   return HH_ERR_CHAIN;
  end=off+HH_HEADER_BYTES+payload;
  if(next!=(end==size?root:root+end))return HH_ERR_CHAIN;
  plan.blocks++;
  if(!used){
   plan.free_bytes+=payload;
   if(payload>plan.largest_free)plan.largest_free=payload;
  }
  if(!plan.block&&((ownership&&used&&block+HH_HEADER_BYTES==owned&&payload>=HH_ROUNDED_BYTES)||
                   (!ownership&&!used&&payload>=HH_ROUNDED_BYTES))){
   plan.block=block;plan.raw=block+HH_HEADER_BYTES;
   plan.arena=(plan.raw+(HH_ALIGNMENT-1u))&~(HH_ALIGNMENT-1u);
   plan.payload=payload;plan.allocated=payload;
   if(!ownership&&payload-HH_ROUNDED_BYTES>31u){
    plan.allocated=HH_ROUNDED_BYTES;
    plan.split_block=plan.raw+HH_ROUNDED_BYTES;
    plan.split_payload=payload-HH_ROUNDED_BYTES-HH_HEADER_BYTES;
   }
  }
  if(end==size)break;
  previous=block;previous_free=!used;off=end;
 }
 if(!plan.block)return ownership?HH_ERR_OWNERSHIP:HH_ERR_OOM;
 /* 4byte raw整列ではpadは0又は4だが、arena全体の上限も明示検査する。 */
 if(plan.arena-plan.raw>plan.allocated||
    HH_ARENA_BYTES>plan.allocated-(plan.arena-plan.raw))return HH_ERR_CHAIN;
 copy(out,&plan);return HH_OK;
}
int HH_Admit(const volatile uint8_t *heap,uint32_t root,uint32_t size,HH_Plan *out)
{ return walk(heap,root,size,0,0,out); }
int HH_CheckOwned(const volatile uint8_t *heap,uint32_t root,uint32_t size,
                  uint32_t raw,HH_Plan *out)
{ return walk(heap,root,size,raw,1,out); }
