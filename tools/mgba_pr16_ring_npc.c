/* Ring gift -> duplicate/denial -> ordinary Save -> fresh Continue -> revisit.
 * Only initial progression, party, location and (full-case) capacity are
 * fixtures. Ring is removed before the write barrier, never injected.
 * All three conversations, the grant, and Save/Continue are game-owned.
 */
#include "pr16_ring_shop_helpers.c"
#include "pr16_ring_npc_generated.h"
#define RN_RESULT 0x02037004U
#define RN_SCOPE "PR16_RING_NPC_GIFT_SAVE_CONTINUE"

static void rn_trace(struct mCore *c,const char *label){
 b_state(c,label);
 fprintf(stderr,"RING_NPC phase=%s frame=%u result=%u save=%u bp=%u\n",label,b_frames,
  read16(c,RN_RESULT),read32(c,P03_SAVE_COUNTER),read16(c,QOL_LEDGER+0x392U));
}
static unsigned rn_talk(struct mCore *c,unsigned expected,const char *shot){
 a_require(b_field(c),"Ring talk did not start in ordinary field");
 b_position(c,RN_GROUP,RN_MAP,RN_FRONT_X,RN_FRONT_Y);
 unsigned avatar=read8(c,P02S_PLAYER_AVATAR+5U);
 a_require(avatar<16U,"Ring player avatar absent");
 if((read8(c,P02S_OBJECT_EVENTS+avatar*0x24U+0x18U)&15U)!=2U)b_frame(c,QOL_KEY_UP);
 b_frames_run(c,0,30U);b_position(c,RN_GROUP,RN_MAP,RN_FRONT_X,RN_FRONT_Y);
 unsigned interaction=b_frames+1U;b_press(c,QOL_KEY_A,30U);
 for(unsigned i=0;i<1800U;++i){
  if(read8(c,P02S_FIELD_LOCK) && read16(c,RN_RESULT)==expected){
   b_frames_run(c,0,45U);rn_trace(c,shot);g_shot(shot);
   g_finish(c);b_position(c,RN_GROUP,RN_MAP,RN_FRONT_X,RN_FRONT_Y);
   a_require(read16(c,RN_RESULT)==expected,"Ring result changed while closing text");
   return interaction;
  }
  b_frame(c,0U);
 }
 rn_trace(c,"talk-timeout");g_shot("talk-timeout");a_die("real Ring NPC did not produce expected dialogue");return 0U;
}
static void rn_full_fixture(struct mCore*c){
 for(unsigned i=0;i<sizeof(rn_key_items)/sizeof(rn_key_items[0]);++i){
  if(!call_preserving(c,0x08099A09U,580U,1U,0,0))return;
  unsigned item=rn_key_items[i];
  if(!call_preserving(c,0x08099949U,item,1U,0,0))
   (void)call_preserving(c,0x08099A8DU,item,1U,0,0);
 }
 a_require(!call_preserving(c,0x08099A09U,580U,1U,0,0),"could not fill key-item pocket fixture");
}
int main(int argc,char **argv){
 if(argc==3 && !strcmp(argv[1],"--guard-check"))a_guard_check(argv[2]);
 if(argc!=7)return 2;
 unsigned expected=0U;
 if(!strcmp(argv[5],"gift-save-revisit"))expected=1U;
 else if(!strcmp(argv[5],"locked-save-revisit"))expected=3U;
 else if(!strcmp(argv[5],"full-save-revisit"))expected=4U;
 else return 2;
 g_prefix=argv[6];char hash[65],seed[65],after[65];sha256_file(argv[1],hash);sha256_file(argv[2],seed);
 a_require(!strcmp(hash,RN_SHA) && !strcmp(hash,argv[3]) && !strcmp(seed,B_SEED_SHA) && !strcmp(seed,argv[4]),"Ring input identity differs");
 struct mLogger logger={.log=qol_log,.filter=NULL};mLogSetDefaultLogger(&logger);p03f_rtc_reserve(argv[2]);
 struct mCore*c=qol_open(argv[1],argv[2]);qol_log_core=c;c->setVideoBuffer(c,b_video,240U);c->reset(c);
 a_require(a_continue(c),"Ring initial Continue failed");a_flash_prepare(c);
 (void)call_preserving(c,0x09220861U,RN_GROUP,RN_MAP,RN_FRONT_X,RN_FRONT_Y);run_key_frames(c,0,1800U);
 for(unsigned i=0;i<12U && !b_field(c);++i)b_press(c,QOL_KEY_B,180U);
 b_position(c,RN_GROUP,RN_MAP,RN_FRONT_X,RN_FRONT_Y);a_require(b_field(c),"Ring fixture field did not settle");
 (void)call_preserving(c,0x0809984DU,0,0,0,0);g_remove_fixture(c,580U);
 (void)call_preserving(c,expected==3U?QOL_FLAG_CLEAR:QOL_FLAG_SET,0x13FFU,0,0,0);
 if(expected==4U)rn_full_fixture(c);
 else a_require(call_preserving(c,0x08099A09U,580U,1U,0,0)!=0U,"normal Ring fixture pocket unexpectedly full");
 uint32_t before[G_ITEMS],wanted[G_ITEMS],now[G_ITEMS];g_inventory(c,before);a_require(!before[580],"Ring fixture must be unowned");memcpy(wanted,before,sizeof(wanted));
 if(expected==1U)wanted[580]=1U;
 uint8_t party[600],loaded[600];b_copy(c,QOL_PLAYER_PARTY,party,600U);
 unsigned party_count=read8(c,QOL_PLAYER_PARTY_COUNT),bp=read16(c,QOL_LEDGER+0x392U),counter=read32(c,P03_SAVE_COUNTER);
 rn_trace(c,"fixture-complete");g_shot("fixture");
 /* No host mutation or function injection after this line. */
 struct mCore original=*c;a_guard(c);
 unsigned interaction=rn_talk(c,expected,"first-dialogue"),returned=b_frames;
 g_inventory(c,now);a_require(!memcmp(now,wanted,sizeof(now)),"Ring first gift changed unexpected Bag bytes");
 a_require(read32(c,P03_SAVE_COUNTER)==counter,"Ring must not force an automatic save");
 unsigned repeat=rn_talk(c,expected==1U?2U:expected,"repeat-dialogue"),repeat_returned=b_frames;
 g_inventory(c,now);a_require(!memcmp(now,wanted,sizeof(now)),"Ring repeated gift changed Bag");
 b_copy(c,QOL_PLAYER_PARTY,loaded,600U);
 a_require(!memcmp(party,loaded,600U) && read8(c,QOL_PLAYER_PARTY_COUNT)==party_count && read16(c,QOL_LEDGER+0x392U)==bp,"Ring dialogue changed party or BP");
 a_require(b_save(c),"Ring normal Start Save failed");unsigned saved=b_frames;
 a_require(read32(c,P03_SAVE_COUNTER)==counter+1U,"Ring manual Save counter differs");
 a_restore(c,&original);c=b_restart(c,argv[1],argv[2]);c->reset(c);original=*c;a_guard(c);
 a_require(b_continue(c),"Ring fresh Continue failed");unsigned reloaded=b_frames;
 b_position(c,RN_GROUP,RN_MAP,RN_FRONT_X,RN_FRONT_Y);g_inventory(c,now);b_copy(c,QOL_PLAYER_PARTY,loaded,600U);
 a_require(!memcmp(now,wanted,sizeof(now)) && !memcmp(party,loaded,600U) && read8(c,QOL_PLAYER_PARTY_COUNT)==party_count && read16(c,QOL_LEDGER+0x392U)==bp && read32(c,P03_SAVE_COUNTER)==counter+1U,"Ring fresh Continue did not preserve inventory/party/BP/save");
 g_shot("reloaded");unsigned revisit=rn_talk(c,expected==1U?2U:expected,"reloaded-dialogue");
 g_inventory(c,now);a_require(!memcmp(now,wanted,sizeof(now)) && read32(c,P03_SAVE_COUNTER)==counter+1U,"Ring reloaded revisit mutated inventory or save");
 unsigned frames=b_frames;a_restore(c,&original);qol_close(c);qol_log_core=NULL;sha256_file(argv[1],after);
 a_require(!strcmp(hash,after) && !log_problem_count,"Ring ROM changed or emulator reported warning/error");
 printf("{\"schema_version\":1,\"status\":\"PASS\",\"scope\":\"%s\",\"case\":\"%s\",\"rom_sha256\":\"%s\",",RN_SCOPE,argv[5],hash);
 printf("\"initial_result\":%u,\"revisit_result\":%u,\"ring_before\":0,\"ring_after\":%u,\"ring_after_continue\":%u,\"manual_saves\":1,\"automatic_saves\":0,\"fresh_cores\":2,\"host_write_barriers\":7,",expected,expected==1U?2U:expected,wanted[580],now[580]);
 printf("\"physical_host\":[%u,%u,%u,%u,%u],\"save_before\":%u,\"save_after\":%u,\"bp_before\":%u,\"bp_after\":%u,",RN_GROUP,RN_MAP,RN_LOCAL_ID,RN_FRONT_X,RN_FRONT_Y-1U,counter,counter+1U,bp,bp);
 printf("\"ring_is_fixture\":false,\"initial_progression_map_capacity_are_fixtures\":true,\"party_and_other_inventory_preserved\":true,\"ordinary_battle_accepted\":false,\"ring_full_acceptance\":false,\"release_ready\":false,\"warnings_errors\":0,\"total_frames\":%u,",frames);
 printf("\"witness\":{\"interaction\":%u,\"returned\":%u,\"repeat\":%u,\"repeat_returned\":%u,\"saved\":%u,\"reloaded\":%u,\"revisit\":%u,\"finished\":%u}}\n",interaction,returned,repeat,repeat_returned,saved,reloaded,revisit,frames);return 0;
}
