/* Candidate ARM scheduler with synthetic flash callbacks. No game boot,
 * source save file, real flash hardware, or story acceptance is claimed. */
#define _POSIX_C_SOURCE 200809L
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <mgba/core/core.h>
#include <mgba/core/config.h>
#include "overlays/dex_owner/dex_owner.h"
#include SCHEDULER_ENTRIES
#define LIVE 0x0203DB40u
#define CHUNKS 0x03005400u
#define SB1 0x02004000u
#define SB2 0x02008000u
#define PCBOX 0x02010000u
#define BUFFER 0x02020000u
#define STACK 0x03007D00u
#define COUNTER 0x030053E0u
#define FIRST 0x030053D0u
#define DAMAGED 0x030053DCu
static struct mCore *c;
static color_t video[240*160];
static uint8_t flash_bytes[32][4096],live[522],backup[14*4096];
static unsigned reads,erases,programs,stock_calls,checks,calls;
static uint64_t steps;
static int fail_after=-1,lie_after=-1;
static const uint16_t sizes[]={0xF24,0xF80,0xF80,0xF80,0xEC0,0xF80,0xF80,0xF80,0xF80,0xF80,0xF80,0xF80,0xF80,0x7D0};
static const uint16_t offsets[]={0,0,0xF80,0x1F00,0x2E80,0,0xF80,0x1F00,0x2E80,0x3E00,0x4D80,0x5D00,0x6C80,0x7C00};
static void need(int yes,const char *s){if(!yes){fprintf(stderr,"scheduler %s case=%u call=%u\n",s,checks,calls);exit(1);}}
static uint32_t reg(const char *n){int32_t v=0;need(c->readRegister(c,n,&v),"register read");return v;}
static void set(const char *n,uint32_t v){need(c->writeRegister(c,n,&v),"register write");}
static uint32_t r32(uint32_t a){return c->busRead32(c,a);}
static uint16_t r16(uint32_t a){return c->busRead16(c,a);}
static void w32(uint32_t a,uint32_t v){c->busWrite32(c,a,v);}
static void put(uint32_t a,const uint8_t *b,unsigned n){for(unsigned i=0;i<n;i++)c->busWrite8(c,a+i,b[i]);}
static void get(uint32_t a,uint8_t *b,unsigned n){for(unsigned i=0;i<n;i++)b[i]=c->busRead8(c,a+i);}
static uint16_t sum(uint32_t a,uint16_t n){uint32_t v=0;for(unsigned i=0;i<n;i+=4)v+=r32(a+i);return (uint16_t)(v+(v>>16));}
static void returned(uint32_t result){set("r0",result);set("pc",reg("lr"));}
static int callback(void)
{
 uint32_t pc=(reg("pc")&~1u)-2u,a=reg("r0"),b=reg("r1"),d=reg("r2");
 if(pc==0x080DB178u){need(a<32,"read sector");reads++;put(b,flash_bytes[a],4096);returned(0);return 1;}
 if(pc==0x080DB190u){returned(sum(a,b));return 1;}
 if(pc==0x08000100u){need(a<32,"erase sector");erases++;memset(flash_bytes[a],255,4096);returned(0);return 1;}
 if(pc==0x08000110u){need(a<32&&b<4096,"program sector byte");programs++;if(fail_after>=0&&(int)programs>=fail_after)returned(1);else{if(lie_after<0||(int)programs!=lie_after)flash_bytes[a][b]&=d;returned(0);}return 1;}
 if(pc==0x080DA9C0u){need(a<32,"try write");erases++;programs+=4096;get(b,flash_bytes[a],4096);returned(1);return 1;}
 if(pc==0x080DB1BCu||pc==0x0804BAB8u){returned(0);return 1;}
 if(pc==0x080DB230u){stock_calls++;need(a==2,"only e-reader stock delegation fixture");returned(0);return 1;}
 return 0;
}
static uint32_t call(uint32_t address,uint32_t a,uint32_t b)
{
 calls++;set("cpsr",0xDF);set("sp",STACK);set("lr",0x08000001);
 for(unsigned i=0;i<12;i++){char n[8];snprintf(n,sizeof(n),"r%u",i);set(n,i==0?a:i==1?b:0x77000000+i);}
 set("cpsr",0xFF);set("pc",address|1u);
 for(unsigned i=0;;i++){
  need(i<20000000,"bounded ARM instruction count");if((reg("pc")&~1u)==0x08000002u)break;
  if(!callback()){c->step(c);steps++;}
 }
 need(reg("sp")==STACK,"stack retained");for(unsigned i=4;i<12;i++){char n[8];snprintf(n,sizeof(n),"r%u",i);need(reg(n)==0x77000000+i,"callee saved register retained");}
 return reg("r0");
}
static void reset(void)
{
 for(unsigned i=0;i<0x40000;i++)c->busWrite8(c,0x02000000+i,0);
 for(unsigned i=0;i<0x8000;i++)c->busWrite8(c,0x03000000+i,0);
 memset(flash_bytes,255,sizeof(flash_bytes));
 w32(0x03005048,SB1);w32(0x0300504C,SB2);w32(0x03005050,PCBOX);w32(0x030053E4,BUFFER);w32(0x03007474,0x08000111);w32(0x03007480,0x08000101);
 for(unsigned i=0;i<0x3D40;i++)c->busWrite8(c,SB1+i,(uint8_t)i);
 for(unsigned i=0;i<0xF24;i++)c->busWrite8(c,SB2+i,(uint8_t)(i+31));
 for(unsigned i=0;i<0x83D0;i++)c->busWrite8(c,PCBOX+i,(uint8_t)(i+67));
 for(unsigned i=0;i<14;i++){w32(CHUNKS+8*i,(i==0?SB2:i<5?SB1:PCBOX)+offsets[i]);w32(CHUNKS+8*i+4,sizes[i]);}
 need(VegaDexInitNew(live,522)==0,"host fixture init");put(LIVE,live,522);
 reads=erases=programs=stock_calls=0;fail_after=lie_after=-1;
}
static void count(void){checks++;printf("{\"case\":%u}\n",checks);fflush(stdout);}
static void access(unsigned owner,unsigned mode){uint8_t value;get(LIVE,live,522);need(VegaDexAccess(live,522,owner,mode,&value)==0,"host fixture access");put(LIVE,live,522);}
static void saved(void){need(call(Stage61State_HandleSavingData,0,0)==0,"normal save result");need(r32(DAMAGED)==0,"normal save damage");}
static unsigned record(void){return 14*(r32(COUNTER)&1u)+(r16(FIRST)+13)%14;}
int main(int argc,char **argv)
{
 need(argc==2,"one private candidate");c=mCoreFind(argv[1]);need(c&&c->init(c),"core init");mCoreInitConfig(c,NULL);mCoreConfigSetDefaultValue(&c->config,"idleOptimization","ignore");need(mCoreLoadFile(c,argv[1]),"private candidate load");c->setVideoBuffer(c,video,240);c->reset(c);
 reset();access(1205,3);saved();need(r32(COUNTER)==1&&r16(FIRST)==1,"first rotation");get(LIVE,live,522);need(!memcmp(live,flash_bytes[record()]+0xDE6,522),"normal MDX persisted");count();
 uint8_t old[522];memcpy(old,live,522);access(128,2);saved();flash_bytes[record()][0xDF2]^=1;
 need(call(Stage61State_GetSaveValidStatus,CHUNKS,0)==255&&r32(COUNTER)==1,"CRC fallback");count();
 memset(live,0x77,522);put(LIVE,live,522);need(call(Stage61State_HandleLoadSector,0,CHUNKS)==1,"selected load");get(LIVE,live,522);need(!memcmp(live,old,522),"same selected MDX");count();
 flash_bytes[record()][0xDF2]^=1;need(call(Stage61State_GetSaveValidStatus,CHUNKS,0)==2,"both banks invalid");(void)call(Stage61State_HandleLoadSector,0,CHUNKS);get(LIVE,live,522);for(unsigned i=0;i<522;i++)need(live[i]==0,"failed load invalidated");count();
 for(unsigned blank=0;blank<2;blank++){reset();saved();memset(flash_bytes[record()]+0xDE6,blank?255:0,522);need(call(Stage61State_GetSaveValidStatus,CHUNKS,0)==1,"legacy selected");(void)call(Stage61State_HandleLoadSector,0,CHUNKS);get(LIVE,live,522);need(VegaDexValidate(live,522)==0&&live[10]==1,"legacy initialized after stock copy");count();}
 for(unsigned mode=0;mode<6;mode++){reset();saved();memcpy(backup,flash_bytes+14,sizeof(backup));c->busWrite8(c,LIVE,0);unsigned e=erases,p=programs,s=stock_calls;need(call(Stage61State_HandleSavingData,mode,0)==255,"invalid live result");need(e==erases&&p==programs&&s==stock_calls,"invalid live no callbacks");need((r32(DAMAGED)&0xFFFFC000u)==0&&!memcmp(backup,flash_bytes+14,sizeof(backup)),"valid source protected by mask");count();}
 reset();saved();access(1205,2);need(call(Stage61State_HandleReplaceSector,13,CHUNKS)==1,"prepare LinkFull");unsigned at=record();need(flash_bytes[at][0xFF8]==255,"signature uncommitted");count();
 unsigned p=programs;flash_bytes[at][0xDE6]^=1;need(call(Stage61State_CommitSignatureByte,14,CHUNKS)==255&&p==programs&&flash_bytes[at][0xFF8]==255,"tampered prepare cannot commit");count();
 w32(DAMAGED,0);need(call(Stage61State_HandleReplaceSector,13,CHUNKS)==1,"reprepare");need(call(Stage61State_CommitSignatureByte,14,CHUNKS)==1&&flash_bytes[at][0xFF8]==0x25,"signature last commit");count();
 reset();saved();uint8_t old_pc[0x7D0];at=record();memcpy(old_pc,flash_bytes[at],sizeof(old_pc));memcpy(old,flash_bytes[at]+0xDE6,522);access(1205,3);
 for(unsigned i=0;i<0x7D0;i++)c->busWrite8(c,PCBOX+0x7C00+i,0xE5);
 need(call(Stage61State_EnsureBackupGeneration,CHUNKS,0)==1&&r32(COUNTER)==1,"backup keeps selector");need(!memcmp(flash_bytes[at-14]+0xDE6,old,522),"backup exact old MDX");count();
 need(call(Stage61State_UpdateRecordOnly,CHUNKS,0)==1&&r32(COUNTER)==2,"record only commit");get(LIVE,live,522);need(!memcmp(flash_bytes[at-14],old_pc,sizeof(old_pc))&&!memcmp(flash_bytes[at-14]+0xDE6,live,522),"record only PC unchanged MDX current");count();
 for(unsigned f=0;f<2;f++){reset();saved();memcpy(backup,flash_bytes+14,sizeof(backup));access(1000,2);if(f==0)fail_after=programs+522;else lie_after=programs+0xDE7;need(call(Stage61State_HandleSavingData,0,0)==255&&r32(COUNTER)==1&&!memcmp(backup,flash_bytes+14,sizeof(backup)),"torn or lying write preserves source");count();}
 printf("{\"status\":\"PASS_ISOLATED_ARM_SCHEDULER_SYNTHETIC_FLASH\",\"cases\":%u,\"calls\":%u,\"steps\":%llu,\"native_processes\":1,\"game_boots\":0,\"ordinary_saves\":0,\"formal_save_changed\":false}\n",checks,calls,(unsigned long long)steps);fflush(stdout);mCoreConfigDeinit(&c->config);c->deinit(c);return 0;
}
