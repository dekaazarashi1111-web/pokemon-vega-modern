/* 通常new-gameのみ。消去Flashから標準キー入力、初回Save、独立Continue。
 * 旧fixture/直接call/warp/台帳注入/文字速度変更は一切呼ばない。 */
static void ng_flash(struct mCore*c,uint8_t*out){
 struct GBASavedata*s=&((struct GBA*)c->board)->memory.savedata;
 si_need(s->type==SAVEDATA_FLASH1M&&s->data,"actual 128KiB Flash");memcpy(out,s->data,131072);
}
static void ng_position(struct mCore*c){
 unsigned s=read32(c,QOL_SAVE_BLOCK1_SLOT),id=read8(c,0x02036FB1U),obj=0x02036D6CU+36*id;
 si_need(si_field(c)&&s>=0x02000000U&&s+6<=0x02040000U,"stable ordinary field");
 si_need(read8(c,s+4)==4&&read8(c,s+5)==0&&read16(c,s)==10&&read16(c,s+2)==2,"authored initial field position");
 si_need(id<16&&(read8(c,obj)&1)&&read16(c,obj+0x10)==17&&read16(c,obj+0x12)==9&&(read8(c,obj+0x18)&15)==3,"real initial player object");
 si_need(!read8(c,0x02036FAEU)&&!read8(c,0x02036FAFU),"player movement settled");
}
static void ng_ledger(struct mCore*c){
 uint8_t got[2048],want[2048]={0};lc_read(c,got);
 memcpy(want,"VGS1",4);lc_w16(want,4,2);lc_w16(want,6,2048);want[29]=1;
 want[0x73f]=1;want[0x740]=64;want[0x745]=1;want[0x763]=1;
 si_need(got[0x746]<=10,"bounded natural minute");want[0x746]=got[0x746];lc_w32(want,8,lc_checksum(want));
 si_need(!memcmp(want,got,2048),"entire new-game ledger has only source defaults and clock");
 si_need(!read8(c,SI_VOL+26)&&!read8(c,SI_VOL+27)&&!read8(c,SI_VOL+28)&&!read8(c,SI_VOL+34),"no migration/recovery/test service");
 si_need(!read8(c,QOL_LEDGER+QOL_LEDGER_TEXT_SPEED),"production default text speed unmodified");
}
static void ng_unchanged(struct mCore*c,const unsigned*items,const uint8_t*party,unsigned counter){
 unsigned now[2048];si_inventory(c,now);si_need(!memcmp(now,items,2048*sizeof(*items)),"all five Bag pockets preserved");
 for(unsigned i=0;i<600;++i)si_need(read8(c,QOL_PLAYER_PARTY+i)==party[i],"all party600 bytes preserved");
 si_need(!read8(c,QOL_PLAYER_PARTY_COUNT),"no starter/party fixture");si_need(read32(c,SI_COUNTER)==counter,"exact first-save counter");ng_ledger(c);ng_position(c);
}
static void ng_event(struct mCore*c,const char*stage){
 ng_position(c);ng_ledger(c);
 printf("{\"field_event\":\"%s\",\"map_group\":4,\"map_num\":0,\"x\":10,\"y\":2,\"live_x\":17,\"live_y\":9,\"facing\":3,\"player_active\":true,\"script_locked\":false,\"text_speed\":0}\n",stage);
 lc_event(c,stage);uint8_t b[131072];char sha[65];ng_flash(c,b);si_digest(b,sizeof(b),sha);
 printf("{\"flash_event\":\"%s\",\"size\":131072,\"sha256\":\"%s\"}\n",stage,sha);fflush(stdout);
}
int main(int argc,char**argv){
 if(argc==3&&!strcmp(argv[1],"--guard-check"))si_guard_check(argv[2]);
 si_need(argc==4&&!strcmp(argv[3],"ordinary-new-game-first-save-two-continues"),"closed new-game case");
 char sha[65];sha256_file(argv[1],sha);si_need(!strcmp(sha,NG_ROM),"exact current candidate");sha256_file(argv[2],sha);si_need(!strcmp(sha,NG_ERASED),"erased Flash only; no user seed");
 struct mLogger logger={.log=qol_log};mLogSetDefaultLogger(&logger);struct mCore*c=qol_open(argv[1],argv[2]);++si_cores;
 qol_log_core=c;c->setVideoBuffer(c,si_video,240);si_flash(c);si_guard(c);
 uint8_t flash[131072],saved[131072],party[600],trace[6*233];unsigned items[2048],frames=0;
 ng_flash(c,flash);for(unsigned i=0;i<131072;++i)si_need(flash[i]==255,"entire initial Flash erased");
 si_need(BATTLE_CORE_FIELD_TRACE_SEGMENTS==233,"reviewed trace extent");
 for(unsigned i=0;i<233;++i){lc_w32(trace,6*i,BOOT_TRACE[i].frames);lc_w16(trace,6*i+4,BOOT_TRACE[i].keys);frames+=BOOT_TRACE[i].frames;}
 si_digest(trace,sizeof(trace),sha);si_need(!strcmp(sha,NG_TRACE_HASH)&&frames==NG_TRACE_FRAMES,"exact input-only trace");
 for(unsigned i=0;i<233;++i)run_key_frames(c,BOOT_TRACE[i].keys,BOOT_TRACE[i].frames);
 run_key_frames(c,0,600);ng_position(c);ng_ledger(c);
 ng_flash(c,flash);for(unsigned i=0;i<131072;++i)si_need(flash[i]==255,"intro performs no hidden Flash save");
 si_need(read32(c,SI_COUNTER)==0&&!read8(c,QOL_PLAYER_PARTY_COUNT),"first new game before any save/starter");
 printf("{\"new_game_boot\":\"erased-flash-input-only\",\"trace_segments\":233,\"trace_frames\":%u,\"settle_frames\":600,\"trace_sha256\":\"%s\",\"initial_save_sha256\":\"%s\"}\n",frames,NG_TRACE_HASH,NG_ERASED);
 si_inventory(c,items);for(unsigned i=0;i<600;++i)party[i]=read8(c,QOL_PLAYER_PARTY+i);ng_event(c,"new_game_field");
 si_need(si_normal_save(c),"ordinary first Start Save");ng_unchanged(c,items,party,1);ng_event(c,"first_saved");ng_flash(c,saved);si_need(memcmp(saved,flash,131072)!=0,"real first Flash write");qol_close(c);
 for(unsigned i=0;i<2;++i){c=si_open(argv[1],argv[2]);si_guard(c);ng_unchanged(c,items,party,1);ng_flash(c,flash);si_need(!memcmp(flash,saved,131072),"Continue does not resave or mutate Flash");ng_event(c,i?"continued_again":"continued");qol_close(c);}
 si_need(!log_problem_count,"no mGBA warnings/errors");
 printf("{\"status\":\"PASS\",\"scope\":\"ORDINARY_NEW_GAME_FIRST_SAVE_AND_TWO_FRESH_CONTINUES\",\"case\":\"ordinary-new-game-first-save-two-continues\",\"candidate_sha256\":\"%s\",\"fresh_cores\":%u,\"manual_saves\":1,\"automatic_saves\":0,\"host_write_barriers\":7,\"guarded_host_writes\":0,\"fixture_calls\":0,\"ram_fixture_writes\":0,\"register_fixture_writes\":0,\"text_speed_writes\":0,\"normal_new_game_accepted\":true,\"starter_acquisition_accepted\":false,\"research_natural_supply_accepted\":false,\"warnings_errors\":%u}\n",NG_ROM,si_cores,log_problem_count);return 0;
}
