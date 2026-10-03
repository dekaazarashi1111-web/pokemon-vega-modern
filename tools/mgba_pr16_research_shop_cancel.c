/* 実背景イベント→実ショップ取消。warp/進行/残高は停止fixture、
 * 観測中は通常入力のみ。shop関数/PC/戻り値/選択結果の注入は行わない。 */
static unsigned uc_frames;
static void uc_frame(struct mCore*c,unsigned key){run_key_frames(c,key,1);++uc_frames;}
/* 既存qol_pressと同じ2frame押下。1frameでは受付周期を跨がない。 */
static void uc_tap(struct mCore*c,unsigned key){for(unsigned i=0;i<2;++i)uc_frame(c,key);for(unsigned i=0;i<30;++i)uc_frame(c,0);}
static bool uc_active(struct mCore*c){return read8(c,SI_VOL+33)==1;}
static void uc_copy_flash(struct mCore*c,uint8_t*out){
 struct GBASavedata*s=&((struct GBA*)c->board)->memory.savedata;
 si_need(s->type==SAVEDATA_FLASH1M&&s->data,"real Flash");memcpy(out,s->data,131072);
}
static void uc_normalize(uint8_t*b,unsigned minute){b[0x746]=(uint8_t)minute;lc_w32(b,8,lc_checksum(b));}
static void uc_same_ledger(struct mCore*c,const uint8_t*expected){
 uint8_t b[2048];lc_read(c,b);si_need(lc_checksum(b)==lc_u32(b,8),"valid full ledger");
 si_need(b[0x746]>=expected[0x746]&&b[0x746]-expected[0x746]<=2,"bounded real minute only");
 uc_normalize(b,expected[0x746]);si_need(!memcmp(b,expected,2048),"all ledger bytes except ordinary minute unchanged");
}
static void uc_same_inventory(struct mCore*c,const unsigned*inventory,const uint8_t*party){
 unsigned now[2048];si_inventory(c,now);si_need(!memcmp(now,inventory,sizeof(now)),"all five Bag pockets unchanged");
 for(unsigned i=0;i<600;++i)si_need(read8(c,QOL_PLAYER_PARTY+i)==party[i],"all party bytes unchanged");
}
static void uc_open_shop(struct mCore*c,const char*stage){
 uc_tap(c,QOL_KEY_UP);
 for(unsigned n=0;n<900;++n){
  if(uc_active(c)){
   unsigned count=read8(c,SI_VOL+30),window=read8(c,SI_VOL+32);
   si_need(count>=1&&count<=23&&window<32&&read8(c,SI_VOL+31)==0,"real first menu page/window");
   si_need(si_read16(c,SI_VOL+18)==65535&&si_read16(c,SI_VOL+16)==9,"native busy/unselected");
   unsigned task_count=0,callback=0;
   for(unsigned t=0;t<16;++t){unsigned a=0x030050D0U+40*t;if(read8(c,a+4)&&read32(c,a)>=0x093BD000U&&read32(c,a)<0x093C0000U){++task_count;callback=read32(c,a);}}
   si_need(task_count==1,"one Research native task");
   printf("{\"shop_open\":\"%s\",\"eligible_count\":%u,\"window\":%u,\"callback\":%u,\"native_tasks\":%u}\n",stage,count,window,callback,task_count);fflush(stdout);for(unsigned i=0;i<30;++i)uc_frame(c,0);return;
  }
  uc_frame(c,n%60==0?QOL_KEY_A:0);
 }
 fprintf(stderr,"shop open limit active=%u result=%u cb=%08x lock=%u page=%u count=%u\n",read8(c,SI_VOL+33),si_read16(c,SI_VOL+16),read32(c,BATTLE_CORE_MAIN_CALLBACK2),read8(c,0x03000F9CU),read8(c,SI_VOL+31),read8(c,SI_VOL+30));
 si_die("background interaction did not open Research shop");
}
static void uc_closed(struct mCore*c){
 for(unsigned n=0;n<900;++n){
  if(!uc_active(c)&&si_field(c)){
   si_need(si_read16(c,SI_VOL+18)==65535&&si_read16(c,SI_VOL+16)==2&&read8(c,SI_VOL+32)==255,"native cancellation/window release");
   for(unsigned t=0;t<16;++t){unsigned a=0x030050D0U+40*t;si_need(!(read8(c,a+4)&&read32(c,a)>=0x093BD000U&&read32(c,a)<0x093C0000U),"no leaked Research task");}
   return;
  }
  uc_frame(c,n%60==0?QOL_KEY_B:0);
 }
 si_die("cancel did not return to idle field");
}
int main(int argc,char**argv){
 if(argc==3&&!strcmp(argv[1],"--guard-check"))si_guard_check(argv[2]);
 si_need(argc==4&&!strcmp(argv[3],"shop-two-cancels-save-continue"),"closed native shop case");char sha[65];
 sha256_file(argv[1],sha);si_need(!strcmp(sha,UC_ROM),"unchanged current candidate");
 sha256_file(argv[2],sha);si_need(!strcmp(sha,UC_FIXTURE),"exact private progress fixture");
 struct mLogger logger={.log=qol_log};mLogSetDefaultLogger(&logger);struct mCore*c=si_open(argv[1],argv[2]);
 unsigned events=read32(c,0x092C2AE0U);si_need(events>=0x08000000U&&events+20<0x0A000000U,"map98/3 event header");
 unsigned bgs=read32(c,events+16);si_need(read8(c,events+3)>=2&&bgs>=0x08000000U&&bgs+24<0x0A000000U,"background records");
 unsigned script=read32(c,bgs+8);si_need(read16(c,bgs)==2&&read16(c,bgs+2)==1&&script>=0x08000000U&&script<0x0A000000U,"authored shop (2,1) root");
 printf("{\"binding\":\"map98/3-background0\",\"events\":%u,\"backgrounds\":%u,\"script\":%u,\"x\":2,\"y\":1}\n",events,bgs,script);fflush(stdout);
 /* Stopped setup only: enter this map through the stock warp delegates. */
 run_key_frames(c,0,2);
 (void)qol_call5_preserving(c,QOL_SET_WARP_DESTINATION,98,3,255,2,2);
 (void)call_preserving(c,QOL_RESET_INITIAL_AVATAR,0,0,0,0);
 (void)call_preserving(c,QOL_WARP_INTO_MAP,0,0,0,0);
 qol_write32(c,QOL_FIELD_CALLBACK_SLOT,QOL_DEFAULT_WARP_EXIT);
 (void)call_preserving(c,QOL_SET_MAIN_CALLBACK2,QOL_CB2_LOAD_MAP,0,0,0);
 si_guard(c);
 for(unsigned i=0;i<900;++i)uc_frame(c,0);
 unsigned save=read32(c,QOL_SAVE_BLOCK1_SLOT);
 si_need(save>=0x02000000U&&save+12<0x02040000U,"save block");
 if(!si_field(c))fprintf(stderr,"warp cb=%08x lock=%u quest=%u/%u\n",read32(c,BATTLE_CORE_MAIN_CALLBACK2),read8(c,0x03000F9CU),read8(c,0x0203AD72U),read8(c,0x03005ED8U));
 si_need(si_field(c)&&read8(c,save+4)==98&&read8(c,save+5)==3&&read16(c,save)==2&&read16(c,save+2)==2,"fixture enters actual shop map/tile");
 si_need(read8(c,SI_VOL+28)==0&&read8(c,SI_VOL+34)==0&&si_read16(c,SI_VOL+20)==65535,"no runtime test/mock services");
 printf("{\"fixture\":\"stock-warp-only\",\"map_group\":98,\"map_num\":3,\"x\":2,\"y\":2,\"shop_dispatch_injected\":false,\"guarded_host_writes\":0}\n");fflush(stdout);
 uint8_t before[2048],party[600],flash[131072],check[131072];unsigned inventory[2048];
 lc_read(c,before);for(unsigned i=0;i<600;++i)party[i]=read8(c,QOL_PLAYER_PARTY+i);si_inventory(c,inventory);uc_copy_flash(c,flash);
 unsigned counter=read32(c,SI_COUNTER),count=read8(c,QOL_PLAYER_PARTY_COUNT);lc_event(c,"fixture");
 uc_open_shop(c,"b");uc_tap(c,QOL_KEY_B);uc_closed(c);
 uc_same_ledger(c,before);uc_same_inventory(c,inventory,party);uc_copy_flash(c,check);si_need(!memcmp(flash,check,131072)&&read32(c,SI_COUNTER)==counter,"B cancel no persistence");lc_event(c,"cancel_b");
 uc_open_shop(c,"row");unsigned eligible=read8(c,SI_VOL+30),pages=(eligible+4)/5;
 for(unsigned page=0;page<pages;++page){
  unsigned rows=eligible-5*page;if(rows>5)rows=5;
  si_need(read8(c,SI_VOL+31)==page,"actual page index");
  for(unsigned row=0;row<rows;++row)uc_tap(c,QOL_KEY_DOWN);
  uc_tap(c,QOL_KEY_A);
  if(page+1<pages){if(!uc_active(c)||read8(c,SI_VOL+31)!=page+1)fprintf(stderr,"page transition expected=%u got=%u active=%u selected=%u result=%u\n",page+1,read8(c,SI_VOL+31),read8(c,SI_VOL+33),si_read16(c,SI_VOL+18),si_read16(c,SI_VOL+16));si_need(uc_active(c)&&read8(c,SI_VOL+31)==page+1,"normal next page action");}
 }
 uc_closed(c);uc_same_ledger(c,before);uc_same_inventory(c,inventory,party);uc_copy_flash(c,check);
 si_need(!memcmp(flash,check,131072)&&read32(c,SI_COUNTER)==counter,"row cancel no persistence");lc_event(c,"cancel_row");
 si_need(si_normal_save(c),"ordinary Start Save after cancellations");uc_same_ledger(c,before);uc_same_inventory(c,inventory,party);
 si_need(read32(c,SI_COUNTER)==counter+1,"exact one manual save");lc_read(c,before);lc_event(c,"saved");qol_close(c);
 for(unsigned pass=0;pass<2;++pass){
  c=si_open(argv[1],argv[2]);si_guard(c);uc_same_ledger(c,before);uc_same_inventory(c,inventory,party);
  si_need(read32(c,SI_COUNTER)==counter+1&&read8(c,QOL_PLAYER_PARTY_COUNT)==count,"fresh Continue counter/party");
  si_need(!uc_active(c)&&read8(c,SI_VOL+32)==255&&si_read16(c,SI_VOL+18)==65535,"cold reset has no stale UI state");
  lc_event(c,pass?"continued_again":"continued");qol_close(c);
 }
 si_need(!log_problem_count,"mGBA warnings/errors");
 printf("{\"status\":\"PASS\",\"scope\":\"NATIVE_RESEARCH_SHOP_TWO_CANCELS_AND_SAVE_CONTINUE\",\"case\":\"shop-two-cancels-save-continue\",\"candidate_sha256\":\"%s\",\"fresh_cores\":%u,\"cancel_routes\":2,\"eligible_count\":%u,\"pages\":%u,\"manual_saves\":1,\"transaction_saves\":0,\"host_write_barriers\":7,\"guarded_host_writes\":0,\"frames_after_warp\":%u,\"fixture_warp_calls\":4,\"fixture_field_callback_writes\":1,\"normal_new_game_accepted\":false,\"purchase_accepted\":false,\"natural_progress_accepted\":false,\"warnings_errors\":%u}\n",UC_ROM,si_cores,eligible,pages,uc_frames,log_problem_count);
 return 0;
}
