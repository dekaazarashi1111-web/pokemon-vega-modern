/* 新規load/newgame接続だけの隔離ARM。QOL結果fixtureと実CFRU wipeを分離。 */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <mgba/core/core.h>
#include <mgba/core/config.h>
#include "overlays/dex_owner/dex_owner.h"
#include DEX_LIFECYCLE_ENTRIES
#define LIVE 0x0203DB40u
#define STACK 0x03007D00u
static struct mCore*c;static color_t video[240*160];
static uint8_t memory[262144],iwram[32768],loaded[522],initial[522];
static unsigned checks,calls,qol_calls,expected_type,qol_status,install_live,init_calls,wipe_calls;
static uint64_t steps;
static void need(int v,const char*s){if(!v){fprintf(stderr,"lifecycle %s case=%u call=%u\n",s,checks,calls);exit(1);}}
static uint32_t reg(const char*n){int32_t v;need(c->readRegister(c,n,&v),"read register");return v;}
static void set(const char*n,uint32_t v){need(c->writeRegister(c,n,&v),"write register");}
static void put(uint32_t a,const uint8_t*b,unsigned n){for(unsigned i=0;i<n;i++)c->busWrite8(c,a+i,b[i]);}
static void get(uint32_t a,uint8_t*b,unsigned n){for(unsigned i=0;i<n;i++)b[i]=c->busRead8(c,a+i);}
static uint32_t current(void){return(reg("pc")&~1u)-2;}
static void done(uint32_t status){set("r0",status);set("pc",reg("lr"));}
static void start(uint32_t address,unsigned arg,unsigned sp)
{
 calls++;qol_calls=init_calls=wipe_calls=0;get(0x03000000,iwram,32768);
 set("cpsr",0xDF);set("sp",sp);set("lr",0x08000001);
 for(unsigned i=0;i<12;i++){char n[8];snprintf(n,sizeof(n),"r%u",i);set(n,i?0x77000000+i:arg);}
 set("cpsr",0xFF);set("pc",address|1u);
}
static void execute(uint32_t stop,int newgame)
{
 for(unsigned i=0;;i++){
  need(i<2000000,"bounded instructions");uint32_t pc=current();if(pc==stop)return;
  if(pc==0x09377694u){
   qol_calls++;c->busWrite16(c,0x030053F0,qol_status);need(reg("r0")==expected_type,"QOL receives exact type");
   if(expected_type!=3){for(unsigned j=0;j<522;j++)need(c->busRead8(c,LIVE+j)==0,"stale valid cleared before QOL");if(install_live)put(LIVE,loaded,522);}
   done(qol_status);continue;
  }
  if(pc==(DEX_ENTRY_VegaDexInitNew&~1u)){init_calls++;need(newgame&&reg("r0")==LIVE&&reg("r1")==522&&(reg("sp")&7)==0,"one aligned actual InitNew ABI");}
  if(pc==0x0912818Cu){wipe_calls++;need(newgame,"actual CFRU wipe only in newgame");}
  /* どのflash入口にも到達しない。 */
  need(pc!=0x080DA9C0u&&pc!=0x080DB178u&&pc!=0x080DB230u,"no flash or save callback");
  c->step(c);steps++;
 }
}
static void registers(unsigned sp,int newgame)
{
 need(reg("sp")==sp,"exact SP retained");
 for(unsigned i=0;i<32768;i++){uint32_t a=0x03000000+i;if((a>=STACK-512&&a<STACK+4)||(a>=0x030053F0&&a<0x030053F2))continue;need(c->busRead8(c,a)==iwram[i],"IWRAM non-owner and upper stack sentinel retained");}
 for(unsigned i=4;i<12;i++){char n[8];snprintf(n,sizeof(n),"r%u",i);unsigned want=0x77000000+i;if(newgame&&i==6)want=0x77000008;need(reg(n)==want,"callee-saved register ABI");}
}
static void count(void){checks++;printf("{\"case\":%u}\n",checks);fflush(stdout);}
int main(int argc,char**argv)
{
 need(argc==2,"one candidate input");c=mCoreFind(argv[1]);need(c&&c->init(c),"init core");mCoreInitConfig(c,NULL);mCoreConfigSetDefaultValue(&c->config,"idleOptimization","ignore");need(mCoreLoadFile(c,argv[1]),"load candidate");c->setVideoBuffer(c,video,240);c->reset(c);
 need(VegaDexInitNew(initial,522)==0,"expected new-game bytes");memcpy(loaded,initial,522);uint8_t v;need(VegaDexAccess(loaded,522,1205,3,&v)==0,"high-owner fixture");
 for(unsigned type=0;type<5;type++)for(unsigned status=0;status<5;status++)for(unsigned install=0;install<2;install++){
  static const unsigned statuses[]={0,1,2,4,255};for(unsigned i=0;i<262144;i++)c->busWrite8(c,0x02000000+i,(uint8_t)(i*7+13));put(LIVE,loaded,522);get(0x02000000,memory,262144);
  expected_type=type;qol_status=statuses[status];install_live=install;start(VegaDexPostQolLoad,type,STACK);execute(0x08000000,0);registers(STACK,0);
  need(c->busRead16(c,0x030053F0)==((type!=3&&(qol_status==1||qol_status==255)&&!install)?2:qol_status),"global status prevents invalid Continue and retains fallback");
  unsigned want=type==3?qol_status:qol_status==1?(install?1:255):qol_status;
  need(reg("r0")==want&&qol_calls==1&&!init_calls&&!wipe_calls,"exact status and one QOL call");
  for(unsigned i=0;i<262144;i++){uint32_t a=0x02000000+i;uint8_t want_byte=memory[i];if(a>=LIVE&&a<LIVE+522&&type!=3&&!((want==1||want==255)&&install))want_byte=0;need(c->busRead8(c,a)==want_byte,"entire EWRAM only intended MDX changes");}count();
 }
 for(unsigned align=0;align<2;align++){
  unsigned sp=STACK+align*4;
  for(unsigned i=0;i<262144;i++)c->busWrite8(c,0x02000000+i,(uint8_t)(i*5+29));get(0x02000000,memory,262144);
  for(unsigned i=0;i<128;i++)c->busWrite8(c,sp-96+i,0xA5);
  start(0x08054324,0,sp);execute(0x0805432C,1);registers(sp-28,1);
  need(init_calls==1&&wipe_calls==1&&!qol_calls&&reg("r0")==0x0805432D,"actual root wipe-init-tail order");
  need(c->busRead32(c,sp-20)==0x77000008&&c->busRead32(c,sp-16)==0x77000004&&c->busRead32(c,sp-12)==0x77000005&&c->busRead32(c,sp-8)==0x77000006&&c->busRead32(c,sp-4)==0x08000001,"original 28byte frame retained");
  for(unsigned i=0;i<262144;i++){uint32_t a=0x02000000+i;uint8_t b=memory[i];if(a>=0x0203B0E8&&a<0x0203DF8C)b=0;if(a>=LIVE&&a<LIVE+522)b=initial[a-LIVE];need(c->busRead8(c,a)==b,"actual wipe owner plus initialized MDX only");}count();
 }
 printf("{\"status\":\"PASS_ISOLATED_ARM_LOAD_NEWGAME_BOUNDARIES\",\"cases\":%u,\"load_cases\":50,\"newgame_root_cases\":2,\"calls\":%u,\"steps\":%llu,\"native_processes\":1,\"ewram_bytes_checked_per_call\":262144,\"iwram_bytes_checked_per_call\":32768,\"ordinary_game_boots\":0,\"ordinary_saves\":0,\"formal_save_changed\":false}\n",checks,calls,(unsigned long long)steps);fflush(stdout);mCoreConfigDeinit(&c->config);c->deinit(c);return 0;
}
