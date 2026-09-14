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

/* Stage20 has two separate exchange-script owners.  The accepted prefix helper
 * is intentionally bound to exchange 1 (0x092CF72C -> battle 2 at 0x092CF680).
 * Extend only the unobserved exchange-2 suffix here, binding its exact owner and
 * battle-3 return boundaries without weakening the accepted first exchange. */
#define RW_EXCHANGE2_OWNER_SCRIPT 0x092CF778U
#define RW_BATTLE3_SCRIPT 0x092CF6BCU
static void rw_single_confirm(struct mCore *c,unsigned slot) {
    bp_require(c,slot<3U,"second exchange slot out of bounds");
    for(unsigned k=0U;k<=8U;++k){
        bp_require(c,read32(c,BATTLE_CORE_MAIN_CALLBACK2)==P02S_CB2_PARTY
            && read32(c,SP_SCRIPT_PTR)==RW_EXCHANGE2_OWNER_SCRIPT
            && !read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER),
            "second exchange chooser owner changed before Confirm");
        for(unsigned i=0U;i<6U;++i)
            bp_require(c,read8(c,SP_ORDER_CFRU+i)==(i?0U:slot+1U),
                "second exchange selected order changed before Confirm");
        unsigned cursor=read8(c,SP_PARTY_SLOT);
        bp_require(c,cursor<8U,"second exchange chooser cursor out of bounds");
        if(cursor==6U)return;
        bp_require(c,k<8U,"second exchange Confirm navigation reached 8-input bound");
        b_press(c,QOL_KEY_UP,60U);
        fprintf(stderr,"BP_REWARD_EXCHANGE_CONFIRM frame=%u input=%u cursor=%u order=%u\n",
            b_frames,k+1U,read8(c,SP_PARTY_SLOT),read8(c,SP_ORDER_CFRU));
    }
}
static bool rw_commit_returned(struct mCore *c) {
    if(read32(c,VEGA_SAVE_TRANSACTION_SCRATCH_ADDRESS)
        || read32(c,BATTLE_CORE_MAIN_CALLBACK2)!=0x08055E75U
        || read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER))return false;
    uint32_t script=read32(c,SP_SCRIPT_PTR);
    return script==RW_BATTLE3_SCRIPT || script==RW_BATTLE3_SCRIPT+6U
        || script==RW_BATTLE3_SCRIPT+8U || script==RW_BATTLE3_SCRIPT+13U;
}
static struct WXResult rw_exchange_next(struct mCore *c,const uint8_t *original,
        unsigned counter,unsigned observed_win) {
    struct WXResult w={.opening=wx_voluntary_count};unsigned start=b_frames;
    uint8_t expected[600],actual[600],cached[100],snapshot[600];
    bp_require(c,observed_win==1U && read8(c,BP_F(reward_pending))==2U
        && read16(c,BP_F(current_streak))==2U,
        "second exchange requires observed native victory and two-win ledger");
    br_trace(c,"second-win-exchange-start");
    for(unsigned f=0;f<12000U;++f){
        bp_require(c,!read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER),
            "third battle launched before second exchange observation");
        if(read32(c,BATTLE_CORE_MAIN_CALLBACK2)==P02S_CB2_PARTY){
            w.menu=b_frames;b_frames_run(c,0U,180U);break;
        }
        b_frame(c,f%90U==0U?QOL_KEY_A:0U);
    }
    bp_require(c,w.menu>start && read8(c,QOL_PLAYER_PARTY_COUNT)==3U
        && read32(c,SP_SCRIPT_PTR)==RW_EXCHANGE2_OWNER_SCRIPT
        && read32(c,VEGA_SAVE_TRANSACTION_SCRATCH_ADDRESS)==0x58434846U,
        "second native exchange chooser/owner absent");
    for(unsigned i=0;i<6U;++i)
        bp_require(c,!read8(c,SP_ORDER_CFRU+i),
            "second exchange order was not cleared");
    b_copy(c,QOL_PLAYER_PARTY,expected,sizeof(expected));
    b_copy(c,VEGA_SAVE_TRANSACTION_SCRATCH_ADDRESS+4U,cached,sizeof(cached));
    bp_read_span(c,"second_exchange_cached_original",
        VEGA_SAVE_TRANSACTION_SCRATCH_ADDRESS+4U,100U);
    w.slot=0U;
    for(unsigned i=1;i<3U;++i)
        if(wx_party_score(c,i)<wx_party_score(c,w.slot))w.slot=i;
    wx_healed_expected(c,cached);memcpy(expected+100U*w.slot,cached,100U);
    sp_observe(c,"second-exchange-single-menu");
    wx_cursor(c,w.slot);sp_entry(c,0U,w.slot);w.selected=b_frames;
    w.order=read8(c,SP_ORDER_CFRU);
    bp_require(c,w.order==w.slot+1U,"second exchange selection order differs");
    rw_single_confirm(c,w.slot);
    for(unsigned i=1;i<6U;++i)
        bp_require(c,!read8(c,SP_ORDER_CFRU+i),
            "second exchange selected extra slots");
    sp_observe(c,"second-exchange-single-selected");
    w.confirm=b_frames+1U;b_press(c,QOL_KEY_A,2U);
    for(unsigned f=0;f<12000U;++f){
        uint32_t bs=read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER);
        uint32_t cb=read32(c,BATTLE_CORE_MAIN_CALLBACK2);
        if(!w.commit && rw_commit_returned(c)){
            w.commit=b_frames;b_copy(c,QOL_PLAYER_PARTY,actual,sizeof(actual));
            bp_read_span(c,"second_exchange_party_committed",QOL_PLAYER_PARTY,600U);
            bp_require(c,!memcmp(expected,actual,sizeof(actual)),
                "second exchange exact600 compare failed");
            for(unsigned i=0;i<3U;++i)
                bp_require(c,read8(c,SP_ORDER_CFRU+i)==i+1U,
                    "second CommitExchange did not normalize order");
            w.replaced=100U;w.preserved=500U;
            sp_observe(c,"second-exchange-committed");
        }
        if(bs && !w.allocated){
            bp_require(c,w.commit>0U,"third battle preceded second exchange commit");
            w.allocated=b_frames;
        }
        if(w.allocated && n_action(c)){w.action=b_frames;break;}
        b_copy(c,BP_F(party_snapshot),snapshot,sizeof(snapshot));
        bp_require(c,!memcmp(snapshot,original,sizeof(snapshot))
            && read8(c,BP_F(marker))==2U && read8(c,BP_F(snapshot_valid))==1U
            && read8(c,BP_F(reward_pending))==2U
            && read16(c,BP_F(current_streak))==2U
            && !read16(c,BP_F(battle_points))
            && read32(c,P03_SAVE_COUNTER)==counter,
            "second exchange changed original snapshot/ledger/save unexpectedly");
        if(w.commit && cb==P02S_CB2_PARTY && read8(c,SP_PARTY_SLOT)!=6U){
            b_press(c,QOL_KEY_UP,60U);continue;
        }
        b_frame(c,f%90U==0U?QOL_KEY_A:0U);
    }
    c->setKeys(c,0U);br_trace(c,"second-exchange-next-action");
    sp_observe(c,"second-exchange-next-action");
    bp_require(c,w.menu<w.selected && w.selected<w.confirm && w.confirm<=w.commit
        && w.commit<=w.allocated && w.allocated<=w.action && w.action==b_frames
        && !read8(c,BATTLE_CORE_BATTLE_OUTCOME) && sp_enemy_count(c)==3U,
        "second native exchange did not reach third battle/action");
    return w;
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
    /* Battle 3 receives the same one normal PKMN-menu switch budget as battles
     * 1/2.  This is controller-only state and does not write game memory. */
    wx_voluntary_count=0U;
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
            if(!wx_voluntary_count){wx_opening_switch(c);continue;}
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

    struct WXResult exchange=rw_exchange_next(c,original,counter,second.outcome);
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
