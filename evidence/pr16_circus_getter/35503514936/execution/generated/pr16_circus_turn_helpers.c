/* 既存の受付・3体選択・実戦開始を前置条件として再利用する追加区間。
 * 観測境界後はキー入力だけ。勝敗/HP/PP/RNG/ledgerへのhost書込みなし。
 * この断片を固定hashの旧controllerのmainより前へ組み込む。 */
struct BPProgress {
    unsigned move,slot,before,after,menu,chosen,spent,returned;
    unsigned player_before,player_after,enemy_before,enemy_after;
};
static struct BPProgress bp_progress(struct mCore *c) {
    struct BPProgress w={0};
    bp_require(c,n_action(c),"progress did not start at native action");
    for(unsigned i=0;i<4U;++i){
        unsigned move=read16(c,ADDR_BATTLE_MONS+BATTLE_MON_MOVES_OFFSET+2U*i);
        unsigned pp=read8(c,ADDR_BATTLE_MONS+BATTLE_MON_PP_OFFSET+i);
        if(move && pp){w.move=move;w.slot=i;w.before=pp;break;}
    }
    bp_require(c,w.move && w.before,"no native move with PP available");
    w.player_before=read16(c,ADDR_BATTLE_MONS+BATTLE_CORE_MON_HP);
    w.enemy_before=read16(c,ADDR_BATTLE_MONS+BATTLE_MON_SIZE+BATTLE_CORE_MON_HP);
    /* command 0x12 can precede the drawn action menu. Observe every frame
     * and retry only that menu; never pulse A through command 0x14. */
    n_cursor(c,0U);
    for(unsigned f=0;f<600U;++f){
        if(read8(c,0x02022B24U)==0x14U && (read32(c,0x02023B28U)&1U))break;
        bp_require(c,!read8(c,BATTLE_CORE_BATTLE_OUTCOME) && read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER),"battle ended before first move menu");
        if(f%90U==0U)fprintf(stderr,"BP_PROGRESS_MENU frame=%u command=%u ctrl=%08x\n",b_frames,read8(c,0x02022B24U),read32(c,0x03005020U));
        b_frame(c,f%90U==0U && n_action(c)?QOL_KEY_A:0U);
    }
    b_frames_run(c,0U,60U);
    bp_require(c,read8(c,0x02022B24U)==0x14U && (read32(c,0x02023B28U)&1U),"native move menu absent");
    w.menu=b_frames;sp_observe(c,"first-move-menu");
    for(unsigned i=0;i<6U && read8(c,BATTLE_CORE_MOVE_SELECTION_CURSOR)!=w.slot;++i){
        unsigned at=read8(c,BATTLE_CORE_MOVE_SELECTION_CURSOR);
        bp_require(c,at<4U,"invalid move cursor");
        b_press(c,(at&1U)!=(w.slot&1U)?((w.slot&1U)?QOL_KEY_RIGHT:QOL_KEY_LEFT):((w.slot&2U)?QOL_KEY_DOWN:QOL_KEY_UP),12U);
    }
    bp_require(c,read8(c,BATTLE_CORE_MOVE_SELECTION_CURSOR)==w.slot,"native move navigation failed");
    w.chosen=b_frames+1U;b_press(c,QOL_KEY_A,2U);
    for(unsigned f=0;f<18000U;++f){
        unsigned pp=read8(c,ADDR_BATTLE_MONS+BATTLE_MON_PP_OFFSET+w.slot);
        if(pp<w.before && !w.spent){w.spent=b_frames;w.after=pp;sp_observe(c,"first-move-pp-spent");}
        if(w.spent && n_action(c)){w.returned=b_frames;break;}
        if(read8(c,BATTLE_CORE_BATTLE_OUTCOME) || !read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER))break;
        b_frame(c,f%60U==0U?QOL_KEY_B:0U);
    }
    c->setKeys(c,0);w.player_after=read16(c,ADDR_BATTLE_MONS+BATTLE_CORE_MON_HP);
    w.enemy_after=read16(c,ADDR_BATTLE_MONS+BATTLE_MON_SIZE+BATTLE_CORE_MON_HP);
    fprintf(stderr,"BP_PROGRESS move=%u slot=%u pp_before=%u pp_after=%u menu=%u chosen=%u spent=%u returned=%u player_hp=%u/%u enemy_hp=%u/%u outcome=%u\n",w.move,w.slot,w.before,w.after,w.menu,w.chosen,w.spent,w.returned,w.player_before,w.player_after,w.enemy_before,w.enemy_after,read8(c,BATTLE_CORE_BATTLE_OUTCOME));
    sp_observe(c,"first-turn-return");
    bp_require(c,w.spent>=w.chosen && w.returned>w.spent && w.before>w.after && w.before-w.after<=2U && n_action(c),"first native turn did not spend PP and return to action");
    bp_require(c,read16(c,ADDR_BATTLE_MONS+BATTLE_MON_MOVES_OFFSET+2U*w.slot)==w.move && read8(c,ADDR_BATTLE_MONS+BATTLE_MON_PP_OFFSET+w.slot)==w.after,"move identity or final PP differs");
    bp_require(c,!read8(c,BATTLE_CORE_BATTLE_OUTCOME) && read8(c,QOL_PLAYER_PARTY_COUNT)==3U && read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER) && !read16(c,BP_F(battle_points)) && !read8(c,BP_F(reward_pending)),"first turn awarded BP or terminated unexpectedly");
    return w;
}
