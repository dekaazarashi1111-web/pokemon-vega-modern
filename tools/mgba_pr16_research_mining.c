/* 採掘: fixture は badge / party / warp だけ。観測barrier後はキー・読取のみ。
 * 標準 field effect37 -> movement -> removeobject -> FieldMining を実行する。
 * return/RP/claim を注入しない。写真/虫取りのmainは実行しない。 */
static unsigned rm_rock(struct mCore *c) {
 unsigned count=0;
 for(unsigned i=0;i<16;++i){unsigned o=0x02036D6CU+36*i;
  if((read8(c,o)&1)&&read8(c,o+8)==12&&read8(c,o+9)==82&&read8(c,o+10)==97)++count;
 }
 return count;
}
static void rm_screen(const char *stage) {
 char hash[65],name[96];ct_screen(40,hash);
 snprintf(name,sizeof(name),"mining-%s.ppm",stage);
 si_need(rename("catalog-page-40.ppm",name)==0,"unique mining screen");
 printf("{\"screen\":\"%s\",\"sha256\":\"%s\"}\n",name,hash);fflush(stdout);
}
static void rm_stance(struct mCore *c) {
 unsigned s=read32(c,QOL_SAVE_BLOCK1_SLOT);
 if(!si_field(c)||read8(c,s+4)!=97||read8(c,s+5)!=82||read16(c,s)!=1||read16(c,s+2)!=21){
  rm_screen("stance-failure");fprintf(stderr,"mining stance field=%u map=%u/%u pos=%u/%u lock=%u cb=%08x\n",si_field(c),read8(c,s+4),read8(c,s+5),read16(c,s),read16(c,s+2),read8(c,0x03000F9CU),read32(c,BATTLE_CORE_MAIN_CALLBACK2));si_die("mining stance");
 }
}
static struct mCore *rm_setup(const char *rom,const char *save,unsigned mode) {
 struct mCore *c=ct_open(rom,save);
 unsigned e=read32(c,0x092C2568U),r=read32(c,e+4);
 si_need(e==0x09413B40U&&read8(c,e)==17&&r==0x0941397CU&&read8(c,r)==12&&read16(c,r+4)==1&&read16(c,r+6)==20&&read32(c,r+16)==0x093C050CU,"actual mining physical root");
 create_mon(c,QOL_PLAYER_PARTY,1,20);
 for(unsigned i=100;i<600;++i)write8(c,QOL_PLAYER_PARTY+i,0);
 write8(c,QOL_PLAYER_PARTY_COUNT,1);
 for(unsigned i=0;i<4;++i)set_mon_data_u32(c,QOL_PLAYER_PARTY,MON_DATA_MOVE1+i,i==0&&mode!=1?249:33);
 (void)call_preserving(c,mode==0?QOL_FLAG_CLEAR:QOL_FLAG_SET,0x825,0,0,0);
 unsigned badge=call_preserving(c,QOL_FLAG_GET,0x825,0,0,0),move=call_preserving(c,BATTLE_CORE_GET_MON_DATA,QOL_PLAYER_PARTY,MON_DATA_MOVE1,0,0);
 si_need(badge==(mode!=0)&&move==(mode!=1?249:33),"stock badge/move fixture readback");
 printf("{\"setup\":\"mining\",\"events\":%u,\"record\":%u,\"script\":%u,\"badge\":%u,\"move\":%u,\"party_count\":1,\"progression_is_fixture\":true,\"rp_injected\":false}\n",e,r,read32(c,r+16),badge,move);fflush(stdout);
 run_key_frames(c,0,2);(void)qol_call5_preserving(c,QOL_SET_WARP_DESTINATION,97,82,255,1,21);
 (void)call_preserving(c,QOL_RESET_INITIAL_AVATAR,0,0,0,0);(void)call_preserving(c,QOL_WARP_INTO_MAP,0,0,0,0);
 qol_write32(c,QOL_FIELD_CALLBACK_SLOT,QOL_DEFAULT_WARP_EXIT);(void)call_preserving(c,QOL_SET_MAIN_CALLBACK2,QOL_CB2_LOAD_MAP,0,0,0);si_guard(c);
 for(unsigned i=0;i<900;++i)uc_frame(c,0);rm_stance(c);
 si_need(rm_rock(c)==1,"live rock before interaction");
 si_need(read8(c,SI_VOL+28)==0&&read8(c,SI_VOL+34)==0&&si_read16(c,SI_VOL+20)==65535,"real services only");return c;
}
static void rm_visit(struct mCore *c,const char *stage,bool confirm,bool eligible,unsigned expected) {
 rm_stance(c);si_need(rm_rock(c)==1,"rock present before physical A");
 unsigned target=read32(c,SI_COUNTER)+(eligible&&confirm&&expected==0?2:0);
 unsigned id=read8(c,0x02036FB1U);
 if((read8(c,0x02036D6CU+36*id+0x18)&15)!=2)uc_tap(c,QOL_KEY_UP);
 if(si_field(c))uc_tap(c,QOL_KEY_A);
 si_need(!si_field(c),"physical rock script entered");
 for(unsigned i=0;i<90;++i)uc_frame(c,0);
 char label[80];snprintf(label,sizeof(label),"%s-prompt",stage);rm_screen(label);
 bool shown=false;
 for(unsigned n=0;n<240;++n){
  if(si_field(c)){
   if(eligible&&confirm)si_need(si_read16(c,SI_VOL+16)==expected,"real mining result");
   si_need(rm_rock(c)==(unsigned)!(eligible&&confirm),"only successful standard rock action removes rock");
   printf("{\"visit\":\"%s\",\"confirmed\":%s,\"eligible\":%s,\"result\":%u,\"rp\":%u,\"counter\":%u,\"rock_count\":%u,\"frame\":%u}\n",stage,confirm?"true":"false",eligible?"true":"false",si_read16(c,SI_VOL+16),si_read16(c,SI_OWNER+4),read32(c,SI_COUNTER),rm_rock(c),uc_frames);fflush(stdout);return;
  }
  uc_tap(c,confirm?QOL_KEY_A:QOL_KEY_B);
  if(eligible&&confirm&&!shown&&rm_rock(c)==0&&si_read16(c,SI_OWNER+4)==10&&si_read16(c,SI_VOL+16)==expected&&read32(c,SI_COUNTER)==target&&!si_field(c)){
   for(unsigned i=0;i<180;++i)uc_frame(c,0);snprintf(label,sizeof(label),"%s-outcome",stage);rm_screen(label);shown=true;
   si_need(!si_field(c)&&rm_rock(c)==0,"reward text before wild encounter tail");
   printf("{\"visit\":\"%s\",\"confirmed\":true,\"eligible\":true,\"result\":%u,\"rp\":%u,\"counter\":%u,\"rock_count\":0,\"frame\":%u,\"stopped_before_wild_tail\":true}\n",stage,si_read16(c,SI_VOL+16),si_read16(c,SI_OWNER+4),read32(c,SI_COUNTER),uc_frames);fflush(stdout);return;
  }
 }
 rm_screen("bounded-failure");fprintf(stderr,"mining bound result=%u RP=%u rock=%u cb=%08x lock=%u frame=%u\n",si_read16(c,SI_VOL+16),si_read16(c,SI_OWNER+4),rm_rock(c),read32(c,BATTLE_CORE_MAIN_CALLBACK2),read8(c,0x03000F9CU),uc_frames);si_die("bounded mining keys");
}
/* 岩の消去は同mapのContinueにも保存される。cap試験は別coreの開始fixtureで
 * 隣接階97/81へstock warpして戻す。自然な往復到達の受入ではない。 */
