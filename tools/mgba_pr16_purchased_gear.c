/* Real shop purchase -> Bag Give -> Save/Continue -> walk to grass -> Mega.
 * The initial map, party, ring, BP, empty item pocket and allowed mechanic
 * policy are fixtures. No item/mon/RNG/battle/map/flag writes after g_open.
 * Prior shop and capture controllers remain immutable embedded helpers. */
#include "pr16_gear_capture_helpers.c"
#include "pr16_gear_route.h"
#define K_SCOPE "PR16_PURCHASE_GIVE_WALK_MEGA_COLD_SAVE"
struct KCase {const char *name;unsigned species,item,mega,ability,base_ability,toggles;};
static const struct KCase k_cases[]={
 {"eelektross-active",411,1012,1634,313,26,1},
 {"eelektross-no-toggle",411,1012,1634,313,26,0},
 {"eelektross-cancel-toggle",411,1012,1634,313,26,2}
};
struct KTrace {unsigned interaction,purchased,bag,equipped,saved,reloaded,boundary,encounter,move_menu,toggle,mega,spent,field,saved_again,reloaded_again;};
static struct KTrace kt;
static unsigned k_growth,k_attack,k_pid;
static void k_state(struct mCore*c,const char*label){
 n_state(c,label);fprintf(stderr,"GEAR item=%u held=%u bagpocket=%u growth=%u attack=%u\n",read16(c,QOL_SPECIAL_VAR_ITEM),read16(c,QOL_PLAYER_PARTY+k_growth+2U),read16(c,BATTLE_CORE_BAG_STATE+6U),k_growth,k_attack);
 fprintf(stderr,"GEAR_FIELD lock=%u quest=%u playback=%u avatar=%u running=%u transition=%u start=%08x\n",read8(c,P02S_FIELD_LOCK),read8(c,P02S_QUEST_LOG_STATE),read8(c,P02S_QUEST_LOG_PLAYBACK_STATE),read8(c,P02S_PLAYER_AVATAR+5U),read8(c,P02S_PLAYER_AVATAR+2U),read8(c,P02S_PLAYER_AVATAR+3U),read32(c,QOL_START_MENU_CALLBACK));
 for(unsigned i=0;i<16U;++i){unsigned t=QOL_TASKS+i*QOL_TASK_SIZE;if(read8(c,t+4U))fprintf(stderr,"TASK %u fn=%08x data=%u,%u,%u,%u,%u,%u\n",i,read32(c,t),read16(c,t+8U),read16(c,t+10U),read16(c,t+12U),read16(c,t+14U),read16(c,t+16U),read16(c,t+18U));}
}
/* Quest-log phase and action-recorder state are distinct enums. The pair
 * (RECORDING=1, RECORDING=2) is live play, not previously-on playback. */
