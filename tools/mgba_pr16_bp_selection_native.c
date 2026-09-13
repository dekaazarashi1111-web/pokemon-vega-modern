/* Native input probe after the accepted initial chooser. No product writes.
 * Historical controller is included as source helpers, never executed as a test.
 * Same pre-boundary progress/party/ledger fixture; all later game writes blocked. */
#include "pr16_bp_control_embedded.c"

#define SP_SCOPE "PR16_P05_SECOND_CHOOSER_DIAGNOSTIC"
#define SP_PARTY_SLOT 0x0203B01DU
#define SP_ORDER_STOCK 0x0203B048U
#define SP_ORDER_CFRU 0x0203C6C8U

static void sp_observe(struct mCore *c,const char *label) {
    bp_state(c,label);bp_context_snapshot(c);
    bp_read_span(c,"party_menu",0x0203B014U,24U);
    bp_read_span(c,"stock_selected_order",SP_ORDER_STOCK,6U);
    bp_read_span(c,"cfru_selected_order",SP_ORDER_CFRU,6U);
    bp_read_span(c,"factory_prefix",BP_FACTORY,106U);
    g_shot(label);
}
static void sp_entry(struct mCore *c,unsigned index,unsigned slot) {
    bp_require(c,read32(c,BATTLE_CORE_MAIN_CALLBACK2)==P02S_CB2_PARTY
        && read8(c,SP_PARTY_SLOT)==slot,"selection cursor not at intended rental");
    char label[32];snprintf(label,sizeof(label),"entry-menu-%u",index+1U);
    b_press(c,QOL_KEY_A,60U);sp_observe(c,label);
    bp_require(c,read8(c,G_CURSOR)==0U,"entry menu default cursor differs");
    b_press(c,QOL_KEY_A,60U);
    snprintf(label,sizeof(label),"selected-%u",index+1U);sp_observe(c,label);
    bp_require(c,read8(c,SP_ORDER_CFRU+index)==slot+1U,"native Enter did not record CFRU selected order");
}

/* ScriptContext layout is pinned by chooser-upstream-sources.zip/script.h:
 * stackDepth/mode/comparison, nativePtr+4, scriptPtr+8. A pending 5D alone
 * is not execution evidence: require the native resume pointer to become +1. */
#define SP_SCRIPT_PTR (0x03000EB0U + 8U)
#define SP_PENDING_5D 0x092CF668U
struct SPLaunch {
    unsigned confirm,advance,allocated,action;
    uint32_t after,callback2,battle_main,newbs;
    unsigned enemies,species,raw_count;
};
/* The fixture's historical 0x02023F8A byte is not a native Factory count
 * contract. Count actual slots with the same +0x20 species ABI already used
 * by the accepted natural-capture controller; keep the raw byte as raw data. */
