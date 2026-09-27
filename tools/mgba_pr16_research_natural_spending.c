/* 新しい稼得->支出境界。旧活動matrix/数値/list試験は呼ばない。
 * earn: 0RP fixtureから実Rock Smashの10RP取引だけを作り、再利用saveを保持。
 * spend: そのcold saveを読んで全ledger/Bag/partyを固定。移動だけの停止fixture
 * で研究所屋外へ置くため、全世界の自然移動/ストーリー到達とは主張しない。
 * 各観測barrier以後はキー・読取だけ。RP/result/claim/PCを注入しない。
 */
static void ns_wait(struct mCore*c,unsigned n){for(unsigned i=0;i<n;++i)uc_frame(c,0);}
static void ns_key(struct mCore*c,unsigned key,unsigned n){
 si_need((key==0||key==1||key==2||key==16||key==32||key==64||key==128)&&n<=1200,"closed physical key range");
 printf("{\"kind\":\"input\",\"keys\":%u,\"frames\":%u,\"start_frame\":%u}\n",key,n,uc_frames);fflush(stdout);
 for(unsigned i=0;i<n;++i)uc_frame(c,key);
}
static void ns_observe(struct mCore*c,const char*label){
 unsigned s=read32(c,QOL_SAVE_BLOCK1_SLOT),w=read8(c,SI_VOL+32);uint8_t b[131072];char fh[65],ih[65],bh[65];unsigned bag[2048];uc_copy_flash(c,b);si_digest(b,sizeof(b),fh);si_inventory(c,bag);si_inventory_digest(bag,2048,ih);si_inventory_digest(bag,4,bh);
 printf("{\"kind\":\"state\",\"stage\":\"%s\",\"frame\":%u,\"map\":[%u,%u,%u,%u],\"field\":%s,\"shop_active\":%s,\"page\":%u,\"eligible\":%u,\"window\":%u,\"counter\":%u,\"rp\":%u,\"lifetime\":%u,\"next_transaction\":%u,\"selected\":%u,\"result\":%u,\"item4\":%u,\"inventory_sha256\":\"%s\",\"other_inventory_sha256\":\"%s\",\"flash_sha256\":\"%s\",\"window0\":\"",label,uc_frames,read8(c,s+4),read8(c,s+5),read16(c,s),read16(c,s+2),si_field(c)?"true":"false",uc_active(c)?"true":"false",read8(c,SI_VOL+31),read8(c,SI_VOL+30),w,read32(c,SI_COUNTER),si_read16(c,SI_OWNER+4),si_read32(c,SI_OWNER+10),si_read32(c,SI_OWNER+36),si_read16(c,SI_VOL+18),si_read16(c,SI_VOL+16),bag[4],ih,bh,fh);
 for(unsigned i=0;i<12;++i)printf("%02x",read8(c,0x02020430U+i));printf("\",\"shop_descriptor\":\"");
 if(w<32)for(unsigned i=0;i<12;++i)printf("%02x",read8(c,0x02020430U+12*w+i));
 printf("\",\"text\":\"");for(unsigned i=0;i<192;++i){unsigned v=read8(c,0x02021C88U+i);printf("%02x",v);if(v==255)break;}printf("\"}\n");lc_event(c,label);fflush(stdout);
}
static void ns_screen(const char*stage){
 char hash[65],name[96];ct_screen(40,hash);snprintf(name,sizeof(name),"%s.ppm",stage);si_need(!rename("catalog-page-40.ppm",name),"unique output screen");
 printf("{\"kind\":\"screen\",\"stage\":\"%s\",\"name\":\"%s\",\"sha256\":\"%s\",\"frame\":%u}\n",stage,name,hash,uc_frames);fflush(stdout);
}
static void ns_earned(struct mCore*c){
 uint8_t owner[64],want[64]={0};si_owner(c,owner);want[0]=1;want[1]=64;want[4]=10;want[6]=1;want[7]=owner[7];want[10]=10;want[22]=10;want[27]=2;want[36]=2;
 si_need(owner[7]<=8&&!memcmp(owner,want,64),"genuine mining owner: 10 balance/lifetime/daily and one claim/transaction");
}
static void ns_spend_invariants(struct mCore*c,const uint8_t*base,const unsigned*items,const uint8_t*party,unsigned counter,bool bought){
 uint8_t want[2048];memcpy(want,base,2048);
 if(bought){lc_w16(want,0x743,0);lc_w32(want,0x763,lc_u32(base,0x763)+1);lc_w32(want,8,lc_checksum(want));}
 uc_same_ledger(c,want);up_inventory(c,items,party,bought);
 si_need(read32(c,SI_COUNTER)==counter+(bought?2U:0U),"only two spend transaction saves; no manual save");
 si_need(si_read32(c,SI_OWNER+10)==10&&si_read16(c,SI_OWNER+22)==10&&read8(c,SI_OWNER+27)==2,"spending never clears lifetime/daily/claim");
}
static void ns_window(struct mCore*c){
 unsigned w=read8(c,SI_VOL+32),a=0x02020430U+12*w;
 si_need(uc_active(c)&&w>0&&w<32,"shop owns separate non-dialogue window");
 si_need(read8(c,a+2)==1&&read8(c,a+3)==21&&read8(c,a+4)<=16&&read16(c,a+6)==0x38&&read32(c,a+8)!=0,"bounded separated pixel allocation");
 si_need(read32(c,0x02020438U)!=0,"dialogue window remains owned");
}
static void ns_close_menu(struct mCore*c){
 ns_key(c,QOL_KEY_B,2);ns_wait(c,90);
 for(unsigned i=0;i<10&&!si_field(c);++i){ns_key(c,QOL_KEY_A,2);ns_wait(c,90);}
 up_no_task(c);si_need(si_field(c),"cancel returns to the field");
}
static void ns_outside_fixture(struct mCore*c){
 (void)qol_call5_preserving(c,QOL_SET_WARP_DESTINATION,96,0,255,16,14);
 (void)call_preserving(c,QOL_RESET_INITIAL_AVATAR,0,0,0,0);(void)call_preserving(c,QOL_WARP_INTO_MAP,0,0,0,0);
 qol_write32(c,QOL_FIELD_CALLBACK_SLOT,QOL_DEFAULT_WARP_EXIT);(void)call_preserving(c,QOL_SET_MAIN_CALLBACK2,QOL_CB2_LOAD_MAP,0,0,0);si_guard(c);ns_wait(c,900);
 unsigned s=read32(c,QOL_SAVE_BLOCK1_SLOT);si_need(si_field(c)&&read8(c,s+4)==96&&read8(c,s+5)==0&&read16(c,s)==16&&read16(c,s+2)==14,"declared outdoor relocation fixture");
 printf("{\"kind\":\"relocation_fixture\",\"stock_warp_calls\":4,\"field_callback_writes\":1,\"rp_injected\":false,\"natural_travel_accepted\":false}\n");fflush(stdout);
}
static void ns_shop_walk(struct mCore*c){
 ns_key(c,QOL_KEY_UP,40);ns_wait(c,200);ns_observe(c,"door_entered");ns_screen("door_entered");
 ns_key(c,QOL_KEY_UP,128);ns_wait(c,60);ns_key(c,QOL_KEY_DOWN,16);ns_key(c,0x20,64);ns_key(c,QOL_KEY_UP,48);ns_wait(c,60);
 ns_key(c,0x20,16);ns_wait(c,30);ns_key(c,QOL_KEY_UP,2);ns_wait(c,30);up_stance(c);ns_observe(c,"shop_stance");
}
int main(int argc,char**argv){
 if(argc==3&&!strcmp(argv[1],"--guard-check"))si_guard_check(argv[2]);
 si_need(argc==4&&(!strcmp(argv[3],"earn")||!strcmp(argv[3],"spend")),"closed new earning-spending modes");
 char hash[65];sha256_file(argv[1],hash);si_need(!strcmp(hash,UC_ROM),"new shop candidate");sha256_file(argv[2],hash);
 printf("{\"kind\":\"input_save\",\"mode\":\"%s\",\"sha256\":\"%s\",\"candidate\":\"%s\"}\n",argv[3],hash,UC_ROM);fflush(stdout);
 struct mLogger logger={.log=qol_log};mLogSetDefaultLogger(&logger);
 if(!strcmp(argv[3],"earn")){
  si_need(!strcmp(hash,UC_FIXTURE),"exact zero-RP input fixture");struct mCore*c=rm_setup(argv[1],argv[2],2);
  uint8_t base[2048],party[600];unsigned items[2048],counter=read32(c,SI_COUNTER);lc_read(c,base);for(unsigned i=0;i<600;++i)party[i]=read8(c,QOL_PLAYER_PARTY+i);si_inventory(c,items);
  si_need(si_read16(c,SI_OWNER+4)==0&&si_read32(c,SI_OWNER+10)==0,"no earned credit injected");ns_observe(c,"earning_fixture");
  rm_visit(c,"spending_input",true,true,0);rm_invariants(c,base,items,party,true,counter+2);ns_earned(c);ns_observe(c,"earned");qol_close(c);
  si_need(!log_problem_count,"clean earning prefix");printf("{\"kind\":\"summary\",\"status\":\"PASS_EARNING_PREFIX\",\"fresh_cores\":%u,\"earned_rp\":10,\"automatic_saves\":2,\"manual_saves\":0,\"old_matrix_executions\":0,\"retained_earned_input\":true,\"natural_story_progress_accepted\":false,\"warnings_errors\":0}\n",si_cores);return 0;
 }
 struct mCore*c=ct_open(argv[1],argv[2]);ns_earned(c);
 uint8_t base[2048],party[600],flash[131072],now[131072];unsigned items[2048],counter=read32(c,SI_COUNTER);lc_read(c,base);for(unsigned i=0;i<600;++i)party[i]=read8(c,QOL_PLAYER_PARTY+i);si_inventory(c,items);uc_copy_flash(c,flash);ns_observe(c,"earned_continue");
 ns_outside_fixture(c);ns_spend_invariants(c,base,items,party,counter,false);uc_copy_flash(c,now);si_need(!memcmp(now,flash,131072),"relocation does not manufacture RP or save");ns_observe(c,"outside");ns_screen("outside");
 ns_shop_walk(c);up_open_shop(c,"pages");unsigned eligible=read8(c,SI_VOL+30);si_need(eligible==19,"unchanged progress reveals original 19 entries");
 for(unsigned page=0;page<4;++page){
  ns_window(c);si_need(read8(c,SI_VOL+31)==page,"stock physical page");char name[40];snprintf(name,sizeof(name),"page_%u",page);ns_observe(c,name);ns_screen(name);
  if(page<3){for(unsigned i=0;i<5;++i){ns_key(c,QOL_KEY_DOWN,2);ns_wait(c,24);}ns_key(c,QOL_KEY_A,2);ns_wait(c,90);}
 }
 ns_close_menu(c);ns_spend_invariants(c,base,items,party,counter,false);uc_copy_flash(c,now);si_need(!memcmp(now,flash,131072),"paging and cancel do not save");ns_observe(c,"pages_closed");ns_screen("pages_closed");
 up_open_shop(c,"purchase");ns_window(c);ns_observe(c,"buy_open");ns_screen("buy_open");
 ns_key(c,QOL_KEY_A,2);ns_wait(c,120);up_no_task(c);si_need(si_read16(c,SI_VOL+18)==0&&si_read16(c,SI_VOL+16)==10,"catalog0 selected by physical A");ns_observe(c,"selected");ns_screen("selected");
 ns_key(c,QOL_KEY_A,2);ns_wait(c,90);ns_observe(c,"confirmation");ns_screen("confirmation");
 up_finish(c,QOL_KEY_A,0);ns_spend_invariants(c,base,items,party,counter,true);ns_observe(c,"purchased");ns_screen("purchased");uc_copy_flash(c,flash);qol_close(c);
 c=ct_open(argv[1],argv[2]);si_guard(c);ns_spend_invariants(c,base,items,party,counter,true);up_no_task(c);uc_copy_flash(c,now);si_need(!memcmp(flash,now,131072),"fresh Continue preserves exact transaction Flash");ns_observe(c,"purchase_continue");ns_screen("purchase_continue");
 up_open_shop(c,"after_spend");ns_window(c);ns_observe(c,"zero_balance_menu");ns_screen("zero_balance_menu");ns_close_menu(c);ns_spend_invariants(c,base,items,party,counter,true);uc_copy_flash(c,now);si_need(!memcmp(flash,now,131072),"post-Continue display/close leaves Flash unchanged");ns_observe(c,"end");ns_screen("end");qol_close(c);
 si_need(!log_problem_count,"clean new spending measurement");printf("{\"kind\":\"summary\",\"status\":\"PASS_NATURALLY_EARNED_SPENDING_MEASURED\",\"fresh_cores\":%u,\"initial_earned_rp\":10,\"spent_rp\":10,\"final_rp\":0,\"lifetime_rp\":10,\"catalog\":0,\"item\":4,\"quantity\":5,\"automatic_spend_saves\":2,\"manual_saves\":0,\"pages\":4,\"guarded_host_writes\":0,\"old_matrix_executions\":0,\"natural_travel_accepted\":false,\"natural_story_progress_accepted\":false,\"warnings_errors\":0}\n",si_cores);return 0;
}
