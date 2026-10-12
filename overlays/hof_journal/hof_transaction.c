/* Pythonの実32sector schedulerのC実装。stock/既存owner検証は省略しない。 */
#include "hof_transaction.h"

#define HT_SIGN 0x08012025u
#define HT_HOF_HALF 3968u
#define HT_SIGNATURE 0xFF8u

static uint16_t rd16(const uint8_t *p)
{ return (uint16_t)((uint16_t)p[0] | (uint16_t)p[1]<<8); }
static uint32_t rd32(const uint8_t *p)
{ return (uint32_t)p[0] | (uint32_t)p[1]<<8 | (uint32_t)p[2]<<16 | (uint32_t)p[3]<<24; }
static uint64_t rd64(const uint8_t *p)
{ return (uint64_t)rd32(p) | (uint64_t)rd32(p+4)<<32; }
static void wr16(uint8_t *p,uint16_t n)
{ p[0]=(uint8_t)n;p[1]=(uint8_t)(n>>8); }
static void wr32(uint8_t *p,uint32_t n)
{ unsigned i;for(i=0;i<4;i++)p[i]=(uint8_t)(n>>(8*i)); }
static void cp(uint8_t *out,const uint8_t *in,unsigned n)
{ unsigned i;for(i=0;i<n;i++)out[i]=in[i]; }
static void fill(uint8_t *p,uint8_t value,unsigned n)
{ unsigned i;for(i=0;i<n;i++)p[i]=value; }
static int same(const uint8_t *a,const uint8_t *b,unsigned n)
{ unsigned i;for(i=0;i<n;i++)if(a[i]!=b[i])return 0;return 1; }
static int all(const uint8_t *p,unsigned n,uint8_t value)
{ unsigned i;for(i=0;i<n;i++)if(p[i]!=value)return 0;return 1; }
static int apart(const void *a,unsigned an,const void *b,unsigned bn)
{
 uintptr_t x=(uintptr_t)a,y=(uintptr_t)b;
 return x<=y ? y-x>=an : x-y>=bn;
}
static unsigned mod14(unsigned p) { return p>=14u ? p-14u : p; }
static unsigned physical(const HT_Main *m,unsigned sid)
{ return m->base+mod14(m->first+sid); }

