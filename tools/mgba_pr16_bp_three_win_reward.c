/* Extend the already-observed first-win/exchange prefix through native battles 2/3.
 * This code only reads game memory and supplies normal keypad input after the guard.
 * It never writes ROM, save, RNG, HP, PP, outcome, ledger, or script state. */
#define RW_SPECIAL_RESULT 0x02037004U
#define RW_EXPECTED_BP 9U

struct RWResult {
    unsigned bp_before;
    unsigned second_start,second_turns,second_switches,second_pp_events;
    unsigned second_outcome,second_outcome_frame,second_afterbattle;
    unsigned second_pending,second_streak,second_bp;
    unsigned second_exchange_menu,second_exchange_selected,second_exchange_confirm;
    unsigned second_exchange_commit,third_struct,third_action,second_exchange_slot;
    unsigned third_start,third_turns,third_switches,third_pp_events;
    unsigned third_outcome,third_outcome_frame,third_afterbattle;
    unsigned third_pending,third_streak,third_bp;
    unsigned complete_frame,bp_after,bp_delta,final_pending,final_streak;
    unsigned final_marker,final_snapshot,final_count,special_result;
    unsigned restored_bytes,afterbattle_script,complete_script,complete_callback2;
};

static void rw_trace(struct mCore *c,const char *label) {
    fprintf(stderr,
        "BP_REWARD label=%s frame=%u outcome=%u newbs=%08x cb2=%08x script=%08x "
        "pending=%u streak=%u bp=%u marker=%u snapshot=%u count=%u result=%u save=%u\n",
        label,b_frames,read8(c,BATTLE_CORE_BATTLE_OUTCOME)&0x7FU,
        read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER),read32(c,BATTLE_CORE_MAIN_CALLBACK2),
        read32(c,SP_SCRIPT_PTR),read8(c,BP_F(reward_pending)),
        read16(c,BP_F(current_streak)),read16(c,BP_F(battle_points)),
        read8(c,BP_F(marker)),read8(c,BP_F(snapshot_valid)),
        read8(c,QOL_PLAYER_PARTY_COUNT),read16(c,RW_SPECIAL_RESULT),
        read32(c,P03_SAVE_COUNTER));
}

static void rw_require_original_snapshot(struct mCore *c,const uint8_t *original) {
    uint8_t actual[600];
    b_copy(c,BP_F(party_snapshot),actual,sizeof(actual));
    bp_require(c,!memcmp(actual,original,sizeof(actual)),
        "three-win path changed original party snapshot");
}

static void rw_require_party(struct mCore *c,const uint8_t *expected,const char *message) {
    uint8_t actual[600];
    b_copy(c,QOL_PLAYER_PARTY,actual,sizeof(actual));
    bp_require(c,!memcmp(actual,expected,sizeof(actual)),message);
}

/* Battle 3 cannot reuse br_battle_return because the same script continues from
 * reward_pending=3 into FacilityRuntime_Complete. Observe both boundaries in one
 * input-only loop so a transient three-win ledger is never inferred from BP alone. */
