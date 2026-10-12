/* 正規NPC受取 -> Bag Give -> Save/fresh Continue -> 歩行エンカウント。
 * 初期位置/進行/party/石だけfixture。RingとNEXTは注入しない。
 * 観測開始以降は7重host-write guard下で入力と読取だけを行う。 */
#include "pr16_ring_gear_helpers.c"
#include "pr16_ring_policy_generated.h"
#include "../overlays/cfru/integration.h"
#include <stddef.h>
#define RP_RESULT 0x02037004U
#define RP_POLICY_OFFSET 0x558U
_Static_assert(offsetof(CfruIntegrationState,mechanic)==793U,"read-only target policy ABI changed");
struct RPCase {struct KCase gear;unsigned grant;};
static const struct RPCase rp_cases[]={
 {{"ring-active",411,1012,1634,313,26,1,1},1},
 {{"ring-unowned",411,1012,1634,313,26,1,1},0},
 {{"ring-wrong-stone",411,1014,1634,313,26,1,1},1},
 {{"ring-no-toggle",411,1012,1634,313,26,0,1},1},
 {{"ring-cancel-toggle",411,1012,1634,313,26,2,1},1}
};
static unsigned rp_mode(struct mCore*c){
 unsigned p=read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER);a_require(p02s_ewram_pointer(p),"Ring policy battle allocation absent");
 return read8(c,p+RP_POLICY_OFFSET+offsetof(CfruIntegrationState,mechanic)+offsetof(CfruMechanicState,battle_mode));
}
static unsigned rp_used(struct mCore*c){
 unsigned p=read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER);a_require(p02s_ewram_pointer(p),"Ring policy usage allocation absent");
 return read8(c,p+RP_POLICY_OFFSET+offsetof(CfruIntegrationState,mechanic)+offsetof(CfruMechanicState,used));
}
static unsigned rp_talk(struct mCore*c,unsigned result){
 a_require(b_field(c),"Ring conversation outside field");b_position(c,RP_GROUP,RP_MAP,RP_X,RP_Y);
 unsigned avatar=read8(c,P02S_PLAYER_AVATAR+5U);a_require(avatar<16U,"Ring avatar absent");
 if((read8(c,P02S_OBJECT_EVENTS+avatar*0x24U+0x18U)&15U)!=2U)b_frame(c,QOL_KEY_UP);
 b_frames_run(c,0,30U);b_position(c,RP_GROUP,RP_MAP,RP_X,RP_Y);
 unsigned frame=b_frames+1U;b_press(c,QOL_KEY_A,30U);
 for(unsigned i=0;i<1800U;++i){
  if(read8(c,P02S_FIELD_LOCK) && read16(c,RP_RESULT)==result){
   b_frames_run(c,0,45U);g_shot("npc-dialogue");g_finish(c);
   a_require(read16(c,RP_RESULT)==result,"Ring dialogue result changed");
   b_position(c,RP_GROUP,RP_MAP,RP_X,RP_Y);return frame;
  }
  b_frame(c,0U);
 }
 k_state(c,"ring-dialogue-timeout");g_shot("ring-dialogue-timeout");a_die("real Ring dialogue absent");return 0;
}
int main(int argc,char**argv){
 if(argc==3 && !strcmp(argv[1],"--guard-check"))a_guard_check(argv[2]);
 if(argc!=7)return 2;
 const struct RPCase*r=NULL;for(unsigned i=0;i<sizeof(rp_cases)/sizeof(rp_cases[0]);++i)if(!strcmp(argv[5],rp_cases[i].gear.name))r=&rp_cases[i];if(!r)return 2;
 const struct KCase*v=&r->gear;bool active=r->grant && v->item==1012U && v->toggles==1U;
 g_prefix=argv[6];char hash[65],seed[65],after[65];sha256_file(argv[1],hash);sha256_file(argv[2],seed);
 a_require(!strcmp(hash,RP_SHA) && !strcmp(hash,argv[3]) && !strcmp(seed,B_SEED_SHA) && !strcmp(seed,argv[4]),"Ring policy input identity differs");
 struct mLogger logger={.log=qol_log,.filter=NULL};mLogSetDefaultLogger(&logger);p03f_rtc_reserve(argv[2]);
 struct mCore*c=qol_open(argv[1],argv[2]);qol_log_core=c;c->setVideoBuffer(c,b_video,240U);c->reset(c);
 a_require(a_continue(c),"Ring policy initial Continue failed");a_flash_prepare(c);
 (void)call_preserving(c,0x09220861U,RP_GROUP,RP_MAP,RP_X,RP_Y);run_key_frames(c,0,1800U);
 for(unsigned i=0;i<12U && !b_field(c);++i)b_press(c,QOL_KEY_B,180U);
 b_position(c,RP_GROUP,RP_MAP,RP_X,RP_Y);a_require(b_field(c),"Ring policy fixture field absent");
 k_fixture_mon(c,v);(void)call_preserving(c,0x0809984DU,0,0,0,0);
 unsigned slots=read32(c,0x020397D8U),ids[42];for(unsigned i=0;i<42U;++i)ids[i]=read16(c,slots+4U*i);
 for(unsigned i=0;i<42U;++i)if(ids[i])g_remove_fixture(c,ids[i]);
 g_remove_fixture(c,580U);
 a_require(call_preserving(c,QOL_ADD_BAG_ITEM,v->item,1U,0,0)==1U,"Ring held-stone fixture rejected");
 (void)call_preserving(c,r->grant?QOL_FLAG_SET:QOL_FLAG_CLEAR,0x13FFU,0,0,0);
 a_require(call_preserving(c,0x08099A09U,580U,1U,0,0)!=0U,"Ring key pocket fixture full");
 write16(c,BATTLE_CORE_BAG_STATE+6U,0U);for(unsigned i=0;i<6U;++i)write16(c,BATTLE_CORE_BAG_STATE+8U+2U*i,0U);
 uint32_t before[G_ITEMS],wanted[G_ITEMS],now[G_ITEMS];g_inventory(c,before);memcpy(wanted,before,sizeof(wanted));
 a_require(!before[580] && before[v->item]==1U && !read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER),"Ring initial unowned/stone/field differs");
 uint8_t mon[100],snapshot[100],loaded[100];b_copy(c,QOL_PLAYER_PARTY,mon,100U);
 unsigned counter=read32(c,P03_SAVE_COUNTER),bp=read16(c,QOL_LEDGER+0x392U);g_shot("fixture");
 /* OBSERVATION_BARRIER: この下にhost RAM/ROM書込・callee注入を置かない。 */
 struct mCore original=*c;a_guard(c);
 kt.interaction=rp_talk(c,r->grant?1U:3U);kt.purchased=b_frames;wanted[580]=r->grant;
 g_inventory(c,now);b_copy(c,QOL_PLAYER_PARTY,loaded,100U);
 a_require(!memcmp(now,wanted,sizeof(now)) && !memcmp(mon,loaded,100U) && read32(c,P03_SAVE_COUNTER)==counter && read16(c,QOL_LEDGER+0x392U)==bp,"Ring grant changed unrelated state or autosaved");
 k_equip(c,v->item);wanted[v->item]=0U;g_inventory(c,now);b_copy(c,QOL_PLAYER_PARTY,snapshot,100U);
 a_require(!memcmp(now,wanted,sizeof(now)),"Ring Give changed unrelated inventory");
 for(unsigned i=0;i<100U;++i)if(i!=k_growth+2U && i!=k_growth+3U && i!=28U && i!=29U)a_require(mon[i]==snapshot[i],"Ring Give changed unrelated individual bytes");
 a_require(b_save(c),"Ring equipped normal Save failed");kt.saved=b_frames;
 a_require(read32(c,P03_SAVE_COUNTER)==counter+1U,"Ring equipped Save counter differs");
 a_restore(c,&original);c=b_restart(c,argv[1],argv[2]);c->reset(c);original=*c;a_guard(c);
 a_require(b_continue(c),"Ring equipped fresh Continue failed");kt.reloaded=b_frames;
 b_copy(c,QOL_PLAYER_PARTY,loaded,100U);g_inventory(c,now);
 a_require(!memcmp(snapshot,loaded,100U) && !memcmp(now,wanted,sizeof(now)) && read32(c,P03_SAVE_COUNTER)==counter+1U && read16(c,QOL_LEDGER+0x392U)==bp,"Ring prebattle Continue lost party/inventory/BP/save");
 b_position(c,RP_GROUP,RP_MAP,RP_X,RP_Y);g_shot("equipped-reloaded");kt.boundary=b_frames+1U;
 k_path(c,RP_GROUP,RP_MAP,k_grass_path,sizeof(k_grass_path)/sizeof(k_grass_path[0]),true);
 for(unsigned i=0;i<1024U && !read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER);++i){unsigned s=b_save1(c),x=read16(c,s),y=read16(c,s+2U);a_require(y==30U && (x==14U || x==15U),"Ring audited grass pair differs");n_step(c,x==14U?QOL_KEY_RIGHT:QOL_KEY_LEFT);}
 a_require(n_action(c),"Ring real walking encounter absent");kt.encounter=b_frames;
 unsigned enemy=read16(c,ADDR_BATTLE_MONS+BATTLE_MON_SIZE),level=read8(c,ADDR_BATTLE_MONS+BATTLE_MON_SIZE+BATTLE_CORE_MON_LEVEL),flags=read32(c,ADDR_BATTLE_TYPE_FLAGS),mode=rp_mode(c),used=rp_used(c);
 fprintf(stderr,"RING_ENCOUNTER species=%u level=%u flags=%08x mode=%u used=%u frame=%u\n",enemy,level,flags,mode,used,kt.encounter);
 a_require(flags==RP_ORDINARY_ACTIVE_FLAGS && mode==r->grant && !used,"Ring cold-load ordinary policy or initial usage differs");
 a_require(!read16(c,ADDR_BATTLER_PARTY_INDEXES) && read16(c,ADDR_BATTLE_MONS)==v->species && read16(c,ADDR_BATTLE_MONS+0x2eU)==v->item && read16(c,ADDR_BATTLE_MONS+0x38U)==v->base_ability && read32(c,QOL_PLAYER_PARTY)==k_pid,"Ring natural battler identity/item/ability differs");g_shot("natural-equipped-battle");
 unsigned move=read16(c,ADDR_BATTLE_MONS+BATTLE_MON_MOVES_OFFSET),pp=read8(c,ADDR_BATTLE_MONS+BATTLE_MON_PP_OFFSET),after_pp=pp,observed_species=v->species,observed_ability=v->base_ability;
 n_cursor(c,0U);b_press(c,QOL_KEY_A,60U);a_require(read8(c,0x02022B24U)==0x14U && (read32(c,0x02023B28U)&1U),"Ring existing move UI absent");kt.move_menu=b_frames;
 for(unsigned i=0;i<6U && read8(c,BATTLE_CORE_MOVE_SELECTION_CURSOR);++i)b_press(c,read8(c,BATTLE_CORE_MOVE_SELECTION_CURSOR)&1U?QOL_KEY_LEFT:QOL_KEY_UP,12U);
 a_require(!read8(c,BATTLE_CORE_MOVE_SELECTION_CURSOR),"Ring move cursor differs");
 for(unsigned i=0;i<v->toggles;++i){if(!kt.toggle)kt.toggle=b_frames+1U;b_press(c,QOL_KEY_START,30U);}
 a_require(!rp_used(c),"Ring selection consumed usage before action");g_shot("mega-selection");b_press(c,QOL_KEY_A,2U);
 for(unsigned f=0;f<18000U;++f){
  unsigned outcome=read8(c,BATTLE_CORE_BATTLE_OUTCOME);if(outcome)n_outcome=outcome;
  unsigned sp=read16(c,ADDR_BATTLE_MONS),ab=read16(c,ADDR_BATTLE_MONS+0x38U),p=read8(c,ADDR_BATTLE_MONS+BATTLE_MON_PP_OFFSET);
  if(read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER)){unsigned value=rp_used(c);a_require(value<=1U,"Ring usage exceeded one");if(value>used)used=value;}
  if(sp==v->mega && !kt.mega){kt.mega=b_frames;observed_species=sp;observed_ability=ab;a_require(used==1U,"Ring Mega did not consume exactly one usage");g_shot("mega-active");}
  if(p<pp && !kt.spent){kt.spent=b_frames;after_pp=p;}
  if(kt.spent && n_action(c))break;
  if(!read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER) && b_field(c))break;
  b_frame(c,f%60U==0U?QOL_KEY_B:0U);
 }
 a_require(kt.spent && pp-after_pp<=2U,"Ring move did not consume native PP");
 a_require(active?(kt.mega>kt.toggle && kt.spent>kt.mega && observed_species==v->mega && observed_ability==v->ability && used==1U):(!kt.mega && !used),"Ring Mega activation/control differs");g_shot("native-turn");
 if(read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER)){a_require(n_action(c),"Ring turn did not return to action controller");n_cursor(c,3U);b_press(c,QOL_KEY_A,60U);n_return(c,false);}
 kt.field=b_frames;unsigned outcome=n_outcome;
 a_require(b_field(c) && !read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER) && (outcome==1U || outcome==4U) && read32(c,QOL_PLAYER_PARTY)==k_pid && read16(c,QOL_PLAYER_PARTY+k_growth)==v->species && read16(c,QOL_PLAYER_PARTY+k_growth+2U)==v->item && read8(c,QOL_PLAYER_PARTY+k_attack+8U)==after_pp,"Ring return/revert/held stone/PP differs");g_shot("reverted-field");
 a_require(b_save(c),"Ring postbattle normal Save failed");kt.saved_again=b_frames;b_copy(c,QOL_PLAYER_PARTY,snapshot,100U);
 a_restore(c,&original);c=b_restart(c,argv[1],argv[2]);c->reset(c);original=*c;a_guard(c);
 a_require(b_continue(c),"Ring postbattle fresh Continue failed");kt.reloaded_again=b_frames;
 b_copy(c,QOL_PLAYER_PARTY,loaded,100U);g_inventory(c,now);
 a_require(!memcmp(snapshot,loaded,100U) && !memcmp(now,wanted,sizeof(now)) && read8(c,QOL_PLAYER_PARTY_COUNT)==1U && read32(c,P03_SAVE_COUNTER)==counter+2U && read16(c,QOL_LEDGER+0x392U)==bp,"Ring final Continue durability differs");g_shot("battle-reloaded");
 a_restore(c,&original);qol_close(c);qol_log_core=NULL;sha256_file(argv[1],after);a_require(!strcmp(hash,after) && !log_problem_count,"Ring ROM changed or emulator warning");
 printf("{\"schema_version\":1,\"status\":\"PASS\",\"scope\":\"PR16_RING_GIFT_COLD_ORDINARY_MEGA\",\"case\":\"%s\",\"rom_sha256\":\"%s\",",v->name,hash);
 printf("\"species\":%u,\"item\":%u,\"mega_species\":%u,\"ability\":%u,\"toggles\":%u,\"ring_before\":0,\"ring_after\":%u,\"ring_after_continue\":%u,\"policy_mode\":%u,\"usage_observed\":%u,",v->species,v->item,observed_species,observed_ability,v->toggles,r->grant,now[580],mode,used);
 printf("\"personality\":%u,\"enemy_species\":%u,\"enemy_level\":%u,\"move\":%u,\"pp_before\":%u,\"pp_after\":%u,\"outcome\":%u,\"walking_steps\":%u,\"save_before\":%u,\"save_after\":%u,\"bp_before\":%u,\"bp_after\":%u,",k_pid,enemy,level,move,pp,after_pp,outcome,n_steps,counter,counter+2U,bp,bp);
 printf("\"manual_saves\":2,\"automatic_saves\":0,\"fresh_cores\":3,\"host_write_barriers\":7,\"ring_is_fixture\":false,\"policy_is_fixture\":false,\"initial_map_progress_party_stone_are_fixtures\":true,\"cold_reload_before_encounter\":true,\"physical_give\":true,\"held_stone_not_consumed\":true,\"party_inventory_bp_persisted\":true,\"ordinary_battle_accepted\":false,\"release_ready\":false,\"warnings_errors\":0,\"total_frames\":%u,\"witness\":{",b_frames);
#define RPW(n) printf("\""#n"\":%u,",kt.n)
 RPW(interaction);printf("\"received\":%u,",kt.purchased);RPW(bag);RPW(equipped);RPW(saved);RPW(reloaded);printf("\"walking\":%u,",kt.boundary);RPW(encounter);RPW(move_menu);RPW(toggle);RPW(mega);RPW(spent);RPW(field);RPW(saved_again);
#undef RPW
 printf("\"reloaded_again\":%u}}\n",kt.reloaded_again);return 0;
}
