/* 通常cold boot/Continue内で保存可用性wordだけをfixture化する。
 * phase0入口でCPUを停止し、1 -> 0の4byteだけを書き、直後に7 API guardを再装着。
 * ledger/owner/PC/戻り値/Flashの注入はしない。物理Flash故障や同一coreのmenu retryではない。
 * 実失敗後は改変しないFlashからfresh通常Continueし、保存1回と2回の冪等性を観測する。 */
#define PL_AVAILABLE 0x03005044U
static struct mCore pl_api;
static unsigned pl_pause,pl_fixture_words;
static unsigned pl_pc(struct mCore*c){return ((unsigned)((struct ARMCore*)c->cpu)->gprs[15]&~1U)-2U;}
static void pl_reset(void){
 vl_root=vl_research=vl_mirage=vl_qol=vl_saves=vl_native_returns=vl_native_result=0;
 memset(vl_phases,0,sizeof(vl_phases));vl_root_lr=vl_root_sp=vl_research_lr=vl_research_sp=0;
 vl_result=vl_root_result=vl_type=vl_counter_at_save=vl_available_at_save=vl_research_done=vl_root_done=0;vl_steps=0;pl_pause=0;
}
static void pl_frames(struct mCore*c,unsigned keys,unsigned frames){
 unsigned start=c->frameCounter(c);c->setKeys(c,keys);
 while(c->frameCounter(c)-start<frames&&!vl_root_done&&!pl_pause){
  vl_observe(c);if(vl_root_done)break;
  if((((struct ARMCore*)c->cpu)->cpsr.packed&32U)&&pl_pc(c)==0x093BF630U){pl_pause=1;break;}
  si_need(++vl_steps<400000000ULL,"phase0 boot instruction bound");c->step(c);
 }
}
static struct mCore*pl_open_until_phase0(const char*rom,const char*save){
 struct mCore*c=qol_open(rom,save);++si_cores;qol_log_core=c;c->setVideoBuffer(c,si_video,240);si_flash(c);pl_api=*c;si_guard(c);
 si_need(qol_stub_target(c,0x080DB4E4U)==0x09FF69D1U,"ordinary root wrapper");
 si_need(read32(c,0x093BDFB4U)==0x093910EDU&&read32(c,0x09391114U)==0x09377695U,"production research Mirage QOL chain");
 si_need(read32(c,0x093BF67CU)==0x09377661U&&read32(c,0x09378B28U)==PL_AVAILABLE&&read32(c,0x09378B2CU)==0x080DB357U,"native save availability rooted delegates");
 pl_frames(c,0,600);
 for(unsigned k=0;k<30&&!vl_root_done&&!pl_pause;++k){pl_frames(c,k==0?QOL_KEY_START:(k>12?QOL_KEY_B:QOL_KEY_A),2);pl_frames(c,0,120);}
 si_need(pl_pause&&!vl_root_done&&vl_phases[0]==1&&vl_saves==0&&vl_root_lr==0x080789FEU,"normal load paused before its first phase0 save");
 return c;
}
static void pl_make_unavailable(struct mCore*c){
 struct ARMCore*cpu=c->cpu;
 si_need(pl_fixture_words==0&&pl_pause&&pl_pc(c)==0x093BF630U&&cpu->gprs[0]==0&&read32(c,SI_COUNTER)==2&&read32(c,PL_AVAILABLE)==1,"one exact external availability fixture");
 uint8_t*ram=malloc(0x48000),*flash=malloc(0x20000);int32_t regs[16];
 si_need(ram&&flash,"fixture snapshot allocation");memcpy(regs,cpu->gprs,sizeof(regs));int32_t cpsr=cpu->cpsr.packed;
 for(unsigned i=0;i<0x40000;++i)ram[i]=read8(c,0x02000000U+i);
 for(unsigned i=0;i<0x8000;++i)ram[0x40000+i]=read8(c,0x03000000U+i);
 struct GBASavedata*s=&((struct GBA*)c->board)->memory.savedata;memcpy(flash,s->data,0x20000);
 si_restore(c,&pl_api);write32_bytes(c,PL_AVAILABLE,0);++pl_fixture_words;si_guard(c);
 for(unsigned i=0;i<0x40000;++i)si_need(ram[i]==read8(c,0x02000000U+i),"fixture cannot change any EWRAM");
 for(unsigned i=0;i<0x8000;++i)if(i<0x5044||i>=0x5048)si_need(ram[0x40000+i]==read8(c,0x03000000U+i),"fixture cannot change other IWRAM");
 si_need(!memcmp(regs,cpu->gprs,sizeof(regs))&&cpsr==cpu->cpsr.packed&&!memcmp(flash,s->data,0x20000)&&read32(c,PL_AVAILABLE)==0,"fixture preserves registers and full Flash");free(ram);free(flash);
 puts("{\"fault_fixture\":\"availability_word_only\",\"address\":50352196,\"pc\":154924592,\"before\":1,\"after\":0,\"word_writes\":1,\"byte_writes\":4,\"ewram_unchanged\":true,\"iwram_except_word_unchanged\":true,\"registers_unchanged\":true,\"flash_unchanged\":true,\"guard_rearmed\":true}");fflush(stdout);
 /* このPCは停止前に一度観測済み。二重計数せず最初の実命令をguard下で進める。 */
 pl_pause=0;++vl_steps;c->step(c);vl_frames(c,0,600);si_need(vl_root_done&&vl_research_done,"failed native load returns normally");
}
static void pl_trace(const char*stage){
 printf("{\"phase0_load_trace\":\"%s\",\"root_calls\":%u,\"research_calls\":%u,\"mirage_calls\":%u,\"qol_calls\":%u,\"save_calls\":%u,\"phase0\":%u,\"phase1\":%u,\"phase2\":%u,\"native_returns\":%u,\"native_result\":%u,\"research_result\":%u,\"root_result\":%u,\"counter_at_save\":%u,\"available_at_save\":%u,\"save_type\":%u,\"root_return_pc\":%u,\"guarded_host_writes\":0,\"steps\":%llu}\n",stage,vl_root,vl_research,vl_mirage,vl_qol,vl_saves,vl_phases[0],vl_phases[1],vl_phases[2],vl_native_returns,vl_native_result,vl_result,vl_root_result,vl_counter_at_save,vl_available_at_save,vl_type,vl_root_lr,(unsigned long long)vl_steps);fflush(stdout);
}
static void pl_invariants(struct mCore*c,const uint8_t*before,const uint8_t*ledger,bool failed){
 const uint8_t*flash=((struct GBA*)c->board)->memory.savedata.data;char sha[65];si_digest(flash,0x20000,sha);
 bool same=!memcmp(flash,before,0x20000),owners=!memcmp(flash+0x1F000,before+0x1F000,100)&&!memcmp(flash+0x1F864,before+0x1F864,0x79C);
 bool restored=!memcmp(ledger,before+0x1F064,2048),durable=!memcmp(ledger,flash+0x1F064,2048);
 si_need(same==failed&&restored==failed&&owners&&durable,"full Flash and ledger/other-owner invariants");
 printf("{\"phase0_load_invariants\":\"%s\",\"input_ledger_restored\":%s,\"full_flash_unchanged\":%s,\"other_private_owners_unchanged\":true,\"durable_matches_ram\":true,\"flash_sha256\":\"%s\"}\n",failed?"failed":"recovered",restored?"true":"false",same?"true":"false",sha);fflush(stdout);
}
int main(int argc,char**argv){
 if(argc==3&&!strcmp(argv[1],"--guard-check"))si_guard_check(argv[2]);
 si_need(argc==4,"usage: phase0-load candidate private-save case");const char*name=argv[3];
 unsigned kind=!strcmp(name,"load-v1-phase0-unavailable")?0:!strcmp(name,"load-pending-phase0-unavailable")?1:99;si_need(kind<2,"closed phase0 cases");char sha[65];
 sha256_file(argv[1],sha);si_need(!strcmp(sha,VL_ROM),"unchanged current candidate SHA");sha256_file(argv[2],sha);si_need(!strcmp(sha,PL_FIXTURES[kind]),"exact offline Flash fixture");
 uint8_t*flash=malloc(0x20000);FILE*f=fopen(argv[2],"rb");si_need(flash&&f&&fread(flash,1,0x20000,f)==0x20000&&!fclose(f),"full Flash input");
 struct mLogger logger={.log=qol_log};mLogSetDefaultLogger(&logger);pl_reset();struct mCore*c=pl_open_until_phase0(argv[1],argv[2]);pl_make_unavailable(c);
 uint8_t failed[2048],recovered[2048],field[2048],again[2048];lc_read(c,failed);vl_state(c,"failed");pl_trace("failed");
 si_need(vl_result==0&&vl_root_result==0&&vl_saves==1&&vl_phases[0]==1&&!vl_phases[1]&&!vl_phases[2]&&vl_native_returns==1&&vl_native_result==255&&read32(c,SI_COUNTER)==2,"real unavailable native return without commit");
 si_need(read8(c,SI_VOL+26)==0&&read8(c,SI_VOL+27)==1&&si_read16(c,SI_VOL+16)==13,"failure rollback flags and error");
 pl_invariants(c,flash,failed,true);si_event(c,"failed",4);qol_close(c);
 /* 保存可用性はhostで1に戻さない。cold bootの本来の初期化が回復する。 */
 pl_reset();c=vl_open(argv[1],argv[2]);lc_read(c,recovered);vl_state(c,"recovered");pl_trace("recovered");
 si_digest(recovered,2048,sha);si_need(!strcmp(sha,PL_RECOVERED[kind]),"complete expected migration/recovery ledger");
 si_need(vl_result==1&&vl_root_result==1&&vl_saves==1&&vl_phases[0]==1&&!vl_phases[1]&&!vl_phases[2]&&vl_native_returns==1&&vl_native_result==1&&read32(c,SI_COUNTER)==3&&vl_available_at_save==1,"cold recovery persists once with native availability");
 si_need(read8(c,SI_VOL+26)==0&&read8(c,SI_VOL+27)==0&&si_read16(c,SI_VOL+16)==0,"recovery clears blocked and dirty");pl_invariants(c,flash,recovered,false);
 run_key_frames(c,0,180);for(unsigned k=0;k<30&&!si_field(c);++k)qol_press(c,k>12?QOL_KEY_B:QOL_KEY_A,120);
 si_need(si_field(c),"recovery Continue reaches field");run_key_frames(c,0,180);si_need(si_field(c),"stable field after recovery");lc_read(c,field);lc_unrelated(recovered,field);lc_event(c,"continued");si_need(read32(c,SI_COUNTER)==3,"no second commit entering field");qol_close(c);
 c=si_open(argv[1],argv[2]);lc_read(c,again);lc_event(c,"continued_again");si_need(!memcmp(field,again,2048)&&read32(c,SI_COUNTER)==3,"first subsequent cold Continue complete equality");qol_close(c);
 c=si_open(argv[1],argv[2]);lc_read(c,failed);lc_event(c,"continued_third");si_need(!memcmp(again,failed,2048)&&read32(c,SI_COUNTER)==3,"second subsequent cold Continue complete equality");
 si_need(pl_fixture_words==1&&si_cores==4&&!log_problem_count,"exact fixture/core/warning counts");qol_close(c);free(flash);
 puts("{\"cold_recovery\":\"PASS\",\"normal_loads_after_failure\":3,\"additional_saves_after_recovery\":0,\"complete_ledger_equal\":true,\"availability_restored_by_cold_boot\":true}");
 printf("{\"status\":\"PASS\",\"scope\":\"ORDINARY_LOAD_PHASE0_AVAILABILITY_FIXTURE_AND_COLD_RECOVERY\",\"case\":\"%s\",\"candidate_sha256\":\"%s\",\"fresh_cores\":%u,\"availability_fixture_words\":1,\"availability_fixture_byte_writes\":4,\"host_write_barriers\":7,\"guarded_host_writes\":0,\"ram_ledger_fixture_writes\":0,\"register_fixture_writes\":0,\"physical_flash_fault_accepted\":false,\"same_core_menu_retry_accepted\":false,\"normal_new_game_accepted\":false,\"transaction_ui_accepted\":false,\"warnings_errors\":%u}\n",name,VL_ROM,si_cores,log_problem_count);return 0;
}
