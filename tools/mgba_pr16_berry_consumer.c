#define _POSIX_C_SOURCE 200809L
/* 現Task/param実行と、明示的なRAMロードchild fixture。実リンク転送や実Saveを受入しない。 */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <mgba/core/core.h>
#include <mgba/core/config.h>
#define START 0x086C48ACu
#define END 0x086C7D38u
#define HIT 0x086C51BFu
#define LOAD 0x02000000u
#define STACK 0x03007C00u
#define STOP 0x03007E00u
static struct mCore *c;
static color_t video[240*160];
static uint8_t ebefore[0x40000],ibefore[0x8000];
static unsigned init_cases,master_cases;
static void need(int ok,const char *message){if(!ok){fprintf(stderr,"berry-consumer %s init=%u master=%u\n",message,init_cases,master_cases);exit(1);}}
static uint32_t reg(const char *name){int32_t v=0;need(c->readRegister(c,name,&v),"register read");return (uint32_t)v;}
static void set(const char *name,uint32_t v){need(c->writeRegister(c,name,&v),"register write");}
static uint32_t pc(void){return (reg("pc")&~1u)-((reg("cpsr")&32u)?2u:4u);}
static uint32_t rn(unsigned n){char name[8];snprintf(name,sizeof name,"r%u",n);return reg(name);}
static uint8_t r8(uint32_t a){return c->busRead8(c,a);}
static uint16_t r16(uint32_t a){return c->busRead16(c,a);}
static uint32_t r32(uint32_t a){return c->busRead32(c,a);}
static void w8(uint32_t a,uint8_t v){c->busWrite8(c,a,v);}
static void w16(uint32_t a,uint16_t v){c->busWrite16(c,a,v);}
static void w32(uint32_t a,uint32_t v){c->busWrite32(c,a,v);}
static void fill(uint32_t a,unsigned n,uint8_t v){for(unsigned i=0;i<n;i++)w8(a+i,v);}
static int in(uint32_t a,uint32_t start,uint32_t end){return a>=start&&a<end;}
static void clean(void){c->reset(c);fill(0x02000000u,0x40000u,0);fill(0x03000000u,0x8000u,0);c->setKeys(c,0);}
static void enter(uint32_t address,int thumb){set("cpsr",thumb?0xFFu:0xDFu);set("sp",STACK);set("lr",STOP|1u);set("pc",address|(thumb?1u:0u));need(pc()==address,"exact entry pipeline");}
static void snapshot(void){for(unsigned i=0;i<sizeof ebefore;i++)ebefore[i]=r8(0x02000000u+i);for(unsigned i=0;i<sizeof ibefore;i++)ibefore[i]=r8(0x03000000u+i);}
static int owned(uint32_t a,uint32_t task,int init){return in(a,PARAM,PARAM+76u)||in(a,STACK-128u,STACK+4u)||(init&&(in(a,MB_START,MB_START+4u)||in(a,MB_SIZE,MB_SIZE+4u)||in(a,task+8u,task+12u)));}
static void unchanged(uint32_t task,int init){
 for(unsigned i=0;i<sizeof ebefore;i++){uint32_t a=0x02000000u+i;if(!owned(a,task,init))need(r8(a)==ebefore[i],"nonowned EWRAM unchanged");}
 for(unsigned i=0;i<sizeof ibefore;i++){uint32_t a=0x03000000u+i;if(!owned(a,task,init))need(r8(a)==ibefore[i],"nonowned IWRAM unchanged");}
 need(reg("sp")==STACK,"stack restored");
}
static unsigned run_host(int init){
 unsigned calls=0;
 for(unsigned step=0;;step++){
  need(step<5000,"finite host budget");uint32_t at=pc();if(at==STOP)break;
  need((init&&in(at,TASK_START,TASK_END))||(!init&&in(at,MASTER_START,MASTER_END))||in(at,INIT_START,INIT_END),"host exact function scope");
  need(reg("cpsr")&32u,"host Thumb state");if(at==INIT_START){calls++;need(rn(0)==PARAM,"actual Init argument");}
  c->step(c);
 }
 return calls;
}
static void init_owner(unsigned id){
 clean();uint32_t task=TASKS+40u*id;w16(task+8u,4u);w16(task+10u,0xFFFFu);
 fill(PARAM,76u,0x5Au);w32(MB_START,0x11111111u);w32(MB_SIZE,0x22222222u);
 enter(TASK_START,1);set("r0",id);snapshot();need(run_host(1)==1,"one actual Init call");
 need(r32(MB_START)==START&&r32(MB_SIZE)==END-START&&r32(PARAM+0x28u)==START,"actual task asset start/end binding");
 need(r8(PARAM+0x4Bu)==0&&r8(PARAM+0x18u)==0&&r8(PARAM+0x1Eu)==0&&r8(PARAM+0x4Au)==15,"actual initialized param");
 need(r16(task+8u)==5&&r16(task+10u)==0,"actual task state and timer");unchanged(task,1);init_cases++;
}
static void master(int length,int speed,int probe,int clients,int wait){
 fill(PARAM,76u,0);w8(PARAM+0x18u,(uint8_t)probe);w8(PARAM+0x1Eu,(uint8_t)clients);w8(PARAM+0x4Au,(uint8_t)wait);
 w32(PARAM+0x20u,0x11111111u);w32(PARAM+0x24u,0x22222222u);w32(STACK,(uint32_t)speed);
 enter(MASTER_START,1);set("r0",PARAM);set("r1",r32(MB_START)+192u);set("r2",(uint32_t)length);set("r3",4u);snapshot();
 unsigned calls=run_host(0);int early=probe||!clients||wait;int rounded=(length+15)&~15;int accepted=!early&&rounded>=256&&rounded<=262144;
 need(calls==(accepted?0u:1u),"actual param acceptance/reset path");
 need(r32(PARAM+0x20u)==(early?0x11111111u:START+192u),"actual partial source store");
 need(r32(PARAM+0x24u)==(accepted?START+192u+(unsigned)rounded:0x22222222u),"actual rounded end store");
 need(r8(PARAM+0x18u)==(accepted?0xD0u:0u)&&r8(PARAM+0x4Au)==(accepted?0u:15u),"actual param control fields");
 if(accepted){int i=speed<0?((4<<3)|(3-speed)):speed==0?(0x38|4):((4<<3)|(speed-1));need(r8(PARAM+0x1Cu)==(((i&0x3F)<<1)|0x81),"actual palette modes");}
 unchanged(0,0);master_cases++;
}
static void child(unsigned scenario){
 clean();for(unsigned i=0;i<END-START;i++)w8(LOAD+i,r8(START+i));
 for(unsigned i=0;i<END-START;i++)need(r8(LOAD+i)==r8(START+i),"full mapped fixture byte identity");
 for(unsigned i=0;i<13;i++){char name[8];snprintf(name,sizeof name,"r%u",i);set(name,0);}
 enter(LOAD,0);c->setKeys(c,scenario?1u:0u);
 unsigned mask=0,steps=0,bl_count=0;uint32_t stop=0;int target_ok=1,escaped=0;
 for(;steps<1500000u;steps++){
  uint32_t at=pc();
  if(!(in(at,LOAD,LOAD+END-START)||in(at,0x03000000u,0x03008000u)||at<0x4000u)){escaped=1;stop=at;break;}
  if((reg("cpsr")&32u)&&in(at,LOAD+(HIT-START)-1u,LOAD+(HIT-START)+5u)){
   unsigned offset=at-(LOAD+(HIT-START)-1u);need(offset%2u==0,"aligned target fetch");
   unsigned index=offset/2u;need(index<3u,"finite target instruction set");
   need(r16(at)==r16(START+(at-LOAD)),"mapped original bytes unchanged at fetch");
   if(index==0){need((r16(at)&0xF800u)==0xF000u,"actual BL first half");}
   if(index==1){need((r16(at)&0xF800u)==0xF800u,"actual BL second half");}
   c->step(c);mask|=1u<<index;
   if(index==1){bl_count++;if(pc()!=LOAD+BL_REL||reg("lr")!=((at+2u)|1u))target_ok=0;}
   if(mask==7u){steps++;stop=pc();break;}
  }else c->step(c);
 }
 if(!steps)steps=1;
 if(scenario)printf(",");
 printf("{\"case\":%u,\"fetch_mask\":%u,\"steps\":%u,\"mapped_original_bytes_unchanged_at_fetch\":true,\"entry_was_bundle_header\":true,\"bl_target_and_link_verified\":%s,\"bl_count\":%u,\"escaped_fixture_scope\":%s,\"stop_pc\":%u,\"keys\":%u}",scenario,mask,steps,(bl_count&&target_ok)?"true":"false",bl_count,escaped?"true":"false",stop,scenario?1u:0u);
}
int main(int argc,char **argv){
 need(argc==2,"one private candidate input");c=mCoreFind(argv[1]);need(c&&c->init(c),"core init");mCoreInitConfig(c,NULL);mCoreConfigSetDefaultValue(&c->config,"idleOptimization","ignore");need(mCoreLoadFile(c,argv[1]),"candidate load");c->setVideoBuffer(c,video,240);
 init_owner(0);init_owner(7);init_owner(15);
 const int lengths[]={-1,0,240,241,256,(int)(END-START-192u),262144,262145};
 for(unsigned i=0;i<8;i++)master(lengths[i],1,0,2,0);
 master((int)(END-START-192u),-4,0,2,0);master((int)(END-START-192u),0,0,2,0);
 master((int)(END-START-192u),1,1,2,0);master((int)(END-START-192u),1,0,0,0);master((int)(END-START-192u),1,0,2,1);
 need(init_cases==3&&master_cases==13,"complete host fixture set");
 printf("{\"host_owner_verified\":true,\"host_init_cases\":3,\"host_master_cases\":13,\"nonowned_host_ram_unchanged\":true,\"rom_writes\":0,\"real_saves\":0,\"native_processes\":1,\"children\":[");
 child(0);child(1);printf("],\"natural_multiboot_transfer_proven\":false,\"donor_safe_bytes\":0}\n");fflush(stdout);mCoreConfigDeinit(&c->config);c->deinit(c);return 0;
}
