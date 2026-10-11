#define _POSIX_C_SOURCE 200809L
/* 現ROM allocatorの隔離試験。game boot、入力save、本番arena所有を主張しない。 */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <mgba/core/core.h>
#include <mgba/core/config.h>
#include "overlays/hof_journal/hof_heap.h"
_Static_assert(sizeof(HH_Plan)==40,"exact plan ABI");
#define ROOT 0x02000000u
#define LIMIT 0x1C000u
#define STACK 0x03007D00u
#define INIT 0x08002B81u
#define ALLOC 0x0800295Du
#define FREE 0x08002A09u
static struct mCore *c;
static color_t video[240*160];
static uint8_t heap[LIMIT],before[0x40000],ibefore[0x8000];
static uint32_t active_size;
static uint8_t arm_code[8192];
static unsigned arm_size,admission_calls;
#define ARM_CODE 0x02030000u
#define ARM_PLAN 0x0202F000u
static unsigned checks,calls,alloc_calls,rejected;
static uint64_t steps;
static void need(int yes,const char *why){if(!yes){fprintf(stderr,"heap %s case=%u call=%u\n",why,checks,calls);exit(1);}}
static uint32_t reg(const char *name){int32_t v=0;need(c->readRegister(c,name,&v),"register read");return (uint32_t)v;}
static void set(const char *name,uint32_t value){need(c->writeRegister(c,name,&value),"register write");}
static void get(uint32_t a,uint8_t *p,unsigned n){for(unsigned i=0;i<n;i++)p[i]=c->busRead8(c,a+i);}
static void fill(uint32_t a,unsigned n,uint8_t v){for(unsigned i=0;i<n;i++)c->busWrite8(c,a+i,v);}
static void prepare(uint32_t address,uint32_t a,uint32_t b)
{
 set("cpsr",0xDF);set("sp",STACK);set("lr",0x08000001u);
 for(unsigned i=0;i<12;i++){char n[8];snprintf(n,sizeof n,"r%u",i);set(n,i==0?a:i==1?b:0x77000000u+i);}
 set("cpsr",0xFF);set("pc",address|1u);
}
static uint32_t pc(void){return (reg("pc")&~1u)-2u;}
static uint32_t call4(uint32_t address,uint32_t a,uint32_t b,uint32_t d,uint32_t e)
{
 get(ROOT,before,sizeof before);get(0x03000000,ibefore,sizeof ibefore);prepare(address,a,b);set("r2",d);set("r3",e);calls++;if(address==ALLOC)alloc_calls++;
 for(unsigned n=0;;n++){need(n<2000000,"bounded actual allocator return");if(pc()==0x08000000u)break;need(reg("sp")>=STACK-1024&&reg("sp")<=STACK,"bounded dedicated call stack");c->step(c);steps++;}
 need(reg("sp")==STACK,"stack restored");
 for(unsigned i=4;i<12;i++){char name[8];snprintf(name,sizeof name,"r%u",i);need(reg(name)==0x77000000u+i,"callee saved register");}
 for(unsigned i=0;i<sizeof before;i++){int allowed=address==HH_ADMIT_ARM_ENTRY?(i>=0x2F000&&i<0x2F028):(i<active_size||(i>=0x20004&&i<0x20010));if(!allowed)need(c->busRead8(c,ROOT+i)==before[i],"nonowner EWRAM unchanged");}
 for(unsigned i=0;i<sizeof ibefore;i++)if(!(i>=STACK-0x03000000-1024&&i<STACK-0x03000000)&&!(address==INIT&&i>=0xA38&&i<0xA40))need(c->busRead8(c,0x03000000+i)==ibefore[i],"nonstack nonroot IWRAM unchanged");
 return reg("r0");
}
static uint32_t call(uint32_t address,uint32_t a,uint32_t b)
{ return call4(address,a,b,0x77000002u,0x77000003u); }
static void init(uint32_t size)
{
 active_size=size;fill(ROOT,0x40000,0x5A);fill(0x03000000,0x8000,0);for(unsigned i=0;i<arm_size;i++)c->busWrite8(c,ARM_CODE+i,arm_code[i]);(void)call(INIT,ROOT,size);
 need(c->busRead32(c,0x03000A38)==ROOT&&c->busRead32(c,0x03000A3C)==size,"real InitHeap root and size globals");
}
static int admit(uint32_t size,HH_Plan *out)
{
 get(ROOT,heap,size);int host=HH_Admit(heap,ROOT,size,out);
 fill(ARM_PLAN,40,0xA5);int32_t actual=(int32_t)call4(HH_ADMIT_ARM_ENTRY,ROOT,ROOT,size,ARM_PLAN);admission_calls++;
 uint8_t observed[40];get(ARM_PLAN,observed,sizeof observed);need(actual==host&&!memcmp(observed,out,sizeof observed),"compiled ARM admission agrees with all host plan bytes");return host;
}
static int owned(uint32_t size,uint32_t raw,HH_Plan *out){get(ROOT,heap,size);return HH_CheckOwned(heap,ROOT,size,raw,out);}
static uint32_t allocate(uint32_t size,HH_Plan *expected)
{
 need(admit(size,expected)==HH_OK,"whole chain admits");uint32_t previous_split=c->busRead32(c,0x0202000C);uint32_t raw=call(ALLOC,ROOT,13359);HH_Plan actual;
 need(raw==expected->raw,"actual first fit raw matches plan");
 need(c->busRead32(c,0x02020004)==ROOT&&c->busRead32(c,0x02020008)==expected->block&&c->busRead32(c,0x0202000C)==(expected->split_block?expected->split_block:previous_split),"exact allocator scratch contract");
 if(expected->split_block){need(c->busRead32(c,expected->split_block+4)==expected->split_payload,"exact split remainder");}
 need(owned(size,raw,&actual)==HH_OK,"actual result owned by whole valid chain");
 need(actual.arena==expected->arena&&actual.payload==expected->allocated,"real split or whole payload predicted");
 need((actual.arena&7u)==0&&actual.arena>=raw&&actual.arena+13352<=raw+actual.payload,"complete aligned arena fits");
 need(c->busRead16(c,ROOT)==1&&c->busRead32(c,ROOT+8)==ROOT,"root prev retains self");return raw;
}
static void released(uint32_t size,uint32_t raw)
{
 uint32_t scratch[3];for(unsigned i=0;i<3;i++)scratch[i]=c->busRead32(c,0x02020004+4*i);
 (void)call(FREE,ROOT,raw);for(unsigned i=0;i<3;i++)need(c->busRead32(c,0x02020004+4*i)==scratch[i],"Free leaves allocator scratch unchanged");HH_Plan p;need(admit(size,&p)==HH_OK&&p.blocks==1&&p.free_bytes==size-16,"real Free coalesces complete heap");
}
int main(int argc,char **argv)
{
 need(argc==3,"private ROM and source-generated ARM admission");FILE *input=fopen(argv[2],"rb");need(input!=NULL,"ARM source image open");arm_size=(unsigned)fread(arm_code,1,sizeof arm_code,input);need(arm_size>0&&arm_size<sizeof arm_code&&fgetc(input)==EOF&&!ferror(input),"bounded ARM source image");fclose(input);c=mCoreFind(argv[1]);need(c&&c->init(c),"core init");mCoreInitConfig(c,NULL);mCoreConfigSetDefaultValue(&c->config,"idleOptimization","ignore");need(mCoreLoadFile(c,argv[1]),"private ROM load");c->setVideoBuffer(c,video,240);c->reset(c);
 HH_Plan p;uint32_t raw;
 init(LIMIT);raw=allocate(LIMIT,&p);need(p.split_block!=0&&p.allocated==13360,"ordinary split");released(LIMIT,raw);checks++;
 init(LIMIT);uint32_t small=call(ALLOC,ROOT,4);need(small==ROOT+16,"small prefix allocation");raw=allocate(LIMIT,&p);need((raw&7u)==4&&p.arena==raw+4,"four byte raw needs eight byte alignment");(void)call(FREE,ROOT,small);released(LIMIT,raw);checks++;
 for(unsigned tail=0;tail<=32;tail+=4){uint32_t size=16+13360+tail;init(size);raw=allocate(size,&p);need(p.allocated==(tail<32?13360+tail:13360),"actual split threshold31");released(size,raw);checks++;}
 init(32000);uint32_t a=call(ALLOC,ROOT,12000);(void)call(ALLOC,ROOT,12000);(void)call(FREE,ROOT,a);unsigned count=alloc_calls;need(admit(32000,&p)==HH_ERR_OOM,"fragmentation rejects before allocator assert");need(alloc_calls==count,"no actual OOM allocation");rejected++;checks++;
 init(13372);count=alloc_calls;need(admit(13372,&p)==HH_ERR_OOM&&alloc_calls==count,"four byte short rejects without call");rejected++;checks++;
 init(LIMIT);raw=allocate(LIMIT,&p);uint32_t separator=call(ALLOC,ROOT,4);(void)call(FREE,ROOT,raw);need(admit(LIMIT,&p)==HH_OK&&p.raw==raw,"normal first fit before later corruption");uint32_t second=separator+4;c->busWrite16(c,second+2,0);count=alloc_calls;need(admit(LIMIT,&p)==HH_ERR_CHAIN&&alloc_calls==count,"corruption after candidate not ignored");rejected++;checks++;
 /* 退避入口はMallocInitより前にheap先頭53300byteを上書きする。 */
 init(LIMIT);raw=allocate(LIMIT,&p);fill(p.arena,13352,0xA5);
 c->busWrite32(c,0x0300504C,0x02021000);c->busWrite32(c,0x03005048,0x02022000);c->busWrite32(c,0x03005050,0x02026000);
 fill(0x02021000,0xF24,0x11);fill(0x02022000,0x3D40,0x22);fill(0x02026000,0x83D0,0x33);
 prepare(0x0804B85D,0,0);unsigned copies=0;
 for(unsigned n=0;;n++){
  need(n<2000000,"bounded pre-reset relocation prefix");uint32_t at=pc();if(at==0x0804B810u)break;
  need(at!=0x08002B80u,"not yet MallocInit");
  if(at==0x081C9D98u){const uint32_t dest[]={ROOT,ROOT+0xF24,ROOT+0x4C64};const uint32_t srcs[]={0x02021000,0x02022000,0x02026000};const uint32_t lens[]={0xF24,0x3D40,0x83D0};need(copies<3&&reg("r0")==dest[copies]&&reg("r1")==srcs[copies]&&reg("r2")==lens[copies],"exact pre-reset copy extents");copies++;}
  c->step(c);steps++;
 }
 need(copies==3,"three actual memcpy calls before reset");unsigned changed=0;for(unsigned i=0;i<13352;i++)changed+=c->busRead8(c,p.arena+i)!=0xA5;
 need(changed==13352&&owned(LIMIT,raw,&p)==HH_ERR_CHAIN,"live arena destroyed before heap reset");checks++;
 printf("{\"status\":\"PASS_ACTUAL_ROM_HEAP_ADMISSION_AND_RELOCATION_HAZARD\",\"cases\":%u,\"allocator_calls\":%u,\"arm_admission_calls\":%u,\"calls\":%u,\"steps\":%llu,\"preflight_rejections_without_alloc\":%u,\"relocation_copy_calls\":3,\"relocation_overwrite_bytes\":53300,\"arena_overwritten_before_heap_reset\":13352,\"native_processes\":1,\"game_boots\":0,\"real_saves\":0,\"all_save_entries_heap_ready\":false,\"runtime_lease_enabled\":false,\"formal_save_changed\":false}\n",checks,alloc_calls,admission_calls,calls,(unsigned long long)steps,rejected);fflush(stdout);mCoreConfigDeinit(&c->config);c->deinit(c);return 0;
}
