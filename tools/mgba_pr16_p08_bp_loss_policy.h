/* 敗北帰還の未完境界へ進む通常入力方策。状態・勝敗・HP/PPは変更しない。
 * 第1turnまでは元runnerのまま。以降は残PPのある変化技→低威力技を選ぶ。
 * 旧試行との差分が初めて現れる入力位置をbyte-prefix照合用に記録する。 */
static unsigned p08_loss_rank(unsigned power,unsigned split) {
    return split==2U?0U:1U+power;
}
static unsigned p08_loss_slot(struct mCore *c) {
    uint32_t table=read32(c,BATTLE_CORE_MOVE_TABLE_REPOINT);
    bp_require(c,table>=0x08000000U && table+1063U*12U<=0x0A000000U && !(table&3U),"P08 loss move table ABI");
    unsigned best=4U,rank=~0U,legacy=4U,moves[4]={0},pps[4]={0},powers[4]={0},splits[4]={0};
    for(unsigned i=0;i<4U;++i){
        unsigned move=read16(c,ADDR_BATTLE_MONS+BATTLE_MON_MOVES_OFFSET+2U*i);
        unsigned pp=read8(c,ADDR_BATTLE_MONS+BATTLE_MON_PP_OFFSET+i);
        if(!move || !pp)continue;
        bp_require(c,move<=1062U,"P08 loss move ID");
        unsigned power=read8(c,table+12U*move+1U),split=read8(c,table+12U*move+10U);
        bp_require(c,split<=2U,"P08 loss split ABI");
        moves[i]=move;pps[i]=pp;powers[i]=power;splits[i]=split;
        unsigned score=p08_loss_rank(power,split);
        if(legacy==4U)legacy=i;
        if(best==4U || score<rank){best=i;rank=score;}
    }
    bp_require(c,best<4U,"P08 loss has no move with PP; no injected Struggle");
    static bool changed=false;
    if(!changed && best!=legacy){
        fprintf(stderr,"P08_BP_INPUT_CHANGE {\"frame\":%u,\"old_slot\":%u,\"new_slot\":%u}\n",b_frames,legacy,best);changed=true;
    }
    if(changed){
        fprintf(stderr,"P08_BP_POLICY frame=%u chosen=%u",b_frames,best);
        for(unsigned i=0;i<4U;++i)fprintf(stderr," move%u=%u pp%u=%u power%u=%u split%u=%u",i,moves[i],i,pps[i],i,powers[i],i,splits[i]);
        fputc('\n',stderr);
    }
    return best;
}
