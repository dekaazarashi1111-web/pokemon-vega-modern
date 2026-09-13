/* 勝利後の単体交換→次戦だけを追加する。RAM/ROMへのhost書込みは行わない。
 * 技選択は威力・命中・攻防・STABによる決定的heuristic。勝敗の保証ではない。 */
/* 通常18タイプ(+予約9)のhost入力heuristic。能力・天候・特性を完全予測する
 * battle simulatorではない。native実データのタイプを読むだけ。未知タイプは等倍。 */
static unsigned wx_effect(unsigned attack,unsigned defense) {
    static const unsigned char table[19][19]={
        {10,10,10,10,10,5,10,0,5,10,10,10,10,10,10,10,10,10,10},
        {20,10,5,5,10,20,5,0,20,10,10,10,10,10,5,20,10,20,5},
        {10,20,10,10,10,5,20,10,5,10,10,10,20,5,10,10,10,10,10},
        {10,10,10,5,5,5,10,5,0,10,10,10,20,10,10,10,10,10,20},
        {10,10,0,20,10,20,5,10,20,10,20,10,5,20,10,10,10,10,10},
        {10,5,20,10,5,10,20,10,5,10,20,10,10,10,10,20,10,10,10},
        {10,5,5,5,10,10,10,5,5,10,5,10,20,10,20,10,10,20,5},
        {0,10,10,10,10,10,10,20,10,10,10,10,10,10,20,10,10,5,10},
        {10,10,10,10,10,20,10,10,5,10,5,5,10,5,10,20,10,10,20},
        {10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10},
        {10,10,10,10,10,5,20,10,20,10,5,5,20,10,10,20,5,10,10},
        {10,10,10,10,20,20,10,10,10,10,20,5,5,10,10,10,5,10,10},
        {10,10,5,5,20,20,5,10,5,10,5,20,5,10,10,10,5,10,10},
        {10,10,20,10,0,10,10,10,10,10,10,20,5,5,10,10,5,10,10},
        {10,20,10,20,10,10,10,10,5,10,10,10,10,10,5,10,10,0,10},
        {10,10,20,10,20,10,10,10,5,10,5,5,20,10,10,5,20,10,10},
        {10,10,10,10,10,10,10,10,5,10,10,10,10,10,10,10,20,10,0},
        {10,5,10,10,10,10,10,20,10,10,10,10,10,10,20,10,10,5,5},
        {10,20,10,5,10,10,10,10,5,10,5,10,10,10,10,10,20,20,10},
    };
    return attack<19U && defense<19U?table[attack][defense]:10U;
}
static unsigned wx_move_slot(struct mCore *c) {
    uint32_t table=read32(c,BATTLE_CORE_MOVE_TABLE_REPOINT);
    bp_require(c,table>=0x08000000U && table+1063U*12U<=0x0A000000U && !(table&3U),"win move table ABI differs");
    unsigned best=4U;uint64_t top=0;
    for(unsigned i=0;i<4U;++i){
        unsigned move=read16(c,ADDR_BATTLE_MONS+BATTLE_MON_MOVES_OFFSET+2U*i);
        unsigned pp=read8(c,ADDR_BATTLE_MONS+BATTLE_MON_PP_OFFSET+i);
        if(!move || !pp)continue;
        bp_require(c,move<=1062U,"win move ID out of canonical range");
        uint32_t row=table+12U*move;
        unsigned power=read8(c,row+1U),type=read8(c,row+2U),accuracy=read8(c,row+3U),split=read8(c,row+10U);
        bp_require(c,split<=2U && type<=24U,"win move type/split ABI differs");
        if(split==2U || !power)continue;
        unsigned attack=read16(c,ADDR_BATTLE_MONS+(split==0U?2U:8U));
        unsigned defense=read16(c,ADDR_BATTLE_MONS+BATTLE_MON_SIZE+(split==0U?4U:10U));
        uint64_t score=(uint64_t)power*(accuracy?accuracy:100U)*(attack?attack:1U)*100U/(defense?defense:1U);
        if(type==read8(c,ADDR_BATTLE_MONS+BATTLE_CORE_MON_TYPE1) || type==read8(c,ADDR_BATTLE_MONS+BATTLE_CORE_MON_TYPE2))score=score*3U/2U;
        unsigned t1=read8(c,ADDR_BATTLE_MONS+BATTLE_MON_SIZE+BATTLE_CORE_MON_TYPE1);
        unsigned t2=read8(c,ADDR_BATTLE_MONS+BATTLE_MON_SIZE+BATTLE_CORE_MON_TYPE2);
        unsigned effect=wx_effect(type,t1)*(t1==t2?10U:wx_effect(type,t2));
        score=score*effect/100U;
        fprintf(stderr,"BP_WIN_MOVE frame=%u slot=%u move=%u pp=%u power=%u type=%u split=%u score=%llu\n",b_frames,i,move,pp,power,type,split,(unsigned long long)score);
        if(best==4U || score>top){best=i;top=score;}
    }
    bp_require(c,best<4U,"win policy has no damaging move; do not inject Struggle");
    return best;
}
static unsigned wx_party_score(struct mCore *c,unsigned slot) {
    uint32_t p=QOL_PLAYER_PARTY+100U*slot;unsigned score=0;
    /* 固定100byte Party ABIのmaxHPと5能力値。現在HP/PPは変更しない。 */
    for(unsigned at=0x58U;at<100U;at+=2U)score+=read16(c,p+at);
    return score;
}
static void wx_cursor(struct mCore *c,unsigned target) {
    bp_require(c,target<6U,"win party target out of bounds");
    for(unsigned tries=0;tries<16U && read8(c,SP_PARTY_SLOT)!=target;++tries){
        unsigned at=read8(c,SP_PARTY_SLOT);
        bp_require(c,at<8U && read32(c,BATTLE_CORE_MAIN_CALLBACK2)==P02S_CB2_PARTY,"win chooser disappeared");
        unsigned key=at>=6U?QOL_KEY_UP:target==0U?QOL_KEY_LEFT:at==0U?QOL_KEY_RIGHT:at<target?QOL_KEY_DOWN:QOL_KEY_UP;
        b_press(c,key,60U);
    }
    bp_require(c,read8(c,SP_PARTY_SLOT)==target,"win party cursor did not follow keys");
}
static void wx_team(struct mCore *c) {
    unsigned used=0U;
    for(unsigned n=0;n<3U;++n){
        unsigned best=6U,score=0U;
        for(unsigned i=0;i<6U;++i){
            unsigned value=wx_party_score(c,i);
            if(!(used&(1U<<i)) && (best==6U || value>score)){best=i;score=value;}
        }
        bp_require(c,best<6U,"win rental ranking has no candidate");used|=1U<<best;
        fprintf(stderr,"BP_WIN_TEAM index=%u original_slot=%u score=%u\n",n,best,score);
        wx_cursor(c,best);sp_entry(c,n,best);
    }
}
/* CFRUのこの候補はgrowth/attackの固定平文配置。採取済みenemy実byteとも照合。
 * HealPlayerPartyのstatus/HP/PPだけをhostの比較用配列へ適用する。gameへは書かない。 */
