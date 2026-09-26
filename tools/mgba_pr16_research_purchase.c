/* 実Research UIのみ。進行/10RP/warpは停止fixture、以後7API guard。
 * 旧取消mainは呼ばず、共通の起動・入力・読取だけを再利用する。 */
static void up_no_task(struct mCore*c){
 si_need(!uc_active(c)&&read8(c,SI_VOL+32)==255,"purchase window released");
 for(unsigned t=0;t<16;++t){unsigned a=0x030050D0U+40*t;si_need(!(read8(c,a+4)&&read32(c,a)>=0x093BD000U&&read32(c,a)<0x093C0000U),"no leaked Research task");}
}
static struct mCore*up_setup(const char*rom,const char*save){
 struct mCore*c=si_open(rom,save);unsigned events=read32(c,0x092C2AE0U),bgs=read32(c,events+16),script=read32(c,bgs+8);
 si_need(events==0x09413C50U&&bgs==0x09413C14U&&script==0x093C0328U&&read16(c,bgs)==2&&read16(c,bgs+2)==1,"exact authored Research root");
 si_need(read16(c,0x093BF9ECU)==4&&read16(c,0x093BF9EEU)==10&&read16(c,0x093BF9F0U)==5,"actual catalog0 item/price/quantity");
 printf("{\"binding\":\"map98/3-background0\",\"events\":%u,\"backgrounds\":%u,\"script\":%u,\"catalog\":0,\"item\":4,\"price\":10,\"quantity\":5}\n",events,bgs,script);fflush(stdout);
 run_key_frames(c,0,2);
 (void)qol_call5_preserving(c,QOL_SET_WARP_DESTINATION,98,3,255,2,2);
 (void)call_preserving(c,QOL_RESET_INITIAL_AVATAR,0,0,0,0);
 (void)call_preserving(c,QOL_WARP_INTO_MAP,0,0,0,0);
 qol_write32(c,QOL_FIELD_CALLBACK_SLOT,QOL_DEFAULT_WARP_EXIT);
 (void)call_preserving(c,QOL_SET_MAIN_CALLBACK2,QOL_CB2_LOAD_MAP,0,0,0);si_guard(c);
 for(unsigned i=0;i<900;++i)uc_frame(c,0);
 unsigned s=read32(c,QOL_SAVE_BLOCK1_SLOT);
 si_need(si_field(c)&&read8(c,s+4)==98&&read8(c,s+5)==3&&read16(c,s)==2&&read16(c,s+2)==2,"actual shop fixture tile");
 si_need(read8(c,SI_VOL+28)==0&&read8(c,SI_VOL+34)==0&&si_read16(c,SI_VOL+20)==65535,"real engine services");
 return c;
}
/* Continue preserves facing.  Unconditional UP can walk onto the BG tile;
 * face only when necessary, as the existing Ring/shop input harness does. */
