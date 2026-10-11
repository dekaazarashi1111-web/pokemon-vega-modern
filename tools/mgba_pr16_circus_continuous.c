/* 実勝敗→固有owner→通常Save/fresh core。注入は初期fixtureまで、以後は通常入力のみ。 */
#include "pr16_streak_legacy.c"
#include "pr16_streak_policy.c"
#define SC_OWNER 0x0203DB00U
static const uint32_t sc_launch[3]={0x09FF4CEBU,0x09FF4D4CU,0x09FF4DADU};
static uint8_t sc_factory[104],sc_party[600];
static unsigned sc_base,sc_admissions;
static unsigned sc_events,sc_wins,sc_losses,sc_battles,sc_turns,sc_switches,sc_id_checks,sc_counter;
static uint32_t sc_pid[3],sc_ot[3];
static unsigned sc_species[3];
static unsigned sc_current(struct mCore *c){return read16(c,SC_OWNER+32U);}
static unsigned sc_best(struct mCore *c){return read16(c,SC_OWNER+34U);}
static unsigned sc_phase(struct mCore *c){return read8(c,SC_OWNER+36U);}
static void sc_frozen(struct mCore *c){
    uint8_t bytes[104];b_copy(c,BP_FACTORY+2U,bytes,sizeof(bytes));
    bp_require(c,!memcmp(bytes,sc_factory,sizeof(bytes)),"Circus changed Factory streak/claim/unlock slots");
}
static void sc_event(struct mCore *c,const char *label,unsigned battle){
    bp_require(c,sc_events++<160U,"Circus streak event budget exceeded");
    fprintf(stderr,"CIRCUS_CONTINUOUS {\"label\":\"%s\",\"frame\":%u,\"battle\":%u,\"callback2\":%u,\"script\":%u,\"newbs\":%u,\"outcome\":%u,\"flags\":%u,\"types\":%u,\"count\":%u,\"bp\":%u,\"save_counter\":%u,\"pending\":%u,\"snapshot\":%u,\"marker\":%u,\"order\":[",
        label,b_frames,battle,read32(c,BATTLE_CORE_MAIN_CALLBACK2),read32(c,SP_SCRIPT_PTR),read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER),
        read8(c,BATTLE_CORE_BATTLE_OUTCOME)&0x7FU,read32(c,CF_FLAGS),read32(c,CF_TYPES),read8(c,QOL_PLAYER_PARTY_COUNT),
        read16(c,BP_F(battle_points)),read32(c,P03_SAVE_COUNTER),read8(c,BP_F(reward_pending)),read8(c,BP_F(snapshot_valid)),read8(c,BP_F(marker)));
    for(unsigned i=0;i<3U;++i)fprintf(stderr,"%s%u",i?",":"",read8(c,SP_ORDER_CFRU+i));
    fprintf(stderr,"],\"owner\":\"");for(unsigned i=0;i<64U;++i)fprintf(stderr,"%02x",read8(c,SC_OWNER+i));
    fprintf(stderr,"\",\"party\":\"");for(unsigned i=0;i<600U;++i)fprintf(stderr,"%02x",read8(c,QOL_PLAYER_PARTY+i));
    fprintf(stderr,"\",\"factory\":\"");for(unsigned i=0;i<104U;++i)fprintf(stderr,"%02x",read8(c,BP_FACTORY+2U+i));
    fprintf(stderr,"\"}\n");
    char shot[64];snprintf(shot,sizeof(shot),"streak-%02u-%s",sc_events,label);g_shot(shot);
}
static void sc_identity_set(struct mCore *c){
    for(unsigned i=0;i<3U;++i){uint32_t p=QOL_PLAYER_PARTY+100U*i;
        sc_pid[i]=read32(c,p);sc_ot[i]=read32(c,p+4U);sc_species[i]=read16(c,p+0x20U);}
}
static void sc_identity_same_pool(struct mCore *c){
    unsigned mask=0U;
    for(unsigned i=0;i<3U;++i){uint32_t p=QOL_PLAYER_PARTY+100U*i;unsigned found=3U;
        for(unsigned j=0;j<3U;++j)if(!(mask&(1U<<j)) && sc_pid[j]==read32(c,p)
            && sc_ot[j]==read32(c,p+4U) && sc_species[j]==read16(c,p+0x20U)){found=j;break;}
        bp_require(c,found<3U,"Circus continuation replaced a selected individual");mask|=1U<<found;}
}
static void sc_select(struct mCore *c){
    wx_team(c);
    for(unsigned k=0;k<8U && read8(c,SP_PARTY_SLOT)!=6U;++k)b_press(c,QOL_KEY_UP,60U);
    bp_require(c,read8(c,SP_PARTY_SLOT)==6U,"Circus first selected Confirm absent");
    sc_event(c,"selected",sc_base);b_press(c,QOL_KEY_A,120U);
}
static void sc_launch_battle(struct mCore *c,unsigned battle){
    for(unsigned f=0;f<18000U;++f){
        if(read32(c,BATTLE_CORE_MAIN_CALLBACK2)==P02S_CB2_PARTY
            && read8(c,QOL_PLAYER_PARTY_COUNT)==3U && read32(c,SP_SCRIPT_PTR)==sc_launch[battle])break;
        bp_require(c,!read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER),"Circus battle before final confirmation");
        /* B closes narration and declines exchange; never press it after next chooser appears. */
        b_frame(c,f%90U==0U?QOL_KEY_B:0U);
    }
    bp_require(c,read32(c,SP_SCRIPT_PTR)==sc_launch[battle]
        && read32(c,BATTLE_CORE_MAIN_CALLBACK2)==P02S_CB2_PARTY,"Circus continuation chooser timeout");
    b_frames_run(c,0,180U);
    bp_require(c,sc_phase(c)==2U && sc_current(c)==sc_base+battle && sc_best(c)==sc_base+battle,"Circus prepare did not arm dedicated streak");
    if(!battle)sc_identity_set(c);else sc_identity_same_pool(c);
    for(unsigned k=0;k<8U && read8(c,SP_PARTY_SLOT)!=6U;++k)b_press(c,QOL_KEY_UP,60U);
    bp_require(c,read8(c,SP_PARTY_SLOT)==6U,"Circus final Confirm absent");
    uint8_t selected[300],actual[300];b_copy(c,QOL_PLAYER_PARTY,selected,sizeof(selected));
    sc_event(c,"confirmation",sc_base+battle);sc_frozen(c);
    for(unsigned f=0;f<18000U;++f){
        b_frame(c,f%90U==0U?QOL_KEY_A:0U);
        if(n_action(c)){c->setKeys(c,0);break;}
    }
    bp_require(c,n_action(c) && read32(c,SP_SCRIPT_PTR)==sc_launch[battle]+43U
        && (read32(c,CF_TYPES)&CF_CIRCUS_BIT) && read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER),"Circus real battle launch absent");
    b_copy(c,QOL_PLAYER_PARTY,actual,sizeof(actual));
    bp_require(c,!memcmp(selected,actual,sizeof(actual)),"Circus selected300 changed between confirmation and action");
    bp_require(c,sc_phase(c)==2U && sc_current(c)==sc_base+battle && sc_best(c)==sc_base+battle,"Circus draw changed dedicated streak");
    sc_frozen(c);sc_event(c,"action",sc_base+battle);++sc_battles;
}
static void sc_switch(struct mCore *c,struct BPReturn *w){
    bp_require(c,!read16(c,ADDR_BATTLE_MONS+BATTLE_CORE_MON_HP),"Circus unexpected voluntary party menu");
    b_frames_run(c,0,60U);unsigned target=wx_reserve(c,read16(c,ADDR_BATTLER_PARTY_INDEXES));
    bp_require(c,target<3U,"Circus forced switch has no living rental");wx_cursor(c,target);
    uint32_t p=QOL_PLAYER_PARTY+100U*target,pid=read32(c,p),ot=read32(c,p+4U);unsigned species=read16(c,p+0x20U);
    b_press(c,QOL_KEY_A,80U);if(read32(c,BATTLE_CORE_MAIN_CALLBACK2)==P02S_CB2_PARTY)b_press(c,QOL_KEY_A,80U);
    for(unsigned f=0;f<18000U;++f){
        if(n_action(c) && read32(c,ADDR_BATTLE_MONS+0x48U)==pid && read32(c,ADDR_BATTLE_MONS+0x54U)==ot
            && read16(c,ADDR_BATTLE_MONS)==species){++w->switches;++sc_id_checks;return;}
        bp_require(c,!read8(c,BATTLE_CORE_BATTLE_OUTCOME),"Circus forced switch ended unexpectedly");
        b_frame(c,f%90U==0U?QOL_KEY_B:0U);
    }
    bp_require(c,false,"Circus forced switch identity timeout");
}
static unsigned sc_finish_battle(struct mCore *c,unsigned battle){
    struct BPReturn w={.start=b_frames};unsigned outcome=0U;
    while(b_frames-w.start<90000U){
        unsigned value=read8(c,BATTLE_CORE_BATTLE_OUTCOME)&0x7FU;
        if(value && !outcome){outcome=value;bp_require(c,value==1U || value==2U,"Circus outcome not native win/loss");sc_event(c,"outcome",sc_base+battle);}
        sc_frozen(c);bp_require(c,read32(c,P03_SAVE_COUNTER)==sc_counter,"Circus battle performed automatic full Save");
        if(outcome && !read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER) && sc_phase(c)!=2U){
            if((outcome==1U && sc_current(c)==sc_base+battle+1U && sc_best(c)==sc_base+battle+1U)
                || (outcome==2U && sc_phase(c)==0U && !sc_current(c) && sc_best(c)==sc_base+battle)){
                b_frames_run(c,0,30U);sc_event(c,"settled",sc_base+battle);sc_turns+=w.turns;sc_switches+=w.switches;
                if(outcome==1U)++sc_wins;else ++sc_losses;return outcome;
            }
        }
        if(!outcome && read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER)){
            if(n_action(c)){bp_require(c,w.turns<64U,"Circus battle turn bound");br_move(c,&w);continue;}
            if(read32(c,BATTLE_CORE_MAIN_CALLBACK2)==P02S_CB2_PARTY){bp_require(c,w.switches<2U,"Circus switch bound");sc_switch(c,&w);continue;}
        }
        b_frame(c,(b_frames-w.start)%90U==0U?QOL_KEY_B:0U);
    }
    sc_event(c,"timeout",sc_base+battle);bp_require(c,false,"Circus native settle timeout");return 0U;
}
static void sc_returned(struct mCore *c){
    for(unsigned f=0;f<12000U && (!b_field(c) || read8(c,BP_F(snapshot_valid)) || sc_phase(c));++f)
        b_frame(c,f%90U==0U?QOL_KEY_B:0U);
    b_frames_run(c,0,180U);uint8_t actual[600];b_copy(c,QOL_PLAYER_PARTY,actual,sizeof(actual));
    bp_require(c,b_field(c) && !read8(c,BP_F(snapshot_valid)) && !read8(c,BP_F(marker)) && !read8(c,BP_F(reward_pending))
        && !sc_phase(c) && !read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER),"Circus session did not end");
    bp_require(c,read8(c,QOL_PLAYER_PARTY_COUNT)==1U && !memcmp(actual,sc_party,sizeof(actual)),"Circus did not restore original600");
    bp_require(c,sc_best(c)==sc_wins && sc_current(c)==(sc_losses?0U:sc_wins)
        && read16(c,BP_F(battle_points))==(9U*(sc_wins/3U)),"Circus final streak/BP differs");sc_frozen(c);
}
int main(int argc,char **argv){
    if(argc==3 && !strcmp(argv[1],"--guard-check"))a_guard_check(argv[2]);
    if(argc!=7 || strcmp(argv[5],"circus-continuous-30-save"))return 2;
    g_prefix=argv[6];char hash[65],seed[65],after[65];sha256_file(argv[1],hash);sha256_file(argv[2],seed);
    a_require(!strcmp(hash,N_SHA) && !strcmp(hash,argv[3]) && !strcmp(seed,B_SEED_SHA) && !strcmp(seed,argv[4]),"Circus streak input identity");
    struct mLogger logger={.log=qol_log,.filter=NULL};mLogSetDefaultLogger(&logger);p03f_rtc_reserve(argv[2]);
    struct mCore *c=qol_open(argv[1],argv[2]);qol_log_core=c;c->setVideoBuffer(c,b_video,240U);c->reset(c);
    a_require(a_continue(c),"Circus streak initial Continue");a_flash_prepare(c);
    (void)call_preserving(c,0x09220861U,96U,5U,20U,20U);run_key_frames(c,0,1800U);
    for(unsigned i=0;i<12U && !b_field(c);++i)b_press(c,QOL_KEY_B,180U);
    b_position(c,96U,5U,20U,20U);clear_parties(c);create_mon(c,QOL_PLAYER_PARTY,4U,50U);write8(c,QOL_PLAYER_PARTY_COUNT,1U);
    (void)call_preserving(c,0x0809984DU,0,0,0,0);
    for(unsigned i=0;i<sizeof(VegaFactoryState);++i)write8(c,BP_FACTORY+i,0U);
    (void)call_preserving(c,QOL_SAVE_FINALIZE,QOL_LEDGER,0,0,0);
    b_copy(c,QOL_PLAYER_PARTY,sc_party,sizeof(sc_party));b_copy(c,BP_FACTORY+2U,sc_factory,sizeof(sc_factory));
    uint32_t inventory[G_ITEMS],inventory_after[G_ITEMS];g_inventory(c,inventory);sc_counter=read32(c,P03_SAVE_COUNTER);
    bp_require(c,!read32(c,CF_FLAGS) && !sc_current(c) && !sc_best(c) && !sc_phase(c),"Circus owner not initially zero; do not inject");
    sc_event(c,"fixture",0U);struct mCore original=*c;a_guard(c);
    /* 新しい連続区間の先頭3勝は不可避のprefix。独立した受入済みcaseは呼ばない。 */
    for(unsigned admission=0;admission<10U;++admission){
        sc_base=sc_wins;++sc_admissions;cp_policy_reset();
        cf_open(c);cf_rentals(c);sc_select(c);
        for(unsigned battle=0;battle<3U;++battle){sc_launch_battle(c,battle);if(sc_finish_battle(c,battle)==2U)break;}
        sc_returned(c);sc_event(c,"returned",sc_battles);g_inventory(c,inventory_after);
        bp_require(c,!memcmp(inventory,inventory_after,sizeof(inventory)),"Circus reentry changed inventory");
        if(sc_losses)break;
    }
    g_inventory(c,inventory_after);
    bp_require(c,!memcmp(inventory,inventory_after,sizeof(inventory)),"Circus altered inventory");
    uint8_t owner[64],loaded[64];b_copy(c,SC_OWNER,owner,sizeof(owner));
    bp_require(c,b_save(c),"Circus streak normal Save failed");sc_event(c,"saved",sc_battles);
    a_restore(c,&original);c=b_restart(c,argv[1],argv[2]);c->reset(c);original=*c;a_guard(c);
    bp_require(c,b_continue(c),"Circus streak fresh Continue failed");b_frames_run(c,0,180U);
    sc_returned(c);b_copy(c,SC_OWNER,loaded,sizeof(loaded));g_inventory(c,inventory_after);
    bp_require(c,!memcmp(owner,loaded,sizeof(owner)) && !memcmp(inventory,inventory_after,sizeof(inventory))
        && read32(c,P03_SAVE_COUNTER)==sc_counter+1U,"Circus streak Save/fresh Continue lost64 or inventory/counter");
    sc_event(c,"reloaded",sc_battles);unsigned final_counter=read32(c,P03_SAVE_COUNTER);
    a_restore(c,&original);qol_close(c);qol_log_core=NULL;sha256_file(argv[1],after);
    a_require(!strcmp(hash,after) && !log_problem_count,"Circus native ROM changed or mGBA warned");
    printf("{\"schema_version\":1,\"status\":\"PASS_CIRCUS_CONTINUOUS_LIFECYCLE\",\"case\":\"%s\",\"candidate_sha256\":\"%s\",\"wins\":%u,\"losses\":%u,\"battles\":%u,\"turns\":%u,\"switches\":%u,\"forced_identity_checks\":%u,",argv[5],hash,sc_wins,sc_losses,sc_battles,sc_turns,sc_switches,sc_id_checks);
    printf("\"admissions\":%u,\"completed_batches\":%u,\"bp_earned\":%u,\"target_wins\":30,",sc_admissions,sc_wins/3U,9U*(sc_wins/3U));
    printf("\"save_counter_before\":%u,\"save_counter_after\":%u,\"manual_saves\":1,\"fresh_cores\":2,\"owner_bytes_verified\":64,\"party_bytes_verified\":600,\"host_write_barriers\":7,\"total_frames\":%u,\"events\":%u,\"input_only_after_guard\":true,\"physical_admission_accepted\":false,\"suppression_accepted\":false,\"release_ready\":false,\"warnings_errors\":0}\n",sc_counter,final_counter,b_frames,sc_events);
    return 0;
}
