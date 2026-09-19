/* 初回turnの既存観測後だけを延長する。ROM/save/HP/PP/RNG/勝敗へのhost書込みなし。
 * 戦闘中の通常入力と瀕死交代だけ。勝利/敗北を両方観測対象とし、逃走を受け入れない。
 * 勝利後はAfterBattleの1勝加算で止め、未修正の交換や3戦報酬を成功としない。 */
struct BPReturn {
    unsigned start,turns,switches,pp_events,outcome,outcome_frame,facility_frame;
    unsigned final_count,marker,snapshot,pending,streak,script,callback2;
};
static void br_trace(struct mCore *c,const char *label) {
    fprintf(stderr,"BP_RETURN label=%s frame=%u cb2=%08x main=%08x command=%u ctrl=%08x exec=%x newbs=%08x outcome=%u index=%u hp=%u enemy_hp=%u slot=%u script=%08x pending=%u streak=%u snapshot=%u marker=%u count=%u bp=%u save=%u\n",
        label,b_frames,read32(c,BATTLE_CORE_MAIN_CALLBACK2),read32(c,0x03004FC4U),
        read8(c,0x02022B24U),read32(c,0x03005020U),read32(c,0x02023B28U),
        read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER),read8(c,BATTLE_CORE_BATTLE_OUTCOME),
        read16(c,ADDR_BATTLER_PARTY_INDEXES),read16(c,ADDR_BATTLE_MONS+BATTLE_CORE_MON_HP),
        read16(c,ADDR_BATTLE_MONS+BATTLE_MON_SIZE+BATTLE_CORE_MON_HP),read8(c,SP_PARTY_SLOT),
        read32(c,SP_SCRIPT_PTR),read8(c,BP_F(reward_pending)),read16(c,BP_F(current_streak)),
        read8(c,BP_F(snapshot_valid)),read8(c,BP_F(marker)),read8(c,QOL_PLAYER_PARTY_COUNT),
        read16(c,BP_F(battle_points)),read32(c,P03_SAVE_COUNTER));
}
static bool br_move_menu(struct mCore *c) {
    return read8(c,0x02022B24U)==0x14U && (read32(c,0x02023B28U)&1U);
}
static void br_move(struct mCore *c,struct BPReturn *w) {
    unsigned slot=4U,move=0U,pp=0U;
    bp_require(c,n_action(c),"return move outside native action");
    for(unsigned i=0;i<4U;++i){
        unsigned m=read16(c,ADDR_BATTLE_MONS+BATTLE_MON_MOVES_OFFSET+2U*i);
        unsigned p=read8(c,ADDR_BATTLE_MONS+BATTLE_MON_PP_OFFSET+i);
        if(m && p){slot=i;move=m;pp=p;break;}
    }
    br_trace(c,"turn-start");
    bp_require(c,slot<4U,"return has no native move with PP; do not fabricate Struggle");
    n_cursor(c,0U);
    for(unsigned f=0;f<600U && !br_move_menu(c);++f)
        b_frame(c,f%90U==0U && n_action(c)?QOL_KEY_A:0U);
    b_frames_run(c,0U,60U);
    bp_require(c,br_move_menu(c),"return native move menu absent");
    for(unsigned i=0;i<6U && read8(c,BATTLE_CORE_MOVE_SELECTION_CURSOR)!=slot;++i){
        unsigned at=read8(c,BATTLE_CORE_MOVE_SELECTION_CURSOR);
        bp_require(c,at<4U,"return invalid native move cursor");
        b_press(c,(at&1U)!=(slot&1U)?((slot&1U)?QOL_KEY_RIGHT:QOL_KEY_LEFT):((slot&2U)?QOL_KEY_DOWN:QOL_KEY_UP),12U);
    }
    bp_require(c,read8(c,BATTLE_CORE_MOVE_SELECTION_CURSOR)==slot,"return move cursor did not follow keys");
    unsigned chosen=b_frames+1U,index=read16(c,ADDR_BATTLER_PARTY_INDEXES),spent=0U;
    b_press(c,QOL_KEY_A,2U);++w->turns;
    for(unsigned f=0;f<18000U;++f){
        if(!spent && read16(c,ADDR_BATTLER_PARTY_INDEXES)==index
            && read16(c,ADDR_BATTLE_MONS+BATTLE_MON_MOVES_OFFSET+2U*slot)==move
            && read8(c,ADDR_BATTLE_MONS+BATTLE_MON_PP_OFFSET+slot)<pp){
            spent=b_frames;++w->pp_events;
        }
        if(read8(c,BATTLE_CORE_BATTLE_OUTCOME) || !read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER)
            || read32(c,BATTLE_CORE_MAIN_CALLBACK2)==P02S_CB2_PARTY || n_action(c)){
            fprintf(stderr,"BP_RETURN_MOVE turn=%u chosen=%u returned=%u move=%u slot=%u pp_before=%u pp_event=%u\n",w->turns,chosen,b_frames,move,slot,pp,spent);
            br_trace(c,"turn-stop");return;
        }
        b_frame(c,f%60U==0U?QOL_KEY_B:0U);
    }
    br_trace(c,"turn-timeout");bp_require(c,false,"return turn reached unchanged 18000-frame bound");
}
static void br_switch(struct mCore *c,struct BPReturn *w) {
    br_trace(c,"forced-switch-start");g_shot("forced-switch-start");
    bp_require(c,read16(c,ADDR_BATTLE_MONS+BATTLE_CORE_MON_HP)==0U,"unexpected voluntary party menu");
    b_frames_run(c,0U,60U);
    unsigned target=6U,active=read16(c,ADDR_BATTLER_PARTY_INDEXES);
    for(unsigned i=0;i<3U;++i)
        if(i!=active && read16(c,QOL_PLAYER_PARTY+i*POKEMON_SIZE+POKEMON_CURRENT_HP_OFFSET)>0U){target=i;break;}
    bp_require(c,target<3U,"forced switch has no living native rental");
    for(unsigned i=0;i<8U && read8(c,SP_PARTY_SLOT)!=target;++i){
        bp_require(c,read32(c,BATTLE_CORE_MAIN_CALLBACK2)==P02S_CB2_PARTY,"forced menu disappeared during navigation");
        b_press(c,QOL_KEY_DOWN,60U);
    }
    bp_require(c,read8(c,SP_PARTY_SLOT)==target,"forced cursor did not reach living rental");
    b_press(c,QOL_KEY_A,80U);
    if(read32(c,BATTLE_CORE_MAIN_CALLBACK2)==P02S_CB2_PARTY)b_press(c,QOL_KEY_A,80U);
    for(unsigned f=0;f<1800U;++f){
        if(read32(c,BATTLE_CORE_MAIN_CALLBACK2)!=P02S_CB2_PARTY
            && read16(c,ADDR_BATTLER_PARTY_INDEXES)==target){
            ++w->switches;br_trace(c,"forced-switch-return");g_shot("forced-switch-return");return;
        }
        b_frame(c,0U);
    }
    br_trace(c,"forced-switch-timeout");bp_require(c,false,"native forced switch did not return");
}
static struct BPReturn br_battle_return(struct mCore *c,const uint8_t *original,unsigned counter) {
    struct BPReturn w={.start=b_frames};unsigned stable=0U,last_outcome=0U;
    uint8_t actual[600];uint32_t last_cb=read32(c,BATTLE_CORE_MAIN_CALLBACK2),last_script=read32(c,SP_SCRIPT_PTR);
    bp_require(c,n_action(c),"return extension did not start after first native turn");
    br_trace(c,"extension-start");
    while(b_frames-w.start<90000U){
        unsigned outcome=read8(c,BATTLE_CORE_BATTLE_OUTCOME)&0x7FU;
        uint32_t cb=read32(c,BATTLE_CORE_MAIN_CALLBACK2),script=read32(c,SP_SCRIPT_PTR),bs=read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER);
        if(outcome!=last_outcome || cb!=last_cb || script!=last_script){
            br_trace(c,"transition");last_outcome=outcome;last_cb=cb;last_script=script;
        }
        if(outcome && !w.outcome){
            w.outcome=outcome;w.outcome_frame=b_frames;g_shot("battle-outcome");
            bp_require(c,outcome==1U || outcome==2U,"first battle outcome is not native win/loss");
        }
        bp_require(c,!read16(c,BP_F(battle_points)) && read32(c,P03_SAVE_COUNTER)==counter,"first battle changed BP or full save counter");
        if(w.outcome && !bs){
            bool returned=false;
            if(w.outcome==1U && read8(c,BP_F(snapshot_valid))==1U && read8(c,BP_F(marker))==2U
                && read8(c,BP_F(reward_pending))==1U && read16(c,BP_F(current_streak))==1U
                && read8(c,QOL_PLAYER_PARTY_COUNT)==3U && script>SP_PENDING_5D+1U && script<0x092CF800U){
                b_copy(c,BP_F(party_snapshot),actual,sizeof(actual));returned=!memcmp(actual,original,sizeof(actual));
            }else if(w.outcome==2U && !read8(c,BP_F(snapshot_valid)) && !read8(c,BP_F(marker))
                && !read8(c,BP_F(reward_pending)) && !read16(c,BP_F(current_streak))
                && read8(c,QOL_PLAYER_PARTY_COUNT)==1U && b_field(c)){
                b_copy(c,QOL_PLAYER_PARTY,actual,sizeof(actual));returned=!memcmp(actual,original,sizeof(actual));
            }
            if(returned){
                if(++stable==30U){w.facility_frame=b_frames;break;}
                b_frame(c,0U);continue;
            }
            stable=0U;
        }
        if(!w.outcome && bs && n_action(c)){
            bp_require(c,w.turns<48U,"first battle move count bound reached");br_move(c,&w);continue;
        }
        if(!w.outcome && bs && cb==P02S_CB2_PARTY){
            bp_require(c,w.switches<2U,"unexpected repeated forced switches");br_switch(c,&w);continue;
        }
        b_frame(c,(b_frames-w.start)%60U==0U?QOL_KEY_B:0U);
    }
    c->setKeys(c,0);br_trace(c,"facility-stop");sp_observe(c,"facility-afterbattle");
    bp_require(c,w.outcome_frame>w.start && w.facility_frame>=w.outcome_frame && w.turns>0U,"first battle did not reach native AfterBattle return");
    w.final_count=read8(c,QOL_PLAYER_PARTY_COUNT);w.marker=read8(c,BP_F(marker));w.snapshot=read8(c,BP_F(snapshot_valid));
    w.pending=read8(c,BP_F(reward_pending));w.streak=read16(c,BP_F(current_streak));
    w.script=read32(c,SP_SCRIPT_PTR);w.callback2=read32(c,BATTLE_CORE_MAIN_CALLBACK2);
    return w;
}