static unsigned sp_enemy_count(struct mCore *c){
    unsigned count=0;
    for(unsigned i=0;i<6U;++i)
        if(read16(c,ADDR_ENEMY_PARTY+i*100U+BATTLE_CORE_PARTY_SPECIES_OFFSET))++count;
    return count;
}
static void sp_launch_trace(struct mCore *c,const char *label){
    fprintf(stderr,"BP_LAUNCH label=%s frame=%u cb2=%08x script=%08x mode=%u native=%08x newbs=%08x main=%08x enemy_count_raw=%u enemy_species=%u\n",
        label,b_frames,read32(c,BATTLE_CORE_MAIN_CALLBACK2),read32(c,SP_SCRIPT_PTR),
        read8(c,0x03000EB1U),read32(c,0x03000EB4U),read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER),
        read32(c,0x03004FC4U),read8(c,BATTLE_CORE_ENEMY_PARTY_COUNT),read16(c,ADDR_BATTLE_MONS+BATTLE_MON_SIZE));
}
static struct SPLaunch sp_confirm_and_launch(struct mCore *c,const uint8_t *enemy_before){
    struct SPLaunch w={0};
    bp_require(c,read32(c,SP_SCRIPT_PTR)==SP_PENDING_5D && read8(c,SP_PENDING_5D)==0x5DU,
        "second chooser does not hold the pinned pending 5D");
    for(unsigned k=0;k<8U && read8(c,SP_PARTY_SLOT)!=6U;++k){
        bp_require(c,read32(c,BATTLE_CORE_MAIN_CALLBACK2)==P02S_CB2_PARTY,"second chooser disappeared before Confirm");
        b_press(c,QOL_KEY_UP,60U);sp_launch_trace(c,"confirm-navigation");
    }
    bp_require(c,read8(c,SP_PARTY_SLOT)==6U,"native cursor did not reach second Confirm");
    for(unsigned i=0;i<3U;++i)bp_require(c,read8(c,SP_ORDER_CFRU+i)==i+1U,"second chooser changed selected order");
    sp_observe(c,"second-confirm");sp_launch_trace(c,"before-confirm");w.confirm=b_frames+1U;
    uint32_t last_cb=read32(c,BATTLE_CORE_MAIN_CALLBACK2),last_ptr=SP_PENDING_5D,last_bs=0U;
    for(unsigned f=0;f<12000U;++f){
        /* One-frame A pulses. Every transition is observed before another key. */
        b_frame(c,f%90U==0U?QOL_KEY_A:0U);
        uint32_t cb=read32(c,BATTLE_CORE_MAIN_CALLBACK2),ptr=read32(c,SP_SCRIPT_PTR),bs=read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER);
        if(cb!=last_cb || ptr!=last_ptr || bs!=last_bs || f==11999U){
            sp_launch_trace(c,"native-transition");last_cb=cb;last_ptr=ptr;last_bs=bs;
        }
        if(!w.advance && ptr!=SP_PENDING_5D){
            w.advance=b_frames;w.after=ptr;sp_observe(c,"script-resumed");
            bp_require(c,ptr==SP_PENDING_5D+1U,"first script advance did not consume exactly pending 5D");
        }
        if(bs && !w.allocated){w.allocated=b_frames;sp_observe(c,"battle-allocated");}
        if(n_action(c)){
            c->setKeys(c,0);w.action=b_frames;w.callback2=cb;w.newbs=bs;w.battle_main=read32(c,0x03004FC4U);
            w.raw_count=read8(c,BATTLE_CORE_ENEMY_PARTY_COUNT);w.enemies=sp_enemy_count(c);w.species=read16(c,ADDR_BATTLE_MONS+BATTLE_MON_SIZE);
            break;
        }
    }
    sp_launch_trace(c,"launch-stop");sp_observe(c,"battle-action");
    uint8_t enemy_after[600];b_copy(c,ADDR_ENEMY_PARTY,enemy_after,sizeof(enemy_after));
    bp_read_span(c,"enemy_party_generated",ADDR_ENEMY_PARTY,600U);
    bp_require(c,w.advance>=w.confirm && w.allocated>=w.advance && w.action>=w.allocated,
        "native second confirmation did not reach script resume/battle/action in order");
    bp_require(c,w.newbs>=0x02000000U && w.newbs<0x02040000U && w.battle_main==0x08013861U
        && w.enemies==3U && w.species>0U && w.species==read16(c,ADDR_ENEMY_PARTY+BATTLE_CORE_PARTY_SPECIES_OFFSET)
        && read8(c,QOL_PLAYER_PARTY_COUNT)==3U && memcmp(enemy_before,enemy_after,600U),
        "battle action lacks allocated state or newly generated enemy party");
    return w;
}

