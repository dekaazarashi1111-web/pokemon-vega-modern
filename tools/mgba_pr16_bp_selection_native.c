/* Native input probe after the accepted initial chooser. No product writes.
 * Historical controller is included as source helpers, never executed as a test.
 * Same pre-boundary progress/party/ledger fixture; all later game writes blocked. */
#include "pr16_bp_control_embedded.c"

#define SP_SCOPE "PR16_P05_THREE_SELECTION_DIAGNOSTIC"
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
int main(int argc,char **argv) {
    if(argc==3 && !strcmp(argv[1],"--guard-check"))a_guard_check(argv[2]);
    if(argc!=7 || strcmp(argv[5],"three-selection-probe"))return 2;
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
    uint8_t party[600],snapshot[600];b_copy(c,QOL_PLAYER_PARTY,party,sizeof(party));
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
    a_restore(c,&original);qol_close(c);qol_log_core=NULL;sha256_file(argv[1],after);
    a_require(!strcmp(hash,after) && !log_problem_count,"selection probe ROM changed or emulator warned");
    printf("{\"schema_version\":1,\"status\":\"DIAGNOSTIC_THREE_SELECTED_SECOND_CHOOSER_NOT_BP\",\"scope\":\"%s\",\"case\":\"%s\",\"candidate_sha256\":\"%s\",",SP_SCOPE,argv[5],hash);
    printf("\"selected_frame\":%u,\"second_chooser_frame\":%u,\"total_frames\":%u,\"selected_count\":3,\"party_count\":3,\"original_snapshot_bytes_verified\":600,",selected_frame,second_frame,b_frames);
    printf("\"bp_earned\":0,\"battle_started\":false,\"save_counter\":%u,\"manual_saves\":0,\"fresh_cores\":1,\"host_write_barriers\":7,\"input_only_after_guard\":true,\"fixture_same_as_accepted_cancel\":true,\"native_bp_earning_accepted\":false,\"p05_native_bp_gap_closed\":false,\"release_ready\":false,\"warnings_errors\":0}\n",counter);
    return 0;
}
