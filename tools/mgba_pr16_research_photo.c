/* 実写真イベントのみ。0RP/進行はディスクfixture、開始warp後はキーだけ。
 * CreditActivity/FieldPhotoのhost呼出し、RP/result/claim書込は禁止。 */
static void ph_stance(struct mCore*c){
 unsigned s=read32(c,QOL_SAVE_BLOCK1_SLOT),id=read8(c,0x02036FB1U),obj=0x02036D6CU+36*id;
 if(!si_field(c)||read8(c,s+4)!=96||read8(c,s+5)!=37||read16(c,s)!=48||read16(c,s+2)!=5){char hash[65];ct_screen(9,hash);fprintf(stderr,"stance frame=%u field=%u map=%u/%u pos=%u/%u facing=%u lock=%u\n",uc_frames,si_field(c),read8(c,s+4),read8(c,s+5),read16(c,s),read16(c,s+2),read8(c,obj+0x18)&15,read8(c,0x03000F9CU));}
 si_need(si_field(c)&&read8(c,s+4)==96&&read8(c,s+5)==37&&read16(c,s)==48&&read16(c,s+2)==5,"photo stance map/tile");
 si_need(id<16&&(read8(c,obj)&1)&&read16(c,obj+0x10)==55&&read16(c,obj+0x12)==12,"photo player object");

}
static struct mCore*ph_setup(const char*rom,const char*save){
 struct mCore*c=ct_open(rom,save);unsigned events=read32(c,0x092C0B20U),bgs=read32(c,events+16),script=read32(c,bgs+8);
 si_need(events==0x09413750U&&bgs==0x09413708U&&script==0x093C05E4U&&read16(c,bgs)==48&&read16(c,bgs+2)==4,"actual photo background root");
 printf("{\"binding\":\"map96/37-background0\",\"events\":%u,\"backgrounds\":%u,\"script\":%u,\"x\":48,\"y\":4,\"activity\":5,\"points\":6,\"cap\":6}\n",events,bgs,script);fflush(stdout);
 run_key_frames(c,0,2);
 (void)qol_call5_preserving(c,QOL_SET_WARP_DESTINATION,96,37,255,48,5);
 (void)call_preserving(c,QOL_RESET_INITIAL_AVATAR,0,0,0,0);
 (void)call_preserving(c,QOL_WARP_INTO_MAP,0,0,0,0);
 qol_write32(c,QOL_FIELD_CALLBACK_SLOT,QOL_DEFAULT_WARP_EXIT);
 (void)call_preserving(c,QOL_SET_MAIN_CALLBACK2,QOL_CB2_LOAD_MAP,0,0,0);si_guard(c);
 for(unsigned i=0;i<900;++i)uc_frame(c,0);ph_stance(c);
 si_need(read8(c,SI_VOL+28)==0&&read8(c,SI_VOL+34)==0&&si_read16(c,SI_VOL+20)==65535,"real services only");
 return c;
}
static void ph_invariants(struct mCore*c,const uint8_t*base,const unsigned*items,const uint8_t*party,bool earned,unsigned counter){
 uint8_t want[2048];memcpy(want,base,2048);
 if(earned){lc_w16(want,0x743,6);lc_w32(want,0x749,6);lc_w16(want,0x757,6);want[0x75a]=4;lc_w32(want,0x763,2);lc_w32(want,8,lc_checksum(want));}
 uc_same_ledger(c,want);uc_same_inventory(c,items,party);si_need(read32(c,SI_COUNTER)==counter,"photo exact transaction count");
}
static void ph_screen(const char*stage,const char*kind,char hash[65]){
 char name[96];ct_screen(20,hash);snprintf(name,sizeof(name),"photo-%s-%s.ppm",stage,kind);
 si_need(rename("catalog-page-20.ppm",name)==0,"unique photo screenshot");
}
static void ph_visit(struct mCore*c,const char*stage,bool confirm,unsigned result){
 unsigned target=read32(c,SI_COUNTER)+(confirm&&result==0?2:0);
 ph_stance(c);unsigned id=read8(c,0x02036FB1U),keys=0;
 if((read8(c,0x02036D6CU+36*id+0x18)&15)!=2){uc_tap(c,QOL_KEY_UP);keys|=QOL_KEY_UP;}
 if(si_field(c)){uc_tap(c,QOL_KEY_A);keys|=QOL_KEY_A;}
 si_need(!si_field(c),"background script entered by physical keys");
 for(unsigned i=0;i<90;++i)uc_frame(c,0);
 char hash[65];ph_screen(stage,"prompt",hash);printf("{\"prompt\":\"%s\",\"entry_keys\":%u,\"screen_sha256\":\"%s\"}\n",stage,keys,hash);fflush(stdout);
 bool shown=false;for(unsigned n=0;n<80;++n){
  if(si_field(c)){
   if(confirm)si_need(si_read16(c,SI_VOL+16)==result,"real photo activity result");
   printf("{\"visit\":\"%s\",\"confirmed\":%s,\"activity_result\":%u,\"frame\":%u}\n",stage,confirm?"true":"false",si_read16(c,SI_VOL+16),uc_frames);fflush(stdout);return;
  }
  uc_tap(c,confirm?QOL_KEY_A:QOL_KEY_B);
  if(confirm&&!shown&&si_read16(c,SI_OWNER+4)==6&&si_read16(c,SI_VOL+16)==result&&read32(c,SI_COUNTER)==target&&!si_field(c)){
   for(unsigned i=0;i<180;++i)uc_frame(c,0);ph_screen(stage,"outcome",hash);
   printf("{\"outcome\":\"%s\",\"screen_sha256\":\"%s\"}\n",stage,hash);fflush(stdout);shown=true;
  }
 }
 fprintf(stderr,"photo limit result=%u owner=%u cb=%08x lock=%u\n",si_read16(c,SI_VOL+16),si_read16(c,SI_OWNER+4),read32(c,BATTLE_CORE_MAIN_CALLBACK2),read8(c,0x03000F9CU));si_die("photo input bound");
}
int main(int argc,char**argv){
 if(argc==3&&!strcmp(argv[1],"--guard-check"))si_guard_check(argv[2]);
 si_need(argc==4&&!strcmp(argv[3],"photo-zero-earn-duplicate-cold-continue"),"photo case");char sha[65];
 sha256_file(argv[1],sha);si_need(!strcmp(sha,UC_ROM),"photo candidate");sha256_file(argv[2],sha);si_need(!strcmp(sha,UC_FIXTURE),"zero-RP fixture");
 struct mLogger logger={.log=qol_log};mLogSetDefaultLogger(&logger);struct mCore*c=ph_setup(argv[1],argv[2]);
 uint8_t ledger[2048],party[600],flash[131072],check[131072];unsigned items[2048];
 lc_read(c,ledger);for(unsigned i=0;i<600;++i)party[i]=read8(c,QOL_PLAYER_PARTY+i);si_inventory(c,items);uc_copy_flash(c,flash);
 unsigned counter=read32(c,SI_COUNTER);si_need(si_read16(c,SI_OWNER+4)==0&&si_read32(c,SI_OWNER+10)==0&&read8(c,SI_OWNER+27)==0,"no initial earned RP");lc_event(c,"fixture");
 ph_visit(c,"decline",false,0);ph_invariants(c,ledger,items,party,false,counter);uc_copy_flash(c,check);si_need(!memcmp(flash,check,131072),"decline no Flash byte change");lc_event(c,"declined");
 ph_visit(c,"earn",true,0);ph_invariants(c,ledger,items,party,true,counter+2);uc_copy_flash(c,check);si_need(memcmp(flash,check,131072),"actual durable earn writes Flash");memcpy(flash,check,131072);lc_event(c,"earned");
 ph_visit(c,"duplicate",true,4);ph_invariants(c,ledger,items,party,true,counter+2);uc_copy_flash(c,check);si_need(!memcmp(flash,check,131072),"same-day duplicate no Flash write");lc_event(c,"duplicate");qol_close(c);
 c=ct_open(argv[1],argv[2]);si_guard(c);ph_stance(c);ph_invariants(c,ledger,items,party,true,counter+2);uc_copy_flash(c,check);si_need(!memcmp(flash,check,131072),"cold Continue no extra save");lc_event(c,"continued");
 ph_visit(c,"duplicate_after_continue",true,4);ph_invariants(c,ledger,items,party,true,counter+2);uc_copy_flash(c,check);si_need(!memcmp(flash,check,131072),"cold duplicate no Flash write");lc_event(c,"duplicate_after_continue");qol_close(c);
 si_need(!log_problem_count,"photo mGBA warnings/errors");
 printf("{\"status\":\"PASS\",\"case\":\"photo-zero-earn-duplicate-cold-continue\",\"candidate_sha256\":\"%s\",\"fresh_cores\":%u,\"initial_rp\":0,\"earned_rp\":6,\"daily_photo\":6,\"simple_claims\":4,\"transaction_saves\":2,\"manual_saves\":0,\"guarded_host_writes\":0,\"real_photo_earning_accepted\":true,\"all_activities_accepted\":false,\"natural_arrival_accepted\":false,\"shop_connection_accepted\":false,\"accepted_case_reruns\":0,\"warnings_errors\":%u}\n",UC_ROM,si_cores,log_problem_count);return 0;
}
