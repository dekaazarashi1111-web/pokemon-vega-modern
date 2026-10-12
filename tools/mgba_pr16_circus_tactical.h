#ifndef VEGA_CIRCUS_TACTICAL_H
#define VEGA_CIRCUS_TACTICAL_H
#include <stdint.h>
/* 16戦目の毒/混乱＋Ghost攻撃と、その後の炎対面から限定追加した通常交代。
 * species/RNG/勝敗は使わない。場のtypeと技種を読み、控えの使用可能技から選ぶ。
 * 技typeから控えの種族typeを断定しない。交代後の実個体/typeも別に記録する。 */
static unsigned tp_request(unsigned streak,unsigned own1,unsigned own2,
    unsigned foe1,unsigned foe2,uint32_t attacks)
{
    if(streak<15U)return 25U;
    unsigned target=25U;
    if(foe1==10U && foe2==10U)target=11U;
    else if(foe1==11U && foe2==11U)target=12U;
    else if(foe1==12U && foe2==12U)target=10U;
    else if(attacks==(1U<<7U))target=17U;
    return own1==target || own2==target?25U:target;
}
static uint64_t tp_rank(unsigned power,unsigned accuracy,unsigned attack,
    unsigned hp,unsigned maxhp)
{
    if(!power || !hp || !maxhp || hp>maxhp || accuracy>100U)return 0U;
    return (uint64_t)power*(accuracy?accuracy:100U)*attack*hp/maxhp;
}
#ifndef CIRCUS_TACTICAL_HOST_TEST
static unsigned tp_streak=65535U,tp_switches,tp_seen;
static uint32_t tp_foe,tp_foe_ot;
static void tp_consider(struct mCore *c)
{
    unsigned streak=read16(c,0x0203DB20U);if(streak<15U)return;
    uint32_t own=ADDR_BATTLE_MONS,foe=own+BATTLE_MON_SIZE,table=read32(c,BATTLE_CORE_MOVE_TABLE_REPOINT);
    bp_require(c,n_action(c) && table>=0x08000000U && table+1063U*12U<=0x0A000000U && !(table&3U),"Circus tactical action/table boundary");
    uint32_t pid=read32(c,foe+0x48U),ot=read32(c,foe+0x54U),attacks=0U;
    if(tp_streak!=streak){tp_streak=streak;tp_switches=tp_seen=0U;}
    if(tp_seen && pid==tp_foe && ot==tp_foe_ot)return;
    if(tp_switches>=6U)return;
    for(unsigned i=0;i<4U;++i){
        unsigned move=read16(c,foe+BATTLE_MON_MOVES_OFFSET+2U*i);
        bp_require(c,move<=1062U,"Circus tactical foe move ABI");
        if(!move || !read8(c,foe+BATTLE_MON_PP_OFFSET+i))continue;
        uint32_t row=table+12U*move;unsigned type=read8(c,row+2U);
        bp_require(c,type<=24U,"Circus tactical foe type ABI");
        if(read8(c,row+1U) && read8(c,row+10U)<2U)attacks|=1U<<type;
    }
    unsigned wanted=tp_request(streak,read8(c,own+BATTLE_CORE_MON_TYPE1),read8(c,own+BATTLE_CORE_MON_TYPE2),
        read8(c,foe+BATTLE_CORE_MON_TYPE1),read8(c,foe+BATTLE_CORE_MON_TYPE2),attacks);
    if(wanted==25U)return;
    uint32_t active=read32(c,own+0x48U),active_ot=read32(c,own+0x54U);
    unsigned target=3U;uint64_t best=0U;
    for(unsigned i=0;i<3U;++i){
        uint32_t p=QOL_PLAYER_PARTY+100U*i;
        if(read32(c,p)==active && read32(c,p+4U)==active_ot)continue;
        for(unsigned j=0;j<4U;++j){
            unsigned move=read16(c,p+0x2CU+2U*j);
            bp_require(c,move<=1062U,"Circus tactical reserve move ABI");
            if(!move || !read8(c,p+0x34U+j))continue;
            uint32_t row=table+12U*move;unsigned split=read8(c,row+10U);
            if(split>1U || read8(c,row+2U)!=wanted)continue;
            uint64_t score=tp_rank(read8(c,row+1U),read8(c,row+3U),read16(c,p+(split?0x60U:0x5AU)),
                read16(c,p+0x56U),read16(c,p+0x58U));
            if(score>best){best=score;target=i;}
        }
    }
    if(target==3U)return;
    uint32_t p=QOL_PLAYER_PARTY+100U*target,target_pid=read32(c,p),target_ot=read32(c,p+4U);
    unsigned species=read16(c,p+0x20U);
    tp_seen=1U;tp_foe=pid;tp_foe_ot=ot;++tp_switches;
    fprintf(stderr,"CIRCUS_TACTICAL begin frame=%u streak=%u foe=%u foe_ot=%u target_pid=%u target_ot=%u species=%u attack_type=%u count=%u\n",b_frames,streak,pid,ot,target_pid,target_ot,species,wanted,tp_switches);
    n_cursor(c,2U);b_press(c,QOL_KEY_A,120U);
    for(unsigned f=0;f<1800U && read32(c,BATTLE_CORE_MAIN_CALLBACK2)!=P02S_CB2_PARTY;++f)b_frame(c,0U);
    bp_require(c,read32(c,BATTLE_CORE_MAIN_CALLBACK2)==P02S_CB2_PARTY,"Circus tactical normal party menu absent");
    b_frames_run(c,0U,60U);
    uint32_t menu_pid[3],menu_ot[3];uint16_t menu_species[3];
    for(unsigned i=0;i<3U;++i){uint32_t q=QOL_PLAYER_PARTY+100U*i;
        menu_pid[i]=read32(c,q);menu_ot[i]=read32(c,q+4U);menu_species[i]=read16(c,q+0x20U);}
    unsigned slot=mi_find(read8(c,QOL_PLAYER_PARTY_COUNT),menu_pid,menu_ot,menu_species,target_pid,target_ot,species);
    bp_require(c,slot<3U,"Circus tactical menu individual absent/ambiguous");wx_cursor(c,slot);
    b_press(c,QOL_KEY_A,80U);if(read32(c,BATTLE_CORE_MAIN_CALLBACK2)==P02S_CB2_PARTY)b_press(c,QOL_KEY_A,80U);
    for(unsigned f=0;f<18000U;++f){
        if(n_action(c) && read32(c,own+0x48U)==target_pid && read32(c,own+0x54U)==target_ot && read16(c,own)==species)break;
        bp_require(c,!read8(c,BATTLE_CORE_BATTLE_OUTCOME),"Circus tactical switch ended unexpectedly");
        b_frame(c,f%90U==0U?QOL_KEY_B:0U);
    }
    bp_require(c,n_action(c) && read32(c,own+0x48U)==target_pid && read32(c,own+0x54U)==target_ot
        && read16(c,own)==species && read16(c,own+BATTLE_CORE_MON_HP),"Circus tactical selected individual did not survive to action");
    fprintf(stderr,"CIRCUS_TACTICAL done frame=%u streak=%u foe=%u foe_ot=%u target_pid=%u target_ot=%u species=%u attack_type=%u count=%u types=%u,%u\n",b_frames,streak,pid,ot,target_pid,target_ot,species,wanted,tp_switches,read8(c,own+BATTLE_CORE_MON_TYPE1),read8(c,own+BATTLE_CORE_MON_TYPE2));
}
#endif
#endif