static void wx_healed_expected(struct mCore *c,uint8_t mon[100]) {
    uint32_t table=read32(c,BATTLE_CORE_MOVE_TABLE_REPOINT);
    for(unsigned i=0;i<4U;++i){
        unsigned move=mon[0x2CU+2U*i]|((unsigned)mon[0x2DU+2U*i]<<8);
        bp_require(c,move<=1062U,"exchange cached move ABI differs");
        unsigned base=read8(c,table+12U*move+4U),boost=(mon[0x28U]>>(2U*i))&3U;
        mon[0x34U+i]=(uint8_t)(base*(5U+boost)/5U);
    }
    memset(mon+0x50U,0,4U);mon[0x56U]=mon[0x58U];mon[0x57U]=mon[0x59U];
}
/* 初手Protectの後だけ、通常PKMNメニューでslot1へ交代する。
 * 観測済みpartyのCrunch所持を境界にし、先頭を終盤まで残す。 */
static unsigned wx_voluntary_count;
static void wx_opening_switch(struct mCore *c) {
    bp_require(c,!wx_voluntary_count && n_action(c) && !read16(c,ADDR_BATTLER_PARTY_INDEXES)
        && read16(c,QOL_PLAYER_PARTY+100U+0x2CU)==242U,"opening switch fixture/phase differs");
    fprintf(stderr,"BP_WIN_SWITCH_OPENING label=start frame=%u target=1\n",b_frames);
    n_cursor(c,2U);
    for(unsigned f=0;f<900U && read32(c,BATTLE_CORE_MAIN_CALLBACK2)!=P02S_CB2_PARTY;++f)
        b_frame(c,f%90U==0U && n_action(c)?QOL_KEY_A:0U);
    bp_require(c,read32(c,BATTLE_CORE_MAIN_CALLBACK2)==P02S_CB2_PARTY,"native voluntary PKMN menu absent");
    b_frames_run(c,0U,60U);
    for(unsigned i=0;i<8U && read8(c,SP_PARTY_SLOT)!=1U;++i)b_press(c,QOL_KEY_DOWN,60U);
    bp_require(c,read8(c,SP_PARTY_SLOT)==1U,"native voluntary slot1 absent");
    b_press(c,QOL_KEY_A,80U);
    if(read32(c,BATTLE_CORE_MAIN_CALLBACK2)==P02S_CB2_PARTY)b_press(c,QOL_KEY_A,80U);
    for(unsigned f=0;f<18000U;++f){
        bp_require(c,!read8(c,BATTLE_CORE_BATTLE_OUTCOME),"opening switch unexpectedly ended battle");
        if(n_action(c) && read16(c,ADDR_BATTLER_PARTY_INDEXES)==1U){
            bp_require(c,read16(c,QOL_PLAYER_PARTY+0x56U)>0U,"opening switch did not preserve original lead");
            wx_voluntary_count=1U;
            fprintf(stderr,"BP_WIN_SWITCH_OPENING label=returned frame=%u target=1 original_hp=%u\n",b_frames,read16(c,QOL_PLAYER_PARTY+0x56U));
            g_shot("opening-voluntary-switch");return;
        }
        b_frame(c,f%60U==0U?QOL_KEY_B:0U);
    }
    bp_require(c,false,"opening switch reached 18000-frame bound");
}
/* 瀕死時は生存partyの実技/実能力値で控えを比較する。partyへ書かない。 */
static unsigned wx_reserve(struct mCore *c,unsigned active) {
    unsigned best=6U;uint64_t top=0U;
    uint32_t table=read32(c,BATTLE_CORE_MOVE_TABLE_REPOINT);
    unsigned t1=read8(c,ADDR_BATTLE_MONS+BATTLE_MON_SIZE+BATTLE_CORE_MON_TYPE1);
    unsigned t2=read8(c,ADDR_BATTLE_MONS+BATTLE_MON_SIZE+BATTLE_CORE_MON_TYPE2);
    for(unsigned i=0;i<3U;++i){
        uint32_t mon=QOL_PLAYER_PARTY+100U*i;
        if(i==active || !read16(c,mon+0x56U))continue;
        uint64_t strongest=0U;
        for(unsigned j=0;j<4U;++j){
            unsigned move=read16(c,mon+0x2CU+2U*j),pp=read8(c,mon+0x34U+j);
            bp_require(c,move<=1062U,"reserve move ABI differs");
            if(!move || !pp)continue;
            uint32_t row=table+12U*move;
            unsigned power=read8(c,row+1U),type=read8(c,row+2U),accuracy=read8(c,row+3U),split=read8(c,row+10U);
            bp_require(c,split<=2U,"reserve split ABI differs");
            if(split==2U || !power)continue;
            unsigned attack=read16(c,mon+(split==0U?0x5AU:0x60U));
            unsigned defense=read16(c,ADDR_BATTLE_MONS+BATTLE_MON_SIZE+(split==0U?4U:10U));
            uint64_t value=(uint64_t)power*(accuracy?accuracy:100U)*attack
                *wx_effect(type,t1)*(t1==t2?10U:wx_effect(type,t2))/(defense?defense:1U);
            if(value>strongest)strongest=value;
        }
        fprintf(stderr,"BP_WIN_RESERVE frame=%u slot=%u score=%llu\n",b_frames,i,(unsigned long long)strongest);
        if(best==6U || strongest>top){best=i;top=strongest;}
    }
    return best;
}
/* WX_EXTENSION_BOUNDARY */
/* run34767145222では単体order=3の記録後もcursor=2。自動Confirm移動は
 * CursorCb_Enterのmax依存であり、単体選択成立の必要条件ではない。
 * 既存の次戦chooser同様、通常UP入力だけでConfirmへ移動する。
 * 選択6byte・owner・callback・未開戦を毎入力の前後で再確認する。 */