static bool k_quest_live(unsigned quest,unsigned playback){
 return (quest==0U && playback==0U) || (quest==1U && playback==2U);
}
static bool k_equipment_field(struct mCore*c){
 unsigned id=read8(c,P02S_PLAYER_AVATAR+5U);
 /* Ordinary item owners can record a Quest Log scene. Only the following
  * real Start-menu Save may cut/serialize it; never clear the state by host. */
 return read32(c,BATTLE_CORE_MAIN_CALLBACK2)==P02S_CB2_FIELD
  && !read8(c,P02S_FIELD_LOCK)
  && k_quest_live(read8(c,P02S_QUEST_LOG_STATE),read8(c,P02S_QUEST_LOG_PLAYBACK_STATE)) && id<16U
  && (read8(c,P02S_OBJECT_EVENTS+id*0x24U)&1U)
  && !read8(c,P02S_PLAYER_AVATAR+2U) && !read8(c,P02S_PLAYER_AVATAR+3U);
}
static void k_start(struct mCore*c,unsigned action){
 a_require(b_field(c),"gear start menu outside field");b_press(c,QOL_KEY_START,120U);
 a_require(read32(c,QOL_START_MENU_CALLBACK)==QOL_START_MENU_INPUT,"gear Start menu absent");
 unsigned count=read8(c,QOL_START_MENU_COUNT),at=read8(c,QOL_START_MENU_CURSOR),target=count;
 a_require(count && count<=9U && at<count,"gear Start menu invalid");
 for(unsigned i=0;i<count;++i)if(read8(c,QOL_START_MENU_ORDER+i)==action)target=i;
 a_require(target<count,"gear Start action absent");
 for(unsigned i=0,n=(target+count-at)%count;i<n;++i)b_press(c,QOL_KEY_DOWN,30U);
 a_require(read8(c,QOL_START_MENU_CURSOR)==target,"gear Start cursor did not follow input");b_press(c,QOL_KEY_A,180U);
}
static void k_equip(struct mCore*c,unsigned item){
 k_start(c,2U);a_require(read32(c,BATTLE_CORE_MAIN_CALLBACK2)==P02S_CB2_BAG,"gear real Bag absent");
 kt.bag=b_frames;g_shot("bag-stone");a_require(!read16(c,BATTLE_CORE_BAG_STATE+6U),"gear item pocket not retained");
 b_press(c,QOL_KEY_A,120U);k_state(c,"item-actions");g_shot("give-menu");
 a_require(read16(c,QOL_SPECIAL_VAR_ITEM)==item,"gear Bag selected another item");
 /* Native item action list: Give is the second action, not a host call. */
 b_press(c,QOL_KEY_DOWN,30U);b_press(c,QOL_KEY_A,180U);k_state(c,"give-party");g_shot("give-party");
 a_require(read32(c,BATTLE_CORE_MAIN_CALLBACK2)==P02S_CB2_PARTY,"gear Give did not enter real party menu");
 a_require(!read8(c,BATTLE_CORE_SELECTED_PARTY_MON),"gear Give did not select first party slot");b_press(c,QOL_KEY_A,180U);
 for(unsigned i=0;i<30U;++i){
  if(read16(c,QOL_PLAYER_PARTY+k_growth+2U)==item){kt.equipped=b_frames;break;}
  b_press(c,QOL_KEY_A,60U);
 }
 a_require(kt.equipped,"gear selected individual did not receive purchased item");g_shot("equipped");
 /* The native Give completion text waits for confirmation, not cancellation. */
 b_press(c,QOL_KEY_A,180U);k_state(c,"give-confirmed");
 for(unsigned i=0;i<20U && !k_equipment_field(c);++i)b_press(c,QOL_KEY_B,120U);
 k_state(c,"equip-menus-closed");g_shot("equip-menus-closed");
 a_require(k_equipment_field(c),"gear equip menus did not return to field");
}
static void k_path(struct mCore*c,unsigned group,unsigned map,const unsigned path[][2],unsigned count,bool may_encounter){
 for(unsigned i=0;i<count;++i){
  unsigned s=b_save1(c),x=read16(c,s),y=read16(c,s+2U),tx=path[i][0],ty=path[i][1];
  a_require(read8(c,s+4U)==group && read8(c,s+5U)==map,"gear path left audited map");
  a_require((x==tx && (y+1U==ty || ty+1U==y)) || (y==ty && (x+1U==tx || tx+1U==x)),"gear path step is not adjacent");
  n_step(c,x<tx?QOL_KEY_RIGHT:x>tx?QOL_KEY_LEFT:y<ty?QOL_KEY_DOWN:QOL_KEY_UP);
  if(read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER)){a_require(may_encounter,"gear encounter before audited grass");return;}
  b_position(c,group,map,tx,ty);
 }
}
static void k_fixture_mon(struct mCore*c,const struct KCase*v){
 clear_parties(c);create_mon(c,QOL_PLAYER_PARTY,v->species,100U);write8(c,QOL_PLAYER_PARTY_COUNT,1U);
 k_pid=read32(c,QOL_PLAYER_PARTY);unsigned ng=0U,na=0U;
 unsigned moves[4],pp[4];
 for(unsigned j=0;j<4U;++j){moves[j]=call_preserving(c,BATTLE_CORE_GET_MON_DATA,QOL_PLAYER_PARTY,QOL_MON_DATA_MOVE1+j,0,0);pp[j]=call_preserving(c,BATTLE_CORE_GET_MON_DATA,QOL_PLAYER_PARTY,MON_DATA_PP1+j,0,0);}
 for(unsigned i=0;i<4U;++i){unsigned at=32U+12U*i;
  if(read16(c,QOL_PLAYER_PARTY+at)==v->species && !read16(c,QOL_PLAYER_PARTY+at+2U)){k_growth=at;++ng;}
  bool match=true;for(unsigned j=0;j<4U;++j)if(read16(c,QOL_PLAYER_PARTY+at+2U*j)!=moves[j] || read8(c,QOL_PLAYER_PARTY+at+8U+j)!=pp[j])match=false;
  if(match){k_attack=at;++na;}
 }
 a_require(ng==1U && na==1U && k_growth!=k_attack && moves[0] && pp[0],"gear fixture mon plain substructures ambiguous");
}
int main(int argc,char**argv){
 if(argc==3 && !strcmp(argv[1],"--guard-check")){a_guard_check(argv[2]);}
 if(argc!=7)return 2;
 const struct KCase*v=NULL;for(unsigned i=0;i<sizeof(k_cases)/sizeof(k_cases[0]);++i)if(!strcmp(argv[5],k_cases[i].name))v=&k_cases[i];if(!v)return 2;
 g_prefix=argv[6];char hash[65],seed[65],after[65];sha256_file(argv[1],hash);sha256_file(argv[2],seed);
 a_require(!strcmp(hash,N_SHA) && !strcmp(hash,argv[3]) && !strcmp(seed,B_SEED_SHA) && !strcmp(seed,argv[4]),"gear fixed inputs differ");
 struct mLogger logger={.log=qol_log,.filter=NULL};mLogSetDefaultLogger(&logger);p03f_rtc_reserve(argv[2]);
 struct mCore*c=qol_open(argv[1],argv[2]);qol_log_core=c;c->setVideoBuffer(c,b_video,240U);c->reset(c);a_require(a_continue(c),"gear initial Continue failed");a_flash_prepare(c);
 (void)call_preserving(c,0x09220861U,96U,5U,24U,20U);run_key_frames(c,0,1800U);
 for(unsigned i=0;i<12U && !b_field(c);++i){b_press(c,QOL_KEY_B,180U);}
 b_position(c,96U,5U,24U,20U);
 k_fixture_mon(c,v);(void)call_preserving(c,0x0809984DU,0,0,0,0);
 uint32_t inventory[G_ITEMS];g_inventory(c,inventory);
 unsigned slots=read32(c,0x020397D8U),ids[42];for(unsigned i=0;i<42U;++i)ids[i]=read16(c,slots+4U*i);
 for(unsigned i=0;i<42U;++i)if(ids[i])g_remove_fixture(c,ids[i]);
 for(unsigned i=0;i<45U;++i){g_remove_fixture(c,999U+i);(void)call_preserving(c,QOL_FLAG_CLEAR,0x14A0U+i,0,0,0);}
 g_remove_fixture(c,580U);a_require(call_preserving(c,QOL_ADD_BAG_ITEM,580U,1U,0,0)==1U,"gear initial ring fixture rejected");
 write16(c,QOL_LEDGER+0x392U,64U);a_require(call_preserving(c,0x091261F5U,5U,1U,0,0)==1U,"gear allowed mechanic policy fixture rejected");
 (void)call_preserving(c,QOL_SAVE_FINALIZE,QOL_LEDGER,0,0,0);
 write16(c,BATTLE_CORE_BAG_STATE+6U,0U);for(unsigned i=0;i<6U;++i)write16(c,BATTLE_CORE_BAG_STATE+8U+2U*i,0U);
 uint32_t before[G_ITEMS],now[G_ITEMS],bought[G_ITEMS];g_inventory(c,before);memcpy(bought,before,sizeof(bought));bought[v->item]++;
 uint8_t mon[100],snapshot[100],loaded[100];b_copy(c,QOL_PLAYER_PARTY,mon,100U);unsigned counter=read32(c,P03_SAVE_COUNTER),index=v->item-999U;
 g_shot("fixture");struct mCore original=*c;a_guard(c);
 /* Synchronize physical direction after native fixture calls. The inherited
  * shop helper uses one frame, which is not a full input pulse at this phase. */
 b_frames_run(c,0U,60U);b_press(c,QOL_KEY_UP,60U);b_position(c,96U,5U,24U,20U);
 unsigned avatar=read8(c,P02S_PLAYER_AVATAR+5U);
 a_require(avatar<16U && (read8(c,P02S_OBJECT_EVENTS+avatar*0x24U+0x18U)&15U)==2U,"gear physical facing did not settle north");
 kt.interaction=b_frames+1U;g_open(c,true);g_menu_check(c,45U);
 for(unsigned page=0;page<index/5U;++page){g_down(c,5U);b_press(c,QOL_KEY_A,60U);g_menu_check(c,45U);a_require(read8(c,G_STATE+95U)==page+1U,"gear shop page differs");}
 g_down(c,index%5U);b_press(c,QOL_KEY_A,180U);g_finish(c);kt.purchased=b_frames;g_inventory(c,now);
 a_require(read16(c,G_STATE+90U)==0U && !memcmp(now,bought,sizeof(now)) && read16(c,QOL_LEDGER+0x392U)==48U && read32(c,P03_SAVE_COUNTER)==counter+1U,"gear physical purchase/BP/autosave differs");g_shot("purchased");
 k_equip(c,v->item);g_inventory(c,now);b_copy(c,QOL_PLAYER_PARTY,snapshot,100U);
 a_require(!memcmp(now,before,sizeof(now)),"gear Give changed unrelated inventory");
 for(unsigned i=0;i<100U;++i)if(i!=k_growth+2U && i!=k_growth+3U && i!=28U && i!=29U)a_require(mon[i]==snapshot[i],"gear Give changed unrelated mon bytes");
 a_require(b_save(c),"gear equipped native Save failed");kt.saved=b_frames;
 a_restore(c,&original);c=b_restart(c,argv[1],argv[2]);c->reset(c);original=*c;a_guard(c);a_require(b_continue(c),"gear equipped cold Continue failed");kt.reloaded=b_frames;
 b_copy(c,QOL_PLAYER_PARTY,loaded,100U);g_inventory(c,now);a_require(!memcmp(snapshot,loaded,100U) && !memcmp(now,before,sizeof(now)) && read32(c,P03_SAVE_COUNTER)==counter+2U && read16(c,QOL_LEDGER+0x392U)==48U,"gear equipped cold save changed data");g_shot("equipped-reloaded");
 k_path(c,96U,5U,k_town_path,sizeof(k_town_path)/sizeof(k_town_path[0]),false);n_step(c,QOL_KEY_UP);b_position(c,96U,17U,11U,39U);kt.boundary=b_frames;g_shot("physical-map-boundary");
 k_path(c,96U,17U,k_grass_path,sizeof(k_grass_path)/sizeof(k_grass_path[0]),true);
 for(unsigned i=0;i<1024U && !read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER);++i){unsigned s=b_save1(c),x=read16(c,s),y=read16(c,s+2U);a_require(y==30U && (x==14U || x==15U),"gear grass pair differs");n_step(c,x==14U?QOL_KEY_RIGHT:QOL_KEY_LEFT);}
 a_require(n_action(c),"gear normal walk did not reach native encounter");kt.encounter=b_frames;
 unsigned enemy=read16(c,ADDR_BATTLE_MONS+BATTLE_MON_SIZE),level=read8(c,ADDR_BATTLE_MONS+BATTLE_MON_SIZE+BATTLE_CORE_MON_LEVEL),flags=read32(c,ADDR_BATTLE_TYPE_FLAGS);
 fprintf(stderr,"GEAR_ENCOUNTER species=%u level=%u flags=%08x frame=%u\n",enemy,level,flags,kt.encounter);
 a_require(!(flags&8U) && !read16(c,ADDR_BATTLER_PARTY_INDEXES) && read16(c,ADDR_BATTLE_MONS)==v->species && read16(c,ADDR_BATTLE_MONS+0x2eU)==v->item && read16(c,ADDR_BATTLE_MONS+0x38U)==v->base_ability && read32(c,QOL_PLAYER_PARTY)==k_pid,"gear natural battler identity/item/base ability differs");g_shot("natural-equipped-battle");
 unsigned move=read16(c,ADDR_BATTLE_MONS+BATTLE_MON_MOVES_OFFSET),pp=read8(c,ADDR_BATTLE_MONS+BATTLE_MON_PP_OFFSET),after_pp=pp,observed_species=v->species,observed_ability=v->base_ability;
 n_cursor(c,0U);b_press(c,QOL_KEY_A,60U);a_require(read8(c,0x02022B24U)==0x14U && (read32(c,0x02023B28U)&1U),"gear physical move menu absent");kt.move_menu=b_frames;
 for(unsigned i=0;i<6U && read8(c,BATTLE_CORE_MOVE_SELECTION_CURSOR);++i)b_press(c,read8(c,BATTLE_CORE_MOVE_SELECTION_CURSOR)&1U?QOL_KEY_LEFT:QOL_KEY_UP,12U);
 a_require(!read8(c,BATTLE_CORE_MOVE_SELECTION_CURSOR),"gear first move cursor differs");
 for(unsigned i=0;i<v->toggles;++i){if(!kt.toggle)kt.toggle=b_frames+1U;b_press(c,QOL_KEY_START,30U);}g_shot("mega-selection");b_press(c,QOL_KEY_A,2U);
 for(unsigned f=0;f<18000U;++f){
  unsigned battle_outcome=read8(c,BATTLE_CORE_BATTLE_OUTCOME);if(battle_outcome)n_outcome=battle_outcome;
  unsigned sp=read16(c,ADDR_BATTLE_MONS),ab=read16(c,ADDR_BATTLE_MONS+0x38U),p=read8(c,ADDR_BATTLE_MONS+BATTLE_MON_PP_OFFSET);
  if(sp==v->mega && !kt.mega){kt.mega=b_frames;observed_species=sp;observed_ability=ab;g_shot("mega-active");}
  if(p<pp && !kt.spent){kt.spent=b_frames;after_pp=p;}
  if(kt.spent && n_action(c))break;
  if(!read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER) && b_field(c))break;
  b_frame(c,f%60U==0U?QOL_KEY_B:0U);
 }
 a_require(kt.spent && pp-after_pp<=2U,"gear battler did not spend native move PP");
 a_require(v->toggles==1U?(kt.mega>kt.toggle && kt.spent>kt.mega && observed_species==v->mega && observed_ability==v->ability):!kt.mega,"gear native Mega activation/control differs");g_shot("native-turn");
 if(read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER)){a_require(n_action(c),"gear native turn did not reach action controller");n_cursor(c,3U);b_press(c,QOL_KEY_A,60U);n_return(c,false);}
 kt.field=b_frames;unsigned outcome=n_outcome;
 a_require(b_field(c) && !read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER) && (outcome==1U || outcome==4U) && read32(c,QOL_PLAYER_PARTY)==k_pid && read16(c,QOL_PLAYER_PARTY+k_growth)==v->species && read16(c,QOL_PLAYER_PARTY+k_growth+2U)==v->item && read8(c,QOL_PLAYER_PARTY+k_attack+8U)==after_pp,"gear native return/reversion/held item/PP differs");g_shot("reverted-field");
 a_require(b_save(c),"gear postbattle native Save failed");kt.saved_again=b_frames;b_copy(c,QOL_PLAYER_PARTY,snapshot,100U);
 a_restore(c,&original);c=b_restart(c,argv[1],argv[2]);c->reset(c);original=*c;a_guard(c);a_require(b_continue(c),"gear third core Continue failed");kt.reloaded_again=b_frames;
 b_copy(c,QOL_PLAYER_PARTY,loaded,100U);g_inventory(c,now);a_require(!memcmp(snapshot,loaded,100U) && !memcmp(now,before,sizeof(now)) && read8(c,QOL_PLAYER_PARTY_COUNT)==1U && read32(c,P03_SAVE_COUNTER)==counter+3U && read16(c,QOL_LEDGER+0x392U)==48U,"gear third core changed party/inventory/BP/save counter");g_shot("battle-reloaded");
 a_restore(c,&original);qol_close(c);qol_log_core=NULL;sha256_file(argv[1],after);a_require(!strcmp(hash,after) && !log_problem_count,"gear ROM changed or emulator warned");
 printf("{\"schema_version\":1,\"status\":\"PASS\",\"scope\":\"%s\",\"case\":\"%s\",\"rom_sha256\":\"%s\",",K_SCOPE,v->name,hash);
 printf("\"species\":%u,\"item\":%u,\"mega_species\":%u,\"ability\":%u,\"toggles\":%u,\"personality\":%u,\"enemy_species\":%u,\"enemy_level\":%u,\"move\":%u,\"pp_before\":%u,\"pp_after\":%u,\"outcome\":%u,\"walking_steps\":%u,",v->species,v->item,observed_species,observed_ability,v->toggles,k_pid,enemy,level,move,pp,after_pp,outcome,n_steps);
 printf("\"bp_before\":64,\"bp_after\":48,\"automatic_saves\":1,\"manual_saves\":2,\"fresh_cores\":3,\"host_write_barriers\":7,\"party_inventory_bp_persisted\":true,\"physical_give\":true,\"physical_map_transition\":true,\"held_stone_not_consumed\":true,\"initial_map_party_ring_bp_policy_are_fixtures\":true,\"ring_bp_natural_acquisition_accepted\":false,\"full_p05_acceptance\":false,\"release_ready\":false,\"warnings_errors\":0,\"total_frames\":%u,\"witness\":{",b_frames);
#define KW(n) printf("\""#n"\":%u,",kt.n)
 KW(interaction);KW(purchased);KW(bag);KW(equipped);KW(saved);KW(reloaded);KW(boundary);KW(encounter);KW(move_menu);KW(toggle);KW(mega);KW(spent);KW(field);KW(saved_again);
#undef KW
 printf("\"reloaded_again\":%u}}\n",kt.reloaded_again);return 0;
}
