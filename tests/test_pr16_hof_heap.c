/* host上の合成chain検査。実ROM呼出し/全入口heap-readyの証明ではない。 */
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include "overlays/hof_journal/hof_heap.h"

#define ROOT 0x02000000u
#define SIZE 0x1C000u
static uint8_t heap[SIZE],before[SIZE];
static unsigned checks;

static uint16_t r16(const uint8_t *p)
{ return (uint16_t)((uint16_t)p[0]|(uint16_t)p[1]<<8); }
static uint32_t r32(const uint8_t *p)
{ return (uint32_t)p[0]|(uint32_t)p[1]<<8|(uint32_t)p[2]<<16|(uint32_t)p[3]<<24; }
static void w16(uint8_t *p,uint16_t n)
{ p[0]=(uint8_t)n;p[1]=(uint8_t)(n>>8); }
static void w32(uint8_t *p,uint32_t n)
{ unsigned i;for(i=0;i<4;i++)p[i]=(uint8_t)(n>>(8*i)); }
static void header(uint32_t off,unsigned used,uint32_t n,uint32_t prev,uint32_t next)
{
 w16(heap+off,(uint16_t)used);w16(heap+off+2,HH_MAGIC);
 w32(heap+off+4,n);w32(heap+off+8,prev);w32(heap+off+12,next);
}
static void init(uint32_t root,uint32_t size)
{ assert(size>=16&&size<=SIZE);memset(heap,0x5a,sizeof(heap));header(0,0,size-16,root,root); }
static int admit(uint32_t root,uint32_t size,HH_Plan *p)
{
 int rc;HH_Plan zero;memset(&zero,0,sizeof(zero));
 memcpy(before,heap,sizeof(heap));memset(p,0xa5,sizeof(*p));
 rc=HH_Admit(heap,root,size,p);assert(!memcmp(before,heap,sizeof(heap)));
 if(rc!=HH_OK)assert(!memcmp(p,&zero,sizeof(*p)));
 checks++;return rc;
}
static int owned(uint32_t root,uint32_t size,uint32_t raw,HH_Plan *p)
{
 int rc;HH_Plan zero;memset(&zero,0,sizeof(zero));
 memcpy(before,heap,sizeof(heap));memset(p,0xa5,sizeof(*p));
 rc=HH_CheckOwned(heap,root,size,raw,p);assert(!memcmp(before,heap,sizeof(heap)));
 if(rc!=HH_OK)assert(!memcmp(p,&zero,sizeof(*p)));
 checks++;return rc;
}

/* 保存済実命令窓から独立に写したhost oracle。ROMとの同等性はnative側で検査。 */
static uint32_t model_alloc(uint32_t root,uint32_t request)
{
 uint32_t off=0,n=(request+3u)&~3u;
 for(;;){
  uint32_t bytes=r32(heap+off+4),next=r32(heap+off+12);
  if(!r16(heap+off)&&bytes>=n){
   w16(heap+off,1);
   if(bytes-n>31u){
    uint32_t split=off+16+n;
    w32(heap+off+4,n);header(split,0,bytes-n-16,root+off,next);
    w32(heap+off+12,root+split);
    if(next!=root)w32(heap+(next-root)+8,root+split);
   }
   return root+off+16;
  }
  if(next==root)return 0;
  off=next-root;
 }
}
static void model_free(uint32_t root,uint32_t raw)
{
 uint32_t off=raw-root-16,next,prev;
 assert(r16(heap+off)==1&&r16(heap+off+2)==HH_MAGIC);w16(heap+off,0);
 next=r32(heap+off+12);
 if(next!=root&&!r16(heap+next-root)){
  uint32_t other=next-root;
  w32(heap+off+4,r32(heap+off+4)+16+r32(heap+other+4));w16(heap+other+2,0);
  next=r32(heap+other+12);w32(heap+off+12,next);
  if(next!=root)w32(heap+next-root+8,root+off);
 }
 prev=r32(heap+off+8);
 if(off&&!r16(heap+prev-root)){
  uint32_t other=prev-root;
  next=r32(heap+off+12);w32(heap+other+12,next);
  if(next!=root)w32(heap+next-root+8,prev);
  w16(heap+off+2,0);w32(heap+other+4,r32(heap+other+4)+16+r32(heap+off+4));
 }
}