static void rm_reentry_fixture(struct mCore *c) {
 for(unsigned step=0;step<2;++step){
  unsigned map=step?82:81,x=step?1:2,y=step?21:3;
  (void)qol_call5_preserving(c,QOL_SET_WARP_DESTINATION,97,map,255,x,y);
  (void)call_preserving(c,QOL_RESET_INITIAL_AVATAR,0,0,0,0);
  (void)call_preserving(c,QOL_WARP_INTO_MAP,0,0,0,0);
  qol_write32(c,QOL_FIELD_CALLBACK_SLOT,QOL_DEFAULT_WARP_EXIT);
  (void)call_preserving(c,QOL_SET_MAIN_CALLBACK2,QOL_CB2_LOAD_MAP,0,0,0);
  if(step)si_guard(c);
  for(unsigned i=0;i<900;++i)uc_frame(c,0);
 }
 rm_stance(c);si_need(rm_rock(c)==1,"stock reentry restores physical rock");
 printf("{\"reentry_fixture\":true,\"stock_warps\":2,\"rp_injected\":false,\"natural_reentry_accepted\":false}\n");fflush(stdout);
}
static void rm_invariants(struct mCore *c,const uint8_t *base,const unsigned *items,const uint8_t *party,bool earned,unsigned counter) {
 uint8_t want[2048];memcpy(want,base,2048);
 if(earned){lc_w16(want,0x743,10);lc_w32(want,0x749,10);lc_w16(want,0x755,10);want[0x75a]=2;lc_w32(want,0x763,2);lc_w32(want,8,lc_checksum(want));}
 uc_same_ledger(c,want);for(unsigned i=0;i<600;++i)if(party[i]!=read8(c,QOL_PLAYER_PARTY+i))fprintf(stderr,"party diff %u %02x -> %02x\n",i,party[i],read8(c,QOL_PLAYER_PARTY+i));uc_same_inventory(c,items,party);si_need(read32(c,SI_COUNTER)==counter,"mining exact Flash transaction count");
}
int main(int argc,char**argv){
 si_need(argc==4,"mining case required");unsigned mode=!strcmp(argv[3],"mining-missing-badge")?0:!strcmp(argv[3],"mining-missing-move")?1:!strcmp(argv[3],"mining-earn-cold-cap")?2:99;si_need(mode<3,"closed mining cases");
 char sha[65];sha256_file(argv[1],sha);si_need(!strcmp(sha,UC_ROM),"repaired candidate");sha256_file(argv[2],sha);si_need(!strcmp(sha,UC_FIXTURE),"zero RP fixture");
 struct mLogger logger={.log=qol_log};mLogSetDefaultLogger(&logger);struct mCore *c=rm_setup(argv[1],argv[2],mode);
 uint8_t ledger[2048],party[600],flash[131072],now[131072];unsigned items[2048];lc_read(c,ledger);for(unsigned i=0;i<600;++i)party[i]=read8(c,QOL_PLAYER_PARTY+i);si_inventory(c,items);uc_copy_flash(c,flash);unsigned counter=read32(c,SI_COUNTER);
 si_need(si_read16(c,SI_OWNER+4)==0&&si_read32(c,SI_OWNER+10)==0&&read8(c,SI_OWNER+27)==0,"no mining credit injected");lc_event(c,"fixture");rm_screen("fixture-field");
 if(mode<2){
  rm_visit(c,"locked",true,false,0);rm_invariants(c,ledger,items,party,false,counter);uc_copy_flash(c,now);si_need(!memcmp(flash,now,sizeof(flash)),"locked no Flash write");lc_event(c,"rejected");qol_close(c);
 }else{
  rm_visit(c,"decline",false,true,0);rm_invariants(c,ledger,items,party,false,counter);uc_copy_flash(c,now);si_need(!memcmp(flash,now,sizeof(flash)),"decline no Flash write");lc_event(c,"declined");
  rm_visit(c,"earn",true,true,0);rm_invariants(c,ledger,items,party,true,counter+2);uc_copy_flash(c,now);si_need(memcmp(flash,now,sizeof(flash)),"earned real Flash write");memcpy(flash,now,sizeof(flash));lc_event(c,"earned");qol_close(c);
  c=ct_open(argv[1],argv[2]);si_guard(c);rm_stance(c);rm_invariants(c,ledger,items,party,true,counter+2);uc_copy_flash(c,now);si_need(!memcmp(flash,now,sizeof(flash)),"independent Continue no extra save");lc_event(c,"continued");rm_screen("continued-field");qol_close(c);
  c=ct_open(argv[1],argv[2]);rm_reentry_fixture(c);rm_invariants(c,ledger,items,party,true,counter+2);uc_copy_flash(c,now);si_need(!memcmp(flash,now,sizeof(flash)),"reentry fixture does not save");lc_event(c,"reentered");
  rm_visit(c,"cold_cap",true,true,4);rm_invariants(c,ledger,items,party,true,counter+2);uc_copy_flash(c,now);si_need(!memcmp(flash,now,sizeof(flash)),"daily cap no Flash write");lc_event(c,"cold_cap");qol_close(c);
 }
 si_need(!log_problem_count,"mining mGBA warnings/errors");
 printf("{\"status\":\"PASS\",\"case\":\"%s\",\"candidate_sha256\":\"%s\",\"fresh_cores\":%u,\"earned_rp\":%u,\"transaction_saves\":%u,\"manual_saves\":0,\"guarded_host_writes\":0,\"accepted_case_reruns\":0,\"natural_arrival_accepted\":false,\"all_activities_accepted\":false,\"warnings_errors\":0}\n",argv[3],UC_ROM,si_cores,mode==2?10:0,mode==2?2:0);return 0;
}