int main(int argc,char **argv) {
    if(argc==3 && !strcmp(argv[1],"--guard-check"))a_guard_check(argv[2]);
    if(argc!=7 || strcmp(argv[5],"second-confirm-battle-probe"))return 2;
    g_prefix=argv[6];char hash[65],seed[65],after[65];sha256_file(argv[1],hash);sha256_file(argv[2],seed);
    a_require(!strcmp(hash,N_SHA) && !strcmp(hash,argv[3]) && !strcmp(seed,B_SEED_SHA) && !strcmp(seed,argv[4]),"selection fixed input identity differs");
    struct mLogger logger={.log=qol_log,.filter=NULL};mLogSetDefaultLogger(&logger);p03f_rtc_reserve(argv[2]);
    struct mCore *c=qol_open(argv[1],argv[2]);qol_log_core=c;c->setVideoBuffer(c,b_video,240U);c->reset(c);
    a_require(a_continue(c),"selection initial Continue failed");a_flash_prepare(c);
    (void)call_preserving(c,0x09220861U,96U,5U,20U,20U);run_key_frames(c,0,1800U);
    for(unsigned i=0;i<12U && !b_field(c);++i)b_press(c,QOL_KEY_B,180U);
    b_position(c,96U,5U,20U,20U);
    clear_parties(c);create_mon(c,QOL_PLAYER_PARTY,4U,50U);write8(c,QOL_PLAYER_PARTY_COUNT,1U);
    (void)call_preserving(c,0x0809984DU,0,0,0,0);
    for(unsigned i=0;i<sizeof(VegaFactoryState);++i)write8(c,BP_FACTORY+i,0U);
    (void)call_preserving(c,QOL_SAVE_FINALIZE,QOL_LEDGER,0,0,0);
    uint8_t party[600],snapshot[600],enemy_before[600];b_copy(c,ADDR_ENEMY_PARTY,enemy_before,sizeof(enemy_before));b_copy(c,QOL_PLAYER_PARTY,party,sizeof(party));
    unsigned counter=read32(c,P03_SAVE_COUNTER);bp_state(c,"fixture");g_shot("fixture");
    struct mCore original=*c;a_guard(c);bp_open(c);bp_trial(c);sp_observe(c,"chooser-start");
    sp_entry(c,0U,0U);b_press(c,QOL_KEY_RIGHT,60U);
    sp_entry(c,1U,1U);b_press(c,QOL_KEY_DOWN,60U);
    sp_entry(c,2U,2U);
    bp_require(c,read8(c,SP_PARTY_SLOT)==6U,"three entries did not move to Confirm");
    unsigned selected_frame=b_frames;sp_observe(c,"three-selected");b_press(c,QOL_KEY_A,120U);
    unsigned second_frame=0U;uint32_t last=0U;
    for(unsigned f=0;f<12000U;++f){
        unsigned cb=read32(c,BATTLE_CORE_MAIN_CALLBACK2);
        if(cb!=last){bp_state(c,"selection-return");last=cb;}
        bp_require(c,!read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER),"unexpected battle before documented redundant chooser");
        if(cb==P02S_CB2_PARTY && read8(c,QOL_PLAYER_PARTY_COUNT)==3U){
            b_frames_run(c,0,180U);second_frame=b_frames;break;
        }
        b_frame(c,f%90U==0U?QOL_KEY_A:0U);
    }
    sp_observe(c,"post-selection");
    bp_require(c,second_frame>selected_frame,"native selection did not reach documented second chooser");
    b_copy(c,BP_F(party_snapshot),snapshot,sizeof(snapshot));
    bp_require(c,!memcmp(party,snapshot,sizeof(party)) && read8(c,BP_F(snapshot_valid))==1U
        && read8(c,BP_F(marker))==2U,"selected party did not retain original snapshot/battle-active marker");
    bp_require(c,read16(c,BP_F(battle_points))==0U && read8(c,BP_F(reward_pending))==0U
        && read32(c,P03_SAVE_COUNTER)==counter,"unplayed battle awarded BP or performed full save");
    struct SPLaunch launch=sp_confirm_and_launch(c,enemy_before);
    bp_require(c,read16(c,BP_F(battle_points))==0U && !read8(c,BP_F(reward_pending))
        && read32(c,P03_SAVE_COUNTER)==counter,"battle launch awarded BP or performed full save");
    a_restore(c,&original);qol_close(c);qol_log_core=NULL;sha256_file(argv[1],after);
    a_require(!strcmp(hash,after) && !log_problem_count,"selection probe ROM changed or emulator warned");
    printf("{\"schema_version\":1,\"status\":\"DIAGNOSTIC_SECOND_CONFIRM_BATTLE_ACTION_NOT_BP\",\"scope\":\"%s\",\"case\":\"%s\",\"candidate_sha256\":\"%s\",",SP_SCOPE,argv[5],hash);
    printf("\"selected_frame\":%u,\"second_chooser_frame\":%u,\"total_frames\":%u,\"selected_count\":3,\"party_count\":3,\"original_snapshot_bytes_verified\":600,",selected_frame,second_frame,b_frames);
    printf("\"confirm_frame\":%u,\"script_advance_frame\":%u,\"battle_struct_frame\":%u,\"action_frame\":%u,",launch.confirm,launch.advance,launch.allocated,launch.action);
    printf("\"pending_script_pointer\":%u,\"script_pointer_after_advance\":%u,\"pending_opcode\":93,\"battle_callback2\":%u,\"battle_main_callback\":%u,\"new_battle_struct\":%u,",SP_PENDING_5D,launch.after,launch.callback2,launch.battle_main,launch.newbs);
    printf("\"enemy_party_count_raw\":%u,\"enemy_party_count\":%u,\"enemy_battle_species\":%u,\"enemy_party_changed\":true,\"script_context_resumed\":true,",launch.raw_count,launch.enemies,launch.species);
    printf("\"bp_earned\":0,\"battle_started\":true,\"save_counter\":%u,\"manual_saves\":0,\"fresh_cores\":1,\"host_write_barriers\":7,\"input_only_after_guard\":true,\"fixture_same_as_accepted_cancel\":true,\"native_bp_earning_accepted\":false,\"p05_native_bp_gap_closed\":false,\"release_ready\":false,\"warnings_errors\":0}\n",counter);
    return 0;
}
