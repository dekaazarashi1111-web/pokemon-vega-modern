/* 最終dialogue枠だけの変更影響。既存の実稼得/実支出セーブを使い、
 * 通貨を稼得/消費せず、4ページ・確認取消・0RP再訪を検査する。 */
int main(int argc,char**argv){
 if(argc==3&&!strcmp(argv[1],"--guard-check"))si_guard_check(argv[2]);
 si_need(argc==5&&!strcmp(argv[3],"ui-only"),"closed UI-only impact case");char hash[65];sha256_file(argv[1],hash);si_need(!strcmp(hash,UC_ROM),"final UI candidate");
 sha256_file(argv[2],hash);si_need(!strcmp(hash,"b51c88f69600a8cbf85a152bb96aec5c6844df7cf299e9c0a464f324dba3ebba"),"original retained earned save");
 printf("{\"kind\":\"input_save\",\"mode\":\"ui-only\",\"sha256\":\"%s\",\"candidate\":\"%s\"}\n",hash,UC_ROM);
 struct mLogger logger={.log=qol_log};mLogSetDefaultLogger(&logger);struct mCore*c=ct_open(argv[1],argv[2]);ns_earned(c);
 uint8_t base[2048],party[600],flash[131072],now[131072];unsigned items[2048],counter=read32(c,SI_COUNTER);lc_read(c,base);for(unsigned i=0;i<600;++i)party[i]=read8(c,QOL_PLAYER_PARTY+i);si_inventory(c,items);uc_copy_flash(c,flash);ns_observe(c,"earned_continue");
 ns_outside_fixture(c);ns_spend_invariants(c,base,items,party,counter,false);ns_observe(c,"outside");ns_shop_walk(c);up_open_shop(c,"ui_pages");
 for(unsigned page=0;page<4;++page){
  ns_window(c);si_need(read8(c,SI_VOL+31)==page,"stock physical page");char name[40];snprintf(name,sizeof(name),"page_%u",page);ns_observe(c,name);ns_screen(name);
  if(page<3){for(unsigned i=0;i<5;++i){ns_key(c,QOL_KEY_DOWN,2);ns_wait(c,24);}ns_key(c,QOL_KEY_A,2);ns_wait(c,90);}
 }
 ns_close_menu(c);ns_spend_invariants(c,base,items,party,counter,false);ns_observe(c,"pages_closed");ns_screen("pages_closed");
 up_open_shop(c,"ui_decline");ns_window(c);ns_key(c,QOL_KEY_A,2);ns_wait(c,120);up_no_task(c);ns_observe(c,"selected");ns_screen("selected");
 ns_key(c,QOL_KEY_A,2);ns_wait(c,90);ns_observe(c,"confirmation");ns_screen("confirmation");up_finish(c,QOL_KEY_B,10);
 ns_spend_invariants(c,base,items,party,counter,false);uc_copy_flash(c,now);si_need(!memcmp(flash,now,131072),"all UI/cancel/decline unchanged earned Flash");ns_observe(c,"declined");ns_screen("declined");qol_close(c);
 sha256_file(argv[4],hash);si_need(!strcmp(hash,"f4309eaa866100ee4cafef4f4980bad98e3b05d1eea11393727d2e0c6624c434"),"original retained purchase save");
 printf("{\"kind\":\"input_save\",\"mode\":\"ui-spent\",\"sha256\":\"%s\",\"candidate\":\"%s\"}\n",hash,UC_ROM);
 c=ct_open(argv[1],argv[4]);si_guard(c);ns_spend_invariants(c,base,items,party,counter,true);uc_copy_flash(c,flash);ns_observe(c,"purchase_continue");ns_screen("purchase_continue");
 up_open_shop(c,"ui_zero");ns_window(c);ns_observe(c,"zero_balance_menu");ns_screen("zero_balance_menu");ns_close_menu(c);
 ns_spend_invariants(c,base,items,party,counter,true);uc_copy_flash(c,now);si_need(!memcmp(flash,now,131072),"zero-RP UI leaves original purchase Flash unchanged");ns_observe(c,"end");ns_screen("end");qol_close(c);
 si_need(!log_problem_count,"clean UI-only impact");printf("{\"kind\":\"summary\",\"status\":\"PASS_SHOP_UI_ONLY_IMPACT\",\"fresh_cores\":%u,\"new_earnings\":0,\"new_purchases\":0,\"new_saves\":0,\"pages\":4,\"confirmation_declined\":true,\"zero_balance_revisit\":true,\"old_matrix_executions\":0,\"natural_travel_accepted\":false,\"natural_story_progress_accepted\":false,\"warnings_errors\":0}\n",si_cores);return 0;
}