/* freestanding SHA-256。16word循環scheduleと64byte blockはworkspace所有。 */
static uint32_t rotr(uint32_t x,unsigned n) { return (x>>n)|(x<<(32u-n)); }
static void sha_block(HT_SHA256 *s)
{
 static const uint32_t k[64]={
  0x428a2f98u,0x71374491u,0xb5c0fbcfu,0xe9b5dba5u,0x3956c25bu,0x59f111f1u,0x923f82a4u,0xab1c5ed5u,
  0xd807aa98u,0x12835b01u,0x243185beu,0x550c7dc3u,0x72be5d74u,0x80deb1feu,0x9bdc06a7u,0xc19bf174u,
  0xe49b69c1u,0xefbe4786u,0x0fc19dc6u,0x240ca1ccu,0x2de92c6fu,0x4a7484aau,0x5cb0a9dcu,0x76f988dau,
  0x983e5152u,0xa831c66du,0xb00327c8u,0xbf597fc7u,0xc6e00bf3u,0xd5a79147u,0x06ca6351u,0x14292967u,
  0x27b70a85u,0x2e1b2138u,0x4d2c6dfcu,0x53380d13u,0x650a7354u,0x766a0abbu,0x81c2c92eu,0x92722c85u,
  0xa2bfe8a1u,0xa81a664bu,0xc24b8b70u,0xc76c51a3u,0xd192e819u,0xd6990624u,0xf40e3585u,0x106aa070u,
  0x19a4c116u,0x1e376c08u,0x2748774cu,0x34b0bcb5u,0x391c0cb3u,0x4ed8aa4au,0x5b9cca4fu,0x682e6ff3u,
  0x748f82eeu,0x78a5636fu,0x84c87814u,0x8cc70208u,0x90befffau,0xa4506cebu,0xbef9a3f7u,0xc67178f2u
 };
 uint32_t a=s->h[0],b=s->h[1],c=s->h[2],d=s->h[3];
 uint32_t e=s->h[4],f=s->h[5],g=s->h[6],h=s->h[7],t1,t2,x,y;
 unsigned i;
 for(i=0;i<16;i++){
  const uint8_t *p=s->block+4*i;
  s->words[i]=(uint32_t)p[0]<<24|(uint32_t)p[1]<<16|(uint32_t)p[2]<<8|p[3];
 }
 for(i=0;i<64;i++){
  if(i>=16){
   x=s->words[(i-15u)&15u];y=s->words[(i-2u)&15u];
   s->words[i&15u]+=(rotr(x,7)^rotr(x,18)^(x>>3))+s->words[(i-7u)&15u]+(rotr(y,17)^rotr(y,19)^(y>>10));
  }
  t1=h+(rotr(e,6)^rotr(e,11)^rotr(e,25))+((e&f)^((~e)&g))+k[i]+s->words[i&15u];
  t2=(rotr(a,2)^rotr(a,13)^rotr(a,22))+((a&b)^(a&c)^(b&c));
  h=g;g=f;f=e;e=d+t1;d=c;c=b;b=a;a=t1+t2;
 }
 s->h[0]+=a;s->h[1]+=b;s->h[2]+=c;s->h[3]+=d;
 s->h[4]+=e;s->h[5]+=f;s->h[6]+=g;s->h[7]+=h;
}
static void sha_begin(HT_SHA256 *s)
{
 static const uint32_t init[8]={0x6a09e667u,0xbb67ae85u,0x3c6ef372u,0xa54ff53au,0x510e527fu,0x9b05688cu,0x1f83d9abu,0x5be0cd19u};
 unsigned i;for(i=0;i<8;i++)s->h[i]=init[i];s->bytes=0;s->used=0;
}
static void sha_add(HT_SHA256 *s,const uint8_t *p,unsigned n)
{
 unsigned i;s->bytes+=n;
 for(i=0;i<n;i++){
  s->block[s->used++]=p[i];
  if(s->used==64){sha_block(s);s->used=0;}
 }
}
static void sha_end(HT_SHA256 *s,uint8_t out[32])
{
 uint32_t lo=s->bytes<<3,hi=s->bytes>>29;unsigned i;
 s->block[s->used++]=0x80;
 if(s->used>56){while(s->used<64)s->block[s->used++]=0;sha_block(s);s->used=0;}
 while(s->used<56)s->block[s->used++]=0;
 for(i=0;i<4;i++){s->block[56+i]=(uint8_t)(hi>>(24-8*i));s->block[60+i]=(uint8_t)(lo>>(24-8*i));}
 sha_block(s);
 for(i=0;i<32;i++)out[i]=(uint8_t)(s->h[i>>2]>>(24-8*(i&3u)));
}
static void digest(HT_Workspace *w,const uint8_t *p,unsigned n,uint8_t out[32])
{ sha_begin(&w->sha);sha_add(&w->sha,p,n);sha_end(&w->sha,out); }

