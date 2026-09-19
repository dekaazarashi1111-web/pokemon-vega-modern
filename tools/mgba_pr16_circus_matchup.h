#ifndef VEGA_CIRCUS_MATCHUP_H
#define VEGA_CIRCUS_MATCHUP_H
#include <stdint.h>
/* 純粋な入力選択。施設/RNG/能力/owner/partyへhost書込みは行わない。 */
static unsigned mt_role(unsigned streak,unsigned own,unsigned foe,uint32_t status,uint32_t foe_status,unsigned hp,unsigned maxhp)
{
    if(streak!=2U)return 0U;
    if(own==12U && foe==10U)return 10U;
    if(own==10U && foe==11U)return 12U;
    if(own==0U && foe==0U && (status&0x88U) && (foe_status&0x88U)
        && (uint64_t)hp*3U<(uint64_t)maxhp*2U)return 12U;
    return 0U;
}
static unsigned mt_toxic(unsigned immune,unsigned spent,unsigned pp,uint32_t status,unsigned t1,unsigned t2)
{
    return immune && spent<4U && pp && !status && t1!=3U && t2!=3U && t1!=8U && t2!=8U;
}
struct mt_feedback {uint32_t own,foe;unsigned seen,toxic_pp,spent,last_slot,last_move,last_pp;};
static unsigned mt_spent(struct mt_feedback *m,uint32_t own,uint32_t foe,unsigned pp)
{
    if(!m->seen || own!=m->own || foe!=m->foe || pp>m->toxic_pp)
        *m=(struct mt_feedback){.own=own,.foe=foe,.seen=1U,.toxic_pp=pp};
    else if(pp<m->toxic_pp)++m->spent;
    m->toxic_pp=pp;return m->spent;
}
#ifndef CIRCUS_MATCHUP_HOST_TEST
static struct mt_feedback mt_memory;
static unsigned mt_shifts;
static unsigned mt_party_move(struct mCore *c,uint32_t p,unsigned move)
{
    for(unsigned i=0;i<4U;++i)
        if(read16(c,p+0x2CU+2U*i)==move && read8(c,p+0x34U+i))return 1U;
    return 0U;
}
static unsigned mt_shift(struct mCore *c,unsigned role)
{
    unsigned active=read16(c,ADDR_BATTLER_PARTY_INDEXES),target=3U;
    for(unsigned i=0;i<3U;++i){uint32_t p=QOL_PLAYER_PARTY+100U*i;
        if(i!=active && read16(c,p+0x56U) && mt_party_move(c,p,role==10U?53U:202U)){
            bp_require(c,target==3U,"Circus matchup ambiguous reserve");target=i;}}
    if(target==3U)return 0U;
    bp_require(c,mt_shifts<6U && n_action(c),"Circus matchup switch bound");
    uint32_t p=QOL_PLAYER_PARTY+100U*target,pid=read32(c,p),ot=read32(c,p+4U),mon=ADDR_BATTLE_MONS;
    unsigned species=read16(c,p+0x20U);
    fprintf(stderr,"CIRCUS_MATCHUP {\"label\":\"begin\",\"frame\":%u,\"from\":%u,\"target\":%u,\"pid\":%u,\"ot\":%u,\"species\":%u,\"type\":%u}\n",b_frames,active,target,pid,ot,species,role);
    n_cursor(c,2U);b_press(c,QOL_KEY_A,120U);
    for(unsigned f=0;f<1800U && read32(c,BATTLE_CORE_MAIN_CALLBACK2)!=P02S_CB2_PARTY;++f)b_frame(c,0U);
    bp_require(c,read32(c,BATTLE_CORE_MAIN_CALLBACK2)==P02S_CB2_PARTY,"Circus matchup normal party menu absent");
    b_frames_run(c,0U,60U);wx_cursor(c,target);
    char shot[64];snprintf(shot,sizeof(shot),"matchup-%u-party",mt_shifts+1U);g_shot(shot);
    b_press(c,QOL_KEY_A,80U);
    if(read32(c,BATTLE_CORE_MAIN_CALLBACK2)==P02S_CB2_PARTY)b_press(c,QOL_KEY_A,80U);
    for(unsigned f=0;f<18000U;++f){
        if(n_action(c) && read32(c,mon+0x48U)==pid && read32(c,mon+0x54U)==ot && read16(c,mon)==species)break;
        bp_require(c,!read8(c,BATTLE_CORE_BATTLE_OUTCOME),"Circus matchup switch ended unexpectedly");
        b_frame(c,f%90U==0U?QOL_KEY_B:0U);
    }
    bp_require(c,n_action(c) && read32(c,mon+0x48U)==pid && read32(c,mon+0x54U)==ot
        && read16(c,mon)==species && read16(c,mon+BATTLE_CORE_MON_HP)>0U
        && read8(c,mon+BATTLE_CORE_MON_TYPE1)==role && read8(c,mon+BATTLE_CORE_MON_TYPE2)==role,
        "Circus matchup actual selected individual/type absent");
    ++mt_shifts;snprintf(shot,sizeof(shot),"matchup-%u-action",mt_shifts);g_shot(shot);
    fprintf(stderr,"CIRCUS_MATCHUP {\"label\":\"done\",\"frame\":%u,\"from\":%u,\"target\":%u,\"pid\":%u,\"ot\":%u,\"species\":%u,\"type\":%u}\n",b_frames,active,target,pid,ot,species,role);
    return 1U;
}
static unsigned mt_move_slot(struct mCore *c)
{
    uint32_t mon=ADDR_BATTLE_MONS,foe=mon+BATTLE_MON_SIZE;
    unsigned streak=read16(c,0x0203DB20U);
    if(streak==2U && mt_memory.seen && mt_memory.own==read32(c,mon+0x48U)
        && mt_memory.foe==read32(c,foe+0x48U) && mt_memory.last_move==73U
        && read8(c,mon+BATTLE_MON_PP_OFFSET+mt_memory.last_slot)==mt_memory.last_pp)
        su_memory.seed=0U; /* 混乱等でPP未消費ならSeed試行として数えない。 */
    unsigned selected=pv_move_slot(c);
    if(streak!=2U)return selected;
    unsigned role=mt_role(streak,read8(c,mon+BATTLE_CORE_MON_TYPE1),read8(c,foe+BATTLE_CORE_MON_TYPE1),
        read32(c,mon+BATTLE_CORE_MON_STATUS1),read32(c,foe+BATTLE_CORE_MON_STATUS1),
        read16(c,mon+BATTLE_CORE_MON_HP),read16(c,mon+0x2CU));
    if(role && mt_shift(c,role))selected=pv_move_slot(c);
    unsigned toxic=4U,drain=4U,damaging=0U,effective=0U;
    uint32_t table=read32(c,BATTLE_CORE_MOVE_TABLE_REPOINT);
    unsigned t1=read8(c,foe+BATTLE_CORE_MON_TYPE1),t2=read8(c,foe+BATTLE_CORE_MON_TYPE2);
    for(unsigned i=0;i<4U;++i){
        unsigned move=read16(c,mon+BATTLE_MON_MOVES_OFFSET+2U*i),pp=read8(c,mon+BATTLE_MON_PP_OFFSET+i);
        if(!move || !pp)continue;
        if(move==92U)toxic=i;
        if(move==202U)drain=i;
        uint32_t row=table+12U*move;
        if(read8(c,row+1U)>0U && read8(c,row+10U)<2U){
            ++damaging;unsigned type=read8(c,row+2U);
            if(wx_effect(type,t1) && wx_effect(type,t2))++effective;
        }
    }
    unsigned pp=toxic<4U?read8(c,mon+BATTLE_MON_PP_OFFSET+toxic):0U;
    unsigned spent=mt_spent(&mt_memory,read32(c,mon+0x48U),read32(c,foe+0x48U),pp),old=selected;
    if(mt_toxic(damaging && !effective,spent,pp,read32(c,foe+BATTLE_CORE_MON_STATUS1),t1,t2))selected=toxic;
    if(drain<4U && read8(c,mon+BATTLE_CORE_MON_TYPE1)==12U && t1==11U && t2==11U)selected=drain;
    unsigned before=read16(c,mon+BATTLE_MON_MOVES_OFFSET+2U*old),move=read16(c,mon+BATTLE_MON_MOVES_OFFSET+2U*selected);
    if(selected!=old){
        if(before==92U && su_memory.toxic)--su_memory.toxic;
        if(before==73U && su_memory.seed)--su_memory.seed;
        if(before==109U && su_memory.confuse)--su_memory.confuse;
        if(before==347U && su_memory.setup)--su_memory.setup;
        su_memory.last=move;
    }
    mt_memory.last_slot=selected;mt_memory.last_move=move;mt_memory.last_pp=read8(c,mon+BATTLE_MON_PP_OFFSET+selected);
    fprintf(stderr,"CIRCUS_MATCHUP_MOVE frame=%u old=%u actual=%u move=%u toxic_paid=%u toxic_pp=%u shifts=%u\n",b_frames,old,selected,move,spent,pp,mt_shifts);
    return selected;
}
#endif
#endif
