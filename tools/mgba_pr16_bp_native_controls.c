/* Native Factory reception and rental cancellation controls.
 * Initial progress/map/party/empty Factory ledger are fixtures. Thereafter all
 * seven host-write APIs are blocked: only GBA keys, frames and reads are used.
 * These two negative controls do not claim earned BP or close the P05 gap. */
#include "pr16_bp_native_helpers.c"
#include "../overlays/factory_high_modes_v2/factory_high_modes_v2.h"
#include "../overlays/save_migration/save_migration.h"
#include <stddef.h>

#define BP_SCOPE "PR16_P05_NATIVE_BP_CANCELLATION_CONTROLS"
#define BP_FACTORY (QOL_LEDGER + 0x392U)
#define BP_HIGH FACTORY_HIGH_MODES_V2_STATE_ADDRESS
#define BP_H(field) (BP_HIGH + offsetof(FactoryHighModesV2State, field))
#define BP_F(field) (BP_FACTORY + offsetof(VegaFactoryState, field))
_Static_assert(offsetof(VegaModernSaveData, factory) == 0x392U, "Factory save ABI differs");
_Static_assert(sizeof(VegaFactoryState) == 714U, "Factory state size differs");
struct BPTrace { unsigned interaction,tier,mode,confirm,rentals,cancel,field,saved,reloaded; };
static struct BPTrace bt;

