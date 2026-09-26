/* 同一coreの再試行だけ。通常scheduler上で実保存、実DestroyTaskを呼ぶ。
 * 観測中のRAM/Flash/registerへのhost書込みを7 APIで禁止する。
 * legacy単回taskを再利用せず、callbackの復帰まで待ってから次を作る。 */
#ifndef RT_ROM
#error "実測候補SHAを生成時に固定する"
#endif
#define RT_AVAILABLE 0x03005044U
static unsigned rt_returns,rt_last,rt_destroy;
static uint32_t rt_transaction(struct mCore*c){
 static const uint8_t code[]={
  0x70,0xb5,0x04,0x00,0x08,0x48,0x09,0x49,0x09,0x4a,0x0a,0x4b,0x00,0xf0,0x0a,0xf8,
  0x05,0x00,0x20,0x00,0x08,0x4b,0x00,0xf0,0x05,0xf8,0x08,0x4b,0x1d,0x60,0x70,0xbc,
  0x02,0xbc,0x08,0x47,0x18,0x47,0xc0,0x46,0xff,0xff,0x00,0x00,0x00,0x00,0x00,0x00,
  0x00,0x00,0x00,0x00,0x5d,0xe1,0x3b,0x09,0xa1,0x6c,0x07,0x08,0x60,0xdc,0x03,0x02};
 for(unsigned i=0;i<sizeof(code);++i)write8(c,0x0203DC00U+i,code[i]);
 write32_bytes(c,0x0203DC60U,0xDEADBEEFU);
 unsigned task=si_call(c,0x08076BB5U,0x0203DC01U,80,0,false);
 si_need(task<16,"retry fixture CreateTask");
 si_saves=si_loads=0;memset(si_phases,0,sizeof(si_phases));rt_returns=rt_last=rt_destroy=0;
 unsigned entries=0,callbacks=0,return_pc=0,entry_sp=0,steps=0;
 struct mCore api=*c;si_guard(c);c->setKeys(c,0);
 for(;;){unsigned pc=(unsigned)read_register(c,"pc");
  if((unsigned)read_register(c,"cpsr")&32U){pc=(pc&~1U)-2U;
   if(pc==0x0203DC00U){++callbacks;si_need((unsigned)read_register(c,"r0")==task,"scheduled task ID");return_pc=(unsigned)read_register(c,"lr")&~1U;entry_sp=(unsigned)read_register(c,"sp");}
   if(pc==0x093BE15CU)++entries;
   if(pc==0x09377660U)++si_saves;
   if(pc==0x09377694U)++si_loads;
   if(pc==0x0937767AU){++rt_returns;rt_last=(unsigned)read_register(c,"r0");}
   if(pc==0x08076CA0U){++rt_destroy;si_need((unsigned)read_register(c,"r0")==task,"native task retirement ID");}
   if(pc==0x093BF630U){unsigned phase=(unsigned)read_register(c,"r0");si_need(phase<3,"phase bound");++si_phases[phase];}
   uint32_t result=read32(c,0x0203DC60U);
   if(result!=0xDEADBEEFU&&pc==return_pc&&(unsigned)read_register(c,"sp")==entry_sp){
    si_need(callbacks==1&&entries==1&&rt_destroy==1,"one scheduled call and native task retirement");
    si_restore(c,&api);return result;
   }
  }
  if(++steps>=240000000U){fprintf(stderr,"retry limit pc=%08x return=%08x calls=%u/%u destroy=%u result=%u\n",pc,return_pc,callbacks,entries,rt_destroy,read32(c,0x0203DC60U));si_die("retry instruction bound");}
  ++si_steps;c->step(c);
 }
}
static void rt_call_event(unsigned n,unsigned result,unsigned counter,unsigned base){
 printf("{\"call\":%u,\"result\":%u,\"saves\":%u,\"loads\":%u,\"phase0\":%u,\"phase1\":%u,\"phase2\":%u,\"native_returns\":%u,\"native_result\":%u,\"counter_delta\":%u,\"destroy_calls\":%u,\"host_task_writes_during_observation\":0}\n",n,result,si_saves,si_loads,si_phases[0],si_phases[1],si_phases[2],rt_returns,rt_last,counter-base,rt_destroy);fflush(stdout);
}
int main(int argc,char**argv){
 if(argc==3&&!strcmp(argv[1],"--guard-check"))si_guard_check(argv[2]);
 si_need(argc==4,"usage: retry candidate private-save case");char sha[65];
 sha256_file(argv[1],sha);si_need(!strcmp(sha,RT_ROM),"retry candidate SHA");
 sha256_file(argv[2],sha);si_need(!strcmp(sha,SI_SEED),"retry seed SHA");
 const char*name=argv[3];bool zero=!strcmp(name,"retry-zero"),erased=!strcmp(name,"retry-erased"),v1=!strcmp(name,"retry-v1");
 bool checksum=!strcmp(name,"reject-v1-checksum"),tail=!strcmp(name,"reject-v1-tail");
 bool quiet=!strcmp(name,"valid-v2-idle"),blocked=!strcmp(name,"valid-v2-blocked");
 bool retry=zero||erased||v1,reject=checksum||tail;
 si_need(retry||reject||quiet||blocked,"closed retry cases");
 struct mLogger logger={.log=qol_log};mLogSetDefaultLogger(&logger);struct mCore*c=si_open(argv[1],argv[2]);
 si_need(read32(c,0x093BF67CU)==0x09377661U&&read32(c,0x093BF530U)==0x08099A09U,"production delegates retained");
 si_need(read32(c,0x09378B28U)==RT_AVAILABLE&&read32(c,0x09378B2CU)==0x080DB357U,"native availability root");
 si_need(read32(c,SI_VOL)==0x31564552U&&read8(c,SI_VOL+26)==0&&read8(c,SI_VOL+27)==0&&read8(c,SI_VOL+28)==0&&read8(c,SI_VOL+29)==0&&read8(c,SI_VOL+34)==0,"real external services and clean volatile state");
 si_need(read32(c,RT_AVAILABLE)==1,"normal availability");
 unsigned base=read32(c,SI_COUNTER);uint8_t baseline[2048],input[2048],after[2048],durable[2048];
 lc_read(c,baseline);lc_event(c,"baseline");memcpy(input,baseline,2048);
 if(zero||erased)memset(input,erased?255:0,2048);
 else if(v1||reject){lc_w16(input,4,1);memset(input+0x73f,0,193);if(tail)input[0x77f]=1;lc_w32(input,8,lc_checksum(input));if(checksum)input[8]^=1;}
 lc_fixture(c,input);if(retry)write32_bytes(c,RT_AVAILABLE,0);if(blocked)write8(c,SI_VOL+27,1);lc_event(c,"fixture");
 uint8_t*flash=malloc(0x20000);si_need(flash!=NULL,"private flash snapshot");
 struct GBASavedata*saved=&((struct GBA*)c->board)->memory.savedata;memcpy(flash,saved->data,0x20000);
 static const char*stages[]={"failed_first","failed_second","retried","idle"};
 for(unsigned n=0;n<4;++n){
  if(retry&&n==2)write32_bytes(c,RT_AVAILABLE,1); /* 外部保存可否fixtureだけ。owner/flagsを修復しない。 */
  unsigned result=rt_transaction(c);lc_read(c,after);lc_event(c,stages[n]);rt_call_event(n+1,result,read32(c,SI_COUNTER),base);
#ifdef RT_PARENT_DIAGNOSTIC
  if(n==1){si_need(zero&&result==5&&si_saves==0&&read32(c,SI_COUNTER)==base&&read8(c,SI_VOL+27)==0,"parent retry silently lost durability");
   si_need(!memcmp(flash,saved->data,0x20000),"parent full Flash unchanged");
   puts("{\"status\":\"BUG_REPRODUCED\",\"scope\":\"PARENT_EMPTY_RETRY_NO_PERSIST\",\"same_core_calls\":2}");free(flash);qol_close(c);return 0;}
  if(n==0)si_need(result==7&&si_saves==1&&rt_last==255,"parent first unavailable failure");
#else
  bool failing=retry&&n<2,saving=retry&&n==2;
  si_need(result==(reject||failing?7U:5U),"retry result");
  si_need(si_saves==(unsigned)(failing||saving)&&!si_loads&&si_phases[0]==si_saves&&!si_phases[1]&&!si_phases[2],"only phase0 attempted");
  si_need(rt_returns==si_saves&&rt_last==(failing?255U:saving?1U:0U),"native result observed");
  si_need(read32(c,SI_COUNTER)==base+(unsigned)(retry&&n>=2),"one durable retry commit");
  si_need(read8(c,SI_VOL+26)==0&&read8(c,SI_VOL+27)==(unsigned)failing,"retry volatile transition");
  if(failing||reject)si_need(!memcmp(input,after,2048),"complete preimage preserved");
  if(!retry||n<2)si_need(!memcmp(flash,saved->data,0x20000),"no unexpected Flash mutation");
  if(retry&&n>=2){lc_owner(c);si_need(si_read16(c,LC_LEDGER+4)==2&&lc_u32(after,8)==lc_checksum(after),"valid V2 retry");if(v1)lc_unrelated(input,after);}
  if(quiet||blocked)si_need(!memcmp(baseline,after,2048),"durable V2 unchanged");
#endif
 }
 free(flash);qol_close(c);c=si_open(argv[1],argv[2]);lc_read(c,durable);lc_event(c,"continued");
 si_need(!memcmp(reject?baseline:after,durable,2048)&&read32(c,SI_COUNTER)==base+(unsigned)retry,"fresh Continue complete durable equality");
 qol_close(c);c=si_open(argv[1],argv[2]);lc_read(c,after);lc_event(c,"continued_again");
 si_need(!memcmp(after,durable,2048)&&read32(c,SI_COUNTER)==base+(unsigned)retry,"second Continue idempotence");
 si_need(!log_problem_count,"mGBA warnings/errors");qol_close(c);
 printf("{\"status\":\"PASS\",\"scope\":\"SAME_CORE_PHASE0_RETRY_SCOPED_NOT_NORMAL_UI\",\"case\":\"%s\",\"candidate_sha256\":\"%s\",\"same_core_calls\":4,\"fresh_cores\":3,\"host_write_barriers\":7,\"normal_ui_accepted\":false,\"physical_flash_fault_accepted\":false,\"v1_load_adapter_accepted\":false,\"warnings_errors\":%u}\n",name,RT_ROM,log_problem_count);
 return 0;
}
