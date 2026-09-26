/* Special wild physical key-item UI -> native capture -> normal Save/fresh
 * Continue. Explicit initial map/lead/items/unlocks/profile/RNG fixtures end at
 * the seven-write-API barrier. No injected encounter, setter or outcome calls. */
#include "pr16_progression_archive.c"
#include <mgba/core/version.h>
static unsigned sw_map;
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wunused-variable"
#include "sw-field-helpers.c"
#pragma GCC diagnostic pop
#include "sw-inventory-helpers.c"
#define SW_ROM "0205af9bd2d92b1b3303195ab0cc84e5ea0f3de390ade15d9f8ce42a6dcdd1a0"
#define SW_SEED "f6bfdb107196ca22b012c1d12ee4bcdc8f5add309bbd3538447cd6e39c449bcb"
static color_t sw_video[240*160];
static const char *sw_prefix,*sw_method;
static unsigned sw_frames,sw_entries[6],sw_special,sw_move,sw_after_setter;
static unsigned sw_attempt,sw_item_frame,sw_encounter_frame,sw_caught_frame,sw_saved_frame,sw_reload_frame;
static uint64_t sw_steps;
static bool sw_trace;
static unsigned sw_return_state,sw_last_pc;
static void (*sw_fast)(struct mCore *);
static void sw_shot(const char *name){
 char path[4096];int n=snprintf(path,sizeof(path),"%s-%s.ppm",sw_prefix,name);
 a_require(n>0 && n<(int)sizeof(path),"screenshot path");FILE*f=fopen(path,"wb");a_require(f!=NULL,"screenshot open");
 a_require(fprintf(f,"P6\n240 160\n255\n")>0,"screenshot header");
 for(unsigned i=0;i<240*160;++i){uint32_t p=(uint32_t)sw_video[i];uint8_t rgb[3]={p,p>>8,p>>16};a_require(fwrite(rgb,1,3,f)==3,"screenshot data");}
 a_require(!fclose(f),"screenshot close");
}
static void sw_state(struct mCore*c,const char*label){
 unsigned s=lb_save1(c);fprintf(stderr,"SW_STATE %s frame=%u cb=%08x map=%u/%u pos=%u,%u lock=%u pocket=%u item=%u quest=%u/%u battle=%08x outcome=%u\n",label,sw_frames,read32(c,BATTLE_CORE_MAIN_CALLBACK2),read8(c,s+4),read8(c,s+5),read16(c,s),read16(c,s+2),read8(c,P02S_FIELD_LOCK),read16(c,BATTLE_CORE_BAG_STATE+6),read16(c,0x0203ACA8U),read8(c,P02S_QUEST_LOG_STATE),read8(c,P02S_QUEST_LOG_PLAYBACK_STATE),read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER),read8(c,BATTLE_CORE_BATTLE_OUTCOME));
 for(unsigned i=0;i<16;++i){unsigned t=QOL_TASKS+i*QOL_TASK_SIZE;if(read8(c,t+4)){fprintf(stderr,"TASK %u %08x:",i,read32(c,t));for(unsigned k=0;k<8;++k)fprintf(stderr," %04x",read16(c,t+8+2*k));fputc('\n',stderr);}}
 fflush(stderr);
}
static void sw_need(struct mCore*c,bool ok,const char*s){if(!ok){sw_state(c,s);sw_shot("failure");a_die(s);}}
static void sw_mon(struct mCore*c,unsigned addr,const char*event){
 printf("{\"event\":\"%s\",\"method\":\"%s\",\"attempt\":%u,\"frame\":%u,\"party\":\"",event,sw_method,sw_attempt,sw_frames);
 for(unsigned i=0;i<100;++i)printf("%02x",read8(c,addr+i));printf("\"}\n");fflush(stdout);
}
static void sw_observe(struct mCore*c){
 unsigned qs=read8(c,P02S_QUEST_LOG_STATE);if(qs!=sw_return_state){printf("{\"event\":\"quest_transition\",\"before\":%u,\"after\":%u,\"previous_pc\":%u,\"pc\":%u,\"lr\":%u,\"frame\":%u}\n",sw_return_state,qs,sw_last_pc,(unsigned)read_register(c,"pc"),(unsigned)read_register(c,"lr"),sw_frames);fflush(stdout);sw_return_state=qs;}
 sw_last_pc=(unsigned)read_register(c,"pc");
 uint32_t pc=(uint32_t)read_register(c,"pc"),psr=(uint32_t)read_register(c,"cpsr");if(!(psr&32U))return;pc=(pc&~1U)-2U;
 static const uint32_t entries[]={0x08082750U,0x09220198U,0x093BEA68U,0x093BEA98U,0x09392714U,0x0939273CU};
 for(unsigned i=0;i<6;++i)if(pc==entries[i]){++sw_entries[i];printf("{\"event\":\"entry\",\"method\":\"%s\",\"attempt\":%u,\"pc\":%u,\"lr\":%u,\"frame\":%u}\n",sw_method,sw_attempt,pc,(unsigned)read_register(c,"lr"),sw_frames);}
 if(pc==0x09114698U){unsigned lr=(unsigned)read_register(c,"lr");if(lr>=154627632U && lr<154696816U && (unsigned)read_register(c,"r0")==ADDR_ENEMY_PARTY && read_register(c,"r2")==3){++sw_special;sw_move=(unsigned)read_register(c,"r1");printf("{\"event\":\"special_setter\",\"attempt\":%u,\"frame\":%u,\"move\":%u,\"lr\":%u}\n",sw_attempt,sw_frames,sw_move,lr);}}
 if(pc==0x093925F4U && sw_special)++sw_after_setter;
}
static void sw_run_frame(struct mCore*c){
 ++sw_frames;
 if(sw_trace || (sw_caught_frame && sw_frames<sw_caught_frame+250U)){unsigned frame=c->frameCounter(c),steps=0;do{sw_observe(c);c->step(c);++sw_steps;a_require(++steps<2000000U,"instruction frame bound");}while(c->frameCounter(c)==frame);}
 else sw_fast(c);
 unsigned outcome=read8(c,BATTLE_CORE_BATTLE_OUTCOME);if(outcome)lb_outcome=outcome;
 if(outcome==BATTLE_CORE_OUTCOME_CAUGHT && !sw_caught_frame)sw_caught_frame=sw_frames;
}
static void sw_pocket(struct mCore*c,unsigned target){
 for(unsigned k=0;k<6;++k){if(read16(c,BATTLE_CORE_BAG_STATE+6)==target)return;lb_press(c,QOL_KEY_RIGHT,90);}
 sw_need(c,false,"physical Bag pocket navigation");
}
static bool sw_bag(struct mCore*c){
 lb_press(c,QOL_KEY_START,120);if(read32(c,QOL_START_MENU_CALLBACK)!=QOL_START_MENU_INPUT)return false;
 unsigned count=read8(c,QOL_START_MENU_COUNT),target=count;if(!count||count>9)return false;
 for(unsigned i=0;i<count;++i)if(read8(c,QOL_START_MENU_ORDER+i)==2)target=i;
 for(unsigned i=0;i<count && read8(c,QOL_START_MENU_CURSOR)!=target;++i)lb_press(c,QOL_KEY_DOWN,30);
 if(target==count||read8(c,QOL_START_MENU_CURSOR)!=target)return false;
 lb_press(c,QOL_KEY_A,180);return read32(c,BATTLE_CORE_MAIN_CALLBACK2)==P02S_CB2_BAG;
}
static void sw_use(struct mCore*c,unsigned item){
 sw_need(c,lb_field(c),"item start not field");sw_need(c,sw_bag(c),"normal Start/Bag failed");lb_wait(c,180);sw_pocket(c,1U);
 lb_press(c,QOL_KEY_A,120);sw_need(c,read16(c,0x0203ACA8U)==item,"physical key item selection mismatch");
 sw_item_frame=sw_frames;sw_shot("key-selected");sw_trace=true;lb_press(c,QOL_KEY_A,180);sw_state(c,"key-used");sw_shot("key-used");
}
static void sw_radar(struct mCore*c){
 sw_use(c,348U);
 /* Fixture mode is AUTO (0). The source declares 6 menu rows, HIDDEN=4. */
 sw_need(c,read8(c,P02S_FIELD_LOCK)!=0 && !read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER),"radar menu absent");
 for(unsigned i=0;i<4;++i)lb_press(c,QOL_KEY_DOWN,24);
 sw_shot("radar-hidden-selected");lb_press(c,QOL_KEY_A,1);
 for(unsigned f=0;f<1800 && !lb_action(c);++f)lb_frame(c,f%60==0?QOL_KEY_A:0);
 sw_need(c,lb_action(c),"radar did not reach natural battle controller");
}
static bool sw_fishing(struct mCore*c){
 sw_use(c,264U);
 for(unsigned f=0;f<2400 && !lb_action(c);++f){
  if(f>120 && lb_field(c))return false;
  if(f%240==0)sw_state(c,"fishing-wait");
  lb_frame(c,f%60==0?QOL_KEY_A:0);
 }
 return lb_action(c);
}
static void sw_catch(struct mCore*c){
 lb_cursor(c,BATTLE_CORE_ACTION_SELECTION_CURSOR,1);lb_press(c,QOL_KEY_A,180);
 for(unsigned f=0;f<1800 && read32(c,BATTLE_CORE_MAIN_CALLBACK2)!=P02S_CB2_BAG;++f)lb_frame(c,0);
 sw_need(c,read32(c,BATTLE_CORE_MAIN_CALLBACK2)==P02S_CB2_BAG,"battle Bag absent");lb_wait(c,180);sw_pocket(c,2U);sw_shot("ball-pocket");
 lb_press(c,QOL_KEY_A,120);sw_need(c,read16(c,0x0203ACA8U)==1U,"Master Ball was not selected");lb_press(c,QOL_KEY_A,180);
 unsigned stable=0,oldcb=0,oldmap=0,oldout=0;
 for(unsigned f=0;f<24000;++f){
  unsigned cb=read32(c,BATTLE_CORE_MAIN_CALLBACK2),map=read16(c,lb_save1(c)+4),out=read8(c,BATTLE_CORE_BATTLE_OUTCOME);if(cb!=oldcb||map!=oldmap||out!=oldout){fprintf(stderr,"RETURN frame=%u cb=%08x saved=%08x map=%04x count=%u quest=%u/%u out=%u\n",sw_frames,cb,read32(c,BATTLE_CORE_MAIN_CALLBACK2+4),map,read8(c,QOL_PLAYER_PARTY_COUNT),read8(c,P02S_QUEST_LOG_STATE),read8(c,P02S_QUEST_LOG_PLAYBACK_STATE),out);oldcb=cb;oldmap=map;oldout=out;}
  if(!read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER) && lb_field(c)){if(++stable==30)return;}else stable=0;
  lb_frame(c,f%60==0?QOL_KEY_B:0);
 }
 sw_need(c,false,"capture did not return to field");
}
static void sw_copy(struct mCore*c,unsigned a,uint8_t*out,unsigned n){for(unsigned i=0;i<n;++i)out[i]=read8(c,a+i);}
int main(int argc,char**argv){
 if(argc==3 && !strcmp(argv[1],"--guard-check"))a_guard_check(argv[2]);
 if(argc!=5)return 2;
 sw_method=argv[3];sw_prefix=argv[4];bool fishing=!strcmp(sw_method,"fishing");if(!fishing && strcmp(sw_method,"hidden"))return 2;sw_map=fishing?38:63;
 a_require(!strcmp(projectVersion,"0.10.2"),"mGBA version");char rh[65],sh[65],after[65];sha256_file(argv[1],rh);sha256_file(argv[2],sh);a_require(!strcmp(rh,SW_ROM)&&!strcmp(sh,SW_SEED),"fixed ROM/seed identity");
 struct mLogger logger={.log=qol_log,.filter=NULL};mLogSetDefaultLogger(&logger);p03f_rtc_reserve(argv[2]);struct mCore*c=qol_open(argv[1],argv[2]);qol_log_core=c;c->setVideoBuffer(c,sw_video,240);c->reset(c);
 a_require(a_continue(c),"initial Continue");a_flash_prepare(c);a_require(p02s_install_field_fixture(c),"initial field fixture");p02s_enable_national_dex(c);
 (void)call_preserving(c,0x09220861U,3,sw_map,fishing?94:14,fishing?10:11);run_key_frames(c,0,1800);
 for(unsigned k=0;k<12 && !lb_field(c);++k)qol_press(c,QOL_KEY_B,180);
 sw_need(c,lb_field(c),"fixture map not idle");lb_position(c,3,sw_map,fishing?94:14,fishing?10:11);
 clear_parties(c);create_mon(c,QOL_PLAYER_PARTY,4U,100U);write8(c,QOL_PLAYER_PARTY_COUNT,1U);(void)call_preserving(c,0x0809984DU,0,0,0,0);
 for(unsigned f=0x0820;f<=0x082C;++f)(void)call_preserving(c,QOL_FLAG_SET,f,0,0,0);(void)call_preserving(c,QOL_FLAG_SET,0x114B,0,0,0);
 a_require(call_preserving(c,154634137U,15U,1U,0,0)==0 && read8(c,0x0203D01FU)==1,"research fixture");(void)call_preserving(c,P02S_VAR_SET,0x51FF,0,0,0);
 unsigned s1=lb_save1(c),s2=read32(c,QOL_SAVE_BLOCK2_SLOT),key=read16(c,s2+0xf20);
 for(unsigned i=0;i<30;++i){write16(c,s1+0x3b8+4*i,0);write16(c,s1+0x3ba+4*i,key);}write16(c,s1+0x3b8,fishing?264:348);write16(c,s1+0x3ba,1^key);
 for(unsigned i=1;i<=12;++i)g_remove_fixture(c,i);a_require(call_preserving(c,BATTLE_CORE_ADD_BAG_ITEM,1,1,0,0)==1,"ball fixture");
 write16(c,BATTLE_CORE_BAG_STATE+6,1);for(unsigned i=0;i<6;++i)write16(c,BATTLE_CORE_BAG_STATE+8+2*i,0);
 write32_bytes(c,BATTLE_CORE_GLOBAL_RNG,fishing?0x24681357U:0x10293847U);
 unsigned inv[G_ITEMS],expected[G_ITEMS],got[G_ITEMS];g_inventory(c,inv);a_require(inv[1]==1,"ball count");memcpy(expected,inv,sizeof(inv));expected[1]=0;
 unsigned counter=read32(c,P03_SAVE_COUNTER);sw_state(c,"fixture");sw_shot("fixture");
 struct mCore original=*c;a_guard(c);sw_fast=c->runFrame;c->runFrame=sw_run_frame;
 if(fishing){lb_press(c,QOL_KEY_LEFT,30);lb_position(c,3,38,94,10);}
 bool found=false;
 for(sw_attempt=1;sw_attempt<=32;++sw_attempt){
  sw_special=0;sw_move=0;sw_after_setter=0;memset(sw_entries,0,sizeof(sw_entries));
  bool battle;if(fishing)battle=sw_fishing(c);else{sw_radar(c);battle=true;}
  sw_trace=false;if(!battle && fishing){sw_need(c,lb_field(c),"fishing failure did not settle");continue;}sw_need(c,battle,"normal item UI produced no encounter");
  sw_mon(c,ADDR_ENEMY_PARTY,"enemy");
  if(sw_special){found=true;break;}
  sw_need(c,fishing,"radar produced no special move");lb_cursor(c,BATTLE_CORE_ACTION_SELECTION_CURSOR,3);lb_press(c,QOL_KEY_A,60);lb_return(c);
 }
 sw_need(c,found && sw_special==1 && !sw_after_setter && sw_entries[fishing?0:1]==1 && sw_entries[fishing?2:3]==1 && sw_entries[fishing?4:5]==1,"special caller/initializer order differs");
 sw_need(c,read16(c,ADDR_ENEMY_PARTY+50)==sw_move,"special slot was overwritten");sw_encounter_frame=sw_frames;unsigned pid=read32(c,ADDR_ENEMY_PARTY),species=read16(c,ADDR_ENEMY_PARTY+32);uint8_t moves[20];sw_copy(c,ADDR_ENEMY_PARTY+40,moves,20);
 sw_shot("special-enemy");sw_catch(c);sw_need(c,lb_outcome==7 && sw_caught_frame && read8(c,QOL_PLAYER_PARTY_COUNT)==2 && read32(c,QOL_PLAYER_PARTY+100)==pid && read16(c,QOL_PLAYER_PARTY+132)==species,"captured identity");
 uint8_t captured_moves[20];sw_copy(c,QOL_PLAYER_PARTY+140,captured_moves,20);sw_need(c,!memcmp(moves,captured_moves,20),"capture moves/PP changed");g_inventory(c,got);sw_need(c,!memcmp(expected,got,sizeof(got)),"unrelated inventory changed");sw_mon(c,QOL_PLAYER_PARTY+100,"captured");sw_shot("captured");
 uint8_t party[200],loaded[200];sw_copy(c,QOL_PLAYER_PARTY,party,200);lb_resume_x=read16(c,lb_save1(c));lb_resume_y=read16(c,lb_save1(c)+2);
 sw_need(c,lb_normal_save(c) && read32(c,P03_SAVE_COUNTER)==counter+1,"normal Save");sw_saved_frame=sw_frames;sw_mon(c,QOL_PLAYER_PARTY+100,"saved");
 a_restore(c,&original);c->runFrame=sw_fast;qol_close(c);c=qol_open(argv[1],argv[2]);qol_log_core=c;c->setVideoBuffer(c,sw_video,240);c->reset(c);original=*c;a_guard(c);sw_fast=c->runFrame;c->runFrame=sw_run_frame;
 sw_need(c,lb_normal_continue(c),"fresh Continue");sw_reload_frame=sw_frames;sw_copy(c,QOL_PLAYER_PARTY,loaded,200);g_inventory(c,got);
 sw_need(c,read8(c,QOL_PLAYER_PARTY_COUNT)==2 && !memcmp(party,loaded,200) && !memcmp(expected,got,sizeof(got)) && read32(c,P03_SAVE_COUNTER)==counter+1,"fresh Continue persistence");sw_mon(c,QOL_PLAYER_PARTY+100,"reloaded");sw_shot("reloaded");
 a_restore(c,&original);c->runFrame=sw_fast;qol_close(c);qol_log_core=NULL;sha256_file(argv[1],after);a_require(!strcmp(rh,after) && !log_problem_count,"ROM changed/emulator warning");
 printf("{\"status\":\"PASS\",\"scope\":\"SPECIAL_WILD_PHYSICAL_UI_CAPTURE_SAVE_CONTINUE\",\"method\":\"%s\",\"candidate_sha256\":\"%s\",\"species\":%u,\"personality\":%u,\"special_move\":%u,\"attempts\":%u,\"manual_saves\":1,\"fresh_cores\":2,\"host_write_barriers\":7,\"initial_fixtures\":true,\"observed_host_calls\":0,\"ball_consumed\":1,\"party_and_inventory_persisted\":true,\"release_ready\":false,\"witness\":[%u,%u,%u,%u,%u],\"frames\":%u,\"cpu_steps\":%llu}\n",sw_method,rh,species,pid,sw_move,sw_attempt,sw_item_frame,sw_encounter_frame,sw_caught_frame,sw_saved_frame,sw_reload_frame,sw_frames,(unsigned long long)sw_steps);return 0;
}