static void up_stance(struct mCore*c){
 unsigned s=read32(c,QOL_SAVE_BLOCK1_SLOT),id=read8(c,0x02036FB1U),obj=0x02036D6CU+36*id;
 si_need(read8(c,s+4)==98&&read8(c,s+5)==3&&read16(c,s)==2&&read16(c,s+2)==2,"authored interaction stance preserved");
 si_need(id<16&&(read8(c,obj)&1)&&read16(c,obj+0x10)==9&&read16(c,obj+0x12)==9,"actual player object stance");
}
static void up_open_shop(struct mCore*c,const char*stage){
 up_stance(c);unsigned id=read8(c,0x02036FB1U);
 if((read8(c,0x02036D6CU+36*id+0x18)&15)!=2)uc_tap(c,QOL_KEY_UP);
 up_stance(c);
 for(unsigned n=0;n<900;++n){
  if(uc_active(c)){
   unsigned count=read8(c,SI_VOL+30),window=read8(c,SI_VOL+32),tasks=0,callback=0;
   si_need(count>=1&&count<=23&&window<32&&read8(c,SI_VOL+31)==0,"real first page/window");
   si_need(si_read16(c,SI_VOL+18)==65535&&si_read16(c,SI_VOL+16)==9,"actual busy/unselected");
   for(unsigned t=0;t<16;++t){unsigned a=0x030050D0U+40*t;if(read8(c,a+4)&&read32(c,a)>=0x093BD000U&&read32(c,a)<0x093C0000U){++tasks;callback=read32(c,a);}}
   si_need(tasks==1,"one Research task");up_stance(c);
   printf("{\"shop_open\":\"%s\",\"eligible_count\":%u,\"window\":%u,\"callback\":%u,\"native_tasks\":%u}\n",stage,count,window,callback,tasks);fflush(stdout);
   for(unsigned i=0;i<30;++i)uc_frame(c,0);return;
  }
  uc_frame(c,n%60<2?QOL_KEY_A:0);
 }
 up_stance(c);si_die("normal Research shop open limit");
}
static void up_select(struct mCore*c,const char*stage){
 up_open_shop(c,stage);si_need(si_read16(c,SI_VOL+36)==0,"first displayed row resolves catalog0");
 uc_tap(c,QOL_KEY_A);si_need(si_read16(c,SI_VOL+18)==0&&si_read16(c,SI_VOL+16)==10,"normal selection before confirmation");up_no_task(c);
}
static void up_finish(struct mCore*c,unsigned key,unsigned result){
 for(unsigned n=0;n<80;++n){
  if(si_field(c)&&!uc_active(c)){up_no_task(c);si_need(si_read16(c,SI_VOL+18)==0&&si_read16(c,SI_VOL+16)==result,"real selected result");return;}
  uc_tap(c,key);
 }
 fprintf(stderr,"purchase endpoint cb=%08x lock=%u selected=%u result=%u\n",read32(c,BATTLE_CORE_MAIN_CALLBACK2),read8(c,0x03000F9CU),si_read16(c,SI_VOL+18),si_read16(c,SI_VOL+16));si_die("purchase endpoint limit");
}
static void up_inventory(struct mCore*c,const unsigned*base,const uint8_t*party,bool bought){
 unsigned now[2048];si_inventory(c,now);
 for(unsigned i=0;i<2048;++i)si_need(now[i]==base[i]+((bought&&i==4)?5:0),"only purchased five items change Bag");
 for(unsigned i=0;i<600;++i)si_need(read8(c,QOL_PLAYER_PARTY+i)==party[i],"all party600 bytes preserved");
}
static void up_invariants(struct mCore*c,const uint8_t*base,const unsigned*items,const uint8_t*party,bool bought,unsigned counter){
 uint8_t want[2048];memcpy(want,base,2048);
 if(bought){lc_w16(want,0x743,0);lc_w32(want,0x763,2);lc_w32(want,8,lc_checksum(want));}
 uc_same_ledger(c,want);up_inventory(c,items,party,bought);si_need(read32(c,SI_COUNTER)==counter,"exact real save counter");
}
int main(int argc,char**argv){
 if(argc==3&&!strcmp(argv[1],"--guard-check"))si_guard_check(argv[2]);
 si_need(argc==4&&!strcmp(argv[3],"shop-select-purchase-insufficient-save-continue"),"closed purchase case");char sha[65];
 sha256_file(argv[1],sha);si_need(!strcmp(sha,UC_ROM),"unchanged candidate");sha256_file(argv[2],sha);si_need(!strcmp(sha,UC_FIXTURE),"exact purchase fixture");
 struct mLogger logger={.log=qol_log};mLogSetDefaultLogger(&logger);struct mCore*c=up_setup(argv[1],argv[2]);
 uint8_t ledger[2048],party[600],flash[131072],check[131072];unsigned items[2048];
 lc_read(c,ledger);for(unsigned i=0;i<600;++i)party[i]=read8(c,QOL_PLAYER_PARTY+i);si_inventory(c,items);uc_copy_flash(c,flash);
 unsigned counter=read32(c,SI_COUNTER),count=read8(c,QOL_PLAYER_PARTY_COUNT);si_need(si_read16(c,SI_OWNER+4)==10&&si_read32(c,SI_OWNER+36)==1,"10RP precondition");lc_event(c,"fixture");
 up_select(c,"decline");up_invariants(c,ledger,items,party,false,counter);lc_event(c,"selected_decline");
 up_finish(c,QOL_KEY_B,10);up_invariants(c,ledger,items,party,false,counter);uc_copy_flash(c,check);si_need(!memcmp(flash,check,131072),"confirmation refusal changes no Flash byte");lc_event(c,"declined");
 up_select(c,"buy");up_invariants(c,ledger,items,party,false,counter);lc_event(c,"selected_buy");
 up_finish(c,QOL_KEY_A,0);up_invariants(c,ledger,items,party,true,counter+2);lc_event(c,"purchased");qol_close(c);
 /* manual Saveより前の独立Continueで取引自体の永続化を検査。 */
 c=si_open(argv[1],argv[2]);si_guard(c);up_invariants(c,ledger,items,party,true,counter+2);up_no_task(c);si_need(si_read16(c,SI_VOL+18)==65535,"cold selected reset");lc_event(c,"transaction_continue");uc_copy_flash(c,flash);
 up_select(c,"insufficient");up_invariants(c,ledger,items,party,true,counter+2);lc_event(c,"selected_insufficient");
 up_finish(c,QOL_KEY_A,14);up_invariants(c,ledger,items,party,true,counter+2);uc_copy_flash(c,check);si_need(!memcmp(flash,check,131072),"insufficient changes no Flash byte");lc_event(c,"insufficient");
 si_need(si_normal_save(c),"ordinary Start Save after purchase/insufficient");up_invariants(c,ledger,items,party,true,counter+3);lc_event(c,"saved");qol_close(c);
 for(unsigned i=0;i<2;++i){c=si_open(argv[1],argv[2]);si_guard(c);up_invariants(c,ledger,items,party,true,counter+3);up_no_task(c);si_need(read8(c,QOL_PLAYER_PARTY_COUNT)==count&&si_read16(c,SI_VOL+18)==65535,"cold party and selected state");lc_event(c,i?"continued_again":"continued");qol_close(c);}
 si_need(!log_problem_count,"mGBA warnings/errors");
 printf("{\"status\":\"PASS\",\"scope\":\"NATIVE_RESEARCH_SELECTION_PURCHASE_INSUFFICIENT_AND_SAVE_CONTINUE\",\"case\":\"shop-select-purchase-insufficient-save-continue\",\"candidate_sha256\":\"%s\",\"fresh_cores\":%u,\"catalog\":0,\"item\":4,\"price\":10,\"quantity\":5,\"manual_saves\":1,\"transaction_saves\":2,\"host_write_barriers\":7,\"guarded_host_writes\":0,\"frames_after_warp\":%u,\"fixture_warp_calls\":4,\"fixture_field_callback_writes\":1,\"normal_new_game_accepted\":false,\"purchase_accepted\":true,\"natural_progress_accepted\":false,\"warnings_errors\":%u}\n",UC_ROM,si_cores,uc_frames,log_problem_count);return 0;
}
