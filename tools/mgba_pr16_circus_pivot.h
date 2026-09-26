#ifndef VEGA_CIRCUS_PIVOT_POLICY_H
#define VEGA_CIRCUS_PIVOT_POLICY_H
/* 入力controllerのみ。第3戦の先発を通常PARTYコマンドで温存する。 */
static unsigned pv_allowed(unsigned streak,unsigned done,unsigned own_type1,unsigned own_type2,
    unsigned enemy_type1,unsigned enemy_type2)
{
    return streak==2U && !done && own_type1!=0U && own_type2!=0U
        && enemy_type1==0U && enemy_type2==0U;
}
#ifndef CIRCUS_PIVOT_HOST_TEST
static unsigned pv_done;
static unsigned pv_move_slot(struct mCore *c)
{
    uint32_t mon=ADDR_BATTLE_MONS,foe=mon+BATTLE_MON_SIZE;
    if(pv_allowed(read16(c,0x0203DB20U),pv_done,read8(c,mon+BATTLE_CORE_MON_TYPE1),
        read8(c,mon+BATTLE_CORE_MON_TYPE2),read8(c,foe+BATTLE_CORE_MON_TYPE1),read8(c,foe+BATTLE_CORE_MON_TYPE2))){
        unsigned active=read16(c,ADDR_BATTLER_PARTY_INDEXES),target=3U;
        for(unsigned i=0;i<3U;++i){
            uint32_t p=QOL_PLAYER_PARTY+100U*i;unsigned toxic=0U,shadow=0U;
            for(unsigned j=0;j<4U;++j){unsigned move=read16(c,p+0x2CU+2U*j);
                if(read8(c,p+0x34U+j)){toxic|=move==92U;shadow|=move==247U;}}
            if(i!=active && read16(c,p+0x56U)>0U && toxic && shadow){
                bp_require(c,target==3U,"Circus pivot ambiguous rental");target=i;}
        }
        bp_require(c,target<3U && n_action(c),"Circus pivot requires living Toxic/Shadow Ball rental");
        uint32_t p=QOL_PLAYER_PARTY+100U*target,pid=read32(c,p),ot=read32(c,p+4U);
        unsigned species=read16(c,p+0x20U),before=b_frames;
        fprintf(stderr,"CIRCUS_PIVOT {\"label\":\"begin\",\"frame\":%u,\"from\":%u,\"target\":%u,\"pid\":%u,\"ot\":%u,\"species\":%u}\n",before,active,target,pid,ot,species);
        n_cursor(c,2U);b_press(c,QOL_KEY_A,120U);
        for(unsigned f=0;f<1800U && read32(c,BATTLE_CORE_MAIN_CALLBACK2)!=P02S_CB2_PARTY;++f)b_frame(c,0U);
        bp_require(c,read32(c,BATTLE_CORE_MAIN_CALLBACK2)==P02S_CB2_PARTY,"Circus pivot normal PARTY menu absent");
        b_frames_run(c,0U,60U);wx_cursor(c,target);g_shot("pivot-party");
        b_press(c,QOL_KEY_A,80U);
        if(read32(c,BATTLE_CORE_MAIN_CALLBACK2)==P02S_CB2_PARTY)b_press(c,QOL_KEY_A,80U);
        for(unsigned f=0;f<18000U;++f){
            if(n_action(c) && read32(c,mon+0x48U)==pid && read32(c,mon+0x54U)==ot
                && read16(c,mon)==species)break;
            bp_require(c,!read8(c,BATTLE_CORE_BATTLE_OUTCOME),"Circus pivot ended battle unexpectedly");
            b_frame(c,f%90U==0U?QOL_KEY_B:0U);
        }
        bp_require(c,n_action(c) && read32(c,mon+0x48U)==pid && read32(c,mon+0x54U)==ot
            && read16(c,mon)==species && read16(c,mon+BATTLE_CORE_MON_HP)>0U
            && read8(c,mon+BATTLE_CORE_MON_TYPE1)==0U && read8(c,mon+BATTLE_CORE_MON_TYPE2)==0U,
            "Circus pivot actual selected Normal individual absent");
        pv_done=1U;g_shot("pivot-action");
        fprintf(stderr,"CIRCUS_PIVOT {\"label\":\"done\",\"frame\":%u,\"from\":%u,\"target\":%u,\"pid\":%u,\"ot\":%u,\"species\":%u}\n",b_frames,active,target,pid,ot,species);
    }
    return ef_move_slot(c);
}
#endif
#endif
