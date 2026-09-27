/* GAME_CORNER専用。開始位置/進行/元手コインのみfixture。
 * barrier後は物理キーと読取だけ。RP/payout/RNG/outcome/PCを注入しない。
 * 診断traceはEOFでSTOPPED。受入を自己宣言しない。 */
#define GC_STATE_SLOT 0x0203F314U
static unsigned gc_coins(struct mCore*c){
 return read16(c,read32(c,0x03005048U)+0x294U)^(read32(c,read32(c,0x0300504CU)+0xF20U)&65535U);
}
static unsigned gc_state(struct mCore*c){
 unsigned p=read32(c,GC_STATE_SLOT);return p>=0x02000000U&&p<=0x0203FFA0U?p:0;
}
static void gc_screen(const char*name){
 char hash[65],path[96];ct_screen(40,hash);snprintf(path,sizeof(path),"game-corner-%s.ppm",name);
 si_need(rename("catalog-page-40.ppm",path)==0,"game-corner screenshot");
 printf("{\"screen\":\"%s\",\"sha256\":\"%s\",\"frame\":%u}\n",path,hash,uc_frames);fflush(stdout);
}
static void gc_observe(struct mCore*c,const char*label){
 unsigned p=gc_state(c),s=read32(c,QOL_SAVE_BLOCK1_SLOT);
 printf("{\"observation\":\"%s\",\"frame\":%u,\"coins\":%u,\"rp\":%u,\"counter\":%u,\"callback\":%u,\"field\":%s,\"map\":[%u,%u,%u,%u],\"state_address\":%u,\"state\":\"",label,uc_frames,gc_coins(c),si_read16(c,SI_OWNER+4),read32(c,SI_COUNTER),read32(c,BATTLE_CORE_MAIN_CALLBACK2),si_field(c)?"true":"false",read8(c,s+4),read8(c,s+5),read16(c,s),read16(c,s+2),p);
 if(p)for(unsigned i=0;i<96;++i)printf("%02x",read8(c,p+i));
 printf("\",\"owner\":\"");for(unsigned i=0;i<64;++i)printf("%02x",read8(c,SI_OWNER+i));
 printf("\",\"volatile\":\"");for(unsigned i=0;i<36;++i)printf("%02x",read8(c,SI_VOL+i));
 printf("\"}\n");fflush(stdout);
}
static struct mCore*gc_setup(const char*rom,const char*save){
 struct mCore*c=ct_open(rom,save);
 printf("{\"root_event\":%u,\"root_script\":%u}\n",read32(c,0x092C3A90U),read32(c,0x09413E18U));fflush(stdout);
 si_need(read32(c,0x092C3A90U)==0x09413F30U&&read32(c,0x09413E18U)==0x094324DDU,"actual slot background13 root");
 (void)call_preserving(c,0x080D1699U,1000,0,0,0); /* fixture: SetCoins, not payout */
 (void)call_preserving(c,QOL_FLAG_SET,0x1860,0,0,0); /* fixture: FlagSet coin case */
 run_key_frames(c,0,2);
 (void)qol_call5_preserving(c,QOL_SET_WARP_DESTINATION,98,56,255,1,7);
 (void)call_preserving(c,QOL_RESET_INITIAL_AVATAR,0,0,0,0);
 (void)call_preserving(c,QOL_WARP_INTO_MAP,0,0,0,0);
 qol_write32(c,QOL_FIELD_CALLBACK_SLOT,QOL_DEFAULT_WARP_EXIT);
 (void)call_preserving(c,QOL_SET_MAIN_CALLBACK2,QOL_CB2_LOAD_MAP,0,0,0);si_guard(c);
 for(unsigned i=0;i<900;++i)uc_frame(c,0);
 si_need(si_field(c)&&gc_coins(c)==1000&&si_read16(c,SI_OWNER+4)==0,"zero-RP game-corner fixture");
 si_need(read8(c,SI_VOL+28)==0&&read8(c,SI_VOL+34)==0&&si_read16(c,SI_VOL+20)==65535,"real services only");
 return c;
}
int main(int argc,char**argv){
 if(argc==3&&!strcmp(argv[1],"--guard-check"))si_guard_check(argv[2]);
 si_need(argc==4&&!strcmp(argv[3],"game-corner-diagnostic"),"closed diagnostic case");char sha[65];
 sha256_file(argv[1],sha);si_need(!strcmp(sha,UC_ROM),"fixed candidate");sha256_file(argv[2],sha);si_need(!strcmp(sha,UC_FIXTURE),"zero RP fixture");
 struct mLogger logger={.log=qol_log};mLogSetDefaultLogger(&logger);struct mCore*c=gc_setup(argv[1],argv[2]);
 lc_event(c,"fixture");gc_observe(c,"fixture");gc_screen("fixture");
 char line[128];unsigned cmd=0,total=0;
 while(fgets(line,sizeof(line),stdin)){
  unsigned key=0,frames=0;char extra;
  si_need(sscanf(line,"%u %u %c",&key,&frames,&extra)==2&&key<=1023&&frames>0&&frames<=10000&&total+frames<=300000,"bounded physical input");
  total+=frames;printf("{\"input\":%u,\"keys\":%u,\"frames\":%u,\"start_frame\":%u}\n",++cmd,key,frames,uc_frames);fflush(stdout);
  for(unsigned i=0;i<frames;++i)uc_frame(c,key);
  char label[32];snprintf(label,sizeof(label),"step-%03u",cmd);gc_observe(c,label);gc_screen(label);
 }
 lc_event(c,"end");qol_close(c);si_need(!log_problem_count,"new game-corner log diagnostics");
 printf("{\"status\":\"STOPPED\",\"case\":\"game-corner-diagnostic\",\"native_acceptance\":false,\"fresh_cores\":%u,\"guarded_host_writes\":0,\"accepted_case_reruns\":0}\n",si_cores);return 0;
}
