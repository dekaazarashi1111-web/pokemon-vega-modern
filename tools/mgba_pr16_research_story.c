static struct mCore *st_open(const char *rom, const char *save) {
    static struct mRTCSource rtc = {
        .sample = NULL, .unixTime = fixed_unix_time,
        .serialize = NULL, .deserialize = NULL,
    };
    struct mCore *core = mCoreFind(rom);
    if (!core || !core->init(core)) qol_die("core initialization failed");
    if (!mCoreLoadFile(core, rom)) qol_die("ROM load failed");
    if (!mCoreLoadSaveFile(core, save, false)) qol_die("save attachment failed");
    mCoreInitConfig(core, NULL);
    mCoreConfigSetDefaultValue(&core->config, "idleOptimization", "ignore");
    mCoreSetRTC(core, &rtc);
    core->setVideoBuffer(core,si_video,240);
    core->reset(core);
    return core;
}

/* 通常進行用キー入力protocol。fixture、CPU/進行/party直接書込は使用しない。
 * 各入力を実行前に記録し、画面と観測値を同一frameで固定する。 */
static unsigned st_frames, st_inputs;
static void st_keys(struct mCore*c,unsigned key,unsigned frames){
 si_need(key==0||key==1||key==2||key==8||key==16||key==32||key==64||key==128,"single ordinary key");
 si_need(frames>0&&frames<=600&&st_frames+frames<=1800000,"bounded story frames");
 printf("{\"input\":%u,\"frame\":%u,\"key\":%u,\"frames\":%u}\n",st_inputs++,st_frames,key,frames);fflush(stdout);
 run_key_frames(c,key,frames);st_frames+=frames;
}
static void st_press(struct mCore*c,unsigned key,unsigned wait){st_keys(c,key,2);st_keys(c,0,wait);}
static void st_screen(unsigned n){
 char name[80],sha[65];snprintf(name,sizeof(name),"screen-%04u.ppm",n);
 FILE*f=fopen(name,"wb");si_need(f!=NULL,"screen file");si_need(fprintf(f,"P6\n240 160\n255\n")>0,"screen header");
 for(unsigned i=0;i<240*160;++i){uint32_t p=si_video[i];uint8_t rgb[3]={p,p>>8,p>>16};si_need(fwrite(rgb,1,3,f)==3,"screen pixels");}
 si_need(!fclose(f),"screen close");sha256_file(name,sha);printf("{\"screen\":%u,\"frame\":%u,\"sha256\":\"%s\"}\n",n,st_frames,sha);
}
static void st_observe(struct mCore*c,unsigned n){
 unsigned s=read32(c,QOL_SAVE_BLOCK1_SLOT),id=read8(c,0x02036FB1U),o=0x02036D6CU+36*id;
 si_need(s>=0x02000000U&&s+0x1000<0x02040000U&&id<16,"read-only field addresses");
 uint8_t p[600],flash[131072],ledger[2048];char ps[65],fs[65],ls[65];
 for(unsigned i=0;i<600;++i)p[i]=read8(c,QOL_PLAYER_PARTY+i);ng_flash(c,flash);lc_read(c,ledger);
 si_digest(p,sizeof(p),ps);si_digest(flash,sizeof(flash),fs);si_digest(ledger,sizeof(ledger),ls);
 printf("{\"observe\":%u,\"frame\":%u,\"map\":[%u,%u],\"xy\":[%u,%u],\"live_xy\":[%u,%u],\"facing\":%u,\"field\":%s,\"lock\":%u,\"callback2\":%u,\"party_count\":%u,\"save_counter\":%u,\"rp\":%u,\"battle_flags\":%u,\"battle_outcome\":%u,\"party_sha256\":\"%s\",\"flash_sha256\":\"%s\",\"ledger_sha256\":\"%s\"}\n",n,st_frames,read8(c,s+4),read8(c,s+5),read16(c,s),read16(c,s+2),read16(c,o+16),read16(c,o+18),read8(c,o+24)&15,si_field(c)?"true":"false",read8(c,0x03000F9CU),read32(c,0x03003134U),read8(c,QOL_PLAYER_PARTY_COUNT),read32(c,SI_COUNTER),read16(c,0x0203D743U),read32(c,0x02022AACU),read8(c,0x02023DEAU),ps,fs,ls);
 st_screen(n);fflush(stdout);
}
static void st_save(struct mCore*c){
 si_need(si_field(c),"save only at idle field");unsigned before=read32(c,SI_COUNTER);
 st_press(c,8,120);si_need(read32(c,QOL_START_MENU_CALLBACK)==QOL_START_MENU_INPUT,"ordinary Start menu");
 unsigned count=read8(c,QOL_START_MENU_COUNT),cur=read8(c,QOL_START_MENU_CURSOR),target=99;
 si_need(count>0&&count<=10&&cur<count,"bounded Start menu");
 for(unsigned i=0;i<count;++i)if(read8(c,QOL_START_MENU_ORDER+i)==4)target=i;
 si_need(target<count,"Save action present");while(cur!=target){st_press(c,128,30);cur=(cur+1)%count;}st_press(c,1,120);
 bool seen=false;for(unsigned i=0;i<32;++i){unsigned cb=read32(c,QOL_START_MENU_CALLBACK);if(cb==0x0806EDB9U)seen=true;
  if(seen&&read32(c,SI_COUNTER)==before+1&&si_field(c)){st_keys(c,0,180);printf("{\"ordinary_save\":true,\"before\":%u,\"after\":%u,\"frame\":%u}\n",before,read32(c,SI_COUNTER),st_frames);fflush(stdout);return;}st_press(c,1,180);}
 si_need(false,"ordinary Save timeout");
}
int main(int argc,char**argv){
 if(argc==3&&!strcmp(argv[1],"--guard-check"))si_guard_check(argv[2]);
 bool fresh=argc==4&&!strcmp(argv[3],"new-game-story");
 bool continuing=argc==5&&!strcmp(argv[3],"continue-story");
 si_need(fresh||continuing,"closed story invocation");
 char sha[65],input_sha[65];sha256_file(argv[1],sha);si_need(!strcmp(sha,NG_ROM),"fixed story candidate");sha256_file(argv[2],input_sha);
 si_need(fresh?!strcmp(input_sha,NG_ERASED):(strlen(argv[4])==64&&!strcmp(input_sha,argv[4])),"exact blank or retained Save identity");
 struct mLogger logger={.log=qol_log};mLogSetDefaultLogger(&logger);struct mCore*c=st_open(argv[1],argv[2]);qol_log_core=c;si_flash(c);si_guard(c);
 printf("{\"begin\":\"%s\",\"candidate_sha256\":\"%s\",\"initial_save_sha256\":\"%s\",\"host_write_barriers\":7}\n",fresh?"NEW_GAME_STORY_DEVELOPMENT":"INDEPENDENT_CONTINUE",NG_ROM,input_sha);
 if(fresh){
  uint8_t flash[131072],trace[233*6];ng_flash(c,flash);for(unsigned i=0;i<sizeof(flash);++i)si_need(flash[i]==255,"entire blank Flash");
  for(unsigned i=0;i<233;++i){lc_w32(trace,6*i,BOOT_TRACE[i].frames);lc_w16(trace,6*i+4,BOOT_TRACE[i].keys);}si_digest(trace,sizeof(trace),sha);si_need(!strcmp(sha,NG_TRACE_HASH),"fixed prerequisite input trace");
  for(unsigned i=0;i<233;++i)st_keys(c,BOOT_TRACE[i].keys,BOOT_TRACE[i].frames);st_keys(c,0,600);
 }else{
  st_keys(c,0,600);bool ready=false;
  for(unsigned i=0;i<100;++i){st_press(c,i==0?8:(i>12?2:1),120);if(si_field(c)){st_keys(c,0,180);if(si_field(c)){ready=true;break;}}}
  si_need(ready,"independent Continue reaches real field");
 }
 st_observe(c,0);char line[128],op[16],tail;unsigned a,b;
 while(fgets(line,sizeof(line),stdin)){
  if(sscanf(line,"%15s %u %u %c",op,&a,&b,&tail)==3&&!strcmp(op,"key")){st_keys(c,a,b);continue;}
  if(sscanf(line,"%15s %u %c",op,&a,&tail)==2&&!strcmp(op,"observe")){st_observe(c,a);continue;}
  if(!strcmp(line,"save\n")){st_save(c);continue;}
  if(!strcmp(line,"quit\n")){si_need(!log_problem_count,"no emulator warning/error");printf("{\"end\":\"STORY_INPUT_CHECKPOINT\",\"frames\":%u,\"inputs\":%u,\"warnings_errors\":%u,\"host_write_barriers\":7,\"guarded_host_writes\":0,\"fixture_calls\":0,\"natural_research_arrival_accepted\":false}\n",st_frames,st_inputs,log_problem_count);fflush(stdout);qol_close(c);return 0;}
  si_need(false,"invalid or overlong story command");
 }
 si_need(false,"explicit quit required");return 1;
}