static void wx_single_confirm(struct mCore *c,unsigned slot) {
    bp_require(c,slot<3U,"single selection slot out of bounds");
    for(unsigned k=0U;k<=8U;++k){
        bp_require(c,read32(c,BATTLE_CORE_MAIN_CALLBACK2)==P02S_CB2_PARTY
            && read32(c,SP_SCRIPT_PTR)==0x092CF72CU
            && !read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER),"single chooser owner changed before Confirm");
        for(unsigned i=0U;i<6U;++i)
            bp_require(c,read8(c,SP_ORDER_CFRU+i)==(i?0U:slot+1U),"single selected order changed before Confirm");
        unsigned cursor=read8(c,SP_PARTY_SLOT);
        bp_require(c,cursor<8U,"single chooser cursor out of bounds");
        if(cursor==6U)return;
        bp_require(c,k<8U,"single Confirm navigation reached 8-input bound");
        b_press(c,QOL_KEY_UP,60U);
        fprintf(stderr,"BP_EXCHANGE_CONFIRM frame=%u input=%u cursor=%u order=%u\n",
            b_frames,k+1U,read8(c,SP_PARTY_SLOT),read8(c,SP_ORDER_CFRU));
    }
}
/* scratch消去はCommitExchangeの途中。run34769665360では最初のPPだけが
 * 回復したframe17303で止まった。次のscript命令境界へ進んでから600byteを
 * 一度だけ厳密比較する。実行途中の092CF731や比較成功そのものを完了条件にしない。
 * 092CF680 message / 092CF688 PrepareBattleは既存candidate scriptの固定境界。 */
