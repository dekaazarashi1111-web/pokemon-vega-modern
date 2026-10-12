/* 新consumer接続の隔離ARM。全非owner RAMとSP/registerを各callで対照。 */
#define _POSIX_C_SOURCE 200809L
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <mgba/core/core.h>
#include <mgba/core/config.h>
#include "overlays/dex_owner/dex_owner.h"
#include DEX_CONSUMER_NATIVE
#define LIVE VEGA_DEX_OWNER_RAM
#define STACK 0x03007D00u
static struct mCore*c;static color_t video[240*160];
static uint8_t memory[262144],iwram[32768],expected[522],initial[522];
static unsigned cases,calls,api_calls,kind,argument;static uint64_t steps;
static void need(int v,const char*s){if(!v){fprintf(stderr,"consumer %s case=%u call=%u\n",s,cases,calls);exit(1);}}
static uint32_t reg(const char*n){int32_t v;need(c->readRegister(c,n,&v),"read register");return v;}
static void set(const char*n,uint32_t v){need(c->writeRegister(c,n,&v),"write register");}
static void put(uint32_t a,const uint8_t*b,unsigned n){for(unsigned i=0;i<n;i++)c->busWrite8(c,a+i,b[i]);}
static void get(uint32_t a,uint8_t*b,unsigned n){for(unsigned i=0;i<n;i++)b[i]=c->busRead8(c,a+i);}
static uint32_t pc(void){return(reg("pc")&~1u)-2;}
static void invoke(uint32_t address,uint32_t stop,unsigned sp,unsigned want)
{
 calls++;api_calls=0;get(0x02000000,memory,262144);get(0x03000000,iwram,32768);
 set("cpsr",0xDF);set("sp",sp);set("lr",0x08000001);
 for(unsigned i=0;i<12;i++){char n[8];snprintf(n,sizeof(n),"r%u",i);set(n,i?0x77000000+i:argument);}
 set("cpsr",0xFF);set("pc",address|1u);
 for(unsigned i=0;;i++){
  need(i<2000000,"bounded instructions");uint32_t at=pc();if(at==stop)break;
  if(at==(DEX_ENTRY_VegaDexSpeciesFlags&~1u)){
   api_calls++;need(kind==0&&reg("r0")==LIVE&&reg("r1")==522&&reg("r2")==argument&&reg("r3")==2&&(reg("sp")&7)==0,"raw SID species ABI aligned once");
  }
  if(at==(DEX_ENTRY_VegaDexOfficialCount&~1u)){
   api_calls++;need(kind==1&&reg("r0")==LIVE&&reg("r1")==522&&reg("r2")==argument&&(reg("sp")&7)==0,"official count ABI aligned once");
  }
  need(at!=0x08042988&&at!=0x08088A50&&at!=0x0810586C,"no lossy conversion or legacy bitmap path");
  need(at!=0x080DA9C0&&at!=0x080DB178&&at!=0x080DB230,"no Flash writer");
  c->step(c);steps++;
 }
 need(reg("r0")==want&&api_calls==1&&reg("sp")==sp,"return, single API call and exact SP");
 for(unsigned i=4;i<12;i++){char n[8];snprintf(n,sizeof(n),"r%u",i);need(reg(n)==0x77000000+i,"callee-saved registers");}
 for(unsigned i=0;i<262144;i++){uint32_t a=0x02000000+i;uint8_t v=a>=LIVE&&a<LIVE+522?expected[a-LIVE]:memory[i];need(c->busRead8(c,a)==v,"whole EWRAM expected owner only");}
 for(unsigned i=0;i<32768;i++){uint32_t a=0x03000000+i;if(a>=sp-512&&a<sp)continue;need(c->busRead8(c,a)==iwram[i],"whole IWRAM except bounded call stack");}
 cases++;printf("{\"case\":%u}\n",cases);fflush(stdout);
}
int main(int argc,char**argv)
{
 need(argc==2,"one candidate input");c=mCoreFind(argv[1]);need(c&&c->init(c),"init core");mCoreInitConfig(c,NULL);mCoreConfigSetDefaultValue(&c->config,"idleOptimization","ignore");need(mCoreLoadFile(c,argv[1]),"candidate load");c->setVideoBuffer(c,video,240);c->reset(c);
 need(VegaDexInitNew(initial,522)==0,"expected initialized owner");
 const unsigned sites[]={0x08012A5E,0x08012AB6,0x08012AD6,0x08012E96,0x08023912};
 const unsigned sids[]={0,1,129,481,253,255,649,650,1620,1669,1670,1671,65535};
 const unsigned owners[]=DEX_SAMPLE_OWNERS;
 for(unsigned w=0;w<5;w++)for(unsigned align=0;align<2;align++)for(unsigned test=0;test<14;test++){
  unsigned index=test==13?3:test;kind=0;argument=sids[index];
  for(unsigned i=0;i<262144;i++)c->busWrite8(c,0x02000000+i,(uint8_t)(i*7+13));
  memcpy(expected,initial,522);if(test==13)expected[4]^=1;
  put(LIVE,expected,522);uint8_t v=0;
  if(owners[index]&&test!=13)need(VegaDexAccess(expected,522,owners[index],2,&v)==0,"independent declared owner fixture");
  invoke(sites[w],sites[w]+14,STACK+4*align,v);
 }
 kind=1;const unsigned modes[]={0,1,2,3,255};
 for(unsigned align=0;align<2;align++)for(unsigned bag=0;bag<2;bag++)for(unsigned valid=0;valid<2;valid++)for(unsigned m=0;m<5;m++){
  for(unsigned i=0;i<262144;i++)c->busWrite8(c,0x02000000+i,(uint8_t)(bag?255:0));
  memcpy(expected,initial,522);uint8_t v;
  for(unsigned owner=1;owner<=1206;owner++)need(VegaDexAccess(expected,522,owner,3,&v)==0,"all owner fixture");
  if(!valid)expected[4]^=1;
  put(LIVE,expected,522);c->busWrite32(c,0x03005008,0x02000000);argument=modes[m];
  invoke(0x09131158,0x08000000,STACK+4*align,valid&&m<2?1025:0);
 }
 need(cases==180,"exact case accounting");
 printf("{\"status\":\"PASS_ISOLATED_ARM_BATTLE_SEEN_AND_OFFICIAL_COUNT\",\"cases\":%u,\"calls\":%u,\"seen_cases\":140,\"count_cases\":40,\"steps\":%llu,\"native_processes\":1,\"ewram_bytes_checked_per_call\":262144,\"iwram_bytes_checked_per_call\":32768,\"ordinary_battles\":0,\"ordinary_saves\":0,\"formal_save_changed\":false}\n",cases,calls,(unsigned long long)steps);fflush(stdout);mCoreConfigDeinit(&c->config);c->deinit(c);return 0;
}
