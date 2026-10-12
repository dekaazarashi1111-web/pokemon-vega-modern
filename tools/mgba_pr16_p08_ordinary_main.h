/* 真正な退出後Save30 -> 物理歩行 -> 通常戦闘callee -> 通常帰還。
 * 通常Continue前から7書込禁止。fixture/関数注入/施設再入場/旧勝利再実行なし。 */
#include "mgba_pr16_p08_ordinary_observer.h"
#include "po_walk.h"
int main(int argc,char **argv){
    if(argc!=7 || strcmp(argv[5],"circus-exit30-ordinary"))return 2;
    char hash[65],savehash[65],after[65];sha256_file(argv[1],hash);sha256_file(argv[2],savehash);
    a_require(!strcmp(hash,N_SHA) && !strcmp(hash,argv[3]) && !strcmp(savehash,argv[4]),"ordinary fixed inputs");
    g_prefix=argv[6];struct mLogger logger={.log=qol_log,.filter=NULL};mLogSetDefaultLogger(&logger);
    p03f_rtc_reserve(argv[2]);struct mCore *c=qol_open(argv[1],argv[2]);qol_log_core=c;
    c->setVideoBuffer(c,b_video,240U);c->reset(c);struct mCore original=*c;a_guard(c);
    bp_require(c,b_continue(c),"ordinary genuine Save30 Continue");b_frames_run(c,0,180U);
    unsigned continued=b_frames;uint8_t owner[64],factory[106],party[600],actual[600];
    uint32_t inventory[G_ITEMS],after_inventory[G_ITEMS];
    bp_require(c,sc_current(c)==30U && sc_best(c)==30U && !sc_phase(c)
        && read16(c,BP_F(battle_points))==90U && read32(c,P03_SAVE_COUNTER)==3U
        && !read32(c,CF_FLAGS) && !read32(c,CF_TYPES) && !read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER)
        && read8(c,QOL_PLAYER_PARTY_COUNT)==1U,"ordinary Save30 state");
    b_position(c,96U,5U,20U,20U);b_copy(c,SC_OWNER,owner,sizeof(owner));
    b_copy(c,BP_FACTORY,factory,sizeof(factory));b_copy(c,QOL_PLAYER_PARTY,party,sizeof(party));g_inventory(c,inventory);
    sc_event(c,"p08-exit30",30U);
    k_path(c,96U,5U,po_town_path,sizeof(po_town_path)/sizeof(po_town_path[0]),false);
    n_step(c,QOL_KEY_UP);b_position(c,96U,17U,11U,39U);unsigned boundary=b_frames;
    sc_event(c,"p08-town-boundary",30U);po_fast_frame=c->runFrame;c->runFrame=po_frame;
    k_path(c,96U,17U,po_grass_path,sizeof(po_grass_path)/sizeof(po_grass_path[0]),true);
    for(unsigned i=0;i<128U && !read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER);++i){
        unsigned s=b_save1(c),x=read16(c,s),y=read16(c,s+2U);
        bp_require(c,y==30U && (x==14U || x==15U),"ordinary audited grass pair");
        n_step(c,x==14U?QOL_KEY_RIGHT:QOL_KEY_LEFT);
    }
    bp_require(c,n_action(c),"ordinary physical encounter absent");unsigned encounter=b_frames;
    unsigned flags=read32(c,CF_TYPES),species=read16(c,ADDR_BATTLE_MONS),ability=read16(c,ADDR_BATTLE_MONS+0x38U);
    unsigned enemy=read16(c,ADDR_BATTLE_MONS+BATTLE_MON_SIZE),level=read8(c,ADDR_BATTLE_MONS+BATTLE_MON_SIZE+BATTLE_CORE_MON_LEVEL);
    bp_require(c,flags==0U && !read32(c,CF_FLAGS) && species==4U && ability>0U
        && !read16(c,ADDR_BATTLER_PARTY_INDEXES) && read32(c,ADDR_BATTLE_MONS+0x48U)==read32(c,QOL_PLAYER_PARTY),
        "ordinary restored lead/flags differ");
    sc_event(c,"p08-normal-action",30U);n_cursor(c,3U);g_shot("ordinary-run-selection");
    b_press(c,QOL_KEY_A,60U);n_return(c,false);unsigned returned=b_frames;c->runFrame=po_fast_frame;
    bp_require(c,po_predicates>0U && po_delegates>0U,"ordinary natural predicate/delegate missing");
    bp_require(c,b_field(c) && !read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER) && !read32(c,CF_FLAGS)
        && !(read32(c,CF_TYPES)&CF_CIRCUS_BIT) && read32(c,P03_SAVE_COUNTER)==3U
        && !read8(c,BP_F(snapshot_valid)) && !read8(c,BP_F(marker)) && !read8(c,BP_F(reward_pending)),"ordinary return residue");
    b_copy(c,SC_OWNER,actual,sizeof(owner));bp_require(c,!memcmp(actual,owner,sizeof(owner)),"ordinary changed Circus owner");
    b_copy(c,BP_FACTORY,actual,sizeof(factory));bp_require(c,!memcmp(actual,factory,sizeof(factory)),"ordinary changed BP/Factory");
    b_copy(c,QOL_PLAYER_PARTY,actual,sizeof(party));g_inventory(c,after_inventory);
    bp_require(c,read8(c,QOL_PLAYER_PARTY_COUNT)==1U && !memcmp(actual,party,8U)
        && !memcmp(inventory,after_inventory,sizeof(inventory)),"ordinary party identity/inventory");
    sc_event(c,"p08-normal-return",30U);a_restore(c,&original);qol_close(c);qol_log_core=NULL;
    sha256_file(argv[1],after);a_require(!strcmp(hash,after) && !log_problem_count,"ordinary ROM/log issue");
    printf("{\"schema_version\":1,\"status\":\"PASS_P08_CIRCUS_POST_EXIT_ORDINARY\",\"case\":\"%s\",\"candidate_sha256\":\"%s\",",argv[5],hash);
    printf("\"new_emulator_processes\":1,\"fresh_cores\":1,\"manual_saves\":0,\"prefix_wins_reexecuted\":0,\"host_write_barriers\":7,\"host_state_injection\":false,\"ordinary_battles\":1,");
    printf("\"predicate_returns\":%u,\"normal_dispatches\":%u,\"trace_frames\":%u,\"trace_instructions\":%llu,\"walking_steps\":%u,",po_predicates,po_delegates,po_trace_frames,(unsigned long long)po_instructions,n_steps);
    printf("\"continued_frame\":%u,\"boundary_frame\":%u,\"encounter_frame\":%u,\"returned_frame\":%u,\"total_frames\":%u,",continued,boundary,encounter,returned,b_frames);
    printf("\"species\":%u,\"ability\":%u,\"enemy_species\":%u,\"enemy_level\":%u,\"outcome\":%u,\"owner_bytes_verified\":64,\"factory_bytes_verified\":106,",species,ability,enemy,level,n_outcome);
    printf("\"bp_before\":90,\"bp_after\":90,\"save_counter_before\":3,\"save_counter_after\":3,\"inventory_preserved\":true,\"party_identity_preserved\":true,\"warnings_errors\":0,\"release_ready\":false}\n");
    return 0;
}