static bool wx_commit_returned(struct mCore *c) {
    if(read32(c,VEGA_SAVE_TRANSACTION_SCRATCH_ADDRESS)
        || read32(c,BATTLE_CORE_MAIN_CALLBACK2)!=0x08055E75U
        || read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER))return false;
    switch(read32(c,SP_SCRIPT_PTR)){
        case 0x092CF680U: case 0x092CF686U:
        case 0x092CF688U: case 0x092CF68DU:return true;
        default:return false;
    }
}
struct WXResult {unsigned menu,selected,confirm,commit,allocated,action,slot,order,preserved,replaced,opening;};
static struct WXResult wx_exchange_next(struct mCore *c,const uint8_t *original,unsigned counter) {
    struct WXResult w={.opening=wx_voluntary_count};unsigned start=b_frames;uint8_t expected[600],actual[600],cached[100],snapshot[600];
    bp_require(c,read8(c,BATTLE_CORE_BATTLE_OUTCOME)==1U,"exchange requires native victory");
    br_trace(c,"win-exchange-start");
    for(unsigned f=0;f<12000U;++f){
        bp_require(c,!read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER),"battle launched before exchange observation");
        if(read32(c,BATTLE_CORE_MAIN_CALLBACK2)==P02S_CB2_PARTY){w.menu=b_frames;b_frames_run(c,0U,180U);break;}
        b_frame(c,f%90U==0U?QOL_KEY_A:0U);
    }
    bp_require(c,w.menu>start && read8(c,QOL_PLAYER_PARTY_COUNT)==3U
        && read32(c,SP_SCRIPT_PTR)==0x092CF72CU
        && read32(c,VEGA_SAVE_TRANSACTION_SCRATCH_ADDRESS)==0x58434846U,"native exchange chooser/owner absent");
    for(unsigned i=0;i<6U;++i)bp_require(c,!read8(c,SP_ORDER_CFRU+i),"single chooser order was not cleared");
    b_copy(c,QOL_PLAYER_PARTY,expected,sizeof(expected));b_copy(c,VEGA_SAVE_TRANSACTION_SCRATCH_ADDRESS+4U,cached,sizeof(cached));
    bp_read_span(c,"exchange_cached_original",VEGA_SAVE_TRANSACTION_SCRATCH_ADDRESS+4U,100U);
    /* 今回は現在の能力値合計が最小の1枠だけをnative UIから交換する。 */
    w.slot=0U;for(unsigned i=1;i<3U;++i)if(wx_party_score(c,i)<wx_party_score(c,w.slot))w.slot=i;
    wx_healed_expected(c,cached);memcpy(expected+100U*w.slot,cached,100U);
    sp_observe(c,"exchange-single-menu");wx_cursor(c,w.slot);sp_entry(c,0U,w.slot);w.selected=b_frames;
    w.order=read8(c,SP_ORDER_CFRU);
    bp_require(c,w.order==w.slot+1U,"single selection order differs");
    wx_single_confirm(c,w.slot);
    for(unsigned i=1;i<6U;++i)bp_require(c,!read8(c,SP_ORDER_CFRU+i),"single chooser selected extra slots");
    sp_observe(c,"exchange-single-selected");w.confirm=b_frames+1U;b_press(c,QOL_KEY_A,2U);
    for(unsigned f=0;f<12000U;++f){
        uint32_t bs=read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER),cb=read32(c,BATTLE_CORE_MAIN_CALLBACK2);
        if(!w.commit && wx_commit_returned(c)){
            w.commit=b_frames;b_copy(c,QOL_PLAYER_PARTY,actual,sizeof(actual));
            bp_read_span(c,"exchange_party_committed",QOL_PLAYER_PARTY,600U);
            bp_require(c,!memcmp(expected,actual,sizeof(actual)),"exchange exact600 compare (selected healed100 + unchanged500) failed");
            for(unsigned i=0;i<3U;++i)bp_require(c,read8(c,SP_ORDER_CFRU+i)==i+1U,"CommitExchange did not normalize order");
            w.replaced=100U;w.preserved=500U;sp_observe(c,"exchange-committed");
        }
        if(bs && !w.allocated){bp_require(c,w.commit>0U,"next battle preceded exchange commit");w.allocated=b_frames;}
        if(w.allocated && n_action(c)){w.action=b_frames;break;}
        b_copy(c,BP_F(party_snapshot),snapshot,sizeof(snapshot));
        bp_require(c,!memcmp(snapshot,original,sizeof(snapshot)) && read8(c,BP_F(marker))==2U
            && read8(c,BP_F(snapshot_valid))==1U && read8(c,BP_F(reward_pending))==1U
            && read16(c,BP_F(current_streak))==1U && !read16(c,BP_F(battle_points))
            && read32(c,P03_SAVE_COUNTER)==counter,"exchange changed original snapshot/ledger/save unexpectedly");
        if(w.commit && cb==P02S_CB2_PARTY && read8(c,SP_PARTY_SLOT)!=6U){
            b_press(c,QOL_KEY_UP,60U);continue;
        }
        b_frame(c,f%90U==0U?QOL_KEY_A:0U);
    }
    c->setKeys(c,0U);br_trace(c,"exchange-next-action");sp_observe(c,"exchange-next-action");
    bp_require(c,w.menu<w.selected && w.selected<w.confirm && w.confirm<=w.commit
        && w.commit<=w.allocated && w.allocated<=w.action && w.action==b_frames
        && !read8(c,BATTLE_CORE_BATTLE_OUTCOME) && sp_enemy_count(c)==3U,"native exchange did not reach next battle/action");
    return w;
}