static int args(const HT_Ops *o,HT_Workspace *w,int writing,int preparing)
{
 if(!o||!w||!w->sector||!w->hof||!o->read_sector||!o->select_main||!o->validate_main_sector)return HT_ERR_ARGUMENT;
 if((writing&&(!o->erase_sector||!o->program_byte))||(preparing&&!o->prepare_main_sector))return HT_ERR_ARGUMENT;
 if(!apart(w,sizeof(*w),w->sector,HT_SECTOR_SIZE)||!apart(w,sizeof(*w),w->hof,HJ_PAYLOAD)||
    !apart(w->sector,HT_SECTOR_SIZE,w->hof,HJ_PAYLOAD)||!apart(o,sizeof(*o),w,sizeof(*w))||
    !apart(o,sizeof(*o),w->sector,HT_SECTOR_SIZE)||!apart(o,sizeof(*o),w->hof,HJ_PAYLOAD))return HT_ERR_ARGUMENT;
 return HT_OK;
}
static int read_sector(const HT_Ops *o,HT_Workspace *w,unsigned sector)
{
 if(sector>=HT_FLASH_SECTORS)return HT_ERR_ARGUMENT;
 return o->read_sector(o->user,sector,w->sector)==1?HT_OK:HT_ERR_IO;
}
static uint16_t checksum(const uint8_t *p,unsigned n)
{ uint32_t sum=0;unsigned i;for(i=0;i<n;i+=4)sum+=rd32(p+i);return (uint16_t)(sum+(sum>>16)); }
static unsigned main_size(unsigned sid)
{ if(sid==0)return 0xF24u;if(sid==4)return 0xEC0u;if(sid==13)return 0x7D0u;return 0xF80u; }
static int main_sector(const HT_Ops *o,const HT_Main *m,unsigned sid,const uint8_t *b)
{
 if(sid>=14||rd16(b+0xFF4)!=sid||rd16(b+0xFF6)!=checksum(b,main_size(sid))||rd32(b+0xFF8)!=HT_SIGN||rd32(b+0xFFC)!=m->counter)return HT_ERR_MAIN;
 if(o->validate_main_sector(o->user,m,sid,b)!=1)return HT_ERR_MAIN;
 return HT_OK;
}
static int hash_sectors(const HT_Ops *o,HT_Workspace *w,unsigned first,unsigned count,uint8_t out[32])
{
 unsigned i;int rc;sha_begin(&w->sha);
 for(i=0;i<count;i++){rc=read_sector(o,w,first+i);if(rc)return rc;sha_add(&w->sha,w->sector,HT_SECTOR_SIZE);}
 sha_end(&w->sha,out);return HT_OK;
}
static int selected_main(const HT_Ops *o,HT_Workspace *w)
{
 HT_Result *r=&w->result;unsigned p,sid;int rc;
 fill((uint8_t *)r,0,sizeof(*r));
 if(o->select_main(o->user,&r->main,w->sector)!=1)return HT_ERR_MAIN;
 if(r->main.first>=14||r->main.base!=14u*(r->main.counter&1u))return HT_ERR_MAIN;
 sha_begin(&w->sha);
 for(p=0;p<14;p++){
  rc=read_sector(o,w,r->main.base+p);if(rc)return rc;
  sid=mod14(p+14u-r->main.first);
  rc=main_sector(o,&r->main,sid,w->sector);if(rc)return rc;
  sha_add(&w->sha,w->sector,HT_SECTOR_SIZE);
  if(sid==4){
   if(!all(w->sector+HT_JOURNAL_OFFSET+HJ_SIZE,48,0))return HT_ERR_JOURNAL;
   cp(w->selected_journal,w->sector+HT_JOURNAL_OFFSET,HJ_SIZE);
   r->has_journal=(uint8_t)!all(w->selected_journal,HJ_SIZE,0);
  }
 }
 sha_end(&w->sha,r->source_sha);
 if(r->has_journal){
  if(!HJ_Validate(w->selected_journal))return HT_ERR_JOURNAL;
  r->epoch=rd64(w->selected_journal+24);
 }
 return HT_OK;
}
static int find_intent(const HT_Ops *o,HT_Workspace *w)
{
 HT_Result *r=&w->result;unsigned p;int rc;const uint8_t *j;
 r->pending=0;
 for(p=0;p<14;p++){
  rc=read_sector(o,w,14u-r->main.base+p);if(rc)return rc;
  if(rd16(w->sector+0xFF4)!=4)continue;
  j=w->sector+HT_JOURNAL_OFFSET;
  if(!HJ_Validate(j)||rd32(j+8)!=r->main.counter||!same(j+220,r->source_sha,32))continue;
  if(r->has_journal&&(rd64(j+16)!=r->epoch||!same(j+32,w->selected_journal+64,32)))continue;
  if(rd32(w->sector+0xFFC)!=rd32(j+12)||!all(j+HJ_SIZE,48,0))continue;
  if(r->pending)return HT_ERR_AMBIGUOUS;
  r->pending=1;r->pending_first=(uint8_t)mod14(p+10u);cp(w->journal,j,HJ_SIZE);
 }
 return HT_OK;
}
static int read_hof(const HT_Ops *o,HT_Workspace *w,unsigned a,unsigned b)
{
 unsigned i;int rc;
 for(i=0;i<2;i++){
  rc=read_sector(o,w,i?b:a);if(rc)return rc;
  if(rd32(w->sector+0xFF8)!=HT_SIGN||rd16(w->sector+0xFF4)!=checksum(w->sector,HT_HOF_HALF))return HT_ERR_HOF;
  cp(w->hof+i*HT_HOF_HALF,w->sector,HT_HOF_HALF);
 }
 digest(w,w->hof,HJ_PAYLOAD,w->result.hof_sha);return HT_OK;
}
static void absent(HT_Workspace *w,unsigned route)
{
 fill(w->hof,0,HJ_PAYLOAD);w->result.has_hof=0;w->result.route=(uint8_t)route;
 digest(w,w->hof,HJ_PAYLOAD,w->result.hof_sha);
}
int HT_Resolve(const HT_Ops *o,HT_Workspace *w)
{
 HT_Result *r;unsigned a,b;int rc=args(o,w,0,0);if(rc)return rc;r=&w->result;
 rc=selected_main(o,w);if(rc)return rc;
 rc=find_intent(o,w);if(rc)return rc;
 if(r->pending&&w->journal[96]==HJ_INITIAL){
  absent(w,HT_ROUTE_INITIAL_ABSENCE);
  /* INITIALはcanonical absenceからしか作れない。CRCだけの偽absenceも拒否。 */
  if(r->has_journal||!same(r->hof_sha,w->journal+32,32)||!all(w->journal+100,HJ_TEAM,0))return HT_ERR_JOURNAL;
  return HT_OK;
 }
 rc=read_hof(o,w,28,29);
 if(rc!=HT_OK&&rc!=HT_ERR_HOF)return rc;
 if(r->pending){
  if(rc==HT_OK&&same(r->hof_sha,w->journal+32,32)){r->has_hof=1;r->route=HT_ROUTE_FIXED_OLD;return HT_OK;}
  if(rc==HT_OK&&same(r->hof_sha,w->journal+64,32)){
   if(!HJ_Rollback(w->hof,w->hof,w->journal))return HT_ERR_JOURNAL;
   digest(w,w->hof,HJ_PAYLOAD,r->hof_sha);
   if(same(r->hof_sha,w->journal+32,32)){r->has_hof=1;r->route=HT_ROUTE_INVERSE;return HT_OK;}
  }
  a=14u-r->main.base+mod14(r->pending_first+8u);b=14u-r->main.base+mod14(r->pending_first+9u);
  rc=read_hof(o,w,a,b);if(rc)return rc;
  if(!same(r->hof_sha,w->journal+32,32))return HT_ERR_HOF;
  r->has_hof=1;r->route=HT_ROUTE_SCRATCH;return HT_OK;
 }
 if(rc==HT_ERR_HOF){
  if(r->has_journal)return HT_ERR_HOF;
  absent(w,HT_ROUTE_LEGACY_UNCLASSIFIED);return HT_OK;
 }
 if(r->has_journal&&!same(r->hof_sha,w->selected_journal+64,32))return HT_ERR_HOF;
 r->has_hof=1;r->route=HT_ROUTE_FIXED;return HT_OK;
}

