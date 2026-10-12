/* 新規の第2戦中断ケース。3勝単体や受入済み敗北を再実行しない。 */
#include "pr16_streak_base.c"

/* RECOVERY_WATCH_BEGIN: runFrameへの一度の委譲後に読取。入力とframe数は不変。 */
static void (*rt_original_frame)(struct mCore *);
static unsigned rt_seen,rt_rows,rt_core;
static uint8_t rt_previous[80];
static void rt_emit(struct mCore *c)
{
    uint8_t now[80];b_copy(c,SC_OWNER,now,64U);
    uint32_t counter=read32(c,P03_SAVE_COUNTER),cb=read32(c,BATTLE_CORE_MAIN_CALLBACK2);
    uint32_t save2=read32(c,0x0300504CU),trainer=0U;
    if(save2>=0x02000000U && save2<=0x0203F000U)
        for(unsigned i=0;i<4U;++i)trainer|=(uint32_t)read8(c,save2+10U+i)<<(8U*i);
    memcpy(now+64U,&counter,4U);memcpy(now+68U,&cb,4U);
    now[72]=read8(c,BP_F(snapshot_valid));now[73]=read8(c,BP_F(marker));
    now[74]=read8(c,BP_F(reward_pending));now[75]=read8(c,QOL_PLAYER_PARTY_COUNT);
    memcpy(now+76U,&trainer,4U);
    if(rt_seen && !memcmp(now,rt_previous,sizeof(now)))return;
    bp_require(c,rt_rows++<512U,"Circus recovery observation bound");rt_seen=1U;memcpy(rt_previous,now,sizeof(now));
    fprintf(stderr,"CIRCUS_RECOVERY {\"sequence\":%u,\"core\":%u,\"frame_boundary\":%u,\"callback2\":%u,\"save_counter\":%u,\"save2\":%u,\"trainer_id\":%u,\"snapshot\":%u,\"marker\":%u,\"pending\":%u,\"count\":%u,\"owner\":\"",
        rt_rows,rt_core,b_frames,cb,counter,save2,trainer,now[72],now[73],now[74],now[75]);
    for(unsigned i=0;i<64U;++i)fprintf(stderr,"%02x",now[i]);
    fprintf(stderr,"\",\"factory\":\"");
    for(unsigned i=0;i<104U;++i)fprintf(stderr,"%02x",read8(c,BP_FACTORY+2U+i));
    fprintf(stderr,"\",\"party\":\"");
    for(unsigned i=0;i<600U;++i)fprintf(stderr,"%02x",read8(c,QOL_PLAYER_PARTY+i));
    fprintf(stderr,"\"}\n");
}
static void rt_frame(struct mCore *c)
{
    rt_original_frame(c);
    rt_emit(c);
}
static void rt_watch(struct mCore *c)
{
    bp_require(c,c->runFrame!=rt_frame,"Circus recovery observer already attached");
    rt_original_frame=c->runFrame;rt_seen=0U;++rt_core;
    c->runFrame=rt_frame;
    rt_emit(c);
}
/* RECOVERY_WATCH_END */

static void ip_recovered(struct mCore *c)
{
    for(unsigned f=0;f<12000U && (!b_field(c) || read8(c,BP_F(snapshot_valid)) || sc_phase(c));++f)
        b_frame(c,f%90U==0U?QOL_KEY_B:0U);
    b_frames_run(c,0,180U);
    uint8_t party[600];b_copy(c,QOL_PLAYER_PARTY,party,sizeof(party));rt_emit(c);
    bp_require(c,b_field(c) && sc_current(c)==0U && sc_best(c)==1U && sc_phase(c)==0U
        && read32(c,SC_OWNER+24U)==2U && read32(c,SC_OWNER+28U)==2U
        && read8(c,SC_OWNER+38U)==3U,"Circus interruption must abort once and preserve real best1");
    bp_require(c,!read8(c,BP_F(snapshot_valid)) && !read8(c,BP_F(marker)) && !read8(c,BP_F(reward_pending))
        && !read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER) && !read16(c,BP_F(battle_points)),"Circus interruption kept session or paid unearned BP");
    bp_require(c,read8(c,QOL_PLAYER_PARTY_COUNT)==1U && !memcmp(party,sc_party,sizeof(party)),"Circus interruption original600 lost");
    sc_frozen(c);
}