static void geometry(void)
{
 HH_Plan p;unsigned i;
 static const uint32_t bad[][2]={
  {0,SIZE},{ROOT-4,SIZE},{0x02040000u,16},{0x0203FFF4u,16},
  {ROOT+1,SIZE},{ROOT,0},{ROOT,12},{ROOT,17},{ROOT,0xffffffffu},
  {ROOT,0x20008u},{0x02020000u,16},{0x02020004u,16},{0x0202000cu,16}
 };
 init(ROOT,SIZE);
 assert(HH_Admit(0,ROOT,SIZE,&p)==HH_ERR_ARGUMENT);
 assert(HH_Admit(heap,ROOT,SIZE,0)==HH_ERR_ARGUMENT);
 memcpy(before,heap,sizeof(heap));
 assert(HH_Admit(heap,ROOT,SIZE,(HH_Plan *)(void *)heap)==HH_ERR_ARGUMENT);
 assert(HH_Admit(heap,ROOT,SIZE,(HH_Plan *)(void *)(heap+SIZE-4))==HH_ERR_ARGUMENT);
 assert(!memcmp(before,heap,sizeof(heap)));
 for(i=0;i<sizeof(bad)/sizeof(bad[0]);i++)assert(admit(bad[i][0],bad[i][1],&p)==HH_ERR_GEOMETRY);
 init(ROOT,16);assert(admit(ROOT,16,&p)==HH_ERR_OOM);
 init(0x02020010u,HH_ROUNDED_BYTES+16);
 assert(admit(0x02020010u,HH_ROUNDED_BYTES+16,&p)==HH_OK);
 /* EWRAM内だけでは所有/heap-readyを証明しない。上の成功もgeometryだけ。 */
}
static void boundaries(void)
{
 unsigned pad,extra;HH_Plan p,q;
 assert(HH_RAW_BYTES==HH_ARENA_BYTES+7&&HH_ROUNDED_BYTES==((HH_RAW_BYTES+3u)&~3u));
 for(pad=0;pad<=4;pad+=4)for(extra=0;extra<=36;extra+=4){
  uint32_t root=ROOT+pad,size=16+HH_ROUNDED_BYTES+extra,raw;
  init(root,size);assert(admit(root,size,&p)==HH_OK);
  assert(p.block==root&&p.raw==root+16&&p.arena==((p.raw+7u)&~7u));
  assert(!(p.arena&7)&&p.payload==size-16&&p.blocks==1);
  assert(p.free_bytes==size-16&&p.largest_free==size-16);
  assert(p.allocated==(extra<32?size-16:HH_ROUNDED_BYTES));
  assert(p.split_block==(extra<32?0:p.raw+HH_ROUNDED_BYTES));
  assert(p.split_payload==(extra<32?0:extra-16));
  raw=model_alloc(root,HH_RAW_BYTES);assert(raw==p.raw);
  assert(owned(root,size,raw,&q)==HH_OK&&q.allocated==p.allocated&&q.arena==p.arena);
  assert(q.arena+HH_ARENA_BYTES<=raw+q.allocated);
  assert(!q.split_block&&!q.split_payload);
  assert(owned(root,size,raw+4,&q)==HH_ERR_OWNERSHIP);
  assert(owned(root,size,raw-4,&q)==HH_ERR_OWNERSHIP);
  assert(owned(root,size,raw|1u,&q)==HH_ERR_OWNERSHIP);
  if(p.arena!=raw)assert(owned(root,size,p.arena,&q)==HH_ERR_OWNERSHIP);
  model_free(root,raw);assert(owned(root,size,raw,&q)==HH_ERR_OWNERSHIP);
  assert(admit(root,size,&q)==HH_OK&&q.payload==size-16&&q.blocks==1);
 }
 init(ROOT,16+HH_ROUNDED_BYTES-4);assert(admit(ROOT,16+HH_ROUNDED_BYTES-4,&p)==HH_ERR_OOM);
}
static void fragmentation(void)
{
 HH_Plan p;uint32_t a,b,c,d;
 init(ROOT,SIZE);
 a=model_alloc(ROOT,HH_RAW_BYTES);b=model_alloc(ROOT,HH_RAW_BYTES);
 c=model_alloc(ROOT,HH_RAW_BYTES);d=model_alloc(ROOT,HH_RAW_BYTES);
 assert(a&&b&&c&&d);model_free(ROOT,b);model_free(ROOT,d);
 assert(admit(ROOT,SIZE,&p)==HH_OK&&p.raw==b&&p.payload==HH_ROUNDED_BYTES);
 assert(p.largest_free>p.payload); /* 最大ではなくfirst-fit */
 model_free(ROOT,c);assert(admit(ROOT,SIZE,&p)==HH_OK&&p.raw==b&&p.blocks==2);
 model_free(ROOT,a);assert(admit(ROOT,SIZE,&p)==HH_OK&&p.blocks==1&&p.payload==SIZE-16);
 /* 合計freeは大きくても連続領域が不足するchain。 */
 init(ROOT,24048);header(0,0,12000,ROOT,ROOT+12016);
 header(12016,1,0,ROOT,ROOT+12032);header(12032,0,12000,ROOT+12016,ROOT);
 assert(admit(ROOT,24048,&p)==HH_ERR_OOM);
 /* used size0はAlloc(0)で作り得るため、壊れたheaderと混同しない。 */
 init(ROOT,SIZE);a=model_alloc(ROOT,0);assert(a==ROOT+16);
 assert(admit(ROOT,SIZE,&p)==HH_OK&&p.blocks==2&&p.raw==ROOT+32);
 model_free(ROOT,a);assert(admit(ROOT,SIZE,&p)==HH_OK&&p.blocks==1);
}
static void corruptions(void)
{
 HH_Plan p;uint32_t a,b,tail;unsigned off,field,bit;
 uint8_t good[SIZE];
 init(ROOT,SIZE);a=model_alloc(ROOT,HH_RAW_BYTES);b=model_alloc(ROOT,32);
 model_free(ROOT,a);tail=r32(heap+(b-ROOT-16)+12)-ROOT;
 memcpy(good,heap,sizeof(good));
 assert(admit(ROOT,SIZE,&p)==HH_OK&&p.raw==a);
 /* 十分なroot候補があっても、後続全headerの構造を壊す各bit変更を拒否。
  * free→usedの単独変更は構造上合法。構造検査は所有履歴を推測しない。 */
 for(off=0;;){
  for(field=0;field<16;field++)for(bit=0;bit<8;bit++){
   memcpy(heap,good,sizeof(heap));heap[off+field]^=(uint8_t)(1u<<bit);
   if(field==0&&bit==0&&!r16(good+off))assert(admit(ROOT,SIZE,&p)==HH_OK);
   else assert(admit(ROOT,SIZE,&p)==HH_ERR_CHAIN);
  }
  if(off==tail)break;
  off=r32(good+off+12)-ROOT;
 }
 memcpy(heap,good,sizeof(heap));w32(heap+8,ROOT+tail); /* root.prevはtailではない */
 assert(admit(ROOT,SIZE,&p)==HH_ERR_CHAIN);
 memcpy(heap,good,sizeof(heap));w16(heap+b-ROOT-16,0); /* 未coalesceの隣接free */
 assert(admit(ROOT,SIZE,&p)==HH_ERR_CHAIN);
 memcpy(heap,good,sizeof(heap));w32(heap+4,0xfffffffcu);
 assert(admit(ROOT,SIZE,&p)==HH_ERR_CHAIN);
 memcpy(heap,good,sizeof(heap));w32(heap+12,ROOT); /* 早すぎるring終端 */
 assert(admit(ROOT,SIZE,&p)==HH_ERR_CHAIN);
 memcpy(heap,good,sizeof(heap));w32(heap+tail+4,r32(heap+tail+4)-4); /* 未被覆tail */
 assert(admit(ROOT,SIZE,&p)==HH_ERR_CHAIN);
 memcpy(heap,good,sizeof(heap));w32(heap+tail+12,ROOT+tail); /* root以外へのcycle */
 assert(admit(ROOT,SIZE,&p)==HH_ERR_CHAIN);
}
static void ownership_boundaries(void)
{
 HH_Plan p;uint32_t raw,tail;unsigned i;
 init(ROOT,SIZE);raw=model_alloc(ROOT,HH_RAW_BYTES);tail=r32(heap+12)-ROOT;
 assert(owned(ROOT,SIZE,raw,&p)==HH_OK);
 heap[tail+2]^=1;assert(owned(ROOT,SIZE,raw,&p)==HH_ERR_CHAIN);
 heap[tail+2]^=1;
 for(i=0;i<16;i++)assert(owned(ROOT,SIZE,ROOT+i,&p)==HH_ERR_OWNERSHIP);
 assert(owned(ROOT,SIZE,ROOT+SIZE,&p)==HH_ERR_OWNERSHIP);
 assert(owned(ROOT,SIZE,0,&p)==HH_ERR_OWNERSHIP);
 assert(owned(ROOT,SIZE,UINT32_MAX,&p)==HH_ERR_OWNERSHIP);
 /* stock退避は先頭53300byteを上書きする。借用中のENTRY自体を禁止する。 */
 memset(heap,0x66,53300);assert(owned(ROOT,SIZE,raw,&p)==HH_ERR_CHAIN);
 init(ROOT,SIZE);assert(owned(ROOT,SIZE,raw,&p)==HH_ERR_OWNERSHIP);
 assert(model_alloc(ROOT,HH_RAW_BYTES)==raw);
 assert(owned(ROOT,SIZE,raw,&p)==HH_OK);
 /* reset後の再利用は同じpointer/構造を作れる。構造だけで世代識別できない。
  * wrapperの同期lifetime/非再入/reset禁止を別途受入する必要がある。 */
}
static uint32_t rng=0x76543210u;
static uint32_t random_word(void)
{ rng^=rng<<13;rng^=rng>>17;rng^=rng<<5;return rng; }
static void sequences(void)
{
 uint32_t live[128]={0};unsigned i,j;HH_Plan p,q;
 init(ROOT,SIZE);
 for(i=0;i<4000;i++){
  uint32_t expected=0,off=0,raw;int rc;
  j=random_word()%128;
  if(live[j]){model_free(ROOT,live[j]);live[j]=0;}
  else live[j]=model_alloc(ROOT,random_word()%8193u);
  for(;;){
   if(!r16(heap+off)&&r32(heap+off+4)>=HH_ROUNDED_BYTES){expected=ROOT+off+16;break;}
   if(r32(heap+off+12)==ROOT)break;
   off=r32(heap+off+12)-ROOT;
  }
  rc=admit(ROOT,SIZE,&p);assert(rc==(expected?HH_OK:HH_ERR_OOM));
  if(!expected)continue; /* runtime OOM予防と同じく、Allocを呼ばない。 */
  assert(p.raw==expected);raw=model_alloc(ROOT,HH_RAW_BYTES);assert(raw==expected);
  assert(owned(ROOT,SIZE,raw,&q)==HH_OK&&q.allocated==p.allocated&&q.arena==p.arena);
  model_free(ROOT,raw);assert(admit(ROOT,SIZE,&q)==HH_OK&&q.raw==p.raw);
 }
 for(j=0;j<128;j++)if(live[j])model_free(ROOT,live[j]);
 assert(admit(ROOT,SIZE,&p)==HH_OK&&p.blocks==1&&p.free_bytes==SIZE-16);
}
int main(void)
{
 geometry();boundaries();fragmentation();corruptions();ownership_boundaries();sequences();
 printf("{\"status\":\"PASS_SYNTHETIC_HEAP_ADMISSION\",\"checks\":%u,\"runtime_integrated\":false,\"native_calls\":0}\n",checks);
 return 0;
}