static void bp_state(struct mCore *c, const char *label) {
    n_state(c,label);
    fprintf(stderr,"BP_CTRL label=%s frame=%u menu=%u stage=%u page=%u mode=%u status=%u window=%u cursor=%u count=%u snapshot=%u marker=%u bp=%u save=%u script=%08x\n",label,b_frames,
       read8(c,BP_H(menu_active)),read8(c,BP_H(menu_stage)),read8(c,BP_H(menu_page)),
       read8(c,BP_H(mode)),read16(c,BP_H(last_status)),read8(c,BP_H(window_id)),
       read8(c,G_CURSOR),read8(c,QOL_PLAYER_PARTY_COUNT),read8(c,BP_F(snapshot_valid)),
       read8(c,BP_F(marker)),read16(c,BP_F(battle_points)),read32(c,P03_SAVE_COUNTER),read32(c,B_CONTEXT+8U));
}
static void bp_require(struct mCore *c,bool ok,const char *message) {
    if(!ok){bp_state(c,message);g_shot("failure");a_die(message);}
}
static bool bp_menu(struct mCore *c,unsigned stage) {
    return read32(c,BP_HIGH)==0x324D4846U && read8(c,BP_H(menu_active))==1U
        && read8(c,BP_H(menu_stage))==stage && read8(c,BP_H(window_id))<32U
        && read8(c,P02S_FIELD_LOCK)!=0U;
}
static void bp_wait_menu(struct mCore *c,unsigned stage) {
    for(unsigned f=0;f<2400U;++f){if(bp_menu(c,stage)){b_frames_run(c,0,60U);bp_state(c,"menu");return;}b_frame(c,0);}
    bp_require(c,false,"native Factory menu did not open expected stage");
}
static void bp_open(struct mCore *c) {
    b_position(c,96U,5U,20U,20U);
    b_frames_run(c,0,60U);b_press(c,QOL_KEY_UP,60U);b_position(c,96U,5U,20U,20U);
    unsigned avatar=read8(c,P02S_PLAYER_AVATAR+5U);
    bp_require(c,avatar<16U && (read8(c,P02S_OBJECT_EVENTS+avatar*0x24U+0x18U)&15U)==2U,"Factory physical facing differs");
    bt.interaction=b_frames+1U;b_press(c,QOL_KEY_A,120U);g_shot("codex-gateway");
    /* Actual native No at the Codex yes/no gateway delegates to Factory.
     * Stop B pulses immediately when the tier menu becomes live. */
    for(unsigned f=0;f<2400U && !bp_menu(c,0U);++f)
        b_frame(c,f%90U==0U?QOL_KEY_B:0U);
    bp_wait_menu(c,0U);bt.tier=b_frames;
    bp_require(c,!read8(c,G_CURSOR) && !read8(c,BP_H(menu_codes)),"native first tier is not Trial");g_shot("reception-tier");
}
static void bp_trial(struct mCore *c) {
    b_press(c,QOL_KEY_A,60U);bp_wait_menu(c,1U);bt.mode=b_frames;
    bp_require(c,!read8(c,BP_H(menu_page)) && !read8(c,G_CURSOR) && !read8(c,BP_H(menu_codes)),"native first Trial mode differs");
    g_shot("reception-mode");b_press(c,QOL_KEY_A,60U);bp_wait_menu(c,3U);bt.confirm=b_frames;
    bp_require(c,!read8(c,BP_H(mode)) && read8(c,BP_H(menu_codes))==1U,"native Trial confirmation differs");
    g_shot("reception-confirm");b_press(c,QOL_KEY_A,60U);
    uint32_t old=0;
    for(unsigned f=0;f<12000U;++f){
        unsigned cb=read32(c,BATTLE_CORE_MAIN_CALLBACK2);
        if(cb!=old){bp_state(c,"enter-rentals");old=cb;}
        if(cb==P02S_CB2_PARTY && read8(c,QOL_PLAYER_PARTY_COUNT)==6U){
            b_frames_run(c,0,180U);bt.rentals=b_frames;
            bp_require(c,read8(c,BP_F(snapshot_valid))==1U && read8(c,BP_F(marker))==1U,"native rental snapshot not committed");
            bp_require(c,!read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER),"cancel control unexpectedly started a battle");
            g_shot("rental-party");return;
        }
        b_frame(c,f%60U==0U?QOL_KEY_A:0U);
    }
    bp_require(c,false,"native Trial did not produce the rental party UI");
}
static void bp_return(struct mCore *c) {
    unsigned stable=0;uint32_t old=0;
    for(unsigned f=0;f<18000U;++f){
        unsigned cb=read32(c,BATTLE_CORE_MAIN_CALLBACK2);
        if(cb!=old){bp_state(c,"cancel-return");old=cb;}
        bp_require(c,!read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER),"cancellation entered battle");
        if(b_field(c)){if(++stable==60U){c->setKeys(c,0);bt.field=b_frames;return;}}else stable=0;
        b_frame(c,f%90U==0U?QOL_KEY_B:0U);
    }
    bp_require(c,false,"native Factory cancellation did not return to idle field");
}
int main(int argc,char **argv) {
    if(argc==3 && !strcmp(argv[1],"--guard-check"))a_guard_check(argv[2]);
    if(argc!=7)return 2;
    bool rental=!strcmp(argv[5],"rental-cancel-save-continue");
    if(!rental && strcmp(argv[5],"reception-cancel-unchanged"))return 2;
    g_prefix=argv[6];char hash[65],seed[65],after_hash[65];sha256_file(argv[1],hash);sha256_file(argv[2],seed);
    a_require(!strcmp(hash,N_SHA) && !strcmp(hash,argv[3]) && !strcmp(seed,B_SEED_SHA) && !strcmp(seed,argv[4]),"BP control fixed input identity differs");
    struct mLogger logger={.log=qol_log,.filter=NULL};mLogSetDefaultLogger(&logger);p03f_rtc_reserve(argv[2]);
    struct mCore *c=qol_open(argv[1],argv[2]);qol_log_core=c;c->setVideoBuffer(c,b_video,240U);c->reset(c);
    a_require(a_continue(c),"BP initial Continue failed");a_flash_prepare(c);
    (void)call_preserving(c,0x09220861U,96U,5U,20U,20U);run_key_frames(c,0,1800U);
    for(unsigned i=0;i<12U && !b_field(c);++i)b_press(c,QOL_KEY_B,180U);
    b_position(c,96U,5U,20U,20U);
    clear_parties(c);create_mon(c,QOL_PLAYER_PARTY,4U,50U);write8(c,QOL_PLAYER_PARTY_COUNT,1U);
    (void)call_preserving(c,0x0809984DU,0,0,0,0);
    for(unsigned i=0;i<sizeof(VegaFactoryState);++i)write8(c,BP_FACTORY+i,0U);
    (void)call_preserving(c,QOL_SAVE_FINALIZE,QOL_LEDGER,0,0,0);
    uint8_t party[600],restored[600],factory_prefix[106],prefix_after[106],rentals[600];
    uint32_t inventory[G_ITEMS],inventory_after[G_ITEMS];b_copy(c,QOL_PLAYER_PARTY,party,sizeof(party));
    b_copy(c,BP_FACTORY,factory_prefix,sizeof(factory_prefix));g_inventory(c,inventory);
    unsigned counter=read32(c,P03_SAVE_COUNTER);bp_state(c,"fixture");g_shot("fixture");
    struct mCore original=*c;a_guard(c);bp_open(c);
    if(rental){
        bp_trial(c);b_copy(c,QOL_PLAYER_PARTY,rentals,sizeof(rentals));
        bp_require(c,memcmp(party,rentals,sizeof(party))!=0,"native rentals did not replace party");
        b_copy(c,BP_F(party_snapshot),restored,sizeof(restored));
        bp_require(c,!memcmp(party,restored,sizeof(party)),"native snapshot did not retain exact original party");
    }
    bt.cancel=b_frames+1U;b_press(c,QOL_KEY_B,120U);bp_return(c);bp_state(c,"returned");g_shot("returned");
    b_copy(c,QOL_PLAYER_PARTY,restored,sizeof(restored));b_copy(c,BP_FACTORY,prefix_after,sizeof(prefix_after));g_inventory(c,inventory_after);
    bp_require(c,!memcmp(party,restored,sizeof(party)) && read8(c,QOL_PLAYER_PARTY_COUNT)==1U,"cancel did not restore all 600 party bytes/count");
    bp_require(c,!memcmp(factory_prefix,prefix_after,sizeof(factory_prefix)) && !read8(c,BP_F(snapshot_valid)) && !read8(c,BP_F(marker)) && !read8(c,BP_F(reward_pending)),"cancel changed BP/streak/claim/unlock or retained a session");
    bp_require(c,!memcmp(inventory,inventory_after,sizeof(inventory)),"cancel changed inventory");
    unsigned before_manual=read32(c,P03_SAVE_COUNTER);
    bp_require(c,before_manual==counter,"cancel unexpectedly performed a full save");
    if(rental){
        bp_require(c,b_save(c),"BP cancel normal Save failed");bt.saved=b_frames;
        a_restore(c,&original);c=b_restart(c,argv[1],argv[2]);c->reset(c);original=*c;a_guard(c);
        bp_require(c,b_continue(c),"BP cancel fresh Continue failed");bt.reloaded=b_frames;
        b_copy(c,QOL_PLAYER_PARTY,restored,sizeof(restored));b_copy(c,BP_FACTORY,prefix_after,sizeof(prefix_after));g_inventory(c,inventory_after);
        bp_require(c,!memcmp(party,restored,sizeof(party)) && read8(c,QOL_PLAYER_PARTY_COUNT)==1U && !memcmp(factory_prefix,prefix_after,sizeof(factory_prefix)) && !memcmp(inventory,inventory_after,sizeof(inventory)),"fresh Continue changed restored party/BP/claims/inventory");
        bp_require(c,!read8(c,BP_F(snapshot_valid)) && !read8(c,BP_F(marker)) && read32(c,P03_SAVE_COUNTER)==counter+1U,"fresh Continue retained Factory session or save counter differs");
        g_shot("fresh-continue");
    }
    unsigned final_counter=read32(c,P03_SAVE_COUNTER);
    a_restore(c,&original);qol_close(c);qol_log_core=NULL;sha256_file(argv[1],after_hash);
    a_require(!strcmp(hash,after_hash) && !log_problem_count,"BP control ROM changed or mGBA warned");
    printf("{\"schema_version\":1,\"status\":\"PASS_SCOPED_CONTROL\",\"scope\":\"%s\",\"case\":\"%s\",\"candidate_sha256\":\"%s\",",BP_SCOPE,argv[5],hash);
    printf("\"native_reception\":true,\"native_rental_selection_entry\":%s,\"native_cancel\":true,\"party_bytes_verified\":600,\"party_and_inventory_preserved\":true,\"bp_before\":0,\"bp_after\":0,\"bp_earned\":0,",rental?"true":"false");
    printf("\"save_counter_before\":%u,\"save_counter_before_manual\":%u,\"save_counter_after\":%u,\"manual_saves\":%u,\"fresh_cores\":%u,\"automatic_full_saves\":0,",counter,before_manual,final_counter,rental?1U:0U,rental?2U:1U);
    printf("\"input_only_after_guard\":true,\"host_write_barriers\":7,\"initial_map_progress_party_factory_ledger_are_fixtures\":true,\"native_ledger_sector_writes_are_not_full_saves\":true,\"physical_bp_earning_accepted\":false,\"p05_native_bp_gap_closed\":false,\"release_ready\":false,\"warnings_errors\":0,\"total_frames\":%u,\"witness\":{",b_frames);
#define BTW(n) printf("\""#n"\":%u,",bt.n)
    BTW(interaction);BTW(tier);BTW(mode);BTW(confirm);BTW(rentals);BTW(cancel);BTW(field);BTW(saved);
#undef BTW
    printf("\"reloaded\":%u}}\n",bt.reloaded);return 0;
}
