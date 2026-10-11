/* 新fallback wrapper、実MDX/台帳validator、synthetic Flash読取。保存callbackなし。 */
#include <mgba/internal/gba/gba.h>
#include "overlays/save_migration/save_migration.h"
static uint8_t fq_iwram[32768],fq_before_flash[131072],fq_ledger[2048];
static unsigned fq_status,fq_global,fq_type,fq_old_calls,fq_reads,fq_validations;
static uint32_t fq_call(unsigned sp)
{
 get(0x02000000,ram_before,262144);get(0x03000000,fq_iwram,32768);memcpy(fq_before_flash,flash_bytes,131072);calls++;
 set("cpsr",0xDF);set("sp",sp);set("lr",0x08000001);
 for(unsigned i=0;i<12;i++){char n[8];snprintf(n,sizeof(n),"r%u",i);set(n,i?0x77000000u+i:fq_type);}set("cpsr",0xFF);set("pc",FALLBACK_ENTRY);
 for(unsigned i=0;;i++){
  need(i<2000000,"bounded fallback ARM");unsigned pc=(reg("pc")&~1u)-2;
  if(pc==0x08000000)break;
  if(pc==FALLBACK_PREVIOUS_LOAD-1){need(reg("r0")==fq_type,"one unchanged prior load argument");fq_old_calls++;c->busWrite16(c,0x030053F0,fq_global);returned(fq_status);continue;}
  if(pc==0x081C2A54){need(reg("r0")==31&&reg("r1")==0x64&&reg("r2")==0x020399B0&&reg("r3")==0xF9C,"only bounded durable ledger read");fq_reads++;put(0x020399B0,flash_bytes[31]+0x64,0xF9C);returned(0);continue;}
  if(pc==0x092D12E0){need(reg("r0")==0x020399B0&&reg("r1")==2048,"non-side-effect pointer and size");fq_validations++;}
  need(pc!=0x080DA9C0&&pc!=0x080DB178&&pc!=0x080C6480&&pc!=0x080DB230&&pc!=0x092D28D8&&pc!=0x09378DAC,"no save/reselection/finalize/ensure/init");c->step(c);steps++;
 }
 need(reg("sp")==sp,"original SP");for(unsigned i=4;i<12;i++){char n[8];snprintf(n,sizeof(n),"r%u",i);need(reg(n)==0x77000000u+i,"all callee registers retained");}
 for(unsigned i=0;i<262144;i++){unsigned a=0x02000000u+i;if((a>=0x020399B0&&a<0x0203A94C)||(a>=LIVE&&a<LIVE+522)||(a>=0x0203D000&&a<0x0203D800))continue;need(c->busRead8(c,a)==ram_before[i],"every other EWRAM byte retained including research volatile state");}
 for(unsigned i=0;i<32768;i++){unsigned a=0x03000000u+i;if((a>=sp-256&&a<sp)||(a>=0x030053F0&&a<0x030053F2))continue;need(c->busRead8(c,a)==fq_iwram[i],"all non-stack IWRAM retained");}
 need(!memcmp(fq_before_flash,flash_bytes,131072)&&fq_old_calls==1,"all Flash unchanged and prior load once");return reg("r0");
}
static void fq_reset(unsigned kind)
{
 reset();memset(flash_bytes[31],0,4096);fq_old_calls=fq_reads=fq_validations=0;fq_status=fq_global=255;fq_type=0;
 VegaModernSaveData q;VegaSaveInitNew(&q,0);q.generation=77;VegaSaveFinalize(&q);
 if(kind==1)memset(&q,0,2048);if(kind==2)memset(&q,255,2048);if(kind==3)q.checksum^=1;if(kind==4)q.version=1;if(kind==5)q.reserved[0]=1;
 if(kind==6)q.factory.marker=1;if(kind==7)q.factory.snapshot_valid=1;if(kind==8)q.factory.reward_pending=1;if(kind==9)q.pending_encounter.valid=1;if(kind==10)q.research_economy.pending_kind=1;if(kind==11)q.raid_in_progress[15]=1;if(kind==12)q.raid_retry_pending[0]=1;
 if(kind>=6)VegaSaveFinalize(&q);memcpy(flash_bytes[31]+0x64,&q,2048);
 VegaSaveInitNew(&q,0);q.generation=88;VegaSaveFinalize(&q);put(0x0203D000,(uint8_t*)&q,2048);memcpy(fq_ledger,&q,2048);
}
int main(int argc,char**argv)
{
 need(argc==2,"one private candidate");c=mCoreFind(argv[1]);need(c&&c->init(c),"init");mCoreInitConfig(c,NULL);mCoreConfigSetDefaultValue(&c->config,"idleOptimization","ignore");need(mCoreLoadFile(c,argv[1]),"load");c->setVideoBuffer(c,video,240);c->reset(c);
 const unsigned globals[]={0,1,2,4,255},types[]={0,1,2,3,4,5,6,255},statuses[]={0,1,2,4,254,255};
 for(unsigned a=0;a<2;a++)for(unsigned t=0;t<8;t++)for(unsigned s=0;s<6;s++)for(unsigned g=0;g<5;g++){
  fq_reset(0);fq_type=types[t];fq_status=statuses[s];fq_global=globals[g];unsigned active=fq_type!=3&&fq_status==255&&fq_global==255;
  need(fq_call(STACK+4*a)==fq_status&&r16(0x030053F0)==fq_global,"status255 not promoted and unrelated statuses unchanged");uint8_t got[2048];get(0x0203D000,got,2048);need(!memcmp(got,active?flash_bytes[31]+0x64:fq_ledger,2048)&&fq_reads==active&&fq_validations==active,"durable ledger wins over stale valid RAM only exact fallback");checks++;
 }
 for(unsigned a=0;a<2;a++)for(unsigned k=1;k<=14;k++){
  fq_reset(k<=12?k:0);if(k==13)c->busWrite8(c,LIVE+4,(uint8_t)(c->busRead8(c,LIVE+4)^1));if(k==14)c->busWrite8(c,LIVE,0);
  need(fq_call(STACK+4*a)==255&&r16(0x030053F0)==2,"corrupt empty pending v1 noauthority blocks Continue");uint8_t got[2048];get(0x0203D000,got,2048);need(!memcmp(got,fq_ledger,2048),"invalid durable never published or initialized");for(unsigned i=0;i<522;i++)need(c->busRead8(c,LIVE+i)==0,"MDX invalidated on rejection");checks++;
 }
 need(checks==508,"480 positive-routing and28 negatives");printf("{\"status\":\"PASS_ARM_FALLBACK_IDLE_LEDGER_RESTORE\",\"cases\":%u,\"calls\":%u,\"steps\":%llu,\"native_processes\":1,\"old_native_reruns\":0,\"flash_writes\":0}\n",checks,calls,(unsigned long long)steps);fflush(stdout);mCoreConfigDeinit(&c->config);c->deinit(c);return 0;
}
