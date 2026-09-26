/* 新scope: 0RP -> 通常Bag/釣り又はレーダー -> 逃走/実捕獲 -> 取引保存のfresh Continue。
 * 既存special-wild受入の再実行ではない。候補26dac23cの研究経済境界だけ。
 * 開始map/lead/items/progressionはfixture。RNG/敵/捕獲結果/RPのhost注入は一切しない。
 * 初期fixture終了からfresh Continueまで7つのhost書込APIを拒否する。 */
static bool rw_fishing;
static unsigned rw_attempts,rw_outcome,rw_caught_frame,rw_encounters;
static const char*rw_method;
static void rw_press(struct mCore*c,unsigned key,unsigned after){
 for(unsigned i=0;i<2;++i)uc_frame(c,key);for(unsigned i=0;i<after;++i)uc_frame(c,0);
}
static void rw_wait(struct mCore*c,unsigned n){for(unsigned i=0;i<n;++i)uc_frame(c,0);}
static void rw_screen(const char*stage){
 char hash[65],name[128];ct_screen(40,hash);snprintf(name,sizeof(name),"research-%s-%s.ppm",rw_method,stage);
 si_need(!rename("catalog-page-40.ppm",name),"unique research wild screen");
 printf("{\"kind\":\"screen\",\"stage\":\"%s\",\"name\":\"%s\",\"sha256\":\"%s\",\"frame\":%u}\n",stage,name,hash,uc_frames);fflush(stdout);
}
static void rw_state(struct mCore*c,const char*why){
 unsigned s=read32(c,QOL_SAVE_BLOCK1_SLOT);
 fprintf(stderr,"research-wild %s method=%s frame=%u map=%u/%u pos=%u/%u cb=%08x lock=%u quest=%u/%u RP=%u result=%u wild=%u/%u/%u species=%u pid=%08x counter=%u\n",why,rw_method,uc_frames,read8(c,s+4),read8(c,s+5),read16(c,s),read16(c,s+2),read32(c,BATTLE_CORE_MAIN_CALLBACK2),read8(c,0x03000F9CU),read8(c,0x0203AD72U),read8(c,0x03005ED8U),si_read16(c,SI_OWNER+4),si_read16(c,SI_VOL+16),read8(c,SI_VOL+24),read8(c,SI_VOL+22),read8(c,SI_VOL+23),si_read16(c,SI_VOL+8),si_read32(c,SI_VOL+4),read32(c,SI_COUNTER));
 for(unsigned i=0;i<16;++i){unsigned t=0x030050D0U+40*i;if(read8(c,t+4)){fprintf(stderr,"task%u %08x",i,read32(c,t));for(unsigned k=0;k<8;++k)fprintf(stderr," %04x",read16(c,t+8+2*k));fputc('\n',stderr);}}
 fflush(stderr);
}
static void rw_need(struct mCore*c,bool good,const char*why){if(!good){rw_state(c,why);rw_screen("failure");si_die(why);}}
static void rw_copy(struct mCore*c,unsigned address,uint8_t*out,unsigned size){for(unsigned i=0;i<size;++i)out[i]=read8(c,address+i);}
static void rw_snapshot(struct mCore*c,const char*stage){
 uint8_t ledger[2048],other[2048],party[600],flash[131072],owner[64];unsigned bag[2048];char lh[65],oh[65],ph[65],fh[65],ih[65],bh[65];
 lc_read(c,ledger);memcpy(other,ledger,2048);memset(other+4,0,2);memset(other+8,0,4);memset(other+0x73f,0,64);
 rw_copy(c,QOL_PLAYER_PARTY,party,600);si_owner(c,owner);uc_copy_flash(c,flash);si_inventory(c,bag);
 si_digest(ledger,2048,lh);si_digest(other,2048,oh);si_digest(party,600,ph);si_digest(flash,131072,fh);si_inventory_digest(bag,2048,ih);si_inventory_digest(bag,1,bh);
 unsigned s=read32(c,QOL_SAVE_BLOCK1_SLOT);
 printf("{\"kind\":\"snapshot\",\"stage\":\"%s\",\"frame\":%u,\"counter\":%u,\"party_count\":%u,\"balls\":%u,\"map\":[%u,%u,%u,%u],\"ledger_sha256\":\"%s\",\"unrelated_ledger_sha256\":\"%s\",\"party_sha256\":\"%s\",\"flash_sha256\":\"%s\",\"inventory_sha256\":\"%s\",\"other_inventory_sha256\":\"%s\",\"checksum_valid\":%s,\"owner\":\"",stage,uc_frames,read32(c,SI_COUNTER),read8(c,QOL_PLAYER_PARTY_COUNT),bag[1],read8(c,s+4),read8(c,s+5),read16(c,s),read16(c,s+2),lh,oh,ph,fh,ih,bh,lc_checksum(ledger)==lc_u32(ledger,8)?"true":"false");
 for(unsigned i=0;i<64;++i)printf("%02x",owner[i]);printf("\",\"wild_armed\":%u,\"result\":%u}\n",read8(c,SI_VOL+24),si_read16(c,SI_VOL+16));fflush(stdout);
}
static bool rw_action(struct mCore*c){
 unsigned ctrl=read32(c,0x03005020U);
 return read32(c,0x03004FC4U)==0x08013861U&&(read32(c,0x02023B28U)&1U)&&read8(c,0x02022B24U)==0x12U&&(ctrl==0x0802DC15U||ctrl==0x09118B85U);
}
static void rw_cursor(struct mCore*c,unsigned target){
 rw_need(c,rw_action(c),"real battle controller required");
 for(unsigned i=0;i<6;++i){unsigned at=read8(c,BATTLE_CORE_ACTION_SELECTION_CURSOR);rw_need(c,at<4,"battle cursor range");if(at==target)return;rw_press(c,(at&1)!=(target&1)?((target&1)?QOL_KEY_RIGHT:QOL_KEY_LEFT):((target&2)?QOL_KEY_DOWN:QOL_KEY_UP),12);}
 rw_need(c,false,"physical battle cursor bound");
}
static void rw_return(struct mCore*c,bool caught){
 unsigned stable=0;rw_outcome=0;rw_caught_frame=0;
 for(unsigned f=0;f<24000;++f){
  unsigned out=read8(c,BATTLE_CORE_BATTLE_OUTCOME);if(out)rw_outcome=out;if(out==7&&!rw_caught_frame)rw_caught_frame=uc_frames;
  if(!read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER)&&si_field(c)){if(++stable==30)return;}else stable=0;
  if(!caught&&rw_action(c)){rw_cursor(c,3);rw_press(c,QOL_KEY_A,60);continue;}
  uc_frame(c,f%60==0?QOL_KEY_B:0);
 }
 rw_need(c,false,"natural wild return bound");
}
static void rw_pocket(struct mCore*c,unsigned target){
 for(unsigned i=0;i<6;++i){if(read16(c,BATTLE_CORE_BAG_STATE+6)==target)return;rw_press(c,QOL_KEY_RIGHT,90);}rw_need(c,false,"physical Bag pocket bound");
}
static void rw_bag(struct mCore*c){
 rw_need(c,si_field(c),"Start Bag from field");rw_press(c,QOL_KEY_START,120);
 rw_need(c,read32(c,QOL_START_MENU_CALLBACK)==QOL_START_MENU_INPUT,"normal Start menu");
 unsigned count=read8(c,QOL_START_MENU_COUNT),target=count;rw_need(c,count&&count<=9,"Start rows");
 for(unsigned i=0;i<count;++i)if(read8(c,QOL_START_MENU_ORDER+i)==2)target=i;
 rw_need(c,target<count,"Bag row exists");for(unsigned i=0;i<count&&read8(c,QOL_START_MENU_CURSOR)!=target;++i)rw_press(c,QOL_KEY_DOWN,30);
 rw_need(c,read8(c,QOL_START_MENU_CURSOR)==target,"physical Bag row");rw_press(c,QOL_KEY_A,180);
 rw_need(c,read32(c,BATTLE_CORE_MAIN_CALLBACK2)==P02S_CB2_BAG,"normal field Bag callback");rw_wait(c,180);rw_pocket(c,1);
}
static bool rw_encounter(struct mCore*c){
 ++rw_attempts;rw_bag(c);rw_press(c,QOL_KEY_A,120);
 rw_need(c,read16(c,0x0203ACA8U)==(rw_fishing?264U:348U),"actual key item selected");rw_press(c,QOL_KEY_A,180);
 if(!rw_fishing){
  rw_need(c,read8(c,0x03000F9CU)&&!read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER),"actual radar menu");
  for(unsigned i=0;i<4;++i)rw_press(c,QOL_KEY_DOWN,24);rw_press(c,QOL_KEY_A,1);
 }
 unsigned idle=0;
 for(unsigned f=0;f<9000&&!rw_action(c);++f){
  bool task=false;for(unsigned i=0;i<16;++i){unsigned t=0x030050D0U+40*i;if(read8(c,t+4)&&read32(c,t)==0x0805CBC1U)task=true;}
  if(rw_fishing&&f>120&&!task&&!read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER)&&si_field(c)){if(++idle>=120){printf("{\"kind\":\"no_bite\",\"attempt\":%u,\"frame\":%u}\n",rw_attempts,uc_frames);fflush(stdout);return false;}}else idle=0;
  uc_frame(c,f%60==0?QOL_KEY_A:0);
 }
 rw_need(c,rw_action(c),"physical item to native wild battle");++rw_encounters;
 unsigned species=read16(c,ADDR_ENEMY_PARTY+32),pid=read32(c,ADDR_ENEMY_PARTY);
 rw_need(c,read8(c,SI_VOL+24)==1&&read8(c,SI_VOL+22)==(rw_fishing?0:1)&&si_read16(c,SI_VOL+8)==species&&si_read32(c,SI_VOL+4)==pid,"runtime provenance matches natural enemy");
 printf("{\"kind\":\"enemy\",\"attempt\":%u,\"frame\":%u,\"species\":%u,\"pid\":%u,\"pre_caught\":%u,\"activity\":%u,\"party\":\"",rw_attempts,uc_frames,species,pid,read8(c,SI_VOL+23),read8(c,SI_VOL+22));
 for(unsigned i=0;i<100;++i)printf("%02x",read8(c,ADDR_ENEMY_PARTY+i));printf("\"}\n");fflush(stdout);return true;
}
static void rw_escape(struct mCore*c){rw_cursor(c,3);rw_press(c,QOL_KEY_A,60);rw_return(c,false);rw_need(c,rw_outcome==4&&read8(c,SI_VOL+24)==0,"escaped result clears provenance");}
static void rw_uncaught(struct mCore*c,unsigned counter){
 for(unsigned i=0;i<32;++i){
  if(!rw_encounter(c))continue;if(!read8(c,SI_VOL+23))return;
  rw_escape(c);rw_need(c,si_read16(c,SI_OWNER+4)==0&&read32(c,SI_COUNTER)==counter,"known species escape does not earn or save");
 }
 rw_need(c,false,"bounded native uncaught species search");
}
static void rw_catch(struct mCore*c){
 rw_cursor(c,1);rw_press(c,QOL_KEY_A,180);
 for(unsigned i=0;i<1800&&read32(c,BATTLE_CORE_MAIN_CALLBACK2)!=P02S_CB2_BAG;++i)uc_frame(c,0);
 rw_need(c,read32(c,BATTLE_CORE_MAIN_CALLBACK2)==P02S_CB2_BAG,"real battle Bag");rw_wait(c,180);rw_pocket(c,2);rw_screen("ball-pocket");
 rw_press(c,QOL_KEY_A,120);rw_need(c,read16(c,0x0203ACA8U)==1,"actual Master Ball selected");rw_press(c,QOL_KEY_A,180);rw_return(c,true);
 rw_need(c,rw_outcome==7&&rw_caught_frame&&read8(c,QOL_PLAYER_PARTY_COUNT)==2&&read8(c,SI_VOL+24)==0,"native caught result and cleared provenance");
}
static struct mCore*rw_setup(const char*rom,const char*save){
 struct mCore*c=ct_open(rom,save);clear_parties(c);create_mon(c,QOL_PLAYER_PARTY,4,100);write8(c,QOL_PLAYER_PARTY_COUNT,1);
 for(unsigned f=0x0820;f<=0x082C;++f)(void)call_preserving(c,QOL_FLAG_SET,f,0,0,0);
 (void)call_preserving(c,QOL_FLAG_SET,0x114B,0,0,0);
 (void)call_preserving(c,154634137U,15,1,0,0);rw_need(c,read8(c,0x0203D01FU)==1,"explicit research-profile fixture");
 /* Empty only the key/ball pockets in the stopped fixture, preserving other items. */
 unsigned key=read16(c,read32(c,QOL_SAVE_BLOCK2_SLOT)+0xF20U);
 for(unsigned pocket=1;pocket<=2;++pocket){unsigned descriptor=0x020397D8U+8*pocket,slots=read32(c,descriptor),count=read8(c,descriptor+4);rw_need(c,count==(pocket==1?30U:13U),"fixture pocket descriptors");for(unsigned i=0;i<count;++i){write16(c,slots+4*i,0);write16(c,slots+4*i+2,key);}write16(c,slots,pocket==1?(rw_fishing?264:348):1);write16(c,slots+2,(pocket==1?1:20)^key);}
 write16(c,BATTLE_CORE_BAG_STATE+6,1);for(unsigned i=0;i<6;++i)write16(c,BATTLE_CORE_BAG_STATE+8+2*i,0);
 run_key_frames(c,0,2);
 (void)qol_call5_preserving(c,QOL_SET_WARP_DESTINATION,3,rw_fishing?38:63,255,rw_fishing?94:14,rw_fishing?10:11);
 (void)call_preserving(c,QOL_RESET_INITIAL_AVATAR,0,0,0,0);(void)call_preserving(c,QOL_WARP_INTO_MAP,0,0,0,0);
 qol_write32(c,QOL_FIELD_CALLBACK_SLOT,QOL_DEFAULT_WARP_EXIT);(void)call_preserving(c,QOL_SET_MAIN_CALLBACK2,QOL_CB2_LOAD_MAP,0,0,0);
 si_guard(c);rw_wait(c,900);rw_need(c,si_field(c),"stock warp settles under write barrier");
 if(rw_fishing)rw_press(c,QOL_KEY_LEFT,30);
 unsigned s=read32(c,QOL_SAVE_BLOCK1_SLOT);rw_need(c,read8(c,s+4)==3&&read8(c,s+5)==(rw_fishing?38:63)&&read16(c,s)==(rw_fishing?94:14)&&read16(c,s+2)==(rw_fishing?10:11),"source-proven native key-item stance");
 rw_need(c,read8(c,SI_VOL+28)==0&&read8(c,SI_VOL+29)==0&&read8(c,SI_VOL+34)==0&&si_read16(c,SI_VOL+20)==65535,"no mock/unlock/fault services");
 return c;
}
int main(int argc,char**argv){
 if(argc==3&&!strcmp(argv[1],"--guard-check"))si_guard_check(argv[2]);
 si_need(argc==4,"research wild arguments");rw_method=argv[3];rw_fishing=!strcmp(rw_method,"fishing");si_need(rw_fishing||!strcmp(rw_method,"ecology"),"closed two new scopes");
 char hash[65];sha256_file(argv[1],hash);si_need(!strcmp(hash,UC_ROM),"current candidate identity");sha256_file(argv[2],hash);si_need(!strcmp(hash,UC_FIXTURE),"zero-RP disk fixture");
 struct mLogger logger={.log=qol_log};mLogSetDefaultLogger(&logger);struct mCore*c=rw_setup(argv[1],argv[2]);
 uint8_t base[2048],want[2048],lead[600],caught[600],flash[131072],now[131072];unsigned bag[2048],after_bag[2048];
 lc_read(c,base);rw_copy(c,QOL_PLAYER_PARTY,lead,600);si_inventory(c,bag);uc_copy_flash(c,flash);unsigned counter=read32(c,SI_COUNTER),points=rw_fishing?4:10;
 rw_need(c,si_read16(c,SI_OWNER+4)==0&&si_read32(c,SI_OWNER+10)==0&&bag[1]==20,"genuine zero initial RP and fixture balls");rw_snapshot(c,"fixture");rw_screen("fixture");
 rw_uncaught(c,counter);rw_escape(c);uc_same_ledger(c,base);uc_same_inventory(c,bag,lead);uc_copy_flash(c,now);rw_need(c,!memcmp(flash,now,131072)&&read32(c,SI_COUNTER)==counter,"escape preserves full Flash and ledger");rw_snapshot(c,"escaped");
 rw_uncaught(c,counter);unsigned pid=read32(c,ADDR_ENEMY_PARTY),species=read16(c,ADDR_ENEMY_PARTY+32);rw_screen("encounter");rw_catch(c);
 rw_snapshot(c,"earned");rw_screen("earned");
 memcpy(want,base,2048);lc_w16(want,0x743,points);lc_w32(want,0x749,points);lc_w16(want,0x74d+(rw_fishing?0:2),points);lc_w32(want,0x763,2);lc_w32(want,8,lc_checksum(want));uc_same_ledger(c,want);
 rw_need(c,read32(c,SI_COUNTER)==counter+2&&read32(c,QOL_PLAYER_PARTY+100)==pid&&read16(c,QOL_PLAYER_PARTY+132)==species,"real capture owns RP transaction and individual");
 rw_copy(c,QOL_PLAYER_PARTY,caught,600);rw_need(c,!memcmp(caught,lead,100)&&!memcmp(caught+200,lead+200,400),"unrelated five party slots unchanged");
 memcpy(after_bag,bag,sizeof(bag));after_bag[1]--;uc_same_inventory(c,after_bag,caught);uc_copy_flash(c,flash);qol_close(c);
 c=ct_open(argv[1],argv[2]);si_guard(c);uc_same_ledger(c,want);uc_same_inventory(c,after_bag,caught);uc_copy_flash(c,now);
 rw_need(c,read32(c,SI_COUNTER)==counter+2&&!memcmp(flash,now,131072),"transaction-only fresh Continue with no extra save");rw_snapshot(c,"continued");rw_screen("continued");qol_close(c);
 si_need(!log_problem_count,"new research wild emulator warnings/errors");
 printf("{\"kind\":\"summary\",\"status\":\"PASS\",\"method\":\"%s\",\"candidate_sha256\":\"%s\",\"initial_rp\":0,\"earned_rp\":%u,\"transaction_saves\":2,\"manual_saves\":0,\"fresh_cores\":%u,\"attempts\":%u,\"encounters\":%u,\"species\":%u,\"pid\":%u,\"physical_escape_verified\":true,\"host_write_barriers\":7,\"guarded_host_writes\":0,\"rng_injected\":false,\"target_injected\":false,\"accepted_case_reruns\":0,\"all_activities_accepted\":false,\"natural_arrival_accepted\":false,\"warnings_errors\":0}\n",rw_method,UC_ROM,points,si_cores,rw_attempts,rw_encounters,species,pid);return 0;
}