static void rw_final_battle(struct mCore *c,const uint8_t *original,
        const uint8_t *rental,unsigned counter,struct RWResult *r) {
    struct BPReturn w={.start=b_frames};
    unsigned last_outcome=0U;uint32_t last_cb=read32(c,BATTLE_CORE_MAIN_CALLBACK2);
    uint32_t last_script=read32(c,SP_SCRIPT_PTR);
    bp_require(c,n_action(c),"third battle did not start at native action");
    r->third_start=b_frames;rw_trace(c,"third-start");
    while(b_frames-w.start<120000U){
        unsigned outcome=read8(c,BATTLE_CORE_BATTLE_OUTCOME)&0x7FU;
        uint32_t cb=read32(c,BATTLE_CORE_MAIN_CALLBACK2);
        uint32_t script=read32(c,SP_SCRIPT_PTR);
        uint32_t bs=read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER);
        if(outcome!=last_outcome || cb!=last_cb || script!=last_script){
            rw_trace(c,"third-transition");last_outcome=outcome;last_cb=cb;last_script=script;
        }
        if(outcome && !w.outcome){
            w.outcome=outcome;w.outcome_frame=b_frames;r->third_outcome_frame=b_frames;
            r->third_outcome=outcome;g_shot("third-battle-outcome");
            bp_require(c,outcome==1U,"third native battle did not win");
        }
        bp_require(c,read32(c,P03_SAVE_COUNTER)==counter,
            "three-win path changed full-save counter");
        unsigned bp=read16(c,BP_F(battle_points));
        bp_require(c,bp==r->bp_before || bp==r->bp_before+RW_EXPECTED_BP,
            "three-win path produced an unexpected BP amount");
        if(w.outcome && !bs && !r->third_afterbattle
            && read8(c,BP_F(snapshot_valid))==1U
            && read8(c,BP_F(marker))==2U
            && read8(c,BP_F(reward_pending))==3U
            && read16(c,BP_F(current_streak))==3U
            && bp==r->bp_before && read8(c,QOL_PLAYER_PARTY_COUNT)==3U){
            rw_require_original_snapshot(c,original);
            rw_require_party(c,rental,"third AfterBattle did not heal/preserve rental party");
            r->third_afterbattle=b_frames;r->third_pending=3U;r->third_streak=3U;
            r->third_bp=bp;r->afterbattle_script=script;
            rw_trace(c,"third-afterbattle");sp_observe(c,"third-afterbattle");
            continue;
        }
        if(r->third_afterbattle && !bs
            && read8(c,BP_F(snapshot_valid))==0U
            && read8(c,BP_F(marker))==0U
            && read8(c,BP_F(reward_pending))==0U
            && read16(c,BP_F(current_streak))==3U
            && read16(c,BP_F(battle_points))==r->bp_before+RW_EXPECTED_BP
            && read8(c,QOL_PLAYER_PARTY_COUNT)==1U
            && read16(c,RW_SPECIAL_RESULT)==RW_EXPECTED_BP){
            rw_require_party(c,original,"three-win completion did not restore exact original party");
            r->complete_frame=b_frames;r->complete_script=script;r->complete_callback2=cb;
            r->bp_after=read16(c,BP_F(battle_points));r->bp_delta=r->bp_after-r->bp_before;
            r->final_pending=read8(c,BP_F(reward_pending));
            r->final_streak=read16(c,BP_F(current_streak));
            r->final_marker=read8(c,BP_F(marker));r->final_snapshot=read8(c,BP_F(snapshot_valid));
            r->final_count=read8(c,QOL_PLAYER_PARTY_COUNT);
            r->special_result=read16(c,RW_SPECIAL_RESULT);r->restored_bytes=600U;
            rw_trace(c,"complete");sp_observe(c,"three-win-complete");break;
        }
        if(!w.outcome && bs && n_action(c)){
            bp_require(c,w.turns<48U,"third battle move count bound reached");
            br_move(c,&w);continue;
        }
        if(!w.outcome && bs && cb==P02S_CB2_PARTY){
            bp_require(c,w.switches<2U,"third battle repeated forced switch");
            br_switch(c,&w);continue;
        }
        unsigned elapsed=b_frames-w.start;
        b_frame(c,w.outcome && elapsed%90U==0U?QOL_KEY_A:
            (!w.outcome && elapsed%60U==0U?QOL_KEY_B:0U));
    }
    c->setKeys(c,0U);
    r->third_turns=w.turns;r->third_switches=w.switches;r->third_pp_events=w.pp_events;
    bp_require(c,r->third_outcome==1U && r->third_afterbattle>=r->third_outcome_frame
        && r->complete_frame>=r->third_afterbattle && r->third_turns>0U
        && r->bp_delta==RW_EXPECTED_BP && r->restored_bytes==600U,
        "third battle did not reach exact native three-win completion");
}

static struct RWResult rw_three_win(struct mCore *c,const uint8_t *original,unsigned counter) {
    struct RWResult r={0};uint8_t second_party[600],third_party[600];
    r.bp_before=read16(c,BP_F(battle_points));
    bp_require(c,r.bp_before==0U && read8(c,BP_F(reward_pending))==1U
        && read16(c,BP_F(current_streak))==1U && n_action(c),
        "reward extension did not start at battle 2 action/one-win ledger");
    b_copy(c,QOL_PLAYER_PARTY,second_party,sizeof(second_party));
    r.second_start=b_frames;rw_trace(c,"second-start");
    /* wx_voluntary_count is host-controller state, not game memory.  The accepted
     * first battle consumed its one normal PKMN-menu switch; battle 2 is a new
     * native battle and therefore receives its own single-switch budget. */
    wx_voluntary_count=0U;
    struct BPReturn second=br_battle_return(c,original,counter,2U);
    r.second_turns=second.turns;r.second_switches=second.switches;
    r.second_pp_events=second.pp_events;r.second_outcome=second.outcome;
    r.second_outcome_frame=second.outcome_frame;r.second_afterbattle=second.facility_frame;
    r.second_pending=second.pending;r.second_streak=second.streak;
    r.second_bp=read16(c,BP_F(battle_points));
    bp_require(c,second.outcome==1U && second.pending==2U && second.streak==2U
        && r.second_bp==r.bp_before && second.final_count==3U
        && second.marker==2U && second.snapshot==1U,
        "second native battle ledger differs from two wins");
    rw_require_original_snapshot(c,original);
    rw_require_party(c,second_party,"second AfterBattle did not heal/preserve rental party");
    rw_trace(c,"second-afterbattle");g_shot("second-afterbattle");

    struct WXResult exchange=wx_exchange_next(c,original,counter,second.outcome,2U);
    r.second_exchange_menu=exchange.menu;r.second_exchange_selected=exchange.selected;
    r.second_exchange_confirm=exchange.confirm;r.second_exchange_commit=exchange.commit;
    r.third_struct=exchange.allocated;r.third_action=exchange.action;
    r.second_exchange_slot=exchange.slot;
    bp_require(c,exchange.replaced==100U && exchange.preserved==500U
        && exchange.action==b_frames && !read16(c,BP_F(battle_points)),
        "second exchange did not reach exact third-battle action");
    b_copy(c,QOL_PLAYER_PARTY,third_party,sizeof(third_party));
    rw_final_battle(c,original,third_party,counter,&r);
    return r;
}