int main(int argc,char **argv)
{
    if(argc==3 && !strcmp(argv[1],"--guard-check"))a_guard_check(argv[2]);
    if(argc!=7 || strcmp(argv[5],"circus-interrupt-second-battle"))return 2;
    g_prefix=argv[6];char hash[65],seed[65],after[65];sha256_file(argv[1],hash);sha256_file(argv[2],seed);
    a_require(!strcmp(hash,N_SHA) && !strcmp(hash,argv[3]) && !strcmp(seed,B_SEED_SHA) && !strcmp(seed,argv[4]),"Circus interruption input identity");
    struct mLogger logger={.log=qol_log,.filter=NULL};mLogSetDefaultLogger(&logger);p03f_rtc_reserve(argv[2]);
    struct mCore *c=qol_open(argv[1],argv[2]);qol_log_core=c;c->setVideoBuffer(c,b_video,240U);c->reset(c);
    a_require(a_continue(c),"Circus interruption initial Continue");a_flash_prepare(c);
    (void)call_preserving(c,0x09220861U,96U,5U,20U,20U);run_key_frames(c,0,1800U);
    for(unsigned i=0;i<12U && !b_field(c);++i)b_press(c,QOL_KEY_B,180U);
    b_position(c,96U,5U,20U,20U);clear_parties(c);create_mon(c,QOL_PLAYER_PARTY,4U,50U);write8(c,QOL_PLAYER_PARTY_COUNT,1U);
    (void)call_preserving(c,0x0809984DU,0,0,0,0);
    for(unsigned i=0;i<sizeof(VegaFactoryState);++i)write8(c,BP_FACTORY+i,0U);
    (void)call_preserving(c,QOL_SAVE_FINALIZE,QOL_LEDGER,0,0,0);
    b_copy(c,QOL_PLAYER_PARTY,sc_party,sizeof(sc_party));b_copy(c,BP_FACTORY+2U,sc_factory,sizeof(sc_factory));
    uint32_t inventory[G_ITEMS],inventory_after[G_ITEMS];g_inventory(c,inventory);sc_counter=read32(c,P03_SAVE_COUNTER);
    bp_require(c,!read32(c,CF_FLAGS) && !sc_current(c) && !sc_best(c) && !sc_phase(c),"Circus owner not initially zero; do not inject");
    sc_event(c,"fixture",0U);struct mCore original=*c;a_guard(c);cf_open(c);cf_rentals(c);sc_select(c);
    sc_launch_battle(c,0U);
    bp_require(c,sc_finish_battle(c,0U)==1U,"Circus interruption requires one real prior win");
    sc_launch_battle(c,1U);
    bp_require(c,sc_current(c)==1U && sc_best(c)==1U && sc_phase(c)==2U
        && read32(c,SC_OWNER+24U)==2U && read32(c,SC_OWNER+28U)==1U
        && read32(c,P03_SAVE_COUNTER)==sc_counter,"Circus interruption missing pending second battle");
    uint8_t armed[64],recovered[64],loaded[64];b_copy(c,SC_OWNER,armed,sizeof(armed));
    /* 通常Saveを押さずcoreを破棄。savestate/RAM/ownerのhostコピーはしない。 */
    a_restore(c,&original);c=b_restart(c,argv[1],argv[2]);c->reset(c);original=*c;a_guard(c);rt_watch(c);
    bp_require(c,b_continue(c),"Circus interruption fresh Continue failed");ip_recovered(c);
    b_copy(c,SC_OWNER,recovered,sizeof(recovered));g_inventory(c,inventory_after);
    bp_require(c,memcmp(armed,recovered,sizeof(armed)) && read32(c,P03_SAVE_COUNTER)==sc_counter
        && !memcmp(inventory,inventory_after,sizeof(inventory)),"Circus recovery did not persist abort or changed inventory/save counter");
    sc_event(c,"recovered",2U);
    bp_require(c,b_save(c),"Circus recovered normal Save failed");sc_event(c,"saved",2U);
    a_restore(c,&original);c=b_restart(c,argv[1],argv[2]);c->reset(c);original=*c;a_guard(c);rt_watch(c);
    bp_require(c,b_continue(c),"Circus recovered Save/fresh Continue failed");ip_recovered(c);
    b_copy(c,SC_OWNER,loaded,sizeof(loaded));g_inventory(c,inventory_after);
    bp_require(c,!memcmp(recovered,loaded,sizeof(loaded)) && !memcmp(inventory,inventory_after,sizeof(inventory))
        && read32(c,P03_SAVE_COUNTER)==sc_counter+1U,"Circus recovery repeated abort or lost64/inventory/counter");
    sc_event(c,"reloaded",2U);unsigned final_counter=read32(c,P03_SAVE_COUNTER);
    a_restore(c,&original);qol_close(c);qol_log_core=NULL;sha256_file(argv[1],after);
    a_require(!strcmp(hash,after) && !log_problem_count,"Circus interruption ROM changed or mGBA warned");
    printf("{\"schema_version\":1,\"status\":\"PASS_CIRCUS_INTERRUPTION_NATIVE\",\"case\":\"%s\",\"candidate_sha256\":\"%s\",\"wins\":%u,\"losses\":%u,\"battles_started\":%u,\"battles_finished\":1,\"interruptions\":1,\"turns\":%u,\"switches\":%u,\"forced_identity_checks\":%u,",argv[5],hash,sc_wins,sc_losses,sc_battles,sc_turns,sc_switches,sc_id_checks);
    printf("\"save_counter_before\":%u,\"save_counter_after\":%u,\"manual_saves\":1,\"fresh_cores\":3,\"owner_bytes_verified\":64,\"party_bytes_verified\":600,\"host_write_barriers\":7,\"total_frames\":%u,\"events\":%u,\"input_only_after_guard\":true,\"physical_admission_accepted\":false,\"suppression_accepted\":false,\"release_ready\":false,\"warnings_errors\":0}\n",sc_counter,final_counter,b_frames,sc_events);
    return 0;
}
