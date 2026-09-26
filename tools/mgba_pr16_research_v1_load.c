/* 通常cold boot/ContinueからV1を読む。RAM ledger/PC/戻り値は注入しない。
 * 入力Flash fixtureは起動前に独立生成し、観測中7 API host-writeを禁止。
 * 拒否例はload adapter戻り境界まで。拒否後メニューUI全体の受入ではない。 */
#include <mgba/internal/arm/arm.h>
#ifndef VL_ROM
#error "bind candidate and fixture SHA in generated source"
#endif
static unsigned vl_root,vl_research,vl_mirage,vl_qol,vl_saves,vl_phases[3],vl_native_returns,vl_native_result;
static unsigned vl_root_lr,vl_root_sp,vl_research_lr,vl_research_sp,vl_result,vl_root_result;
static unsigned vl_type,vl_counter_at_save,vl_available_at_save,vl_research_done,vl_root_done;
static uint64_t vl_steps;
static void vl_observe(struct mCore*c){
 const struct ARMCore*cpu=c->cpu;
 if(!(cpu->cpsr.packed&32))return;
 unsigned pc=((unsigned)cpu->gprs[15]&~1U)-2U,sp=(unsigned)cpu->gprs[13],r0=(unsigned)cpu->gprs[0];
 if(pc==0x080DB4E4U){si_need(++vl_root==1,"one ordinary load root");vl_root_lr=(unsigned)cpu->gprs[14]&~1U;vl_root_sp=sp;vl_type=r0;}
 if(pc==0x093BDF20U){si_need(++vl_research==1&&vl_root==1,"root reaches production research adapter");vl_research_lr=(unsigned)cpu->gprs[14]&~1U;vl_research_sp=sp;}
 if(pc==0x093910ECU)++vl_mirage;
 if(pc==0x09377694U)++vl_qol;
 if(pc==0x09377660U){++vl_saves;vl_counter_at_save=read32(c,SI_COUNTER);vl_available_at_save=read32(c,0x03005044U);}
 if(pc==0x093BF630U){si_need(r0<3,"phase bound");++vl_phases[r0];}
 if(pc==0x0937767AU){++vl_native_returns;vl_native_result=r0;}
 if(vl_research&&!vl_research_done&&pc==vl_research_lr&&sp==vl_research_sp){vl_research_done=1;vl_result=r0;}
 if(vl_root&&!vl_root_done&&pc==vl_root_lr&&sp==vl_root_sp){vl_root_done=1;vl_root_result=r0;}
}
static void vl_frames(struct mCore*c,unsigned keys,unsigned frames){
 unsigned start=c->frameCounter(c);c->setKeys(c,keys);
 while(c->frameCounter(c)-start<frames&&!vl_root_done){
  vl_observe(c);if(vl_root_done)break;
  si_need(++vl_steps<400000000ULL,"bounded cold boot instruction count");c->step(c);
 }
}
static struct mCore*vl_open(const char*rom,const char*save){
 struct mCore*c=qol_open(rom,save);++si_cores;qol_log_core=c;c->setVideoBuffer(c,si_video,240);si_flash(c);
 si_need(qol_stub_target(c,0x080DB4E4U)==0x09FF69D1U,"normal root wrapper binding");
 si_need(read32(c,0x093BDFB4U)==0x093910EDU&&read32(c,0x09391114U)==0x09377695U,"research Mirage QOL load chain");
 si_need((unsigned)read_register(c,"pc")== (unsigned)((struct ARMCore*)c->cpu)->gprs[15],"read-only PC representation");
 si_guard(c);vl_frames(c,0,600);
 for(unsigned k=0;k<30&&!vl_root_done;++k){vl_frames(c,k==0?QOL_KEY_START:(k>12?QOL_KEY_B:QOL_KEY_A),2);vl_frames(c,0,120);}
 si_need(vl_root_done&&vl_research_done,"ordinary load returned through both adapters");
 return c;
}
static void vl_state(struct mCore*c,const char*stage){
 uint8_t ledger[2048];char sha[65];lc_read(c,ledger);si_digest(ledger,2048,sha);
 printf("{\"load_state\":\"%s\",\"counter\":%u,\"version\":%u,\"checksum_valid\":%s,\"migration_dirty\":%u,\"recovery_blocked\":%u,\"last_result\":%u,\"ledger_sha256\":\"%s\",\"ledger_hex\":\"",stage,read32(c,SI_COUNTER),si_read16(c,LC_LEDGER+4),lc_u32(ledger,8)==lc_checksum(ledger)?"true":"false",read8(c,SI_VOL+26),read8(c,SI_VOL+27),si_read16(c,SI_VOL+16),sha);
 for(unsigned i=0;i<2048;++i)printf("%02x",ledger[i]);puts("\"}");fflush(stdout);
}
int main(int argc,char**argv){
 if(argc==3&&!strcmp(argv[1],"--guard-check"))si_guard_check(argv[2]);
 si_need(argc==4,"usage: v1-load candidate private-v1-save case");char sha[65];
 sha256_file(argv[1],sha);si_need(!strcmp(sha,VL_ROM),"fixed current retry candidate");
 const char*name=argv[3];unsigned kind=!strcmp(name,"v1-load-valid")?0:!strcmp(name,"v1-load-checksum")?1:!strcmp(name,"v1-load-tail")?2:99;
 si_need(kind<3,"closed V1 cold load cases");sha256_file(argv[2],sha);si_need(!strcmp(sha,VL_FIXTURES[kind]),"exact independent Flash fixture");
 FILE*f=fopen(argv[2],"rb");si_need(f!=NULL,"private fixture open");uint8_t*flash=malloc(0x20000);si_need(flash&&fread(flash,1,0x20000,f)==0x20000&&!fclose(f),"full private fixture read");
 uint8_t input[2048],loaded[2048],field[2048],again[2048];memcpy(input,flash+0x1F064U,2048);
 struct mLogger logger={.log=qol_log};mLogSetDefaultLogger(&logger);struct mCore*c=vl_open(argv[1],argv[2]);
 vl_state(c,"adapter_return");lc_read(c,loaded);
 printf("{\"trace\":\"ordinary_load\",\"root_calls\":%u,\"research_calls\":%u,\"mirage_calls\":%u,\"qol_load_calls\":%u,\"save_calls\":%u,\"phase0\":%u,\"phase1\":%u,\"phase2\":%u,\"native_returns\":%u,\"native_result\":%u,\"research_result\":%u,\"root_result\":%u,\"save_type\":%u,\"counter_at_save\":%u,\"available_at_save\":%u,\"steps\":%llu,\"host_writes\":0}\n",vl_root,vl_research,vl_mirage,vl_qol,vl_saves,vl_phases[0],vl_phases[1],vl_phases[2],vl_native_returns,vl_native_result,vl_result,vl_root_result,vl_type,vl_counter_at_save,vl_available_at_save,(unsigned long long)vl_steps);fflush(stdout);
 si_need(vl_root==1&&vl_research==1&&vl_mirage==1&&vl_qol==1&&!vl_phases[1]&&!vl_phases[2],"one full normal load chain");
 if(kind){
  si_need(vl_result==0&&vl_root_result==0&&!vl_saves&&!vl_phases[0]&&!vl_native_returns,"invalid V1 rejected by normal adapter");
  si_need(!memcmp(input,loaded,2048),"invalid durable V1 must not self-normalize");
  si_need(read32(c,SI_COUNTER)==2&&read8(c,SI_VOL+26)==0&&si_read16(c,SI_VOL+16)==7,"invalid V1 error propagated");
  si_need(!memcmp(flash,((struct GBA*)c->board)->memory.savedata.data,0x20000),"entire Flash unchanged on rejection");
 }else{
  si_need(vl_result==1&&vl_root_result==1&&vl_saves==1&&vl_phases[0]==1&&vl_native_returns==1&&vl_native_result==1,"V1 migration persists once on normal load");
  si_need(vl_counter_at_save==2&&vl_available_at_save==1&&read32(c,SI_COUNTER)==3,"native load migration counter");
  si_need(read8(c,SI_VOL+26)==0&&read8(c,SI_VOL+27)==0&&si_read16(c,SI_VOL+16)==0,"load migration state cleared");
  lc_unrelated(input,loaded);lc_owner(c);si_need(si_read16(c,LC_LEDGER+4)==2&&lc_u32(loaded,8)==lc_checksum(loaded),"valid migrated V2");
  const uint8_t*after=((struct GBA*)c->board)->memory.savedata.data;
  si_need(!memcmp(after+0x1F064U,loaded,2048),"actual Flash has complete migrated ledger");
  si_need(!memcmp(flash+0x1F000U,after+0x1F000U,100)&&!memcmp(flash+0x1F864U,after+0x1F864U,0x79CU),"other private-sector owners preserved");
  run_key_frames(c,0,180);for(unsigned k=0;k<30&&!si_field(c);++k)qol_press(c,k>12?QOL_KEY_B:QOL_KEY_A,120);
  si_need(si_field(c),"normal Continue reached field");run_key_frames(c,0,180);si_need(si_field(c),"stable field");lc_read(c,field);lc_event(c,"continued");
  lc_unrelated(loaded,field);lc_owner(c);si_need(read32(c,SI_COUNTER)==3,"no extra save at field");
  qol_close(c);c=si_open(argv[1],argv[2]);lc_read(c,again);lc_event(c,"continued_again");
  si_need(!memcmp(field,again,2048)&&read32(c,SI_COUNTER)==3,"fresh Continue full equality");
  qol_close(c);c=si_open(argv[1],argv[2]);lc_read(c,loaded);lc_event(c,"continued_third");
  si_need(!memcmp(loaded,again,2048)&&read32(c,SI_COUNTER)==3,"second fresh Continue idempotence");
 }
 free(flash);si_need(!log_problem_count,"mGBA warnings/errors");qol_close(c);
 printf("{\"status\":\"PASS\",\"scope\":\"V1_FLASH_FIXTURE_ORDINARY_LOAD_CHAIN\",\"case\":\"%s\",\"candidate_sha256\":\"%s\",\"fresh_cores\":%u,\"host_write_barriers\":7,\"ram_fixture_writes\":0,\"physical_flash_fault_accepted\":false,\"normal_new_game_accepted\":false,\"transaction_ui_accepted\":false,\"warnings_errors\":%u}\n",name,VL_ROM,si_cores,log_problem_count);
 return 0;
}
