/* Natural walking -> native wild -> physical Bag/ball -> Save/Continue.
 * Initial map, lead and one Master Ball are fixtures. The target is NOT
 * created/injected; neither RNG nor encounter/ball routines are called.
 * The seven host-write barriers remain active throughout observation. */
#include "pr16_capture_shop_helpers.c"
#define N_SHA "e630f7f199194fb4b531ff3a561da866902aea200770a832aec5c276e1636267"
#define N_SCOPE "PR16_NATURAL_WALK_CAPTURE_COLD_SAVE"
#define N_TARGET 411U
struct NCase {const char *name;unsigned map,x,y,ex,ey;};
static const struct NCase n_cases[]={
 {"cave-113",113,2,1,3,1},{"cave-118",118,11,4,12,4}
};
static unsigned n_encounters,n_target_level,n_steps,n_bags,n_outcome,n_escaped;
static unsigned n_walk_frame,n_encounter_frame,n_bag_frame,n_caught_frame,n_saved_frame,n_reload_frame;
static unsigned n_pid;
static void n_state(struct mCore*c,const char*label){
 g_state(c,label);fprintf(stderr,"CAPTURE encounters=%u steps=%u target_level=%u newbs=%08x main=%08x ctrl=%08x exec=%x command=%u cursor=%u outcome=%u enemy=%u\n",n_encounters,n_steps,n_target_level,read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER),read32(c,0x03004FC4U),read32(c,0x03005020U),read32(c,0x02023B28U),read8(c,0x02022B24U),read8(c,BATTLE_CORE_ACTION_SELECTION_CURSOR),read8(c,BATTLE_CORE_BATTLE_OUTCOME),read16(c,ADDR_BATTLE_MONS+BATTLE_MON_SIZE));
}
static bool n_action(struct mCore*c){
 unsigned ctrl=read32(c,0x03005020U);
 return read32(c,0x03004FC4U)==0x08013861U && (read32(c,0x02023B28U)&1U) && read8(c,0x02022B24U)==0x12U && (ctrl==0x0802DC15U || ctrl==0x09118B85U);
}
static void n_wait_action(struct mCore*c){
 for(unsigned f=0;f<12000U;++f){if(n_action(c)){c->setKeys(c,0);return;}b_frame(c,f%60U==0U?QOL_KEY_A:0);}
 n_state(c,"action-timeout");g_shot("action-timeout");a_die("natural encounter did not reach action controller");
}
static void n_cursor(struct mCore*c,unsigned target){
 a_require(n_action(c),"action selection outside real controller");
 for(unsigned k=0;k<6U;++k){unsigned at=read8(c,BATTLE_CORE_ACTION_SELECTION_CURSOR);a_require(at<4U,"invalid battle cursor");if(at==target)return;
  b_press(c,(at&1U)!=(target&1U)?((target&1U)?QOL_KEY_RIGHT:QOL_KEY_LEFT):((target&2U)?QOL_KEY_DOWN:QOL_KEY_UP),12U);
 }
 a_die("battle cursor did not follow physical input");
}
static void n_return(struct mCore*c,bool caught){
 unsigned stable=0;
 for(unsigned f=0;f<24000U;++f){
  unsigned outcome=read8(c,BATTLE_CORE_BATTLE_OUTCOME);if(outcome)n_outcome=outcome;
  if(caught && outcome==BATTLE_CORE_OUTCOME_CAUGHT && !n_caught_frame)n_caught_frame=b_frames;
  if(!read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER) && b_field(c)){if(++stable==30U){c->setKeys(c,0);return;}}else stable=0;
  if(!caught && n_action(c)){n_cursor(c,3U);b_press(c,QOL_KEY_A,60U);continue;}
  b_frame(c,f%60U==0U?QOL_KEY_B:0);
 }
 n_state(c,"return-timeout");g_shot("return-timeout");a_die("capture/run did not return to field");
}
static void n_step(struct mCore*c,unsigned key){
 a_require(b_field(c),"natural step outside idle field");unsigned s=b_save1(c),x=read16(c,s),y=read16(c,s+2U);bool moved=false;
 for(unsigned f=0;f<90U;++f){b_frame(c,key);s=b_save1(c);if(read16(c,s)!=x || read16(c,s+2U)!=y){moved=true;break;}}
 c->setKeys(c,0);a_require(moved,"natural walking pair blocked");++n_steps;unsigned stable=0;
 for(unsigned f=0;f<12000U;++f){
  if(read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER)){n_wait_action(c);return;}
  if(b_field(c)){if(++stable==12U)return;}else stable=0;
  b_frame(c,0);
 }
 n_state(c,"walk-timeout");g_shot("walk-timeout");a_die("natural step neither settled nor entered battle");
}
static void n_capture(struct mCore*c){
 n_cursor(c,1U);b_press(c,QOL_KEY_A,180U);
 for(unsigned f=0;f<1800U && read32(c,BATTLE_CORE_MAIN_CALLBACK2)!=P02S_CB2_BAG;++f)b_frame(c,0);
 a_require(read32(c,BATTLE_CORE_MAIN_CALLBACK2)==P02S_CB2_BAG,"battle did not open real Bag");
 b_frames_run(c,0,180U);++n_bags;n_bag_frame=b_frames;n_state(c,"ball-pocket");g_shot("ball-pocket");
 a_require(read16(c,BATTLE_CORE_BAG_STATE+6U)==BATTLE_CORE_BAG_BALL_POCKET,"prepared ball pocket was not retained");
 b_press(c,QOL_KEY_A,180U);g_shot("ball-selected");b_press(c,QOL_KEY_A,180U);n_return(c,true);
 a_require(n_outcome==BATTLE_CORE_OUTCOME_CAUGHT && n_caught_frame && read8(c,QOL_PLAYER_PARTY_COUNT)==2U,"native capture result missing");
 a_require(read16(c,QOL_PLAYER_PARTY+100U+32U)==N_TARGET && read32(c,QOL_PLAYER_PARTY+100U)==n_pid,"captured individual is not the naturally generated target");
}
int main(int argc,char**argv){
 if(argc==3 && !strcmp(argv[1],"--guard-check"))a_guard_check(argv[2]);
 if(argc!=7)return 2;
 const struct NCase*v=NULL;
 for(unsigned k=0;k<sizeof(n_cases)/sizeof(n_cases[0]);++k)if(!strcmp(argv[5],n_cases[k].name))v=&n_cases[k];
 if(!v)return 2;
 g_prefix=argv[6];char hash[65],seed[65],after[65];sha256_file(argv[1],hash);sha256_file(argv[2],seed);
 a_require(!strcmp(hash,N_SHA) && !strcmp(hash,argv[3]) && !strcmp(seed,B_SEED_SHA) && !strcmp(seed,argv[4]),"natural capture input identity differs");
 struct mLogger logger={.log=qol_log,.filter=NULL};mLogSetDefaultLogger(&logger);p03f_rtc_reserve(argv[2]);
 struct mCore*c=qol_open(argv[1],argv[2]);qol_log_core=c;c->setVideoBuffer(c,b_video,240U);c->reset(c);a_require(a_continue(c),"capture initial Continue failed");a_flash_prepare(c);
 (void)call_preserving(c,0x09220861U,1U,v->map,v->x,v->y);run_key_frames(c,0,1800U);
 for(unsigned k=0;k<12U && !b_field(c);++k)b_press(c,QOL_KEY_B,180U);
 n_state(c,"fixture-warp");g_shot("fixture");b_position(c,1U,v->map,v->x,v->y);
 clear_parties(c);create_mon(c,QOL_PLAYER_PARTY,4U,100U);write8(c,QOL_PLAYER_PARTY_COUNT,1U);
 (void)call_preserving(c,0x0809984DU,0,0,0,0);
 for(unsigned i=1U;i<=12U;++i)g_remove_fixture(c,i);
 a_require(call_preserving(c,BATTLE_CORE_ADD_BAG_ITEM,BATTLE_CORE_MASTER_BALL,1U,0,0)==1U,"one ball fixture rejected");
 write16(c,BATTLE_CORE_BAG_STATE+6U,BATTLE_CORE_BAG_BALL_POCKET);for(unsigned i=0;i<6U;++i)write16(c,BATTLE_CORE_BAG_STATE+8U+i*2U,0U);
 uint32_t before[G_ITEMS],expected[G_ITEMS],now[G_ITEMS];g_inventory(c,before);a_require(before[1]==1U,"ball fixture count differs");memcpy(expected,before,sizeof(expected));expected[1]=0;
 unsigned counter=read32(c,P03_SAVE_COUNTER);a_require(!read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER),"fixture unexpectedly in battle");
 /* No target/RNG/encounter/ball edits. No host writes from here through reload. */
 struct mCore original=*c;a_guard(c);n_walk_frame=b_frames+1U;
 bool found=false;
 for(unsigned step=0;step<2048U && n_encounters<64U;++step){
  unsigned s=b_save1(c),x=read16(c,s),y=read16(c,s+2U);a_require(read8(c,s+4U)==1U && read8(c,s+5U)==v->map,"walking left audited map");
  bool start=x==v->x && y==v->y,end=x==v->ex && y==v->ey;a_require(start || end,"walk left audited coordinate pair");
  n_step(c,start?(v->ex>v->x?QOL_KEY_RIGHT:QOL_KEY_DOWN):(v->ex>v->x?QOL_KEY_LEFT:QOL_KEY_UP));
  if(!read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER))continue;
  ++n_encounters;unsigned species=read16(c,ADDR_BATTLE_MONS+BATTLE_MON_SIZE),level=read8(c,ADDR_BATTLE_MONS+BATTLE_MON_SIZE+BATTLE_CORE_MON_LEVEL);
  fprintf(stderr,"NATURAL_ENCOUNTER number=%u step=%u species=%u level=%u flags=%08x frame=%u\n",n_encounters,n_steps,species,level,read32(c,ADDR_BATTLE_TYPE_FLAGS),b_frames);
  if(species==N_TARGET){n_target_level=level;n_pid=read32(c,ADDR_ENEMY_PARTY);n_encounter_frame=b_frames;g_shot("natural-target");found=true;break;}
  n_cursor(c,3U);b_press(c,QOL_KEY_A,60U);n_return(c,false);++n_escaped;
 }
 a_require(found,"bounded real walking did not encounter the source-proven target");n_capture(c);g_inventory(c,now);a_require(!memcmp(now,expected,sizeof(now)),"capture changed unrelated inventory");
 uint8_t party[200],reloaded[200];b_copy(c,QOL_PLAYER_PARTY,party,200U);g_shot("captured-field");
 a_require(b_save(c),"captured individual normal Save failed");n_saved_frame=b_frames;
 a_require(read32(c,P03_SAVE_COUNTER)==counter+1U,"capture save counter differs");a_restore(c,&original);c=b_restart(c,argv[1],argv[2]);c->reset(c);original=*c;a_guard(c);
 a_require(b_continue(c),"captured individual cold Continue failed");n_reload_frame=b_frames;
 b_copy(c,QOL_PLAYER_PARTY,reloaded,200U);g_inventory(c,now);
 a_require(read8(c,QOL_PLAYER_PARTY_COUNT)==2U && !memcmp(party,reloaded,200U) && !memcmp(now,expected,sizeof(now)) && read32(c,P03_SAVE_COUNTER)==counter+1U,"cold Continue lost capture/inventory/save identity");
 g_shot("reloaded");a_restore(c,&original);qol_close(c);qol_log_core=NULL;sha256_file(argv[1],after);a_require(!strcmp(hash,after) && !log_problem_count,"capture ROM changed or emulator warned");
 printf("{\"schema_version\":1,\"status\":\"PASS\",\"scope\":\"%s\",\"case\":\"%s\",\"rom_sha256\":\"%s\",\"species\":411,\"map\":%u,\"level\":%u,\"personality\":%u,",N_SCOPE,v->name,hash,v->map,n_target_level,n_pid);
 printf("\"walking_steps\":%u,\"encounters\":%u,\"escaped\":%u,\"bag_openings\":%u,\"outcome\":%u,\"manual_saves\":1,\"fresh_cores\":2,\"host_write_barriers\":7,\"ball_consumed\":1,\"party_and_inventory_persisted\":true,",n_steps,n_encounters,n_escaped,n_bags,n_outcome);
 printf("\"map_lead_ball_are_fixtures\":true,\"target_and_rng_injected\":false,\"natural_capture_accepted\":true,\"gear_acquisition_accepted\":false,\"battle_connection_accepted\":false,\"full_p05_acceptance\":false,\"release_ready\":false,\"warnings_errors\":0,\"total_frames\":%u,",b_frames);
 printf("\"witness\":{\"walking\":%u,\"encounter\":%u,\"bag\":%u,\"caught\":%u,\"saved\":%u,\"reloaded\":%u}}\n",n_walk_frame,n_encounter_frame,n_bag_frame,n_caught_frame,n_saved_frame,n_reload_frame);return 0;
}