/* 全erase/program経路に同じ保護範囲制約。aux30/31は読取りだけ。 */
static int writable(HT_Workspace *w,unsigned sector)
{ return sector<30&&(sector<w->result.main.base||sector>=w->result.main.base+14u); }
static int erase_verified(const HT_Ops *o,HT_Workspace *w,unsigned sector)
{
 int rc;if(!writable(w,sector))return HT_ERR_ARGUMENT;
 if(o->erase_sector(o->user,sector)!=1)return HT_ERR_IO;
 rc=read_sector(o,w,sector);if(rc)return rc;
 return all(w->sector,HT_SECTOR_SIZE,0xff)?HT_OK:HT_ERR_READBACK;
}
typedef int (*Builder)(const HT_Ops *,HT_Workspace *,const void *);
/* erase readbackでsector bufferが消えるので、画像を再生成して別SHAと照合。
 * FF8以外の全byteも署名前にreadbackする。checksum対象外のomitでも、
 * 不一致sectorをvalid化しない。最後の署名byte自体も全像SHAでreadback。 */
static int write_built(const HT_Ops *o,HT_Workspace *w,unsigned sector,
                       Builder build,const void *context,const uint8_t *preflight)
{
 uint8_t expected[32],prepared[32],actual[32],signature;unsigned n;int rc;
 if(!writable(w,sector))return HT_ERR_ARGUMENT;
 rc=build(o,w,context);if(rc)return rc;
 digest(w,w->sector,HT_SECTOR_SIZE,expected);
 if(preflight&&!same(expected,preflight,32))return HT_ERR_CHANGED;
 rc=erase_verified(o,w,sector);if(rc)return rc;
 rc=build(o,w,context);if(rc)return rc;
 digest(w,w->sector,HT_SECTOR_SIZE,actual);
 if(!same(actual,expected,32))return HT_ERR_CHANGED;
 signature=w->sector[HT_SIGNATURE];w->sector[HT_SIGNATURE]=0xff;
 digest(w,w->sector,HT_SECTOR_SIZE,prepared);w->sector[HT_SIGNATURE]=signature;
 for(n=0;n<HT_SIGNATURE;n++)if(o->program_byte(o->user,sector,n,w->sector[n])!=1)return HT_ERR_IO;
 for(n=HT_SIGNATURE+1;n<HT_SECTOR_SIZE;n++)if(o->program_byte(o->user,sector,n,w->sector[n])!=1)return HT_ERR_IO;
 rc=read_sector(o,w,sector);if(rc)return rc;
 digest(w,w->sector,HT_SECTOR_SIZE,actual);
 if(!same(actual,prepared,32))return HT_ERR_READBACK;
 if(o->program_byte(o->user,sector,HT_SIGNATURE,signature)!=1)return HT_ERR_IO;
 rc=read_sector(o,w,sector);if(rc)return rc;
 digest(w,w->sector,HT_SECTOR_SIZE,actual);
 return same(actual,expected,32)?HT_OK:HT_ERR_READBACK;
}
typedef struct {const HT_Main *source,*target;const uint8_t *journal;unsigned sid;} MainBuild;
static int build_main(const HT_Ops *o,HT_Workspace *w,const void *context)
{
 const MainBuild *c=(const MainBuild *)context;int rc;
 if(o->prepare_main_sector(o->user,c->source,c->target,c->sid,c->journal,w->sector)!=1)return HT_ERR_PREPARE;
 rc=main_sector(o,c->target,c->sid,w->sector);if(rc)return rc;
 if(c->sid==4){
  if(c->journal){if(!same(w->sector+HT_JOURNAL_OFFSET,c->journal,HJ_SIZE))return HT_ERR_PREPARE;}
  else if(!all(w->sector+HT_JOURNAL_OFFSET,HJ_SIZE,0))return HT_ERR_PREPARE;
  if(!all(w->sector+HT_JOURNAL_OFFSET+HJ_SIZE,48,0))return HT_ERR_PREPARE;
 }
 return HT_OK;
}
typedef struct {const uint8_t *payload;unsigned half;} HofBuild;
static int build_hof(const HT_Ops *o,HT_Workspace *w,const void *context)
{
 const HofBuild *c=(const HofBuild *)context;(void)o;
 fill(w->sector,0,HT_SECTOR_SIZE);cp(w->sector,c->payload+c->half*HT_HOF_HALF,HT_HOF_HALF);
 wr16(w->sector+0xFF4,checksum(w->sector,HT_HOF_HALF));wr32(w->sector+0xFF8,HT_SIGN);return HT_OK;
}
static int build_copy(const HT_Ops *o,HT_Workspace *w,const void *context)
{ return read_sector(o,w,*(const unsigned *)context); }
/* ARMのaggregate assignmentがmemcpy libcall化するため、各fieldだけを写す。 */
static void copy_main(HT_Main *out,const HT_Main *in)
{ out->counter=in->counter;out->base=in->base;out->first=in->first; }
static void target_main(const HT_Main *source,HT_Main *target)
{ target->counter=source->counter+1u;target->base=(uint8_t)(14u*(target->counter&1u));target->first=(uint8_t)mod14(source->first+1u); }
static int preflight(const HT_Ops *o,HT_Workspace *w,MainBuild *c)
{
 int rc;for(c->sid=0;c->sid<14;c->sid++){
  rc=build_main(o,w,c);if(rc)return rc;digest(w,w->sector,HT_SECTOR_SIZE,w->prepared_sha[c->sid]);
 }
 return HT_OK;
}
static int protect_after(const HT_Ops *o,HT_Workspace *w,const HT_Main *source,const uint8_t source_sha[32])
{
 uint8_t actual[32];int rc=hash_sectors(o,w,source->base,14,actual);if(rc)return rc;
 if(!same(actual,source_sha,32))return HT_ERR_CHANGED;
 rc=hash_sectors(o,w,30,2,actual);if(rc)return rc;
 return same(actual,w->aux_sha,32)?HT_OK:HT_ERR_CHANGED;
}
int HT_Recover(const HT_Ops *o,HT_Workspace *w)
{
 HT_Main source;HofBuild c;uint8_t source_sha[32];unsigned i,ids[2],retire,had_hof,route;int rc=args(o,w,1,0);if(rc)return rc;
 rc=HT_Resolve(o,w);if(rc||!w->result.pending)return rc;
 copy_main(&source,&w->result.main);cp(source_sha,w->result.source_sha,32);cp(w->old_sha,w->result.hof_sha,32);
 had_hof=w->result.has_hof;route=w->result.route;
 ids[0]=14u-source.base+mod14(w->result.pending_first+8u);ids[1]=14u-source.base+mod14(w->result.pending_first+9u);
 retire=14u-source.base+mod14(w->result.pending_first+4u);
 rc=hash_sectors(o,w,30,2,w->aux_sha);if(rc)return rc;
 if(had_hof){
  c.payload=w->hof;
  /* scratchが唯一の旧像なら、そのscratchをeraseしない。inverse時は先に退避。 */
  if(route!=HT_ROUTE_SCRATCH)for(i=0;i<2;i++){c.half=i;rc=write_built(o,w,ids[i],build_hof,&c,0);if(rc)return rc;}
  for(i=0;i<2;i++){c.half=i;rc=write_built(o,w,28+i,build_hof,&c,0);if(rc)return rc;}
  rc=read_hof(o,w,28,29);if(rc)return rc;
  if(!same(w->result.hof_sha,w->old_sha,32))return HT_ERR_READBACK;
 }else{
  for(i=0;i<2;i++){rc=erase_verified(o,w,28+i);if(rc)return rc;}
 }
 rc=erase_verified(o,w,retire);if(rc)return rc;
 rc=HT_Resolve(o,w);if(rc)return rc;
 if(w->result.pending||w->result.has_hof!=had_hof||!same(w->result.source_sha,source_sha,32)||!same(w->result.hof_sha,w->old_sha,32))return HT_ERR_CHANGED;
 return protect_after(o,w,&source,source_sha);
}
int HT_Commit(const HT_Ops *o,HT_Workspace *w,const uint8_t next[HJ_PAYLOAD],
              unsigned kind,unsigned slot,int verified_absence)
{
 HT_Main source,target;MainBuild c;HofBuild h;uint8_t source_sha[32];uint64_t epoch;unsigned i,from;int rc=args(o,w,1,1);if(rc)return rc;
 if(!next||!apart(next,HJ_PAYLOAD,w,sizeof(*w))||!apart(next,HJ_PAYLOAD,w->sector,HT_SECTOR_SIZE)||!apart(next,HJ_PAYLOAD,w->hof,HJ_PAYLOAD))return HT_ERR_ARGUMENT;
 rc=HT_Resolve(o,w);if(rc)return rc;
 if(w->result.pending)return HT_ERR_PENDING;
 if(!w->result.has_hof){
  if(verified_absence!=1||kind!=HJ_INITIAL||w->result.has_journal)return HT_ERR_ABSENCE;
 }else if(kind==HJ_INITIAL)return HT_ERR_ABSENCE;
 copy_main(&source,&w->result.main);target_main(&source,&target);epoch=w->result.epoch;
 cp(source_sha,w->result.source_sha,32);cp(w->old_sha,w->result.hof_sha,32);digest(w,next,HJ_PAYLOAD,w->new_sha);
 if(!HJ_Build(w->journal,w->hof,next,source.counter,epoch,w->old_sha,w->new_sha,source_sha,kind,slot))return HT_ERR_TRANSITION;
 c.source=&source;c.target=&target;c.journal=w->journal;
 rc=preflight(o,w,&c);if(rc)return rc;
 rc=hash_sectors(o,w,30,2,w->aux_sha);if(rc)return rc;
 rc=erase_verified(o,w,physical(&target,13));if(rc)return rc;
 for(i=0;i<2;i++){from=28+i;rc=write_built(o,w,physical(&target,8+i),build_copy,&from,0);if(rc)return rc;}
 c.sid=4;rc=write_built(o,w,physical(&target,4),build_main,&c,w->prepared_sha[4]);if(rc)return rc;
 h.payload=next;
 for(i=0;i<2;i++){h.half=i;rc=write_built(o,w,28+i,build_hof,&h,0);if(rc)return rc;}
 rc=read_hof(o,w,28,29);if(rc)return rc;
 if(!same(w->result.hof_sha,w->new_sha,32))return HT_ERR_READBACK;
 for(i=0;i<14;i++){
  if(i==4)continue;
  c.sid=i;
  rc=write_built(o,w,physical(&target,i),build_main,&c,w->prepared_sha[i]);if(rc)return rc;
 }
 rc=HT_Resolve(o,w);if(rc)return rc;
 if(w->result.pending||w->result.main.counter!=target.counter||w->result.main.base!=target.base||w->result.main.first!=target.first||
    !w->result.has_hof||!w->result.has_journal||w->result.epoch!=epoch+1u||!same(w->result.hof_sha,w->new_sha,32)||
    !same(w->selected_journal,w->journal,HJ_SIZE))return HT_ERR_CHANGED;
 return protect_after(o,w,&source,source_sha);
}
int HT_Normal(const HT_Ops *o,HT_Workspace *w)
{
 HT_Main source,target;MainBuild c;uint8_t source_sha[32];uint64_t epoch;unsigned i,had_hof,had_journal;int rc=args(o,w,1,1);if(rc)return rc;
 /* prepareを含む通常writerはrecoveryの後。未完journal上へ先に書かせない。 */
 rc=HT_Recover(o,w);if(rc)return rc;
 copy_main(&source,&w->result.main);target_main(&source,&target);epoch=w->result.epoch;
 had_hof=w->result.has_hof;had_journal=w->result.has_journal;
 cp(source_sha,w->result.source_sha,32);cp(w->old_sha,w->result.hof_sha,32);cp(w->journal,w->selected_journal,HJ_SIZE);
 c.source=&source;c.target=&target;c.journal=had_journal?w->journal:0;
 rc=preflight(o,w,&c);if(rc)return rc;
 rc=hash_sectors(o,w,30,2,w->aux_sha);if(rc)return rc;
 rc=erase_verified(o,w,physical(&target,13));if(rc)return rc;
 for(i=0;i<14;i++){
  c.sid=i;rc=write_built(o,w,physical(&target,i),build_main,&c,w->prepared_sha[i]);if(rc)return rc;
 }
 rc=HT_Resolve(o,w);if(rc)return rc;
 if(w->result.pending||w->result.main.counter!=target.counter||w->result.main.base!=target.base||w->result.main.first!=target.first||
    w->result.has_hof!=had_hof||w->result.has_journal!=had_journal||w->result.epoch!=epoch||!same(w->result.hof_sha,w->old_sha,32)||
    !same(w->selected_journal,w->journal,HJ_SIZE))return HT_ERR_CHANGED;
 return protect_after(o,w,&source,source_sha);
}
