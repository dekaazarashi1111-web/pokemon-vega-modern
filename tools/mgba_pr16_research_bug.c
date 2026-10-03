/* 虫取りの実NPC。party/進行/warpは開始fixture。barrier後はキーと読取のみ。 */
static void rb_stance(struct mCore*c){
 unsigned s=read32(c,QOL_SAVE_BLOCK1_SLOT);
 si_need(si_field(c)&&read8(c,s+4)==97&&read8(c,s+5)==0&&read16(c,s)==43&&read16(c,s+2)==7,"bug stance map/tile");
}
static struct mCore*rb_setup(const char*rom,const char*save,bool bug){
 struct mCore*c=ct_open(rom,save);unsigned e=read32(c,0x092C0B80U),objs=read32(c,e+4),r=objs+24*10;
 si_need(e==0x09413968U&&read8(c,e)==15&&read8(c,r)==11&&read16(c,r+4)==43&&read16(c,r+6)==6&&read32(c,r+16)==0x093C048CU,"current actual bug NPC root");
 unsigned species=bug?39:1,stats=read32(c,0x080001BCU)+32*species;
 si_need((read8(c,stats+6)==6||read8(c,stats+7)==6)==bug,"candidate native Bug type fixture");
 create_mon(c,QOL_PLAYER_PARTY,(uint16_t)species,20);for(unsigned i=100;i<600;++i)write8(c,QOL_PLAYER_PARTY+i,0);write8(c,QOL_PLAYER_PARTY_COUNT,1);
 printf("{\"setup\":\"bug\",\"events\":%u,\"record\":%u,\"script\":%u,\"species\":%u,\"type1\":%u,\"type2\":%u,\"party_count\":1,\"progression_is_fixture\":true,\"rp_injected\":false}\n",e,r,read32(c,r+16),species,read8(c,stats+6),read8(c,stats+7));fflush(stdout);
 run_key_frames(c,0,2);(void)qol_call5_preserving(c,QOL_SET_WARP_DESTINATION,97,0,255,43,7);
 (void)call_preserving(c,QOL_RESET_INITIAL_AVATAR,0,0,0,0);(void)call_preserving(c,QOL_WARP_INTO_MAP,0,0,0,0);
 qol_write32(c,QOL_FIELD_CALLBACK_SLOT,QOL_DEFAULT_WARP_EXIT);(void)call_preserving(c,QOL_SET_MAIN_CALLBACK2,QOL_CB2_LOAD_MAP,0,0,0);si_guard(c);
 for(unsigned i=0;i<900;++i)uc_frame(c,0);rb_stance(c);
 si_need(read8(c,SI_VOL+28)==0&&read8(c,SI_VOL+34)==0&&si_read16(c,SI_VOL+20)==65535,"real services only");return c;
}
static void rb_screen(const char*stage,const char*kind){
 char hash[65],name[100];ct_screen(30,hash);snprintf(name,sizeof(name),"bug-%s-%s.ppm",stage,kind);si_need(rename("catalog-page-30.ppm",name)==0,"unique bug image");
 printf("{\"screen\":\"%s\",\"sha256\":\"%s\"}\n",name,hash);fflush(stdout);
}
static void rb_visit(struct mCore*c,const char*stage,bool confirm,unsigned result,unsigned rp){
 rb_stance(c);unsigned id=read8(c,0x02036FB1U),counter=read32(c,SI_COUNTER),target=counter+(confirm&&result==0?2:0);
 if((read8(c,0x02036D6CU+36*id+0x18)&15)!=2)uc_tap(c,QOL_KEY_UP);
 if(si_field(c))uc_tap(c,QOL_KEY_A);si_need(!si_field(c),"physical NPC conversation entered");
 for(unsigned i=0;i<90;++i)uc_frame(c,0);rb_screen(stage,"prompt");
 bool shown=false;for(unsigned n=0;n<120;++n){
  if(si_field(c)){
   si_need(!confirm||si_read16(c,SI_VOL+16)==result,"native bug result");
   printf("{\"visit\":\"%s\",\"confirmed\":%s,\"result\":%u,\"rp\":%u,\"counter\":%u,\"frame\":%u}\n",stage,confirm?"true":"false",si_read16(c,SI_VOL+16),si_read16(c,SI_OWNER+4),read32(c,SI_COUNTER),uc_frames);fflush(stdout);return;
  }
  uc_tap(c,confirm?QOL_KEY_A:QOL_KEY_B);
  if(confirm&&!shown&&si_read16(c,SI_OWNER+4)==rp&&si_read16(c,SI_VOL+16)==result&&read32(c,SI_COUNTER)==target&&!si_field(c)){
   for(unsigned i=0;i<180;++i)uc_frame(c,0);rb_screen(stage,"outcome");shown=true;
  }
 }
 fprintf(stderr,"bug input limit result=%u RP=%u cb=%08x lock=%u frame=%u\n",si_read16(c,SI_VOL+16),si_read16(c,SI_OWNER+4),read32(c,BATTLE_CORE_MAIN_CALLBACK2),read8(c,0x03000F9CU),uc_frames);si_die("bug bounded keys");
}
static void rb_invariants(struct mCore*c,const uint8_t*base,const unsigned*items,const uint8_t*party,bool earned,unsigned counter){
 uint8_t want[2048];memcpy(want,base,2048);
 if(earned){lc_w16(want,0x743,8);lc_w32(want,0x749,8);lc_w16(want,0x753,8);want[0x75a]=1;lc_w32(want,0x763,2);lc_w32(want,8,lc_checksum(want));}
 uc_same_ledger(c,want);uc_same_inventory(c,items,party);si_need(read32(c,SI_COUNTER)==counter,"bug exact save counter");
}
int main(int argc,char**argv){
 si_need(argc==4,"bug case required");bool bug=!strcmp(argv[3],"bug-earn-duplicate-cold");si_need(bug||!strcmp(argv[3],"bug-missing-type-rejected"),"closed bug cases");
 char sha[65];sha256_file(argv[1],sha);si_need(!strcmp(sha,UC_ROM),"map-view repaired candidate");sha256_file(argv[2],sha);si_need(!strcmp(sha,UC_FIXTURE),"zero-RP fixture");
 struct mLogger logger={.log=qol_log};mLogSetDefaultLogger(&logger);struct mCore*c=rb_setup(argv[1],argv[2],bug);
 uint8_t ledger[2048],party[600],flash[131072],now[131072];unsigned items[2048];lc_read(c,ledger);for(unsigned i=0;i<600;++i)party[i]=read8(c,QOL_PLAYER_PARTY+i);si_inventory(c,items);uc_copy_flash(c,flash);unsigned counter=read32(c,SI_COUNTER);
 si_need(si_read16(c,SI_OWNER+4)==0&&si_read32(c,SI_OWNER+10)==0&&read8(c,SI_OWNER+27)==0,"no earned credit before NPC");lc_event(c,"fixture");rb_screen("fixture","field");
 if(!bug){
  rb_visit(c,"missing",true,3,0);rb_invariants(c,ledger,items,party,false,counter);uc_copy_flash(c,now);si_need(!memcmp(flash,now,sizeof(flash)),"missing type no Flash write");lc_event(c,"rejected");qol_close(c);
 }else{
  rb_visit(c,"decline",false,0,0);rb_invariants(c,ledger,items,party,false,counter);uc_copy_flash(c,now);si_need(!memcmp(flash,now,sizeof(flash)),"decline no Flash write");lc_event(c,"declined");
  rb_visit(c,"earn",true,0,8);rb_invariants(c,ledger,items,party,true,counter+2);uc_copy_flash(c,now);si_need(memcmp(flash,now,sizeof(flash)),"earn writes real Flash");memcpy(flash,now,sizeof(flash));lc_event(c,"earned");
  rb_visit(c,"duplicate",true,4,8);rb_invariants(c,ledger,items,party,true,counter+2);uc_copy_flash(c,now);si_need(!memcmp(flash,now,sizeof(flash)),"duplicate no Flash write");lc_event(c,"duplicate");qol_close(c);
  c=ct_open(argv[1],argv[2]);si_guard(c);rb_stance(c);rb_invariants(c,ledger,items,party,true,counter+2);uc_copy_flash(c,now);si_need(!memcmp(flash,now,sizeof(flash)),"cold Continue no write");lc_event(c,"continued");rb_screen("continued","field");
  rb_visit(c,"cold_duplicate",true,4,8);rb_invariants(c,ledger,items,party,true,counter+2);uc_copy_flash(c,now);si_need(!memcmp(flash,now,sizeof(flash)),"cold duplicate no write");lc_event(c,"cold_duplicate");qol_close(c);
 }
 si_need(!log_problem_count,"bug mGBA warnings/errors");printf("{\"status\":\"PASS\",\"case\":\"%s\",\"candidate_sha256\":\"%s\",\"fresh_cores\":%u,\"earned_rp\":%u,\"transaction_saves\":%u,\"manual_saves\":0,\"guarded_host_writes\":0,\"accepted_case_reruns\":0,\"natural_arrival_accepted\":false,\"all_activities_accepted\":false,\"warnings_errors\":0}\n",argv[3],UC_ROM,si_cores,bug?8:0,bug?2:0);return 0;
}
